from django.db import models

class Investor(models.Model):
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