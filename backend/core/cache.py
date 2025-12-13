"""
============================================
cache.py - 快取層（物件導向版本）
============================================

【設計原則】
- 單一職責原則 (SRP): 每個類別只負責一件事
- 開放封閉原則 (OCP): 對擴展開放，對修改封閉
- 依賴反轉原則 (DIP): 依賴抽象而非具體實現
"""

import sys
import os

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from enum import IntEnum
from flask_caching import Cache
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Generic
import hashlib

T = TypeVar('T')


# ============================================
# 枚舉定義
# ============================================

class CacheTimeout(IntEnum):
    """
    快取時間枚舉
    
    使用 IntEnum 可以直接作為整數使用，同時保有類型安全
    """
    SHORT = 60        # 1 分鐘
    MEDIUM = 300      # 5 分鐘
    LONG = 600        # 10 分鐘
    HOUR = 3600       # 1 小時
    DAY = 86400       # 1 天


# ============================================
# 抽象基底類別
# ============================================

class BaseCacheKeyGenerator(ABC):
    """
    快取 Key 產生器的抽象基底類別
    
    遵循開放封閉原則：可以建立不同的 key 產生策略
    """
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """產生快取 key"""
        pass


class ICacheService(ABC):
    """
    快取服務的介面
    
    遵循依賴反轉原則：上層模組依賴這個抽象介面
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = CacheTimeout.MEDIUM) -> None:
        """設定快取值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """刪除快取"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有快取"""
        pass
    
    @abstractmethod
    def get_or_set(self, key: str, callback: Callable[[], T], timeout: int = CacheTimeout.MEDIUM) -> T:
        """取得快取，不存在則執行 callback 並設定"""
        pass


# ============================================
# Key 產生器實作
# ============================================

class HashKeyGenerator(BaseCacheKeyGenerator):
    """使用 MD5 hash 產生 key"""
    
    def generate(self, *args, **kwargs) -> str:
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class PrefixKeyGenerator(BaseCacheKeyGenerator):
    """使用前綴和 ID 產生 key"""
    
    def __init__(self, prefix: str):
        self._prefix = prefix
    
    def generate(self, *args, **kwargs) -> str:
        if args:
            return f"{self._prefix}:{args[0]}"
        return self._prefix


# ============================================
# 快取 Key 管理器
# ============================================

class CacheKeyManager:
    """
    集中管理所有快取 key 的類別
    
    遵循單一職責原則：只負責 key 的產生和管理
    """
    
    # Key 產生器
    _user_key = PrefixKeyGenerator("user")
    _project_stats_key = PrefixKeyGenerator("project_stats")
    _notification_count_key = PrefixKeyGenerator("notification_count")
    _project_members_key = PrefixKeyGenerator("project_members")
    _hash_key = HashKeyGenerator()
    
    @classmethod
    def user(cls, user_id: int) -> str:
        """使用者資料的快取 key"""
        return cls._user_key.generate(user_id)
    
    @classmethod
    def project_stats(cls, project_id: int) -> str:
        """專案統計的快取 key"""
        return cls._project_stats_key.generate(project_id)
    
    @classmethod
    def notification_count(cls, user_id: int) -> str:
        """通知數量的快取 key"""
        return cls._notification_count_key.generate(user_id)
    
    @classmethod
    def project_members(cls, project_id: int) -> str:
        """專案成員的快取 key"""
        return cls._project_members_key.generate(project_id)
    
    @classmethod
    def custom(cls, *args, **kwargs) -> str:
        """自訂 key（使用 hash）"""
        return cls._hash_key.generate(*args, **kwargs)


# ============================================
# 快取服務實作
# ============================================

class FlaskCacheService(ICacheService):
    """
    Flask-Caching 的實作
    
    實現 ICacheService 介面
    """
    
    def __init__(self, cache: Cache):
        self._cache = cache
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, timeout: int = CacheTimeout.MEDIUM) -> None:
        self._cache.set(key, value, timeout=timeout)
    
    def delete(self, key: str) -> None:
        self._cache.delete(key)
    
    def clear(self) -> None:
        self._cache.clear()
    
    def get_or_set(self, key: str, callback: Callable[[], T], timeout: int = CacheTimeout.MEDIUM) -> T:
        cached = self.get(key)
        if cached is not None:
            return cached
        
        result = callback()
        if result is not None:
            self.set(key, result, timeout)
        return result


# ============================================
# 快取裝飾器類別
# ============================================

class CacheDecorator:
    """
    快取裝飾器工廠類別
    
    提供各種快取裝飾器
    """
    
    def __init__(self, cache_service: ICacheService):
        self._cache_service = cache_service
    
    def cached(self, key_func: Callable[..., str], timeout: int = CacheTimeout.MEDIUM):
        """
        通用快取裝飾器
        
        參數:
            key_func: 產生快取 key 的函數
            timeout: 快取時間
        
        使用方式:
            @cache_decorator.cached(lambda user_id: f"user:{user_id}")
            def get_user(user_id):
                return User.query.get(user_id)
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                cache_key = key_func(*args, **kwargs)
                cached = self._cache_service.get(cache_key)
                if cached is not None:
                    return cached
                
                result = f(*args, **kwargs)
                if result is not None:
                    self._cache_service.set(cache_key, result, timeout)
                return result
            return wrapper
        return decorator
    
    def cached_user(self, timeout: int = CacheTimeout.MEDIUM):
        """使用者資料快取裝飾器"""
        return self.cached(
            lambda user_id, *args, **kwargs: CacheKeyManager.user(user_id),
            timeout
        )
    
    def cached_project_stats(self, timeout: int = CacheTimeout.LONG):
        """專案統計快取裝飾器"""
        return self.cached(
            lambda project_id, *args, **kwargs: CacheKeyManager.project_stats(project_id),
            timeout
        )


# ============================================
# 快取失效器
# ============================================

class CacheInvalidator:
    """
    集中管理快取失效的類別
    
    遵循單一職責原則：只負責快取失效
    """
    
    def __init__(self, cache_service: ICacheService):
        self._cache_service = cache_service
    
    def invalidate_user(self, user_id: int) -> None:
        """使使用者快取失效"""
        self._cache_service.delete(CacheKeyManager.user(user_id))
    
    def invalidate_project_stats(self, project_id: int) -> None:
        """使專案統計快取失效"""
        self._cache_service.delete(CacheKeyManager.project_stats(project_id))
    
    def invalidate_notification_count(self, user_id: int) -> None:
        """使通知數量快取失效"""
        self._cache_service.delete(CacheKeyManager.notification_count(user_id))
    
    def invalidate_project_members(self, project_id: int) -> None:
        """使專案成員快取失效"""
        self._cache_service.delete(CacheKeyManager.project_members(project_id))
    
    def invalidate_all_project_caches(self, project_id: int) -> None:
        """使專案相關的所有快取失效"""
        self.invalidate_project_stats(project_id)
        self.invalidate_project_members(project_id)


# ============================================
# 專門的快取服務
# ============================================

class UserCacheService:
    """
    使用者相關的快取服務
    
    遵循單一職責原則：只處理使用者相關的快取
    """
    
    def __init__(self, cache_service: ICacheService):
        self._cache_service = cache_service
    
    def get_notification_count(self, user_id: int) -> int:
        """取得使用者的未讀通知數量（帶快取）"""
        cache_key = CacheKeyManager.notification_count(user_id)
        
        def fetch_count():
            from models import Notification
            return Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
        
        return self._cache_service.get_or_set(cache_key, fetch_count, CacheTimeout.SHORT)


class ProjectCacheService:
    """
    專案相關的快取服務
    
    遵循單一職責原則：只處理專案相關的快取
    """
    
    def __init__(self, cache_service: ICacheService):
        self._cache_service = cache_service
    
    def get_members(self, project_id: int) -> Optional[list]:
        """取得專案成員列表（帶快取）"""
        cache_key = CacheKeyManager.project_members(project_id)
        
        def fetch_members():
            from models import ProjectMember, Project
            from sqlalchemy.orm import joinedload
            
            project = Project.query.options(joinedload(Project.owner)).get(project_id)
            if not project:
                return None
            
            members = ProjectMember.query.filter_by(project_id=project_id).options(
                joinedload(ProjectMember.user)
            ).all()
            
            result = [{
                'id': project.owner.id,
                'username': project.owner.username,
                'email': project.owner.email,
                'role': 'admin',
                'is_owner': True
            }]
            
            for m in members:
                if m.user.id != project.owner_id:
                    result.append({
                        'id': m.user.id,
                        'username': m.user.username,
                        'email': m.user.email,
                        'role': m.role,
                        'is_owner': False
                    })
            
            return result
        
        return self._cache_service.get_or_set(cache_key, fetch_members, CacheTimeout.MEDIUM)


# ============================================
# 全域實例和初始化
# ============================================

# Flask-Caching 實例
cache = Cache()

# 全域服務實例（在 init_cache 後設定）
cache_service: Optional[FlaskCacheService] = None
cache_invalidator: Optional[CacheInvalidator] = None
cache_decorator: Optional[CacheDecorator] = None
user_cache_service: Optional[UserCacheService] = None
project_cache_service: Optional[ProjectCacheService] = None


def init_cache(app):
    """
    初始化快取並建立服務實例
    
    使用依賴注入模式
    """
    global cache_service, cache_invalidator, cache_decorator
    global user_cache_service, project_cache_service
    
    cache_config = {
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
    }
    
    if cache_config['CACHE_TYPE'] == 'RedisCache':
        cache_config.update({
            'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            'CACHE_KEY_PREFIX': 'nexus_'
        })
    
    app.config.from_mapping(cache_config)
    cache.init_app(app)
    
    # 建立服務實例
    cache_service = FlaskCacheService(cache)
    cache_invalidator = CacheInvalidator(cache_service)
    cache_decorator = CacheDecorator(cache_service)
    user_cache_service = UserCacheService(cache_service)
    project_cache_service = ProjectCacheService(cache_service)
    
    return cache


# ============================================
# 向後相容的函數（保持舊 API）
# ============================================

def invalidate_user_cache(user_id: int) -> None:
    """向後相容：使使用者快取失效"""
    if cache_invalidator:
        cache_invalidator.invalidate_user(user_id)


def invalidate_project_stats(project_id: int) -> None:
    """向後相容：使專案統計快取失效"""
    if cache_invalidator:
        cache_invalidator.invalidate_project_stats(project_id)


def invalidate_notification_count(user_id: int) -> None:
    """向後相容：使通知數量快取失效"""
    if cache_invalidator:
        cache_invalidator.invalidate_notification_count(user_id)


def invalidate_project_members(project_id: int) -> None:
    """向後相容：使專案成員快取失效"""
    if cache_invalidator:
        cache_invalidator.invalidate_project_members(project_id)


# 向後相容的類別別名
class CacheService:
    """向後相容：舊的 CacheService API"""
    
    @staticmethod
    def get_or_set(key: str, callback: Callable, timeout: int = CacheTimeout.MEDIUM):
        if cache_service:
            return cache_service.get_or_set(key, callback, timeout)
        return callback()
    
    @staticmethod
    def get_notification_count(user_id: int) -> int:
        if user_cache_service:
            return user_cache_service.get_notification_count(user_id)
        from models import Notification
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def get_project_members_cached(project_id: int):
        if project_cache_service:
            return project_cache_service.get_members(project_id)
        return None
    
    @staticmethod
    def clear_all():
        if cache_service:
            cache_service.clear()
