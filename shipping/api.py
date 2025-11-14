import requests
from django.conf import settings



def get_order_weight(order):
    
    total = 0

    for item in order.orderitem_set.all():

        total += item.product.weight * item.quantity

    return total



SHIPPO_API_URL = "https://api.goshippo.com"
HEADERS = {
    "Authorization": f"ShippoToken {settings.SHIPPO_API_KEY}",
    "Content-Type": "application/json",
}

def create_shipment(order, address1, address2, city, state, zipcode):
    """
    建立 Shipment，Shippo 回傳所有可選的運送方案（rates）。
    """
    url = f"{SHIPPO_API_URL}/shipments/"

    data = {
        "address_from": {
            "name": "Buyria Store",
            "street1": "525 Market St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
            "country": "US",
            "email": "your_store_email@example.com", 
            "phone": "4151234567",
        },
        "address_to": {
            "name": order.full_name,
            "street1": address1,
            "street2": address2,
            "city": city,
            "state": state,
            "zip": zipcode,
            "country": "US",
        },
        "parcels": [
            {
                "length": "20",
                "width": "15",
                "height": "10",
                "distance_unit": "cm",
                "weight": str(get_order_weight(order)),  # g
                "mass_unit": "g",
            }
        ],
        "async": False,
    }

    response = requests.post(url, headers=HEADERS, json=data)
    return response.json()


def buy_shipping_label(rate_id):
    """
    使用選定 rate 購買 label（產生 tracking number）
    """
    url = f"{SHIPPO_API_URL}/transactions/"

    data = {
        "rate": rate_id,
        "label_file_type": "PDF",
        "async": False,
    }

    response = requests.post(url, headers=HEADERS, json=data)
    return response.json()




def register_test_tracking(tracking_number, carrier="usps"):
    """
    啟動 Shippo Tracking（新版 API 用 GET）
    Test mode 下：GET=啟動模擬 tracking + Register webhook
    """

    url = f"https://api.goshippo.com/tracks/{carrier}/{tracking_number}"

    headers = {
        "Authorization": f"Shippo Token {settings.SHIPPO_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    # Debug 用的，可寫 log
    print("Shippo tracking init response:", response.status_code, response.text)

    return response