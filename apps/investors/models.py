from django.conf import settings
from django.db import models


class Investor(models.Model):
    # Link to Django's auth User (optional — null for existing records)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='investor_profile',
        help_text='The login account linked to this investor profile.'
    )

    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Ito ang nag-aayos ng error sa database
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        db_table = 'tblinvestors'
        ordering = ['name']

    def __str__(self):
        return self.name