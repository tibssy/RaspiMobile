from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from products.models import Product
from django.db.models import Avg, Q
from django.db.models.functions import Coalesce


class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        ).exclude(
            image='placeholder'
        ).annotate(
            calculated_average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
        )
        featured_products = base_queryset.filter(is_featured=True)[:3]
        featured_pks = list(featured_products.values_list('pk', flat=True))
        best_rated_products = base_queryset.exclude(
            pk__in=featured_pks
        ).filter(
            calculated_average_rating__isnull=False
        ).order_by(
            Coalesce('calculated_average_rating', 0).desc()
        )[:2]

        context['featured_products'] = featured_products
        context['best_rated_products'] = best_rated_products

        return context
