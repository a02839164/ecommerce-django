from django.db import models
from django.contrib.auth.models import User
from store.models import Product



class ProductView(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['viewed_at']),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        viewer = self.user or self.ip_address or "Guest"
        return f"{self.product.title} viewed at {self.viewed_at} by {viewer} "