#!/bin/bash
# 生成安全的密鑰
# 用法: ./scripts/generate-secrets.sh

echo "=== NexusTeam 密鑰生成器 ==="
echo ""

echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo ""

echo "將以上密鑰複製到你的 .env 檔案中"
echo ""

echo "完整 .env 範例："
echo "================================"
cat << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://user:password@host:5432/nexusteam
REDIS_URL=redis://host:6379/0
CACHE_TYPE=RedisCache
CORS_ORIGINS=https://your-frontend.vercel.app
ENABLE_RATE_LIMIT=true
PASSWORD_MIN_LENGTH=8
EOF
echo "================================"
