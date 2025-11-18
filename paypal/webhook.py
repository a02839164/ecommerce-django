# 處理 PayPal Webhook 回拋

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import verify_paypal_signature, get_capture_id_from_links
from payment.models import Order

logger = logging.getLogger(__name__) 


@csrf_exempt
def paypal_webhook(request):

    # Step 1：簽章驗證
    is_valid, data = verify_paypal_signature(request)

    if not is_valid:

        return JsonResponse({"status": "invalid signature"}, status=400)

    logger.info("✔ PayPal Webhook signature VERIFIED")

    event_type = data.get("event_type")
    resource = data.get("resource", {}) or {}

    # Step 2：抓 order_id / capture_id
    # A. 付款 webhook：resource.id = capture_id
    capture_id_from_resource_id = resource.get("id")

    # B. 有些付款 webhook 會帶 order_id
    order_id = (
        resource.get("supplementary_data", {})
                .get("related_ids", {})
                .get("order_id")
    )

    # C. REFUND webhook：真正 capture_id 在 links["up"]
    capture_id_from_links = get_capture_id_from_links(resource)

    logger.info(
        f"resource.id={capture_id_from_resource_id}, "
        f"order_id={order_id}, "
        f"capture_id_from_links={capture_id_from_links}"
    )

    # =================================
    # Step 3：尋找訂單
    # =================================

    order = None

    # 用 order_id 找
    if order_id:
        order = Order.objects.filter(paypal_order_id=order_id).first()

    # 用 capture_id_from_resource_id 找（付款）
    if not order and capture_id_from_resource_id:
        order = Order.objects.filter(paypal_capture_id=capture_id_from_resource_id).first()

    # 用 capture_id_from_links 找（退款）
    if not order and capture_id_from_links:
        order = Order.objects.filter(paypal_capture_id=capture_id_from_links).first()

    if not order:
        logger.warning(
            f"⚠ Webhook received but ORDER NOT FOUND → "
            f"order_id={order_id}, "
            f"resource_id={capture_id_from_resource_id}, "
            f"capture_from_links={capture_id_from_links}"
        )
        return JsonResponse({"status": "order_not_found"}, status=200)


    # Step 4：更新訂單狀態
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
        f"Order #{order.id} UPDATED → "
        f"payment_status={order.payment_status}, "
        f"verify_webhook={order.verify_webhook}"
    )

    return JsonResponse({"status": "ok"})