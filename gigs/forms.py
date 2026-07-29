from django import forms

from .models import Gig


class GigForm(forms.ModelForm):
    class Meta:
        model = Gig
        exclude = ['poster']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError('Title is required.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError('Description is required.')
        return description

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget <= 0:
            raise forms.ValidationError('Budget must be greater than 0.')
        return budget
