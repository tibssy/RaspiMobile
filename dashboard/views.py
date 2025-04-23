from django.views.generic import TemplateView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@method_decorator(user_passes_test(is_staff_user, login_url=reverse_lazy('account_login')), name='dispatch')
class DashboardOverviewView(TemplateView):
    template_name = 'dashboard/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Dashboard"
        return context