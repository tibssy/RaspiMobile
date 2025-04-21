from django.urls import path
from . import views


urlpatterns = [
    path('address/edit/', views.EditCreateAddressView.as_view(), name='edit_create_address'),
]