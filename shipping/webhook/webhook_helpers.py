import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# 驗證 Shippo 傳來的 token 是否正確
def validate_token(token: str) -> bool:

    return token and token == settings.SHIPPO_WEBHOOK_TOKEN

# 解析 webhook decode 成 JSON
def parse_webhook_json(request):

    try:
        data = json.loads(request.body)
        logger.info(f"Full webhook data: {json.dumps(data, indent=2)}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None

# 處理 Shippo 不同格式回傳的 tracking_number
def extract_tracking_number(data):

    return (
        data.get("tracking_number")
        or data.get("data", {}).get("tracking_number")
        or None
    )

# 處理 Shippo 不同格式回傳的 status
def extract_status(data):
    
    return (
        data.get("tracking_status", {}).get("status")
        or data.get("data", {}).get("tracking_status", {}).get("status")
        or data.get("status")
        or "UNKNOWN"
    )