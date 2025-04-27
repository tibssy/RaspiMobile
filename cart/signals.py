"""
Signal handlers for the cart application.

This module contains functions that are executed in response to specific
Django signals, such as user login, to perform cart-related actions like
merging session carts into database carts.
"""

from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from .models import Cart, CartItem
from products.models import Product
from .views import GUEST_CART_SESSION_ID


@receiver(user_logged_in)
def merge_session_cart_into_db_cart(sender, request, user, **kwargs):
    """
    Merges items from the guest session cart into the user's database cart
    upon login.

    This function is connected to the `user_logged_in` signal. It checks if a
    guest cart exists in the session. If so, it iterates through the session
    cart items, retrieves or creates the corresponding user's database cart
    and cart items, updates quantities, and handles potential errors like
    non-existent products. The session cart is cleared after successful
    merging. Uses a database transaction to ensure atomicity.

    :param sender: The sender of the signal (typically the user model).
    :param request: The HttpRequest object containing the session.
    :type request: django.http.HttpRequest
    :param user: The user instance who just logged in.
    :type user: django.contrib.auth.models.User
    :param kwargs: Additional keyword arguments passed by the signal.
    """

    session_cart = request.session.get(GUEST_CART_SESSION_ID)

    if not session_cart:
        return

    try:
        with transaction.atomic():
            db_cart, created = Cart.objects.get_or_create(user=user)

            items_merged = 0
            items_created = 0

            for product_id_str, item_data in session_cart.items():
                try:
                    product_id = int(product_id_str)
                    quantity = int(item_data.get('quantity', 0))

                    if quantity <= 0:
                        continue

                    product = Product.objects.get(id=product_id)
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=db_cart,
                        product=product,
                        defaults={'quantity': quantity}
                    )

                    if not item_created:
                        cart_item.quantity += quantity
                        cart_item.save()
                        items_merged += 1
                    else:
                        items_created += 1

                except Product.DoesNotExist:
                    continue
                except (ValueError, TypeError) as e:
                    continue

            del request.session[GUEST_CART_SESSION_ID]
            request.session.modified = True

    except Exception as e:
        pass
