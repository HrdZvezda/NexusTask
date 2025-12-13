"""
============================================
health.py - 健康檢查端點
============================================

【這個檔案的作用】
提供健康檢查端點，讓監控系統可以檢查應用程式的狀態。

【使用場景】
- Kubernetes 的 liveness/readiness probe
- Load balancer 的健康檢查
- 監控系統（如 Prometheus、Datadog）
- CI/CD pipeline 的部署驗證
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import time
import os
import sys

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

health_bp = Blueprint('health', __name__)


def check_database():
    """
    檢查資料庫連接
    """
    try:
        from models import db
        # 執行簡單的查詢測試連接
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'healthy', 'latency_ms': None}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def check_redis():
    """
    檢查 Redis 連接
    """
    try:
        import redis
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        
        start = time.time()
        client = redis.from_url(redis_url)
        client.ping()
        latency = (time.time() - start) * 1000
        
        return {'status': 'healthy', 'latency_ms': round(latency, 2)}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def check_cache():
    """
    檢查快取服務
    """
    try:
        from cache import cache
        
        # 測試設定和取得
        test_key = '_health_check_'
        cache.set(test_key, 'ok', timeout=10)
        result = cache.get(test_key)
        cache.delete(test_key)
        
        if result == 'ok':
            return {'status': 'healthy'}
        else:
            return {'status': 'degraded', 'error': 'Cache read/write mismatch'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def get_system_info():
    """
    取得系統資訊
    """
    import platform
    
    return {
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'processor': platform.processor(),
        'hostname': platform.node()
    }


def get_app_info():
    """
    取得應用程式資訊
    """
    return {
        'name': 'NexusTeam API',
        'version': current_app.config.get('API_VERSION', '2.0.0'),
        'environment': current_app.config.get('ENV', 'development'),
        'debug': current_app.debug
    }


# ============================================
# 端點定義
# ============================================

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    基本健康檢查
    
    用於快速檢查應用程式是否存活
    
    回應範例：
    {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness 檢查
    
    用於 Kubernetes liveness probe
    只檢查應用程式是否在運行
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness 檢查
    
    用於 Kubernetes readiness probe
    檢查應用程式是否準備好接收流量
    """
    # 檢查資料庫
    db_status = check_database()
    
    # 判斷整體狀態
    is_ready = db_status['status'] == 'healthy'
    
    status = 'ready' if is_ready else 'not_ready'
    status_code = 200 if is_ready else 503
    
    return jsonify({
        'status': status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': {
            'database': db_status
        }
    }), status_code


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    詳細健康檢查
    
    檢查所有依賴服務的狀態
    
    回應範例：
    {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "app": {
            "name": "NexusTeam API",
            "version": "2.0.0",
            "environment": "development"
        },
        "checks": {
            "database": { "status": "healthy", "latency_ms": 5.2 },
            "redis": { "status": "healthy", "latency_ms": 1.1 },
            "cache": { "status": "healthy" }
        },
        "system": {
            "python_version": "3.12.0",
            "platform": "..."
        }
    }
    """
    # 執行所有檢查
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'cache': check_cache()
    }
    
    # 判斷整體狀態
    all_healthy = all(
        check['status'] == 'healthy' 
        for check in checks.values()
    )
    
    any_unhealthy = any(
        check['status'] == 'unhealthy'
        for check in checks.values()
    )
    
    if all_healthy:
        overall_status = 'healthy'
        status_code = 200
    elif any_unhealthy:
        overall_status = 'unhealthy'
        status_code = 503
    else:
        overall_status = 'degraded'
        status_code = 200
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'app': get_app_info(),
        'checks': checks,
        'system': get_system_info()
    }), status_code


@health_bp.route('/health/metrics', methods=['GET'])
def metrics():
    """
    基本指標端點
    
    提供一些基本的應用程式指標
    """
    from models import User, Project, Task, Notification
    
    try:
        # 統計資料
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_projects = Project.query.count()
        active_projects = Project.query.filter_by(status='active').count()
        total_tasks = Task.query.count()
        pending_tasks = Task.query.filter(Task.status != 'done').count()
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metrics': {
                'users': {
                    'total': total_users,
                    'active': active_users
                },
                'projects': {
                    'total': total_projects,
                    'active': active_projects
                },
                'tasks': {
                    'total': total_tasks,
                    'pending': pending_tasks
                },
                'notifications': {
                    'unread': unread_notifications
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to collect metrics',
            'details': str(e)
        }), 500


@health_bp.route('/health/version', methods=['GET'])
def version():
    """
    版本資訊端點
    """
    return jsonify({
        'name': 'NexusTeam API',
        'version': current_app.config.get('API_VERSION', '2.0.0'),
        'build_date': os.getenv('BUILD_DATE', 'unknown'),
        'git_commit': os.getenv('GIT_COMMIT', 'unknown')
    }), 200

