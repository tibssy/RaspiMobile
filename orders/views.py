from django.shortcuts import render
from django.views import View


class CreateOrderView(View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        return render(request, self.template_name)