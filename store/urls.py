from django.urls import path
from . import views

urlpatterns = [

    # Store main page
    path('', views.store, name='store'),

    #Individual product
    path('product/<slug:product_slug>/', views.product_info, name='product-info'),     # <型別:變數名稱>

    #Individual category
    path('products/<slug:category_slug>/', views.list_category, name='list-category'), # <型別:變數名稱>
    
    #search
    path('search/', views.product_search, name='product-search'),
]