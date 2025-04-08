from django.contrib import admin
from .models import Category, Product, SpecificationType, ProductSpecification
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    autocomplete_fields = ['spec_type']
    fields = ['spec_type', 'value']
    verbose_name = 'Specification'
    verbose_name_plural = 'Specifications'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_on', 'updated_on', 'image_tag')
    search_fields = ('name',)
    inlines = [ProductSpecificationInline]

    def image_tag(self, obj):
        return format_html('<img src="{}" width="60" />', obj.image.url)
    image_tag.short_description = 'Image'


@admin.register(SpecificationType)
class SpecificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('categories',)


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'spec_type', 'value')
    search_fields = ('product__name', 'spec_type__name', 'value')
    list_filter = ('spec_type',)
