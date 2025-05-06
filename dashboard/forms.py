from django import forms


class EmailConfigurationForm(forms.Form):
    subject = forms.CharField(label="Your subject", max_length=250)
    body = forms.CharField(widget=forms.Textarea)
