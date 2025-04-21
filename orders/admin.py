from django.contrib import admin
from .models import Order, OrderItem, DeliveryMethod


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('lineitem_total',)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
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
    list_filter = ['status', 'date_ordered', 'delivery_method', 'shipping_country']
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
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']