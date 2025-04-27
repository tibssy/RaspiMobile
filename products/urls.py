"""
URL configuration for the products application.

Defines the URL patterns that map request paths to the corresponding
product views, such as the product list page and the product detail page.
"""

from django.urls import path
from .views import ProductListView, ProductDetailView

urlpatterns = [
    # URL pattern for the main product listing page
    path(
        '',
        ProductListView.as_view(),
        name='product_list'
    ),
    # URL pattern for a specific product's detail page
    path(
        'product/<int:pk>/',
        ProductDetailView.as_view(),
        name='product_detail'
    ),
]
