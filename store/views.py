from django.shortcuts import render,get_object_or_404
from . models import Category , Product
from django.core.paginator import Paginator
from analytics.services.views_tracker import track_product_view
from analytics.services.hot_products import get_most_viewed_products, get_best_selling_products
from analytics.services.recent_product import get_recent_products
from django.db import connection
import math

class MockPage:
    def __init__(self, items, number, total, limit):
        self.object_list = items
        self.number = number
        self.total_count = total
        self.num_pages = math.ceil(total / limit) if total > 0 else 1
        start = max(1, self.number - 5)
        end = min(self.num_pages, self.number + 5)
        self.page_range = range(start, end + 1)
    def __iter__(self): return iter(self.object_list)
    def has_other_pages(self): return self.num_pages > 1
    def has_next(self): return self.number < self.num_pages
    def has_previous(self): return self.number > 1
    def next_page_number(self): return self.number + 1
    def previous_page_number(self): return self.number - 1


def store(request):

    all_product = Product.objects.filter(is_fake=False)
    most_viewed_products = get_most_viewed_products(days=7, limit=10)
    best_selling_products = get_best_selling_products(days=90, limit=10)
    recent_views = get_recent_products(request, limit=10)

    context = {
        'all_product':all_product,
        'most_viewed_products': most_viewed_products,
        'recent_views':recent_views,
        'best_selling_products':best_selling_products
    }
    
    return render(request, 'store/store.html', context)


def list_category(request, category_slug):
    category = get_object_or_404(Category,slug = category_slug)
    products_list = Product.objects.filter(
        category=category, 
        is_fake=False
    ).only('title', 'price', 'slug', 'thumbnail').order_by('-id')

    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    context = {'category': category, 'products': products}


    return render(request, 'store/list-category.html', context) 


def product_info(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_fake=False )

    track_product_view(request, product)

    context = {'product':product}
    
    return render(request, 'store/product-info.html',context)


def product_search(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'relevance') # 取得排序參數
    try:
        page = int(request.GET.get('page', 1))
        if page < 1: page = 1
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * 18

    if query:

        search_filter = "WHERE (title ILIKE %s OR brand ILIKE %s)"
        params = [f'%{query}%', f'%{query}%']

        if category_id:
            search_filter += " AND category_id = %s"
            params.append(category_id)

        count_sql = f"SELECT COUNT(*) FROM store_product {search_filter}"

        with connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()[0]


        if sort_by == "price_low":
            order_sql = "ORDER BY price ASC, id DESC"
        elif sort_by == "price_high":
            order_sql = "ORDER BY price DESC, id DESC"
        else:
            order_sql = "ORDER BY id DESC"  
            
        paged_params = params + [offset]
        paged_sql = f"SELECT id FROM store_product {search_filter} {order_sql} LIMIT 18 OFFSET %s"

        with connection.cursor() as cursor:
            cursor.execute(paged_sql, paged_params)
            ids = [row[0] for row in cursor.fetchall()]

        if not ids:
            page_obj = None
        else:
            # 3. 拿到 ID 後，這裏的排序也要跟 SQL 保持一致，否則順序會亂掉
            results = Product.objects.filter(id__in=ids)
            if sort_by == "price_low":
                results = results.order_by("price", "id")
            elif sort_by == "price_high":
                results = results.order_by("-price", "-id")
            else:
                results = results.order_by("-id")

            page_obj = MockPage(list(results), page, total_count, 18)
    else:
        # 沒搜尋時走正常分頁
        results = Product.objects.all().order_by("-id")
        if category_id:
            results = results.filter(category_id=category_id)

        if sort_by == 'price_low':
            results = results.order_by('price')
        elif sort_by == 'price_high':
            results = results.order_by('-price')
        else:
            results = results.order_by('-id')

        total_count = results.count()
        paged_results = results[offset : offset + 18].select_related('category')
        page_obj = MockPage(list(paged_results), page, total_count, 18)

    context = {
        "query": query,
        "page_obj": page_obj,
        "selected_category": category_id,
        "categories": Category.objects.all(),
        "sort_by": sort_by,
    }
    return render(request, "store/product-search.html", context)