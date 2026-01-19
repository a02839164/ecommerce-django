from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from shipping.webhook.webhook import shippo_webhook
from paypal.webhook.webhook import paypal_webhook


urlpatterns = [
    #Admin url
    path('admin/', admin.site.urls),
    #Store app
    path('',include('store.urls')),
    #Cart app
    path('cart/',include('cart.urls')),
    #Account app
    path('account/',include('myaccount.urls')),
    #Payment app
    path('payment/',include('payment.urls')),
    #Support app
    path("support/", include("support.urls")),
    
    #Webhook URL
    path('webhooks/shippo/',shippo_webhook , name="shippo-webhook"),
    path('webhooks/paypal/',paypal_webhook , name="paypal-webhook"),

    #Inventory
    path("inventory/", include("inventory.urls")),
]


if settings.DEBUG:
    
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)