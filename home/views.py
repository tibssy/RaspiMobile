"""
Views for the RaspiMobile 'home' application.

This module contains the class-based views responsible for rendering the
main public-facing pages like the homepage and the about/contact page.
"""

from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from products.models import Product
from django.db.models import Avg, Q
from django.db.models.functions import Coalesce
from .forms import ContactForm


class HomeView(TemplateView):
    """
    Renders the main homepage of the RaspiMobile website.

    Displays featured products and top-rated products based on availability
    and reviews.
    """

    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        """
        Adds featured and best-rated products to the template context.

        Filters active, in-stock products, excluding placeholders, calculates
        average ratings, and selects top products based on criteria.

        :param kwargs: Keyword arguments passed to the view.
        :return: Context dictionary with 'featured_products' and
                 'best_rated_products'.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        base_queryset = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        ).exclude(
            image='placeholder'
        ).annotate(
            calculated_average_rating=Avg('reviews__rating',
                                          filter=Q(reviews__is_approved=True))
        )
        featured_products = base_queryset.filter(is_featured=True)[:3]
        featured_pks = list(featured_products.values_list('pk', flat=True))
        best_rated_products = base_queryset.exclude(
            pk__in=featured_pks
        ).filter(
            calculated_average_rating__isnull=False
        ).order_by(
            Coalesce('calculated_average_rating', 0).desc()
        )[:2]

        context['featured_products'] = featured_products
        context['best_rated_products'] = best_rated_products

        return context


class AboutView(FormMixin, TemplateView):
    """
    Renders the "About Us" page and handles the contact form submission.

    Inherits from FormMixin to manage the ContactForm and TemplateView
    to render the static content of the page.
    """

    template_name = 'home/about.html'
    form_class = ContactForm
    success_url = reverse_lazy('about')

    def get_context_data(self, **kwargs):
        """
        Adds the contact form instance to the template context for GET requests.

        :param kwargs: Keyword arguments passed to the view.
        :return: Context dictionary containing the 'contact_form'.
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        context['contact_form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, validating and processing the contact form.

        Calls form_valid if the form is valid, otherwise calls form_invalid.

        :param request: The incoming HTTP POST request.
        :type request: HttpRequest
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: An HttpResponse (either a redirect or re-render).
        :rtype: HttpResponse
        """

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        Processes the valid contact form data, sends an email, and redirects.

        Extracts cleaned data, formats an email message, attempts to send it
        using settings-defined credentials, adds a success message, and
        redirects to the success_url.

        :param form: The validated instance of ContactForm.
        :type form: ContactForm
        :return: An HttpResponseRedirect to the success_url.
        :rtype: HttpResponseRedirect
        """

        name = form.cleaned_data['name']
        from_email = form.cleaned_data['email']
        subject = form.cleaned_data['subject']
        message_body = form.cleaned_data['message']

        email_subject = f"[RaspiMobile Contact Form] - {subject}"
        email_message = (
            f"You have received a new message from your website contact form.\n\n"
            f"Here are the details:\n"
            f"Name: {name}\n"
            f"Email: {from_email}\n\n"
            f"Message:\n{message_body}\n"
        )
        admin_email = settings.EMAIL_HOST_USER

        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[admin_email, ],
                fail_silently=False,
            )
            messages.success(self.request,
                             'Thank you for your message! We will get back to you soon.')
        except Exception as e:
            messages.error(self.request,
                           'Sorry, there was an error sending your message. Please try again later.')

        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles invalid form submissions by re-rendering the page with errors.

        Adds an error message to be displayed to the user and returns the
        response generated by TemplateResponseMixin (re-rendering the template
        with the bound, invalid form instance).

        :param form: The invalid instance of ContactForm containing errors.
        :type form: ContactForm
        :return: An HttpResponse rendering the template with the invalid form.
        :rtype: HttpResponse
        """

        messages.error(self.request,
                       'Please correct the errors below and try again.')
        return super().form_invalid(form)
