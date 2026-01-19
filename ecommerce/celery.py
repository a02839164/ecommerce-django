from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 設置 Django 的預設設定模組
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# 任務引擎本體
app = Celery('ecommerce')

# 從 Django 設定檔讀取所有 Celery 相關設定
app.config_from_object('django.conf:settings', namespace='CELERY')

# 掃描所有 INSTALLED_APPS，找 app 裡的 tasks.py自動註冊任務
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')