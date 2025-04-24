from django.db import models
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = CloudinaryField('image', default='placeholder')
    categories = models.ManyToManyField(Category, related_name='products')
    description = models.TextField(default="")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.name


class SpecificationType(models.Model):
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(Category, related_name='specification_types')

    def __str__(self):
        return self.name


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    spec_type = models.ForeignKey(SpecificationType, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.spec_type.name}: {self.value}'