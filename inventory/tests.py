from django.test import TestCase
from django.db import transaction
from store.models import Product
from payment.models import Order, OrderItem
from inventory.models import InventoryLog
from inventory.services import InventoryService



class InventoryServiceTest(TestCase):

    def setUp(self):
        self.product = Product.objects.create(title="測試商品", stock=10, reserved_stock=0, price=1000, is_fake=False)
        self.service = InventoryService()

    # 預扣庫存，產生 Log
    def test_reserve_stock_success(self):

        order = Order.objects.create(amount_paid=1000)
        OrderItem.objects.create(order=order, product=self.product, quantity=3, price=self.product.price)

        self.service.reserve_stock(order)
        self.product.refresh_from_db()

        self.assertEqual(self.product.reserved_stock, 3)
        self.assertTrue(InventoryLog.objects.filter(action="RESERVE", product=self.product).exists())

    # 測試前台 reserve_stock
    def test_reserve_stock_insufficient(self):

        order = Order.objects.create(amount_paid=1000)
        OrderItem.objects.create(order=order, product=self.product, quantity=11, price=self.product.price) # 超過庫存 10

        with self.assertRaises(ValueError) as cm:
            self.service.reserve_stock(order)
        
        self.assertIn("庫存不足（無法預扣）", str(cm.exception))
        self.product.refresh_from_db()
        # 確認失敗沒被預扣
        self.assertEqual(self.product.reserved_stock, 0) 

     # 測試後台 decrease_stock
    def test_decrease_stock_safety(self):

        self.product.reserved_stock = 5
        self.product.save()

        # 目前剩 10 個，預扣 5 個，可用只有 5 個。若嘗試直接減 6 個應該失敗。
        with self.assertRaises(ValueError):
            self.service.decrease_stock(self.product.id, 6)