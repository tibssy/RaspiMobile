from django.contrib import admin
from .models import ShippingAddress


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'full_name',
        'email',
        'address1',
        'city',
        'country',
        'zipcode'
        ]

    search_fields = [
        'full_name',
        'email',
        'address1',
        'city',
        'zipcode',
        'country',
        'user__username',
        'user__email'
        ]

    list_filter = [
        'country',
        'user'
    ]

    fieldsets = (
        (None, {
            'fields': ('user', 'full_name', 'email', 'phone_number')
        }),
        ('Address Details', {
            'fields': ('address1', 'address2', 'city', 'state', 'zipcode', 'country')
        }),
    )