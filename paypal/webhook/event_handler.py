# from inventory.services import apply_inventory_sale, apply_inventory_refund, release_stock
from inventory.services import InventoryService
import logging

logger = logging.getLogger(__name__)

class PaypalEventHandler:

    @staticmethod
    def handle(event_type, resource, order):

        logger.info(f"Updating order #{order.id} with event {event_type}")

        order.verify_webhook = event_type

        if event_type == "PAYMENT.CAPTURE.COMPLETED":

            if order.payment_status != "COMPLETED":                   # 冪等保護 / 避免重複扣
                InventoryService.apply_inventory_sale(order)          # 正式扣庫存
        
        elif event_type in ["CHECKOUT.ORDER.CANCELLED","PAYMENT.CAPTURE.DENIED","PAYMENT.CAPTURE.EXPIRED",]:

            if order.payment_status not in ["CANCELLED", "FAILED", "EXPIRED"]:
                InventoryService.release_stock(order)                  # 釋放預扣


        elif event_type == "PAYMENT.CAPTURE.REFUNDED":

            if order.payment_status != "REFUNDED":
                InventoryService.apply_inventory_refund(order)   

        order.save(update_fields=["verify_webhook"])

        logger.info(
            f"Order #{order.id} UPDATED → "
            f"payment_status={order.payment_status}, "
            f"verify_webhook={order.verify_webhook}"
        )