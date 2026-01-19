from decimal import Decimal
from store.models import Product
import copy


class Cart():

    def __init__(self, request):

        self.session = request.session

        # Returning user - obrain his/her existing session
        cart = self.session.get('session_key')

        # New user - generate a new session
        if 'session_key' not in self.session:

            cart = self.session['session_key'] = {}

        self.cart= cart


    def add(self, product, product_qty):
        product_id = str(product.id)

        if product_id in self.cart:

            self.cart[product_id]['qty'] += product_qty    # 累加
        else:
            self.cart[product_id] = {'qty': product_qty}   # 只存數量

        self.session.modified = True   #session 的內容有改過，存回去


    def delete(self, product_id):

        product_id = str(product_id)

        if product_id in self.cart:

            del self.cart[product_id]

        self.session.modified = True


    def update(self, product_id, qty):

        product_id = str(product_id)
        product_quantity = qty

        if product_id in self.cart:

                self.cart[product_id]['qty'] = product_quantity # 直接設定數量

        self.session.modified = True

    def clear(self):

        if 'session_key' in self.session:

            del self.session['session_key']
            
            self.session.modified = True


    def __len__(self):

        return sum(item['qty'] for item in self.cart.values())
        

    def __iter__(self):

        all_product_ids = self.cart.keys()     #取出字典中所有的key

        products = Product.objects.filter(id__in=all_product_ids)   # 一次從Product抓出所有購物車商品； id__in = id在這個清單裡 

        cart = copy.deepcopy(self.cart)

         # 增強數據（塞入完整產品物件）
        for product in products:             
            product_id = str(product.id)
            cart[product_id]['product'] = product  # 字典中新增一個名為 'product' 的鍵，並把完整的 Product 物件賦值給它
            cart[product_id]['price'] = product.price

        for item in cart.values():

            if 'product' in item:

                item['total'] = item['price'] * item['qty'] # 單一商品的小計

                yield item


    def get_total(self):

        all_product_ids = self.cart.keys()
        products = Product.objects.filter(id__in = all_product_ids)

         # 建立一個查找表 { "id": price }
        price_map = {str(p.id): p.price for p in products}
        
            # 計算總額
        return sum(price_map.get(p_id, 0) * item['qty']  for p_id, item in self.cart.items() if p_id in price_map)
        

    def get_shipping_fee(self):

        total = self.get_total()

        if total >= Decimal(49.00):

            return Decimal('0.00')
        
        else:
            
            return Decimal('9.99')