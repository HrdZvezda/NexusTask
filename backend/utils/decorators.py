"""
============================================
utils/decorators.py - 通用裝飾器
============================================

提供常用的裝飾器：
- 輸入驗證
- 請求日誌
- 權限檢查
"""

from functools import wraps
from flask import request, g
import logging
import time

logger = logging.getLogger(__name__)


def validate_json(f):
    """
    驗證請求是否為有效的 JSON
    
    使用方式：
    @app.route('/api/endpoint', methods=['POST'])
    @validate_json
    def my_endpoint():
        data = request.get_json()
        ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from utils.response import error_response, ErrorCode
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return error_response(
                    'Content-Type must be application/json',
                    code=ErrorCode.INVALID_FORMAT,
                    status=400
                )
            
            try:
                request.get_json()
            except Exception:
                return error_response(
                    'Invalid JSON body',
                    code=ErrorCode.INVALID_FORMAT,
                    status=400
                )
        
        return f(*args, **kwargs)
    
    return wrapper


def log_request(f):
    """
    記錄 API 請求的日誌
    
    使用方式：
    @app.route('/api/endpoint')
    @log_request
    def my_endpoint():
        ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # 記錄請求
        logger.info(f"Request: {request.method} {request.path}")
        
        # 執行函數
        response = f(*args, **kwargs)
        
        # 計算執行時間
        duration = time.time() - start_time
        
        # 取得回應狀態碼
        status_code = response[1] if isinstance(response, tuple) else 200
        
        # 記錄回應
        logger.info(f"Response: {status_code} ({duration:.3f}s)")
        
        return response
    
    return wrapper


def require_admin(f):
    """
    要求系統管理員權限
    
    使用方式：
    @app.route('/admin/endpoint')
    @jwt_required()
    @require_admin
    def admin_only():
        ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from models import User
        from utils.response import forbidden
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return forbidden('Admin privileges required')
        
        return f(*args, **kwargs)
    
    return wrapper


def require_project_access(f):
    """
    要求專案存取權限
    
    使用方式：
    @app.route('/projects/<int:project_id>/...')
    @jwt_required()
    @require_project_access
    def project_endpoint(project_id):
        ...
    """
    @wraps(f)
    def wrapper(project_id, *args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from models import Project, ProjectMember
        from utils.response import not_found, forbidden
        
        user_id = get_jwt_identity()
        
        # 檢查專案是否存在
        project = Project.query.get(project_id)
        if not project:
            return not_found('Project')
        
        # 檢查是否為 owner
        if project.owner_id == user_id:
            g.project = project
            g.project_role = 'owner'
            return f(project_id, *args, **kwargs)
        
        # 檢查是否為成員
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if member:
            g.project = project
            g.project_role = member.role
            return f(project_id, *args, **kwargs)
        
        return forbidden('You are not a member of this project')
    
    return wrapper


def require_project_admin(f):
    """
    要求專案管理員權限
    """
    @wraps(f)
    def wrapper(project_id, *args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from models import Project, ProjectMember
        from utils.response import not_found, forbidden
        
        user_id = get_jwt_identity()
        
        project = Project.query.get(project_id)
        if not project:
            return not_found('Project')
        
        # Owner 有管理員權限
        if project.owner_id == user_id:
            g.project = project
            g.project_role = 'owner'
            return f(project_id, *args, **kwargs)
        
        # 檢查是否為管理員成員
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            role='admin'
        ).first()
        
        if member:
            g.project = project
            g.project_role = 'admin'
            return f(project_id, *args, **kwargs)
        
        return forbidden('Admin privileges required for this project')
    
    return wrapper


def timer(f):
    """
    計時裝飾器，用於效能分析
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = f(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"{f.__name__} took {end - start:.4f} seconds")
        return result
    
    return wrapper

