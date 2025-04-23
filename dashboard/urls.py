from django.urls import path
from .views import DashboardOverviewView


urlpatterns = [
    path('', DashboardOverviewView.as_view(), name='base_dashboard'),
]