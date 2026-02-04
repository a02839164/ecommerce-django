import json
from django.core.cache import caches
from django_redis import get_redis_connection

def get_client_ip(request):
    # 1. 優先抓取 Cloudflare 提供的真實 IP
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip
    
    # 2. 如果沒有 CF IP，抓取轉發清單 (可能經過 Nginx)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X_FORWARDED_FOR 可能包含多個 IP，第一個通常是真實客戶端
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip
    
    # 3. 最後才拿 REMOTE_ADDR (Docker 內網 IP)
    return request.META.get('REMOTE_ADDR')


def track_product_view(request, product):

    if not request.session.session_key:
            request.session.create()

    ip_address = get_client_ip(request)
    session_id = request.session.session_key
    session_cache = caches['sessions']
    # 防重複計數鎖：60 秒內同個 Session 看同個商品不重複計入 Redis 緩衝
    prevent_key = f"view_prevent:{product.id}:{session_id}"
    if session_cache.get(prevent_key):
        return
    session_cache.set(prevent_key, True, timeout=60)

    # 準備寫入資料庫所需的資料
    view_data = {
        'product_id': product.id,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'session_id': session_id,
        'ip_address': ip_address,
    }

    # 直接使用 Redis 原生連線，將資料存入名為 'product_view_queue' 的列表
    con = get_redis_connection("default")
    con.lpush("product_view_queue", json.dumps(view_data))