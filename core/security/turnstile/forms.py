# core/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.security.turnstile.service import verify_turnstile


class TurnstileFormMixin(forms.Form):
    """
        在 view 中初始化表單：YourForm(request.POST, request=request)

    功能：
        - 自動從 request.POST 拿 cf-turnstile-response
        - 自動驗證 Turnstile token
        - 驗證失敗會 raise ValidationError
    """
    def __init__(self, *args, request=None, **kwargs):
        self._request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # 只有 POST 才需要驗證
        if self._request and self._request.method == "POST":
            token = self._request.POST.get("cf-turnstile-response")   # Cloudflare JS 自動插入 form 裡的 hidden input
            remote_ip = self._request.META.get("REMOTE_ADDR")         #瀏覽器送到伺服器的 header

            ok, detail = verify_turnstile(token, remote_ip)

            if not ok:
                raise ValidationError(_("❌ 機器人驗證失敗，請再試一次。"))

        return cleaned_data
