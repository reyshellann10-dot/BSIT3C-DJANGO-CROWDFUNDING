from django.contrib import admin
from .models import Investment, Transaction

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('investor', 'project', 'amount', 'shares')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('investment', 'amount', 'status')