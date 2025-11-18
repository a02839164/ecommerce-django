from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from payment.models import Order , OrderItem ,ShippingAddress
from paypal.services.views import process_single_order_refund

admin.site.register(ShippingAddress)
admin.site.register(OrderItem)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'user', 'subtotal', 'shipping_fee', 'amount_paid',
        'payment_status', 'paypal_capture_id', 'verify_webhook',
    )

    actions = ['admin_refund_orders']

    @admin.action(description='Refund selected orders')
    def admin_refund_orders(self, request, queryset):
        """
        對選定的訂單執行退款，並將處理工作委派給外部邏輯函數。
        """
        
        successful_refunds = 0
        
        # 遍歷所有選定的訂單 (QuerySet)
        for order in queryset:
            # 呼叫外部邏輯函數，傳入 request 和 order id
            is_success = process_single_order_refund(request, order.id)
            if is_success:
                successful_refunds += 1
        
        # 總結訊息 (可選，因為 process_single_order_refund 已經發送了訊息)
        # if successful_refunds > 0:
        #     self.message_user(request, f"共成功請求退款 {successful_refunds} 筆訂單。", level=messages.INFO)
