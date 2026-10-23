from django.contrib import admin
from .models import Investor

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact') # Tinanggal natin ang 'image' dito
    search_fields = ('name', 'contact')