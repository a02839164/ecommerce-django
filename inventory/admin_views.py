from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .services import increase_stock, decrease_stock
from store.models import Product



@staff_member_required
def adjust_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        qty = int(request.POST.get("qty"))
        note = request.POST.get("note") or ""

        try:
            if qty > 0:

                increase_stock(product, qty, note=note, user=request.user)

            else:
                
                decrease_stock(product, abs(qty), note=note, user=request.user)

            messages.success(request, "庫存調整成功")
            return redirect("/admin/store/product/")

        except Exception as e:
            messages.error(request, f"錯誤：{str(e)}")

    return render(request, "inventory/adjust_stock.html", {"product": product})
