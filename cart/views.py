from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product


GUEST_CART_SESSION_ID = 'guest_cart'


class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                messages.error(request, "Quantity must be a positive number.")
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1

        if request.user.is_authenticated:
            self._add_to_db_cart(request, product, quantity)
        else:
            self._add_to_session_cart(request, product, quantity)

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
