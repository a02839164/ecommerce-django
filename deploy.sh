#!/bin/bash

set -e

git pull origin main
sudo docker compose up -d --build

sleep 10

sudo docker compose ps
sudo docker compose logs --tail=20 web
sudo docker compose ps web | grep 'Up'

