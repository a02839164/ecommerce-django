from django.urls import path
from . import views

urlpatterns = [

    # Store main page
    path('', views.store, name='store'),

    #Individual product
    path('product/<slug:product_slug>/', views.product_info, name='product-info'),

    #Individual category
    path('products/<slug:category_slug>/', views.list_category, name='list-category'),
    
    #search
    path('search/', views.product_search, name='product-search'),
]