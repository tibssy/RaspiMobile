from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import ShippingAddress
from .forms import ShippingAddressForm
from django.urls import reverse_lazy


@method_decorator(login_required, name='dispatch')
class EditCreateAddressView(View):
    template_name = 'profiles/edit_create_address.html'
    form_class = ShippingAddressForm
    success_url = reverse_lazy('edit_create_address')

    def get_object(self):
        return ShippingAddress.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        address_form = self.form_class(instance=instance)
        context = {
            'address_form': address_form,
            'existing_address': instance is not None
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        address_form = self.form_class(request.POST, instance=instance)

        if address_form.is_valid():
            try:
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()

                if instance:
                    messages.success(request, "Shipping address updated successfully.")
                else:
                    messages.success(request, "Shipping address saved successfully.")

                return redirect(self.success_url)
            except Exception as e:
                 messages.error(request, "Failed to save address. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")

        context = {
            'address_form': address_form,
            'existing_address': instance is not None
        }

        return render(request, self.template_name, context)