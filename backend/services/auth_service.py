"""
============================================
services/auth_service.py - 認證服務
============================================

【職責】
- 使用者認證（登入、登出）
- 使用者註冊
- 密碼管理（重設、修改）
- Token 管理
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token

from .base import BaseService, ServiceResult, ServiceErrorCode, PermissionMixin


# ============================================
# 資料傳輸物件（DTO）
# ============================================

@dataclass
class LoginDTO:
    """登入資料"""
    email: str
    password: str


@dataclass
class RegisterDTO:
    """註冊資料"""
    email: str
    password: str
    username: str
    department: Optional[str] = None


@dataclass
class UserDTO:
    """使用者資料"""
    id: int
    email: str
    username: str
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    role: str = 'member'
    
    @classmethod
    def from_model(cls, user) -> 'UserDTO':
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            avatar_url=user.avatar_url,
            department=user.department,
            role=user.role
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'avatar_url': self.avatar_url,
            'department': self.department,
            'role': self.role
        }


# ============================================
# 密碼服務
# ============================================

class PasswordService(BaseService):
    """
    密碼相關服務
    
    處理密碼的：
    - 強度驗證
    - 雜湊
    - 驗證
    - 重設
    """
    
    def validate_strength(self, password: str) -> ServiceResult[bool]:
        """
        驗證密碼強度
        
        根據設定檢查：
        - 最小長度
        - 是否需要大寫字母
        - 是否需要數字
        - 是否需要特殊字元
        """
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
        require_upper = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', False)
        require_numbers = current_app.config.get('PASSWORD_REQUIRE_NUMBERS', False)
        require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', False)
        
        if len(password) < min_length:
            return ServiceResult.validation_error(
                f'Password must be at least {min_length} characters'
            )
        
        if require_upper and not any(c.isupper() for c in password):
            return ServiceResult.validation_error(
                'Password must contain at least one uppercase letter'
            )
        
        if require_numbers and not any(c.isdigit() for c in password):
            return ServiceResult.validation_error(
                'Password must contain at least one number'
            )
        
        if require_special and not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            return ServiceResult.validation_error(
                'Password must contain at least one special character'
            )
        
        return ServiceResult.ok(True)
    
    def hash_password(self, password: str) -> str:
        """雜湊密碼"""
        bcrypt = self._get_bcrypt()
        return bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """驗證密碼"""
        bcrypt = self._get_bcrypt()
        return bcrypt.check_password_hash(password_hash, password)
    
    def generate_reset_token(self) -> str:
        """產生密碼重設 Token"""
        return secrets.token_urlsafe(32)
    
    def _get_bcrypt(self):
        """取得 bcrypt 實例"""
        bcrypt = current_app.extensions.get('bcrypt')
        if bcrypt is None:
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt(current_app)
            current_app.extensions['bcrypt'] = bcrypt
        return bcrypt


# ============================================
# 帳號鎖定服務
# ============================================

class AccountLockService(BaseService):
    """
    帳號鎖定服務
    
    處理：
    - 登入嘗試記錄
    - 帳號鎖定檢查
    """
    
    def __init__(self, lockout_threshold: int = 5, lockout_duration: int = 15):
        super().__init__()
        self._lockout_threshold = lockout_threshold
        self._lockout_duration = lockout_duration  # 分鐘
    
    def is_locked(self, email: str) -> Tuple[bool, int]:
        """
        檢查帳號是否被鎖定
        
        Returns:
            Tuple[bool, int]: (是否鎖定, 剩餘分鐘數)
        """
        from models import LoginAttempt
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._lockout_duration)
        
        failed_attempts = LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success.is_(False),
            LoginAttempt.timestamp > cutoff_time
        ).count()

        if failed_attempts >= self._lockout_threshold:
            last_attempt = LoginAttempt.query.filter(
                LoginAttempt.email == email,
                LoginAttempt.success.is_(False)
            ).order_by(LoginAttempt.timestamp.desc()).first()
            
            if last_attempt:
                unlock_time = last_attempt.timestamp + timedelta(minutes=self._lockout_duration)
                remaining = (unlock_time - datetime.utcnow()).total_seconds() / 60
                return True, max(0, int(remaining))
        
        return False, 0
    
    def record_attempt(self, email: str, success: bool, failure_reason: str = None) -> None:
        """記錄登入嘗試"""
        from models import db, LoginAttempt
        
        try:
            attempt = LoginAttempt(
                email=email,
                ip_address=request.remote_addr if request else None,
                success=success,
                failure_reason=failure_reason
            )
            db.session.add(attempt)
            db.session.commit()
        except Exception as e:
            self._log_error(f"Failed to record login attempt: {str(e)}")
            db.session.rollback()


# ============================================
# 認證服務
# ============================================

class AuthService(BaseService, PermissionMixin):
    """
    認證服務
    
    處理：
    - 使用者登入
    - 使用者註冊
    - Token 刷新
    - 個人資料管理
    """
    
    def __init__(self):
        super().__init__()
        self._password_service = PasswordService()
        self._lock_service = AccountLockService()
    
    def login(self, email: str, password: str) -> ServiceResult[dict]:
        """
        使用者登入
        
        流程：
        1. 檢查帳號是否被鎖定
        2. 查找使用者
        3. 驗證密碼
        4. 產生 Token
        5. 記錄登入
        """
        from models import db, User
        
        # 1. 檢查帳號鎖定
        is_locked, remaining_minutes = self._lock_service.is_locked(email)
        if is_locked:
            return ServiceResult.fail(
                ServiceErrorCode.FORBIDDEN,
                f'Account is temporarily locked. Please try again in {remaining_minutes} minutes.'
            )
        
        # 2. 查找使用者
        user = User.query.filter_by(email=email).first()
        if not user:
            self._lock_service.record_attempt(email, False, 'User not found')
            return ServiceResult.fail(
                ServiceErrorCode.UNAUTHORIZED,
                'Invalid email or password'
            )
        
        # 3. 檢查帳號狀態
        if not user.is_active:
            self._lock_service.record_attempt(email, False, 'Account disabled')
            return ServiceResult.fail(
                ServiceErrorCode.FORBIDDEN,
                'Account has been disabled'
            )
        
        # 4. 驗證密碼
        if not self._password_service.verify_password(password, user.password_hash):
            self._lock_service.record_attempt(email, False, 'Invalid password')
            return ServiceResult.fail(
                ServiceErrorCode.UNAUTHORIZED,
                'Invalid email or password'
            )
        
        # 5. 成功登入
        self._lock_service.record_attempt(email, True)
        
        # 更新最後登入時間
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 產生 Token
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        self._log_info(f"User {email} logged in successfully")
        
        return ServiceResult.ok({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': UserDTO.from_model(user).to_dict()
        })
    
    def register(self, email: str, password: str, username: str, 
                 department: str = None) -> ServiceResult[dict]:
        """
        使用者註冊
        """
        from models import db, User
        
        # 1. 檢查 email 是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return ServiceResult.conflict('Email already registered')
        
        # 2. 驗證密碼強度
        password_result = self._password_service.validate_strength(password)
        if not password_result.is_ok():
            return password_result
        
        # 3. 建立使用者
        password_hash = self._password_service.hash_password(password)
        
        user = User(
            email=email,
            password_hash=password_hash,
            username=username,
            department=department
        )
        
        db.session.add(user)
        db.session.commit()
        
        self._log_info(f"New user registered: {email}")
        
        return ServiceResult.ok({
            'message': 'Registration successful',
            'user': UserDTO.from_model(user).to_dict()
        })
    
    def get_user_by_id(self, user_id: int) -> ServiceResult[UserDTO]:
        """取得使用者資料"""
        from models import User
        
        user = User.query.get(user_id)
        if not user:
            return ServiceResult.not_found('User')
        
        return ServiceResult.ok(UserDTO.from_model(user))
    
    def update_profile(self, user_id: int, **kwargs) -> ServiceResult[UserDTO]:
        """更新個人資料"""
        from models import db, User
        
        user = User.query.get(user_id)
        if not user:
            return ServiceResult.not_found('User')
        
        allowed_fields = ['username', 'avatar_url', 'bio', 'phone', 'department', 'position']
        
        for field in allowed_fields:
            if field in kwargs:
                setattr(user, field, kwargs[field])
        
        db.session.commit()
        
        return ServiceResult.ok(UserDTO.from_model(user))
    
    def change_password(self, user_id: int, current_password: str, 
                        new_password: str) -> ServiceResult[bool]:
        """修改密碼"""
        from models import db, User
        
        user = User.query.get(user_id)
        if not user:
            return ServiceResult.not_found('User')
        
        # 驗證目前密碼
        if not self._password_service.verify_password(current_password, user.password_hash):
            return ServiceResult.fail(
                ServiceErrorCode.UNAUTHORIZED,
                'Current password is incorrect'
            )
        
        # 驗證新密碼強度
        password_result = self._password_service.validate_strength(new_password)
        if not password_result.is_ok():
            return password_result
        
        # 更新密碼
        user.password_hash = self._password_service.hash_password(new_password)
        db.session.commit()
        
        self._log_info(f"User {user.email} changed password")
        
        return ServiceResult.ok(True)
    
    def request_password_reset(self, email: str) -> ServiceResult[str]:
        """請求密碼重設"""
        from models import db, User, PasswordResetToken
        
        user = User.query.filter_by(email=email).first()
        
        # 即使使用者不存在也回傳成功（防止帳號枚舉）
        if not user:
            self._log_warning(f"Password reset requested for non-existent email: {email}")
            return ServiceResult.ok('If the email exists, a reset link has been sent.')
        
        # 產生 Token
        token = self._password_service.generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(reset_token)
        db.session.commit()
        
        # TODO: 發送 Email（透過 Celery 任務）
        self._log_info(f"Password reset token generated for {email}")
        
        return ServiceResult.ok(token)
    
    def reset_password(self, token: str, new_password: str) -> ServiceResult[bool]:
        """重設密碼"""
        from models import db, User, PasswordResetToken
        
        # 查找 Token
        reset_token = PasswordResetToken.query.filter_by(
            token=token,
            used=False
        ).first()
        
        if not reset_token:
            return ServiceResult.fail(
                ServiceErrorCode.VALIDATION_ERROR,
                'Invalid or expired reset token'
            )
        
        # 檢查是否過期
        if reset_token.expires_at < datetime.utcnow():
            return ServiceResult.fail(
                ServiceErrorCode.VALIDATION_ERROR,
                'Reset token has expired'
            )
        
        # 驗證新密碼強度
        password_result = self._password_service.validate_strength(new_password)
        if not password_result.is_ok():
            return password_result
        
        # 更新密碼
        user = User.query.get(reset_token.user_id)
        if not user:
            return ServiceResult.not_found('User')
        
        user.password_hash = self._password_service.hash_password(new_password)
        reset_token.used = True
        reset_token.used_at = datetime.utcnow()
        
        db.session.commit()
        
        self._log_info(f"Password reset completed for user {user.email}")
        
        return ServiceResult.ok(True)


# ============================================
# 全域服務實例
# ============================================

# 可以在應用程式啟動時建立
_auth_service: Optional[AuthService] = None
_password_service: Optional[PasswordService] = None


def get_auth_service() -> AuthService:
    """取得認證服務實例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_password_service() -> PasswordService:
    """取得密碼服務實例"""
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service

