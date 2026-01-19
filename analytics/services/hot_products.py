from django.utils import timezone
from datetime import timedelta
from store.models import Product
from payment.models import OrderItem 
from django.db.models import Count, Sum
from django.core.cache import cache

CACHE_TTL_ANALYTICS = 60 * 60

def get_most_viewed_products(days, limit):

    cache_key = f"hot_product:{days}:{limit}"
    products = cache.get(cache_key)              #依照門牌號碼取得 QuerySet
    if products is not None:
        return products
    

    since = timezone.now() - timedelta(days)

    products = list(
        Product.objects
        .filter(productview__viewed_at__gte=since)
        .annotate(total_views=Count('productview'))
        .order_by('-total_views')[:limit]
    )

    cache.set(cache_key, products, CACHE_TTL_ANALYTICS)

    return products


def get_best_selling_products(days, limit):
    
    cache_key = f"hot_sale:{days}:{limit}"
    products = cache.get(cache_key)

    if products :
        return products
    

    since = timezone.now() - timedelta(days)

    qs = (OrderItem.objects
          .filter(order__date_ordered__gte=since, order__payment_status="COMPLETED")
          .values("product")
          .annotate(total_sold=Sum("quantity"))
          .order_by("-total_sold")[:limit]
          )
    
    product_ids = [item["product"]for item in qs]

    products = list(Product.objects.filter(id__in=product_ids))
    cache.set(cache_key, products , CACHE_TTL_ANALYTICS)

    return products