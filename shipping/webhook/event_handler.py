import logging
from django.utils import timezone
from notifications.handlers.order import send_shipping_update_email

logger = logging.getLogger(__name__)


class ShippoEventHandler:
    """
    專門處理 Shippo Webhook 回拋事件：
    - 更新 shipping_status
    - 寄信通知
    - 之後可加入 delivered 邏輯、lost 處理...
    """

    @staticmethod
    def handle(order, status):
        old_status = order.shipping_status

        order.shipping_status = status
        order.tracking_updated_at = timezone.now()
        order.save()

        logger.info(
            f"Order {order.id} shipping status updated: "
            f"{old_status} -> {status}"
        )

        # 状態變更時寄信（你原本程式沒加，但這裡預留 hooks）
        if status == "IN_TRANSIT":

            try:

                send_shipping_update_email(order)

                logger.info(f"Shipping email sent for order {order.id}")

            except Exception as e:

                logger.error(
                    f"Failed to send shipping email for order {order.id}: {e}"
                )