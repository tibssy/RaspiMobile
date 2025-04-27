"""
Views for the RaspiMobile 'profiles' application.

Handles user profile management, including viewing/editing shipping addresses
and account deletion. All views require the user to be logged in.
"""

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
    """
    Manages the user's profile page, focusing on shipping address.

    Allows logged-in users to view, add, or edit their default shipping
    address. Also serves as the page containing the trigger for account
    deletion.
    """

    template_name = 'profiles/manage_profile.html'
    form_class = ShippingAddressForm
    success_url = reverse_lazy('manage_profile')

    def get_object(self):
        """
        Retrieves the first shipping address associated with the current user.

        :return: The ShippingAddress instance or None if not found.
        :rtype: ShippingAddress or None
        """

        return ShippingAddress.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests: Displays the address form.

        Pre-populates the form with the user's existing address if available.

        :param request: The incoming HTTP GET request.
        :type request: HttpRequest
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: An HttpResponse rendering the manage profile template.
        :rtype: HttpResponse
        """

        instance = self.get_object()
        address_form = self.form_class(instance=instance)
        context = {
            'page_title': "Manage Profile & Address",
            'address_form': address_form,
            'existing_address': instance is not None
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests: Processes the submitted shipping address form.

        Validates the form. If valid, saves or updates the address and
        redirects. If invalid, re-renders the page with errors.

        :param request: The incoming HTTP POST request.
        :type request: HttpRequest
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: An HttpResponse (redirect or re-render).
        :rtype: HttpResponse
        """

        instance = self.get_object()
        address_form = self.form_class(request.POST, instance=instance)

        if address_form.is_valid():
            try:
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()

                if instance:
                    messages.success(request,
                                     "Shipping address updated successfully.")
                else:
                    messages.success(request,
                                     "Shipping address saved successfully.")

                return redirect(self.success_url)
            except Exception as e:
                messages.error(request,
                               "Failed to save address. Please try again.")
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
    """
    Handles the permanent deletion of a user's account via POST request.
    """

    def post(self, request, *args, **kwargs):
        """
        Processes the account deletion request.

        Logs the user out, deletes the user object (cascading to related
        data like ShippingAddress), displays a success message, and redirects
        to the homepage.

        :param request: The incoming HTTP POST request.
        :type request: HttpRequest
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: An HttpResponseRedirect to the homepage.
        :rtype: HttpResponseRedirect
        """

        user = request.user
        try:
            logout(request)
            user.delete()
            messages.success(
                request,
                "Your account has been successfully deleted."
            )
            return redirect('home')
        except Exception as e:
            message = (
                "There was an error deleting your account. "
                "Please contact support if the issue persists."
            )
            messages.error(request, message)
            return redirect('home')

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests by redirecting away.

        Account deletion should only be triggered by a POST request from the
        confirmation modal.

        :param request: The incoming HTTP GET request.
        :type request: HttpRequest
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: An HttpResponseRedirect to the manage profile page.
        :rtype: HttpResponseRedirect
        """

        messages.error(request, "Invalid request method.")
        return redirect('manage_profile')
