"""
Application configuration for the products app.

Defines the configuration class for the 'products' Django application.
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """
    Configuration class for the 'products' application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
