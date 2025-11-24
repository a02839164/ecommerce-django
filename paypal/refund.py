# 管理後台 / Refund 按鈕使用的邏輯單元


from django.contrib import messages
from paypal.api import PaypalService
from payment.models import Order # 假設 Order 已經被 import

# 這裡我們不再需要 @require_POST 和 redirect，因為它不再是獨立的 View
def process_single_order_refund(request, order_id):
    """
    處理單筆訂單的退款邏輯，供 Admin Action 內部呼叫。
    接受 request (用於 messages) 和 order_id。
    返回 True/False 表示是否成功處理。
    """
    
    # 找訂單
    order = Order.objects.filter(id=order_id).first()

    if not order:
        messages.error(request, f"Order {order_id} not found.")
        return False

    if not order.paypal_capture_id:
        messages.error(request, f"Order {order_id}: This order has no PayPal capture ID.")
        return False

    if order.payment_status != "COMPLETED":
        messages.error(request, f"Order {order_id}: Only COMPLETED orders can be refunded.")
        return False

    # 呼叫 PayPal Refund API
    try:
        svc = PaypalService()
        refund_res = svc.refund_capture(
            order.paypal_capture_id,
            amount=str(order.amount_paid),
            currency="USD"
        )

        # 本地更新狀態
        order.payment_status = "REFUNDING"
        order.verify_webhook = "REFUND_REQUESTED"
        order.save()

        refund_id = getattr(refund_res, "id", "N/A")
        messages.success(request, f"Order {order_id} Refund requested! Refund ID: {refund_id}")
        return True

    except Exception as e:
        messages.error(request, f"Order {order_id} Refund failed: {e}")
        return False

# ⚠️ 注意：原來的 admin_refund_order (帶有 @require_POST, redirect) 應該被刪除或重命名。