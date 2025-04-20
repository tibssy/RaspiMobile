from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import logging


logger = logging.getLogger(__name__)


def send_confirmation_email(order):
    if not order or not order.shipping_address or not order.delivery_method:
        logger.error(f"Attempted to send confirmation email for incomplete order: {order.order_number if order else 'N/A'}")
        return False

    recipient_email = order.shipping_address.email
    if not recipient_email:
        logger.warning(f"No recipient email found for order: {order.order_number}. Cannot send confirmation.")
        return False

    subtotal = order.order_total - order.delivery_method.price

    context = {
        'order': order,
        'subtotal': subtotal,
    }

    try:
        subject = render_to_string('orders/email/confirmation_email_subject.txt', context).strip()
        subject_prefix = getattr(settings, 'ACCOUNT_EMAIL_SUBJECT_PREFIX', '')
        full_subject = f"{subject_prefix}{subject}"
        text_body = render_to_string('orders/email/confirmation_email_body.txt', context)
        html_body = render_to_string('orders/email/confirmation_email_body.html', context)

        msg = EmailMultiAlternatives(
            subject=full_subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(f"Confirmation email sent successfully for order: {order.order_number} to {recipient_email}")

        return True

    except Exception as e:
        logger.error(f"Error sending confirmation email for order {order.order_number}: {e}", exc_info=True)
        return False