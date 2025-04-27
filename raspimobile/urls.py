"""
Main URL configuration for the E-commerce project.

This module defines the top-level URL patterns for the entire Django project.
It includes paths for the admin interface, authentication (via django-allauth),
and routes requests to the specific URL configurations defined within each
application (home, products, cart, orders, profiles, dashboard). It also
includes a custom redirect view for the base '/accounts/' path.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings


def accounts_root_redirect(request):
    """
    Redirects requests to the base '/accounts/' URL.

    If the user is authenticated, redirects them to the URL specified by
    `settings.LOGIN_REDIRECT_URL` (typically the user profile or dashboard).
    If the user is not authenticated, redirects them to the login page
    defined by the 'account_login' URL name (provided by django-allauth).

    :param request: The HttpRequest object.
    :type request: django.http.HttpRequest
    :return: An HttpResponseRedirect to the appropriate page.
    :rtype: django.http.HttpResponseRedirect
    """

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
