import logging
from django.utils import timezone

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