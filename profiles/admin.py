"""
Django admin configurations for the profiles application models.

Registers models from the profiles app, like ShippingAddress, with the
Django admin site, providing interfaces for managing user profile data.
"""

from django.contrib import admin
from .models import ShippingAddress


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ShippingAddress model.

    Customizes the display, filtering, searching, and editing of user
    shipping addresses in the Django admin interface. Organizes fields
    into logical sections for clarity.
    """

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
        (
            None,
            {'fields': ('user', 'full_name', 'email', 'phone_number')}
        ),
        (
            'Address Details',
            {
                'fields': (
                    'address1',
                    'address2',
                    'city',
                    'state',
                    'zipcode',
                    'country'
                )
            }
        )
    )
