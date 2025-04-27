from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings


def accounts_root_redirect(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return redirect('account_login')


urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', accounts_root_redirect, name='accounts_base_redirect'),
    path("accounts/", include("allauth.urls")),
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('profile/', include('profiles.urls')),
    path('dashboard/', include('dashboard.urls')),
]
