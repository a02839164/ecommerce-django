from inventory.models import InventoryLog
from store.models import Product
from django.db.models import F
from django.db import transaction
from django.db.models.functions import Greatest
import csv
import io

class InventoryService:

    @staticmethod
    @transaction.atomic
    def reserve_stock(order):

        # transaction.atomic + select_for_update
        for item in order.orderitem_set.all():
            product = Product.objects.select_for_update().get(pk=item.product_id)

            if item.quantity > product.available_stock:
                raise ValueError(f"{product.title} 庫存不足（無法預扣）")

            # update + F()原子更新剛剛鎖住的這一筆 product
            Product.objects.filter(pk=product.pk).update(
                reserved_stock=F("reserved_stock") + item.quantity
            )

            InventoryLog.objects.create(
                product=product,
                quantity=item.quantity,
                action="RESERVE",
                note=f"RESERVE for order {order.id}",
            )

    @staticmethod
    @transaction.atomic
    def release_stock(order):

        if order.payment_status == "CANCELLED":
            return

        for item in order.orderitem_set.all():
            product = Product.objects.select_for_update().get(pk=item.product_id)

            Product.objects.filter(pk=product.pk).update(
                reserved_stock=Greatest(F("reserved_stock") - item.quantity, 0)
            )

            InventoryLog.objects.create(
                product=product,
                quantity=item.quantity,
                action="RELEASE",
                note=f"RELEASE for order {order.id}",
            )


    @staticmethod
    @transaction.atomic
    def apply_inventory_sale(order):

        if order.payment_status == "COMPLETED":
            return

        for item in order.orderitem_set.all():
            product = Product.objects.select_for_update().get(pk=item.product_id)

            if product.reserved_stock < item.quantity:
                raise ValueError(f"Reserved stock mismatch for product {product.id}")

            Product.objects.filter(pk=product.pk).update(
                stock=Greatest(F("stock") - item.quantity,0),
                reserved_stock=Greatest(F("reserved_stock") - item.quantity,0)
            )

            InventoryLog.objects.create(
                product=product,
                quantity=-item.quantity,
                action="SALE",
                note=f"Order #{order.id} PayPal SALE",
            )


    @staticmethod
    @transaction.atomic
    def apply_inventory_refund(order):
        
        order = type(order).objects.select_for_update().get(id=order.id)

        if order.payment_status == "REFUNDED":
            return

        for item in order.orderitem_set.all():
            product = Product.objects.select_for_update().get(pk=item.product_id)

            Product.objects.filter(pk=product.pk).update(
                stock=F("stock") + item.quantity
            )

            InventoryLog.objects.create(
                product=product,
                quantity=item.quantity,
                action="REFUND",
                note=f"Order #{order.id} PayPal REFUND",
            )


    @staticmethod             
    @transaction.atomic
    def increase_stock(product_id, qty, action="MANUAL_ADD", note="", user=None):
        
        product = Product.objects.select_for_update().get(id=product_id)

        Product.objects.filter(pk=product.pk).update(stock=F("stock") + qty )

        InventoryLog.objects.create(
            product=product,
            quantity=qty,
            action=action,
            note=note,
            performed_by=user,
        )

    @staticmethod
    @transaction.atomic
    def decrease_stock(product_id, qty, action="SALE", note="", user=None):


        product = Product.objects.select_for_update().get(id=product_id)

        # 篩選出  id + stock 必須大於 (reserved_stock + 這次要扣的 qty) 再去做更新
        updated = Product.objects.filter(id=product_id,stock__gte=F("reserved_stock") + qty   
        ).update(stock=F("stock") - qty)

        if updated == 0:
            raise ValueError("庫存不足，或目前有進行中的預扣訂單，無法直接減庫存")

        InventoryLog.objects.create(
            product=product,
            quantity=-qty,
            action=action,
            note=note,
            performed_by=user,
        )

    @staticmethod
    def parse_and_validate_csv(csv_data):

        io_string = io.StringIO(csv_data)
        reader = csv.DictReader(io_string)
        
        preview_list = []
        error_list = []

        for row in reader:
            if not any(row.values()): 
                continue
            
            pid = (row.get("id") or "").strip()
            raw_s = (row.get("stock") or "").strip()

            if not pid or not raw_s:
                error_list.append(f"缺少資料：{row}")
                continue

            try:
                new_stock = int(raw_s)
                product = Product.objects.get(id=pid, is_fake=False)
                
                old_stock = product.stock
                diff = new_stock - old_stock
                
                # 只有變動的才放入預覽
                if diff != 0:
                    preview_list.append({
                        "product": product,
                        "old": old_stock,
                        "new": new_stock,
                        "diff": diff,
                        "reserved": product.reserved_stock
                    })
            except Product.DoesNotExist:
                error_list.append(f"找不到商品 ID：{pid}")
            except ValueError:
                error_list.append(f"無效的庫存數值：{raw_s}")
            except Exception as e:
                error_list.append(f"未知錯誤：{str(e)}")

        return preview_list, error_list

    @staticmethod
    def execute_bulk_import(preview_data, user):

        updated_count = 0
        success_rows = []
        
        with transaction.atomic():
            for item in preview_data:
                product = item['product']
                new_stock = item['new']
                
                # 再次鎖定並執行最終檢查
                locked_product = Product.objects.select_for_update().get(id=product.id)
                
                if new_stock < locked_product.reserved_stock:
                    raise Exception(f"ID {product.id} 新庫存不可小於預扣量")

                old_stock = locked_product.stock
                locked_product.stock = new_stock
                locked_product.save(update_fields=["stock"])

                InventoryLog.objects.create(
                    product=locked_product,
                    quantity=new_stock - old_stock,
                    action="BULK_UPDATE",
                    note="Service Bulk Import",
                    performed_by=user
                )
                
                success_rows.append(item)
                updated_count += 1
                
        return updated_count, success_rows