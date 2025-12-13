"""
============================================
token_blacklist.py - JWT Token 黑名單管理
============================================

【這個檔案要解決什麼問題？】

JWT (JSON Web Token) 有一個設計特性：它是「無狀態」的。
這意味著一旦 Token 被簽發，伺服器就無法「撤銷」它。

這帶來一個問題：如果使用者登出了，但 Token 還沒過期，
理論上這個 Token 還是可以繼續使用！

【問題情境說明】
┌──────────────────────────────────────────────────────────────┐
│  時間線                                                        │
│  ─────────────────────────────────────────────────────────    │
│  09:00  使用者登入，取得 Token（有效期 24 小時）                   │
│  10:00  使用者登出                                              │
│  10:05  駭客偷到 Token                                          │
│  10:06  駭客用 Token 存取系統 → 成功！（Token 還沒過期）           │
│                                                                │
│  問題：使用者已經登出了，為什麼駭客還能用？                        │
│  答案：因為 JWT 是無狀態的，伺服器不知道 Token 已經「無效」         │
└──────────────────────────────────────────────────────────────┘

【解決方案：Token 黑名單】
我們需要一個地方來記錄「哪些 Token 已經被撤銷」。
每次收到請求時，除了驗證 Token 是否有效，還要檢查它是否在黑名單中。

┌──────────────────────────────────────────────────────────────┐
│  有了 Token 黑名單之後                                          │
│  ─────────────────────────────────────────────────────────    │
│  09:00  使用者登入，取得 Token                                   │
│  10:00  使用者登出 → Token 加入黑名單 ✓                          │
│  10:05  駭客偷到 Token                                          │
│  10:06  駭客用 Token 存取系統                                    │
│         → 檢查黑名單 → Token 在黑名單中 → 拒絕！✓                │
└──────────────────────────────────────────────────────────────┘

【為什麼需要這個模組？】
1. 安全性：確保登出後 Token 真的失效
2. 強制登出：管理員可以強制讓某個使用者的 Token 失效
3. 密碼變更：密碼變更後，舊的 Token 應該失效

【儲存方式選擇】
- 開發環境：使用記憶體儲存（程式重啟會清空，但簡單方便）
- 生產環境：使用 Redis（持久化、可分散式部署）

【使用方式】
1. 登出時將 Token 加入黑名單：
   from core import revoke_token
   revoke_token(jwt_payload['jti'])

2. 每次請求時自動檢查（在 app.py 中設定）：
   @jwt.token_in_blocklist_loader
   def check_if_token_in_blocklist(jwt_header, jwt_payload):
       return check_if_token_revoked(jwt_header, jwt_payload)
"""

# ============================================
# 導入模組區域
# ============================================

from datetime import datetime, timedelta
# datetime: Python 處理日期時間的模組
#   datetime.utcnow(): 取得目前的 UTC 時間
#   為什麼用 UTC？因為伺服器可能在不同時區，用 UTC 統一
#
# timedelta: 表示時間差的類別
#   例如：timedelta(hours=24) 表示 24 小時
#   可以做時間運算：datetime.utcnow() + timedelta(hours=1) = 一小時後

from typing import Optional
# Optional 是型別提示，表示這個值可能是某個型別或 None
# Optional[timedelta] = Union[timedelta, None]

from flask import current_app
# current_app 是 Flask 的特殊變數
# 它可以在任何地方取得目前運行中的 Flask 應用程式實例
#
# 【為什麼需要它？】
# 在 Flask 中，應用程式設定（如 Redis 連線）存在 app 物件中
# 但這個模組不一定知道 app 是什麼
# current_app 讓我們可以在需要時動態取得 app

import logging
# Python 標準日誌模組

# 建立這個模組的 logger
logger = logging.getLogger(__name__)


# ============================================
# TokenBlacklist 類別
# ============================================

class TokenBlacklist:
    """
    Token 黑名單服務

    這是一個「類別方法」(Class Method) 設計的類別。
    不需要建立實例，直接呼叫類別方法即可。

    【為什麼用類別方法而不是一般函數？】
    1. 狀態共享：_memory_store 是類別變數，所有方法共用
    2. 組織性：相關的功能都放在同一個類別中
    3. 擴展性：未來可以繼承這個類別來擴展功能

    【使用範例】
    # 加入黑名單
    TokenBlacklist.add('token-jti-12345')

    # 檢查是否在黑名單
    is_blocked = TokenBlacklist.is_blacklisted('token-jti-12345')

    【支援的儲存方式】
    1. 記憶體（開發環境）：使用 Python dict，快速但不持久
    2. Redis（生產環境）：持久化、支援分散式部署、有自動過期功能
    """

    # ----------------------------------------
    # 類別變數（Class Variable）
    # ----------------------------------------
    # 這個變數屬於「類別」而不是「實例」
    # 所有使用 TokenBlacklist 的地方都會共用這個 dict
    #
    # 儲存格式：{jti: expires_at}
    # 例如：{'abc123': datetime(2024, 1, 15, 12, 0, 0)}
    _memory_store: dict = {}

    @classmethod
    def add(cls, jti: str, expires_delta: Optional[timedelta] = None) -> bool:
        """
        將 Token 加入黑名單

        【什麼是 JTI？】
        JTI (JWT ID) 是每個 JWT Token 的唯一識別碼。
        當我們建立 Token 時，Flask-JWT-Extended 會自動產生一個 JTI。

        JWT Token 的結構（簡化版）：
        {
            "sub": "user123",       # Subject - 使用者 ID
            "jti": "abc-123-xyz",   # JWT ID - 這個 Token 的唯一識別碼
            "exp": 1705320000,      # Expiration - 過期時間
            ...
        }

        我們不儲存整個 Token，只儲存 JTI，這樣更節省空間。

        【參數說明】
        Args:
            jti: str
                JWT 的唯一識別碼
                這個值來自 JWT Token 的 payload

            expires_delta: Optional[timedelta]
                這個黑名單記錄要保留多久
                - 如果不指定，預設 24 小時
                - 這個時間應該 >= Token 的有效期，確保 Token 過期前都在黑名單中
                - 之後可以自動清理，節省儲存空間

        【回傳值說明】
        Returns:
            bool: 是否成功加入黑名單（目前總是回傳 True）

        【使用範例】
        Example:
            # 登出時撤銷 Token
            from flask_jwt_extended import get_jwt
            jwt_data = get_jwt()
            TokenBlacklist.add(jwt_data['jti'])

            # 指定保留時間
            TokenBlacklist.add(jti, expires_delta=timedelta(hours=48))
        """
        # 如果沒指定過期時間，預設 24 小時
        # 這個時間應該大於 access token 的有效期
        # 假設 access token 有效期是 15 分鐘，24 小時絕對夠用
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        # 計算這筆黑名單記錄的過期時間
        # 過期後可以安全地刪除這筆記錄，因為 Token 本身也過期了
        expires_at = datetime.utcnow() + expires_delta

        try:
            # ----------------------------------------
            # 嘗試使用 Redis（生產環境優先）
            # ----------------------------------------
            redis_client = cls._get_redis_client()
            if redis_client:
                # Redis 的 key 使用前綴，方便管理和查詢
                # 例如：token_blacklist:abc-123-xyz
                key = f"token_blacklist:{jti}"

                # setex: SET with EXpiration
                # 這個命令會設定值，並在指定時間後自動刪除
                # 參數：(key, 過期時間, 值)
                #
                # Redis 會自動處理過期記錄的清理，我們不用管！
                redis_client.setex(
                    key,
                    expires_delta,  # Redis 會自動處理 timedelta
                    datetime.utcnow().isoformat()  # 儲存加入黑名單的時間（用於除錯）
                )

                # 只顯示 JTI 的前 8 個字元，避免日誌太長
                logger.debug(f"Token {jti[:8]}... added to Redis blacklist")
                return True

        except Exception as e:
            # Redis 不可用時，退回到記憶體儲存
            # 這個錯誤不是很嚴重，用 warning 級別
            logger.warning(f"Redis not available, using memory store: {e}")

        # ----------------------------------------
        # 使用記憶體儲存（開發環境或 Redis 不可用時）
        # ----------------------------------------
        # 直接存入 class 變數 _memory_store
        cls._memory_store[jti] = expires_at

        # 順便清理已過期的記錄，避免記憶體無限增長
        cls._cleanup_expired()

        logger.debug(f"Token {jti[:8]}... added to memory blacklist")
        return True

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """
        檢查 Token 是否在黑名單中

        這個方法會在每次 API 請求時被呼叫。
        Flask-JWT-Extended 會在驗證 Token 後呼叫我們註冊的回調函數。

        【檢查流程】
        1. 收到 API 請求
        2. Flask-JWT-Extended 驗證 Token 簽名
        3. 呼叫 token_in_blocklist_loader 回調（就是用這個方法）
        4. 如果回傳 True，拒絕請求（回傳 401 或 403）
        5. 如果回傳 False，繼續處理請求

        【參數說明】
        Args:
            jti: str - JWT 的唯一識別碼

        【回傳值說明】
        Returns:
            bool:
                - True: Token 在黑名單中（已被撤銷）
                - False: Token 不在黑名單中（可以使用）

        【效能考量】
        這個方法在每次 API 請求都會被呼叫，必須非常快：
        - Redis: O(1) 查詢，非常快
        - 記憶體: O(1) dict 查詢，更快

        【使用範例】
        Example:
            # 在 app.py 中註冊
            @jwt.token_in_blocklist_loader
            def check_if_token_in_blocklist(jwt_header, jwt_payload):
                jti = jwt_payload.get("jti")
                return TokenBlacklist.is_blacklisted(jti)
        """
        try:
            # ----------------------------------------
            # 嘗試從 Redis 檢查
            # ----------------------------------------
            redis_client = cls._get_redis_client()
            if redis_client:
                key = f"token_blacklist:{jti}"
                # exists() 回傳符合條件的 key 數量
                # 如果 > 0 表示存在
                return redis_client.exists(key) > 0

        except Exception:
            # Redis 錯誤時，靜默失敗並檢查記憶體
            # 這裡用 pass 是因為我們有備用方案（記憶體儲存）
            pass

        # ----------------------------------------
        # 從記憶體檢查
        # ----------------------------------------
        if jti in cls._memory_store:
            # 檢查這筆記錄是否已過期
            if cls._memory_store[jti] > datetime.utcnow():
                # 還沒過期，Token 在黑名單中
                return True
            else:
                # 已過期，從記憶體中移除
                # 這是一種「惰性刪除」(Lazy Deletion) 策略
                # 只有在存取時才檢查和刪除過期記錄
                del cls._memory_store[jti]

        # Token 不在黑名單中
        return False

    @classmethod
    def remove(cls, jti: str) -> bool:
        """
        從黑名單中移除 Token

        【什麼時候需要移除？】
        通常不需要！讓 Token 記錄自動過期即可。

        可能的使用情境：
        - 管理員誤操作，需要恢復使用者的 Token
        - 測試環境需要清理

        【安全警告】
        移除黑名單記錄會讓被撤銷的 Token 重新生效！
        除非你非常確定要這樣做，否則不要使用這個方法。

        【參數說明】
        Args:
            jti: str - 要移除的 Token JTI

        【回傳值說明】
        Returns:
            bool: 是否成功移除（如果本來就不存在，回傳 False）
        """
        try:
            redis_client = cls._get_redis_client()
            if redis_client:
                key = f"token_blacklist:{jti}"
                # delete() 刪除指定的 key
                redis_client.delete(key)
                return True
        except Exception:
            pass

        # 從記憶體移除
        if jti in cls._memory_store:
            del cls._memory_store[jti]
            return True

        return False

    @classmethod
    def _get_redis_client(cls):
        """
        取得 Redis 客戶端（如果可用）

        這是一個「私有方法」（前綴 _），表示只在類別內部使用。
        外部程式碼不應該直接呼叫這個方法。

        【為什麼需要這個方法？】
        Redis 客戶端的取得邏輯在多個地方都會用到。
        把它抽出來成為獨立方法，避免重複程式碼。

        【Flask Extensions 機制說明】
        Flask 的擴展（Extension）通常會把自己的物件存在 app.extensions 中。
        例如：
        - app.extensions['redis'] = Redis 客戶端
        - app.extensions['sqlalchemy'] = SQLAlchemy 實例

        我們可以透過 current_app.extensions 來存取這些擴展。

        【回傳值說明】
        Returns:
            Redis client 或 None:
                - 如果 Redis 可用，回傳 Redis 客戶端物件
                - 如果 Redis 不可用或不在 Flask context 中，回傳 None
        """
        try:
            # hasattr: 檢查物件是否有某個屬性
            # 確保 current_app 有 extensions 屬性，且 redis 在其中
            if hasattr(current_app, 'extensions') and 'redis' in current_app.extensions:
                return current_app.extensions['redis']
        except RuntimeError:
            # RuntimeError: Working outside of application context
            # 這個錯誤發生在沒有 Flask app context 的情況下
            # 例如：在單元測試中、在背景任務中
            pass
        return None

    @classmethod
    def _cleanup_expired(cls):
        """
        清理過期的 Token（僅記憶體模式）

        【為什麼需要清理？】
        記憶體儲存不像 Redis 有自動過期功能。
        如果不清理，_memory_store 會一直增長，最終耗盡記憶體。

        【清理策略】
        我們使用「惰性清理」策略：
        - 不是定時清理（那需要額外的執行緒）
        - 而是在新增記錄時順便清理

        這樣的好處是簡單，不需要複雜的排程機制。
        缺點是如果系統閒置很久，過期記錄不會被清理。
        但對於開發環境來說，這不是問題。

        【Redis 不需要這個】
        Redis 的 setex 命令會自動處理過期記錄。
        Redis 在背景有專門的執行緒清理過期的 key。
        """
        now = datetime.utcnow()

        # 找出所有已過期的 JTI
        # 使用 list comprehension 建立要刪除的清單
        #
        # 為什麼不直接在迭代時刪除？
        # 因為在迭代 dict 時修改它會導致 RuntimeError
        expired_keys = [
            jti for jti, expires_at in cls._memory_store.items()
            if expires_at <= now  # 過期時間 <= 現在 = 已過期
        ]

        # 刪除過期的記錄
        for jti in expired_keys:
            del cls._memory_store[jti]

        # 如果有清理，記錄到日誌
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired tokens from memory blacklist")

    @classmethod
    def get_blacklist_count(cls) -> int:
        """
        取得黑名單中的 Token 數量

        這個方法主要用於監控和除錯：
        - 健康檢查 API 可以顯示黑名單大小
        - 管理介面可以顯示統計資訊

        【效能警告】
        在 Redis 中使用 keys() 命令來計數。
        當黑名單很大時（數萬筆以上），這個操作可能會很慢。
        生產環境中如果需要頻繁查詢數量，應該使用其他方式：
        - 維護一個計數器
        - 使用 Redis 的 SCAN 命令分批查詢

        【回傳值說明】
        Returns:
            int: 黑名單中的 Token 數量
        """
        try:
            redis_client = cls._get_redis_client()
            if redis_client:
                # keys() 回傳所有符合 pattern 的 key
                # "token_blacklist:*" 匹配所有以 token_blacklist: 開頭的 key
                #
                # 注意：在大型生產環境中，keys() 可能會阻塞 Redis
                # 更好的做法是使用 SCAN 命令
                keys = redis_client.keys("token_blacklist:*")
                return len(keys)
        except Exception:
            pass

        # 先清理過期記錄，再計數
        cls._cleanup_expired()
        return len(cls._memory_store)


# ============================================
# Flask-JWT-Extended 整合函數
# ============================================
#
# 這些函數是給 Flask-JWT-Extended 使用的回調函數。
# 它們作為「橋樑」，連接 Flask-JWT-Extended 和我們的 TokenBlacklist。
#

def check_if_token_revoked(jwt_header, jwt_payload) -> bool:
    """
    Flask-JWT-Extended 的 Token 撤銷檢查回調函數

    【這個函數如何被使用？】
    在 app.py 中，我們會這樣註冊：

    from core import check_if_token_revoked

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return check_if_token_revoked(jwt_header, jwt_payload)

    之後，每次有人用 Token 發送請求時：
    1. Flask-JWT-Extended 驗證 Token 的簽名和有效期
    2. 呼叫這個回調函數檢查 Token 是否被撤銷
    3. 如果回傳 True，請求被拒絕（401 Unauthorized）
    4. 如果回傳 False，繼續處理請求

    【參數說明】
    Args:
        jwt_header: dict
            JWT 的 header 部分，包含：
            - alg: 簽名演算法，如 "HS256"
            - typ: Token 類型，通常是 "JWT"
            我們通常不需要用到 header

        jwt_payload: dict
            JWT 的 payload 部分，包含：
            - sub: Subject，使用者 ID
            - jti: JWT ID，Token 的唯一識別碼
            - exp: Expiration，過期時間（Unix timestamp）
            - iat: Issued At，簽發時間
            - type: Token 類型，"access" 或 "refresh"
            - fresh: 是否為「新鮮」的 Token（剛登入）

    【回傳值說明】
    Returns:
        bool:
            - True: Token 已被撤銷，拒絕請求
            - False: Token 有效，允許請求

    【JWT 結構視覺化】
    一個 JWT Token 長這樣（用 . 分隔三個部分）：

    eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.abc123xyz
    ─────────────────────┬─────────────────────┬─────────
          Header          │      Payload        │ Signature
          (Base64)        │      (Base64)       │ (Base64)

    解碼後：
    Header:  {"alg": "HS256", "typ": "JWT"}
    Payload: {"sub": "1234", "jti": "abc-xyz", "exp": 1705320000, ...}
    """
    # 從 payload 取得 JTI
    # 使用 .get() 而不是 [] 存取，避免 key 不存在時拋出例外
    jti = jwt_payload.get("jti")

    # 如果沒有 JTI（不太可能發生，因為 Flask-JWT-Extended 會自動產生）
    # 回傳 False 讓請求繼續，不要因為這個意外情況阻擋使用者
    if jti is None:
        return False

    # 檢查是否在黑名單中
    return TokenBlacklist.is_blacklisted(jti)


def revoke_token(jti: str, expires_delta: Optional[timedelta] = None) -> bool:
    """
    撤銷 Token（便利函數）

    這個函數是 TokenBlacklist.add() 的簡單包裝。
    讓程式碼更易讀：

    # 不用記住類別名稱和方法
    revoke_token(jti)

    # 比起
    TokenBlacklist.add(jti)

    【使用範例】
    Example:
        # 在登出 API 中使用
        @app.route('/auth/logout', methods=['POST'])
        @jwt_required()
        def logout():
            # 取得目前的 JWT 資訊
            jwt_data = get_jwt()

            # 撤銷這個 Token
            revoke_token(jwt_data['jti'])

            return jsonify({'message': 'Logged out successfully'})

    【參數說明】
    Args:
        jti: str - JWT 的唯一識別碼
        expires_delta: Optional[timedelta] - 黑名單記錄保留時間

    【回傳值說明】
    Returns:
        bool: 是否成功撤銷
    """
    return TokenBlacklist.add(jti, expires_delta)


# ============================================
# 補充說明：為什麼不直接讓 Token 立即過期？
# ============================================
#
# 【問題】
# 有人可能會問：為什麼不在登出時修改 Token 的過期時間？
#
# 【答案】
# 因為 JWT 是「自包含」的（self-contained）。
# Token 的內容（包括過期時間）在簽發時就確定了。
# 如果我們修改 Token 的內容，簽名就會失效。
# 沒有私鑰的話，我們無法產生新的有效簽名。
#
# 即使我們有私鑰，已經發出去的 Token 也無法被修改。
# Token 已經在客戶端（瀏覽器）了，我們只能「不認可」它。
#
# 這就是為什麼需要 Token 黑名單。
#
# ============================================
# Token 黑名單的替代方案
# ============================================
#
# 1. 短效期 Token + Refresh Token
#    - Access Token 設定很短的有效期（如 5 分鐘）
#    - Refresh Token 用來獲取新的 Access Token
#    - 登出時只需要撤銷 Refresh Token
#    - 優點：黑名單較小（只有 Refresh Token）
#    - 缺點：更頻繁的 Token 更新
#
# 2. Token 版本號
#    - 在使用者資料中存一個 Token 版本號
#    - Token 中包含這個版本號
#    - 登出時增加版本號
#    - 驗證時檢查版本號是否匹配
#    - 優點：不需要黑名單
#    - 缺點：需要查詢資料庫
#
# 3. Session-based Authentication
#    - 完全不用 JWT，用傳統的 Session
#    - 登出時刪除 Session
#    - 優點：簡單直接
#    - 缺點：不適合分散式系統、不是無狀態的
#
# ============================================
# 安全考量
# ============================================
#
# 1. 黑名單大小
#    如果系統有很多使用者頻繁登出，黑名單可能會很大。
#    確保設定合適的過期時間，讓記錄能夠自動清理。
#
# 2. 分散式環境
#    如果有多台伺服器，必須使用 Redis（或其他共享儲存）。
#    否則在 A 伺服器登出，B 伺服器不會知道。
#
# 3. 記憶體儲存的風險
#    記憶體儲存在程式重啟時會清空。
#    這意味著重啟後，之前撤銷的 Token 會「復活」。
#    生產環境務必使用 Redis。
