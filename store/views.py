from django.shortcuts import render, get_object_or_404,redirect
from .models import Product,ReviewRating,ProductGallery
from category.models import Category
from carts.models import Cart, CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger , Paginator
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from .forms import Reviewform
from orders.models import OrderProduct

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, is_available=True)
        paginator = Paginator(products,1)
        page=request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products,3)
        page=request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    
    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    category = get_object_or_404(Category, slug=category_slug)
    single_product = get_object_or_404(Product, slug=product_slug, category=category)

    try:
        cart_obj = Cart.objects.get(cart_id=request.session.session_key)
        in_cart = CartItem.objects.filter(cart=cart_obj, product=single_product).exists()
    except Cart.DoesNotExist:
        in_cart = False

    # Check if user purchased product
    if request.user.is_authenticated:
      try:

        orderproduct = OrderProduct.objects.filter(
        user=request.user,
        product_id=single_product.id
        ).exists()
      except OrderProduct.DoesNotExist:
         orderproduct=None
    else:
        orderproduct=None

    #ALWAYS define reviews (outside any try/except)
    reviews = ReviewRating.objects.filter(
        product_id=single_product.id,
        status=True
    )
     
     #get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery':product_gallery,
    }

    return render(request, 'store/product_detail.html', context)

def search(request):
    keyword = request.GET.get('keyword')

    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) |
            Q(product_name__icontains=keyword)
        ).order_by('-created_date')
        product_count = products.count()
    else:
        products = Product.objects.none()
        product_count = 0

    context = {
        'products': products,          
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    product = Product.objects.get(id=product_id)

    if request.method == "POST":

        review = ReviewRating.objects.filter(
            user=request.user,
            product=product
        ).first()

        if review:
            # UPDATE
            form = Reviewform(request.POST, instance=review)
            if form.is_valid():
                form.save()
                messages.success(request, "Your review has been updated.")
                return redirect(url)

        else:
            # CREATE
            form = Reviewform(request.POST)
            if form.is_valid():
                data = form.save(commit=False)
                data.product = product   
                data.user = request.user
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()
                messages.success(request, "Your review has been submitted.")
                return redirect(url)

    return redirect(url)