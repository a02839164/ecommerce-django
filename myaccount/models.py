from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='profile_pics/', default='default.png', blank=True)
    name =models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    is_google_user = models.BooleanField(default=False)

    def __str__(self):

        return f"{self.user.username} Profile"
    
