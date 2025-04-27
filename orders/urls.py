"""
URL configuration for the orders application.

Defines the URL patterns that map request paths to the corresponding
order processing views, including checkout, payment, confirmation,
and the Stripe webhook endpoint.
"""

from django.urls import path
from .views import CreateOrderView, PaymentView, OrderConfirmationView
from .webhooks import StripeWebhookView

urlpatterns = [
    # URL for the main checkout page
    path(
        'checkout/',
        CreateOrderView.as_view(),
        name='checkout'
    ),
    # URL for the payment page, requires an order number
    path(
        'payment/<str:order_number>/',
        PaymentView.as_view(),
        name='payment_page'
    ),
    # URL for the order confirmation page, requires an order number
    path(
        'confirmation/<str:order_number>/',
        OrderConfirmationView.as_view(),
        name='order_confirmation'
    ),
    # URL for the Stripe webhook handler
    path(
        'stripe/webhook/',
        StripeWebhookView.as_view(),
        name='stripe_webhook'
    ),
]
