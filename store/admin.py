from django.contrib import admin
from .models import Category,Product
from django.utils.html import format_html
from django.urls import reverse


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    prepopulated_fields = {'slug':('name',)}   # 輔助功能 根據name欄輸入，即時自動產生slug欄的值


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price", "stock", "stock_status", "adjust_stock_link")
    search_fields = ("title",)
    prepopulated_fields = {'slug':('title',)}

    def stock_status(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color:red;font-weight:bold;">已售完</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color:orange;">低庫存 ({})</span>', obj.stock)
        return format_html('<span style="color:green;">{} 件</span>', obj.stock)

    stock_status.short_description = "庫存狀態"

    def adjust_stock_link(self, obj):
        url = reverse("inventory:adjust-stock", args=[obj.id])
        return format_html('<a class="button" href="{}">調整</a>', url)

    adjust_stock_link.short_description = "調整庫存"