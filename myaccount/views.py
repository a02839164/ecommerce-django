import requests
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from .forms import CreateUserForm, LoginForm , UpdateForm, ProfileUpdateForm
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from .tokens import user_tokenizer_generate
from .models import Profile
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from notifications.handlers.account import send_verification_email, send_password_changed_email
from django.db import transaction
from django.urls import reverse

from django.contrib.auth import login, logout
from django.conf import settings
from urllib.parse import urlencode
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from django.contrib import messages

from payment.forms import ShippingForm
from payment.models import ShippingAddress
from payment.models import Order, OrderItem

# def preview_email_template(request):
#     context = {
#         'user': request.user,
#         'activation_link': 'https://example.com/email-verification/MjQ/3kg-xxxx/',
#     }
#     return render(request, 'account/registration/email-verification.html', context)


def register(request):

    form = CreateUserForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        
        with transaction.atomic():

            user = form.save(commit=False)
            user.is_active = False
            user.save()
        
            # Email verification setup (template)
            activation_link = request.build_absolute_uri(
                reverse(
                    'email-verification', 
                    kwargs={
                        'uidb64':urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': user_tokenizer_generate.make_token(user),
                    }
                )
            )

            try:

                send_verification_email(user, activation_link)

            except Exception as e:

                user.delete()

            return redirect('email-verification-sent')

       
    context = {'form':form}

    return render(request, 'account/registration/register.html', context)



def email_verification(request,uidb64, token):
    try:

        unique_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=unique_id)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):

        user = None

    # Success
    if user and user_tokenizer_generate.check_token(user, token):

        user.is_active = True
        user.save()
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

# Login
def my_login(request):

    form = LoginForm(request, data=request.POST or None)

    if  request.method == 'POST' and form.is_valid():

        user = form.get_user()

        if not user.is_active:

            messages.warning(request, 'Your account is inactive. Please verify your email.')
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

    #導向google授權
    google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'   # 登入請求入口

    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,   # 回傳授權碼的網址
        "scope": "openid email profile",                # 要哪些資料
        "access_type": "online",                       # 存取模式； 若要長期登入或自動同步 Google 資料」 - offline
        "prompt": "select_account",                     # 每次登入都可選帳號
    }

    auth_url = f"{google_auth_url}?{urlencode(params)}"

    return redirect(auth_url)

#登入成功後 依照Google OAuth 建立 OAuth 憑證時設定的Authorized redirect URIs 導回

def google_callback(request):

    #google回傳code 交換 token 取得使用者資料
    code = request.GET.get("code")

    if not code :

        return HttpResponse("未收到code , 登入失敗", status=400)
    
    # 取得 access_token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_response = requests.post(token_url, data=data)

    if token_response.status_code != 200:
        return HttpResponse(f"Token 回傳錯誤: {token_response.text}", status = 400)

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return HttpResponse("無法取得 access_token" , status=400)
    
    # 取得使用者資料
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization":f"Bearer {access_token}"}
    userinfo_response = requests.get(userinfo_url,headers=headers)

    if userinfo_response.status_code != 200:
        return HttpResponse("取得使用者資料失敗", status=400)
    
    userinfo = userinfo_response.json()
    email = userinfo.get("email")
    name = userinfo.get("name")

    if not email :
        return HttpResponse("無法取得使用者Email", status=400)
    
    # 建立或取得使用者
    user, created = User.objects.get_or_create(

        username =email,
        defaults={
            "email":email,
            "first_name": name or ""
        }

    )
    if created:
        
        user.set_unusable_password()
        user.save()

        if hasattr(user, "profile"):
            
            user.profile.is_google_user = True
            user.profile.save()

    login(request,user)

    return redirect("dashboard")




@login_required
def dashboard(request):
    return render(request,'account/dashboard.html')


@login_required
def profile_management(request):

    # Updating our user's email and profiles
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

    # Updating our user's email and profiles
    user = request.user
    profile = get_object_or_404(Profile ,user=user)


    if request.method == 'POST':

        user_form = UpdateForm(request.POST, instance=request.user)
        profile_form= ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(request, ' Account updated ')

            return redirect ('profile-management')
        
        else:

            messages.error(request, '更新失敗，請檢查欄位內容。')
            
    else:

        user_form = UpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)
        
    context = {
        'user_form':user_form,
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
        shipping = ShippingAddress.objects.get(user=request.user.id)       # 嘗試去資料庫找 目前登入的使用者 的收件地址

    except ShippingAddress.DoesNotExist:

        shipping = None                                                    # 如果這個使用者還沒有收件地址，就設為 None

    form = ShippingForm(instance=shipping)                                 # 建立一個表單，並把 shipping 資料塞進去。

    if request.method == 'POST':

        form = ShippingForm(request.POST, instance=shipping)

        if form.is_valid():
        
            # Assign the user FK on the object
            shipping_user = form.save(commit=False)                        # form.save(commit=False) → 建立物件，但暫時不要存到資料庫，因為我們還要加上 user。

            # Adding the FK itself
            shipping_user.user = request.user                              # 手動把 user 欄位綁定到目前登入的使用者。

            shipping_user.save()

            return redirect ('profile-management')
    
    context = {'form':form}

    return render(request, 'account/manage-shipping.html', context)



@login_required
def track_orders(request):

    try:
        orders = Order.objects.filter(user=request.user).order_by('-date_ordered')  # 撈出使用者的所有訂單（照日期排序）
        order_list = []

        for order in orders:
            items = OrderItem.objects.filter(order=order)
            order_list.append({
                'order': order,
                'items': items,
            })
        
        paginator = Paginator(order_list, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'page_obj': page_obj}

        return render(request, 'account/track-orders.html', context )
    
    except:

        return render(request, 'account/track-orders.html' )



class MyPasswordChangeView(PasswordChangeView):


    def form_valid(self, form):
        response = super().form_valid(form)
        send_password_changed_email(self.request.user)
        return response