"""
Defines the views for the cart application.

This module contains the views responsible for handling user interactions
with the shopping cart, such as adding items, removing items, and potentially
viewing the cart contents (though a dedicated cart view page might be
elsewhere). It supports both authenticated users (database-backed carts) and
guest users (session-backed carts), and handles both standard HTTP requests
and AJAX requests.
"""

from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product
from .context_processors import cart_context
from .constants import GUEST_CART_SESSION_ID


class AddToCartView(View):
    """
    Handles adding a product to the user's shopping cart.

    Supports both authenticated users (cart stored in the database) and
    guest users (cart stored in the session). It handles both standard
    POST requests (redirecting back) and AJAX POST requests (returning JSON).
    Validates quantity and checks against available stock before adding.
    """

    def post(self, request, *args, **kwargs):
        """
        Process the POST request to add a specified product to the cart.

        Retrieves product details, validates the requested quantity against
        available stock, and calls the appropriate method to add the item
        either to the database cart (authenticated users) or the session cart
        (guest users). Returns a JSON response for AJAX requests or redirects
        for standard requests.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments, expected to contain
        'product_id'.
        :return: A JsonResponse if the request is AJAX, otherwise an
        HttpResponseRedirect.
        :rtype: django.http.JsonResponse | django.http.HttpResponseRedirect
        """

        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            quantity_to_add = int(request.POST.get('quantity', 1))
            if quantity_to_add <= 0:
                messages.error(request, "Quantity must be a positive number.")
                if is_ajax:
                    messages_html = render_to_string('partials/messages.html',
                                                     {}, request=request)
                    return JsonResponse(
                        {'status': 'error', 'messages_html': messages_html})
                else:
                    return redirect(
                        request.META.get('HTTP_REFERER', 'product_list'))
        except (ValueError, TypeError):
            quantity_to_add = 1

        if product.stock_quantity == 0:
            message = f"Sorry, {product.name} is out of stock."
            messages.error(request, message)
            if is_ajax:
                messages_html = render_to_string('partials/messages.html', {},
                                                 request=request)
                return JsonResponse(
                    {'status': 'error', 'messages_html': messages_html})
            else:
                return redirect(
                    request.META.get('HTTP_REFERER', 'product_list'))

        if quantity_to_add > product.stock_quantity:
            message = (
                f"Cannot add {quantity_to_add} x {product.name}. "
                f"Only {product.stock_quantity} available."
            )
            messages.error(request, message)
            if is_ajax:
                messages_html = render_to_string('partials/messages.html', {},
                                                 request=request)
                return JsonResponse(
                    {'status': 'error', 'messages_html': messages_html})
            else:
                return redirect(
                    request.META.get('HTTP_REFERER', 'product_list'))

        success = False
        if request.user.is_authenticated:
            success = self._add_to_db_cart(request, product, quantity_to_add)
        else:
            success = self._add_to_session_cart(request, product,
                                                quantity_to_add)

        if is_ajax:
            if success:
                context = cart_context(request)
                cart_sidebar_html = render_to_string(
                    'cart/partials/cart_sidebar.html', context,
                    request=request)
                messages_html = render_to_string('partials/messages.html', {},
                                                 request=request)
                return JsonResponse({'status': 'success',
                                     'cart_sidebar_html': cart_sidebar_html,
                                     'messages_html': messages_html})
            else:
                messages_html = render_to_string('partials/messages.html', {},
                                                 request=request)
                return JsonResponse(
                    {'status': 'error', 'messages_html': messages_html})
        else:
            # fallback if javascript doesn't load
            redirect_url = request.META.get('HTTP_REFERER', 'product_list')
            return redirect(redirect_url)

    def _add_to_db_cart(self, request, product, quantity_to_add):
        """
        Adds or updates a product quantity in the database cart for an
        authenticated user.

        Retrieves or creates the user's cart and the specific cart item.
        Checks if adding the requested quantity exceeds the product's
        available stock, considering items already in the cart. Updates the
        quantity if valid, otherwise adds an error message.

        :param request: The HttpRequest object, used for adding messages.
        :type request: django.http.HttpRequest
        :param product: The Product instance to add.
        :type product: products.models.Product
        :param quantity_to_add: The quantity of the product to add.
        :type quantity_to_add: int
        :return: True if the item was successfully added or updated, False
        otherwise.
        :rtype: bool
        """

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 0}
        )

        current_quantity_in_cart = cart_item.quantity
        requested_total_quantity = current_quantity_in_cart + quantity_to_add
        available_stock = product.stock_quantity

        if requested_total_quantity > available_stock:
            can_add = available_stock - current_quantity_in_cart
            if can_add > 0:
                message = (
                    f"Cannot add {quantity_to_add}. Only {can_add} more "
                    f"{product.name} available (Total stock: "
                    f"{available_stock}). You already have "
                    f"{current_quantity_in_cart} in your cart."
                )
            elif current_quantity_in_cart >= available_stock:
                message = (
                    f"Cannot add more {product.name}. You already "
                    f"have the maximum available ({current_quantity_in_cart})"
                    f" in your cart."
                )
            else:
                message = (
                    f"Not enough stock for {product.name}. "
                    f"Only {available_stock} available in total."
                )

            messages.error(request, message)
            return False

        cart_item.quantity += quantity_to_add
        cart_item.save()

        if created or quantity_to_add > 0:
            message = f'Added {quantity_to_add} x {product.name} to your cart.'
            messages.success(request, message)
        elif not created and quantity_to_add > 0:
            message = f'Updated quantity for {product.name} in your cart.'
            messages.success(request, message)
        return True

    def _add_to_session_cart(self, request, product, quantity_to_add):
        """
        Adds or updates a product quantity in the session cart for
        a guest user.

        Retrieves the guest cart from the session. Checks if adding the
        requested quantity exceeds the product's available stock, considering
        items already in the session cart. Updates the quantity if valid,
        otherwise adds an error message.

        :param request: The HttpRequest object, used for accessing session and
        adding messages.
        :type request: django.http.HttpRequest
        :param product: The Product instance to add.
        :type product: products.models.Product
        :param quantity_to_add: The quantity of the product to add.
        :type quantity_to_add: int
        :return: True if the item was successfully added or updated, False
        otherwise.
        :rtype: bool
        """

        guest_cart = request.session.setdefault(GUEST_CART_SESSION_ID, {})
        product_id_str = str(product.id)
        current_quantity_in_cart = guest_cart.get(product_id_str, {}).get(
            'quantity', 0)
        requested_total_quantity = current_quantity_in_cart + quantity_to_add
        available_stock = product.stock_quantity

        if requested_total_quantity > available_stock:
            can_add = available_stock - current_quantity_in_cart
            if can_add > 0:
                message = (
                    f"Cannot add {quantity_to_add}. Only {can_add} more "
                    f"{product.name} available (Total stock: "
                    f"{available_stock}). You already have "
                    f"{current_quantity_in_cart} in your cart."
                )
            elif current_quantity_in_cart >= available_stock:
                message = (
                    f"Cannot add more {product.name}. You already have the "
                    f"maximum available ({current_quantity_in_cart}) "
                    f"in your cart."
                )
            else:
                message = (
                    f"Not enough stock for {product.name}. "
                    f"Only {available_stock} available in total."
                )

            messages.error(request, message)
            return False

        if product_id_str in guest_cart:
            guest_cart[product_id_str]['quantity'] += quantity_to_add
            message = f'Updated quantity for {product.name} in your cart.'
            messages.success(request, message)
        else:
            guest_cart[product_id_str] = {'quantity': quantity_to_add}
            message = f'Added {quantity_to_add} x {product.name} to your cart.'
            messages.success(request, message)

        request.session.modified = True
        return True


class RemoveFromCartView(View):
    """
    Handles removing a product from the user's shopping cart.

    Supports both authenticated users (database cart) and guest users
    (session cart). Handles both standard POST requests (redirecting back)
    and AJAX POST requests (returning JSON with updated cart state).
    """

    def post(self, request, *args, **kwargs):
        """
        Process the POST request to remove a specified product from the cart.

        Determines if the user is authenticated or guest and calls the
        appropriate removal method. Adds a success message if removal is
        successful.
        Returns a JSON response for AJAX requests or redirects
        for standard requests.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments, expected to
        contain 'product_id'.
        :return: A JsonResponse if the request is AJAX,
        otherwise an HttpResponseRedirect.
        :rtype: django.http.JsonResponse | django.http.HttpResponseRedirect
        """

        product_id = self.kwargs.get('product_id')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        product_name = 'Item'

        if request.user.is_authenticated:
            product_name = self._remove_from_db_cart(
                request, product_id
            ) or product_name
        else:
            product_name = self._remove_from_session_cart(
                request, product_id
            ) or product_name

        if product_name != 'Item':
            messages.success(request,
                             f'Removed {product_name} from your cart.')

        if is_ajax:
            context = cart_context(request)
            cart_sidebar_html = render_to_string(
                'cart/partials/cart_sidebar.html', context, request=request)
            messages_html = render_to_string('partials/messages.html', {},
                                             request=request)

            return JsonResponse({
                'cart_sidebar_html': cart_sidebar_html,
                'messages_html': messages_html,
            })
        else:
            # Fallback for non-AJAX call
            redirect_url = request.META.get('HTTP_REFERER', 'product_list')
            return redirect(redirect_url)

    def _remove_from_db_cart(self, request, product_id):
        """
        Removes a product from the database cart for an authenticated user.

        Finds the user's cart and the specific cart item. If found, deletes
        the item and returns its name. Handles cases where the cart or item
        doesn't exist, adding appropriate messages.

        :param request: The HttpRequest object, used for adding messages.
        :type request: django.http.HttpRequest
        :param product_id: The ID of the product to remove.
        :type product_id: int
        :return: The name of the removed product if successful, otherwise None.
        :rtype: Optional[str]
        """

        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.select_related('product').get(
                cart=cart, product_id=product_id)
            product_name = cart_item.product.name
            cart_item.delete()
            return product_name
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
            return None
        except CartItem.DoesNotExist:
            try:
                product = Product.objects.get(id=product_id)
                messages.warning(request,
                                 f'{product.name} was not found in your cart.')
            except Product.DoesNotExist:
                messages.warning(request, 'Item was not found in your cart.')
            return None

    def _remove_from_session_cart(self, request, product_id):
        """
        Removes a product from the session cart for a guest user.

        Retrieves the guest cart from the session. If the product is found,
        removes it from the session dictionary and returns the product name.
        Handles cases where the item isn't in the session cart.

        :param request: The HttpRequest object, used for accessing session
        and adding messages.
        :type request: django.http.HttpRequest
        :param product_id: The ID of the product to remove.
        :type product_id: int
        :return: The name of the removed product if successful, otherwise None.
        :rtype: Optional[str]
        """

        guest_cart = request.session.get(GUEST_CART_SESSION_ID, {})
        product_id_str = str(product_id)
        product_name_for_message = None

        try:
            product = Product.objects.get(id=product_id)
            product_name_for_message = product.name
        except Product.DoesNotExist:
            product_name_for_message = 'Item'

        if product_id_str in guest_cart:
            del guest_cart[product_id_str]
            request.session.modified = True
            return product_name_for_message
        else:
            message = f'{product_name_for_message} was not found in your cart.'
            messages.warning(request, message)
            return None
