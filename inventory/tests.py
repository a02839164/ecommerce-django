from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from store.models import Product
from inventory.models import InventoryLog
from inventory.services import (
    apply_inventory_sale,
    apply_inventory_refund,
    increase_stock,
    decrease_stock,
)

# 建立假的 Order + OrderItem
class DummyOrder:
    def __init__(self, id, items):
        self.id = id
        self._items = items

    @property
    def orderitem_set(self):
        class Manager:
            def __init__(self, items):
                self._items = items

            def all(self):
                return self._items

        return Manager(self._items)


class DummyOrderItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity


class InventoryServiceTest(TestCase):

    def setUp(self):
        # 建立測試用使用者
        self.user = User.objects.create_user(
            username="admin", password="test123"
        )

        # 建立測試用商品
        self.product = Product.objects.create(
            title="Test Product",
            price=Decimal("100.00"),
            stock=10,
            is_fake=False,
        )

    # 1.測試付款扣庫存
    def test_apply_inventory_sale(self):
        order = DummyOrder(
            id=1,
            items=[DummyOrderItem(self.product, 3)]
        )

        apply_inventory_sale(order)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    # 2.測試付款會寫入 SALE Log
    def test_apply_inventory_sale_log(self):
        order = DummyOrder(
            id=2,
            items=[DummyOrderItem(self.product, 2)]
        )

        apply_inventory_sale(order)

        log = InventoryLog.objects.last()
        self.assertEqual(log.product, self.product)
        self.assertEqual(log.quantity, -2)
        self.assertEqual(log.action, "SALE")
        self.assertIn("Order #2", log.note)

    # 3. 測試退款會補回庫存
    def test_apply_inventory_refund(self):
        order = DummyOrder(
            id=3,
            items=[DummyOrderItem(self.product, 4)]
        )

        apply_inventory_sale(order)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 6)

        apply_inventory_refund(order)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    # 4.測試退款會寫入 REFUND Log
    def test_apply_inventory_refund_log(self):
        order = DummyOrder(
            id=4,
            items=[DummyOrderItem(self.product, 1)]
        )

        apply_inventory_refund(order)

        log = InventoryLog.objects.last()
        self.assertEqual(log.quantity, 1)
        self.assertEqual(log.action, "REFUND")
        self.assertIn("Order #4", log.note)

    # 5.測試手動增加庫存
    def test_increase_stock(self):
        increase_stock(self.product, 5, note="Manual Add", user=self.user)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 15)

        log = InventoryLog.objects.last()
        self.assertEqual(log.quantity, 5)
        self.assertEqual(log.action, "MANUAL_ADD")
        self.assertEqual(log.performed_by, self.user)

    # 6. 測試庫存不足會拋錯
    def test_decrease_stock_not_enough(self):
        with self.assertRaises(ValueError):
            decrease_stock(self.product, 99)
