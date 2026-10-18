# -*- coding: utf-8 -*-
"""apply_meal_display.py - round MD-1, 18 Oct 2026.

MEAL PLANS, RELEASE 1 - GROUPS D AND E.

THE NAME. The master list and the design record's build order both call
this round MP-2. **MP-2 has been a shipped round since 3 October** - the
meal plan form's bar to the top, Cancel becomes Back - and
test_ae_line.py PINS THE STRING 'MP-2' BY NAME, so a second one would
make a sibling suite's pin ambiguous rather than merely confuse a
reader. check_gates.py asked the question before a line was written.
See claude/mp2_name_collision_18_oct.

    D   display and navigation             21-28
    E   speed and code hygiene             29-33

TWELVE ITEMS, NOT THIRTEEN. **#30 is not release 1 and the record says
so itself**: "Paged endpoint (lands with the faster picker, D8)", and
D8 is a release-2 item. Shipping a paged endpoint without the picker
that pages through it would be a new endpoint nobody calls.

WHAT THE MEASUREMENT CHANGED, ITEM BY ITEM. Five of the twelve are not
quite what the record describes, and in four of those cases the real
fault is WORSE:

    D21 IS NOT "A DATE FILTER ON A STRING". `day.day_name` and
    `day.formatted_date` do not exist on MealPlanDay - it has
    meal_plan_day_id, meal_plan and date, and nothing else. So the
    heading does not render "Mon" with no date; it renders THE ICON AND
    NOTHING ELSE. Both halves are empty.

    D22'S TWO SELECTORS NEED TWO DIFFERENT FIXES, not one repair twice.
    `.btn-action-disabled` is worn by three spans on the page and
    NOTHING ANYWHERE DEFINES IT - so it is repaired. `.action-more-menu`
    is defined in base.html with house tokens; the copy trapped in this
    page's mobile media query is a LOCAL DUPLICATE with raw values and
    a different z-index. AE-2's own note in base says "two pages wrote
    the rule out locally rather than lean on that" - this is one of
    them. It is DELETED, not repaired.

    D24 IS HALF DONE ALREADY. BK-1 fixed the Back control on 3 Oct:
    create/edit carries `from=calendar` and returns to that week. What
    survives is the REDIRECT AFTER SAVING - it goes to view_meal_plan
    with no from= and no week=, so the calendar context is thrown away
    by the save rather than by the Back button.

    D25 IS AN ORDERING FAULT, and the two lines are four apart.
    meal_plans.html writes `sessionStorage.setItem(..., 'list')` at
    script top level and the DOMContentLoaded handler below it READS
    the preference - so the read can only ever see 'list'. The calendar
    does the same with 'calendar'. Each page stamps its own name over
    the preference before asking what it says. The TOGGLES already
    write on click, correctly, so the fix is to delete two lines.

    E29c NEEDS A DIFFERENT NAME THAN THE OBVIOUS ONE, and finding
    that out cost a wrong claim first. This round was written saying
    the calendar's recipe count was ABSENT rather than slow, on the
    grounds that all_meal_plans is a plain .all() with no annotation.
    That was wrong: `total_recipes` is a PROPERTY on MealPlan that runs
    its own COUNT, so the number does appear and the record's "1 per
    plan for counts" is exactly right.

    And annotating over that name does not work. `annotate(
    total_recipes=...)` raises "property total_recipes of MealPlan
    object has no setter" the moment the queryset is iterated - which
    is how the error was found: by applying the round and driving all
    five pages. The annotation is `recipe_count`, which meal_plans()
    has used for the same expression since it was written.

AND ONE WHERE THE RECORD'S FIX WOULD HAVE INTRODUCED A BUG:

    E33 asks for MealPlanRecipe.servings_multiplier, which is unused, to
    be "used by the shopping list". As written it is

        return self.servings / self.recipe.servings

    - float division with NO GUARD. A recipe with servings of 0 or None
    is a ZeroDivisionError or a TypeError. The aggregator's inline
    expression, which is what would be replaced, is

        Decimal(meal_recipe.servings) / Decimal(recipe.servings or 1)

    So the property is corrected to the safe expression FIRST and then
    used. Using it as it stands would have moved a crash into a
    property and called it a dedupe.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealdisplay'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
MODELS = os.path.join('pages', 'models.py')
CAL = os.path.join('pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join('pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join('pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join('pages', 'templates', 'view_meal_plan.html')
ME = 'test_meal_display.py'
PATCHER = 'apply_meal_display.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

# ==================================================================== D21
# THE DAY HEADING ON THE VIEW PAGE RENDERED THE ICON AND NOTHING ELSE.
# MealPlanDay has three fields - meal_plan_day_id, meal_plan, date - and
# neither `day_name` nor `formatted_date` is one of them, so Django's
# template layer resolved both to the empty string in silence.
D21_WAS = """                        <i class="fas fa-calendar-day"></i> 
                        {{ day.day_name|slice:":3" }} {{ day.formatted_date|date:"M d" }}"""
D21_NOW = """                        {# MD-1, 18 Oct 2026 - D21. This was                        #}
                        {# `day.day_name|slice:":3"` and                            #}
                        {# `day.formatted_date|date:"M d"`, and MealPlanDay has      #}
                        {# NEITHER attribute - it carries meal_plan_day_id,          #}
                        {# meal_plan and date. Both halves resolved to the empty     #}
                        {# string, so the heading was the icon and nothing else.     #}
                        {# One field, one filter: Mon 19 Oct.                        #}
                        <i class="fas fa-calendar-day"></i> 
                        {{ day.date|date:"D j M" }}"""

# ==================================================================== D22
# TWO SWALLOWED SELECTORS, TWO DIFFERENT FIXES.
#
# `}tn-action-disabled {` ate a `.b`. The brace closed `.header-meta
# span` and `tn-action-disabled` is an invalid type selector, so the
# whole block below it - the grey background, the muted text, the half
# opacity, pointer-events: none - NEVER APPLIED. Three spans on this
# page wear .btn-action-disabled and NOTHING anywhere defines it, so a
# reader without edit permission sees three live-looking buttons that
# do nothing. Repaired.
D22A_WAS = """.header-meta span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}tn-action-disabled {"""
D22A_NOW = """.header-meta span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}

/* MD-1, 18 Oct 2026 - D22. This selector read `}tn-action-disabled {`:
   the `.b` had been eaten, so the brace closed the rule above and
   `tn-action-disabled` was an invalid type selector. Everything below
   it was dead, and the three spans on this page that wear
   .btn-action-disabled rendered as live action-secondary buttons that
   do nothing when pressed.

   REPAIRED rather than deleted, because nothing anywhere else in the
   tree defines this class - unlike .action-more-menu below, which base
   owns. */
.btn-action-disabled {"""

# `}ction-more-menu {` ate a `.a` the same way - but this one is a LOCAL
# DUPLICATE of a component base.html already owns, written with raw
# values where base uses tokens, and trapped inside a mobile media
# query. Repairing it would reinstate an override nobody wants. It goes,
# and `.days-grid` gets its closing brace back.
D22B_WAS = """    .days-grid {
        grid-template-columns: 1fr;
    }ction-more-menu {
        position: absolute;
        top: calc(100% + 6px);
        right: 0;
        z-index: 200;
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        border-radius: 8px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        min-width: 240px;
        padding: 6px 0;
    }"""
D22B_NOW = """    .days-grid {
        grid-template-columns: 1fr;
    }

    /* MD-1, 18 Oct 2026 - D22, the second swallowed selector. This read
       `}ction-more-menu {`, the `.a` eaten exactly as the `.b` was
       above - and the rule it opened is DELETED rather than repaired.

       base.html defines .action-more-menu itself, with the house radius
       and shadow tokens and z-index 1030. The block that was here used
       raw 8px, a raw rgba shadow and z-index 200, and it sat inside a
       max-width 768px query, so repairing it would have given the phone
       a worse version of a component the desktop already gets right.

       AE-2's own note in base says it: "two pages wrote the rule out
       locally rather than lean on that". This was one of the two. */"""

# ==================================================================== D23
# "CREATE MEAL PLAN FOR THIS WEEK" OPENED A BLANK FORM. The calendar
# links with ?start_date=<the week it was showing> and the create view's
# GET path never looks at request.GET at all - the dates came from
# today, every time.
#
# GUARDED, because A5 is the same lesson one screen away: a date in the
# address bar is a string somebody can type.
D23_WAS = """    today = datetime.now().date()
    default_end = today + timedelta(days=6)"""
D23_NOW = """    # MD-1, 18 Oct 2026 - D23. THE CALENDAR'S ?start_date IS READ NOW.
    # It has been sent since the calendar was written - "Create Meal
    # Plan for This Week" links with the week it is showing - and this
    # function never looked at request.GET, so the form always opened on
    # today and the reader re-typed what they had just clicked.
    #
    # Guarded exactly as A5 guards the calendar's own address: a date in
    # a URL is a string somebody can type. A bad one falls back to
    # today rather than raising.
    today = datetime.now().date()
    start_param = request.GET.get('start_date')
    if start_param:
        try:
            default_start = datetime.strptime(start_param, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            default_start = today
    else:
        default_start = today
    default_end = default_start + timedelta(days=6)"""

D23B_WAS = """        'today': today,
        'default_start_date': today.strftime('%Y-%m-%d'),
        'default_end_date': default_end.strftime('%Y-%m-%d'),"""
D23B_NOW = """        # MD-1, 18 Oct 2026 - D23. default_start_date was today even
        # when the calendar had just said which week it meant.
        #
        # `today` STAYS IN THE CONTEXT and is no longer used to bound
        # the inputs - D27. The template reads it nowhere else, and it
        # costs nothing to leave for the next round that wants it.
        'today': today,
        'default_start_date': default_start.strftime('%Y-%m-%d'),
        'default_end_date': default_end.strftime('%Y-%m-%d'),"""

# And the LIST's Create button sends next Monday, which is what the
# record asks for: "(or next Monday from the list)". Two links, because
# the page has one in the bar and one in its empty state.
D23C_WAS = """        <a href="{% url 'create_meal_plan' %}" class="btn action-primary">"""
D23C_NOW = """        {# MD-1, 18 Oct 2026 - D23. Next Monday, so the form opens on a #}
        {# week rather than mid-week on today. The calendar sends the    #}
        {# week it is showing; the list has no week, so it sends the     #}
        {# next one.                                                     #}
        <a href="{% url 'create_meal_plan' %}?start_date={{ next_monday|date:'Y-m-d' }}" class="btn action-primary">"""

D23D_WAS = """                <a href="{% url 'create_meal_plan' %}" class="btn action-primary btn-lg">"""
D23D_NOW = """                {# MD-1, 18 Oct 2026 - D23, the empty state's copy of it. #}
                <a href="{% url 'create_meal_plan' %}?start_date={{ next_monday|date:'Y-m-d' }}" class="btn action-primary btn-lg">"""

# ==================================================================== D24
# BK-1 FIXED THE BACK BUTTON ON 3 OCT. What survives is the redirect
# after SAVING: it lands on view_meal_plan with no from= and no week=,
# so the save is what throws the calendar context away, and the View
# page's own Back then goes to the list.
D24_WAS = """            messages.success(request, f'Meal plan "{new_plan_name}" updated successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan_id)"""
D24_NOW = """            messages.success(request, f'Meal plan "{new_plan_name}" updated successfully!')
            # MD-1, 18 Oct 2026 - D24. CARRY THE CALENDAR THROUGH THE
            # SAVE. BK-1 taught the Back control to return to the week
            # you came from, on 3 Oct; this redirect still dropped
            # from= and week= on the floor, so saving an edit sent you
            # to the View page with no idea where you had started and
            # ITS Back went to the list.
            dest = reverse('view_meal_plan',
                           kwargs={'meal_plan_id': meal_plan_id})
            if request.GET.get('from') == 'calendar':
                dest = '%s?from=calendar&week=%s' % (
                    dest, request.GET.get('week', ''))
            return redirect(dest)"""

# ==================================================================== D25
# "RETURN TO THE VIEW YOU USED LAST" COULD NEVER WORK, AND THE TWO LINES
# ARE FOUR APART.
#
#     sessionStorage.setItem('meal_plan_view_preference', 'list');   <- top level
#     ...
#     const preference = sessionStorage.getItem(...)                 <- four lines down
#
# Every load of the list stamps 'list' over the preference and then asks
# what the preference says. The calendar does the same with 'calendar'.
# The TOGGLES already write on click - meal_plans.html:239/243 and
# meal_plan_calendar.html:745/749 - which is the only place a preference
# should ever be written, so the fix is to delete two lines.
D25A_WAS = """// Store view preference when on list view
sessionStorage.setItem('meal_plan_view_preference', 'list');"""
D25A_NOW = """// MD-1, 18 Oct 2026 - D25. THIS LINE IS GONE, and it is the whole fix.
//
// It read:
//     sessionStorage.setItem('meal_plan_view_preference', 'list');
//
// at script top level, FOUR LINES ABOVE the handler that reads the same
// key - so the read could only ever see 'list', and the redirect to the
// calendar below has never once fired. The calendar carried the mirror
// image of this line and stamped 'calendar' over it.
//
// Nothing replaces it. The two view toggles up at lines 239 and 243
// already write the preference on click, which is the only moment a
// person expresses one."""

D25B_WAS = """// Store view preference when on calendar view
sessionStorage.setItem('meal_plan_view_preference', 'calendar');"""
D25B_NOW = """// MD-1, 18 Oct 2026 - D25. GONE, with its twin on the list page.
//
// This stamped 'calendar' over the preference on every load of the
// calendar, exactly as meal_plans.html stamped 'list' over it on every
// load of the list - so each page overwrote the answer before the other
// one could read it. The toggles at lines 745 and 749 write it on
// click, which is where a preference comes from."""

# ==================================================================== D26
# THE WEEK, NORMALISED TO MONDAY - AND HIGHLIGHTED.
#
# Clicking a plan calls selectMealPlan(plan.start_date, ...), which puts
# the plan's START DAY in ?week=. A plan beginning on a Wednesday
# therefore opened a "week" of Wednesday to Tuesday, and the mini
# calendar's rows - which really are Monday to Sunday - lined up with
# nothing.
#
# Normalised in the VIEW and not in the JS, because ?week= is an address
# anybody can type and A5 is the lesson next door. One line serves the
# plan list, the month grid, a typed URL and a bookmark.
D26A_WAS = """    selected_week_end = selected_week_start + timedelta(days=6)"""
D26A_NOW = """    # MD-1, 18 Oct 2026 - D26. WHATEVER ARRIVES, THE WEEK STARTS ON A
    # MONDAY. selectMealPlan() sends a plan's start_date as ?week=, so a
    # plan beginning on a Wednesday opened a Wednesday-to-Tuesday band
    # that matched none of the mini calendar's rows - and the row it was
    # meant to highlight could never match either, which is the other
    # half of D26.
    #
    # Here rather than in the JS: ?week= is an address anybody can type,
    # and one line covers the plan list, the month grid, a typed URL and
    # a bookmark alike.
    selected_week_start -= timedelta(days=selected_week_start.weekday())
    selected_week_end = selected_week_start + timedelta(days=6)"""

# AND THE ROW IS HIGHLIGHTED. `.mini-calendar-week.selected` has been in
# this page's stylesheet since it was written - line 112 - and NOTHING
# HAS EVER ADDED THE CLASS. Dead CSS waiting for one template tag.
D26B_WAS = """                    <div class="mini-calendar-week"
                         {% if week.week_start %}onclick="selectWeek('{{ week.week_start|date:'Y-m-d'|escapejs }}')"{% endif %}"""
D26B_NOW = """                    {# MD-1, 18 Oct 2026 - D26. `.mini-calendar-week.selected`  #}
                    {# has been in this page's stylesheet since the page was    #}
                    {# written and NOTHING EVER ADDED THE CLASS, so the week    #}
                    {# you were looking at was never marked. It could not have  #}
                    {# matched before the view normalised the week to a Monday, #}
                    {# which is why the two halves of D26 ship together.        #}
                    <div class="mini-calendar-week{% if week.week_start and week.week_start == selected_week_start %} selected{% endif %}"
                         {% if week.week_start %}onclick="selectWeek('{{ week.week_start|date:'Y-m-d'|escapejs }}')"{% endif %}"""

# ==================================================================== D27
# CREATE BLOCKED PAST DATES AND EDIT DID NOT, from ONE template - the
# asymmetry is that `today` is in the create context and not in the edit
# one, so `min="{{ today|date:'Y-m-d' }}"` renders `min=""` on Edit.
#
# Demetri's decision, recorded in the design record: BOTH allow past
# dates, because a meal plan is also a record of what you ate.
# THE EXPLANATION GOES ABOVE THE form-group, NOT BETWEEN THE LABEL AND
# ITS INPUT - and that is a measurement, not a preference.
#
# The first spelling put twelve comment lines where the `min` had been.
# test_label_weight censuses "plain field labels" by pairing a <label>
# with the first form-control input WITHIN 400 CHARACTERS, and twelve
# lines of explanation is more than four hundred characters - so Start
# Date lost its pairing and the recipe side went from 57 plain labels to
# 56. The label and the input were both still there; the census could no
# longer see that they belonged together.
#
# A comment is not weightless. It sits in the file that other
# instruments read.
D27A_WAS = """                <div class="form-group">
                    <label for="start_date">Start Date *</label>"""
D27A_NOW = """                {# MD-1, 18 Oct 2026 - D27. NO min ON EITHER DATE BELOW.    #}
                {#                                                           #}
                {# One template serves Create and Edit, and `today` is only  #}
                {# in the Create context - so min="{{ today }}" rendered a   #}
                {# real date on Create and min="" on Edit. Past dates were   #}
                {# blocked on one screen and allowed on the other, from the  #}
                {# same line of markup.                                      #}
                {#                                                           #}
                {# Both allow them now, per the design record: a meal plan   #}
                {# is also a record of what you ate. The 1-to-7 day rule is  #}
                {# unchanged and still checked in the browser and on the     #}
                {# server.                                                   #}
                {#                                                           #}
                {# This note is ABOVE the form-group and not between the     #}
                {# label and its input: test_label_weight pairs the two      #}
                {# within 400 characters, and an explanation written in      #}
                {# between is enough to break the pairing.                   #}
                <div class="form-group">
                    <label for="start_date">Start Date *</label>"""

D27A2_WAS = """                           id="start_date"
                           name="start_date"
                           min="{{ today|date:'Y-m-d' }}"
                           required>"""
D27A2_NOW = """                           id="start_date"
                           name="start_date"
                           required>"""

D27B_WAS = """                           id="end_date"
                           name="end_date"
                           min="{{ today|date:'Y-m-d' }}"
                           required>"""
D27B_NOW = """                           id="end_date"
                           name="end_date"
                           required>"""

# ==================================================================== D28
# "DELETE ORIGINAL AFTER DUPLICATING" - the control that turns a
# duplicate into a SHIFT - existed on the View page only. Both other
# Duplicate dialogs post to the same view, which has read
# `delete_original` all along; they simply never offered it.
#
# Written twice rather than factored into an include: the two modals are
# four spaces apart in indentation and release 3 deletes both. An
# include whose only two callers are about to go is a component nobody
# will ever reuse.
D28A_WAS = """                            <small class="form-text text-muted">
                                The plan will maintain the same duration as the original.
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">"""
D28A_NOW = """                            <small class="form-text text-muted">
                                The plan will maintain the same duration as the original.
                            </small>
                        </div>

                        {# MD-1, 18 Oct 2026 - D28. SHIFTING A PLAN WAS ONLY  #}
                        {# POSSIBLE FROM THE VIEW PAGE. duplicate_meal_plan   #}
                        {# has read delete_original since it was written, and #}
                        {# this dialog - which posts to that same view - just #}
                        {# never offered it. Same markup as view_meal_plan.   #}
                        <hr>
                        <div class="form-group">
                            <div class="custom-control custom-checkbox">
                                <input type="checkbox"
                                       class="custom-control-input"
                                       id="delete_original"
                                       name="delete_original"
                                       value="yes">
                                <label class="custom-control-label" for="delete_original">
                                    <strong>Delete original meal plan after duplicating</strong>
                                </label>
                            </div>
                            <small class="form-text text-muted">
                                <i class="fas fa-info-circle"></i> If checked, this will shift the meal plan to new dates (original will be deleted)
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">"""

D28B_WAS = """                        <small class="form-text text-muted">
                            The plan will maintain the same duration as the original.
                        </small>
                    </div>
                </div>
                <div class="modal-footer">"""
D28B_NOW = """                        <small class="form-text text-muted">
                            The plan will maintain the same duration as the original.
                        </small>
                    </div>

                    {# MD-1, 18 Oct 2026 - D28, the list page's copy. #}
                    <hr>
                    <div class="form-group">
                        <div class="custom-control custom-checkbox">
                            <input type="checkbox"
                                   class="custom-control-input"
                                   id="delete_original"
                                   name="delete_original"
                                   value="yes">
                            <label class="custom-control-label" for="delete_original">
                                <strong>Delete original meal plan after duplicating</strong>
                            </label>
                        </div>
                        <small class="form-text text-muted">
                            <i class="fas fa-info-circle"></i> If checked, this will shift the meal plan to new dates (original will be deleted)
                        </small>
                    </div>
                </div>
                <div class="modal-footer">"""

# ==================================================================== E29
# THE CALENDAR ASKED THE DATABASE ONCE PER PLAN AND TWICE PER DAY.
#
# (a) the month's dots: one query per overlapping plan
# (b) the week detail: one for the day plus one for its recipes, seven
#     times over - fourteen queries to draw one week
# (c) the plan list's recipe count: NOT a slow query. There is no
#     annotation at all, so {{ plan.total_recipes }} renders EMPTY
# (d) the View page: courses and categories per recipe
# (e) the Edit form: courses, categories and proteins per recipe
E29A_WAS = """    dates_with_meals = set()
    for plan in month_meal_plans:
        days_with_recipes = MealPlanDay.objects.filter(
            meal_plan=plan,
            recipes__isnull=False
        ).values_list('date', flat=True).distinct()
        dates_with_meals.update(days_with_recipes)"""
E29A_NOW = """    # MD-1, 18 Oct 2026 - E29. ONE QUERY, NOT ONE PER PLAN. This was a
    # loop that asked the database for each overlapping plan's days
    # separately; a month with eight plans in it cost eight queries to
    # draw the dots.
    dates_with_meals = set(
        MealPlanDay.objects.filter(
            meal_plan__in=month_meal_plans,
            recipes__isnull=False
        ).values_list('date', flat=True).distinct())"""

E29B_WAS = """    all_meal_plans = MealPlan.objects.all().order_by('-start_date')"""
E29B_NOW = """    # MD-1, 18 Oct 2026 - E29. ONE QUERY FOR EVERY PLAN'S COUNT.
    #
    # The plan list prints {{ plan.total_recipes }}, which is a PROPERTY
    # on MealPlan that runs its own COUNT - so a list of twelve plans
    # cost twelve queries to print twelve numbers. Exactly what the
    # design record says, and the annotation is the answer.
    #
    # `recipe_count` AND NOT `total_recipes`. Annotating over the
    # property's name raises "property total_recipes of MealPlan object
    # has no setter" the moment the queryset is iterated - measured, by
    # writing it that way first and driving the page. And
    # `recipe_count` is not a name invented here: meal_plans() has
    # annotated exactly that, with exactly this expression, since it was
    # written, and meal_plans.html reads it.
    #
    # The property stays. view_meal_plan.html uses it for ONE plan,
    # where one query is the right number.
    all_meal_plans = MealPlan.objects.annotate(
        recipe_count=Count('days__recipes')
    ).order_by('-start_date')"""

# AND THE TEMPLATE READS THE ANNOTATION, pluralised like its sibling on
# the list page rather than always saying "recipes".
E29B2_WAS = """                            <i class="fas fa-utensils"></i> {{ plan.total_recipes }} recipes"""
E29B2_NOW = """                            {# MD-1, 18 Oct 2026 - E29. The annotation, not the    #}
                            {# model property - the property runs a COUNT of its   #}
                            {# own, so this line was one query per plan in the      #}
                            {# list. Pluralised while it was being touched, the     #}
                            {# way meal_plans.html already does it: a plan with     #}
                            {# one meal on it said "1 recipes".                     #}
                            <i class="fas fa-utensils"></i> {{ plan.recipe_count }} recipe{{ plan.recipe_count|pluralize }}"""

E29C_WAS = """        # If there's a meal plan for this week, get recipes for this day
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

                for mpr in recipes:"""
E29C_NOW = """        # If there's a meal plan for this week, get recipes for this day
        #
        # MD-1, 18 Oct 2026 - E29. FOURTEEN QUERIES BECAME ONE PAIR.
        # This used to ask for the day and then for its recipes, inside
        # a loop over seven days. week_day_map is built once above.
        if selected_meal_plan:
            meal_plan_day = week_day_map.get(day_date)

            if meal_plan_day:
                day_data['meal_plan_day_id'] = meal_plan_day.meal_plan_day_id
                recipes = meal_plan_day.recipes.all()

                for mpr in recipes:"""

E29D_WAS = """    # Build week detail data
    week_days = []"""
E29D_NOW = """    # MD-1, 18 Oct 2026 - E29. THE WEEK'S DAYS AND MEALS, IN ONE GO.
    #
    # The loop below used to ask for each day and then for that day's
    # recipes - two queries a day, fourteen to draw a week. One
    # prefetched query answers both, and the loop reads a dict.
    #
    # .all() on the prefetched manager keeps the cache; the Prefetch
    # carries the sort order, so the ordering the page relies on is the
    # queryset's and not a second trip.
    week_day_map = {}
    if selected_meal_plan:
        week_day_map = dict(
            (d.date, d) for d in MealPlanDay.objects.filter(
                meal_plan=selected_meal_plan,
                date__gte=selected_week_start,
                date__lte=selected_week_end,
            ).prefetch_related(
                Prefetch('recipes',
                         queryset=MealPlanRecipe.objects
                         .select_related('recipe')
                         .order_by('sort_order'))))

    # Build week detail data
    week_days = []"""

# E29 (d) and (e) - the two Prefetch blocks that stop at the recipe.
# `select_related('recipe')` fetches the recipe row and nothing hanging
# off it, so `recipe.courses.all` in the template and
# `recipe.courses.all()` in the view are each a query per recipe. A
# seven-day plan with three meals a day is sixty-three of them on the
# View page alone.
E29E_WAS = """                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        queryset=MealPlanRecipe.objects.select_related('recipe')
                    )
                )"""
E29E_NOW = """                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        # MD-1, 18 Oct 2026 - E29. The TAGS as well as
                        # the recipe. This stopped at select_related,
                        # so recipe.courses.all and
                        # recipe.categories.all in the template were a
                        # query each, per recipe - sixty-three of them
                        # on a seven-day plan with three meals a day.
                        queryset=MealPlanRecipe.objects
                        .select_related('recipe')
                        .prefetch_related('recipe__courses',
                                          'recipe__categories')
                    )
                )"""

E29F_WAS = """                        queryset=MealPlanRecipe.objects.select_related('recipe').order_by('sort_order')"""
E29F_NOW = """                        # MD-1, 18 Oct 2026 - E29. And the three the Edit
                        # form serialises per recipe: courses,
                        # categories and proteins.
                        queryset=MealPlanRecipe.objects
                        .select_related('recipe')
                        .prefetch_related('recipe__courses',
                                          'recipe__categories',
                                          'recipe__proteins')
                        .order_by('sort_order')"""

# ==================================================================== E31
# THE CALENDAR LOADED ITS OWN COPY OF jQUERY ON TOP OF BASE'S.
# base.html already loads jquery-3.6.0 - the same version, from the same
# CDN - after {% block content %}, so this tag fetched it a second time
# and replaced the one every other page shares.
E31_WAS = """<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
// Navigation functions"""
E31_NOW = """{# MD-1, 18 Oct 2026 - E31. THE SECOND COPY OF jQUERY IS GONE.      #}
{#                                                                  #}
{# base.html loads jquery-3.6.0 from the same CDN after             #}
{# {% block content %}, so this page fetched the same file twice and #}
{# the second one replaced the instance the rest of the application  #}
{# shares - including any plugin that had already registered on it.  #}
{#                                                                   #}
{# The functions below are called on interaction, never at parse      #}
{# time, so $ is defined by the time any of them runs. That is the    #}
{# same arrangement every other page in the tree uses.               #}
<script>
// Navigation functions"""

# ==================================================================== E32
# DEBUG OUTPUT, IN BOTH LANGUAGES.
#
# THE PYTHON SIDE. Three handlers print a traceback to stdout:
#
#     print(f"\\n!!! ERROR: {str(e)} !!!")
#     traceback.print_exc()
#
# On Railway that is an unlabelled traceback in the deploy log with
# nothing to say which view produced it, and `print` is not a channel
# anybody can turn down. The house already has the pattern - ai_extract
# and recipe_extras both carry `logger = logging.getLogger(__name__)` -
# and logger.exception writes the SAME traceback with the module's name
# in front of it.
E32LOG_WAS = """from pages.models import ("""
E32LOG_NOW = """# MD-1, 18 Oct 2026 - E32. Three handlers in this module printed a
# traceback to stdout with print() and traceback.print_exc(), which on
# Railway is an unlabelled traceback in the deploy log and not a channel
# anybody can turn down. ai_extract.py and recipe_extras.py already do
# this; meal_planning.py is the third.
logger = logging.getLogger(__name__)

from pages.models import ("""

E32IMP_WAS = """import json
import math
import traceback"""
# MD-1 - AND `math` GOES WITH IT. Every math.ceil in this module lived
# inside the nested round_shopping_qty that E33 deletes, so after the
# dedupe the import has no caller. Measured after the deletion, not
# before: `traceback` goes for E32 and `math` for E33, and `logging`
# arrives for E32.
E32IMP_NOW = """import json
import logging"""

E32A_WAS = """        except Exception as e:
            print(f"\\n!!! ERROR: {str(e)} !!!")
            traceback.print_exc()
            messages.error(request, f'Error creating meal plan: {str(e)}')"""
E32A_NOW = """        except Exception as e:
            # MD-1, 18 Oct 2026 - E32. Was print() plus
            # traceback.print_exc(). logger.exception writes the same
            # traceback with this module's name in front of it.
            logger.exception('create_meal_plan failed')
            messages.error(request, f'Error creating meal plan: {str(e)}')"""

E32B_WAS = """        except Exception as e:
            print(f"\\n!!! ERROR: {str(e)} !!!")
            traceback.print_exc()
            messages.error(request, f'Error updating meal plan: {str(e)}')"""
E32B_NOW = """        except Exception as e:
            # MD-1, 18 Oct 2026 - E32, the second of three.
            logger.exception('edit_meal_plan failed for plan %s',
                             meal_plan_id)
            messages.error(request, f'Error updating meal plan: {str(e)}')"""

E32C_WAS = """    except Exception as e:
        traceback.print_exc()
        messages.error(request, f'Error generating shopping list: {str(e)}')"""
E32C_NOW = """    except Exception as e:
        # MD-1, 18 Oct 2026 - E32, the third. This one had no print()
        # in front of it, so the traceback arrived in the log with
        # neither a module nor a message to say what had been attempted.
        logger.exception('meal_plan_shopping_list failed for plan %s',
                         meal_plan_id)
        messages.error(request, f'Error generating shopping list: {str(e)}')"""

# THE BROWSER SIDE. Nineteen console.log calls trace the create and
# edit form line by line - the recipe count, every parsed date, every
# restored day - and one console.error dumps three booleans about which
# elements were not found.
#
# TRACING GOES, FAILURE REPORTING STAYS. The four remaining
# console.error calls each record something that actually went wrong and
# have no other record: a recipe list that is not on the page, a date
# the browser could not parse, and two conversion saves that the server
# refused. Removing those would make a failure silent, which is the
# opposite of this item.
#
# Counted, not matched loosely: the removal is driven by a pattern, so
# the number it removes is the measurement. See strip_console().
E32DUMP_WAS = """    if (!container || !section || !saveBtn) {
        console.error('Required elements not found:', {
            container: !!container,
            section: !!section,
            saveBtn: !!saveBtn
        });
        return;
    }"""
E32DUMP_NOW = """    if (!container || !section || !saveBtn) {
        // MD-1, 18 Oct 2026 - E32. This dumped three booleans to the
        // console. It wears console.error but it is tracing, not a
        // failure anybody can act on - and the function returns here
        // anyway, so the form simply does not open its day section.
        return;
    }"""

# ==================================================================== E33
# THREE DUPLICATIONS, AND ONE OF THEM WOULD HAVE SHIPPED A CRASH.
#
# (a) THE ROUNDING HELPER, written twice. aggregate_meal_plan_ingredients
#     carries a nested round_shopping_qty that is byte-for-byte the same
#     decisions as shopping.round_shopping_quantity - the same three unit
#     types, the same thresholds at 10 and 100, the same round-UP in
#     every branch. The module's own docstring has flagged it as "a
#     post-split dedupe candidate" since the split.
E33A_WAS = """from .conversions import convert_quantity, get_conversion_cache"""
E33A_NOW = """from .conversions import convert_quantity, get_conversion_cache
# MD-1, 18 Oct 2026 - E33. The nested round_shopping_qty in
# aggregate_meal_plan_ingredients made the same decisions as this, in
# the same order, with the same thresholds. This module's docstring has
# called it a dedupe candidate since the views were split.
from .shopping import round_shopping_quantity"""

E33A2_WAS = """    def round_shopping_qty(qty, unit):
        \"\"\"
        Round quantities intelligently based on unit type for shopping lists.
        NEVER rounds down - always rounds UP to ensure you have enough.
        \"\"\"
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

    def get_unit_display(unit, qty):"""
E33A2_NOW = """    # MD-1, 18 Oct 2026 - E33. THE NESTED COPY IS GONE.
    #
    # round_shopping_qty lived here and made exactly the same decisions
    # as shopping.round_shopping_quantity, which is imported at the top
    # of the module now: the same three unit types, the same thresholds
    # at 10 and 100, round UP in every branch, and the same `if qty <= 0
    # return qty` guard. Compared line by line before this was deleted,
    # not assumed from the name.
    round_shopping_qty = round_shopping_quantity

    def get_unit_display(unit, qty):"""

# (b) THE RECIPE ROW, WRITTEN OUT THREE TIMES in create_meal_plan.html -
#     once for the rows an Edit loads, once for the rows a date change
#     restores, and once for the row the picker adds. The three differ
#     only in which variable holds the name, the id and the servings.
#
#     This is also B10's surface. MP-1 had to wrap the same recipe name
#     in esc() three times yesterday afternoon; one function is one
#     place for the next person to get that right.
E33B_WAS = """// MP-1, 18 Oct 2026 - B10. EVERY PIECE OF DATABASE TEXT THAT REACHES"""
E33B_NOW = """// MD-1, 18 Oct 2026 - E33. ONE RECIPE ROW, NOT THREE.
//
// This markup was written out three times on this page: once for the
// rows an Edit loads (populateExistingRecipes), once for the rows a
// date change puts back (restoreRecipes), and once for the row the
// picker adds (selectRecipeForDay). The three differed only in which
// variable held the name, the id and the servings.
//
// It is also B10's surface. MP-1 wrapped the same recipe name in esc()
// three times yesterday; one function is one place for the next person
// to get that right.
function recipeRowHtml(dateKey, recipeId, recipeName, servings) {
    return `
                <input type="hidden" name="recipes_${dateKey}[]" value="${recipeId}">
                <div style="flex: 1;">
                    <strong>${esc(recipeName)}</strong>
                </div>

                <div style="display: flex; align-items: center; gap: 5px;">
                    <input type="number"
                           name="servings_${dateKey}[]"
                           class="servings-input"
                           min="1"
                           value="${servings}"
                           required>
                    <span style="color: var(--alv-neutral); font-size: 14px;">servings</span>
                </div>

                <button type="button" class="icon-action-btn icon-delete" onclick="removeRecipe(this)" aria-label="Remove this recipe">
                    <i class="fas fa-trash"></i>
                </button>
            `;
}

// MP-1, 18 Oct 2026 - B10. EVERY PIECE OF DATABASE TEXT THAT REACHES"""

# The three call sites, each collapsing to one line.
E33B1_WAS = """            recipeItem.innerHTML = `
                <input type="hidden" name="recipes_${day.date}[]" value="${recipe.recipe_id}">
                <div style="flex: 1;">
                    <strong>${esc(recipe.recipe_name)}</strong>
                </div>

                <div style="display: flex; align-items: center; gap: 5px;">
                    <input type="number"
                           name="servings_${day.date}[]"
                           class="servings-input"
                           min="1"
                           value="${recipe.servings}"
                           required>
                    <span style="color: var(--alv-neutral); font-size: 14px;">servings</span>
                </div>

                <button type="button" class="icon-action-btn icon-delete" onclick="removeRecipe(this)" aria-label="Remove this recipe">
                    <i class="fas fa-trash"></i>
                </button>
            `;"""
E33B1_NOW = """            // MD-1, 18 Oct 2026 - E33, one of three.
            recipeItem.innerHTML = recipeRowHtml(
                day.date, recipe.recipe_id, recipe.recipe_name,
                recipe.servings);"""

E33B2_WAS = """            recipeItem.innerHTML = `
                <input type="hidden" name="recipes_${dateStr}[]" value="${recipe.recipeId}">
                <div style="flex: 1;">
                    <strong>${esc(recipe.recipeName)}</strong>
                </div>

                <div style="display: flex; align-items: center; gap: 5px;">
                    <input type="number"
                           name="servings_${dateStr}[]"
                           class="servings-input"
                           min="1"
                           value="${recipe.servings}"
                           required>
                    <span style="color: var(--alv-neutral); font-size: 14px;">servings</span>
                </div>

                <button type="button" class="icon-action-btn icon-delete" onclick="removeRecipe(this)" aria-label="Remove this recipe">
                    <i class="fas fa-trash"></i>
                </button>
            `;"""
E33B2_NOW = """            // MD-1, 18 Oct 2026 - E33, two of three.
            recipeItem.innerHTML = recipeRowHtml(
                dateStr, recipe.recipeId, recipe.recipeName,
                recipe.servings);"""

E33B3_WAS = """    recipeItem.innerHTML = `
        <input type="hidden" name="recipes_${currentMealPlanDate}[]" value="${recipeId}">
        <div style="flex: 1;">
            <strong>${esc(recipeName)}</strong>
        </div>

        <div style="display: flex; align-items: center; gap: 5px;">
            <input type="number"
                   name="servings_${currentMealPlanDate}[]"
                   class="servings-input"
                   min="1"
                   value="${servings}"
                   required>
            <span style="color: var(--alv-neutral); font-size: 14px;">servings</span>
        </div>

        <button type="button" class="icon-action-btn icon-delete" onclick="removeRecipe(this)" aria-label="Remove this recipe">
            <i class="fas fa-trash"></i>
        </button>
    `;"""
E33B3_NOW = """    // MD-1, 18 Oct 2026 - E33, three of three.
    recipeItem.innerHTML = recipeRowHtml(
        currentMealPlanDate, recipeId, recipeName, servings);"""

# (c) MealPlanRecipe.servings_multiplier - A PROPERTY NOBODY CALLS, AND
#     THE RECORD'S FIX WOULD HAVE SHIPPED A CRASH.
#
#     It reads `self.servings / self.recipe.servings`: float division,
#     NO GUARD. A recipe whose servings are 0 or None is a
#     ZeroDivisionError or a TypeError. The expression it would replace,
#     inline in the aggregator, is
#
#         Decimal(meal_recipe.servings) / Decimal(recipe.servings or 1)
#
#     Decimal, and guarded. So the property takes the safe expression
#     FIRST and is then used - using it as it stood would have moved a
#     crash into a property and called it a dedupe.
E33C_WAS = """    @property
    def servings_multiplier(self):
        \"\"\"Calculate multiplier for scaling ingredients\"\"\"
        return self.servings / self.recipe.servings"""
E33C_NOW = """    @property
    def servings_multiplier(self):
        \"\"\"How far to scale this recipe's ingredients for this meal.

        MD-1, 18 Oct 2026 - E33. This property had no caller. It read

            return self.servings / self.recipe.servings

        - float division with no guard, so a recipe whose servings are 0
        or None raised ZeroDivisionError or TypeError. The design record
        asks for the shopping list to use it; the shopping list's own
        inline expression was already the safe one, and THAT is what is
        here now:

            Decimal(self.servings) / Decimal(self.recipe.servings or 1)

        Decimal because every quantity downstream is a Decimal and
        mixing the two raises, and `or 1` because a recipe with no yield
        recorded should scale by one rather than refuse to be shopped
        for.
        \"\"\"
        return Decimal(self.servings) / Decimal(self.recipe.servings or 1)"""

E33C2_WAS = """            servings_multiplier = Decimal(meal_recipe.servings) / Decimal(recipe.servings or 1)"""
E33C2_NOW = """            # MD-1, 18 Oct 2026 - E33. The model's own property, which
            # was unused until now and carried this expression's unsafe
            # twin. It is this expression now.
            servings_multiplier = meal_recipe.servings_multiplier"""


# ============================================== THREE SIBLING PREMISES MOVED
# E33 collapses three copies of the recipe row into one function, and
# D28 puts a checkbox on two more pages. Three instruments measured the
# old shape, all three were right to, and all three are corrected here -
# because a round that changes a premise owns the correction.

# (a) THE LOOSE-BUTTON REGISTER. alv_rowactions.NAMED pins an EXACT
#     count per page, deliberately: "A page that grows one more loose
#     button does not inherit the exemption." It caught this one
#     SHRINKING, which is the same discipline working in the other
#     direction - three copies of the trashcan became one.
RA = 'alv_rowactions.py'
RA_WAS = """    'create_meal_plan.html': {
        'count': 3,
        'classes': ('icon-delete',),
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal.',
    },"""
RA_NOW = """    # MD-1, 18 Oct 2026 - THREE BECAME ONE. E33 collapsed the three
    # copies of the recipe row on this page into one recipeRowHtml()
    # function, so there is one trashcan in the source where there were
    # three. The pin caught it - which is the register working in the
    # direction nobody designed it for: it was built so a page that
    # GREW a loose button could not inherit the exemption, and it
    # refused a page that lost two just as loudly.
    'create_meal_plan.html': {
        'count': 1,
        'classes': ('icon-delete',),
        # AND `since`, FOR THE SAME REASON VC-1 ADDED THE KEY.
        # test_row_exempt reads a named page AS THE ROUND THAT NAMED IT
        # LEFT IT, which for this entry is RA-5's era - and there were
        # three then. Without this the count would be read against a
        # snapshot taken before E33 existed and the register would be
        # called wrong for being right.
        'since': '.bak_mealdisplay',
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal, written once since MD-1.',
    },"""

# (b) THE CUSTOM-CHECKBOX CENSUS. D28 puts the shift option on two more
#     Duplicate dialogs, so the component goes from 3 pages to 5 and
#     from 13 controls to 15.
CC = 'test_custom_control.py'
CC_WAS = """ok(len(users) == 3, 'the component is used on %d pages, base aside'
   % len(users))
ok(sum(users.values()) == 13,"""
CC_NOW = """# MD-1, 18 Oct 2026 - 3 PAGES BECAME 5, AND 13 CONTROLS 15. D28 put
# "Delete original after duplicating" on the Duplicate dialogs of the
# Meal Plans list and the calendar; it had been on the plan page only,
# so a plan could be SHIFTED from one screen out of three. Same markup
# as the one that was already there, and base serves all of them.
ok(len(users) == 5, 'the component is used on %d pages, base aside'
   % len(users))
ok(sum(users.values()) == 15,"""

# (c) MP-1'S OWN SUITE. It names each of nine escaped interpolations
#     one at a time, on purpose - "a count would pass on nine wrong
#     sites as happily as nine right ones". E33 wrote the row once, so
#     one of the nine names is gone: the restore path and the Edit path
#     and the picker path now call the same function.
#
#     MP-1'S CLAIM IS STILL TRUE AND IS NOW STRONGER - the name is
#     escaped in ONE place rather than three. What changed is where to
#     look.
MF = 'test_meal_fixes.py'
MF_WAS = """                 '${esc(recipe.recipeName)}',
"""
MF_NOW = """"""
MF2_WAS = """    # AND NOTHING BARE LEFT. The positive checks above would all pass on
    # a page that also still carried an unescaped copy."""
MF2_NOW = """    # MD-1, 18 Oct 2026 - ONE OF THE NINE NAMES IS GONE, and the claim
    # is stronger for it. E33 collapsed the three copies of the recipe
    # row into recipeRowHtml(), so the restore path's
    # `${esc(recipe.recipeName)}` no longer exists - all three paths
    # call one function, and that function escapes the name once.
    c['B10 the row is built in one place, and it escapes there'] = (
        'function recipeRowHtml(' in code
        and '${esc(recipeName)}' in code)
    # AND NOTHING BARE LEFT. The positive checks above would all pass on
    # a page that also still carried an unescaped copy."""

#     AND test_row_exempt PINS THE TOTAL TWICE - once from the register
#     and once from the report's own printed line. Both move from five
#     on three pages to three on three, for the same reason.
RX = 'test_row_exempt.py'
RX_WAS = """total = sum(e['count'] for e in RA.NAMED.values())
ok(total == 5, 'it names %d control(s) on %d page(s)'"""
RX_NOW = """total = sum(e['count'] for e in RA.NAMED.values())
# MD-1, 18 Oct 2026 - FIVE BECAME THREE. E33 collapsed the three copies
# of the recipe row on create_meal_plan into one recipeRowHtml(), so
# that page's entry went from three loose trashcans to one. Still three
# pages; two fewer controls.
ok(total == 3, 'it names %d control(s) on %d page(s)'"""

RX2_WAS = """ok('NAMED, NOT IN A WRAPPER - 5 button(s) on 3 page(s)' in out,
   'the report names all five', out[-500:])"""
RX2_NOW = """# MD-1, 18 Oct 2026 - and the report's own line says three now.
ok('NAMED, NOT IN A WRAPPER - 3 button(s) on 3 page(s)' in out,
   'the report names all three', out[-500:])"""

#     AND THREE MORE CENSUSES READ THE SAME TWO NUMBERS. The register
#     total is pinned in four files altogether, and E31's deleted
#     jQuery tag is pinned in a fifth. Every one of them was right.
VC = 'test_vocabulary.py'
VC_WAS = """ok(len(ra.NAMED) == 3
   and sum(v['count'] for v in ra.NAMED.values()) == 5,
   '  which makes five such controls on three pages',"""
VC_NOW = """# MD-1, 18 Oct 2026 - still three pages, three controls now. E33 wrote
# create_meal_plan's recipe row once instead of three times.
ok(len(ra.NAMED) == 3
   and sum(v['count'] for v in ra.NAMED.values()) == 3,
   '  which makes three such controls on three pages',"""

RW = 'test_row_wrap.py'
RW_WAS = """LOOSE_NOW = 5   # VC-1, 14 Oct 2026"""
RW_NOW = """LOOSE_NOW = 3   # MD-1, 18 Oct 2026 - E33 collapsed create_meal_plan's three copies of the recipe row into one recipeRowHtml(), so three loose trashcans became one. The first count in this register to go DOWN.   # (was 5)   # VC-1, 14 Oct 2026"""

# AND THE SECOND jQUERY. E31 removed the calendar's duplicate copy -
# base.html already loads jquery-3.6.0 from the same CDN - so the
# census of pages that load a second one is 33 where it was 34. This
# suite counts them deliberately without fixing them; MD-1 fixed one.
PV = 'test_pdf_viewer.py'
PV_WAS = """N_DUP_JQUERY = 34"""
PV_NOW = """N_DUP_JQUERY = 33   # MD-1, 18 Oct 2026 - E31 took meal_plan_calendar's second copy out; base already loads the same file from the same CDN   # (was 34)"""

# ============================================================ REGISTRATION
TREE_WAS = """    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    # Nineteen items that break, expose or lose data. Wide from birth.
    'test_meal_fixes.py',
]"""
TREE_NOW = """    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    # Nineteen items that break, expose or lose data. Wide from birth.
    'test_meal_fixes.py',
    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Twelve
    # display, navigation, query and hygiene items. Wide from birth.
    'test_meal_display.py',
]"""

REG_WAS = """    # MP-1, 18 Oct 2026 - Meal Plans release 1. The nineteen items from
    # the design record that break, expose or lose data.
    '.bak_mealfix',
]"""
REG_NOW = """    # MP-1, 18 Oct 2026 - Meal Plans release 1. The nineteen items from
    # the design record that break, expose or lose data.
    '.bak_mealfix',
    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Named
    # MD-1 and not MP-2, which has been a shipped round since 3 October.
    '.bak_mealdisplay',
]"""

SUITE_WAS = """    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    'test_meal_fixes.py'
)"""
SUITE_NOW = """    # MP-1, 18 Oct 2026 - Meal Plans release 1, groups A, B and C.
    'test_meal_fixes.py',
    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E.
    'test_meal_display.py'
)"""

SENT_WAS = (
    "    @{ File = 'pages/templates/create_meal_plan.html'; "
    "Text = 'function esc('; What = 'MP-1: recipe names are escaped "
    "before they reach innerHTML' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- MD-1, 18 Oct 2026
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'week_day_map'; What = 'MD-1: the calendar week is one pair of queries, not fourteen' },
    @{ File = 'pages/templates/view_meal_plan.html'; Text = '.btn-action-disabled'; What = 'MD-1: the swallowed selector that made disabled buttons look live' },"""


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
    raise SystemExit('MD-1 REFUSED: %s' % msg)


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
    """Every occurrence, and the count must be the one that was measured."""
    old = fit(text, old)
    new = fit(text, new)
    got = text.count(old)
    if got != want:
        refuse('%s: expected exactly %d occurrence(s) of %r, found %d - '
               're-measure rather than widening the number'
               % (where, want, old[:60], got))
    return text.replace(old, new)


CONSOLE = re.compile(r'(?m)^[ \t]*console\.log\([^\n]*\);[ \t]*\r?\n')


def strip_console(text, want, where):
    """Remove whole-line console.log statements. COUNTED.

    E32 asks for the debug output to go, and nineteen single-line calls
    are not nineteen literal anchors anybody should maintain - so this
    is driven by a pattern, and the pattern's COUNT is the measurement.
    A file that grew a twentieth call since 18 Oct is a file this round
    has not read.

    console.log ONLY, and only where the whole statement is the line.
    The four console.error calls that remain each record a real failure
    with no other trace - a recipe list missing from the page, a date
    the browser could not parse, two conversion saves the server
    refused. Removing those would make a failure silent, which is the
    opposite of this item.

    A multi-line call is not matched and must be given its own literal;
    there is one, and E32DUMP is it."""
    got = len(CONSOLE.findall(text))
    if got != want:
        refuse('%s: expected exactly %d single-line console.log call(s), '
               'found %d. Debug output moves; the count is how this round '
               'knows it is reading the file it measured.'
               % (where, want, got))
    return CONSOLE.sub('', text)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    v = read(pv)

    # ---------------------------------------------------------------- 0
    if 'MD-1, 18 Oct 2026' in v:
        print('MD-1  already applied.')
        return 0

    # ---------------------------------------------------------------- 1
    # MP-1 FIRST. Four of MD-1's anchors are lines MP-1 wrote - the
    # esc() helper it added, the C13 warning before the Edit redirect,
    # the two Prefetch blocks it did not touch but whose neighbours it
    # did - and six more sit inside blocks MP-1 rewrote. Applying MD-1
    # to a tree without MP-1 would refuse on an anchor and say nothing
    # useful about why.
    if 'MP-1, 18 Oct 2026' not in v:
        refuse('MP-1 is not applied. MD-1 builds on it - four of its '
               'anchors are lines MP-1 wrote - so run apply_meal_fixes.py '
               'first.')
    if not os.path.isfile(os.path.join(root, ME)):
        refuse('%s is not on disk - it is half the round' % ME)

    # ---------------------------------------------------------------- 2
    # THE VIEW MODULE.
    v = swap(v, E32IMP_WAS, E32IMP_NOW, '%s (E32+E33, the imports)' % VIEW)
    v = swap(v, E32LOG_WAS, E32LOG_NOW, '%s (E32, the logger)' % VIEW)
    v = swap(v, E33A_WAS, E33A_NOW, '%s (E33, the shared helper)' % VIEW)
    v = swap(v, E33A2_WAS, E33A2_NOW, '%s (E33, the nested copy)' % VIEW)
    v = swap(v, E33C2_WAS, E33C2_NOW, '%s (E33, the multiplier)' % VIEW)
    v = swap(v, E32A_WAS, E32A_NOW, '%s (E32, create)' % VIEW)
    v = swap(v, E32B_WAS, E32B_NOW, '%s (E32, edit)' % VIEW)
    v = swap(v, E32C_WAS, E32C_NOW, '%s (E32, shopping list)' % VIEW)
    v = swap(v, D23_WAS, D23_NOW, '%s (D23, the start date)' % VIEW)
    v = swap(v, D23B_WAS, D23B_NOW, '%s (D23, the context)' % VIEW)
    v = swap(v, D24_WAS, D24_NOW, '%s (D24, the redirect)' % VIEW)
    v = swap(v, D26A_WAS, D26A_NOW, '%s (D26, Monday)' % VIEW)
    v = swap(v, E29A_WAS, E29A_NOW, '%s (E29, the dots)' % VIEW)
    v = swap(v, E29B_WAS, E29B_NOW, '%s (E29, the counts)' % VIEW)
    v = swap(v, E29D_WAS, E29D_NOW, '%s (E29, the week map)' % VIEW)
    v = swap(v, E29C_WAS, E29C_NOW, '%s (E29, the week loop)' % VIEW)
    v = swap_all(v, E29E_WAS, E29E_NOW, 1, '%s (E29, view tags)' % VIEW)
    v = swap(v, E29F_WAS, E29F_NOW, '%s (E29, edit tags)' % VIEW)

    # NOTHING MAY STILL REACH FOR WHAT THE IMPORTS LOST. Two names leave
    # this module in this round - traceback for E32 and math for E33 -
    # and a surviving caller is an ImportError on the next deploy, which
    # is the one failure mode a patcher must never create.
    try:
        parsed = ast.parse(v)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (VIEW, e.lineno, e.msg))

    # ASKED OF THE PARSE TREE, NOT OF THE TEXT. Two names leave this
    # module in this round - `traceback` for E32 and `math` for E33 -
    # and a surviving caller is a NameError on the next request, which
    # is the one failure a patcher must never create.
    #
    # The first spelling of this check searched for the strings
    # 'traceback.' and 'math.' and REFUSED THE CORRECT FILE, because
    # MD-1's own comments explain that print() and traceback.print_exc()
    # used to be there. That is the third time today a check has read a
    # comment about a thing as the thing - A4, C14 and the Workspace
    # docstring were the others - and the answer is the same: ask the
    # instrument that can tell code from prose. Here that is the tree.
    gone = set()
    for node in ast.walk(parsed):
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in ('traceback', 'math')):
            gone.add(node.value.id)
    if gone:
        refuse('%s still calls %s after the imports were trimmed - E32 '
               'removes traceback and E33 removes math, so a surviving '
               'caller is a NameError on the next request'
               % (VIEW, ' and '.join(sorted(gone))))
    out[pv] = v

    # ---------------------------------------------------------------- 3
    # THE LIST PAGE NEEDS next_monday, so the view that renders it has
    # to supply it. D23.
    mp = out[pv]
    LIST_WAS = """    context = {
        'meal_plans': meal_plans_list,
    }"""
    LIST_NOW = """    # MD-1, 18 Oct 2026 - D23. The list has no week of its own, so its
    # Create button sends the NEXT Monday - which is what the design
    # record asks for, and what the calendar does with the week it is
    # showing.
    today = datetime.now().date()
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)

    context = {
        'meal_plans': meal_plans_list,
        'next_monday': next_monday,
    }"""
    out[pv] = swap(mp, LIST_WAS, LIST_NOW, '%s (D23, next_monday)' % VIEW)
    try:
        ast.parse(out[pv])
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (VIEW, e.lineno, e.msg))

    # ---------------------------------------------------------------- 4
    # THE MODEL PROPERTY.
    p = os.path.join(root, MODELS)
    s = swap(read(p), E33C_WAS, E33C_NOW, '%s (E33, the property)' % MODELS)
    try:
        ast.parse(s)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (MODELS, e.lineno, e.msg))
    out[p] = s

    # ---------------------------------------------------------------- 5
    # THE VIEW PAGE - D21, D22a.
    p = os.path.join(root, VIEWT)
    t = read(p)
    t = swap(t, D21_WAS, D21_NOW, '%s (D21, the day heading)' % VIEWT)
    t = swap(t, D22A_WAS, D22A_NOW, '%s (D22, btn-action-disabled)' % VIEWT)
    t = swap(t, D22B_WAS, D22B_NOW, '%s (D22, action-more-menu)' % VIEWT)
    out[p] = t

    # ---------------------------------------------------------------- 6
    # THE CALENDAR - D26b, D28, E29 markup, E31, D25.
    p = os.path.join(root, CAL)
    t = read(p)
    t = swap(t, D26B_WAS, D26B_NOW, '%s (D26, the selected week)' % CAL)
    t = swap(t, E29B2_WAS, E29B2_NOW, '%s (E29, the plan count)' % CAL)
    t = swap(t, D28A_WAS, D28A_NOW, '%s (D28, the shift option)' % CAL)
    t = swap(t, E31_WAS, E31_NOW, '%s (E31, the second jQuery)' % CAL)
    t = swap(t, D25B_WAS, D25B_NOW, '%s (D25, the preference)' % CAL)
    out[p] = t

    # ---------------------------------------------------------------- 7
    # THE LIST PAGE - D23, D25, D28.
    p = os.path.join(root, LIST)
    t = read(p)
    t = swap(t, D23C_WAS, D23C_NOW, '%s (D23, the bar link)' % LIST)
    t = swap(t, D23D_WAS, D23D_NOW, '%s (D23, the empty state)' % LIST)
    t = swap(t, D25A_WAS, D25A_NOW, '%s (D25, the preference)' % LIST)
    t = swap(t, D28B_WAS, D28B_NOW, '%s (D28, the shift option)' % LIST)
    out[p] = t

    # ---------------------------------------------------------------- 8
    # CREATE / EDIT - D27, E32, E33.
    p = os.path.join(root, CREATE)
    t = read(p)
    t = swap(t, D27A_WAS, D27A_NOW, '%s (D27, the note)' % CREATE)
    t = swap(t, D27A2_WAS, D27A2_NOW, '%s (D27, the start date)' % CREATE)
    t = swap(t, D27B_WAS, D27B_NOW, '%s (D27, the end date)' % CREATE)
    t = swap(t, E33B_WAS, E33B_NOW, '%s (E33, the row helper)' % CREATE)
    t = swap(t, E33B1_WAS, E33B1_NOW, '%s (E33, site 1)' % CREATE)
    t = swap(t, E33B2_WAS, E33B2_NOW, '%s (E33, site 2)' % CREATE)
    t = swap(t, E33B3_WAS, E33B3_NOW, '%s (E33, site 3)' % CREATE)
    t = swap(t, E32DUMP_WAS, E32DUMP_NOW, '%s (E32, the element dump)' % CREATE)
    t = strip_console(t, 18, '%s (E32)' % CREATE)
    out[p] = t

    # ---------------------------------------------------------------- 9
    # THE SHOPPING LIST - E32 only.
    p = os.path.join(root, SHOP)
    out[p] = strip_console(read(p), 1, '%s (E32)' % SHOP)

    # -------------------------------------------------------------- 9b
    # THE THREE SIBLING PREMISES THIS ROUND MOVED.
    p = os.path.join(root, RA)
    out[p] = swap(read(p), RA_WAS, RA_NOW, '%s (the loose-button pin)' % RA)

    p = os.path.join(root, CC)
    out[p] = swap(read(p), CC_WAS, CC_NOW, '%s (the component census)' % CC)

    p = os.path.join(root, VC)
    out[p] = swap(read(p), VC_WAS, VC_NOW, '%s (the register total)' % VC)

    p = os.path.join(root, RW)
    out[p] = swap(read(p), RW_WAS, RW_NOW, '%s (LOOSE_NOW)' % RW)

    p = os.path.join(root, PV)
    out[p] = swap(read(p), PV_WAS, PV_NOW, '%s (N_DUP_JQUERY)' % PV)

    p = os.path.join(root, RX)
    t = swap(read(p), RX_WAS, RX_NOW, '%s (the register total)' % RX)
    t = swap(t, RX2_WAS, RX2_NOW, '%s (the report line)' % RX)
    out[p] = t

    p = os.path.join(root, MF)
    t = swap(read(p), MF_WAS, MF_NOW, '%s (the vanished name)' % MF)
    t = swap(t, MF2_WAS, MF2_NOW, '%s (what replaced it)' % MF)
    out[p] = t

    # --------------------------------------------------------------- 10
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
    out[p] = s.replace('CONVERTED_N = %d' % was,
                       'CONVERTED_N = %d   # MD-1, 18 Oct 2026 - this '
                       'round own suite   # (was %d)' % (was + 1, was), 1)

    # --------------------------------------------------------------- 11
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))

    if CHECK:
        print('MD-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, val in out.items():
        backup(k)
        write(k, val)
    print('MD-1 applied.  Meal Plans release 1, groups D and E.')
    print('   D  the day heading on the View page says Mon 19 Oct rather')
    print('      than nothing; two swallowed CSS selectors - one repaired,')
    print('      one deleted because base owns it; Create opens on the week')
    print('      the calendar was showing; saving an Edit keeps the calendar')
    print('      context; the remembered view finally works, by deleting two')
    print('      lines; the week is a Monday and is highlighted; past dates')
    print('      are allowed on both screens; and a plan can be shifted from')
    print('      the list and the calendar, not only from the View page')
    print('   E  the calendar asks the database twice instead of twenty-odd')
    print('      times, and its recipe counts appear at all; the View and')
    print('      Edit pages prefetch their tags; the second copy of jQuery')
    print('      is gone; nineteen console.log calls and three stdout')
    print('      tracebacks go, four console.error calls stay; and three')
    print('      duplications become one - including a property whose')
    print('      unguarded division would have crashed on a recipe with no')
    print('      servings recorded')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
