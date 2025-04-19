from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views import View
from django.contrib import messages
from dataclasses import dataclass
from django.db import transaction
from django.conf import settings
from cart.models import Cart, CartItem
from cart.context_processors import cart_context
from cart.constants import GUEST_CART_SESSION_ID
from products.models import Product
from .models import Order, OrderItem, ShippingAddress, DeliveryMethod, OrderStatus
from .forms import ShippingAddressForm, DeliveryMethodForm, OrderItemFormSet
from decimal import Decimal
import stripe


@dataclass
class StatusDisplayData:
    page_title: str
    heading: str
    message_template: str
    message_level: int
    icon_class: str
    status_message_css_class: str
    show_order_details: bool
    show_retry_button: bool = False


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
                            messages.error(request, f"Product with ID '{product_id}' not found. Your order could not be placed.")
                            raise ValueError(f"Product not found: {product_id}")

                        if product.stock_quantity < quantity:
                            form.add_error('quantity', f"Only {product.stock_quantity} left in stock for {product.name}.")
                            messages.error(request, f"Not enough stock for {product.name}. Please adjust quantity.")
                            raise ValueError(f"Insufficient stock for {product.name}")

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            price=product.price,
                            quantity=quantity,
                        )
                        final_order_subtotal += (product.price * Decimal(quantity))
                        products_to_update[product] = quantity

                    for product, quantity_ordered in products_to_update.items():
                        product.stock_quantity -= quantity_ordered
                        product.save(update_fields=['stock_quantity'])

                    order.order_total = final_order_subtotal + delivery_method.price
                    order.save(update_fields=['order_total'])

                    messages.info(request, "Your order details are saved. Please proceed with payment.")
                    return redirect(reverse('payment_page', kwargs={'order_number': order.order_number}))

            except ValueError as e:
                pass
            except Exception as e:
                messages.error(request, "An unexpected error occurred while creating your order. Please try again or contact support.")

        else:
            messages.error(request, "Please correct the errors highlighted below.")

        cart_data = cart_context(request)
        current_cart_total = cart_data.get('current_cart_total', Decimal('0.00'))
        current_cart_item_count = cart_data.get('current_cart_item_count', 0)
        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in delivery_methods}

        product_ids = []
        for form in order_item_formset.forms:
            pid_str = form.data.get(f'{form.prefix}-product_id', form.initial.get('product_id'))
            pid = None
            if pid_str:
                try:
                    pid = int(pid_str)
                    product_ids.append(pid)
                except (ValueError, TypeError):
                    pass # Ignore if ID is invalid

        products = Product.objects.in_bulk(list(set(product_ids)))

        for form in order_item_formset.forms:
            pid_str = form.data.get(f'{form.prefix}-product_id', form.initial.get('product_id'))
            pid = None
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


class PaymentView(View):
    template_name = 'orders/payment.html'

    def get(self, request, order_number, *args, **kwargs):
        if not settings.STRIPE_PUBLIC_KEY:
            messages.error(request, "Stripe public key is not configured.")
            return redirect(reverse('product_list'))

        order = get_object_or_404(Order, order_number=order_number)

        if order.user is not None and order.user != request.user:
            messages.error(request, "You do not have permission to view this payment page.")
            return redirect(reverse('product_list'))

        if order.status != OrderStatus.PENDING:
            messages.warning(request, f"This order ({order_number}) cannot be paid for again. Status: {order.get_status_display()}")

            if order.status == OrderStatus.PROCESSING or order.status == OrderStatus.SHIPPED or order.status == OrderStatus.DELIVERED:
                return redirect(reverse('order_confirmation', kwargs={'order_number': order.order_number}))
            else:
                return redirect(reverse('product_list'))

        if order.order_total is None or order.order_total <= 0:
            messages.error(request, "Invalid order total. Cannot proceed with payment.")
            return redirect(reverse('checkout'))

        stripe_total = int(order.order_total * 100)

        try:
            intent = stripe.PaymentIntent.create(
                amount=stripe_total,
                currency='eur',
                metadata={
                    'order_number': order.order_number,
                    'user_id': request.user.id if request.user.is_authenticated else None,
                }
            )
        except stripe.error.StripeError as e:
            messages.error(request, f"Failed to initialize payment: {e}. Please try again.")
            return redirect(reverse('checkout'))

        subtotal = Decimal('0.00')
        if order.order_total is not None and order.delivery_method and order.delivery_method.price is not None:
            subtotal = Decimal(order.order_total) - Decimal(order.delivery_method.price)
        else:
            subtotal = sum(item.lineitem_total for item in order.items.all())


        context = {
            'order': order,
            'subtotal': subtotal,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'client_secret': intent.client_secret,
        }
        return render(request, self.template_name, context)


class OrderConfirmationView(View):
    template_name = 'orders/order_confirmation.html'

    STATUS_CONFIG = {
        'succeeded': StatusDisplayData(
            page_title="Order Confirmed",
            heading="Order Confirmed!",
            icon_class="fa-check-circle text-success",
            message_template="Thank you! Your payment was successful. Your order #{order_number} is now being processed.",
            message_level=messages.SUCCESS,
            status_message_css_class="text-success",
            show_order_details=True
        ),
        'processing': StatusDisplayData(
            page_title="Payment Processing",
            heading="Payment Processing",
            icon_class="fa-spinner fa-spin text-info",
            message_template="Your payment for order #{order_number} is processing. We will update the order status shortly.",
            message_level=messages.INFO,
            status_message_css_class="text-info",
            show_order_details=True
        ),
        'requires_payment_method': StatusDisplayData(
            page_title="Payment Failed",
            heading="Payment Required",
            icon_class="fa-exclamation-triangle text-warning",
            message_template="Payment for order #{order_number} failed because a payment method is required. Please try again.",
            message_level=messages.WARNING,
            status_message_css_class="text-warning",
            show_order_details=False,
            show_retry_button=True
        ),
    }
    DEFAULT_FAILURE_CONFIG = StatusDisplayData(
        page_title="Payment Issue",
        heading="Payment Issue",
        icon_class="fa-times-circle text-danger",
        message_template="Unfortunately, the payment for order #{order_number} could not be completed. Status: {status}. Please check your details or contact us if the problem persists.",
        message_level=messages.ERROR,
        status_message_css_class="text-danger",
        show_order_details=False,
        show_retry_button=True
    )
    VIEW_ORDER_CONFIG = StatusDisplayData(
        page_title="Order Details",
        heading="Order Summary",
        icon_class="fa-file-alt",
        message_template="",
        message_level=messages.INFO,
        status_message_css_class="text-muted",
        show_order_details=True,
        show_retry_button=False
    )

    def get(self, request, order_number, *args, **kwargs):
        order = get_object_or_404(Order, order_number=order_number)
        subtotal = Decimal('0.00')

        if order.user is not None and order.user != request.user:
            messages.error(request, "Permission Denied.")
            return redirect(reverse('product_list'))

        if order.order_total is not None and order.delivery_method and order.delivery_method.price is not None:
            subtotal = Decimal(order.order_total) - Decimal(order.delivery_method.price)

        payment_intent_secret = request.GET.get('payment_intent_client_secret')
        redirect_status = request.GET.get('redirect_status')
        payment_just_processed = bool(payment_intent_secret and redirect_status)

        status_data = None
        on_page_message_text = None

        if payment_just_processed:
            status_data = self.STATUS_CONFIG.get(redirect_status, self.DEFAULT_FAILURE_CONFIG)

            if status_data.message_template:
                on_page_message_text = status_data.message_template.format(
                    order_number=order.order_number,
                    status=redirect_status
                )
                messages.add_message(request, status_data.message_level, on_page_message_text)

            if redirect_status == 'succeeded':
                if order.cart:
                    CartItem.objects.filter(cart=order.cart).delete()
                elif not order.user and GUEST_CART_SESSION_ID in request.session:
                    del request.session[GUEST_CART_SESSION_ID]
                    request.session.modified = True
        else:
            if order.status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                status_data = self.VIEW_ORDER_CONFIG
                status_data.show_order_details = True
            elif order.status == OrderStatus.FAILED or order.status == OrderStatus.CANCELLED:
                status_data = self.DEFAULT_FAILURE_CONFIG
                status_data.message_template = ''
                status_data.show_order_details = False
            else:
                status_data = self.VIEW_ORDER_CONFIG
                status_data.show_order_details = True

        if not status_data:
            status_data = self.VIEW_ORDER_CONFIG

        if not status_data.show_order_details:
            subtotal = Decimal('0.00')

        context = {
            'order': order,
            'subtotal': subtotal,
            'page_title': status_data.page_title,
            'heading': status_data.heading,
            'icon_class': status_data.icon_class,
            'show_retry_button': status_data.show_retry_button,
            'payment_just_processed': payment_just_processed,
            'on_page_message_text': on_page_message_text,
            'status_message_css_class': status_data.status_message_css_class,
            'show_order_details': status_data.show_order_details,
        }

        return render(request, self.template_name, context)
