from django import forms
from .models import Investment

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        # Siguraduhing WALANG 'investor' dito. Project, amount, shares lang.
        fields = ['project', 'amount', 'shares']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1000'}),
            'shares': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10'}),
        }