from .models import Cart, CartItem
from decimal import Decimal


def cart_context(request):
    cart = None
    cart_items = []
    cart_total = Decimal('0.00')
    cart_item_count = 0

    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            if cart_id := request.session.get('cart_id'):
                cart = Cart.objects.filter(id=cart_id, user=None).first()

        if cart:
            cart_items = cart.items.all().select_related('product')
            for item in cart_items:
                cart_total += item.total_price()
                cart_item_count += item.quantity

    except Cart.DoesNotExist:
        pass

    return {
        'current_cart': cart,
        'current_cart_items': cart_items,
        'current_cart_total': cart_total,
        'current_cart_item_count': cart_item_count,
    }
