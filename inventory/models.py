from django.db import models
from store.models import Product
from django.contrib.auth.models import User



class InventoryLog(models.Model):
    ACTION_CHOICES = [
        ("SALE", "Order Sold"),
        ("REFUND", "Order Refunded"),
        ("MANUAL_ADD", "Manual Add"),
        ("MANUAL_SUB", "Manual Subtract"),
        ("CANCEL", "Order Canceled"),
        ("RESERVE", "Stock Reserved"),
        ("RELEASE", "Reserved Released"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()  
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} {self.quantity} ({self.action})"

    
class BulkStockEntry(models.Model):
    class Meta:
        managed = False                     #  不建立資料表
        app_label = "inventory"
        verbose_name = "Bulk Stock Manager"
        verbose_name_plural = "Bulk Stock Manager"

    def __str__(self):
        return "Bulk Stock Manager"
    
