from django.contrib import admin
from .models import ShippingAddress,Order , OrderItem



admin.site.register(ShippingAddress)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'subtotal',
        'shipping_fee',
        'amount_paid',
        'payment_status',
        'date_ordered',
    )
    list_filter = ('payment_status', 'date_ordered')
    search_fields = ('id', 'user__username', 'email')


admin.site.register(OrderItem)