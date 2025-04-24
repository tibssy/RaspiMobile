from django.urls import path
from .views import (
    DashboardOverviewView,
    DashboardProductListView,
    DashboardProductEditView,
    DashboardProductDeleteView,
    DashboardProductCreateView,
    DashboardOrderListView,
    DashboardUpdateOrderStatusView
)


urlpatterns = [
    path('', DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('products/', DashboardProductListView.as_view(), name='dashboard_product_list'),
    path('products/add/', DashboardProductCreateView.as_view(), name='dashboard_product_add'),
    path('products/<int:pk>/edit/', DashboardProductEditView.as_view(), name='dashboard_product_edit'),
    path('products/<int:pk>/delete/', DashboardProductDeleteView.as_view(), name='dashboard_product_delete'),
    path('orders/', DashboardOrderListView.as_view(), name='dashboard_order_list'),
    path('orders/<int:pk>/update_status/', DashboardUpdateOrderStatusView.as_view(), name='dashboard_order_update_status'),
]