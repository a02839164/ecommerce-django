from django.db import models
from django.contrib.auth.models import User

from store.models import Product


class ShippingAddress(models.Model):

    full_name = models.CharField(max_length=100)

    email = models.EmailField(max_length=255)

    address1 = models.CharField(max_length=255)

    address2 = models.CharField(max_length=255)

    city = models.CharField(max_length=255)

    #Optional
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode= models.CharField(max_length=50, null=True, blank=True)

    #FK
    #Authenticated / not authenticated user (bear in mind)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


    class Meta:

        verbose_name_plural = 'Shipping Address'

    def __str__(self):

        return 'Shipping Address - ' + str(self.id)
    


class Order(models.Model):

    full_name = models.CharField(max_length=50)

    email = models.EmailField(max_length=255)

    shipping_address = models.TextField(max_length=1000)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)     
    
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0) 

    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)

    date_ordered = models.DateTimeField(auto_now_add=True)

    #FK
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # update PayPal 
    paypal_order_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payer_id = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=50, null=True, blank=True)    


    def __str__(self):

        return 'Order - #' + str(self.id)
    
class OrderItem(models.Model):

    # FK ->
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)


    quantity = models.PositiveBigIntegerField(default=2)

    price = models.DecimalField(max_digits=8, decimal_places=2)

    #FK
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):

        return 'Order Item - #' + str(self.id)