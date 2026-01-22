#!/bin/bash

# 1. 讀取 .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "找不到 .env 檔案"
    exit 1
fi


BACKUP_DIR="./db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_NAME="backup_${DATE}.sql.gz"


mkdir -p $BACKUP_DIR

echo "開始備份資料庫 [${POSTGRES_NAME}] 自容器 [buyria_db]"

# pg_dump 執行備份
docker exec -e PGPASSWORD=${POSTGRES_PASSWORD} buyria_db pg_dump -U ${POSTGRES_USER} ${POSTGRES_NAME} | gzip > ${BACKUP_DIR}/${FILE_NAME}


if [ $? -eq 0 ]; then
    echo "備份完成！"
    echo "檔案儲存於: ${BACKUP_DIR}/${FILE_NAME}"
    echo "檔案大小: $(du -h ${BACKUP_DIR}/${FILE_NAME} | cut -f1)"
else
    echo "備份過程發生錯誤。"
    exit 1
fi



COUNT=$(ls -1 ${BACKUP_DIR}/*.gz 2>/dev/null | wc -l)
if [ "$COUNT" -gt 3 ]; then
    echo "清理舊檔案，保留最近 3 份"
    ls -t ${BACKUP_DIR}/*.gz | tail -n +4 | xargs rm -f
fi