from django.urls import path
from .views import CreateOrderView, PaymentView

urlpatterns = [
    path('checkout/', CreateOrderView.as_view(), name='checkout'),
    path('payment/<str:order_number>/', PaymentView.as_view(), name='payment_page'),
]