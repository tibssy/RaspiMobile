"""
Django admin configurations for the orders application models.

Registers the Order, OrderItem, and DeliveryMethod models with the Django
admin site, providing customized interfaces for managing order and
delivery data.
"""

from django.contrib import admin
from .models import Order, OrderItem, DeliveryMethod


class OrderItemInline(admin.TabularInline):
    """
    Inline admin configuration for OrderItem models.

    Allows viewing and editing OrderItems directly within the Order admin page.
    Makes the calculated `lineitem_total` read-only.
    """

    model = OrderItem
    readonly_fields = ('lineitem_total',)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Order model.

    Customizes the display, filtering, searching, and editing of Order
    objects. Includes an inline editor for associated OrderItems and
    organizes fields into fieldsets.
    """

    inlines = [OrderItemInline]

    list_display = [
        'order_number',
        'user',
        'shipping_full_name',
        'shipping_city',
        'shipping_country',
        'delivery_method',
        'order_total',
        'status',
        'date_ordered'
    ]
    list_filter = [
        'status',
        'date_ordered',
        'delivery_method',
        'shipping_country'
    ]
    search_fields = [
        'order_number',
        'shipping_full_name',
        'shipping_email',
        'shipping_address1',
        'shipping_zipcode',
        'user__username',
        'user__email'
    ]
    readonly_fields = [
        'order_number',
        'order_total',
        'date_ordered',
        'date_updated'
    ]
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'cart', 'status')
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_full_name',
                'shipping_email',
                'shipping_phone_number',
                'shipping_address1',
                'shipping_address2',
                'shipping_city',
                'shipping_state',
                'shipping_zipcode',
                'shipping_country',
            )
        }),
        ('Delivery and Totals', {
            'fields': ('delivery_method', 'order_total')
        }),
        ('Timestamps', {
            'fields': ('date_ordered', 'date_updated')
        }),
    )


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    """
    Admin configuration for the DeliveryMethod model.

    Customizes the display, filtering, and searching for delivery methods.
    """

    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
