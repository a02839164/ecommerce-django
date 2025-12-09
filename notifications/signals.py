from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from payment.models import Order       
from support.models import SupportMessage  

from notifications.handlers.account import send_password_changed_email
from notifications.handlers.order import send_order_confirm_email, send_shipping_update_email, send_refund_success_email
from notifications.handlers.support import send_support_reply_email


#變更密碼通知信
@receiver(pre_save, sender=User)
def detect_password_change(sender, instance, **kwargs):

    if not instance.pk:
        return  # 新建 User 不算修改密碼

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # 密碼有被修改
    if old_user.password != instance.password:
        send_password_changed_email(instance)



#訂單成立信
@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):

    # 新建訂單（通常是 PENDING），不寄任何狀態信
    if created:
        return

    # 取舊狀態（注意：這裡一定要查 DB）
    old = Order.objects.filter(pk=instance.pk).only("payment_status").first()
    if not old:
        return

    # 只在「狀態真的改變」時處理
    if old.payment_status == instance.payment_status:
        return

    # ✅ 狀態轉換後才寄信，而且保證在 transaction commit 之後才寄
    def _send():


        if instance.payment_status in ["COMPLETED", "FAILED", "CANCELLED"]:
            send_order_confirm_email(instance)

        elif instance.payment_status == "REFUNDED":
            send_refund_success_email(instance)

    transaction.on_commit(_send)


#出貨通知信
@receiver(pre_save, sender=Order)
def detect_shipping_status_change(sender, instance, **kwargs):

    # 1. 新增訂單沒有舊狀態，不處理
    if not instance.pk:
        return

    old_order = Order.objects.get(pk=instance.pk)

    # 2. 若 shipping_status 沒變更，不做任何事
    if old_order.shipping_status == instance.shipping_status:
        return

    # 3. 若變成 IN_TRANSIT，寄出郵寄通知信
    if instance.shipping_status == "IN_TRANSIT":
        send_shipping_update_email(instance)




#客服回覆通知
@receiver(post_save, sender=SupportMessage)
def notify_support_reply(sender, instance, created, **kwargs):

    # 只在 "管理員回覆" 且是新訊息時寄信
    if created and instance.is_staff_reply:
        ticket = instance.ticket
        reply_message = instance.message
        send_support_reply_email(ticket, reply_message)

