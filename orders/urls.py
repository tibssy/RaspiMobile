from django.urls import path
from .views import CreateOrderView, PaymentView, OrderConfirmationView

urlpatterns = [
    path('checkout/', CreateOrderView.as_view(), name='checkout'),
    path('payment/<str:order_number>/', PaymentView.as_view(), name='payment_page'),
    path('confirmation/<str:order_number>/', OrderConfirmationView.as_view(), name='order_confirmation'),
]