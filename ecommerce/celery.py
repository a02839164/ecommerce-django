from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 設置 Django 的預設設定模組
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

app = Celery('ecommerce')

# 從 Django 設定檔讀取所有 Celery 相關設定
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動從所有已註冊的 Django app 中載入任務
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')