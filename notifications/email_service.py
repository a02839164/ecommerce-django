import requests
from django.conf import settings
from django.template.loader import render_to_string


#通用寄信引擎
def send_email_via_requests(subject, to_email, template_base_name, context=None):
    
    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
    context = context or {}

    # text_body = render_to_string(f"email/{template_base_name}.txt", context)
    html_body = render_to_string(f"email/{template_base_name}.html", context)

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject,
            }
        ],
        "from": {"email": settings.DEFAULT_FROM_EMAIL},
        "content": [
            {"type": "text/html", "value": html_body},
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(SENDGRID_API_URL, headers=headers, json=payload)

    print("SendGrid API Response:", response.status_code, response.text)

    response.raise_for_status()  # 失敗會直接 raise，成功會安靜回傳
    return True
