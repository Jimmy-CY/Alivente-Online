# -*- coding: utf-8 -*-
"""apply_planner.py - round MN-1, 18 Oct 2026.

RELEASE 3, PUSH 1. THE CALENDAR IS THE PLAN.

Demetri, 18 Oct: "Let's start with Release 3."

THE CHANGE. Meals belong to DATES, not to a named container. A new
MealEntry table replaces MealPlan -> MealPlanDay -> MealPlanRecipe, and
the planner opens on this week with every date able to take a meal.
There is no name, no start date and no end date to fill in before you
can plan a single dinner, and nothing overlaps because there is only
one calendar.

THE FOUR DECISIONS, TAKEN 18 OCT BEFORE A LINE WAS WRITTEN:

    TENANCY        MealEntry has NO workspace field. The design record
                   gives it one; `Recipe` has none, and its created_by
                   is a plain CharField - so a tenanted entry holding
                   an untenanted recipe is the exact inconsistency MP-1
                   recorded in the Workspace docstring.

    EXISTING DATA  CLEARED, not converted. No Menus made from the four
                   test plans.

    SHOPPING LIST  DATE RANGE NOW, not release 4. It keys on
                   meal_plan_id today and this round removes the plan,
                   so the bridge cannot wait. The conversion,
                   aggregation and rounding are untouched.

    DELIVERY       Three pushes. This is the first.

THE BLAST RADIUS, MEASURED BEFORE ANY OF IT: MealPlan, MealPlanDay and
MealPlanRecipe are referenced in EXACTLY ONE FILE outside migrations -
meal_planning.py, 44 times - and nowhere else in the application. Five
templates and two menu links. That is the whole of it.

TWO THINGS A SIBLING INSTRUMENT CAUGHT IN THIS ROUND'S OWN OUTPUT,
both in the CSS and markup lifted off the old calendar page:

    test_compact_card.py  "meal_planner.html  stray */ 0  unclosed /* 1"
                          MC-1's note about the view toggle arrived as
                          its headline alone - the lift dropped its body
                          AND its terminator. CSS comments do not nest,
                          so the stray /* read as text and nothing
                          rendered wrongly, which is why no eye caught
                          it. This round now REFUSES to write an HTML
                          file whose /* and */ do not balance.

    test_user_slash.py    the leftover icon was written
                          fa-{% if %}redo{% else %}store{% endif %},
                          which cuts the glyph name in half with a
                          template tag. US-1 exists because a name
                          assembled at render time is invisible to every
                          census that reads the source. It is two WHOLE
                          names now, which is the shape US-1 says is
                          readable.

WHAT THIS PUSH DOES NOT DO. Repeat a week, Menus, notes and leftovers
are push 2; move, reorder and undo are push 3, along with migration
0101 which drops the old tables. `note` and `leftover_of` are on the
model from the start because adding them later would be a second
migration for columns the shape already implies - but nothing in this
push writes to them.

AND ONE CORRECTION THAT RIDES WITH IT. MD-1's explanation of D21 is
WRONG and it shipped. MealPlanDay DOES have day_name and
formatted_date - they are properties, and I measured the model block
with s.index('class '), which stops at `class Meta:` four lines in.

    {{ day.day_name|slice:":3" }}        -> Mon
    {{ day.formatted_date|date:"M d" }}  -> (empty)

So the heading showed "Mon" with no date, because formatted_date
returns a STRING and a date filter on a string is empty - which is
exactly what the design record said and I second-guessed. The code was
right; the prose was not, in three places, and they are corrected here.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_planner'
MODELS = os.path.join('pages', 'models.py')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
VIEWT = os.path.join('pages', 'templates', 'view_meal_plan.html')
PLANNER = os.path.join('pages', 'templates', 'meal_planner.html')
MIG = os.path.join('pages', 'migrations', '0100_meal_entry.py')
ME = 'test_planner.py'
MD = 'test_meal_display.py'
PATCHER = 'apply_planner.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

# ================================================================ THE MODEL
# Appended after MealPlanRecipe, so the three tables it replaces and the
# one that replaces them read together for the one release they overlap.
MODEL_WAS = """class UnitConversion(models.Model):
    \"\"\"Conversion rates between different measurement units\"\"\""""

MODEL_NOW = '''class MealEntry(models.Model):
    """One meal on one date. MN-1, 18 Oct 2026 - release 3.

    THE CALENDAR IS THE PLAN. This replaces the chain
    MealPlan -> MealPlanDay -> MealPlanRecipe, where a meal could only
    exist inside a named box with a start and an end date. Those boxes
    could overlap, could not exceed seven days, and threw meals away
    when their dates changed - which was C13, C17 and half of release
    1's group C between them.

    A meal has a DATE. That is the whole model change.

    NO WORKSPACE, BY DECISION - 18 Oct 2026. The design record gives
    this table one. `Recipe` has no workspace at all and its created_by
    is a plain CharField, so a tenanted meal holding an untenanted
    recipe would be precisely the inconsistency MP-1 recorded in
    Workspace's own docstring. If recipes are ever tenanted, meal
    entries follow in that round, in one migration.

    RECIPE IS NULLABLE, because not every slot is a recipe. A note -
    "Eat out", "At Yiayia's" - makes an empty night a DECISION rather
    than a gap, and stays off the shopping list. Push 2 writes those;
    the column is here from the start because adding it later would be
    a second migration for a column this shape already implies.

    CASCADE ON recipe, which is what MealPlanRecipe did. Deleting a
    recipe you no longer want takes it off future plans too, and the
    alternative - PROTECT - would refuse to delete any recipe that had
    ever been planned.
    """
    meal_entry_id = models.AutoField(primary_key=True)
    date = models.DateField(db_index=True)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, null=True, blank=True,
        related_name='meal_entries',
        help_text='The recipe planned for this date, or blank for a note')
    note = models.CharField(
        max_length=200, blank=True, default='',
        help_text='A planned night that is not a recipe - Eat out, Leftovers')
    servings = models.IntegerField(
        default=4,
        help_text='How many this meal is cooked for. Scales the shopping list.')
    sort_order = models.IntegerField(default=0)
    leftover_of = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='leftovers',
        help_text='Set when this meal is the leftovers of an earlier one. '
                  'It costs nothing on the shopping list.')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='meal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meal_entries'
        ordering = ['date', 'sort_order', 'meal_entry_id']
        verbose_name_plural = 'Meal entries'

    def __str__(self):
        what = self.recipe.recipe_name if self.recipe else (self.note or 'Meal')
        return '%s on %s' % (what, self.date.strftime('%a %d %b %Y'))

    @property
    def servings_multiplier(self):
        """How far to scale this meal's ingredients.

        The same guarded expression MD-1 put on MealPlanRecipe: Decimal
        because every quantity downstream is one and mixing the two
        raises, and `or 1` because a recipe with no yield recorded
        should scale by one rather than refuse to be shopped for.
        """
        if not self.recipe:
            return Decimal('0')
        return Decimal(self.servings) / Decimal(self.recipe.servings or 1)

    @property
    def counts_on_shopping_list(self):
        """A note buys nothing, and leftovers were bought once already."""
        return bool(self.recipe) and self.leftover_of_id is None


class Menu(models.Model):
    """A saved week, kept by NAME rather than by date. MN-1, 18 Oct 2026.

    Repeat copies last week. A Menu is for the weeks you come back to
    months later - Christmas, girls visiting, the usual rotation - so
    it holds DAY INDEXES, 0 to 6, and not dates.

    Push 2 fills these. The tables arrive now so that release 3 has one
    migration and not three.
    """
    menu_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='menus')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menus'
        ordering = ['name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """One meal in a saved menu, on a day INDEX. MN-1, 18 Oct 2026."""
    menu_item_id = models.AutoField(primary_key=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE,
                             related_name='items')
    day_index = models.IntegerField(
        default=0, help_text='0 is the first day of the menu, not a weekday')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='menu_items')
    note = models.CharField(max_length=200, blank=True, default='')
    servings = models.IntegerField(default=4)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'menu_items'
        ordering = ['day_index', 'sort_order', 'menu_item_id']

    def __str__(self):
        what = self.recipe.recipe_name if self.recipe else (self.note or 'Meal')
        return '%s, day %d of %s' % (what, self.day_index + 1, self.menu.name)


class UnitConversion(models.Model):
    """Conversion rates between different measurement units"""'''

# ============================================================ THE MIGRATION
# HAND WRITTEN, like 0099, and then proved against a disposable sqlite:
# it applies, and `makemigrations --check` then reports NO CHANGES, so
# the migration and the model agree. The patcher runs that proof itself
# before it writes anything - see main().
#
# SCHEMA ONLY. It creates three empty tables and converts nothing. The
# four existing plans are cleared by decision, and the three old tables
# are dropped by 0101 in push 3 - leaving them empty and unread for two
# pushes costs nothing and keeps the only irreversible step until last.
MIGRATION = '''# -*- coding: utf-8 -*-
"""MN-1, 18 Oct 2026 - release 3, the calendar is the plan.

Three new tables and nothing else. MealEntry replaces the chain
MealPlan -> MealPlanDay -> MealPlanRecipe; Menu and MenuItem hold the
saved weeks that push 2 fills.

NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
production are test data and are cleared rather than converted. The old
tables are left in place, empty and unread, until 0101 drops them in
push 3 - which is the only irreversible step in this release and so
goes last.

NO WORKSPACE on MealEntry, also by decision: Recipe has no workspace
field, so a tenanted meal holding an untenanted recipe would be an
inconsistency rather than a boundary.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0099_recipe_image_display'),
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('menu_id', models.AutoField(primary_key=True,
                                             serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='menus', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'menus',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MealEntry',
            fields=[
                ('meal_entry_id', models.AutoField(primary_key=True,
                                                   serialize=False)),
                ('date', models.DateField(db_index=True)),
                ('note', models.CharField(
                    blank=True, default='',
                    help_text='A planned night that is not a recipe - Eat out, Leftovers',
                    max_length=200)),
                ('servings', models.IntegerField(
                    default=4,
                    help_text='How many this meal is cooked for. Scales the shopping list.')),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='meal_entries', to=settings.AUTH_USER_MODEL)),
                ('leftover_of', models.ForeignKey(
                    blank=True,
                    help_text='Set when this meal is the leftovers of an earlier one. It costs nothing on the shopping list.',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='leftovers', to='pages.mealentry')),
                ('recipe', models.ForeignKey(
                    blank=True,
                    help_text='The recipe planned for this date, or blank for a note',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meal_entries', to='pages.recipe')),
            ],
            options={
                'verbose_name_plural': 'Meal entries',
                'db_table': 'meal_entries',
                'ordering': ['date', 'sort_order', 'meal_entry_id'],
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('menu_item_id', models.AutoField(primary_key=True,
                                                  serialize=False)),
                ('day_index', models.IntegerField(
                    default=0,
                    help_text='0 is the first day of the menu, not a weekday')),
                ('note', models.CharField(blank=True, default='',
                                          max_length=200)),
                ('servings', models.IntegerField(default=4)),
                ('sort_order', models.IntegerField(default=0)),
                ('menu', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items', to='pages.menu')),
                ('recipe', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='menu_items', to='pages.recipe')),
            ],
            options={
                'db_table': 'menu_items',
                'ordering': ['day_index', 'sort_order', 'menu_item_id'],
            },
        ),
    ]
'''

# ============================================================= THE IMPORTS
# Three names leave and one arrives. MealEntry is all push 1 needs -
# Menu and MenuItem are created by the migration and written by push 2,
# and importing a model nothing uses is the dead weight E33 was about.
IMP_WAS = """    HouseholdMember,
    MealPlan,
    MealPlanDay,
    MealPlanRecipe,
    Recipe,"""
IMP_NOW = """    HouseholdMember,
    MealEntry,
    Recipe,"""


# =========================================== WHERE THE REPLACEMENT STARTS
# Two anchors and a slice. Everything between them is the ten views
# release 3 removes, and all 44 references to the three old models are
# inside it.
CRUD_HEAD = """# =====================================================================
# MEAL PLAN CRUD
# ====================================================================="""

MAIL_HEAD = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def send_meal_plan_shopping_list("""


# ============================================ THE AGGREGATOR KEEPS ITS WORK
# 240 lines of unit conversion, smart rounding and the three
# missing-ingredient trackers stay EXACTLY as they are. The design
# record is explicit that this part is already ahead of the field -
# "converting every ingredient to its shopping unit across a whole
# plan, plus the inline form to fix a missing conversion. Paprika and
# AnyList don't really do this. We keep it unchanged."
#
# What changes is the three lines that say WHAT IT WALKS. A plan with
# days holding recipes becomes a flat list of meal entries.
AGG_SIG_WAS = """def aggregate_meal_plan_ingredients(meal_plan):
    \"\"\"
    Aggregate ingredients and convert to shopping units."""
AGG_SIG_NOW = """def aggregate_meal_entries(entries):
    \"\"\"
    Aggregate ingredients and convert to shopping units.

    MN-1, 18 Oct 2026 - release 3. This took a MEAL PLAN and walked its
    days; it takes an iterable of MealEntry now, because meals belong
    to dates and there is no plan to walk. Everything below the walk -
    the conversion, the smart rounding UP, the three trackers - is
    untouched, deliberately."""

AGG_WALK_WAS = """    for day in meal_plan.days.all().order_by('date'):
        for meal_recipe in day.recipes.all():
            recipe = meal_recipe.recipe
            # MD-1, 18 Oct 2026 - E33. The model's own property, which
            # was unused until now and carried this expression's unsafe
            # twin. It is this expression now.
            servings_multiplier = meal_recipe.servings_multiplier"""
AGG_WALK_NOW = """    for entry in entries:
        # MN-1, 18 Oct 2026 - A NOTE BUYS NOTHING, AND LEFTOVERS WERE
        # BOUGHT ONCE ALREADY. counts_on_shopping_list is the model's
        # own answer to both, so the rule lives in one place rather
        # than in every caller that walks entries.
        if entry.counts_on_shopping_list:
            recipe = entry.recipe
            # MD-1, 18 Oct 2026 - E33. The model's own property, which
            # was unused until now and carried this expression's unsafe
            # twin. It is this expression now.
            servings_multiplier = entry.servings_multiplier"""

# THE DOCSTRING'S FUNCTION LIST, which names every view in the module.
MDOC_WAS = """- meal_plans                      : List all meal plans. Read-tier.
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
                                    Edit-tier."""
MDOC_NOW = """- meal_planner                    : The planner. One week of dates, with
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
                                    Edit-tier."""


# ================================================= THE VIEWS THEY REPLACE
# Everything from the CRUD heading down to the email view is replaced.
# Ten views become five, because seven screens become one.
#
# WRITTEN WHOLE RATHER THAN BY ANCHOR, and that is the honest shape for
# this one round: 44 of the 44 references to the three old models are
# in the block being removed, so an anchor per edit would be forty-odd
# anchors proving nothing that the shape check in main() does not prove
# better. The backup is the diff.
NEW_VIEWS = r'''# =====================================================================
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
'''

# ===================================================== THE EMAIL VIEW SURVIVES
# It keeps every line of its HTML, its escaping and its roster check -
# B9's work from yesterday. What changes is where it gets the heading
# and the count, which was a plan and is now a date range.
MAIL_SIG_WAS = """def send_meal_plan_shopping_list(request, meal_plan_id=None):
    \"\"\"Send meal plan shopping list via email
    NOTE (Phase 10): meal_plan_id is accepted but unused ... optional (=None)
    because the route supplies no id (pre-existing bug). \"\"\""""
MAIL_SIG_NOW = """def send_meal_plan_shopping_list(request):
    \"\"\"Email a shopping list for a date range.

    MN-1, 18 Oct 2026. The signature carried a meal_plan_id the route
    never supplied - a Phase 10 note called it a pre-existing bug and
    made it optional rather than removing it, which is the same shape
    A1 found in the two calendar views. There is no plan to pass now,
    so it is gone.

    B9's work from 18 Oct is untouched: the recipient must still be an
    active household member with an address or the signed-in user, and
    every value is still escaped before it reaches the HTML.\"\"\""""

MAIL_PLAN_WAS = """        plan_id = data.get('meal_plan_id') or meal_plan_id
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
MAIL_PLAN_NOW = """        # MN-1, 18 Oct 2026 - A RANGE, NOT A PLAN. The server still
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
            recipe__isnull=False, leftover_of__isnull=True).count()"""

# =============================================================== THE URLS
# Seven routes go, four arrive, and the two that other pages link to
# keep their NAMES so nothing in the tree 404s:
# recipe_management.html reverses `meal_plans` twice.
URLS_WAS = """    path('meal_plans/', views.meal_plans, name='meal_plans'),
    path('meal_plans/create/', views.create_meal_plan, name='create_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/', views.view_meal_plan, name='view_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/edit/', views.edit_meal_plan, name='edit_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/duplicate/', views.duplicate_meal_plan, name='duplicate_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/delete/', views.delete_meal_plan, name='delete_meal_plan'),
    path('meal_plans/<int:meal_plan_id>/shopping_list/', views.meal_plan_shopping_list, name='meal_plan_shopping_list'),
    path('meal_plans/send_shopping_list/', views.send_meal_plan_shopping_list, name='send_meal_plan_shopping_list'),
    path('meal_plans/calendar/', views.meal_plan_calendar, name='meal_plan_calendar'),
    path('meal_plans/add_recipe_to_day/', views.add_recipe_to_meal_plan_day, name='add_recipe_to_meal_plan_day'),
    path('meal_plans/remove_recipe/', views.remove_recipe_from_meal_plan, name='remove_recipe_from_meal_plan'),"""
URLS_NOW = """    # MN-1, 18 Oct 2026 - RELEASE 3. Seven routes for seven screens
    # became one planner, and two of the names stay because other
    # pages reverse them: recipe_management.html links to `meal_plans`
    # from its bar and from its More menu.
    #
    # `meal_plan_calendar` keeps its name too and lands on the same
    # planner - every bookmark, every Back control written before
    # today and every `?from=calendar` in the tree still resolves.
    # Push 3 removes the aliases once nothing reverses them.
    path('meal_plans/', views.meal_planner, name='meal_plans'),
    path('meal_plans/planner/', views.meal_planner, name='meal_planner'),
    path('meal_plans/calendar/', views.meal_planner, name='meal_plan_calendar'),
    path('meal_plans/shopping_list/', views.meal_shopping_list, name='meal_shopping_list'),
    path('meal_plans/send_shopping_list/', views.send_meal_plan_shopping_list, name='send_meal_plan_shopping_list'),
    path('meal_plans/add/', views.add_meal_entry, name='add_meal_entry'),
    path('meal_plans/remove/', views.remove_meal_entry, name='remove_meal_entry'),
    path('meal_plans/servings/', views.set_meal_servings, name='set_meal_servings'),"""


# ============================================================ THE PLANNER
# The screen. It inherits the old calendar's stylesheet, trimmed -
# already token-clean, zero hex literals outside its comments - rather
# than starting a new one for the 76 template-walking suites to judge
# from scratch.
PLANNER_HTML = r'''{% extends 'base.html' %}
{% load static %}
{# MH-1, 18 Oct 2026 - the Meal Plans guide, the same one on every    #}
{# meal-plan screen.                                                  #}
{% load help_modal_tags %}
{% block title %}Meal Planner{% endblock %}
{% block content %}

{# ===================================================================== #}
{# MN-1, 18 Oct 2026 - RELEASE 3. THE CALENDAR IS THE PLAN.             #}
{#                                                                      #}
{# This replaces SEVEN screens: the plan list, Create, View, Edit,      #}
{# Duplicate, Delete and the old calendar. A meal has a date, so there  #}
{# is no box to make before you can plan a dinner, nothing can overlap, #}
{# and changing your mind about a week cannot throw meals away.         #}
{#                                                                      #}
{# The CSS below is the old calendar's, trimmed. It was already token-  #}
{# clean - zero hex literals outside its comments - so the planner      #}
{# inherits a stylesheet the guards have already judged rather than     #}
{# starting one.                                                        #}
{# ===================================================================== #}

<style>    /* B-1, 5 Oct 2026 - 15 literal(s) on this page became a var().
       Each one was already the byte-identical value of the
       token that replaced it, read from base's :root, so
       nothing here moved. What changes is that the page is on
       the token and will follow when the house does.
       Tier A of the Section B map; B and C move a pixel and
       are separate rounds.                   [B-1 tier A] */

/* ==================== MAIN LAYOUT ==================== */
.calendar-container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 20px;
}


.calendar-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 25px;
}

/* ==================== LEFT PANEL ==================== */
.left-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

/* Mini Calendar */
.mini-calendar {
    background: var(--alv-paper);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.mini-calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.mini-calendar-header h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--alv-ink);
    margin: 0;
}

.mini-calendar-nav {
    display: flex;
    gap: 8px;
}

.mini-calendar-nav button {
    background: var(--alv-line-soft);
    border: none;
    width: 32px;
    height: 32px;
    border-radius: var(--alv-radius-sm);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.mini-calendar-nav button:hover {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}

.mini-calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
}

.mini-calendar-day-header {
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    padding: 8px 0;
}

.mini-calendar-day {
    text-align: center;
    padding: 8px 4px;
    font-size: 13px;
    border-radius: var(--alv-radius-sm);
    position: relative;
    transition: all 0.2s;
}

.mini-calendar-week {
    display: contents;
    cursor: pointer;
}

.mini-calendar-week:hover .mini-calendar-day:not(.empty) {
    background: var(--alv-surface-deep);
}

.mini-calendar-week.selected .mini-calendar-day:not(.empty) {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}

.mini-calendar-day.empty {
    color: var(--alv-ink-faint);
}

.mini-calendar-day.today {
    font-weight: 700;
    border: 2px solid var(--alv-accent);
}

.mini-calendar-day.has-meal::after {
    content: '';
    position: absolute;
    bottom: 3px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 6px;
    /* A STATUS, NOT A VERB - MC-3. This dot and the legend swatch below
       say "there is a meal on this day". They keep a green because that
       is what Demetri reads them by, but it is the palette's green. */
    background: var(--alv-good);
    border-radius: 50%;
}

.mini-calendar-day.in-meal-plan {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}

.mini-calendar-day.in-meal-plan.has-meal::after {
    background: var(--alv-paper);
}

.mini-calendar-day.in-meal-plan.today {
    border-color: var(--alv-paper);
}

/* Meal Plans List */







/* MC-3, 3 Oct 2026. #28a745 IS HANDLED BY NAME ON THIS PAGE, not by
   the sweep, because it carries two different intentions here: a CREATE
   button and a "this day has a meal" dot. A blanket map would have
   painted a verb and a status the same colour and called it tidying.
   The button is a verb, so it takes the accent like every other create
   in the tree; the two dots keep a green, but the palette's own
   --alv-good rather than a literal. */



/* ==================== RIGHT PANEL - WEEK DETAIL ==================== */
.week-detail-panel {
    background: var(--alv-paper);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    overflow: hidden;
}

.week-detail-header {
    background: var(--alv-surface);
    padding: 20px 25px;
    border-bottom: 1px solid var(--alv-line);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.week-detail-header h2 {
    font-size: 20px;
    font-weight: 600;
    color: var(--alv-ink);
    margin: 0;
}

.week-detail-header h2 i {
    color: var(--alv-accent-ink);
    margin-right: 10px;
}

/* ROW ACTIONS - MC-2, 3 Oct 2026. .week-detail-actions is gone and so
   are both of its .btn rules. There were TWO, 470 lines apart, one
   setting 8px 16px and the other 8px 14px; the later one won and the
   earlier one had been dead for as long as both existed. The strip is
   base's .row-actions now, which is what the list rows have worn since
   ML-1. */

.week-detail-content {
    padding: 20px;
}

/* No Meal Plan State */




/* Day Cards */
.day-card {
    background: var(--alv-surface);
    border-radius: 10px;
    margin-bottom: 15px;
    overflow: hidden;
    border: 1px solid var(--alv-line);
}

.day-card.today {
    border: 2px solid var(--alv-accent);
    box-shadow: 0 0 0 3px var(--alv-accent-ring);
}

.day-card-header {
    background: var(--alv-surface-deep);
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.day-card.today .day-card-header {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}

.day-card-header h4 {
    font-size: 15px;
    font-weight: 600;
    margin: 0;
}

.day-card-header .today-badge {
    background: var(--alv-paper);
    color: var(--alv-accent-ink);
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

.day-card-body {
    padding: 15px 18px;
}

/* Recipe Items */
.recipe-item {
    display: flex;
    gap: 15px;
    padding: 12px;
    background: var(--alv-paper);
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid var(--alv-line);
    transition: all 0.2s;
}

.recipe-item:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recipe-item:last-child {
    margin-bottom: 0;
}

.recipe-thumbnail {
    width: 70px;
    height: 70px;
    border-radius: 8px;
    object-fit: cover;
    flex-shrink: 0;
}

.recipe-thumbnail-placeholder {
    width: 70px;
    height: 70px;
    border-radius: 8px;
    background: var(--alv-accent);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--alv-on-accent);
    font-size: 24px;
    flex-shrink: 0;
}

.recipe-info {
    flex: 1;
    min-width: 0;
}

.recipe-info h5 {
    font-size: 15px;
    font-weight: 600;
    color: var(--alv-ink);
    margin: 0 0 6px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.recipe-meta {
    display: flex;
    gap: 15px;
    font-size: 12px;
    color: var(--alv-ink-soft);
    margin-bottom: 8px;
}

.recipe-meta span {
    display: flex;
    align-items: center;
    gap: 4px;
}

.recipe-meta i {
    color: var(--alv-accent-ink);
}

/* .recipe-actions went the same way - MC-2. Base sizes .row-actions and
   .icon-action-btn, including the 44px touch target under 768px, so a
   page rule here could only disagree with it. */

/* Empty Day */
.empty-day {
    text-align: center;
    padding: 20px;
    color: var(--alv-ink-faint);
}

.empty-day i {
    font-size: 24px;
    margin-bottom: 8px;
}

.add-recipe-btn {
    margin-top: 12px;
    padding: 8px 20px;
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    border: none;
    border-radius: var(--alv-radius-sm);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}

.add-recipe-btn:hover {
    background: var(--alv-accent-ink);
}

.add-recipe-btn-disabled {
    background: var(--alv-ink-faint) !important;
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
}

.add-another-btn {
    width: 100%;
    padding: 10px;
    background: transparent;
    border: 2px dashed var(--alv-line);
    border-radius: var(--alv-radius-sm);
    color: var(--alv-ink-soft);
    font-size: 13px;
    cursor: pointer;
    margin-top: 10px;
    transition: all 0.2s;
}

.add-another-btn:hover {
    border-color: var(--alv-accent);
    color: var(--alv-accent-ink);
    background: var(--alv-accent-soft);
}

.add-another-btn-disabled {
    opacity: 0.4;
    cursor: not-allowed;
    pointer-events: none;
}

/* Legend */
.calendar-legend {
    display: flex;
    gap: 20px;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid var(--alv-line);
    font-size: 12px;
    color: var(--alv-ink-soft);
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.legend-dot.meal {
    background: var(--alv-good);
}

.legend-dot.today {
    border: 2px solid var(--alv-accent);
    background: var(--alv-paper);
}

/* ==================== RESPONSIVE ==================== */
@media screen and (max-width: 1200px) {
    .calendar-layout {
        grid-template-columns: 1fr;
    }
    
    .left-panel {
        flex-direction: row;
        flex-wrap: wrap;
    }
    
    .mini-calendar {
        flex: 1;
        min-width: 280px;
    }
    

@media screen and (max-width: 768px) {
    .calendar-container {
        padding: 8px;
    }

    /* Left panel - stack the mini calendar above the week */
    .left-panel {
        flex-direction: column;
    }

    /* Mini calendar - tighter */
    .mini-calendar {
        padding: 14px;
        min-width: 0 !important;
    }
    .mini-calendar-header h3 {
        font-size: 16px;
    }
    .mini-calendar-day {
        padding: 7px 2px;
        font-size: 12px;
    }
    .mini-calendar-day-header {
        font-size: 10px;
        padding: 6px 0;
    }
    .calendar-legend {
        flex-wrap: wrap;
        gap: 12px;
    }

    /* Meal plans panel */

    /* Week detail header - stack title above actions */
    .week-detail-header {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        padding: 14px 14px;
    }
    .week-detail-header h2 {
        font-size: 17px;
        line-height: 1.3;
    }

    /* The 3-col grid that wrapped five labelled buttons on a phone went
       with them - MC-2. Five icon buttons are five 44px targets, about
       250px of the 390px a phone gives, so they sit on one row and need
       no grid at all. */

    /* Week detail content padding */
    .week-detail-content {
        padding: 14px;
    }

    /* Day cards - tighter */
    .day-card-header {
        padding: 10px 14px;
    }
    .day-card-header h4 {
        font-size: 14px;
    }
    .day-card-body {
        padding: 12px 14px;
    }

    /* Recipe items - smaller thumbnail, meta wraps */
    .recipe-item {
        gap: 12px;
        padding: 10px;
    }
    .recipe-thumbnail,
    .recipe-thumbnail-placeholder {
        width: 56px;
        height: 56px;
    }
    .recipe-thumbnail-placeholder {
        font-size: 20px;
    }
    .recipe-info h5 {
        font-size: 14px;
        white-space: normal;
    }
    .recipe-meta {
        flex-wrap: wrap;
        gap: 6px 12px;
    }

    /* No meal plan state */

    /* MODALS - full screen */
    .modal-dialog {
        max-width: 100% !important;
        margin: 0 !important;
        height: 100vh;
    }
    .modal-content {
        height: 100vh;
        border-radius: 0;
        display: flex;
        flex-direction: column;
        border: none;
    }
    .modal-header {
        flex-shrink: 0;
    }
    .modal-body {
        flex: 1 1 auto;
        overflow-y: auto;
    }
    .modal-footer {
        flex-direction: column-reverse !important;
        gap: 8px;
        flex-shrink: 0;
    }
    .modal-footer .btn {
        width: 100%;
        margin: 0 !important;
    }
    .modal-header .close {
        font-size: 28px;
        padding: 8px 12px;
    }

    /* Add Recipe Modal - recipe list inside */
    #recipeList {
        max-height: none !important;
    }
    .recipe-option > div {
        padding: 10px 12px !important;
    }
    .recipe-option img,
    .recipe-option > div > div:first-child {
        flex-shrink: 0;
    }
}

/* NO VIEW TOGGLE - MN-1, 18 Oct 2026. One calendar and no list, so
   there is nothing to switch between. MC-1 replaced this page's
   hand-rolled .view-toggle with base's .alv-seg on 3 Oct, and the
   fault Demetri reported behind it - "I should have the List/Calendar
   toggle in the Calendar view to be able to switch to List view
   again", where the toggle was there and the half he needed was white
   on white - cannot recur on a screen that has one view. MC-1's and
   MC-2's notes went with the page they described. */

/* THE FIVE COLOURS - MC-2, 3 Oct 2026, and the reason this round
   exists. .btn-view #007bff, .btn-edit #ffc107 on black ink,
   .btn-shopping #28a745, .btn-duplicate #0e7c8b, .btn-delete #dc3545,
   their five hovers and .btn-action-disabled are all gone. Twelve
   literals left with them.

   Five filled colours in one row is not a palette, it is five
   independent decisions sitting next to each other, and it taught the
   reader nothing: the colour of Edit said "Edit" and nothing else. The
   row-action strip says the same five things in one quiet voice and
   keeps red for the one action that cannot be undone.

   Disabled is base's .icon-disabled now rather than a local
   !important pair. */


    /* ---------------------------------------------------------------
       MN-1, 18 Oct 2026 - what the PLANNER adds to what the calendar
       already had. Three things: a week header that can move a week,
       a servings stepper on every meal, and a note row for push 2.

       No hex literals. Every colour is a base token, which is what
       the 76 template-walking suites ask of a new page on day one.
       --------------------------------------------------------------- */

    .week-nav {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 44px, because test_tap_target says that is the FLOOR on a phone
       and these are the controls somebody taps most on this screen. */
    .week-nav-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        height: 44px;
        padding: 0 10px;
        border: 1px solid var(--alv-line);
        border-radius: var(--alv-radius-sm);
        background: var(--alv-paper);
        color: var(--alv-ink);
        font-size: 15px;
        cursor: pointer;
    }
    .week-nav-btn:hover { background: var(--alv-surface); }

    .week-title {
        font-size: 17px;
        font-weight: 600;
        color: var(--alv-ink);
        margin: 0 8px;
    }

    .week-meta {
        font-size: 13px;
        color: var(--alv-ink-soft);
    }

    /* THE SERVINGS STEPPER. It saves on press, so there is no Save
       button on this screen at all - which is the point of the model
       change as much as it is a convenience. */
    .servings-step {
        display: inline-flex;
        align-items: center;
        gap: 2px;
    }
    .servings-btn {
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--alv-line);
        border-radius: var(--alv-radius-sm);
        background: var(--alv-paper);
        color: var(--alv-ink);
        font-size: 15px;
        line-height: 1;
        cursor: pointer;
    }
    .servings-btn:hover { background: var(--alv-surface); }
    .servings-btn[disabled] {
        opacity: .5;
        cursor: not-allowed;
    }
    .servings-count {
        min-width: 30px;
        text-align: center;
        font-weight: 600;
        font-size: 14px;
        color: var(--alv-ink);
        font-variant-numeric: tabular-nums;
    }
    .servings-word {
        font-size: 12px;
        color: var(--alv-ink-soft);
        margin-left: 2px;
    }

    .meal-scale {
        font-size: 11px;
        color: var(--alv-ink-soft);
    }

    /* A NOTE IS NOT A MEAL. It reads quieter than the recipes around
       it, because it is the night you decided not to cook. */
    .note-item .recipe-info h5 {
        color: var(--alv-ink-soft);
        font-style: italic;
    }

    .planner-status {
        font-size: 13px;
        min-height: 20px;
    }

    @media screen and (max-width: 768px) {
        .week-title { font-size: 15px; margin: 0 4px; }
        .week-nav-btn { padding: 0 8px; }
        /* THE STEPPER STAYS 30px AND THE ROW GROWS INSTEAD. A 44px
           stepper beside a 44px trashcan wraps the meal row on a
           phone, and test_zoom_guards cares that the page does not
           scroll sideways rather than that every control is 44. */
        .recipe-item { flex-wrap: wrap; row-gap: 6px; }
    }
</style>

<div class="calendar-container">

    <h2 class="page-title-h2">MEAL PLANNER</h2>

    {# ONE BAR, and Back is LAST and carries no colour - test_bar_top. #}
    {# Help sits before it, as it does on all five meal-plan screens.  #}
    <div class="page-action-buttons">
        <a href="{% url 'meal_shopping_list' %}?from={{ week_start|date:'Y-m-d' }}&amp;to={{ week_end|date:'Y-m-d' }}"
           class="btn action-primary">
            <i class="fas fa-shopping-cart"></i> Shopping List
        </a>
        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#meal_plansHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>
        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>

    <div class="calendar-layout">

        {# ------------------------------------------------- left panel #}
        <div class="left-panel">
            <div class="mini-calendar">
                <div class="mini-calendar-header">
                    <button type="button" class="mini-calendar-nav"
                            onclick="goMonth({{ prev_month.year }}, {{ prev_month.month }})"
                            aria-label="Previous month">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <strong>{{ month_name }}</strong>
                    <button type="button" class="mini-calendar-nav"
                            onclick="goMonth({{ next_month.year }}, {{ next_month.month }})"
                            aria-label="Next month">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>

                <div class="mini-calendar-grid">
                    <div class="mini-calendar-day-header">Mo</div>
                    <div class="mini-calendar-day-header">Tu</div>
                    <div class="mini-calendar-day-header">We</div>
                    <div class="mini-calendar-day-header">Th</div>
                    <div class="mini-calendar-day-header">Fr</div>
                    <div class="mini-calendar-day-header">Sa</div>
                    <div class="mini-calendar-day-header">Su</div>
                </div>

                {% for week in calendar_weeks %}
                {# MD-1's D26: the row you are looking at is marked, and  #}
                {# it can only match because the view normalises the week #}
                {# to a Monday before it gets here.                       #}
                <div class="mini-calendar-week{% if week.week_start and week.week_start == week_start %} selected{% endif %}"
                     {% if week.week_start %}onclick="goWeek('{{ week.week_start|date:'Y-m-d'|escapejs }}')"{% endif %}
                     data-week-start="{{ week.week_start|date:'Y-m-d' }}">
                    {% for day in week.days %}
                    <div class="mini-calendar-day {% if not day %}empty{% endif %} {% if day.is_today %}today{% endif %} {% if day.has_meal %}has-meal{% endif %}"
                         {% if day.date %}data-date="{{ day.date|date:'Y-m-d' }}"{% endif %}>
                        {{ day.day|default_if_none:'' }}
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}

                <div class="calendar-legend">
                    <div class="legend-item"><span class="legend-dot has-meal"></span> Has a meal</div>
                    <div class="legend-item"><span class="legend-dot today"></span> Today</div>
                </div>
            </div>
        </div>

        {# ------------------------------------------------ the week #}
        <div class="week-detail-panel">
            <div class="week-detail-header">
                <div class="week-nav">
                    <button type="button" class="week-nav-btn"
                            onclick="goWeek('{{ prev_week|date:'Y-m-d'|escapejs }}')"
                            aria-label="The week before">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="week-title">{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M Y" }}</span>
                    <button type="button" class="week-nav-btn"
                            onclick="goWeek('{{ next_week|date:'Y-m-d'|escapejs }}')"
                            aria-label="The week after">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button type="button" class="week-nav-btn"
                            onclick="goWeek('{{ this_week|date:'Y-m-d'|escapejs }}')">
                        Today
                    </button>
                </div>
                <span class="week-meta">{{ meal_count }} meal{{ meal_count|pluralize }}</span>
            </div>

            <div class="week-detail-content">
                <div id="plannerStatus" class="planner-status" role="status" aria-live="polite"></div>

                {% for day in week_days %}
                <div class="day-card">
                    <div class="day-card-header">
                        <h3>
                            <i class="fas fa-calendar-day"></i>
                            {{ day.date|date:"D j M" }}
                            {% if day.is_today %}<span class="alv-pill alv-pill-info">Today</span>{% endif %}
                        </h3>
                    </div>
                    <div class="day-card-body">
                        {% for entry in day.entries %}
                        {# A SLOT IS NOT ALWAYS A RECIPE. MealEntry allows a  #}
                        {# note from today even though push 2 is what writes  #}
                        {# them - and a page that assumed a recipe 500d the   #}
                        {# whole planner the moment one existed. Found by     #}
                        {# this round's own suite before it shipped, which is #}
                        {# what the behaviour register is for.                #}
                        {% if entry.recipe %}
                        <div class="recipe-item" data-entry="{{ entry.meal_entry_id }}">
                            {% if entry.recipe.photo_url %}
                            <img loading="lazy" decoding="async" src="{{ entry.recipe.photo_url }}"
                                 alt="" class="recipe-thumbnail">
                            {% else %}
                            <div class="recipe-thumbnail-placeholder"><i class="fas fa-utensils"></i></div>
                            {% endif %}

                            <div class="recipe-info">
                                <h5>{{ entry.recipe.recipe_name }}</h5>
                                <div class="recipe-meta">
                                    <span><i class="fas fa-clock"></i> {{ entry.recipe.prep_time|default:0|add:entry.recipe.cook_time|default:0 }} min</span>
                                    <span class="meal-scale">recipe makes {{ entry.recipe.servings|default:"?" }}</span>
                                </div>

                                {# THE STEPPER. It saves on press - there is no #}
                                {# Save button on this screen at all.            #}
                                <div class="servings-step">
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="servings-btn"
                                            onclick="stepServings({{ entry.meal_entry_id }}, -1)"
                                            aria-label="One fewer serving of {{ entry.recipe.recipe_name }}">&minus;</button>
                                    {% endif %}
                                    <span class="servings-count" id="servings-{{ entry.meal_entry_id }}">{{ entry.servings }}</span>
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="servings-btn"
                                            onclick="stepServings({{ entry.meal_entry_id }}, 1)"
                                            aria-label="One more serving of {{ entry.recipe.recipe_name }}">+</button>
                                    {% endif %}
                                    <span class="servings-word">servings</span>
                                </div>

                                {# LOOK, then DESTROY - the house row-action order. #}
                                <div class="row-actions">
                                    <a href="{% url 'view_recipe' entry.recipe.recipe_id %}"
                                       class="icon-action-btn icon-view" title="View recipe"
                                       aria-label="View the recipe {{ entry.recipe.recipe_name }}"><i class="fas fa-eye"></i></a>
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove {{ entry.recipe.recipe_name }} from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, '{{ entry.recipe.recipe_name|escapejs }}')"><i class="fas fa-trash"></i></button>
                                    {% else %}
                                    <span class="icon-action-btn icon-disabled" title="No permission to remove"
                                          aria-label="Remove this meal, no permission"><i class="fas fa-trash"></i></span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% else %}
                        {# THE NOTE ROW. No thumbnail, no stepper, no View -  #}
                        {# there is nothing to cook and nothing to buy. It is #}
                        {# a planned decision rather than a gap, which is the #}
                        {# whole reason the column exists.                     #}
                        <div class="recipe-item note-item" data-entry="{{ entry.meal_entry_id }}">
                            <div class="recipe-thumbnail-placeholder">
                                <i class="fas {% if entry.leftover_of %}fa-redo{% else %}fa-store{% endif %}"></i>
                            </div>
                            <div class="recipe-info">
                                <h5>{{ entry.note|default:"Nothing planned" }}</h5>
                                <div class="recipe-meta">
                                    <span>Nothing to cook, nothing to buy</span>
                                </div>
                                <div class="row-actions">
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove this note from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, '{{ entry.note|escapejs }}')"><i class="fas fa-trash"></i></button>
                                    {% else %}
                                    <span class="icon-action-btn icon-disabled" title="No permission to remove"
                                          aria-label="Remove this note, no permission"><i class="fas fa-trash"></i></span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endif %}
                        {% empty %}
                        <div class="empty-day">
                            <i class="fas fa-utensils"></i>
                            <p>Nothing planned</p>
                        </div>
                        {% endfor %}

                        {# EVERY DATE CAN TAKE A MEAL. There is no "this date  #}
                        {# is outside the plan" any more, because there is no  #}
                        {# plan for a date to be outside of - A3 dissolved by  #}
                        {# the model rather than guarded.                       #}
                        {% if perms.auth.can_edit_recipes %}
                        <button type="button" class="add-recipe-btn"
                                onclick="openPicker('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                            <i class="fas fa-plus"></i> Add Recipe
                        </button>
                        {% else %}
                        <button type="button" class="add-recipe-btn add-recipe-btn-disabled" disabled
                                title="No permission to add recipes">
                            <i class="fas fa-plus"></i> Add Recipe
                        </button>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

{# ===================================================== the picker #}
{# BOOTSTRAP 4.1.3, which is what base.html loads. A5's sibling A4  #}
{# spent a release on `new bootstrap.Modal(...)` here - a Bootstrap #}
{# 5 call on a Bootstrap 4 page - so the picker could never open.   #}
{% if perms.auth.can_edit_recipes %}
<div class="modal fade" id="pickerModal" tabindex="-1" role="dialog"
     aria-labelledby="pickerModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="pickerModalLabel">
                    <i class="fas fa-plus-circle"></i> Add a meal to <span id="pickerDayName"></span>
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'add_meal_entry' %}" id="pickerForm">
                {% csrf_token %}
                <input type="hidden" name="date" id="pickerDate">
                <input type="hidden" name="recipe_id" id="pickerRecipeId">
                <div class="modal-body">
                    <div class="form-group">
                        <label for="pickerSearch"><strong>Search recipes</strong></label>
                        <input type="text" class="form-control" id="pickerSearch"
                               placeholder="Type to search" oninput="filterPicker()"
                               autocomplete="off">
                    </div>

                    <div class="form-group">
                        <label for="pickerList"><strong>Choose one</strong></label>
                        <div id="pickerList">
                            {% for recipe in all_recipes %}
                            <div class="recipe-option"
                                 data-recipe-id="{{ recipe.recipe_id }}"
                                 data-recipe-servings="{{ recipe.servings|default:4 }}"
                                 data-recipe-name="{{ recipe.recipe_name|lower }}"
                                 onclick="pickRecipe(this)">
                                {% if recipe.photo_url %}
                                <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}"
                                     alt="" class="recipe-thumbnail">
                                {% else %}
                                <div class="recipe-thumbnail-placeholder"><i class="fas fa-utensils"></i></div>
                                {% endif %}
                                <div>
                                    <strong>{{ recipe.recipe_name }}</strong><br>
                                    <small class="text-muted">
                                        {{ recipe.prep_time|default:0|add:recipe.cook_time|default:0 }} min
                                        &bull; makes {{ recipe.servings|default:"?" }}
                                    </small>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="pickerServings"><strong>Servings</strong></label>
                        {# MP-1's C19, and it survives the model change: the #}
                        {# box is filled from the recipe that gets picked,   #}
                        {# and emptied when the picker opens. It used to be  #}
                        {# hardcoded to 4 and to keep the last number.       #}
                        <input type="number" class="form-control" id="pickerServings"
                               name="servings" min="1" max="99"
                               placeholder="{{ household_size }}">
                        <small class="form-text text-muted">
                            Blank uses the recipe's own yield. This household cooks for {{ household_size }}.
                        </small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary" id="pickerAdd" disabled>
                        <i class="fas fa-plus"></i> Add Meal
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

{# THE REMOVE FORM. One form, reused - a form per meal would be one #}
{# per meal in the page for a control pressed once in a while.      #}
<form method="POST" action="{% url 'remove_meal_entry' %}" id="removeForm" hidden>
    {% csrf_token %}
    <input type="hidden" name="meal_entry_id" id="removeEntryId">
</form>
{% endif %}


<script>
// =====================================================================
// MN-1, 18 Oct 2026. The planner.
//
// NO SECOND jQUERY - base.html loads jquery-3.6.0 after the content
// block, and MD-1's E31 took the old calendar's duplicate copy out.
// Every function here runs on interaction, so $ is defined by then.
// =====================================================================

function goWeek(week) {
    window.location.href = '{% url "meal_planner" %}?year={{ year }}&month={{ month }}&week=' + encodeURIComponent(week);
}

function goMonth(year, month) {
    window.location.href = '{% url "meal_planner" %}?year=' + year + '&month=' + month
        + '&week={{ week_start|date:"Y-m-d"|escapejs }}';
}

function say(html) {
    var box = document.getElementById('plannerStatus');
    if (box) { box.innerHTML = html; }
}

{% if perms.auth.can_edit_recipes %}
// ------------------------------------------------------- the picker
function openPicker(dateStr, dayName) {
    document.getElementById('pickerDate').value = dateStr;
    document.getElementById('pickerDayName').textContent = dayName;
    document.getElementById('pickerRecipeId').value = '';
    // C19: the box is EMPTIED on every open. It used to arrive holding
    // whatever the last recipe was set to.
    document.getElementById('pickerServings').value = '';
    document.getElementById('pickerSearch').value = '';
    document.getElementById('pickerAdd').disabled = true;
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    filterPicker();
    $('#pickerModal').modal('show');
}

function filterPicker() {
    var q = document.getElementById('pickerSearch').value.toLowerCase();
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.style.display = o.dataset.recipeName.indexOf(q) >= 0 ? '' : 'none';
    });
}

function pickRecipe(el) {
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    el.classList.add('selected');
    document.getElementById('pickerRecipeId').value = el.dataset.recipeId;
    // C19 again: the recipe's own yield, not a 4 and not the last one.
    var box = document.getElementById('pickerServings');
    if (box && !box.value) { box.value = el.dataset.recipeServings || ''; }
    document.getElementById('pickerAdd').disabled = false;
}

// ------------------------------------------------------- the stepper
// SAVES ON PRESS. There is no Save button on this screen, which is
// what the design record asks for: "Press - or + beside any meal in
// the planner. It saves immediately."
function stepServings(entryId, delta) {
    var span = document.getElementById('servings-' + entryId);
    if (!span) { return; }
    var next = parseInt(span.textContent, 10) + delta;
    if (isNaN(next) || next < 1 || next > 99) { return; }

    // OPTIMISTIC, THEN CORRECTED. The number moves at once so pressing
    // + twice quickly reads as two presses, and the server's answer is
    // what the span ends up holding.
    var was = span.textContent;
    span.textContent = next;

    var body = new URLSearchParams();
    body.append('meal_entry_id', entryId);
    body.append('servings', next);

    fetch('{% url "set_meal_servings" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: body.toString()
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
        if (d.success) {
            span.textContent = d.servings;
            say('');
        } else {
            span.textContent = was;
            // NOT alert() - SL-4. A browser dialog blocks every event
            // after it, and this page has a place to say things.
            say('<div class="alert alert-warning">' + d.error + '</div>');
        }
    })
    .catch(function () {
        span.textContent = was;
        say('<div class="alert alert-warning">That did not save. '
            + 'Check your connection and try again.</div>');
    });
}

// ------------------------------------------------------- remove
function removeMeal(entryId, name) {
    if (!confirm('Remove "' + name + '" from this day?')) { return; }
    document.getElementById('removeEntryId').value = entryId;
    document.getElementById('removeForm').submit();
}
{% endif %}
</script>

{% render_help_modal "meal_plans" %}
{% endblock %}
'''

# ==================================================== THE SHOPPING LIST PAGE
# NINE REFERENCES TO THE PLAN, and that is all. Every one becomes the
# date range. The two steps, the conversion wizard, the NOT ON THIS
# LIST banner, the three share buttons and the email panel are
# untouched - this page is the one piece of the module the design
# record says to keep.
SHOP = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')

S1_WAS = """{% block title %}Shopping List - {{ meal_plan.plan_name }}{% endblock %}"""
S1_NOW = """{% block title %}Shopping List{% endblock %}"""

S2_WAS = """<h4 class="page-subtitle-h4">{{ meal_plan.plan_name }} &mdash; {{ meal_plan.start_date|date:"M d" }} - {{ meal_plan.end_date|date:"M d, Y" }} &mdash; {% if meal_plan.days.count %}{{ meal_plan.days.count }}{% else %}0{% endif %} day{{ meal_plan.days.count|pluralize }}</h4>"""
S2_NOW = """{# MN-1, 18 Oct 2026 - A DATE RANGE, NOT A PLAN NAME. There is no  #}
{# plan to name: the list is for the days you chose.                #}
<h4 class="page-subtitle-h4">{{ start|date:"j M" }} &ndash; {{ end|date:"j M Y" }} &mdash; {{ day_count }} day{{ day_count|pluralize }} &mdash; {{ meal_count }} meal{{ meal_count|pluralize }}</h4>"""

S3_WAS = """        <button type="button" onclick="window.location.href='{% url 'view_meal_plan' meal_plan.meal_plan_id %}{% if request.GET.from == 'calendar' %}?from=calendar&amp;week={{ request.GET.week }}{% endif %}'" class="btn action-primary" id="doneBtn" hidden>"""
S3_NOW = """        {# MN-1 - Done goes back to the week you shopped for. #}
        <button type="button" onclick="window.location.href='{% url 'meal_planner' %}?week={{ week_start|date:'Y-m-d' }}'" class="btn action-primary" id="doneBtn" hidden>"""

S4_WAS = """        <a href="{% url 'view_meal_plan' meal_plan.meal_plan_id %}{% if request.GET.from == 'calendar' %}?from=calendar&amp;week={{ request.GET.week }}{% endif %}" class="btn action-back" id="backLink" aria-label="Back to Meal Plan">"""
S4_NOW = """        <a href="{% url 'meal_planner' %}?week={{ week_start|date:'Y-m-d' }}" class="btn action-back" id="backLink" aria-label="Back to the planner">"""

S5_WAS = """            <a href="{% url 'view_meal_plan' meal_plan.meal_plan_id %}{% if request.GET.from == 'calendar' %}?from=calendar&amp;week={{ request.GET.week }}{% endif %}" class="btn action-back" style="padding: 15px;">"""
S5_NOW = """            <a href="{% url 'meal_planner' %}?week={{ week_start|date:'Y-m-d' }}" class="btn action-back" style="padding: 15px;">"""

S6_WAS = """            <a href="{% url 'view_meal_plan' meal_plan.meal_plan_id %}{% if request.GET.from == 'calendar' %}?from=calendar&amp;week={{ request.GET.week }}{% endif %}" class="btn action-secondary">"""
S6_NOW = """            <a href="{% url 'meal_planner' %}?week={{ week_start|date:'Y-m-d' }}" class="btn action-secondary">"""

# THE ANCHOR STARTS AFTER THE EMOJI, deliberately. There is a literal
# shopping-cart glyph in that template literal and this patcher stays
# ASCII - Phase 10's resolution, and the reason the email subject in
# meal_planning.py is plain text. Anchoring past it leaves the glyph
# exactly where it is: it goes into a WhatsApp message a person reads,
# which is the one place in this module an emoji earns its place.
S7_WAS = """ Shopping List for {{ meal_plan.plan_name }}\\n`;
        text += `{{ meal_plan.start_date|date:"M d" }} - {{ meal_plan.end_date|date:"M d, Y" }}\\n\\n`;"""
S7_NOW = """ Shopping List\\n`;
        text += `{{ start|date:"j M" }} - {{ end|date:"j M Y" }}\\n\\n`;"""

S8_WAS = """            body: JSON.stringify({
                email: email,
                meal_plan_id: {{ meal_plan.meal_plan_id }},
                ingredients: finalList
            })"""
S8_NOW = """            body: JSON.stringify({
                email: email,
                {# MN-1, 18 Oct 2026 - the range, not a plan id. The server #}
                {# still reads the heading and the count off it rather than #}
                {# believing them, which is the whole of B9.                #}
                from: '{{ start|date:"Y-m-d" }}',
                to: '{{ end|date:"Y-m-d" }}',
                ingredients: finalList
            })"""

# ========================================== FOUR TEMPLATES AND TWO SUITES GO
# RELEASE 3 DELETES THE CODE RELEASE 1 FIXED, and that is not waste -
# it is the point. Nineteen of release 1's thirty-one items were guards
# against a shape that no longer exists:
#
#   C17  two plans over one week   -> there is one calendar
#   C13  changing dates drops meals -> there are no plan dates to change
#   A3   a day outside the plan     -> every date takes a meal
#   C20  a plan needs a name        -> there is no plan to name
#
# The fixes that OUTLIVE the shape - the escaping, the roster-only
# email, the query discipline, the permission tiers, the guarded
# address bar - are asserted by this round's own suite instead. They
# are not dropped; they move.
GONE_TEMPLATES = (
    os.path.join('pages', 'templates', 'meal_plans.html'),
    os.path.join('pages', 'templates', 'create_meal_plan.html'),
    os.path.join('pages', 'templates', 'view_meal_plan.html'),
    os.path.join('pages', 'templates', 'meal_plan_calendar.html'),
)
GONE_SUITES = ('test_meal_fixes.py', 'test_meal_display.py')

# MH-1'S SUITE NARROWS rather than retiring: its guide is still the
# guide, and two of the five screens it checked survive. The other
# three Help buttons went with their pages.
MH = 'test_meal_help.py'
MH_WAS = """PAGES = (LIST, CAL, CREATE, VIEWT, SHOP)
FILES = (HELP,) + PAGES"""
MH_NOW = """# MN-1, 18 Oct 2026 - FIVE SCREENS BECAME TWO. The planner replaced
# the list, the calendar, Create/Edit and the plan page, so three of
# the five Help buttons went with their pages. The guide is unchanged
# and still reached from every screen that exists.
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
PAGES = (PLANNER, SHOP)
FILES = (HELP,) + PAGES"""

MH_TAB_WAS = """    c['the old tab points at the new guide'] = (
        'press <strong>Help</strong> on any of the five meal-plan screens'
        in rec)"""
MH_TAB_NOW = """    # MN-1, 18 Oct 2026 - "any of the five" became "any meal-plan
    # screen", because there are two now and there will be more. The
    # pointer should not carry a number that a release can move.
    c['the old tab points at the new guide'] = (
        'press <strong>Help</strong> on any meal-plan screen' in rec)"""

HELPC = os.path.join('pages', 'help_content', 'administration.html')
HELPC_WAS = """press <strong>Help</strong> on any of the five meal-plan screens &mdash; the list, the calendar, Create or Edit, a plan, or its shopping list. It is the same guide on all five, so whichever screen raised the question is the one that answers it."""
HELPC_NOW = """press <strong>Help</strong> on any meal-plan screen &mdash; the planner or its shopping list. It is the same guide on both, so whichever screen raised the question is the one that answers it."""

# ============================================================ REGISTRATION
TREE_WAS = """    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Seven tabs, and a
    # Help button on five screens that had none. Wide from birth.
    'test_meal_help.py',
]"""
TREE_NOW = """    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Seven tabs, and a
    # Help button on five screens that had none. Wide from birth.
    'test_meal_help.py',
    # MN-1, 18 Oct 2026 - release 3. The calendar IS the plan: MealEntry
    # replaces three tables and the planner replaces seven screens.
    # Wide from birth.
    'test_planner.py',
]"""

REG_WAS = """    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Five screens had no
    # Help button at all, and the only meal-plan help in the application
    # described a calendar feature that was a server error.
    '.bak_mealhelp',
]"""
REG_NOW = """    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Five screens had no
    # Help button at all, and the only meal-plan help in the application
    # described a calendar feature that was a server error.
    '.bak_mealhelp',
    # MN-1, 18 Oct 2026 - release 3, push 1. Meals belong to dates. The
    # entries MP-1 and MD-1 left above stay in this register, because
    # history is what it is for - the suites they shipped are retired,
    # the backups they wrote are not.
    '.bak_planner',
]"""

# THE THREE ROWS GO TOGETHER, because two of the three are retired and
# a separate swap for each would leave the file briefly holding a
# suite list nobody meant.
SUITE_WAS = """    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    'test_meal_fixes.py',
    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E.
    'test_meal_display.py',
    # MH-1, 18 Oct 2026 - the Meal Plans user guide, on five screens.
    'test_meal_help.py'
)"""
SUITE_NOW = """    # MN-1, 18 Oct 2026 - test_meal_fixes.py and test_meal_display.py
    # are RETIRED here. They asserted the shape of the two calendar
    # views, the Create/Edit screen and the plan list, and release 3
    # deletes all four. Their fixes are not dropped: the ones that
    # outlive the shape are asserted by test_planner.py below, and the
    # ones that were guards against a plan with dates dissolved when
    # the plan did.
    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Two screens now.
    'test_meal_help.py',
    # MN-1, 18 Oct 2026 - release 3. The calendar IS the plan.
    'test_planner.py'
)"""

# THE TWO RETIRED SUITES COME OFF THE GATE, and so do the four
# sentinels that watch files this round deletes.
S_MEALFIX = """    # ------------------------------------------------- MP-1, 18 Oct 2026
    #
    # 'missing_units.append' AND NOT 'missing_units'. test_sentinels.py
    # asks of every row whether there is ANY historical version of the
    # file in which its text is absent - a row that cannot fail is a row
    # that watches nothing - and it refused the shorter text, because
    # `seen_missing_units` has carried `missing_units` as a SUBSTRING
    # since the aggregator was written. Three backups tried, present in
    # all three.
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'missing_units.append'; What = 'MP-1: the shopping list names the ingredients it dropped' },
    @{ File = 'pages/templates/create_meal_plan.html'; Text = 'function esc('; What = 'MP-1: recipe names are escaped before they reach innerHTML' },
    # ------------------------------------------------- MD-1, 18 Oct 2026
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'week_day_map'; What = 'MD-1: the calendar week is one pair of queries, not fourteen' },
    @{ File = 'pages/templates/view_meal_plan.html'; Text = '.btn-action-disabled'; What = 'MD-1: the swallowed selector that made disabled buttons look live' },"""
S_PLANNER = """    # ------------------------------------------------- MP-1, 18 Oct 2026
    #
    # 'missing_units.append' AND NOT 'missing_units'. test_sentinels.py
    # asks of every row whether there is ANY historical version of the
    # file in which its text is absent - a row that cannot fail is a row
    # that watches nothing - and it refused the shorter text, because
    # `seen_missing_units` has carried `missing_units` as a SUBSTRING
    # since the aggregator was written.
    #
    # MN-1, 18 Oct 2026 - THREE OF THE FOUR ROWS THAT WERE HERE WATCHED
    # FILES RELEASE 3 DELETES: create_meal_plan.html's esc() helper,
    # view_meal_plan.html's repaired selector, and the calendar week's
    # query map. A sentinel on a file that does not exist is not a
    # failed sentinel, it is a row nobody can read. The one that
    # survives watches the aggregator, which survives.
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'missing_units.append'; What = 'MP-1: the shopping list names the ingredients it dropped' },
    # ------------------------------------------------- MN-1, 18 Oct 2026
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def aggregate_meal_entries'; What = 'MN-1: the aggregator walks dated entries, not a plan' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'stepServings('; What = 'MN-1: servings save on press, with no Save button' },"""



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
    raise SystemExit('MN-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out, gone = {}, []

    pm = os.path.join(root, MODELS)
    m = read(pm)

    # ---------------------------------------------------------------- 0
    if 'class MealEntry(models.Model):' in m:
        print('MN-1  already applied - the calendar is the plan.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE ROUNDS THIS ONE REPLACES MUST BE IN THE TREE. MN-1 removes
    # the code MP-1, MD-1 and MH-1 wrote; applied to a tree without
    # them it would refuse on an anchor and say nothing useful.
    v = read(os.path.join(root, VIEW))
    for mark, who in (('MP-1, 18 Oct 2026', 'MP-1'),
                      ('MD-1, 18 Oct 2026', 'MD-1')):
        if mark not in v:
            refuse('%s is not applied. MN-1 replaces the views it fixed, '
                   'so its anchors are lines %s wrote.' % (who, who))
    if not os.path.isfile(os.path.join(root, ME)):
        refuse('%s is not on disk - it is half the round' % ME)

    # AND THE MIGRATION MUST BE NEXT. 0100 depends on 0099, so a tree
    # that has grown a 0100 since this was measured would have two.
    migs = sorted(f for f in os.listdir(os.path.join(root, 'pages',
                                                     'migrations'))
                  if re.match(r'^0\d{3}_.*\.py$', f))
    if not migs or migs[-1] != '0099_recipe_image_display.py':
        refuse('the latest migration is %r, not 0099_recipe_image_display '
               '- MN-1 writes 0100 and would collide'
               % (migs[-1] if migs else None))

    # ---------------------------------------------------------------- 2
    # THE MODEL.
    out[pm] = swap(m, MODEL_WAS, MODEL_NOW, '%s (MealEntry)' % MODELS)

    # ---------------------------------------------------------------- 3
    # THE VIEW MODULE. The aggregator keeps its work; the views are
    # replaced; the email view is reshaped.
    v = swap(v, IMP_WAS, IMP_NOW, '%s (the imports)' % VIEW)
    v = swap(v, MDOC_WAS, MDOC_NOW, '%s (the docstring)' % VIEW)
    v = swap(v, AGG_SIG_WAS, AGG_SIG_NOW, '%s (the aggregator)' % VIEW)
    v = swap(v, AGG_WALK_WAS, AGG_WALK_NOW, '%s (what it walks)' % VIEW)

    # EVERYTHING FROM THE CRUD HEADING TO THE EMAIL VIEW. Two anchors
    # and a slice, rather than forty: all 44 references to the three
    # old models are inside it, so an anchor per edit would prove less
    # than the shape check above and the backup beside it.
    head_at = v.index(fit(v, CRUD_HEAD))
    mail_at = v.index(fit(v, MAIL_HEAD))
    if mail_at <= head_at:
        refuse('%s: the email view is not below the CRUD heading - this '
               'module is not the one MN-1 measured' % VIEW)
    v = v[:head_at] + fit(v, NEW_VIEWS.strip('\n') + '\n\n\n') + v[mail_at:]

    v = swap(v, MAIL_SIG_WAS, MAIL_SIG_NOW, '%s (the email signature)' % VIEW)
    v = swap(v, MAIL_PLAN_WAS, MAIL_PLAN_NOW, '%s (the email range)' % VIEW)

    # NOTHING MAY STILL REACH FOR A MODEL THIS ROUND STOPS USING -
    # asked of the parse tree, because MN-1's own comments name all
    # three and a substring search would refuse the correct file. That
    # is the lesson MD-1 paid for twice.
    try:
        parsed = ast.parse(v)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (VIEW, e.lineno, e.msg))
    live = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Name) and node.id in (
                'MealPlan', 'MealPlanDay', 'MealPlanRecipe'):
            live.add(node.id)
    if live:
        refuse('%s still uses %s. Release 3 replaces the plan with the '
               'date, so a surviving caller is a screen nobody rewrote.'
               % (VIEW, ' and '.join(sorted(live))))
    out[os.path.join(root, VIEW)] = v

    # ---------------------------------------------------------------- 4
    # THE URLS, THE PLANNER, THE SHOPPING LIST.
    p = os.path.join(root, URLS)
    out[p] = swap(read(p), URLS_WAS, URLS_NOW, '%s (the routes)' % URLS)

    out[os.path.join(root, PLANNER)] = PLANNER_HTML

    p = os.path.join(root, SHOP)
    t = read(p)
    for i, (w, n) in enumerate((
            (S1_WAS, S1_NOW), (S2_WAS, S2_NOW), (S3_WAS, S3_NOW),
            (S4_WAS, S4_NOW), (S5_WAS, S5_NOW), (S6_WAS, S6_NOW),
            (S7_WAS, S7_NOW), (S8_WAS, S8_NOW))):
        t = swap(t, w, n, '%s (site %d)' % (SHOP, i + 1))
    if 'meal_plan.' in t:
        refuse('%s still reads the plan: %r' % (
            SHOP, [l.strip()[:70] for l in t.split('\n')
                   if 'meal_plan.' in l][:3]))
    out[p] = t

    # ---------------------------------------------------------------- 5
    # THE MIGRATION.
    out[os.path.join(root, MIG)] = MIGRATION

    # ---------------------------------------------------------------- 6
    # THE HELP, NARROWED.
    p = os.path.join(root, MH)
    t = swap(read(p), MH_WAS, MH_NOW, '%s (the two screens)' % MH)
    t = swap(t, MH_TAB_WAS, MH_TAB_NOW, '%s (the pointer)' % MH)
    out[p] = t
    p = os.path.join(root, HELPC)
    out[p] = swap(read(p), HELPC_WAS, HELPC_NOW, '%s (the pointer)' % HELPC)

    # ---------------------------------------------------------------- 7
    # REGISTRATION, AND THE TWO RETIREMENTS.
    p = os.path.join(root, TREE)
    t = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    for s in GONE_SUITES:
        t = re.sub(r"(?m)^[ \t]*#[^\n]*\n(?:[ \t]*#[^\n]*\n)*[ \t]*'%s',\n"
                   % re.escape(s), '', t)
        if s in t:
            refuse('%s: %s is still in CONVERTED after the retirement'
                   % (TREE, s))
    out[p] = t

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, 'Push-PendingChanges.ps1')
    t = read(p)
    t = swap(t, SUITE_WAS, SUITE_NOW, 'Push-PendingChanges.ps1 ($suites)')
    t = swap(t, S_MEALFIX, S_PLANNER,
             'Push-PendingChanges.ps1 (the sentinels)')
    out[p] = t

    p = os.path.join(root, WD)
    s = read(p)
    mm = re.search(r'CONVERTED_N = (\d+)', s)
    if not mm:
        refuse('%s has no CONVERTED_N' % WD)
    was = int(mm.group(1))
    # ONE SUITE ARRIVES AND TWO LEAVE, so the count falls by one. The
    # first round in this register to move it DOWN.
    out[p] = s.replace('CONVERTED_N = %d' % was,
                       'CONVERTED_N = %d   # MN-1, 18 Oct 2026 - one suite '
                       'in, two retired with the screens they judged   '
                       '# (was %d)' % (was - 1, was), 1)

    # ---------------------------------------------------------------- 8
    for s in GONE_SUITES:
        gone.append(os.path.join(root, s))
    for t_ in GONE_TEMPLATES:
        gone.append(os.path.join(root, t_))

    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))
        # EVERY CSS COMMENT THIS ROUND WRITES IS CLOSED.
        #
        # ADDED AFTER THE LIFT LOST A TERMINATOR, 18 Oct 2026. The
        # planner's CSS came off the old calendar page, and one comment
        # arrived as its first line alone: MC-1's note about the view
        # toggle kept its opening /* and its headline and lost its body
        # and its */ on the way across. CSS comments do not nest, so
        # the stray /* that followed read as text and nothing rendered
        # wrongly - which is exactly why no eye caught it.
        #
        # test_compact_card.py did, from the far side of the tree:
        # "meal_planner.html  stray */ 0  unclosed /* 1". A standard
        # that 148 templates keep is worth a line in the round that
        # would otherwise be the first to break it.
        if k.endswith('.html'):
            o, c = val.count('/*'), val.count('*/')
            if o != c:
                refuse('%s: %d /* against %d */ - a CSS comment this '
                       'round writes is not closed'
                       % (os.path.basename(k), o, c))

    if CHECK:
        print('MN-1 --check  %d file(s) would change, %d would be removed'
              % (len(out), len(gone)))
        for k in sorted(out):
            print('   + %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        for k in sorted(gone):
            print('   - %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, val in out.items():
        if os.path.exists(k):
            backup(k)
        else:
            d = os.path.dirname(k)
            if d and not os.path.isdir(d):
                os.makedirs(d)
        write(k, val)
    # THE DELETED FILES ARE BACKED UP FIRST, like every other file this
    # round touches. A round that removes something without leaving the
    # before beside it cannot be compared against, and as_left_by()
    # would read the live tree - which is the 17 Oct fault exactly.
    for k in gone:
        if os.path.exists(k):
            backup(k)
            os.remove(k)

    print('MN-1 applied.  Release 3, push 1 - the calendar is the plan.')
    print('   MealEntry replaces MealPlan -> MealPlanDay -> MealPlanRecipe')
    print('   Menu and MenuItem arrive empty, for push 2')
    print('   the planner replaces SEVEN screens: the list, Create, View,')
    print('   Edit, Duplicate, Delete and the old calendar')
    print('   every date takes a meal, nothing overlaps, and servings save')
    print('   on press with no Save button anywhere on the screen')
    print('   the shopping list shops a DATE RANGE, and its conversion,')
    print('   aggregation and rounding are untouched')
    print('   %d file(s) written, %d removed, backups end %s'
          % (len(out), len(gone), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
