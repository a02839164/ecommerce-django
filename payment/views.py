from django.shortcuts import render, redirect

from .models import ShippingAddress, Order, OrderItem
from cart.cart import Cart

from django.http import JsonResponse

from django.contrib import messages

from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required

from paypal.api import PaypalService
from decimal import Decimal

from shipping.api import create_shipment, buy_shipping_label
from shipping.fake_webhook import simulate_fake_webhook
from django.utils import timezone
from notifications.handlers.order import send_order_confirm_email

@login_required(login_url='my-login')
def checkout(request):
    
    cart = Cart(request)

    if len(cart) == 0 :

        messages.error(request, "Your shopping cart has no items to check out . ")

        return redirect('cart-summary')


    try:

            # Authenticated users WITH shipping infomation
        shipping_address = ShippingAddress.objects.get(user=request.user.id)

        context = {'shipping':shipping_address}

        return render (request, 'payment/checkout.html', context)

    except :
        
        # Authenticated users with NO shipping infomation
        return render (request, 'payment/checkout.html')




def _validate_required(*values):

    return all(v not in (None, "") for v in values)   #如果有任何一個值是 None 或 ""，回傳整個 all() 變成 False


@require_POST
def create_paypal_order(request):

    cart = Cart(request)

    if len(cart) == 0:

        return JsonResponse({'error':'Cart is empty'}, status=400)

    for item in cart:
        
        product = item['product']
        qty = item['qty']

        if product.stock <= 0:
            return JsonResponse({'error': f'{product.title} 已售完'}, status=400)

        if qty > product.stock:
            return JsonResponse({'error': f'{product.title} 庫存不足'}, status=400)


    total_amount  = cart.get_total() + cart.get_shipping_fee()
    svc =PaypalService()
    order = svc.create_order(total_value=str(total_amount) , currency='USD')

    return JsonResponse({'id':order.id})

@require_POST
def capture_paypal_order(request):

           
        #Shipping cart information
        cart = Cart(request)
        #Get the total price of items
        total_cost = cart.get_total()+ cart.get_shipping_fee()

        if len(cart) == 0:

            return JsonResponse({'error': 'Cart is empty'}, status=400)

        order_id = request.POST.get('order_id')

        name = request.POST.get('name')
        email = request.POST.get('email')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')

        if not _validate_required(order_id, name, email, address1, address2, city):

            return JsonResponse({'error':'Missing fields'}, status=400)

        # All in-one shipping address
        shipping_address = (
            address1 +'\n' +
            address2 +'\n' +
            city +'\n' +
            state +'\n' +
            zipcode +'\n'
        )

        local_total = total_cost

        svc = PaypalService()

        result = svc.capture_order(order_id)

        #驗證交易結果
        status = getattr(result, "status", None)

        if status != "COMPLETED":

            return JsonResponse({'error':'Payment not completed'}, status=400)
        
        paypal_capture = result.purchase_units[0].payments.captures[0]
        paypal_capture_id = paypal_capture.id
        paypal_cur = paypal_capture.amount.currency_code
        paypal_total = Decimal(paypal_capture.amount.value)

        if paypal_cur != "USD":

            return JsonResponse({'error':'Currency mismatch'}, status=400)
        
        if paypal_total != local_total:

            try:
                svc.refund_capture(paypal_capture.id, amount=str(paypal_total), currency=paypal_cur)

            finally:

                return JsonResponse({'error':'Amount mismatch'}, status=400)



        # Create order -> Account users WITH + WITHOUT shipping information
        if request.user.is_authenticated:

            order = Order.objects.create(
                full_name = name,
                email=email,
                shipping_address=shipping_address,

                subtotal = cart.get_total(),
                shipping_fee = cart.get_shipping_fee(),
                amount_paid = total_cost,
                user = request.user,

                paypal_order_id = result.id,
                payer_id = getattr(result.payer, 'payer_id', None),
                paypal_capture_id = paypal_capture_id,
                payment_status = "PENDING",
            )

            order_id = order.pk

            for item in cart:

                OrderItem.objects.create(
                    order_id=order_id,
                    product = item['product'],
                    quantity = item['qty'],
                    price= item['price'],
                    user = request.user
                )

            try:
                # Step 1: 建立 Shipment（Shippo 回傳 rates）
                shipment_res = create_shipment(order, address1, address2, city, state, zipcode)

                if shipment_res.get("rates"):
    
                    #找到 USPS
                    rate = next((r for r in shipment_res["rates"] if r["provider"] == "USPS"), None)


                    # Step 2: 購買 label（Shippo 回傳 tracking number）
                    label_res = buy_shipping_label(rate["object_id"])



                    # Step 3: 寫入 order
                    order.tracking_number = label_res.get("tracking_number")
                    order.shipping_carrier = rate.get("provider")
                    order.shipping_status = label_res.get("tracking_status", "UNKNOWN")
                    order.tracking_updated_at = timezone.now()
                    order.save()

                    # Step 4: Celery 假追蹤狀態
                    simulate_fake_webhook(order.tracking_number)
                    send_order_confirm_email(order)
            except Exception as e:

                print("Shippo API error:", e)



        return JsonResponse({'success': True})


def payment_success(request):

    # Clear shopping cart

    cart = Cart(request)

    cart.clear()



    return render(request,'payment/payment-success.html')


def payment_failed(request):

    return render(request,'payment/payment-failed.html')

