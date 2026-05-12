from django.db import connection, transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import tenant, VacancyPeriod, Recipe, RecipeIngredient, Ingredient, UnitConversion, RecipeNutritionCache
from .nutrition_calc import calculate_recipe_nutrition

@receiver(post_save, sender=tenant)
def manage_vacancy_periods(sender, instance, created, **kwargs):
    """
    Manage VacancyPeriod rows when a tenant lease is saved.

    Strategy: full rebuild for the property in three passes:
      1. Create/update a FILLED vacancy for every gap between consecutive tenants
      2. Delete obsolete FILLED vacancies (a new tenant slotted into a former gap)
      3. Maintain at most one ACTIVE vacancy when the property is currently vacant

    Relies on VacancyPeriod.save() to auto-calculate days_vacant and to flip
    ACTIVE -> FILLED whenever end_date is set, so this handler never sets
    days_vacant manually and never flips status manually.
    """
    from datetime import datetime, timedelta

    # Nothing to manage if this tenant has no lease window
    if not instance.tenant_lease_start_date or not instance.tenant_lease_end_date:
        return

    prop = instance.prop
    today = datetime.now().date()

    tenant_list = list(
        tenant.objects
        .filter(prop=prop)
        .exclude(tenant_lease_start_date__isnull=True)
        .order_by('tenant_lease_start_date')
    )
    if not tenant_list:
        return

    # ---- Pass 1: upsert FILLED vacancies between consecutive tenants ----
    for i in range(len(tenant_list) - 1):
        current = tenant_list[i]
        next_t = tenant_list[i + 1]

        if not (current.tenant_lease_end_date and next_t.tenant_lease_start_date):
            continue

        gap_start = current.tenant_lease_end_date + timedelta(days=1)
        gap_end = next_t.tenant_lease_start_date - timedelta(days=1)

        if gap_start <= gap_end:
            existing = VacancyPeriod.objects.filter(
                prop=prop,
                previous_lease=current,
                next_lease=next_t,
            ).first()
            if existing:
                existing.start_date = gap_start
                existing.end_date = gap_end
                existing.save()  # save() flips status and recomputes days_vacant
            else:
                VacancyPeriod.objects.create(
                    prop=prop,
                    start_date=gap_start,
                    end_date=gap_end,
                    status='FILLED',
                    reason='BETWEEN_TENANTS',
                    previous_lease=current,
                    next_lease=next_t,
                )
        else:
            # No actual gap — wipe any leftover vacancy between this pair
            VacancyPeriod.objects.filter(
                prop=prop,
                previous_lease=current,
                next_lease=next_t,
            ).delete()

    # ---- Pass 2: delete FILLED vacancies that no longer represent a real gap ----
    # (A new tenant may have slotted into a former gap)
    for v in VacancyPeriod.objects.filter(prop=prop, status='FILLED'):
        if not (v.previous_lease_id and v.next_lease_id):
            continue
        if not (v.previous_lease.tenant_lease_end_date and v.next_lease.tenant_lease_start_date):
            continue
        gap_start = v.previous_lease.tenant_lease_end_date + timedelta(days=1)
        gap_end = v.next_lease.tenant_lease_start_date - timedelta(days=1)
        overlapping = tenant.objects.filter(
            prop=prop,
            tenant_lease_start_date__lte=gap_end,
            tenant_lease_end_date__gte=gap_start,
        ).exclude(pk=v.previous_lease_id).exclude(pk=v.next_lease_id).exists()
        if overlapping:
            v.delete()

    # ---- Pass 3: maintain ACTIVE vacancy if the property is currently vacant ----
    is_currently_vacant = True
    for t in tenant_list:
        if t.tenant_lease_start_date <= today and (
            t.tenant_lease_end_date is None or t.tenant_lease_end_date >= today
        ):
            is_currently_vacant = False
            break

    if is_currently_vacant:
        latest = max(
            (t for t in tenant_list if t.tenant_lease_end_date),
            key=lambda t: t.tenant_lease_end_date,
            default=None,
        )
        if latest and latest.tenant_lease_end_date < today:
            already = VacancyPeriod.objects.filter(
                prop=prop,
                previous_lease=latest,
                next_lease__isnull=True,
                status='ACTIVE',
            ).exists()
            if not already:
                VacancyPeriod.objects.create(
                    prop=prop,
                    start_date=latest.tenant_lease_end_date + timedelta(days=1),
                    end_date=None,
                    status='ACTIVE',
                    reason='BETWEEN_TENANTS',
                    previous_lease=latest,
                    next_lease=None,
                )
    else:
        # Not vacant — delete any orphan ACTIVE vacancies
        VacancyPeriod.objects.filter(
            prop=prop,
            status='ACTIVE',
            next_lease__isnull=True,
        ).delete()

def sync_all_historical_vacancies():
    """
    ONE-TIME FUNCTION: Analyze all historical tenants and create vacancy periods.
    
    Run this once after implementing the VacancyPeriod model to populate historical data.
    
    Usage:
        python manage.py shell
        >>> from pages.signals import sync_all_historical_vacancies
        >>> sync_all_historical_vacancies()
    """
    from .models import props, tenant
    from datetime import timedelta
    
    print("Starting historical vacancy sync...")
    vacancies_created = 0
    
    # Process each property
    for property in props.objects.filter(prop_status='Active'):
        print(f"\nProcessing: {property.prop_name}")
        
        # Get all tenants for this property, ordered by lease start date
        property_tenants = tenant.objects.filter(
            prop=property
        ).order_by('tenant_lease_start_date')
        
        if not property_tenants.exists():
            print(f"  ⚠ No tenants found - skipping")
            continue
        
        # Check for gaps between consecutive tenants
        tenant_list = list(property_tenants)
        for i in range(len(tenant_list) - 1):
            current_tenant = tenant_list[i]
            next_tenant = tenant_list[i + 1]
            
            if not current_tenant.tenant_lease_end_date or not next_tenant.tenant_lease_start_date:
                continue
            
            # Calculate gap in days
            gap_days = (next_tenant.tenant_lease_start_date - current_tenant.tenant_lease_end_date).days
            
            if gap_days > 0:
                # There was a vacancy period - create it if it doesn't exist
                vacancy, created = VacancyPeriod.objects.get_or_create(
                    prop=property,
                    start_date=current_tenant.tenant_lease_end_date,
                    end_date=next_tenant.tenant_lease_start_date,
                    defaults={
                        'previous_lease': current_tenant,
                        'next_lease': next_tenant,
                        'reason': 'BETWEEN_TENANTS',
                        'status': 'FILLED'
                    }
                )
                
                if created:
                    print(f"  ✓ Created vacancy: {gap_days} days ({current_tenant.tenant_lease_end_date} to {next_tenant.tenant_lease_start_date})")
                    vacancies_created += 1
                else:
                    print(f"  - Vacancy already exists: {gap_days} days")
        
        # Check if the last tenant's lease has ended (current vacancy)
        last_tenant = tenant_list[-1]
        if (last_tenant.tenant_current == 'No' and 
            last_tenant.tenant_lease_end_date and 
            last_tenant.tenant_lease_end_date < timezone.now().date()):
            
            # Check if active vacancy already exists
            existing = VacancyPeriod.objects.filter(
                prop=property,
                previous_lease=last_tenant,
                status='ACTIVE'
            ).first()
            
            if not existing:
                vacancy = VacancyPeriod.objects.create(
                    prop=property,
                    start_date=last_tenant.tenant_lease_end_date,
                    previous_lease=last_tenant,
                    reason='BETWEEN_TENANTS',
                    status='ACTIVE'
                )
                days_vacant = (timezone.now().date() - last_tenant.tenant_lease_end_date).days
                print(f"  ✓ Created ACTIVE vacancy: {days_vacant} days (since {last_tenant.tenant_lease_end_date})")
                vacancies_created += 1
    
    print(f"\n{'='*60}")
    print(f"Sync complete! Created {vacancies_created} new vacancy periods.")
    print(f"{'='*60}")
    
    # Summary statistics
    total_vacancies = VacancyPeriod.objects.count()
    active_vacancies = VacancyPeriod.objects.filter(status='ACTIVE').count()
    filled_vacancies = VacancyPeriod.objects.filter(status='FILLED').count()
    
    print(f"\nVacancy Statistics:")
    print(f"  Total vacancy periods: {total_vacancies}")
    print(f"  Currently vacant: {active_vacancies}")
    print(f"  Filled vacancies: {filled_vacancies}")
    
    if active_vacancies > 0:
        print(f"\nCurrently Vacant Properties:")
        for vacancy in VacancyPeriod.objects.filter(status='ACTIVE'):
            print(f"  - {vacancy.prop.prop_name}: {vacancy.days_vacant} days (since {vacancy.start_date})")

# ============================================================================
# CORE RECALC FUNCTION
# ============================================================================
 
NUTRITION_FIELDS = {
    'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g',
    'fiber_per_100g', 'sugar_per_100g', 'sodium_per_100g',
    'fdc_id',  # also triggers recalc — covers the "freshly mapped" case
}
 
 
def _recalculate_cache_for_recipe(recipe):
    """
    Run the nutrition calculator for a single recipe and upsert the cache row.
    Safe to call directly from a management command or signal handler.
    """
    try:
        result = calculate_recipe_nutrition(recipe)
    except Exception as exc:
        # Don't let a calculator failure cascade and break the user's save.
        # Log and bail.
        print(f"[nutrition_cache] Skipping recipe {recipe.recipe_id} ({recipe.recipe_name}) — calculator raised: {exc}")
        return
    
    per_100g    = result.get('per_100g', {})
    per_serving = result.get('per_serving', {})
    
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
            'is_complete':         result.get('is_complete', False),
            'mapped_count':        result.get('mapped_count', 0),
            'unmapped_count':      result.get('unmapped_count', 0),
            'unconvertible_count': result.get('unconvertible_count', 0),
        }
    )
 
 
def _recalculate_caches_for_recipes(recipe_qs):
    """Recalculate caches for a queryset of recipes (used by Ingredient/UnitConversion handlers)."""
    for recipe in recipe_qs:
        _recalculate_cache_for_recipe(recipe)
 
 
# ============================================================================
# RECIPE SIGNALS
# ============================================================================
#
# All cache-recompute signals below defer their work via transaction.on_commit().
# Why: when Django saves a Recipe via a ModelForm/FormSet, the parent Recipe.save()
# fires its post_save BEFORE the formset finishes writing child RecipeIngredient
# changes. If we recompute the cache at that moment, the calculator reads a
# half-applied state — which on at least two confirmed cases (Lasagne, Pork
# Belly with Crunchy Crackling) produced 0 cal/100g while the live calc returned
# the correct value. on_commit() pushes the cache write to AFTER the transaction
# fully commits, so the calculator reads the final state.
#
# Querysets are also materialized to lists of IDs BEFORE being deferred. Querysets
# are lazy and would re-execute at on_commit time — by then the IDs we want
# might be different. Materializing now and re-fetching by ID later is safer.
# ============================================================================
 
@receiver(post_save, sender=Recipe)
def recipe_saved__refresh_nutrition_cache(sender, instance, raw, created, **kwargs):
    """
    When a recipe is saved (created or edited), refresh its nutrition cache.
    Skips fixture loads (raw=True). Deferred to on_commit so we read post-
    transaction state, not mid-save state.
    """
    if raw:
        return
    recipe_id = instance.pk
    def _do():
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return
        _recalculate_cache_for_recipe(recipe)
    transaction.on_commit(_do)
 
 
# Recipe deletion is handled by CASCADE on the OneToOne — no explicit handler needed.
 
 
# ============================================================================
# RECIPE INGREDIENT SIGNALS
# ============================================================================
 
@receiver(post_save, sender=RecipeIngredient)
def recipe_ingredient_saved__refresh_parent_recipe(sender, instance, raw, **kwargs):
    """
    When a recipe ingredient is added/changed, refresh the parent recipe's cache.
    Deferred to on_commit so all sibling formset writes have landed first.
    """
    if raw:
        return
    if not instance.recipe_id:
        return
    recipe_id = instance.recipe_id
    def _do():
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return
        _recalculate_cache_for_recipe(recipe)
    transaction.on_commit(_do)
 
 
@receiver(post_delete, sender=RecipeIngredient)
def recipe_ingredient_deleted__refresh_parent_recipe(sender, instance, **kwargs):
    """
    When a recipe ingredient is removed, refresh the parent recipe's cache.
    Wrapped in try/except because the parent Recipe may also be in the process
    of being deleted (cascade delete). Deferred to on_commit so the deletion
    is fully committed before recalc.
    """
    if not instance.recipe_id:
        return
    recipe_id = instance.recipe_id
    def _do():
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            # Parent recipe is being deleted too — cache row will cascade away.
            return
        _recalculate_cache_for_recipe(recipe)
    transaction.on_commit(_do)
 
 
# ============================================================================
# INGREDIENT SIGNALS — only recalc when NUTRITION changed
# ============================================================================
 
@receiver(post_save, sender=Ingredient)
def ingredient_saved__refresh_dependent_recipes(sender, instance, raw, created, update_fields, **kwargs):
    """
    When an ingredient's NUTRITION data changes (mapping to USDA, manual edit
    of per-100g values, etc.), refresh every recipe that uses this ingredient.
    
    Skips when only non-nutrition fields changed (notes, category, default_unit).
    Deferred to on_commit so the ingredient write is fully committed.
    """
    if raw:
        return
    
    # If `update_fields` was passed, we know exactly what changed.
    # If it wasn't, we have to assume nutrition might have changed and recalc.
    if update_fields is not None:
        if not (set(update_fields) & NUTRITION_FIELDS):
            return  # nothing nutrition-related changed
    
    # Materialize the list of affected recipe IDs NOW, before we defer.
    # If we passed the queryset itself to on_commit, it would re-evaluate
    # later and could pick up a different set of rows.
    affected_ids = list(
        Recipe.objects
        .filter(recipe_ingredients__ingredient=instance)
        .values_list('pk', flat=True)
        .distinct()
    )
    if not affected_ids:
        return
    
    def _do():
        recipes = Recipe.objects.filter(pk__in=affected_ids)
        _recalculate_caches_for_recipes(recipes)
    transaction.on_commit(_do)
 
 
# Ingredient deletion: handled by CASCADE on RecipeIngredient. When the
# ingredient is gone, the RecipeIngredient rows go too, which fires the
# RecipeIngredient post_delete handler above.
 
 
# ============================================================================
# UNIT CONVERSION SIGNALS
# ============================================================================
 
@receiver(post_save, sender=UnitConversion)
def unit_conversion_saved__refresh_dependent_recipes(sender, instance, raw, **kwargs):
    """
    When a unit conversion is added/changed, find every recipe that uses
    either the from_unit or to_unit and refresh its cache.
    
    For ingredient-specific conversions, we only need to refresh recipes
    that use that specific ingredient. For generic conversions, we have to
    refresh anything using the affected units.
    
    Deferred to on_commit so the conversion row is fully committed.
    """
    if raw:
        return
    
    if instance.specific_ingredient_id:
        # Ingredient-specific: only recipes using THIS ingredient are affected.
        affected_qs = Recipe.objects.filter(
            recipe_ingredients__ingredient_id=instance.specific_ingredient_id
        )
    else:
        # Generic: recipes using either the from_unit or to_unit.
        affected_qs = Recipe.objects.filter(
            recipe_ingredients__unit_id__in=[instance.from_unit_id, instance.to_unit_id]
        )
    
    affected_ids = list(affected_qs.values_list('pk', flat=True).distinct())
    if not affected_ids:
        return
    
    def _do():
        recipes = Recipe.objects.filter(pk__in=affected_ids)
        _recalculate_caches_for_recipes(recipes)
    transaction.on_commit(_do)
 
 
@receiver(post_delete, sender=UnitConversion)
def unit_conversion_deleted__refresh_dependent_recipes(sender, instance, **kwargs):
    """
    When a unit conversion is deleted, the affected recipes might no longer
    be convertible. Refresh them so is_complete reflects reality.
    
    Deferred to on_commit so the deletion is fully committed.
    """
    if instance.specific_ingredient_id:
        affected_qs = Recipe.objects.filter(
            recipe_ingredients__ingredient_id=instance.specific_ingredient_id
        )
    else:
        affected_qs = Recipe.objects.filter(
            recipe_ingredients__unit_id__in=[instance.from_unit_id, instance.to_unit_id]
        )
    
    affected_ids = list(affected_qs.values_list('pk', flat=True).distinct())
    if not affected_ids:
        return
    
    def _do():
        recipes = Recipe.objects.filter(pk__in=affected_ids)
        _recalculate_caches_for_recipes(recipes)
    transaction.on_commit(_do)

def _run_wcim_recompute():
    """Lazy import to avoid circular imports at module load time."""
    from pages.services.wcim import recompute_recipe_stats
    try:
        recompute_recipe_stats()
    except Exception:
        # We never want a stats-recompute failure to roll back the original
        # save. Swallow and log; user can re-run the management command.
        import logging
        logging.getLogger(__name__).exception("WCIM stats recompute failed")


@receiver(post_save, sender=RecipeIngredient)
@receiver(post_delete, sender=RecipeIngredient)
def schedule_wcim_stats_recompute(sender, **kwargs):
    """
    Schedule a WCIM stats recompute when a recipe's ingredients change.

    Dedupes within a transaction using a connection-level flag so bulk
    operations only trigger one recompute at commit time.
    """
    # Already scheduled on this connection's current transaction? Skip.
    if getattr(connection, "_wcim_recompute_pending", False):
        return
    connection._wcim_recompute_pending = True

    def _run_then_reset():
        try:
            _run_wcim_recompute()
        finally:
            connection._wcim_recompute_pending = False

    transaction.on_commit(_run_then_reset)