"""Keep scores in step with facts and rules automatically."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Criterion, Property, ScenarioMatch
from .scoring import apply_score


@receiver(post_save, sender=Property)
def rescore_property(sender, instance, **kwargs):
    for match in instance.matches.select_related("scenario"):
        apply_score(match)


@receiver(post_save, sender=Criterion)
@receiver(post_delete, sender=Criterion)
def rescore_scenario(sender, instance, **kwargs):
    matches = ScenarioMatch.objects.filter(scenario_id=instance.scenario_id)
    for match in matches.select_related("scenario", "property"):
        apply_score(match)
