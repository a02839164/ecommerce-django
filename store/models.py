from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid
class Category(models.Model):
    name = models.CharField(max_length=250 , db_index=True)
    slug = models.SlugField(max_length=250, unique=True)

    class Meta:

        verbose_name_plural = 'categories' 
    
    def __str__(self):

        return self.name
    
    def get_absolute_url(self):

        return reverse('list-category', args=[self.slug])     # 讓 template 乾淨、不會知道太多 routing 細節

class Product(models.Model):
    #建立關聯
    category = models.ForeignKey(Category,related_name='product', on_delete=models.CASCADE,null=True)
    
    title = models.CharField(max_length=250)
    brand = models.CharField(max_length=250,default="un-branded")
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    price = models.DecimalField(max_digits=8,decimal_places=2)
    discountpercentage= models.DecimalField(max_digits=5,  decimal_places=2, default=0, help_text="折扣百分比")

    stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    dimensions = models.JSONField(blank=True, null=True)

    warrantyinformation = models.CharField(max_length=255, blank=True, null=True) 
    shippinginformation = models.CharField(max_length=255, blank=True, null=True)
    returnpolicy = models.CharField(max_length=255, blank=True, null=True)

    thumbnail = models.ImageField(upload_to='product_image/', blank=True, null=True)
    image = models.JSONField(blank=True, null=True)
    
    is_fake = models.BooleanField(default=False)

    class Meta:

        verbose_name_plural = 'products' 

        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category', 'price']),
        ]

    def __str__(self):

        return self.title
    
    def get_absolute_url(self):

        return reverse('product-info', args=[self.slug])
    
    #override
    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = f"{slugify(self.title)}-{uuid.uuid4().hex[:8]}"

        super().save(*args, **kwargs)

    @property
    def available_stock(self):                  #真正可賣的數量 = 實際庫存 - 已預扣

        return self.stock - self.reserved_stock