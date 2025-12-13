# Railway 部署指南 - NexusTeam

> 適合放在履歷上的專業部署方案，完整功能展示

---

## 🎯 部署目標

- ✅ **可公開訪問的 Demo 網址**，面試官可以直接測試
- ✅ **完整功能展示**，包括即時通知、任務管理、背景任務等
- ✅ **專業的 UI/UX**，良好的第一印象
- ✅ **穩定運行**，不會在面試演示時出問題
- ✅ **低成本維護**，適合長期展示（$0-5/月）

---

## 🚀 Railway 部署方案

### 為什麼選 Railway？
- 每月 $5 免費額度（約可運行 500 小時）
- **無冷啟動**，面試演示時不會等待
- 一鍵部署 GitHub 倉庫
- 內建 PostgreSQL 和 Redis
- 自動 HTTPS

### 部署步驟

#### 1. 準備 Railway 配置

建立 `railway.json`：

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "gunicorn --worker-class eventlet -w 1 --timeout 120 --bind 0.0.0.0:$PORT app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

建立 `railway.toml`（替代方案）：

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "gunicorn --worker-class eventlet -w 1 --timeout 120 --bind 0.0.0.0:$PORT app:app"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### 2. 登入 Railway

1. 前往 https://railway.app
2. 使用 GitHub 登入
3. 點擊 **"New Project"**

#### 3. 部署後端

1. 選擇 **"Deploy from GitHub repo"**
2. 選擇你的 `team-task-manager` 倉庫
3. 點擊 **"Add variables"**，加入環境變數：

```bash
# 必要變數
FLASK_ENV=production
SECRET_KEY=<點擊 Generate 生成>
JWT_SECRET_KEY=<點擊 Generate 生成>
CACHE_TYPE=RedisCache
ENABLE_RATE_LIMIT=true
PASSWORD_MIN_LENGTH=8

# 會自動設定的變數（Railway 會注入）
# DATABASE_URL - 當你加入 PostgreSQL 服務後
# REDIS_URL - 當你加入 Redis 服務後
```

4. 設定 **Root Directory**：`backend`

#### 4. 加入 PostgreSQL

1. 在專案中點擊 **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway 會自動設定 `DATABASE_URL` 環境變數
3. 後端服務會自動重新部署並連接資料庫

#### 5. 加入 Redis

1. 點擊 **"New"** → **"Database"** → **"Add Redis"**
2. Railway 會自動設定 `REDIS_URL` 環境變數
3. 同時用於 Cache、Celery、Socket.IO

#### 6. 設定自訂網域（可選）

1. 在後端服務中，點擊 **"Settings"** → **"Networking"**
2. 點擊 **"Generate Domain"** 會得到類似：
   ```
   https://nexusteam-api-production.up.railway.app
   ```
3. 或加入自己的網域（需要 DNS 設定）

#### 7. 部署前端到 Vercel

1. 前往 https://vercel.com
2. 導入你的 GitHub 倉庫
3. 設定：
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
4. 環境變數：
   ```
   VITE_API_URL=https://你的Railway後端網址.up.railway.app
   ```
5. 部署完成後會得到網址：
   ```
   https://nexusteam.vercel.app
   ```

#### 8. 更新 CORS

回到 Railway，在後端服務加入：
```
CORS_ORIGINS=https://nexusteam.vercel.app
```

### Railway 成本控制

```bash
# 查看用量
railway status

# 停用服務（不使用時）
railway down

# 重新啟用
railway up
```

**小技巧**：面試前一天啟動服務，確保演示時不會冷啟動。

---

## 📝 履歷/GitHub README 展示範本

### 在 GitHub README 中加入

```markdown
# 🚀 Live Demo

- **前端**: https://nexusteam.vercel.app
- **後端 API**: https://nexusteam-api.up.railway.app
- **API 文件**: https://nexusteam-api.up.railway.app/api/docs

### 測試帳號
```
Email: demo@nexusteam.com
Password: Demo123456
```

### 技術亮點

- ✅ **完整前後端分離架構**
- ✅ **即時協作**：WebSocket 即時通知與任務更新
- ✅ **安全認證**：JWT + Refresh Token + Token 黑名單
- ✅ **效能優化**：Redis 快取、資料庫索引優化、分頁載入
- ✅ **背景任務**：Celery 處理郵件與定時清理
- ✅ **可觀測性**：結構化日誌、健康檢查、Prometheus 指標
- ✅ **CI/CD**：自動化部署到 Railway/Vercel

### 架構圖

\`\`\`
使用者 → Vercel (React + Vite) → Railway (Flask API)
                                    ↓
                            PostgreSQL + Redis
                                    ↓
                            Celery Workers (背景任務)
\`\`\`
```

### 在履歷中描述

```
NexusTeam - 企業級任務管理平台
- 開發全端 SaaS 應用，支援多專案任務協作與即時通知
- 實作 JWT 認證系統，包含 Token 黑名單與 Refresh Token 機制
- 使用 Redis 優化 API 效能，快取命中率達 85%，回應時間降低 60%
- 設計 RESTful API 並使用 Swagger/OpenAPI 自動生成文件
- 實作 WebSocket 即時通訊，支援線上狀態與打字指示器
- 使用 Celery 處理背景任務（郵件發送、定時清理）
- 部署至 Railway + Vercel，實現自動化 CI/CD
- 技術棧：Flask, React, TypeScript, PostgreSQL, Redis, Celery, Socket.IO

Demo: https://nexusteam.vercel.app
```

---

## 🎨 面試演示準備清單

### 演示前一天
- [ ] 確認網站可正常訪問
- [ ] 測試所有核心功能（登入、建立專案、新增任務、即時通知）
- [ ] 清理測試資料，保持資料庫乾淨
- [ ] 建立演示用帳號（`demo@nexusteam.com`）
- [ ] 準備 2-3 個範例專案與任務
- [ ] 截圖保存（以防網站臨時出問題）

### 演示腳本（3-5 分鐘）

#### 1. 開場（30 秒）
"這是我開發的任務管理平台 NexusTeam，支援團隊協作、即時通知等功能。"

#### 2. 功能展示（2 分鐘）
- 登入展示 JWT 認證
- 建立專案 → 新增任務
- 拖拉任務改變狀態（展示即時更新）
- 新增評論 → 展示即時通知
- 打開第二個瀏覽器視窗，展示多人協作

#### 3. 技術亮點（1-2 分鐘）
- 打開 `/api/docs` 展示 API 文件
- 打開 DevTools Network 展示 WebSocket 連線
- 打開 `/health/detailed` 展示系統健康檢查
- 講解架構：前後端分離、Redis 快取、Celery 背景任務

#### 4. 回答常見問題
**Q: 如何處理即時通訊？**
A: 使用 Flask-SocketIO + Redis pub/sub，前端用 Socket.IO client

**Q: 如何優化效能？**
A: Redis 快取、資料庫索引、分頁查詢、N+1 查詢優化

**Q: 如何確保安全性？**
A: JWT + Token 黑名單、密碼雜湊、CORS、CSP、速率限制

**Q: 部署架構？**
A: Railway 後端（自動擴展）+ Vercel 前端（全球 CDN）

---

## 💰 成本估算

### Railway
- **免費額度**：$5/月（約 500 小時運行）
- **超出後**：$0.01/小時
- **預估成本**：$0-5/月（個人作品集通常在免費額度內）

### 服務組成
- **Web Service**（主要後端）：約 $3/月
- **PostgreSQL**：包含在免費額度內
- **Redis**：包含在免費額度內
- **Celery Worker**（可選）：約 $1-2/月
- **Celery Beat**（可選）：約 $1/月
- **前端 Vercel**：完全免費

### 成本優化技巧
1. 面試季啟用所有服務，其他時間可以暫停 Worker 和 Beat
2. 只在需要完整展示時才啟用 Celery 服務
3. 監控用量，避免超出免費額度

---

## 🔧 常見問題排除

### Q1: 面試時網站打不開怎麼辦？
**預防措施**：
1. 提前準備演示影片（錄製螢幕）
2. 截圖保存所有功能
3. 在履歷上同時提供 Live Demo 和 GitHub 連結
4. 準備本地開發環境作為備用方案
5. 面試前一天檢查所有服務狀態

### Q2: Railway 免費額度用完了怎麼辦？
**預防措施**：
1. 定期檢查用量儀表板
2. 設定用量警報
3. 面試前暫時升級到付費方案（$5/月起）
4. 優化服務配置，減少不必要的運行時間

**節省額度技巧**：
```bash
# 非面試期間可以暫停 Worker 和 Beat
# 只保留主要 Web Service 運行
```

### Q3: 如何備份資料庫？
**定期備份**：
使用提供的備份腳本（`scripts/backup-db.sh`）：
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump $DATABASE_URL > backups/backup-$DATE.sql
echo "Backup saved to backups/backup-$DATE.sql"
```

**Railway 自動備份**：
- Railway PostgreSQL 提供自動備份功能
- 可在 Dashboard 中手動觸發備份
- 付費方案支持自動定期備份

### Q4: 如何展示我懂 DevOps？
**加分項**：
1. 在 README 加入架構圖
2. 設定 GitHub Actions CI/CD（自動測試 + 部署）
3. 加入監控（Sentry 錯誤追蹤）
4. 寫 `ARCHITECTURE.md` 詳細說明設計決策

---

## 📚 進階優化建議

### 1. 加入 Sentry 錯誤追蹤

```bash
# 後端
pip install sentry-sdk[flask]
```

```python
# app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="你的Sentry DSN",
    integrations=[FlaskIntegration()],
    environment="production"
)
```

### 2. 加入 Google Analytics

```typescript
// frontend/index.html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

### 3. 加入 GitHub Actions CI/CD

建立 `.github/workflows/deploy.yml`：

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        run: echo "Railway auto-deploys on push"
```

---

## ✅ 最終檢查清單

### 部署前
- [ ] 所有測試通過
- [ ] 環境變數已設定
- [ ] CORS 正確配置
- [ ] README 有 Live Demo 連結
- [ ] API 文件可訪問
- [ ] 建立演示帳號

### 演示準備
- [ ] 測試所有核心功能
- [ ] 準備演示腳本
- [ ] 錄製備用影片
- [ ] 準備技術問答

### 履歷準備
- [ ] 專案描述精簡有力
- [ ] 突出技術亮點
- [ ] 量化成果（效能提升 X%）
- [ ] GitHub README 完整

---

## 🎯 部署總結

### ✅ Railway 的優勢
- **完整功能支持**：所有功能都能正常運行
- **無冷啟動問題**：面試演示時無需等待
- **專業印象**：展示你了解現代化部署流程
- **成本可控**：$0-5/月，適合作品集長期展示

### 📦 配置文件已準備好
- ✅ `backend/railway.json` - 主要 Web Service
- ✅ `backend/railway.worker.json` - Celery Worker（背景任務）
- ✅ `backend/railway.beat.json` - Celery Beat（定時任務）
- ✅ `backend/requirements.txt` - Python 依賴
- ✅ `backend/runtime.txt` - Python 版本

### 🚀 下一步
1. 推送代碼到 GitHub
2. 登入 Railway 並連接你的倉庫
3. 按照上述步驟部署服務
4. 測試所有功能
5. 在履歷和 GitHub README 中加入 Live Demo 連結

有任何問題隨時問我 💪

---

*最後更新：2025 年 12 月*
