from django import forms
from .models import DeliveryMethod
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from products.models import Product


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

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        product_id = cleaned_data.get('product_id')
        product = None

        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                self.add_error('product_id', 'Invalid product selected.')
                return cleaned_data

        if quantity is not None and product is not None:
            if quantity > product.stock_quantity:
                self.add_error('quantity', f'Only {product.stock_quantity} available.')

        return cleaned_data


OrderItemFormSet = formset_factory(OrderItemQuantityForm, extra=0)