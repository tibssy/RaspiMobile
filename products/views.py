from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Review
from .forms import ReviewForm
from django.db.models import Q, Avg
from django.urls import reverse
from django.contrib import messages


class ProductListView(ListView):
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        search_query = self.request.GET.get('q')
        sort_by = self.request.GET.get('sort')
        selected_category_slugs = self.request.GET.getlist('category')
        queryset = queryset.annotate(calculated_average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)))

        if selected_category_slugs:
            queryset = queryset.filter(categories__slug__in=selected_category_slugs).distinct()

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
        elif sort_by == 'rating_desc':
            queryset = queryset.order_by('-calculated_average_rating')
        else:
            queryset = queryset.order_by('-created_on')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_categories'] = Category.objects.all().order_by('name')
        context['selected_categories'] = self.request.GET.getlist('category')
        context['search_term'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


class ProductDetailView(FormMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    form_class = ReviewForm

    def get_object(self):
        obj = get_object_or_404(Product.objects.filter(is_active=True), pk=self.kwargs['pk'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        reviews = Review.objects.filter(product=product, is_approved=True).select_related('user').order_by('-created_on')
        context['reviews'] = reviews
        context['review_count'] = reviews.count()
        context['review_form'] = self.get_form()
        related_products = Product.objects.filter(categories__in=product.categories.all(), is_active=True).exclude(pk=product.pk).distinct()
        context['related_products'] = related_products[:4]
        context['user_has_reviewed'] = False

        if self.request.user.is_authenticated:
            context['user_has_reviewed'] = Review.objects.filter(product=product, user=self.request.user).exists()

        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        context['average_rating'] = round(avg_rating, 1) if avg_rating else None
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to submit a review.")
            return redirect('account_login')

        self.object = self.get_object()
        form = self.get_form()

        if Review.objects.filter(product=self.object, user=request.user).exists():
            messages.warning(request, "You have already submitted a review for this product.")
            return redirect(self.get_success_url())

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        review = form.save(commit=False)
        review.product = self.object
        review.user = self.request.user
        review.save()

        if review.is_approved:
            messages.success(self.request, "Thank you! Your review has been published.")
        else:
            messages.success(self.request, "Thank you! Your review has been submitted and is pending approval.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to submit review. Please check the errors below.")
        return self.get(self.request, *self.args, **self.kwargs)

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.pk})
