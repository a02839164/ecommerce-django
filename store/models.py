from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=250 , db_index=True)
    slug = models.SlugField(max_length=250, unique=True)

    class Meta:

        verbose_name_plural = 'categories' 
    
    def __str__(self):

        return self.name
    
    def get_absolute_url(self):

        return reverse('list-category', args=[self.slug])

class Product(models.Model):
    #建立關聯
    category = models.ForeignKey(Category,related_name='product', on_delete=models.CASCADE,null=True)
    
    title = models.CharField(max_length=250)
    brand = models.CharField(max_length=250,default="un-branded")
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    price = models.DecimalField(max_digits=8,decimal_places=2)
    discountpercentage= models.FloatField(blank=True, null=True)

    stock = models.PositiveIntegerField(default=0)
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
    
    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)