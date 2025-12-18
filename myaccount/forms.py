from django.contrib.auth.forms import UserCreationForm        #  User registration 
from django.contrib.auth.models import User                   #  User registration 
from django import forms                                      #  User registration 

from django.contrib.auth.forms import AuthenticationForm     # User authentication - Login
from django.forms.widgets import PasswordInput, TextInput    # User authentication - Login

from django.contrib.auth.forms import PasswordResetForm

from .models import Profile
from django.core.exceptions import ValidationError
from core.security.turnstile.forms import TurnstileFormMixin
from core.security.email_verification.cooldown import can_send, mark_sent

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

    def save(self, **kwargs):
        """
        重寫 save，加入冷卻時間限制
        """
        # 取得表單中的 email
        email = self.cleaned_data.get("email")
        
        # 1. 檢查冷卻 (使用 'password_reset' 作為 prefix，區隔驗證信)
        # 這裡建議設定短一點，例如 1-5 分鐘，防止惡意刷信即可
        if can_send(email, action="password_reset"):
            # 2. 呼叫父類別真正發信
            super().save(**kwargs)
            
            # 3. 標記已發送，設定 60 秒或更久
            mark_sent(email, action="password_reset")
        else:
            # 靜默失敗：不發信，也不報錯
            # 這樣攻擊者不知道該 Email 是否存在，也不知道我們有沒有攔截
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Password reset rate limited for: {email}")


class ResendVerificationEmailForm(forms.Form):
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })
    )