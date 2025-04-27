"""
Context processors for the orders application.

Provides functions that add order-related information, like recent order
history for the logged-in user, to the template context for every request.
"""

from .models import Order, OrderStatus
from django.urls import reverse


def order_history_context(request):
    """
    Adds recent order history for the logged-in user to the template context.

    Fetches the latest 10 orders for the authenticated user and prepares a list
    of dictionaries containing key order details (number, date, status display,
    status icon/color, confirmation URL) for easy display in templates
    (e.g., sidebar).

    :param request: The HttpRequest object, used to access the user.
    :type request: django.http.HttpRequest
    :return: A dictionary containing the 'user_orders' list.
             Each item in the list is a dictionary representing order summary.
             Returns an empty list if the user is not authenticated.
    :rtype: dict
    """

    user_orders = []
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by(
            '-date_ordered')[:10]

        status_map = {
            OrderStatus.PENDING: {
                'icon': 'fa-clock',
                'color': 'text-warning'
            },
            OrderStatus.PROCESSING: {
                'icon': 'fa-spinner fa-spin',
                'color': 'text-info'
            },
            OrderStatus.SHIPPED: {
                'icon': 'fa-truck',
                'color': 'text-primary'
            },
            OrderStatus.DELIVERED: {
                'icon': 'fa-check-circle',
                'color': 'text-success'
            },
            OrderStatus.CANCELLED: {
                'icon': 'fa-times-circle',
                'color': 'text-muted'
            },
            OrderStatus.FAILED: {
                'icon': 'fa-exclamation-triangle',
                'color': 'text-danger'
            },
        }

        for order in orders:
            status_info = status_map.get(
                order.status,
                {'icon': 'fa-question-circle', 'color': 'text-secondary'}
            )
            user_orders.append({
                'order_number': order.order_number,
                'date_ordered': order.date_ordered,
                'status_display': order.get_status_display(),
                'status_icon': status_info['icon'],
                'status_color': status_info['color'],
                'url': reverse(
                    'order_confirmation',
                    kwargs={'order_number': order.order_number}
                ),
            })

    return {'user_orders': user_orders}
