from analytics.models import ProductView
from django.utils import timezone
from datetime import timedelta

def track_product_view(request, product):

    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key    
    ip_address = request.META.get("REMOTE_ADDR")

    recent = timezone.now() - timedelta(seconds=60)
    exists= ProductView.objects.filter(product=product,session_id=session_id, viewed_at__gte=recent).exists()

    if exists:
        return

    ProductView.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        session_id=session_id,
        ip_address=ip_address,
    )
