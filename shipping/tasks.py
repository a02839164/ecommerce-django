from celery import shared_task
import requests
from django.conf import settings

@shared_task
def send_fake_webhook_task(tracking_number, status):
    """
    Celery 模擬 Shippo webhook，依照 status 更新訂單物流狀態。
    """

    url = f"http://127.0.0.1:8000/webhooks/shippo/?token={settings.SHIPPO_WEBHOOK_TOKEN}"

    payload = {
        "tracking_number": tracking_number,
        "tracking_status": {"status": status},
        "test": True
    }

    print(f"Celery ➜ 模擬 Webhook 狀態：{status}")

    try:
        res = requests.post(url, json=payload, timeout=5)
        print("Celery 回應：", res.status_code, res.text)
    except Exception as e:
        print("Celery ERROR:", e)

    return True