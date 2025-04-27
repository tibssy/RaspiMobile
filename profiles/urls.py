from django.urls import path
from .views import ManageProfileView, DeleteAccountView


urlpatterns = [
    path('manage/', ManageProfileView.as_view(), name='manage_profile'),
    path('delete/', DeleteAccountView.as_view(), name='delete_account'),
]