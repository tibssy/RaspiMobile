from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404
from .models import Product
from django.db.models import Q


class ProductListView(ListView):
    # model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 3

    def get_queryset(self):
        queryset = Product.objects.all().order_by("-created_on")
        search_query = self.request.GET.get('q')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'


    def get_object(self):
        return get_object_or_404(Product, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        related_products = Product.objects.filter(categories__in=product.categories.all()).exclude(pk=product.pk).distinct()
        context['related_products'] = related_products[:4]

        return context