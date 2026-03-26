from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product,Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required



def cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)

    # ================= AUTHENTICATED USER =================
    if current_user.is_authenticated:
        product_variation = []

        if request.method == 'POST':
            for key, value in request.POST.items():
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        # get cart items (QUERYSET, NOT exists)
        cart_items = CartItem.objects.filter(product=product, user=current_user)

        if cart_items.exists():
            for item in cart_items:
                existing_variations = list(item.variations.all())

                if existing_variations == product_variation:
                    item.quantity += 1
                    item.save()
                    return redirect('carts:cart')

        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=current_user
        )

        if product_variation:
            cart_item.variations.add(*product_variation)

        cart_item.save()
        return redirect('carts:cart')

    # ================= GUEST USER =================
    else:
        product_variation = []

        if request.method == 'POST':
            for key, value in request.POST.items():
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        cart, created = Cart.objects.get_or_create(
            cart_id=cart_id(request)
        )

        cart_items = CartItem.objects.filter(product=product, cart=cart)

        if cart_items.exists():
            for item in cart_items:
                existing_variations = list(item.variations.all())

                if existing_variations == product_variation:
                    item.quantity += 1
                    item.save()
                    return redirect('carts:cart')

        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )

        if product_variation:
            cart_item.variations.add(*product_variation)

        cart_item.save()
        return redirect('carts:cart')


def cart(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    cart_items = []

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    else:
        cart = Cart.objects.get(cart_id=cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/cart.html', context)


def decrease_cart(request, cart_item_id):

    if request.user.is_authenticated:
        cart_item = get_object_or_404(
            CartItem,
            id=cart_item_id,
            user=request.user
        )
    else:
        if not request.session.session_key:
            request.session.create()

        cart = get_object_or_404(
            Cart,
            cart_id=request.session.session_key
        )

        cart_item = get_object_or_404(
            CartItem,
            id=cart_item_id,
            cart=cart
        )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('carts:cart')

def delete_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect('carts:cart')

@login_required(login_url='accounts:login')
def checkout(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    cart_items = []

    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user,is_active=True)
        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/checkout.html', context)
