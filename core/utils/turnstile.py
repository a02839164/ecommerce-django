# core/utils/turnstile.py
import requests
from django.conf import settings

def verify_turnstile(token: str, remote_ip: str | None = None):
    if not token:
        return False, {"error": "missing-token"}

    data = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        resp = requests.post(
            settings.TURNSTILE_VERIFY_URL,
            data=data,
            timeout=5,
        )
        result = resp.json()
        return result.get("success", False), result
    except Exception as e:
        return False, {"error": "request-failed", "detail": str(e)}
