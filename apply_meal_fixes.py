# -*- coding: utf-8 -*-
"""apply_meal_fixes.py - round MP-1, 18 Oct 2026.

MEAL PLANS, RELEASE 1 - GROUPS A, B AND C.

The nineteen items from the Meal Plans design record that BREAK,
EXPOSE or LOSE DATA. Every one was reproduced in the tree on 18 Oct
before a line was written; none had already been fixed.

    A   things that fail outright          1-6
    B   security and privacy               8-12   (7 is a DECISION)
    C   data lost or wrong                 13-20

WHAT IS NOT HERE. **#7, "no scoping", is not a fix.** Demetri decided
on 18 Oct that all users see all meal plans, and the code agrees with
him: `Recipe` has no workspace field either, so plans being global
follows the module around them. Scoping meal plans would have made
them LESS consistent. Recorded in claude/decisions_kept.

TWO THINGS THE REVIEW COULD NOT HAVE KNOWN, both found by reading:

    A1'S FIX IS TWO WORDS, NOT A CHAIN. The review says "URLs pass the
    plan ID". Neither view ever USES meal_plan_id - it appears in the
    two signatures and nowhere else; add works from meal_plan_day_id
    and remove from meal_plan_recipe_id, both out of the POST body.
    And both templates already reverse the URLs with no argument:
    `{% url "add_recipe_to_meal_plan_day" %}`.

    So the parameter is deleted. Adding `<int:meal_plan_id>` would
    need both {% url %} tags changed, the JS taught where to find an
    ID, and the views would still ignore it - and on a day with no
    plan there IS no ID, which is A3. The small fix makes A3 easier;
    the large one makes it harder.

    A1 AND B8 MUST SHIP TOGETHER. Those two `created_by` checks are
    the ONLY ownership checks in the module, and they live inside the
    two views A1 proves can never run. Fix A1 alone and they come
    alive for the first time - and start refusing people the 18 Oct
    decision says are allowed. A1 without B8 turns a 500 into a "You
    do not have permission".

AND FIVE THE REVIEW UNDERSTATED OR MISPLACED:

    A2 is not "a second error". The `return redirect(...)` sits
    OUTSIDE the try and reads `meal_plan_day`, which the except path
    never assigns. The error message is set and then the redirect
    raises. Restructured so the failure path returns before anything
    can read an unbound name.

    A6 IS ONE SITE, NOT TWO. The record names shopping_list 1183 and
    1342. Line 1054-1057 already carries `|escapejs`, added by an
    earlier round; 1183 is a CSRF token. Only 1342, the plan name in
    the email POST body, is bare. Counted, not assumed.

    B10 IS NINE INTERPOLATIONS, NOT TWO ROWS. The record names
    create_meal_plan.html:565 and 1030. The same page also builds the
    recipe-selector CARD (title, image src, alt, courses, categories,
    proteins, difficulty), the RESTORE path at 712, and five FILTER
    `<option>` lists at 938-959 - all from database text, all through
    innerHTML. A fix that escapes two of nine leaves the hole open, so
    this round adds one `esc()` and routes every one of them through
    it.

    B12 IS THREE COPIES, NOT ONE. The same four names are typed into
    meal_planning.py twice AND recipe_crud.py:374, while
    `Recipe.AUTHOR_CHOICES` on the model is the actual list the column
    validates against. All three now read the model. recipe_crud.py is
    outside the meal-plans module and is fixed anyway, because leaving
    the third copy means the pickers can still disagree - which is the
    whole of B12.

    C16 IS THREE SILENT DROPS, NOT ONE. The record names
    `if not from_unit: continue` and `if data['amount'] > 0`. There is
    a third: `missing_shopping_units` is computed, put in the context,
    and THE TEMPLATE NEVER READS IT. And the first drop is the worst,
    because an ingredient line with no unit at all is recorded
    NOWHERE - the other two at least leave a trace.

WHERE THIS ROUND STOPS SHORT, DELIBERATELY, AND SAYS SO:

    C13's full fix is "meals move with the start date". That is a
    behaviour decision - whether shifting a plan by a day carries its
    meals with it or keeps them on their dates - and it belongs with
    release 3, where the calendar IS the plan. What ships here is that
    THE LOSS BECOMES VISIBLE: the browser counts what it is about to
    discard and says so before saving, and the server names what it
    removed after saving. Today both are silent, and the server's half
    is a `console.log`.

    C15's record says "rows indexed by their own ID". The Edit form
    does not post row IDs - it posts `recipes_<date>[]`, a list of
    RECIPE ids - so indexing by row ID means adding a parallel hidden
    input to three JS blocks and teaching the view to trust it. The
    same outcome falls out of keying the existing rows by recipe id to
    a LIST and consuming one per posted entry, which is four lines and
    changes no form. Two copies of a recipe on a day now survive.

    C17's record asks the calendar to show all plans in a week. That
    is release-3 markup. Here the arbitrary `.first()` becomes
    DETERMINISTIC and the reader is TOLD there are others, and Create
    and Duplicate warn when the dates overlap an existing plan.

RELEASE 1 IS DELIBERATELY NOT POLISH. D2-D13 are approved, so these
screens are temporary: MealEntry replaces the markup they live in.
Four of group C fix code release 3 deletes - C13 and C15 on the Edit
screen, C17 which the design record itself says "disappears entirely
in release 3", and C20's plan name. They are fixed anyway, MINIMALLY -
a guard, not a redesign - because C13 is losing data today and release
3 is weeks away.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealfix'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
CRUD = os.path.join('pages', 'views', 'recipes', 'recipe_crud.py')
MODELS = os.path.join('pages', 'models.py')
CAL = os.path.join('pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join('pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join('pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join('pages', 'templates', 'view_meal_plan.html')
ME = 'test_meal_fixes.py'
PATCHER = 'apply_meal_fixes.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

# B11 - THE PERMISSION MISMATCH, PER FILE AND COUNTED.
# Templates gate on can_edit_personal; every view in meal_planning.py
# gates on can_access_recipes (read) or can_edit_recipes (edit). Zero
# overlap, so a control appears and then refuses, or hides from someone
# who is allowed. Demetri, 18 Oct: "The views are right - fix the
# templates."
#
# ALL 26 SITES GATE AN EDIT CONTROL - create, edit, delete, duplicate,
# add or remove a recipe, send the email. Each was read before the
# count was written down; none gates a read-only control, so there is
# one target and not two. The counts are exact and the patcher refuses
# on any other number, because a file that grew a 27th check since the
# measurement is a file this round has not read.
PERMS = {
    CAL: 10,
    SHOP: 4,
    LIST: 7,
    VIEWT: 5,
}
PERM_WAS = 'perms.auth.can_edit_personal'
PERM_NOW = 'perms.auth.can_edit_recipes'

# =================================================================== C16
# THREE SILENT DROPS ON THE SHOPPING LIST. Two are named in the design
# record; the third is that the page is handed a list of the dropped
# ingredients and never prints it.
#
# WHAT THIS DOES NOT DO, and why. The record's second drop is
# `if data['amount'] > 0`, which keeps an ingredient out of the buy
# list when nothing converted. That line STAYS. Every ingredient it
# drops is one of exactly two kinds - no unit on the recipe line, or no
# shopping unit on the ingredient - and once both are tracked and both
# are printed, every one of them is named on the page. The alternative
# is a row reading "0 g Flour" in a list headed "Items to Buy", which
# is a worse answer than a banner saying Flour has no shopping unit.
# Measured, not skipped.
TRACK_WAS = """    # Track issues
    missing_conversions = []
    missing_shopping_units = []
    seen_missing_conversions = set()
    seen_missing_units = set()"""
TRACK_NOW = """    # Track issues
    missing_conversions = []
    missing_shopping_units = []
    # MP-1, 18 Oct 2026 - C16. A recipe line with NO UNIT at all was
    # dropped by `if not from_unit: continue` below and recorded
    # nowhere: not in the list, not in a warning, not in a log. The
    # other two drops at least left a trace. This is the trace.
    missing_units = []
    seen_missing_conversions = set()
    seen_missing_units = set()
    seen_no_unit = set()"""

NOUNIT_WAS = """                if not from_unit:
                    continue"""
NOUNIT_NOW = """                if not from_unit:
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
                    continue"""

RET_WAS = """    return (dict(categorized_ingredients), missing_conversions, missing_shopping_units)"""
RET_NOW = """    # MP-1, 18 Oct 2026 - C16. A FOURTH ELEMENT, and the one caller
    # updated with it. Folding the no-unit lines into
    # missing_shopping_units would have been smaller and would have
    # made that name a lie: those are two different faults with two
    # different fixes - one is a recipe to correct, one is an
    # ingredient to configure - and the page says so separately.
    return (dict(categorized_ingredients), missing_conversions,
            missing_shopping_units, missing_units)"""

DOC_WAS = """    Aggregate ingredients and convert to shopping units.
    Always uses the ingredient's shopping unit. Prompts for missing conversions.
    Returns: (aggregated_dict, missing_conversions_list, missing_shopping_units_list)
    \"\"\""""
DOC_NOW = """    Aggregate ingredients and convert to shopping units.
    Always uses the ingredient's shopping unit. Prompts for missing conversions.

    Returns a FOUR-tuple:

        (aggregated_dict, missing_conversions, missing_shopping_units,
         missing_units)

    MP-1, 18 Oct 2026 - C16. `missing_units` is new: recipe ingredient
    lines that carry no unit at all. They were dropped silently.
    \"\"\""""

SHOPCALL_WAS = """        ingredients, missing_conversions, missing_shopping_units = aggregate_meal_plan_ingredients(meal_plan)"""
SHOPCALL_NOW = """        (ingredients, missing_conversions, missing_shopping_units,
         missing_units) = aggregate_meal_plan_ingredients(meal_plan)"""

CTX_WAS = """            'has_missing_conversions': len(missing_conversions) > 0,
            'has_missing_shopping_units': len(missing_shopping_units) > 0,
            'has_issues': has_issues,"""
CTX_NOW = """            'has_missing_conversions': len(missing_conversions) > 0,
            # MP-1, 18 Oct 2026 - C16. has_missing_shopping_units has
            # been in this context all along and no template ever read
            # it, so an ingredient with no shopping unit vanished from
            # the list in silence. The page prints both lists now.
            'has_missing_shopping_units': len(missing_shopping_units) > 0,
            'missing_shopping_units_list': missing_shopping_units,
            'missing_units_list': missing_units,
            'has_missing_units': len(missing_units) > 0,
            'has_issues': has_issues,"""

ISSUES_WAS = """        has_issues = len(missing_conversions) > 0 or len(missing_shopping_units) > 0"""
ISSUES_NOW = """        has_issues = (len(missing_conversions) > 0
                      or len(missing_shopping_units) > 0
                      or len(missing_units) > 0)"""

# ============================================================ C20+C14+C17
# CREATE. Three items meet in one block, so it is replaced whole.
#
#   C20  a blank plan name was accepted here and refused on Edit
#   C14  nothing wrapped the day/recipe loop, so a bad recipe id left
#        a plan with some of its days
#   C17  overlapping plans are allowed and the calendar can only show
#        one of them, so the second one's meals become invisible
CREATE_WAS = """    if request.method == 'POST':
        try:
            plan_name = request.POST.get('plan_name')
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            days_diff = (end_date - start_date).days + 1
            if days_diff < 1 or days_diff > 7:
                messages.error(request, 'Meal plan must be between 1 and 7 days.')
                return redirect('create_meal_plan')

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
            return redirect('view_meal_plan', meal_plan_id=meal_plan.meal_plan_id)"""

CREATE_NOW = """    if request.method == 'POST':
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
            return redirect('view_meal_plan', meal_plan_id=meal_plan.meal_plan_id)"""

# =================================================================== B12
# THE AUTHOR PICKER, TYPED OUT THREE TIMES.
#
# Recipe.author is `choices=AUTHOR_CHOICES` - the model already holds
# the list the column validates against. Three places type the same
# four names out by hand instead: twice here and once in
# recipe_crud.py. Add a fifth author to the model and all three pickers
# keep offering four.
#
# The design record says "authors read from household members". They
# are NOT the same list - HouseholdMember is people, AUTHOR_CHOICES
# includes "General", which is not a person - and the column would
# refuse a member who is not in the choices. The model is the honest
# source; moving the column to a foreign key is a release-2 decision.
AUTHORS_WAS = """    all_authors = [
        {'value': 'General', 'name': 'General'},
        {'value': 'Demetri & Angy', 'name': 'Demetri & Angy'},
        {'value': 'Erene', 'name': 'Erene'},
        {'value': 'Alexandra', 'name': 'Alexandra'},
    ]"""
AUTHORS_NOW = """    # MP-1, 18 Oct 2026 - B12. The model's own choices. This list was
    # typed out by hand in three places, including recipe_crud.py, and
    # Recipe.author validates against AUTHOR_CHOICES - so a name added
    # to the model never reached any of the three pickers.
    all_authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]"""

CRUD_WAS = """    authors = [
        {'value': 'General', 'name': 'General'},
        {'value': 'Demetri & Angy', 'name': 'Demetri & Angy'},
        {'value': 'Erene', 'name': 'Erene'},
        {'value': 'Alexandra', 'name': 'Alexandra'},
    ]"""
CRUD_NOW = """    # MP-1, 18 Oct 2026 - B12. The third copy of the hand-typed author
    # list. It is outside the meal-plans module and is fixed here
    # anyway: the fault B12 names is that the pickers can disagree with
    # the model, and leaving one copy behind leaves that true.
    authors = [{'value': v, 'name': n} for v, n in Recipe.AUTHOR_CHOICES]"""

# =============================================================== C13+C15
# EDIT. Two items, both in the save path, both losing meals.
DROP_WAS = """                dates_to_keep = set(new_dates)
                for date_obj, day in existing_days.items():
                    if date_obj not in dates_to_keep:
                        day.delete()"""
DROP_NOW = """                # MP-1, 18 Oct 2026 - C13. COUNT WHAT GOES. Shortening
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
                        day.delete()"""

SAME_WAS = """                    existing_recipes = {mr.recipe.recipe_id: mr for mr in meal_day.recipes.all()}
                    recipes_to_keep = set()

                    for idx, recipe_id in enumerate(recipe_ids):
                        if recipe_id:
                            recipe_id = int(recipe_id)
                            recipes_to_keep.add(recipe_id)

                            recipe = Recipe.objects.get(recipe_id=recipe_id)
                            servings = int(servings_list[idx]) if idx < len(servings_list) else recipe.servings

                            if recipe_id in existing_recipes:
                                meal_recipe = existing_recipes[recipe_id]
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

                    for recipe_id, meal_recipe in existing_recipes.items():
                        if recipe_id not in recipes_to_keep:
                            meal_recipe.delete()"""
SAME_NOW = """                    # MP-1, 18 Oct 2026 - C15. A QUEUE PER RECIPE, NOT
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
                            meal_recipe.delete()"""

EDOK_WAS = """            messages.success(request, f'Meal plan "{new_plan_name}" updated successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan_id)"""
EDOK_NOW = """            # MP-1, 18 Oct 2026 - C13. SAY WHAT WAS REMOVED. A
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
            return redirect('view_meal_plan', meal_plan_id=meal_plan_id)"""

# =============================================================== C14+C17
# DUPLICATE. Unwrapped, like Create, and it silently drops the order of
# the meals it copies.
DUP_WAS = """            try:
                # Parse the new start date
                new_start = datetime.strptime(new_start_date, '%Y-%m-%d').date()

                # Calculate duration of original plan
                duration = (original_plan.end_date - original_plan.start_date).days
                new_end = new_start + timedelta(days=duration)

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
                    for meal_recipe in day.recipes.all():
                        MealPlanRecipe.objects.create(
                            meal_plan_day=new_day,
                            recipe=meal_recipe.recipe,
                            servings=meal_recipe.servings
                        )

                # Check if user wants to delete original (shift functionality)
                delete_original = request.POST.get('delete_original') == 'yes'

                if delete_original:"""
DUP_NOW = """            try:
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

                if delete_original:"""

# ==================================================================== A5
# THE CALENDAR'S ADDRESS BAR. ?year=abc is a 500. So is ?month=13, on
# the line after, because date(year, 13, 1) raises - and so is
# ?year=99999 on date(year + 1, 1, 1) in December. All three fall back.
ADDR_WAS = """    # Get requested month/year or default to current
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Get selected week start date (Monday)
    selected_week_start = request.GET.get('week')
    if selected_week_start:
        selected_week_start = datetime.strptime(selected_week_start, '%Y-%m-%d').date()
    else:
        # Default to current week (find Monday)
        selected_week_start = today - timedelta(days=today.weekday())"""
ADDR_NOW = """    # Get requested month/year or default to current
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
        selected_week_start = today - timedelta(days=today.weekday())"""

# =================================================================== C17
# THE CALENDAR PICKS ONE PLAN FOR THE WEEK AND NEVER SAYS SO.
SEL_WAS = """    # Get the meal plan for the selected week (if any)
    selected_meal_plan = MealPlan.objects.filter(
        start_date__lte=selected_week_end,
        end_date__gte=selected_week_start
    ).first()"""
SEL_NOW = """    # Get the meal plan for the selected week (if any)
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
            % (len(week_plans), selected_meal_plan.plan_name))"""

# =============================================================== B9+C18
# THE EMAIL ENDPOINT. Everything it sent came out of the request body:
# the recipient, the plan name, the date range, the recipe count and
# every line of the list. Any signed-in user with can_edit_recipes
# could send arbitrary HTML to an arbitrary address, from the
# application's own From address.
#
# C18 is the same block: `total_recipes` was the DAY count, so the
# email said "7 recipes" about a seven-day plan.
#
# THE INGREDIENTS STILL COME FROM THE BROWSER - and that is on
# purpose. The page's list is what the reader resolved conversions for
# and ticked items off; re-deriving it on the server would email a
# different list from the one on the screen. What changes is that the
# recipient must be on the roster, the plan must be one the server
# looked up, the name, dates and count come from that plan, and every
# value is escaped before it reaches the HTML.
MAIL_WAS = """    try:
        data = json.loads(request.body)

        meal_plan_name = data.get('meal_plan_name')
        date_range = data.get('date_range')
        total_recipes = data.get('total_recipes')
        email = data.get('email')
        ingredients_by_category = data.get('ingredients', {})

        # Validate
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address is required'}, status=400)

        if not ingredients_by_category:
            return JsonResponse({'success': False, 'error': 'No ingredients to send'}, status=400)"""
MAIL_NOW = """    try:
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
            meal_plan_day__meal_plan=plan).count()"""

# EVERY VALUE THAT REACHES THE HTML IS ESCAPED. The categories and the
# ingredient lines genuinely come from the browser, so they are the
# ones that needed it; the plan name is escaped too, because a name
# with an angle bracket in it is a name, not markup.
IMP_WAS = """from django.utils import timezone"""
IMP_NOW = """from django.utils import timezone
# MP-1, 18 Oct 2026 - B9. The shopping-list email interpolated every
# value straight into HTML.
from django.utils.html import escape"""

H1_WAS = """        <p><strong>{meal_plan_name}</strong></p>"""
H1_NOW = """        <p><strong>{escape(meal_plan_name)}</strong></p>"""

CATH_WAS = """        <div class="category-header">{category}</div>"""
CATH_NOW = """        <div class="category-header">{escape(category)}</div>"""

LI_WAS = """                <span><span class="quantity">{qty_str} {item['unit']}</span> {item['ingredient']}</span>"""
LI_NOW = """                <span><span class="quantity">{qty_str} {escape(item['unit'])}</span> {escape(item['ingredient'])}</span>"""

# ============================================================== MODULE DOC
MDOC_WAS = """- aggregate_meal_plan_ingredients : Shared helper (no request). Walks every
                                    recipe in a meal plan, converts each
                                    ingredient to its shopping unit (via the
                                    conversion layer in recipes/conversions.py),
                                    smart-rounds UP, and reports missing
                                    conversions / missing shopping units."""
MDOC_NOW = """- aggregate_meal_plan_ingredients : Shared helper (no request). Walks every
                                    recipe in a meal plan, converts each
                                    ingredient to its shopping unit (via the
                                    conversion layer in recipes/conversions.py),
                                    smart-rounds UP, and reports missing
                                    conversions / missing shopping units /
                                    recipe lines with no unit at all.
                                    MP-1, 18 Oct 2026: returns a FOUR-tuple -
                                    the fourth element is new and was dropped
                                    silently before."""

# ============================================================= THE DOCSTRING
# One stale sentence in models.py, found while checking whether meal
# plans should be scoped. Workspace claims Recipes are tenanted; only
# Passports carry the field. The docstring sent a whole session looking
# for scoping that does not exist. No behaviour changes.
WS_WAS = '''    """A tenancy boundary for Personal-module data (Passports, Celebrations,
    Recipes).

    Every tenanted record (passport, celebration, recipe, ingredient, etc.)
    references exactly one Workspace; users belong to exactly one Workspace
    (via UserProfile.workspace) and see only the data within it.'''
WS_NOW = '''    """A tenancy boundary for Personal-module data (Passports,
    Celebrations).

    Every tenanted record references exactly one Workspace; users belong to
    exactly one Workspace (via UserProfile.workspace) and see only the data
    within it.

    MP-1, 18 Oct 2026. THIS DOCSTRING USED TO NAME RECIPES among the
    tenanted records, twice - "(Passports, Celebrations, Recipes)" and
    "(passport, celebration, recipe, ingredient, etc.)". Only Passports and
    Celebrations actually carry the field. `Recipe` has no workspace at all -
    its `created_by` is a plain CharField, not even a user link - so recipes,
    ingredients and meal plans are global across the installation.

    It cost a session: this text sent MP-1 looking for meal-plan scoping that
    does not exist. It is a recorded position now rather than an oversight.
    Demetri decided on 18 Oct that all users see all meal plans, and the code
    already agreed with him - plans built from global recipes being global
    follows the module around them. The cost is nil while there is one
    household. If a second one ever uses the system, recipes and meal plans
    are the two things that would not separate.'''


# ===================================================================== A3
# `addRecipeToDay({{ day.meal_plan_day_id }}, ...)` on a day with no
# MealPlanDay row renders the literal `None`, which is not a JS value -
# so the click is a ReferenceError before the function body runs, and
# no guard inside the function can help. It has to be fixed in the
# markup.
#
# A week always shows seven days. A plan shorter than seven covers
# fewer, so a three-day plan puts FOUR dead buttons on the page.
#
# The button goes, and says why. The record asks for "button hidden on
# days with no plan"; a button that vanishes with nothing in its place
# reads as a page that forgot to render, and the reader's actual next
# step - lengthen the plan - is one link away.
A3_WAS = """                                <div class="empty-day">
                                    <i class="fas fa-utensils"></i>
                                    <p>No meal planned</p>
                                    {% if perms.auth.can_edit_recipes %}
                                    <button class="add-recipe-btn" onclick="addRecipeToDay({{ day.meal_plan_day_id }}, '{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                        <i class="fas fa-plus"></i> Add Recipe
                                    </button>
                                    {% else %}
                                    <button class="add-recipe-btn add-recipe-btn-disabled" disabled title="No permission to add recipes">
                                        <i class="fas fa-plus"></i> Add Recipe
                                    </button>
                                    {% endif %}
                                </div>"""
A3_NOW = """                                <div class="empty-day">
                                    <i class="fas fa-utensils"></i>
                                    <p>No meal planned</p>
                                    {# MP-1, 18 Oct 2026 - A3. THE BUTTON NEEDS A DAY TO    #}
                                    {# ADD TO. A week shows seven days; a plan shorter      #}
                                    {# than seven has no MealPlanDay row for the rest, and  #}
                                    {# day.meal_plan_day_id rendered the literal `None`     #}
                                    {# into the onclick - a ReferenceError on click, before #}
                                    {# the function was even entered. A three-day plan put  #}
                                    {# four of them on the page.                            #}
                                    {#                                                      #}
                                    {# Release 3 lets any day take meals. Until then the    #}
                                    {# reader is pointed at the thing that would actually   #}
                                    {# work - lengthening the plan - instead of at a        #}
                                    {# control that cannot.                                 #}
                                    {% if day.meal_plan_day_id %}
                                    {% if perms.auth.can_edit_recipes %}
                                    <button class="add-recipe-btn" onclick="addRecipeToDay({{ day.meal_plan_day_id }}, '{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                        <i class="fas fa-plus"></i> Add Recipe
                                    </button>
                                    {% else %}
                                    <button class="add-recipe-btn add-recipe-btn-disabled" disabled title="No permission to add recipes">
                                        <i class="fas fa-plus"></i> Add Recipe
                                    </button>
                                    {% endif %}
                                    {% else %}
                                    <p class="text-muted">This date is outside
                                    {% if selected_meal_plan %}&ldquo;{{ selected_meal_plan.plan_name }}&rdquo;{% else %}the plan{% endif %}.
                                    {% if perms.auth.can_edit_recipes and selected_meal_plan %}
                                    <a href="{% url 'edit_meal_plan' selected_meal_plan.meal_plan_id %}?from=calendar&amp;week={{ selected_week_start|date:'Y-m-d' }}">Change the dates</a>
                                    to plan a meal for it.
                                    {% endif %}
                                    </p>
                                    {% endif %}
                                </div>"""

# The OTHER call site - "Add Another Recipe", which only renders inside
# `{% if day.recipes %}`. A day WITH recipes always has a row, so this
# one cannot render None today. It is guarded anyway, because that is a
# fact about the view's shape and not about this template, and the next
# person to read it should not have to prove it again.
A3B_WAS = """                                {% if perms.auth.can_edit_recipes %}
                                <button class="add-another-btn" onclick="addRecipeToDay({{ day.meal_plan_day_id }}, '{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                    <i class="fas fa-plus"></i> Add Another Recipe
                                </button>"""
A3B_NOW = """                                {# MP-1, 18 Oct 2026 - A3, the second call site. This one #}
                                {# renders only inside {% if day.recipes %}, and a day     #}
                                {# with recipes always has a MealPlanDay row - so it       #}
                                {# cannot pass None today. Guarded regardless: that is a   #}
                                {# fact about the view's shape, not about this template.   #}
                                {% if perms.auth.can_edit_recipes and day.meal_plan_day_id %}
                                <button class="add-another-btn" onclick="addRecipeToDay({{ day.meal_plan_day_id }}, '{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                    <i class="fas fa-plus"></i> Add Another Recipe
                                </button>"""

# NO NEW CLASS FOR THE NOTE. `.text-muted` is already on this page -
# the recipe options use it - so the note needs no CSS and the round
# adds no selector anyone has to learn.
# ==================================================================== C19
# THE PICKER'S SERVINGS BOX. Hard-coded to 4, and never reset, so the
# number left behind by the last recipe was offered for the next one.
# The server's half of C19 is in add_recipe_to_meal_plan_day.
C19A_WAS = """                        <div class="recipe-option" data-recipe-id="{{ recipe.recipe_id }}" data-recipe-name="{{ recipe.recipe_name|lower }}" onclick="selectRecipeOption(this)">"""
C19A_NOW = """                        {# MP-1, 18 Oct 2026 - C19. The recipe's own yield, carried #}
                        {# on the option so the servings box can read it.            #}
                        <div class="recipe-option" data-recipe-id="{{ recipe.recipe_id }}" data-recipe-servings="{{ recipe.servings|default:4 }}" data-recipe-name="{{ recipe.recipe_name|lower }}" onclick="selectRecipeOption(this)">"""

C19B_WAS = """                <div class="form-group">
                    <label><strong>Servings</strong></label>
                    <input type="number" class="form-control" id="recipeServings" value="4" min="1" style="max-width: 100px;">
                </div>"""
C19B_NOW = """                <div class="form-group">
                    <label><strong>Servings</strong></label>
                    {# MP-1, 18 Oct 2026 - C19. No value="4". The box is filled #}
                    {# from the recipe that gets picked, and emptied when the   #}
                    {# modal opens - it used to arrive carrying whatever the    #}
                    {# last recipe was set to.                                  #}
                    <input type="number" class="form-control" id="recipeServings" min="1" placeholder="4" style="max-width: 100px;">
                </div>"""

C19C_WAS = """function addRecipeToDay(dayId, date, dayName) {
    document.getElementById('addRecipeDayId').value = dayId;
    document.getElementById('addRecipeDate').value = date;
    document.getElementById('addRecipeDayName').textContent = dayName;
    selectedRecipeId = null;
    document.getElementById('confirmAddRecipeBtn').disabled = true;"""
C19C_NOW = """function addRecipeToDay(dayId, date, dayName) {
    document.getElementById('addRecipeDayId').value = dayId;
    document.getElementById('addRecipeDate').value = date;
    document.getElementById('addRecipeDayName').textContent = dayName;
    selectedRecipeId = null;
    // MP-1, 18 Oct 2026 - C19. RESET ON EVERY OPEN. The box kept the
    // number the last recipe put there, so the second recipe of the
    // evening was planned for the first one's household.
    document.getElementById('recipeServings').value = '';
    document.getElementById('confirmAddRecipeBtn').disabled = true;"""

C19D_WAS = """    element.style.background = 'var(--alv-accent-soft)';
    selectedRecipeId = element.dataset.recipeId;
    document.getElementById('confirmAddRecipeBtn').disabled = false;"""
C19D_NOW = """    element.style.background = 'var(--alv-accent-soft)';
    selectedRecipeId = element.dataset.recipeId;
    // MP-1, 18 Oct 2026 - C19. THE RECIPE'S OWN YIELD. The box was
    // hard-coded to 4 in the markup and the server fell back to 4 as
    // well, so a recipe for six was planned for four at both ends.
    // Household size takes over in release 2.
    const servingsBox = document.getElementById('recipeServings');
    if (servingsBox && !servingsBox.value) {
        servingsBox.value = element.dataset.recipeServings || '';
    }
    document.getElementById('confirmAddRecipeBtn').disabled = false;"""

# ===================================================================== A4
# BOOTSTRAP 5 CALLS ON A BOOTSTRAP 4.1.3 PAGE. base.html loads
# bootstrap@4.1.3, where there is no `window.bootstrap` at all - the
# modal plugin is a jQuery method. So `new bootstrap.Modal(...)` is a
# TypeError and the recipe selector has never opened from this page;
# `.getInstance(...)` is the same fault on the way out.
#
# Every other modal in the tree, the calendar's included, uses the
# jQuery form. These two now match them.
BS1_WAS = """    const modal = new bootstrap.Modal(document.getElementById('recipeSelectorModal'));
    modal.show();"""
BS1_NOW = """    // MP-1, 18 Oct 2026 - A4. base.html loads bootstrap@4.1.3, where
    // there is no window.bootstrap: the modal is a jQuery plugin. This
    // was `new bootstrap.Modal(...)`, a Bootstrap 5 call, so it threw
    // a TypeError and the selector never opened.
    $('#recipeSelectorModal').modal('show');"""

BS2_WAS = """    const modal = bootstrap.Modal.getInstance(document.getElementById('recipeSelectorModal'));
    modal.hide();"""
BS2_NOW = """    // MP-1, 18 Oct 2026 - A4, the same fault on the way out.
    $('#recipeSelectorModal').modal('hide');"""

# ==================================================================== B10
# RECIPE NAMES AS RAW HTML. Nine interpolations of database text into
# innerHTML on one page: the row on Create, the row on Edit, the row on
# restore, the selector card's title, image source and alt text, its
# difficulty, course, category and protein badges, and five filter
# <option> lists. A recipe named with an angle bracket in it is markup
# on this page.
#
# ONE HELPER, AND IT ESCAPES QUOTES. The house has two spellings of
# this. The textContent/innerHTML trick - nmEscapeHtml in
# ingredient_base_units_management.html - is right for a text node and
# WRONG here, because three of these sites are inside a double-quoted
# attribute and it leaves `"` alone. fsr.html's spelling escapes the
# quote; this is that, plus the apostrophe.
ESC_WAS = """
// Parse JSON data from Django
const recipes = JSON.parse('{{ recipes_json|escapejs }}');"""
ESC_NOW = """
// MP-1, 18 Oct 2026 - B10. EVERY PIECE OF DATABASE TEXT THAT REACHES
// innerHTML ON THIS PAGE GOES THROUGH HERE.
//
// Nine sites: the recipe row on Create, on Edit and on restore, the
// selector card's title, image src and alt, its difficulty, course,
// category and protein badges, and five filter <option> lists. All of
// it is recipe text somebody typed.
//
// NOT the textContent/innerHTML trick the house uses elsewhere
// (nmEscapeHtml, in ingredient_base_units_management.html). That is
// correct for a text node and wrong here: three of these sites sit
// inside a double-quoted attribute and it does not touch `"`.
function esc(s) {
    return String(s === null || s === undefined ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Parse JSON data from Django
const recipes = JSON.parse('{{ recipes_json|escapejs }}');"""

B10A_WAS = """                <input type="hidden" name="recipes_${day.date}[]" value="${recipe.recipe_id}">
                <div style="flex: 1;">
                    <strong>${recipe.recipe_name}</strong>
                </div>"""
B10A_NOW = """                <input type="hidden" name="recipes_${day.date}[]" value="${recipe.recipe_id}">
                <div style="flex: 1;">
                    <strong>${esc(recipe.recipe_name)}</strong>
                </div>"""

B10B_WAS = """                <input type="hidden" name="recipes_${dateStr}[]" value="${recipe.recipeId}">
                <div style="flex: 1;">
                    <strong>${recipe.recipeName}</strong>
                </div>"""
B10B_NOW = """                <input type="hidden" name="recipes_${dateStr}[]" value="${recipe.recipeId}">
                <div style="flex: 1;">
                    <strong>${esc(recipe.recipeName)}</strong>
                </div>"""

B10C_WAS = """        <input type="hidden" name="recipes_${currentMealPlanDate}[]" value="${recipeId}">
        <div style="flex: 1;">
            <strong>${recipeName}</strong>
        </div>"""
B10C_NOW = """        <input type="hidden" name="recipes_${currentMealPlanDate}[]" value="${recipeId}">
        <div style="flex: 1;">
            <strong>${esc(recipeName)}</strong>
        </div>"""

B10D_WAS = """    allCourses.forEach(course => {
        courseSelect.innerHTML += `<option value="${course.name}">${course.name}</option>`;
    });"""
B10D_NOW = """    allCourses.forEach(course => {
        courseSelect.innerHTML += `<option value="${esc(course.name)}">${esc(course.name)}</option>`;
    });"""

B10E_WAS = """    allCategories.forEach(cat => {
        categorySelect.innerHTML += `<option value="${cat.name}">${cat.name}</option>`;
    });"""
B10E_NOW = """    allCategories.forEach(cat => {
        categorySelect.innerHTML += `<option value="${esc(cat.name)}">${esc(cat.name)}</option>`;
    });"""

B10F_WAS = """    allProteins.forEach(protein => {
        proteinSelect.innerHTML += `<option value="${protein.name}">${protein.name}</option>`;
    });"""
B10F_NOW = """    allProteins.forEach(protein => {
        proteinSelect.innerHTML += `<option value="${esc(protein.name)}">${esc(protein.name)}</option>`;
    });"""

B10G_WAS = """    allAuthors.forEach(author => {
        authorSelect.innerHTML += `<option value="${author.value}">${author.name}</option>`;
    });"""
B10G_NOW = """    allAuthors.forEach(author => {
        authorSelect.innerHTML += `<option value="${esc(author.value)}">${esc(author.name)}</option>`;
    });"""

B10H_WAS = """        imageHtml = `<img loading="lazy" decoding="async" src="${recipe.recipe_image}" class="recipe-selector-card-image" alt="${recipe.recipe_name}">`;"""
B10H_NOW = """        imageHtml = `<img loading="lazy" decoding="async" src="${esc(recipe.recipe_image)}" class="recipe-selector-card-image" alt="${esc(recipe.recipe_name)}">`;"""

B10I_WAS = """        metaHtml += `<span class="recipe-selector-card-badge"><i class="fas fa-signal"></i> ${recipe.difficulty_level}</span>`;"""
B10I_NOW = """        metaHtml += `<span class="recipe-selector-card-badge"><i class="fas fa-signal"></i> ${esc(recipe.difficulty_level)}</span>`;"""

B10J_WAS = """    recipe.courses.forEach(course => {
        tagsHtml += `<span class="recipe-selector-card-badge" style="background: #0e7c8b; color: white;">${course}</span>`;
    });
    recipe.categories.forEach(cat => {
        tagsHtml += `<span class="recipe-selector-card-badge" style="background: var(--alv-accent); color: white;">${cat}</span>`;
    });"""
B10J_NOW = """    recipe.courses.forEach(course => {
        tagsHtml += `<span class="recipe-selector-card-badge" style="background: #0e7c8b; color: white;">${esc(course)}</span>`;
    });
    recipe.categories.forEach(cat => {
        tagsHtml += `<span class="recipe-selector-card-badge" style="background: var(--alv-accent); color: white;">${esc(cat)}</span>`;
    });"""

B10K_WAS = """        recipe.proteins.forEach(protein => {
            tagsHtml += `<span class="recipe-selector-card-badge" style="background: var(--alv-spice); color: white;">${protein}</span>`;
        });"""
B10K_NOW = """        recipe.proteins.forEach(protein => {
            tagsHtml += `<span class="recipe-selector-card-badge" style="background: var(--alv-spice); color: white;">${esc(protein)}</span>`;
        });"""

B10L_WAS = """            <div class="recipe-selector-card-title">${recipe.recipe_name}</div>"""
B10L_NOW = """            <div class="recipe-selector-card-title">${esc(recipe.recipe_name)}</div>"""

# ==================================================================== C13
# THE BROWSER HALF. Changing the dates on Edit regenerates the day
# cards and then tries to put the recipes back by DATE - so a date that
# is no longer in range loses its meals, and the only record of it was
# a console.log nobody reads. The design record points at this exact
# line.
#
# A note, in a place on the page, before the save. The warning says
# what it is about to cost, and the save button still works - the
# reader may well mean it.
C13T_WAS = """            <div id="daysContainer">
                <!-- Days will be dynamically added here -->
            </div>"""
C13T_NOW = """            {# MP-1, 18 Oct 2026 - C13. A PLACE FOR THE PAGE TO SAY     #}
            {# WHAT CHANGING THE DATES WILL COST. Shortening a plan, or  #}
            {# moving its start, drops the meals on the days that fall   #}
            {# outside the new range - and the only trace of it was a    #}
            {# console.log. Empty unless there is something to say.      #}
            <div id="dateChangeNote" role="status" aria-live="polite"></div>

            <div id="daysContainer">
                <!-- Days will be dynamically added here -->
            </div>"""

C13J_WAS = """        if (!recipeList) {
            console.log(`Date ${dateStr} no longer exists in range - recipes discarded`);
            return;
        }"""
C13J_NOW = """        if (!recipeList) {
            // MP-1, 18 Oct 2026 - C13. COUNTED, NOT LOGGED. This used
            // to be a console.log, so meals left the plan with nothing
            // on the screen to say they had.
            droppedDates += 1;
            droppedMeals += (savedRecipes[dateStr] || []).length;
            return;
        }"""

C13J2_WAS = """function restoreRecipes(savedRecipes) {
    console.log('Restoring recipes...');

    Object.keys(savedRecipes).forEach(dateStr => {"""
C13J2_NOW = """function restoreRecipes(savedRecipes) {
    console.log('Restoring recipes...');

    // MP-1, 18 Oct 2026 - C13. Returns what it could not put back.
    let droppedDates = 0;
    let droppedMeals = 0;

    Object.keys(savedRecipes).forEach(dateStr => {"""

C13J3_WAS = """        console.log(`Restored ${savedRecipes[dateStr].length} recipes for ${dateStr}`);
    });
}"""
C13J3_NOW = """        console.log(`Restored ${savedRecipes[dateStr].length} recipes for ${dateStr}`);
    });

    return { dates: droppedDates, meals: droppedMeals };
}"""

C13J4_WAS = """    // In edit mode, restore recipes for days that still exist
    if (editMode && Object.keys(savedRecipes).length > 0) {
        restoreRecipes(savedRecipes);
    }
}"""
C13J4_NOW = """    // In edit mode, restore recipes for days that still exist
    const note = document.getElementById('dateChangeNote');
    if (note) { note.innerHTML = ''; }
    if (editMode && Object.keys(savedRecipes).length > 0) {
        // MP-1, 18 Oct 2026 - C13. SAY SO BEFORE THE SAVE. The dropped
        // meals used to go to the console. The save button is left
        // enabled: shortening a plan on purpose is a normal thing to
        // do, and this is a warning, not a refusal.
        const dropped = restoreRecipes(savedRecipes);
        if (note && dropped && dropped.meals > 0) {
            note.innerHTML = '<div class="alert alert-warning">'
                + '<i class="fas fa-exclamation-triangle"></i> '
                + '<strong>' + dropped.meals + ' meal'
                + (dropped.meals === 1 ? '' : 's')
                + '</strong> on ' + dropped.dates + ' day'
                + (dropped.dates === 1 ? '' : 's')
                + ' fall outside the new dates and will be removed when you '
                + 'save.</div>';
        }
    }
}"""

# ===================================================================== A6
# ONE SITE, counted rather than taken from the record - which names two
# (1183 and 1342). 1183 is the CSRF token; the ingredient rows at
# 1054-1057 already carry |escapejs from an earlier round. Only the
# plan name in the email POST body is bare, and a plan called
# "Yiayia's week" ends the string early and breaks every script below
# it on the page.
#
# B9 AND C18 ARE THE SAME FOUR LINES. The name, the date range and the
# count are no longer sent at all - the server reads them off the plan,
# which is what made the endpoint an open relay. What goes up is the
# plan's id and the list on the screen.
A6_WAS = """            body: JSON.stringify({
                email: email,
                meal_plan_name: '{{ meal_plan.plan_name }}',
                date_range: '{{ meal_plan.start_date|date:"M d" }} - {{ meal_plan.end_date|date:"M d, Y" }}',
                total_recipes: {{ meal_plan.days.count }},
                ingredients: finalList
            })"""
A6_NOW = """            {# MP-1, 18 Oct 2026 - A6, B9 and C18 are one change here.   #}
            {#                                                           #}
            {# A6: the plan name went up inside a single-quoted JS string #}
            {# with no |escapejs, so "Yiayia's week" closed the string    #}
            {# and broke every script after it.                          #}
            {#                                                           #}
            {# B9: the name, the dates and the count are not sent any    #}
            {# more. The server reads them off the plan it looks up -    #}
            {# sending them was what let anyone email arbitrary content  #}
            {# from this application's address.                          #}
            {#                                                           #}
            {# C18: the count sent was days.count, so a seven-day plan's #}
            {# email said "7 recipes". The server counts the meals.      #}
            {#                                                           #}
            {# The LIST still goes up, on purpose: it is what the reader #}
            {# resolved conversions for and ticked items off, and        #}
            {# re-deriving it on the server would email a different list #}
            {# from the one on the screen.                               #}
            body: JSON.stringify({
                email: email,
                meal_plan_id: {{ meal_plan.meal_plan_id }},
                ingredients: finalList
            })"""

# ==================================================================== C16
# THE PAGE PRINTS THE INGREDIENTS IT DROPPED.
#
# Both lists were computed, both were put in the context, and no
# template ever read either of them. The banner sits above both
# branches of the page - the conversion wizard and the normal list -
# because an ingredient with no shopping unit is missing from the list
# whichever branch the reader is on.
C16T_WAS = """    {% if has_missing_conversions %}
    {% if perms.auth.can_edit_recipes %}"""
C16T_NOW = """    {# MP-1, 18 Oct 2026 - C16. THE INGREDIENTS THAT ARE NOT ON THE   #}
    {# LIST. Two kinds, and two different fixes, so two sentences:     #}
    {#                                                                 #}
    {#   no unit on the recipe line  -> the RECIPE needs correcting    #}
    {#   no shopping unit on the     -> the INGREDIENT needs a base    #}
    {#   ingredient                     unit configured                #}
    {#                                                                 #}
    {# The second list has been in this page's context since the page  #}
    {# was written and nothing ever read it; the first was not even    #}
    {# counted - MP-1 added the counting. Above both branches, because #}
    {# an ingredient is missing from the list either way.              #}
    {% if has_missing_units or has_missing_shopping_units %}
    <div class="conversions-needed-card">
        <h2>
            <i class="fas fa-exclamation-triangle"></i>
            NOT ON THIS LIST
        </h2>
        {% if has_missing_units %}
        <p>These recipe lines have no unit, so there is no quantity to add up:</p>
        <ul>
            {% for miss in missing_units_list %}
            <li><strong>{{ miss.ingredient_name }}</strong> in {{ miss.recipe }}</li>
            {% endfor %}
        </ul>
        <p>Give the ingredient a unit on the recipe and it will appear here.</p>
        {% endif %}
        {% if has_missing_shopping_units %}
        <p>These ingredients have no shopping unit, so there is nothing to convert to:</p>
        <ul>
            {% for miss in missing_shopping_units_list %}
            <li><strong>{{ miss.ingredient_name }}</strong> in {{ miss.recipe }}</li>
            {% endfor %}
        </ul>
        {% if perms.auth.can_edit_recipes %}
        <p>
            <a href="{% url 'ingredient_base_units_management' %}" class="btn action-secondary">
                <i class="fas fa-balance-scale"></i> Set base units
            </a>
        </p>
        {% endif %}
        {% endif %}
    </div>
    {% endif %}

    {% if has_missing_conversions %}
    {% if perms.auth.can_edit_recipes %}"""

# =============================================================== A1+A2+B8
# The two calendar views, rewritten whole. Four items meet here and the
# restructure is what fixes A2: the failure path RETURNS, so nothing
# downstream can read a name the except branch never bound.
ADD_WAS = '''def add_recipe_to_meal_plan_day(request, meal_plan_id):
    """Add a recipe to a meal plan day"""
    meal_plan_day_id = request.POST.get('meal_plan_day_id')
    recipe_id = request.POST.get('recipe_id')
    servings = request.POST.get('servings', 4)

    try:
        meal_plan_day = MealPlanDay.objects.get(meal_plan_day_id=meal_plan_day_id)
        recipe = Recipe.objects.get(recipe_id=recipe_id)

        # Verify user owns this meal plan
        if meal_plan_day.meal_plan.created_by != request.user:
            messages.error(request, 'You do not have permission to modify this meal plan.')
            return redirect('meal_plan_calendar')

        # Get max sort order for this day
        max_order = MealPlanRecipe.objects.filter(
            meal_plan_day=meal_plan_day
        ).aggregate(Max('sort_order'))['sort_order__max'] or 0

        # Create the meal plan recipe
        MealPlanRecipe.objects.create(
            meal_plan_day=meal_plan_day,
            recipe=recipe,
            servings=int(servings),
            sort_order=max_order + 1
        )

        messages.success(request, f'Added "{recipe.recipe_name}" to {meal_plan_day.date.strftime("%A, %B %d")}')

    except (MealPlanDay.DoesNotExist, Recipe.DoesNotExist) as e:
        messages.error(request, 'Error adding recipe. Please try again.')

    # Redirect back to calendar with current view
    return redirect(f"{reverse('meal_plan_calendar')}?week={meal_plan_day.date.strftime('%Y-%m-%d')}")'''

ADD_NOW = '''def add_recipe_to_meal_plan_day(request):
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
    return redirect(f"{reverse('meal_plan_calendar')}?week={meal_plan_day.date.strftime('%Y-%m-%d')}")'''

REMOVE_WAS = '''def remove_recipe_from_meal_plan(request, meal_plan_id):
    """Remove a recipe from a meal plan day"""
    meal_plan_recipe_id = request.POST.get('meal_plan_recipe_id')

    try:
        meal_plan_recipe = MealPlanRecipe.objects.get(meal_plan_recipe_id=meal_plan_recipe_id)
        meal_plan_day = meal_plan_recipe.meal_plan_day

        # Verify user owns this meal plan
        if meal_plan_day.meal_plan.created_by != request.user:
            messages.error(request, 'You do not have permission to modify this meal plan.')
            return redirect('meal_plan_calendar')

        recipe_name = meal_plan_recipe.recipe.recipe_name
        week_date = meal_plan_day.date.strftime('%Y-%m-%d')

        meal_plan_recipe.delete()

        messages.success(request, f'Removed "{recipe_name}" from the meal plan')

        return redirect(f"{reverse('meal_plan_calendar')}?week={week_date}")

    except MealPlanRecipe.DoesNotExist:
        messages.error(request, 'Recipe not found.')
        return redirect('meal_plan_calendar')'''

REMOVE_NOW = '''def remove_recipe_from_meal_plan(request):
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
    return redirect(f"{reverse('meal_plan_calendar')}?week={week_date}")'''


# ============================================================ REGISTRATION
# THREE COMMENTS STILL SAY PF-1. The pre-flight round was called PF-1
# for about an hour on 18 Oct before the name was found to belong to the
# 5 October picker-lazy round, and was renamed PG-1. The register was
# corrected; three comments were not, and two of them have shipped:
#
#   alv_tree.py            the CONVERTED entry for test_preflight.py
#   test_waiting_down.py   the CONVERTED_N bump note
#   apply_crs_buttons.py   BG-1's register ANCHOR, which no longer
#                          matches alv_rounds.py at all - that patcher
#                          would refuse if it were ever re-run
#
# They are corrected here, in the round that is already editing two of
# the three files, rather than in a round of their own for nine words.
# A label reused for two things has now caused a wrong statement four
# times in three days - PF-1, RC-1, and these.
TREE_WAS = """    # PF-1, 18 Oct 2026 - E24. The gate reads the subject line and asks
    # the tree whether it has the rounds it names. Wide from birth.
    'test_preflight.py',
]"""
TREE_NOW = """    # PG-1, 18 Oct 2026 - E24. The gate reads the subject line and asks
    # the tree whether it has the rounds it names. Wide from birth.
    #
    # MP-1, 18 Oct 2026: this comment said PF-1, which is the 5 October
    # picker-lazy round. The pre-flight carried that name for an hour
    # before the collision was found; the register was corrected and
    # this was missed.
    'test_preflight.py',
    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    # Nineteen items that break, expose or lose data. Wide from birth.
    'test_meal_fixes.py',
]"""

CRS = 'apply_crs_buttons.py'
CRSPF_WAS = """REG_WAS = \"\"\"    # PF-1, 18 Oct 2026 - E24. A subject naming a round the tree does
    # not have is refused before the sweep rather than after it.
    '.bak_preflight',
]\"\"\"
REG_NOW = \"\"\"    # PF-1, 18 Oct 2026 - E24. A subject naming a round the tree does"""
CRSPF_NOW = """# MP-1, 18 Oct 2026. BOTH NAMES HERE SAID PF-1, which is the 5 October
# picker-lazy round, not the pre-flight. This anchor stopped matching
# alv_rounds.py the moment the register was corrected to PG-1 - so this
# patcher, which has already been applied, would REFUSE if it were ever
# re-run, and the message would blame a missing anchor rather than a
# renamed round.
REG_WAS = \"\"\"    # PG-1, 18 Oct 2026 - E24. A subject naming a round the tree does
    # not have is refused before the sweep rather than after it.
    '.bak_preflight',
]\"\"\"
REG_NOW = \"\"\"    # PG-1, 18 Oct 2026 - E24. A subject naming a round the tree does"""

REG_WAS = """    # CU-1, 18 Oct 2026 - three places decided what a receipt's currency
    # looks like and they disagreed. One helper now, three callers.
    '.bak_recsymbol',
]"""
REG_NOW = """    # CU-1, 18 Oct 2026 - three places decided what a receipt's currency
    # looks like and they disagreed. One helper now, three callers.
    '.bak_recsymbol',
    # MP-1, 18 Oct 2026 - Meal Plans release 1. The nineteen items from
    # the design record that break, expose or lose data.
    '.bak_mealfix',
]"""

SUITE_WAS = """    # PG-1, 18 Oct 2026 - E24, the subject read against the tree.
    'test_preflight.py'
)"""
SUITE_NOW = """    # PG-1, 18 Oct 2026 - E24, the subject read against the tree.
    'test_preflight.py',
    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    'test_meal_fixes.py'
)"""

SENT_WAS = (
    "    @{ File = 'alv_preflight.py'; Text = 'as_left_by'; "
    "What = 'PG-1: the pre-flight says what missing backups cost' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- MP-1, 18 Oct 2026
    #
    # 'missing_units.append' AND NOT 'missing_units'. test_sentinels.py
    # asks of every row whether there is ANY historical version of the
    # file in which its text is absent - a row that cannot fail is a row
    # that watches nothing - and it refused the shorter text, because
    # `seen_missing_units` has carried `missing_units` as a SUBSTRING
    # since the aggregator was written. Three backups tried, present in
    # all three.
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'missing_units.append'; What = 'MP-1: the shopping list names the ingredients it dropped' },
    @{ File = 'pages/templates/create_meal_plan.html'; Text = 'function esc('; What = 'MP-1: recipe names are escaped before they reach innerHTML' },"""


# ================================================= A SIBLING SUITE'S PREMISE
# PX-1, 13 Oct, counts the JavaScript sites that read `recipe_image`
# straight out of the serialisers - its point being that those six
# needed no edit when the photo URL moved. B10 wraps one of them in
# esc(), so the regex stopped matching and the count went 6 to 5.
#
# PX-1 IS RIGHT TO NOTICE AND ITS CLAIM IS STILL TRUE: the site still
# reads recipe_image, and still needs no edit for the photo URL. What
# moved is the shape of the expression around it, which was never what
# PX-1 was about. The regex is widened to the inside of the braces, so
# it counts the read however it is wrapped.
PX = 'test_recipe_photos.py'
PX_WAS = r"""    js += len(re.findall(r'\$\{[\w.]*recipe_image\}', t))"""
PX_NOW = r"""    # MP-1, 18 Oct 2026 - ANYTHING INSIDE THE BRACES, not a bare
    # dotted name. B10 wrapped one of these six in esc(), because the
    # same page inserts recipe text with innerHTML, and this regex went
    # from six matches to five - reporting a site as "left behind" when
    # what had actually happened was that it had been made safe.
    #
    # The claim PX-1 makes is that the JS READS recipe_image and so took
    # the new URL for free. That is still exactly true. The shape of the
    # expression around the read was never the point.
    js += len(re.findall(r'\$\{[^}]*recipe_image[^}]*\}', t))"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('MP-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def swap_all(text, old, new, want, where):
    """Every occurrence, and the count must be the one that was measured.

    B11 is 26 identical strings across four files. `once()` cannot see
    them and a bare .replace() cannot tell 10 from 11 - so a file that
    grew another permission check since 18 Oct would be rewritten
    without anybody noticing. The count is the measurement.

    AND IT GOES THROUGH fit(), like swap() does. The first spelling did
    not, and the first multi-line anchor it was given - B12's author
    list, in a CRLF file - was reported as zero occurrences. A counted
    replace that cannot find anything fails loudly, which is the only
    reason that was a two-minute fault instead of a silent one."""
    old = fit(text, old)
    new = fit(text, new)
    got = text.count(old)
    if got != want:
        refuse('%s: expected exactly %d occurrence(s) of %r, found %d. '
               'This file has moved since MP-1 measured it - re-measure '
               'rather than widening the number.' % (where, want, old, got))
    return text.replace(old, new)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    v = read(pv)

    # ---------------------------------------------------------------- 0
    # ASKED OF THE TREE, NOT OF A FLAG FILE, AND ASKED FIRST.
    if 'MP-1, 18 Oct 2026' in v:
        print('MP-1  already applied.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE SUITE IS THE ROUND, not a side effect of it. A patcher that
    # registers a suite nobody shipped turns a guard into a broken gate.
    if not os.path.isfile(os.path.join(root, ME)):
        refuse('%s is not on disk - it is half the round' % ME)

    # ---------------------------------------------------------------- 2
    # THE VIEW MODULE. Eleven of the nineteen land here.
    v = swap(v, MDOC_WAS, MDOC_NOW, '%s (module docstring)' % VIEW)
    v = swap(v, IMP_WAS, IMP_NOW, '%s (escape import)' % VIEW)
    # C16 - the aggregator
    v = swap(v, DOC_WAS, DOC_NOW, '%s (C16, aggregator docstring)' % VIEW)
    v = swap(v, TRACK_WAS, TRACK_NOW, '%s (C16, the trackers)' % VIEW)
    v = swap(v, NOUNIT_WAS, NOUNIT_NOW, '%s (C16, the silent continue)' % VIEW)
    v = swap(v, RET_WAS, RET_NOW, '%s (C16, the return)' % VIEW)
    # C20 + C14 + C17 - create
    v = swap(v, CREATE_WAS, CREATE_NOW, '%s (C20+C14+C17, create)' % VIEW)
    # C13 + C15 - edit
    v = swap(v, DROP_WAS, DROP_NOW, '%s (C13, the dropped days)' % VIEW)
    v = swap(v, SAME_WAS, SAME_NOW, '%s (C15, one row per recipe)' % VIEW)
    v = swap(v, EDOK_WAS, EDOK_NOW, '%s (C13, saying what went)' % VIEW)
    # C14 + C17 - duplicate
    v = swap(v, DUP_WAS, DUP_NOW, '%s (C14+C17, duplicate)' % VIEW)
    # A5 + C17 - the calendar
    v = swap(v, ADDR_WAS, ADDR_NOW, '%s (A5, the address bar)' % VIEW)
    v = swap(v, SEL_WAS, SEL_NOW, '%s (C17, one plan a week)' % VIEW)
    # C16 - the shopping list view
    v = swap(v, SHOPCALL_WAS, SHOPCALL_NOW, '%s (C16, the call)' % VIEW)
    v = swap(v, ISSUES_WAS, ISSUES_NOW, '%s (C16, has_issues)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (C16, the context)' % VIEW)
    # B9 + C18 - the email
    v = swap(v, MAIL_WAS, MAIL_NOW, '%s (B9+C18, the email)' % VIEW)
    v = swap(v, H1_WAS, H1_NOW, '%s (B9, the heading)' % VIEW)
    v = swap(v, CATH_WAS, CATH_NOW, '%s (B9, the category head)' % VIEW)
    v = swap(v, LI_WAS, LI_NOW, '%s (B9, the item line)' % VIEW)
    # A1 + A2 + B8 + C19 - the two calendar views
    v = swap(v, ADD_WAS, ADD_NOW, '%s (A1+A2+B8+C19, add)' % VIEW)
    v = swap(v, REMOVE_WAS, REMOVE_NOW, '%s (A1+B8, remove)' % VIEW)
    # B12 - the author picker, both copies in this module
    v = swap_all(v, AUTHORS_WAS, AUTHORS_NOW, 2, '%s (B12, the authors)' % VIEW)
    out[pv] = v

    # ---------------------------------------------------------------- 3
    # THE URLS. A1 deletes a parameter from two view signatures, so the
    # two routes must not be sending one. They are not - that is the
    # whole of A1 - and the patcher proves it rather than assuming it,
    # because a round that removed the parameter from a view the URL
    # DID feed would break two working screens.
    pu = os.path.join(root, 'pages', 'urls.py')
    u = read(pu)
    for route in ('add_recipe_to_day', 'remove_recipe'):
        line = [ln for ln in u.split('\n') if route + "/'" in ln]
        if len(line) != 1:
            refuse('pages/urls.py: expected exactly one route for %r, '
                   'found %d' % (route, len(line)))
        if 'int:' in line[0] or '<' in line[0]:
            refuse('pages/urls.py: %s now captures something - A1 deletes '
                   'the view parameter and would break it: %s'
                   % (route, line[0].strip()))

    # ---------------------------------------------------------------- 4
    # B12's THIRD COPY, outside this module.
    pc = os.path.join(root, CRUD)
    out[pc] = swap(read(pc), CRUD_WAS, CRUD_NOW, '%s (B12, copy three)' % CRUD)

    # ---------------------------------------------------------------- 5
    # THE STALE DOCSTRING.
    pm = os.path.join(root, MODELS)
    out[pm] = swap(read(pm), WS_WAS, WS_NOW, '%s (Workspace docstring)' % MODELS)

    # ------------------------------------------------------------- 5b
    # THE STALE PF-1 ANCHOR in an already-applied patcher.
    p = os.path.join(root, CRS)
    out[p] = swap(read(p), CRSPF_WAS, CRSPF_NOW, '%s (the PF-1 name)' % CRS)

    # ---------------------------------------------------------------- 6
    # B11 FIRST, AND ACROSS ALL FOUR TEMPLATES, because three of the
    # literal blocks below quote a permission check and they quote the
    # corrected spelling. Doing it the other way round would leave
    # those anchors unfindable and the counts wrong.
    tpl = {}
    for path, want in PERMS.items():
        p = os.path.join(root, path)
        tpl[p] = swap_all(read(p), PERM_WAS, PERM_NOW, want,
                          '%s (B11)' % path)

    # ---------------------------------------------------------------- 7
    # THE CALENDAR - A3 and C19.
    p = os.path.join(root, CAL)
    t = tpl[p]
    t = swap(t, A3_WAS, A3_NOW, '%s (A3, the empty day)' % CAL)
    t = swap(t, A3B_WAS, A3B_NOW, '%s (A3, add another)' % CAL)
    t = swap(t, C19A_WAS, C19A_NOW, '%s (C19, the option)' % CAL)
    t = swap(t, C19B_WAS, C19B_NOW, '%s (C19, the box)' % CAL)
    t = swap(t, C19C_WAS, C19C_NOW, '%s (C19, reset on open)' % CAL)
    t = swap(t, C19D_WAS, C19D_NOW, '%s (C19, the recipe yield)' % CAL)
    out[p] = t

    # ---------------------------------------------------------------- 8
    # CREATE / EDIT - A4, B10 and C13's browser half.
    p = os.path.join(root, CREATE)
    t = read(p)
    t = swap(t, BS1_WAS, BS1_NOW, '%s (A4, show)' % CREATE)
    t = swap(t, BS2_WAS, BS2_NOW, '%s (A4, hide)' % CREATE)
    t = swap(t, ESC_WAS, ESC_NOW, '%s (B10, the helper)' % CREATE)
    for i, (w, n) in enumerate((
            (B10A_WAS, B10A_NOW), (B10B_WAS, B10B_NOW), (B10C_WAS, B10C_NOW),
            (B10D_WAS, B10D_NOW), (B10E_WAS, B10E_NOW), (B10F_WAS, B10F_NOW),
            (B10G_WAS, B10G_NOW), (B10H_WAS, B10H_NOW), (B10I_WAS, B10I_NOW),
            (B10J_WAS, B10J_NOW), (B10K_WAS, B10K_NOW), (B10L_WAS, B10L_NOW))):
        t = swap(t, w, n, '%s (B10, site %d)' % (CREATE, i + 1))
    t = swap(t, C13T_WAS, C13T_NOW, '%s (C13, the note)' % CREATE)
    t = swap(t, C13J_WAS, C13J_NOW, '%s (C13, counted)' % CREATE)
    t = swap(t, C13J2_WAS, C13J2_NOW, '%s (C13, the counters)' % CREATE)
    t = swap(t, C13J3_WAS, C13J3_NOW, '%s (C13, returned)' % CREATE)
    t = swap(t, C13J4_WAS, C13J4_NOW, '%s (C13, shown)' % CREATE)
    out[p] = t

    # ---------------------------------------------------------------- 9
    # THE SHOPPING LIST - A6, B9's body, C16's banner.
    p = os.path.join(root, SHOP)
    t = tpl[p]
    t = swap(t, A6_WAS, A6_NOW, '%s (A6+B9+C18, the POST body)' % SHOP)
    t = swap(t, C16T_WAS, C16T_NOW, '%s (C16, the banner)' % SHOP)
    out[p] = t

    # --------------------------------------------------------------- 10
    # The other two templates are B11 only.
    out[os.path.join(root, LIST)] = tpl[os.path.join(root, LIST)]
    out[os.path.join(root, VIEWT)] = tpl[os.path.join(root, VIEWT)]

    # -------------------------------------------------------------- 10b
    # THE SIBLING SUITE WHOSE PREMISE THIS ROUND MOVED.
    p = os.path.join(root, PX)
    s = swap(read(p), PX_WAS, PX_NOW, '%s (the JS census regex)' % PX)
    try:
        ast.parse(s)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (PX, e.lineno, e.msg))
    out[p] = s

    # --------------------------------------------------------------- 11
    # REGISTRATION.
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, 'Push-PendingChanges.ps1')
    t = read(p)
    t = swap(t, SUITE_WAS, SUITE_NOW, 'Push-PendingChanges.ps1 ($suites)')
    t = swap(t, SENT_WAS, SENT_NOW, 'Push-PendingChanges.ps1 (sentinels)')
    out[p] = t

    p = os.path.join(root, WD)
    s = read(p)
    m = re.search(r'CONVERTED_N = (\d+)', s)
    if not m:
        refuse('%s has no CONVERTED_N' % WD)
    was = int(m.group(1))
    s = s.replace('CONVERTED_N = %d' % was,
                  'CONVERTED_N = %d   # MP-1, 18 Oct 2026 - this '
                  'round own suite   # (was %d)' % (was + 1, was), 1)
    # AND THE STALE NAME ON THE LINE BEFORE IT. See TREE_WAS above: the
    # bump note for the pre-flight round says PF-1, which belongs to the
    # 5 October picker round.
    if '# PF-1, 18 Oct 2026' not in s:
        refuse('%s: the stale PF-1 note is not where MP-1 measured it - '
               'if somebody has already corrected it, delete this block '
               'rather than widening it' % WD)
    s = s.replace('# PF-1, 18 Oct 2026 - this round own suite',
                  '# PG-1, 18 Oct 2026 - this round own suite   '
                  '# (said PF-1; corrected by MP-1, 18 Oct 2026 - PF-1 is '
                  'the 5 October picker round)', 1)
    out[p] = s

    # --------------------------------------------------------------- 12
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))

    if CHECK:
        print('MP-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, val in out.items():
        backup(k)
        write(k, val)
    print('MP-1 applied.  Meal Plans release 1, groups A, B and C.')
    print('   A  the calendar add and remove work at all; a missing day is')
    print('      a message; days outside a plan no longer render None; the')
    print('      recipe picker opens; a bad address falls back; apostrophes')
    print('   B  the ownership checks go, consistently with the 18 Oct')
    print('      decision; the email endpoint will only write to the')
    print('      roster and reads the plan itself; recipe names are escaped')
    print('      before they reach innerHTML; 26 permission checks moved')
    print('      to the tier the views actually use; the author picker')
    print('      reads the model, in all three places it was typed out')
    print('   C  Edit says what it is about to drop and what it dropped;')
    print('      Create and Duplicate are one transaction each; the same')
    print('      recipe twice on a day survives; the shopping list names')
    print('      what it left off; overlapping plans are warned about and')
    print('      the calendar picks the same one twice; the email counts')
    print('      recipes; a blank plan name is refused on Create too')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
