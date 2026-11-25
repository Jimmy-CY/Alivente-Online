"""Keep scores in step with facts and rules automatically.

RA27, 25 Nov 2026 - ONE RE-SCORE PER SAVE. Saving a scenario saves each of
its rules, and each rule saved re-scored every listing the scenario tracks:
ten rules and 826 plots made eight thousand evaluations in one request.
The scenario editor now saves its rules inside quiet() and re-scores once,
after the last one (Scenario.rescore_all).
"""
import threading

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Criterion, Property, ScenarioMatch
from .scoring import apply_score


@receiver(post_save, sender=Property)
def rescore_property(sender, instance, **kwargs):
    for match in instance.matches.select_related("scenario"):
        apply_score(match)


_held = threading.local()


class quiet:
    """Hold the per-rule re-scoring while a whole set of rules is saved."""

    def __enter__(self):
        _held.n = getattr(_held, "n", 0) + 1
        return self

    def __exit__(self, *exc):
        _held.n -= 1
        return False


def is_quiet():
    return getattr(_held, "n", 0) > 0


@receiver(post_save, sender=Criterion)
@receiver(post_delete, sender=Criterion)
def rescore_scenario(sender, instance, **kwargs):
    if is_quiet():
        return
    matches = ScenarioMatch.objects.filter(scenario_id=instance.scenario_id)
    for match in matches.select_related("scenario", "property"):
        apply_score(match)
