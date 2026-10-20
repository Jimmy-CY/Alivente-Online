# -*- coding: utf-8 -*-
"""apply_chip_menu.py - round RD-2, 19 Oct 2026.

RELEASE 4, PUSH 2. A MEAL IN THE CALENDAR HAS A MENU.

Demetri, answering Q2 of the Release 4 questions, in his own words:
"maybe if I hover over a recipe name in the calendar, it gives me the
option to view the recipe ... or to remove the recipe". And then, on
19 Oct, that Move should be in it too.

    View recipe      opens RD-1's dialog
    Move to...       a date, and the leftovers travel with it
    Remove           what the Day card's trashcan already does

NO MENU IN THE DAY VIEW, and that is a decision rather than an
omission. The Day card already carries View, Leftovers and Remove as
buttons and has the room for them; a menu there would be a second way
to do the same thing. It gains ONE button - Move to... - beside
Leftovers. The menu exists because a 152px week column and a 162px
month cell have room for a name and nothing else.

THE CLICK HAS TO BE STOPPED IN THE CAPTURE PHASE, and this is the
part that is easy to get wrong.

The month cell carries `onclick="openPicker(...)"` - Demetri's Q2
again: "I want it to go straight to the Picker, when I click a day."
A chip sits INSIDE that cell. So a click on a chip must open the menu
and must NOT also open the picker.

The obvious shape - one delegated listener on `document`, calling
`e.stopPropagation()` - DOES NOT WORK. A bubbling event reaches the
cell before it reaches the document, so the inline onclick has already
run by the time anything on document sees it. Stopping propagation
there stops nothing: there is nothing left above.

So the listener is registered with `capture: true`. The capture phase
runs top-down, document first, which is the only place a single
delegated handler can get in front of an inline onclick further down
the tree. Section 3 drives it: it clicks a chip and asks whether the
picker opened.

That is MO-1's trashcan lesson - a control inside a clickable row has
to stop the click going up - with the twist that WHERE you listen
decides whether you can.

LEFTOVERS TRAVEL WITH THEIR PARENT, KEEPING THE GAP, and a leftover
cannot overtake its parent. That logic was written for MM-1 on 19 Oct,
never run, and lost with the mirror rebuild; it is written again here,
where its buttons finally exist. Move a Monday dinner to Wednesday and
its Tuesday leftovers become Thursday's.

Idempotent. Every file backed up to .bak_chipmenu.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_chipmenu'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_chip_menu.py'
PATCHER = 'apply_chip_menu.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
BASE = os.path.join('pages', 'templates', 'base.html')
MARK = 'RD-2, 19 Oct 2026'
CHECK = False
CREATES = ()


# ======================================================== THE ENDPOINT
MOVE_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):"""
MOVE_NOW = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def move_meal_entry(request):
    \"\"\"Move a meal to another day, and its leftovers with it.

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
    \"\"\"
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
def remove_meal_entry(request):"""

URL_WAS = """    path('meal_plans/remove/', views.remove_meal_entry, name='remove_meal_entry'),"""
URL_NOW = """    path('meal_plans/remove/', views.remove_meal_entry, name='remove_meal_entry'),
    # RD-2, 19 Oct 2026 - move a meal to another day. Beside remove,
    # because the chip menu offers them together.
    path('meal_plans/move/', views.move_meal_entry, name='move_meal_entry'),"""


# =========================================================== THE CHIPS
#
# A SPAN BECOMES A BUTTON. It is a control now, so it has to be one -
# a span with a click handler is invisible to a keyboard and to a
# screen reader, and this is the only way to reach Move at all in
# Month or Week.
MONTH_WAS = """                    <span class="month-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</span>"""
MONTH_NOW = """                    {# THE CHIP IS A CONTROL - RD-2, 19 Oct 2026. A span with #}
                    {# a click handler cannot be reached by a keyboard, and in #}
                    {# Month and Week this menu is the ONLY way to Move or     #}
                    {# Remove: the row actions live on the Day card.           #}
                    <button type="button" class="month-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}"
                            data-chip="{{ e.meal_entry_id }}"
                            data-chip-name="{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}"
                            data-chip-date="{{ e.date|date:'Y-m-d' }}"{% if e.recipe_id %}
                            data-chip-view="{% url 'recipe_quicklook' e.recipe.recipe_id %}"{% endif %}
                            aria-haspopup="menu"
                            aria-label="{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %} - view, move or remove">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</button>"""

WEEK_WAS = """                            <span class="week-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</span>"""
WEEK_NOW = """                            <button type="button" class="week-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}"
                                    data-chip="{{ e.meal_entry_id }}"
                                    data-chip-name="{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}"
                                    data-chip-date="{{ e.date|date:'Y-m-d' }}"{% if e.recipe_id %}
                                    data-chip-view="{% url 'recipe_quicklook' e.recipe.recipe_id %}"{% endif %}
                                    aria-haspopup="menu"
                                    aria-label="{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %} - view, move or remove">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</button>"""


# ================================== AND ONE BUTTON ON THE DAY CARD
#
# The Day card has the room, so it keeps its buttons; it was simply
# missing this one. Beside Leftovers, because both are "this meal,
# but on another day".
DAYBTN_WAS = """                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove {{ entry.recipe.recipe_name }} from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, '{{ entry.recipe.recipe_name|escapejs }}')"><i class="fas fa-trash"></i></button>"""
DAYBTN_NOW = """                                    {# MOVE - RD-2, 19 Oct 2026. The Day card keeps  #}
                                    {# buttons rather than gaining the chip menu:    #}
                                    {# it has the room, and a second way to do the   #}
                                    {# same thing is not a feature.                  #}
                                    <button type="button" class="icon-action-btn icon-move"
                                            title="Move to another day"
                                            aria-label="Move {{ entry.recipe.recipe_name }} to another day"
                                            data-move="{{ entry.meal_entry_id }}"
                                            data-move-name="{{ entry.recipe.recipe_name }}"
                                            data-move-date="{{ entry.date|date:'Y-m-d' }}"><i class="fas fa-arrow-right"></i></button>
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Remove from this day"
                                            aria-label="Remove {{ entry.recipe.recipe_name }} from this day"
                                            onclick="removeMeal({{ entry.meal_entry_id }}, '{{ entry.recipe.recipe_name|escapejs }}')"><i class="fas fa-trash"></i></button>"""


# ====================================== AND BASE LEARNS ONE NAME
#
# ALIAS THE COLOUR, NEVER THE NAME - the rule MO-1 paid for. Move
# changes which day a meal is on, which is a write exactly as
# Duplicating and Leftovers are, so it points at --alv-edit and joins
# that family. It gets its OWN NAME because a class carries ONE
# PICTURE: .icon-leftover already wears fa-redo and .icon-duplicate
# fa-copy, and hanging fa-arrow-right on either is what test_icon_names
# refused MO-1 for in under a minute.
BASE_WAS = """.icon-leftover       { color: var(--alv-edit); border-color: var(--alv-edit); }
.icon-leftover:hover { background-color: var(--alv-edit); color: var(--alv-on-accent); }
.icon-color-leftover { color: var(--alv-edit); }"""
BASE_NOW = """.icon-leftover       { color: var(--alv-edit); border-color: var(--alv-edit); }
.icon-leftover:hover { background-color: var(--alv-edit); color: var(--alv-on-accent); }
.icon-color-leftover { color: var(--alv-edit); }

/* Move: the fifth NAME on the same colour - RD-2, 19 Oct 2026. Moving a
   meal to another day changes a row rather than creating or destroying
   one, so it is CHANGE, like Leftovers beside it and Duplicate above.
   Its own name, for the reason written there: a class carries one
   picture, this one is fa-arrow-right, and .icon-leftover is already
   spoken for by fa-redo. */
.icon-move       { color: var(--alv-edit); border-color: var(--alv-edit); }
.icon-move:hover { background-color: var(--alv-edit); color: var(--alv-on-accent); }
.icon-color-move { color: var(--alv-edit); }"""


# ========================================= THE MENU, ITS RULES AND ITS JS
MENU_WAS = """{% include 'recipe_quicklook_shell.html' %}"""
MENU_NOW = """{% include 'recipe_quicklook_shell.html' %}

{# ------------------------------------- THE CHIP MENU - RD-2, 19 Oct 2026 #}
{# One menu, moved to whichever chip was pressed. Thirty-five cells of     #}
{# month times three meals is a hundred menus if each chip carries its own #}
{# and only ever one of them is open.                                      #}
<div id="chipMenu" class="chip-menu" role="menu" hidden>
    <button type="button" class="chip-menu-item" data-act="view" role="menuitem">
        <i class="fas fa-eye"></i> View recipe
    </button>
    {% if perms.auth.can_edit_recipes %}
    <button type="button" class="chip-menu-item" data-act="move" role="menuitem">
        <i class="fas fa-arrow-right"></i> Move to&hellip;
    </button>
    <button type="button" class="chip-menu-item chip-menu-danger" data-act="remove" role="menuitem">
        <i class="fas fa-trash"></i> <span data-slot="remove">Remove</span>
    </button>
    {% endif %}
</div>

{% if perms.auth.can_edit_recipes %}
{# -------------------------------------------------- MOVE TO, RD-2 #}
{# A native date input, because a date picker that works offline, on #}
{# a phone, with a keyboard and in every locale is one the browser   #}
{# already wrote. AP-1 builds a mini month for ADDING from the       #}
{# library, where the shortcuts earn their room; moving is one date. #}
<div class="modal fade" id="moveModal" tabindex="-1" role="dialog"
     aria-labelledby="moveTitle" aria-hidden="true">
    <div class="modal-dialog modal-sm" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="moveTitle">
                    <i class="fas fa-arrow-right"></i> Move to another day
                </h5>
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'move_meal_entry' %}">
                {% csrf_token %}
                {# AND THE VIEW TRAVELS WITH IT - PB-2, 19 Oct 2026. #}
                <input type="hidden" name="view" value="{{ view_mode }}">
                <input type="hidden" name="meal_entry_id" id="moveEntry">
                <div class="modal-body">
                    <p class="move-what" id="moveWhat"></p>
                    <label for="moveDate" class="move-label">New day</label>
                    <input type="date" class="form-control" id="moveDate"
                           name="date" required>
                </div>
                <div class="modal-footer">
                    {# HOUSE TONE - RS-1a's rule, which this round broke #}
                    {# once and test_recipe_tones caught.                 #}
                    <button type="button" class="btn action-secondary"
                            data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary">Move</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endif %}

<style>
/* THE CHIP MENU - RD-2, 19 Oct 2026. No colour here that is not a token. */
.chip-menu {
    position: absolute;
    z-index: 1060;
    min-width: 190px;
    padding: 4px;
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
.chip-menu[hidden] { display: none; }
.chip-menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    /* 44px, because this is the only way to Move or Remove on a phone. */
    min-height: 44px;
    padding: 0 12px;
    border: 0;
    border-radius: var(--alv-radius-sm);
    background: transparent;
    color: var(--alv-ink);
    font-size: 14px;
    text-align: left;
    cursor: pointer;
}
.chip-menu-item:hover { background: var(--alv-surface); }
.chip-menu-item:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}
/* A WORD SOMEBODY READS GETS ink-soft; a mark may stay faint. */
.chip-menu-item i { width: 15px; color: var(--alv-ink-faint); }
.chip-menu-danger { color: var(--alv-bad-ink); }
.chip-menu-danger i { color: var(--alv-bad-ink); }
/* THE CHIPS ARE BUTTONS NOW, so they must not look like buttons.

   AND THIS RULE DOES NOT SET display. It did - `display: block` - and
   it sits LATER in the file than MV-2's phone rule, which hides
   .month-chip below 768px so the month shows marks instead of names.
   So the names came back on the phone: 38 chips drawn at 390px in a
   48px cell, which is five characters of noise. test_month_view
   caught it.

   A reset that reaches for display is a reset that outranks every
   decision about whether a thing is shown at all. */
.month-chip, .week-chip {
    width: 100%;
    border: 0;
    background: transparent;
    text-align: left;
    font: inherit;
    cursor: pointer;
}
.month-chip:focus-visible, .week-chip:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: 1px;
}
.move-what { color: var(--alv-ink-soft); font-size: 14px; }
.move-label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--alv-ink-strong);
}
</style>

<script>
(function () {
    var menu = document.getElementById('chipMenu');
    if (!menu) { return; }
    var open = null;

    function place(chip) {
        var r = chip.getBoundingClientRect();
        menu.hidden = false;
        var mw = menu.offsetWidth, mh = menu.offsetHeight;
        // IT MUST NOT GO OFF THE EDGE. A month cell on the Sunday
        // column is at the right-hand edge of the page, and a menu
        // that opens rightwards from there is half off the screen.
        var left = Math.min(r.left + window.scrollX,
                            window.scrollX + document.documentElement.clientWidth - mw - 8);
        var top = r.bottom + window.scrollY + 2;
        if (r.bottom + mh + 8 > window.innerHeight) {
            top = r.top + window.scrollY - mh - 2;
        }
        menu.style.left = Math.max(window.scrollX + 8, left) + 'px';
        menu.style.top = top + 'px';
    }

    function close() {
        menu.hidden = true;
        open = null;
    }

    // CAPTURE, NOT BUBBLE - RD-2, 19 Oct 2026, and this is the whole
    // trick of this round.
    //
    // The month cell carries onclick="openPicker(...)" and the chip
    // sits inside it. A bubbling event reaches the CELL before it
    // reaches the document, so a delegated listener here in the bubble
    // phase would be told about the click only after the picker had
    // already opened - stopPropagation at that point stops nothing,
    // because there is nothing left above.
    //
    // The capture phase runs top-down, document first, which is the
    // only place one delegated handler can get in front of an inline
    // onclick further down the tree.
    document.addEventListener('click', function (e) {
        var chip = e.target.closest('[data-chip]');
        if (chip) {
            e.preventDefault();
            e.stopPropagation();
            if (open === chip) { close(); return; }
            open = chip;
            var view = menu.querySelector('[data-act="view"]');
            var url = chip.getAttribute('data-chip-view');
            // A NOTE IS NOT A RECIPE. "Eat out" has nothing to view.
            view.hidden = !url;
            view.setAttribute('data-url', url || '');
            var slot = menu.querySelector('[data-slot="remove"]');
            if (slot) {
                slot.textContent = 'Remove from ' +
                    new Date(chip.getAttribute('data-chip-date') +
                             'T00:00:00').toLocaleDateString(undefined,
                        {weekday: 'short', day: 'numeric', month: 'short'});
            }
            place(chip);
            return;
        }
        if (!e.target.closest('#chipMenu')) { close(); }
    }, true);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { close(); }
    });

    menu.addEventListener('click', function (e) {
        var item = e.target.closest('[data-act]');
        if (!item || !open) { return; }
        var act = item.getAttribute('data-act');
        var chip = open;
        close();
        if (act === 'view') {
            var url = item.getAttribute('data-url');
            if (url) { openQuickLookAt(url, chip); }
        } else if (act === 'move') {
            askMove(chip.getAttribute('data-chip'),
                    chip.getAttribute('data-chip-name'),
                    chip.getAttribute('data-chip-date'));
        } else if (act === 'remove') {
            removeMeal(chip.getAttribute('data-chip'),
                       chip.getAttribute('data-chip-name'));
        }
    });

    // THE DAY CARD'S OWN MOVE BUTTON, which has no menu around it.
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-move]');
        if (!btn) { return; }
        e.preventDefault();
        askMove(btn.getAttribute('data-move'),
                btn.getAttribute('data-move-name'),
                btn.getAttribute('data-move-date'));
    });

    function askMove(entryId, name, dateStr) {
        var form = document.getElementById('moveEntry');
        if (!form) { return; }
        form.value = entryId;
        document.getElementById('moveWhat').textContent =
            'Moving ' + name;
        var d = document.getElementById('moveDate');
        d.value = dateStr || '';
        $('#moveModal').modal('show');
        window.setTimeout(function () { d.focus(); }, 300);
    }

    // RD-1's dialog, opened from here rather than from a link - the
    // chip is not an anchor, so there is no href to fall back to and
    // the menu item passes the URL it was given.
    function openQuickLookAt(url, chip) {
        var box = document.getElementById('quickLookContent');
        if (!box) { window.location.href = url; return; }
        box.innerHTML = '<div class="modal-body text-center ql-none">' +
            '<i class="fas fa-spinner fa-spin fa-2x"></i></div>';
        $('#quickLookModal').modal('show');
        fetch(url, {credentials: 'same-origin'})
            .then(function (r) {
                if (!r.ok) { throw new Error(r.status); }
                return r.text();
            })
            .then(function (html) { box.innerHTML = html; })
            .catch(function () {
                box.innerHTML = '<div class="modal-body ql-none">' +
                    'Could not load the recipe.</div>';
            });
    }
})();
</script>"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back('; What = 'PB-2: a write on the planner leaves you where you were - eleven redirects carried the date and dropped the view, so every add and remove bounced you to Month' },"""
DRIFT_WAS = """N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 88, 87   # MO-1, 19 Oct 2026"""
DRIFT_NOW = """N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 90, 89   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026"""
DRIFT = 'test_drift_root.py'

SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back('; What = 'PB-2: a write on the planner leaves you where you were - eleven redirects carried the date and dropped the view, so every add and remove bounced you to Month' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def move_meal_entry('; What = 'RD-2: move a meal to another day, and its leftovers travel with it keeping the gap - MM-1 logic, finally with buttons to reach it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-chip='; What = 'RD-2: a meal in Month or Week is a button with a menu - View, Move to and Remove - because a 152px column has room for a name and nothing else' },
    @{ File = 'pages/templates/meal_planner.html'; Text = "}, true);"; What = 'RD-2: the chip listens in the CAPTURE phase - the month cell opens the picker on click, and a bubble-phase handler is told only after that has already happened' },"""

SUITE_WAS = """    'test_planner_back.py'
)"""
SUITE_NOW = """    'test_planner_back.py',
    # RD-2, 19 Oct 2026 - the chip menu. Section 3 clicks a chip and
    # asks whether the picker ALSO opened, which is the question the
    # capture phase exists to answer.
    'test_chip_menu.py'
)"""

TREE_WAS = """    # PB-2, 19 Oct 2026 - the regression push 1 shipped: eleven
    # redirects that kept the date and dropped the view.
    'test_planner_back.py',
]"""
TREE_NOW = """    # PB-2, 19 Oct 2026 - the regression push 1 shipped: eleven
    # redirects that kept the date and dropped the view.
    'test_planner_back.py',
    # RD-2, 19 Oct 2026 - the chip menu, and the move behind it.
    # Leftovers travel with their parent and cannot overtake it.
    'test_chip_menu.py',
]"""

RD_WAS = """    '.bak_viewback',
]"""
RD_NOW = """    '.bak_viewback',
    # RD-2, 19 Oct 2026 - a meal in the calendar has a menu, and base
    # learns one more name on the CHANGE colour.
    '.bak_chipmenu',
]"""

WD_WAS = """CONVERTED_N = 121   # PB-2, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 122   # RD-2, 19 Oct 2026 - this round own suite   # (was 121)"""


# ============================== AND A REPAIR TO MN-1's OWN SUITE
#
# test_planner reads the row controls out of a 900-CHARACTER WINDOW
# from the first `class="row-actions"`, and asks that icon-view comes
# before icon-delete in it. RD-1's five-line comment above the eye and
# this round's Move button between Leftovers and Remove push
# icon-delete past 900, and the claim raises ValueError rather than
# failing - a crash blocks a push exactly as hard as a failure and
# says far less about why.
#
# A WINDOW CHOSEN BY GUESS IS NOT THE SUBJECT. The block is, and it
# ends where the div does. The repaired claim also says more than the
# old one: LOOK before CHANGE before DESTROY, which is the house order
# and is now three controls rather than two.
PLANNER_WAS = """_ra = PC[PC.index('class="row-actions"'):][:900]
ok(_ra.index('icon-view') < _ra.index('icon-delete'),
   '  in house order: LOOK before DESTROY')"""
PLANNER_NOW = """# EVERY BLOCK, AND ONLY THE CONTROLS IT HAS - repaired by RD-2,
# 19 Oct 2026, twice.
#
# It read a 900-CHARACTER WINDOW from the first `class="row-actions"`.
# RD-1's comment above the eye and this round's Move button pushed
# icon-delete past it and .index() RAISED rather than failing - a
# crash blocks a push as hard as a failure and says less about why.
#
# The first repair then asked for icon-move in that same first block,
# which is the LEFTOVER row - and a leftover has no Move, because its
# date is tied to the meal it came from. Asking every block for the
# order of the controls IT HAS is the claim that was always meant.
# LOOK, COPY, CHANGE, DESTROY - and Move is CHANGE, so it sits after
# Leftovers (which creates a row) and before Remove (which ends one).
# That is where RD-2 put the button; this is the same order written
# down.
_order = ['icon-view', 'icon-leftover', 'icon-move', 'icon-delete']
_blocks = [b[:b.index('</div>')]
           for b in PC.split('class="row-actions"')[1:]]
ok(_blocks, 'the row controls are in blocks this suite can read')
_bad = []
for _b in _blocks:
    _seen = [(_b.index(n), n) for n in _order if n in _b]
    if [n for _i, n in sorted(_seen)] != [n for n in _order
                                          if n in _b]:
        _bad.append([n for _i, n in sorted(_seen)])
ok(not _bad,
   '  in house order: LOOK before CHANGE before DESTROY, in each of '
   'the %d block(s)' % len(_blocks), _bad)"""
PLANNER = 'test_planner.py'


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
    raise SystemExit('RD-2 REFUSED: %s' % msg)


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
    out = {}

    pv = os.path.join(root, VIEW)
    pu = os.path.join(root, URLS)
    pt = os.path.join(root, TPL)
    pb = os.path.join(root, BASE)
    v = read(pv)
    t = read(pt)
    b = read(pb)

    # ---------------------------------------------------------------- 0
    if 'def move_meal_entry(' in v:
        print('RD-2  already applied - a meal in the calendar has a menu.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE: chips that are spans, and no way to move.
    sys.path.insert(0, root)
    import alv_tree as T
    markup = T.code_only(t)
    if 'data-chip=' in markup:
        refuse('%s already carries a chip menu' % TPL)
    if 'planner_back(' not in T.python_code_only(v, payloads=True):
        refuse('%s has no planner_back - PB-2 goes first, because every '
               'redirect this round writes uses it' % VIEW)
    if '.icon-move' in T.code_only(b):
        refuse('%s already knows .icon-move' % BASE)

    # ---------------------------------------------------------------- 2
    v = swap(v, MOVE_WAS, MOVE_NOW, '%s (the endpoint)' % VIEW)
    out[pv] = v
    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    t = swap(t, MONTH_WAS, MONTH_NOW, '%s (the month chip)' % TPL)
    t = swap(t, WEEK_WAS, WEEK_NOW, '%s (the week chip)' % TPL)
    t = swap(t, DAYBTN_WAS, DAYBTN_NOW, '%s (the day card move)' % TPL)
    t = swap(t, MENU_WAS, MENU_NOW, '%s (the menu)' % TPL)
    out[pt] = t

    out[pb] = swap(b, BASE_WAS, BASE_NOW, '%s (.icon-move)' % BASE)

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    pdr = os.path.join(root, DRIFT)
    out[pdr] = swap(read(pdr), DRIFT_WAS, DRIFT_NOW,
                    '%s (the footer census)' % DRIFT)

    ppl = os.path.join(root, PLANNER)
    out[ppl] = swap(read(ppl), PLANNER_WAS, PLANNER_NOW,
                    '%s (the row-actions window)' % PLANNER)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nt = T.code_only(out[pt])

    # THE CAPTURE PHASE, which is the whole trick. A bubble-phase
    # listener on document is told about the click only after the
    # month cell's inline onclick has already opened the picker.
    if '}, true);' not in nt:
        refuse('%s does not register its click listener with capture. '
               'The month cell opens the picker on click and the chip '
               'is INSIDE it, so a bubble-phase handler cannot get in '
               'front of that.' % TPL)

    # ONE MENU, NOT ONE PER CHIP. Thirty-five cells times three meals
    # is a hundred menus of which one is ever open.
    if nt.count('id="chipMenu"') != 1:
        refuse('%s renders %d chip menus, expected exactly 1'
               % (TPL, nt.count('id="chipMenu"')))

    # THE CHIPS ARE BUTTONS. A span with a click handler cannot be
    # reached by a keyboard, and in Month and Week this menu is the
    # only way to Move or Remove at all.
    for cls in ('month-chip', 'week-chip'):
        if re.search(r'<span class="%s' % cls, nt):
            refuse('%s still renders .%s as a span. It is a control '
                   'now.' % (TPL, cls))

    # BASE OWNS THE NAME, AND IT IS A NEW NAME ON AN OLD COLOUR.
    nb = T.code_only(out[pb])
    if '.icon-move' not in nb:
        refuse('%s did not learn .icon-move' % BASE)
    if 'var(--alv-edit)' not in nb.split('.icon-move')[1][:200]:
        refuse('%s gives .icon-move a colour of its own. Move is a '
               'CHANGE, like Leftovers and Duplicate beside it - alias '
               'the colour, never the name.' % BASE)

    # AND THE MOVE FORM CARRIES THE VIEW, because PB-2 made that the
    # rule and a form added after it is exactly where it gets forgotten.
    move_form = nt.split("action=\"{% url 'move_meal_entry' %}\"", 1)
    if len(move_form) < 2 or 'name="view"' not in move_form[1][:600]:
        refuse('%s: the Move form does not carry the view. PB-2 put a '
               'hidden view on every form on this page; this is the '
               'first one added since.' % TPL)

    nv = T.python_code_only(out[pv], payloads=True)
    if 'leftover_of.date' not in nv:
        refuse('%s does not compare a leftover with its parent, so a '
               'leftover could be moved before the meal it comes from'
               % VIEW)
    # SLICED TO THE FUNCTION, NOT TO A NUMBER OF CHARACTERS.
    #
    # The first spelling of this took the 3000 characters after the
    # def and refused the round: python_code_only blanks a docstring
    # line-for-line rather than removing it, so the body still starts
    # 1400 characters in and `update_fields` landed at 3025. A window
    # chosen by guess is not the subject; the function is.
    body = nv.split('def move_meal_entry', 1)[1]
    body = re.split(r'\n@|\ndef ', body)[0]
    if 'update_fields=' not in body:
        refuse('%s rewrites whole rows to change one date' % VIEW)
    if 'transaction.atomic' not in body:
        refuse('%s moves a parent and its leftovers without a '
               'transaction - a half-moved chain leaves leftovers on a '
               'date nobody chose' % VIEW)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('RD-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)

    print('RD-2  applied - a meal in the calendar has a menu.')
    print('      View, Move to and Remove, and the leftovers travel.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
