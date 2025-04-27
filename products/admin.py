"""
Django admin configurations for the products application models.

Registers the Category, Product, SpecificationType, ProductSpecification,
and Review models with the Django admin site, providing customized interfaces
for managing product catalog and review data.
"""

from django.contrib import admin
from .models import (
    Category,
    Product,
    SpecificationType,
    ProductSpecification,
    Review
)
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.

    Displays name, slug, and description. Allows searching by name and
    description. Automatically populates the slug field based on the name.
    """

    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class ProductSpecificationInline(admin.TabularInline):
    """
    Inline admin configuration for ProductSpecification models.

    Allows editing product specifications directly within the Product admin
    page. Uses a compact tabular layout and enables autocomplete for the
    spec_type field.
    """

    model = ProductSpecification
    extra = 1
    autocomplete_fields = ['spec_type']
    fields = ['spec_type', 'value']
    verbose_name = 'Specification'
    verbose_name_plural = 'Specifications'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Product model.

    Displays key product details in the list view, including an image
    thumbnail. Allows searching by product name. Includes an inline editor
    for specifications.
    """

    list_display = ('name', 'price', 'created_on', 'updated_on', 'image_tag')
    search_fields = ('name',)
    inlines = [ProductSpecificationInline]

    def image_tag(self, obj):
        """
        Displays the product image as an HTML img tag in the admin
        list/detail view.

        :param obj: The Product instance.
        :type obj: Product
        :return: An HTML string for the image tag, or 'No Image'
                 if none exists.
        :rtype: str
        """

        return format_html('<img src="{}" width="60" />', obj.image.url)

    image_tag.short_description = 'Image'


@admin.register(SpecificationType)
class SpecificationTypeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the SpecificationType model.

    Displays the name and allows searching. Uses a filter_horizontal widget
    for associating with categories.
    """

    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('categories',)


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ProductSpecification model.

    Displays product, spec type, and value. Allows searching and filtering.
    Useful for managing specifications directly, outside the Product
    inline view.
    """

    list_display = ('product', 'spec_type', 'value')
    search_fields = ('product__name', 'spec_type__name', 'value')
    list_filter = ('spec_type',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Review model.

    Displays key review details, allows filtering and searching.
    Enables direct editing of the 'is_approved' status in the list view and
    provides a bulk action to approve multiple reviews.
    """

    list_display = ('product', 'user', 'rating', 'is_approved', 'created_on')
    list_filter = ('rating', 'created_on', 'is_approved')
    search_fields = ('user__username', 'product__name', 'comment')
    readonly_fields = ('created_on', 'updated_on')
    list_editable = ('is_approved',)
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        """
        Bulk action to approve selected reviews.

        Updates the `is_approved` field to True for all reviews in
        the queryset.

        :param request: The HttpRequest object.
        :param queryset: The QuerySet of selected Review objects.
        """

        queryset.update(is_approved=True)

    approve_reviews.short_description = "Approve selected reviews"
