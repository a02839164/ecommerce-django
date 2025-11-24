from notifications.email_service import send_email_via_requests



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
