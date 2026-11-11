from django.apps import AppConfig


class InvestmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.investments'

    def ready(self):
        # Keep Project.current_amount in step with investment rows.
        from . import signals  # noqa: F401
