from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum  # IDINAGDAG NATIN ITO PARA SA CALCULATION


class Investment(models.Model):
    investor = models.ForeignKey(
        'investors.Investor', related_name='investments', on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        'campaigns.Project', related_name='investments', on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    shares = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tblinvestments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.investor} -> {self.project} ({self.amount})'

    # --- GINANSYA (PROFIT) ---
    @property
    def profit(self):
        if self.project and hasattr(self.project, 'profit_rate') and self.project.profit_rate:
            return (self.amount * self.project.profit_rate) / 100
        return 0.00
    
    @property
    def total_return(self):
        return self.amount + self.profit

    # --- SHARE PERCENTAGE (Ito yung para sa % sa table) ---
    @property
    def share_percentage(self):
        total_project_shares = Investment.objects.filter(project=self.project).aggregate(Sum('shares'))['shares__sum']
        if total_project_shares and total_project_shares > 0:
            return round((self.shares / total_project_shares) * 100, 2)
        return 0


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    investment = models.ForeignKey(
        Investment, related_name='transactions', on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbltransactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Txn {self.pk} - {self.status}'