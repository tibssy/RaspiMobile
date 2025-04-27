"""
URL configuration for the dashboard application.

Defines the URL patterns that map request paths to the corresponding
dashboard views for staff users. Includes paths for overview, product
management, order management, review management, and statistics.
"""

from django.urls import path
from .views import (
    DashboardOverviewView,
    DashboardProductListView,
    DashboardProductEditView,
    DashboardProductDeleteView,
    DashboardProductCreateView,
    DashboardOrderListView,
    DashboardUpdateOrderStatusView,
    DashboardReviewListView,
    DashboardReviewToggleApprovalView,
    DashboardStatisticsView,
)


urlpatterns = [
    # Dashboard home/overview
    path(
        '',
        DashboardOverviewView.as_view(),
        name='dashboard_overview'
    ),
    # Product Management URLs
    path(
        'products/',
        DashboardProductListView.as_view(),
        name='dashboard_product_list'
    ),
    path(
        'products/add/',
        DashboardProductCreateView.as_view(),
        name='dashboard_product_add'
    ),
    path(
        'products/<int:pk>/edit/',
        DashboardProductEditView.as_view(),
        name='dashboard_product_edit'
    ),
    path(
        'products/<int:pk>/delete/',
        DashboardProductDeleteView.as_view(),
        name='dashboard_product_delete'
    ),
    # Order Management URLs
    path(
        'orders/',
        DashboardOrderListView.as_view(),
        name='dashboard_order_list'
    ),
    path(
        'orders/<int:pk>/update_status/',
        DashboardUpdateOrderStatusView.as_view(),
        name='dashboard_order_update_status'
    ),
    # Review Management URLs
    path(
        'reviews/',
        DashboardReviewListView.as_view(),
        name='dashboard_review_list'
    ),
    path(
        'reviews/<int:pk>/toggle_approval/',
        DashboardReviewToggleApprovalView.as_view(),
        name='dashboard_review_toggle_approval'
    ),
    # Statistics URL
    path(
        'statistics/',
        DashboardStatisticsView.as_view(),
        name='dashboard_statistics'
    ),
]
