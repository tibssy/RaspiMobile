from django import forms
from products.models import Product, Category


class ProductForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'price',
            'categories',
            'description',
            'sku',
            'stock_quantity',
            'is_active',
            'is_featured',
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'is_active': 'Product Active (Visible in shop)',
            'is_featured': 'Featured Product (Show on homepage)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            'name': 'Product Name',
            'price': 'Price (e.g., 99.99)',
            'description': 'Detailed product description',
            'sku': 'Stock Keeping Unit (Unique Code)',
            'stock_quantity': 'Number in stock',
        }

        self.fields['name'].widget.attrs['autofocus'] = True

        for field_name, field in self.fields.items():
            if field_name not in ['categories', 'is_active', 'is_featured']:
                if field.required:
                    placeholder = f'{placeholders.get(field_name, "")} *'
                else:
                    placeholder = placeholders.get(field_name, "")
                field.widget.attrs['placeholder'] = placeholder
            if field_name != 'is_active' and field_name != 'is_featured' and not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'form-control'
            if field_name == 'description':
                field.widget.attrs['class'] = 'form-control'