from django.core.validators import MinValueValidator
from django.db import models

class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Farmer Details
    farmer_name = models.CharField(max_length=100, blank=True, null=True)
    crop_type = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Palay, Mais, Gulay")
    location = models.CharField(max_length=100, blank=True, null=True)

    # Existing fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    class Meta:
        db_table = 'tblprojects'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # --- MGA PROPERTIES PARA SA PROGRESS BAR ---
    @property
    def total_raised(self):
        return self.investments.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            progress = (self.total_raised / self.target_amount) * 100
            return round(min(progress, 100), 1)
        return 0