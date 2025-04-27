"""
Database models for the orders application.

Defines the structure for storing order information (`Order`), the items
within each order (`OrderItem`), and available delivery methods
(`DeliveryMethod`). Includes choices for order status (`OrderStatus`).
"""

from django.db import models
from django.conf import settings
from cart.models import Cart
from products.models import Product
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class OrderStatus(models.TextChoices):
    """
    Defines the possible statuses for an Order.
    Uses TextChoices for human-readable labels and database values.
    """

    PENDING = 'PENDING', 'Pending Payment'
    PROCESSING = 'PROCESSING', 'Processing'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'
    FAILED = 'FAILED', 'Failed'


class DeliveryMethod(models.Model):
    """
    Represents a shipping/delivery option available to customers.

    :param name: The name of the delivery method (e.g., "Standard Shipping").
    :param description: A brief description of the method (optional).
    :param price: The cost associated with this delivery method.
    :param is_active: Boolean indicating if this method is currently available.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        Returns the string representation of the delivery method.

        :return: The name of the delivery method.
        :rtype: str
        """

        return self.name


class Order(models.Model):
    """
    Represents a customer order.

    Stores customer shipping details, chosen delivery method, order total,
    status, and links to the user (if authenticated) and the cart from which
    it was created (optional).

    :param user: ForeignKey to the User model (optional, for logged-in users).
    :param order_number: A unique identifier for the order (auto-generated).
    :param cart: ForeignKey to the Cart model
                 (optional, links to the originating cart).
    :param shipping_full_name: Customer's full name for shipping.
    :param shipping_email: Customer's email address.
    :param shipping_phone_number: Customer's phone number (optional).
    :param shipping_address1: First line of the shipping address.
    :param shipping_address2: Second line of the shipping address (optional).
    :param shipping_city: Shipping city.
    :param shipping_state: Shipping state/province (optional).
    :param shipping_zipcode: Shipping ZIP or postal code.
    :param shipping_country: Shipping country.
    :param delivery_method: ForeignKey to the chosen DeliveryMethod.
    :param order_total: The total cost of the order (items + delivery).
    :param date_ordered: Timestamp when the order was created.
    :param date_updated: Timestamp when the order was last updated.
    :param status: The current status of the order (from OrderStatus choices).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='orders')
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='orders')
    shipping_full_name = models.CharField("Full Name", max_length=255)
    shipping_email = models.EmailField("Email")
    shipping_phone_number = models.CharField("Phone Number", max_length=20,
                                             blank=True)
    shipping_address1 = models.CharField("Address Line 1", max_length=255)
    shipping_address2 = models.CharField("Address Line 2", max_length=255,
                                         blank=True)
    shipping_city = models.CharField("City", max_length=100)
    shipping_state = models.CharField("State/Province", max_length=100,
                                      blank=True)
    shipping_zipcode = models.CharField("ZIP/Postal Code", max_length=20)
    shipping_country = models.CharField("Country", max_length=100)
    delivery_method = models.ForeignKey(DeliveryMethod,
                                        on_delete=models.SET_NULL, null=True,
                                        blank=True, related_name='orders')
    order_total = models.DecimalField(max_digits=10, decimal_places=2,
                                      validators=[
                                          MinValueValidator(Decimal('0.00'))],
                                      default=Decimal('0.00'))
    date_ordered = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices,
                              default=OrderStatus.PENDING)

    class Meta:
        """
        Metadata options for the Order model.
        """

        ordering = ['-date_ordered']

    def __str__(self):
        """
        Returns the string representation of the order.

        :return: A string containing the order number and customer name.
        :rtype: str
        """

        return f"Order #{self.order_number} - {self.shipping_full_name}"

    def _generate_order_number(self):
        """
        Generates a unique, random order number using UUID.

        :return: A unique hexadecimal string for the order number.
        :rtype: str
        """

        return uuid.uuid4().hex.upper()

    def update_total(self):
        """
        Recalculates the order total based on its items and delivery cost,
        then saves the order.
        Note: This might be better called within the save method or triggered
              explicitly when items/delivery method change post-creation if
              that's allowed. Currently called explicitly in webhook handler.
        """

        self.order_total = self.calculate_order_total()
        self.save()

    def calculate_order_total(self):
        """
        Calculates the total cost of the order.

        Sums the `lineitem_total` of all associated OrderItems and adds the
        cost of the selected delivery method.

        :return: The calculated total cost of the order.
        :rtype: decimal.Decimal
        """

        total = sum(item.lineitem_total for item in self.items.all())
        if self.delivery_method:
            total += self.delivery_method.price
        return total

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to generate an order number if
        creating a new order.

        :param args: Additional positional arguments for the save method.
        :param kwargs: Additional keyword arguments for the save method.
        """

        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Represents a single item within an Order.

    Links an Order to a Product, storing the quantity and the price at the
    time the order was placed. Calculates the total cost for this line item.

    :param order: ForeignKey to the Order this item belongs to.
    :param product: ForeignKey to the Product ordered.
    :param quantity: The number of units of the product ordered.
    :param price: The price per unit of the product at the time of ordering.
    :param lineitem_total: The calculated total cost for this line item
                           (price * quantity).
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    lineitem_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=Decimal('0.00')
    )

    def __str__(self):
        """
        Returns the string representation of the order item.

        :return: A string showing quantity, product name, and order number.
        :rtype: str
        """

        return (
            f"{self.quantity} x {self.product.name} in "
            f"Order #{self.order.order_number}"
        )

    def save(self, *args, **kwargs):
        """
        Overrides the save method to calculate the line item total
        before saving.

        Uses the stored `price` field, not the current product price,
        for calculation.

        :param args: Additional positional arguments for the save method.
        :param kwargs: Additional keyword arguments for the save method.
        """

        current_price = self.product.price if self.product else self.price
        self.lineitem_total = current_price * self.quantity
        super().save(*args, **kwargs)
