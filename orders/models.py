from django.db import models
from django.conf import settings
from cart.models import Cart
from products.models import Product
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Payment'
    PROCESSING = 'PROCESSING', 'Processing'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'
    FAILED = 'FAILED', 'Failed'


class DeliveryMethod(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    shipping_full_name = models.CharField("Full Name", max_length=255)
    shipping_email = models.EmailField("Email")
    shipping_phone_number = models.CharField("Phone Number", max_length=20, blank=True)
    shipping_address1 = models.CharField("Address Line 1", max_length=255)
    shipping_address2 = models.CharField("Address Line 2", max_length=255, blank=True)
    shipping_city = models.CharField("City", max_length=100)
    shipping_state = models.CharField("State/Province", max_length=100, blank=True)
    shipping_zipcode = models.CharField("ZIP/Postal Code", max_length=20)
    shipping_country = models.CharField("Country", max_length=100)
    delivery_method = models.ForeignKey(DeliveryMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    date_ordered = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    class Meta:
        ordering = ['-date_ordered']

    def __str__(self):
        return f"Order #{self.order_number} - {self.shipping_full_name}"

    def _generate_order_number(self):
        return uuid.uuid4().hex.upper()

    def update_total(self):
        self.order_total = self.calculate_order_total()
        self.save()

    def calculate_order_total(self):
        total = sum(item.lineitem_total for item in self.items.all())
        if self.delivery_method:
            total += self.delivery_method.price
        return total

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
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
        return f"{self.quantity} x {self.product.name} in Order #{self.order.order_number}"

    def save(self, *args, **kwargs):
        current_price = self.product.price if self.product else self.price
        self.lineitem_total = current_price * self.quantity
        super().save(*args, **kwargs)