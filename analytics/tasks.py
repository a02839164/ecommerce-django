from celery import shared_task
from django_redis import get_redis_connection
import json
from .models import ProductView

@shared_task
def batch_sync_product_views():
    con = get_redis_connection("default")
    views_to_create = []
    
    # 每次最多取出 1000 筆，避免一次處理太多導致記憶體問題
    for _ in range(1000):
        data = con.rpop("product_view_queue")
        if not data:
            break
            
        item = json.loads(data)
        views_to_create.append(ProductView(
            product_id=item['product_id'],
            user_id=item['user_id'],
            session_id=item['session_id'],
            ip_address=item['ip_address']
        ))

    # 使用 bulk_create：將 1000 次 INSERT 變成 1 次 SQL 指令
    if views_to_create:
        ProductView.objects.bulk_create(views_to_create)