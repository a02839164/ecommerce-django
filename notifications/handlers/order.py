from notifications.email_service import send_email_via_requests



#下單成功
def send_order_confirm_email(order):
    subject = f"Order #{order.id} {order.payment_status} Confirmation"

    context = {
        "order": order,
        "user": order.user,
    }

    send_email_via_requests(
        subject=subject,
        to_email=order.user.email,
        template_base_name="order_confirm",
        context=context,
    )


#出貨通知
def send_shipping_update_email(order):
    subject = f"Order #{order.id} Shipping Update"

    context = {
        "order": order,
        "user": order.user,
    }

    send_email_via_requests(
        subject=subject,
        to_email=order.user.email,
        template_base_name="shipping_update",
        context=context,
    )



#退款成功
def send_refund_success_email(order):
    subject = f"Order #{order.id} Refund Completed"

    context = {
        "order": order,
        "user": order.user,
    }

    send_email_via_requests(
        subject=subject,
        to_email=order.user.email,
        template_base_name="refund_success",
        context=context,
    )
