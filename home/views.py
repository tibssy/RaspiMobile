from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from products.models import Product
from django.db.models import Avg, Q
from django.db.models.functions import Coalesce
from .forms import ContactForm


class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        ).exclude(
            image='placeholder'
        ).annotate(
            calculated_average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
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
    template_name = 'home/about.html'
    form_class = ContactForm
    success_url = reverse_lazy('about')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
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
                recipient_list=[admin_email,],
                fail_silently=False,
            )
            messages.success(self.request, 'Thank you for your message! We will get back to you soon.')
        except Exception as e:
            print(f"Error sending email: {e}")
            messages.error(self.request, 'Sorry, there was an error sending your message. Please try again later.')

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below and try again.')
        return super().form_invalid(form)