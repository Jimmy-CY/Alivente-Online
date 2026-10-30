from django.apps import AppConfig


class WellnessConfig(AppConfig):
    """WL-1, 30 Oct 2026 - the Wellness module.

    ITS OWN APP, AND OUTSIDE THE HOUSE STANDARD ON PURPOSE. Demetri's
    decision of 29 Oct: Wellness is the one module not held to the house
    design. Its templates live in wellness/templates, which is NOT one of
    alv_tree.TEMPLATE_ROOTS, so the house suites never walk them; its own
    suite (test_wellness_one.py) is what holds it to account.

    ONE PERSON, ONE WELLNESS. Every row belongs to one login and every
    query is filtered by request.user - superusers included. Nobody sees
    anyone else's data (decision 1, 30 Oct).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wellness'
    verbose_name = 'Wellness'

    def ready(self):
        # Connects the login signal that stamps the main app's hour.
        from . import session  # noqa: F401
