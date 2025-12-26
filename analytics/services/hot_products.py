from django.utils import timezone
from datetime import timedelta
from store.models import Product
from django.db.models import Count



def get_hot_products(days=7, limit=10):
    since = timezone.now() - timedelta(days=days)

    return (
        Product.objects
        .filter(productview__viewed_at__gte=since)
        .annotate(total_views=Count('productview'))
        .order_by('-total_views')
    )[:limit]
