from django.test import TestCase
from cart.cart import Cart
from decimal import Decimal

#模擬 request.session
class DummySession(dict):
    modified = False

class DummyRequest:
    def __init__(self):
        self.session = DummySession()


#單元測試
class CartUnitTests(TestCase):
    
    def setUp(self):

        request = DummyRequest()
        request.session["session_key"] = {
            "1": {"price": "10.00", "qty": 50},   # subtotal = 500
            "2": {"price": "5.00", "qty": 50},    # subtotal = 250
            "3": {"price": "15.00", "qty": 1},    # subtotal = 15
        }

        self.cart = Cart(request)


    def test_len(self):

        self.assertEqual(len(self.cart), 101)


    def test_get_total(self):

        total = self.cart.get_total()

        self.assertEqual(total, Decimal("765.00"))


    def test_shipping_fee_over_49(self):
        self.cart.cart = {"1": {"price": "10.00", "qty": 50}}
        fee = self.cart.get_shipping_fee()

        self.assertEqual(fee, Decimal("0.00"))


    def test_shipping_fee_under_49(self):
        self.cart.cart = {"3": {"price": "15.00", "qty": 1}}
        fee = self.cart.get_shipping_fee()

        self.assertEqual(fee, Decimal("9.99"))


    def test_add_item(self):

        # 清空購物車
        self.cart.cart = {}
        # 偽造一個商品物件 id & price
        class DummyProduct:
            id = 10
            price = Decimal("20.00")

        product = DummyProduct()

        # 加入 3 個
        self.cart.add(product, 3)

        self.assertIn("10", self.cart.cart)
        self.assertEqual(self.cart.cart["10"]["qty"], 3)
        self.assertEqual(self.cart.cart["10"]["price"], "20.00")

        # 再加入 2 個 → 應該累加變 5
        self.cart.add(product, 2)

        self.assertEqual(self.cart.cart["10"]["qty"], 5)



    def test_update_item(self):

        self.cart.cart = {
            "1": {"price": "10.00", "qty": 2}
        }

        self.cart.update("1", 7)

        self.assertEqual(self.cart.cart["1"]["qty"], 7)

    def test_delete_item(self):

        self.cart.cart = {
            "1": {"price": "10.00", "qty": 2},
            "2": {"price": "5.00", "qty": 1},
        }

        self.cart.delete("1")

        self.assertNotIn("1", self.cart.cart)
        self.assertIn("2", self.cart.cart)