"""
This module defines the URL patterns for the 'home' app.

It maps the root URL ('') to the 'home' view function,
providing access to the home page.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Maps the root URL to the home view.
    path('', views.home, name='home'),
]