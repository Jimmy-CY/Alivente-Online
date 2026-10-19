# -*- coding: utf-8 -*-
"""apply_meal_day.py - round MO-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE DAY SPEAKS.

Demetri, 19 Oct, was asked what a day should be able to say besides
"here is a recipe" and chose: "A note row, and Leftovers marked on a
meal."

    A NOTE       A planned night that is not a recipe. Eat out,
                 takeaway, at Helen's. MN-1 built MealEntry so a slot
                 need not have a recipe and the planner has RENDERED
                 the note row since - but nothing in the application
                 could make one, which is a column nobody can fill.

    LEFTOVERS    Monday's soup again on Wednesday. MealEntry.leftover_of
                 and counts_on_shopping_list have been in the model
                 since MN-1 and MW-1 took care to copy them correctly;
                 this is the round that lets somebody MAKE one.

WHY A LEFTOVER IS NOT JUST ANOTHER MEAL. counts_on_shopping_list
returns False for it, so the second night is free: you bought the
ingredients once, on the night you cooked. That is the whole feature.
It is also why a leftover row has NO SERVINGS STEPPER - a number that
changes nothing on the shopping list is a control that lies - and why
it names the day it was cooked on instead.

THREE DECISIONS THIS ROUND TAKES, AND THE REASONS

    A LEFTOVER OF A LEFTOVER POINTS AT THE ORIGINAL. Soup on Monday,
    leftovers Wednesday, leftovers again Friday: all three of Wednesday
    and Friday point at Monday. The shopping list works either way -
    any leftover_of at all is free - but a chain would have the screen
    saying "leftovers of leftovers of soup" and would make "how many
    nights did this pot feed us" a recursive question instead of a
    count. Flattened at the point of creation, which is the only place
    that knows.

    A LEFTOVER CANNOT BE DATED BEFORE THE MEAL IT CAME FROM. You
    cannot eat Wednesday's leftovers on Monday. Refused with a
    sentence, not silently moved - C13 is what silently moving dates
    looks like.

    A NOTE IS TRIMMED AND REQUIRED. MealEntry.note is 200 characters;
    a note of spaces is a row that says nothing, and the empty state
    already says "Nothing planned" better than an empty row would.

AND ONE QUERY, NOT ONE PER ROW. The leftover row names the day it was
cooked on, which reaches through entry.leftover_of - so the planner's
one query for the week gains select_related('leftover_of'). E29 spent
a round taking this fault off four screens and MW-1 refused to put it
back on one; neither does this.

NO MIGRATION. Nothing new is stored. Both columns shipped with 0100.

Idempotent. Every file backed up to .bak_mealday.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealday'
BASE = os.path.join('pages', 'templates', 'base.html')
RA = 'alv_rowactions.py'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_meal_day.py'
PATCHER = 'apply_meal_day.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MO-1, 19 Oct 2026'
CHECK = False


# ========================================================== THE DOCSTRING
DOC_WAS = """- send_meal_plan_shopping_list    : Email a shopping list (POST)."""
DOC_NOW = """- add_meal_note                   : A planned night that is not a
                                    recipe - Eat out, takeaway (POST).
                                    Edit-tier. MO-1, 19 Oct 2026.
- add_leftover                    : Monday's soup again on Wednesday,
                                    and it costs nothing the second
                                    time (POST). Edit-tier.
                                    MO-1, 19 Oct 2026.
- send_meal_plan_shopping_list    : Email a shopping list (POST)."""


# ============================================================= ONE QUERY
# THE LEFTOVER ROW NAMES THE DAY IT WAS COOKED ON, which reaches through
# entry.leftover_of - a query per leftover row without this. E29 took
# this fault off four screens and nothing is putting it back.
SEL_WAS = """        MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)
        .select_related('recipe')
        .prefetch_related('recipe__courses', 'recipe__categories'))"""
SEL_NOW = """        MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)
        # MO-1, 19 Oct 2026 - leftover_of joins the ONE query. The
        # leftover row prints the date of the meal it came from, and
        # that is a query per row without this. [E29]
        .select_related('recipe', 'leftover_of')
        .prefetch_related('recipe__courses', 'recipe__categories'))"""


# ============================================================== THE VIEWS
NEW_VIEWS = '''

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
    back = '%s?week=%s' % (reverse('meal_planner'),
                           monday_of(when).strftime('%Y-%m-%d'))
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
    back = '%s?week=%s' % (reverse('meal_planner'),
                           monday_of(when).strftime('%Y-%m-%d'))

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

'''

# The views go in beside MW-1's, above the shopping list - the planner's
# own endpoints end there and a different subject starts.
VIEW_AT = """# =====================================================================
# SHOPPING LIST - A DATE RANGE, NOT A PLAN
# ====================================================================="""


# =============================================================== THE URLS
URLS_WAS = """    path('meal_plans/menus/delete/', views.delete_menu, name='delete_menu'),"""
URLS_NOW = """    path('meal_plans/menus/delete/', views.delete_menu, name='delete_menu'),
    # MO-1, 19 Oct 2026 - the day speaks. Two routes, no migration:
    # both columns came with 0100 and nothing could fill them.
    path('meal_plans/note/', views.add_meal_note, name='add_meal_note'),
    path('meal_plans/leftover/', views.add_leftover, name='add_leftover'),"""


# ============================================================ THE ROW CSS
CSS_AT = """/* Empty Day */"""
CSS = """/* THE LEFTOVER ROW - MO-1, 19 Oct 2026. It is a recipe row with the
   stepper taken out, because a number that changes nothing on the
   shopping list is a control that lies. The tint says the night is
   free; the pill says why. */
.recipe-item.leftover-item {
    background: var(--alv-surface);
    border-style: dashed;
}

.leftover-source {
    color: var(--alv-ink-soft);
}

/* TWO CONTROLS UNDER A DAY, SIDE BY SIDE ON A DESKTOP and stacked on a
   phone - a row of two buttons at 390px puts six words on two lines
   inside each of them.

   AND BOTH KEEP THEIR NATURAL WIDTH. The first cut wrote
   `flex: 1 1 auto` and the before-and-after render showed what that
   does: Add Recipe stopped being the small pill it has been since
   MN-1 and became half the width of the card. This round came to add
   a control, not to restyle the one already there, and a round that
   quietly changes the look of something outside its own subject is a
   round nobody can review. The phone block below is where they
   stretch, because there they are stacked and a full-width button is
   the point. */
.day-add-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}

.day-add-row .add-recipe-btn {
    margin-top: 0;
    flex: 0 0 auto;
}

/* Empty Day */"""

PHONE_AT = """    .recipe-option img {
        flex-shrink: 0;
    }
}"""
PHONE = """    .recipe-option img {
        flex-shrink: 0;
    }

    /* MO-1, 19 Oct 2026 - TWO ADD CONTROLS STACK ON A PHONE. Side by
       side at 390px each button wraps its own label onto two lines,
       and test_tap_target reads the rendered height of both. */
    .day-add-row {
        flex-direction: column;
    }
    .day-add-row .add-recipe-btn {
        width: 100%;
    }
}"""


# ======================================================= THE NEW ALIAS
# ALIAS THE COLOUR, NEVER THE NAME - base.html's own words, beside
# .icon-manage, and the first cut of this round broke them.
#
# Leftovers was written as `icon-action-btn icon-duplicate` with a
# fa-redo glyph, on the reasoning that a leftover is the same meal
# again on another day and therefore COPY - which is right about the
# FAMILY and wrong about the CLASS. test_icon_names refused it inside a
# minute: ".icon-duplicate fa-copy(11) fa-redo(1)". A CLASS CARRIES ONE
# PICTURE, and that suite exists because .icon-edit had drifted to two
# glyphs across the system.
#
# So Leftovers gets its own name on the existing colour, which is the
# .icon-duplicate, .icon-manage and .icon-upload precedent and the rule
# base states for any new action. No new token enters base -
# test_verb_colours counts them and would say so - and COPY's own
# --alv-edit is what it points at, because a leftover is a write that
# creates something new, exactly as duplicating is.
BASE_WAS = """/* Manage: the third NAME on an existing colour, and for the same reason as"""
BASE_NOW = """/* Leftovers: the fourth NAME on an existing colour - MO-1, 19 Oct 2026.
   Putting a meal on another day as leftovers creates a new row, which is a
   write exactly as Duplicating is, so it points at --alv-edit and sits in
   the COPY family beside it. It gets its own name rather than wearing
   .icon-duplicate because A CLASS CARRIES ONE PICTURE: the first cut of
   MO-1 hung fa-redo on .icon-duplicate beside the fa-copy it already wore
   on eleven buttons, and test_icon_names refused it in under a minute.
   Alias the colour, never the name. */
.icon-leftover       { color: var(--alv-edit); border-color: var(--alv-edit); }
.icon-leftover:hover { background-color: var(--alv-edit); color: var(--alv-on-accent); }
.icon-color-leftover { color: var(--alv-edit); }

/* Manage: the third NAME on an existing colour, and for the same reason as"""


# ======================================================= THE VOCABULARY
# A CONTROL THE REGISTER CANNOT SEE IS A CONTROL NOBODY CAN CHECK.
#
# alv_rowactions.verbs_of reads the icon- class off every button in a
# .row-actions wrapper and keeps the ones it recognises:
#
#     nm = c[5:]
#     if nm in FAMILY:
#         out.append(nm)
#
# An unknown verb is SILENTLY DROPPED. So with icon-leftover unknown,
# the Leftovers control was invisible to the whole register: verbs_of
# did not return it, in_order never judged where it sits, and
# Show-RowActionDrift would not have printed it. Every row-action suite
# passed, which is exactly what makes it worth fixing - the checks were
# green because the control was not there as far as they could tell.
#
# So the verb is registered, as NV-1c registered Notify on 16 October
# for the same reason. COPY, beside duplicate, on --alv-edit: putting a
# meal on another day as leftovers creates a new row, which is a write.
RA_WAS = """    # CHANGE
    'edit': CHANGE,
    # COPY
    'duplicate': COPY,"""
RA_NOW = """    # CHANGE
    'edit': CHANGE,
    # COPY
    'duplicate': COPY,
    # MO-1, 19 Oct 2026 - LEFTOVERS. Putting a meal on another day as
    # leftovers makes a new row from an existing one, which is COPY
    # and nothing else; it sits beside duplicate and wears the same
    # colour. It has its own NAME because a class carries one picture
    # - fa-redo, against duplicate's fa-copy - which is base.html's
    # rule beside .icon-manage: alias the colour, never the name.
    #
    # REGISTERED BECAUSE verbs_of DROPS WHAT IT DOES NOT KNOW. Without
    # this line the control is invisible to in_order, to rank and to
    # Show-RowActionDrift, and every row-action suite passes by not
    # seeing it.
    'leftover': COPY,"""

RA_TONE_WAS = """TONE = {
    'view': '--alv-view',
    'edit': '--alv-edit',
    'duplicate': '--alv-edit',
    'delete': '--alv-danger',
}"""
RA_TONE_NOW = """TONE = {
    'view': '--alv-view',
    'edit': '--alv-edit',
    'duplicate': '--alv-edit',
    # MO-1, 19 Oct 2026 - the same token duplicate wears, which is the
    # point of the entry: base aliases .icon-leftover onto --alv-edit
    # rather than inventing a seventh colour, and this register is
    # where that decision is written down once.
    'leftover': '--alv-edit',
    'delete': '--alv-danger',
}"""


# ========================================================== THE TWO ROWS
# A RECIPE ROW AND A LEFTOVER ROW ARE DIFFERENT ROWS, and the branch is
# on leftover_of rather than on the recipe - a leftover HAS a recipe
# (that is how you know what the leftovers are) and would otherwise get
# a servings stepper that buys nothing.
#
# THE ROW ACTIONS KEEP THE HOUSE ORDER AND THE HOUSE VOCABULARY. LOOK,
# then COPY, then DESTROY: icon-view, icon-duplicate, icon-delete.
# Leftovers is COPY - it is the same meal again on another day - which
# alv_rowactions.FAMILY already knows and alv_rowactions.TONE already
# colours. No new verb enters the vocabulary: "COPY shares CHANGE's
# token because base's own .icon-duplicate does - the two are told
# apart by their glyph, not their colour", and fa-redo is the glyph.
ROW_WAS = """                                {# LOOK, then DESTROY - the house row-action order. #}
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
                                </div>"""
ROW_NOW = """                                {# LOOK, then COPY, then DESTROY - the house order.  #}
                                {# MO-1, 19 Oct 2026: Leftovers is COPY - the same    #}
                                {# meal again on another day - so it takes COPY's     #}
                                {# colour under its OWN name. It was written as       #}
                                {# icon-duplicate first and test_icon_names refused   #}
                                {# it: a class carries one picture, and that one       #}
                                {# already wears fa-copy on eleven buttons. Alias the #}
                                {# colour, never the name.                            #}
                                <div class="row-actions">
                                    <a href="{% url 'view_recipe' entry.recipe.recipe_id %}"
                                       class="icon-action-btn icon-view" title="View recipe"
                                       aria-label="View the recipe {{ entry.recipe.recipe_name }}"><i class="fas fa-eye"></i></a>
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="icon-action-btn icon-leftover"
                                            title="Eat it again on another day"
                                            aria-label="Add leftovers of {{ entry.recipe.recipe_name }} to another day"
                                            onclick="openLeftover({{ entry.meal_entry_id }}, '{{ entry.recipe.recipe_name|escapejs }}', '{{ entry.date|date:'Y-m-d'|escapejs }}')"><i class="fas fa-redo"></i></button>
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove {{ entry.recipe.recipe_name }} from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, '{{ entry.recipe.recipe_name|escapejs }}')"><i class="fas fa-trash"></i></button>
                                    {% else %}
                                    <span class="icon-action-btn icon-disabled" title="No permission to remove"
                                          aria-label="Remove this meal, no permission"><i class="fas fa-trash"></i></span>
                                    {% endif %}
                                </div>"""

# THE BRANCH. `{% if entry.recipe %}` becomes a three-way: a leftover
# first, because a leftover HAS a recipe and would otherwise be caught
# by the recipe arm.
BRANCH_WAS = """                        {% if entry.recipe %}
                        <div class="recipe-item" data-entry="{{ entry.meal_entry_id }}">"""
BRANCH_NOW = """                        {% if entry.recipe and entry.leftover_of %}
                        {# THE LEFTOVER ROW - MO-1, 19 Oct 2026. Tested     #}
                        {# FIRST, because a leftover has a recipe and the    #}
                        {# arm below would otherwise catch it and hand it a  #}
                        {# servings stepper that buys nothing.               #}
                        <div class="recipe-item leftover-item" data-entry="{{ entry.meal_entry_id }}">
                            {% if entry.recipe.photo_url %}
                            <img loading="lazy" decoding="async" src="{{ entry.recipe.photo_url }}"
                                 alt="" class="recipe-thumbnail">
                            {% else %}
                            <div class="recipe-thumbnail-placeholder"><i class="fas fa-redo"></i></div>
                            {% endif %}

                            <div class="recipe-info">
                                <h5>
                                    {{ entry.recipe.recipe_name }}
                                    <span class="alv-pill alv-pill-info">Leftovers</span>
                                </h5>
                                <div class="recipe-meta">
                                    {# NO STEPPER. The number would change    #}
                                    {# nothing: counts_on_shopping_list is     #}
                                    {# False for a leftover, which is the whole #}
                                    {# feature. So the row says the day it was  #}
                                    {# cooked on instead, which is the thing    #}
                                    {# somebody actually wants to know.         #}
                                    <span class="leftover-source">
                                        <i class="fas fa-utensils"></i>
                                        Cooked on {{ entry.leftover_of.date|date:"D j M" }}
                                    </span>
                                    <span class="meal-scale">nothing to buy</span>
                                </div>

                                <div class="row-actions">
                                    <a href="{% url 'view_recipe' entry.recipe.recipe_id %}"
                                       class="icon-action-btn icon-view" title="View recipe"
                                       aria-label="View the recipe {{ entry.recipe.recipe_name }}"><i class="fas fa-eye"></i></a>
                                    {% if perms.auth.can_edit_recipes %}
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove these leftovers from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, 'leftovers of {{ entry.recipe.recipe_name|escapejs }}')"><i class="fas fa-trash"></i></button>
                                    {% else %}
                                    <span class="icon-action-btn icon-disabled" title="No permission to remove"
                                          aria-label="Remove these leftovers, no permission"><i class="fas fa-trash"></i></span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% elif entry.recipe %}
                        <div class="recipe-item" data-entry="{{ entry.meal_entry_id }}">"""


# ======================================================== THE ADD CONTROLS
ADD_WAS = """                        {% if perms.auth.can_edit_recipes %}
                        <button type="button" class="add-recipe-btn"
                                onclick="openPicker('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                            <i class="fas fa-plus"></i> Add Recipe
                        </button>
                        {% else %}
                        <button type="button" class="add-recipe-btn add-recipe-btn-disabled" disabled
                                title="No permission to add recipes">
                            <i class="fas fa-plus"></i> Add Recipe
                        </button>
                        {% endif %}"""
ADD_NOW = """                        {# TWO CONTROLS NOW - MO-1, 19 Oct 2026. A day can     #}
                        {# take a recipe or a planned night that is not one.   #}
                        {# The second is what makes the note row fillable:     #}
                        {# MN-1 has drawn it since 18 October and nothing in    #}
                        {# the application could make one.                      #}
                        <div class="day-add-row">
                        {% if perms.auth.can_edit_recipes %}
                            <button type="button" class="add-recipe-btn"
                                    onclick="openPicker('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                <i class="fas fa-plus"></i> Add Recipe
                            </button>
                            <button type="button" class="add-recipe-btn"
                                    onclick="openNote('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }}')">
                                <i class="fas fa-store"></i> Add Note
                            </button>
                        {% else %}
                            <button type="button" class="add-recipe-btn add-recipe-btn-disabled" disabled
                                    title="No permission to add recipes">
                                <i class="fas fa-plus"></i> Add Recipe
                            </button>
                            <button type="button" class="add-recipe-btn add-recipe-btn-disabled" disabled
                                    title="No permission to add notes">
                                <i class="fas fa-store"></i> Add Note
                            </button>
                        {% endif %}
                        </div>"""


# ============================================================= THE DIALOGS
# They go above MW-1's copy dialog, inside the edit-tier block that
# already wraps the picker - so a reader never receives the markup.
MODAL_AT = """{# ============================================= copy this week to... #}"""

MODALS = """{# ================================================== a planned night #}
{# MO-1, 19 Oct 2026. The note row has been drawn since MN-1 and     #}
{# nothing could fill it. Three suggestions, because the point is    #}
{# speed: a night you are not cooking should take one tap and a word.#}
<div class="modal fade" id="noteModal" tabindex="-1" role="dialog"
     aria-labelledby="noteModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="noteModalLabel">
                    <i class="fas fa-store"></i> A planned night on <span id="noteDayName"></span>
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'add_meal_note' %}">
                {% csrf_token %}
                <input type="hidden" name="date" id="noteDate">
                <div class="modal-body">
                    <div class="form-group">
                        <label for="noteText"><strong>What is happening?</strong></label>
                        <input type="text" class="form-control" id="noteText"
                               name="note" maxlength="200" autocomplete="off"
                               placeholder="e.g. Eat out" required>
                        <small class="form-text text-muted">
                            A night that is planned and is not cooking. It buys nothing.
                        </small>
                    </div>
                    <div class="note-suggestions">
                        <button type="button" class="alv-pill alv-pill-info"
                                onclick="setNote('Eat out')">Eat out</button>
                        <button type="button" class="alv-pill alv-pill-info"
                                onclick="setNote('Takeaway')">Takeaway</button>
                        <button type="button" class="alv-pill alv-pill-info"
                                onclick="setNote('Out for the night')">Out for the night</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary">
                        <i class="fas fa-plus"></i> Add Note
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

{# ======================================================== leftovers #}
{# A LEFTOVER COSTS NOTHING, and the dialog says so before the button #}
{# - the same principle as MW-1's copy dialog, for the same reason:   #}
{# the free night is the whole feature and a user who does not know   #}
{# it is free will not use it.                                        #}
<div class="modal fade" id="leftoverModal" tabindex="-1" role="dialog"
     aria-labelledby="leftoverModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="leftoverModalLabel">
                    <i class="fas fa-redo"></i> Eat it again
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'add_leftover' %}">
                {% csrf_token %}
                <input type="hidden" name="meal_entry_id" id="leftoverEntryId">
                <div class="modal-body">
                    <p>
                        <strong id="leftoverName"></strong> again, on another day.
                        It costs nothing on the shopping list - you bought
                        the ingredients on the night you cooked it.
                    </p>
                    <div class="form-group">
                        <label for="leftoverDate"><strong>Which day?</strong></label>
                        <input type="date" class="form-control" id="leftoverDate"
                               name="date" required>
                        <small class="form-text text-muted">
                            On or after the day it was cooked. Leftovers cannot come first.
                        </small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary">
                        <i class="fas fa-redo"></i> Add Leftovers
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

"""

SUGG_AT = """.menu-list {"""
SUGG = """/* THE THREE SUGGESTIONS - MO-1, 19 Oct 2026. House pills, used as
   buttons, so a planned night is one tap and no typing. */
.note-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.note-suggestions .alv-pill {
    border: none;
    cursor: pointer;
}

.menu-list {"""


# ================================================================ THE JS
JS_AT = """// ------------------------------------------------------- the week moves"""

JS = """// --------------------------------------------------------- the day speaks
// MO-1, 19 Oct 2026. A planned night, and leftovers.

function openNote(dateStr, dayName) {
    document.getElementById('noteDate').value = dateStr;
    document.getElementById('noteDayName').textContent = dayName;
    // EMPTIED ON OPEN, like the picker above it. C19 is the round that
    // paid for a dialog arriving with the last answer still in it.
    document.getElementById('noteText').value = '';
    $('#noteModal').modal('show');
}

function setNote(text) {
    document.getElementById('noteText').value = text;
}

function openLeftover(entryId, name, cookedOn) {
    document.getElementById('leftoverEntryId').value = entryId;
    document.getElementById('leftoverName').textContent = name;
    var box = document.getElementById('leftoverDate');
    box.value = '';
    // THE BROWSER REFUSES IT BEFORE THE SERVER HAS TO. The view checks
    // the same thing and says so in words - a min attribute is a
    // courtesy, not a guard, and anybody can post past it.
    box.min = cookedOn;
    $('#leftoverModal').modal('show');
}

// ------------------------------------------------------- the week moves"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/urls.py'; Text = "name='meal_week_preview'"; What = 'MW-1: the route the dialog asks the count of' },"""
SENT_NOW = """    @{ File = 'pages/urls.py'; Text = "name='meal_week_preview'"; What = 'MW-1: the route the dialog asks the count of' },
    # ------------------------------------------------- MO-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="noteModal"'; What = 'MO-1: a day can take a planned night that is not a recipe' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="leftoverModal"'; What = 'MO-1: and a meal can be eaten again on another day' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'leftover-item'; What = 'MO-1: the leftover row is its own row - no stepper, because it buys nothing' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def add_leftover('; What = 'MO-1: and a leftover of a leftover points at the original' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "select_related('recipe', 'leftover_of')"; What = 'MO-1: in the ONE query the week already costs' },"""

SUITE_WAS = """    'test_meal_week.py'
)"""
SUITE_NOW = """    'test_meal_week.py',
    # MO-1, 19 Oct 2026 - release 3, push 2. The day speaks: a
    # planned night that is not a recipe, and leftovers that
    # cost nothing. Both columns shipped with 0100 and nothing
    # in the application could fill either.
    'test_meal_day.py'
)"""

TREE_WAS = """    'test_meal_week.py',
]"""
TREE_NOW = """    'test_meal_week.py',
    # MO-1, 19 Oct 2026 - release 3, push 2. The day speaks. Wide from
    # birth: it asks every page in both roots whether any of them grew
    # a second copy of the two dialogs.
    'test_meal_day.py',
]"""

RD_WAS = """    '.bak_mealweek',
]"""
RD_NOW = """    '.bak_mealweek',
    # MO-1, 19 Oct 2026 - the day speaks. Reads meal_planner.html as
    # MW-1 left it, which is the same afternoon.
    '.bak_mealday',
]"""

WD_WAS = """CONVERTED_N = 107   # MW-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 108   # MO-1, 19 Oct 2026 - this round own suite   # (was 107)   # MW-1, 19 Oct 2026 - this round own suite"""


# ====================================================== THE FOOTER PIN
# FIVE NEW DIALOGS ON ONE PAGE MOVE A TREE-WIDE COUNT.
# test_drift_root keeps a PAIR of numbers - how many
# .modal-footer wrappers a loose substring match finds and how
# many a token match finds - and the pair is the point: an
# ordinary wrapper raises both by the same one, and only a
# wrapper with a second class beside it moves them apart. This
# round adds 2 dialogs and therefore 2 ordinary footers, so
# both numbers rise by 2 and the gap of one stays exactly
# where it was.
#
# IT IS SPLIT ACROSS THIS ROUND AND MW-1 RATHER THAN MOVED ONCE
# AT THE END. The two ship in one push and revert together, but
# a tree with only one of them applied has to be green too -
# the gate runs on whatever is on disk, not on what was
# intended.
DR = 'test_drift_root.py'
DR_WAS = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 86, 85   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)'
DR_NOW = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 88, 87   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)'


# =================================================== THE FILL/INK PIN
# test_pair_contrast censuses every rule in the tree that sets
# BOTH a background and a colour, and pins the gross count. The
# .icon-leftover:hover rule this round adds to base is one of
# them - --alv-on-accent on --alv-edit, which is what
# .icon-duplicate:hover already pairs, so the suite's table of
# pairs below AA does not move and only the count does.
#
# IT IS THE COST OF ALIASING A COLOUR RATHER THAN INVENTING ONE,
# and it is the cheap half of the trade: a seventh token would
# have moved test_verb_colours as well, which asserts base holds
# exactly as many --alv- tokens as before.
PC = 'test_pair_contrast.py'
PC_WAS = 'EXPECT_PAIRS = 694   # RT-1, 18 Oct 2026 - four rules that set both a background and a colour went with the four pages MN-1 retired, and the planner that replaced them brought its own already on tokens. Measured, not deduced: every pair below AA this table names is untouched, and the gross count is what moved.   # (was 698)   # DT-1, 16 Oct 2026 - eight rules that set both a background and a colour went with the two .data-table stylesheets. Every pair below AA that this table names is untouched; the gross count is what moved.   # (was 706)   # CC-1, 15 Oct 2026 - .day-more and .day-more:hover, the chip that opens a busy day. Both are house pairs, so the AA check below is unchanged.   # (was 704)   # MH-2, 13 Oct 2026 - eight rules that set'
PC_NOW = 'EXPECT_PAIRS = 695   # MO-1, 19 Oct 2026 - one rule, .icon-leftover:hover in base, which sets --alv-on-accent on --alv-edit. It is base .icon-duplicate:hover pairing exactly - the alias this round took rather than inventing a seventh colour - so the AA table below is untouched and the gross count is what moved.   # (was 694)   # RT-1, 18 Oct 2026 - four rules that set both a background and a colour went with the four pages MN-1 retired, and the planner that replaced them brought its own already on tokens. Measured, not deduced: every pair below AA this table names is untouched, and the gross count is what moved.   # (was 698)   # DT-1, 16 Oct 2026 - eight rules that set both a background and a colour went with the two .data-table stylesheets. Every pair below AA that this table names is untouched; the gross count is what moved.   # (was 706)   # CC-1, 15 Oct 2026 - .day-more and .day-more:hover, the chip that opens a busy day. Both are house pairs, so the AA check below is unchanged.   # (was 704)   # MH-2, 13 Oct 2026 - eight rules that set'


# ============================================================== HELPERS
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
    raise SystemExit('MO-1 REFUSED: %s' % msg)


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


def before(text, anchor, block, where):
    once(text, anchor, where)
    a = fit(text, anchor)
    return text.replace(a, fit(text, block) + a)


def tag_counts(text):
    return ({'{%': text.count('{%'), '{{': text.count('{{'),
             '{#': text.count('{#')},
            {'%}': text.count('%}'), '}}': text.count('}}'),
             '#}': text.count('#}')})


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    pt = os.path.join(root, TPL)

    # ---------------------------------------------------------------- 0
    if 'def add_leftover(' in read(pv):
        print('MO-1  already applied - the day speaks.')
        return 0

    # ---------------------------------------------------------------- 1
    # MW-1 MUST BE APPLIED FIRST. This round uses monday_of and
    # day_label, which MW-1 wrote, and its dialogs go above MW-1's.
    v = read(pv)
    for fn in ('def monday_of(', 'def day_label(', 'def copy_meal_week('):
        if fn not in v:
            refuse('%s has no %s - MO-1 uses MW-1\'s helpers and its '
                   'dialogs sit above MW-1\'s. Apply MW-1 first.'
                   % (VIEW, fn[4:-1]))
    models = read(os.path.join(root, 'pages', 'models.py'))
    if 'leftover_of' not in models:
        refuse('MealEntry has no leftover_of. It shipped with 0100 in '
               'push 1; this round writes no migration.')
    if 'def counts_on_shopping_list' not in models:
        refuse('MealEntry has no counts_on_shopping_list. A leftover that '
               'is not free is not a leftover.')

    # ---------------------------------------------------------------- 2
    v = swap(v, DOC_WAS, DOC_NOW, '%s (the module docstring)' % VIEW)
    v = swap(v, SEL_WAS, SEL_NOW, '%s (the one query)' % VIEW)
    v = before(v, VIEW_AT, NEW_VIEWS.lstrip('\n'),
               '%s (above the shopping list)' % VIEW)
    out[pv] = v

    # ---------------------------------------------------------------- 3
    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URLS_WAS, URLS_NOW, '%s (the routes)' % URLS)

    # ---------------------------------------------------------------- 4
    pb = os.path.join(root, BASE)
    out[pb] = swap(read(pb), BASE_WAS, BASE_NOW, '%s (the new alias)' % BASE)

    pra = os.path.join(root, RA)
    ra_src = read(pra)
    ra_src = swap(ra_src, RA_WAS, RA_NOW, '%s (FAMILY)' % RA)
    ra_src = swap(ra_src, RA_TONE_WAS, RA_TONE_NOW, '%s (TONE)' % RA)
    out[pra] = ra_src

    t = read(pt)
    t_before = t
    t = swap(t, SUGG_AT, SUGG, '%s (the suggestion pills CSS)' % TPL)
    t = swap(t, CSS_AT, CSS, '%s (the leftover row CSS)' % TPL)
    t = swap(t, PHONE_AT, PHONE, '%s (the phone block)' % TPL)
    t = swap(t, ROW_WAS, ROW_NOW, '%s (the recipe row actions)' % TPL)
    t = swap(t, BRANCH_WAS, BRANCH_NOW, '%s (the row branch)' % TPL)
    t = swap(t, ADD_WAS, ADD_NOW, '%s (the add controls)' % TPL)
    t = before(t, MODAL_AT, MODALS, '%s (the two dialogs)' % TPL)
    t = swap(t, JS_AT, JS, '%s (the script)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 5
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pr = os.path.join(root, TREE)
    out[pr] = swap(read(pr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    ppc = os.path.join(root, PC)
    out[ppc] = swap(read(ppc), PC_WAS, PC_NOW,
                    '%s (the fill/ink pin)' % PC)

    pdr = os.path.join(root, DR)
    out[pdr] = swap(read(pdr), DR_WAS, DR_NOW,
                    '%s (the footer pin)' % DR)

    # ---------------------------------------------------------------- 6
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    o, c = out[pt].count('/*'), out[pt].count('*/')
    if o != c:
        refuse('%s: %d /* against %d */ - a CSS comment that does not '
               'close eats every rule after it' % (TPL, o, c))

    was_o, was_c = tag_counts(t_before)
    now_o, now_c = tag_counts(out[pt])
    for k in now_o:
        pair = {'{%': '%}', '{{': '}}', '{#': '#}'}[k]
        if now_o[k] - was_o[k] != now_c[pair] - was_c[pair]:
            refuse('%s: this round added %d %s and %d %s - a tag that '
                   'does not close renders as text'
                   % (TPL, now_o[k] - was_o[k], k,
                      now_c[pair] - was_c[pair], pair))

    # THE BRANCH STILL CLOSES. A three-way if written as two arms and
    # one endif is a template that renders the rest of the day inside
    # the wrong branch - and Django will not say so, it will just draw
    # the week wrong.
    for tag, n in (('{% if entry.recipe and entry.leftover_of %}', 1),
                   ('{% elif entry.recipe %}', 1)):
        if out[pt].count(tag) != n:
            refuse('%s: %d of %r, expected %d'
                   % (TPL, out[pt].count(tag), tag, n))
    # AND EVERY {% if %} THIS ROUND OPENS, IT CLOSES. The first cut of
    # this gate demanded the {% if %} count not move at all, on the
    # theory that the row branch only turns an if into an elif - and
    # refused the round, correctly: the leftover arm carries its own
    # photo_url and permission branches. The invariant is not the count,
    # it is the DELTA, and a round that opens three and closes two
    # renders the rest of the day inside the wrong branch, which Django
    # draws without complaining.
    d_if = out[pt].count('{% if ') - t_before.count('{% if ')
    d_end = out[pt].count('{% endif %}') - t_before.count('{% endif %}')
    if d_if != d_end:
        refuse('%s: this round opens %d {%% if %%} and closes %d - a '
               'branch that does not close draws the rest of the day in '
               'the wrong arm' % (TPL, d_if, d_end))

    # NO NESTED FORM, and no second copy of a dialog id.
    depth, worst = 0, 0
    for m in re.finditer(r'<form\b|</form>', out[pt]):
        depth += 1 if m.group(0) == '<form' else -1
        worst = max(worst, depth)
    if worst > 1 or depth != 0:
        refuse('%s: forms nest %d deep and close at %d' % (TPL, worst, depth))
    for mid in ('noteModal', 'leftoverModal'):
        if out[pt].count('id="%s"' % mid) != 1:
            refuse('%s: %d dialogs with id %s, expected 1'
                   % (TPL, out[pt].count('id="%s"' % mid), mid))

    # THE ROW ACTIONS KEEP THE HOUSE ORDER. LOOK, then COPY, then
    # DESTROY - alv_rowactions writes that order down once and this is
    # the round that adds a COPY to a row that had LOOK and DESTROY.
    # A CLASS CARRIES ONE PICTURE. The gate this round grew after
    # test_icon_names refused its first cut - asked of the planner and
    # of base together, because the fault was a NEW glyph on an OLD
    # class and either file alone looks fine.
    # ASKED OF THE CODE. The comment that explains why this round does
    # NOT wear icon-duplicate names the class, so the first cut of this
    # gate refused its own round over its own explanation - the fifth
    # time today, and the reason alv_tree.code_only_js exists.
    import alv_tree
    tcode = alv_tree.code_only_js(out[pt])
    if 'icon-duplicate' in tcode:
        refuse('%s wears icon-duplicate. That class carries fa-copy on '
               'eleven buttons already and a class carries ONE picture; '
               'Leftovers has its own name on the same colour. Alias the '
               'colour, never the name.' % TPL)
    if 'icon-duplicate' not in out[pt]:
        refuse('%s does not say WHY it avoids icon-duplicate. The next '
               'round to add a row action will make the same mistake; '
               'the note is the only thing that stops it.' % TPL)
    if '.icon-leftover ' not in out[pb] and '.icon-leftover{' not in out[pb]:
        refuse('%s has no .icon-leftover rule, so the control would draw '
               'with no colour at all' % BASE)
    if 'icon-leftover' not in tcode:
        refuse('%s does not use icon-leftover' % TPL)
    # AND NO NEW TOKEN. test_verb_colours counts base's --alv- tokens
    # and asserts there are exactly as many as before; an alias that
    # invented a colour would move that number.
    import re as _re
    was_tok = set(_re.findall(r'--alv-[a-z0-9-]+', read(pb)))
    now_tok = set(_re.findall(r'--alv-[a-z0-9-]+', out[pb]))
    if now_tok - was_tok:
        refuse('%s gains %s - this round aliases an existing colour and '
               'adds none' % (BASE, sorted(now_tok - was_tok)))

    # THE REGISTER, AS THIS ROUND WOULD LEAVE IT - compiled out of the
    # patched text, not imported from disk, because the point is
    # whether the EDIT is right and the module on disk is still the
    # old one at this moment.
    rns = {'__file__': pra, '__name__': 'alv_rowactions_probe'}
    try:
        exec(compile(out[pra], RA, 'exec'), rns)
    except Exception as e:
        refuse('the patched %s will not import: %s' % (RA, e))
    fam, tone = rns['FAMILY'], rns['TONE']
    if 'leftover' not in fam:
        refuse('%s still has no leftover verb, so verbs_of would drop '
               'the control and no row-action check could see it' % RA)
    if fam['leftover'] != rns['COPY']:
        refuse('%s files leftover under %r, not COPY' % (RA, fam['leftover']))
    if tone.get('leftover') != '--alv-edit':
        refuse('%s gives leftover the tone %r, not duplicate\'s --alv-edit'
               % (RA, tone.get('leftover')))
    if not (fam['view'] < fam['leftover'] < fam['delete']):
        refuse('%s no longer orders view before leftover before delete, '
               'which is the order this round writes them in' % RA)

    # AND THE REGISTER REALLY SEES THE CONTROL. The strongest form of
    # the claim: the patched module read against the patched row.
    arm = out[pt].split('{% elif entry.recipe %}')[-1].split('{% empty %}')[0]
    wrap = rns['blocks'] and None
    seen = []
    for g, blk in rns['blocks'](
            arm[arm.find('<div class="row-actions">'):]):
        seen.extend(rns['verbs_of'](blk))
    if seen[:3] != ['view', 'leftover', 'delete']:
        refuse('%s reads the recipe row as %r, expected view, leftover, '
               'delete - a verb it cannot see is a verb nobody can check'
               % (RA, seen[:3]))
    if not rns['in_order'](seen):
        refuse('%s says the recipe row is out of house order: %r'
               % (RA, seen))

    # EVERY ROUTE THE TEMPLATE REVERSES MUST EXIST.
    names = set(re.findall(r"name='([a-z_]+)'", out[pu]))
    used = (set(re.findall(r'{%\s*url\s+"([a-z_]+)"', out[pt]))
            | set(re.findall(r"{%\s*url\s+'([a-z_]+)'", out[pt])))
    for u in sorted(used):
        if u not in names:
            refuse('%s reverses %r and %s registers no such name'
                   % (TPL, u, URLS))
    for fn in ('add_meal_note', 'add_leftover'):
        if out[pv].count('def %s(' % fn) != 1:
            refuse('%s defines %s %d times, expected 1'
                   % (VIEW, fn, out[pv].count('def %s(' % fn)))

    # NO %-d, ASKED OF THE CODE. day_label's docstring explains why it
    # does not use one, and MW-1's gate refused its own round over that
    # sentence before it learned to ask python_code_only.
    code = alv_tree.python_code_only(out[pv], payloads=True)
    for bad in ('%-d', '%#d', '%-m', '%#m'):
        if bad in code:
            refuse('%s uses %s, which exists on one of the two platforms '
                   'this project runs on' % (VIEW, bad))

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('MO-1 --check')
        print('  views      : 2 new, no migration')
        print('  routes     : 2')
        print('  dialogs    : 2')
        print('  files      : %d' % len(out))
        for k in sorted(out):
            print('    %s' % os.path.relpath(k, root))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
        print('  wrote %s' % os.path.relpath(k, root))
    print('MO-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_meal_day.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
