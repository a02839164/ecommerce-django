from analytics.models import ProductView

def track_product_view(request, product):
    session_id = request.session.session_key or request.session.save()
    ip_address = request.META.get("REMOTE_ADDR")

    ProductView.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        session_id=session_id,
        ip_address=ip_address,
    )
