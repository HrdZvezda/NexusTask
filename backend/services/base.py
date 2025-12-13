"""
============================================
services/base.py - 服務層基底類別
============================================

【設計原則】
- 提供統一的服務結果格式
- 定義服務的抽象介面
- 封裝通用功能
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
import logging

T = TypeVar('T')


# ============================================
# 服務結果類別
# ============================================

class ServiceErrorCode(Enum):
    """服務錯誤代碼"""
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    NOT_FOUND = 'NOT_FOUND'
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    CONFLICT = 'CONFLICT'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


@dataclass
class ServiceError:
    """
    服務錯誤資訊
    """
    code: ServiceErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = {
            'code': self.code.value,
            'message': self.message
        }
        if self.details:
            result['details'] = self.details
        return result


@dataclass
class ServiceResult(Generic[T]):
    """
    服務操作結果
    
    使用方式：
    # 成功
    return ServiceResult.success(data={'user': user})
    
    # 失敗
    return ServiceResult.failure(
        ServiceErrorCode.NOT_FOUND, 
        'User not found'
    )
    """
    success: bool
    data: Optional[T] = None
    error: Optional[ServiceError] = None
    
    @classmethod
    def ok(cls, data: T = None) -> 'ServiceResult[T]':
        """建立成功結果"""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, code: ServiceErrorCode, message: str, 
             details: Dict = None) -> 'ServiceResult[T]':
        """建立失敗結果"""
        return cls(
            success=False,
            error=ServiceError(code=code, message=message, details=details)
        )
    
    @classmethod
    def not_found(cls, resource: str = 'Resource') -> 'ServiceResult[T]':
        """資源不存在"""
        return cls.fail(ServiceErrorCode.NOT_FOUND, f'{resource} not found')
    
    @classmethod
    def unauthorized(cls, message: str = 'Unauthorized') -> 'ServiceResult[T]':
        """未授權"""
        return cls.fail(ServiceErrorCode.UNAUTHORIZED, message)
    
    @classmethod
    def forbidden(cls, message: str = 'Permission denied') -> 'ServiceResult[T]':
        """禁止存取"""
        return cls.fail(ServiceErrorCode.FORBIDDEN, message)
    
    @classmethod
    def validation_error(cls, message: str, details: Dict = None) -> 'ServiceResult[T]':
        """驗證錯誤"""
        return cls.fail(ServiceErrorCode.VALIDATION_ERROR, message, details)
    
    @classmethod
    def conflict(cls, message: str) -> 'ServiceResult[T]':
        """衝突"""
        return cls.fail(ServiceErrorCode.CONFLICT, message)
    
    def is_ok(self) -> bool:
        """是否成功"""
        return self.success
    
    def is_error(self) -> bool:
        """是否失敗"""
        return not self.success


# ============================================
# 基底服務類別
# ============================================

class BaseService(ABC):
    """
    服務基底類別
    
    所有服務都應該繼承這個類別
    """
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def logger(self) -> logging.Logger:
        """取得 Logger"""
        return self._logger
    
    def _log_info(self, message: str, **kwargs):
        """記錄資訊"""
        self._logger.info(message, extra=kwargs)
    
    def _log_error(self, message: str, exc_info: bool = False, **kwargs):
        """記錄錯誤"""
        self._logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def _log_warning(self, message: str, **kwargs):
        """記錄警告"""
        self._logger.warning(message, extra=kwargs)


# ============================================
# Repository 基底類別（資料存取層）
# ============================================

class BaseRepository(Generic[T], ABC):
    """
    Repository 基底類別
    
    封裝資料庫操作
    """
    
    def __init__(self, model_class: type):
        self._model_class = model_class
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def get_by_id(self, id: int) -> Optional[T]:
        """根據 ID 取得"""
        return self._model_class.query.get(id)
    
    def get_all(self) -> List[T]:
        """取得所有"""
        return self._model_class.query.all()
    
    def create(self, **kwargs) -> T:
        """建立新記錄"""
        from models import db
        instance = self._model_class(**kwargs)
        db.session.add(instance)
        return instance
    
    def update(self, instance: T, **kwargs) -> T:
        """更新記錄"""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance
    
    def delete(self, instance: T) -> None:
        """刪除記錄"""
        from models import db
        db.session.delete(instance)
    
    def save(self) -> None:
        """儲存變更"""
        from models import db
        db.session.commit()
    
    def rollback(self) -> None:
        """回滾變更"""
        from models import db
        db.session.rollback()


# ============================================
# 驗證器基底類別
# ============================================

class BaseValidator(ABC):
    """
    驗證器基底類別
    """
    
    @abstractmethod
    def validate(self, data: Dict) -> ServiceResult:
        """驗證資料"""
        pass


class SchemaValidator(BaseValidator):
    """
    使用 Marshmallow Schema 的驗證器
    """
    
    def __init__(self, schema_class):
        self._schema = schema_class()
    
    def validate(self, data: Dict) -> ServiceResult:
        from marshmallow import ValidationError
        try:
            validated = self._schema.load(data)
            return ServiceResult.ok(validated)
        except ValidationError as e:
            return ServiceResult.validation_error(
                'Validation failed',
                details=e.messages
            )


# ============================================
# 權限檢查 Mixin
# ============================================

class PermissionMixin:
    """
    權限檢查 Mixin
    
    提供通用的權限檢查方法
    """
    
    def check_owner(self, resource, user_id: int) -> bool:
        """檢查是否為資源擁有者"""
        owner_id = getattr(resource, 'owner_id', None)
        return owner_id == user_id
    
    def check_member(self, project_id: int, user_id: int) -> bool:
        """檢查是否為專案成員"""
        from models import ProjectMember
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        return member is not None
    
    def check_admin(self, project_id: int, user_id: int) -> bool:
        """檢查是否為專案管理員"""
        from models import Project, ProjectMember
        
        project = Project.query.get(project_id)
        if not project:
            return False
        
        if project.owner_id == user_id:
            return True
        
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            role='admin'
        ).first()
        
        return member is not None


# ============================================
# 單元工作模式 (Unit of Work)
# ============================================

class UnitOfWork:
    """
    單元工作模式
    
    管理交易（Transaction）的邊界
    
    使用方式：
    with UnitOfWork() as uow:
        user = uow.users.create(email='test@test.com')
        uow.commit()
    """
    
    def __init__(self):
        from models import db
        self._db = db
        self._committed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        elif not self._committed:
            self.rollback()
    
    def commit(self):
        """提交交易"""
        self._db.session.commit()
        self._committed = True
    
    def rollback(self):
        """回滾交易"""
        self._db.session.rollback()

