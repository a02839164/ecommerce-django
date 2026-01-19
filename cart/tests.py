from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from store.models import Product
from cart.cart import Cart
from decimal import Decimal


#單元測試
class CartUnitTests(TestCase):
    
    def setUp(self):
        # 建立測試商品
        self.product1 = Product.objects.create(id=10,title="測試商品1",price=Decimal("20.00"),stock=100)
        self.product2 = Product.objects.create(id=11,title="測試商品2",price=Decimal("745.00"),stock=10)

        # 模擬 Request 與 Session
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        # 讓 request 擁有 session 功能
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(self.request)
        self.request.session.save()

        self.cart = Cart(self.request)


    def test_len(self):
        self.cart.add(product=self.product1, product_qty=2)
        self.cart.add(product=self.product2, product_qty=5)
        self.assertEqual(len(self.cart), 7)


    def test_get_total(self):

        self.cart.add(product=self.product1, product_qty=2)  # 20 * 2 = 40
        self.cart.add(product=self.product2, product_qty=1)  # 745 * 1 = 745
        self.assertEqual(self.cart.get_total(), Decimal("785.00"))

    def test_add_item(self):

        self.cart.add(product=self.product1, product_qty=2)
        # 驗證 Session 只存 ID 和數量
        self.assertEqual(self.request.session['session_key']["10"]["qty"], 2)
        self.cart.add(product=self.product1, product_qty=2)
        self.assertEqual(len(self.cart), 4)

    def test_update_item(self):

        self.cart.add(product=self.product1, product_qty=1)
        self.cart.update(product_id=10, qty=10)
        self.assertEqual(self.cart.cart["10"]["qty"], 10)
        self.assertEqual(len(self.cart), 10)

    def test_delete_item(self):

        self.cart.add(product=self.product1, product_qty=1)
        self.cart.delete(product_id=10)
        self.assertNotIn("10", self.cart.cart)
        self.assertEqual(len(self.cart), 0)


    def test_shipping_fee_over_49(self):

        self.cart.add(product=self.product2, product_qty=1) # 745 元
        self.assertEqual(self.cart.get_shipping_fee(), Decimal("0.00"))


    def test_shipping_fee_under_49(self):

        self.cart.add(product=self.product1, product_qty=1) # 20 元
        self.assertEqual(self.cart.get_shipping_fee(), Decimal("9.99"))
