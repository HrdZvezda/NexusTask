from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta
import logging
import secrets

# 從父目錄導入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, User, LoginAttempt, PasswordResetToken

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# ============================================
# 安全性輔助函數
# ============================================

def validate_password_strength(password: str) -> tuple:
    """
    根據 config 驗證密碼強度
    
    Returns:
        tuple: (is_valid, error_message)
    """
    min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
    require_upper = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', False)
    require_numbers = current_app.config.get('PASSWORD_REQUIRE_NUMBERS', False)
    require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', False)
    
    if len(password) < min_length:
        return False, f'Password must be at least {min_length} characters'
    
    if require_upper and not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter'
    
    if require_numbers and not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number'
    
    if require_special and not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return False, 'Password must contain at least one special character'
    
    return True, ''

def check_account_locked(email: str) -> tuple:
    """
    檢查帳號是否因登入失敗過多而被鎖定
    
    Returns:
        tuple: (is_locked, remaining_minutes)
    """
    lockout_threshold = 5  # 5 次失敗後鎖定
    lockout_duration = 15  # 鎖定 15 分鐘
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=lockout_duration)
    
    failed_attempts = LoginAttempt.query.filter(
        LoginAttempt.email == email,
        LoginAttempt.success.is_(False),
        LoginAttempt.timestamp > cutoff_time
    ).count()
    
    if failed_attempts >= lockout_threshold:
        # 找出最後一次失敗的時間，計算剩餘鎖定時間
        last_attempt = LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success.is_(False)
        ).order_by(LoginAttempt.timestamp.desc()).first()
        
        if last_attempt:
            unlock_time = last_attempt.timestamp + timedelta(minutes=lockout_duration)
            remaining = (unlock_time - datetime.utcnow()).total_seconds() / 60
            return True, max(0, int(remaining))
    
    return False, 0

def record_login_attempt(email: str, success: bool, failure_reason: str = None):
    """記錄登入嘗試"""
    try:
        attempt = LoginAttempt(
            email=email,
            ip_address=request.remote_addr,
            success=success,
            failure_reason=failure_reason
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to record login attempt: {str(e)}")
        db.session.rollback()



# ============================================
# Input Validation Schemas (用 marshmallow)
# ============================================

class RegisterSchema(Schema):
    """註冊輸入驗證"""
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    password = fields.Str(
        required=True,
        validate=validate.Length(min=4, max=128, error='Password must be 4-128 characters'),
        error_messages={'required': 'Password is required'}
    )
    username = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=50, error='Username must be 2-50 characters'),
        error_messages={'required': 'Username is required'}
    )
    department = fields.Str(validate=validate.Length(max=100))

class LoginSchema(Schema):
    """登入輸入驗證"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

# ============================================
# Helper Functions
# ============================================

def get_bcrypt():
    """從 Flask app extensions 取得 bcrypt 實例 (不用 global variable)"""
    try:
        bcrypt = current_app.extensions.get('bcrypt')
        if bcrypt is None:
            # 如果還是找不到,嘗試直接從 app 取得
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt(current_app)
            current_app.extensions['bcrypt'] = bcrypt
        return bcrypt
    except Exception as e:
        logger.error(f"Failed to get bcrypt: {str(e)}")
        return None

def validate_request_data(schema_class, data):
    """
    統一的輸入驗證函數
    
    Returns:
        tuple: (is_valid, data_or_errors)
    """
    schema = schema_class()
    try:
        validated_data = schema.load(data)
        return True, validated_data
    except ValidationError as err:
        return False, err.messages

# ============================================
# 註冊 API
# ============================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    使用者註冊
    
    安全措施:
    1. Input validation (marshmallow)
    2. 密碼強度驗證（根據 config 設定）
    3. Email 唯一性檢查
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(RegisterSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 驗證密碼強度
    is_strong, error_msg = validate_password_strength(result['password'])
    if not is_strong:
        return jsonify({'error': error_msg}), 400
    
    # 檢查 email 是否已存在
    if User.query.filter_by(email=result['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # 加密密碼 (使用 current_app 而非 global variable)
    bcrypt = get_bcrypt()
    if not bcrypt:
        logger.error("Bcrypt extension not loaded correctly.")
        return jsonify({'error': 'Server configuration error (Bcrypt missing)'}), 500

    hashed_password = bcrypt.generate_password_hash(result['password']).decode('utf-8')

    # 判斷是否為第一個使用者（自動成為管理員）
    # 這確保系統至少有一個管理員
    is_first_user = User.query.count() == 0
    
    # 建立使用者
    user = User(
        email=result['email'],
        username=result['username'],
        password_hash=hashed_password,
        department=result.get('department'),
        role='admin' if is_first_user else 'member'  # 第一個用戶自動成為管理員
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # 不要把 exception 細節洩漏給前端
        logger.error(f"Registration error for {result['email']}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Registration failed due to server error'}), 500

# ============================================
# 登入 API
# ============================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    使用者登入
    
    安全措施:
    1. 帳號鎖定（5 次失敗後鎖定 15 分鐘）
    2. 登入嘗試記錄
    3. 不區分 email/password 錯誤（避免帳號枚舉攻擊）
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(LoginSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    email = result['email']
    
    # 檢查帳號是否被鎖定
    is_locked, remaining_minutes = check_account_locked(email)
    if is_locked:
        logger.warning(f"Locked account login attempt: {email}")
        return jsonify({
            'error': f'Account is temporarily locked. Please try again in {remaining_minutes} minutes.',
            'locked': True,
            'remaining_minutes': remaining_minutes
        }), 429
    
    # 查詢使用者
    user = User.query.filter_by(email=email).first()
    
    # 驗證密碼
    bcrypt = get_bcrypt()
    if not user or not bcrypt.check_password_hash(user.password_hash, result['password']):
        # 記錄失敗的登入嘗試
        record_login_attempt(email, success=False, failure_reason='invalid_credentials')
        logger.warning(f"Failed login attempt for email: {email}")
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # 檢查帳號是否被停用
    if not user.is_active:
        record_login_attempt(email, success=False, failure_reason='account_disabled')
        logger.warning(f"Inactive user login attempt: {user.email}")
        return jsonify({'error': 'Account is disabled'}), 403
    
    # 記錄成功的登入
    record_login_attempt(email, success=True)
    
    # 建立 JWT tokens (包含 access token 和 refresh token)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # 更新最後登入時間
    try:
        user.last_login = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        # 這個錯誤不影響登入,只記錄就好
        logger.error(f"Failed to update last_login for {user.email}: {str(e)}")
    
    logger.info(f"User logged in: {user.email}")
    
    # 判斷是否為管理員（使用 User 模型的 is_admin 方法）
    is_admin = user.is_admin()
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'name': user.username,
            'avatar_url': user.avatar_url or f"https://ui-avatars.com/api/?name={user.username}&background=random",
            'department': user.department,
            'role': 'admin' if is_admin else 'member'
        }
    }), 200

# ============================================
# Token 刷新 API (新增)
# ============================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    刷新 access token
    
    這是新增的功能,讓前端可以用 refresh token 換新的 access token
    避免使用者頻繁重新登入
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid or inactive user'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token
    }), 200

# ============================================
# 登出 API (新增,需要 Redis)
# ============================================

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    登出 (將 token 加入黑名單)

    Token 會被加入黑名單，確保登出後無法再使用該 token
    """
    from core import revoke_token

    jwt_data = get_jwt()
    jti = jwt_data['jti']  # JWT ID

    # 計算 token 剩餘有效時間
    exp_timestamp = jwt_data.get('exp')
    if exp_timestamp:
        expires_delta = timedelta(seconds=max(0, exp_timestamp - datetime.utcnow().timestamp()))
    else:
        expires_delta = timedelta(hours=24)  # 預設 24 小時

    # 將 token 加入黑名單
    revoke_token(jti, expires_delta)

    user_id = get_jwt_identity()
    logger.info(f"User logged out: {user_id}, token revoked: {jti[:8]}...")

    return jsonify({'message': 'Logout successful'}), 200

# ============================================
# 取得當前使用者資訊
# ============================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """
    取得當前登入使用者的資訊
    
    改進點:
    1. 返回更多有用的資訊
    2. 更好的錯誤處理
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        logger.warning(f"Token valid but user not found: {user_id}")
        return jsonify({'error': 'User not found'}), 404
    
    # 判斷是否為管理員（使用 User 模型的 is_admin 方法）
    is_admin = user.is_admin()
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'name': user.username,  # 前端使用 name
        'avatar_url': user.avatar_url or f"https://ui-avatars.com/api/?name={user.username}&background=random",
        'bio': user.bio,
        'department': user.department,
        'position': user.position,
        'role': 'admin' if is_admin else 'member',
        'is_active': user.is_active,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'created_at': user.created_at.isoformat()
    }), 200

# ============================================
# 更新個人資料 (新增)
# ============================================

class UpdateProfileSchema(Schema):
    """個人資料更新驗證"""
    username = fields.Str(validate=validate.Length(min=2, max=50))
    bio = fields.Str(validate=validate.Length(max=500))
    phone = fields.Str(validate=validate.Length(max=20))
    department = fields.Str(validate=validate.Length(max=100))
    position = fields.Str(validate=validate.Length(max=100))

@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_me():
    """更新當前使用者資料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(UpdateProfileSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 更新欄位
    for field in ['username', 'bio', 'phone', 'department', 'position']:
        if field in result:
            setattr(user, field, result[field])
    
    try:
        db.session.commit()
        logger.info(f"User profile updated: {user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'bio': user.bio,
                'phone': user.phone,
                'department': user.department,
                'position': user.position
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error for {user.email}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Update failed due to server error'}), 500

# ============================================
# 修改密碼 (新增)
# ============================================

class ChangePasswordSchema(Schema):
    """密碼修改驗證"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=4, max=128)
    )

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    修改密碼
    
    安全措施:
    1. 需要驗證舊密碼
    2. 新密碼強度驗證
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(ChangePasswordSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 驗證舊密碼
    bcrypt = get_bcrypt()
    if not bcrypt.check_password_hash(user.password_hash, result['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # 驗證新密碼強度
    is_strong, error_msg = validate_password_strength(result['new_password'])
    if not is_strong:
        return jsonify({'error': error_msg}), 400
    
    # 更新密碼
    user.password_hash = bcrypt.generate_password_hash(result['new_password']).decode('utf-8')
    
    try:
        db.session.commit()
        logger.info(f"Password changed for user: {user.email}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password change error for {user.email}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Password change failed due to server error'}), 500

# ============================================
# 忘記密碼功能
# ============================================

class ForgotPasswordSchema(Schema):
    """忘記密碼輸入驗證"""
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    """重設密碼輸入驗證"""
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=4, max=128))

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    請求重設密碼
    
    安全措施:
    1. 不管 email 存不存在，都回傳相同訊息（防止帳號枚舉）
    2. Token 有過期時間（1 小時）
    3. 舊的 token 會被標記為已使用
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    is_valid, result = validate_request_data(ForgotPasswordSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    email = result['email']
    user = User.query.filter_by(email=email).first()
    
    # 不管有沒有找到用戶，都回傳相同訊息（防止帳號枚舉攻擊）
    if user:
        # 使舊的 tokens 失效
        PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).update({'used': True})
        
        # 產生新的 token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        try:
            db.session.add(reset_token)
            db.session.commit()
            
            # TODO: 發送 email（需要設定 SMTP）
            # send_password_reset_email(user.email, token)
            
            # 開發環境下，印出 token 方便測試
            if current_app.debug:
                logger.info(f"Password reset token for {email}: {token}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create reset token: {str(e)}")
    
    return jsonify({
        'message': 'If the email exists, a password reset link has been sent'
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    使用 token 重設密碼
    
    安全措施:
    1. Token 過期檢查
    2. Token 只能使用一次
    3. 密碼強度驗證
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    is_valid, result = validate_request_data(ResetPasswordSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    token = result['token']
    new_password = result['new_password']
    
    # 查找有效的 token
    reset_token = PasswordResetToken.query.filter_by(
        token=token, 
        used=False
    ).first()
    
    if not reset_token:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    if reset_token.expires_at < datetime.utcnow():
        return jsonify({'error': 'Reset token has expired'}), 400
    
    # 驗證新密碼強度
    is_strong, error_msg = validate_password_strength(new_password)
    if not is_strong:
        return jsonify({'error': error_msg}), 400
    
    # 更新密碼
    user = User.query.get(reset_token.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    bcrypt = get_bcrypt()
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    # 標記 token 為已使用
    reset_token.used = True
    reset_token.used_at = datetime.utcnow()
    
    try:
        db.session.commit()
        logger.info(f"Password reset successful for user: {user.email}")
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Password reset failed due to server error'}), 500

@auth_bp.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """
    驗證重設密碼的 token 是否有效
    前端可以用這個 API 檢查 token，在顯示重設密碼表單前先驗證
    """
    data = request.get_json()
    token = data.get('token') if data else None
    
    if not token:
        return jsonify({'valid': False, 'error': 'Token is required'}), 400
    
    reset_token = PasswordResetToken.query.filter_by(
        token=token, 
        used=False
    ).first()
    
    if not reset_token:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 200
    
    if reset_token.expires_at < datetime.utcnow():
        return jsonify({'valid': False, 'error': 'Token has expired'}), 200
    
    return jsonify({'valid': True}), 200

# ============================================
# 輔助函數 (供其他模組使用)
# ============================================

def get_current_user():
    """
    取得當前登入的使用者
    
    改進點:加上錯誤處理
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None