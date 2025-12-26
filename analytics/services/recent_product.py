from django.db.models import Max
from store.models import Product



def get_recent_products(request, limit=10):

    session_id = request.session.session_key

    if not session_id:
        
        request.session.create()
        session_id = request.session.session_key

    return (
        Product.objects
        .filter(productview__session_id=session_id)
        .annotate(latest_view=Max("productview__viewed_at")) #對 Product計算關聯 ProductView 的 viewed_at(最大)最新時間，放到一個 latest_view
        .order_by('-latest_view')
    )[:limit]

