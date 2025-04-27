"""
Database models for the RaspiMobile 'profiles' application.

Includes the ShippingAddress model to store user address information.
"""

from django.db import models
from django.conf import settings


class ShippingAddress(models.Model):
    """
    Represents a shipping address associated with a user.

    Stores standard address components and links to the user account.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='shipping_addresses')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        """
        Return a string representation of the address.

        Includes the full name, first address line, city, and associated
        username if available.

        :return: Formatted address string.
        :rtype: str
        """

        user_info = f" ({self.user.get_username()})" if self.user else " (Guest/Unlinked)"
        return f"{self.full_name}, {self.address1}, {self.city}{user_info}"

    class Meta:
        """Meta options for the ShippingAddress model."""
        verbose_name_plural = "User Profile Shipping Addresses"
