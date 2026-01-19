import requests
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from .forms import CreateUserForm, LoginForm , ProfileUpdateForm, ResendVerificationEmailForm 
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from .models import Profile
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.db import transaction
from django.contrib.auth import login, logout
from django.conf import settings
from urllib.parse import urlencode
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from payment.forms import ShippingForm
from payment.models import ShippingAddress, Order
from core.security.email_verification.service import EmailVerificationService
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .google import exchange_code_for_user, GoogleOAuthError

def register(request):

    form = CreateUserForm(request.POST or None, request=request)

    if request.method == "POST" and form.is_valid():

        with transaction.atomic():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

        return redirect("email-verification-sent")

    context = {'form':form}

    return render(request,"account/registration/register.html",context)


def email_verification(request,uidb64, token):
    try:
        unique_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=unique_id)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):

        user = None

    # is_active
    if user and user.is_active:

        return redirect("email-verification-success")

    # Success
    if user and default_token_generator.check_token(user, token):

        user.is_active = True
        user.save(update_fields=["is_active"])
        return redirect('email-verification-success')
    
    # Failed
    else:
        return redirect('email-verification-failed')


def email_verification_sent(request):
    return render(request, 'account/registration/email-verification-result.html', {'status':'sent'})

def email_verification_success(request):
    return render(request, 'account/registration/email-verification-result.html', {'status':'success'})

def email_verification_failed(request):
    return render(request, 'account/registration/email-verification-result.html', {'status':'failed'})


@require_http_methods(["GET", "POST"])
def resend_verification_by_email(request):

    form = ResendVerificationEmailForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():

        email = form.cleaned_data["email"]
        user = User.objects.filter(email=email).first()

        if user:
            try:
                EmailVerificationService.send(user)
                
            except ValidationError:

                pass

        messages.info(request,"If the email exists, a verification email has been sent.")
        return redirect("my-login")
    
    context = {'form':form}

    return render(request, "account/registration/resend_verification.html", context)


# Login
def my_login(request):

    form = LoginForm(request=request, data=request.POST or None)

    if  request.method == 'POST' and form.is_valid():

        user = form.get_user()

        if not user.is_active:

            messages.warning(request, 'Your account is inactive. Please verify your email.')
            return redirect('my-login')
        
        elif user.profile.is_google_user:

            messages.error(request, 'This account uses Google Login only. Please sign in with Google instead.')
            return redirect('my-login')

        else:

            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
            
    context = {'form':form}
    return render (request,'account/my-login.html',context)

# Logout
def user_logout(request):
    
    logout(request)

    messages.success(request, 'Logout successful.')

    return redirect('store')



def google_login(request):

    google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'   # 授權端點

    params = {                                          #請求參數
        "response_type": "code",                            # 一次性授權憑證
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,       # 回傳授權碼的網址
        "scope": "openid email profile",                    # 需要的資料
        "access_type": "online",                            # 存取模式； 若要長期登入或自動同步 Google 資料」 - offline
        "prompt": "select_account",                         # 每次登入都可選帳號
    }

    auth_url = f"{google_auth_url}?{urlencode(params)}" # urlencode把 dict轉成URL可使用的字串

    return redirect(auth_url)
#google_login負責產生+導向授權網址，登入、帳號處理在 callback 完成
#登入成功後 依照建立OAuth憑證設定的Authorized redirect URIs 導回
def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Missing code", status=400)

    try:
        user = exchange_code_for_user(code)
    except GoogleOAuthError as e:
        return HttpResponse(str(e), status=400)

    login(request, user)
    return redirect("dashboard")


@login_required
def dashboard(request):
    return render(request,'account/dashboard.html')


@login_required
def profile_management(request):

    # Updating our user's profiles
    user = request.user
    profile = get_object_or_404(Profile ,user=user)

    try:
        shipping = ShippingAddress.objects.get(user=user)
    except ShippingAddress.DoesNotExist:
        shipping = None

    context = {
        'user':user,
        'profile':profile,
        'shipping':shipping     
    }

    return render(request, 'account/profile-management.html', context)


@login_required
def profile_update(request):

    # Updating our user's profiles
    user = request.user
    profile = get_object_or_404(Profile ,user=user)
    profile_form = ProfileUpdateForm(instance=profile)

    if request.method == 'POST':
        # Form(data, instance=obj)  Update 模式
        profile_form= ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if profile_form.is_valid():

            profile_form.save()

            messages.success(request, ' Account updated ')
            return redirect ('profile-management')
        
        else:

            messages.error(request, '更新失敗，請檢查欄位內容。')
        
    context = {
        'profile_form':profile_form,    
    }

    return render(request, 'account/profile-update.html', context)


@login_required
def delete_account(request):

    user = User.objects.get(id=request.user.id)

    if request.method == 'POST':

        confirm = request.POST.get('confirm')

        if confirm.upper() == "YES":
            
            user.delete()

            messages.error(request, ' Account deleted ')

            return redirect ('store')
        
    
    return render(request,'account/delete-account.html')


# Shipping view
@login_required
def manage_shipping(request):

    try:                                                                  
        #Account user with shipment information
        shipping = ShippingAddress.objects.get(user=request.user.id)       # 先去資料庫找 目前登入的使用者 的收件地址

    except ShippingAddress.DoesNotExist:

        shipping = None                                                    # 如果使用者還沒有收件地址，設為 None

    form = ShippingForm(instance=shipping)                                 # Form(data, instance=obj)  Update 模式

    if request.method == 'POST':

        form = ShippingForm(request.POST, instance=shipping)

        if form.is_valid():
        
            # Assign the user FK on the object
            shipping_user = form.save(commit=False)                        # (commit=False)暫時不要存到資料庫
            # Adding the FK itself
            shipping_user.user = request.user                              # 加上 user 欄位
            shipping_user.save()
            return redirect ('profile-management')
    
    context = {'form':form}

    return render(request, 'account/manage-shipping.html', context)



@login_required
def track_orders(request):

        orders = (
            Order.objects
            .filter(user=request.user)           # 篩選使用者的所有訂單
            .order_by('-date_ordered')           # 排序
            .prefetch_related('orderitem_set'))  # 先把下一層的明細一次抓回來 prefetch_related 適用一對多

        paginator = Paginator(orders, 5)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {'page_obj': page_obj}

        return render(request, 'account/track-orders.html', context )