"""
============================================
api - API 路由層
============================================

【這個模組的作用】
集中管理所有 API 端點（routes/endpoints）

【架構說明】
- 每個檔案對應一個領域的 API
- API 層只負責：接收請求 → 呼叫服務 → 回傳結果
- 業務邏輯在 services/ 層處理

【使用方式】
from api import register_blueprints
register_blueprints(app)
"""

# 從各個 API 模組導入 Blueprint
from .auth import auth_bp
from .projects import projects_bp
from .tasks import tasks_bp
from .notifications import notifications_bp
from .members import members_bp
from .tags import tags_bp
from .uploads import uploads_bp
from .health import health_bp

__all__ = [
    'auth_bp',
    'projects_bp',
    'tasks_bp',
    'notifications_bp',
    'members_bp',
    'tags_bp',
    'uploads_bp',
    'health_bp',
    'register_blueprints',
]


def register_blueprints(app):
    """
    註冊所有 API Blueprint 到 Flask app
    
    使用方式：
    from api import register_blueprints
    register_blueprints(app)
    """
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(tasks_bp)
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(members_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(health_bp)
    
    return app
