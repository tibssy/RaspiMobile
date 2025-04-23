from django import forms
from products.models import Product, Category, SpecificationType, ProductSpecification
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Field, Div
from crispy_forms.bootstrap import AppendedText, PrependedText


class ProductForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    image = forms.ImageField(
        label='Replace current image',
        required=False,
        widget=forms.ClearableFileInput,
        help_text='Select a new image file to replace the current one. Leave blank to keep existing.'
    )

    class Meta:
        model = Product
        fields = [
            'name', 'price', 'image', 'categories', 'description',
            'sku', 'stock_quantity', 'is_active', 'is_featured',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'is_active': 'Product Active (Visible in shop)',
            'is_featured': 'Featured Product (Show on homepage)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'post'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        placeholders = {
            'name': 'Product Name',
            'price': '99.99',
            'description': 'Detailed product description',
            'sku': 'Stock Keeping Unit (Unique Code)',
            'stock_quantity': 'Number in stock',
        }

        self.fields['name'].widget.attrs['autofocus'] = True
        for field_name, field in self.fields.items():
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders.get(field_name, "")

        self.helper.layout = Layout(
            Fieldset(
                'Product Details',
                Row(
                    Column('name', css_class='form-group col-md-6 mb-3'),
                    Column(PrependedText('price', '€', css_class="mb-3"), css_class='form-group col-md-6 mb-3'),
                ),
                Div(
                    HTML("""
                        <label class="form-label d-block mb-2 fw-bold">Product Image</label>
                        <div class="d-flex flex-column flex-md-row align-items-md-start gap-3">
                    """),
                    HTML('{% include "dashboard/partials/product_image_preview.html" with form=form %}'),
                    Column(Field('image'), css_class='flex-grow-1'),
                    HTML("""
                        </div>
                    """),
                    css_class='col-12 mb-3 pb-2 border-bottom'
                ),
                Field('description', css_class='mb-3'),
                Row(
                    Column('sku', css_class='form-group col-md-6 mb-3'),
                    Column('stock_quantity', css_class='form-group col-md-6 mb-3'),
                ),
                Div(
                    Field('categories'),
                    css_class='form-control checkbox-select-multiple-container p-2 mb-3',
                    style='max-height: 150px; overflow-y: auto; border: 1px solid #ced4da; border-radius: 0.375rem;'
                ),
                Row(
                    Column(
                        Field('is_active', css_class='form-check-input'),
                        css_class='form-group col-md-6 mb-3 form-switch pt-1'
                    ),
                    Column(
                        Field('is_featured', css_class='form-check-input'),
                        css_class='form-group col-md-6 mb-3 form-switch pt-1'
                    ),
                )
            )
        )


class ProductSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProductSpecification
        fields = ('spec_type', 'value')
        labels = {
            'spec_type': 'Specification Type (Key)',
            'value': 'Value'
        }
        widgets = {
            'spec_type': forms.Select(attrs={'class': 'form-select mb-2'}),
            'value': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'DELETE': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['spec_type'].queryset = SpecificationType.objects.order_by('name')
        self.fields['spec_type'].empty_label = 'Select Type...'
        self.fields['value'].widget.attrs['placeholder'] = 'Enter specification value'
