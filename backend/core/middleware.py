"""
============================================
middleware.py - 中介軟體
============================================

【這個檔案的作用】
提供各種中介軟體（Middleware），在請求和回應之間執行：
- 安全性標頭
- 請求日誌
- 回應壓縮
- 錯誤處理
"""

import sys
import os

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import request, g
import time
import uuid
import logging
import gzip

logger = logging.getLogger(__name__)


def init_middleware(app):
    """
    初始化所有中介軟體
    """
    register_security_headers(app)
    register_request_logging(app)
    register_request_id(app)
    register_error_handlers(app)


# ============================================
# 安全性標頭
# ============================================

def register_security_headers(app):
    """
    為所有回應加上安全性標頭
    """
    @app.after_request
    def add_security_headers(response):
        # 防止點擊劫持
        response.headers['X-Frame-Options'] = 'DENY'
        
        # 防止 MIME 類型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # 啟用 XSS 過濾器
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # 控制 Referrer 資訊
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # 權限政策
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # 內容安全政策（CSP）
        # 注意：這是比較寬鬆的設定，生產環境應該更嚴格
        if not app.debug:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'"
            )
        
        # HSTS（只在生產環境啟用）
        if not app.debug and request.is_secure:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        
        return response


# ============================================
# 請求日誌
# ============================================

def register_request_logging(app):
    """
    記錄每個請求的資訊
    """
    @app.before_request
    def log_request_start():
        g.start_time = time.time()
        
        # 跳過健康檢查的日誌
        if request.path.startswith('/health'):
            return
        
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string
            }
        )
    
    @app.after_request
    def log_request_end(response):
        # 跳過健康檢查的日誌
        if request.path.startswith('/health'):
            return response
        
        duration = time.time() - getattr(g, 'start_time', time.time())
        
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        logger.log(
            log_level,
            f"Request completed: {request.method} {request.path} -> {response.status_code} ({duration:.3f}s)",
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': duration,
                'request_id': getattr(g, 'request_id', None)
            }
        )
        
        return response


# ============================================
# 請求 ID
# ============================================

def register_request_id(app):
    """
    為每個請求生成唯一 ID，方便追蹤和除錯
    """
    @app.before_request
    def set_request_id():
        # 從 header 取得或生成新的 request ID
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    
    @app.after_request
    def add_request_id_header(response):
        # 在回應中加上 request ID
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        return response


# ============================================
# 錯誤處理
# ============================================

def register_error_handlers(app):
    """
    註冊全域錯誤處理器
    """
    from utils.response import (
        error_response, 
        ErrorCode, 
        not_found, 
        internal_error,
        rate_limited
    )
    
    @app.errorhandler(400)
    def handle_400(error):
        return error_response(
            str(error.description) if hasattr(error, 'description') else 'Bad request',
            code=ErrorCode.VALIDATION_ERROR,
            status=400
        )
    
    @app.errorhandler(401)
    def handle_401(error):
        return error_response(
            'Authentication required',
            code=ErrorCode.AUTH_REQUIRED,
            status=401
        )
    
    @app.errorhandler(403)
    def handle_403(error):
        return error_response(
            'Permission denied',
            code=ErrorCode.PERMISSION_DENIED,
            status=403
        )
    
    @app.errorhandler(404)
    def handle_404(error):
        return not_found('Resource')
    
    @app.errorhandler(405)
    def handle_405(error):
        return error_response(
            'Method not allowed',
            code=ErrorCode.VALIDATION_ERROR,
            status=405
        )
    
    @app.errorhandler(429)
    def handle_429(error):
        return rate_limited('Too many requests. Please try again later.')
    
    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        return internal_error()
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        if app.debug:
            # 開發環境顯示詳細錯誤
            return error_response(
                str(error),
                code=ErrorCode.INTERNAL_ERROR,
                details={'type': type(error).__name__},
                status=500
            )
        
        return internal_error()


# ============================================
# CORS 增強
# ============================================

def setup_cors(app):
    """
    設定 CORS 允許的來源
    """
    from flask_cors import CORS
    
    origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000'])
    
    CORS(app, 
         origins=origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Request-ID'],
         expose_headers=['X-Request-ID', 'X-RateLimit-Remaining'],
         methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])


# ============================================
# 結構化日誌設定
# ============================================

def setup_structured_logging(app):
    """
    設定結構化日誌（JSON 格式）
    
    這讓日誌可以被 ELK、Datadog 等工具解析
    """
    import structlog
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# ============================================
# 請求大小限制
# ============================================

def register_request_size_limit(app):
    """
    限制請求大小
    """
    @app.before_request
    def check_content_length():
        max_length = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        
        content_length = request.content_length
        if content_length and content_length > max_length:
            from utils.response import error_response, ErrorCode
            return error_response(
                f'Request too large. Maximum size is {max_length // (1024*1024)}MB',
                code=ErrorCode.VALIDATION_ERROR,
                status=413
            )


# ============================================
# 維護模式
# ============================================

def register_maintenance_mode(app):
    """
    維護模式中介軟體
    """
    @app.before_request
    def check_maintenance():
        if app.config.get('MAINTENANCE_MODE', False):
            # 允許健康檢查端點
            if request.path.startswith('/health'):
                return None
            
            from utils.response import error_response, ErrorCode
            return error_response(
                'Service is under maintenance. Please try again later.',
                code=ErrorCode.SERVICE_UNAVAILABLE,
                status=503
            )

