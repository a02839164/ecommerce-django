import json
import requests
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


# 驗證 PayPal Webhook 簽章，回傳 True / False
def verify_paypal_signature(request):

    raw_body = request.body.decode('utf-8')
    data = json.loads(raw_body)

    logger.info("Starting PayPal signature verification")

    transmission_id = request.headers.get("Paypal-Transmission-Id")
    timestamp = request.headers.get("Paypal-Transmission-Time")
    cert_url = request.headers.get("Paypal-Cert-Url")
    auth_algo = request.headers.get("Paypal-Auth-Algo")
    transmission_sig = request.headers.get("Paypal-Transmission-Sig")
    webhook_id = settings.PAYPAL_WEBHOOK_ID

    verify_payload = {
        "auth_algo": auth_algo,
        "cert_url": cert_url,
        "transmission_id": transmission_id,
        "transmission_sig": transmission_sig,
        "transmission_time": timestamp,
        "webhook_id": webhook_id,
        "webhook_event": data
    }

    # Step 1：拿 Access Token
    auth_res = requests.post(
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
    )

    access_token = auth_res.json().get("access_token")

    if not access_token:
        logger.error("Failed to obtain PayPal access token")

        return False, data

    # Step 2：呼叫 PayPal Verify API
    verify_res = requests.post(
        "https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature",
        json=verify_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    ).json()


    is_valid = verify_res.get("verification_status") == "SUCCESS"


    if is_valid:

        logger.info("PayPal signature verification SUCCESS")

    else:
        logger.warning("PayPal signature verification FAILED")


    return is_valid, data



def get_capture_id_from_links(resource):
    """
    REFUND webhook 使用 refund_id 作為 resource.id
    真正的 capture_id 被藏在 links[].href 裡（rel = "up"）
    例：
    "href": "https://api.sandbox.paypal.com/v2/payments/captures/935885208W2191049"
    """
    links = resource.get("links", [])
    for link in links:
        if link.get("rel") == "up":
            href = link.get("href")
            return href.rstrip("/").split("/")[-1]  # 取 URL 最後一段
    return None

