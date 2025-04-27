"""
Database models for the cart application.

Defines the structure of the shopping cart (`Cart`) and the items
within it (`CartItem`) as stored in the database.
"""

from django.db import models
from django.conf import settings
from products.models import Product


class Cart(models.Model):
    """
    Represents a shopping cart.

    A cart can be associated with a logged-in user (`user` field) or represent
    a guest cart implicitly (if `user` is None, though typically guest carts
    are handled via session first). Tracks creation and update timestamps.

    :param user: ForeignKey relationship to the User model. Can be null for
    guest identification logic elsewhere.
    :param created_on: DateTimeField automatically set when the
    cart is created.
    :param updated_on: DateTimeField automatically set when the cart is
    last updated.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True, blank=True,
                             related_name='carts')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Returns a string representation of the cart.

        :return: A string indicating the user (or 'Guest') and the cart ID.
        :rtype: str
        """

        user_type = self.user if self.user else 'Guest'
        return f'Cart for {user_type} - ID: {self.id}'


class CartItem(models.Model):
    """
    Represents an item within a shopping cart.

    Links a specific product to a cart with a specified quantity. Ensures that
    a product can only appear once per cart (unique_together constraint).

    :param cart: ForeignKey relationship to the Cart this item belongs to.
    :param product: ForeignKey relationship to the Product being added.
    :param quantity: PositiveIntegerField representing the number of units of
    the product.
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                             related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        """
        Returns a string representation of the cart item.

        :return: A string showing quantity, product name, and cart ID.
        :rtype: str
        """

        return f'{self.quantity} x {self.product.name} in Cart {self.cart.id}'

    def total_price(self):
        """
        Calculates the total price for this cart item line.

        Multiplies the item's quantity by the product's price.

        :return: The total price for the quantity of this product.
        :rtype: decimal.Decimal
        """

        return self.quantity * self.product.price

    class Meta:
        """
        Metadata options for the CartItem model.
        """

        unique_together = ('cart', 'product')
