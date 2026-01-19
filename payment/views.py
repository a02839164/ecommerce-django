from django.shortcuts import render, redirect
from .models import ShippingAddress
from cart.cart import Cart
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from payment.services import CheckoutService
from core.security.rate_limit.limiter import CheckoutRateLimiter

@login_required
def checkout(request):
    
    cart = Cart(request)
    if len(cart) == 0 :

        messages.error(request, "Your shopping cart has no items to check out . ")
        return redirect('cart-summary')


    shipping_address = ShippingAddress.objects.filter(user=request.user).first()
    context = {'shipping':shipping_address}

    return render (request, 'payment/checkout.html', context)



@require_POST
def create_paypal_order(request):

    if not request.user.is_authenticated:
        
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        cart = Cart(request)

        paypal_order = CheckoutService.create_paypal_order(cart=cart)

        return JsonResponse({"id": paypal_order.id})

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        return JsonResponse({"error": "系統忙碌中，請稍後再試"}, status=500)



@require_POST
def capture_paypal_order(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)
    
    if CheckoutRateLimiter.is_blocked(request.user.id):
        return JsonResponse({"error": "Too many failed attempts. Try later."},status=429)

    try:
        order = CheckoutService.capture_paypal_order(
            user=request.user,
            cart=Cart(request),
            order_id=request.POST.get("order_id"),
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            address1=request.POST.get("address1"),
            address2=request.POST.get("address2"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            zipcode=request.POST.get("zipcode"),
        )

        CheckoutRateLimiter.clear(request.user.id)
        return JsonResponse({"success": True, "order_id": order.id})

    except ValueError as e:
        CheckoutRateLimiter.increase_fail(request.user.id) 
        return JsonResponse({"error": str(e)}, status=400)  # 使用者造成的錯誤（欄位錯、金額錯、重複訂單）

    except Exception as e:
        return JsonResponse({"error": "System error, try later"}, status=500) # 系統錯誤，不應該算使用者失敗


def payment_success(request):

    # Clear shopping cart
    cart = Cart(request)
    cart.clear()

    return render(request,'payment/payment-success.html')


def payment_failed(request):

    return render(request,'payment/payment-failed.html')