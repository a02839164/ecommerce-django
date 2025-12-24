from django.utils import timezone
from datetime import timedelta
from store.models import Product
from django.db.models import Count
from django.core.cache import cache


def get_hot_products(days=7, limit=10):

    cache_key = f"hot_product:{days}:{limit}"
    products = cache.get(cache_key)              #依照門牌號碼取得 QuerySet
    if products is not None:
        return products
    

    since = timezone.now() - timedelta(days=days)

    products = (
        Product.objects
        .filter(productview__viewed_at__gte=since)
        .annotate(total_views=Count('productview'))
        .order_by('-total_views')[:limit]
    )

    cache.set(cache_key, products, 60 * 5)

    return products
