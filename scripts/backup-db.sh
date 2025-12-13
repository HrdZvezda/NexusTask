#!/bin/bash
# 資料庫備份腳本
# 用法: ./scripts/backup-db.sh

set -e

# 設定
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nexusteam_backup_$DATE.sql"

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 檢查 DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "錯誤: DATABASE_URL 環境變數未設定"
    echo "使用方式: DATABASE_URL=postgresql://... ./scripts/backup-db.sh"
    exit 1
fi

echo "開始備份資料庫..."
echo "備份檔案: $BACKUP_FILE"

# 執行備份
pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

# 壓縮備份
gzip "$BACKUP_FILE"

echo "✅ 備份完成: ${BACKUP_FILE}.gz"
echo "檔案大小: $(du -h ${BACKUP_FILE}.gz | cut -f1)"

# 清理 30 天前的備份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
echo "已清理 30 天前的舊備份"
