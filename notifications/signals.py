from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from payment.models import Order       
from support.models import SupportMessage  

from notifications.handlers.account import send_verification_email, send_password_changed_email
from notifications.handlers.order import send_order_confirm_email, send_shipping_update_email, send_refund_success_email
from notifications.handlers.support import send_support_reply_email


@receiver(post_save, sender=User)
def send_account_activation_email(sender, instance, created, **kwargs):
    """
    新註冊且尚未啟用帳號 → 寄送驗證信
    """
    if not created:
        return

    if instance.is_active:
        return

    transaction.on_commit(lambda: send_verification_email(instance))


#變更密碼通知信
# 1. 在儲存前偵測變更
@receiver(pre_save, sender=User)
def track_password_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    # 檢查「新密碼」是否為不可用密碼 (Google 用戶通常會設為 !)
    # 如果新密碼本身就是不可用的，這絕對不是使用者「變更」密碼，不應發信
    if not instance.has_usable_password():
        return

    try:
        old_user = User.objects.only('password').get(pk=instance.pk)
        
        # 只有當「舊密碼」也是可用的，且兩者不同，才標記變更
        if old_user.has_usable_password() and old_user.password != instance.password:
            instance._password_changed = True
    except User.DoesNotExist:
        pass

# 2. 在儲存後執行發信
@receiver(post_save, sender=User)
def send_password_change_notification(sender, instance, created, **kwargs):
    # 建立帳號時絕對不寄
    if created:
        return
    
    # 雙重保險：如果是 Google 用戶則跳過
    if hasattr(instance, "profile") and instance.profile.is_google_user:
        return

    # 只有被標記為變更過的才發信
    if getattr(instance, "_password_changed", False):
        send_password_changed_email(instance)
        
        # 發信後立刻清理標記
        delattr(instance, "_password_changed")



#訂單成立信
@receiver(pre_save, sender=Order)
def remember_old_order_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_payment_status = None
    else:
        old = Order.objects.filter(pk=instance.pk).only("payment_status").first()
        instance._old_payment_status = old.payment_status if old else None


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

