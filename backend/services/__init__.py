"""
============================================
services - 服務層
============================================

【服務層的作用】
將業務邏輯從 API 端點（routes）中分離出來

【設計原則】
- 單一職責原則 (SRP): 每個服務只處理一個領域
- 依賴反轉原則 (DIP): 依賴抽象介面
- 開放封閉原則 (OCP): 對擴展開放，對修改封閉
"""

from .base import BaseService, ServiceResult, ServiceError
from .auth_service import AuthService, PasswordService
from .project_service import ProjectService
from .task_service import TaskService
from .notification_service import NotificationService

__all__ = [
    'BaseService',
    'ServiceResult',
    'ServiceError',
    'AuthService',
    'PasswordService',
    'ProjectService',
    'TaskService',
    'NotificationService',
]

