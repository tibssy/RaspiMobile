from django.contrib import admin
from .models import Category, Product
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_on', 'updated_on', 'image_tag')
    search_fields = ('name',)

    def image_tag(self, obj):
        return format_html('<img src="{}" width="60" />', obj.image.url)

    image_tag.short_description = 'Image'