from django import forms
from .models import Investment

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        # investor is assigned programmatically in the view — never from the form
        fields = ['project', 'amount', 'shares', 'payment_method']
        widgets = {
            'project':        forms.Select(attrs={'class': 'form-control'}),
            'amount':         forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1000'}),
            'shares':         forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }