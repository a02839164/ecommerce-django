from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .services import InventoryService
from store.models import Product
from django.utils import timezone
import csv
from django.core.cache import cache
import uuid


# 單一商品庫存
@staff_member_required
def adjust_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST" and not request.user.is_superuser:
        messages.error(request, "您沒有權限調整庫存")
        return redirect(request.path)

    if request.method == "POST" and request.user.is_superuser:
        qty = int(request.POST.get("qty"))
        note = request.POST.get("note") or ""

        try:
            if qty > 0:

                InventoryService.increase_stock(product.id, qty, note=note, user=request.user)

            else:
                
                InventoryService.decrease_stock(product.id, abs(qty), note=note, user=request.user)

            messages.success(request, "庫存調整成功")
            return redirect("admin:store_product_changelist")

        except Exception as e:
            messages.error(request, f"錯誤：{str(e)}")

    return render(request, "inventory/adjust_stock.html", {"product": product})


# 下載全部商品庫存（ 含 reserved 與 available）
@staff_member_required
def download_all_stock_csv(request):

    today_str = timezone.now().strftime("%Y-%m-%d")
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="all_product_stock_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(["id","title","stock","reserved_stock","available_stock"])

    queryset = Product.objects.filter(is_fake=False).only("id", "title", "stock", "reserved_stock")

    for p in queryset:
        available = p.stock - p.reserved_stock
        writer.writerow([p.id, p.title, p.stock, p.reserved_stock, available])

    return response



#批次匯入庫存（含：下載、預覽、匯入）
@staff_member_required
def bulk_update_stock(request):

    # Step 0：下載目前庫存 CSV
    if "download_all" in request.GET:
        return download_all_stock_csv(request)

    # Step 1：預覽
    if request.method == "POST" and "preview" in request.POST:

        file = request.FILES.get("file")
        if not file:
            messages.error(request, "格式錯誤，請選擇 CSV 檔案。")
            return redirect("inventory:bulk-stock")
        
        if not request.user.is_superuser:
            messages.error(request, "您沒有權限進行庫存匯入。")
            return redirect("inventory:bulk-stock")

        try:

            decoded = file.read().decode("utf-8-sig")   # 讀取csv
            preview_list, error_list = InventoryService.parse_and_validate_csv(decoded)

            cache_key = f"bulk_csv_{uuid.uuid4()}"
            cache.set(cache_key, decoded, timeout=600)
            request.session["bulk_stock_cache"] = cache_key

            return render(request, "inventory/bulk_stock_preview.html", {"preview_data":preview_list,"errors":error_list,})

        except Exception as e:
            messages.error(request, f"解析 CSV 發生錯誤：{e}")
            return redirect("inventory:bulk-stock")


    # Step 2：預覽後匯入
    if request.method == "POST" and "confirm_import" in request.POST:
        cache_key = request.session.get("bulk_stock_cache")
        csv_data = cache.get(cache_key)

        if not csv_data:
            messages.error(request, "暫存資料已過期")
            return redirect("inventory:bulk-stock")
        
        if not request.user.is_superuser:
            messages.error(request, "您沒有權限進行庫存匯入。")
            return redirect("inventory:bulk-stock")
        try:
            preview_list, error_list = InventoryService.parse_and_validate_csv(csv_data)

            if not preview_list and error_list:
            
                messages.error(request, "資料解析後發現嚴重錯誤，無法匯入。")
                return redirect("inventory:bulk-stock")
            
            updated, success = InventoryService.execute_bulk_import(preview_list, request.user)

            cache.delete(cache_key)
            if "bulk_stock_cache" in request.session:
                del request.session["bulk_stock_cache"]

            return render(request, "inventory/bulk_stock_result.html", {"updated":updated, "success":success})
        
        except Exception as e:

            messages.error(request, f"匯入失敗：{e}")
            return redirect("inventory:bulk-stock")
        

    return render(request, "inventory/bulk_stock.html")