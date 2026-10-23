from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0002_alter_project_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='campaigns/'),
        ),
    ]