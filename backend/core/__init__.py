"""
============================================
core - 核心模組
============================================

【這個模組的作用】
集中管理核心基礎設施：
- 快取
- 中介軟體
- WebSocket
- 背景任務
- API 文件

【使用方式】
from core import init_cache, init_middleware, init_socketio
"""

# 從各個核心模組導入
from .cache import (
    cache,
    init_cache,
    CacheTimeout,
    CacheKeyManager,
    CacheService,
    invalidate_user_cache,
    invalidate_project_stats,
    invalidate_notification_count,
    invalidate_project_members,
)

from .middleware import init_middleware

from .socket_events import (
    socketio,
    init_socketio,
    emit_to_user,
    emit_to_project,
    emit_notification,
    emit_task_created,
    emit_task_updated,
    emit_task_deleted,
)

from .api_docs import init_swagger

from .celery_tasks import celery

from .token_blacklist import (
    TokenBlacklist,
    check_if_token_revoked,
    revoke_token,
)

__all__ = [
    # Cache
    'cache',
    'init_cache',
    'CacheTimeout',
    'CacheKeyManager',
    'CacheService',
    'invalidate_user_cache',
    'invalidate_project_stats',
    'invalidate_notification_count',
    'invalidate_project_members',
    
    # Middleware
    'init_middleware',
    
    # Socket
    'socketio',
    'init_socketio',
    'emit_to_user',
    'emit_to_project',
    'emit_notification',
    'emit_task_created',
    'emit_task_updated',
    'emit_task_deleted',
    
    # API Docs
    'init_swagger',
    
    # Celery
    'celery',

    # Token Blacklist
    'TokenBlacklist',
    'check_if_token_revoked',
    'revoke_token',
]
