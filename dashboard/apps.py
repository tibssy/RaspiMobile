"""
Application configuration for the dashboard app.

Defines the configuration class for the 'dashboard' Django application.
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Configuration class for the 'dashboard' application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
