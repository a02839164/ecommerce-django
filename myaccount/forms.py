from django.contrib.auth.forms import UserCreationForm        #  User registration 
from django.contrib.auth.models import User                   #  User registration 
from django import forms                                      #  User registration 

from django.contrib.auth.forms import AuthenticationForm     # User authentication - Login
from django.forms.widgets import PasswordInput, TextInput    # User authentication - Login

from django.contrib.auth.forms import PasswordResetForm

from .models import Profile
from django.core.exceptions import ValidationError
from core.forms.turnstile import TurnstileFormMixin

# Registration form
class CreateUserForm(TurnstileFormMixin ,UserCreationForm):

    class Meta:

        model = User
        fields= ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, request=None, **kwargs):

        super().__init__(*args, request=request, **kwargs)
        # Mark email field as required
        self.fields['email'].required = True

    #Email valdation
    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError('This email is invalid')
        
        if len(email) >= 350:

            raise forms.ValidationError('Your email is too long')
        
        return email
    

# Login form

class LoginForm(TurnstileFormMixin, AuthenticationForm):

    username = forms.CharField(widget=TextInput())
    password = forms.CharField(widget=PasswordInput())

    def __init__(self, *args, request=None, **kwargs):
        # 注意：AuthenticationForm 期望的是 request=...、data=...
        super().__init__(request=request, *args, **kwargs)



# Update form
class UpdateForm(forms.ModelForm):
    
    password = None

    class Meta:

        model = User

        fields = ['email']

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)

        # Mark email field as required
        self.fields['email'].disabled = True

    #Email valdation
    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():

            raise forms.ValidationError('This email is invalid')
        
        if len(email) >= 350:

            raise forms.ValidationError('Your email is too long')
        
        return email
    
class ProfileUpdateForm(forms.ModelForm):

    class Meta:

        model = Profile
        fields = ['photo', 'name', 'phone']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_photo(self):

        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 2 * 1024 * 1024:  # 2MB 限制
            
            raise ValidationError("圖片大小不能超過 2MB。")
        
        return photo
    

class TurnstilePasswordResetForm(TurnstileFormMixin, PasswordResetForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)