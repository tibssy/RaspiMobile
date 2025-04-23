from django.urls import path
from .views import DashboardOverviewView, DashboardProductListView, DashboardProductEditView


urlpatterns = [
    path('', DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('products/', DashboardProductListView.as_view(), name='dashboard_product_list'),
    path('products/<int:pk>/edit/', DashboardProductEditView.as_view(), name='dashboard_product_edit'),
]