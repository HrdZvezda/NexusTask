# Team Task Manager 完整部署指南

> 前後端完整部署步驟，適用於此專案和未來類似架構的專案

---

## 架構總覽

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     前端        │     │     後端        │     │    資料庫       │
│    Vercel       │────▶│  GCP Cloud Run  │────▶│     Neon        │
│   (React/Vue)   │     │    (Flask)      │     │  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
nexus-task-xi           nexustask-backend-      neon.tech
.vercel.app             xxx.run.app             (免費 512MB)
```

---

# 第一部分：資料庫設定 (Neon)

## 步驟 1：建立 Neon 帳號

1. 前往 [neon.tech](https://neon.tech)
2. 使用 GitHub 或 Google 登入
3. 建立新專案，選擇離您最近的區域

## 步驟 2：取得連線字串

1. 進入專案 Dashboard
2. 點擊 **Connect**
3. 複製連線字串（格式如下）：

```
postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

> ⚠️ 妥善保存此字串，包含密碼！

---

# 第二部分：後端部署 (GCP Cloud Run)

## 前置準備

- [ ] 已安裝 Docker Desktop
- [ ] 已安裝 gcloud CLI (`brew install google-cloud-sdk`)
- [ ] 有 Neon 資料庫連線字串

## 步驟 1：建立 Dockerfile

在 `backend/` 目錄建立 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
```

## 步驟 2：建立 .dockerignore

```
venv/
.venv/
__pycache__/
*.py[cod]
.env
.env.*
tests/
.pytest_cache/
.vscode/
.idea/
.git/
.gitignore
.DS_Store
Dockerfile
.dockerignore
*.md
```

## 步驟 3：本地測試

```bash
cd backend

# 建置映像
docker build -t my-backend .

# 測試運行
docker run -p 5001:5000 \
  -e DATABASE_URL="你的Neon連線字串" \
  -e SECRET_KEY="test-key" \
  -e FLASK_ENV="production" \
  my-backend
```

打開 http://localhost:5001 確認正常。

## 步驟 4：GCP 設定（首次使用需執行）

```bash
# 登入
gcloud auth login

# 建立專案
gcloud projects create 你的專案ID --name="專案名稱"

# 設定專案
gcloud config set project 你的專案ID

# 綁定帳單（到 GCP Console 操作）
# https://console.cloud.google.com/billing

# 啟用 API
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 步驟 5：部署到 Cloud Run

```bash
cd backend

gcloud run deploy 服務名稱 \
  --source . \
  --platform managed \
  --region asia-east1 \
  --port 5000 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=xxx,SECRET_KEY=xxx,FLASK_ENV=production"
```

部署成功後會顯示 Service URL，例如：
```
https://服務名稱-xxxxx.asia-east1.run.app
```

**記下這個 URL，前端需要用！**

---

# 第三部分：前端部署 (Vercel)

## 步驟 1：連接 GitHub

1. 前往 [vercel.com](https://vercel.com)
2. 使用 GitHub 登入
3. 點擊 **Import Project**
4. 選擇您的 GitHub Repository

## 步驟 2：設定建置

| 設定項目 | 值 |
|---------|-----|
| Framework Preset | Vite / Next.js / React |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` 或 `.next` |

## 步驟 3：設定環境變數（重要！）

在 Vercel 專案設定 → Environment Variables：

| 變數名稱 | 值 |
|---------|-----|
| `VITE_API_URL` | `https://你的服務.run.app` |

> 如果用 Next.js，變數名稱是 `NEXT_PUBLIC_API_URL`

## 步驟 4：部署

點擊 **Deploy** 即可！

Vercel 會給您一個 URL，例如：
```
https://你的專案.vercel.app
```

---

# 第四部分：連接前後端

## 更新前端 API URL

後端部署完成後，要更新前端的環境變數：

1. 在 Vercel Dashboard 進入專案
2. Settings → Environment Variables
3. 更新 `VITE_API_URL` 為 Cloud Run 的 URL
4. Redeploy（重新部署）

---

# 常用指令速查

## 後端 (GCP)

```bash
# 查看服務
gcloud run services list

# 查看日誌
gcloud run logs read --service 服務名稱 --region asia-east1

# 重新部署
gcloud run deploy 服務名稱 --source . --region asia-east1

# 刪除服務
gcloud run services delete 服務名稱 --region asia-east1
```

## 前端 (Vercel)

```bash
# 安裝 Vercel CLI
npm i -g vercel

# 部署
vercel

# 部署到生產
vercel --prod
```

---

# 故障排除

## 後端問題

| 問題 | 解決方法 |
|------|---------|
| Port 錯誤 | 加 `--port 5000` |
| 資料庫連不上 | 檢查 DATABASE_URL |
| 權限錯誤 | `sudo chown -R $(whoami) ~/.config` |

## 前端問題

| 問題 | 解決方法 |
|------|---------|
| API 404 | 確認 VITE_API_URL 正確 |
| CORS 錯誤 | 後端需設定 CORS 允許前端域名 |
| 建置失敗 | 檢查 Build Command 和 Output Directory |

---

# 費用估算（側專案）

| 服務 | 費用 |
|------|------|
| Vercel (前端) | $0（免費方案）|
| Cloud Run (後端) | $0（免費額度內）|
| Neon (資料庫) | $0（免費 512MB）|
| Upstash Redis（選用）| $0（免費方案）|
| **總計** | **$0/月** |

---

# 選用功能：Redis 部署（背景任務/Email）

> ⚠️ **此功能為選用**，Side Project 初期不需要設定

## 什麼時候需要 Redis？

| 功能需求 | 需要 Redis？ |
|---------|-------------|
| 基本 CRUD 操作 | ❌ 不需要 |
| 發送 Email（異步）| ✅ 需要 |
| 背景任務（Celery）| ✅ 需要 |
| 跨多個 Cloud Run 實例的 Rate Limiting | ✅ 建議有 |

## 免費 Redis：使用 Upstash

1. 前往 [upstash.com](https://upstash.com)
2. 使用 GitHub 登入
3. 建立 Redis 資料庫，選擇離您最近的區域
4. 複製 Redis URL（格式：`redis://default:xxx@xxx.upstash.io:6379`）

## 更新 Cloud Run 環境變數

```bash
gcloud run deploy nexustask-backend \
  --region asia-east1 \
  --update-env-vars "REDIS_URL=redis://default:xxx@xxx.upstash.io:6379"
```

## 關於 Celery Worker

如果要使用 Celery 背景任務（例如異步發送 Email），還需要：

1. **另外部署 Celery Worker**（需要額外的 Cloud Run 服務或 VM）
2. 這會增加複雜度和可能的費用

### 替代方案：同步發送 Email

對於 Side Project，建議改成**同步發送 Email**（不透過 Celery）：
- 優點：不需要 Redis 和 Celery Worker
- 缺點：使用者需等待 1-2 秒

---

# 部署檢查清單

## 必要服務

- [x] Neon 資料庫（免費）
- [x] GCP Cloud Run 後端（免費額度）
- [x] Vercel 前端（免費）

## 選用服務

- [ ] Upstash Redis（需要 Email/背景任務時才設定）
- [ ] Celery Worker（需要異步任務時才設定）
- [ ] 自訂域名（需要時再設定）

---

# 本專案部署資訊

| 服務 | URL / 資訊 |
|------|------------|
| 前端 | https://nexus-task-xi.vercel.app |
| 後端 | https://nexustask-backend-160761384347.asia-east1.run.app |
| 資料庫 | Neon PostgreSQL (ap-southeast-1) |
| Redis | 未設定（目前不需要）|

---

# 更新記錄

| 日期 | 更新內容 |
|------|---------|
| 2026-01-24 | 初始部署：後端部署至 GCP Cloud Run |
