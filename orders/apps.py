"""
Application configuration for the orders app.

Defines the configuration class for the 'orders' Django application.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuration class for the 'orders' application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
