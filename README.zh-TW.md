# NexusTeam - 安全任務協作平台

**繁體中文** | **[English](./README.md)**

NexusTeam 是一個全端協作套件，專注於後端韌性、安全性和架構清晰度。Flask API 透過服務層、快取、背景任務、即時事件和結構化可觀測性提供模組化藍圖，React 前端則透過 React Query 和 Socket.IO 使用 API。

## 🚀 線上展示

| 服務 | URL |
|------|-----|
| **前端** | [https://nexus-task-xi.vercel.app](https://nexus-task-xi.vercel.app) |
| **後端 API** | [https://nexustask-backend-160761384347.asia-east1.run.app](https://nexustask-backend-160761384347.asia-east1.run.app) |

> 展示帳號：`howard@test.com` / `password`

---

## 目錄

- [概述](#概述)
- [功能亮點](#功能亮點)
- [架構快照](#架構快照)
- [技術棧](#技術棧)
- [專案結構](#專案結構)
- [後端能力](#後端能力)
- [前端體驗](#前端體驗)
- [快速開始](#快速開始)
  - [先決條件](#先決條件)
  - [快速啟動](#快速啟動)
  - [手動設定](#手動設定)
  - [環境變數](#環境變數)
- [API 文件與健康檢查](#api-文件與健康檢查)
- [統一 API 回應](#統一-api-回應)
- [測試與品質關卡](#測試與品質關卡)
- [部署檢查清單](#部署檢查清單)
- [路線圖](#路線圖)
- [貢獻](#貢獻)
- [授權](#授權)
- [維護者](#維護者)

## 概述

- 為需要任務編排、審計追蹤、即時感知和治理的團隊提供安全工作空間。
- 後端透過專用服務、儲存庫、快取管理器、驗證器、DTO 和 `ServiceResult` 回應遵循 SRP/OCP/LSP/DIP 原則。
- 營運工具涵蓋速率限制、Redis 快取、Celery workers/beat、結構化日誌、Swagger 文件和多階段健康探測。
- React + React Query 提供樂觀的、支援離線的客戶端，可選的 Socket.IO hooks 在伺服器推送更新時自動更新快取。

## 功能亮點

**安全性與合規性**
- 可設定的密碼政策（`PASSWORD_MIN_LENGTH`、大寫/數字/特殊字元標誌）加上 bcrypt 雜湊和 JWT access/refresh tokens。
- LoginAttempt 審計日誌、IP 感知速率限制，以及重複失敗後的自動帳號鎖定保護認證流程。
- 忘記/重設密碼流程發出簽署 token、透過 Celery 排程交易郵件，並定期清除過期/已使用的 token。
- 安全標頭（CSP、HSTS、X-Frame-Options、Referrer-Policy）、請求大小上限、維護模式中介軟體和消毒後的錯誤回應。

**效能與擴展性**
- Task（`idx_task_assigned_due`、`idx_task_project_priority`、`idx_task_project_assigned`）和 Notification 表的複合索引加速過濾。
- 分頁加上留言計數子查詢消除 `/projects/:id/tasks`、`/tasks/all` 和 `/tasks/my` 上的 N+1 查詢。
- CacheKeyManager + CacheTimeout 列舉集中管理鍵格式和 TTL，而失效輔助函式在寫入時清除使用者、專案和通知快取。
- Redis 儲存快取項目、速率限制計數器、Celery 訊息和 Socket.IO 會話資料，實現水平擴展。

**協作與自動化**
- Celery handlers 涵蓋電子郵件、通知廣播、逾期提醒、專案快照生成和多個清理例程；beat 排程每天執行它們。
- Flask-SocketIO 發布通知/任務/成員/留言事件，並追蹤線上使用者、輸入指示器和專案房間。
- 統一的 API 回應建構器、DTO 和服務層驗證器讓每個端點都可預測且可測試。

**營運卓越性**
- Health 藍圖公開 `/health`、`/health/live`、`/health/ready`、`/health/detailed`、`/health/metrics` 和 `/health/version` 供負載平衡器和監控使用。
- Structlog + python-json-logger 與輪替檔案處理器、每請求 ID 和請求/回應日誌 hooks 整合。
- Swagger/OpenAPI（`/api/docs` + `/api/docs/swagger.json`）記錄每個藍圖的標籤、模式、錯誤代碼和速率限制說明。

## 架構快照

請求從 React 客戶端流入模組化 Flask 藍圖，經過服務層，進入協調 SQLAlchemy、快取和背景佇列的儲存庫。Redis 支援速率限制、Celery 和 Socket.IO，而健康探測和結構化日誌公開系統狀態。

```
┌────────────── 前端 (React + React Query + Socket.IO) ──────────────┐
│ AuthProvider · QueryProvider · useApi/useSocket hooks              │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTPS / WebSocket
┌────────────────────────────┴───────────────────────────────────────┐
│         後端 (Flask Blueprints + Services + Core Infrastructure)   │
│  api/* blueprints  →  services/*Service  →  repositories/models    │
│  core/cache · core/celery_tasks · core/socket_events · utils/response │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                 PostgreSQL/SQLite · Redis · Celery Workers/Beat
```

## 技術棧

### 前端

| 層級 | 技術 | 用途 |
| --- | --- | --- |
| UI 框架 | React 19 + TypeScript 5.8 | 元件模型 + 靜態型別 |
| 路由 | React Router 7 (HashRouter) | 無需後端重寫的 SPA 路由 |
| 伺服器狀態 | @tanstack/react-query 5 | 取得、快取、樂觀更新 |
| 圖表與視覺化 | Recharts 3 | 儀表板指標 |
| 圖示 | lucide-react 0.554 | 輕量圖示集 |
| 建構工具 | Vite 6 | 開發伺服器、HMR、打包 |
| 即時通訊 | socket.io-client 4.7 | WebSocket 傳輸至 Flask-SocketIO |

### 後端

| 層級 | 技術 | 用途 |
| --- | --- | --- |
| Web 框架 | Flask 3 | 藍圖、中介軟體、CLI |
| 認證與安全 | Flask-JWT-Extended, Flask-Bcrypt, Flask-Limiter | JWT 發行、雜湊、速率限制 |
| ORM 與資料庫 | Flask-SQLAlchemy 3 (SQLAlchemy 2) | 模型、程式碼遷移 |
| 驗證 | Marshmallow 3 | DTO/模式驗證 |
| 快取與訊息 | Redis 5, Flask-Caching 2, Celery 5, APScheduler 3 | 記憶體加速 + 非同步工作 |
| 即時通訊 | Flask-SocketIO 5 + python-socketio 5 + eventlet | 推送通知和任務串流 |
| API 文件 | Flasgger + flask-swagger-ui | Swagger UI + OpenAPI JSON |
| 可觀測性 | structlog, python-json-logger, RotatingFileHandler | 結構化日誌 + 檔案保留 |

### 基礎設施與工具

| 需求 | 選擇 | 說明 |
| --- | --- | --- |
| 本地工作流程 | `.start/dev` 腳本 | venv/npm install 後啟動後端 + 前端 |
| 測試 | pytest, pytest-cov | 單元/整合覆蓋率 |
| 品質關卡 | black, flake8, mypy | 格式化、程式碼檢查、型別檢查 |
| 部署執行環境 | Gunicorn 21 (eventlet workers) | 生產 WSGI + WebSocket 支援 |
| 資料儲存 | SQLite (開發) / PostgreSQL (生產) | 透過 `DATABASE_URL` 設定 |
| 訊息/快取 | Redis 5 | 速率限制、Celery broker/result、快取儲存 |

## 專案結構

```
nexusteam/
├── backend/
│   ├── api/                        # 藍圖 (auth, projects, tasks, notifications, members, uploads, health)
│   ├── core/                       # Cache, Celery tasks, middleware, socket events, Swagger config
│   │   └── token_blacklist.py      # JWT Token 撤銷系統 (Redis/記憶體)
│   ├── services/                   # 服務層 (BaseService, auth/project/task/notification services)
│   │   └── permissions.py          # 集中式權限檢查（避免循環引用）
│   ├── utils/                      # 工具函數
│   │   ├── response.py             # ApiResponse factory, ErrorCode enum, ResponseBuilder
│   │   └── validators.py           # 共用驗證（Marshmallow、密碼、日期、Email、分頁）
│   ├── models.py                   # models_legacy 的橋接（向後相容）
│   ├── models_legacy.py            # SQLAlchemy 模型 + 索引
│   ├── config.py                   # 環境驅動的設定
│   ├── app.py                      # Flask 入口點、中介軟體連接、藍圖
│   ├── Dockerfile                  # Docker 容器建置配置
│   ├── requirements.txt            # 後端依賴
│   └── tests/                      # pytest 測試套件
├── frontend/
│   ├── App.tsx                     # 認證感知路由器 + QueryProvider + NotificationProvider
│   ├── hooks/useApi.ts             # React Query hooks + 樂觀更新
│   ├── hooks/useSocket.ts          # Socket.IO 輔助 + 房間輔助
│   ├── providers/QueryProvider.tsx # React Query 客戶端啟動
│   ├── context/AuthContext.tsx     # 認證會話狀態
│   ├── context/NotificationContext.tsx # 共享通知狀態（Dashboard 與 Notifications 同步）
│   └── pages/...                   # UI 頁面
├── .start/dev                      # 啟動兩個應用程式的便利腳本
├── DEPLOYMENT.md                   # 部署指南（GCP Cloud Run + Vercel + Neon）
├── CODE_REVIEW.md                  # 程式碼審查報告
└── README.md
```


## 後端能力

### 服務層流程
- `api/*.py` 藍圖驗證輸入、附加速率限制，並將工作委派給 `services/*.py`。
- 服務繼承自 `BaseService`，回傳 `ServiceResult`，並可以組合儲存庫、驗證器（`SchemaValidator`）和權限輔助函式。
- 儲存庫包裝 SQLAlchemy 模型，而 `UnitOfWork` 保持交易緊密且回滾安全。
- `utils/response.ApiResponse` 和 `ResponseBuilder` 將 `ServiceResult` 物件轉換為統一的 payload 封包（success/data/meta 或 error/code/details）。
- 快取失效輔助函式（`invalidate_user_cache`、`invalidate_project_stats` 等）在資料庫寫入旁觸發，以保持 Redis 同步。

### 安全支柱
- 密碼要求、bcrypt 雜湊和 JWT access/refresh tokens 可按環境設定。
- LoginAttempt 記錄和 limiter 裝飾器強制鎖定；`/auth/login`、`/auth/register` 和 `/auth/forgot-password` 有更嚴格的速率限制。
- 密碼重設 token 對應到使用者，在一小時內過期，並在被 Celery 電子郵件處理器使用後標記為已使用。
- 中介軟體堆疊注入 CSP、HSTS（當 TLS + 非除錯時）、frame/XSS 保護、請求 ID、維護模式閘道和請求大小強制執行。
- JWT 回調集中錯誤處理（過期、無效、撤銷、遺失）以保持回應可預測。

### 效能與可靠性
- 分頁預設值（`DEFAULT_PAGE_SIZE`、`MAX_PAGE_SIZE`）保護繁重的任務端點；查詢參數 `page` 和 `per_page` 在所有地方都被遵守。
- 留言計數透過單一子查詢取得並連接回任務 payload，以消除 N+1 留言查找。
- CacheKeyManager 和 CacheTimeout 列舉編纂使用者、專案統計、通知和成員名冊的鍵格式和 TTL。
- Redis 是快取、速率限制、Socket.IO 狀態和 Celery broker/result 後端的單一事實來源，實現未來的水平擴展。
- 資料庫索引和 SQLAlchemy `text` 使用即使對於大型表也保持過濾/重新排序便宜。

### 即時通訊與背景工作
- `core/socket_events.py` 透過 JWT 認證 socket，追蹤已連接的使用者，公開加入/離開專案房間、輸入指示器，並響應服務事件發出事件（`task_created`、`task_updated`、`notification` 等）。
- `core/celery_tasks.py` 定義電子郵件、密碼重設、通知廣播、登入嘗試清理、密碼重設清理、通知清理、活動修剪、逾期提醒和專案統計快照的處理器。
- Celery beat 排程每天執行清理和快照任務；存在臨時入隊的命令。
- APScheduler 就緒的抽象允許遷移排程或在需要時混合 cron 風格的作業與 Celery beat。

### 可觀測性與營運
- Health 藍圖回傳存活性、就緒性、依賴診斷（DB、Redis、快取）、聚合指標（使用者/專案/任務/通知）和版本元資料。
- 中介軟體記錄每個請求/回應的時間，附加 `X-Request-ID`，並跳過嘈雜的健康路由。
- `setup_structured_logging`（可選）在您偏好機器可讀遙測時啟用與 ELK/Datadog 相容的 JSON 日誌。
- 輪替檔案處理器在生產模式下寫入 `logs/app.log` 和 `logs/error.log`；`LOG_LEVEL` 驅動詳細程度。
- 維護模式（`MAINTENANCE_MODE=true`）立即回傳 503 回應（除了健康端點）用於部署。

## 前端體驗

- `App.tsx` 用 `QueryProvider` 和 `AuthProvider` 包裝路由器，因此每個路由都透過 `ProtectedRoute` 強制執行認證。
- React Query hooks（`useApi.ts`）集中取得、快取、分頁和專案、任務、留言、通知和個人檔案設定的樂觀更新。
- `useSocket.ts` 管理 Socket.IO 客戶端，加入專案房間，監視通知/任務/成員/留言，處理輸入指示器，並在即時事件到達時使快取失效。
- Layout/components 提供一致的導航、儀表板、專案看板和個人任務清單，而查詢 hooks 確保資料與後端保持同步。

## 快速開始

### 先決條件

- Python 3.10+
- Node.js 18+ 和 npm（或 Yarn）
- Redis 5+（速率限制、快取、Celery 和 Socket.IO 所需）
- PostgreSQL 14+（可選；SQLite 是預設的開發資料庫）
- OpenSSL 用於本地執行 HTTPS 的 TLS 金鑰

### 快速啟動

```bash
./.start/dev
```

輔助腳本釋放埠 8888/5173，啟動 `backend/venv`，啟動 `python app.py`，然後執行 `npm run dev`。第一次執行仍需要您建立虛擬環境並安裝依賴（見下文）。

### 手動設定

#### 後端 API

1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate`（Windows: `venv\Scripts\activate`）
4. `pip install -r requirements.txt`
5. 建立 `.env` 檔案（見[環境變數](#環境變數)）或在 shell 中匯出變數。
6. 初始化資料庫（表在啟動時透過 `db.create_all()` 自動建立）。
7. 啟動 API：

```bash
FLASK_DEBUG=true FLASK_PORT=8888 python app.py
# 或: FLASK_DEBUG=true flask --app app run --port 8888
```

#### Celery Workers 與 Scheduler

Celery 依賴相同的 `.env` 和 Redis 設定：

```bash
cd backend
source venv/bin/activate
celery -A core.celery_tasks.celery worker --loglevel=info
celery -A core.celery_tasks.celery beat --loglevel=info
```

Workers 處理電子郵件/通知/清理任務；beat 觸發 `core/celery_tasks.py` 中定義的每日排程。

#### 前端

```bash
cd frontend
npm install
npm run dev    # 服務於 http://localhost:5173
```

如果後端在不同的來源上執行，在 `frontend/.env.local` 中設定 `VITE_API_URL`。

#### 支援服務

- **Redis**: `brew services start redis`（macOS）或 `docker run --name nexusteam-redis -p 6379:6379 redis:7`
- **PostgreSQL**（可選）: 更新 `DATABASE_URL=postgresql://user:pass@localhost:5432/nexusteam`
- **Email**（可選）: 提供 `MAIL_SERVER`、`MAIL_USERNAME` 和 `MAIL_PASSWORD` 以啟用密碼重設郵件

### 環境變數

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `FLASK_ENV` | `development` | Flask 環境（`development`、`testing`、`production`）|
| `FLASK_DEBUG` | `False` | 啟用自動重新載入 + 詳細錯誤 |
| `SECRET_KEY` | `dev-secret-key...` | Flask 會話密鑰 |
| `JWT_SECRET_KEY` | 鏡像 `SECRET_KEY` | JWT 簽署密鑰 |
| `DATABASE_URL` | `sqlite:///task_manager.db` | SQLAlchemy 連接字串 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 用於快取、limiter、Celery、Socket.IO |
| `CELERY_BROKER_URL` | `REDIS_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | `REDIS_URL` | Celery result backend |
| `ENABLE_RATE_LIMIT` | `false` | 即使在開發中也強制速率限制 |
| `PASSWORD_MIN_LENGTH` | `8` | 密碼長度要求 |
| `PASSWORD_REQUIRE_UPPERCASE/NUMBERS/SPECIAL` | `False` | 額外的密碼限制 |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | `1` | Access token 生命週期 |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | `30` | Refresh token 生命週期 |
| `MAX_CONTENT_LENGTH` | `16777216` | 上傳大小（bytes）|
| `MAIL_*` | none | 密碼重設郵件的 SMTP 設定 |
| `LOG_LEVEL` | `INFO` | 日誌層級 |
| `API_VERSION` | `2.1.0` | 在 `/` 和健康端點中顯示 |
| `MAINTENANCE_MODE` | `False` | 對非健康路由回傳 503 |

範例 `.env`：

```env
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=請替換這個
JWT_SECRET_KEY=也請替換這個
DATABASE_URL=sqlite:///task_manager.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
ENABLE_RATE_LIMIT=false
PASSWORD_MIN_LENGTH=10
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=app-specific-password
MAIL_DEFAULT_SENDER=noreply@nexusteam.local
```

## API 文件與健康檢查

- **Swagger UI**: `http://localhost:8888/api/docs`
- **OpenAPI JSON**: `http://localhost:8888/api/docs/swagger.json`

健康端點：

| 端點 | 用途 |
| --- | --- |
| `/health` | 基本健康 + DB ping |
| `/health/live` | 存活性探測 |
| `/health/ready` | 就緒性（檢查 DB 連線）|
| `/health/detailed` | 完整依賴檢查（DB、Redis、快取）+ 系統資訊 |
| `/health/metrics` | 使用者/專案/任務/通知的聚合計數 |
| `/health/version` | 建構元資料和 API 版本 |

所有路由發出統一回應格式，並在啟用時附加 `X-Request-ID` 和速率限制標頭。

## 統一 API 回應

`utils/response.py` 強制執行單一 payload 形狀：

```json
// 成功
{
  "success": true,
  "data": {... 領域 payload ...},
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 125,
      "total_pages": 7,
      "has_next": true
    }
  }
}

// 錯誤
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "標題為必填",
    "details": {"title": ["必填欄位缺少資料。"]}
  }
}
```

每個藍圖透過 `ResponseBuilder` 和 `ErrorCode` 列舉建構回應，使客戶端易於處理成功/錯誤分支，而無需每個端點特殊處理。

## 測試與品質關卡

```bash
cd backend
source venv/bin/activate

# 執行所有測試
pytest

# 執行覆蓋率測試
pytest --cov=. --cov-report=term-missing

# 程式碼檢查 / 格式化 / 型別檢查
black .
flake8 .
mypy .
```

前端測試尚未連接；在啟用 CI 關卡之前，在路線圖部分新增 Vitest/React Testing Library。

## 部署檢查清單

- 建構前端（`cd frontend && npm install && npm run build`）並提供靜態資產（或單獨部署）。
- 設定 `FLASK_ENV=production`、`ENABLE_RATE_LIMIT=true`、`MAINTENANCE_MODE=false`，並設定強密鑰。
- 在生產中使用 PostgreSQL，將 `DATABASE_URL` 指向您的叢集。
- 使用 Gunicorn + eventlet workers 啟動 API 以保持 Socket.IO 功能：

```bash
cd backend
source venv/bin/activate
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8888 app:app
```

- 在 Supervisor/systemd 下執行至少一個 Celery worker 和一個 beat 實例。
- 確保 Redis 可訪問以支援快取、速率限制、Socket.IO 和 Celery。
- 將結構化日誌連接到您的日誌傳送器（在啟動期間呼叫 `setup_structured_logging(app)` 或設定處理器）。
- 監控 `/health/*` 端點和速率限制標頭；對緩慢的 DB/Redis 檢查或 5xx 激增發出警報。
- 在您的代理/負載平衡器上終止 TLS，並對 HTTPS 流量保持 HSTS 啟用。

## 部署

本專案使用**免費方案**部署：

| 服務 | 平台 | 費用 |
|------|------|------|
| 前端 | Vercel | 免費 |
| 後端 | GCP Cloud Run | 免費額度 |
| 資料庫 | Neon PostgreSQL | 免費 512MB |

詳細部署說明請參考 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 路線圖

| 領域 | 狀態 | 說明 |
| --- | --- | --- |
| 即時任務與通知串流 | 完成 | Flask-SocketIO + `useSocket` hooks |
| 密碼政策 + 帳號鎖定 | 完成 | 設定驅動 + LoginAttempt 審計 |
| 自動清理與專案快照 | 完成 | Celery beat 排程（每日作業）|
| 電子郵件/通知摘要 | 進行中 | 提供 SMTP 憑證 + 擴展 Celery handlers |
| **GCP Cloud Run 部署** | **完成** | Docker 容器化 + Neon PostgreSQL |
| 深色模式與響應式優化 | 計劃中 | 需要更新的設計 tokens |
| CI/CD 與前端單元測試 | 計劃中 | 新增 Vitest + 管道範圍的品質關卡 |

## 貢獻

1. Fork 此儲存庫。
2. 建立功能分支：`git checkout -b feature/my-change`。
3. 提交您的變更：`git commit -m 'Add amazing feature'`。
4. 推送到分支：`git push origin feature/my-change`。
5. 開啟 Pull Request。

## 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案。

## 維護者

**Howard Li**
- Email: HrdZvezda@gmail.com
- GitHub: [@HrdZvezda](https://github.com/HrdZvezda)

---

如果這個專案對您有幫助，請給它一個 ⭐！

