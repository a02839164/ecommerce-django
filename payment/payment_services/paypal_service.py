from django.conf import settings
import json
from paypalcheckoutsdk.core import SandboxEnvironment, PayPalHttpClient 
from paypalcheckoutsdk.orders import OrdersGetRequest, OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.payments import CapturesRefundRequest



#建立API連線客戶端
class PaypalClient:


    def __init__(self):
        
        environment = SandboxEnvironment(

            client_id = settings.PAYPAL_CLIENT_ID,
            client_secret = settings.PAYPAL_CLIENT_SECRET

        )
        self.client = PayPalHttpClient(environment)


    def handle_response(self, response):

        #將 PayPal 回傳結果轉成 dict
        return json.loads(response.result.__repr__())


# PayPal 退款與查詢功能
class PaypalService(PaypalClient):

    #訂單查詢
    def get_order(self, order_id: str):

        request = OrdersGetRequest(order_id)
        response = self.client.execute(request)
        return response.result
    
    def create_order(self, total_value: str, currency: str = "USD"):

        request = OrdersCreateRequest()                   #建立「建立訂單」請求物件
        request.prefer("return=representation")           #回傳完整的資料表示
        request.request_body({                            #把要送出的金額、幣別放進請求裡
            "intent": "CAPTURE",           
            "purchase_units": [
                {"amount": {"currency_code": currency, "value": total_value}}
            ]
        })
        response = self.client.execute(request)                #請求送給 PayPal，SDK 幫你處理憑證與 HTTPS 並建立一筆新訂單、存進 PayPal 資料庫 回傳訂單資料存進response
        return response.result                             #從 PayPal 回傳中取出主要資料（訂單 ID、狀態等）
   
    def capture_order(self, order_id: str):
        request = OrdersCaptureRequest(order_id)   #用你傳入捕獲請求的order_id存入request
        request.prefer("return=representation")    #回傳request完整的資料表示
        response = self.client.execute(request)    #驗證該筆訂單是否可扣款 /執行實際付款 /更新伺服器資料庫裡訂單狀態/生成一筆「付款紀錄（capture）」
        return response.result  


    def refund_capture(self, capture_id: str, amount: str, currency: str = "USD"):
        request = CapturesRefundRequest(capture_id)
        request.prefer("return=representation")
        request.request_body({
            "amount": {"value": amount, "currency_code": currency}
        })
        response = self.client.execute(request)     #把退款請求 (request) 交給 PayPal伺服器執行退款/更新資料庫 回傳退款結果存進response
        return response.result