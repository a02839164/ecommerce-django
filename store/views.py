from django.shortcuts import render,get_object_or_404
from . models import Category , Product
from django.db.models import Q
from django.core.paginator import Paginator
from analytics.services.views_tracker import track_product_view
from analytics.services.hot_products import get_hot_products
from analytics.services.recent_product import get_recent_products

def store(request):

    all_product = Product.objects.filter(is_fake=False)
    hot_products = get_hot_products(days=7, limit=10)
    recent_views = get_recent_products(request, limit=10)


    context = {
        'all_product':all_product,
        'hot_products': hot_products,
        'recent_views':recent_views
    }
    
    return render(request, 'store/store.html', context)


def categories(request):
    all_categories = Category.objects.all()

    return {'all_categories': all_categories}

def list_category(request, category_slug=None):
    category = get_object_or_404(Category,slug = category_slug)
    products = Product.objects.filter(category=category, is_fake=False)
    context = {'category':category ,'products':products}

    return render(request, 'store/list-category.html', context) 


def product_info(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_fake=False )

    track_product_view(request, product)

    context = {'product':product}
    
    return render(request, 'store/product-info.html',context)


def product_search(request):

    query = request.GET.get('q', '').strip()         #取得name = q裡面的value，預設空白，  .strip() 去掉前後空白
    category_id = request.GET.get('category', '')    #取得name = category 裡面的value，預設空白
    sort_by = request.GET.get('sort', 'relevance')   #取得name = sort 裡面的value，預設「相似度」
    results = Product.objects.only("id", "title", "price", "slug", "thumbnail", "category_id")

    # 搜尋條件
    if query:
        results = results.filter(title__icontains=query)

    if category_id:
        results = results.filter(category_id=category_id)

    # 排序
    if sort_by == "price_low":
        results = results.order_by("price", "id")   # 升序
    elif sort_by == "price_high":
        results = results.order_by("-price", "-id") # 降序
    else:
        results = results.order_by("id")            # relevance = id 預設順序

    # 限制最多結果（加速）
    MAX_RESULTS = 1000
    results = results[:MAX_RESULTS]

    # 分頁
    paginator = Paginator(results, 18)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "page_obj": page_obj,
        "selected_category": category_id,
        "categories": Category.objects.all(),
        "sort_by": sort_by,
    }

    return render(request, "store/product-search.html", context)