from django.contrib import admin
from .models import ShippingAddress


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'address1', 'city', 'country']
    search_fields = ['full_name', 'email', 'address1', 'city', 'zipcode']
