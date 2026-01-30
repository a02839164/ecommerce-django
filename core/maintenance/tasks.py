import os
import subprocess
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(name="core.maintenance.tasks.auto_db_backup")
def auto_db_backup():
    #先抓腳本路徑
    script_path = os.path.join(settings.BASE_DIR, 'local_backup.sh')
    # 執行
    try:

        result = subprocess.run(
            ['bash', script_path], # 用 bash 執行
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR  # cd 到專案根目錄，執行腳本(腳本內有.env相對路徑)
        )

        if result.returncode == 0:
            logger.info(f"備份成功：\n{result.stdout}")
            return f"Success: {result.stdout}"
        else:
            logger.error(f"備份失敗！錯誤訊息：\n{result.stderr}")
            return f"Failed: {result.stderr}"

    except Exception as e:
        return f"Error: {str(e)}"