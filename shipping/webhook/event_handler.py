import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# 處理 Shippo Webhook 回拋事件 - 更新 shipping_status
class ShippoEventHandler:

    @staticmethod
    def handle(order, new_status):
        
        old_status = order.shipping_status
        order.shipping_status = new_status
        order.tracking_updated_at = timezone.now()
        order.save()

        logger.info(
            f"Order {order.id} shipping status updated: "
            f"{old_status} -> {new_status}"
        )