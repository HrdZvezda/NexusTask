# NexusTeam 專案結構完整說明

> 本文件詳細說明專案中每個檔案和目錄的用途

---

## 📁 專案根目錄

```
team-task-manager/
├── 📄 文件檔案
├── 🔧 配置檔案
├── 📂 backend/          (後端 Flask API)
├── 📂 frontend/         (前端 React 應用)
├── 📂 .start/           (開發啟動腳本)
├── 📂 .github/          (GitHub 設定)
└── 📂 scripts/          (工具腳本)
```

---

## 📄 根目錄文件檔案

### 核心文件

| 檔案 | 用途 |
|------|------|
| **README.md** | 專案說明（英文版），給面試官/GitHub 訪客看 |
| **README.zh-TW.md** | 專案說明（繁體中文版） |
| **CODE_REVIEW.md** | 程式碼審查報告，記錄改進建議和最佳實踐 |
| **LICENSE** | 開源授權（MIT License） |

### 部署文件

| 檔案 | 用途 | 適用場景 |
|------|------|----------|
| **DEPLOYMENT.md** | 🎯 **完整部署指南（推薦）** | GCP Cloud Run + Vercel + Neon 部署 |
| **PROJECT_STRUCTURE.md** | 本檔案，專案結構說明 | 理解專案架構 |

---

## 🔧 根目錄配置檔案

| 檔案 | 用途 | 說明 |
|------|------|------|
| **.env.example** | 環境變數範例模板 | 複製成 `.env` 後填入實際值 |
| **.gitignore** | Git 忽略檔案清單 | 避免提交敏感檔案和暫存檔 |

---

## 📂 backend/ (後端 Flask API)

### 核心應用檔案

| 檔案 | 用途 | 說明 |
|------|------|------|
| **app.py** | Flask 應用主程式入口 | 啟動伺服器、註冊 Blueprint、初始化中介軟體 |
| **config.py** | 應用配置管理 | 從環境變數載入設定（DB、Redis、JWT 等） |
| **models.py** | 資料模型簡化導入 | 向後兼容的 shim 檔案 |
| **models_legacy.py** | 完整的 SQLAlchemy 資料模型 | User、Project、Task、Notification 等 |
| **requirements.txt** | Python 套件依賴清單 | `pip install -r requirements.txt` 安裝 |
| **runtime.txt** | Python 版本指定 | 部署平台使用（如 `python-3.12` ） |

### 部署配置檔案

| 檔案 | 用途 | 使用平台 |
|------|------|----------|
| **Dockerfile** | Docker 容器建置配置 | GCP Cloud Run、本地 Docker |
| **.dockerignore** | Docker 建置排除檔案 | 避免打包不必要的檔案 |
| **.env** | 環境變數（本地開發） | **包含敏感資訊，不應提交到 Git** |
| **.env.example** | 環境變數範例 | 新環境設定時參考 |
| **.flake8** | Flake8 程式碼檢查配置 | Python 程式碼風格檢查 |
| **mypy.ini** | MyPy 型別檢查配置 | Python 靜態型別檢查 |

### 📂 backend/api/ (API 端點 - Blueprints)

每個檔案是一個功能模組的 RESTful API 端點：

| 檔案 | 功能 | 主要端點 |
|------|------|----------|
| **__init__.py** | Blueprint 初始化 | - |
| **auth.py** | 使用者認證 | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh` |
| **projects.py** | 專案管理 | `/projects` (CRUD), `/projects/:id/members`, `/projects/:id/stats` |
| **tasks.py** | 任務管理 | `/tasks` (CRUD), `/tasks/all`, `/tasks/my`, `/tasks/:id/comments` |
| **notifications.py** | 通知系統 | `/notifications`, `/notifications/read`, `/notifications/unread-count` |
| **members.py** | 成員管理 | `/projects/:id/members` (add/remove/update role) |
| **tags.py** | 標籤系統 | `/tags` (CRUD) |
| **uploads.py** | 檔案上傳 | `/uploads` (upload/download/delete attachments) |
| **health.py** | 健康檢查 | `/health`, `/health/live`, `/health/ready`, `/health/detailed` |

### 📂 backend/core/ (核心基礎設施)

系統核心功能模組：

| 檔案 | 功能 | 說明 |
|------|------|------|
| **__init__.py** | 模組初始化 | - |
| **cache.py** | 快取管理 | CacheKeyManager、CacheTimeout、invalidate 快取輔助函數 |
| **celery_tasks.py** | 背景任務 | Celery 設定、郵件發送、通知廣播、定時清理任務 |
| **socket_events.py** | WebSocket 事件 | Flask-SocketIO 即時通訊、線上狀態、打字指示器 |
| **middleware.py** | 中介軟體 | 安全標頭、請求日誌、維護模式、請求 ID |
| **api_docs.py** | API 文件 | Swagger/OpenAPI 配置 |
| **token_blacklist.py** | Token 黑名單 | JWT 登出時撤銷 Token（Redis/記憶體） |

### 📂 backend/services/ (業務邏輯層)

Service Layer Pattern - 業務邏輯與資料存取分離：

| 檔案 | 功能 | 說明 |
|------|------|------|
| **__init__.py** | 服務初始化 | - |
| **base.py** | 基礎服務類別 | BaseService、ServiceResult、UnitOfWork |
| **auth_service.py** | 認證業務邏輯 | 註冊、登入、密碼重設、Token 管理 |
| **project_service.py** | 專案業務邏輯 | 專案 CRUD、成員管理、權限檢查 |
| **task_service.py** | 任務業務邏輯 | 任務 CRUD、狀態更新、評論管理 |
| **notification_service.py** | 通知業務邏輯 | 建立通知、標記已讀、清理過期通知 |
| **permissions.py** | 權限檢查 | 集中式權限驗證，避免循環引用 |

### 📂 backend/utils/ (工具函數)

共用輔助工具：

| 檔案 | 功能 | 說明 |
|------|------|------|
| **__init__.py** | 工具初始化 | - |
| **response.py** | 統一 API 回應 | ApiResponse、ResponseBuilder、ErrorCode 枚舉 |
| **validators.py** | 驗證器 | SchemaValidator (Marshmallow)、密碼驗證、日期驗證、分頁驗證 |
| **decorators.py** | 裝飾器 | 自訂裝飾器（如權限檢查） |

### 📂 backend/tests/ (測試套件)

Pytest 測試檔案：

| 檔案 | 測試範圍 | 說明 |
|------|----------|------|
| **conftest.py** | 測試配置 | Fixtures、測試資料庫設定 |
| **test_auth.py** | 認證 API 測試 | 註冊、登入、登出、Token 刷新 |
| **test_projects.py** | 專案 API 測試 | 專案 CRUD、成員管理 |
| **test_tasks.py** | 任務 API 測試 | 任務 CRUD、評論 |
| **test_notifications.py** | 通知 API 測試 | 通知建立、已讀 |
| **test_members.py** | 成員 API 測試 | 成員增刪改 |
| **test_tags.py** | 標籤 API 測試 | 標籤 CRUD |
| **test_attachments.py** | 附件 API 測試 | 檔案上傳下載 |

執行測試：
```bash
cd backend
pytest                              # 執行所有測試
pytest --cov=. --cov-report=html   # 生成覆蓋率報告
```

### 📂 backend/instance/

| 檔案 | 用途 | 說明 |
|------|------|------|
| **task_manager.db** | SQLite 資料庫檔案 | 本地開發用，生產環境用 PostgreSQL |

⚠️ 這些檔案應在 `.gitignore` 中，不應提交到 Git

### 📂 backend/models/

| 檔案 | 用途 | 說明 |
|------|------|------|
| **__init__.py** | 模型初始化 | 可能用於模組化資料模型 |

---

## 📂 frontend/ (前端 React 應用)

### 核心檔案

| 檔案 | 用途 | 說明 |
|------|------|------|
| **index.html** | HTML 入口檔案 | Vite 掛載點，定義 `<div id="root">` |
| **index.tsx** | React 入口點 | 渲染 `<App />` 到 DOM |
| **App.tsx** | 主應用元件 | 路由、AuthProvider、QueryProvider 包裝 |
| **types.ts** | TypeScript 型別定義 | User、Project、Task、Notification 等介面 |
| **vite.config.ts** | Vite 建置配置 | 開發伺服器、打包設定 |
| **tsconfig.json** | TypeScript 配置 | 編譯選項、路徑映射 |
| **package.json** | npm 套件依賴 | React、React Query、Socket.IO 等 |
| **package-lock.json** | 依賴版本鎖定 | 確保團隊安裝相同版本 |
| **.env.local** | 環境變數（本地） | `VITE_API_URL` 設定後端網址 |
| **README.md** | 前端專屬說明 | 啟動指令、技術棧 |
| **metadata.json** | 專案中繼資料 | 可能用於建置資訊 |
| **vite-env.d.ts** | Vite 型別定義 | TypeScript 環境宣告 |

### 📂 frontend/pages/ (頁面元件)

SPA 路由對應的頁面：

| 檔案 | 路由 | 功能 |
|------|------|------|
| **Login.tsx** | `/login` | 登入頁面 |
| **Register.tsx** | `/register` | 註冊頁面 |
| **Dashboard.tsx** | `/` | 儀表板，顯示統計資料、可點擊的 Recent Activity |
| **Projects.tsx** | `/projects` | 專案列表 |
| **ProjectDetail.tsx** | `/projects/:id` | 專案詳情與看板 |
| **MyTasks.tsx** | `/tasks/my` | 個人任務列表 |
| **Notifications.tsx** | `/notifications` | 通知列表，支援 mark all as read |
| **Settings.tsx** | `/settings` | 使用者設定 |

### 📂 frontend/components/ (共用元件)

可重用的 UI 元件：

| 檔案 | 用途 | 說明 |
|------|------|------|
| **Layout.tsx** | 主版面配置 | Header、Sidebar、內容區域 |
| **TaskDetailModal.tsx** | 任務詳情彈窗 | 顯示/編輯任務詳細資訊 |

### 📂 frontend/context/ (React Context)

全域狀態管理：

| 檔案 | 用途 | 說明 |
|------|------|------|
| **AuthContext.tsx** | 認證狀態 | 登入使用者資訊、Token、登入/登出方法 |
| **NotificationContext.tsx** | 通知狀態同步 | Dashboard 與 Notifications 頁面共享通知狀態 |

### 📂 frontend/providers/ (Provider 元件)

狀態提供者：

| 檔案 | 用途 | 說明 |
|------|------|------|
| **QueryProvider.tsx** | React Query 設定 | QueryClient 配置、快取策略 |

### 📂 frontend/hooks/ (自訂 Hooks)

可重用的業務邏輯：

| 檔案 | 用途 | 主要 Hooks |
|------|------|------------|
| **useApi.ts** | API 呼叫與資料管理 | `useProjects`, `useTasks`, `useNotifications` 等 |
| **useSocket.ts** | WebSocket 連線 | `useSocket`, `useProjectRoom`, `useNotificationListener` |

### 📂 frontend/services/ (服務層)

API 通訊封裝：

| 檔案 | 用途 | 說明 |
|------|------|------|
| **apiService.ts** | HTTP 請求封裝 | Fetch API 包裝、錯誤處理、Token 注入 |

### 📂 frontend/utils/ (工具函數)

| 檔案 | 用途 | 說明 |
|------|------|------|
| **helpers.ts** | 輔助函數 | 日期格式化、字串處理等 |

---

## 📂 .start/ (開發啟動腳本)

| 檔案 | 用途 | 使用方式 |
|------|------|----------|
| **dev** | 一鍵啟動開發環境 | `./.start/dev` |

功能：
1. 釋放 8888 和 5173 埠（kill 舊程序）
2. 啟動後端（`cd backend && python app.py`）
3. 啟動前端（`cd frontend && npm run dev`）

---

## 📂 scripts/ (工具腳本)

### Shell 腳本

| 檔案 | 用途 | 使用方式 |
|------|------|----------|
| **backup-db.sh** | 備份 PostgreSQL 資料庫 | `DATABASE_URL=... ./scripts/backup-db.sh` |
| **restore-db.sh** | 還原資料庫 | `./scripts/restore-db.sh backups/backup.sql.gz` |
| **generate-secrets.sh** | 生成安全密鑰 | `./scripts/generate-secrets.sh` |

---

## 🔍 檔案依賴關係圖

### 應用啟動流程

```
app.py (主程式)
  ├─> config.py (載入配置)
  ├─> models_legacy.py (資料模型)
  ├─> core/middleware.py (註冊中介軟體)
  ├─> core/socket_events.py (初始化 SocketIO)
  ├─> api/* (註冊所有 Blueprints)
  │    ├─> services/* (呼叫業務邏輯)
  │    │    ├─> models_legacy.py (資料存取)
  │    │    ├─> core/cache.py (快取)
  │    │    └─> core/celery_tasks.py (背景任務)
  │    └─> utils/response.py (統一回應格式)
  └─> core/api_docs.py (Swagger 文件)
```

### 前端應用流程

```
index.tsx (入口)
  └─> App.tsx
       ├─> providers/QueryProvider.tsx (React Query)
       ├─> context/AuthContext.tsx (認證狀態)
       ├─> context/NotificationContext.tsx (通知狀態同步)
       ├─> components/Layout.tsx (版面)
       └─> pages/* (頁面路由)
            ├─> hooks/useApi.ts (API 呼叫)
            ├─> hooks/useSocket.ts (WebSocket)
            └─> services/apiService.ts (HTTP 請求)
```

---

## 📊 檔案重要性等級

### 核心檔案（必須理解）

**後端**
- `backend/app.py` - 應用入口
- `backend/config.py` - 配置管理
- `backend/models_legacy.py` - 資料模型
- `backend/api/*.py` - 所有 API 端點
- `backend/services/*.py` - 業務邏輯

**前端**
- `frontend/App.tsx` - 應用主元件
- `frontend/hooks/useApi.ts` - API 管理
- `frontend/pages/*.tsx` - 所有頁面
- `frontend/context/AuthContext.tsx` - 認證
- `frontend/context/NotificationContext.tsx` - 通知狀態同步

**文件**
- `README.md` - 專案說明
- `DEPLOYMENT.md` - 部署指南

### 重要檔案（需要了解）

**後端**
- `backend/core/cache.py` - 快取管理
- `backend/core/celery_tasks.py` - 背景任務
- `backend/core/socket_events.py` - WebSocket
- `backend/utils/response.py` - API 回應

**前端**
- `frontend/hooks/useSocket.ts` - 即時通訊
- `frontend/services/apiService.ts` - HTTP 封裝

**配置**
- `backend/requirements.txt` - Python 依賴
- `frontend/package.json` - Node 依賴

### 輔助檔案（選擇性理解）

**測試**
- `backend/tests/*.py` - 測試套件

**工具**
- `scripts/*.sh` - 輔助腳本
- `.start/dev` - 開發啟動

**部署**
- `backend/Dockerfile` - Docker 映像建置
- `backend/.dockerignore` - Docker 排除設定

### 配置檔案（必要但不需深入）

- `.gitignore` - Git 忽略
- `tsconfig.json` - TypeScript 配置
- `vite.config.ts` - Vite 配置
- `.env.example` - 環境變數範例

### 自動生成/暫存檔案（可忽略）

- `package-lock.json` - npm 鎖定
- `vite-env.d.ts` - 型別定義
- `backend/instance/*.db` - SQLite 資料庫

---

## 🎯 快速導航指南

### 我想了解...

**❓ 如何新增 API 端點？**
→ 查看 `backend/api/tasks.py` 範例
→ 閱讀 `backend/services/task_service.py` 業務邏輯

**❓ 如何修改資料模型？**
→ 編輯 `backend/models_legacy.py`
→ 需要資料庫遷移（目前使用 `db.create_all()`）

**❓ 如何新增前端頁面？**
→ 在 `frontend/pages/` 建立新元件
→ 在 `frontend/App.tsx` 加入路由

**❓ 如何部署到線上？**
→ 閱讀 `DEPLOYMENT.md`
→ 後端：GCP Cloud Run（Docker 容器）
→ 前端：Vercel（全球 CDN）
→ 資料庫：Neon PostgreSQL

**❓ 如何執行測試？**
→ `cd backend && pytest`

**❓ 如何啟動開發環境？**
→ `./.start/dev`（或手動啟動後端+前端）

---

## 📝 檔案命名規範

### 後端 Python
- **檔案名稱**：`snake_case.py`（如 `auth_service.py`）
- **類別名稱**：`PascalCase`（如 `AuthService`）
- **函數名稱**：`snake_case`（如 `get_user_by_id`）

### 前端 TypeScript/React
- **元件檔案**：`PascalCase.tsx`（如 `Dashboard.tsx`）
- **工具檔案**：`camelCase.ts`（如 `apiService.ts`）
- **Hook 檔案**：`useXxx.ts`（如 `useApi.ts`）
- **型別檔案**：`types.ts` 或 `*.types.ts`

### 配置檔案
- **Docker**：`Dockerfile`, `.dockerignore`
- **環境變數**：`.env`, `.env.example`, `.env.local`

---

## 🔐 敏感檔案注意事項

### ⚠️ 不應提交到 Git 的檔案

```bash
# 後端
backend/.env                    # 包含密鑰
backend/instance/*.db          # 本地資料庫
backend/__pycache__/           # Python 快取
backend/venv/                  # 虛擬環境

# 前端
frontend/.env.local            # 本地環境變數
frontend/node_modules/         # npm 套件
frontend/dist/                 # 建置產物

# 其他
.DS_Store                      # macOS 系統檔案
*.pyc                          # Python 編譯檔案
*.log                          # 日誌檔案
```

### ✅ 應該提交的配置範例檔案

```bash
.env.example                   # 環境變數範例
backend/.env.example
backend/requirements.txt       # Python 依賴
frontend/package.json          # Node 依賴
```

---

## 🚀 下一步建議

### 新手入門順序

1. **閱讀文件**
   - `README.md` - 了解專案概況
   - 本檔案 `PROJECT_STRUCTURE.md` - 掌握檔案結構

2. **本地開發**
   - 參考 `README.md` 的 "Getting Started"
   - 執行 `./.start/dev` 啟動應用
   - 瀏覽 `http://localhost:5173`（前端）
   - 測試 `http://localhost:8888/api/docs`（API 文件）

3. **理解程式碼**
   - 從 `backend/app.py` 開始
   - 追蹤一個 API 請求流程（如登入）
   - 查看對應的前端頁面（`frontend/pages/Login.tsx`）

4. **部署到線上**
   - 閱讀 `DEPLOYMENT.md`
   - 使用 GCP Cloud Run 部署後端
   - 使用 Vercel 部署前端
   - 使用 Neon 建立 PostgreSQL 資料庫

---

## 🛠️ 工具與技術棧總覽

### 後端技術
- **框架**: Flask 3
- **ORM**: SQLAlchemy 2 + Flask-SQLAlchemy 3
- **認證**: Flask-JWT-Extended + Flask-Bcrypt
- **快取**: Redis 5 + Flask-Caching 2（選用）
- **背景任務**: Celery 5（選用）
- **即時通訊**: Flask-SocketIO 5
- **API 文件**: Flasgger (Swagger)
- **測試**: pytest + pytest-cov
- **WSGI 伺服器**: Gunicorn 21

### 前端技術
- **框架**: React 19
- **語言**: TypeScript 5.8
- **路由**: React Router 7
- **狀態管理**: React Query 5
- **即時通訊**: Socket.IO Client 4.7
- **圖表**: Recharts 3
- **建置工具**: Vite 6
- **圖示**: lucide-react

### 基礎設施
- **資料庫**: PostgreSQL 15 (Neon) / SQLite (開發)
- **快取/訊息**: Redis 7 (選用，未來擴展)
- **部署平台**:
  - **後端**: GCP Cloud Run（Docker 容器）
  - **前端**: Vercel（全球 CDN）

---

*本文件最後更新：2026 年 1 月 24 日*

*GitHub: [HrdZvezda/NexusTask](https://github.com/HrdZvezda/NexusTask)*
