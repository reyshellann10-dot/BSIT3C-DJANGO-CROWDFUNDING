"""Make tblinvestors.contact / .address nullable in the database.

Migration 0004 already declares both fields as ``blank=True, null=True``, but the
live MySQL table still has them as ``NOT NULL`` (0004 was likely applied with
--fake, or the table predates it). Django's state therefore looks correct while
the schema is not, so an Investor created without a contact/address raised
``IntegrityError: Column 'contact' cannot be null``.

AlterField would be a no-op here because the recorded state already says null,
so the ALTER statements are issued explicitly.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('investors', '0006_add_user_to_investor'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE tblinvestors MODIFY contact varchar(50) NULL DEFAULT NULL;",
                "ALTER TABLE tblinvestors MODIFY address longtext NULL;",
            ],
            # Going back to NOT NULL would fail on any row holding NULL, and the
            # model allows NULL anyway, so the reverse is a deliberate no-op.
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
