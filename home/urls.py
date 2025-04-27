"""
URL configuration for the RaspiMobile 'home' application.

Defines the URL patterns that map browser requests to the views
responsible for the homepage and about page.
"""

from django.urls import path
from .views import HomeView, AboutView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
]