from .models import Cart, CartItem

def counter(request):
    from .utils import _cart_id

    cart_count = 0

    if 'admin' in request.path:
        return {}

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    else:
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    cart_count = sum(item.quantity for item in cart_items)

    return {'cart_count': cart_count}
