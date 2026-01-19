from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from payment.models import Order       
from support.models import SupportMessage  

from notifications.handlers.account import send_verification_email, send_password_changed_email
from notifications.handlers.order import send_order_confirm_email, send_shipping_update_email, send_refund_success_email
from notifications.handlers.support import send_support_reply_email

# 註冊驗證信
# 監聽存檔後 + 事件來源的 model
@receiver(post_save, sender=User)
def send_account_activation_email(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.is_active:
        return

    transaction.on_commit(lambda: send_verification_email(instance))


#變更密碼通知信
# 1. 儲存前標記
@receiver(pre_save, sender=User)
def track_password_change(sender, instance, **kwargs):
    
    # 排除新註冊
    if not instance.pk:
        return

    # 排除 Google用戶
    if not instance.has_usable_password():
        return


    old_user = User.objects.filter(pk=instance.pk).only('password').first()
    
    if not old_user:
        return
    # 只有當「舊密碼」也是可用的，且兩者不同，才標記變更
    if old_user.has_usable_password() and old_user.password != instance.password:
        instance._password_changed = True


# 2. 儲存後執行標記
@receiver(post_save, sender=User)
def send_password_change_notification(sender, instance, created, **kwargs):

    # 排除註冊
    if created:
        return
    
    # 排除 Google 用戶
    if hasattr(instance, "profile") and instance.profile.is_google_user:
        return

    # 只有被標記為變更過的才發信
    if getattr(instance, "_password_changed", False):
        send_password_changed_email(instance)
        
        # 發信後清理標記
        delattr(instance, "_password_changed")



#訂單狀態通知信
# 1. 儲存前標記
@receiver(pre_save, sender=Order)
def remember_old_order_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_payment_status = None
    else:
        old = Order.objects.filter(pk=instance.pk).only("payment_status").first()
        instance._old_payment_status = old.payment_status if old else None

# 2. 儲存後執行
@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):

    # 新建訂單（PENDING）不寄信
    if created:
        return

    old_status = getattr(instance, "_old_payment_status", None)
    new_status = instance.payment_status

    # 狀態沒變 → 不寄
    if old_status == new_status:
        return

    def _send():
        if new_status in ["COMPLETED", "FAILED", "CANCELLED"]:
            send_order_confirm_email(instance)

        elif new_status == "REFUNDED":
            send_refund_success_email(instance)

    transaction.on_commit(_send)


#出貨通知信(僅在狀態"IN_TRANSIT"寄信)
@receiver(pre_save, sender=Order)
def detect_shipping_status_change(sender, instance, **kwargs):

    # 1. 新增訂單沒有舊狀態，不處理
    if not instance.pk:
        return

    old_order = Order.objects.filter(pk=instance.pk).only('shipping_status').first()

    if not old_order:
        return
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

