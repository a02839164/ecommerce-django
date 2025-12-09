from inventory.models import InventoryLog
from store.models import Product
from django.db.models import F
from django.db import transaction
from django.db.models.functions import Greatest

@transaction.atomic
def reserve_stock(order):


    for item in order.orderitem_set.all():
        product = Product.objects.select_for_update().get(pk=item.product_id)

        if item.quantity > product.available_stock:
            raise ValueError(f"{product.title} 庫存不足（無法預扣）")

        Product.objects.filter(pk=product.pk).update(
            reserved_stock=F("reserved_stock") + item.quantity
        )

        InventoryLog.objects.create(
            product=product,
            quantity=item.quantity,
            action="RESERVE",
            note=f"RESERVE for order {order.id}",
        )

@transaction.atomic
def release_stock(order):

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
    order.payment_status = "CANCELLED"
    order.save(update_fields=["payment_status"])


@transaction.atomic
def apply_inventory_sale(order):

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

    order.payment_status = "COMPLETED"
    order.save(update_fields=["payment_status"])


@transaction.atomic
def apply_inventory_refund(order):
    
    order = type(order).objects.select_for_update().get(id=order.id)

    if order.payment_status == "REFUNDED":
        return

    for item in order.orderitem_set.select_related("product"):
        product = Product.objects.select_for_update().get(id=item.product.id)

        Product.objects.filter(id=product.id).update(
            stock=F("stock") + item.quantity
        )

        InventoryLog.objects.create(
            product=product,
            quantity=item.quantity,
            action="REFUND",
            note=f"Order #{order.id} PayPal REFUND",
        )

    order.payment_status = "REFUNDED"
    order.save(update_fields=["payment_status"])


        
@transaction.atomic
def increase_stock(product_id, qty, action="MANUAL_ADD", note="", user=None):
    
    product = (Product.objects.select_for_update().get(id=product_id)
    )

    Product.objects.filter(pk=product.pk).update(stock=F("stock") + qty
    )

    InventoryLog.objects.create(
        product=product,
        quantity=qty,
        action=action,
        note=note,
        performed_by=user,
    )

@transaction.atomic
def decrease_stock(product_id, qty, action="SALE", note="", user=None):


    product = Product.objects.select_for_update().get(id=product_id)
    updated = Product.objects.filter(id=product_id,stock__gte=F("reserved_stock") + qty   # stock 必須 ≥ reserved_stock + 這次要扣的 qty
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
