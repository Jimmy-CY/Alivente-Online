from django.apps import AppConfig


class AcquisitionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acquisitions"
    verbose_name = "Property Acquisitions"

    def ready(self):
        from . import signals  # noqa: F401
