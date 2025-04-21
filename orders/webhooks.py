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
import logging


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Listen for webhooks from Stripe"""

    def post(self, request, *args, **kwargs):
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
            print(f"Webhook Error (ValueError): {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            print(f"Webhook Error (SignatureVerificationError): {e}")
            return HttpResponse(status=400)
        except Exception as e:
            # Generic error during signature verification
            print(f"Webhook Error (Exception): {e}")
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
            print(f"Error processing webhook event {event_type}: {e}")
            return HttpResponse(status=500)


    def handle_payment_intent_succeeded(self, event):
        intent = event['data']['object']
        logger.info("Webhook: Handling payment_intent.succeeded")
        order_number = intent.get('metadata', {}).get('order_number')

        if not order_number:
            logger.error("Webhook Error: order_number missing in PaymentIntent metadata")
            return HttpResponse("Webhook Error: Missing order_number in metadata", status=400)

        try:
            order = Order.objects.select_related('delivery_method', 'cart', 'user').get(order_number=order_number)
        except Order.DoesNotExist:
            logger.warning(f"Webhook Succeeded: Order {order_number} not found (might be test).")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Webhook Error (DB Query - Succeeded Event): Order {order_number} - {e}", exc_info=True)
            return HttpResponse(status=500)

        order_processed_successfully = False
        if order.status == OrderStatus.PENDING:
            try:
                with transaction.atomic():
                    order.status = OrderStatus.PROCESSING
                    order.save(update_fields=['status'])
                    logger.info(f"Webhook: Order {order_number} status updated to PROCESSING.")
                    order_processed_successfully = True
            except Exception as e:
                logger.error(f"Webhook Error (DB Update - Succeeded Event): Order {order_number} - {e}", exc_info=True)
                return HttpResponse(status=500)
        else:
            logger.info(f"Webhook: Order {order_number} status already '{order.status}'. No action taken.")
            order_processed_successfully = True

        if order_processed_successfully:
            logger.info(f"Attempting to send confirmation email for order {order.order_number}...")
            try:
                email_sent = send_confirmation_email(order)
                if not email_sent:
                     logger.error(f"Attempt to send confirmation email for order {order.order_number} failed (function returned False).")
            except Exception as e:
                 logger.error(f"Unexpected error calling send_confirmation_email for order {order.order_number}: {e}", exc_info=True)

        return HttpResponse(status=200)


    def handle_payment_intent_failed(self, event):
        intent = event['data']['object']
        order_number = intent.get('metadata', {}).get('order_number')

        if not order_number:
            return HttpResponse("Webhook Error: Missing order_number in metadata", status=400)

        try:
            order = Order.objects.get(order_number=order_number)
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.FAILED
                order.save(update_fields=['status'])
            else:
                print(f"Webhook: Failed payment for order {order_number}, but status is '{order.status}'. No action taken.")

        except Order.DoesNotExist:
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=500)

        return HttpResponse(status=200)

    def handle_unknown_event(self, event):
        return HttpResponse(status=200)