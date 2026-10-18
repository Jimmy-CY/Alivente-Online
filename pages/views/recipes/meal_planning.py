"""
Meal-plan management for recipes.

Owns the meal-plan CRUD / calendar / shopping-list endpoints plus the shared
ingredient-aggregation helper that powers meal-plan shopping lists.

Functions
---------
- aggregate_meal_plan_ingredients : Shared helper (no request). Walks every
                                    recipe in a meal plan, converts each
                                    ingredient to its shopping unit (via the
                                    conversion layer in recipes/conversions.py),
                                    smart-rounds UP, and reports missing
                                    conversions / missing shopping units /
                                    recipe lines with no unit at all.
                                    MP-1, 18 Oct 2026: returns a FOUR-tuple -
                                    the fourth element is new and was dropped
                                    silently before.
- meal_plans                      : List all meal plans. Read-tier.
- create_meal_plan                : Create a meal plan. Edit-tier.
- view_meal_plan                  : View one meal plan. Read-tier.
- delete_meal_plan                : Delete a meal plan (POST). Edit-tier.
- edit_meal_plan                  : Edit a meal plan. Edit-tier.
- duplicate_meal_plan             : Duplicate / shift a meal plan. Edit-tier.
- meal_plan_calendar              : Month/week calendar view. Read-tier.
- meal_plan_shopping_list         : Render a meal plan's shopping list. Read-tier.
- add_recipe_to_meal_plan_day     : Add a recipe to a day (POST). Edit-tier.
- remove_recipe_from_meal_plan    : Remove a recipe from a day (POST). Edit-tier.
- send_meal_plan_shopping_list    : Email a meal plan's shopping list (POST).
                                    Edit-tier.

Auth tiers
----------
Read-tier  -> auth.can_access_recipes
Edit-tier  -> auth.can_edit_recipes
aggregate_meal_plan_ingredients is an undecorated internal helper (correct -
it is not a view).

Cross-module
------------
aggregate_meal_plan_ingredients calls convert_quantity and
get_conversion_cache from recipes/conversions.py (Phase 5); imported
explicitly below. If those symbols live elsewhere the failure is a loud
ImportError on Django startup - caught instantly, no silent corruption.

Encoding note (Phase 10)
------------------------
The original send_meal_plan_shopping_list (and one comment in meal_plans)
carried corrupted multi-byte glyphs - decorative emoji in the email
subject/body that had been mojibake-mangled in the source, the same class of
defect as the production cron-email bug. Per the project's hardened
ASCII-only resolution those decorative glyphs were replaced with clean ASCII.
NO behavioral content (quantities, categories, ingredient data, recipients,
control flow) was altered - those parts were pure ASCII and are byte-faithful.
Each replacement is tagged with an inline "NOTE (Phase 10 ASCII):" comment.
Decorative emoji can be reinstated later as ASCII-safe \\N{...} escapes if
wanted.

aggregate_meal_plan_ingredients carries its own nested round_shopping_qty,
duplicating recipes/shopping.py:round_shopping_quantity. Preserved as-is for
byte-faithfulness; flagged as a post-split dedupe candidate.
"""

import json
import math
import traceback
from calendar import monthcalendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Count, Max, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
# MP-1, 18 Oct 2026 - B9. The shopping-list email interpolated every
# value straight into HTML.
from django.utils.html import escape
from django.views.decorators.http import require_POST

from pages.models import (
    CustomProtein,
    HouseholdMember,
    MealPlan,
    MealPlanDay,
    MealPlanRecipe,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
)

from .conversions import convert_quantity, get_conversion_cache


# =====================================================================
# SHARED HELPER - INGREDIENT AGGREGATION
# =====================================================================

def aggregate_meal_plan_ingredients(meal_plan):
    """
    Aggregate ingredients and convert to shopping units.
    Always uses the ingredient's shopping unit. Prompts for missing conversions.

    Returns a FOUR-tuple:

        (aggregated_dict, missing_conversions, missing_shopping_units,
         missing_units)

    MP-1, 18 Oct 2026 - C16. `missing_units` is new: recipe ingredient
    lines that carry no unit at all. They were dropped silently.
    """

    def smart_categorize(ingredient_name):
        """Intelligently categorize ingredients based on name"""
        ingredient_lower = ingredient_name.lower()

        canned_terms = ['stock', 'broth', 'cube', 'bouillon', 'canned', 'tinned', 'tin', 'paste', 'sauce', 'puree', 'concentrate']
        for term in canned_terms:
            if term in ingredient_lower:
                return 'Canned & Packaged'

        beverages = ['wine', 'beer', 'sherry', 'brandy', 'rum', 'vodka', 'whiskey', 'liqueur']
        for term in beverages:
            if term in ingredient_lower:
                return 'Beverages'

        herbs_spices = ['oregano', 'origanum', 'basil', 'thyme', 'rosemary', 'sage', 'parsley', 'cilantro', 'pepper', 'salt', 'paprika', 'cumin', 'turmeric', 'cinnamon', 'nutmeg', 'cloves', 'curry', 'chili', 'cayenne']
        for term in herbs_spices:
            if term in ingredient_lower:
                return 'Herbs & Spices'

        meats = ['beef', 'pork', 'chicken', 'lamb', 'mince', 'meat', 'bacon', 'sausage', 'fish', 'salmon', 'tuna', 'shrimp', 'prawns']
        for term in meats:
            if term in ingredient_lower:
                return 'Meat & Seafood'

        dairy = ['milk', 'cream', 'yogurt', 'cheese', 'butter']
        is_beverage = any(bev in ingredient_lower for bev in beverages)
        if not is_beverage:
            for term in dairy:
                if term in ingredient_lower:
                    return 'Dairy'

        oils_fats = ['oil', 'olive oil', 'vegetable oil', 'butter', 'margarine', 'lard', 'ghee']
        for term in oils_fats:
            if term in ingredient_lower:
                return 'Oils & Fats'

        grains = ['flour', 'rice', 'pasta', 'spaghetti', 'noodles', 'bread', 'quinoa', 'couscous', 'oats', 'macaroni']
        for term in grains:
            if term in ingredient_lower:
                return 'Grains & Pasta'

        vegetables = ['onion', 'garlic', 'tomato', 'potato', 'carrot', 'celery', 'pepper', 'lettuce', 'spinach', 'broccoli', 'mushroom', 'peas', 'corn']
        for term in vegetables:
            if term in ingredient_lower:
                return 'Vegetables'

        return 'Other'

    def round_shopping_qty(qty, unit):
        """
        Round quantities intelligently based on unit type for shopping lists.
        NEVER rounds down - always rounds UP to ensure you have enough.
        """
        if qty <= 0:
            return qty

        unit_type = getattr(unit, 'unit_type', 'other')

        if unit_type == 'count':
            # Always round UP to whole number, minimum 1
            return max(1, math.ceil(qty))

        elif unit_type == 'weight':
            # Round UP to sensible numbers based on magnitude
            if qty < 10:
                return math.ceil(qty * 2) / 2
            elif qty < 100:
                return math.ceil(qty / 5) * 5
            else:
                return math.ceil(qty / 10) * 10

        elif unit_type == 'volume':
            # Round UP to sensible numbers based on magnitude
            if qty < 10:
                return math.ceil(qty * 4) / 4
            elif qty < 100:
                return math.ceil(qty / 5) * 5
            else:
                return math.ceil(qty / 10) * 10

        else:
            # OTHER (dash, pinch, to taste): round UP
            return max(1, math.ceil(qty))

    def get_unit_display(unit, qty):
        """Get the proper unit display with pluralization"""
        if qty == 1:
            return unit.abbreviation or unit.name
        else:
            return unit.abbreviation_plural or unit.abbreviation or unit.name_plural or unit.name

    # Pre-load all unit conversions for fast lookups (prevents N+1 queries)
    conversion_cache = get_conversion_cache()

    # Track issues
    missing_conversions = []
    missing_shopping_units = []
    # MP-1, 18 Oct 2026 - C16. A recipe line with NO UNIT at all was
    # dropped by `if not from_unit: continue` below and recorded
    # nowhere: not in the list, not in a warning, not in a log. The
    # other two drops at least left a trace. This is the trace.
    missing_units = []
    seen_missing_conversions = set()
    seen_missing_units = set()
    seen_no_unit = set()

    # Dictionary: ingredient_id -> {amount, unit, ingredient_obj, unconverted_items}
    aggregated = defaultdict(lambda: {
        'unit': None,
        'amount': Decimal('0'),
        'ingredient_obj': None,
        'unconverted_items': []  # Items that couldn't be converted
    })

    # Process all recipes in meal plan
    for day in meal_plan.days.all().order_by('date'):
        for meal_recipe in day.recipes.all():
            recipe = meal_recipe.recipe
            servings_multiplier = Decimal(meal_recipe.servings) / Decimal(recipe.servings or 1)

            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                ingredient_id = ingredient.ingredient_id
                quantity = Decimal(recipe_ingredient.amount or 0) * servings_multiplier
                from_unit = recipe_ingredient.unit

                if not from_unit:
                    # MP-1, 18 Oct 2026 - C16. Was a bare `continue`.
                    # The ingredient left the shopping list and nothing
                    # anywhere said so.
                    if ingredient_id not in seen_no_unit:
                        seen_no_unit.add(ingredient_id)
                        missing_units.append({
                            'ingredient_id': ingredient_id,
                            'ingredient_name': ingredient.name,
                            'recipe': recipe.recipe_name,
                        })
                    continue

                # CRITICAL: Always use the ingredient's shopping unit
                shopping_unit = ingredient.default_unit

                # Track ingredients without shopping units
                if not shopping_unit:
                    if ingredient_id not in seen_missing_units:
                        seen_missing_units.add(ingredient_id)
                        missing_shopping_units.append({
                            'ingredient_id': ingredient_id,
                            'ingredient_name': ingredient.name,
                            'recipe': recipe.recipe_name
                        })
                    # Add to unconverted items
                    if ingredient_id not in aggregated:
                        aggregated[ingredient_id]['ingredient_obj'] = ingredient
                        aggregated[ingredient_id]['unit'] = from_unit  # Fallback

                    aggregated[ingredient_id]['unconverted_items'].append({
                        'quantity': float(quantity),
                        'unit': from_unit.name,
                        'recipe': recipe.recipe_name,
                        'reason': 'No shopping unit defined'
                    })
                    continue

                # Initialize if first time seeing this ingredient
                if aggregated[ingredient_id]['unit'] is None:
                    aggregated[ingredient_id]['unit'] = shopping_unit
                    aggregated[ingredient_id]['ingredient_obj'] = ingredient

                shopping_unit = aggregated[ingredient_id]['unit']

                # Convert to shopping unit
                if from_unit.measurement_unit_id == shopping_unit.measurement_unit_id:
                    # Same unit - just add
                    aggregated[ingredient_id]['amount'] += quantity
                else:
                    # Need conversion - USE CACHE for fast lookup
                    converted_qty, multiplier = convert_quantity(quantity, from_unit, shopping_unit, ingredient, conversion_cache)

                    if converted_qty is not None:
                        # Conversion successful
                        aggregated[ingredient_id]['amount'] += converted_qty
                    else:
                        # NO CONVERSION EXISTS - Track it
                        conversion_key = f"{from_unit.measurement_unit_id}-{shopping_unit.measurement_unit_id}"
                        if conversion_key not in seen_missing_conversions:
                            seen_missing_conversions.add(conversion_key)
                            missing_conversions.append({
                                'ingredient': ingredient.name,
                                'from_unit': from_unit.name,
                                'from_unit_id': from_unit.measurement_unit_id,
                                'to_unit': shopping_unit.name,
                                'to_unit_id': shopping_unit.measurement_unit_id,
                                'quantity': float(quantity),
                                'recipe': recipe.recipe_name
                            })

                        # Add to unconverted items
                        aggregated[ingredient_id]['unconverted_items'].append({
                            'quantity': float(quantity),
                            'unit': from_unit.name,
                            'recipe': recipe.recipe_name,
                            'reason': f'Missing conversion from {from_unit.name} to {shopping_unit.name}'
                        })

    # Build categorized shopping list
    categorized_ingredients = defaultdict(list)

    for ingredient_id in sorted(aggregated.keys(), key=lambda x: aggregated[x]['ingredient_obj'].name):
        data = aggregated[ingredient_id]
        ingredient_obj = data['ingredient_obj']
        unit = data['unit']

        # Determine category
        if ingredient_obj and ingredient_obj.category:
            category = ingredient_obj.category.name
        else:
            category = smart_categorize(ingredient_obj.name)

        # Only add to shopping list if we successfully converted some amount
        if data['amount'] > 0:
            # Apply smart rounding for shopping
            raw_qty = float(data['amount'])
            qty = round_shopping_qty(raw_qty, unit)

            # Get proper unit display with pluralization
            unit_display = get_unit_display(unit, qty)

            entry = {
                'ingredient': ingredient_obj.name,
                'quantity': qty,
                'unit': unit_display
            }

            # Add note about unconverted items
            if data['unconverted_items']:
                entry['has_unconverted'] = True
                entry['unconverted_count'] = len(data['unconverted_items'])
                entry['unconverted_items'] = data['unconverted_items']

            categorized_ingredients[category].append(entry)

    # MP-1, 18 Oct 2026 - C16. A FOURTH ELEMENT, and the one caller
    # updated with it. Folding the no-unit lines into
    # missing_shopping_units would have been smaller and would have
    # made that name a lie: those are two different faults with two
    # different fixes - one is a recipe to correct, one is an
    # ingredient to configure - and the page says so separately.
    return (dict(categorized_ingredients), missing_conversions,
            missing_shopping_units, missing_units)


# =====================================================================
# MEAL PLAN CRUD
# =====================================================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plans(request):
    """List all meal plans"""

    # Get all meal plans with recipe counts, sorted by most recent first
    meal_plans_list = MealPlan.objects.annotate(
        recipe_count=Count('days__recipes')
    ).order_by('-start_date')  # NOTE (Phase 10 ASCII): orders newest first

    context = {
        'meal_plans': meal_plans_list,
    }

    return render(request, 'meal_plans.html', context)


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def create_meal_plan(request):
    """Create a new meal plan"""

    if request.method == 'POST':
        try:
            # MP-1, 18 Oct 2026 - C20. .strip(), and a name is
            # REQUIRED. Edit has refused a blank name since it was
            # written; Create accepted one, so the list could carry a
            # plan with no name on it and no way to tell two apart.
            plan_name = request.POST.get('plan_name', '').strip()
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            if not plan_name:
                messages.error(request, 'Plan name is required.')
                return redirect('create_meal_plan')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            days_diff = (end_date - start_date).days + 1
            if days_diff < 1 or days_diff > 7:
                messages.error(request, 'Meal plan must be between 1 and 7 days.')
                return redirect('create_meal_plan')

            # MP-1, 18 Oct 2026 - C17. A WARNING, NOT A REFUSAL. Two
            # plans over the same dates are allowed and the calendar
            # can only show one of them for a week, so the second
            # one's meals are invisible there. Refusing the overlap
            # would be a new rule nobody asked for; saying so is what
            # the design record asks for, and the calendar now says it
            # too.
            clash = MealPlan.objects.filter(
                start_date__lte=end_date, end_date__gte=start_date
            ).order_by('start_date').first()
            if clash:
                messages.warning(
                    request,
                    'These dates overlap "%s" (%s to %s). Both plans are '
                    'kept, but the calendar can only show one plan for a '
                    'week.' % (clash.plan_name,
                               clash.start_date.strftime('%d %b'),
                               clash.end_date.strftime('%d %b %Y')))

            # MP-1, 18 Oct 2026 - C14. ONE TRANSACTION. There was
            # exactly one transaction.atomic() in this module and it
            # was in Edit, so a bad recipe id - or any error part way
            # down the week - left a plan with some of its days and
            # some of its meals, and the message said the create had
            # failed. Duplicate had the same hole and is fixed the
            # same way.
            with transaction.atomic():
                meal_plan = MealPlan.objects.create(
                    plan_name=plan_name,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=request.user
                )

                current_date = start_date
                while current_date <= end_date:
                    meal_day = MealPlanDay.objects.create(
                        meal_plan=meal_plan,
                        date=current_date
                    )

                    date_key = current_date.strftime('%Y-%m-%d')
                    recipe_ids = request.POST.getlist(f'recipes_{date_key}[]')
                    servings_list = request.POST.getlist(f'servings_{date_key}[]')

                    for idx, recipe_id in enumerate(recipe_ids):
                        if recipe_id:
                            recipe = Recipe.objects.get(recipe_id=recipe_id)
                            servings = int(servings_list[idx]) if idx < len(servings_list) else recipe.servings

                            MealPlanRecipe.objects.create(
                                meal_plan_day=meal_day,
                                recipe=recipe,
                                servings=servings,
                                sort_order=idx
                            )

                    current_date += timedelta(days=1)

            messages.success(request, f'Meal plan "{plan_name}" created successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan.meal_plan_id)

        except Exception as e:
            print(f"\n!!! ERROR: {str(e)} !!!")
            traceback.print_exc()
            messages.error(request, f'Error creating meal plan: {str(e)}')
            return redirect('create_meal_plan')

    # GET request - show form
    recipes_qs = Recipe.objects.prefetch_related(
        'courses', 'categories', 'proteins'
    ).all().order_by('recipe_name')

    recipes = []
    for recipe in recipes_qs:
        recipes.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'servings': recipe.servings,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'difficulty_level': recipe.difficulty_level or '',
            'is_vegetarian': recipe.is_vegetarian,
            'author': recipe.author,
            'recipe_image': recipe.photo_url,
            'courses': [course.name for course in recipe.courses.all()],
            'categories': [cat.name for cat in recipe.categories.all()],
            'proteins': [protein.name for protein in recipe.proteins.all()]
        })

    all_courses = list(RecipeCourse.objects.all().order_by('name').values('recipe_course_id', 'name'))
    all_categories = list(RecipeCategory.objects.all().order_by('name').values('recipe_category_id', 'name'))
    all_proteins = list(CustomProtein.objects.all().order_by('name').values('custom_protein_id', 'name'))

    # MP-1, 18 Oct 2026 - B12. The model's own choices. This list was
    # typed out by hand in three places, including recipe_crud.py, and
    # Recipe.author validates against AUTHOR_CHOICES - so a name added
    # to the model never reached any of the three pickers.
    all_authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]

    today = datetime.now().date()
    default_end = today + timedelta(days=6)

    user_favourite_ids = list(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )

    context = {
        'edit_mode': False,
        'recipes_json': json.dumps(recipes),
        'all_courses_json': json.dumps(all_courses),
        'all_categories_json': json.dumps(all_categories),
        'all_proteins_json': json.dumps(all_proteins),
        'all_authors_json': json.dumps(all_authors),
        'user_favourite_ids_json': json.dumps(user_favourite_ids),
        'today': today,
        'default_start_date': today.strftime('%Y-%m-%d'),
        'default_end_date': default_end.strftime('%Y-%m-%d'),
    }

    return render(request, 'create_meal_plan.html', context)


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def view_meal_plan(request, meal_plan_id):
    """View a meal plan with all days and recipes"""

    # Get meal plan with optimized prefetch
    meal_plan = get_object_or_404(
        MealPlan.objects.prefetch_related(
            Prefetch(
                'days',
                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        queryset=MealPlanRecipe.objects.select_related('recipe')
                    )
                )
            )
        ),
        meal_plan_id=meal_plan_id
    )

    # Days are already prefetched and ordered
    days = meal_plan.days.all()

    user_favourites = set(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )

    context = {
        'meal_plan': meal_plan,
        'days': days,
        'user_favourites': user_favourites,
    }

    return render(request, 'view_meal_plan.html', context)


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def delete_meal_plan(request, meal_plan_id):
    """Delete a meal plan"""

    # Only allow POST requests for deletion
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('meal_plans')

    try:
        meal_plan = MealPlan.objects.get(meal_plan_id=meal_plan_id)
        plan_name = meal_plan.plan_name

        # Delete the meal plan (cascade will delete days and recipes)
        meal_plan.delete()

        messages.success(request, f'Meal plan "{plan_name}" has been deleted successfully.')

    except MealPlan.DoesNotExist:
        messages.error(request, 'Meal plan not found.')

    # Check where to redirect
    redirect_to = request.POST.get('redirect_to', 'list')
    if redirect_to == 'calendar':
        return redirect('meal_plan_calendar')
    return redirect('meal_plans')


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def edit_meal_plan(request, meal_plan_id):
    """Edit an existing meal plan"""

    meal_plan = get_object_or_404(
        MealPlan.objects.prefetch_related(
            Prefetch(
                'days',
                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        queryset=MealPlanRecipe.objects.select_related('recipe').order_by('sort_order')
                    )
                )
            )
        ),
        meal_plan_id=meal_plan_id
    )

    if request.method == 'POST':
        try:
            new_plan_name = request.POST.get('plan_name', '').strip()
            new_start_date_str = request.POST.get('start_date')
            new_end_date_str = request.POST.get('end_date')

            if not new_plan_name:
                messages.error(request, 'Plan name is required.')
                return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)

            new_start_date = datetime.strptime(new_start_date_str, '%Y-%m-%d').date()
            new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()

            days_diff = (new_end_date - new_start_date).days + 1
            if days_diff < 1 or days_diff > 7:
                messages.error(request, 'Meal plan must be between 1 and 7 days.')
                return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)

            with transaction.atomic():
                meal_plan.plan_name = new_plan_name
                meal_plan.start_date = new_start_date
                meal_plan.end_date = new_end_date
                meal_plan.save()

                existing_days = {day.date: day for day in meal_plan.days.all()}

                new_dates = []
                current_date = new_start_date
                while current_date <= new_end_date:
                    new_dates.append(current_date)
                    current_date += timedelta(days=1)

                # MP-1, 18 Oct 2026 - C13. COUNT WHAT GOES. Shortening
                # the dates, or moving the start by one day, deletes the
                # days that fall outside the new range - and CASCADE
                # takes their meals. That part is intended; the silence
                # was not. Nothing in the app said a meal had been
                # removed, here or in the browser.
                #
                # WHAT IS NOT FIXED HERE: the record's "meals move with
                # the start date". Whether shifting a plan carries its
                # meals or leaves them on their dates is a behaviour
                # decision, and release 3 - where the calendar IS the
                # plan - is where it belongs. This round makes the loss
                # visible at both ends: the browser warns before saving,
                # the server names it after.
                dates_to_keep = set(new_dates)
                dropped_days = 0
                dropped_meals = 0
                for date_obj, day in existing_days.items():
                    if date_obj not in dates_to_keep:
                        dropped_days += 1
                        dropped_meals += day.recipes.count()
                        day.delete()

                for date_obj in new_dates:
                    if date_obj in existing_days:
                        meal_day = existing_days[date_obj]
                    else:
                        meal_day = MealPlanDay.objects.create(
                            meal_plan=meal_plan,
                            date=date_obj
                        )

                    date_key = date_obj.strftime('%Y-%m-%d')
                    recipe_ids = request.POST.getlist(f'recipes_{date_key}[]')
                    servings_list = request.POST.getlist(f'servings_{date_key}[]')

                    # MP-1, 18 Oct 2026 - C15. A QUEUE PER RECIPE, NOT
                    # ONE ROW PER RECIPE.
                    #
                    # This was `{mr.recipe.recipe_id: mr for ...}`. Two
                    # servings of the same recipe on one day collapsed
                    # into a single key, so the second row was never
                    # visited - it kept its old servings and sort order,
                    # was never updated and was never deleted, because
                    # its recipe id WAS in recipes_to_keep. The reader
                    # saw two rows, edited both, and one of the edits
                    # went nowhere.
                    #
                    # The record says "rows indexed by their own ID".
                    # The form does not post row IDs - it posts
                    # `recipes_<date>[]`, a list of RECIPE ids - so that
                    # would mean a parallel hidden input in three JS
                    # blocks and a view that trusts it. Keying to a LIST
                    # and consuming one row per posted entry reaches the
                    # same outcome, changes no form, and the leftovers
                    # in the queues are exactly the rows to delete, so
                    # recipes_to_keep is not needed at all.
                    #
                    # `.all()` and not `.order_by()`: the day's recipes
                    # were prefetched in sort_order above, and asking
                    # for an order here throws that cache away and costs
                    # a query per day.
                    existing_rows = {}
                    for mr in meal_day.recipes.all():
                        existing_rows.setdefault(
                            mr.recipe.recipe_id, []).append(mr)

                    for idx, recipe_id in enumerate(recipe_ids):
                        if recipe_id:
                            recipe_id = int(recipe_id)

                            recipe = Recipe.objects.get(recipe_id=recipe_id)
                            servings = int(servings_list[idx]) if idx < len(servings_list) else recipe.servings

                            queue = existing_rows.get(recipe_id) or []
                            if queue:
                                meal_recipe = queue.pop(0)
                                meal_recipe.servings = servings
                                meal_recipe.sort_order = idx
                                meal_recipe.save()
                            else:
                                MealPlanRecipe.objects.create(
                                    meal_plan_day=meal_day,
                                    recipe=recipe,
                                    servings=servings,
                                    sort_order=idx
                                )

                    for rows in existing_rows.values():
                        for meal_recipe in rows:
                            meal_recipe.delete()

            # MP-1, 18 Oct 2026 - C13. SAY WHAT WAS REMOVED. A
            # warning, after the success, because the save did succeed
            # and the reader still needs to know a meal is gone.
            if dropped_meals:
                messages.warning(
                    request,
                    '%d meal%s on %d day%s fell outside the new dates and '
                    'were removed.'
                    % (dropped_meals, '' if dropped_meals == 1 else 's',
                       dropped_days, '' if dropped_days == 1 else 's'))
            messages.success(request, f'Meal plan "{new_plan_name}" updated successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

        except Exception as e:
            print(f"\n!!! ERROR: {str(e)} !!!")
            traceback.print_exc()
            messages.error(request, f'Error updating meal plan: {str(e)}')
            return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)

    # GET request - prepare data for editing
    meal_plan_data = {
        'meal_plan_id': meal_plan.meal_plan_id,
        'plan_name': meal_plan.plan_name,
        'start_date': meal_plan.start_date.strftime('%Y-%m-%d'),
        'end_date': meal_plan.end_date.strftime('%Y-%m-%d'),
        'days': []
    }

    for day in meal_plan.days.all():
        day_data = {
            'date': day.date.strftime('%Y-%m-%d'),
            'recipes': []
        }

        for meal_recipe in day.recipes.all():
            recipe = meal_recipe.recipe
            day_data['recipes'].append({
                'meal_plan_recipe_id': meal_recipe.meal_plan_recipe_id,
                'recipe_id': recipe.recipe_id,
                'recipe_name': recipe.recipe_name,
                'servings': meal_recipe.servings,
                'sort_order': meal_recipe.sort_order,
                'recipe_image': recipe.photo_url,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'difficulty_level': recipe.difficulty_level or '',
                'is_vegetarian': recipe.is_vegetarian,
                'courses': [course.name for course in recipe.courses.all()],
                'categories': [cat.name for cat in recipe.categories.all()],
                'proteins': [protein.name for protein in recipe.proteins.all()]
            })

        meal_plan_data['days'].append(day_data)

    recipes_qs = Recipe.objects.prefetch_related(
        'courses', 'categories', 'proteins'
    ).all().order_by('recipe_name')

    recipes = []
    for recipe in recipes_qs:
        recipes.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'servings': recipe.servings,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'difficulty_level': recipe.difficulty_level or '',
            'is_vegetarian': recipe.is_vegetarian,
            'author': recipe.author,
            'recipe_image': recipe.photo_url,
            'courses': [course.name for course in recipe.courses.all()],
            'categories': [cat.name for cat in recipe.categories.all()],
            'proteins': [protein.name for protein in recipe.proteins.all()]
        })

    all_courses = list(RecipeCourse.objects.all().order_by('name').values('recipe_course_id', 'name'))
    all_categories = list(RecipeCategory.objects.all().order_by('name').values('recipe_category_id', 'name'))
    all_proteins = list(CustomProtein.objects.all().order_by('name').values('custom_protein_id', 'name'))

    # MP-1, 18 Oct 2026 - B12. The model's own choices. This list was
    # typed out by hand in three places, including recipe_crud.py, and
    # Recipe.author validates against AUTHOR_CHOICES - so a name added
    # to the model never reached any of the three pickers.
    all_authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]

    user_favourite_ids = list(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )

    context = {
        'edit_mode': True,
        'meal_plan': meal_plan,
        'meal_plan_json': json.dumps(meal_plan_data),
        'recipes_json': json.dumps(recipes),
        'all_courses_json': json.dumps(all_courses),
        'all_categories_json': json.dumps(all_categories),
        'all_proteins_json': json.dumps(all_proteins),
        'all_authors_json': json.dumps(all_authors),
        'user_favourite_ids_json': json.dumps(user_favourite_ids),
    }

    return render(request, 'create_meal_plan.html', context)


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def duplicate_meal_plan(request, meal_plan_id):
    """Duplicate a meal plan to new dates"""

    try:
        # Get the original meal plan with all related data
        original_plan = MealPlan.objects.prefetch_related(
            'days__recipes__recipe'
        ).get(meal_plan_id=meal_plan_id)

        if request.method == 'POST':
            new_plan_name = request.POST.get('new_plan_name', '').strip()
            new_start_date = request.POST.get('new_start_date')

            if not new_plan_name:
                messages.error(request, 'Please enter a name for the duplicated meal plan.')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

            if not new_start_date:
                messages.error(request, 'Please select a start date.')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

            try:
                # Parse the new start date
                new_start = datetime.strptime(new_start_date, '%Y-%m-%d').date()

                # Calculate duration of original plan
                duration = (original_plan.end_date - original_plan.start_date).days
                new_end = new_start + timedelta(days=duration)

                # MP-1, 18 Oct 2026 - C17, the same warning Create now
                # gives. A duplicate landing on top of another plan is
                # the commonest way to make two plans share a week, and
                # the calendar can only show one of them. The original
                # is excluded because a shift - duplicate then delete -
                # always overlaps itself.
                clash = MealPlan.objects.filter(
                    start_date__lte=new_end, end_date__gte=new_start
                ).exclude(meal_plan_id=original_plan.meal_plan_id
                          ).order_by('start_date').first()
                if clash:
                    messages.warning(
                        request,
                        'These dates overlap "%s" (%s to %s). Both plans '
                        'are kept, but the calendar can only show one plan '
                        'for a week.' % (clash.plan_name,
                                         clash.start_date.strftime('%d %b'),
                                         clash.end_date.strftime('%d %b %Y')))

                # MP-1, 18 Oct 2026 - C14. ONE TRANSACTION, as on
                # Create. A failure part way through the copy used to
                # leave a plan with some of its days, and - on a SHIFT,
                # where the original is deleted afterwards - the
                # original was deleted whether or not the copy was
                # whole.
                with transaction.atomic():
                    # Create new meal plan with user-provided name
                    new_plan = MealPlan.objects.create(
                        plan_name=new_plan_name,
                        start_date=new_start,
                        end_date=new_end,
                        created_by=request.user
                    )

                    # Duplicate all days and recipes
                    for day in original_plan.days.all().order_by('date'):
                        # Calculate the offset from original start date
                        day_offset = (day.date - original_plan.start_date).days
                        new_day_date = new_start + timedelta(days=day_offset)

                        # Create new day
                        new_day = MealPlanDay.objects.create(
                            meal_plan=new_plan,
                            date=new_day_date
                        )

                        # Copy all recipes for this day
                        # MP-1, 18 Oct 2026 - AND sort_order, which the
                        # copy used to drop. Found while wrapping this
                        # block for C14: every copied meal took the
                        # column's default, so a duplicated day came out
                        # in an arbitrary order. Two words, in a block
                        # already being rewritten.
                        for meal_recipe in day.recipes.all().order_by('sort_order'):
                            MealPlanRecipe.objects.create(
                                meal_plan_day=new_day,
                                recipe=meal_recipe.recipe,
                                servings=meal_recipe.servings,
                                sort_order=meal_recipe.sort_order
                            )

                # Check if user wants to delete original (shift functionality)
                delete_original = request.POST.get('delete_original') == 'yes'

                if delete_original:
                    # Delete the original meal plan (this is a "shift" operation)
                    original_plan_name = original_plan.plan_name
                    original_plan.delete()
                    messages.success(request, f'Meal plan "{original_plan_name}" shifted to new dates: {new_start.strftime("%B %d, %Y")} - {new_end.strftime("%B %d, %Y")}')
                else:
                    # Regular duplicate (keep original)
                    messages.success(request, f'Meal plan "{new_plan_name}" created successfully starting on {new_start.strftime("%B %d, %Y")}.')

                return redirect('view_meal_plan', meal_plan_id=new_plan.meal_plan_id)

            except ValueError as e:
                messages.error(request, f'Invalid date format: {str(e)}')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
            except Exception as e:
                messages.error(request, f'Error duplicating meal plan: {str(e)}')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

        # GET request - should not happen with modal, but redirect just in case
        return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

    except MealPlan.DoesNotExist:
        messages.error(request, 'Meal plan not found.')
        return redirect('meal_plans')


# =====================================================================
# CALENDAR
# =====================================================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plan_calendar(request):
    """Calendar view for meal plans"""

    # Get requested month/year or default to current
    #
    # MP-1, 18 Oct 2026 - A5. A NON-NUMERIC OR OUT-OF-RANGE ADDRESS
    # FALLS BACK, it does not 500. Three different failures lived here:
    #
    #   ?year=abc      int() raises straight away
    #   ?month=13      survives int() and raises three lines down, in
    #                  date(year, month, 1) - and again in monthcalendar
    #   ?year=99999    survives both and raises in December only, where
    #                  the next month is date(year + 1, 1, 1)
    #
    # So the range matters as much as the type. The window is kept
    # plainly readable rather than pushed to date.MAXYEAR: a meal plan
    # calendar for the year 9999 is a typo, not a request.
    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        if not 1900 <= year <= 2200:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request.GET.get('month', today.month))
        if not 1 <= month <= 12:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        month = today.month

    # Get selected week start date (Monday)
    selected_week_start = request.GET.get('week')
    if selected_week_start:
        try:
            selected_week_start = datetime.strptime(
                selected_week_start, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            selected_week_start = today - timedelta(days=today.weekday())
    else:
        # Default to current week (find Monday)
        selected_week_start = today - timedelta(days=today.weekday())

    selected_week_end = selected_week_start + timedelta(days=6)

    # Build calendar data for the month
    # Get first day of month and adjust to start from Monday
    first_of_month = date(year, month, 1)

    # Get all days we need to show (including overflow from prev/next months)
    cal = monthcalendar(year, month)  # Returns weeks starting from Monday

    # Get all meal plans (shared across users)
    all_meal_plans = MealPlan.objects.all().order_by('-start_date')

    # Get meal plans that overlap with this month (for dot indicators)
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    month_meal_plans = MealPlan.objects.filter(
        start_date__lte=month_end,
        end_date__gte=month_start
    )

    # Build a set of dates that have meals planned
    dates_with_meals = set()
    for plan in month_meal_plans:
        days_with_recipes = MealPlanDay.objects.filter(
            meal_plan=plan,
            recipes__isnull=False
        ).values_list('date', flat=True).distinct()
        dates_with_meals.update(days_with_recipes)

    # Build calendar weeks with metadata
    calendar_weeks = []
    for week in cal:
        week_data = []
        week_dates = []
        for day_num in week:
            if day_num == 0:
                week_data.append(None)
            else:
                day_date = date(year, month, day_num)
                week_dates.append(day_date)
                week_data.append({
                    'day': day_num,
                    'date': day_date,
                    'has_meal': day_date in dates_with_meals,
                    'is_today': day_date == today,
                })

        # Calculate week start (Monday) for this row
        if week_dates:
            # Find the Monday of this week
            first_valid_date = week_dates[0]
            week_start = first_valid_date - timedelta(days=first_valid_date.weekday())
        else:
            week_start = None

        calendar_weeks.append({
            'days': week_data,
            'week_start': week_start,
        })

    # Get the meal plan for the selected week (if any)
    #
    # MP-1, 18 Oct 2026 - C17. DETERMINISTIC, AND IT SAYS SO.
    # .first() on an unordered queryset asked the database to choose,
    # so which of two overlapping plans a week showed could change
    # between two loads of the same page - and the meals in the other
    # one were invisible with nothing on the screen to suggest they
    # existed. Showing every plan in the week is release-3 markup; what
    # ships here is a stable choice and a sentence.
    week_plans = list(MealPlan.objects.filter(
        start_date__lte=selected_week_end,
        end_date__gte=selected_week_start
    ).order_by('start_date', 'meal_plan_id'))
    selected_meal_plan = week_plans[0] if week_plans else None
    if len(week_plans) > 1:
        messages.info(
            request,
            '%d meal plans cover this week. Showing "%s"; the others are '
            'on the Meal Plans list.'
            % (len(week_plans), selected_meal_plan.plan_name))

    # Build week detail data
    week_days = []
    for i in range(7):
        day_date = selected_week_start + timedelta(days=i)
        day_data = {
            'date': day_date,
            'day_name': day_date.strftime('%A'),
            'day_short': day_date.strftime('%a'),
            'day_num': day_date.day,
            'is_today': day_date == today,
            'recipes': [],
            'meal_plan_day_id': None,
        }

        # If there's a meal plan for this week, get recipes for this day
        if selected_meal_plan:
            meal_plan_day = MealPlanDay.objects.filter(
                meal_plan=selected_meal_plan,
                date=day_date
            ).first()

            if meal_plan_day:
                day_data['meal_plan_day_id'] = meal_plan_day.meal_plan_day_id
                recipes = MealPlanRecipe.objects.filter(
                    meal_plan_day=meal_plan_day
                ).select_related('recipe').order_by('sort_order')

                for mpr in recipes:
                    recipe = mpr.recipe
                    day_data['recipes'].append({
                        'meal_plan_recipe_id': mpr.meal_plan_recipe_id,
                        'recipe_id': recipe.recipe_id,
                        'name': recipe.recipe_name,
                        'image': recipe.photo_url,
                        'prep_time': recipe.prep_time,
                        'cook_time': recipe.cook_time,
                        'total_time': (recipe.prep_time or 0) + (recipe.cook_time or 0),
                        'servings': mpr.servings,
                        'difficulty': recipe.difficulty_level,
                    })

        week_days.append(day_data)

    # Previous and next month for navigation
    if month == 1:
        prev_month = {'year': year - 1, 'month': 12}
    else:
        prev_month = {'year': year, 'month': month - 1}

    if month == 12:
        next_month = {'year': year + 1, 'month': 1}
    else:
        next_month = {'year': year, 'month': month + 1}

    # Month name for display
    month_name = date(year, month, 1).strftime('%B %Y')

    # Get all recipes for the "Add Recipe" modal
    all_recipes = Recipe.objects.all().order_by('recipe_name')

    context = {
        'calendar_weeks': calendar_weeks,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'next_month': next_month,
        'today': today,
        'selected_week_start': selected_week_start,
        'selected_week_end': selected_week_end,
        'selected_meal_plan': selected_meal_plan,
        'week_days': week_days,
        'all_meal_plans': all_meal_plans,
        'all_recipes': all_recipes,
    }

    return render(request, 'meal_plan_calendar.html', context)


# =====================================================================
# SHOPPING LIST (RENDER / MUTATE / EMAIL)
# =====================================================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plan_shopping_list(request, meal_plan_id):
    """Display shopping list with unit conversion and prompt for missing conversions"""

    try:
        # Get meal plan with optimized prefetching
        meal_plan = get_object_or_404(
            MealPlan.objects.prefetch_related(
                Prefetch(
                    'days',
                    queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                        Prefetch(
                            'recipes',
                            queryset=MealPlanRecipe.objects.select_related('recipe').prefetch_related(
                                Prefetch(
                                    'recipe__recipe_ingredients',
                                    queryset=RecipeIngredient.objects.select_related(
                                        'ingredient',
                                        'ingredient__category',
                                        'ingredient__default_unit',
                                        'unit'
                                    )
                                )
                            )
                        )
                    )
                )
            ),
            meal_plan_id=meal_plan_id
        )

        # Aggregate ingredients with conversion
        (ingredients, missing_conversions, missing_shopping_units,
         missing_units) = aggregate_meal_plan_ingredients(meal_plan)

        # Check for missing conversions or shopping units
        has_issues = (len(missing_conversions) > 0
                      or len(missing_shopping_units) > 0
                      or len(missing_units) > 0)

        # SL-4, 3 Oct 2026. THE ADDRESSES COME FROM THE ROSTER NOW.
        #
        # The template carried four <option> elements with four people's
        # addresses typed into it. HouseholdMember's own docstring says
        # the table exists to replace exactly this kind of hard-coding -
        # "Members are an AUDIENCE ... Replaces the hardcoded
        # notify_demetri / notify_angy / notify_erene / notify_alexandra
        # flags" - and the flags were replaced while this list was not.
        #
        # Active members with an address, by name. A member with no email
        # is a real row (the table allows blank for people who never sign
        # in and are only tagged on celebrations), so they are excluded
        # here rather than offered as an empty option.
        household_emails = (
            HouseholdMember.objects.for_user(request.user)
            .filter(is_active=True)
            .exclude(email='')
            .order_by('name')
        )

        context = {
            'meal_plan': meal_plan,
            'household_emails': household_emails,
            'ingredients': ingredients,
            'total_ingredients': sum(len(items) for items in ingredients.values()),
            'missing_conversions': json.dumps(missing_conversions) if missing_conversions else '[]',
            'missing_shopping_units': json.dumps(missing_shopping_units) if missing_shopping_units else '[]',
            'has_missing_conversions': len(missing_conversions) > 0,
            # MP-1, 18 Oct 2026 - C16. has_missing_shopping_units has
            # been in this context all along and no template ever read
            # it, so an ingredient with no shopping unit vanished from
            # the list in silence. The page prints both lists now.
            'has_missing_shopping_units': len(missing_shopping_units) > 0,
            'missing_shopping_units_list': missing_shopping_units,
            'missing_units_list': missing_units,
            'has_missing_units': len(missing_units) > 0,
            'has_issues': has_issues,
        }

        return render(request, 'meal_plan_shopping_list.html', context)

    except Exception as e:
        traceback.print_exc()
        messages.error(request, f'Error generating shopping list: {str(e)}')
        return redirect('view_meal_plan', meal_plan_id=meal_plan_id)


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_recipe_to_meal_plan_day(request):
    """Add a recipe to a meal plan day.

    MP-1, 18 Oct 2026 - A1. `meal_plan_id` used to be a required
    positional argument and the URL supplies none:

        path('meal_plans/add_recipe_to_day/', views.add_recipe_to_meal_plan_day)

    so every add on the calendar was a TypeError before this function
    ran. The parameter is gone rather than added to the URL, because
    nothing here ever read it - the day comes from meal_plan_day_id in
    the POST body - and because a day with no plan has no plan id to
    send, which is A3.

    A2 - THE FAILURE PATH RETURNS. The redirect used to sit outside
    the try and read meal_plan_day, which the except branch never
    assigns, so a missing day set an error message and then raised
    UnboundLocalError on the way out.

    B8 - NO OWNERSHIP CHECK. It used to refuse anyone who was not
    created_by. That check and its twin in remove() were the only two
    in the module and they have never run, because A1 stopped this
    function being reached at all. Demetri decided on 18 Oct that all
    users may edit all plans; the checks go rather than come alive.
    """
    meal_plan_day_id = request.POST.get('meal_plan_day_id')
    recipe_id = request.POST.get('recipe_id')
    servings = request.POST.get('servings')

    try:
        meal_plan_day = MealPlanDay.objects.get(meal_plan_day_id=meal_plan_day_id)
        recipe = Recipe.objects.get(recipe_id=recipe_id)
    except (MealPlanDay.DoesNotExist, Recipe.DoesNotExist,
            ValueError, TypeError):
        messages.error(request, 'That day or recipe no longer exists.')
        return redirect('meal_plan_calendar')

    # C19 - THE RECIPE'S OWN YIELD, not a hardcoded 4. The picker sent
    # 4 whatever the recipe made, and the server fell back to 4 too, so
    # a recipe for six was planned for four in both directions.
    try:
        servings = int(servings)
    except (TypeError, ValueError):
        servings = recipe.servings or 4

    max_order = MealPlanRecipe.objects.filter(
        meal_plan_day=meal_plan_day
    ).aggregate(Max('sort_order'))['sort_order__max'] or 0

    MealPlanRecipe.objects.create(
        meal_plan_day=meal_plan_day,
        recipe=recipe,
        servings=servings,
        sort_order=max_order + 1
    )

    messages.success(request, f'Added "{recipe.recipe_name}" to {meal_plan_day.date.strftime("%A, %B %d")}')
    return redirect(f"{reverse('meal_plan_calendar')}?week={meal_plan_day.date.strftime('%Y-%m-%d')}")


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_recipe_from_meal_plan(request):
    """Remove a recipe from a meal plan day.

    MP-1, 18 Oct 2026 - A1 and B8, the same two as add() above. The
    URL supplies no plan id and this function never read one; the
    ownership check goes with its twin.
    """
    meal_plan_recipe_id = request.POST.get('meal_plan_recipe_id')

    try:
        meal_plan_recipe = MealPlanRecipe.objects.get(
            meal_plan_recipe_id=meal_plan_recipe_id)
    except (MealPlanRecipe.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That meal is no longer on the plan.')
        return redirect('meal_plan_calendar')

    recipe_name = meal_plan_recipe.recipe.recipe_name
    week_date = meal_plan_recipe.meal_plan_day.date.strftime('%Y-%m-%d')
    meal_plan_recipe.delete()

    messages.success(request, f'Removed "{recipe_name}" from the meal plan')
    return redirect(f"{reverse('meal_plan_calendar')}?week={week_date}")


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def send_meal_plan_shopping_list(request, meal_plan_id=None):
    """Send meal plan shopping list via email
    NOTE (Phase 10): meal_plan_id is accepted but unused ... optional (=None)
    because the route supplies no id (pre-existing bug). """

    try:
        try:
            data = json.loads(request.body)
        except (TypeError, ValueError):
            return JsonResponse({'success': False,
                                 'error': 'Could not read the request.'},
                                status=400)
        if not isinstance(data, dict):
            return JsonResponse({'success': False,
                                 'error': 'Could not read the request.'},
                                status=400)

        email = (data.get('email') or '').strip()
        ingredients_by_category = data.get('ingredients') or {}

        # Validate
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address is required'}, status=400)

        if not isinstance(ingredients_by_category, dict) or not ingredients_by_category:
            return JsonResponse({'success': False, 'error': 'No ingredients to send'}, status=400)

        # MP-1, 18 Oct 2026 - B9. THE RECIPIENT MUST BE ON THE ROSTER.
        #
        # This address used to be whatever the request body said, and
        # the message went out from DEFAULT_FROM_EMAIL - the
        # application's own domain. The page only ever offers household
        # members (SL-4 built that list from HouseholdMember), so the
        # server now requires what the page offers, plus the signed-in
        # user's own address, which is always a legitimate place to
        # send your own shopping list.
        allowed = set(
            HouseholdMember.objects.for_user(request.user)
            .filter(is_active=True).exclude(email='')
            .values_list('email', flat=True))
        own = (getattr(request.user, 'email', '') or '').strip()
        if own:
            allowed.add(own)
        if email.lower() not in set(a.strip().lower() for a in allowed):
            return JsonResponse(
                {'success': False,
                 'error': 'That address is not a household member.'},
                status=403)

        # MP-1, 18 Oct 2026 - B9 and C18. THE PLAN'S OWN NAME, DATES
        # AND RECIPE COUNT, read from the plan.
        #
        # All three used to arrive in the request body, so the email's
        # heading was whatever the sender typed. And the count was
        # `meal_plan.days.count` - the number of DAYS - so a seven-day
        # plan's email said "7 recipes" however many recipes were on
        # it. That is C18, and it is the same line.
        plan_id = data.get('meal_plan_id') or meal_plan_id
        plan = MealPlan.objects.filter(meal_plan_id=plan_id).first()
        if plan is None:
            return JsonResponse({'success': False,
                                 'error': 'That meal plan no longer exists.'},
                                status=400)
        meal_plan_name = plan.plan_name
        date_range = '%s - %s' % (plan.start_date.strftime('%d %b'),
                                  plan.end_date.strftime('%d %b %Y'))
        total_recipes = MealPlanRecipe.objects.filter(
            meal_plan_day__meal_plan=plan).count()

        # Build email content
        # NOTE (Phase 10 ASCII): subject originally led with a corrupted/
        # mojibake cart emoji; replaced with clean ASCII text.
        subject = f'Shopping List for {meal_plan_name}'

        # Plain text version
        text_content = f"""Shopping List for {meal_plan_name}

{date_range}
{total_recipes} recipes

Items to Buy:
"""

        for category in sorted(ingredients_by_category.keys()):
            text_content += f"\n{category}:\n"
            for item in ingredients_by_category[category]:
                qty = item['quantity']
                # Format quantity nicely
                if qty % 1 == 0:
                    qty_str = f"{int(qty)}"
                else:
                    qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')
                # NOTE (Phase 10 ASCII): per-item marker was a corrupted glyph;
                # replaced with an ASCII checkbox "[ ]".
                text_content += f"[ ] {qty_str} {item['unit']} {item['ingredient']}\n"

        text_content += "\n---\nGenerated by ALIVENTE ONLINE - Recipe Management"

        # HTML version
        # NOTE (Phase 10 ASCII): the <h1> and category headers originally led
        # with corrupted/mojibake emoji; replaced with clean ASCII text.
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            color: #2c3e50;
        }}
        .header {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.95;
        }}
        .category {{
            margin-bottom: 25px;
        }}
        .category-header {{
            color: #28a745;
            font-size: 20px;
            font-weight: 600;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 15px;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        li {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        li:hover {{
            background: #f8f9fa;
        }}
        li:last-child {{
            border-bottom: none;
        }}
        .checkbox {{
            width: 18px;
            height: 18px;
            border: 2px solid #28a745;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        .quantity {{
            font-weight: 600;
            color: #28a745;
            margin-right: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Shopping List</h1>
        <p><strong>{escape(meal_plan_name)}</strong></p>
        <p>{date_range}</p>
        <p>{total_recipes} recipes</p>
    </div>
"""

        # Add categories
        for category in sorted(ingredients_by_category.keys()):
            html_content += f"""
    <div class="category">
        <div class="category-header">{escape(category)}</div>
        <ul>
"""
            for item in ingredients_by_category[category]:
                qty = item['quantity']
                if qty % 1 == 0:
                    qty_str = f"{int(qty)}"
                else:
                    qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')

                html_content += f"""
            <li>
                <div class="checkbox"></div>
                <span><span class="quantity">{qty_str} {escape(item['unit'])}</span> {escape(item['ingredient'])}</span>
            </li>
"""
            html_content += """
        </ul>
    </div>
"""

        html_content += f"""
    <div class="footer">
        <p>Generated by <strong>ALIVENTE ONLINE</strong> - Recipe Management</p>
        <p>{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
</body>
</html>
"""

        # Send email using same method as recipe shopping list
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return JsonResponse({
            'success': True,
            'message': f'Shopping list sent to {email}'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)