from inventory.models import InventoryLog
from store.models import Product


def apply_inventory_sale(order):
    """
    正式扣庫存（付款完成）
    """
    for item in order.items.all():
        product = item.product

        # 扣庫存
        product.stock -= item.quantity
        product.save()

        # 寫入 Log
        InventoryLog.objects.create(
            product=product,
            quantity=-item.quantity,
            action="SALE",
            note=f"Order #{order.id} PayPal SALE",
        )


def apply_inventory_refund(order):
    """
    補庫存（退款完成）
    """
    for item in order.items.all():
        product = item.product

        product.stock += item.quantity
        product.save()

        InventoryLog.objects.create(
            product=product,
            quantity=item.quantity,
            action="REFUND",
            note=f"Order #{order.id} PayPal REFUND",
        )

        
def increase_stock(product, qty, action="MANUAL_ADD", note="", user=None):
    
    product.stock += qty
    product.save()

    InventoryLog.objects.create(
        product=product,
        quantity=qty,
        action=action,
        note=note,
        performed_by=user
    )

def decrease_stock(product, qty, action="MANUAL_SUB", note="", user=None):
    if product.stock < qty:
        raise ValueError("Not enough stock")

    product.stock -= qty
    product.save()

    InventoryLog.objects.create(
        product=product,
        quantity=-qty,
        action=action,
        note=note,
        performed_by=user
    )