# Team Task Manager 系統架構完整說明

> 這份文件是為完全新手準備的，會用最淺顯易懂的方式解釋整個系統如何運作。

---

## 目錄

1. [系統概覽](#1-系統概覽)
2. [前後端如何溝通](#2-前後端如何溝通)
3. [後端架構詳解](#3-後端架構詳解)
4. [前端架構詳解](#4-前端架構詳解)
5. [認證流程詳解](#5-認證流程詳解)
6. [資料庫設計](#6-資料庫設計)
7. [API 串接完整流程](#7-api-串接完整流程)
8. [常見問題與除錯](#8-常見問題與除錯)

---

## 1. 系統概覽

### 1.1 什麼是前後端分離？

想像一家餐廳：
- **前端 (Frontend)** = 餐廳的用餐區（顧客看到的地方）
  - 負責呈現漂亮的介面
  - 接收使用者的操作（點餐）
  - 顯示結果（上菜）

- **後端 (Backend)** = 廚房
  - 接收前端的請求（訂單）
  - 處理業務邏輯（烹飪）
  - 存取資料庫（冰箱、倉庫）
  - 回傳結果（出餐）

- **資料庫 (Database)** = 冰箱和倉庫
  - 儲存所有的資料

### 1.2 技術棧

```
前端 (Frontend)
├── React 19          # UI 框架
├── TypeScript        # 程式語言（有型別的 JavaScript）
├── Vite              # 開發工具
├── React Query       # 資料狀態管理
└── Socket.IO Client  # 即時通訊

後端 (Backend)
├── Flask 3.0         # Web 框架
├── SQLAlchemy        # ORM（資料庫操作）
├── Flask-JWT-Extended # 認證
├── Flask-Bcrypt      # 密碼加密
└── Flask-SocketIO    # 即時通訊

資料庫
├── SQLite            # 開發環境
└── PostgreSQL        # 生產環境
```

### 1.3 資料夾結構

```
team-task-manager/
│
├── backend/                    # 後端程式碼
│   ├── app.py                 # 入口點（啟動伺服器）
│   ├── config.py              # 設定檔
│   ├── models.py              # 資料模型（資料庫結構）
│   │
│   ├── api/                   # API 路由
│   │   ├── auth.py           # 認證 API（登入、註冊）
│   │   ├── projects.py       # 專案 API
│   │   ├── tasks.py          # 任務 API
│   │   ├── notifications.py  # 通知 API
│   │   └── members.py        # 成員 API
│   │
│   ├── services/              # 業務邏輯
│   │   ├── auth_service.py   # 認證邏輯
│   │   ├── permissions.py    # 權限檢查
│   │   └── ...
│   │
│   ├── core/                  # 核心功能
│   │   ├── cache.py          # 快取
│   │   ├── token_blacklist.py # Token 黑名單
│   │   └── socket_events.py  # WebSocket 事件
│   │
│   └── utils/                 # 工具函數
│       ├── validators.py     # 輸入驗證
│       └── response.py       # 回應格式
│
└── frontend/                   # 前端程式碼
    ├── App.tsx                # 根元件
    ├── types.ts               # TypeScript 型別定義
    │
    ├── pages/                 # 頁面元件
    │   ├── Login.tsx         # 登入頁
    │   ├── Dashboard.tsx     # 首頁
    │   ├── Projects.tsx      # 專案列表
    │   └── ...
    │
    ├── services/              # API 服務
    │   └── apiService.ts     # 所有 API 呼叫
    │
    ├── context/               # React Context
    │   └── AuthContext.tsx   # 認證狀態
    │
    └── hooks/                 # 自訂 Hooks
        ├── useApi.ts         # API 相關 hooks
        └── useSocket.ts      # WebSocket hooks
```

---

## 2. 前後端如何溝通

### 2.1 HTTP 請求基礎

前後端透過 **HTTP 請求** 溝通，就像寄信一樣：

```
前端（寄信）                          後端（收信）
    │                                    │
    │  ┌─────────────────────────────┐   │
    │  │ HTTP 請求                    │   │
    │  │ ─────────────────────────── │   │
    │  │ 方法：POST                   │   │
    │  │ 路徑：/auth/login            │   │
    │  │ 標頭：Content-Type: JSON     │   │
    │  │ 內容：{"email": "...",       │   │
    │  │       "password": "..."}     │   │
    │  └─────────────────────────────┘   │
    │ ──────────────────────────────────>│
    │                                    │
    │  ┌─────────────────────────────┐   │
    │  │ HTTP 回應                    │   │
    │  │ ─────────────────────────── │   │
    │  │ 狀態碼：200 OK               │   │
    │  │ 內容：{"access_token": "..."} │   │
    │  └─────────────────────────────┘   │
    │ <──────────────────────────────────│
```

### 2.2 HTTP 方法

| 方法 | 用途 | 範例 |
|------|------|------|
| GET | 取得資料 | 取得專案列表 |
| POST | 建立資料 | 建立新專案 |
| PATCH | 更新部分資料 | 更新任務狀態 |
| PUT | 完整替換資料 | 替換整個專案 |
| DELETE | 刪除資料 | 刪除任務 |

### 2.3 HTTP 狀態碼

| 狀態碼 | 意義 | 說明 |
|--------|------|------|
| 200 | OK | 請求成功 |
| 201 | Created | 建立成功 |
| 400 | Bad Request | 請求格式錯誤 |
| 401 | Unauthorized | 未認證（需要登入） |
| 403 | Forbidden | 沒有權限 |
| 404 | Not Found | 資源不存在 |
| 500 | Server Error | 伺服器錯誤 |

### 2.4 CORS（跨來源請求）

```
問題：
前端在 http://localhost:3000
後端在 http://localhost:8888
網址不同 → 瀏覽器會阻擋請求！

解決方案：
後端設定 CORS，告訴瀏覽器「這些來源是安全的」

在 app.py 中：
CORS(app, origins=['http://localhost:3000', ...])
```

---

## 3. 後端架構詳解

### 3.1 Flask 基礎

```python
# Flask 是一個 Web 框架，讓你可以輕鬆建立 API

from flask import Flask
app = Flask(__name__)

# 定義一個路由（API 端點）
@app.route('/hello')
def hello():
    return {'message': 'Hello World'}

# 啟動伺服器
app.run(port=8888)
```

### 3.2 Blueprint（模組化路由）

```python
# 把相關的 API 放在一起，像是把部門分開

# auth.py
from flask import Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    # 登入邏輯
    pass

# app.py
from api.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# 結果：
# /login 變成 /auth/login
```

### 3.3 請求處理流程

```
HTTP 請求進入
      │
      ▼
┌─────────────────────┐
│ 1. CORS 檢查        │ ← 是否允許這個來源？
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 2. Rate Limiting    │ ← 請求是否太頻繁？
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 3. JWT 認證         │ ← Token 是否有效？
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 4. 路由匹配         │ ← 這個路徑對應哪個函數？
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 5. 輸入驗證         │ ← 請求資料格式正確嗎？
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 6. 業務邏輯處理     │ ← 實際執行操作
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 7. 資料庫操作       │ ← 讀取/寫入資料
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ 8. 回傳結果         │ ← JSON 格式
└─────────────────────┘
```

### 3.4 SQLAlchemy ORM

```python
# ORM 讓你用 Python 物件操作資料庫，不用寫 SQL

# 定義模型（對應資料表）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(100))

# 查詢資料
user = User.query.get(1)                    # 用 ID 查詢
user = User.query.filter_by(email='...').first()  # 用條件查詢
users = User.query.all()                    # 取得所有

# 新增資料
new_user = User(email='...', username='...')
db.session.add(new_user)
db.session.commit()

# 更新資料
user.username = 'new name'
db.session.commit()

# 刪除資料
db.session.delete(user)
db.session.commit()
```

---

## 4. 前端架構詳解

### 4.1 React 元件

```tsx
// React 用「元件」來組成畫面
// 每個元件就像一塊積木

function Button({ text, onClick }) {
  return (
    <button onClick={onClick}>
      {text}
    </button>
  );
}

// 使用元件
<Button text="登入" onClick={handleLogin} />
```

### 4.2 TypeScript 型別

```typescript
// TypeScript 讓你定義資料的「形狀」
// 可以避免很多錯誤

// 定義使用者的型別
interface User {
  id: number;
  email: string;
  username: string;
}

// 使用型別
const user: User = {
  id: 1,
  email: 'test@example.com',
  username: 'Test User'
};

// 如果資料不符合型別，編輯器會提醒你
const badUser: User = {
  id: 'abc',  // 錯誤！id 應該是 number
  email: 'test@example.com',
  username: 'Test User'
};
```

### 4.3 apiService.ts 結構

```typescript
// apiService.ts 集中管理所有 API 呼叫

// 基本的 API 請求函數
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAccessToken()}`
    },
    ...options
  });

  // 處理 401（Token 過期）
  if (response.status === 401) {
    // 嘗試刷新 token
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // 重試請求
      return apiRequest(endpoint, options);
    }
    // 刷新失敗，登出
    clearTokens();
    throw new Error('Session expired');
  }

  return response.json();
}

// 認證服務
export const authService = {
  login: (email, password) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }),

  logout: () =>
    apiRequest('/auth/logout', { method: 'POST' }),
};

// 專案服務
export const projectService = {
  getProjects: () =>
    apiRequest('/projects'),

  createProject: (data) =>
    apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
};
```

### 4.4 React Context（全域狀態）

```tsx
// AuthContext 用來管理登入狀態
// 讓所有元件都能存取「誰登入了」

// 建立 Context
const AuthContext = createContext<AuthContextType | null>(null);

// Provider 元件
export function AuthProvider({ children }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    const response = await authService.login(email, password);
    setUser(response.user);
    // 儲存 token
    localStorage.setItem('access_token', response.access_token);
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
    localStorage.removeItem('access_token');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// 在任何元件中使用
function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav>
      <span>歡迎，{user?.username}</span>
      <button onClick={logout}>登出</button>
    </nav>
  );
}
```

---

## 5. 認證流程詳解

### 5.1 JWT 是什麼？

```
JWT (JSON Web Token) 就像是「電子通行證」

結構：xxxxx.yyyyy.zzzzz
      Header.Payload.Signature

Header（標頭）：
{
  "alg": "HS256",  // 使用的加密演算法
  "typ": "JWT"     // Token 類型
}

Payload（內容）：
{
  "sub": "123",           // 使用者 ID
  "exp": 1699999999,      // 過期時間
  "iat": 1699000000       // 簽發時間
}

Signature（簽名）：
用密鑰加密 Header + Payload
確保 Token 沒有被竄改
```

### 5.2 雙 Token 機制

```
為什麼要有兩個 Token？

Access Token（通行證）
├── 有效期短（1 小時）
├── 每次 API 請求都要帶
└── 如果被盜，損失有限

Refresh Token（續期憑證）
├── 有效期長（30 天）
├── 只用來換新的 Access Token
└── 很少傳輸，較安全
```

### 5.3 完整認證流程

```
1. 使用者登入
   ┌──────────────────────────────────────┐
   │ POST /auth/login                     │
   │ Body: { email, password }            │
   └──────────────────────────────────────┘
                    │
                    ▼
   ┌──────────────────────────────────────┐
   │ 後端驗證密碼，產生 Tokens            │
   │ 回傳 access_token + refresh_token    │
   └──────────────────────────────────────┘
                    │
                    ▼
   ┌──────────────────────────────────────┐
   │ 前端儲存 Tokens 到 localStorage      │
   └──────────────────────────────────────┘

2. 一般 API 請求
   ┌──────────────────────────────────────┐
   │ GET /projects                        │
   │ Headers: Authorization: Bearer <token>│
   └──────────────────────────────────────┘
                    │
                    ▼
   ┌──────────────────────────────────────┐
   │ 後端驗證 Token，回傳資料             │
   └──────────────────────────────────────┘

3. Token 過期時
   ┌──────────────────────────────────────┐
   │ API 回傳 401 Unauthorized            │
   └──────────────────────────────────────┘
                    │
                    ▼
   ┌──────────────────────────────────────┐
   │ 前端用 Refresh Token 換新 Token      │
   │ POST /auth/refresh                   │
   │ Headers: Authorization: Bearer <refresh>│
   └──────────────────────────────────────┘
                    │
                    ▼
   ┌──────────────────────────────────────┐
   │ 取得新 Access Token，重試原本請求    │
   └──────────────────────────────────────┘

4. 登出
   ┌──────────────────────────────────────┐
   │ POST /auth/logout                    │
   │ 後端將 Token 加入黑名單              │
   │ 前端清除 localStorage                │
   └──────────────────────────────────────┘
```

---

## 6. 資料庫設計

### 6.1 實體關係圖 (ER Diagram)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Project   │       │    Task     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ email       │  │    │ name        │  │    │ title       │
│ password    │  │    │ description │  │    │ description │
│ username    │  │    │ owner_id(FK)│◄─┤    │ status      │
│ ...         │  │    │ ...         │  │    │ project_id  │◄─┐
└─────────────┘  │    └─────────────┘  │    │ assigned_to │──┤
                 │                      │    │ created_by  │──┤
                 │                      │    └─────────────┘  │
                 │                      │                      │
                 │    ┌─────────────┐  │                      │
                 │    │ProjectMember│  │                      │
                 │    ├─────────────┤  │                      │
                 ├───►│ user_id(FK) │  │                      │
                 │    │ project_id  │◄─┘                      │
                 │    │ role        │                         │
                 │    └─────────────┘                         │
                 │                                             │
                 │    ┌─────────────┐                         │
                 │    │ TaskComment │                         │
                 │    ├─────────────┤                         │
                 │    │ id (PK)     │                         │
                 ├───►│ user_id(FK) │                         │
                      │ task_id(FK) │◄────────────────────────┘
                      │ content     │
                      └─────────────┘

PK = Primary Key（主鍵）
FK = Foreign Key（外鍵）
```

### 6.2 關聯類型

```
一對多 (1:N)
├── User → Project（一個使用者可以建立多個專案）
├── Project → Task（一個專案有多個任務）
└── Task → Comment（一個任務有多個評論）

多對多 (M:N)
├── User ↔ Project（透過 ProjectMember）
│   一個使用者可以加入多個專案
│   一個專案可以有多個成員
│
└── Task ↔ Tag（透過 task_tags）
    一個任務可以有多個標籤
    一個標籤可以用在多個任務
```

---

## 7. API 串接完整流程

### 7.1 以「建立任務」為例

```
使用者在 ProjectDetail.tsx 點擊「新增任務」

步驟 1：前端收集資料
─────────────────────
const handleCreateTask = async (taskData) => {
  // taskData = { title: '新任務', priority: 'high', ... }
}

步驟 2：呼叫 API 服務
─────────────────────
// 在 apiService.ts
taskService.createTask(projectId, taskData);

// 實際執行
const response = await fetch('/projects/1/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGc...'  // JWT Token
  },
  body: JSON.stringify({
    title: '新任務',
    priority: 'high'
  })
});

步驟 3：後端接收請求
─────────────────────
# 在 tasks.py

@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@jwt_required()  # 驗證 Token
def create_task(project_id):
    # 1. 驗證輸入
    data = request.get_json()
    is_valid, result = validate_request_data(CreateTaskSchema, data)

    # 2. 檢查權限
    has_access, project, role = check_project_access(project_id, user_id)

    # 3. 建立任務
    task = Task(
        title=result['title'],
        priority=result['priority'],
        project_id=project_id,
        created_by=user_id
    )
    db.session.add(task)
    db.session.commit()

    # 4. 回傳結果
    return jsonify({'task': {...}}), 201

步驟 4：前端處理回應
─────────────────────
// React Query 會自動更新畫面
const mutation = useMutation({
  mutationFn: (data) => taskService.createTask(projectId, data),
  onSuccess: () => {
    // 重新取得任務列表
    queryClient.invalidateQueries(['tasks', projectId]);
  }
});
```

### 7.2 資料轉換

```typescript
// 後端回傳的資料格式（snake_case）
{
  "id": 1,
  "project_id": 1,
  "assigned_to": 2,
  "due_date": "2024-01-15T00:00:00",
  "created_at": "2024-01-01T10:30:00"
}

// 前端需要的格式（camelCase）
{
  id: 1,
  projectId: 1,
  assigneeId: 2,
  dueDate: new Date("2024-01-15"),
  createdAt: new Date("2024-01-01T10:30:00")
}

// 在 apiService.ts 中轉換
const transformTask = (backendTask: any): Task => ({
  id: backendTask.id,
  projectId: backendTask.project_id,
  assigneeId: backendTask.assigned_to,
  dueDate: backendTask.due_date ? new Date(backendTask.due_date) : undefined,
  createdAt: new Date(backendTask.created_at),
  // ...
});
```

---

## 8. 常見問題與除錯

### 8.1 CORS 錯誤

```
錯誤訊息：
Access to fetch at 'http://localhost:8888/api' from origin
'http://localhost:3000' has been blocked by CORS policy

解決方法：
1. 確認後端 CORS 設定包含前端網址
2. 確認請求的 headers 是允許的
3. 確認 HTTP 方法是允許的
```

### 8.2 401 Unauthorized

```
可能原因：
1. Token 過期
2. Token 格式錯誤
3. Token 被撤銷（登出後）
4. 沒有帶 Token

解決方法：
1. 檢查 localStorage 是否有 token
2. 確認 Authorization header 格式正確
3. 嘗試重新登入
```

### 8.3 資料不同步

```
問題：
建立任務後，列表沒有更新

原因：
React Query 還在使用快取的資料

解決方法：
// 在 mutation 成功後，使快取失效
onSuccess: () => {
  queryClient.invalidateQueries(['tasks']);
}
```

### 8.4 如何除錯

```
前端除錯：
1. 開啟瀏覽器的開發者工具（F12）
2. 查看 Network 分頁，檢視 API 請求
3. 查看 Console 分頁，檢視錯誤訊息

後端除錯：
1. 查看終端機的日誌輸出
2. 檢視 logs/app.log 和 logs/error.log
3. 使用 print() 或 logger.info() 印出變數
```

---

## 附錄：重要檔案對照表

| 功能 | 前端檔案 | 後端檔案 |
|------|----------|----------|
| 登入 | Login.tsx, authService | auth.py |
| 專案列表 | Projects.tsx, projectService | projects.py |
| 任務管理 | ProjectDetail.tsx, taskService | tasks.py |
| 通知 | Layout.tsx, notificationService | notifications.py |
| 型別定義 | types.ts | models.py |
| API 呼叫 | apiService.ts | - |
| 認證狀態 | AuthContext.tsx | - |
| 設定 | vite.config.ts | config.py |
