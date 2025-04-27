"""
Defines forms used within the products application.

Includes the form for submitting product reviews (`ReviewForm`), which also
incorporates basic sentiment analysis for automatic approval suggestions.
"""

from django import forms
from .models import Review
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    """
    Form for users to submit product reviews (rating and comment).

    Uses RadioSelect for the rating and Textarea for the comment.
    Overrides the save method to perform sentiment analysis on the comment
    to set the initial `is_approved` status based on positivity.
    """

    class Meta:
        """
        Metaclass options for the ReviewForm.
        """

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
        labels = {'rating': 'Your Rating', 'comment': 'Your Review'}
        help_texts = {'rating': None}

    def save(self, commit=True):
        """
        Overrides the default save method to include sentiment analysis.

        Calculates the sentiment polarity of the review comment using VADER.
        Sets `is_approved` to True if the compound sentiment score is
        non-negative (>= 0.05 threshold used here), suggesting automatic
        approval for positive reviews.

        :param commit: If True, saves the instance to the database.
                       Default is True.
        :type commit: bool
        :return: The saved (or unsaved if commit=False) Review instance.
        :rtype: products.models.Review
        """

        review = super().save(commit=False)
        analyzer = SentimentIntensityAnalyzer()
        comment_text = review.comment
        vs = analyzer.polarity_scores(comment_text)
        review.is_approved = vs['compound'] >= 0.05

        if commit:
            review.save()

        return review
