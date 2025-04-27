"""
Contact forms for the RaspiMobile home application.

Includes the main contact form used on the About Us page.
"""

from django import forms


class ContactForm(forms.Form):
    """
    A form for users to submit contact inquiries via the website.

    Handles collection of sender's name, email, subject, and message.
    """

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
        """
        Initialize the form and add custom widget attributes.

        Sets placeholders, aria-labels, specific labels, and applies
        Bootstrap's 'form-control' class to all field widgets.
        """

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
