"""
URL configuration for the cart application.

Defines the URL patterns that map request paths to the corresponding
cart views (e.g., adding or removing items from the cart).
"""

from django.urls import path
from .views import AddToCartView, RemoveFromCartView

# Define the URL patterns for the cart app
urlpatterns = [
    # URL pattern for adding a product to the cart
    path('add/<int:product_id>/', AddToCartView.as_view(),
         name='add_to_cart'),
    # URL pattern for removing a product from the cart
    path('remove/<int:product_id>/', RemoveFromCartView.as_view(),
         name='remove_from_cart'),
]
