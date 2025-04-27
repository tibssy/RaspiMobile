"""
Defines the views for the products application.

This module contains views for displaying lists of products (`ProductListView`)
and the detailed view of a single product (`ProductDetailView`),
including handling product reviews submission via a form.
"""

from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Review
from .forms import ReviewForm
from django.db.models import Q, Avg
from django.urls import reverse
from django.contrib import messages


class ProductListView(ListView):
    """
    Displays a list of active products.

    Handles filtering by category, searching across multiple fields (name,
    description, SKU, category, specifications), and sorting by various
    criteria (newest, price, rating). Supports pagination.
    """

    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        """
        Retrieves and filters the queryset of active products.

        Applies filters based on GET parameters for search query ('q'),
        category slugs ('category'), and sorting ('sort'). Annotates the
        queryset with the calculated average rating for sorting purposes.

        :return: A filtered and sorted QuerySet of Product objects.
        :rtype: django.db.models.QuerySet
        """

        queryset = Product.objects.filter(is_active=True)
        search_query = self.request.GET.get('q')
        sort_by = self.request.GET.get('sort')
        selected_category_slugs = self.request.GET.getlist('category')
        queryset = queryset.annotate(
            calculated_average_rating=Avg(
                'reviews__rating',
                filter=Q(reviews__is_approved=True)
            )
        )

        if selected_category_slugs:
            queryset = queryset.filter(
                categories__slug__in=selected_category_slugs
            ).distinct()

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
        """
        Adds filtering, sorting, and category data to the template context.

        Includes all categories for filter display, the currently selected
        categories, the search term, and the current sort parameter.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['all_categories'] = Category.objects.all().order_by('name')
        context['selected_categories'] = self.request.GET.getlist('category')
        context['search_term'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


class ProductDetailView(FormMixin, DetailView):
    """
    Displays the detail page for a single active product.

    Includes product information, approved reviews, a form for submitting
    new reviews (using FormMixin), related products, and average rating.
    Handles POST requests for review submission.
    """

    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    form_class = ReviewForm

    def get_object(self):
        """
        Retrieves the active Product object based on the primary
        key in the URL.

        Ensures only active products are displayed and returns a 404 if
        not found or not active.

        :param queryset: Optional queryset to use.
        :return: The active Product instance.
        :rtype: products.models.Product
        :raises: Http404 if the product is not found or not active.
        """

        return get_object_or_404(
            Product.objects.filter(is_active=True),
            pk=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        """
        Populates the context data for the product detail template.

        Includes the product, approved reviews, review count, review form,
        related products, average rating, and checks if the current user
        has already reviewed this product.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        product = self.object
        reviews = Review.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user').order_by('-created_on')
        context['reviews'] = reviews
        context['review_count'] = reviews.count()
        context['review_form'] = self.get_form()
        related_products = Product.objects.filter(
            categories__in=product.categories.all(),
            is_active=True
        ).exclude(pk=product.pk).distinct().annotate(
            calculated_average_rating=Avg(
                'reviews__rating',
                filter=Q(reviews__is_approved=True)
            )
        )
        context['related_products'] = related_products[:4]
        context['user_has_reviewed'] = False

        if self.request.user.is_authenticated:
            context['user_has_reviewed'] = Review.objects.filter(
                product=product,
                user=self.request.user
            ).exists()

        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        context['average_rating'] = round(
            avg_rating,
            1
        ) if avg_rating else None
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for submitting a product review.

        Requires user authentication. Checks if the user has already reviewed
        the product. Validates the submitted review form.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Keyword arguments containing the product
                       primary key ('pk').
        :return: An HttpResponse
                 (redirect on success/failure, or re-render on invalid form).
        :rtype: django.http.HttpResponse
        """

        if not request.user.is_authenticated:
            messages.error(request,
                           "You must be logged in to submit a review.")
            return redirect('account_login')

        self.object = self.get_object()
        form = self.get_form()

        if Review.objects.filter(product=self.object,
                                 user=request.user).exists():
            messages.warning(
                request,
                "You have already submitted a review for this product."
            )
            return redirect(self.get_success_url())

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        Processes a valid review form submission.

        Saves the review, associating it with the product and current user.
        Adds a success message (different based on auto-approval status).
        Redirects to the product detail page.

        :param form: The valid ReviewForm instance.
        :type form: products.forms.ReviewForm
        :return: An HttpResponseRedirect to the product detail page.
        :rtype: django.http.HttpResponseRedirect
        """

        review = form.save(commit=False)
        review.product = self.object
        review.user = self.request.user
        review.save()

        if review.is_approved:
            messages.success(
                self.request,
                "Thank you! Your review has been published."
            )
        else:
            messages.success(
                self.request,
                "Thank you! Your review has been submitted"
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles an invalid review form submission.

        Adds an error message and re-renders the product detail page with the
        form containing errors.

        :param form: The invalid ReviewForm instance.
        :type form: products.forms.ReviewForm
        :return: An HttpResponse rendering the product
                 detail template with context.
        :rtype: django.http.HttpResponse
        """

        messages.error(
            self.request,
            "Failed to submit review. Please check the errors below."
        )
        return self.get(self.request, *self.args, **self.kwargs)

    def get_success_url(self):
        """
        Returns the URL to redirect to after a successful review submission.

        :return: The URL of the current product's detail page.
        :rtype: str
        """

        return reverse('product_detail', kwargs={'pk': self.object.pk})
