from django.contrib import admin
from .models import Order, OrderItem, DeliveryMethod


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'shipping_address', 'delivery_method', 'order_total', 'status', 'date_ordered']
    list_filter = ['status', 'date_ordered', 'delivery_method']
    search_fields = ['order_number', 'shipping_address__full_name', 'user__username', 'shipping_address__email']
    readonly_fields = ['order_number', 'date_ordered', 'date_updated']
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'shipping_address', 'delivery_method', 'status')
        }),
        ('Totals', {
            'fields': ('order_total',)
        }),
        ('Dates', {
            'fields': ('date_ordered', 'date_updated')
        }),
    )


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']