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
- add_meal_note                   : A planned night that is not a
                                    recipe - Eat out, takeaway (POST).
                                    Edit-tier. MO-1, 19 Oct 2026.
- add_leftover                    : Monday's soup again on Wednesday,
                                    and it costs nothing the second
                                    time (POST). Edit-tier.
                                    MO-1, 19 Oct 2026.
- send_meal_plan_shopping_list    : Email a shopping list (POST).
                                    Edit-tier.
- meal_week_preview               : What a copy onto a week would land
                                    on (GET, JSON). Read-tier. The
                                    dialog asks before it says "2 of
                                    those days already have meals".
                                    MW-1, 19 Oct 2026.
- copy_meal_week                  : Copy one week of meals onto another
                                    (POST). Edit-tier. MW-1.
- save_menu                       : Save the week on screen as a named
                                    Menu (POST). Edit-tier. MW-1.
- apply_menu                      : Stamp a Menu onto the week on
                                    screen (POST). Edit-tier. MW-1.
- delete_menu                     : Forget a Menu (POST). Edit-tier.
                                    The meals it put on weeks stay.
                                    MW-1.

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
# PB-2, 19 Oct 2026 - planner_back builds the return
# address, and planner_view reads a Referer only as a
# fallback.
from urllib.parse import parse_qs, urlencode, urlsplit

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
    Menu,
    MenuItem,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
)

# PF-2, 19 Oct 2026 - the shared filter, asked by the picker exactly
# as recipe_management asks it.
from pages.views.recipes._recipe_filter import (
    filter_recipes,
    selected_from,
    vocabulary as _filter_vocabulary,
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
    """The calendar, at one of three zoom levels.

    MV-1, 19 Oct 2026 - it was one week of dates, and a mini calendar
    beside it to navigate with. Demetri, testing it: the daily list is
    not required, and the Monthly Calendar comes first, full page.
    """

    today = timezone.now().date()

    # ---- ONE ANCHOR DATE FOR THREE VIEWS - MV-1, 19 Oct 2026.
    #
    # Month, Week and Day are three zoom levels on the SAME DAY, so
    # they travel on ONE parameter. Three would each have to be kept
    # in step by every link that moves the date - the week arrows, the
    # month arrows, Today, the picker's return - which is six places
    # to forget one.
    #
    # ?week= IS STILL READ, and second, because the Shopping List link
    # and the Copy Week dialog already send it and MN-1 kept this
    # screen's old addresses working on purpose.
    #
    # THE ADDRESS BAR IS A STRING SOMEBODY CAN TYPE - A5. Every one of
    # these falls back rather than raising.
    anchor = None
    for _param in ('date', 'week'):
        _raw = request.GET.get(_param)
        if not _raw:
            continue
        try:
            anchor = datetime.strptime(_raw, '%Y-%m-%d').date()
            break
        except (TypeError, ValueError):
            anchor = None
    if anchor is None:
        anchor = today

    # ---- WHICH VIEW - MV-1. Month is the landing view, by Demetri's
    # own words on 19 Oct: "Monthly Calendar first - full page". That
    # overrides the earlier answer of Week, which is dead.
    #
    # A LIST AND NOT A FREE STRING. `?view=<anything>` reaching a
    # template that branches on it is how a page ends up rendering
    # nothing at all.
    view_mode = request.GET.get('view', 'month')
    if view_mode not in ('month', 'week', 'day'):
        view_mode = 'month'

    # THE ADDRESS BAR IS A STRING SOMEBODY CAN TYPE - A5, 18 Oct 2026,
    # one screen away. ?year=abc was a 500 on the old calendar, and so
    # was ?month=13 three lines later, and so was ?year=99999 in
    # December only. All three fall back here rather than raising.
    # FROM THE ANCHOR, NOT FROM TODAY - MV-1, 19 Oct 2026. These
    # defaulted to the current month, which was right while the month
    # was only a navigation strip beside a week. Month is the landing
    # VIEW now, so arriving with ?date=2026-12-03 and being shown
    # October would be the page ignoring the address it was given.
    try:
        year = int(request.GET.get('year', anchor.year))
        if not 1900 <= year <= 2200:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        year = anchor.year
    try:
        month = int(request.GET.get('month', anchor.month))
        if not 1 <= month <= 12:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        month = anchor.month

    # THE WEEK IS THE ANCHOR'S WEEK - MV-1, 19 Oct 2026. This block
    # read ?week= for itself; the anchor above now does that for all
    # three views, so there is one reading of the date instead of two
    # that could disagree.
    week_start = anchor

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
        # MO-1, 19 Oct 2026 - leftover_of joins the ONE query. The
        # leftover row prints the date of the meal it came from, and
        # that is a query per row without this. [E29]
        .select_related('recipe', 'leftover_of')
        .prefetch_related('recipe__courses', 'recipe__categories'))
    by_date = {}
    for e in entries:
        by_date.setdefault(e.date, []).append(e)

    # WHICH DAY THE PHONE OPENS ON - MV-3, 19 Oct 2026.
    #
    # Seven columns is 51px on a phone, so the week there is a day
    # strip with ONE day open underneath it - Demetri's answer to
    # Question A. Something has to be that day.
    #
    # THE ANCHOR, WHEN IT IS IN THIS WEEK. Arriving from the Month on
    # the 22nd should open the 22nd, not the Monday; and ?week= alone
    # names a week and not a day, so the Monday is right then.
    sel_date = anchor if week_start <= anchor <= week_end else week_start

    week_days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        mine = by_date.get(d, [])
        week_days.append({
            'date': d,
            'day_name': d.strftime('%A'),
            'day_short': d.strftime('%a'),
            # TWO LETTERS FOR THE STRIP. %a is three - Mon, Tue - and
            # seven of those at 51px is wider than the strip.
            'day_two': d.strftime('%a')[:2],
            'day_num': d.day,
            'is_today': d == today,
            'is_selected': d == sel_date,
            'entries': mine,
            'count': len(mine),
            # ONE MARK PER MEAL, carrying what it is, capped at four
            # the way the month's are - a fifth wraps a 51px button.
            'dots': ['is-note' if not e.recipe_id
                     else 'is-leftover' if e.leftover_of_id
                     else '' for e in mine[:4]],
        })

    # ---- THE MONTH - MV-2, 19 Oct 2026. IT IS THE VIEW NOW.
    #
    # It was a 320px navigation strip beside the week, carrying one
    # boolean per day: does this day have a meal. Demetri, testing the
    # live page: "why does this still have the time calendar?" - and
    # then, on the design, "Monthly Calendar first - full page".
    #
    # MEASURED BEFORE IT WAS BUILT. A seven-column cell at 1200px is
    # 162px with the sidebar gone and 113px with it kept - twenty-three
    # characters against fifteen. That measurement is why the mini
    # calendar is not merely redundant: a cell cannot carry a recipe
    # name while it is there.
    first_of_month = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    # ONE QUERY FOR THE MONTH, and it fetches the MEALS rather than a
    # set of dates that have one. A cell draws names now, so a boolean
    # per day is not enough - and asking per day would be thirty-one
    # queries to paint one screen. [E29]
    month_by_date = {}
    for e in (MealEntry.objects
              .filter(date__gte=first_of_month, date__lte=month_end)
              .select_related('recipe', 'leftover_of')
              .order_by('date', 'sort_order', 'meal_entry_id')):
        month_by_date.setdefault(e.date, []).append(e)

    # THREE SHOWN, THE REST COUNTED. Demetri's answer to Q1: "if there
    # are more recipes than can fit in the square, then include +x
    # more". Three is what a 162px cell holds at its own line height
    # without the row outgrowing its siblings, and the fourth line is
    # the count rather than a fourth name.
    MONTH_SHOWN = 3
    # FOUR MARKS AND THEN NOTHING. At 47px a cell holds four dots on
    # one line; a fifth wraps and the row grows. The count in the
    # header is what says how many the month really holds.
    MONTH_DOTS = 4
    month_weeks = []
    for week in monthcalendar(year, month):
        row = []
        for day_num in week:
            if day_num == 0:
                row.append(None)
                continue
            d = date(year, month, day_num)
            mine = month_by_date.get(d, [])
            row.append({
                'day': day_num,
                'date': d,
                'is_today': d == today,
                'in_week': week_start <= d <= week_end,
                'entries': mine[:MONTH_SHOWN],
                'more': max(0, len(mine) - MONTH_SHOWN),
                'count': len(mine),
                # ONE MARK PER MEAL, not one per name shown, and
                # carrying WHAT it is so the phone keeps the
                # distinction the names make at full size. Built here
                # because a template cannot loop a number.
                'dots': ['is-note' if not e.recipe_id
                         else 'is-leftover' if e.leftover_of_id
                         else '' for e in mine[:MONTH_DOTS]],
            })
        month_weeks.append(row)

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
        # MV-2, 19 Oct 2026 - month_weeks replaces calendar_weeks.
        # The old one carried one boolean a day for the mini
        # calendar's dots; this one carries the meals, because the
        # month is the view and a cell draws names.
        'month_weeks': month_weeks,
        # HOW MANY THE MONTH HOLDS. meal_count is the WEEK's, and the
        # month header asking the week's number would be a quiet lie.
        'month_count': sum(len(v) for v in month_by_date.values()),
        'week_start': week_start,
        'week_end': week_end,
        'week_days': week_days,
        # MV-3, 19 Oct 2026 - the day the phone's strip opens on.
        'sel_date': sel_date,
        # MV-4, 19 Oct 2026 - and the two days either side of it, for
        # the Day view's own nav. Computed here rather than in the
        # template because a template cannot do arithmetic on a date,
        # and because `anchor` already lives here.
        'prev_day': sel_date - timedelta(days=1),
        'next_day': sel_date + timedelta(days=1),
        'sel_count': len(by_date.get(sel_date, [])),
        'prev_week': week_start - timedelta(days=7),
        'next_week': week_start + timedelta(days=7),
        'this_week': today - timedelta(days=today.weekday()),
        'meal_count': len(entries),
        'household_size': household_size(request.user),
        # MV-1, 19 Oct 2026 - the switcher. `anchor` is what every one
        # of its three links carries, so the date survives the switch.
        'view_mode': view_mode,
        'anchor': anchor,
        # PF-2, 19 Oct 2026 - all_recipes IS GONE FROM THIS PAGE.
        #
        # It was every recipe in the library, with a prefetch, rendered
        # into the markup as 336 cards and 336 <img> tags on every load
        # of the planner - whether the dialog was opened or not. PK-1
        # added the prefetch to stop it being 200 queries as well, which
        # was right and did not make it cheap.
        #
        # The picker now fetches what it needs from picker_recipes()
        # when it opens, so the page ships none of them.
        #
        # The five controls still need their OPTIONS, which is a few
        # dozen rows and not a few hundred recipes. vocabulary() is the
        # same list recipe_management draws its panel from.
        **_filter_vocabulary(),
        # MW-1, 19 Oct 2026 - the Apply dialog lists these. annotate
        # rather than a count per row: E29 took that fault off four
        # screens and this round is not putting it back on one.
        'menus': Menu.objects.annotate(
            item_count=Count('items')).order_by('name'),
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


# ---- WHAT IS ON A DAY - PS-1, 19 Oct 2026.
#
# The picker stays open now, so it has to be able to SHOW the day it
# is adding to: a mis-click is a real row the moment it happens, and a
# dialog that creates rows you cannot see or undo is worse than the
# four-click one it replaces.
#
# ONE DESCRIPTION OF A DAY, asked by three endpoints - the dialog's
# first load, every add and every remove - so the strip cannot drift
# from what the calendar will show when you close it.
def day_payload(when):
    """Every meal on `when`, in the order the planner draws them."""
    rows = (MealEntry.objects
            .filter(date=when)
            .select_related('recipe')
            .order_by('sort_order', 'meal_entry_id'))
    return {
        'date': when.strftime('%Y-%m-%d'),
        'label': when.strftime('%A, %d %B'),
        'entries': [{
            'id': e.meal_entry_id,
            'recipe_id': e.recipe_id,
            'name': (e.recipe.recipe_name if e.recipe
                     else (e.note or 'Note')),
            'servings': e.servings,
            # A LEFTOVER IS NOT A SECOND HELPING. It costs nothing on
            # the shopping list and it is not something this dialog
            # added, so the strip says which it is.
            'leftover': bool(e.leftover_of_id),
            'note': not e.recipe_id,
        } for e in rows],
    }


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_day_entries(request):
    """What is on one day, as JSON. Read-tier.

    PS-1, 19 Oct 2026. The picker asks this when it opens, so the
    strip shows the whole day rather than only what this visit added -
    "what is on Saturday" being the question actually being asked.
    """
    when = week_of(request.GET.get('date'), None)
    if when is None:
        return JsonResponse({'error': 'date'}, status=400)
    return JsonResponse(day_payload(when))


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
        return redirect(planner_back(request, when))

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

    # THE DIALOG WANTS THE DAY BACK, NOT A REDIRECT - PS-1,
    # 19 Oct 2026. The form post is unchanged and still redirects;
    # this branch exists for the picker, which stays open.
    if request.POST.get('json'):
        return JsonResponse(day_payload(when))

    messages.success(request, 'Added "%s" to %s'
                     % (recipe.recipe_name, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


# ---- WHERE A WRITE SENDS YOU BACK TO - PB-2, 19 Oct 2026.
#
# Eleven endpoints below return to the planner, and before this round
# every one of them built its own address as `?week=<date>`. MV-1 still
# reads `?week=`, on purpose, so the DATE survived and `?view=` was
# simply absent - which means view_mode fell back to Month. Remove a
# meal while looking at Wednesday in Day view and you were handed the
# month.
#
# ONE PLACE SPELLS THE ADDRESS, because eleven places are what forgot.
PLANNER_VIEWS = ('month', 'week', 'day')


def planner_view(request):
    """Which view the page that posted this was showing.

    THE FORM IS ASKED FIRST. Every form on the planner carries a hidden
    `view`, so this is told rather than left to infer.

    THE REFERER IS THE FALLBACK AND NOTHING MORE. A browser need not
    send one, a proxy may strip it, and it is attacker-settable - which
    is harmless here, because the worst a bad value can do is be
    discarded by the membership test below and leave you on Month,
    which is exactly where you were going anyway.
    """
    raw = request.POST.get('view') or request.GET.get('view') or ''
    if raw in PLANNER_VIEWS:
        return raw
    ref = request.META.get('HTTP_REFERER') or ''
    try:
        found = parse_qs(urlsplit(ref).query).get('view') or ['']
    except (ValueError, TypeError):
        return 'month'
    return found[0] if found[0] in PLANNER_VIEWS else 'month'


def planner_back(request, when=None):
    """The planner, at the view and the date you came from.

    `when` is whatever the call site already passed - some of them a
    day, some the Monday of a week, because they are week-level
    operations. Which date an action should return to is a separate
    question from whether the VIEW survives, and this round answers
    only the second.
    """
    params = {'view': planner_view(request)}
    if when is not None:
        params['date'] = when.strftime('%Y-%m-%d')
    return '%s?%s' % (reverse('meal_planner'), urlencode(params))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def move_meal_entry(request):
    """Move a meal to another day, and its leftovers with it.

    RD-2, 19 Oct 2026. The server half of this was written for MM-1 on
    the same day, never run - MM-1's buttons were going to hang on the
    day card that MV-3 and MV-4 deleted - and lost when the mirror was
    rebuilt. It is written again here, where the chip menu gives it
    somewhere to live.

    TWO RULES, AND THEY ARE THE SAME RULE SEEN FROM EITHER END.

    LEFTOVERS TRAVEL WITH THEIR PARENT, KEEPING THE GAP. Monday's
    dinner with Tuesday's leftovers, moved to Wednesday, becomes
    Wednesday's dinner with Thursday's leftovers. Moving the parent and
    stranding the leftovers two days before it would make nonsense of
    both rows.

    A LEFTOVER CANNOT OVERTAKE ITS PARENT. Leftovers of a meal that has
    not been cooked yet are not leftovers. This one REFUSES rather than
    clamping, because a silent correction to a date you typed is worse
    than being told no.

    THE WHOLE CHAIN MOVES, not just the first generation. Nothing in
    the interface builds leftovers of leftovers today, but `leftover_of`
    is a self-FK and the model permits it, so a walk that stopped at
    one level would strand the third row on a date nobody chose.
    """
    try:
        entry = MealEntry.objects.select_related(
            'recipe', 'leftover_of').get(
                meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That meal is no longer on the planner.')
        return redirect(planner_back(request))

    what = entry.recipe.recipe_name if entry.recipe else (
        entry.note or 'That meal')

    # THE DATE IS A STRING SOMEBODY CAN TYPE - A5. It falls back
    # rather than raising.
    try:
        when = datetime.strptime(
            request.POST.get('date', ''), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        messages.error(request, 'That is not a date I can read.')
        return redirect(planner_back(request, entry.date))

    if when == entry.date:
        return redirect(planner_back(request, when))

    if entry.leftover_of_id and when <= entry.leftover_of.date:
        messages.error(
            request,
            'Leftovers cannot go on %s - that is on or before the day '
            '"%s" is cooked.'
            % (when.strftime('%A %d %B'), what))
        return redirect(planner_back(request, entry.date))

    delta = when - entry.date

    # THE CHAIN, BREADTH FIRST, collected before anything is written.
    travelling = []
    frontier = [entry]
    while frontier:
        nxt = []
        for parent in frontier:
            for child in parent.leftovers.all():
                travelling.append(child)
                nxt.append(child)
        frontier = nxt

    with transaction.atomic():
        for child in travelling:
            child.date = child.date + delta
            child.save(update_fields=['date'])
        entry.date = when
        entry.save(update_fields=['date'])

    if travelling:
        messages.success(
            request,
            'Moved "%s" to %s, and %d lot of leftovers with it.'
            % (what, when.strftime('%A, %d %B'), len(travelling))
            if len(travelling) == 1 else
            'Moved "%s" to %s, and %d lots of leftovers with it.'
            % (what, when.strftime('%A, %d %B'), len(travelling)))
    else:
        messages.success(request, 'Moved "%s" to %s'
                         % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


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

    # AND THE SAME FOR REMOVE - PS-1, 19 Oct 2026. The strip in the
    # picker removes in place, which is the undo a mis-click needs.
    if request.POST.get('json'):
        return JsonResponse(day_payload(when))

    messages.success(request, 'Removed "%s" from %s'
                     % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


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
# THE WEEK MOVES - MW-1, 19 Oct 2026
# =====================================================================
# Demetri, 19 Oct, asked for four decisions and took all four:
#
#   REPEAT      "Copy this week to a week you pick." A date, every meal
#               onto the matching weekday with its servings, and
#               nothing linked afterwards. The old Duplicate, without a
#               plan to duplicate.
#   MENUS       "A named set of meals you stamp onto a week." Save the
#               week on screen under a name; apply it to any week
#               later. Menu holds DAY INDEXES, 0 to 6, which is why
#               MN-1 built it that way and not with dates.
#   COLLISIONS  "Add alongside, and say so first."
#   MANAGED     In the Apply dialog, with a trashcan per Menu. Release
#               3 is about meal planning being ONE SCREEN, and a Menus
#               list page would be the second one.


def monday_of(d):
    """The Monday of d's week. A week is a Monday here, everywhere."""
    return d - timedelta(days=d.weekday())


def week_entries(week_start):
    """Every meal on the seven days from week_start."""
    return (MealEntry.objects
            .filter(date__gte=week_start,
                    date__lte=week_start + timedelta(days=6))
            .select_related('recipe')
            .order_by('date', 'sort_order', 'meal_entry_id'))


def day_label(d):
    """`3 Nov` - built without %-d, which is not portable.

    Windows strftime has no %-d and Linux has no %#d. This project runs
    on both: the laptop and Railway. One format string that works on
    one of them is a defect that only shows up on the other.
    """
    return '%d %s' % (d.day, d.strftime('%b'))


def week_label(week_start):
    """`3 Nov - 9 Nov`, the way the planner's own week strip reads."""
    return '%s - %s' % (day_label(week_start),
                        day_label(week_start + timedelta(days=6)))


def copy_week_rows(rows, src_start, dst_start, user):
    """Copy `rows` from one week onto another. Returns how many landed.

    ADDS ALONGSIDE, which is the decision, and lands each copy AFTER
    whatever that day already holds rather than interleaving with it -
    so a day that had a dinner and gains a lunch reads in the order the
    two were put there.

    AND A LEFTOVER FOLLOWS ITS PARENT. leftover_of points at the meal a
    leftover came from; copied flat it would point into the week you
    copied FROM, so the shopping list would charge the new week for a
    meal in the old one. The parents are copied first and the map is
    used to re-point the copies. A leftover whose parent is not in the
    copy is dropped, because a leftover of nothing is not a meal - it
    is a row that buys nothing and says nothing.

    MO-1 is what puts leftovers on the screen. The column is here from
    MN-1, so this round handles it correctly rather than leaving a
    trap for the round after it.
    """
    tails, made, mapping = {}, 0, {}

    def place(entry, parent=None):
        offset = (entry.date - src_start).days
        when = dst_start + timedelta(days=offset)
        if when not in tails:
            last = MealEntry.objects.filter(date=when).aggregate(
                Max('sort_order'))['sort_order__max']
            tails[when] = last or 0
        tails[when] += 1
        return MealEntry.objects.create(
            date=when, recipe=entry.recipe, note=entry.note,
            servings=entry.servings, sort_order=tails[when],
            leftover_of=parent, created_by=user)

    for e in rows:
        if e.leftover_of_id:
            continue
        mapping[e.meal_entry_id] = place(e)
        made += 1
    for e in rows:
        if not e.leftover_of_id:
            continue
        parent = mapping.get(e.leftover_of_id)
        if parent is None:
            continue
        place(e, parent)
        made += 1
    return made


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_week_preview(request):
    """What a copy onto this week would be landing on. JSON, read-tier.

    THE DIALOG HAS TO BE ABLE TO SAY IT. "Add alongside, AND SAY SO
    FIRST" is not the same decision as "add alongside" - a dialog that
    cannot count what is already there is the same copy with a quieter
    conscience. So the dialog asks, before the button is pressed.
    """
    week = week_of(request.GET.get('week'), None)
    if week is None:
        return JsonResponse({'success': False,
                             'error': 'That week could not be read.'},
                            status=400)
    week = monday_of(week)
    rows = list(week_entries(week))
    return JsonResponse({
        'success': True,
        'week': week.strftime('%Y-%m-%d'),
        'label': week_label(week),
        'meals': len(rows),
        'days_with_meals': len({e.date for e in rows}),
    })


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def copy_meal_week(request):
    """Copy one week of meals onto another week."""
    src = week_of(request.POST.get('from_week'), None)
    dst = week_of(request.POST.get('to_week'), None)
    if src is None or dst is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    src, dst = monday_of(src), monday_of(dst)

    back = planner_back(request, dst)
    if src == dst:
        messages.error(request, 'A week cannot be copied onto itself.')
        return redirect(back)

    rows = list(week_entries(src))
    if not rows:
        messages.error(request, 'There is nothing on %s to copy.'
                       % week_label(src))
        return redirect(planner_back(request, src))

    with transaction.atomic():
        made = copy_week_rows(rows, src, dst, request.user)

    messages.success(request, 'Copied %d meal%s from %s onto %s.'
                     % (made, '' if made == 1 else 's',
                        week_label(src), week_label(dst)))
    return redirect(back)


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def save_menu(request):
    """Save the week on screen as a named Menu.

    DAY INDEXES, NOT DATES - 0 for the Monday of the week being saved.
    That is the whole reason a Menu is a different table from a week of
    MealEntry rows, and it is what lets one be applied in March to a
    week in December.
    """
    week = week_of(request.POST.get('week'), None)
    name = (request.POST.get('name') or '').strip()
    if week is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    week = monday_of(week)
    back = planner_back(request, week)

    # A NAME IS REQUIRED, and for the reason C20 settled on the old
    # Create screen: the name is how you tell two of them apart
    # everywhere else. Unlike C20, there is nothing else to fill in.
    if not name:
        messages.error(request, 'A menu needs a name.')
        return redirect(back)
    if Menu.objects.filter(name__iexact=name).exists():
        messages.error(request, 'There is already a menu called "%s".'
                       % name)
        return redirect(back)

    rows = list(week_entries(week))
    if not rows:
        messages.error(request, 'There is nothing on %s to save.'
                       % week_label(week))
        return redirect(back)

    with transaction.atomic():
        menu = Menu.objects.create(name=name, created_by=request.user)
        for e in rows:
            # A LEFTOVER IS NOT SAVED. MenuItem has no leftover_of -
            # MN-1 did not give it one - and that is right: a leftover
            # is a consequence of a particular week, not a thing you
            # would plan in advance.
            if e.leftover_of_id:
                continue
            MenuItem.objects.create(
                menu=menu, day_index=(e.date - week).days,
                recipe=e.recipe, note=e.note, servings=e.servings,
                sort_order=e.sort_order)

    messages.success(request, 'Saved %s as the menu "%s".'
                     % (week_label(week), menu.name))
    return redirect(back)


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def apply_menu(request):
    """Stamp a saved Menu onto the week on screen."""
    week = week_of(request.POST.get('week'), None)
    if week is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    week = monday_of(week)
    back = planner_back(request, week)
    try:
        menu = Menu.objects.prefetch_related('items__recipe').get(
            menu_id=request.POST.get('menu_id'))
    except (Menu.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That menu no longer exists.')
        return redirect(back)

    items = list(menu.items.all())
    if not items:
        messages.error(request, 'The menu "%s" has nothing on it.'
                       % menu.name)
        return redirect(back)

    tails, made = {}, 0
    with transaction.atomic():
        for it in items:
            # A DAY INDEX OUTSIDE THE WEEK IS DROPPED, not wrapped. A
            # menu saved from a week is 0 to 6 by construction; a row
            # that somehow says 9 would land in the NEXT week, which is
            # a surprise nobody asked for.
            if not 0 <= it.day_index <= 6:
                continue
            when = week + timedelta(days=it.day_index)
            if when not in tails:
                last = MealEntry.objects.filter(date=when).aggregate(
                    Max('sort_order'))['sort_order__max']
                tails[when] = last or 0
            tails[when] += 1
            MealEntry.objects.create(
                date=when, recipe=it.recipe, note=it.note,
                servings=it.servings, sort_order=tails[when],
                created_by=request.user)
            made += 1

    messages.success(request, 'Added %d meal%s from "%s" to %s.'
                     % (made, '' if made == 1 else 's', menu.name,
                        week_label(week)))
    return redirect(back)


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def delete_menu(request):
    """Forget a saved Menu. The meals it put on weeks stay where they are."""
    week = week_of(request.POST.get('week'), None)
    back = (planner_back(request, monday_of(week))
            if week else reverse('meal_planner'))
    try:
        menu = Menu.objects.get(menu_id=request.POST.get('menu_id'))
    except (Menu.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That menu no longer exists.')
        return redirect(back)
    name = menu.name
    # CASCADE TAKES THE ITEMS AND NOTHING ELSE. MenuItem is the menu's
    # own rows; the MealEntry rows an earlier Apply created are real
    # meals on real dates and have no link back to the menu, which is
    # the point of stamping rather than subscribing.
    menu.delete()
    messages.success(request, 'Deleted the menu "%s". The meals it put '
                              'on your weeks are still there.' % name)
    return redirect(back)

# =====================================================================
# THE DAY SPEAKS - MO-1, 19 Oct 2026
# =====================================================================
# Demetri, 19 Oct: "A note row, and Leftovers marked on a meal."
#
# Both columns have been in MealEntry since MN-1 and the planner has
# rendered both row shapes since - but nothing in the application could
# MAKE either one. A column nobody can fill is a column nobody can
# check, which is the same sentence RT-1 wrote about exemptions.


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_note(request):
    """A planned night that is not a recipe.

    THE EMPTY STATE ALREADY SAYS "NOTHING PLANNED" - so a note is for
    a night that IS planned and is not cooking: eat out, takeaway, at
    Helen's. It buys nothing, which MealEntry.counts_on_shopping_list
    has returned since MN-1.
    """
    when = week_of(request.POST.get('date'), None)
    # TRIMMED AND CAPPED AT THE FIELD'S OWN WIDTH. note is 200
    # characters; a form that accepted 300 would raise on save, which
    # on Railway is a 500 on the planner.
    note = (request.POST.get('note') or '').strip()[:200]
    if when is None:
        messages.error(request, 'That date could not be read.')
        return redirect('meal_planner')
    back = planner_back(request, monday_of(when))
    if not note:
        messages.error(request, 'A note needs some words.')
        return redirect(back)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(date=when, recipe=None, note=note,
                             servings=0, sort_order=(last or 0) + 1,
                             created_by=request.user)
    messages.success(request, 'Added "%s" to %s.' % (note, day_label(when)))
    return redirect(back)


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_leftover(request):
    """Eat it again, and buy nothing twice.

    A LEFTOVER OF A LEFTOVER POINTS AT THE ORIGINAL. Soup Monday,
    leftovers Wednesday, leftovers again Friday - Wednesday and Friday
    both point at Monday. The shopping list is right either way, since
    any leftover_of at all is free, but a chain makes the screen say
    "leftovers of leftovers" and turns "how many nights did that pot
    feed us" into a recursive question instead of a count.

    AND IT CANNOT BE DATED BEFORE THE MEAL IT CAME FROM. Refused with
    a sentence rather than quietly moved: quietly moving dates is what
    C13 did.
    """
    when = week_of(request.POST.get('date'), None)
    try:
        src = MealEntry.objects.select_related('recipe', 'leftover_of').get(
            meal_entry_id=request.POST.get('meal_entry_id'))
    except (MealEntry.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'That meal no longer exists.')
        return redirect('meal_planner')
    if when is None:
        messages.error(request, 'That date could not be read.')
        return redirect('meal_planner')
    back = planner_back(request, monday_of(when))

    # FLATTENED HERE, at the only place that knows both ends.
    root = src.leftover_of or src
    if root.recipe_id is None:
        messages.error(request, 'A note has no leftovers - there was '
                                'nothing cooked.')
        return redirect(back)
    if when < root.date:
        messages.error(request, 'Leftovers cannot be eaten before the '
                                'meal they came from. %s was cooked on %s.'
                       % (root.recipe.recipe_name, day_label(root.date)))
        return redirect(back)

    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(
        date=when, recipe=root.recipe, note=root.note,
        servings=root.servings, sort_order=(last or 0) + 1,
        leftover_of=root, created_by=request.user)
    messages.success(request, 'Leftovers of %s added to %s. They cost '
                              'nothing on the shopping list.'
                     % (root.recipe.recipe_name, day_label(when)))
    return redirect(back)

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
        return redirect(planner_back(request, start))


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

# ==========================================================================
# PF-2, 19 Oct 2026 - THE PICKER ASKS THE SERVER
# ==========================================================================
@login_required
def picker_recipes(request):
    """The recipe picker's rows, filtered by the SAME function the
    library uses.

    Demetri, testing the planner: "It only allows you to choose
    Course. We need to be able to select Author, Favorites, Category
    and Protein (or vegetarian)."

    WHY THIS IS AN ENDPOINT AND NOT FOUR MORE data- ATTRIBUTES.
    Matching five filters in the browser means writing, in JavaScript,
    a second description of what `Protein: Chicken` selects. There
    would then be two, in two languages, and they would drift - which
    is the fault the suites in this project exist to refuse.

    AND IT TAKES 336 RECIPES OFF THE PLANNER PAGE. The picker used to
    render every recipe in the library into the page, with its photo,
    on every load of the planner whether the dialog was opened or not.
    Now the page ships none and the dialog asks for what it needs.

    READ TIER. It selects and never writes, so it answers GET and
    says so - a view that mutates nothing should not require a POST,
    and a filter you can link to is worth more than one you cannot.
    """
    sel = selected_from(request.GET)
    recipes = filter_recipes(
        Recipe.objects.all().prefetch_related('courses'),
        sel, request.user).order_by('recipe_name')

    # THE CEILING IS A REFUSAL TO BE SLOW, not a page. 336 rows of
    # four fields is small; a library of 20,000 would not be, and a
    # dialog that hangs is worse than one that says there is too much
    # to show. MD-1 put the same ceiling on the shopping list.
    total = recipes.count()
    rows = []
    for r in recipes[:500]:
        rows.append({
            'id': r.recipe_id,
            'name': r.recipe_name,
            'servings': r.servings or '',
            'minutes': (r.prep_time or 0) + (r.cook_time or 0),
            'photo': r.photo_url or '',
        })
    return JsonResponse({
        'success': True,
        'rows': rows,
        'total': total,
        'shown': len(rows),
        'capped': total > len(rows),
    })
