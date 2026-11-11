from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Investment


def sync_project_raised(project_id):
    """Recompute Project.current_amount from this project's investments."""
    if not project_id:
        return
    from apps.campaigns.models import Project

    total = (
        Investment.objects.filter(project_id=project_id).aggregate(t=Sum('amount'))['t']
        or 0
    )
    # .update() avoids re-saving the project (no signal recursion, no
    # updated_at churn from an investment being added).
    Project.objects.filter(pk=project_id).update(current_amount=total)


@receiver(post_save, sender=Investment)
def _investment_saved(sender, instance, **kwargs):
    sync_project_raised(instance.project_id)


@receiver(post_delete, sender=Investment)
def _investment_deleted(sender, instance, **kwargs):
    sync_project_raised(instance.project_id)
