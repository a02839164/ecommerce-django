# shipping/webhook/webhook.py

import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from payment.models import Order

from .webhook_helpers import (
    validate_token,
    parse_webhook_json,
    extract_tracking_number,
    extract_status,
)
from .event_handler import ShippoEventHandler

logger = logging.getLogger(__name__)


@csrf_exempt
def shippo_webhook(request):
    try:
        # 1. 限 POST
        if request.method != 'POST':
            logger.warning(f"Invalid method received: {request.method}")
            return JsonResponse({"error": "Method not allowed"}, status=405)

        # 2. token 驗證
        token = request.GET.get("token")
        if not validate_token(token):
            logger.warning(f"Invalid token received: {token}")
            return JsonResponse({"error": "invalid token"}, status=400)

        # 3. 解析 JSON
        data = parse_webhook_json(request)
        if data is None:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # 4. 抽取資料
        tracking_number = extract_tracking_number(data)
        new_status = extract_status(data)

        logger.info(f"Extracted - Tracking: {tracking_number}, Status: {new_status}")

        if not tracking_number:
            logger.error("Missing tracking_number in webhook data.")
            return JsonResponse({
                "success": True,
                "message": "No tracking number in test data"
            })

        # 5. 找訂單
        order = Order.objects.filter(tracking_number=tracking_number).first()
        if not order:
            logger.warning(f"Order not found for tracking number: {tracking_number}")
            return JsonResponse({
                "success": True,
                "message": "Order not found but webhook processed"
            })

        # 6. 把事件交給 event handler
        ShippoEventHandler.handle(order, new_status)

        return JsonResponse({"success": True})

    except Exception as e:
        logger.error(f"Unexpected error in shippo_webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"error": "Internal server error"}, status=500)
