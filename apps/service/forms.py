from django import forms
from .models import Review


class CommentsForm(forms.ModelForm):
    content_type = forms.CharField(widget=forms.HiddenInput, initial='content_type')
    object_id = forms.IntegerField(widget=forms.HiddenInput, initial=123)

    class Meta:
        model = Review
        fields = ('review',)
        error_messages = {
            'review': {
                'required': "Please Enter your review before you post."
            },
        }
        widgets = {
            'review': forms.TextInput(
                attrs={'class': 'form', 'placeholder': 'Comment Your Review', 'required': True})
        }
        labels = {
            'review': '',
        }
