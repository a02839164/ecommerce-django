#!/bin/sh
# wait-for-postgres.sh

set -e
  
HOST=$1
PORT=$POSTGRES_PORT

while ! pg_isready -h $HOST -p $PORT
do
    echo "$(date) - waiting for database to start"
    sleep 5
done
