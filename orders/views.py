from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from cart.models import Cart, CartItem
from cart.context_processors import cart_context
from cart.constants import GUEST_CART_SESSION_ID
from products.models import Product
from .models import Order, OrderItem, ShippingAddress, DeliveryMethod, OrderStatus
from .forms import ShippingAddressForm, DeliveryMethodForm, OrderItemFormSet
from decimal import Decimal


class CreateOrderView(View):
    template_name = 'orders/checkout.html'

    def get(self, request, *args, **kwargs):
        cart_data = cart_context(request)
        current_cart_items = cart_data.get('current_cart_items', [])

        if not current_cart_items:
            messages.warning(request, "Your cart is empty. Please add items to proceed.")
            return redirect(reverse('product_list'))

        initial_formset_data = []
        product_ids = []
        for item in current_cart_items:
            product_obj = None
            quantity = 0
            if isinstance(item, CartItem):
                product_obj = item.product
                quantity = item.quantity
            elif isinstance(item, dict) and 'product' in item:
                 product_obj = item.get('product')
                 quantity = item.get('quantity', 1)

            if product_obj:
                 product_id = product_obj.id
                 initial_formset_data.append({'product_id': product_id, 'quantity': quantity})
                 product_ids.append(product_id)

        products_in_cart = Product.objects.in_bulk(list(set(product_ids)))

        shipping_form = ShippingAddressForm(prefix='shipping')
        delivery_form = DeliveryMethodForm(prefix='delivery')
        order_item_formset = OrderItemFormSet(initial=initial_formset_data, prefix='items')

        for form in order_item_formset.forms:
            product_id = form.initial.get('product_id')
            if product_id:
                form.product = products_in_cart.get(product_id)

        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in delivery_methods}

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_total': cart_data.get('current_cart_total', Decimal('0.00')),
            'current_cart_item_count': cart_data.get('current_cart_item_count', 0),
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        shipping_form = ShippingAddressForm(request.POST, prefix='shipping')
        delivery_form = DeliveryMethodForm(request.POST, prefix='delivery')
        order_item_formset = OrderItemFormSet(request.POST, prefix='items')

        users_cart = None
        if request.user.is_authenticated:
            try:
                users_cart = Cart.objects.filter(user=request.user).latest('updated_on')
            except Cart.DoesNotExist:
                pass
            except AttributeError:
                messages.error(request, "There is an issue with the cart configuration (missing 'updated_on'). Please contact support.")

        if shipping_form.is_valid() and delivery_form.is_valid() and order_item_formset.is_valid():
            try:
                with transaction.atomic():
                    shipping_address = shipping_form.save()
                    delivery_method = delivery_form.cleaned_data['delivery_method']

                    order_data = {
                        'shipping_address': shipping_address,
                        'delivery_method': delivery_method,
                        'status': OrderStatus.PENDING,
                    }
                    if request.user.is_authenticated:
                        order_data['user'] = request.user

                        if users_cart:
                            order_data['cart'] = users_cart

                    order = Order.objects.create(**order_data)

                    final_order_subtotal = Decimal('0.00')
                    products_to_update = {}

                    for form in order_item_formset:
                        cleaned_data = form.cleaned_data
                        product_id = cleaned_data.get('product_id')
                        quantity = cleaned_data.get('quantity')

                        if not product_id or not quantity:
                             raise ValueError("Invalid item data in formset.")

                        try:
                            product = Product.objects.select_for_update().get(id=product_id)
                        except Product.DoesNotExist:
                            messages.error(request, f"Product '{product_id}' not found. Your order could not be placed.")
                            raise ValueError(f"Product not found: {product_id}")

                        if product.stock_quantity < quantity:
                            form.add_error('quantity', f"Only {product.stock_quantity} left in stock.")
                            messages.error(request, f"Not enough stock for {product.name}. Please adjust quantity.")
                            raise ValueError(f"Insufficient stock for {product.name}")

                        OrderItem.objects.create(
                            order=order, product=product, price=product.price, quantity=quantity,
                        )
                        final_order_subtotal += (product.price * quantity)
                        products_to_update[product] = quantity

                    for product, quantity_ordered in products_to_update.items():
                        product.stock_quantity -= quantity_ordered
                        product.save(update_fields=['stock_quantity'])

                    order.order_total = final_order_subtotal + delivery_method.price
                    order.save(update_fields=['order_total'])

                    if request.user.is_authenticated:
                        if users_cart:
                            CartItem.objects.filter(cart=users_cart).delete()
                        else:
                            pass
                    else:
                        if GUEST_CART_SESSION_ID in request.session:
                            del request.session[GUEST_CART_SESSION_ID]
                            request.session.modified = True

                    messages.success(request, f"Thank you! Your order #{order.order_number} has been placed successfully.")
                    return redirect(reverse('product_list'))

            except ValueError as e:
                 pass
            except Exception as e:
                messages.error(request, "An unexpected error occurred while processing your order. Please try again.")

        else:
            messages.error(request, "Please correct the errors highlighted below.")

        cart_data = cart_context(request)
        current_cart_total = cart_data.get('current_cart_total', Decimal('0.00'))
        current_cart_item_count = cart_data.get('current_cart_item_count', 0)
        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in delivery_methods}

        product_ids = []
        for form in order_item_formset.forms:
            pid = None
            pid_str = form.data.get(f'{form.prefix}-product_id')
            if pid_str:
                try: pid = int(pid_str)
                except (ValueError, TypeError): pass
            if pid:
                product_ids.append(pid)

        products = Product.objects.in_bulk(list(set(product_ids)))

        for form in order_item_formset.forms:
            pid = None
            pid_str = form.data.get(f'{form.prefix}-product_id')
            if pid_str:
                 try: pid = int(pid_str)
                 except (ValueError, TypeError): pass

            if pid:
                form.product = products.get(pid)
            else:
                form.product = None

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_total': current_cart_total,
            'current_cart_item_count': current_cart_item_count,
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)
