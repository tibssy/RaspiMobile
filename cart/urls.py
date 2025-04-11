from django.urls import path
from .views import AddToCartView


urlpatterns = [
    path('add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
]