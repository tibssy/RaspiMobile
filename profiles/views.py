from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import ShippingAddress
from .forms import ShippingAddressForm
from django.urls import reverse_lazy
from django.contrib.auth import logout


@method_decorator(login_required, name='dispatch')
class ManageProfileView(View):
    template_name = 'profiles/manage_profile.html'
    form_class = ShippingAddressForm
    success_url = reverse_lazy('manage_profile')

    def get_object(self):
        return ShippingAddress.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        address_form = self.form_class(instance=instance)
        context = {
            'page_title': "Manage Profile & Address",
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
            'page_title': "Manage Profile & Address",
            'address_form': address_form,
            'existing_address': instance is not None
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class DeleteAccountView(View):
    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            logout(request)
            user.delete()
            messages.success(request, "Your account has been successfully deleted.")
            return redirect('home')
        except Exception as e:
            messages.error(request, "There was an error deleting your account. Please contact support if the issue persists.")
            return redirect('home')

    def get(self, request, *args, **kwargs):
        messages.error(request, "Invalid request method.")
        return redirect('manage_profile')
