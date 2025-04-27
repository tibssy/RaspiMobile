"""
URL configuration for the RaspiMobile 'profiles' application.

Maps URLs to the views responsible for managing user profiles,
shipping addresses, and account deletion.
"""

from django.urls import path
from .views import ManageProfileView, DeleteAccountView


urlpatterns = [
    path('manage/', ManageProfileView.as_view(), name='manage_profile'),
    path('delete/', DeleteAccountView.as_view(), name='delete_account'),
]