# core/security/email_verification/service.py
from django.core.exceptions import ValidationError
import logging
from core.security.email_verification.cooldown import can_send, mark_sent
from notifications.handlers.account import send_verification_email

logger = logging.getLogger(__name__)

class EmailVerificationService:
    @staticmethod
    def send(user):
        # 已驗證就不能再寄
        if user.is_active:
            logger.info("Email verification resend blocked: already verified (user_id=%s)",user.id,)
            raise ValidationError("Email already verified")

        # 冷卻時間限制
        if not can_send(user.id, action="verification"):
            logger.info("Email verification resend blocked: cooldown (user_id=%s)",user.id,)
            raise ValidationError("Please wait 60 minutes before resending")
        
        logger.info("Sending verification email (user_id=%s, email=%s)",user.id,user.email)


        # 寄信（通知層）
        send_verification_email(user)

        # 標記已寄
        mark_sent(user.id, action="verification")
