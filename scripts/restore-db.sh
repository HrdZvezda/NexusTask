#!/bin/bash
# 資料庫還原腳本
# 用法: ./scripts/restore-db.sh backups/nexusteam_backup_20251213.sql.gz

set -e

# 檢查參數
if [ -z "$1" ]; then
    echo "用法: ./scripts/restore-db.sh <備份檔案>"
    echo "範例: ./scripts/restore-db.sh backups/nexusteam_backup_20251213.sql.gz"
    exit 1
fi

BACKUP_FILE=$1

# 檢查檔案是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "錯誤: 備份檔案不存在: $BACKUP_FILE"
    exit 1
fi

# 檢查 DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "錯誤: DATABASE_URL 環境變數未設定"
    echo "使用方式: DATABASE_URL=postgresql://... ./scripts/restore-db.sh <備份檔案>"
    exit 1
fi

echo "⚠️  警告: 此操作將覆蓋現有資料庫！"
read -p "確定要繼續嗎？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消還原操作"
    exit 0
fi

echo "開始還原資料庫..."

# 解壓縮（如果是 .gz 檔案）
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "解壓縮備份檔案..."
    gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"
else
    psql "$DATABASE_URL" < "$BACKUP_FILE"
fi

echo "✅ 資料庫還原完成"
