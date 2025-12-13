"""
============================================
models - 資料模型層
============================================

【這個模組的作用】
定義所有資料庫模型（ORM）

【使用方式】
from models import db, User, Project, Task
"""

import sys
import os

# 確保可以從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 從 models_legacy 重新導出所有模型
from models_legacy import (
    db,
    User,
    Project,
    ProjectMember,
    Task,
    TaskComment,
    Notification,
    ActivityLog,
    Tag,
    task_tags,  # 這是一個 Table，不是 Class
    Attachment,
    TaskTemplate,
    TaskDependency,
    AuditLog,
    UserPreference,
    LoginAttempt,
    PasswordResetToken,
    ProjectStatSnapshot,
)

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
