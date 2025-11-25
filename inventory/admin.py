from django.contrib import admin
from .models import InventoryLog , BulkStockEntry
from django.http import HttpResponseRedirect
from django.urls import reverse



@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'action', 'performed_by', 'note', 'created_at')
    list_filter = ('action', 'performed_by', 'created_at')
    raw_id_fields = ('product', 'performed_by')
    search_fields = ('product__title', 'note')
    ordering = ('-created_at',)

@admin.register(BulkStockEntry)
class BulkStockEntryAdmin(admin.ModelAdmin):

    def changelist_view(self, request, extra_context=None):
        # 直接跳轉到你的 bulk import 頁面
        url = reverse("inventory:bulk-stock")   # 對應 inventory/urls.py
        return HttpResponseRedirect(url)
    
