"""
============================================
utils/response.py - 統一 API 回應格式（物件導向版本）
============================================

【設計原則】
- 單一職責原則 (SRP): 每個類別只負責一件事
- 開放封閉原則 (OCP): 對擴展開放，對修改封閉
- 里氏替換原則 (LSP): 子類別可以替換父類別
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from flask import jsonify
from typing import Any, Dict, Optional, List, Union
from http import HTTPStatus


# ============================================
# 錯誤代碼枚舉
# ============================================

class ErrorCode(Enum):
    """
    統一的錯誤代碼枚舉
    
    使用 Enum 而非類別常數，提供類型安全和更好的文件化
    """
    
    # 認證相關 (1xxx)
    AUTH_REQUIRED = "AUTH_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    
    # 驗證相關 (2xxx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # 資源相關 (3xxx)
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    
    # 權限相關 (4xxx)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PRIVILEGES = "INSUFFICIENT_PRIVILEGES"
    
    # 伺服器相關 (5xxx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # 限流相關 (6xxx)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# ============================================
# 資料類別（Data Classes）
# ============================================

@dataclass
class PaginationInfo:
    """
    分頁資訊的資料類別
    
    使用 dataclass 自動產生 __init__, __repr__, __eq__ 等方法
    """
    total: int
    page: int
    per_page: int
    
    @property
    def total_pages(self) -> int:
        """計算總頁數"""
        return (self.total + self.per_page - 1) // self.per_page if self.per_page > 0 else 0
    
    @property
    def has_next(self) -> bool:
        """是否有下一頁"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """是否有上一頁"""
        return self.page > 1
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'total': self.total,
            'page': self.page,
            'per_page': self.per_page,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev
        }


@dataclass
class ErrorInfo:
    """
    錯誤資訊的資料類別
    """
    code: Union[ErrorCode, str]
    message: str
    details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        result = {
            'code': self.code.value if isinstance(self.code, ErrorCode) else self.code,
            'message': self.message
        }
        if self.details:
            result['details'] = self.details
        return result


# ============================================
# 回應基底類別
# ============================================

class BaseResponse(ABC):
    """
    API 回應的抽象基底類別
    
    遵循里氏替換原則：所有子類別可以替換父類別使用
    """
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """轉換為字典"""
        pass
    
    @abstractmethod
    def to_flask_response(self):
        """轉換為 Flask 回應"""
        pass
    
    @property
    @abstractmethod
    def status_code(self) -> int:
        """HTTP 狀態碼"""
        pass


# ============================================
# 成功回應類別
# ============================================

@dataclass
class SuccessResponse(BaseResponse):
    """
    成功回應類別
    """
    data: Optional[Any] = None
    message: Optional[str] = None
    meta: Optional[Dict] = None
    _status_code: int = field(default=HTTPStatus.OK, repr=False)
    
    @property
    def status_code(self) -> int:
        return self._status_code
    
    def to_dict(self) -> Dict:
        response = {'success': True}
        
        if self.data is not None:
            response['data'] = self.data
        
        if self.message:
            response['message'] = self.message
        
        if self.meta:
            response['meta'] = self.meta
        
        return response
    
    def to_flask_response(self):
        return jsonify(self.to_dict()), self._status_code
    
    def with_pagination(self, pagination: PaginationInfo) -> 'SuccessResponse':
        """加入分頁資訊"""
        self.meta = self.meta or {}
        self.meta['pagination'] = pagination.to_dict()
        return self


@dataclass
class ErrorResponse(BaseResponse):
    """
    錯誤回應類別
    """
    error: ErrorInfo
    _status_code: int = field(default=HTTPStatus.BAD_REQUEST, repr=False)
    
    @property
    def status_code(self) -> int:
        return self._status_code
    
    def to_dict(self) -> Dict:
        return {
            'success': False,
            'error': self.error.to_dict()
        }
    
    def to_flask_response(self):
        return jsonify(self.to_dict()), self._status_code


# ============================================
# 回應建構器（Builder Pattern）
# ============================================

class ResponseBuilder:
    """
    回應建構器
    
    使用建構器模式來建立回應，提供流暢的 API
    """
    
    def __init__(self):
        self._data: Optional[Any] = None
        self._message: Optional[str] = None
        self._meta: Optional[Dict] = None
        self._status_code: int = HTTPStatus.OK
        self._error: Optional[ErrorInfo] = None
    
    def with_data(self, data: Any) -> 'ResponseBuilder':
        """設定回應資料"""
        self._data = data
        return self
    
    def with_message(self, message: str) -> 'ResponseBuilder':
        """設定訊息"""
        self._message = message
        return self
    
    def with_meta(self, meta: Dict) -> 'ResponseBuilder':
        """設定額外資訊"""
        self._meta = meta
        return self
    
    def with_status(self, status_code: int) -> 'ResponseBuilder':
        """設定 HTTP 狀態碼"""
        self._status_code = status_code
        return self
    
    def with_pagination(self, total: int, page: int, per_page: int) -> 'ResponseBuilder':
        """設定分頁資訊"""
        pagination = PaginationInfo(total=total, page=page, per_page=per_page)
        self._meta = self._meta or {}
        self._meta['pagination'] = pagination.to_dict()
        return self
    
    def with_error(self, code: Union[ErrorCode, str], message: str, details: Optional[Dict] = None) -> 'ResponseBuilder':
        """設定錯誤"""
        self._error = ErrorInfo(code=code, message=message, details=details)
        return self
    
    def build(self) -> BaseResponse:
        """建立回應物件"""
        if self._error:
            return ErrorResponse(error=self._error, _status_code=self._status_code)
        return SuccessResponse(
            data=self._data,
            message=self._message,
            meta=self._meta,
            _status_code=self._status_code
        )
    
    def build_flask_response(self):
        """建立 Flask 回應"""
        return self.build().to_flask_response()


# ============================================
# API 回應工廠（Factory Pattern）
# ============================================

class ApiResponse:
    """
    API 回應工廠類別
    
    使用工廠模式建立各種回應
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = None,
        meta: Dict = None,
        status: int = HTTPStatus.OK
    ):
        """建立成功回應"""
        response = SuccessResponse(
            data=data,
            message=message,
            meta=meta,
            _status_code=status
        )
        return response.to_flask_response()
    
    @staticmethod
    def error(
        message: str,
        code: Union[ErrorCode, str] = ErrorCode.INTERNAL_ERROR,
        details: Dict = None,
        status: int = HTTPStatus.BAD_REQUEST
    ):
        """建立錯誤回應"""
        error_info = ErrorInfo(code=code, message=message, details=details)
        response = ErrorResponse(error=error_info, _status_code=status)
        return response.to_flask_response()
    
    @staticmethod
    def paginated(
        items: List,
        total: int,
        page: int,
        per_page: int,
        item_key: str = 'items'
    ):
        """建立分頁回應"""
        pagination = PaginationInfo(total=total, page=page, per_page=per_page)
        response = SuccessResponse(
            data={item_key: items},
            meta={'pagination': pagination.to_dict()}
        )
        return response.to_flask_response()
    
    @classmethod
    def builder(cls) -> ResponseBuilder:
        """取得回應建構器"""
        return ResponseBuilder()


# ============================================
# 預設錯誤回應（Preset Responses）
# ============================================

class PresetErrors:
    """
    常用錯誤回應的預設類別
    
    提供常用錯誤的便捷方法
    """
    
    @staticmethod
    def not_found(resource: str = 'Resource'):
        """404 Not Found"""
        return ApiResponse.error(
            f'{resource} not found',
            code=ErrorCode.NOT_FOUND,
            status=HTTPStatus.NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(message: str = 'Authentication required'):
        """401 Unauthorized"""
        return ApiResponse.error(
            message,
            code=ErrorCode.AUTH_REQUIRED,
            status=HTTPStatus.UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message: str = 'Permission denied'):
        """403 Forbidden"""
        return ApiResponse.error(
            message,
            code=ErrorCode.PERMISSION_DENIED,
            status=HTTPStatus.FORBIDDEN
        )
    
    @staticmethod
    def validation_error(message: str = 'Validation failed', details: Dict = None):
        """400 Validation Error"""
        return ApiResponse.error(
            message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            status=HTTPStatus.BAD_REQUEST
        )
    
    @staticmethod
    def conflict(message: str = 'Resource already exists'):
        """409 Conflict"""
        return ApiResponse.error(
            message,
            code=ErrorCode.ALREADY_EXISTS,
            status=HTTPStatus.CONFLICT
        )
    
    @staticmethod
    def rate_limited(message: str = 'Too many requests', retry_after: int = 60):
        """429 Rate Limited"""
        return ApiResponse.error(
            message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details={'retry_after': retry_after},
            status=HTTPStatus.TOO_MANY_REQUESTS
        )
    
    @staticmethod
    def internal_error(message: str = 'An internal error occurred'):
        """500 Internal Server Error"""
        return ApiResponse.error(
            message,
            code=ErrorCode.INTERNAL_ERROR,
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )


# ============================================
# 向後相容的便捷函數
# ============================================

def success_response(data=None, message=None, meta=None, status=200):
    """成功回應的便捷函數"""
    return ApiResponse.success(data, message, meta, status)


def error_response(message, code=ErrorCode.INTERNAL_ERROR, details=None, status=400):
    """錯誤回應的便捷函數"""
    return ApiResponse.error(message, code, details, status)


def paginated_response(items, total, page, per_page, item_key='items'):
    """分頁回應的便捷函數"""
    return ApiResponse.paginated(items, total, page, per_page, item_key)


# 向後相容的別名
not_found = PresetErrors.not_found
unauthorized = PresetErrors.unauthorized
forbidden = PresetErrors.forbidden
validation_error = PresetErrors.validation_error
conflict = PresetErrors.conflict
rate_limited = PresetErrors.rate_limited
internal_error = PresetErrors.internal_error
