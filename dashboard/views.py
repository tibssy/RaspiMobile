from django.views.generic import TemplateView, ListView, UpdateView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from products.models import Product
from .forms import ProductForm


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

    def get_success_url(self):
        return reverse_lazy('dashboard_product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'products'
        context['page_title'] = f"Edit: {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Successfully updated product "{form.instance.name}".')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to update product. Please check the form for errors.')
        return super().form_invalid(form)