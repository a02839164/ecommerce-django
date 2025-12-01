from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from payment.models import Order , OrderItem ,ShippingAddress
from paypal.refund import process_single_order_refund

admin.site.register(ShippingAddress)

class OrderItemInline(admin.TabularInline):
    model = OrderItem

    # 只讀欄位（避免破壞訂單紀錄）
    readonly_fields = ('product', 'quantity', 'price', 'user')
    # 避免超大下拉選單卡死
    raw_id_fields = ('product', 'user')
    # 避免 N+1 加速列表
    list_select_related = ('product', 'user')

        # 禁止新增 inline item
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # 禁止刪除

    def has_change_permission(self, request, obj=None):
        return False #禁止修改

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
        return False  # 禁止新增

    def has_delete_permission(self, request, obj=None):
        return False  # 禁止刪除
    
    def get_actions(self, request):

        actions = super().get_actions(request)

        if not request.user.is_superuser:
            actions.clear()

        return actions




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


# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
    

#     list_display = ('id', 'order', 'product', 'quantity', 'price', 'user')
#     raw_id_fields = ('order', 'product', 'user')         #FK下拉選單改成「搜尋框」
#     list_select_related = ('order', 'product', 'user')   #加速 ForeignKey
#     search_fields = ('order__id', 'product__title', 'user__username')
#     readonly_fields = ('order', 'product', 'quantity', 'price', 'user')

#     # 6. 讓後台不要顯示「新增」和「刪除」按鈕
#     def has_add_permission(self, request):
#         return False  # 禁止新增

#     def has_change_permission(self, request, obj=None):
#         return False  # 禁止編輯

#     def has_delete_permission(self, request, obj=None):
#         return False  # 禁止刪除
