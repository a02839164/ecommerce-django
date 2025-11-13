import json
from django.http import JsonResponse
from django.utils import timezone
from payment.models import Order
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def shippo_webhook(request):
    try:
        if request.method != 'POST':
            logger.warning(f"Invalid method received: {request.method}")
            return JsonResponse({"error": "Method not allowed"}, status=405)
        
        token = request.GET.get("token")
        logger.info(f"Received token: {token}")
        logger.info(f"Expected token: {settings.SHIPPO_WEBHOOK_TOKEN}")
        
        if not token or token != settings.SHIPPO_WEBHOOK_TOKEN:
            logger.warning(f"Invalid token received: {token}")
            return JsonResponse({"error": "invalid token"}, status=400)

        try:
            data = json.loads(request.body)
            logger.info(f"Full webhook data: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        tracking_number = data.get("tracking_number") or data.get("data", {}).get("tracking_number")
        
        status = (
            data.get("tracking_status", {}).get("status") or
            data.get("data", {}).get("tracking_status", {}).get("status") or
            data.get("status") or
            "UNKNOWN"
        )

        logger.info(f"Extracted - Tracking: {tracking_number}, Status: {status}")

        if not tracking_number:
            logger.error("Missing tracking_number in webhook data.")
            return JsonResponse({"success": True, "message": "No tracking number in test data"})

        order = Order.objects.filter(tracking_number=tracking_number).first()

        if not order:
            logger.warning(f"Order not found for tracking number: {tracking_number}")
            return JsonResponse({"success": True, "message": "Order not found but webhook processed"})

        old_status = order.shipping_status
        order.shipping_status = status
        order.tracking_updated_at = timezone.now()
        order.save()
        
        logger.info(f"Order {order.id} shipping status updated: {old_status} -> {status}")

        return JsonResponse({"success": True})
        
    except Exception as e:
        logger.error(f"Unexpected error in shippo_webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"error": "Internal server error"}, status=500)
