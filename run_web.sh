#!/bin/sh

echo "Waiting for DB..."
sh wait-for-postgres.sh db

echo "Running migrations..."
python manage.py migrate

echo "Starting Django Server..."
exec python manage.py runserver 0.0.0.0:8000