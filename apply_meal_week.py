# -*- coding: utf-8 -*-
"""apply_meal_week.py - round MW-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE WEEK MOVES.

Demetri, 19 Oct, was asked four questions before a line was written and
took all four recommendations:

    REPEAT      "Copy this week to a week you pick." A date picker,
                every meal onto the matching weekday with its servings,
                nothing linked afterwards. This is the old Duplicate
                without a plan to duplicate.

    MENUS       "A named set of meals you stamp onto a week." Save the
                week on screen under a name; apply it to any week
                later. A Menu is a TEMPLATE - stamping it makes real
                meals you can then change.

    COLLISIONS  "Add alongside, and say so first." The dialog counts
                what is already on the target week BEFORE the button is
                pressed. Nothing is ever lost, and a day with two
                dinners on it is visibly wrong rather than silently
                repaired.

    MANAGED     Menus are managed in the Apply dialog, a trashcan per
                row, not on a screen of their own. Release 3 is about
                meal planning being ONE SCREEN and a Menus list page
                would be the second one.

ON COLLISIONS, AND WHY NOT REPLACE. Replacing was the only one of the
three that can destroy something kept - and that is exactly what C13
did, when changing a plan's dates dropped the meals that fell outside
the new range. Skipping loses nothing either, but leaves a week that is
neither the copy nor what was there, which is harder to reason about
afterwards.

NO MIGRATION. Menu and MenuItem shipped in 0100 with push 1, and MN-1
stored them as DAY INDEXES 0 to 6 rather than dates precisely so that a
Menu could be stamped onto any week later. Its docstring says so. This
round is three dialogs and five views against tables that already
exist.

TWO THINGS THIS ROUND GETS RIGHT THAT IT WOULD HAVE BEEN EASY TO LEAVE
FOR THE ROUND AFTER IT:

    A LEFTOVER FOLLOWS ITS PARENT. leftover_of points at the meal a
    leftover came from. Copied flat it would point into the week you
    copied FROM, and the shopping list would charge the new week for a
    meal in the old one. The parents are copied first and the map
    re-points the copies; a leftover whose parent is not in the copy is
    dropped, because a leftover of nothing is a row that buys nothing
    and says nothing. MO-1 is what puts leftovers on the screen - the
    column is here from MN-1, so this round handles it rather than
    leaving a trap.

    A MENU DOES NOT SAVE LEFTOVERS. MenuItem has no leftover_of and
    that is right: a leftover is a consequence of a particular week,
    not something you plan in advance.

AND A SECOND SUBJECT, WHICH DEMETRI CHOSE TO PUT HERE. While writing
the three dialogs I found that .recipe-option - the rows of the
Add-a-Meal picker - HAS NO CSS RULE ANYWHERE. Not on this page, not in
base, and not in any of the twenty-seven backups of this template or
its ancestor. Clicking a recipe adds a `.selected` class that paints
nothing, so the only confirmation you get that the click landed is the
Add button un-greying.

He was offered it three ways - a small round of its own in this push, a
fold into this round, or push 3 - and chose the fold. So this round
carries two subjects and that is recorded here rather than disguised:
one gate, two things, and if it refuses, read which section refused.
The picker work is three rules and three REMOVALS - #recipeList,
.recipe-option > div and .recipe-option > div > div:first-child were
all written for markup that no longer exists, the first for a list id
MN-1 renamed to pickerList and the other two for a two-level nesting
the current row does not have. A rule for a selector nothing matches is
a rule nobody can check.

Idempotent. Every file backed up to .bak_mealweek. Python is compiled
and the template's braces and Django tags are counted before anything
is written.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealweek'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_meal_week.py'
PATCHER = 'apply_meal_week.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
# The two suites that count the pages wearing base's More menu. Both are
# present-tense readings and this round hangs a menu on the planner.
MM = 'test_more_menu.py'
LM = 'test_last_menus.py'
MARK = 'MW-1, 19 Oct 2026'
CHECK = False

# ============================================================ THE IMPORT
IMP_WAS = """from pages.models import (
    CustomProtein,
    HouseholdMember,
    MealEntry,
    Recipe,"""
IMP_NOW = """from pages.models import (
    CustomProtein,
    HouseholdMember,
    MealEntry,
    Menu,
    MenuItem,
    Recipe,"""

# ========================================================= THE DOCSTRING
DOC_WAS = """- send_meal_plan_shopping_list    : Email a shopping list (POST).
                                    Edit-tier."""
DOC_NOW = """- send_meal_plan_shopping_list    : Email a shopping list (POST).
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
                                    MW-1."""

NEW_VIEWS = '''

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

    back = '%s?week=%s' % (reverse('meal_planner'),
                           dst.strftime('%Y-%m-%d'))
    if src == dst:
        messages.error(request, 'A week cannot be copied onto itself.')
        return redirect(back)

    rows = list(week_entries(src))
    if not rows:
        messages.error(request, 'There is nothing on %s to copy.'
                       % week_label(src))
        return redirect('%s?week=%s' % (reverse('meal_planner'),
                                        src.strftime('%Y-%m-%d')))

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
    back = '%s?week=%s' % (reverse('meal_planner'),
                           week.strftime('%Y-%m-%d'))

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
    back = '%s?week=%s' % (reverse('meal_planner'),
                           week.strftime('%Y-%m-%d'))
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
    back = ('%s?week=%s' % (reverse('meal_planner'),
                            monday_of(week).strftime('%Y-%m-%d'))
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

'''


# ============================================================== THE URLS
URLS_WAS = """    path('meal_plans/servings/', views.set_meal_servings, name='set_meal_servings'),"""
URLS_NOW = """    path('meal_plans/servings/', views.set_meal_servings, name='set_meal_servings'),
    # MW-1, 19 Oct 2026 - the week moves. Five routes, no migration:
    # Menu and MenuItem arrived with 0100 in push 1.
    path('meal_plans/week_preview/', views.meal_week_preview, name='meal_week_preview'),
    path('meal_plans/copy_week/', views.copy_meal_week, name='copy_meal_week'),
    path('meal_plans/menus/save/', views.save_menu, name='save_menu'),
    path('meal_plans/menus/apply/', views.apply_menu, name='apply_menu'),
    path('meal_plans/menus/delete/', views.delete_menu, name='delete_menu'),"""

# THE VIEWS GO IN ABOVE THE SHOPPING LIST, which is where the planner's
# own endpoints end and a different subject starts.
VIEW_AT = """# =====================================================================
# SHOPPING LIST - A DATE RANGE, NOT A PLAN
# ====================================================================="""

# ========================================================== THE CONTEXT
# The Apply dialog lists every Menu, so the planner has to hand them to
# the template. prefetch, because the dialog prints how many meals each
# one holds and a count per row is N+1 queries otherwise - which is the
# fault E29 spent a round removing from four screens.
CTX_WAS = """        'all_recipes': Recipe.objects.all().order_by('recipe_name'),
    }
    return render(request, 'meal_planner.html', context)"""
CTX_NOW = """        'all_recipes': Recipe.objects.all().order_by('recipe_name'),
        # MW-1, 19 Oct 2026 - the Apply dialog lists these. annotate
        # rather than a count per row: E29 took that fault off four
        # screens and this round is not putting it back on one.
        'menus': Menu.objects.annotate(
            item_count=Count('items')).order_by('name'),
    }
    return render(request, 'meal_planner.html', context)"""

# ======================================================== THE ACTION BAR
# A MORE MENU, because the bar is full. Shopping List, Help and Back is
# three and the house keeps Back last and uncoloured; three more
# controls beside them wraps the bar on a phone, which is the exact
# thing test_secondary_visible and test_tap_target measure. 31 pages
# already wear base's More menu and base already binds it - this round
# writes no JavaScript for it and no CSS.
BAR_WAS = """        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#meal_plansHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>"""
BAR_NOW = """        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#meal_plansHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>
        {% if perms.auth.can_edit_recipes %}
        {# MW-1, 19 Oct 2026 - THE WEEK MOVES, and the three controls   #}
        {# that move it live here rather than in the bar. Shopping      #}
        {# List, Help and Back fill a phone already; base owns this     #}
        {# menu, its CSS and the binder, so this page writes neither.   #}
        <div class="action-more-wrapper" data-menu>
            <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle
                    aria-label="More actions" aria-expanded="false" aria-haspopup="true">
                <i class="fas fa-ellipsis-v"></i>
            </button>
            <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
                {# data-toggle OPENS IT AND onclick EMPTIES IT FIRST.    #}
                {# base's binder closes this panel on any item click and #}
                {# says so, so the modal is Bootstrap's to open; the     #}
                {# inline reset is the page's own openPicker pattern and #}
                {# needs no reasoning about when jQuery is defined,      #}
                {# which a top-level $(document).on would. C19 is why    #}
                {# a dialog is emptied on open and not on close.         #}
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetCopyWeek()"
                        data-toggle="modal" data-target="#copyWeekModal">
                    <i class="fas fa-copy"></i> Copy this week to...
                </button>
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetSaveMenu()"
                        data-toggle="modal" data-target="#saveMenuModal">
                    <i class="fas fa-bookmark"></i> Save this week as a Menu
                </button>
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetApplyMenu()"
                        data-toggle="modal" data-target="#applyMenuModal">
                    <i class="fas fa-list-ul"></i> Apply a Menu...
                </button>
            </div>
        </div>
        {% endif %}"""


# ============================================================ THE MODALS
# THREE DIALOGS, AND THEY GO INSIDE THE EDIT-TIER BLOCK that already
# wraps the picker and the remove form - lines that begin
# {% if perms.auth.can_edit_recipes %} above the picker and end
# {% endif %} below removeForm. Inserting above the remove form's own
# comment puts them inside it, so this round writes no second guard: a
# reader who can see the planner but not edit it never receives the
# markup at all, which is the same shape MN-1 left.
#
# BOOTSTRAP 4.1.3. data-toggle / data-target / data-dismiss, and
# $('#id').modal('show') where a dialog is opened from script. A4 spent
# a release on `new bootstrap.Modal(...)` on this very page.
MODAL_AT = """{# THE REMOVE FORM. One form, reused - a form per meal would be one #}"""

MODALS = """{# ============================================= copy this week to... #}
{# MW-1, 19 Oct 2026. "Copy this week to a week you pick" - the old    #}
{# Duplicate, without a plan to duplicate it from.                    #}
<div class="modal fade" id="copyWeekModal" tabindex="-1" role="dialog"
     aria-labelledby="copyWeekLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="copyWeekLabel">
                    <i class="fas fa-copy"></i> Copy this week to&hellip;
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'copy_meal_week' %}">
                {% csrf_token %}
                <input type="hidden" name="from_week" value="{{ week_start|date:'Y-m-d' }}">
                <div class="modal-body">
                    <p>
                        Every meal on <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>
                        goes onto the matching weekday of the week you pick, with its servings.
                    </p>
                    <div class="form-group">
                        <label for="copyWeekTo"><strong>Copy to the week of</strong></label>
                        <input type="date" class="form-control" id="copyWeekTo"
                               name="to_week" onchange="copyPreview()" required>
                        <small class="form-text text-muted">
                            Any day in the week you want. The whole week it belongs to is what receives the meals.
                        </small>
                    </div>
                    {# SAY SO FIRST. The decision was "add alongside, AND  #}
                    {# say so first", and a dialog that cannot count what  #}
                    {# the target week already holds is the same copy with #}
                    {# a quieter conscience. So it asks before the button  #}
                    {# can be pressed - which is also why the button       #}
                    {# starts disabled and the answer is what enables it.  #}
                    <div id="copyWeekNote" aria-live="polite"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary" id="copyWeekGo" disabled>
                        <i class="fas fa-copy"></i> Copy the Week
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

{# ========================================= save this week as a menu #}
{# A MENU IS A TEMPLATE. It holds day indexes 0 to 6, not dates, which #}
{# is why MN-1 built MenuItem that way: a week saved in October can be #}
{# stamped onto a week in December. Leftovers are not saved - a        #}
{# leftover is a consequence of a particular week, not a plan.         #}
<div class="modal fade" id="saveMenuModal" tabindex="-1" role="dialog"
     aria-labelledby="saveMenuLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="saveMenuLabel">
                    <i class="fas fa-bookmark"></i> Save this week as a Menu
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'save_menu' %}">
                {% csrf_token %}
                <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                <div class="modal-body">
                    <p>
                        The meals on <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>
                        are kept under a name, by weekday. Apply it to any week later.
                    </p>
                    <div class="form-group">
                        <label for="saveMenuName"><strong>Name</strong></label>
                        <input type="text" class="form-control" id="saveMenuName"
                               name="name" maxlength="100" autocomplete="off"
                               placeholder="e.g. Easy Winter Week" required>
                        <small class="form-text text-muted">
                            This is how you will recognise it in the Apply list.
                        </small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary">
                        <i class="fas fa-bookmark"></i> Save the Menu
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

{# ================================================== apply a menu... #}
{# MANAGED HERE, NOT ON A PAGE OF ITS OWN - the fourth decision, and   #}
{# the reason is Release 3's whole subject: meal planning is ONE       #}
{# SCREEN. A Menus list page would be the second one, reached from     #}
{# here, holding one verb. So the trashcan lives per row in the        #}
{# dialog that already has to list them.                               #}
<div class="modal fade" id="applyMenuModal" tabindex="-1" role="dialog"
     aria-labelledby="applyMenuLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="applyMenuLabel">
                    <i class="fas fa-list-ul"></i> Apply a Menu
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'apply_menu' %}">
                {% csrf_token %}
                <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                <input type="hidden" name="menu_id" id="applyMenuId">
                <div class="modal-body">
                    {% if menus %}
                    <p>
                        The menu you pick is added to
                        <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>,
                        alongside whatever is already there.
                    </p>
                    <div class="menu-list">
                        {% for menu in menus %}
                        <div class="menu-option" data-menu-id="{{ menu.menu_id }}"
                             onclick="pickMenu(this)">
                            <div class="menu-option-name">
                                <strong>{{ menu.name }}</strong><br>
                                <small class="text-muted">
                                    {{ menu.item_count }} meal{{ menu.item_count|pluralize }}
                                </small>
                            </div>
                            <div class="row-actions">
                                <button type="button" class="icon-action-btn icon-delete"
                                        title="Delete this menu"
                                        aria-label="Delete the menu {{ menu.name }}"
                                        onclick="deleteMenu(event, {{ menu.menu_id }}, '{{ menu.name|escapejs }}')"><i class="fas fa-trash"></i></button>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    {# THE EMPTY STATE SAYS WHERE MENUS COME FROM. There   #}
                    {# is no other place to make one, so a dialog that     #}
                    {# only said "none yet" would be a dead end.           #}
                    <div class="empty-day">
                        <i class="fas fa-list-ul"></i>
                        <p>No menus yet.</p>
                        <p class="text-muted">
                            Put some meals on a week, then choose
                            <strong>Save this week as a Menu</strong>.
                        </p>
                    </div>
                    {% endif %}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    {% if menus %}
                    <button type="submit" class="btn action-primary" id="applyMenuGo" disabled>
                        <i class="fas fa-check"></i> Add to This Week
                    </button>
                    {% endif %}
                </div>
            </form>
        </div>
    </div>
</div>

{# THE DELETE FORM. Outside the Apply form, because a form inside a    #}
{# form is not a thing HTML has - the trashcan is a plain button that  #}
{# fills this one and submits it, the same shape removeForm below has  #}
{# worn since MN-1.                                                   #}
<form method="POST" action="{% url 'delete_menu' %}" id="deleteMenuForm" hidden>
    {% csrf_token %}
    <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
    <input type="hidden" name="menu_id" id="deleteMenuId">
</form>

"""

# ============================================================== THE CSS
# TWO RULES AND A SELECTED STATE, in the page's own style block, using
# the page's own tokens - var(--alv-line), --alv-paper, --alv-accent,
# --alv-accent-soft, --alv-accent-ring, --alv-radius-sm, all of which
# are already spent on this page. No new colour literal enters the
# tree; test_palette and test_radius_token both read this file.
#
# A ROW IS A ROW, which is why .menu-option is flex with the name on
# the left and base's .row-actions on the right - the same shape the
# meal rows above it wear. And the 44px floor under 768px comes from
# base sizing .icon-action-btn, not from here: test_tap_target reads
# the rendered button, and a page rule could only disagree with base.
CSS_AT = """/* Empty Day */"""

CSS = """/* THE MENU LIST - MW-1, 19 Oct 2026. The Apply dialog's rows, and
   the only new CSS this round writes. The More menu that opens the
   three dialogs is base's, CSS and binder both. */
.menu-list {
    max-height: 320px;
    overflow-y: auto;
}

.menu-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    cursor: pointer;
    transition: all 0.2s;
}

.menu-option:last-child {
    margin-bottom: 0;
}

.menu-option:hover {
    border-color: var(--alv-accent);
}

/* THE SELECTED ROW HAS TO LOOK SELECTED. Two signals, not one: the
   ring and the tint. A border colour alone is the fault MC-2 found
   five times over on this screen's ancestor - a state you can only
   see if you already know where to look. */
.menu-option.selected {
    border-color: var(--alv-accent);
    background: var(--alv-accent-soft);
    box-shadow: 0 0 0 2px var(--alv-accent-ring);
}

.menu-option-name {
    min-width: 0;
    overflow-wrap: break-word;
}

/* THE PICKER ROW IS A ROW - MW-1, 19 Oct 2026, and it is the second
   subject in this round, which the docstring says and says why.

   .recipe-option had NO RULE. Not here, not in base, and not in any
   backup of this template or of the calendar it descends from. The
   markup has an image and a block of text side by side and nothing
   was laying them out; pickRecipe() has added a .selected class since
   the picker was written and nothing was drawing it. The only signal
   that a click had landed was the Add button un-greying, at the
   bottom of a dialog, away from the thing that was clicked.

   Same two signals as the menu rows above, for the same reason. */

/* AND THE LIST GETS THE CAP ITS OWN OVERRIDE WAS WRITTEN TO UNDO. The
   under-768px block carried `#recipeList { max-height: none
   !important; }` - an override of a desktop cap that is not in this
   file and is in no backup of it. Bootstrap 4.1.3 has no
   .modal-dialog-scrollable, so a tree with two hundred recipes makes a
   dialog taller than the screen with its Add button below the fold.
   The cap is restored at the size .menu-list above uses, and the
   phone override is kept - it now has something to override. */
#pickerList {
    max-height: 320px;
    overflow-y: auto;
}

.recipe-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    cursor: pointer;
    transition: all 0.2s;
}

.recipe-option:last-child {
    margin-bottom: 0;
}

.recipe-option:hover {
    border-color: var(--alv-accent);
}

.recipe-option.selected {
    border-color: var(--alv-accent);
    background: var(--alv-accent-soft);
    box-shadow: 0 0 0 2px var(--alv-accent-ring);
}

/* Empty Day */"""

# =============================================================== THE JS
# IT GOES INSIDE THE PAGE'S OWN EDIT-TIER BLOCK, below removeMeal and
# above the {% endif %} that closes it - so a reader never receives a
# line of it.
#
# NO TOP-LEVEL jQUERY. base.html loads jquery-3.6.0 AFTER the content
# block, which is why the script's own header says "Every function here
# runs on interaction, so $ is defined by then." A $(document).on at the
# top of this block would be a ReferenceError that aborts the rest of
# it. Every function below is called from an onclick or from fetch.
JS_AT = """    document.getElementById('removeEntryId').value = entryId;
    document.getElementById('removeForm').submit();
}
{% endif %}"""

JS = """    document.getElementById('removeEntryId').value = entryId;
    document.getElementById('removeForm').submit();
}

// ------------------------------------------------------- the week moves
// MW-1, 19 Oct 2026. Three dialogs: copy a week, save a week as a
// Menu, apply a Menu. Each is emptied as it opens - C19's lesson, and
// the picker above does the same thing for the same reason.

function resetCopyWeek() {
    document.getElementById('copyWeekTo').value = '';
    document.getElementById('copyWeekNote').innerHTML = '';
    document.getElementById('copyWeekGo').disabled = true;
}

function resetSaveMenu() {
    document.getElementById('saveMenuName').value = '';
}

function resetApplyMenu() {
    document.querySelectorAll('.menu-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    document.getElementById('applyMenuId').value = '';
    // THE BUTTON IS NOT THERE WHEN THERE ARE NO MENUS - the template
    // leaves it out rather than disabling it, so this asks.
    var go = document.getElementById('applyMenuGo');
    if (go) { go.disabled = true; }
}

// SAY SO FIRST. "Add alongside, and say so first" was the decision, and
// this is the second half of it: before Copy can be pressed, the dialog
// asks the server what the target week already holds and says it. The
// button is enabled by the ANSWER, not by the date being typed - a
// Copy that went ahead while the count was still in flight would be
// the quieter conscience the decision was taken to avoid.
function copyPreview() {
    var box = document.getElementById('copyWeekTo');
    var note = document.getElementById('copyWeekNote');
    var go = document.getElementById('copyWeekGo');
    go.disabled = true;
    if (!box.value) { note.innerHTML = ''; return; }

    note.innerHTML = '<p class="text-muted"><i class="fas fa-spinner fa-spin"></i> '
        + 'Checking that week...</p>';

    fetch('{% url "meal_week_preview" %}?week=' + encodeURIComponent(box.value), {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
        if (!d.success) {
            // NOT alert() - SL-4. A browser dialog blocks every event
            // after it, and this dialog has a place to say things.
            note.innerHTML = '<div class="alert alert-warning">' + d.error + '</div>';
            return;
        }
        if (d.week === '{{ week_start|date:"Y-m-d"|escapejs }}') {
            note.innerHTML = '<div class="alert alert-warning">'
                + 'That is this week. A week cannot be copied onto itself.</div>';
            return;
        }
        if (d.meals === 0) {
            note.innerHTML = '<div class="alert alert-info">'
                + '<strong>' + d.label + '</strong> is empty. '
                + 'The copy lands on a clear week.</div>';
        } else {
            // THE COUNT, IN WORDS, BEFORE THE BUTTON. Nothing is
            // replaced and nothing is skipped: a day that had a dinner
            // and gains another has two, visibly, which is a thing you
            // can fix. A silent repair is not.
            note.innerHTML = '<div class="alert alert-warning">'
                + '<strong>' + d.label + '</strong> already has '
                + d.meals + ' meal' + (d.meals === 1 ? '' : 's')
                + ' on ' + d.days_with_meals + ' day'
                + (d.days_with_meals === 1 ? '' : 's') + '. '
                + 'The copy is <strong>added alongside</strong> them - '
                + 'nothing is removed or replaced.</div>';
        }
        go.disabled = false;
    })
    .catch(function () {
        note.innerHTML = '<div class="alert alert-warning">That week could not '
            + 'be checked. Check your connection and try again.</div>';
    });
}

function pickMenu(el) {
    document.querySelectorAll('.menu-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    el.classList.add('selected');
    document.getElementById('applyMenuId').value = el.dataset.menuId;
    document.getElementById('applyMenuGo').disabled = false;
}

// THE TRASHCAN IS INSIDE A CLICKABLE ROW, so it stops the click going
// up - without this, deleting a menu would also select it, and the
// Apply button would be left armed with an id that no longer exists.
function deleteMenu(ev, menuId, name) {
    ev.stopPropagation();
    if (!confirm('Delete the menu "' + name + '"? The meals it has already '
                 + 'put on your weeks stay where they are.')) { return; }
    document.getElementById('deleteMenuId').value = menuId;
    document.getElementById('deleteMenuForm').submit();
}
{% endif %}"""

# ====================================================== THE SENTINEL ROWS
# WHAT A DEPLOY MUST BE ABLE TO SEE. The pre-flight reads these off the
# tree; a round that ships markup and registers nothing is a round whose
# absence is invisible next week.
SENT_WAS = """    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Adding a Meal"'; What = 'MH-2: and the guide describes adding a meal to a day, not building a plan' },"""
SENT_NOW = """    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Adding a Meal"'; What = 'MH-2: and the guide describes adding a meal to a day, not building a plan' },
    # ------------------------------------------------- MW-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="copyWeekModal"'; What = 'MW-1: a week can be copied onto a week you pick' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="saveMenuModal"'; What = 'MW-1: and saved under a name, by weekday' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="applyMenuModal"'; What = 'MW-1: and a saved Menu stamped onto any week' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'added alongside'; What = 'MW-1: and the dialog counts what is there BEFORE the button - add alongside, and say so first' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def copy_week_rows('; What = 'MW-1: one function copies a week, parents before leftovers' },
    @{ File = 'pages/urls.py'; Text = "name='meal_week_preview'"; What = 'MW-1: the route the dialog asks the count of' },"""

# =========================================================== THE SUITES
SUITE_WAS = """    'test_retired.py'
)"""
SUITE_NOW = """    'test_retired.py',
    # MW-1, 19 Oct 2026 - release 3, push 2. The week moves: copy
    # a week onto a week you pick, save one as a Menu, stamp a
    # Menu onto any week. No migration - Menu and MenuItem came
    # with 0100 in push 1, holding DAY INDEXES and not dates
    # exactly so that this round could exist.
    'test_meal_week.py'
)"""

TREE_WAS = """    'test_retired.py',
]"""
TREE_NOW = """    'test_retired.py',
    # MW-1, 19 Oct 2026 - release 3, push 2. The week moves. Wide from
    # birth: section 7 asks every page in both template roots whether
    # any of them grew a second copy of these three dialogs.
    'test_meal_week.py',
]"""

RD_WAS = """    '.bak_mealguide',
]"""
RD_NOW = """    '.bak_mealguide',
    # MW-1, 19 Oct 2026 - release 3, push 2. The week moves. The
    # register's own subject: this round reads meal_planner.html as
    # MN-1 left it, and MH-2 has written to it since.
    '.bak_mealweek',
]"""

# The list is one physical line with its history appended as comments -
# every round that has moved it has added one. The anchor is the value
# and the newest comment, which is RT-1's.
WD_WAS = """CONVERTED_N = 106   # RT-1, 18 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 107   # MW-1, 19 Oct 2026 - this round own suite   # (was 106)   # RT-1, 18 Oct 2026 - this round own suite"""

# ======================================== THE TWO PAGE COUNTS, REPAIRED
# NOT A RE-PIN. The first cut of this round swapped 31 for 32 in both
# suites and both of them FAILED - test_more_menu with three checks
# down and test_last_menus with four - and the reason is worth more
# than the number.
#
# BOTH SUITES READ A PRESENT-TENSE CENSUS THROUGH A HISTORICAL READ.
# Each builds its list of pages off TODAY's disk and then asks each one
# a question through `now(p)`, which is alv_rounds.as_left_by - the
# page as that suite's own round left it. For the 31 pages that already
# existed when H8 and H10 ran, those two readings are the same text. On
# a page that joined the census LATER they are not: the planner reads
# 41,017 characters as .bak_moremenu left it and 60,973 today, and the
# menu this round hangs on it is in the second number only. So the
# census counted 32 and then went looking for H8's work on a page H8
# never saw.
#
# IT IS RT-1'S LESSON, ARRIVING FROM THE OTHER SIDE. RT-1 was told that
# a census of what a round DID cannot be read off today's disk. This is
# the inverse and the same sentence: a census of what the tree HAS
# cannot be read out of the past. Historical and present-tense reads
# are different questions, and the call site is the only place that
# knows which one is being asked.
#
# SO EACH SUITE IS GIVEN THE READ ITS OWN WORDS ALREADY CLAIM.
# test_last_menus' section 1 says "the pages that carry a More menu
# TODAY" and now reads today. test_more_menu's `mine` says "this
# round's" and is now taken from this round's BACKUPS instead of being
# subtracted from today's census - which is what made a later round
# able to join it at all.
MM_WAS = """mine = [(n, p) for n, p in pages if n not in DEFERRED and n not in ALREADY]

# ==========================================================================
head('1. THE CENSUS')
# ==========================================================================
# 31 AND 26 SINCE RT-1, 18 Oct 2026. Both are readings of the
# tree as it stands, not of what this round did - the round
# converted 27 pages and MN-1 has since retired one of them,
# view_meal_plan.html. Nobody should read 26 as the size of
# this round; section 3 reads that from the backups.
ok(len(pages) == 31, '31 pages carry the More menu in markup', len(pages))
ok(len(mine) == 26, '  26 of them are this round\\'s', len(mine))"""

MM_NOW = """# MW-1, 19 Oct 2026 - THIS ROUND'S PAGES COME FROM THIS ROUND'S
# BACKUPS. `mine` used to be today's census minus two exemption lists,
# and that worked only while no later round joined the census. MW-1 is
# that round: it hangs a More menu on meal_planner.html, which H8 never
# saw, and the planner arrived in `mine` - so sections 2, 3 and 7 went
# looking for H8's work on it and three checks failed. A set of pages a
# round TOUCHED is a fact about the past and alv_tree.touched_by reads
# it from the only place it is still written down.
TOUCHED = set(alv_tree.rel(q).replace(os.sep, '/')
              for q in alv_tree.touched_by(SUFFIX) if q.endswith('.html'))
TOUCHED.discard('base.html')
# The one page of the twenty-seven the tree has since retired. It is
# counted and named rather than quietly dropped, which is the whole
# point of RT-1's register: an exemption for a page nobody can reach is
# a line nobody can check.
GONE = sorted(n for n in TOUCHED if alv_tree.retired(n))
mine = [(n, p) for n, p in pages if n in TOUCHED]
# Pages carrying a menu that are neither this round's, nor deferred,
# nor already bound - which is to say, pages a LATER round put on the
# binder. A round that hangs a More menu on a page adds it here.
LATER = sorted(set(n for n, _ in pages)
               - TOUCHED - set(DEFERRED) - set(ALREADY))

# ==========================================================================
head('1. THE CENSUS')
# ==========================================================================
# 32 TODAY, 27 FROM THE BACKUPS, 26 OF THEM STILL IN THE TREE.
# Three numbers now, because they are three different questions
# and reading one of them as another is what broke this section
# on 19 October. 32 is what the tree HAS; 27 is what H8 DID and
# cannot change again; 26 is the part of H8's work still on a
# page the tree serves. Section 3 measures the round from the
# backups and nobody should read any of these as its size.
ok(len(pages) == 32, '32 pages carry the More menu in markup', len(pages))
ok(len(TOUCHED) == 27, '  27 of them are this round\\'s, from its backups',
   len(TOUCHED))
ok(GONE == ['view_meal_plan.html'],
   '  and one of the 27 has been retired since - %s'
   % (GONE[0] if GONE else 'none'), GONE)
ok(len(mine) == 26, '  so 26 of this round\\'s pages are still in the tree',
   len(mine))
ok(LATER == ['meal_planner.html'],
   '  and 1 page was put on the binder by a LATER round - %s, MW-1, '
   '19 Oct 2026' % (LATER[0] if LATER else 'none'), LATER)"""

LM_WAS = """# 31 SINCE RT-1, 18 Oct 2026. This counts the pages that carry
# a More menu TODAY. view_meal_plan.html carried one and MN-1
# retired it; the planner that replaced it has no More menu.
# H8 still bound 32 of them, and that is section 2's claim,
# read from the backups.
ok(len(pages) == 31, '31 pages carry a More menu', len(pages))
off = [rel for rel, p in pages
       if not all(a in markup(now(p)) for a in ATTRS)]
ok(not off, '  and every one of them is on base\\'s binder', off)
holding = [rel for rel, p in pages if 'actionMoreBtn' in js_of(now(p))]
ok(not holding, '  NOT ONE still writes its own handler', holding)
painting = [rel for rel, p in pages if paints(now(p))]
ok(painting == [PAINTER],
   '  and exactly one still paints it - %s, named and measured in H9'
   % PAINTER.replace('.html', ''), painting)
ok(all(re.search(r'id="actionMoreMenu"[^>]*\\bhidden\\b', markup(now(p)))
       for _, p in pages),
   '  every panel starts closed in its own markup')"""

LM_NOW = """# 32 SINCE MW-1, 19 Oct 2026, AND THE HEADING ABOVE IS TRUE
# AGAIN - but the number is the small half of what changed here.
#
# THIS SECTION SAYS "TODAY" AND USED TO READ THE PAST. Every
# check below went through now(), which is as_left_by: the page
# as H10 left it. For the 31 pages that existed when H10 ran
# that is the same text as today's. MW-1 hung a More menu on
# meal_planner.html - a page H10 never saw - and the planner
# joined this census while its historical read, 41,017
# characters against today's 60,973, has no menu in it at all.
# Four checks failed, correctly: they were asked about a page
# and answered about a different version of it.
#
# So today() is what a present-tense census reads with, and
# now() stays where it belongs - sections 2 and 3, which ask
# what H10 DID. Historical and present-tense reads are
# different questions and the call site is the only place that
# knows which one is being asked. [RT-1, 18 Oct 2026]


def today(p):
    \"\"\"The page's text as the tree holds it NOW.

    Not now() - that is the page as this round left it, which is a
    question about the past and the wrong one to ask of a census
    built from today's disk.
    \"\"\"
    return read(p)


ok(len(pages) == 32, '32 pages carry a More menu', len(pages))
off = [rel for rel, p in pages
       if not all(a in markup(today(p)) for a in ATTRS)]
ok(not off, '  and every one of them is on base\\'s binder', off)
holding = [rel for rel, p in pages if 'actionMoreBtn' in js_of(today(p))]
ok(not holding, '  NOT ONE still writes its own handler', holding)
# AND THE ONE DEBT H9 COULD NOT TAKE HAS BEEN PAID - which
# this section could not see, because it was reading H10's
# tree. property_management_dashboard.html kept SEVEN rules
# naming the component when H10 ran; that measurement is a
# fact about the past and is asserted as one, from the
# backups, on the line below. DB-5 took those seven out on
# 12 OCTOBER, together with the ten .dashboard-side-actions
# rules beside them - and for the seven days since, this
# line has said one page still paints it and passed, because
# a claim asked of the past cannot notice that the present
# has moved on. That is the whole lesson of this round's
# repair, found by accident while re-pinning a count.
ok(len(paints(now(alv_tree.last_join(PAINTER)))) == 7,
   '  %s painted it with 7 rules when H10 ran - from the backups'
   % PAINTER.replace('.html', ''),
   len(paints(now(alv_tree.last_join(PAINTER)))))
painting = [rel for rel, p in pages if paints(today(p))]
ok(not painting,
   '  and TODAY not one page paints it - DB-5 took the last seven '
   'on 12 Oct 2026', painting)
ok(all(re.search(r'id="actionMoreMenu"[^>]*\\bhidden\\b', markup(today(p)))
       for _, p in pages),
   '  every panel starts closed in its own markup')"""


# ================================================= THE THREE DEAD RULES
# A RULE FOR A SELECTOR NOTHING MATCHES IS A RULE NOBODY CAN CHECK, and
# all three of these are inside the under-768px block, which is where a
# phone reads them.
#
#   #recipeList            the picker's list was renamed to pickerList
#                          by MN-1, so this one has had nothing to say
#                          since 18 October.
#
#   .recipe-option > div             both were written for a row shaped
#   .recipe-option > div > div:...   .recipe-option > div > img + div,
#                                    a two-level nesting the markup
#                                    does not have: the image is a
#                                    direct child of .recipe-option
#                                    now. The second one has never
#                                    matched anything at all.
#
# .recipe-option img is KEPT - it matches, and flex-shrink: 0 on the
# thumbnail is what stops a long recipe name squeezing the photo.
DEAD_WAS = """    /* Add Recipe Modal - recipe list inside */
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
}"""
DEAD_NOW = """    /* THE PICKER LIST ON A PHONE - MW-1, 19 Oct 2026. Three rules
       left here when this round gave .recipe-option the layout it
       never had: #recipeList (MN-1 renamed that list to pickerList),
       .recipe-option > div and .recipe-option > div > div:first-child
       (both written for a two-level nesting the row does not have -
       the thumbnail is a direct child). The one below matches, and
       is what stops a long recipe name squeezing the photo. */
    #pickerList {
        max-height: none !important;
    }
    .recipe-option img {
        flex-shrink: 0;
    }
}"""


# ====================================================== THE FOOTER PIN
# FIVE NEW DIALOGS ON ONE PAGE MOVE A TREE-WIDE COUNT.
# test_drift_root keeps a PAIR of numbers - how many
# .modal-footer wrappers a loose substring match finds and how
# many a token match finds - and the pair is the point: an
# ordinary wrapper raises both by the same one, and only a
# wrapper with a second class beside it moves them apart. This
# round adds 3 dialogs and therefore 3 ordinary footers, so
# both numbers rise by 3 and the gap of one stays exactly
# where it was.
#
# IT IS SPLIT ACROSS THIS ROUND AND MO-1 RATHER THAN MOVED ONCE
# AT THE END. The two ship in one push and revert together, but
# a tree with only one of them applied has to be green too -
# the gate runs on whatever is on disk, not on what was
# intended.
DR = 'test_drift_root.py'
DR_WAS = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 83, 82   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)'
DR_NOW = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 86, 85   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)'


# ================================================== THE !important PIN
# test_important_base counts every !important declaration in
# every <style> in the tree and pins the total. This round
# DELETES one: the dead .recipe-option > div padding rule.
#
# Split with PK-1 rather than moved once at the end, for the
# same reason as the footer pin - the gate runs on whatever is
# on disk, so a tree with only one of the two applied has to be
# green too.
IB = 'test_important_base.py'
IB_WAS = "IMP_TREE = 806   # RT-1, 18 Oct 2026 - twenty went with the four meal-plan screens MN-1 retired, and the planner that replaced them declares none: measured, not deduced.   # (was 826)   # SB-1, 17 Oct 2026 - the hover that forced --alv-good-ink on the invoice icon. The icon is not green any more, so nothing needed forcing.   # (was 827)   # CC-2, 17 Oct 2026 - the one that forced .contact-details open inside an expanded card. Nothing expands now, so the rule had no element left.   # (was 828)   # DT-1, 16 Oct 2026 - fourteen went with the two table-as-cards blocks on home and notifications. Each was a copy of a declaration base already makes, with the same !important.   # (was 842)   # NV-1b, 16 Oct 2026 - thirteen of them went with the title deeds phone card block. Every one was a copy of a declaration base already makes, with the same !important, so nothing changed about what wins - there is simply one copy of each now. The page goes from 14 to 1.   # (was 855)   # PV-1, 15 Oct 2026 - three !important declarations went with the two hand-rolled viewers: an iframe height, an img max-height and a phone-only body height. The component sizes its own body.   # (was 858)   # PH-2, 14 Oct 2026 - the .bg-light line in base   # (was 857)   # MH-2, 13 Oct 2026 - suppliers' one"
IB_NOW = "IMP_TREE = 805   # MW-1, 19 Oct 2026 - one went with the dead phone rule .recipe-option > div { padding: 10px 12px !important }, written for a two-level nesting the row does not have and matching nothing since MN-1.   # (was 806)   # RT-1, 18 Oct 2026 - twenty went with the four meal-plan screens MN-1 retired, and the planner that replaced them declares none: measured, not deduced.   # (was 826)   # SB-1, 17 Oct 2026 - the hover that forced --alv-good-ink on the invoice icon. The icon is not green any more, so nothing needed forcing.   # (was 827)   # CC-2, 17 Oct 2026 - the one that forced .contact-details open inside an expanded card. Nothing expands now, so the rule had no element left.   # (was 828)   # DT-1, 16 Oct 2026 - fourteen went with the two table-as-cards blocks on home and notifications. Each was a copy of a declaration base already makes, with the same !important.   # (was 842)   # NV-1b, 16 Oct 2026 - thirteen of them went with the title deeds phone card block. Every one was a copy of a declaration base already makes, with the same !important, so nothing changed about what wins - there is simply one copy of each now. The page goes from 14 to 1.   # (was 855)   # PV-1, 15 Oct 2026 - three !important declarations went with the two hand-rolled viewers: an iframe height, an img max-height and a phone-only body height. The component sizes its own body.   # (was 858)   # PH-2, 14 Oct 2026 - the .bg-light line in base   # (was 857)   # MH-2, 13 Oct 2026 - suppliers' one"


# ================================== TWO SUITES THIS ROUND'S BAR BREAKS
# BOTH ARE THE SAME SENTENCE AGAIN, and both are repairs rather than
# re-pins: the claims were right and the way they were read was not.
#
# test_planner SLICED THE ACTION BAR BY CHARACTER COUNT.
#
#     _bar = PC[PC.index('class="page-action-buttons"'):][:1800]
#
# 1,800 was the length of that bar on the day MN-1 wrote it. This
# round hangs a More menu in it - about 1,400 characters - and the
# window stopped short of Back, so .index('action-back') raised
# ValueError and the suite DIED rather than failing. A slice by
# character count is a measurement of nothing. Counted by div depth
# instead, which is what a bar really is.
#
# test_retired COMPARED TODAY'S SENTINEL TABLE WITH THE PRE-RT-1 ONE.
# RT-1 cut sixteen dead rows and MH-2 added two, so the claim is "the
# table lost at least fourteen" - true of what RT-1 DID, and read off
# today's disk. Push 2 adds eleven rows and the table is now LARGER
# than the one RT-1 started from, so the check failed on a round that
# had done nothing wrong. alv_rounds.as_left_by answers the question
# that was actually being asked.
#
# That is the fifth repair this sentence has cost in two days:
# historical and present-tense reads are different questions, and the
# call site is the only place that knows which one is being asked.
PL = 'test_planner.py'
PL_WAS = '# BACK IS LAST, asked of the order in the bar and not of its presence.\n_bar = PC.split(\'class="page-action-buttons"\')[1].split(\'</div>\')[0] \\\n    if \'class="page-action-buttons"\' in PC else \'\'\n_bar = PC[PC.index(\'class="page-action-buttons"\'):][:1800]'
PL_NOW = '# BACK IS LAST, asked of the order in the bar and not of its presence.\n#\n# MW-1, 19 Oct 2026 - THE WHOLE BAR, COUNTED, NOT A WINDOW OF 1,800\n# CHARACTERS. That number was the length of this bar on the day this\n# round was written; MW-1 hung a More menu in it and the window\n# stopped 1,400 characters short of Back, so .index() raised\n# ValueError and this suite DIED instead of failing. A slice by\n# character count is a measurement of nothing.\n#\n# Two spellings stood here and the first was dead - computed, then\n# overwritten by the next line before anything read it. Both are\n# replaced by one that counts div depth from the opening tag, which\n# is what a bar is.\n_i = PC.index(\'class="page-action-buttons"\')\n_depth, _bar = 0, \'\'\nfor _m in re.finditer(r\'<div\\b|</div>\', PC[_i:]):\n    _depth += 1 if _m.group(0) == \'<div\' else -1\n    if _depth < 0:\n        _bar = PC[_i:_i + _m.start()]\n        break\nok(bool(_bar), \'  and the bar is readable as one element\', len(_bar))'

PQ_WAS = "    ok(q_big <= 12, '  and that number is under 12', q_big)"
PQ_NOW = "    # MW-1, 19 Oct 2026 - THIRTEEN, because this round asks for one\n    # more thing: the Menus the Apply dialog lists. It is ONE query\n    # however many menus there are - Count() in an annotate, not a\n    # count per row, which is the fault E29 took off four screens -\n    # and the check above is the one that proves it: the number\n    # does not move with the data.\n    ok(q_big <= 13, '  and that number is under 13', q_big)"

RT = 'test_retired.py'
RT_WAS = "ok(len(old_rows) - len(rows) >= N_DEAD_SENTINELS - 2,\n   '  the table is %d rows, down from %d' % (len(rows), len(old_rows)))"
RT_NOW = '# MW-1, 19 Oct 2026 - ASKED OF THE TABLE AS THIS ROUND LEFT IT.\n# This read today\'s PS1 against the pre-RT-1 one, which is a\n# present-tense reading of a claim about the past: RT-1 cut sixteen\n# dead rows and MH-2 added two, so the claim is that THIS ROUND took\n# the table down by at least fourteen. Push 2 adds eleven rows of its\n# own and the table is now larger than the one RT-1 started from, so\n# the check failed on a round that had done nothing wrong.\n#\n# alv_rounds.as_left_by reads the file as the round whose backups end\n# in SUFFIX left it, which is the question this line was always\n# asking. Five repairs in two days, all the same sentence.\nmine_rows = re.findall(r"(?m)^\\s*@\\{\\s*File\\s*=\\s*\'([^\']+)\'",\n                       alv_rounds.as_left_by(os.path.join(ROOT, PS1), SUFFIX, read))\nok(len(old_rows) - len(mine_rows) >= N_DEAD_SENTINELS - 2,\n   \'  as this round left it the table was %d rows, down from %d\'\n   % (len(mine_rows), len(old_rows)),\n   (len(old_rows), len(mine_rows)))\nok(len(rows) >= len(mine_rows),\n   \'  and later rounds have added %d row(s) since, which is not this \'\n   \'round\\\'s business\' % (len(rows) - len(mine_rows)),\n   (len(mine_rows), len(rows)))'


# ============================================ TWO SENTINELS REVEALED
# test_sentinels section 4 asks whether every sentinel row COULD
# ever have failed - a row whose text is in every version of the
# file it names is a row that says nothing.
#
# This round backs meal_planner.html up for the first time since
# MH-2, and with four versions in hand two of MN-1's own rows are
# provably blind: MN-1 CREATED that page, and created it with the
# stepper and the Help modal in it. No version of the file has
# ever lacked either string, and none can have.
#
# They are PINNED rather than rewritten, which is what the
# register exists for and what its own fifth and sixth entries
# say in their own words: a row that guards against a FUTURE
# deletion is the right shape. This round did not break them. It
# made them checkable.
TS = 'test_sentinels.py'
TS_WAS = 'PINNED = {\n    # THE SIXTH, 18 OCT 2026, and it arrived the way the fifth did -'
TS_NOW = "PINNED = {\n    # THE SEVENTH AND EIGHTH, 19 OCT 2026, AND THE SAME STORY AS THE\n    # FIFTH AND SIXTH - revealed, not broken.\n    #\n    # MN-1 CREATED meal_planner.html, and it created the page WITH the\n    # servings stepper and WITH the Help modal. So no version of that\n    # file has ever lacked either string, and no version ever can have:\n    # the page did not exist before the round that wrote them. MW-1 is\n    # the first round since to back the page up, and with four versions\n    # in hand the verdict is provable rather than merely likely.\n    #\n    # That is the correct shape for a guard against a FUTURE deletion.\n    # `stepServings(` is the one control on the planner that writes\n    # without a Save button, and `meal_plansHelpModal` is the Help\n    # button five meal-plan screens were given; the day either is\n    # removed the row fails. Pinned, not rewritten - and said plainly,\n    # as the fifth and sixth were: MW-1 did not break these rows. It\n    # made them checkable.\n    'stepServings(':\n        'the planner servings stepper, which saves on press - MN-1 '\n        'wrote the page WITH it, so no version has ever lacked it',\n    'meal_plansHelpModal':\n        'the Help button MH-2 wired to the guide - present in every '\n        'version of a page MN-1 created on 18 Oct',\n    # THE SIXTH, 18 OCT 2026, and it arrived the way the fifth did -"


# ============================================================= HELPERS
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
    raise SystemExit('MW-1 REFUSED: %s' % msg)


def fit(text, lit):
    """A LF literal as the file's own line ending.

    EVERY literal goes through this. The laptop checks out CRLF and the
    mirror holds LF, and a round that matched one of them would be a
    round that applies on one machine.
    """
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
    """Put `block` immediately above `anchor`."""
    once(text, anchor, where)
    a = fit(text, anchor)
    return text.replace(a, fit(text, block) + a)


def tag_counts(text):
    """({'{%': n, '{{': n, '{#': n}, {'%}': n, '}}': n, '#}': n})"""
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
    # ALREADY APPLIED IS ASKED OF THE TREE, FIRST, and asked of the
    # VIEW rather than the template: a half-applied round that got the
    # views written and died on the template would otherwise be told it
    # was finished. The view is what the urls and the dialogs both need.
    if 'def copy_meal_week(' in read(pv):
        print('MW-1  already applied - the week moves.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE TREE THIS ROUND NEEDS. MN-1 must have shipped (the planner and
    # MealEntry), and Menu / MenuItem must be in models.py - they came
    # with migration 0100 and this round writes no migration at all.
    if not os.path.isfile(pt):
        refuse('%s is not in the tree. MW-1 moves the planner\'s week; '
               'apply MN-1 first.' % TPL)
    models = read(os.path.join(root, 'pages', 'models.py'))
    for cls in ('class Menu(', 'class MenuItem('):
        if cls not in models:
            refuse('pages/models.py has no %s. Menu and MenuItem shipped '
                   'with migration 0100 in push 1; this round writes no '
                   'migration and cannot make them.' % cls[6:-1])
    if 'day_index' not in models:
        refuse('MenuItem has no day_index. A Menu holds DAY INDEXES 0 to '
               '6, not dates - that is the whole reason it can be '
               'stamped onto a week in a different month.')

    # ---------------------------------------------------------------- 2
    # THE VIEWS, THE CONTEXT AND THE IMPORT.
    v = read(pv)
    v = swap(v, IMP_WAS, IMP_NOW, '%s (the model import)' % VIEW)
    v = swap(v, DOC_WAS, DOC_NOW, '%s (the module docstring)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the planner context)' % VIEW)
    v = before(v, VIEW_AT, NEW_VIEWS.lstrip('\n'),
               '%s (above the shopping list)' % VIEW)
    out[pv] = v

    # ---------------------------------------------------------------- 3
    # THE ROUTES.
    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URLS_WAS, URLS_NOW, '%s (the routes)' % URLS)

    # ---------------------------------------------------------------- 4
    # THE BAR, THE CSS, THE THREE DIALOGS AND THE SCRIPT.
    t = read(pt)
    t_before = t
    t = swap(t, BAR_WAS, BAR_NOW, '%s (the action bar)' % TPL)
    t = swap(t, CSS_AT, CSS, '%s (the menu list CSS)' % TPL)
    t = swap(t, DEAD_WAS, DEAD_NOW, '%s (the three dead phone rules)' % TPL)
    t = before(t, MODAL_AT, MODALS, '%s (the three dialogs)' % TPL)
    t = swap(t, JS_AT, JS, '%s (the script)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 5
    # THE TWO PAGE COUNTS. Both are present-tense readings and both
    # have to move with the menu this round hangs on the planner.
    for name, was, now_ in ((MM, MM_WAS, MM_NOW), (LM, LM_WAS, LM_NOW)):
        p = os.path.join(root, name)
        out[p] = swap(read(p), was, now_, '%s (the page count)' % name)

    # ---------------------------------------------------------------- 6
    # THE REGISTERS.
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

    pib = os.path.join(root, IB)
    out[pib] = swap(read(pib), IB_WAS, IB_NOW,
                    '%s (the !important pin)' % IB)

    ppl = os.path.join(root, PL)
    ppl_src = swap(read(ppl), PL_WAS, PL_NOW,
                   '%s (the bar slice)' % PL)
    out[ppl] = swap(ppl_src, PQ_WAS, PQ_NOW,
                    '%s (the query pin)' % PL)
    prt = os.path.join(root, RT)
    out[prt] = swap(read(prt), RT_WAS, RT_NOW,
                    '%s (the sentinel table)' % RT)

    pts = os.path.join(root, TS)
    out[pts] = swap(read(pts), TS_WAS, TS_NOW,
                    '%s (two revealed rows)' % TS)

    pdr = os.path.join(root, DR)
    out[pdr] = swap(read(pdr), DR_WAS, DR_NOW,
                    '%s (the footer pin)' % DR)

    # ---------------------------------------------------------------- 7
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    # A CSS COMMENT THAT DOES NOT CLOSE EATS THE REST OF THE BLOCK. MN-1
    # shipped one of these - test_compact_card found it the same day,
    # "meal_planner.html stray */ 0 unclosed /* 1" - and the gate MN-1
    # grew for it is the gate this round wears too.
    o, c = out[pt].count('/*'), out[pt].count('*/')
    if o != c:
        refuse('%s: %d /* against %d */ - a CSS comment that does not '
               'close eats every rule after it' % (TPL, o, c))

    # AND A DJANGO TAG THAT DOES NOT CLOSE IS THE SAME FAULT ONE LAYER
    # UP. Counted as a DELTA, not a balance: administration.html has
    # never balanced by raw count because its prose shows markup, and
    # Push-PendingChanges.ps1 does not balance its braces either. What
    # must hold is that every tag this round opens, it also closes.
    was_o, was_c = tag_counts(t_before)
    now_o, now_c = tag_counts(out[pt])
    for k in now_o:
        pair = {'{%': '%}', '{{': '}}', '{#': '#}'}[k]
        if now_o[k] - was_o[k] != now_c[pair] - was_c[pair]:
            refuse('%s: this round added %d %s and %d %s - a tag that '
                   'does not close renders as text'
                   % (TPL, now_o[k] - was_o[k], k,
                      now_c[pair] - was_c[pair], pair))

    # NO SECOND MORE MENU. base owns the ids, so two on a page is two
    # elements answering to #actionMoreBtn - which is the fault H8 spent
    # a round removing from 31 pages.
    if out[pt].count('id="actionMoreBtn"') != 1:
        refuse('%s: %d copies of id="actionMoreBtn" - base keys the '
               'binder on that id and two of them is one too many'
               % (TPL, out[pt].count('id="actionMoreBtn"')))

    # THE THREE DIALOGS, AND THE ONE CONTROL EACH THAT OPENS THEM.
    for mid in ('copyWeekModal', 'saveMenuModal', 'applyMenuModal'):
        if out[pt].count('id="%s"' % mid) != 1:
            refuse('%s: %d dialogs with id %s, expected 1'
                   % (TPL, out[pt].count('id="%s"' % mid), mid))
        if out[pt].count('data-target="#%s"' % mid) != 1:
            refuse('%s: %d controls open %s, expected 1'
                   % (TPL, out[pt].count('data-target="#%s"' % mid), mid))

    # NO NESTED FORM. The trashcan sits inside the Apply form's row
    # list, so the delete had to be a separate form outside it - a form
    # inside a form is not a thing HTML has, and the browser silently
    # drops the inner one, which would be a trashcan that does nothing.
    depth, worst = 0, 0
    for m in re.finditer(r'<form\b|</form>', out[pt]):
        depth += 1 if m.group(0) == '<form' else -1
        worst = max(worst, depth)
    if worst > 1 or depth != 0:
        refuse('%s: forms nest %d deep and close at %d - a form inside a '
               'form is dropped by the browser' % (TPL, worst, depth))

    # EVERY ROUTE THE TEMPLATE REVERSES MUST EXIST. The round adds five
    # names and the dialogs name all five; a {% url %} on a name that is
    # not registered is a NoReverseMatch on the planner, which is the
    # screen, not a corner of it.
    names = set(re.findall(r"name='([a-z_]+)'", out[pu]))
    for used in sorted(set(re.findall(r'{%\s*url\s+"([a-z_]+)"', out[pt]))
                       | set(re.findall(r"{%\s*url\s+'([a-z_]+)'",
                                        out[pt]))):
        if used not in names:
            refuse('%s reverses %r and %s registers no such name'
                   % (TPL, used, URLS))

    # AND EVERY VIEW THE ROUTES NAME MUST BE IN THE MODULE. urls.py
    # imports the package, so a route pointing at a function that is not
    # there is an AttributeError on startup - loud, but on Railway it is
    # loud in a deploy log at two in the morning.
    for fn in ('meal_week_preview', 'copy_meal_week', 'save_menu',
               'apply_menu', 'delete_menu'):
        if 'def %s(' % fn not in out[pv]:
            refuse('%s names views.%s and %s does not define it'
                   % (URLS, fn, VIEW))
        if out[pv].count('def %s(' % fn) != 1:
            refuse('%s defines %s %d times' % (VIEW, fn,
                                               out[pv].count('def %s(' % fn))
                   )

    # NO %-d AND NO %#d. Windows strftime has neither the one nor the
    # other of the pair, and this project runs on both the laptop and
    # Railway. day_label builds the date with %d and .day instead.
    #
    # ASKED OF THE CODE AND NOT OF THE FILE. day_label's own docstring
    # explains why it does not use %-d, and the first cut of this gate
    # refused the round over that sentence: to a substring search, a
    # comment about a thing is the thing. python_code_only blanks the
    # comments and the docstrings line for line and leaves the payload
    # strings alone, which is what makes the verdict about the code.
    import alv_tree
    code = alv_tree.python_code_only(out[pv], payloads=True)
    for bad in ('%-d', '%#d', '%-m', '%#m'):
        if bad in code:
            refuse('%s uses %s, which exists on one of the two platforms '
                   'this project runs on' % (VIEW, bad))

    # ---------------------------------------------------------------- 8
    if CHECK:
        print('MW-1 --check')
        print('  views      : 5 new, no migration')
        print('  routes     : 5')
        print('  dialogs    : 3')
        print('  files      : %d' % len(out))
        for k in sorted(out):
            print('    %s' % os.path.relpath(k, root))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
        print('  wrote %s' % os.path.relpath(k, root))
    print('MW-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_meal_week.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
