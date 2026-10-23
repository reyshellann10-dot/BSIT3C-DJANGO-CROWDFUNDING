from django import forms
from .models import Investment

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['investor', 'project', 'amount', 'shares']
        widgets = {
            'investor': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'shares': forms.NumberInput(attrs={'class': 'form-control'}),
        }