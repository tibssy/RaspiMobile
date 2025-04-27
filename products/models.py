"""
Database models for the products application.

Defines the structure for storing product information (`Product`), categories
(`Category`), product specifications
(`SpecificationType`, ProductSpecification`), and customer reviews (`Review`).
"""

from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.db.models import Avg


class Category(models.Model):
    """
    Represents a category for organizing products.

    :param name: The name of the category (must be unique).
    :param slug: A URL-friendly version of the name (must be unique).
    :param description: An optional description of the category.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        """
        Metadata options for the Category model.
        """

        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        """
        Returns the string representation of the category.

        :return: The name of the category.
        :rtype: str
        """

        return self.name


class Product(models.Model):
    """
    Represents a product available for sale.

    :param name: The name of the product.
    :param price: The price of the product (must be positive).
    :param image: The main image for the product (uses CloudinaryField).
    :param categories: ManyToMany relationship to Category model.
    :param description: A detailed description of the product.
    :param sku: Stock Keeping Unit (optional, unique identifier).
    :param stock_quantity: The number of units currently in stock.
    :param is_featured: Boolean indicating if the product should be featured
                        (e.g., on homepage).
    :param is_active: Boolean indicating if the product is available
                      for sale/visible.
    :param created_on: Timestamp when the product was added.
    :param updated_on: Timestamp when the product was last updated.
    """

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[
        MinValueValidator(Decimal('0.01'))])
    image = CloudinaryField('image', default='placeholder')
    categories = models.ManyToManyField(Category, related_name='products')
    description = models.TextField(default="")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True,
                           default=None)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Metadata options for the Product model.
        """

        ordering = ['-created_on']

    def __str__(self):
        """
        Returns the string representation of the product.

        :return: The name of the product.
        :rtype: str
        """

        return self.name

    @property
    def average_rating(self):
        """
        Calculates the average rating based on approved reviews for this
        product.

        :return: The average rating as a float, or 0 if no approved
                 reviews exist.
        :rtype: float
        """

        avg = self.reviews.filter(is_approved=True).aggregate(
            average=Avg('rating'))
        return avg.get('average') or 0


class SpecificationType(models.Model):
    """
    Represents a type of specification attribute (e.g., "Color", "Material").

    Can be associated with specific categories to suggest relevant
    specifications.

    :param name: The name of the specification type.
    :param categories: ManyToMany relationship linking spec types to
                       relevant categories.
    """

    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(Category,
                                        related_name='specification_types')

    def __str__(self):
        """
        Returns the string representation of the specification type.

        :return: The name of the specification type.
        :rtype: str
        """

        return self.name


class ProductSpecification(models.Model):
    """
    Represents a specific attribute value for a product.

    Links a Product to a SpecificationType and stores the corresponding value
    (e.g., Product: "T-Shirt", SpecType: "Color", Value: "Red").

    :param product: ForeignKey to the Product this specification belongs to.
    :param spec_type: ForeignKey to the SpecificationType (e.g., "Color").
    :param value: The actual value of the specification (e.g., "Red").
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='specifications')
    spec_type = models.ForeignKey(SpecificationType, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        """
        Metadata options for the ProductSpecification model.
        """

        unique_together = ('product', 'spec_type')

    def __str__(self):
        """
        Returns a string representation of the product specification.

        :return: A string combining the specification type name and its value.
        :rtype: str
        """

        return f'{self.spec_type.name}: {self.value}'


class Review(models.Model):
    """
    Represents a customer review for a specific product.

    Links a Product to a User, storing their rating and comments. Includes
    an approval status, typically moderated by staff.

    :param product: ForeignKey to the Product being reviewed.
    :param user: ForeignKey to the User who wrote the review.
    :param rating: An integer rating (e.g., 1 to 5).
    :param comment: The text content of the review.
    :param created_on: Timestamp when the review was submitted.
    :param updated_on: Timestamp when the review was last updated.
    :param is_approved: Boolean indicating if the review is visible to
                        other users.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rate the product from 1 (worst) to 5 (best).')
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        """
        Metadata options for the Review model.
        """

        ordering = ['-created_on']
        unique_together = ('product', 'user')
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'

    def __str__(self):
        """
        Returns a string representation of the review.

        :return: A string summarizing the review (product, user, rating).
        :rtype: str
        """

        return (
            f'Review for "{self.product.name}" '
            f'by {self.user.username} ({self.rating}/5)'
        )
