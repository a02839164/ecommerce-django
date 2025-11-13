import json
from django.http import JsonResponse
from django.utils import timezone
from payment.models import Order
from django.conf import settings


def shippo_webhook(request):

    # Step 1：驗證 token
    token = request.GET.get("token")

    if token != settings.SHIPPO_WEBHOOK_TOKEN :   # 或用 settings.SHIPPO_WEBHOOK_TOKEN

        return JsonResponse({"error": "invalid token"}, status=400)

    # Step 2：解析 webhook 資料
    data = json.loads(request.body)
    tracking_number = data.get("tracking_number")
    status = data.get("tracking_status", {}).get("status")

    order = Order.objects.filter(tracking_number=tracking_number).first()

    if not order:
        
        return JsonResponse({"error": "order not found"}, status=404)

    order.shipping_status = status
    order.tracking_updated_at = timezone.now()
    order.save()

    return JsonResponse({"success": True})