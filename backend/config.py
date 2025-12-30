"""
============================================
config.py - 應用程式設定檔
============================================

【這個檔案的作用】
集中管理所有的應用程式設定，包括：
- 資料庫連接
- JWT 認證設定
- 安全性設定
- 各種環境的不同設定

【為什麼需要設定檔？】
1. 集中管理：所有設定放在一起，方便查看和修改
2. 環境區分：開發、測試、生產環境可以有不同的設定
3. 安全性：敏感資訊（密碼、密鑰）從環境變數讀取，不會寫死在程式碼中
4. 可維護性：修改設定不需要改動程式碼

【環境變數是什麼？】
環境變數是作業系統提供的一種儲存設定的方式。
好處是：
- 不會被提交到 Git（避免洩漏密碼）
- 不同伺服器可以有不同的設定
- 可以在部署時動態設定

設定環境變數的方式：
1. 在終端機：export SECRET_KEY="my-secret-key"
2. 在 .env 檔案中：SECRET_KEY=my-secret-key
3. 在部署平台的設定介面

【這個檔案在哪裡被使用？】
在 app.py 中：
app.config.from_object(Config)
"""

# ============================================
# 導入需要的模組
# ============================================

# os 模組用來讀取環境變數
import os

# timedelta 用來設定時間間隔（例如 token 的有效期）
from datetime import timedelta

# python-dotenv 用來從 .env 檔案讀取環境變數
from dotenv import load_dotenv

# ============================================
# 載入 .env 檔案
# ============================================

"""
load_dotenv() 會讀取專案根目錄的 .env 檔案，
把裡面的設定載入成環境變數。

.env 檔案範例：
SECRET_KEY=my-super-secret-key
DATABASE_URL=postgresql://user:pass@localhost/mydb
JWT_SECRET_KEY=another-secret-key
"""
load_dotenv()

# ============================================
# 主要設定類別
# ============================================

class Config:
    """
    應用程式的基本設定
    
    這個類別定義了所有的設定項目。
    其他環境的設定類別（DevelopmentConfig、ProductionConfig）會繼承這個類別。
    
    【設定項目說明】
    每個設定都使用 os.getenv('KEY', 'default_value') 的格式：
    - 'KEY': 環境變數的名稱
    - 'default_value': 如果環境變數不存在時使用的預設值
    """
    
    # ============================================
    # 基本設定
    # ============================================
    
    """
    SECRET_KEY - 應用程式的密鑰
    
    【用途】
    - 用於加密 session
    - 用於 CSRF 保護
    - 用於其他需要加密的地方
    
    【重要！】
    在生產環境中，必須設定一個強隨機值！
    可以用這個指令產生：python -c "import secrets; print(secrets.token_hex(32))"
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    """
    ENV 和 DEBUG - 環境設定
    
    【環境類型】
    - development: 開發環境（你的電腦上）
    - production: 生產環境（正式上線的伺服器）
    - testing: 測試環境
    
    【DEBUG 模式】
    DEBUG=True 時：
    - 程式碼修改會自動重新載入
    - 錯誤會顯示詳細的除錯資訊
    - ⚠️ 絕對不能在生產環境開啟！（會洩漏敏感資訊）
    """
    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # ============================================
    # 資料庫設定
    # ============================================
    
    """
    SQLALCHEMY_DATABASE_URI - 資料庫連接字串
    
    【格式說明】
    不同資料庫的連接字串格式不同：
    
    SQLite（輕量級，適合開發）:
    sqlite:///task_manager.db
    
    PostgreSQL（適合生產環境）:
    postgresql://username:password@localhost:5432/database_name
    
    MySQL:
    mysql://username:password@localhost:3306/database_name
    
    【開發 vs 生產】
    - 開發環境：使用 SQLite（簡單，不需要安裝額外軟體）
    - 生產環境：使用 PostgreSQL 或 MySQL（效能好，功能完整）
    """
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', # 先看有沒有設定環境變數
        'sqlite:///task_manager.db'  # 沒有設定的話 預設用 SQLite
    )
    
    # 關閉 SQLAlchemy 的修改追蹤（提升效能）
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    """
    SQLALCHEMY_ENGINE_OPTIONS - 資料庫連接池設定
    
    【什麼是連接池？】
    資料庫連接是「昂貴」的操作（需要時間建立）。
    連接池會預先建立一些連接，需要時直接拿來用，用完放回去。
    這樣可以大幅提升效能。
    
    【設定說明】
    - pool_size: 連接池的大小（同時保持多少個連接）
    - pool_recycle: 多久回收一個連接（秒）
    - pool_pre_ping: 使用前先檢查連接是否有效
    - max_overflow: 超過 pool_size 時最多可以再建立多少個連接
    """
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 10))
    }
    
    # ============================================
    # JWT 設定
    # ============================================
    
    """
    JWT (JSON Web Token) 設定
    
    【什麼是 JWT？】
    JWT 是一種身份認證的方式，就像是「電子通行證」。
    使用者登入後，伺服器會發給他一個 token。
    之後使用者每次請求都要帶著這個 token，證明自己的身份。
    
    【為什麼用 JWT？】
    1. 無狀態：伺服器不需要記住誰登入了
    2. 可擴展：多台伺服器都可以驗證同一個 token
    3. 安全：token 有簽名，無法偽造
    """
    
    # JWT 專用的密鑰（可以和 SECRET_KEY 不同，提高安全性）
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    
    """
    Token 過期時間
    
    【Access Token】
    - 短期有效（預設 1 小時）
    - 用於日常的 API 請求
    - 過期後需要用 Refresh Token 換新的
    
    【Refresh Token】
    - 長期有效（預設 30 天）
    - 只用於獲取新的 Access Token
    - 過期後需要重新登入
    
    【為什麼要分兩種 Token？】
    安全性考量：
    - Access Token 經常傳輸，風險較高，所以設定較短的有效期
    - Refresh Token 很少傳輸，可以設定較長的有效期
    """
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    )
    
    # Token 放在 HTTP Headers 中
    JWT_TOKEN_LOCATION = ['headers']
    # Header 的名稱
    JWT_HEADER_NAME = 'Authorization'
    # Token 的前綴（格式：Bearer <token>）
    JWT_HEADER_TYPE = 'Bearer'
    
    # 自訂錯誤訊息的 key 名稱
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    # ============================================
    # CORS 設定
    # ============================================
    
    """
    CORS (Cross-Origin Resource Sharing) 設定
    
    【什麼是 CORS？】
    當前端（localhost:3000）要請求後端（localhost:8888）時，
    瀏覽器會因為「網址不同」而阻擋請求。
    CORS 設定告訴瀏覽器：「這些來源是安全的，可以放行」。
    
    【注意】
    生產環境不要使用 '*'（允許所有來源），
    要明確指定允許的來源。
    """
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # ============================================
    # Rate Limiting 設定
    # ============================================
    
    """
    Rate Limiting - 請求頻率限制
    
    【用途】
    防止惡意使用者發送大量請求，例如：
    - 暴力破解密碼
    - DDoS 攻擊
    - 爬蟲過度抓取
    
    【儲存位置】
    - 開發環境：memory://（存在記憶體中）
    - 生產環境：Redis（分散式，可跨伺服器）
    """
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    RATELIMIT_STORAGE_URL = REDIS_URL if ENV == 'production' else 'memory://'
    RATELIMIT_STRATEGY = 'fixed-window'  # 固定時間窗口策略
    RATELIMIT_HEADERS_ENABLED = True  # 在回應中加上限流相關的 headers
    
    # ============================================
    # Session 設定
    # ============================================
    
    """
    Session Cookie 安全設定
    
    【SESSION_COOKIE_SECURE】
    True: Cookie 只能透過 HTTPS 傳輸
    生產環境一定要開啟！
    
    【SESSION_COOKIE_HTTPONLY】
    True: JavaScript 無法讀取這個 Cookie
    可以防止 XSS 攻擊竊取 session
    
    【SESSION_COOKIE_SAMESITE】
    'Lax': Cookie 只會在同站請求時發送
    可以防止 CSRF 攻擊
    """
    SESSION_COOKIE_SECURE = ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ============================================
    # 檔案上傳設定
    # ============================================
    
    """
    檔案上傳相關設定
    
    【MAX_CONTENT_LENGTH】
    上傳檔案的大小限制，預設 16MB
    超過這個大小的請求會被拒絕
    
    【ALLOWED_EXTENSIONS】
    允許上傳的檔案類型
    限制可以上傳的檔案類型可以防止惡意檔案
    """
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # ============================================
    # Email 設定
    # ============================================
    
    """
    郵件伺服器設定
    
    【用途】
    - 發送密碼重設郵件
    - 發送通知郵件
    - 發送邀請郵件
    
    【設定說明】
    這裡使用 Gmail 的 SMTP 伺服器作為預設值。
    如果要使用其他郵件服務，需要修改這些設定。
    
    Gmail 的話要用「應用程式密碼」
    如果你要用 Gmail 發信，不能用普通密碼！
    步驟：
    Google 帳號 → 安全性 → 兩步驟驗證（開啟）
    安全性 → 應用程式密碼 → 產生一組 16 碼密碼
    把這組密碼填入 MAIL_PASSWORD
    
    盡量用專門的帳號寄信, 免費帳號每天最多500封
    """
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587)) # 587(TSL) or 465(SSL)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true' # 是否加密
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # 寄信人的 email 帳號
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # 寄信人的 email 密碼或應用程式密碼
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@taskmanager.com')
    
    # ============================================
    # 日誌設定
    # ============================================
    
    """
    日誌（Logging）設定
    
    【LOG_LEVEL】
    日誌的詳細程度，從多到少：
    DEBUG > INFO > WARNING > ERROR > CRITICAL
    
    開發環境可以用 DEBUG，生產環境建議用 INFO 或 WARNING
    
    這個專案已經有寫在app.py了, 所以這裡可以不寫
    but 建議寫在config.py中, 這樣可以方便修改, 而且可以透過環境變數修改
    """
    # LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    # LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # ============================================
    # 安全設定
    # ============================================
    
    """
    密碼強度要求
    
    這些設定決定使用者的密碼需要滿足什麼條件。
    更嚴格的要求 = 更安全，但使用者體驗較差。
    """
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'False').lower() == 'true'
    PASSWORD_REQUIRE_NUMBERS = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'False').lower() == 'true'
    PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'False').lower() == 'true' # 特殊符號
    
    # ============================================
    # Celery 設定（非同步任務）
    # ============================================
    
    """
    Celery 設定
    
    【什麼是 Celery？】
    Celery 是一個非同步任務佇列，用來處理耗時的任務可以在背景做，例如：
    - 發送大量郵件
    - 產生報表
    - 處理大量資料
    
    這樣這些任務就不會阻塞 API 的回應。
    """
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    # ============================================
    # 其他設定
    # ============================================
    
    # API 版本
    # API_VERSION = '2.1.1'
    
    # 時區設定
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    
    # 分頁設定
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', 20))  # 預設每頁筆數
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', 50))  # 最大每頁筆數
    
    # ============================================
    # 快取設定
    # ============================================
    
    """
    快取設定
    
    【快取後端】
    - SimpleCache：記憶體快取，適合開發
    - RedisCache：分散式快取，適合生產
    """
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))  # 5 分鐘
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # ============================================
    # WebSocket 設定
    # ============================================
    
    """
    SocketIO 設定(即時通知or即時更新)
    async mode:
    eventlet	輕量級，適合 I/O 密集型（如 WebSocket）,需pip i eventlet
    gevent	類似 eventlet，另一種選擇
    threading	用多執行緒，簡單但效能較差
    """
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', REDIS_URL)
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'eventlet')
    
    # ============================================
    # 帳號安全設定
    # ============================================
    
    """
    帳號鎖定設定
    
    用於防止暴力破解攻擊
    """
    LOGIN_ATTEMPT_LOCKOUT_THRESHOLD = int(os.getenv('LOGIN_ATTEMPT_LOCKOUT_THRESHOLD', 5)) # 登入失敗幾次後鎖定帳號	
    LOGIN_ATTEMPT_LOCKOUT_DURATION_MINUTES = int(os.getenv('LOGIN_ATTEMPT_LOCKOUT_DURATION_MINUTES', 15)) # 鎖定時間
    
    # 密碼重設 Token 過期時間（小時）
    PASSWORD_RESET_TOKEN_EXPIRES_HOURS = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRES_HOURS', 1))
    
    # ============================================
    # 維護模式
    # ============================================
    # 因為app.py沒有寫維護模式, 所以這邊註解起來
    # MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'
    
    # ============================================
    # 設定驗證
    # ============================================
    """
    類型	                能存取什麼	用途
    實例方法	            self（物件的資料）	操作單個物件的資料
    靜態方法@staticmethod	什麼都不能存取	工具函數，跟物件無關
    類別方法@classmethod	cls（類別本身）	操作類別的資料，或建立物件
    """
    @staticmethod # 固定寫法
    def validate():
        """
        驗證設定是否正確
        
        【什麼時候執行？】
        應用程式啟動時應該呼叫這個方法，
        確保所有必要的設定都有正確設定。
        
        【檢查項目】
        1. 生產環境是否有設定必要的環境變數
        2. 是否還在使用預設的 SECRET_KEY

        【情況	            用哪個】
        正常回傳結果	    return
        錯誤但可以處理	    return None 或回傳錯誤碼
        嚴重錯誤，必須停止	 raise
        """
        # 生產環境必須設定的環境變數
        required_in_production = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL'
        ]
        
        # 只在生產環境檢查
        # 開發環境用預設值就能跑, 測試用假資料也能跑
        if Config.ENV == 'production':
            missing = [] # 空list用來存缺少的環境變數

            # 
            for key in required_in_production:
                if not os.getenv(key): # 如果這個環境變數不存在,如果全部都有設定的話, missing 就會是空的
                    missing.append(key) # 就把這個環境變數加入到list中
            
            # 如果有缺少的環境變數，拋出錯誤
            if missing: # 如果 missing 清單「不是空的」（有缺少的）
                # raise：拋出錯誤，程式停止
                raise ValueError(
                    f"Missing required environment variables in production: {', '.join(missing)}"
                )
            
            # 檢查是否使用預設的 secret key（這是不安全的！）
            if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
                raise ValueError("You must set a strong SECRET_KEY in production!")


# ============================================
# 環境特定設定
# (Config) = 繼承自Config class,繼承 Config 的所有設定，只覆蓋需要改變的部分
# ============================================

class DevelopmentConfig(Config):
    """
    開發環境設定. 加了除錯功能

    【特點】
    - DEBUG 模式開啟
    - SQL 查詢會印出來（方便除錯）
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 印出所有 SQL 查詢


class ProductionConfig(Config):
    """
    生產環境設定. 加了安全性功能
    
    【特點】
    - DEBUG 模式關閉
    - 強制使用 HTTPS
    - 更嚴格的安全設定
    
    SSL: Secure Sockets Layer
    TLS: Transport Layer Security, 新版加密協議, SSL升級版 
    HTTPS：HTTP + 安全層（SSL/TLS）
    - 加密:資料傳輸時加密
    - 身份驗證:確保資料來源可靠
    - 資料完整性:防止資料被篡改

    """
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # 強制使用 HTTPS


class TestingConfig(Config):
    """
    測試環境設定. 加了測試功能
    
    Flask-WTF = (Flask 的表單擴展套件）
    CSRF = Cross-Site Request Forgery（跨站請求偽造, 偽造用戶請求）
    XSS = Cross-Site Scripting（跨站腳本攻擊, 注入惡意 JavaScript, 危險程度更高）
    【特點】
    - 使用記憶體資料庫（每次測試都是乾淨的）
    - 關閉 CSRF 保護（方便測試）
    """
    TESTING = True # 使用記憶體資料庫（每次測試都是乾淨的）
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 記憶體資料庫
    # CSRF未使用，專案用 JWT放在localstorage 所以不需要另外寫CSRF
    # WTF_CSRF_ENABLED = False


# ============================================
# 設定dict
# ============================================

"""
config dict讓我們可以根據環境名稱取得對應的設定類別

使用方式：
config_class = config.get('development')  # 取得 DevelopmentConfig
config_class = config.get('production')   # 取得 ProductionConfig
"""
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    取得當前環境的設定類別
    
    【使用方式】
    from config import get_config
    
    config_class = get_config()
    app.config.from_object(config_class)
    
    【環境判斷】
    根據 FLASK_ENV 環境變數決定使用哪個設定
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
