from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0002_alter_project_id'),
    ]

    operations = [
        # 'image' is already created by 0001_initial; adding it again breaks
        # fresh databases (Duplicate column name 'image').
        migrations.AlterField(
            model_name='project',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='campaigns/'),
        ),
    ]