#!/bin/bash

# 1. 讀取 .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo " 找不到 .env 檔案，請確認腳本位置"
    exit 1
fi

# 2. 設定路徑、檔名
BACKUP_DIR="./db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_NAME="backup_${DATE}.sql.gz"

# 建立備份資料夾
mkdir -p $BACKUP_DIR

echo "開始備份資料庫 [${POSTGRES_NAME}] 自容器 [buyria_db]..."

# 3. pg_dump 工具執行備份
docker exec -e PGPASSWORD=${POSTGRES_PASSWORD} buyria_db pg_dump -U ${POSTGRES_USER} ${POSTGRES_NAME} | gzip > ${BACKUP_DIR}/${FILE_NAME}

# 4. 檢查執行結果
if [ $? -eq 0 ]; then
    echo "備份完成！"
    echo "檔案儲存於: ${BACKUP_DIR}/${FILE_NAME}"
    echo "檔案大小: $(du -h ${BACKUP_DIR}/${FILE_NAME} | cut -f1)"
else
    echo "備份過程發生錯誤。"
    exit 1
fi

# 5. 保留最近 3 個備份，避免硬碟爆滿
echo "正在清理舊備份，僅保留最近 3 份..."
ls -t ${BACKUP_DIR}/*.gz | tail -n +4 | xargs rm -f 2>/dev/null