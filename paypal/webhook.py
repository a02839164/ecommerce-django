import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from paypal.utils import verify_paypal_signature
from payment.models import Order

logger = logging.getLogger(__name__) 

@csrf_exempt
def paypal_webhook(request):

    # Step 1：簽章驗證 + 拿解析後資料
    is_valid, data = verify_paypal_signature(request)

    if not is_valid:

        return JsonResponse({"status": "invalid signature"}, status=400)

    logger.info("✔ PayPal Webhook signature VERIFIED")


    event_type = data.get("event_type")
    resource = data.get("resource", {}) or {}


    # Step 2：取 capture_id / order_id
    capture_id = resource.get("id")
    related_order = (
        resource.get("supplementary_data", {})
                .get("related_ids", {})
                .get("order_id")
    )

    logger.info(f"capture_id={capture_id}, paypal_order_id={related_order}")

    # Step 3：找訂單
    order = None

    if related_order:
        order = Order.objects.filter(paypal_order_id=related_order).first()

    if not order and capture_id:
        order = Order.objects.filter(paypal_capture_id=capture_id).first()

    if not order:
        logger.warning(
            f"Webhook received but order not found. paypal_order_id={related_order}, capture_id={capture_id}"
        )
        return JsonResponse({"status": "order_not_found"}, status=200)

    # Step 4：更新訂單
    logger.info(f"Updating order #{order.id} with event {event_type}")

    order.verify_webhook = event_type

    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        order.payment_status = "COMPLETED"

    elif event_type == "PAYMENT.CAPTURE.REFUNDED":
        order.payment_status = "REFUNDED"

    elif event_type == "CHECKOUT.ORDER.APPROVED":
        order.payment_status = "APPROVED"

    order.save()

    logger.info(
        f"Order #{order.id} updated → payment_status={order.payment_status}, verify_webhook={order.verify_webhook}"
    )

    return JsonResponse({"status": "ok"})
