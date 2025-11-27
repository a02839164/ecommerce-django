from django.urls import path
from . import admin_views


app_name = "inventory"

urlpatterns = [

    #單一
    path("adjust-stock/<int:product_id>/", admin_views.adjust_stock, name="adjust-stock"),
    #批次
    path("bulk-stock/", admin_views.bulk_update_stock, name="bulk-stock"),
    
]

