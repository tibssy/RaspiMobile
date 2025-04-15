from django import forms
from .models import ShippingAddress, DeliveryMethod
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        exclude = []
        widgets = {
            'address2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, unit, etc. (optional)'}),
            'state': forms.TextInput(attrs={'placeholder': 'State / Province / Region'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Shipping Information',
                'full_name',
                'email',
                'phone_number',
                'address1',
                'address2',
                'city',
                'state',
                'zipcode',
                'country'
            )
        )


class DeliveryMethodForm(forms.Form):
    delivery_method = forms.ModelChoiceField(
        queryset=DeliveryMethod.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        required=True,
        empty_label=None,
        label="Choose Delivery Method"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
             Fieldset(
                'Delivery Options',
                'delivery_method'
            )
        )


class OrderItemQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm quantity-input', 'min': '1'})
    )
    product_id = forms.IntegerField(widget=forms.HiddenInput())


OrderItemFormSet = formset_factory(OrderItemQuantityForm, extra=0)