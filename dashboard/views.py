from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, CreateView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from cloudinary import uploader
from django.forms import inlineformset_factory
from django.db import transaction, models
from products.models import Product, ProductSpecification, SpecificationType
from orders.models import Order
from .forms import ProductForm, ProductSpecificationForm, OrderStatusForm


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardOverviewView(TemplateView):
    template_name = 'dashboard/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Dashboard"
        context['active_nav'] = 'overview'
        return context


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardProductListView(ListView):
    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
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
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['current_dir'] = self.request.GET.get('dir', 'asc')
        context['active_nav'] = 'products'
        context['page_title'] = "Product Management"
        context['total_product_count'] = self.get_queryset().count()
        return context


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardProductEditView(UpdateView):
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
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['spec_formset'] = self.SpecificationFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='specs')
        else:
            context['spec_formset'] = self.SpecificationFormSet(instance=self.object, prefix='specs')

        context['active_nav'] = 'products'
        context['page_title'] = f"Edit: {self.object.name}"
        context['all_spec_types'] = SpecificationType.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        spec_formset = self.SpecificationFormSet(request.POST, request.FILES, instance=self.object, prefix='specs')

        if form.is_valid() and spec_formset.is_valid():
            return self.form_valid(form, spec_formset)
        else:
            messages.error(self.request, 'Failed to update product. Please check the form for errors.')
            return self.form_invalid(form, spec_formset)

    def form_valid(self, form, spec_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                spec_formset.instance = self.object
                spec_formset.save()

            messages.success(self.request, f'Successfully updated product "{self.object.name}".')
            return super(UpdateView, self).form_valid(form)

        except Exception as e:
            messages.error(self.request, f'An error occurred while saving: {e}')
            return self.form_invalid(form, spec_formset)

    def form_invalid(self, form, spec_formset):
        context = self.get_context_data(form=form, spec_formset=spec_formset)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse_lazy('dashboard_product_list')


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('dashboard_product_list')
    template_name = 'dashboard/product_confirm_delete.html'
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        product_name = self.object.name
        public_id = None

        if self.object.image:
            public_id = self.object.image.public_id

        if public_id and public_id != 'placeholder':
            try:
                result = uploader.destroy(public_id)
            except Exception as e:
                messages.warning(request, f"Product '{product_name}' deleted, but failed to delete image {public_id} from Cloudinary.")

        try:
            self.object.delete()
            messages.success(request, f'Product "{product_name}" was deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting product "{product_name}" from database: {e}')
            return redirect('dashboard_product_edit', pk=self.object.pk)

        return redirect(self.get_success_url())


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardProductCreateView(CreateView):
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
        context = {}
        if self.request.method == 'GET':
            context = super().get_context_data(**kwargs)
            context['spec_formset'] = self.SpecificationFormSet(prefix='specs')
        context['page_title'] = "Add New Product"
        context['active_nav'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        spec_formset = self.SpecificationFormSet(request.POST, request.FILES, prefix='specs')

        if form.is_valid() and spec_formset.is_valid():
            return self.form_valid(form, spec_formset)
        else:
            messages.error(self.request, 'Failed to add product. Please check the form for errors.')
            return self.form_invalid(form, spec_formset)

    def form_valid(self, form, spec_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                spec_formset.instance = self.object
                spec_formset.save()
            messages.success(self.request, f'Product "{self.object.name}" was created successfully.')
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f'An error occurred while saving: {e}')
            return self.form_invalid(form, spec_formset)

    def form_invalid(self, form, spec_formset):
        context = {
            'form': form,
            'spec_formset': spec_formset,
            'page_title': "Add New Product",
            'active_nav': 'products',
        }

        return self.render_to_response(context)


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardOrderListView(ListView):
    model = Order
    template_name = 'dashboard/order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related(
            'items', 'items__product'
        )
        sort_by = self.request.GET.get('sort', '-date_ordered')
        allowed_sort_fields = ['date_ordered', '-date_ordered', 'status', '-status', 'order_number', '-order_number', 'order_total', '-order_total']
        if sort_by not in allowed_sort_fields:
            sort_by = '-date_ordered'
        queryset = queryset.order_by(sort_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-date_ordered')
        context['active_nav'] = 'orders'
        context['page_title'] = 'Order Management'
        context['total_order_count'] = context['paginator'].count
        context['status_form_class'] = OrderStatusForm
        return context


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardUpdateOrderStatusView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        order_pk = kwargs.get('pk')
        order = get_object_or_404(Order, pk=order_pk)
        form = OrderStatusForm(request.POST, instance=order)

        if form.is_valid():
            form.save()
            messages.success(request, f'Status for order {order.order_number} updated successfully.')
        else:
            error_str = ', '.join([f"{field}: {err[0]}" for field, err in form.errors.items()])
            messages.error(request, f'Failed to update status for order {order.order_number}. Error: {error_str}')

        redirect_url = reverse('dashboard_order_list')
        sort_param = request.GET.get('sort')
        if sort_param:
            redirect_url += f'?sort={sort_param}'

        return HttpResponseRedirect(redirect_url)
