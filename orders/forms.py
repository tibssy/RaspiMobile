from django import forms
from .models import DeliveryMethod
from profiles.models import ShippingAddress
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset


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
        self.helper.form_tag = False
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