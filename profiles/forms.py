"""
Forms for the RaspiMobile 'profiles' application.

Includes the form for creating and editing user shipping addresses.
"""

from django import forms
from django.core.validators import RegexValidator, MinLengthValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column
from .models import ShippingAddress

# Define reusable validators
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. "
            "Up to 15 digits allowed."
)

zipcode_regex = RegexValidator(
    regex=r'^[A-Z0-9\s\-]+$',
    message="Invalid characters in ZIP/Postal Code."
)


class ShippingAddressForm(forms.ModelForm):
    """
    Form for creating and editing ShippingAddress instances.

    Uses ModelForm features and adds custom validation and layout using
    Crispy Forms.
    """

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
        widget=forms.TextInput(
            attrs={'placeholder': 'Phone Number (Optional)'})
    )
    address1 = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Street Address'})
    )
    address2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Apartment, suite, etc. (optional)'})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'City'})
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'State / Province / Region'})
    )
    zipcode = forms.CharField(
        max_length=20,
        validators=[
            MinLengthValidator(3,
                               message="ZIP / Postal code seems too short."),
            zipcode_regex
        ],
        widget=forms.TextInput(attrs={'placeholder': 'ZIP / Postal Code'})
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Country'})
    )

    class Meta:
        """Meta options for the ShippingAddressForm."""

        model = ShippingAddress
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and configure Crispy Forms helper.

        Sets up the layout structure for rendering with {% crispy form %}.
        """

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
        """
        Validate and clean the full_name field.

        Ensures the name contains at least two parts (first and last name)
        and strips leading/trailing whitespace.

        :raises forms.ValidationError: If the name has fewer than two parts.
        :return: The cleaned full name.
        :rtype: str
        """

        full_name = self.cleaned_data.get('full_name', '').strip()
        if full_name and len(full_name.split()) < 2:
            raise forms.ValidationError(
                "Please provide at least a first and last name.")

        return full_name

    def clean_phone_number(self):
        """
        Clean the phone_number field.

        Strips leading/trailing whitespace.

        :return: The cleaned phone number.
        :rtype: str
        """

        return self.cleaned_data.get('phone_number', '').strip()

    def clean_zipcode(self):
        """
        Clean the zipcode field.

        Strips leading/trailing whitespace and converts to uppercase.

        :return: The cleaned and uppercased ZIP/Postal code.
        :rtype: str
        """

        zipcode = self.cleaned_data.get('zipcode', '').strip()
        return zipcode.upper()

    def clean_country(self):
        """
        Clean the country field.

        Strips leading/trailing whitespace.

        :return: The cleaned country name.
        :rtype: str
        """

        return self.cleaned_data.get('country', '').strip()

    def clean_state(self):
        """
        Clean the state field.

        Strips leading/trailing whitespace.

        :return: The cleaned state/province/region name.
        :rtype: str
        """

        return self.cleaned_data.get('state', '').strip()

    def clean(self):
        """
        Perform cross-field validation.

        Specifically checks if 'state' is provided when 'country' is the
        United States (or common variants).

        :return: The dictionary of cleaned data.
        :rtype: dict
        """

        cleaned_data = super().clean()
        country = cleaned_data.get("country", "").lower()
        state = cleaned_data.get("state")

        us_variants = ['united states', 'usa', 'us', 'u.s.a.', 'u.s.']

        if country in us_variants:
            if not state:
                self.add_error(
                    'state',
                    "State is required for shipments within the United States."
                )

        return cleaned_data
