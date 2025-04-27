"""
Defines the views for the staff dashboard application.

This module contains views accessible only to staff users (authenticated users
with `is_staff=True`). It provides functionality for managing products, orders,
reviews, and viewing site statistics and an overview dashboard. Access control
is enforced using the `user_passes_test` decorator.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    UpdateView,
    DeleteView,
    CreateView
)
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from cloudinary import uploader
from django.forms import inlineformset_factory
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, F, FloatField
from django.db.models.functions import TruncDate, Cast
from products.models import (
    Product,
    ProductSpecification,
    SpecificationType,
    Review
)
from orders.models import Order, OrderItem, OrderStatus
from .forms import (
    ProductForm,
    ProductSpecificationForm,
    OrderStatusForm,
    ReviewApprovalForm
)
import json


def is_staff_user(user):
    """
    Checks if the given user is authenticated and has staff privileges.

    Used by the `user_passes_test` decorator to restrict access to dashboard
    views.

    :param user: The user object to check.
    :type user: django.contrib.auth.models.User
    :return: True if the user is authenticated and is_staff is True, False
    otherwise.
    :rtype: bool
    """

    return user.is_authenticated and user.is_staff


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardOverviewView(TemplateView):
    """
    Displays the main dashboard overview page for staff users.

    Shows key statistics like total products, pending orders, pending reviews,
    recent sales totals, and charts for recent daily sales and order status
    distribution.
    """

    template_name = 'dashboard/overview.html'

    def get_context_data(self, **kwargs):
        """
        Populates the context data for the overview template.

        Fetches counts for products, pending orders, pending reviews,
        and recent sales. Generates data for daily sales and order status
        charts. Handles potential database errors gracefully.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['page_title'] = "Dashboard"
        context['active_nav'] = 'overview'

        try:
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            seven_days_ago = today - timedelta(days=7)
            context['total_product_count'] = Product.objects.count()
            context['pending_order_count'] = Order.objects.filter(
                status=OrderStatus.PENDING).count()
            context['pending_review_count'] = Review.objects.filter(
                is_approved=False).count()

            recent_sales = Order.objects.filter(
                date_ordered__date__gte=thirty_days_ago,
                status__in=[
                    OrderStatus.PENDING,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED
                ]
            ).aggregate(total=Sum('order_total'))
            context['recent_sales_total'] = recent_sales.get('total') or 0

            daily_sales_query = Order.objects.filter(
                date_ordered__date__gte=seven_days_ago,
                status__in=[
                    OrderStatus.PENDING,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED
                ]
            ).annotate(
                day=TruncDate('date_ordered')
            ).values('day').annotate(
                total_sales=Sum('order_total')
            ).order_by('day')

            sales_dict = {stat['day']: float(stat['total_sales'] or 0) for stat
                          in daily_sales_query}
            overview_sales_labels = []
            overview_sales_data = []
            for i in range(6, -1, -1):
                current_date = today - timedelta(days=i)
                overview_sales_labels.append(current_date.strftime('%b %d'))
                overview_sales_data.append(sales_dict.get(current_date, 0))

            context['overview_sales_labels'] = json.dumps(
                overview_sales_labels
            )
            context['overview_sales_data'] = json.dumps(
                overview_sales_data
            )
            status_counts = Order.objects.values('status').annotate(
                count=Count('id')).order_by('status')
            status_display_map = dict(OrderStatus.choices)
            overview_status_labels = [
                status_display_map.get(item['status'], item['status']) for item
                in status_counts]
            overview_status_data = [item['count'] for item in status_counts]

            status_colors = {
                OrderStatus.PENDING: 'rgba(255, 193, 7, 0.7)',
                OrderStatus.PROCESSING: 'rgba(13, 202, 240, 0.7)',
                OrderStatus.SHIPPED: 'rgba(13, 110, 253, 0.7)',
                OrderStatus.DELIVERED: 'rgba(25, 135, 84, 0.7)',
                OrderStatus.CANCELLED: 'rgba(220, 53, 69, 0.7)',
                OrderStatus.FAILED: 'rgba(108, 117, 125, 0.7)',
            }
            default_color = 'rgba(150, 150, 150, 0.7)'
            overview_status_colors_list = [
                status_colors.get(item['status'], default_color) for item in
                status_counts]
            context['overview_status_labels'] = json.dumps(
                overview_status_labels)
            context['overview_status_data'] = json.dumps(overview_status_data)
            context['overview_status_colors'] = json.dumps(
                overview_status_colors_list)
        except Exception as e:
            message = (
                "An error occurred while loading dashboard data. "
                "Please try again later."
            )
            messages.error(self.request, message)
            context['total_product_count'] = 0
            context['pending_order_count'] = 0
            context['pending_review_count'] = 0
            context['recent_sales_total'] = 0
            context['overview_sales_labels'] = '[]'
            context['overview_sales_data'] = '[]'
            context['overview_status_labels'] = '[]'
            context['overview_status_data'] = '[]'
            context['overview_status_colors'] = '[]'

        return context


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardProductListView(ListView):
    """
    Displays a paginated list of products for management.

    Allows sorting the product list by name, stock quantity, price,
    or creation date.
    """

    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        """
        Retrieves and sorts the queryset of products based on GET parameters.

        Handles 'sort' and 'dir' GET parameters for sorting logic. Defaults to
        sorting by name ascending.

        :return: A sorted QuerySet of Product objects.
        :rtype: django.db.models.QuerySet
        """

        queryset = super().get_queryset()
        sort_by = self.request.GET.get('sort', 'name')
        direction = self.request.GET.get('dir', 'asc')
        allowed_sort_fields = ['name', 'stock_quantity', 'price', 'created_on']
        if sort_by not in allowed_sort_fields:
            sort_by = 'name'

        order_field = f'-{sort_by}' if direction == 'desc' else sort_by
        queryset = queryset.order_by(order_field)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds sorting parameters and page context to the template context.

        Includes current sort field, direction, active navigation marker,
        page title, and total product count.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['current_dir'] = self.request.GET.get('dir', 'asc')
        context['active_nav'] = 'products'
        context['page_title'] = "Product Management"
        context['total_product_count'] = self.get_queryset().count()
        return context


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardProductEditView(UpdateView):
    """
    Handles the editing of an existing product, including its specifications.

    Uses `ProductForm` for the main product details and an inline formset
    (`SpecificationFormSet`) for managing associated `ProductSpecification`
    objects. Ensures atomicity using a database transaction on save.
    """

    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_edit.html'
    context_object_name = 'product'

    SpecificationFormSet = inlineformset_factory(
        Product,
        ProductSpecification,
        form=ProductSpecificationForm,
        fields=('spec_type', 'value'),
        extra=1,
        can_delete=True
    )

    def get_context_data(self, **kwargs):
        """
        Adds the product specification formset to the template context.

        Initializes the formset with the current product instance or with
        POST data if the form is being re-rendered after submission.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data, including the
        spec_formset.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['spec_formset'] = self.SpecificationFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
                prefix='specs'
            )
        else:
            context['spec_formset'] = self.SpecificationFormSet(
                instance=self.object,
                prefix='specs'
            )

        context['active_nav'] = 'products'
        context['page_title'] = f"Edit: {self.object.name}"
        context['all_spec_types'] = SpecificationType.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for updating the product and its specifications.

        Validates both the main product form and the specification formset.
        Calls `form_valid` or `form_invalid` accordingly.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse, typically a redirect on success or re-render
        on failure.
        :rtype: django.http.HttpResponse
        """

        self.object = self.get_object()
        form = self.get_form()
        spec_formset = self.SpecificationFormSet(
            request.POST,
            request.FILES,
            instance=self.object,
            prefix='specs'
        )

        if form.is_valid() and spec_formset.is_valid():
            return self.form_valid(form, spec_formset)
        else:
            messages.error(
                self.request,
                'Failed to update product. Please check the form for errors.'
            )
            return self.form_invalid(form, spec_formset)

    def form_valid(self, form, spec_formset):
        """
        Saves the valid product form and specification formset within a
        transaction.

        Adds a success message and redirects to the success URL. Handles
        potential exceptions during saving.

        :param form: The valid main product form instance.
        :type form: ProductForm
        :param spec_formset: The valid specification inline formset instance.
        :type spec_formset: SpecificationFormSet
        :return: An HttpResponseRedirect to the success URL.
        :rtype: django.http.HttpResponseRedirect
        """

        try:
            with transaction.atomic():
                self.object = form.save()
                spec_formset.instance = self.object
                spec_formset.save()

            messages.success(
                self.request,
                f'Successfully updated product "{self.object.name}".'
            )
            return super(UpdateView, self).form_valid(form)

        except Exception as e:
            messages.error(
                self.request,
                f'An error occurred while saving: {e}'
            )
            return self.form_invalid(form, spec_formset)

    def form_invalid(self, form, spec_formset):
        """
        Re-renders the edit page with the invalid forms and error messages.

        :param form: The invalid main product form instance.
        :type form: ProductForm
        :param spec_formset: The invalid or valid specification inline formset
        instance.
        :type spec_formset: SpecificationFormSet
        :return: An HttpResponse rendering the edit template with context.
        :rtype: django.http.HttpResponse
        """

        context = self.get_context_data(form=form, spec_formset=spec_formset)
        return self.render_to_response(context)

    def get_success_url(self):
        """
        Returns the URL to redirect to after successful product update.

        :return: The URL for the product list view.
        :rtype: str
        """

        return reverse_lazy('dashboard_product_list')


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardProductDeleteView(DeleteView):
    """
    Handles the deletion of a product.

    Includes logic to attempt deletion of the associated image from Cloudinary
    before deleting the product record from the database.
    """

    model = Product
    success_url = reverse_lazy('dashboard_product_list')
    template_name = 'dashboard/product_confirm_delete.html'
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        """
        Processes the deletion of the product upon confirmation (POST request).

        Retrieves the product object, attempts to delete its associated
        Cloudinary image (if applicable and not the placeholder), deletes the
        product record from the database, and adds appropriate success/error
        messages. Redirects to the success URL upon successful
        database deletion.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Keyword arguments containing the primary
                 key ('pk') of the product.
        :return: An HttpResponseRedirect to the success_url on success, or
                 a redirect back to the edit view if database deletion fails.
        :rtype: django.http.HttpResponseRedirect
        """

        self.object = self.get_object()
        product_name = self.object.name
        public_id = None

        if self.object.image:
            public_id = self.object.image.public_id

        if public_id and public_id != 'placeholder':
            try:
                result = uploader.destroy(public_id)
            except Exception as e:
                message = (
                    f"Product '{product_name}' deleted, but failed to "
                    f"delete image {public_id} from Cloudinary."
                )
                messages.warning(request, message)

        try:
            self.object.delete()
            messages.success(
                request,
                f'Product "{product_name}" was deleted successfully.'
            )
        except Exception as e:
            messages.error(
                request,
                f'Error deleting product "{product_name}" from database: {e}'
            )
            return redirect('dashboard_product_edit', pk=self.object.pk)

        return redirect(self.get_success_url())


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardProductCreateView(CreateView):
    """
    Handles the creation of a new product, including its specifications.

    Uses `ProductForm` and an inline formset (`SpecificationFormSet`).
    Ensures atomicity using a database transaction on save.
    """

    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_add.html'
    success_url = reverse_lazy('dashboard_product_list')

    SpecificationFormSet = inlineformset_factory(
        Product,
        ProductSpecification,
        form=ProductSpecificationForm,
        fields=('spec_type', 'value'),
        extra=1,
        can_delete=False
    )

    def get_context_data(self, **kwargs):
        """
        Adds the specification formset to the template context for
        GET requests.

        Initializes an empty formset when the page is first loaded.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data, including the
                 spec_formset.
        :rtype: dict
        """

        context = {}
        if self.request.method == 'GET':
            context = super().get_context_data(**kwargs)
            context['spec_formset'] = self.SpecificationFormSet(prefix='specs')
        context['page_title'] = "Add New Product"
        context['active_nav'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for creating the product and its specifications.

        Validates both the main product form and the specification formset.
        Calls `form_valid` or `form_invalid` accordingly.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: An HttpResponse, typically a redirect on success or re-render
                 on failure.
        :rtype: django.http.HttpResponse
        """

        form = self.get_form()
        spec_formset = self.SpecificationFormSet(
            request.POST,
            request.FILES,
            prefix='specs'
        )

        if form.is_valid() and spec_formset.is_valid():
            return self.form_valid(form, spec_formset)
        else:
            messages.error(
                self.request,
                'Failed to add product. Please check the form for errors.'
            )
            return self.form_invalid(form, spec_formset)

    def form_valid(self, form, spec_formset):
        """
        Saves the new product and its specifications within a transaction.

        Assigns the newly created product instance to the formset before
        saving it. Adds a success message and redirects to the success URL.

        :param form: The valid main product form instance.
        :type form: ProductForm
        :param spec_formset: The valid specification inline formset instance.
        :type spec_formset: SpecificationFormSet
        :return: An HttpResponseRedirect to the success URL.
        :rtype: django.http.HttpResponseRedirect
        """

        try:
            with transaction.atomic():
                self.object = form.save()
                spec_formset.instance = self.object
                spec_formset.save()
            messages.success(
                self.request,
                f'Product "{self.object.name}" was created successfully.'
            )
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(
                self.request,
                f'An error occurred while saving: {e}'
            )
            return self.form_invalid(form, spec_formset)

    def form_invalid(self, form, spec_formset):
        """
        Re-renders the creation page with the invalid forms and error messages.

        Ensures both the main form and the formset are passed to the context.

        :param form: The invalid main product form instance.
        :type form: ProductForm
        :param spec_formset: The invalid or valid specification inline
                 formset instance.
        :type spec_formset: SpecificationFormSet
        :return: An HttpResponse rendering the creation template with context.
        :rtype: django.http.HttpResponse
        """

        context = {
            'form': form,
            'spec_formset': spec_formset,
            'page_title': "Add New Product",
            'active_nav': 'products',
        }

        return self.render_to_response(context)


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardOrderListView(ListView):
    """
    Displays a paginated list of orders for management.

    Allows sorting orders by date, status, order number, or total.
    Includes functionality to update order status directly from the list view.
    """

    model = Order
    template_name = 'dashboard/order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        """
        Retrieves and sorts the queryset of orders based on GET parameters.

        Optimizes database queries by selecting related user and prefetching
        items and their products. Handles 'sort' GET parameter.

        :return: A sorted and optimized QuerySet of Order objects.
        :rtype: django.db.models.QuerySet
        """

        queryset = Order.objects.select_related('user').prefetch_related(
            'items', 'items__product'
        )
        sort_by = self.request.GET.get('sort', '-date_ordered')
        allowed_sort_fields = [
            'date_ordered',
            '-date_ordered',
            'status',
            '-status',
            'order_number',
            '-order_number',
            'order_total',
            '-order_total'
        ]
        if sort_by not in allowed_sort_fields:
            sort_by = '-date_ordered'
        queryset = queryset.order_by(sort_by)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds sorting parameters, pagination info, and status form class to
        the context.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-date_ordered')
        context['active_nav'] = 'orders'
        context['page_title'] = 'Order Management'
        context['total_order_count'] = context['paginator'].count
        context['status_form_class'] = OrderStatusForm
        return context


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardUpdateOrderStatusView(View):
    """
    Handles POST requests to update the status of a specific order.

    Uses `OrderStatusForm` to validate and save the status change.
    Redirects back to the order list, preserving sorting parameters.
    """

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        """
        Processes the POST request to update an order's status.

        Retrieves the order, validates the submitted status using
        OrderStatusForm, saves the change if valid, and redirects back to
        the order list.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Keyword arguments, expected to contain 'pk'
                 (order primary key).
        :return: An HttpResponseRedirect back to the order list.
        :rtype: django.http.HttpResponseRedirect
        """

        order_pk = kwargs.get('pk')
        order = get_object_or_404(Order, pk=order_pk)
        form = OrderStatusForm(request.POST, instance=order)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Status for order {order.order_number} updated successfully.'
            )
        else:
            error_str = ', '.join(
                [f"{field}: {err[0]}" for field, err in form.errors.items()]
            )
            message = (
                f'Failed to update status for order {order.order_number}. '
                f'Error: {error_str}'
            )
            messages.error(request, message)

        redirect_url = reverse('dashboard_order_list')
        sort_param = request.GET.get('sort')
        if sort_param:
            redirect_url += f'?sort={sort_param}'

        return HttpResponseRedirect(redirect_url)


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardReviewListView(ListView):
    """
    Displays a paginated list of product reviews for management.

    Allows filtering reviews by approval status (pending, approved, all)
    and sorting by creation date, rating, product, or user. Includes
    functionality for approving/unapproving reviews.
    """

    model = Review
    template_name = 'dashboard/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        """
        Retrieves, filters, and sorts the queryset of reviews based on GET
        parameters.

        Optimizes database queries by selecting related user and product.
        Handles 'status' GET parameter for filtering and 'sort' for sorting.

        :return: A filtered, sorted, and optimized QuerySet of Review objects.
        :rtype: django.db.models.QuerySet
        """

        queryset = Review.objects.select_related('user', 'product')
        filter_status = self.request.GET.get('status', 'pending')

        if filter_status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif filter_status == 'pending':
            queryset = queryset.filter(is_approved=False)

        sort_by = self.request.GET.get('sort', '-created_on')
        allowed_sort_fields = [
            'created_on',
            '-created_on',
            'rating',
            '-rating',
            'product__name',
            'user__username'
        ]
        if sort_by not in allowed_sort_fields:
            sort_by = '-created_on'

        queryset = queryset.order_by(sort_by)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds sorting, filtering parameters, and approval form to the context.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-created_on')
        context['current_status_filter'] = self.request.GET.get(
            'status',
            'pending'
        )
        context['active_nav'] = 'comments'
        context['page_title'] = 'Review Management'
        context['total_review_count'] = context['paginator'].count
        context['approval_form'] = ReviewApprovalForm()
        return context


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardReviewToggleApprovalView(View):
    """
    Handles POST requests to toggle the approval status of a specific review.

    Redirects back to the review list, preserving filter, sort, and
    pagination state.
    """

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        """
        Processes the POST request to toggle a review's approval status.

        Retrieves the review, flips its `is_approved` status, saves
        the change, and redirects back to the review list with appropriate
        query parameters.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Keyword arguments, expected to contain 'pk'
                 (review primary key).
        :return: An HttpResponseRedirect back to the review list.
        :rtype: django.http.HttpResponseRedirect
        """

        review_pk = kwargs.get('pk')
        review = get_object_or_404(Review, pk=review_pk)
        review.is_approved = not review.is_approved
        review.save(update_fields=['is_approved', 'updated_on'])
        action = 'approved' if review.is_approved else 'unapproved'
        message = (
            f'Review for "{review.product.name}" '
            f'by {review.user.username} has been {action}.'
        )
        messages.success(request, message)
        redirect_url = reverse('dashboard_review_list')
        status_filter = request.POST.get('status_filter')
        sort_param = request.POST.get('sort')
        page_num = request.POST.get('page')

        params = {}
        if status_filter:
            params['status'] = status_filter
        if sort_param:
            params['sort'] = sort_param
        if page_num:
            params['page'] = page_num

        if params:
            from urllib.parse import urlencode
            redirect_url += f'?{urlencode(params)}'

        return HttpResponseRedirect(redirect_url)


@method_decorator(
    user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')),
    name='dispatch')
class DashboardStatisticsView(TemplateView):
    """
    Displays various statistics charts for the dashboard.

    Handles both the initial page load (rendering the template with
    initial data) and AJAX requests to fetch updated chart data based on
    selected date ranges.
    """

    template_name = 'dashboard/statistics.html'

    def get_start_date(self, range_param):
        """
        Calculates the start date based on the selected range parameter.

        :param range_param: The range identifier ('10', '30', 'all').
        :type range_param: str
        :return: The calculated start date, or None if range is 'all'.
        :rtype: datetime.date or None
        """

        today = timezone.now().date()
        if range_param == '30':
            return today - timedelta(days=30)
        elif range_param == '10':
            return today - timedelta(days=10)
        else:
            return None

    def get_chart_data(self, chart_id, range_param):
        """
        Fetches and processes data for a specific chart and date range.

        Supports 'sales', 'orders', and 'topProducts' charts. Filters
        data based on the calculated start date. Aggregates and formats data
        suitable for Chart.js.

        :param chart_id: The identifier of the chart
                 ('sales', 'orders', 'topProducts').
        :type chart_id: str
        :param range_param: The date range identifier
                 ('10', '30', 'all').
        :type range_param: str
        :return: A dictionary containing 'labels' and 'data'
                 lists for the chart.
        :rtype: dict
        :raises SuspiciousOperation: If an invalid chart_id is requested.
        """

        start_date = self.get_start_date(range_param)
        order_qs = Order.objects.all()
        order_item_qs = OrderItem.objects.all()

        if start_date:
            order_qs = order_qs.filter(date_ordered__date__gte=start_date)
            order_item_qs = order_item_qs.filter(
                order__date_ordered__date__gte=start_date
            )

        if chart_id == 'sales' or chart_id == 'orders':
            daily_stats_query = order_qs.annotate(
                day=TruncDate('date_ordered')).values('day').annotate(
                total_sales=Sum('order_total'),
                order_count=Count('id')).order_by('day')
            stats_dict = {stat['day']: {
                'sales': stat['total_sales'], 'count': stat['order_count']
            } for stat in daily_stats_query}
            chart_labels = []
            sales_data = []
            order_count_data = []
            date_format = '%b %d, %Y' if range_param == 'all' else '%b %d'

            if start_date:
                days_in_range = (timezone.now().date() - start_date).days
                for i in range(days_in_range, -1, -1):
                    current_date = timezone.now().date() - timedelta(days=i)
                    chart_labels.append(current_date.strftime(date_format))
                    if current_date in stats_dict:
                        sales_data.append(
                            float(stats_dict[current_date]['sales'])
                        )
                        order_count_data.append(
                            stats_dict[current_date]['count']
                        )
                    else:
                        sales_data.append(0)
                        order_count_data.append(0)
            else:
                for stat in daily_stats_query:
                    chart_labels.append(stat['day'].strftime(date_format))
                    sales_data.append(float(stat['total_sales']))
                    order_count_data.append(stat['order_count'])

            if chart_id == 'sales':
                return {'labels': chart_labels, 'data': sales_data}
            else:
                return {'labels': chart_labels, 'data': order_count_data}

        elif chart_id == 'topProducts':
            top_products_query = (
                order_item_qs.values('product__name')
                .annotate(total_revenue=Sum(
                    F('quantity') * Cast(F('price'), FloatField())
                ))
                .order_by('-total_revenue')[:10]
            )
            top_product_labels = [item['product__name'] for item in
                                  top_products_query][::-1]
            top_product_revenue = [item['total_revenue'] for item in
                                   top_products_query][::-1]
            return {'labels': top_product_labels, 'data': top_product_revenue}
        else:
            raise SuspiciousOperation(
                f"Invalid chart_id requested: {chart_id}"
            )

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests.

        If 'fetch=true' GET parameter is present, it acts as an API endpoint
        to return JSON chart data based on 'chart_id' and 'range' parameters.
        Otherwise, it renders the statistics page template with initial
        chart data.

        :param request: The HttpRequest object.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse if fetch=true, otherwise HttpResponse rendering
                 the template.
        :rtype: django.http.JsonResponse | django.http.HttpResponse
        """

        if request.GET.get('fetch') == 'true':
            chart_id = request.GET.get('chart_id')
            range_param = request.GET.get('range', '30')
            if chart_id not in ['sales', 'orders', 'topProducts']:
                return JsonResponse({'error': 'Invalid chart ID'}, status=400)
            if range_param not in ['10', '30', 'all']:
                range_param = '30'

            try:
                chart_data = self.get_chart_data(chart_id, range_param)
                return JsonResponse(chart_data)
            except Exception as e:
                return JsonResponse(
                    {'error': 'Failed to fetch chart data'},
                    status=500
                )

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """
        Populates the context data for the initial statistics page load.

        Fetches initial data for all charts using the default range ('30').
        Handles potential errors during initial data fetching.

        :param kwargs: Keyword arguments passed to the view.
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['page_title'] = "Dashboard Statistics"
        context['active_nav'] = 'statistics'
        initial_range = '30'
        context['current_range'] = initial_range
        context['range_title_suffix'] = "(Last 30 Days)"

        try:
            sales_initial = self.get_chart_data(
                'sales',
                initial_range
            )
            orders_initial = self.get_chart_data(
                'orders',
                initial_range
            )
            top_products_initial = self.get_chart_data(
                'topProducts',
                initial_range
            )

            context['chart_labels'] = json.dumps(
                sales_initial.get('labels', [])
            )
            context['sales_data'] = json.dumps(
                sales_initial.get('data', [])
            )
            context['order_count_data'] = json.dumps(
                orders_initial.get('data', [])
            )
            context['top_product_labels'] = json.dumps(
                top_products_initial.get('labels', [])
            )
            context['top_product_revenue'] = json.dumps(
                top_products_initial.get('data', [])
            )
        except Exception as e:
            messages.error(self.request, "Could not load initial chart data.")

            context['chart_labels'] = '[]'
            context['sales_data'] = '[]'
            context['order_count_data'] = '[]'
            context['top_product_labels'] = '[]'
            context['top_product_revenue'] = '[]'

        return context
