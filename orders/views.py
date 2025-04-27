"""
Defines the views for the orders application.

This module handles the customer-facing order process, including the checkout
form, payment integration with Stripe, order confirmation display, and
potentially viewing past order details
(though full history might be in profiles).
"""
from django.contrib.messages import success
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
from .models import Order, OrderItem, DeliveryMethod, OrderStatus
from .forms import DeliveryMethodForm, OrderItemFormSet
from profiles.forms import ShippingAddressForm
from profiles.models import ShippingAddress as ProfileShippingAddress
from decimal import Decimal
import stripe


@dataclass
class StatusDisplayData:
    """
    A data class to hold configuration for displaying order status information
    on the confirmation page. Simplifies passing status-specific details to
    the template.

    :param page_title: The title to display in the browser tab/window.
    :param heading: The main heading to display on the page.
    :param message_template: A format string for the main status message.
                             Placeholders like {order_number} and {status}
                             will be filled.
    :param message_level: The Django messages level (e.g., messages.SUCCESS).
    :param icon_class: CSS class(es) for the status icon (e.g., Font Awesome).
    :param status_message_css_class: CSS class for styling the status
                                     message text.
    :param show_order_details: Boolean indicating whether to show the
                               full order summary.
    :param show_retry_button: Boolean indicating whether to show a
                              'Retry Payment' button.
    """

    page_title: str
    heading: str
    message_template: str
    message_level: int
    icon_class: str
    status_message_css_class: str
    show_order_details: bool
    show_retry_button: bool = False


class CreateOrderView(View):
    """
    Handles the checkout process, displaying forms for shipping address,
    delivery method, and order items (derived from the cart). Processes the
    submitted data to create an Order and OrderItem records.
    """

    template_name = 'orders/checkout.html'

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests for the checkout page.

        Retrieves cart contents, initializes shipping, delivery, and item
        forms. Pre-populates shipping form if user is authenticated and
        has a saved address. Populates the context with necessary data for
        rendering the checkout template.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse rendering the checkout template.
        :rtype: django.http.HttpResponse
        """

        cart_data = cart_context(request)
        current_cart_items = cart_data.get('current_cart_items', [])

        if not current_cart_items:
            messages.warning(
                request,
                "Your cart is empty. Please add items to proceed."
            )
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
                initial_formset_data.append(
                    {'product_id': product_id, 'quantity': quantity}
                )
                product_ids.append(product_id)

        products_in_cart = Product.objects.in_bulk(list(set(product_ids)))
        initial_shipping_data = None

        if request.user.is_authenticated:
            try:
                latest_profile_address = ProfileShippingAddress.objects.filter(
                    user=request.user
                ).latest('id')
                initial_shipping_data = {
                    field.name: getattr(latest_profile_address, field.name)
                    for field in latest_profile_address._meta.fields
                    if field.name != 'id' and field.name != 'user'
                }
            except ProfileShippingAddress.DoesNotExist:
                pass

        shipping_form = ShippingAddressForm(
            prefix='shipping',
            initial=initial_shipping_data
        )
        delivery_form = DeliveryMethodForm(
            prefix='delivery'
        )
        order_item_formset = OrderItemFormSet(
            initial=initial_formset_data,
            prefix='items'
        )

        for form in order_item_formset.forms:
            product_id = form.initial.get('product_id')
            if product_id:
                product = products_in_cart.get(product_id)
                form.product = product
                form.fields['quantity'].widget.attrs[
                    'max'] = product.stock_quantity
            else:
                form.product = None
                form.fields['quantity'].widget.attrs['max'] = 0
                form.fields['quantity'].widget.attrs['disabled'] = True

        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in
                               delivery_methods}

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_total': cart_data.get(
                'current_cart_total',
                Decimal('0.00')
            ),
            'current_cart_item_count': cart_data.get(
                'current_cart_item_count',
                0
            ),
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for submitting the checkout form.

        Validates shipping, delivery, and item forms. If valid, creates
        an Order and associated OrderItems within a transaction, updates
        product stock, saves the shipping address to the profile if requested,
        and redirects to the payment page. If invalid, re-renders the checkout
        page with errors.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse (redirect or re-render).
        :rtype: django.http.HttpResponse
        """

        shipping_form = ShippingAddressForm(
            request.POST,
            prefix='shipping'
        )
        delivery_form = DeliveryMethodForm(
            request.POST,
            prefix='delivery'
        )
        order_item_formset = OrderItemFormSet(
            request.POST,
            prefix='items'
        )

        users_cart = None
        if request.user.is_authenticated:
            try:
                users_cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                pass
            except Cart.MultipleObjectsReturned:
                users_cart = Cart.objects.filter(user=request.user).latest(
                    'updated_on')

        is_valid_shipping = shipping_form.is_valid()
        is_valid_delivery = delivery_form.is_valid()
        is_valid_item = order_item_formset.is_valid()

        if is_valid_shipping and is_valid_delivery and is_valid_item:
            try:
                with transaction.atomic():
                    address_data = shipping_form.cleaned_data
                    delivery_method = delivery_form.cleaned_data[
                        'delivery_method'
                    ]

                    if request.user.is_authenticated and request.POST.get(
                            'save_address_profile'):
                        try:
                            profile_address, created = (
                                ProfileShippingAddress.objects
                                .update_or_create(
                                    user=request.user,
                                    defaults=address_data
                                )
                            )
                            if created:
                                message = (
                                    "Shipping address saved to your profile."
                                )
                                messages.info(request, message)
                            else:
                                message = (
                                    "Your profile shipping address "
                                    "has been updated."
                                )
                                messages.info(request, message)
                        except Exception as e:
                            message = (
                                "There was an issue saving the address to "
                                "your profile, but your order is proceeding."
                            )
                            messages.warning(request, message)

                    order_data = {
                        'shipping_full_name': address_data['full_name'],
                        'shipping_email': address_data['email'],
                        'shipping_phone_number': address_data.get(
                            'phone_number',
                            ''
                        ),
                        'shipping_address1': address_data['address1'],
                        'shipping_address2': address_data.get('address2', ''),
                        'shipping_city': address_data['city'],
                        'shipping_state': address_data.get('state', ''),
                        'shipping_zipcode': address_data['zipcode'],
                        'shipping_country': address_data['country'],
                        'delivery_method': delivery_method,
                        'status': OrderStatus.PENDING,
                        'user': (
                            request.user if request.user.is_authenticated
                            else None
                        ),
                        'cart': users_cart
                    }

                    order = Order.objects.create(**order_data)
                    final_ord_total = Decimal('0.00')
                    products_to_update = {}

                    for form in order_item_formset:
                        cleaned_data = form.cleaned_data
                        product_id = cleaned_data.get('product_id')
                        quantity = cleaned_data.get('quantity')

                        if not product_id or not quantity:
                            message = (
                                "Invalid item data detected. Please review "
                                "your cart and try again."
                            )
                            messages.error(request, message)
                            raise ValueError("Invalid item data in formset.")

                        try:
                            product = Product.objects.select_for_update().get(
                                id=product_id)
                        except Product.DoesNotExist:
                            message = (
                                f"Sorry, a product in your order "
                                f"(ID: {product_id}) is no longer available. "
                                f"Please remove it and try again."
                            )
                            messages.error(request, message)
                            raise ValueError(
                                f"Product not found: {product_id}"
                            )

                        if product.stock_quantity < quantity:
                            msg = (
                                f"Insufficient stock for {product.name}. "
                                f"Only {product.stock_quantity} available."
                            )
                            form.add_error('quantity', msg)
                            message = (
                                f"Not enough stock for {product.name}. "
                                f"Please adjust the quantity."
                            )
                            messages.error(request, message)
                            raise ValueError(
                                f"Insufficient stock for {product.name}"
                            )

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            price=product.price,
                            quantity=quantity,
                        )
                        final_ord_total += (product.price * Decimal(quantity))
                        products_to_update[product] = quantity

                    for product, ord_quantity in products_to_update.items():
                        product.stock_quantity -= ord_quantity
                        product.save(update_fields=['stock_quantity'])

                    order.order_total = final_ord_total + delivery_method.price
                    order.save(update_fields=['order_total'])
                    messages.info(
                        request,
                        "Order details saved successfully!"
                    )
                    return redirect(
                        reverse(
                            'payment_page',
                            kwargs={'order_number': order.order_number}
                        )
                    )

            except ValueError as e:
                pass
            except Exception as e:
                message = (
                    "An unexpected error occurred while creating "
                    "your order. Please try again or contact support "
                    "if the problem persists."
                )
                messages.error(request, message)

        else:
            messages.error(
                request,
                "Please correct the errors highlighted below."
            )

        cart_data = cart_context(request)
        delivery_methods = DeliveryMethod.objects.filter(is_active=True)
        delivery_costs_dict = {str(method.id): method.price for method in
                               delivery_methods}

        product_ids_from_post = []
        if order_item_formset.is_bound:
            for i in range(order_item_formset.total_form_count()):
                key = f'{order_item_formset.prefix}-{i}-product_id'
                pid_str = request.POST.get(key)
                if pid_str:
                    try:
                        product_ids_from_post.append(int(pid_str))
                    except (ValueError, TypeError):
                        pass

        products_for_formset = Product.objects.in_bulk(
            list(set(product_ids_from_post))
        )

        for form in order_item_formset.forms:
            pid_str = form.data.get(f'{form.prefix}-product_id')
            pid = None
            if pid_str:
                try:
                    pid = int(pid_str)
                except (ValueError, TypeError):
                    pass

            if pid:
                form.product = products_for_formset.get(pid)
            else:
                form.product = None

        context = {
            'shipping_form': shipping_form,
            'delivery_form': delivery_form,
            'order_item_formset': order_item_formset,
            'current_cart_total': cart_data.get(
                'current_cart_total',
                Decimal('0.00')
            ),
            'current_cart_item_count': cart_data.get(
                'current_cart_item_count',
                0
            ),
            'delivery_costs_data': delivery_costs_dict,
        }
        return render(request, self.template_name, context)


class PaymentView(View):
    """
    Handles displaying the payment page for a specific order.

    Initializes a Stripe Payment Intent, retrieves the order details,
    and renders the payment form including the Stripe Elements integration.
    Performs checks to ensure the order exists, belongs to the user
    (if authenticated), and is in a payable status (PENDING).
    """

    template_name = 'orders/payment.html'

    def get(self, request, order_number, *args, **kwargs):
        """
        Handles GET requests for the payment page.

        Fetches the order, validates permissions and order status, creates
        a Stripe Payment Intent, and renders the payment template with
        necessary context.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param order_number: The unique identifier for the order.
        :type order_number: str
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse (render or redirect).
        :rtype: django.http.HttpResponse
        """

        if not settings.STRIPE_PUBLIC_KEY:
            messages.error(request, "Stripe public key is not configured.")
            return redirect(reverse('product_list'))

        order = get_object_or_404(Order, order_number=order_number)

        if order.user is not None and order.user != request.user:
            messages.error(
                request,
                "You do not have permission to view this payment page."
            )
            return redirect(reverse('product_list'))

        if order.status != OrderStatus.PENDING:
            message = (
                f"This order ({order_number}) cannot be paid for again. "
                f"Status: {order.get_status_display()}"
            )
            messages.warning(request, message)

            is_processing = order.status == OrderStatus.PROCESSING
            is_shipped = order.status == OrderStatus.SHIPPED
            is_delivered = order.status == OrderStatus.DELIVERED

            if is_processing or is_shipped or is_delivered:
                return redirect(
                    reverse(
                        'order_confirmation',
                        kwargs={'order_number': order.order_number}
                    )
                )
            else:
                return redirect(reverse('product_list'))

        if order.order_total is None or order.order_total <= 0:
            messages.error(
                request,
                "Invalid order total. Cannot proceed with payment."
            )
            return redirect(reverse('checkout'))

        stripe_total = int(order.order_total * 100)

        try:
            u_id = request.user.id if request.user.is_authenticated else None
            intent = stripe.PaymentIntent.create(
                amount=stripe_total,
                currency='eur',
                metadata={
                    'order_number': order.order_number,
                    'user_id': u_id,
                }
            )
        except stripe.error.StripeError as e:
            messages.error(
                request,
                f"Failed to initialize payment: {e}. Please try again."
            )
            return redirect(reverse('checkout'))

        subtotal = Decimal('0.00')
        ord_total = order.order_total
        ord_delivery = order.delivery_method
        ord_price = order.delivery_method.price

        if ord_total is not None and ord_delivery and ord_price is not None:
            subtotal = Decimal(ord_total) - Decimal(ord_price)
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
    """
    Displays the order confirmation page based on the payment status.

    Handles redirects from Stripe after payment attempts. Shows success,
    processing, or failure messages and optionally the order details.
    Also allows viewing details of previously completed orders. Clears the
    user's cart on successful payment confirmation.
    """

    template_name = 'orders/order_confirmation.html'

    STATUS_CONFIG = {
        'succeeded': StatusDisplayData(
            page_title="Order Confirmed",
            heading="Order Confirmed!",
            icon_class="fa-check-circle text-success",
            message_template="Thank you! Your payment was successful. Your "
                             "order #{order_number} is now being processed.",
            message_level=messages.SUCCESS,
            status_message_css_class="text-success",
            show_order_details=True
        ),
        'processing': StatusDisplayData(
            page_title="Payment Processing",
            heading="Payment Processing",
            icon_class="fa-spinner fa-spin text-info",
            message_template="Your payment for order #{order_number} is "
                             "processing. We will update the order status "
                             "shortly.",
            message_level=messages.INFO,
            status_message_css_class="text-info",
            show_order_details=True
        ),
        'requires_payment_method': StatusDisplayData(
            page_title="Payment Failed",
            heading="Payment Required",
            icon_class="fa-exclamation-triangle text-warning",
            message_template="Payment for order #{order_number} failed "
                             "because a payment method is required. "
                             "Please try again.",
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
        message_template="Unfortunately, the payment for order "
                         "#{order_number} could not be completed. "
                         "Status: {status}. Please check your details or "
                         "contact us if the problem persists.",
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
        """
        Handles GET requests for the order confirmation page.

        Determines the display context based on whether the user just
        completed payment (indicated by query parameters from Stripe redirect)
        or is viewing an existing order. Retrieves order details, calculates
        subtotal, and renders the template using the appropriate
        status configuration.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param order_number: The unique identifier for the order.
        :type order_number: str
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse rendering the confirmation template.
        :rtype: django.http.HttpResponse
        """

        order = get_object_or_404(Order, order_number=order_number)
        subtotal = Decimal('0.00')

        if order.user is not None and order.user != request.user:
            messages.error(request, "Permission Denied.")
            return redirect(reverse('product_list'))

        ord_total = order.order_total
        ord_delivery = order.delivery_method
        ord_price = order.delivery_method.price

        if ord_total is not None and ord_delivery and ord_price is not None:
            subtotal = Decimal(ord_total) - Decimal(ord_price)

        payment_intent_secret = request.GET.get('payment_intent_client_secret')
        redirect_status = request.GET.get('redirect_status')
        payment_just_processed = bool(
            payment_intent_secret and redirect_status)

        status_data = None
        on_page_message_text = None

        if payment_just_processed:
            status_data = self.STATUS_CONFIG.get(
                redirect_status,
                self.DEFAULT_FAILURE_CONFIG
            )

            if status_data.message_template:
                on_page_message_text = status_data.message_template.format(
                    order_number=order.order_number,
                    status=redirect_status
                )
                messages.add_message(
                    request,
                    status_data.message_level,
                    on_page_message_text
                )

            if redirect_status == 'succeeded':
                guest_cart_id = GUEST_CART_SESSION_ID
                if order.cart:
                    CartItem.objects.filter(cart=order.cart).delete()
                elif not order.user and guest_cart_id in request.session:
                    del request.session[guest_cart_id]
                    request.session.modified = True
        else:
            success_statuses = {
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED
            }
            failure_statuses = {
                OrderStatus.FAILED,
                OrderStatus.CANCELLED
            }

            if order.status in success_statuses:
                status_data = self.VIEW_ORDER_CONFIG
                status_data.show_order_details = True
            elif order.status in failure_statuses:
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
