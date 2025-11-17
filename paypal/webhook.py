import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def paypal_webhook(request):
    # Step 1：取得原始 body（PayPal 的 JSON）
    raw_body = request.body.decode('utf-8')

    # Step 2：印出內容（之後你在 console / log 會看到）
    print("===== PAYPAL WEBHOOK RECEIVED =====")
    print(raw_body)
    print("====================================")

    # Step 3：回 200（很重要，否則 PayPal 會重送 25 次）
    return JsonResponse({"status": "ok"})

