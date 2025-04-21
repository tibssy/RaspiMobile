from django import forms
from .models import ShippingAddress
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column
import re
from django.core.validators import RegexValidator, MinLengthValidator


phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

zipcode_regex = RegexValidator(
    regex=r'^[A-Z0-9\s\-]+$',
    message="Invalid characters in ZIP/Postal Code."
)


class ShippingAddressForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=255,
        validators=[
            MinLengthValidator(3, message="Full name seems too short.")
        ],
        widget=forms.TextInput(attrs={'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        validators=[
             phone_regex
        ],
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number (Optional)'})
    )
    address1 = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Street Address'})
    )
    address2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)'})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'City'})
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'State / Province / Region'})
    )
    zipcode = forms.CharField(
        max_length=20,
        validators=[
            MinLengthValidator(3, message="ZIP / Postal code seems too short."),
            zipcode_regex
        ],
        widget=forms.TextInput(attrs={'placeholder': 'ZIP / Postal Code'})
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Country'})
    )

    class Meta:
        model = ShippingAddress
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Shipping Information',
                'full_name',
                'email',
                'phone_number',
                'address1',
                'address2',
                'city',
                 Row(
                     Column('state', css_class='form-group col-md-8 mb-3'),
                     Column('zipcode', css_class='form-group col-md-4 mb-3'),
                 ),
                 'country'
            )
        )

    def clean_full_name(self):
        return self.cleaned_data.get('full_name', '').strip()

    def clean_phone_number(self):
        return self.cleaned_data.get('phone_number', '').strip()

    def clean_zipcode(self):
        zipcode = self.cleaned_data.get('zipcode', '').strip()
        return zipcode.upper()

    def clean_country(self):
        return self.cleaned_data.get('country', '').strip()

    def clean_state(self):
        return self.cleaned_data.get('state', '').strip()

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get("country", "").lower()
        state = cleaned_data.get("state")

        us_variants = ['united states', 'usa', 'us', 'u.s.a.', 'u.s.']

        if country in us_variants:
            if not state:
                self.add_error('state', "State is required for shipments within the United States.")

        return cleaned_data
