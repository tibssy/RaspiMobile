from django.views.generic import ListView
from django.shortcuts import render
from .models import Product


class ProductListView(ListView):
    # model = Product
    queryset = Product.objects.all().order_by("-created_on")
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 4