from .utils import send_email_via_requests



#######註冊驗證信#######   OK
def send_verification_email(user, activation_link):

    subject = "Account verification email"
    context = {
        "user": user,
        "activation_link": activation_link,
    }

    send_email_via_requests(
        subject=subject,
        to_email=user.email,
        template_base_name="verify_email",
        context=context
    )


#######密碼變更信#######
def send_password_changed_email(user):
    subject = "Your password has been changed"

    context = {
        "user": user,
    }

    send_email_via_requests(
        subject=subject,
        to_email=user.email,
        template_base_name="password_changed",
        context=context,
    )



#######下單成功信#######  OK
def send_order_confirm_email(order):
    subject = f"Order #{order.id} Confirmation"

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



#######出貨通知信#######
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





######退款成功信#######  OK
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
