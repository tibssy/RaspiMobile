from django import forms
from .models import Review
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '1'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write your review here...',
                'class': 'form-control'
            }),
        }
        labels = {
            'rating': 'Your Rating (1-5)',
            'comment': 'Your Review',
        }
        help_texts = {
            'rating': None
        }

    def save(self, commit=True):
        review = super().save(commit=False)
        analyzer = SentimentIntensityAnalyzer()
        comment_text = review.comment
        vs = analyzer.polarity_scores(comment_text)
        review.is_approved = vs['compound'] >= 0.05

        if commit:
            review.save()

        return review

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
