from notifications.email_service import send_email_via_requests
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator



def build_activation_link(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    path = reverse(
        "email-verification",
        kwargs={"uidb64": uidb64, "token": token},
    )

    return f"{settings.SITE_DOMAIN}{path}"


def send_verification_email(user):
    activation_link = build_activation_link(user)

    subject = "Account verification email"
    context = {
        "user": user,
        "activation_link": activation_link,
    }

    send_email_via_requests(
        subject=subject,
        to_email=user.email,
        template_base_name="verify_email",
        context=context,
    )


#密碼變更信
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
