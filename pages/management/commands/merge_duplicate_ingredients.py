"""
Management command: merge_duplicate_ingredients

Merges known duplicate ingredient rows by repointing every reverse FK from
the source ingredient to the target, then deleting the source.

Discovers reverse FK relations automatically via Ingredient._meta.related_objects,
so any future model with an FK to Ingredient (RecipeModificationSuggestion etc.)
is handled without code changes here.

Handles unique_together conflicts (e.g. PantryStaple's unique (user, ingredient))
by dropping the source row when the user already has the target.

Wrapped in a single transaction — any error rolls everything back.
Idempotent — already-merged sources are skipped with a warning.

Usage:
    python manage.py merge_duplicate_ingredients
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from pages.models import Ingredient


# (source_id, target_id, description)
# Source = duplicate to delete after repointing FKs.
# Target = canonical row to keep.
MERGES = [
    (1,   172, "Eggs (1) → Egg (172)"),
    (75,  197, "Basil (75) → Basil Leaves (197)"),
    (371, 323, "Cilantro, Fresh (371) → Coriander, Fresh (323)"),
    (194, 370, "Corn, Canned (194) → Sweetcorn, Canned (370)"),
    (154, 264, "Nando's Lemon And Herb (154) → Nando's Lemon & Herb (264)"),
]


class Command(BaseCommand):
    help = "Merge known duplicate ingredients. Idempotent and transactional."

    @transaction.atomic
    def handle(self, *args, **options):
        for source_id, target_id, description in MERGES:
            self.stdout.write(f"\nProcessing: {description}")

            source = Ingredient.objects.filter(ingredient_id=source_id).first()
            if not source:
                self.stdout.write(self.style.WARNING(
                    f"  Source ID {source_id} not in DB — already merged or never existed. Skipping."
                ))
                continue

            target = Ingredient.objects.filter(ingredient_id=target_id).first()
            if not target:
                self.stdout.write(self.style.WARNING(
                    f"  Target ID {target_id} not in DB — skipping this merge "
                    "(expected on local dev with small dataset)."
                ))
                continue

            # Discover every reverse FK to Ingredient and repoint it
            for rel in Ingredient._meta.related_objects:
                related_model = rel.related_model
                fk_name = rel.field.name

                qs = related_model.objects.filter(**{fk_name: source})
                count = qs.count()
                if count == 0:
                    continue

                # Find unique_together constraints involving this FK
                unique_constraints = [
                    ut for ut in related_model._meta.unique_together
                    if fk_name in ut
                ]

                if unique_constraints:
                    # Row-by-row: check for conflict before repointing
                    repointed = 0
                    dropped = 0
                    for obj in qs:
                        conflict = False
                        for ut in unique_constraints:
                            other_fields = [f for f in ut if f != fk_name]
                            filter_kwargs = {f: getattr(obj, f) for f in other_fields}
                            filter_kwargs[fk_name] = target
                            if related_model.objects.filter(**filter_kwargs).exists():
                                conflict = True
                                break
                        if conflict:
                            obj.delete()
                            dropped += 1
                        else:
                            setattr(obj, fk_name, target)
                            obj.save(update_fields=[fk_name])
                            repointed += 1
                    self.stdout.write(
                        f"  {related_model.__name__}.{fk_name}: "
                        f"repointed {repointed}, dropped {dropped} conflicts"
                    )
                else:
                    # No unique constraints — bulk update
                    qs.update(**{fk_name: target})
                    self.stdout.write(
                        f"  {related_model.__name__}.{fk_name}: repointed {count}"
                    )

            source_name = source.name
            source.delete()
            self.stdout.write(self.style.SUCCESS(
                f"  Deleted source '{source_name}' (ID {source_id})"
            ))

        # Final count check
        remaining = Ingredient.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\nAll merges complete. {remaining} ingredients remain in DB."
        ))

        # Recompute WCIM stats — bulk .update() bypassed the post_save signal
        # on RecipeIngredient, so the stored idf and weighted_total values are
        # now stale relative to the new ingredient relationships.
        self.stdout.write("\nRecomputing WCIM stats (IDF + weighted_total)...")
        from pages.services.wcim import recompute_recipe_stats
        stats = recompute_recipe_stats()
        self.stdout.write(self.style.SUCCESS(
            f"  Updated {stats['ingredients_updated']} ingredients, "
            f"{stats['recipes_updated']} recipes ({stats['elapsed_ms']} ms)."
        ))