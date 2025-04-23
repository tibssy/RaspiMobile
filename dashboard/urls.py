from django.urls import path
from .views import DashboardOverviewView, DashboardProductListView


urlpatterns = [
    path('', DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('products/', DashboardProductListView.as_view(), name='dashboard_product_list'),
]