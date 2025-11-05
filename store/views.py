from django.shortcuts import render,get_object_or_404
from . models import Category , Product
from django.db.models import Q
from django.core.paginator import Paginator

def store(request):
    all_product = Product.objects.filter(is_fake=False)
    context = {'all_product':all_product}
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
    context = {'product':product}
    
    return render(request, 'store/product-info.html',context)


def product_search(request):

    query = request.GET.get('q', '').strip()         #取得name = q裡面的value，預設空白，  .strip() 去掉前後空白
    category_id = request.GET.get('category', '')    #取得name = category 裡面的value，預設空白
    sort_by = request.GET.get('sort', 'relevance')   #取得name = sort 裡面的value，預設「相似度」
    results = Product.objects.all()

    if query:

        results = results.filter(Q(title__icontains=query)) # icontains不分大小寫的模糊比對
        
    if category_id:

        results = results.filter(category_id=category_id)



    if sort_by == "price_low":

        results = results.order_by('price')

    if sort_by == "price_high":

        results = results.order_by('-price')
    else:

        pass
    

    paginator = Paginator(results.distinct(), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        'query':query,
        # 'results': results.distinct(),
        'page_obj':page_obj,
        'selected_category': category_id,
        'categories': Category.objects.all(),
        'sort_by':sort_by,
    }

    return render(request, 'store/product-search.html', context)