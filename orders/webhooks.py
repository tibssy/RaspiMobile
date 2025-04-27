"""
Defines webhook handlers for receiving events from external services,
primarily Stripe.

This module contains views that listen for incoming webhook notifications,
verify their authenticity, and trigger corresponding actions within the
application, such as updating order statuses based on payment events.
"""

from django.views import View
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from cart.models import Cart, CartItem
from .models import Order, OrderStatus
import stripe
from .emails import send_confirmation_email

stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Handles incoming webhooks from Stripe.

    Verifies the webhook signature and routes the event payload to the
    appropriate handler based on the event type
    (e.g., 'payment_intent.succeeded').
    Requires CSRF exemption as Stripe cannot send a CSRF token.
    """

    def post(self, request, *args, **kwargs):
        """
        Processes POST requests containing Stripe webhook events.

        Reads the request body, verifies the Stripe signature using the
        webhook secret, parses the event, and calls the relevant handler
        method based on the event type.

        :param request: The HttpRequest object containing the webhook
                        payload and signature.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse indicating success (200 OK) or failure
                 (400 Bad Request, 500 Server Error).
        :rtype: django.http.HttpResponse
        """

        wh_secret = settings.STRIPE_WEBHOOK_SECRET
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, wh_secret
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)
        except Exception as e:
            # Generic error during signature verification
            return HttpResponse(status=400)

        handler_map = {
            'payment_intent.succeeded': self.handle_payment_intent_succeeded,
            'payment_intent.payment_failed': self.handle_payment_intent_failed,
        }

        event_type = event['type']
        handler = handler_map.get(event_type, self.handle_unknown_event)

        try:
            response = handler(event)
            return response
        except Exception as e:
            return HttpResponse(status=500)

    def handle_payment_intent_succeeded(self, event):
        """
        Handles the 'payment_intent.succeeded' event from Stripe.

        Retrieves the order based on metadata in the PaymentIntent, updates
        the order status to 'PROCESSING' if it was 'PENDING', and triggers
        the sending of a confirmation email.

        :param event: The Stripe event object.
        :type event: stripe.Event
        :return: An HttpResponse indicating success (200 OK).
        :rtype: django.http.HttpResponse
        """

        intent = event['data']['object']
        order_number = intent.get('metadata', {}).get('order_number')

        if not order_number:
            return HttpResponse(
                "Webhook Error: Missing order_number in metadata",
                status=400
            )

        try:
            order = Order.objects.select_related(
                'delivery_method', 'cart', 'user'
            ).get(order_number=order_number)
        except Order.DoesNotExist:
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=500)

        order_processed_successfully = False
        if order.status == OrderStatus.PENDING:
            try:
                with transaction.atomic():
                    order.status = OrderStatus.PROCESSING
                    order.save(update_fields=['status'])
                    order_processed_successfully = True
            except Exception as e:
                return HttpResponse(status=500)
        else:
            order_processed_successfully = True

        if order_processed_successfully:
            try:
                send_confirmation_email(order)
            except Exception as e:
                pass

        return HttpResponse(status=200)

    def handle_payment_intent_failed(self, event):
        """
        Handles the 'payment_intent.payment_failed' event from Stripe.

        Retrieves the order based on metadata and updates its status
        to 'FAILED' if it was previously 'PENDING'.

        :param event: The Stripe event object.
        :type event: stripe.Event
        :return: An HttpResponse indicating success (200 OK).
        :rtype: django.http.HttpResponse
        """

        intent = event['data']['object']
        order_number = intent.get('metadata', {}).get('order_number')

        if not order_number:
            return HttpResponse(
                "Webhook Error: Missing order_number in metadata",
                status=400
            )

        try:
            order = Order.objects.get(order_number=order_number)
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.FAILED
                order.save(update_fields=['status'])

        except Order.DoesNotExist:
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=500)

        return HttpResponse(status=200)

    def handle_unknown_event(self, event):
        """
        Handles webhook events that are not explicitly defined in the
        handler_map.

        Logs the event type and returns a 200 OK response to Stripe to
        acknowledge receipt, even though no specific action is taken.

        :param event: The Stripe event object.
        :type event: stripe.Event
        :return: An HttpResponse indicating success (200 OK).
        :rtype: django.http.HttpResponse
        """

        return HttpResponse(status=200)
