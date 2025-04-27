"""
Application configuration for the cart app.

Defines the configuration class for the 'cart' Django application,
including settings like the default auto field and performing setup
tasks like importing signals when the app is ready.
"""

from django.apps import AppConfig


class CartConfig(AppConfig):
    """
    Configuration class for the 'cart' application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "cart"

    def ready(self):
        """
        Called when the Django application registry is fully populated.

        Used here to import the application's signal handlers, ensuring
        they are connected when the application starts.
        """

        import cart.signals  # noqa
