from django.db import models
from django.contrib.auth.models import User


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "未處理"),
        ("PENDING", "處理中"),
        ("RESOLVED", "已解決"),
    ]

    PRIORITY_CHOICES = [
        ("NORMAL", "一般"),
        ("URGENT", "緊急"),
    ]

    CATEGORY_CHOICES = [
        ("order", "訂單問題"),
        ("refund", "付款問題"), 
        ("product", "商品提問"),
        ("account", "帳號問題"),
        ("other", "其他"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)
    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=20,choices=CATEGORY_CHOICES,default="OTHER",)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="OPEN")
    priority = models.CharField(max_length=20,choices=PRIORITY_CHOICES,default="NORMAL")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.user.username})"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket,related_name="messages",on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "SupportMessage"

