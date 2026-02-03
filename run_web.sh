#!/bin/sh
 
echo "Waiting for DB..."
sh ./wait-for-postgres.sh db

#判斷環境執行不同指令
if [ "$DJANGO_ENV" = "production" ]; then
    echo "Current Mode: [ PRODUCTION ]"
    
    # 生產環境才需要收集靜態檔案
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Running migrations..."
    python manage.py migrate

    echo "Starting Gunicorn..."
    exec gunicorn ecommerce.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --log-level info \
        --access-logfile -
else
    echo "Current Mode: [ DEVELOPMENT ]"
    
    echo "Running migrations..."
    python manage.py migrate

    echo "Starting Django Development Server..."
    exec python manage.py runserver 0.0.0.0:8000
fi