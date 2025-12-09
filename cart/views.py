from django.shortcuts import render

from .cart import Cart
from store.models import Product
from django.shortcuts import get_object_or_404

from django.views.decorators.http import require_POST
from django.http import JsonResponse

from decimal import Decimal

def cart_summary(request):

    cart = Cart(request)
    shipping_fee = cart.get_shipping_fee()
    grand_total = Decimal(cart.get_total()) + shipping_fee
    context= {
        'cart':cart,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total
    }            

    return render(request, 'cart/cart-summary.html', context)


@require_POST
def cart_add(request):
    cart = Cart(request)


    product_id = int(request.POST.get('product_id'))
    product_quantity = int(request.POST.get('product_quantity'))

    product = get_object_or_404(Product,id=product_id)

    # --- 庫存檢查：防止加入沒庫存的商品 ---
    if product.available_stock <= 0:
        return JsonResponse({'error': '商品已售完'}, status=400)
    
    #計算購物車內已有數量 + 新增量 > 庫存 → 禁止加入
    current_cart_qty = cart.cart.get(str(product.id), {}).get("qty", 0)

    # 4. 已有數量 + 新增量 > 庫存 → 禁止
    if current_cart_qty + product_quantity > product.available_stock:
        return JsonResponse({'error': '超過庫存數量'}, status=400)

    cart.add(product=product, product_qty=product_quantity)   # 更新使用者的購物車資料到 session

    cart_quantity = cart.__len__()

    return JsonResponse({'qty':cart_quantity})
    

@require_POST
def cart_delete(request):

    cart = Cart(request)
    product_id = int(request.POST.get('product_id'))
    cart.delete(product = product_id)

    cart_quantity = cart.__len__()
    subtotal = cart.get_total()
    shipping_fee = cart.get_shipping_fee()
    grand_total = subtotal + shipping_fee

    return JsonResponse({
        'qty': cart_quantity,
        'subtotal': str(subtotal),
        'shipping_fee': str(shipping_fee),
        'grand_total': str(grand_total),
    })



@require_POST
def cart_update(request):

    cart = Cart(request)

    product_id = int(request.POST.get('product_id'))
    product_quantity = int(request.POST.get('product_quantity'))

    product = get_object_or_404(Product, id=product_id)

    if product.available_stock <= 0:

        return JsonResponse({'error': '商品已售完'}, status=400)

    # 2. (安全) 最低數量必須是 1
    if product_quantity < 1:
        return JsonResponse({'error': '商品數量不能小於 1'}, status=400)

    # 3. 更新數量不能超過庫存
    if product_quantity > product.available_stock:
        return JsonResponse({'error': '超過庫存數量'}, status=400)


    cart.update(product = product_id, qty = product_quantity)

    cart_quantity = cart.__len__()
    subtotal = cart.get_total()
    shipping_fee = cart.get_shipping_fee()
    grand_total = subtotal + shipping_fee

    return JsonResponse({
        'qty': cart_quantity,
        'subtotal': str(subtotal),
        'shipping_fee': str(shipping_fee),
        'grand_total': str(grand_total),
        
        })
