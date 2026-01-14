"""
============================================
models.py - 資料模型（向後相容入口）
============================================

這個檔案保留作為向後相容的入口點。
實際的模型定義在 models_legacy.py 中。

【使用方式】
from models import db, User, Project, Task
"""

# 從 models_legacy 重新導出所有內容
from models_legacy import *
from models_legacy import db # 👈 不管怎樣，db 一定要進來！

# 確保可以直接 import
__all__ = [
    'db',
    'User',
    'Project',
    'ProjectMember',
    'Task',
    'TaskComment',
    'Notification',
    'ActivityLog',
    'Tag',
    'task_tags',
    'Attachment',
    'TaskTemplate',
    'TaskDependency',
    'AuditLog',
    'UserPreference',
    'LoginAttempt',
    'PasswordResetToken',
    'ProjectStatSnapshot',
]
