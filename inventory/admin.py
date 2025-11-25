from django.contrib import admin
from .models import InventoryLog


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'action', 'performed_by', 'note', 'created_at')
    list_filter = ('action', 'performed_by', 'created_at')
    raw_id_fields = ('product', 'performed_by')
    search_fields = ('product__title', 'note')
    ordering = ('-created_at',)

