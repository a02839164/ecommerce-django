#!/bin/bash

# 1. 載入環境變數
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "找不到 .env 檔案"
    exit 1
fi

BACKUP_DIR="./db_backups"


echo " 目前可用備份："
(cd "${BACKUP_DIR}" && ls -1 *.gz)
echo "------------------------------------------"
read -p "輸入檔名: " FILE_NAME


if [ ! -f "${BACKUP_DIR}/${FILE_NAME}" ]; then
    echo "找不到檔案"
    exit 1
fi

read -p "即將重置資料庫並還原備份，確定執行？(y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "已取消。"
    exit 0
fi


echo "重置資料庫"
docker exec -i -e PGPASSWORD=${POSTGRES_PASSWORD} buyria_db psql -U ${POSTGRES_USER} -d ${POSTGRES_NAME} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"


echo "還原備份"
gunzip -c ${BACKUP_DIR}/${FILE_NAME} | docker exec -i -e PGPASSWORD=${POSTGRES_PASSWORD} buyria_db psql -U ${POSTGRES_USER} -d ${POSTGRES_NAME}


if [ $? -eq 0 ]; then
    echo "成功"
else
    echo "失敗"
fi