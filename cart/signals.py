from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from .models import Cart, CartItem
from products.models import Product
from .views import GUEST_CART_SESSION_ID


@receiver(user_logged_in)
def merge_session_cart_into_db_cart(sender, request, user, **kwargs):
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
