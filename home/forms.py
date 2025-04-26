from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'})
    )
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': 5, 'placeholder': 'Your Message'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'name': 'Your Name',
            'email': 'Your Email',
            'subject': 'Subject',
            'message': 'Message',
        }

        self.fields['name'].widget.attrs['aria-label'] = 'Your Name'
        self.fields['email'].widget.attrs['aria-label'] = 'Your Email Address'
        self.fields['subject'].widget.attrs['aria-label'] = 'Subject'
        self.fields['message'].widget.attrs['aria-label'] = 'Your Message'

        for field in self.fields:
            self.fields[field].label = labels[field]
            self.fields[field].widget.attrs['class'] = 'form-control mb-2'
