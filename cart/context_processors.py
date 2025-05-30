"""
Context processors for the cart application.

Provides functions that add cart-related information to the template context
for every request, making cart details easily accessible in templates.
"""

from .models import Cart, CartItem
from products.models import Product
from decimal import Decimal
from .constants import GUEST_CART_SESSION_ID


def cart_context(request):
    """
    Provides cart context data to templates.

    Calculates the current cart's items, total price, and item count,
    handling both authenticated users (database cart) and guest users
    (session cart).

    For authenticated users:
    - Fetches the user's Cart object and related CartItems.
    - Calculates total price and item count from CartItems.

    For guest users:
    - Retrieves cart data from the session.
    - Fetches Product details for items in the session cart.
    - Constructs a list of temporary item dictionaries mimicking
    CartItem structure.
    - Calculates total price and item count from session data.

    :param request: The HttpRequest object, used to access user and session.
    :type request: django.http.HttpRequest
    :return: A dictionary containing cart context variables:
             'current_cart': The Cart object (or None for guests).
             'current_cart_items': A list of CartItem objects (auth) or
             dicts (guest).
             'current_cart_total': The total price of items in the cart
             (Decimal).
             'current_cart_item_count': The total number of individual items
             in the cart (int).
    :rtype: dict
    """

    cart = None
    cart_items = []
    cart_total = Decimal('0.00')
    cart_item_count = 0

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.prefetch_related('items__product').get(
                user=request.user)
            db_cart_items = cart.items.all()
            for item in db_cart_items:
                cart_items.append(item)
                cart_total += item.total_price()
                cart_item_count += item.quantity

        except Cart.DoesNotExist:
            pass
    else:
        raw_cart_data = request.session.get(GUEST_CART_SESSION_ID, {})
        if raw_cart_data:
            product_ids = [int(pid) for pid in raw_cart_data.keys()]
            products = Product.objects.filter(id__in=product_ids)
            products_dict = {p.id: p for p in products}

            temp_cart_items = []
            for product_id_str, item_data in raw_cart_data.items():
                product_id = int(product_id_str)
                product = products_dict.get(product_id)
                quantity = item_data.get('quantity', 0)

                if product and quantity > 0:
                    item_total = product.price * quantity
                    cart_total += item_total
                    cart_item_count += quantity

                    temp_item = {
                        'product': product,
                        'quantity': quantity,
                        'total_price': item_total,
                        'id': product_id
                    }
                    temp_cart_items.append(temp_item)

            cart_items = temp_cart_items

    return {
        'current_cart': cart,
        'current_cart_items': cart_items,
        'current_cart_total': cart_total,
        'current_cart_item_count': cart_item_count,
    }
