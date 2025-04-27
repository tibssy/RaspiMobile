"""
Application configuration for the profiles app.

Defines the configuration class for the 'profiles' Django application,
which typically handles user profile data like shipping addresses.
"""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """
    Configuration class for the 'profiles' application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"
