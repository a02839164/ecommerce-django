from django.contrib import admin
from .models import ProductView

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    raw_id_fields = ('product', 'user')   #改成「輸入 ID」+ 放大鏡