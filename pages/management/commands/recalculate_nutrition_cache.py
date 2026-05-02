"""
============================================================================
SAVE THIS FILE AS:
    pages/management/commands/recalculate_nutrition_cache.py
============================================================================

This file goes alongside your existing management commands. The folder
should already exist (you mentioned `pages/management/commands/` earlier
with the cron-job command).

Once saved, run:
    python manage.py recalculate_nutrition_cache

Optional flags:
    --recipe-id 123       : only recalculate one specific recipe
    --only-stale          : only recalculate recipes whose cache is missing
                            (skips already-cached rows — useful when re-running)
    --quiet               : suppress per-recipe output (final summary only)
============================================================================
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from pages.models import Recipe, RecipeNutritionCache
from pages.nutrition_calc import calculate_recipe_nutrition


class Command(BaseCommand):
    help = "Recalculate the RecipeNutritionCache for all recipes (or a single recipe)."
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--recipe-id',
            type=int,
            help='Only recalculate this specific recipe ID.',
        )
        parser.add_argument(
            '--only-stale',
            action='store_true',
            help='Skip recipes that already have a cache row (only fill gaps).',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress per-recipe progress output.',
        )
    
    def handle(self, *args, **options):
        recipe_id = options.get('recipe_id')
        only_stale = options.get('only_stale', False)
        quiet = options.get('quiet', False)
        
        # Build the queryset
        recipes = Recipe.objects.all()
        if recipe_id is not None:
            recipes = recipes.filter(recipe_id=recipe_id)
            if not recipes.exists():
                self.stderr.write(self.style.ERROR(f"No recipe with recipe_id={recipe_id}"))
                return
        
        if only_stale:
            cached_ids = RecipeNutritionCache.objects.values_list('recipe_id', flat=True)
            recipes = recipes.exclude(recipe_id__in=cached_ids)
        
        total = recipes.count()
        if total == 0:
            self.stdout.write("No recipes to process.")
            return
        
        self.stdout.write(f"Recalculating nutrition cache for {total} recipe(s)…")
        
        succeeded = 0
        failed = 0
        complete_count = 0
        partial_count = 0
        empty_count = 0
        
        for idx, recipe in enumerate(recipes.iterator(), start=1):
            try:
                with transaction.atomic():
                    result = calculate_recipe_nutrition(recipe)
                    
                    per_100g = result.get('per_100g', {})
                    per_serving = result.get('per_serving', {})
                    is_complete = result.get('is_complete', False)
                    has_any_data = result.get('has_any_data', False)
                    
                    RecipeNutritionCache.objects.update_or_create(
                        recipe=recipe,
                        defaults={
                            'calories_per_100g': per_100g.get('calories'),
                            'protein_per_100g':  per_100g.get('protein'),
                            'carbs_per_100g':    per_100g.get('carbs'),
                            'fat_per_100g':      per_100g.get('fat'),
                            'fiber_per_100g':    per_100g.get('fiber'),
                            'sugar_per_100g':    per_100g.get('sugar'),
                            'sodium_per_100g':   per_100g.get('sodium'),
                            
                            'calories_per_serving': per_serving.get('calories'),
                            'protein_per_serving':  per_serving.get('protein'),
                            'carbs_per_serving':    per_serving.get('carbs'),
                            'fat_per_serving':      per_serving.get('fat'),
                            'fiber_per_serving':    per_serving.get('fiber'),
                            'sugar_per_serving':    per_serving.get('sugar'),
                            'sodium_per_serving':   per_serving.get('sodium'),
                            
                            'total_weight_g':      result.get('total_weight_g'),
                            'is_complete':         is_complete,
                            'mapped_count':        result.get('mapped_count', 0),
                            'unmapped_count':      result.get('unmapped_count', 0),
                            'unconvertible_count': result.get('unconvertible_count', 0),
                        }
                    )
                
                succeeded += 1
                if is_complete:
                    complete_count += 1
                elif has_any_data:
                    partial_count += 1
                else:
                    empty_count += 1
                
                if not quiet:
                    status = "✓" if is_complete else ("~" if has_any_data else "·")
                    self.stdout.write(
                        f"  [{idx}/{total}] {status} {recipe.recipe_name} "
                        f"(mapped {result.get('mapped_count', 0)}, "
                        f"unmapped {result.get('unmapped_count', 0)}, "
                        f"unconvertible {result.get('unconvertible_count', 0)})"
                    )
            
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.WARNING(
                    f"  [{idx}/{total}] ✗ {recipe.recipe_name} (id={recipe.recipe_id}) — error: {exc}"
                ))
        
        # Final summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. {succeeded} succeeded, {failed} failed."))
        self.stdout.write(f"  Complete (sortable):  {complete_count}")
        self.stdout.write(f"  Partial data:         {partial_count}")
        self.stdout.write(f"  No nutrition data:    {empty_count}")