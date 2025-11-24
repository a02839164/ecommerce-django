from django.utils import timezone
from datetime import timedelta
from analytics.models import ProductView
from store.models import Product
from django.db.models import Count



def get_hot_products(days=7, limit=10):
    since = timezone.now() - timedelta(days=days)

    product_ids = (
        ProductView.objects.filter(viewed_at__gte=since)
        .values('product')
        .annotate(total_views=Count('id'))
        .order_by('-total_views')[:limit]
    )

    return Product.objects.filter(id__in=[p['product'] for p in product_ids])
