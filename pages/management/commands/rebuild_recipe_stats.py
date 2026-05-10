"""
Management command: rebuild_recipe_stats

Recomputes IDF for every Ingredient and weighted_total for every Recipe.
Run once after the WCIM Phase 1a migration. Safe to re-run anytime.

Usage:
    python manage.py rebuild_recipe_stats
"""
from django.core.management.base import BaseCommand

from pages.services.wcim import recompute_recipe_stats


class Command(BaseCommand):
    help = "Recompute IDF + weighted_total stats used by the What Can I Make? matching engine."

    def handle(self, *args, **options):
        self.stdout.write("Recomputing WCIM stats...")
        stats = recompute_recipe_stats()

        if stats["recipes"] == 0:
            self.stdout.write(self.style.WARNING("No recipes found. Nothing to do."))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Updated {stats['ingredients_updated']} ingredients with document_frequency + idf"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Updated {stats['recipes_updated']} recipes with weighted_total"
        ))
        self.stdout.write(f"Done in {stats['elapsed_ms']}ms")