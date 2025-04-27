"""
Utility functions for sending order-related emails.

Includes functions for sending order confirmation emails to customers after
successful payment and order processing.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal


def send_confirmation_email(order):
    """
    Sends an order confirmation email to the customer.

    Renders text and HTML versions of the email body using templates.
    Requires the order object to have necessary details like shipping email
    and delivery method.

    :param order: The Order instance for which to send the confirmation.
    :type order: orders.models.Order
    :return: True if the email was sent successfully, False otherwise.
    :rtype: bool
    """

    if not order or not order.shipping_email or not order.delivery_method:
        return False

    recipient_email = order.shipping_email

    if not recipient_email:
        return False

    subtotal = Decimal('0.00')
    ord_total = order.order_total
    if ord_total is not None and order.delivery_method.price is not None:
        subtotal = ord_total - order.delivery_method.price
    else:
        subtotal = sum(item.lineitem_total for item in order.items.all())

    cost = order.delivery_method.price if order.delivery_method else Decimal(
        '0.00'),
    context = {
        'order': order,
        'subtotal': subtotal,
        'delivery_cost': cost
    }

    try:
        subject = render_to_string(
            'orders/email/confirmation_email_subject.txt',
            context
        ).strip()
        subject_prefix = getattr(settings, 'ACCOUNT_EMAIL_SUBJECT_PREFIX', '')
        full_subject = f"{subject_prefix}{subject}"
        text_body = render_to_string(
            'orders/email/confirmation_email_body.txt',
            context
        )
        html_body = render_to_string(
            'orders/email/confirmation_email_body.html',
            context  #
        )

        msg = EmailMultiAlternatives(
            subject=full_subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True

    except Exception as e:
        return False
