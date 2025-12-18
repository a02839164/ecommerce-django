# payment/services.py
from payment.models import Order, OrderItem
from paypal.services import PaypalService
from inventory.services import InventoryService
from shipping.services import create_shipment, buy_shipping_label
from shipping.fake_webhook import simulate_fake_webhook
from decimal import Decimal
from django.utils import timezone
from django.db import transaction


class CheckoutService:

    @staticmethod
    def _validate_required(*values):
        return all(v is not None and str(v).strip() != "" for v in values)   #如果有任何一個值是 None 或 ""，回傳整個 all() 變成 False


    @staticmethod
    def create_paypal_order(*, cart):
        """
        ✅ 建立 PayPal 訂單（尚未扣款）
        原本 view 內：
        - 檢查購物車是否為空
        - 檢查每個商品的 available_stock
        - 計算總金額
        - 呼叫 PayPal create_order
        """

        if len(cart) == 0:
            raise ValueError("Cart is empty")

        for item in cart:
            product = item["product"]
            qty = item["qty"]

            if product.available_stock <= 0:
                raise ValueError(f"{product.title} 已售完")

            if qty > product.available_stock:
                raise ValueError(f"{product.title} 庫存不足")

        total_amount = cart.get_total() + cart.get_shipping_fee()

        svc = PaypalService()
        order = svc.create_order(
            total_value=str(total_amount),
            currency="USD"
        )

        # ✅ 回傳 PayPal 原始 order（裡面有 id 給前端用）
        return order


    @staticmethod
    @transaction.atomic
    def capture_paypal_order(*,user,cart,order_id,name,email,address1,address2,city,state,zipcode,):
        """
    ✅ 交易總指揮：
    - 驗證 PayPal 付款結果
    - 驗證金額與幣別
    - 建立訂單
    - 預扣庫存
    - 建立物流
        """
    
        # -------------------------------------------------
        # 0️⃣ 基本防呆
        # -------------------------------------------------

        if not user or not user.is_authenticated:
            raise ValueError("Login required")
        
        if Order.objects.filter(paypal_order_id=order_id).exists():
            raise ValueError("Duplicate PayPal order")
        
        if len(cart) == 0:
            raise ValueError("Cart is empty")

        if not CheckoutService._validate_required(order_id, name, email, address1, address2, city):
            raise ValueError("Missing fields")

        total_cost = cart.get_total() + cart.get_shipping_fee()

        shipping_address = "\n".join([
            address1 or "",
            address2 or "",
            city or "",
            state or "",
            zipcode or "",
        ])

        # -------------------------------------------------
        # 1️⃣ 呼叫 PayPal Capture
        # -------------------------------------------------
        svc = PaypalService()
        result = svc.capture_order(order_id)

        # -------------------------------------------------
        # 2️⃣ 交易驗證（✅ 正確歸位在 payment）
        # -------------------------------------------------
        status = getattr(result, "status", None)
        if status != "COMPLETED":
            raise ValueError("Payment not completed")

        paypal_capture = result.purchase_units[0].payments.captures[0]
        paypal_capture_id = paypal_capture.id
        paypal_cur = paypal_capture.amount.currency_code
        paypal_total = Decimal(paypal_capture.amount.value)

        if paypal_cur != "USD":
            raise ValueError("Currency mismatch")

        if paypal_total != total_cost:
            # ✅ 金額不符 → 強制退款
            svc.refund_capture(
                paypal_capture_id,
                amount=str(paypal_total),
                currency=paypal_cur,
            )
            raise ValueError("Amount mismatch")

        # -------------------------------------------------
        # 3️⃣ 建立訂單與 OrderItem
        # -------------------------------------------------
        order = Order.objects.create(
            full_name=name,
            email=email,
            shipping_address=shipping_address,

            subtotal=cart.get_total(),
            shipping_fee=cart.get_shipping_fee(),
            amount_paid=total_cost,

            user=user,

            paypal_order_id=result.id,
            payer_id=getattr(result.payer, "payer_id", None),
            paypal_capture_id=paypal_capture_id,
            payment_status="PENDING",
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["qty"],
                price=item["price"],
                user=user,
            )

        # -------------------------------------------------
        # 4️⃣ 預扣庫存（✅ 唯一合法入口）
        # -------------------------------------------------
        try:
            InventoryService.reserve_stock(order)
        except Exception as e:
            # ✅ 預扣失敗 → 自動退款
            svc.refund_capture(
                paypal_capture_id,
                amount=str(paypal_total),
                currency=paypal_cur,
            )

            order.payment_status = "FAILED"
            order.save(update_fields=["payment_status"])

            raise ValueError(f"Stock error: {str(e)}")

        # -------------------------------------------------
        # 5️⃣ 建立物流（Shippo）
        # -------------------------------------------------
        try:
            shipment_res = create_shipment(
                order,
                address1,
                address2,
                city,
                state,
                zipcode,
            )

            if shipment_res.get("rates"):
                # ✅ 你原本是找 USPS
                rate = next(
                    (r for r in shipment_res["rates"] if r["provider"] == "USPS"),
                    None
                )

                if rate:
                    label_res = buy_shipping_label(rate["object_id"])

                    order.tracking_number = label_res.get("tracking_number")
                    order.shipping_carrier = rate.get("provider")
                    order.shipping_status = label_res.get("tracking_status", "UNKNOWN")
                    order.tracking_updated_at = timezone.now()
                    order.save(
                        update_fields=[
                            "tracking_number",
                            "shipping_carrier",
                            "shipping_status",
                            "tracking_updated_at",
                        ]
                    )
                    simulate_fake_webhook(order.tracking_number)

        except Exception as e:
            # ⚠️ 物流錯誤不回滾付款（避免實務災難）
            print("Shippo API error:", e)

        # -------------------------------------------------
        # ✅ 交易完成
        # -------------------------------------------------
        return order
