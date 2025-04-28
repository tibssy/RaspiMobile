"""
Defines forms used within the orders application, particularly during checkout.

Includes forms for selecting a delivery method (`DeliveryMethodForm`)
and a formset for handling order item quantities (`OrderItemFormSet` based on
`OrderItemQuantityForm`). Uses django-crispy-forms for layout rendering
where applicable.
"""

from django import forms
from .models import DeliveryMethod
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from products.models import Product
from django.utils.safestring import mark_safe


class DeliveryMethodChoiceField(forms.ModelChoiceField):
    """
    Custom ModelChoiceField that displays delivery method name, price,
    and description in the choice label.
    """

    def label_from_instance(self, obj):
        """
        Generates the label for each delivery method option.

        Includes name, price, and description (if available).
        Uses mark_safe to allow HTML for better formatting within the label.

        :param obj: The DeliveryMethod instance.
        :type obj: DeliveryMethod
        :return: An HTML string representing the choice label.
        :rtype: SafeString
        """
        label_html = f"{obj.name} (+€{obj.price:.2f})"
        if obj.description:
            label_html += f"<br><small class='text-muted'>{obj.description}</small>"
        return mark_safe(label_html)


class DeliveryMethodForm(forms.Form):
    """
    Form for selecting a delivery method during checkout.

    Uses a custom ModelChoiceField (`DeliveryMethodChoiceField`) with a
    RadioSelect widget to display active delivery methods with their
    descriptions.
    """

    delivery_method = DeliveryMethodChoiceField(
        queryset=DeliveryMethod.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        required=True,
        empty_label=None,
        label="Choose Delivery Method"
    )

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and configures its Crispy Forms helper.
        """
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
    """
    A single form within the OrderItemFormSet, representing one item line.

    Contains the quantity and a hidden field for the product ID. Includes
    validation to check quantity against available stock.
    """

    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={'class': 'form-control form-control-sm quantity-input',
                   'min': '1'})
    )
    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        """
        Performs cross-field validation.

        Checks if the requested quantity exceeds the available stock for the
        associated product.

        :return: The cleaned data dictionary.
        :rtype: dict
        """

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
                self.add_error('quantity',
                               f'Only {product.stock_quantity} available.')

        return cleaned_data


OrderItemFormSet = formset_factory(OrderItemQuantityForm, extra=0)
