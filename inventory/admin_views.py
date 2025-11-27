from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .services import increase_stock, decrease_stock
from store.models import Product
from inventory.models import InventoryLog
import csv
import io


#單一商品庫存
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
            return redirect("admin:store_product_changelist")

        except Exception as e:
            messages.error(request, f"錯誤：{str(e)}")

    return render(request, "inventory/adjust_stock.html", {"product": product})



# 下載全部商品庫存（排除 is_fake=TRUE）
@staff_member_required
def download_all_stock_csv():
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="all_product_stock.csv"'

    writer = csv.writer(response)
    writer.writerow(["id", "title", "stock"])

    queryset = Product.objects.filter(is_fake=False).only("id", "title", "stock")  #資料庫龐大，可用.iterator()批次載入

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
            messages.error(request, "格式錯誤，請選擇 CSV 檔案。")
            return redirect("inventory:bulk-stock")

        try:
            decoded = file.read().decode("utf-8")   #讀取csv， decoded UTF-8純字串
            io_string = io.StringIO(decoded)        #字串包裝成檔案物件
            reader = csv.DictReader(io_string)      #讀取「檔案狀態」資料

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
                    error_list.append(f"找不到商品 ID：{product_id}")
                    continue

                old_stock = product.stock
                diff = new_stock - old_stock

                if diff == 0:
                    continue

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
            return redirect("inventory:bulk-stock")


    # Step 2：使用者按「確認匯入」
    if request.method == "POST" and "confirm_import" in request.POST:

        csv_data = request.session.get("bulk_csv")
        if not csv_data:
            messages.error(request, "找不到要匯入的 CSV 資料（session 遺失）。")
            return redirect("inventory:bulk-stock")

        io_string = io.StringIO(csv_data)
        reader = csv.DictReader(io_string)

        success_rows = []
        error_rows = []
        updated_count = 0

        for row in reader:

            # ✨ 跳過整列空白
            if not any(row.values()):
                continue

            product_id = (row.get("id") or "").strip()
            new_stock_raw = (row.get("stock") or "").strip()

            # ✨ id 或 stock 空白 → 跳過並記錄錯誤
            if not product_id or not new_stock_raw:
                error_rows.append(f"缺少欄位（id 或 stock）：{row}")
                continue

            # ✨ stock 必須是整數
            try:
                new_stock = int(new_stock_raw)
            except ValueError:
                error_rows.append(f"無效的庫存數值：{new_stock_raw}")
                continue

            # ✨ 查商品
            try:
                product = Product.objects.get(id=product_id, is_fake=False)
            except Product.DoesNotExist:
                error_rows.append(f"找不到商品 ID：{product_id}")
                continue

            old_stock = product.stock
            diff = new_stock - old_stock

            # ⭐️ 若沒有變化 → 跳過，不寫 Log，不算成功更新
            if diff == 0:

                continue
 
            # ✨ 更新庫存
            product.stock = new_stock
            product.save()

            # ✨ 寫入 Log
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

        # ✨ 清除 session
        request.session.pop("bulk_csv", None)

        return render(request, "inventory/bulk_stock_result.html", {
            "updated": updated_count,
            "success": success_rows,
            "errors": error_rows,
        })

    return render(request, "inventory/bulk_stock.html")