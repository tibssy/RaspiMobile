from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from django.db.models import Q


class ProductListView(ListView):
    # model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        queryset = Product.objects.all()
        search_query = self.request.GET.get('q')
        sort_by = self.request.GET.get('sort')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(categories__name__icontains=search_query) |
                Q(specifications__value__icontains=search_query) |
                Q(specifications__spec_type__name__icontains=search_query)
            ).distinct()

        if sort_by == 'newest':
            queryset = queryset.order_by('-created_on')
        elif sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('-created_on')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
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
