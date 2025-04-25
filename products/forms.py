from django import forms
from .models import Review
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=RATING_CHOICES),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write your review here...',
                'class': 'form-control'
            }),
        }
        labels = { 'rating': 'Your Rating', 'comment': 'Your Review', }
        help_texts = { 'rating': None }

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
