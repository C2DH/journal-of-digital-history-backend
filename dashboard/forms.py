from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit




class EmailConfigurationForm(forms.Form):
    subject= forms.CharField(label='Your subject', max_length=250)
    body= forms.CharField(widget=forms.Textarea)