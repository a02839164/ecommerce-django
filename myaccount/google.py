import requests
from django.conf import settings
from django.contrib.auth.models import User

class GoogleOAuthError(Exception):
    pass

def exchange_code_for_user(code: str):

    # 使用 Google OAuth 授權碼交換並取得 Django User ；回傳 user


    token_url = "https://oauth2.googleapis.com/token"           # token endpoint
    data = {
        "code": code,                                           # Google 回傳給的授權碼
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,           # 再次確認是發給 redirect_uri；如果跟第一次授權用的不同，Google 直接拒絕
        "grant_type": "authorization_code",                     # 選擇走授權碼流程
    }

    token_response = requests.post(token_url, data)              # 帶著data，POST去 token_url 換回 token_response
    if token_response.status_code != 200:                             
        raise GoogleOAuthError(f"Token error: {token_response.text}") 

    access_token = token_response.json().get("access_token")            # 把 JSON 字串解析成 dict並取值
    if not access_token:                                             
        raise GoogleOAuthError("No access_token returned from Google")


    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"      # 用 access token 拿使用者資料
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_response = requests.get(userinfo_url, headers=headers)

    if userinfo_response.status_code != 200:
        raise GoogleOAuthError("Failed to fetch user info from Google")

    userinfo = userinfo_response.json()
    email = userinfo.get("email")
    name = userinfo.get("name")

    if not email:
        raise GoogleOAuthError("Google account has no email")


    user, created = User.objects.get_or_create(                      # 建立或取得 Django User
        username=email,
        defaults={"email": email,"first_name": name or "",}
    )

    if created:
        user.set_unusable_password()
        user.save()

        if hasattr(user, "profile"):
            user.profile.is_google_user = True
            user.profile.save()

    return user