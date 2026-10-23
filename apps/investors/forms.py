from django import forms
from .models import Investor

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = ['name', 'contact', 'address'] # Tinanggal natin ang 'image' dito
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }