"""
============================================
app.py - 後端應用程式的入口點（主程式）
============================================

【這個檔案的作用】
這是整個後端伺服器的「大腦」，負責：
1. 啟動 Flask 伺服器
2. 設定各種中間件（CORS、JWT、限流等）
3. 連接資料庫
4. 註冊所有的 API 路由
5. 處理各種錯誤

【什麼是後端？】
後端就是運行在伺服器上的程式，負責：
- 接收前端的請求
- 處理業務邏輯（例如：驗證使用者、儲存資料）
- 和資料庫互動
- 回傳結果給前端

【串接流程圖】

前端 (React)                    後端 (Flask)
   │                                │
   │ HTTP 請求 (例如 POST /auth/login)
   │──────────────────────────────>│
   │                                │
   │                          app.py (這個檔案)
   │                                │
   │                                ├─ CORS 檢查 (是否允許這個來源？)
   │                                │
   │                                ├─ JWT 檢查 (有沒有帶 token？)
   │                                │
   │                                ├─ Rate Limit 檢查 (請求是否太頻繁？)
   │                                │
   │                                └─ 路由到對應的處理函數
   │                                      │
   │                                      ├─ /auth/* → auth.py
   │                                      ├─ /projects/* → projects.py
   │                                      ├─ /tasks/* → tasks.py
   │                                      ├─ /api/notifications/* → notifications.py
   │                                      └─ /members/* → members.py
   │                                            │
   │                                            └─ 和資料庫互動 (models.py)
   │                                                    │
   │ HTTP 回應 (JSON 格式)                              │
   │<──────────────────────────────────────────────────┘

【後端架構】

app.py (入口點，你現在在這裡)
   │
   ├─ config.py (設定檔：資料庫路徑、JWT 密鑰等)
   │
   ├─ models.py (資料模型：定義資料表的結構)
   │
   ├─ auth.py (認證 API：登入、註冊、登出等)
   │
   ├─ projects.py (專案 API：建立、刪除、成員管理等)
   │
   ├─ tasks.py (任務 API：建立、更新、評論等)
   │
   ├─ notifications.py (通知 API：取得通知、標記已讀等)
   │
   └─ members.py (成員 API：取得所有使用者)
"""

# ============================================
# 導入需要的模組
# ============================================

# Flask 核心
# Flask: 建立網頁應用程式的框架
# request: 存取 HTTP 請求的內容（標頭、參數等）
# jsonify: 把 Python 字典轉成 JSON 格式的回應
from flask import Flask, request, jsonify

# Flask-CORS: 處理跨來源請求
# 【什麼是 CORS？】Cross-Origin Resource Sharing
# 當前端 (localhost:3000) 要請求後端 (localhost:8888) 時，
# 瀏覽器會因為「安全原因」阻擋這個請求（因為網址不同）
# CORS 設定告訴瀏覽器：「沒關係，我允許這個來源的請求」
from flask_cors import CORS

# Flask-JWT-Extended: 處理 JWT (JSON Web Token) 認證
# JWT 就像是一張「電子通行證」，證明使用者的身份
from flask_jwt_extended import JWTManager

# Flask-Bcrypt: 密碼加密
# 密碼不能直接存到資料庫（太危險了！）
# Bcrypt 會把密碼「雜湊」成一串亂碼，這樣即使資料外洩也不會洩漏密碼
from flask_bcrypt import Bcrypt

# Flask-Limiter: 請求限流
# 防止有人惡意發送大量請求（例如暴力破解密碼）
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 導入設定檔
from config import Config

# 導入資料庫模型
from models import db

# SQLAlchemy 的 text 函數，用來執行原生 SQL
from sqlalchemy import text

# 日期時間處理
from datetime import datetime

# 日誌記錄
import logging
from logging.handlers import RotatingFileHandler

# 作業系統相關功能（讀取環境變數、建立資料夾等）
import os

# ============================================
# 新增：快取、WebSocket、API 文件等模組
# ============================================

# 從 core 模組導入核心功能
from core import (
    init_cache,
    cache,
    init_socketio,
    socketio,
    init_swagger,
    init_middleware,
    check_if_token_revoked,
)

# 從 api 模組導入 Blueprint
from api import health_bp

# ============================================
# 初始化 Flask 應用程式
# ============================================

"""
Flask(__name__) 建立一個 Flask 應用程式實例
__name__ 是 Python 的特殊變數，代表目前的模組名稱

這就像是開一家店：
- Flask 是店的框架
- app 是你的店
- 接下來的程式碼會設定店的各種功能
"""
app = Flask(__name__)

"""
app.config.from_object(Config) 載入設定
Config 類別定義在 config.py 中，包含：
- 資料庫連接字串
- JWT 密鑰
- 其他設定
"""
app.config.from_object(Config)

# ============================================
# CORS 設定（跨來源資源共享）
# ============================================

"""
【為什麼需要 CORS？】

當你的前端在 http://localhost:3000 運行，
後端在 http://localhost:8888 運行，
瀏覽器會認為這是「不同的網站」（因為 port 不同）。

出於安全考量，瀏覽器預設會阻擋「跨來源」的請求。
CORS 設定告訴瀏覽器：「這些來源是我允許的，放行吧！」

【allowed_origins 設定】
列出所有允許的前端網址：
- localhost:3000 - React 開發伺服器
- localhost:5173 - Vite 開發伺服器
- 127.0.0.1:5173 - 同上，只是用 IP 而不是 localhost
- localhost:5500 - Live Server（VS Code 擴展）
- CORS_ORIGINS 環境變數 - 部署後的前端網址    
"""
allowed_origins = os.getenv(
    'CORS_ORIGINS', 
    'http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5500,http://localhost:5500'
).split(',')
'''
app.logger.info
- app -  Flask 應用程式
- logger - Flask 的日誌工具,日誌記錄器
- info - 日誌等級, info 為一般訊息
'''
app.logger.info(f"CORS allowed origins: {allowed_origins}")

"""
CORS 設定說明：
- supports_credentials=True: 允許帶上認證資訊（cookies、Authorization header）
- origins: 允許的來源網址列表
- methods: 允許的 HTTP 方法
- allow_headers: 允許的請求標頭
"""
CORS(app, 
     supports_credentials=True, 
     origins=allowed_origins,
     methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS', 'PUT'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'])

# ============================================
# 擴展初始化
# ============================================

"""
db.init_app(app) 初始化資料庫連接
db 是在 models.py 中定義的 SQLAlchemy 實例
這行程式碼把資料庫連接到我們的 Flask 應用程式
"""
db.init_app(app)

"""
JWTManager(app) 初始化 JWT 認證系統
JWT (JSON Web Token) 用來驗證使用者身份
"""
jwt = JWTManager(app)

# 註冊 token 黑名單檢查器
# 當使用者登出後，他們的 token 會被加入黑名單
# 這個回調函數會在每次請求時檢查 token 是否被撤銷
# jwt_header: token 的 header(設定)
# jwt_payload: token 的 payload(資料)
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return check_if_token_revoked(jwt_header, jwt_payload)

"""
Bcrypt(app) 初始化密碼加密系統
用來安全地儲存和驗證使用者密碼
"""
bcrypt = Bcrypt(app)

'''
把 bcrypt 存到 app.extensions，讓其他file可以存取
extensions 是 Flask 的一個機制，讓我們可以跨模組分享工具
在其他file可以from flask import current_app
current_app是flask內建的,代表目前正在處理請求的 Flask 應用程式
'''
app.extensions['bcrypt'] = bcrypt

# ============================================
# 初始化新增的擴展
# ============================================

"""
初始化快取層 - cache
開發環境使用 SimpleCache（記憶體）
生產環境使用 Redis
SimpleCache 是 Flask-Caching 提供的簡單快取實例,程式重啟就清空
Redis 是一個專業的快取伺服器,資料會保存在記憶體中,程式重啟不會清空
"""
init_cache(app)
app.logger.info('Cache initialized')

"""
初始化 WebSocket - socketio
用於即時通知和任務同步
Flask-SocketIO 是 Flask 的 WebSocket 擴展
Socket.IO 是底層的 WebSocket 函式庫
"""
init_socketio(app)
app.logger.info('SocketIO initialized')

"""
初始化 API 文件（Swagger）
存取路徑：/api/docs
flasgger 是 Flask 的 Swagger 擴展，提供 API 文件 UI 和 OpenAPI 規格
swagger - 自動產生的「API 說明書 + 測試台」
"""
init_swagger(app)
app.logger.info('Swagger API docs initialized at /api/docs')

"""
初始化中介軟體
包含安全性標頭、請求日誌、錯誤處理等
"""
init_middleware(app)
app.logger.info('Middleware initialized')

"""
Limiter 初始化請求限流
防止惡意使用者發送過多請求

設定說明：
- app=app: 將限流器綁定到 Flask 應用程式
- key_func=get_remote_address: 用什麼來識別使用者
- storage_uri: 請求計數要存在哪（開發環境用記憶體,生產環境用Redis）
- strategy: 限流策略（固定時間窗口or滑動時間窗口）
- enabled: 是否啟用限流
"""
limiter = Limiter(
    app=app,
    key_func=get_remote_address, # 用 IP 來識別使用者,也可以用user_id API_KEY等
    # 開發環境放寬限制，避免頻繁測試時被擋
    default_limits=["10000 per day", "1000 per hour", "100 per minute"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'), # 如果有設定REDIS_URL 環境變數 → 用 Redis, 否則用記憶體memory://
    storage_options={"socket_connect_timeout": 30}, # 連接 Redis 超過 30 秒就放棄
    strategy="fixed-window", # 每分鐘00:00 - 00:59, 01:00 - 01:59... 
    # 開發模式下可以關閉限流
    '''
    如果（不是開發環境）或（明確啟用限流）  → 開啟限流
    開發環境 + 沒設定 ENABLE_RATE_LIMIT → 關閉（開發時不擋你）
    生產環境                           → 開啟（保護伺服器）
    開發環境 + ENABLE_RATE_LIMIT=true  → 開啟（測試限流功能）
    '''
    enabled=os.getenv('FLASK_ENV') != 'development' or os.getenv('ENABLE_RATE_LIMIT', 'false').lower() == 'true'
)

# ============================================
# 日誌設定
# ============================================

def setup_logging(app):
    """
    設定日誌系統
    
    【什麼是日誌？】
    日誌就像是「航行日誌」，記錄系統發生的所有事情：
    - 誰在什麼時候登入
    - 發生了什麼錯誤
    - 系統運作是否正常
    
    這對於除錯和監控非常重要！
    
    【日誌分類】
    - app.log: 記錄一般資訊（誰登入、什麼請求）
    - error.log: 只記錄錯誤（方便快速找問題）
    """
    # 確保 logs 目錄存在
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 設定日誌格式
    # [時間] 等級 in 模組: 訊息
    # 例如：[2024-01-15 10:30:00] INFO in auth: User login successful
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # 一般資訊日誌
    # RotatingFileHandler: 當檔案太大時，會自動建立新檔案
    # maxBytes=10240000: 最大 10MB
    # backupCount=10: 最多保留 10 個備份檔案
    info_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,
        backupCount=10
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    
    # 錯誤日誌
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10240000,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # 把處理器加到 app 的日誌系統
    app.logger.addHandler(info_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('Application startup')

# 在非除錯模式下啟用日誌
# 如果不是除錯模式(通常是生產環境)
if not app.debug:
    setup_logging(app)

# ============================================
# 資料庫初始化
# ============================================

"""
with app.app_context(): 
建立應用程式上下文，讓我們可以操作資料庫

db.create_all() 
根據 models.py 中定義的模型，建立所有資料表
如果資料表已存在，不會重複建立
"""
with app.app_context():
    db.create_all()
    app.logger.info('Database tables created')

# ============================================
# 註冊 Blueprints（路由模組）
# ============================================

"""
【什麼是 Blueprint？】
Blueprint 就像是「分店」的概念。

想像你開了一家大型百貨公司（Flask app），
你不會把所有商品都放在同一層樓，
而是分成不同的樓層（Blueprint）：
- 1F 認證部門 (auth.py)
- 2F 專案部門 (projects.py)
- 3F 任務部門 (tasks.py)
- 4F 通知部門 (notifications.py)
- 5F 成員部門 (members.py)

每個 Blueprint 負責處理自己領域的 API。

【url_prefix 是什麼？】
url_prefix 是 API 路徑的前綴。
例如：url_prefix='/auth' 表示這個 Blueprint 的所有路由都會加上 /auth
- auth.py 中的 /login → 變成 /auth/login
- auth.py 中的 /register → 變成 /auth/register
"""

# ============================================
# 使用 api 模組註冊所有 API Blueprint
# ============================================
from api import (
    auth_bp, 
    projects_bp, 
    tasks_bp, 
    notifications_bp, 
    members_bp, 
    uploads_bp, 
    tags_bp,
    health_bp
)

# 認證相關 API
app.register_blueprint(auth_bp, url_prefix='/auth')

# 專案相關 API
app.register_blueprint(projects_bp, url_prefix='/projects')

# 任務相關 API
app.register_blueprint(tasks_bp)

# 通知相關 API
app.register_blueprint(notifications_bp, url_prefix='/api')

# 成員相關 API
app.register_blueprint(members_bp)

# 附件上傳相關 API
app.register_blueprint(uploads_bp)

# 標籤相關 API
app.register_blueprint(tags_bp)

# 健康檢查 API
app.register_blueprint(health_bp)

# ============================================
# JWT 錯誤處理
# ============================================

"""
【JWT 錯誤處理的作用】
當 JWT token 出問題時（過期、無效等），
我們要回傳有意義的錯誤訊息給前端，
而不是讓程式當掉。

@jwt.xxx_loader 是裝飾器，告訴 Flask-JWT-Extended：
「當發生這種錯誤時，執行這個函數」
"""

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """
    處理 Token 過期的情況
    
    當使用者的 access token 過期時，會執行這個函數
    前端收到這個錯誤後，應該嘗試用 refresh token 換新的 access token
    
    【對應前端】apiService.ts 的 tryRefreshToken() 函數
    """
    # {request.remote_addr} - 當前請求的 IP 位址
    app.logger.warning(f"Expired token attempt from: {request.remote_addr}")
    return jsonify({
        'error': 'token_expired',
        'message': 'The token has expired. Please refresh your token or login again.'
    }), 401  # 401 = Unauthorized（未授權）

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """
    處理無效 Token 的情況
    
    當 token 格式錯誤或被竄改時，會執行這個函數
    """
    app.logger.warning(f"Invalid token attempt from: {request.remote_addr}, error: {error}")
    return jsonify({
        'error': 'invalid_token',
        'message': 'Token validation failed. Please provide a valid token.'
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    """
    處理缺少 Token 的情況
    
    當需要認證的 API 沒有帶 token 時，會執行這個函數
    """
    app.logger.warning(f"Unauthorized access attempt from: {request.remote_addr}, error: {error}")
    return jsonify({
        'error': 'authorization_required',
        'message': 'Access token is required. Please provide an authorization token.'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """
    處理被撤銷的 Token
    
    例如：使用者登出後，他的 token 應該被撤銷
    """
    return jsonify({
        'error': 'token_revoked',
        'message': 'The token has been revoked. Please login again.'
    }), 401

# ============================================
# 全域錯誤處理
# ============================================

"""
【全域錯誤處理的作用】
當 API 發生錯誤時，我們不想讓使用者看到：
"Internal Server Error" 這種醜陋的訊息

我們要：
1. 回傳有格式的 JSON 錯誤訊息
2. 記錄錯誤到日誌（方便除錯）
3. 不洩漏敏感資訊給前端

@app.errorhandler(400) 是裝飾器，告訴 Flask：
「當發生 HTTP 400 錯誤時，執行這個函數」
"""

@app.errorhandler(400)
def bad_request(error):
    """
    處理 400 Bad Request 錯誤
    
    當前端送的請求格式錯誤時（例如 JSON 格式不對）
    """
    return jsonify({
        'error': 'bad_request',
        'message': 'The request is malformed or invalid',
        'status': 400
    }), 400

@app.errorhandler(404)
def not_found(error):
    """
    處理 404 Not Found 錯誤
    
    當前端請求的 API 路徑不存在時
    """
    return jsonify({
        'error': 'not_found',
        'message': 'The requested resource does not exist',
        'status': 404
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """
    處理 405 Method Not Allowed 錯誤
    
    當前端用錯 HTTP 方法時
    例如：用 GET 請求一個只接受 POST 的 API
    """
    return jsonify({
        'error': 'method_not_allowed',
        'message': 'The HTTP method is not allowed for this endpoint',
        'status': 405
    }), 405

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """
    處理 429 Too Many Requests 錯誤
    
    當使用者請求太頻繁，超過限制時
    """
    app.logger.warning(f"Rate limit exceeded from: {request.remote_addr}")
    return jsonify({
        'error': 'rate_limit_exceeded',
        'message': 'Too many requests. Please try again later.',
        'status': 429
    }), 429

@app.errorhandler(500)
def internal_server_error(error):
    """
    處理 500 Internal Server Error 錯誤
    
    當伺服器發生未預期的錯誤時
    
    重要：
    - 不要把錯誤細節告訴前端（可能洩漏敏感資訊）
    - 要記錄完整的錯誤到日誌（方便除錯）
    - 要 rollback 資料庫交易（避免資料不一致）
    """
    # 回滾資料庫交易
    db.session.rollback()
    
    # 記錄完整錯誤到日誌（exc_info=True 會記錄 stack trace）
    app.logger.error(f"Internal server error: {str(error)}", exc_info=True)
    
    # 只給前端看通用訊息
    return jsonify({
        'error': 'internal_server_error',
        'message': 'An internal error occurred. Our team has been notified.',
        'status': 500
    }), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """
    處理所有未預期的錯誤（最後防線）
    
    如果有任何錯誤沒被上面的處理器捕捉到，
    這個函數會捕捉它，確保程式不會當掉
    """
    db.session.rollback()
    
    app.logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    return jsonify({
        'error': 'unexpected_error',
        'message': 'An unexpected error occurred. Please try again later.',
        'status': 500
    }), 500

# ============================================
# 請求/回應日誌
# ============================================

@app.before_request
def log_request():
    """
    在處理每個請求之前執行
    
    記錄：誰（IP）在什麼時候請求了什麼（方法、路徑）
    """
    if not app.debug:
        app.logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    """
    在每個請求處理完成後執行
    
    記錄：回應的狀態碼
    """
    if not app.debug:
        app.logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
   
    return response

@app.after_request
def add_security_headers(response):
    """
    加上安全相關的 HTTP 標頭
    """

    # X-Content-Type-Options: 防止瀏覽器猜測 MIME 類型
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # X-Frame-Options: 防止網頁被嵌入到 iframe 中（防止點擊劫持）
    response.headers['X-Frame-Options'] = 'DENY'
    # X-XSS-Protection: 啟用瀏覽器的 XSS 過濾器
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response 

# ============================================
# 健康檢查端點
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康檢查 API
    
    【用途】
    - 監控系統用來檢查服務是否正常運作
    - 負載平衡器用來判斷要不要把請求送到這台伺服器
    
    【對應前端】
    前端可以呼叫這個 API 來檢查後端是否在線
    
    @app.route('/health', methods=['GET']) 說明：
    - '/health': API 的路徑
    - methods=['GET']: 只接受 GET 請求
    """
    try:
        # 測試資料庫連線是否正常
        # 執行一個簡單的 SQL 查詢
        db.session.execute(text('SELECT 1'))
        
        # 資料庫正常，回傳健康狀態
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200  # 200 = OK
        
    except Exception as e:
        # 資料庫連線失敗
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': 'Database connection failed'
        }), 503  # 503 = Service Unavailable

# ============================================
# API 首頁（文件）
# ============================================

@app.route('/')
@limiter.limit("10 per minute")  # 限制每分鐘最多 10 次請求
def home():
    """
    API 首頁
    
    顯示 API 的基本資訊和所有可用的端點
    這就像是一份「菜單」，告訴前端有哪些 API 可以使用
    """
    return jsonify({
        'message': 'Team Task Manager API',
        'version': '2.1.0',
        'documentation': '/api/docs',
        'endpoints': {
            'health': {
                'path': '/health',
                'methods': ['GET'],
                'description': 'Health check endpoint'
            },
            'auth': {
                'register': {'path': '/auth/register', 'methods': ['POST']},
                'login': {'path': '/auth/login', 'methods': ['POST'], 'note': 'Account locks after 5 failed attempts'},
                'refresh': {'path': '/auth/refresh', 'methods': ['POST']},
                'logout': {'path': '/auth/logout', 'methods': ['POST']},
                'me': {'path': '/auth/me', 'methods': ['GET', 'PATCH']},
                'change_password': {'path': '/auth/change-password', 'methods': ['POST']},
                'forgot_password': {'path': '/auth/forgot-password', 'methods': ['POST']},
                'reset_password': {'path': '/auth/reset-password', 'methods': ['POST']},
                'verify_reset_token': {'path': '/auth/verify-reset-token', 'methods': ['POST']}
            },
            'projects': {
                'list': {'path': '/projects', 'methods': ['GET', 'POST']},
                'detail': {'path': '/projects/:id', 'methods': ['GET', 'PATCH', 'DELETE']},
                'members': {'path': '/projects/:id/members', 'methods': ['GET', 'POST']},
                'stats': {'path': '/projects/:id/stats', 'methods': ['GET']}
            },
            'tasks': {
                'list': {'path': '/projects/:id/tasks', 'methods': ['GET', 'POST'], 'note': 'Supports pagination'},
                'all_tasks': {'path': '/tasks/all', 'methods': ['GET'], 'note': 'Supports pagination'},
                'my_tasks': {'path': '/tasks/my', 'methods': ['GET'], 'note': 'Supports pagination'},
                'detail': {'path': '/tasks/:id', 'methods': ['GET', 'PATCH', 'DELETE']},
                'comments': {'path': '/tasks/:id/comments', 'methods': ['GET', 'POST']}
            },
            'notifications': {
                'list': {'path': '/api/notifications', 'methods': ['GET']},
                'mark_read': {'path': '/api/notifications/:id/read', 'methods': ['PATCH']},
                'settings': {'path': '/api/notifications/settings', 'methods': ['GET', 'PATCH']}
            }
        },
        'security_features': {
            'account_lockout': 'Account locks for 15 minutes after 5 failed login attempts',
            'password_strength': 'Configurable via PASSWORD_MIN_LENGTH, PASSWORD_REQUIRE_UPPERCASE, etc.',
            'password_reset': 'Reset tokens expire after 1 hour'
        },
        'rate_limits': {
            'default': '200 per hour, 1000 per day',
            'auth': {
                'register': '5 per hour',
                'login': '10 per minute',
                'forgot_password': '3 per hour'
            }
        }
    })

# ============================================
# 開發環境專用的除錯路由
# ============================================

if app.debug:
    @app.route('/debug/routes')
    def debug_routes():
        """
        列出所有註冊的路由（僅開發環境可用）
        
        用於除錯：查看所有 API 路徑
        """
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        return jsonify({'routes': routes})

# ============================================
# 啟動應用程式
# ============================================

"""
if __name__ == '__main__':
這個條件判斷的意思是：
「只有當這個檔案被直接執行時，才執行以下程式碼」

如果這個檔案被其他檔案 import，就不會執行

【執行方式】
在終端機中執行：python app.py
這會啟動 Flask 開發伺服器

【生產環境注意】
生產環境不應該用 Flask 內建的伺服器
應該使用 gunicorn 或 uwsgi 這類的 WSGI 伺服器
"""
if __name__ == '__main__':
    # 從環境變數讀取設定
    # FLASK_DEBUG=true 會啟用除錯模式
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    # FLASK_PORT 設定監聽的連接埠，預設 8888
    port = int(os.getenv('FLASK_PORT', 8888))
    # 印出 現在使用哪個DB
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # 啟動伺服器
    app.run(
        debug=debug_mode,  # 除錯模式（會自動重新載入程式碼）
        port=port,         # 連接埠
        host='0.0.0.0'     # 監聽所有網路介面（允許其他電腦連接）
    )
