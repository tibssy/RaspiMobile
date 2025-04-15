from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from cart.context_processors import cart_context
from cart.constants import GUEST_CART_SESSION_ID
from cart.models import CartItem
from products.models import Product
from .models import Order, OrderItem, ShippingAddress, DeliveryMethod, OrderStatus
from .forms import ShippingAddressForm, DeliveryMethodForm, OrderItemFormSet
from decimal import Decimal


class CreateOrderView(View):
    template_name = 'orders/checkout.html'

    def get(self, request, *args, **kwargs):
        cart_data = cart_context(request)
        current_cart_items = cart_data['current_cart_items']

        if not current_cart_items:
            messages.warning(request, "Your cart is empty. Please add items to proceed.")
            return redirect(reverse('product_list'))

        initial_formset_data = []
        for item in current_cart_items:
            product_id = None
            quantity = 0
            product_obj = item.product if isinstance(item, CartItem) else item.get('product')
            if product_obj:
                 product_id = product_obj.id
                 quantity = item.quantity if isinstance(item, CartItem) else item.get('quantity', 1)
                 initial_formset_data.append({'product_id': product_id, 'quantity': quantity})

        shipping_form = ShippingAddressForm(prefix='shipping')
        delivery_form = DeliveryMethodForm(prefix='delivery')
        order_item_formset = OrderItemFormSet(initial=initial_formset_data, prefix='items')
        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in delivery_methods}

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_items': current_cart_items,
            'current_cart_total': cart_data['current_cart_total'],
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        shipping_form = ShippingAddressForm(request.POST, prefix='shipping')
        delivery_form = DeliveryMethodForm(request.POST, prefix='delivery')
        order_item_formset = OrderItemFormSet(request.POST, prefix='items')

        if shipping_form.is_valid() and delivery_form.is_valid() and order_item_formset.is_valid():
            try:
                with transaction.atomic():
                    shipping_address = shipping_form.save()
                    delivery_method = delivery_form.cleaned_data['delivery_method']
                    order = Order.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        shipping_address=shipping_address,
                        delivery_method=delivery_method,
                    )

                    final_order_subtotal = Decimal('0.00')
                    products_to_update = {}

                    for form in order_item_formset:
                        cleaned_data = form.cleaned_data
                        product_id = cleaned_data.get('product_id')
                        quantity = cleaned_data.get('quantity')

                        try:
                            product = Product.objects.get(id=product_id)
                        except Product.DoesNotExist:
                            messages.error(request, f"Product with ID {product_id} not found. Please review your order.")
                            raise ValueError("Product not found")

                        if product.stock_quantity < quantity:
                            messages.error(request, f"Not enough stock for {product.name} ({product.stock_quantity} left). Please adjust quantity.")
                            raise ValueError(f"Insufficient stock for {product.name}")

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            price=product.price,
                            quantity=quantity,
                        )
                        final_order_subtotal += (product.price * quantity)
                        products_to_update[product] = quantity

                    for product, quantity_ordered in products_to_update.items():
                        product.stock_quantity -= quantity_ordered
                        product.save()

                    order.order_total = final_order_subtotal + delivery_method.price
                    order.status = OrderStatus.PENDING
                    order.save()

                    if request.user.is_authenticated:
                        CartItem.objects.filter(cart__user=request.user).delete()
                    else:
                        if GUEST_CART_SESSION_ID in request.session:
                            del request.session[GUEST_CART_SESSION_ID]
                            request.session.modified = True

                    messages.success(request, f"Thank you! Your order #{order.order_number} has been placed successfully.")
                    return redirect(reverse('product_list'))

            except ValueError as e:
                pass
            except Exception as e:
                print(f"ERROR Placing Order: {e}")
                messages.error(request, "An unexpected error occurred. Please try again.")

        else:
            messages.error(request, "Please correct the errors below.")

        cart_data = cart_context(request)
        current_cart_items = cart_data['current_cart_items']
        current_cart_total = cart_data['current_cart_total']
        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in delivery_methods}

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_items': current_cart_items,
            'current_cart_total': current_cart_total,
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)
