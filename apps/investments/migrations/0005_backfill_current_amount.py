from django.db import migrations
from django.db.models import Sum


def backfill_current_amount(apps, schema_editor):
    Project = apps.get_model('campaigns', 'Project')
    Investment = apps.get_model('investments', 'Investment')

    totals = dict(
        Investment.objects.values_list('project_id')
        .annotate(total=Sum('amount'))
        .values_list('project_id', 'total')
    )
    for project in Project.objects.all().only('pk', 'current_amount'):
        total = totals.get(project.pk) or 0
        if project.current_amount != total:
            Project.objects.filter(pk=project.pk).update(current_amount=total)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0008_restore_created_at'),
        ('investments', '0004_add_payment_method'),
    ]

    operations = [
        migrations.RunPython(backfill_current_amount, noop),
    ]
