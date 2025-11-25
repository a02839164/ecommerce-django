from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .services import increase_stock, decrease_stock
from store.models import Product
from inventory.models import InventoryLog
import csv
import io



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



# 下載全部商品庫存（排除 is_fake=TRUE）
def download_all_stock_csv():
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="all_product_stock.csv"'

    writer = csv.writer(response)
    writer.writerow(["id", "title", "stock"])

    queryset = Product.objects.filter(is_fake=False).only("id", "title", "stock")

    for p in queryset:
        writer.writerow([p.id, p.title, p.stock])

    return response


#批次匯入庫存（含：下載、預覽、匯入）
@staff_member_required
def bulk_update_stock(request):


    # Step 0：下載目前庫存 CSV
    if "download_all" in request.GET:
        return download_all_stock_csv()



    # Step 1：收到 CSV → 預覽差異
    if request.method == "POST" and "preview" in request.POST:

        file = request.FILES.get("file")
        if not file:
            messages.error(request, "請選擇 CSV 檔案。")
            return redirect("bulk-stock")

        try:
            decoded = file.read().decode("utf-8")
            io_string = io.StringIO(decoded)
            reader = csv.DictReader(io_string)

            preview_list = []
            error_list = []

            for row in reader:
                product_id = row.get("id")
                new_stock_raw = row.get("stock")

                # 格式錯誤檢查
                if not product_id or not new_stock_raw:
                    error_list.append(f"缺少資料：{row}")
                    continue

                try:
                    new_stock = int(new_stock_raw)
                except:
                    error_list.append(f"無效的庫存數值：{new_stock_raw}")
                    continue

                # 查商品（排除 fake）
                try:
                    product = Product.objects.get(id=product_id, is_fake=False)
                except Product.DoesNotExist:
                    error_list.append(f"找不到商品 ID：{product_id}（可能是假商品）")
                    continue

                old_stock = product.stock
                diff = new_stock - old_stock

                preview_list.append({
                    "product": product,
                    "old": old_stock,
                    "new": new_stock,
                    "diff": diff,
                })

            # 保存 CSV 內容到 session，稍後用於「真正匯入」
            request.session["bulk_csv"] = decoded

            return render(request, "inventory/bulk_stock_preview.html", {
                "preview_data": preview_list,
                "errors": error_list,
            })

        except Exception as e:
            messages.error(request, f"解析 CSV 發生錯誤：{e}")
            return redirect("bulk-stock")



    # Step 2：使用者按「確認匯入」
    if request.method == "POST" and "confirm_import" in request.POST:

        csv_data = request.session.get("bulk_csv")
        if not csv_data:
            messages.error(request, "找不到要匯入的 CSV 資料（session 遺失）。")
            return redirect("bulk-stock")

        io_string = io.StringIO(csv_data)
        reader = csv.DictReader(io_string)

        success_rows = []
        error_rows = []
        updated_count = 0

        for row in reader:

            if not any(row.values()):
                continue

            product_id = row.get("id")
            new_stock = int(row.get("stock"))

            if not product_id or not new_stock:

                continue

            try:
                product = Product.objects.get(id=product_id, is_fake=False)

            except Product.DoesNotExist:
                
                error_rows.append(f"找不到商品 ID：{product_id}")
                continue

            old_stock = product.stock
            diff = new_stock - old_stock

            # 更新庫存
            product.stock = new_stock
            product.save()

            # 寫入庫存 Log
            InventoryLog.objects.create(
                product=product,
                quantity=diff,
                action="BULK_UPDATE",
                note=f"BULK IMPORT: {old_stock} → {new_stock}",
            )

            success_rows.append({
                "product": product,
                "old": old_stock,
                "new": new_stock,
                "diff": diff,
            })

            updated_count += 1

        # 清除 session
        if "bulk_csv" in request.session:
            del request.session["bulk_csv"]

        return render(request, "inventory/bulk_stock_result.html", {
            "updated": updated_count,
            "success": success_rows,
            "errors": error_rows,
        })


    # -----------------------------------------
    # 🔹 Step 0：預設 GET → 顯示上傳頁
    # -----------------------------------------
    return render(request, "inventory/bulk_stock.html")