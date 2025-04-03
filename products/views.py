from django.views.generic import ListView
from django.shortcuts import render
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
