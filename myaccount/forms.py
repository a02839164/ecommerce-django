from django.contrib.auth.forms import UserCreationForm        #  User registration 
from django.contrib.auth.models import User                   #  User registration 
from django import forms                                      #  User registration 

from django.contrib.auth.forms import AuthenticationForm     # User authentication - Login
from django.forms.widgets import PasswordInput, TextInput    # User authentication - Login

from django.contrib.auth.forms import PasswordResetForm
from .models import Profile
from django.core.exceptions import ValidationError
from core.security.turnstile.forms import TurnstileFormMixin
from core.security.email_verification.cooldown import is_cooldown, mark_sent
from PIL import Image
import logging

logger = logging.getLogger(__name__)


# Registration form
class CreateUserForm(TurnstileFormMixin ,UserCreationForm):

    class Meta:

        model = User
        fields= ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, request=None, **kwargs):

        super().__init__(*args, request=request, **kwargs)
        # Mark email field as required
        self.fields['email'].required = True


    def clean_email(self):                                            #  clean_<fieldname>() ； 回傳值寫回 cleaned_data[fieldname]

        email = self.cleaned_data.get('email').lower()

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError('This email is already registered')
        
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

    
class ProfileUpdateForm(forms.ModelForm):

    class Meta:

        model = Profile
        fields = ['photo', 'name', 'phone']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),   # 前端顯示元素
        }

    def clean_photo(self):

        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        if photo.size > 2 * 1024 * 1024:               # 限制大小
             raise ValidationError("圖片大小不能超過 2MB。")
        
        try:
            img = Image.open(photo)                              # 驗證圖片內容
            img.verify()
            if img.width * img.height > 10_000_000:
                raise ValidationError("圖片解析度過大")
        except Exception:
            raise ValidationError("圖片檔案格式不正確或已損壞。")


        return photo
    
# 密碼忘記表單- 新增人機驗證、冷卻時間、擋google用戶
class TurnstilePasswordResetForm(TurnstileFormMixin, PasswordResetForm):

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)


    def save(self, **kwargs):    #重寫 save  加入冷卻時間限制

        email = self.cleaned_data.get("email")
        
        # 1. 檢查冷卻 (使用 'password_reset' 作為 prefix，區隔驗證信)
        if not is_cooldown(email, action="password_reset"):                   # 1-1. can_send去 cache 查 key ； 回傳 False = 可以寄
            # 2. 呼叫父類別真正發信
            super().save(**kwargs)
            
            # 3. 標記已發送
            mark_sent(email, action="password_reset")
        else:
            logger.warning(f"Password reset rate limited for: {email}")


# Action Form
class ResendVerificationEmailForm(TurnstileFormMixin, forms.Form):
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })
    )

    def clean_email(self):
        
        return self.cleaned_data["email"].strip().lower()