# -*- coding: utf-8 -*-
"""apply_picker_stays.py - round PS-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE PICKER ADDS ON CLICK, AND STAYS OPEN.

Demetri: "Should clicking on a meal just add it to the day, without
needing to have 1 '+ Add Meal' button. And the picker should just stay
open until I close the modal with the 'x' or pressing a 'Done' button?
... Because if I want to add a few recipes/sides to a day, currently,
I would have to click on '+ Add Recipe', then filter, then click on
the recipe, then click on '+ Add Meal', then click on '+ Add Recipe'
again ...... and repeat."

And again on 19 Oct: "On the picker, we are going to change it so that
you don't have to add a meal, only click on a recipe", and "I also
don't need the servings right now. When I add a recipe, it must just
add the standard servings for that recipe."

THE ARITHMETIC, WHICH IS WORSE THAN HE PUT IT. Four items onto a
Saturday:

    open - filter - click - Add Meal
    open - filter - click - Add Meal     <- THE FILTERS ARE FORGOTTEN
    open - filter - click - Add Meal        on every open, by C19,
    open - filter - click - Add Meal        which is right for ONE add
    ~20 actions                             and a tax on four

    open - filter - click click click click - Done
    7 actions

**The re-filtering is the real cost.** C19 made the dialog forget its
filters on every open - correct for a dialog you use once, a tax on a
dialog you use four times in a row. C19's rule is unchanged here: the
filters still reset ON OPEN. They simply survive while it is open,
which is the whole point.

NAMED PS-1, NOT PA-1. `claude/pa1_picker_adds_decided_19_oct.md` calls
this round PA-1 and that name is wrong: check_gates.name_free refused
it, because apply_passport_filter.py has declared PA-1 since long
before this module existed, with twenty references across four files.
Third time that gate has paid for itself this week.

WHAT IT COSTS, AND THE ANSWERS

  THE SERVINGS FIELD GOES. The recipe's own yield, which is exactly
  what leaving that box blank already did - so the BEHAVIOUR does not
  change, only the field disappears. Adjust afterwards with the day's
  stepper, which saves on press: one click after, rather than a field
  every time.

  A MIS-CLICK BECOMES A REAL ROW. Today Cancel discards it. So the
  dialog MUST show what you have added - and it shows the whole day,
  not just this visit's additions, because "what is on Saturday" is
  the question you are actually asking. Each row removable in place.
  WITHOUT THAT, THIS CHANGE SHOULD NOT BE MADE.

  CANCEL GOES TOO. There is nothing to cancel when every action has
  already happened, and a Cancel that did not undo them would be a
  lie. The footer is Done.

THE ENDPOINTS ANSWER IN JSON WHEN ASKED. add and remove already
existed and already redirected; a dialog that stays open needs the
day back instead. They keep their redirect for a form post and gain a
JSON branch for this one, rather than being replaced - the Move
dialog, the note form and the menus all still post normally.

Idempotent. Every file backed up to .bak_pickerstays.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_pickerstays'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_picker_stays.py'
PATCHER = 'apply_picker_stays.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PS-1, 19 Oct 2026'
CHECK = False
CREATES = ()


# ======================================================== THE DAY, AS JSON
PAYLOAD_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_entry(request):"""
PAYLOAD_NOW = """# ---- WHAT IS ON A DAY - PS-1, 19 Oct 2026.
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
    \"\"\"Every meal on `when`, in the order the planner draws them.\"\"\"
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
    \"\"\"What is on one day, as JSON. Read-tier.

    PS-1, 19 Oct 2026. The picker asks this when it opens, so the
    strip shows the whole day rather than only what this visit added -
    "what is on Saturday" being the question actually being asked.
    \"\"\"
    when = week_of(request.GET.get('date'), None)
    if when is None:
        return JsonResponse({'error': 'date'}, status=400)
    return JsonResponse(day_payload(when))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_entry(request):"""

ADD_WAS = """    messages.success(request, 'Added "%s" to %s'
                     % (recipe.recipe_name, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))"""
ADD_NOW = """    # THE DIALOG WANTS THE DAY BACK, NOT A REDIRECT - PS-1,
    # 19 Oct 2026. The form post is unchanged and still redirects;
    # this branch exists for the picker, which stays open.
    if request.POST.get('json'):
        return JsonResponse(day_payload(when))

    messages.success(request, 'Added "%s" to %s'
                     % (recipe.recipe_name, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))"""

REM_WAS = """    when = entry.date
    what = entry.recipe.recipe_name if entry.recipe else (entry.note or 'Meal')
    entry.delete()
    messages.success(request, 'Removed "%s" from %s'
                     % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))"""
REM_NOW = """    when = entry.date
    what = entry.recipe.recipe_name if entry.recipe else (entry.note or 'Meal')
    entry.delete()

    # AND THE SAME FOR REMOVE - PS-1, 19 Oct 2026. The strip in the
    # picker removes in place, which is the undo a mis-click needs.
    if request.POST.get('json'):
        return JsonResponse(day_payload(when))

    messages.success(request, 'Removed "%s" from %s'
                     % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))"""

URL_WAS = """    path('meal_plans/move/', views.move_meal_entry, name='move_meal_entry'),"""
URL_NOW = """    path('meal_plans/move/', views.move_meal_entry, name='move_meal_entry'),
    # PS-1, 19 Oct 2026 - what is on one day, for the picker's strip.
    path('meal_plans/day_entries/', views.meal_day_entries,
         name='meal_day_entries'),"""


# ====================================================== THE DIALOG
#
# THE SERVINGS FIELD GOES. Demetri: "I also don't need the servings
# right now. When I add a recipe, it must just add the standard
# servings for that recipe." Which is what a blank box already did -
# C19's own note says so - so the behaviour is unchanged and only the
# field disappears.
SERV_WAS = """                    <div class="form-group">
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
"""
SERV_NOW = """                    {# THE SERVINGS FIELD WAS HERE - PS-1, 19 Oct 2026.   #}
                    {#                                                     #}
                    {# Demetri: "I also don't need the servings right now. #}
                    {# When I add a recipe, it must just add the standard  #}
                    {# servings for that recipe."                          #}
                    {#                                                     #}
                    {# WHICH IS WHAT A BLANK BOX ALREADY DID. C19's own    #}
                    {# note above said so - "Blank uses the recipe's own   #}
                    {# yield" - so nothing about the BEHAVIOUR changes      #}
                    {# here. add_meal_entry still falls back to the         #}
                    {# recipe's yield, then the household size, then 4.     #}
                    {# The day's stepper adjusts it afterwards and saves    #}
                    {# on press: one click after, rather than a field       #}
                    {# before, every time.                                  #}

                    {# ---------------- WHAT IS ON THIS DAY NOW - PS-1 #}
                    {# A MIS-CLICK IS A REAL ROW THE MOMENT IT HAPPENS, #}
                    {# because there is no Add Meal to think twice      #}
                    {# before. So the dialog shows the day and lets you #}
                    {# take anything off it in place. Without this, the #}
                    {# round should not be made at all.                 #}
                    <div class="picker-day" id="pickerDay" hidden>
                        <div class="picker-day-head">
                            <strong>On <span id="pickerDayLabel"></span></strong>
                        </div>
                        <ul class="picker-day-list" id="pickerDayList"></ul>
                    </div>
"""

FOOT_WAS = """                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary" id="pickerAdd" disabled>
                        <i class="fas fa-plus"></i> Add Meal
                    </button>
                </div>"""
FOOT_NOW = """                <div class="modal-footer">
                    {# NO CANCEL - PS-1, 19 Oct 2026. There is nothing to #}
                    {# cancel when every action has already happened, and #}
                    {# a Cancel that did not undo them would be a lie.    #}
                    {# The strip above is where you undo.                 #}
                    <span class="picker-hint" id="pickerHint">Click a recipe to add it.</span>
                    <button type="button" class="btn action-primary" id="pickerDone"
                            onclick="closePicker()">Done</button>
                </div>"""

CSS_WAS = """   three times shorter than the column it replaces. */
#pickerList {"""
OPTRULE_WAS = """.recipe-option {
    display: flex;"""
OPTRULE_NOW = """.recipe-option {
    /* RELATIVE, so PS-1's added-count badge has something to sit in.
       On MW-1's own rule rather than in a second one earlier in the
       file - see the note beside .pf-added. */
    position: relative;
    display: flex;"""

CSS_NOW = """   three times shorter than the column it replaces. */

/* WHAT IS ON THIS DAY - PS-1, 19 Oct 2026. The strip that makes
   adding-on-click safe: every row it created, removable in place. */
.picker-day {
    margin-top: 14px;
    padding: 10px 12px;
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
}
.picker-day-head { font-size: 13px; color: var(--alv-ink); }
.picker-day-list { list-style: none; margin: 6px 0 0; padding: 0; }
.picker-day-row {
    display: flex;
    align-items: center;
    gap: 8px;
    /* 44px, because taking a mis-click off again is the one thing
       this dialog must not make fiddly. */
    min-height: 44px;
    padding: 2px 0;
    font-size: 14px;
    color: var(--alv-ink);
    border-bottom: 1px solid var(--alv-line-soft);
}
.picker-day-row:last-child { border-bottom: none; }
.picker-day-name { flex: 1; min-width: 0; }
.picker-day-note { color: var(--alv-ink-soft); font-size: 12px; }
.picker-day-drop {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border: 0;
    background: transparent;
    color: var(--alv-bad-ink);
    cursor: pointer;
    border-radius: var(--alv-radius-sm);
}
.picker-day-drop:hover { background: var(--alv-bad-soft); }
.picker-hint {
    margin-right: auto;
    font-size: 13px;
    color: var(--alv-ink-soft);
}
/* ADDED, AND HOW MANY TIMES - PS-1. A card that has been added twice
   is two helpings, not an error, so the card says the number.

   THE POSITIONING GOES ON MW-1's OWN RULE, further down, rather than
   in a second `.recipe-option {` up here. A second rule for the same
   selector is not wrong CSS, but test_picker_grid reads MW-1's card
   by splitting the stylesheet on the FIRST `.recipe-option {` - and a
   new one earlier in the file hid it. One rule per selector costs
   nothing and leaves nothing to trip over. */
.pf-added {
    position: absolute;
    top: 6px;
    right: 6px;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    border-radius: 10px;
    background: var(--alv-good);
    color: var(--alv-on-accent);
    font-size: 11px;
    font-weight: 600;
    line-height: 20px;
    text-align: center;
}
#pickerList {"""


# ============================================================ THE SCRIPT
PICK_WAS = """function pickRecipe(el) {
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    el.classList.add('selected');
    document.getElementById('pickerRecipeId').value = el.dataset.recipeId;
    // C19 again: the recipe's own yield, not a 4 and not the last one.
    var box = document.getElementById('pickerServings');
    if (box && !box.value) { box.value = el.dataset.recipeServings || ''; }
    document.getElementById('pickerAdd').disabled = false;
}"""
PICK_NOW = """// CLICK IS THE ADD - PS-1, 19 Oct 2026.
//
// There is no Add Meal button any more, so this is not a selection:
// the row exists the moment you let go of the mouse. SELECTION IS
// GONE WITH IT - a card that is "selected" and a card that has been
// ADDED are different things, and keeping both would say neither.
// The card shows a COUNT instead, because a second click is a second
// helping rather than a mistake.
var pickerBusy = false;

function pickAdd(el) {
    if (pickerBusy) { return; }
    var date = document.getElementById('pickerDate').value;
    if (!date) { return; }
    pickerBusy = true;
    el.classList.add('is-adding');

    var body = new URLSearchParams();
    body.append('recipe_id', el.dataset.recipeId);
    body.append('date', date);
    // NO SERVINGS. Left out entirely rather than sent empty, so the
    // server takes the branch it already had: the recipe's own yield,
    // then the household size, then 4.
    body.append('json', '1');
    body.append('view', plannerView);
    body.append('csrfmiddlewaretoken', '{{ csrf_token }}');

    fetch('{% url "add_meal_entry" %}', {
        method: 'POST', credentials: 'same-origin', body: body
    })
        .then(function (r) {
            if (!r.ok) { throw new Error(r.status); }
            return r.json();
        })
        .then(function (d) { pickerDirty = true; pdDraw(d); })
        .catch(function () {
            var hint = document.getElementById('pickerHint');
            if (hint) {
                hint.textContent = 'Could not add that. Try again.';
            }
        })
        .then(function () {
            pickerBusy = false;
            el.classList.remove('is-adding');
        });
}

// WHAT IS ON THE DAY, DRAWN - PS-1. One function for the strip and
// the counts, so the two cannot disagree about what was added.
var pickerDirty = false;

function pdDraw(d) {
    var wrap = document.getElementById('pickerDay');
    var list = document.getElementById('pickerDayList');
    var label = document.getElementById('pickerDayLabel');
    if (!wrap || !list) { return; }
    var rows = (d && d.entries) || [];
    // KEPT, because the cards are destroyed and rebuilt every time a
    // filter moves and the badges have to be put back from something.
    window.pdLast = d;

    if (label) { label.textContent = (d && d.label) || ''; }
    wrap.hidden = rows.length === 0;
    while (list.firstChild) { list.removeChild(list.firstChild); }

    var counts = {};
    rows.forEach(function (e) {
        if (e.recipe_id) {
            counts[e.recipe_id] = (counts[e.recipe_id] || 0) + 1;
        }

        var li = document.createElement('li');
        li.className = 'picker-day-row';

        // BUILT, NOT INTERPOLATED. A recipe called Ben & Jerry's goes
        // into textContent intact and into innerHTML as a hole -
        // PK-1's note, and SL-4's lesson about alert().
        var name = document.createElement('span');
        name.className = 'picker-day-name';
        name.textContent = e.name;
        if (e.leftover) {
            var tag = document.createElement('span');
            tag.className = 'picker-day-note';
            tag.textContent = ' leftovers';
            name.appendChild(tag);
        }
        li.appendChild(name);

        var drop = document.createElement('button');
        drop.type = 'button';
        drop.className = 'picker-day-drop';
        drop.title = 'Take off this day';
        drop.setAttribute('aria-label', 'Take ' + e.name +
                          ' off this day');
        drop.innerHTML = '<i class="fas fa-times"></i>';
        drop.onclick = function () { pickDrop(e.id); };
        li.appendChild(drop);

        list.appendChild(li);
    });

    // AND THE CARDS SAY HOW MANY. Two of something is two helpings.
    document.querySelectorAll('.recipe-option').forEach(function (card) {
        var had = card.querySelector('.pf-added');
        if (had) { had.remove(); }
        var n = counts[card.dataset.recipeId];
        if (n) {
            var b = document.createElement('span');
            b.className = 'pf-added';
            b.textContent = n > 1 ? ('x' + n) : '\\u2713';
            card.appendChild(b);
        }
    });

    var hint = document.getElementById('pickerHint');
    if (hint) {
        hint.textContent = rows.length
            ? (rows.length + ' on this day')
            : 'Click a recipe to add it.';
    }
}

function pickDrop(entryId) {
    if (pickerBusy) { return; }
    pickerBusy = true;
    var body = new URLSearchParams();
    body.append('meal_entry_id', entryId);
    body.append('json', '1');
    body.append('view', plannerView);
    body.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    fetch('{% url "remove_meal_entry" %}', {
        method: 'POST', credentials: 'same-origin', body: body
    })
        .then(function (r) {
            if (!r.ok) { throw new Error(r.status); }
            return r.json();
        })
        .then(function (d) { pickerDirty = true; pdDraw(d); })
        .catch(function () {
            var hint = document.getElementById('pickerHint');
            if (hint) {
                hint.textContent = 'Could not remove that. Try again.';
            }
        })
        .then(function () { pickerBusy = false; });
}

// DONE RELOADS, AND ONLY IF SOMETHING HAPPENED - PS-1.
//
// The calendar behind the dialog is server-rendered and now out of
// date, so closing has to fetch it again. Opening the picker and
// closing it without adding anything should not cost a page load,
// which is what `pickerDirty` is for. The x and the backdrop go
// through the same path, because a dialog that only updates the page
// when you press the right button is a dialog that lies half the
// time.
function closePicker() {
    $('#pickerModal').modal('hide');
}"""

OPEN_WAS = """    document.getElementById('pickerRecipeId').value = '';
    // C19: the box is EMPTIED on every open. It used to arrive holding
    // whatever the last recipe was set to.
    document.getElementById('pickerServings').value = '';
    document.getElementById('pickerSearch').value = '';"""
OPEN_NOW = """    document.getElementById('pickerRecipeId').value = '';
    document.getElementById('pickerSearch').value = '';

    // WHAT IS ALREADY ON THIS DAY - PS-1, 19 Oct 2026. The strip
    // shows the WHOLE day, not just what this visit added, because
    // "what is on Saturday" is the question being asked.
    pickerDirty = false;
    pdDraw({ entries: [], label: dayName });
    fetch('{% url "meal_day_entries" %}?date=' +
          encodeURIComponent(dateStr), {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d) { pdDraw(d); } })
        .catch(function () { /* the strip stays empty; adds still work */ });"""

OPENEND_WAS = """    pfClear(true);
    document.getElementById('pickerAdd').disabled = true;
    filterPicker();
    $('#pickerModal').modal('show');
}"""
OPENEND_NOW = """    pfClear(true);
    filterPicker();
    $('#pickerModal').modal('show');
}

// THE CALENDAR BEHIND IS STALE ONCE ANYTHING WAS ADDED - PS-1. Bound
// to the dialog's own hide event rather than to the Done button, so
// the x and the backdrop behave identically.
//
// WRAPPED AND GUARDED, BECAUSE NO TOP-LEVEL jQUERY. This was written
// as `$(function () { ... })` and that is a house rule broken: if
// jQuery has not loaded, the call throws and EVERYTHING AFTER IT IN
// THE SAME SCRIPT BLOCK never registers - which took PF-2's
// outside-click handler with it and left its filter menus unable to
// close. test_pick_filter caught it; nothing in the source could
// have. An IIFE with a guard cannot take its neighbours down.
//
// It still needs jQuery, because hidden.bs.modal is a jQuery event
// and addEventListener never sees it.
(function () {
    var el = document.getElementById('pickerModal');
    if (!el || !window.jQuery) { return; }
    window.jQuery(el).on('hidden.bs.modal', function () {
        if (pickerDirty) { window.location.reload(); }
    });
})();"""

CARD_WAS = """        card.onclick = function () { pickRecipe(card); };"""
CARD_NOW = """        card.onclick = function () { pickAdd(card); };"""

DRAWEND_WAS = """    if (empty) {
        empty.hidden = (d.rows || []).length !== 0;"""
DRAWEND_NOW = """    // THE COUNTS SURVIVE A REFILTER - PS-1, 19 Oct 2026. The cards
    // are rebuilt every time a filter moves, so the badges have to be
    // put back from the day we already hold.
    if (window.pdLast) { pdDraw(window.pdLast); }

    if (empty) {
        empty.hidden = (d.rows || []).length !== 0;"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="dc-tags"'; What = 'DC-1: the Day card is one line and the width carries the recipe facts - it was four lines using 37% of the row' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="dc-tags"'; What = 'DC-1: the Day card is one line and the width carries the recipe facts - it was four lines using 37% of the row' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def day_payload('; What = 'PS-1: ONE description of what is on a day, asked by the dialog on open, on every add and on every remove, so the strip cannot drift from the calendar' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pickAdd('; What = 'PS-1: clicking a recipe ADDS it - twenty actions to put four things on a Saturday became seven, because the filters stop being forgotten between adds' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerDayList"'; What = 'PS-1: and the dialog shows the day it is adding to, each row removable - without it a mis-click would be a row you could not see' },"""

SUITE_WAS = """    'test_day_card.py'
)"""
SUITE_NOW = """    'test_day_card.py',
    # PS-1, 19 Oct 2026 - the picker adds on click and stays open.
    # Section 3 drives it in a browser: four adds, one open, and the
    # filters still set at the end.
    'test_picker_stays.py'
)"""

TREE_WAS = """    # DC-1, 19 Oct 2026 - the Day card on one line, with the tags the
    # planner was already fetching and never showing.
    'test_day_card.py',
]"""
TREE_NOW = """    # DC-1, 19 Oct 2026 - the Day card on one line, with the tags the
    # planner was already fetching and never showing.
    'test_day_card.py',
    # PS-1, 19 Oct 2026 - the picker adds on click and stays open,
    # and shows the day so a mis-click can be undone.
    'test_picker_stays.py',
]"""

RD_WAS = """    '.bak_daycard',
]"""
RD_NOW = """    '.bak_daycard',
    # PS-1, 19 Oct 2026 - the picker adds on click and stays open.
    '.bak_pickerstays',
]"""

WD_WAS = """CONVERTED_N = 125   # DC-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 126   # PS-1, 19 Oct 2026 - this round own suite   # (was 125)"""

# ---- AND THE FOOTER IT MEASURES AGAINST IS CALLED Done NOW.
#
# PK-1 measures the Add Meal button's top to prove the cards have not
# pushed the footer below the fold - the fault MW-1's work caused and
# PK-1 fixed. The CLAIM is untouched by this round; only the button's
# name changed, because there is nothing to press to add any more.
# Left alone it reads null and raises.
PKFOLD_WAS = """                const add = document.getElementById('pickerAdd');"""
PKFOLD_NOW = """                // Done, not Add Meal - PS-1, 19 Oct 2026. Same
                // button, same claim: the footer must stay on the
                // screen. Only the errand changed.
                const add = document.getElementById('pickerDone');"""
PKFOLD2_WAS = """               'so Add Meal stays reachable' % m['listH'], m['listH'])
            ok(m['addTop'] < VH,
               '  and the Add Meal button is ON the screen at %dpx'
               % m['addTop'], (m['addTop'], VH))"""
PKFOLD2_NOW = """               'so Done stays reachable' % m['listH'], m['listH'])
            ok(m['addTop'] < VH,
               '  and the Done button is ON the screen at %dpx'
               % m['addTop'], (m['addTop'], VH))"""

PKG = 'test_picker_grid.py'

# ================= AND PK-1's SELECTION CLAIMS RETIRE WITH SELECTION
#
# test_picker_grid drives `pickRecipe()` and asks that the card ends
# up `.selected` with the Add Meal button armed. THIS ROUND DELETED
# ALL THREE, so the claim raises ReferenceError rather than failing -
# and a crash blocks a push as hard as a failure while saying less
# about why.
#
# A SUITE RETIRES WITH THE THING IT JUDGED, and so does a claim. PK-1
# was right when it was written: Demetri could select a card and
# nothing told him he had. Selection is gone - a card that has been
# ADDED and a card that is SELECTED are different things, and keeping
# both would have said neither - so the claims about it go, and the
# comment says where the question is answered now.
#
# The first attempt at this rewrote PK-1's harness to drive PS-1's
# behaviour instead. That is a worse answer: test_picker_stays
# already drives exactly this, with a stubbed fetch it was built for,
# and a second copy in somebody else's suite is a second thing to
# keep in step.
PKG_WAS = """        # ---- AND THE THING HE ACTUALLY REPORTED
        pg.evaluate(DRAW, ROWS)
        pg.evaluate(\"\"\"() => {
            pickRecipe(document.querySelector('.recipe-option'));
        }\"\"\")
        sel = pg.evaluate(\"\"\"() => {
            const o = document.querySelector('.recipe-option');
            const st = getComputedStyle(o);
            return {cls: o.className, shadow: st.boxShadow,
                    bg: st.backgroundColor, border: st.borderColor,
                    add: !document.getElementById('pickerAdd').disabled};
        }\"\"\")
        ok('selected' in sel['cls'],
           'CLICKING A CARD SELECTS IT', sel['cls'])
        ok(sel['add'], '  and arms the Add Meal button', sel['add'])
        # THE WHOLE POINT. He could select; nothing TOLD him he had.
        ok(sel['shadow'] not in ('none', ''),
           '  AND IT IS VISIBLE - a ring, %s' % sel['shadow'],
           sel['shadow'])
        ok(sel['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent'),
           '  and a tint, %s - two signals, not one' % sel['bg'],
           sel['bg'])"""
PKG_NOW = """        # ---- AND THE THING HE ACTUALLY REPORTED
        #
        # RETIRED BY PS-1, 19 Oct 2026, with the thing it judged.
        #
        # This drove pickRecipe() and asked that the card ended up
        # `.selected` with the Add Meal button armed. PS-1 deleted all
        # three: clicking a card ADDS it now, there is no selection to
        # show and no button to arm.
        #
        # PK-1's point was that pressing a card must visibly do
        # something, and it still holds - it is asked in
        # test_picker_stays, which drives four clicks against a
        # stubbed fetch and reads the strip, the badges and the four
        # posts that resulted. The CSS claims below stay here, because
        # the card itself is still PK-1's.
        pg.evaluate(DRAW, ROWS)
        sel = pg.evaluate(\"\"\"() => {
            const o = document.querySelector('.recipe-option');
            if (!o) { return {cls: '', shadow: '', bg: '', border: ''}; }
            const st = getComputedStyle(o);
            return {cls: o.className, shadow: st.boxShadow,
                    bg: st.backgroundColor, border: st.borderColor};
        }\"\"\")
        ok(not pg.evaluate("() => typeof pickRecipe === 'function'"),
           'pickRecipe is gone - PS-1 made the click an ADD, so there '
           'is no selection left to judge')
        ok(not pg.evaluate(
               "() => !!document.getElementById('pickerAdd')"),
           '  and so is the Add Meal button it armed')
        ok(sel['cls'] and 'selected' not in sel['cls'],
           '  and a card carries no selected state, because there is '
           'no selection', sel['cls'])"""

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
    raise SystemExit('PS-1 REFUSED: %s' % msg)


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
    pt = os.path.join(root, TPL)
    v = read(pv)
    t = read(pt)

    if 'def day_payload(' in v:
        print('PS-1  already applied - the picker adds on click.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    markup = T.code_only(t)
    if 'id="pickerAdd"' not in markup:
        refuse('%s has no Add Meal button, so there is nothing to '
               'remove - PK-1 and PF-2 go first' % TPL)
    if 'id="pickerServings"' not in markup:
        refuse('%s has no Servings field' % TPL)
    if 'planner_back(' not in T.python_code_only(v, payloads=True):
        refuse('%s has no planner_back - PB-2 goes first' % VIEW)

    v = swap(v, PAYLOAD_WAS, PAYLOAD_NOW, '%s (the day, as JSON)' % VIEW)
    v = swap(v, ADD_WAS, ADD_NOW, '%s (add answers in JSON)' % VIEW)
    v = swap(v, REM_WAS, REM_NOW, '%s (remove answers in JSON)' % VIEW)
    out[pv] = v

    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    t = swap(t, SERV_WAS, SERV_NOW, '%s (the servings field)' % TPL)
    t = swap(t, FOOT_WAS, FOOT_NOW, '%s (the footer)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the strip rules)' % TPL)
    t = swap(t, OPTRULE_WAS, OPTRULE_NOW, '%s (the card)' % TPL)
    t = swap(t, PICK_WAS, PICK_NOW, '%s (click is the add)' % TPL)
    t = swap(t, OPEN_WAS, OPEN_NOW, '%s (what is on the day)' % TPL)
    t = swap(t, OPENEND_WAS, OPENEND_NOW, '%s (the reload)' % TPL)
    t = swap(t, CARD_WAS, CARD_NOW, '%s (the card)' % TPL)
    t = swap(t, DRAWEND_WAS, DRAWEND_NOW, '%s (the badges)' % TPL)
    out[pt] = t

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

    ppk = os.path.join(root, PKG)
    pk = read(ppk)
    pk = swap(pk, PKG_WAS, PKG_NOW, "%s (PK-1's selection claims)" % PKG)
    pk = swap(pk, PKFOLD_WAS, PKFOLD_NOW, '%s (the footer it measures)'
              % PKG)
    pk = swap(pk, PKFOLD2_WAS, PKFOLD2_NOW, '%s (and what it calls it)'
              % PKG)
    out[ppk] = pk

    ppk = os.path.join(root, PKG)
    pk = read(ppk)
    pk = swap(pk, PKG_WAS, PKG_NOW, "%s (PK-1's selection claims)" % PKG)
    pk = swap(pk, PKFOLD_WAS, PKFOLD_NOW, '%s (the footer it measures)'
              % PKG)
    pk = swap(pk, PKFOLD2_WAS, PKFOLD2_NOW, '%s (and what it calls it)'
              % PKG)
    out[ppk] = pk

    # ---- THE GATES
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nv = T.python_code_only(out[pv], payloads=True)
    nt = T.code_only(out[pt])

    # ONE DESCRIPTION OF A DAY, asked by three endpoints. Three
    # descriptions would let the strip disagree with the calendar.
    # THE CALLS, NOT THE DECLARATION. `day_payload(when)` matches
    # `def day_payload(when):` too, so this counted 4 and refused the
    # round over the function it had just written. PB-2 made exactly
    # this mistake an hour earlier in the same push, with
    # planner_back. A name is not a use of it.
    n_calls = len(re.findall(r'(?<!def )day_payload\(when\)', nv))
    if n_calls != 3:
        refuse('%s calls day_payload %d time(s), expected 3 - the '
               'dialog opening, an add and a remove' % (VIEW, n_calls))

    # THE FORM POST IS UNCHANGED. Other things on this page still post
    # normally, and a round that replaced the redirect would break the
    # Move dialog and the note form.
    for endpoint in ('def add_meal_entry', 'def remove_meal_entry'):
        body = nv.split(endpoint, 1)[1]
        body = re.split(r'\n@|\ndef ', body)[0]
        if 'planner_back(' not in body:
            refuse('%s: %s no longer redirects. The JSON branch is for '
                   'the picker; every other form on this page still '
                   'posts and expects to be sent back.'
                   % (VIEW, endpoint))

    # THE SERVINGS FIELD IS GONE, AND SO IS ADD MEAL.
    for dead, why in (
            ('id="pickerServings"', 'the servings field'),
            ('id="pickerAdd"', 'the Add Meal button')):
        if dead in nt:
            refuse('%s still carries %s' % (TPL, why))

    # AND THE STRIP IS THERE, because without it a mis-click is a row
    # you cannot see. This round should not exist without it.
    if 'id="pickerDayList"' not in nt:
        refuse('%s has no strip showing the day. Adding on click '
               'without one makes a mis-click into a row nobody can '
               'undo from here.' % TPL)
    if 'function pickDrop(' not in nt:
        refuse('%s: the strip has no remove' % TPL)

    # NOTHING IS INTERPOLATED INTO MARKUP. A recipe called
    # Ben & Jerry's is a hole in innerHTML and a name in textContent.
    strip = nt.split('function pdDraw(', 1)[1].split('function pickDrop',
                                                     1)[0]
    if '.innerHTML = ' in strip and 'e.name' in \
            strip.split('.innerHTML = ', 1)[1][:200]:
        refuse('%s: a recipe name reaches innerHTML in the strip' % TPL)

    # C19 STILL HOLDS ON OPEN. The filters survive WHILE the dialog is
    # open - that is the round - but they still reset when it opens.
    opener = nt.split('function openPicker(', 1)[1][:1800]
    if 'pfClear(true)' not in opener:
        refuse('%s: openPicker no longer clears the filters. C19 is '
               'unchanged by this round: they survive while the dialog '
               'is open, and still reset when it opens.' % TPL)

    if CHECK:
        print('PS-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    # EVERY FILE THIS ROUND MEANT TO TOUCH, WRITTEN. A round that
    # half-applies is the 17 October failure; a round that does not
    # apply at all and says nothing is this one, 19 October, caught
    # only because stage_round found no backups to enumerate.
    for k in out:
        if not os.path.exists(k):
            refuse('%s was never written' % os.path.relpath(k, root))

    print('PS-1  applied - the picker adds on click and stays open.')
    print('      The Servings field is gone; the day is shown instead.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
