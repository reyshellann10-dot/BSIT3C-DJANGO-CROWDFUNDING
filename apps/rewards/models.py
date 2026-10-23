from django.db import models


class Reward(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    project = models.ForeignKey('campaigns.Project', on_delete=models.CASCADE, related_name='rewards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblrewards'

    def __str__(self):
        return self.name
