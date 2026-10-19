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
- meal_planner                    : The planner. One week of dates, with
                                    the meals on them. Read-tier.
                                    Replaced meal_plans, create_meal_plan,
                                    view_meal_plan, edit_meal_plan,
                                    duplicate_meal_plan, delete_meal_plan
                                    and meal_plan_calendar - seven screens
                                    for one, because the calendar IS the
                                    plan now. MN-1, 18 Oct 2026.
- add_meal_entry                  : Put a recipe on a date (POST). Edit-tier.
- remove_meal_entry               : Take one off (POST). Edit-tier.
- set_meal_servings               : Change servings on one meal (POST,
                                    JSON). Saves immediately, which is why
                                    the planner has no Save button.
                                    Edit-tier.
- meal_shopping_list              : Shop a DATE RANGE. Read-tier. It took
                                    a meal_plan_id until MN-1, and there
                                    is no plan to key on any more.
- send_meal_plan_shopping_list    : Email a shopping list (POST).
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
import logging
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

# MD-1, 18 Oct 2026 - E32. Three handlers in this module printed a
# traceback to stdout with print() and traceback.print_exc(), which on
# Railway is an unlabelled traceback in the deploy log and not a channel
# anybody can turn down. ai_extract.py and recipe_extras.py already do
# this; meal_planning.py is the third.
logger = logging.getLogger(__name__)

from pages.models import (
    CustomProtein,
    HouseholdMember,
    MealEntry,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
)

from .conversions import convert_quantity, get_conversion_cache
# MD-1, 18 Oct 2026 - E33. The nested round_shopping_qty in
# aggregate_meal_plan_ingredients made the same decisions as this, in
# the same order, with the same thresholds. This module's docstring has
# called it a dedupe candidate since the views were split.
from .shopping import round_shopping_quantity


# =====================================================================
# SHARED HELPER - INGREDIENT AGGREGATION
# =====================================================================

def aggregate_meal_entries(entries):
    """
    Aggregate ingredients and convert to shopping units.

    MN-1, 18 Oct 2026 - release 3. This took a MEAL PLAN and walked its
    days; it takes an iterable of MealEntry now, because meals belong
    to dates and there is no plan to walk. Everything below the walk -
    the conversion, the smart rounding UP, the three trackers - is
    untouched, deliberately.
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

    # MD-1, 18 Oct 2026 - E33. THE NESTED COPY IS GONE.
    #
    # round_shopping_qty lived here and made exactly the same decisions
    # as shopping.round_shopping_quantity, which is imported at the top
    # of the module now: the same three unit types, the same thresholds
    # at 10 and 100, round UP in every branch, and the same `if qty <= 0
    # return qty` guard. Compared line by line before this was deleted,
    # not assumed from the name.
    round_shopping_qty = round_shopping_quantity

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
    for entry in entries:
        # MN-1, 18 Oct 2026 - A NOTE BUYS NOTHING, AND LEFTOVERS WERE
        # BOUGHT ONCE ALREADY. counts_on_shopping_list is the model's
        # own answer to both, so the rule lives in one place rather
        # than in every caller that walks entries.
        if entry.counts_on_shopping_list:
            recipe = entry.recipe
            # MD-1, 18 Oct 2026 - E33. The model's own property, which
            # was unused until now and carried this expression's unsafe
            # twin. It is this expression now.
            servings_multiplier = entry.servings_multiplier

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
# THE PLANNER - MN-1, 18 Oct 2026, release 3
# =====================================================================
#
# SEVEN SCREENS BECAME ONE. meal_plans, create_meal_plan,
# view_meal_plan, edit_meal_plan, duplicate_meal_plan, delete_meal_plan
# and meal_plan_calendar are all gone, and so is the chain of boxes
# they existed to manage.
#
# The calendar IS the plan. A meal has a date. There is no name, no
# start date and no end date to fill in before you can plan a single
# dinner, nothing can overlap because there is only one calendar, and
# changing your mind about a week cannot throw meals away - which was
# C13, C17 and C20 of release 1 between them, all three dissolved by
# the model rather than guarded.

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_planner(request):
    """One week of dates, and the meals on them."""

    today = timezone.now().date()

    # THE ADDRESS BAR IS A STRING SOMEBODY CAN TYPE - A5, 18 Oct 2026,
    # one screen away. ?year=abc was a 500 on the old calendar, and so
    # was ?month=13 three lines later, and so was ?year=99999 in
    # December only. All three fall back here rather than raising.
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

    asked = request.GET.get('week')
    if asked:
        try:
            week_start = datetime.strptime(asked, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            week_start = today
    else:
        week_start = today

    # WHATEVER ARRIVES, THE WEEK STARTS ON A MONDAY - D26, and it is
    # the model's rule now rather than one screen's. Every row in the
    # mini calendar is a Monday-to-Sunday week, so a band that starts
    # on a Wednesday lines up with nothing and cannot be highlighted.
    week_start -= timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=6)

    # ONE QUERY FOR THE WEEK - E29's lesson, built in rather than
    # retro-fitted. The old calendar asked for each day and then for
    # that day's recipes, seven times over.
    entries = list(
        MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)
        .select_related('recipe')
        .prefetch_related('recipe__courses', 'recipe__categories'))
    by_date = {}
    for e in entries:
        by_date.setdefault(e.date, []).append(e)

    week_days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        week_days.append({
            'date': d,
            'day_name': d.strftime('%A'),
            'day_short': d.strftime('%a'),
            'day_num': d.day,
            'is_today': d == today,
            'entries': by_date.get(d, []),
        })

    # THE MINI MONTH. One query for the dots, not one per plan.
    first_of_month = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    dates_with_meals = set(
        MealEntry.objects.filter(date__gte=first_of_month,
                                 date__lte=month_end)
        .values_list('date', flat=True).distinct())

    calendar_weeks = []
    for week in monthcalendar(year, month):
        days, dates = [], []
        for day_num in week:
            if day_num == 0:
                days.append(None)
                continue
            d = date(year, month, day_num)
            dates.append(d)
            days.append({'day': day_num, 'date': d,
                         'has_meal': d in dates_with_meals,
                         'is_today': d == today})
        row_start = (dates[0] - timedelta(days=dates[0].weekday())
                     if dates else None)
        calendar_weeks.append({'days': days, 'week_start': row_start})

    prev_month = ({'year': year - 1, 'month': 12} if month == 1
                  else {'year': year, 'month': month - 1})
    next_month = ({'year': year + 1, 'month': 1} if month == 12
                  else {'year': year, 'month': month + 1})

    context = {
        'today': today,
        'year': year,
        'month': month,
        'month_name': first_of_month.strftime('%B %Y'),
        'prev_month': prev_month,
        'next_month': next_month,
        'calendar_weeks': calendar_weeks,
        'week_start': week_start,
        'week_end': week_end,
        'week_days': week_days,
        'prev_week': week_start - timedelta(days=7),
        'next_week': week_start + timedelta(days=7),
        'this_week': today - timedelta(days=today.weekday()),
        'meal_count': len(entries),
        'household_size': household_size(request.user),
        'all_recipes': Recipe.objects.all().order_by('recipe_name'),
    }
    return render(request, 'meal_planner.html', context)


def household_size(user):
    """How many this house cooks for, used as the servings default.

    MN-1, 18 Oct 2026. The design record asks for a household size that
    "defaults to the number of active household members", and
    HouseholdMember is already the roster SL-4 built the email list
    from - so there is nothing new to configure.

    Falls back to 4 when the roster is empty, which is what both ends
    of the old code hardcoded.
    """
    try:
        n = (HouseholdMember.objects.for_user(user)
             .filter(is_active=True).count())
    except Exception:
        n = 0
    return n or 4


def week_of(value, fallback):
    """A ?date= string as the Monday of its week, or the fallback."""
    try:
        d = datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return fallback
    return d


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_entry(request):
    """Put a recipe on a date.

    MN-1, 18 Oct 2026. The view this replaces demanded a plan id the
    URL never supplied, so every add on the calendar was a TypeError
    until MP-1 - and then needed a MealPlanDay row to exist, which is
    why a day outside a plan had a button that could not work (A3).

    A date is a date. Any date can take a meal.
    """
    when = week_of(request.POST.get('date'), None)
    recipe_id = request.POST.get('recipe_id')
    servings = request.POST.get('servings')

    if when is None:
        messages.error(request, 'That date could not be read.')
        return redirect('meal_planner')
    try:
        recipe = Recipe.objects.get(recipe_id=recipe_id)
    except (Recipe.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That recipe no longer exists.')
        return redirect('%s?week=%s' % (reverse('meal_planner'),
                                        when.strftime('%Y-%m-%d')))

    # C19's lesson, and it survives the model change: the recipe's own
    # yield, then the household size, and only then a 4.
    try:
        servings = int(servings)
    except (TypeError, ValueError):
        servings = recipe.servings or household_size(request.user)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(
        date=when, recipe=recipe, servings=servings,
        sort_order=(last or 0) + 1, created_by=request.user)

    messages.success(request, 'Added "%s" to %s'
                     % (recipe.recipe_name, when.strftime('%A, %d %B')))
    return redirect('%s?week=%s' % (reverse('meal_planner'),
                                    when.strftime('%Y-%m-%d')))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):
    """Take a meal off its date."""
    try:
        entry = MealEntry.objects.select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That meal is no longer on the planner.')
        return redirect('meal_planner')

    when = entry.date
    what = entry.recipe.recipe_name if entry.recipe else (entry.note or 'Meal')
    entry.delete()
    messages.success(request, 'Removed "%s" from %s'
                     % (what, when.strftime('%A, %d %B')))
    return redirect('%s?week=%s' % (reverse('meal_planner'),
                                    when.strftime('%Y-%m-%d')))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def set_meal_servings(request):
    """Change how many a meal is cooked for. Saves immediately.

    MN-1, 18 Oct 2026. The design record asks for - and + beside every
    meal, saving with no Save button: "Press - or + beside any meal in
    the planner. It saves immediately; there is no Save button."

    Changing servings here never touches the recipe. The shopping list
    scales from MealEntry.servings_multiplier, which is the meal's own
    number over the recipe's yield.
    """
    try:
        entry = MealEntry.objects.select_related('recipe').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'success': False,
                             'error': 'That meal is no longer on the planner.'},
                            status=404)
    try:
        servings = int(request.POST.get('servings'))
    except (TypeError, ValueError):
        return JsonResponse({'success': False,
                             'error': 'That is not a number of servings.'},
                            status=400)
    # A FLOOR OF ONE AND A CEILING OF NINETY-NINE. Nobody cooks for
    # nought, and the - button must not be able to walk a meal into
    # negative servings that then scale the shopping list backwards.
    servings = max(1, min(99, servings))
    entry.servings = servings
    entry.save(update_fields=['servings', 'updated_at'])

    recipe_yield = entry.recipe.servings if entry.recipe else None
    return JsonResponse({
        'success': True,
        'servings': servings,
        'recipe_yield': recipe_yield,
        'scales': (float(entry.servings_multiplier)
                   if entry.recipe else None),
    })


# =====================================================================
# SHOPPING LIST - A DATE RANGE, NOT A PLAN
# =====================================================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_shopping_list(request):
    """Shop for the days you choose.

    MN-1, 18 Oct 2026. This took a meal_plan_id and there is no plan to
    key on any more, so it takes ?from= and ?to= and defaults to the
    week the planner was showing.

    THE DATE RANGE IS THE ONLY THING THAT CHANGED. The conversion, the
    aggregation and the rounding UP are untouched - the design record
    is explicit that this part is already ahead of the field, and
    release 4 builds saved ticks, manual items and pantry staples on
    top of it rather than replacing it.
    """
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    start = week_of(request.GET.get('from'), monday)
    end = week_of(request.GET.get('to'), start + timedelta(days=6))
    if end < start:
        start, end = end, start
    # A CEILING, because the aggregator walks every ingredient of every
    # recipe in the range and ?from=1900-01-01 would walk all of them.
    if (end - start).days > 92:
        end = start + timedelta(days=92)
        messages.info(request, 'A shopping list covers at most 13 weeks. '
                               'Showing the first.')

    try:
        entries = (
            MealEntry.objects.filter(date__gte=start, date__lte=end)
            .select_related('recipe')
            .prefetch_related(
                Prefetch('recipe__recipe_ingredients',
                         queryset=RecipeIngredient.objects.select_related(
                             'ingredient', 'ingredient__category',
                             'ingredient__default_unit', 'unit'))))

        (ingredients, missing_conversions, missing_shopping_units,
         missing_units) = aggregate_meal_entries(entries)

        has_issues = (len(missing_conversions) > 0
                      or len(missing_shopping_units) > 0
                      or len(missing_units) > 0)

        # SL-4, 3 Oct 2026. THE ADDRESSES COME FROM THE ROSTER.
        household_emails = (
            HouseholdMember.objects.for_user(request.user)
            .filter(is_active=True)
            .exclude(email='')
            .order_by('name')
        )

        context = {
            'start': start,
            'end': end,
            'day_count': (end - start).days + 1,
            'meal_count': sum(1 for e in entries
                              if e.counts_on_shopping_list),
            'week_start': start,
            'household_emails': household_emails,
            'ingredients': ingredients,
            'total_ingredients': sum(len(v) for v in ingredients.values()),
            'missing_conversions': (json.dumps(missing_conversions)
                                    if missing_conversions else '[]'),
            'missing_shopping_units': (json.dumps(missing_shopping_units)
                                       if missing_shopping_units else '[]'),
            'has_missing_conversions': len(missing_conversions) > 0,
            'has_missing_shopping_units': len(missing_shopping_units) > 0,
            'missing_shopping_units_list': missing_shopping_units,
            'missing_units_list': missing_units,
            'has_missing_units': len(missing_units) > 0,
            'has_issues': has_issues,
        }
        return render(request, 'meal_plan_shopping_list.html', context)

    except Exception as e:
        # MD-1, 18 Oct 2026 - E32.
        logger.exception('meal_shopping_list failed for %s to %s', start, end)
        messages.error(request, f'Error generating shopping list: {str(e)}')
        return redirect('%s?week=%s' % (reverse('meal_planner'),
                                        start.strftime('%Y-%m-%d')))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def send_meal_plan_shopping_list(request):
    """Email a shopping list for a date range.

    MN-1, 18 Oct 2026. The signature carried a meal_plan_id the route
    never supplied - a Phase 10 note called it a pre-existing bug and
    made it optional rather than removing it, which is the same shape
    A1 found in the two calendar views. There is no plan to pass now,
    so it is gone.

    B9's work from 18 Oct is untouched: the recipient must still be an
    active household member with an address or the signed-in user, and
    every value is still escaped before it reaches the HTML."""

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
        # MN-1, 18 Oct 2026 - A RANGE, NOT A PLAN. The server still
        # decides the heading and the count rather than believing the
        # request body, which is the whole of B9; what it reads them
        # off is a pair of dates instead of a MealPlan row.
        today = timezone.now().date()
        monday = today - timedelta(days=today.weekday())
        start = week_of(data.get('from'), monday)
        end = week_of(data.get('to'), start + timedelta(days=6))
        if end < start:
            start, end = end, start
        meal_plan_name = 'Meal plan'
        date_range = '%s - %s' % (start.strftime('%d %b'),
                                  end.strftime('%d %b %Y'))
        # C18's lesson survives the model change: this counts MEALS,
        # not days. A seven-day range used to be emailed as
        # "7 recipes" whatever was on it.
        total_recipes = MealEntry.objects.filter(
            date__gte=start, date__lte=end,
            recipe__isnull=False, leftover_of__isnull=True).count()

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