from __future__ import absolute_import, unicode_literals

# 這會確保 app 在 Django 啟動時就被載入
from .celery import app as celery_app

__all__ = ('celery_app',)