from django.utils import timezone
from datetime import timedelta
from store.models import Product
from payment.models import OrderItem 
from django.db.models import Count, Sum
from django.core.cache import cache
import time

CACHE_TTL_ANALYTICS = 60 * 60

def get_most_viewed_products(days, limit):

    cache_key = f"hot_product:{days}:{limit}"
    lock_key = f"{cache_key}:lock"

    products = cache.get(cache_key)              #依照門牌號碼取得 QuerySet
    if products:
        return products
    
    if cache.add(lock_key, "locked", timeout=10):
        try:

            since = timezone.now() - timedelta(days)
            products = list(
                Product.objects
                .filter(productview__viewed_at__gte=since)
                .annotate(total_views=Count('productview'))
                .order_by('-total_views')[:limit]
            )
            cache.set(cache_key, products, CACHE_TTL_ANALYTICS)
            return products
        finally:

            cache.delete(lock_key)
    else:

        time.sleep(0.1) 
        return get_most_viewed_products(days, limit)



def get_best_selling_products(days, limit):
    cache_key = f"hot_sale:{days}:{limit}"
    lock_key = f"{cache_key}:lock"

    # 先嘗試拿資料，拿得到就直接回傳
    products = cache.get(cache_key)
    if products:
        return products

    # 搶旗
    if cache.add(lock_key, "locked", timeout=10):
        try:
            # 拿到旗的人進資料庫
            since = timezone.now() - timedelta(days)
            qs = (OrderItem.objects
                  .filter(order__date_ordered__gte=since, order__payment_status="COMPLETED")
                  .values("product")
                  .annotate(total_sold=Sum("quantity"))
                  .order_by("-total_sold")[:limit]
                  )
            product_ids = [item["product"] for item in qs]
            products = list(Product.objects.filter(id__in=product_ids))

            # 更新資料門牌，讓之後的人都拿得到
            cache.set(cache_key, products, CACHE_TTL_ANALYTICS)
            return products
        finally:
            # 事情做完(刪除鎖)
            cache.delete(lock_key)
    else:
        # 其他人暫時睡 0.1 秒後再去重新呼叫
        # 等他們醒來，第一個人已經把資料存好了
        time.sleep(0.1)
        return get_best_selling_products(days, limit)