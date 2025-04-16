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
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                messages.error(request, "Quantity must be a positive number.")
                if not is_ajax:
                    return redirect(request.META.get('HTTP_REFERER', 'product_list'))
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1

        if request.user.is_authenticated:
            self._add_to_db_cart(request, product, quantity)
        else:
            self._add_to_session_cart(request, product, quantity)

        if is_ajax:
            context = cart_context(request)
            cart_sidebar_html = render_to_string('cart/partials/cart_sidebar.html', context, request=request)
            messages_html = render_to_string('partials/messages.html', {}, request=request)

            return JsonResponse({
                'cart_sidebar_html': cart_sidebar_html,
                'messages_html': messages_html,
            })
        else:
            # fallback if javascript doesn't load
            redirect_url = request.META.get('HTTP_REFERER', 'product_list')
            return redirect(redirect_url)

    def _add_to_db_cart(self, request, product, quantity):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, f'Updated quantity for {product.name} in your cart.')
        else:
            messages.success(request, f'Added {quantity} x {product.name} to your cart.')

    def _add_to_session_cart(self, request, product, quantity):
        guest_cart = request.session.setdefault(GUEST_CART_SESSION_ID, {})
        product_id_str = str(product.id)

        if product_id_str in guest_cart:
            guest_cart[product_id_str]['quantity'] += quantity
            messages.success(request, f'Updated quantity for {product.name} in your cart.')
        else:
            guest_cart[product_id_str] = {'quantity': quantity}
            messages.success(request, f'Added {quantity} x {product.name} to your cart.')

        request.session.modified = True


class RemoveFromCartView(View):
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if request.user.is_authenticated:
            self._remove_from_db_cart(request, product_id, product.name)
        else:
            self._remove_from_session_cart(request, product_id, product.name)

        if is_ajax:
            context = cart_context(request)
            cart_sidebar_html = render_to_string('cart/partials/cart_sidebar.html', context, request=request)
            messages_html = render_to_string('partials/messages.html', {}, request=request)

            return JsonResponse({
                'cart_sidebar_html': cart_sidebar_html,
                'messages_html': messages_html,
            })
        else:
            # Fallback for non-AJAX call
            redirect_url = request.META.get('HTTP_REFERER', 'product_list')
            return redirect(redirect_url)

    def _remove_from_db_cart(self, request, product_id, product_name):
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            messages.success(request, f'Removed {product_name} from your cart.')
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
        except CartItem.DoesNotExist:
            messages.warning(request, f'{product_name} was not found in your cart.')

    def _remove_from_session_cart(self, request, product_id, product_name):
        guest_cart = request.session.get(GUEST_CART_SESSION_ID, {})
        product_id_str = str(product_id)

        if product_id_str in guest_cart:
            del guest_cart[product_id_str]
            request.session.modified = True
            messages.success(request, f'Removed {product_name} from your cart.')
        else:
            messages.warning(request, f'{product_name} was not found in your cart.')
