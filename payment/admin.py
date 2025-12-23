from django.contrib import admin
from payment.models import Order , OrderItem ,ShippingAddress
from paypal.admin_refund import process_single_order_refund

admin.site.register(ShippingAddress)

class OrderItemInline(admin.TabularInline):
    model = OrderItem

    # 只讀欄位（避免破壞訂單紀錄）
    readonly_fields = ('product', 'quantity', 'price', 'user')
    # ID 輸入框 取代下拉選單
    raw_id_fields = ('product', 'user')
    # 避免 N+1 加速列表
    list_select_related = ('product', 'user')

    # 禁止新增 inline item
    def has_add_permission(self, request, obj=None):
        return False
    # 禁止刪除
    def has_delete_permission(self, request, obj=None):
        return False  
    # 禁止修改
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'user', 'subtotal', 'shipping_fee', 'amount_paid',
        'payment_status', 'paypal_capture_id', 'verify_webhook',
    )

    actions = ['admin_refund_orders']
    inlines = [OrderItemInline]
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]
    
    def has_add_permission(self, request):
        return False  

    def has_delete_permission(self, request, obj=None):
        return False  
    
    # 只有 superuser 才看得到 action
    def get_actions(self, request):

        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.clear()

        return actions


    @admin.action(description='Refund selected orders')
    def admin_refund_orders(self, request, queryset):

        # 遍歷所有選定的訂單
        for order in queryset:
            # 呼叫 paypal退款邏輯
            process_single_order_refund(request, order.id)