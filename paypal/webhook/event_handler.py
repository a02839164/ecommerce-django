from inventory.services import apply_inventory_sale, apply_inventory_refund
import logging

logger = logging.getLogger(__name__)

class PaypalEventHandler:

    @staticmethod
    def handle(event_type, resource, order):

        logger.info(f"Updating order #{order.id} with event {event_type}")

        order.verify_webhook = event_type

        if event_type == "PAYMENT.CAPTURE.COMPLETED":

            if order.payment_status != "COMPLETED":  # 避免重複扣

                apply_inventory_sale(order)
                order.payment_status = "COMPLETED"

        elif event_type == "PAYMENT.CAPTURE.REFUNDED":

            if order.payment_status != "REFUNDED":
                apply_inventory_refund(order)

            order.payment_status = "REFUNDED"

        elif event_type == "CHECKOUT.ORDER.APPROVED":
            order.payment_status = "APPROVED"

        order.save()

        logger.info(
            f"Order #{order.id} UPDATED → "
            f"payment_status={order.payment_status}, "
            f"verify_webhook={order.verify_webhook}"
        )