"""
============================================
utils/validators.py - 通用驗證函數
============================================

【這個檔案的目的】
提供統一的輸入驗證功能，確保使用者輸入的資料符合預期格式。

【為什麼需要輸入驗證？】
1. 安全性：防止惡意輸入（如 SQL 注入、XSS 攻擊）
2. 資料完整性：確保存入資料庫的資料格式正確
3. 使用者體驗：提供清楚的錯誤訊息，幫助使用者修正輸入

【驗證的基本原則】
1. 永遠不要信任使用者輸入
   即使前端已經驗證過，後端也要再驗證一次。
   前端驗證可以被繞過（直接呼叫 API）。

2. 早期失敗（Fail Fast）
   在資料進入系統之前就驗證。
   不要等到存入資料庫時才發現問題。

3. 明確的錯誤訊息
   告訴使用者哪裡錯了、該怎麼修正。
   不要只說「驗證失敗」。

【這個模組提供的功能】
- validate_request_data: 使用 Marshmallow Schema 驗證請求資料
- validate_password_strength: 驗證密碼強度
- parse_date / parse_due_date: 解析日期字串
- validate_email: 驗證電子郵件格式
- validate_pagination: 驗證分頁參數

【使用方式】
from utils.validators import validate_request_data, validate_password_strength

# 驗證請求資料
is_valid, result = validate_request_data(CreateUserSchema, request.get_json())
if not is_valid:
    return jsonify({'error': 'Validation failed', 'details': result}), 400

# 驗證密碼強度
is_valid, error = validate_password_strength(password)
if not is_valid:
    return jsonify({'error': error}), 400
"""

# ============================================
# 導入模組區域
# ============================================

from marshmallow import Schema, ValidationError
# Marshmallow 是一個強大的物件序列化/反序列化庫
#
# 【什麼是序列化？】
# - 序列化 (Serialize): 把 Python 物件轉成 JSON（給前端）
# - 反序列化 (Deserialize): 把 JSON 轉成 Python 物件（給後端用）
#
# 【Marshmallow 能做什麼？】
# 1. 驗證：檢查輸入資料是否符合定義的規則
# 2. 轉換：把字串轉成數字、日期等適當的型別
# 3. 過濾：只允許特定的欄位
#
# 【基本使用範例】
# class UserSchema(Schema):
#     name = fields.Str(required=True, validate=Length(min=1, max=100))
#     email = fields.Email(required=True)
#     age = fields.Int(validate=Range(min=0, max=150))
#
# schema = UserSchema()
# result = schema.load({"name": "Alice", "email": "alice@example.com"})
# # 如果驗證失敗，會拋出 ValidationError

from datetime import datetime
# Python 標準的日期時間處理模組
# datetime.strptime(): 把字串解析成 datetime 物件
# datetime.utcnow(): 取得目前 UTC 時間

from typing import Tuple, Union, Optional, Any
# Python 型別提示（Type Hints）
#
# 【為什麼要用型別提示？】
# 1. 自動補全：IDE 可以根據型別提供更好的建議
# 2. 錯誤檢測：可以在執行前發現型別錯誤
# 3. 文件化：讓其他開發者一眼就知道參數和回傳值的型別
#
# 【常用的型別提示】
# - Tuple[int, str]: 包含整數和字串的元組
# - Union[str, int]: 可以是字串或整數
# - Optional[str]: 可以是字串或 None（等於 Union[str, None]）
# - Any: 任何型別

from flask import current_app
# Flask 的 current_app 代理物件
# 用於存取應用程式的設定（如密碼強度規則）

import logging
# Python 標準日誌模組

# 建立這個模組的 logger
logger = logging.getLogger(__name__)


# ============================================
# Marshmallow Schema 驗證
# ============================================

def validate_request_data(
    schema_class: type,
    data: dict,
    partial: bool = False
) -> Tuple[bool, Union[dict, dict]]:
    """
    使用 Marshmallow Schema 驗證請求資料

    這是一個通用的驗證函數，可以搭配任何 Marshmallow Schema 使用。
    它統一了驗證的呼叫方式和回傳格式。

    【為什麼需要這個函數？】
    直接使用 Schema.load() 會拋出例外，需要 try-catch。
    這個函數把例外轉換成回傳值，讓程式碼更簡潔。

    不用這個函數：
    ```python
    schema = CreateUserSchema()
    try:
        validated_data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': err.messages}), 400
    ```

    使用這個函數：
    ```python
    is_valid, result = validate_request_data(CreateUserSchema, request.get_json())
    if not is_valid:
        return jsonify({'error': result}), 400
    ```

    【參數說明】
    Args:
        schema_class: type
            Marshmallow Schema 的「類別」（不是實例）
            例如：CreateUserSchema（不是 CreateUserSchema()）
            為什麼傳類別？因為這樣更靈活，函數內部會自動建立實例

        data: dict
            要驗證的資料字典
            通常來自 request.get_json()

        partial: bool = False
            是否允許部分欄位
            - False（預設）：所有 required 欄位都必須存在
            - True：只驗證有提供的欄位，適合 PATCH 請求

            【什麼時候用 partial=True？】
            PATCH 請求只更新部分欄位，使用者不需要提供所有資料
            例如：只更新使用者的 email，不需要提供 name

    【回傳值說明】
    Returns:
        Tuple[bool, Union[dict, dict]]:
        回傳一個包含兩個值的元組

        成功時：(True, validated_data)
        - validated_data 是經過驗證和轉換的資料
        - 欄位已經被轉換成正確的型別（如字串日期轉成 datetime）
        - 可以安全地使用這些資料

        失敗時：(False, error_messages)
        - error_messages 是欄位到錯誤訊息的字典
        - 例如：{'email': ['Invalid email format'], 'name': ['Missing data']}
        - 可以直接回傳給前端顯示

    【使用範例】
    Example:
        from utils.validators import validate_request_data
        from marshmallow import Schema, fields

        # 定義 Schema
        class CreateUserSchema(Schema):
            name = fields.Str(required=True)
            email = fields.Email(required=True)

        # 在 API 中使用
        @app.route('/users', methods=['POST'])
        def create_user():
            is_valid, result = validate_request_data(
                CreateUserSchema,
                request.get_json()
            )
            if not is_valid:
                return jsonify({'error': 'Validation failed', 'details': result}), 400

            # result 現在包含驗證後的資料
            user = User(name=result['name'], email=result['email'])
            db.session.add(user)
            db.session.commit()
            return jsonify({'id': user.id}), 201
    """
    # 建立 Schema 實例
    # 為什麼每次都建立新實例？因為 Schema 可能有狀態（context 等）
    schema = schema_class()

    try:
        # schema.load() 會：
        # 1. 驗證資料是否符合定義的規則
        # 2. 轉換資料型別（如字串轉數字）
        # 3. 如果有錯誤，拋出 ValidationError
        #
        # partial=True 時，只驗證有提供的欄位
        validated_data = schema.load(data, partial=partial)
        return True, validated_data

    except ValidationError as err:
        # err.messages 是欄位到錯誤訊息的字典
        # 例如：{'email': ['Not a valid email address.']}
        return False, err.messages


# ============================================
# 密碼強度驗證
# ============================================

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    根據應用程式配置驗證密碼強度

    這個函數會檢查密碼是否符合設定的強度要求。
    強度要求可以在 config.py 中設定，讓每個部署環境可以有不同的規則。

    【為什麼密碼強度很重要？】
    弱密碼是最常見的安全漏洞之一：
    - '123456' 可以在 1 秒內被暴力破解
    - 'password' 在常見密碼字典中
    - 短密碼容易被猜到

    【設定項目說明】（在 config.py 中設定）
    - PASSWORD_MIN_LENGTH: 最小長度（預設 8）
      8 個字元是 NIST 建議的最低標準

    - PASSWORD_REQUIRE_UPPERCASE: 是否需要大寫字母（預設 False）
      混合大小寫可以增加密碼複雜度

    - PASSWORD_REQUIRE_NUMBERS: 是否需要數字（預設 False）
      加入數字可以防止純字母的字典攻擊

    - PASSWORD_REQUIRE_SPECIAL: 是否需要特殊字元（預設 False）
      特殊字元大幅增加暴力破解的難度

    【參數說明】
    Args:
        password: str
            要驗證的密碼明文
            注意：這是明文密碼，驗證後要立即雜湊處理，不要儲存明文！

    【回傳值說明】
    Returns:
        Tuple[bool, str]:
        - (True, ''): 密碼符合強度要求
        - (False, error_message): 密碼不符合要求，附帶錯誤訊息

    【使用範例】
    Example:
        # 在註冊 API 中使用
        @app.route('/register', methods=['POST'])
        def register():
            password = request.json.get('password')

            is_valid, error = validate_password_strength(password)
            if not is_valid:
                return jsonify({'error': error}), 400

            # 密碼符合強度要求，繼續處理
            # 記得要雜湊處理！
            hashed = generate_password_hash(password)
            user = User(password_hash=hashed)
    """
    try:
        # 從 Flask 應用程式設定中讀取密碼規則
        # current_app.config 是一個字典，包含所有設定值
        # .get(key, default) 在 key 不存在時回傳 default 值
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
        require_upper = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', False)
        require_numbers = current_app.config.get('PASSWORD_REQUIRE_NUMBERS', False)
        require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', False)

    except RuntimeError:
        # RuntimeError: Working outside of application context
        # 這個錯誤發生在沒有 Flask app context 的情況下
        # 例如：單元測試、背景任務
        # 此時使用預設值
        min_length = 8
        require_upper = False
        require_numbers = False
        require_special = False

    # ----------------------------------------
    # 檢查長度
    # ----------------------------------------
    if len(password) < min_length:
        return False, f'Password must be at least {min_length} characters'

    # ----------------------------------------
    # 檢查大寫字母
    # ----------------------------------------
    # any() 函數：只要有一個元素為 True，就回傳 True
    # c.isupper() 檢查字元 c 是否為大寫字母
    #
    # 這個寫法等於：
    # has_upper = False
    # for c in password:
    #     if c.isupper():
    #         has_upper = True
    #         break
    if require_upper and not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter'

    # ----------------------------------------
    # 檢查數字
    # ----------------------------------------
    # c.isdigit() 檢查字元 c 是否為數字 (0-9)
    if require_numbers and not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number'

    # ----------------------------------------
    # 檢查特殊字元
    # ----------------------------------------
    # 使用 in 運算子檢查字元是否在特殊字元集合中
    # 這個集合包含常見的鍵盤上的特殊字元
    if require_special and not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return False, 'Password must contain at least one special character'

    # 所有檢查都通過
    return True, ''


# ============================================
# 日期解析函數
# ============================================

def parse_date(
    date_string: str,
    formats: Optional[list] = None
) -> Tuple[bool, Union[datetime, str]]:
    """
    安全地解析日期字串

    將各種格式的日期字串轉換成 Python datetime 物件。
    支援多種常見的日期格式，包括 ISO 8601。

    【為什麼需要這個函數？】
    前端可能會傳來各種格式的日期：
    - '2024-01-15' (只有日期)
    - '2024-01-15T10:30:00Z' (ISO 8601 帶時區)
    - '2024-01-15T10:30:00.123Z' (ISO 8601 帶毫秒)
    - '2024-01-15 10:30:00' (空格分隔)

    這個函數會嘗試多種格式，找到能成功解析的那一個。

    【什麼是 ISO 8601？】
    ISO 8601 是國際標準的日期時間格式：
    - 格式：YYYY-MM-DDTHH:mm:ss.sssZ
    - 例如：2024-01-15T10:30:00.000Z
    - T: 日期和時間的分隔符
    - Z: 表示 UTC 時區（Zulu time）
    - 優點：沒有歧義、排序友好、全球通用

    【參數說明】
    Args:
        date_string: str
            要解析的日期字串
            例如：'2024-01-15' 或 '2024-01-15T10:30:00Z'

        formats: Optional[list] = None
            可接受的日期格式列表
            如果不指定，使用預設格式列表

            格式字串使用 strptime 的格式符號：
            - %Y: 四位數年份 (2024)
            - %m: 兩位數月份 (01-12)
            - %d: 兩位數日期 (01-31)
            - %H: 兩位數小時 (00-23)
            - %M: 兩位數分鐘 (00-59)
            - %S: 兩位數秒數 (00-59)
            - %f: 微秒 (000000-999999)

    【回傳值說明】
    Returns:
        Tuple[bool, Union[datetime, str]]:
        - (True, datetime_object): 解析成功，回傳 datetime 物件
        - (False, error_message): 解析失敗，回傳錯誤訊息

    【使用範例】
    Example:
        # 解析 ISO 8601 格式
        success, result = parse_date('2024-01-15T10:30:00Z')
        if success:
            print(result)  # datetime(2024, 1, 15, 10, 30, 0)

        # 解析只有日期
        success, result = parse_date('2024-01-15')
        if success:
            print(result)  # datetime(2024, 1, 15, 0, 0, 0)

        # 解析失敗
        success, result = parse_date('not a date')
        if not success:
            print(result)  # 'Invalid date format: not a date'
    """
    # 空字串直接回傳錯誤
    if not date_string:
        return False, 'Date string is empty'

    # 如果沒有指定格式，使用預設的格式列表
    # 按照可能性從高到低排列，提高效率
    if formats is None:
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO 8601 完整格式（帶毫秒和 Z）
            '%Y-%m-%dT%H:%M:%SZ',      # ISO 8601（不帶毫秒，有 Z）
            '%Y-%m-%dT%H:%M:%S',       # ISO 8601（不帶 Z）
            '%Y-%m-%d',                 # 只有日期
        ]

    # ----------------------------------------
    # 正規化日期字串
    # ----------------------------------------
    # 處理一些常見的變體，讓後續解析更容易
    #
    # replace('+00:00', 'Z'): 把 +00:00 時區轉成 Z
    #   '+00:00' 和 'Z' 都表示 UTC，但 strptime 不支援 +00:00
    #
    # replace(' ', 'T'): 把空格分隔轉成 T 分隔
    #   有些系統會用空格而不是 T 分隔日期和時間
    normalized = date_string.replace('+00:00', 'Z').replace(' ', 'T')

    # ----------------------------------------
    # 嘗試各種格式
    # ----------------------------------------
    for fmt in formats:
        try:
            # strptime: string parse time
            # 把字串按照指定格式解析成 datetime
            #
            # 移除 Z 是因為 strptime 的 %Z 行為不一致
            # 我們已經把時區資訊去掉，假設都是 UTC
            return True, datetime.strptime(
                normalized.replace('Z', ''),
                fmt.replace('Z', '')
            )
        except ValueError:
            # 這個格式不符合，試下一個
            continue

    # ----------------------------------------
    # 嘗試使用 fromisoformat
    # ----------------------------------------
    # Python 3.7+ 的 fromisoformat 可以解析更多 ISO 8601 變體
    # 但它不支援 'Z' 後綴，需要轉成 '+00:00'
    try:
        # 把 Z 轉回 +00:00，fromisoformat 才能解析
        clean_string = normalized.replace('Z', '+00:00')
        return True, datetime.fromisoformat(clean_string)
    except ValueError:
        pass

    # 所有格式都試過了，還是無法解析
    return False, f'Invalid date format: {date_string}'


def parse_due_date(date_string: str) -> Optional[datetime]:
    """
    解析到期日期（便利函數）

    這是 parse_date 的簡化版，專門用於解析任務到期日。
    解析失敗時回傳 None，不會拋出例外。

    【為什麼需要這個便利函數？】
    在處理任務到期日時，通常只需要知道結果（datetime 或 None）。
    不需要詳細的錯誤訊息，因為到期日是選填的。

    使用 parse_date：
    ```python
    due_date = None
    if data.get('due_date'):
        success, result = parse_date(data['due_date'])
        if success:
            due_date = result
    ```

    使用 parse_due_date：
    ```python
    due_date = parse_due_date(data.get('due_date'))
    ```

    【參數說明】
    Args:
        date_string: str
            日期字串，可以是 None 或空字串

    【回傳值說明】
    Returns:
        Optional[datetime]:
        - datetime 物件：解析成功
        - None：date_string 是空的或解析失敗

    【使用範例】
    Example:
        # 在建立任務時使用
        task = Task(
            title=data['title'],
            due_date=parse_due_date(data.get('due_date'))
        )

        # 空值處理
        due_date = parse_due_date(None)  # 回傳 None
        due_date = parse_due_date('')    # 回傳 None
    """
    # 空值處理：None 或空字串都回傳 None
    if not date_string:
        return None

    # 呼叫 parse_date 解析
    success, result = parse_date(date_string)

    if success:
        # 解析成功，回傳 datetime 物件
        return result
    else:
        # 解析失敗，記錄警告並回傳 None
        # 用 warning 而不是 error，因為這不是致命錯誤
        logger.warning(f"Failed to parse due_date: {date_string}, error: {result}")
        return None


# ============================================
# 電子郵件驗證
# ============================================

def validate_email(email: str) -> Tuple[bool, str]:
    """
    驗證電子郵件格式

    檢查電子郵件是否符合基本格式要求。
    注意：這只是格式驗證，不會檢查郵箱是否真的存在。

    【Email 格式規則】
    - 必須包含 @ 符號
    - @ 前面是 local part（使用者名稱）
    - @ 後面是 domain（網域名稱）
    - domain 必須包含至少一個 .
    - domain 的最後一段必須至少 2 個字元（如 .com, .tw）

    【為什麼不用更複雜的正則表達式？】
    完整的 RFC 5322 email 規範非常複雜。
    實際上，用簡單的正則表達式就能過濾大部分無效輸入。
    真正確認 email 存在的唯一方法是發送驗證信。

    【參數說明】
    Args:
        email: str - 要驗證的電子郵件地址

    【回傳值說明】
    Returns:
        Tuple[bool, str]:
        - (True, ''): 格式正確
        - (False, error_message): 格式錯誤

    【使用範例】
    Example:
        is_valid, error = validate_email('user@example.com')
        # (True, '')

        is_valid, error = validate_email('invalid-email')
        # (False, 'Invalid email format')

        is_valid, error = validate_email('')
        # (False, 'Email is required')
    """
    import re  # 正則表達式模組

    # 空值檢查
    if not email:
        return False, 'Email is required'

    # ----------------------------------------
    # 使用正則表達式驗證格式
    # ----------------------------------------
    # 正則表達式說明：
    # ^                 - 字串開頭
    # [a-zA-Z0-9._%+-]+ - local part：字母、數字、. _ % + - 至少一個字元
    # @                 - @ 符號
    # [a-zA-Z0-9.-]+    - domain name：字母、數字、. - 至少一個字元
    # \.                - 一個點（需要跳脫）
    # [a-zA-Z]{2,}      - 頂級域名：至少 2 個字母
    # $                 - 字串結尾
    #
    # 例如：user.name+tag@sub.example.com
    #       ^^^^^^^^^^^^^ ^^^^^^^^^^^^^^
    #       local part    domain
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, 'Invalid email format'

    # ----------------------------------------
    # 長度檢查
    # ----------------------------------------
    # RFC 5321 規定 email 最長 254 個字元
    # 但我們用 255 作為一個合理的上限
    if len(email) > 255:
        return False, 'Email is too long'

    return True, ''


# ============================================
# 分頁參數驗證
# ============================================

def validate_pagination(
    page: Any,
    per_page: Any,
    max_per_page: int = 100
) -> Tuple[int, int]:
    """
    驗證並正規化分頁參數

    將使用者輸入的分頁參數轉換成安全的整數值。
    處理各種無效輸入，確保不會發生錯誤。

    【什麼是分頁？】
    當資料很多時，不會一次回傳全部，而是分成多「頁」。
    例如：總共 100 筆資料，每頁 20 筆，分成 5 頁。

    分頁 API 通常會有這些參數：
    - page: 要取第幾頁（從 1 開始）
    - per_page: 每頁多少筆

    【為什麼需要驗證？】
    使用者可能會傳來各種奇怪的值：
    - page=-1 （負數）
    - per_page=999999 （太大）
    - page='abc' （不是數字）
    - page=null （空值）

    這個函數會把這些都處理成合理的值。

    【參數說明】
    Args:
        page: Any
            頁碼，可能是字串、數字或 None
            來自 request.args.get('page')

        per_page: Any
            每頁數量，可能是字串、數字或 None
            來自 request.args.get('per_page')

        max_per_page: int = 100
            每頁最大數量限制
            防止使用者要求太多資料導致伺服器負載過重

    【回傳值說明】
    Returns:
        Tuple[int, int]: (validated_page, validated_per_page)
        - page: 至少為 1 的整數
        - per_page: 1 到 max_per_page 之間的整數

    【轉換規則】
    page:
    - None/空字串 → 1（預設第一頁）
    - 負數/0 → 1（至少第一頁）
    - 無法轉成數字 → 1

    per_page:
    - None/空字串 → 20（預設每頁 20 筆）
    - 負數/0 → 1（至少 1 筆）
    - > max_per_page → max_per_page（不超過上限）
    - 無法轉成數字 → 20

    【使用範例】
    Example:
        # 從 request.args 取得並驗證
        page, per_page = validate_pagination(
            request.args.get('page'),
            request.args.get('per_page')
        )

        # 使用 SQLAlchemy 分頁
        tasks = Task.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # 處理各種輸入
        validate_pagination(None, None)      # (1, 20)
        validate_pagination('2', '50')       # (2, 50)
        validate_pagination(-1, 999)         # (1, 100) - 限制在合理範圍
        validate_pagination('abc', 'xyz')    # (1, 20) - 無效值用預設值
    """
    # ----------------------------------------
    # 處理 page 參數
    # ----------------------------------------
    try:
        # 嘗試轉成整數
        # int() 可以處理字串和數字
        # 如果 page 是 None 或空字串，使用預設值 1
        page = int(page) if page else 1

        # 確保至少為 1
        # max(1, page) 回傳 1 和 page 中較大的那個
        page = max(1, page)

    except (ValueError, TypeError):
        # ValueError: int('abc') 無法轉換
        # TypeError: int(None) 型別錯誤
        # 這些情況都使用預設值
        page = 1

    # ----------------------------------------
    # 處理 per_page 參數
    # ----------------------------------------
    try:
        per_page = int(per_page) if per_page else 20

        # 確保在 1 到 max_per_page 之間
        # min(a, b) 回傳較小的
        # max(a, b) 回傳較大的
        #
        # max(1, min(per_page, max_per_page)) 的意思是：
        # 1. 先確保 per_page 不超過 max_per_page
        # 2. 再確保結果至少為 1
        per_page = max(1, min(per_page, max_per_page))

    except (ValueError, TypeError):
        per_page = 20

    return page, per_page


# ============================================
# 補充說明：驗證的層次
# ============================================
#
# 一個完整的應用程式通常有多層驗證：
#
# 【第一層：前端驗證】
# - 在瀏覽器中執行
# - 提供即時回饋
# - 可以被繞過（不可信任）
#
# 【第二層：API 驗證（這個模組）】
# - 檢查請求格式和基本規則
# - 防止無效資料進入系統
# - 這是「防線」，不能被繞過
#
# 【第三層：業務邏輯驗證】
# - 檢查業務規則（如：使用者餘額是否足夠）
# - 通常在 service 層處理
#
# 【第四層：資料庫約束】
# - 最後的防線
# - 如：unique 約束、not null 約束
# - 即使程式有 bug，資料庫也會拒絕不合法的資料
#
# ============================================
# 常見的驗證錯誤
# ============================================
#
# 1. 只在前端驗證
#    問題：攻擊者可以直接呼叫 API 繞過前端
#    解法：後端一定要驗證
#
# 2. 相信 Content-Type
#    問題：攻擊者可以偽造 Content-Type
#    解法：不要只看 Content-Type，要實際驗證內容
#
# 3. 驗證後不使用驗證結果
#    問題：驗證了 data，但實際使用 request.json
#    解法：使用驗證函數回傳的 validated_data
#
# 4. 錯誤訊息洩漏資訊
#    問題：「密碼錯誤」vs「使用者不存在」讓攻擊者知道帳號存在
#    解法：統一回傳「帳號或密碼錯誤」
