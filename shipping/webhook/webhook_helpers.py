import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def validate_token(token: str) -> bool:

    #驗證 Shippo 傳來的 token 是否正確
    return token and token == settings.SHIPPO_WEBHOOK_TOKEN


def parse_webhook_json(request):

    #解析 webhook JSON，失敗則回傳 None
    try:
        data = json.loads(request.body)
        logger.info(f"Full webhook data: {json.dumps(data, indent=2)}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None


def extract_tracking_number(data):

    #處理 Shippo 不同格式回傳的 tracking_number
    return (
        data.get("tracking_number")
        or data.get("data", {}).get("tracking_number")
        or None
    )


def extract_status(data):
    
    #處理 Shippo 不同格式回傳的 status
    return (
        data.get("tracking_status", {}).get("status")
        or data.get("data", {}).get("tracking_status", {}).get("status")
        or data.get("status")
        or "UNKNOWN"
    )