from django.urls import path
from . import views

urlpatterns = [

    path('checkout/', views.checkout, name='checkout'),

    path("create-paypal-order/", views.create_paypal_order, name="create-paypal-order"),
    path("capture-paypal-order/", views.capture_paypal_order, name="capture-paypal-order"),


    path('payment-success/', views.payment_success, name='payment-success'),
    path('payment-failed/', views.payment_failed, name='payment-failed'),





]