from notifications.handlers.order import send_refund_success_email
import logging

logger = logging.getLogger(__name__)

class PaypalEventHandler:

    @staticmethod
    def handle(event_type, resource, order):

        logger.info(f"Updating order #{order.id} with event {event_type}")

        order.verify_webhook = event_type

        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            order.payment_status = "COMPLETED"

        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            order.payment_status = "REFUNDED"
            send_refund_success_email(order)

        elif event_type == "CHECKOUT.ORDER.APPROVED":
            order.payment_status = "APPROVED"

        order.save()

        logger.info(
            f"Order #{order.id} UPDATED → "
            f"payment_status={order.payment_status}, "
            f"verify_webhook={order.verify_webhook}"
        )