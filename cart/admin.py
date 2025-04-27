"""
Django admin configurations for the cart application models.

Registers the Cart and CartItem models with the Django admin site,
providing customized interfaces for managing cart data.
"""

from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """
    Inline admin configuration for CartItem models.

    Allows editing CartItems directly within the Cart admin page.
    Provides a compact tabular interface for associated items.
    """

    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Cart model.

    Customizes the display, filtering, searching, and editing
    of Cart objects in the Django admin interface. Includes an
    inline editor for associated CartItems.
    """

    list_display = ['id', 'user', 'created_on', 'updated_on']
    list_filter = ['user', 'created_on', 'updated_on']
    search_fields = ['user__username', 'id']
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the CartItem model.

    Customizes the display, filtering, and searching of CartItem objects
    directly in the admin interface. Useful for viewing or managing
    individual items across different carts.
    """

    list_display = ['id', 'cart', 'product', 'quantity']
    list_filter = ['cart', 'product']
    search_fields = ['product__name', 'cart__id']
