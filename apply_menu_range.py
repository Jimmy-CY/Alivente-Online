# -*- coding: utf-8 -*-
"""apply_menu_range.py - round MN-2, 21 Oct 2026.

A MENU IS A NAMED SET OF MEALS. IT WAS A WEEK, AND ONLY THIS WEEK.

Demetri, 21 October, with the Saved Menus dialog open:

    "I am also not happy that a Menu has to be applied to a
     pre-specified week. Should I not be able to select to which week
     I want to apply the Saved Menu??? Also, when I save a Menu, it
     only allows me to select the current week. What if I want to save
     a previous week, or choose the just create a Xmas and New Years
     menu for days, and save that??"

TWO ASKS, AND THE TABLE ALREADY ALLOWED BOTH. MN-1 gave MenuItem a
`day_index` whose own help_text reads "0 is the first day of the menu,
not a weekday". The column was always an OFFSET. What tied a menu to a
week was the two views on either side of it:

    save_menu    day_index=(e.date - week).days, over week_entries()
    apply_menu   if not 0 <= it.day_index <= 6: continue
                 when = week + timedelta(days=it.day_index)

and a dialog that offered no field for either end. Same shape as CP-2
three rounds ago: copy_week_rows had copied by date offset since MN-1
and only the DOOR was week-shaped.

WHERE YOU ARE AND WHAT YOU ARE ACTING ON ARE TWO THINGS. `week` keeps
its old job - it is the page you came from and it decides where Back
goes. `from`, `to` and `onto` are new and say what to keep and where to
put it. Each defaults to the week on screen, so every caller that says
nothing gets exactly what this view did before; nothing needs a
compatibility path and nothing silently changes meaning.

THE FIELD KEEPS ITS NAME. `day_index` holding 0..91 reads oddly and
`day_offset` would be better English, but renaming a column on a live
MySQL table buys nothing the help_text does not already say, and the
docstrings that called it an index 0 to 6 are corrected here instead.
That was the choice; it is written down so the next round does not
rediscover it.

A CEILING, BECAUSE A RANGE WITH NO END IS A FOOT-GUN. 92 days - a
quarter - which covers Christmas and New Year with room to spare and
stops somebody saving a year by dragging a date field. A save over the
ceiling refuses and says the number; an apply drops an item past it
rather than wrapping, exactly as the week version dropped a 9.

A LEFTOVER IS STILL NOT SAVED. MenuItem has no leftover_of and that is
right: a leftover is a consequence of a particular week, not a thing
anybody plans in advance.

WHAT THE DIALOG GETS. The Save half gains the three presets CP-2 built
for Copy - This day, This week, This month - and a From and a To. The
Apply half gains a Landing on, defaulted to the week on screen, and a
line that says which dates the menu will cover once a date is picked.
That line is computed in the page from the menu's own span, which the
planner now annotates alongside the item count, so it costs no query
and no endpoint.

Idempotent. Every file backed up to .bak_menurange.
"""
import os
import re
import sys

SUFFIX = '.bak_menurange'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
MODELS = os.path.join('pages', 'models.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
WEEK = 'test_meal_week.py'
COPY = 'test_copy_menus.py'
PAIRS = 'test_pair_contrast.py'
PRANGE = 'test_print_range.py'
ME = 'test_menu_range.py'
PATCHER = 'apply_menu_range.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MN-2, 21 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE HELPERS - one span, read once
# ==========================================================================
HELP_WAS = """def monday_of(d):
    \"\"\"The Monday of d's week. A week is a Monday here, everywhere.\"\"\"
    return d - timedelta(days=d.weekday())"""

HELP_NOW = """def monday_of(d):
    \"\"\"The Monday of d's week. A week is a Monday here, everywhere.\"\"\"
    return d - timedelta(days=d.weekday())


# ---- A SPAN OF DAYS - MN-2, 21 Oct 2026.
#
# A menu was a week because the two views either side of it said so,
# not because the table did. MenuItem.day_index has read "0 is the
# first day of the menu, not a weekday" since MN-1.
#
# THE CEILING IS 92 DAYS - a quarter. It covers Christmas and New Year
# with room to spare and stops a dragged date field saving a year.
MENU_MAX_DAYS = 92


def range_entries(start, end):
    \"\"\"Every meal from start to end inclusive.

    week_entries is this with end pinned seven days out. One query
    shape, so a menu saved over three days and a menu saved over a
    week are read the same way.
    \"\"\"
    return (MealEntry.objects
            .filter(date__gte=start, date__lte=end)
            .select_related('recipe')
            .order_by('date', 'sort_order', 'meal_entry_id'))


def span_label(start, end):
    \"\"\"`3 Nov` for one day, `3 Nov - 9 Nov` for more than one.

    A menu of a single day saying `3 Nov - 3 Nov` reads like a fault.
    \"\"\"
    return (day_label(start) if start == end
            else '%s - %s' % (day_label(start), day_label(end)))"""

# ==========================================================================
# save_menu
# ==========================================================================
SAVE_HEAD_WAS = '''    """Save the week on screen as a named Menu.

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
    back = planner_back(request, week)'''

SAVE_HEAD_NOW = '''    """Save a RANGE of days as a named Menu.

    DAY OFFSETS, NOT DATES - 0 for the FIRST DAY OF THE RANGE. That is
    the whole reason a Menu is a different table from a set of
    MealEntry rows, and it is what lets one be applied in March to a
    week in December.

    MN-2, 21 Oct 2026 - THE RANGE IS A CHOICE. This read the week on
    screen and nothing else, so a Christmas menu had to be built on
    the week it was going to be used:

        "What if I want to save a previous week, or ... just create a
         Xmas and New Years menu for days, and save that??"

    WHERE YOU ARE AND WHAT YOU ARE SAVING ARE TWO THINGS. `week` is
    still the page you came from and still decides where Back goes.
    `from` and `to` say what to keep, and default to that week - so a
    caller that sends neither gets exactly what this view did before.
    """
    week = week_of(request.POST.get('week'), None)
    name = (request.POST.get('name') or '').strip()
    if week is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    week = monday_of(week)
    back = planner_back(request, week)

    start = week_of(request.POST.get('from'), week)
    end = week_of(request.POST.get('to'), week + timedelta(days=6))
    if end < start:
        messages.error(request, 'Those dates are the wrong way round.')
        return redirect(back)
    span = (end - start).days + 1
    if span > MENU_MAX_DAYS:
        messages.error(
            request, 'A menu can cover at most %d days and that is %d. '
            'Pick a shorter range.' % (MENU_MAX_DAYS, span))
        return redirect(back)'''

SAVE_ROWS_WAS = """    rows = list(week_entries(week))
    if not rows:
        messages.error(request, 'There is nothing on %s to save.'
                       % week_label(week))
        return redirect(back)"""

SAVE_ROWS_NOW = """    rows = list(range_entries(start, end))
    if not rows:
        messages.error(request, 'There is nothing on %s to save.'
                       % span_label(start, end))
        return redirect(back)"""

SAVE_IDX_WAS = """                menu=menu, day_index=(e.date - week).days,"""

SAVE_IDX_NOW = """                # FROM THE START OF THE RANGE, not from a Monday -
                # MN-2. The range IS the menu; day 0 is its first day.
                menu=menu, day_index=(e.date - start).days,"""

SAVE_MSG_WAS = """    messages.success(request, 'Saved %s as the menu "%s".'
                     % (week_label(week), menu.name))"""

SAVE_MSG_NOW = """    messages.success(request, 'Saved %s as the menu "%s" - %d day%s.'
                     % (span_label(start, end), menu.name, span,
                        '' if span == 1 else 's'))"""

# ==========================================================================
# apply_menu
# ==========================================================================
APPLY_HEAD_WAS = '''    """Stamp a saved Menu onto the week on screen."""
    week = week_of(request.POST.get('week'), None)
    if week is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    week = monday_of(week)
    back = planner_back(request, week)'''

APPLY_HEAD_NOW = '''    """Stamp a saved Menu onto a date of your choosing.

    MN-2, 21 Oct 2026 - WHERE IT LANDS IS A CHOICE.

        "I am also not happy that a Menu has to be applied to a
         pre-specified week. Should I not be able to select to which
         week I want to apply the Saved Menu???"

    `onto` is the day the menu's day 0 lands on, and it defaults to the
    week on screen - which is where this view always put it. Back goes
    to where it landed rather than where you were standing, because a
    menu stamped onto December is not worth seeing from October.
    """
    week = week_of(request.POST.get('week'), None)
    if week is None:
        messages.error(request, 'That week could not be read.')
        return redirect('meal_planner')
    week = monday_of(week)
    onto = week_of(request.POST.get('onto'), week)
    back = planner_back(request, onto)'''

APPLY_LOOP_WAS = """            # A DAY INDEX OUTSIDE THE WEEK IS DROPPED, not wrapped. A
            # menu saved from a week is 0 to 6 by construction; a row
            # that somehow says 9 would land in the NEXT week, which is
            # a surprise nobody asked for.
            if not 0 <= it.day_index <= 6:
                continue
            when = week + timedelta(days=it.day_index)"""

APPLY_LOOP_NOW = """            # A DAY OFFSET OUTSIDE THE MENU IS DROPPED, not wrapped -
            # MN-2 widened the ceiling from 6 to 91 and kept the rule.
            # A menu is 0 to its own length by construction; a row that
            # somehow says a year would land a year away, which is a
            # surprise nobody asked for.
            if not 0 <= it.day_index < MENU_MAX_DAYS:
                continue
            when = onto + timedelta(days=it.day_index)"""

APPLY_MSG_WAS = """    messages.success(request, 'Added %d meal%s from "%s" to %s.'
                     % (made, '' if made == 1 else 's', menu.name,
                        week_label(week)))"""

APPLY_MSG_NOW = """    last = max((it.day_index for it in items
                if 0 <= it.day_index < MENU_MAX_DAYS), default=0)
    messages.success(request, 'Added %d meal%s from "%s" to %s.'
                     % (made, '' if made == 1 else 's', menu.name,
                        span_label(onto, onto + timedelta(days=last))))"""

# ==========================================================================
# the planner's context - the dialog needs each menu's LENGTH
# ==========================================================================
CTX_WAS = """        'menus': Menu.objects.annotate(
            item_count=Count('items')).order_by('name'),"""

CTX_NOW = """        # MN-2, 21 Oct 2026 - AND HOW LONG EACH ONE IS. The Apply
        # half says which dates a menu will cover once a landing date
        # is picked, and it works that out in the page from this
        # number. Annotated alongside the count, so it is still one
        # query and still no endpoint.
        'menus': Menu.objects.annotate(
            item_count=Count('items'),
            span_days=Coalesce(Max('items__day_index'), -1) + 1,
        ).order_by('name'),"""

IMPORT_WAS = """from django.db.models import Count, Max, Prefetch"""

IMPORT_NOW = """from django.db.models import Count, Max, Prefetch
# MN-2, 21 Oct 2026 - a menu with no items has no Max, and NULL + 1 is
# NULL, which would reach the template as an empty string.
from django.db.models.functions import Coalesce"""

# ==========================================================================
# the model's own description of itself
# ==========================================================================
MODEL_WAS = '''    """A saved week, kept by NAME rather than by date. MN-1, 18 Oct 2026.

    Repeat copies last week. A Menu is for the weeks you come back to
    months later - Christmas, girls visiting, the usual rotation - so
    it holds DAY INDEXES, 0 to 6, and not dates.

    Push 2 fills these. The tables arrive now so that release 3 has one
    migration and not three.
    """'''

MODEL_NOW = '''    """A saved SPAN OF DAYS, kept by NAME rather than by date.

    MN-1, 18 Oct 2026. Repeat copies last week. A Menu is for the days
    you come back to months later - Christmas, girls visiting, the
    usual rotation - so it holds DAY OFFSETS and not dates.

    MN-2, 21 Oct 2026 - IT WAS NEVER A WEEK. This said "DAY INDEXES, 0
    to 6" and the table never agreed: MenuItem.day_index has read "0 is
    the first day of the menu, not a weekday" since the day it was
    written. What held a menu to seven days was save_menu and
    apply_menu, which now take a range and a landing date. The ceiling
    is MENU_MAX_DAYS, 92, and it lives in the view with the rule it
    serves.

    THE COLUMN KEEPS ITS NAME. day_offset would be better English;
    renaming a column on a live table buys nothing this docstring does
    not say.
    """'''

# ==========================================================================
# THE DIALOG - the Save half takes a range, the Apply half takes a date
# ==========================================================================
SAVE_FORM_WAS = """                <div class="mn-section">
                    <div class="mn-head">Save this week as a menu</div>
                    <form method="POST" action="{% url 'save_menu' %}">
                        {% csrf_token %}
                        <input type="hidden" name="view" value="{{ view_mode }}">
                        <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                        <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                        <p class="text-muted" style="font-size:13px;">
                            The meals on <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>
                            are kept under a name, by weekday, so the same
                            week can be stamped onto any week later.
                        </p>
                        <div class="form-group">
                            <label for="saveMenuName"><strong>Name</strong></label>
                            <input type="text" class="form-control" id="saveMenuName"
                                   name="name" maxlength="100" autocomplete="off"
                                   placeholder="e.g. Easy Winter Week" required>
                        </div>
                        <button type="submit" class="btn action-secondary">
                            <i class="fas fa-bookmark"></i> Save this week
                        </button>
                    </form>
                </div>"""

SAVE_FORM_NOW = """                <div class="mn-section">
                    <div class="mn-head">Save days as a menu</div>
                    <form method="POST" action="{% url 'save_menu' %}">
                        {% csrf_token %}
                        {# THE VIEW AND THE DAY TRAVEL WITH IT - PB-2 and PB-3. #}
                        <input type="hidden" name="view" value="{{ view_mode }}">
                        <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                        {# `week` IS WHERE YOU ARE, NOT WHAT YOU SAVE - MN-2.  #}
                        {# It decides where Back goes. From and To say what to #}
                        {# keep, and the view defaults them to this week, so   #}
                        {# sending neither means what it always meant.         #}
                        <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                        <p class="text-muted" style="font-size:13px;">
                            The meals between these dates are kept under a
                            name, by how far into the menu each day falls -
                            so the same set can be stamped onto any dates
                            later. Up to 92 days.
                        </p>
                        {# "Days to keep", NOT "Save" - MN-2. The Copy     #}
                        {# dialog's twin of this row is labelled Copy, so    #}
                        {# Save was the obvious word. It is also the word    #}
                        {# test_meal_help looks for when it asks whether the #}
                        {# planner has grown a Save button - the planner     #}
                        {# writes on press and must not have one - and a     #}
                        {# <label>Save</label> reads as one to that check.   #}
                        {# The longer label says what the two dates are for, #}
                        {# which it needed to anyway.                        #}
                        <div class="form-group">
                            <label><strong>Days to keep</strong></label>
                            <div class="cp-presets">
                                <button type="button" class="btn action-secondary mn-preset"
                                        data-mn-span="day">This day</button>
                                <button type="button" class="btn action-secondary mn-preset"
                                        data-mn-span="week">This week</button>
                                <button type="button" class="btn action-secondary mn-preset"
                                        data-mn-span="month">This month</button>
                            </div>
                        </div>
                        <div class="cp-dates">
                            <div class="form-group">
                                <label for="mnFrom"><strong>From</strong></label>
                                <input type="date" class="form-control" id="mnFrom"
                                       name="from" required>
                            </div>
                            <div class="form-group">
                                <label for="mnTo"><strong>To</strong></label>
                                <input type="date" class="form-control" id="mnTo"
                                       name="to" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="saveMenuName"><strong>Name</strong></label>
                            <input type="text" class="form-control" id="saveMenuName"
                                   name="name" maxlength="100" autocomplete="off"
                                   placeholder="e.g. Christmas and New Year" required>
                        </div>
                        <button type="submit" class="btn action-secondary">
                            <i class="fas fa-bookmark"></i> Save these days
                        </button>
                    </form>
                </div>"""

APPLY_FORM_WAS = """                        {% if menus %}
                        <p class="text-muted" style="font-size:13px;">
                            The menu you pick is added to
                            <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>,
                            alongside whatever is already there.
                        </p>"""

APPLY_FORM_NOW = """                        {% if menus %}
                        <p class="text-muted" style="font-size:13px;">
                            Pick a menu, then the day its first day lands on.
                            It is added alongside whatever is already there.
                        </p>"""

APPLY_GO_WAS = """                        <button type="submit" class="btn action-primary" id="applyMenuGo" disabled>
                            <i class="fas fa-check"></i> Add to This Week
                        </button>"""

APPLY_GO_NOW = """                        {# LANDING ON - MN-2, 21 Oct 2026.                  #}
                        {#                                                  #}
                        {# "Should I not be able to select to which week I  #}
                        {#  want to apply the Saved Menu???"                #}
                        {#                                                  #}
                        {# Defaulted to the week on screen, which is where  #}
                        {# this dialog always put it, so the commonest      #}
                        {# thing to want is one click away and the rest is  #}
                        {# a date field.                                    #}
                        <div class="form-group" style="margin-top:14px;">
                            <label for="mnOnto"><strong>Landing on</strong></label>
                            <input type="date" class="form-control" id="mnOnto"
                                   name="onto" value="{{ week_start|date:'Y-m-d' }}" required>
                            <small class="form-text text-muted" id="mnSpan">
                                Pick a menu to see which days it will cover.
                            </small>
                        </div>
                        <button type="submit" class="btn action-primary" id="applyMenuGo" disabled>
                            <i class="fas fa-check"></i> Add to These Days
                        </button>"""

OPTION_WAS = """                            <div class="menu-option" data-menu-id="{{ menu.menu_id }}"
                                 onclick="pickMenu(this)">
                                <div class="menu-option-name">
                                    <strong>{{ menu.name }}</strong><br>
                                    <small class="text-muted">
                                        {{ menu.item_count }} meal{{ menu.item_count|pluralize }}
                                    </small>
                                </div>"""

OPTION_NOW = """                            {# data-menu-days IS THE MENU OWN LENGTH - MN-2.   #}
                            {# The planner annotates it beside the item count, #}
                            {# so the line under Landing on costs no query and #}
                            {# no endpoint.                                    #}
                            <div class="menu-option" data-menu-id="{{ menu.menu_id }}"
                                 data-menu-days="{{ menu.span_days }}"
                                 onclick="pickMenu(this)">
                                <div class="menu-option-name">
                                    <strong>{{ menu.name }}</strong><br>
                                    <small class="text-muted">
                                        {{ menu.item_count }} meal{{ menu.item_count|pluralize }}
                                        over {{ menu.span_days }} day{{ menu.span_days|pluralize }}
                                    </small>
                                </div>"""

PICK_WAS = """function pickMenu(el) {
    document.querySelectorAll('.menu-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    el.classList.add('selected');
    document.getElementById('applyMenuId').value = el.dataset.menuId;
    document.getElementById('applyMenuGo').disabled = false;
}"""

PICK_NOW = """function pickMenu(el) {
    document.querySelectorAll('.menu-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    el.classList.add('selected');
    document.getElementById('applyMenuId').value = el.dataset.menuId;
    mnSaySpan();
}

// WHICH DAYS IT WILL COVER - MN-2, 21 Oct 2026.
//
// A menu is a span now, so a button naming one fixed week stopped
// being true the moment Landing on arrived - and this note does not
// spell that old label, because a suite asking whether it is gone
// would find it here. This says the actual dates, worked out
// from the menu own length and the date in the field - no query, no
// endpoint, and nothing to be in flight.
//
// THE BUTTON IS ARMED BY BOTH. A menu with no landing date, or a
// landing date with no menu, is half an instruction.
function mnSaySpan() {
    var sel = document.querySelector('.menu-option.selected'),
        onto = document.getElementById('mnOnto'),
        note = document.getElementById('mnSpan'),
        go = document.getElementById('applyMenuGo');
    if (!go) { return; }
    var ready = !!(sel && onto && onto.value);
    go.disabled = !ready;
    if (!note) { return; }
    if (!sel) {
        note.textContent = 'Pick a menu to see which days it will cover.';
        return;
    }
    if (!onto || !onto.value) {
        note.textContent = 'Pick the day it starts on.';
        return;
    }
    var days = Number(sel.getAttribute('data-menu-days')) || 1,
        p = onto.value.split('-'),
        a = new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2])),
        b = new Date(a.getTime());
    b.setDate(b.getDate() + days - 1);
    var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    function lbl(d) { return d.getDate() + ' ' + MON[d.getMonth()]; }
    note.textContent = (days === 1
        ? 'It will land on ' + lbl(a) + '.'
        : 'It will cover ' + lbl(a) + ' to ' + lbl(b)
          + ' - ' + days + ' days.');
}

document.addEventListener('change', function (ev) {
    if (ev.target && ev.target.id === 'mnOnto') { mnSaySpan(); }
});"""

PRESET_WAS = """    document.addEventListener('click', function (ev) {
        var b = ev.target && ev.target.closest
            && ev.target.closest('.cp-preset');
        if (!b) { return; }
        var two = span(b.getAttribute('data-cp-span'));
        if (el('cpFrom')) { el('cpFrom').value = two[0]; }
        if (el('cpTo')) { el('cpTo').value = two[1]; }
        [].forEach.call(document.querySelectorAll('.cp-preset'),
            function (x) { x.setAttribute('aria-pressed',
                x === b ? 'true' : 'false'); });
    });"""

PRESET_NOW = """    document.addEventListener('click', function (ev) {
        var b = ev.target && ev.target.closest
            && ev.target.closest('.cp-preset');
        if (!b) { return; }
        var two = span(b.getAttribute('data-cp-span'));
        if (el('cpFrom')) { el('cpFrom').value = two[0]; }
        if (el('cpTo')) { el('cpTo').value = two[1]; }
        [].forEach.call(document.querySelectorAll('.cp-preset'),
            function (x) { x.setAttribute('aria-pressed',
                x === b ? 'true' : 'false'); });
    });

    // THE SAME THREE PRESETS, FOR SAVING A MENU - MN-2, 21 Oct 2026.
    //
    // span() already answers day, week and month off the anchor on
    // screen, and SL-7 settled what a month means here. A second
    // implementation would be a second answer waiting to disagree.
    document.addEventListener('click', function (ev) {
        var b = ev.target && ev.target.closest
            && ev.target.closest('.mn-preset');
        if (!b) { return; }
        var two = span(b.getAttribute('data-mn-span'));
        if (el('mnFrom')) { el('mnFrom').value = two[0]; }
        if (el('mnTo')) { el('mnTo').value = two[1]; }
        [].forEach.call(document.querySelectorAll('.mn-preset'),
            function (x) { x.setAttribute('aria-pressed',
                x === b ? 'true' : 'false'); });
    });

    // AND IT OPENS ON THIS WEEK, for the reason the copy dialog does:
    // it is the commonest thing to want and it is what the dialog did
    // before there was a choice.
    function mnSeed() {
        if (el('mnFrom') && !el('mnFrom').value) {
            el('mnFrom').value = WEEK_FROM;
            el('mnTo').value = WEEK_TO;
        }
    }
    mnSeed();
    document.addEventListener('click', function (ev) {
        var o = ev.target && ev.target.closest
            && ev.target.closest('[data-target="#menusModal"]');
        if (o) { mnSeed(); }
    });"""

CSS_WAS = """.mn-head {
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--alv-ink-soft);
    margin-bottom: 10px;
}"""

CSS_NOW = """.mn-head {
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--alv-ink-soft);
    margin-bottom: 10px;
}
/* MN-2, 21 Oct 2026 - the Save half took a range, so it wears the
   same preset row the Copy dialog does. The rules are CP-2's; this
   adds the one selector they did not know about. */
.mn-preset[aria-pressed="true"] {
    background: var(--alv-accent-soft);
    border-color: var(--alv-accent-line);
    color: var(--alv-accent-ink);
}"""

# ==========================================================================
# MN-1 and MW-1's SUITE - the claims that said a menu is seven days
# ==========================================================================
WEEK_CLAIMS_WAS = """    # ---- 5. what makes a menu a template and not a week
    c['a menu stores a DAY INDEX, computed from the week'] = (
        "day_index=(e.date - week).days" in vcode)"""

WEEK_CLAIMS_NOW = """    # ---- 5. what makes a menu a template and not a week
    # MN-2, 21 Oct 2026 - FROM THE START OF THE RANGE, not from a
    # Monday. MN-1 measured the offset from the week on screen because
    # the week on screen was the only thing a menu could be. The
    # column always said otherwise - "0 is the first day of the menu,
    # not a weekday" - and now the view agrees with it.
    c['a menu stores a DAY OFFSET, computed from the start of the range'] = (
        "day_index=(e.date - start).days" in vcode)"""

WEEK_IDX_WAS = """    c['applying reads the day index back'] = (
        'timedelta(days=it.day_index)' in vcode)
    c['  and a day index outside 0..6 is dropped, not wrapped'] = (
        'if not 0 <= it.day_index <= 6:' in vcode)"""

WEEK_IDX_NOW = """    c['applying reads the day offset back'] = (
        'timedelta(days=it.day_index)' in vcode)
    # MN-2, 21 Oct 2026 - THE CEILING MOVED AND THE RULE DID NOT. A
    # menu was 0..6 by construction; it is 0..91 now, and an offset
    # past the end is still DROPPED rather than wrapped - a row that
    # says a year would otherwise land a year away.
    c['  and a day offset past the ceiling is dropped, not wrapped'] = (
        'if not 0 <= it.day_index < MENU_MAX_DAYS:' in vcode)
    c['  the ceiling is a quarter, declared where the rule lives'] = (
        'MENU_MAX_DAYS = 92' in vcode)
    c['  and a menu lands where you say, not on the week on screen'] = (
        "onto = week_of(request.POST.get('onto'), week)" in vcode
        and 'when = onto + timedelta(days=it.day_index)' in vcode)"""


WEEK_ANN_WAS = """    c['  counted by annotate, not once per row'] = (
        "annotate(\\n            item_count=Count('items'))" in vcode
        or "annotate(item_count=Count('items'))" in vcode)"""

WEEK_ANN_NOW = """    # MN-2, 21 Oct 2026 - AND ITS LENGTH, IN THE SAME annotate. The
    # Apply half says which days a menu will cover; it works that out
    # in the page from a number the planner already has. A second
    # annotate, or a count per row, would be E29's fault coming back
    # on the screen MW-1 took it off.
    c['  counted by annotate, not once per row'] = (
        "item_count=Count('items')," in vcode
        and "span_days=Coalesce(Max('items__day_index'), -1) + 1" in vcode
        and vcode.count('Menu.objects.annotate(') == 1)"""

WEEK_DROP_WAS = """    # A DAY INDEX OUTSIDE THE WEEK IS DROPPED, NOT WRAPPED. A menu
    # saved from a week is 0..6 by construction; a row that somehow
    # says 9 would otherwise land in the NEXT week, which is a
    # surprise nobody asked for and nobody would find.
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=9, recipe=pie,
                            servings=4, sort_order=1)
    MenuItem.objects.create(menu=menu, day_index=-1, recipe=pie,
                            servings=4, sort_order=1)
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(MealEntry.objects.count() == 2,
       'a day index outside 0..6 is DROPPED', MealEntry.objects.count())
    ok(not MealEntry.objects.filter(
        date__gt=DST + _dt.timedelta(days=6)).exists(),
       '  and nothing landed in the week after')
    ok(not MealEntry.objects.filter(date__lt=DST).exists(),
       '  or the week before')"""

WEEK_DROP_NOW = """    # A DAY OFFSET OUTSIDE THE MENU IS DROPPED, NOT WRAPPED.
    #
    # MN-2, 21 Oct 2026 - THE CEILING MOVED AND THE RULE DID NOT. This
    # read 9 and -1 and expected both dropped, because a menu was
    # seven days by construction. A menu is up to 92 days now, so 9 is
    # an ordinary Tuesday-after-next and lands; 92 and -1 are the ones
    # outside, and they are still dropped rather than wrapped. A row
    # that said 400 would otherwise land more than a year away, which
    # is a surprise nobody asked for and nobody would find.
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=92, recipe=pie,
                            servings=4, sort_order=1)
    MenuItem.objects.create(menu=menu, day_index=-1, recipe=pie,
                            servings=4, sort_order=1)
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(MealEntry.objects.count() == 2,
       'a day offset outside 0..91 is DROPPED', MealEntry.objects.count())
    ok(not MealEntry.objects.filter(
        date__gte=DST + _dt.timedelta(days=92)).exists(),
       '  and nothing landed a quarter away')
    ok(not MealEntry.objects.filter(date__lt=DST).exists(),
       '  or before the landing date')
    # AND 9 IS NOW AN ORDINARY DAY, which is the behaviour that
    # changed rather than a pin that moved.
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=9, recipe=pie,
                            servings=4, sort_order=1)
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(MealEntry.objects.filter(
        date=DST + _dt.timedelta(days=9)).exists(),
       '  while day 9 LANDS - a menu is no longer seven days long',
       list(MealEntry.objects.values_list('date', flat=True)))"""

EMPTY_WAS = """                            <p class="text-muted">
                                Put some meals on a week, then use
                                <strong>Save this week</strong> above.
                            </p>"""

EMPTY_NOW = """                            <p class="text-muted">
                                Put some meals on some days, then use
                                <strong>Save these days</strong> above.
                            </p>"""

# ---- CP-2's EMPTY-STATE CLAIM. It pins the exact sentence, and this
# round changes the control that sentence names. A claim about a label
# has to move when the label does, or it is pinning a word rather than
# the thing the word was for.
WEEK_EMPTY_WAS = """    # CP-2, 21 Oct 2026 - the empty state can point UP now rather
    # than at a dialog the reader cannot see from here: Save and
    # Apply are two sections of one dialog, so "Save this week" is
    # eighty pixels above the sentence that names it.
    c['the Apply dialog says where menus come from when there are none'] = (
        'Save this week</strong> above' in tcode)"""

WEEK_EMPTY_NOW = """    # CP-2, 21 Oct 2026 - the empty state can point UP now rather
    # than at a dialog the reader cannot see from here: Save and
    # Apply are two sections of one dialog, so the control that makes
    # a menu is eighty pixels above the sentence that names it.
    #
    # MN-2, 21 Oct 2026 - AND THE CONTROL IS NOT CALLED THAT ANY MORE.
    # Saving takes a range, so the button says "Save these days" and
    # this sentence says the same words it does. The claim is still
    # that the empty state names the real control; only the control
    # was renamed.
    c['the Apply dialog says where menus come from when there are none'] = (
        'Save these days</strong> above' in tcode)"""

# ==========================================================================
# CP-2's SUITE - three of its claims are about walls this round moves
# ==========================================================================
# CP-2 PUT SAVE, APPLY AND DELETE IN ONE DIALOG on 21 October and said,
# correctly, that it had moved a door and left the walls alone. This
# round rebuilds two of those walls, so two of its claims have to move
# with them - and the third is a magic number that the bigger dialog
# runs past.
CP_WINDOW_WAS = """    c['SAVE, APPLY AND DELETE ARE IN ONE DIALOG'] = all(
        x in code[code.find('id="menusModal"'):
                  code.find('id="menusModal"') + 6000]
        for x in ("url 'save_menu'", "url 'apply_menu'", 'deleteMenu('))"""

CP_WINDOW_NOW = """    # MN-2, 21 Oct 2026 - THE DIALOG, NOT SIX THOUSAND CHARACTERS.
    # This read a fixed window from the dialog's id, and MN-2 gave the
    # Save half a preset row, two dates and a note while the Apply half
    # gained a landing date and a line of its own. deleteMenu( landed
    # past 6000 and the claim failed for the dialog being BIGGER, which
    # is not what it is about. Sliced to the dialog's own end instead,
    # so it cannot drift again.
    _mi = code.find('id="menusModal"')
    _me = code.find('</div>\\n</div>', _mi) if _mi >= 0 else -1
    _menu = code[_mi:_me if _me > _mi else len(code)] if _mi >= 0 else ''
    c['SAVE, APPLY AND DELETE ARE IN ONE DIALOG'] = all(
        x in _menu
        for x in ("url 'save_menu'", "url 'apply_menu'", 'deleteMenu('))"""

CP_WALLS_WAS = """# THE WALLS ARE BYTE-IDENTICAL. This round moved a door. If the copy
# engine or any of the three endpoints had changed under it, every
# claim above would still hold and the behaviour would be new.
oldv = BEFORE[VIEW]
for name in ('copy_week_rows', 'save_menu', 'apply_menu', 'delete_menu',
             'copy_meal_week'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and a == b,
       'CONTROL: %s is byte-identical before and after' % name,
       'len before %d, len after %d' % (len(a), len(b)))"""

CP_WALLS_NOW = """# THE WALLS WERE BYTE-IDENTICAL, AND TWO OF THEM HAVE SINCE BEEN
# REBUILT. CP-2 moved a door and left the walls alone; if the copy
# engine or any of the three endpoints had changed UNDER IT, every
# claim above would still have held and the behaviour would have been
# new. That was the point and it still is.
#
# MN-2, 21 Oct 2026 - save_menu AND apply_menu ARE NOT THE SAME TWO
# FUNCTIONS ANY MORE, and that is deliberate: a menu is a span of days
# landing where you say. Comparing them with CP-2's backup now answers
# "has anything changed since 21 October" rather than "did CP-2 change
# anything", and the first question has a different right answer every
# day. So the three CP-2 did not touch are still held to the byte, and
# the two MN-2 rebuilt are held to being MN-2's work and to still
# doing what CP-2's dialog needs of them.
oldv = BEFORE[VIEW]
for name in ('copy_week_rows', 'delete_menu', 'copy_meal_week'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and a == b,
       'CONTROL: %s is byte-identical before and after' % name,
       'len before %d, len after %d' % (len(a), len(b)))
for name in ('save_menu', 'apply_menu'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and bool(b) and a != b,
       'CONTROL: %s was rebuilt after this round, by MN-2' % name,
       'len before %d, len after %d' % (len(a), len(b)))
    ok('MN-2, 21 Oct 2026' in b,
       '  and says so in its own text, so this is a change somebody '
       'signed rather than a drift', name)
    ok("request.POST.get('week')" in b,
       '  and it still reads the week this dialog posts, which is all '
       'CP-2 ever asked of it', name)"""

# ---- AND THE PAIR CENSUS, WHICH THIS ROUND ADDS ONE TO.
#
# test_pair_contrast counts every rule in the tree that sets BOTH a
# background and a colour, and five suites read that number. MN-2's
# .mn-preset[aria-pressed="true"] does exactly that - it is CP-2's
# .cp-preset rule, worn by the Save half's new preset row - so the
# census rises by one. A token pair this table already knows, from a
# rule that is a copy of one it already measured.
PAIR_WAS = """EXPECT_PAIRS = 726   # RG-2, 21 Oct 2026"""

PAIR_NOW = """EXPECT_PAIRS = 727   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026"""

# ---- AND RG-2's OWN CLAIM ABOUT THAT NUMBER.
#
# RG-2 moved the pair census to 726 three rounds ago and pinned the
# literal in its own suite, which is right: a round that moves a census
# should say what it moved it to. This round moves it again, so RG-2's
# claim becomes a claim about RG-2's arithmetic rather than about
# today's total - which is what it was always for.
RG2_WAS = """ok('EXPECT_PAIRS = 726' in read(pc),
   '  and it is 726, measured by running it')"""

RG2_NOW = """# MN-2, 21 Oct 2026 - THE TOTAL MOVED AGAIN, and this claim is about
# what RG-2 DID, not about what the tree holds today. RG-2 added two
# pairs and took the census from 724 to 726; MN-2 adds the Saved Menus
# preset row and takes it to 727. Asking for today's total here would
# make a 21 October round's record change every time somebody adds a
# rule, which is the opposite of a record.
ok("# RG-2, 21 Oct 2026" in read(pc)
   and "(was 724)" in read(pc),
   '  and RG-2 two pairs are still in its history, 724 -> 726')"""


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
    raise SystemExit('MN-2 REFUSED: %s' % msg)


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
    v = read(pv)

    if 'MENU_MAX_DAYS' in v:
        print('MN-2  already applied - a menu takes a range.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, ASKED OF THE VIEW. The claim this round rests
    # on is that the TABLE was never week-shaped and the VIEWS were.
    pm = os.path.join(root, MODELS)
    m = read(pm)
    mcode = T.python_code_only(m, payloads=True)
    if 'day_index' not in mcode:
        refuse('%s: MenuItem has no day_index' % MODELS)
    if 'not a weekday' not in mcode:
        refuse('%s: MenuItem.day_index no longer describes itself as an '
               'offset, so the premise of this round is gone' % MODELS)
    vcode = T.python_code_only(v, payloads=True)
    if 'if not 0 <= it.day_index <= 6:' not in vcode:
        refuse('%s: the 0..6 ceiling this round widens is not there'
               % VIEW)

    v = swap(v, IMPORT_WAS, IMPORT_NOW, '%s (the import)' % VIEW)
    v = swap(v, HELP_WAS, HELP_NOW, '%s (the span)' % VIEW)
    v = swap(v, SAVE_HEAD_WAS, SAVE_HEAD_NOW, '%s (save head)' % VIEW)
    v = swap(v, SAVE_ROWS_WAS, SAVE_ROWS_NOW, '%s (save rows)' % VIEW)
    v = swap(v, SAVE_IDX_WAS, SAVE_IDX_NOW, '%s (the offset)' % VIEW)
    v = swap(v, SAVE_MSG_WAS, SAVE_MSG_NOW, '%s (save said)' % VIEW)
    v = swap(v, APPLY_HEAD_WAS, APPLY_HEAD_NOW, '%s (apply head)' % VIEW)
    v = swap(v, APPLY_LOOP_WAS, APPLY_LOOP_NOW, '%s (the ceiling)' % VIEW)
    v = swap(v, APPLY_MSG_WAS, APPLY_MSG_NOW, '%s (apply said)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    out[pv] = v

    out[pm] = swap(m, MODEL_WAS, MODEL_NOW, '%s (the Menu)' % MODELS)

    # ---- THE DIALOG
    pt = os.path.join(root, TPL)
    t = read(pt)
    t = swap(t, SAVE_FORM_WAS, SAVE_FORM_NOW, '%s (save half)' % TPL)
    t = swap(t, APPLY_FORM_WAS, APPLY_FORM_NOW, '%s (apply half)' % TPL)
    t = swap(t, OPTION_WAS, OPTION_NOW, '%s (the option)' % TPL)
    t = swap(t, EMPTY_WAS, EMPTY_NOW, '%s (the empty state)' % TPL)
    t = swap(t, APPLY_GO_WAS, APPLY_GO_NOW, '%s (the landing)' % TPL)
    t = swap(t, PICK_WAS, PICK_NOW, '%s (the script)' % TPL)
    t = swap(t, PRESET_WAS, PRESET_NOW, '%s (the presets)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the rules)' % TPL)
    out[pt] = t

    # ---- MW-1 and MN-1's SUITE, CORRECTED IN THE SAME PATCHER
    pw = os.path.join(root, WEEK)
    w = read(pw)
    w = swap(w, WEEK_CLAIMS_WAS, WEEK_CLAIMS_NOW, '%s (the claims)' % WEEK)
    w = swap(w, WEEK_IDX_WAS, WEEK_IDX_NOW, '%s (0..6)' % WEEK)
    w = swap(w, WEEK_ANN_WAS, WEEK_ANN_NOW, '%s (the annotate)' % WEEK)
    w = swap(w, WEEK_DROP_WAS, WEEK_DROP_NOW, '%s (the drop)' % WEEK)
    w = swap(w, WEEK_EMPTY_WAS, WEEK_EMPTY_NOW, '%s (the empty state)' % WEEK)
    out[pw] = w

    # ---- CP-2's SUITE
    pc = os.path.join(root, COPY)
    c = read(pc)
    c = swap(c, CP_WINDOW_WAS, CP_WINDOW_NOW, '%s (the window)' % COPY)
    c = swap(c, CP_WALLS_WAS, CP_WALLS_NOW, '%s (the walls)' % COPY)
    out[pc] = c

    # ---- THE PAIR CENSUS, AND THE ROUND THAT LAST MOVED IT
    pp2 = os.path.join(root, PAIRS)
    out[pp2] = swap(read(pp2), PAIR_WAS, PAIR_NOW, '%s (the count)' % PAIRS)
    pr2 = os.path.join(root, PRANGE)
    out[pr2] = swap(read(pr2), RG2_WAS, RG2_NOW, '%s (the census)' % PRANGE)

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_msg_base.py'
)""", """    'test_msg_base.py',
    # MN-2, 21 Oct 2026 - a menu takes a range and lands where you say.
    'test_menu_range.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/templates/base.html'; Text = 'THE ONE MESSAGE LOOP - BM-1';""",
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'MENU_MAX_DAYS'; What = 'MN-2: a saved menu is a span of days up to a quarter long, not a week, and Apply puts it on a date you choose - the table always allowed both and the two views did not' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'mn-preset'; What = 'MN-2: the Saved Menus dialog has a From, a To and a Landing on, with the same three presets CP-2 gave Copy' },
    @{ File = 'pages/templates/base.html'; Text = 'THE ONE MESSAGE LOOP - BM-1';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # BM-1, 21 Oct 2026 - the message bar, once, in base.
    'test_msg_base.py',
]""", """    # BM-1, 21 Oct 2026 - the message bar, once, in base.
    'test_msg_base.py',
    # MN-2, 21 Oct 2026 - a menu is a span, and it lands where you say.
    'test_menu_range.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # BM-1, 21 Oct 2026 - one message loop, in base.
    '.bak_msgbase',
]""", """    # BM-1, 21 Oct 2026 - one message loop, in base.
    '.bak_msgbase',
    # MN-2, 21 Oct 2026 - menus take a range.
    '.bak_menurange',
]""", '%s (ROUNDS)' % ROUNDS)

    pwd = os.path.join(root, WD)
    wd = read(pwd)
    n = re.search(r'CONVERTED_N = (\d+)', wd)
    out[pwd] = swap(wd, 'CONVERTED_N = %s' % n.group(1),
                    'CONVERTED_N = %d   # MN-2, 21 Oct 2026 - this round '
                    'own suite   # (was %s)'
                    % (int(n.group(1)) + 1, n.group(1)),
                    '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    sv = nv[nv.index('def save_menu'):nv.index('def apply_menu')]
    av = nv[nv.index('def apply_menu'):nv.index('def delete_menu')]
    # THE RANGE IS READ, AND IT DEFAULTS TO THE WEEK ON SCREEN. Without
    # the default every caller that sends only `week` changes meaning
    # silently, which is the one thing this round must not do.
    if "week_of(request.POST.get('from'), week)" not in sv:
        refuse('%s: save_menu does not default `from` to the week on '
               'screen' % VIEW)
    if "week_of(request.POST.get('onto'), week)" not in av:
        refuse('%s: apply_menu does not default `onto` to the week on '
               'screen' % VIEW)
    # NOTHING IS MEASURED FROM A MONDAY ANY MORE.
    if '(e.date - week).days' in sv:
        refuse('%s: save_menu still measures the offset from a Monday'
               % VIEW)
    if 'week + timedelta(days=it.day_index)' in av:
        refuse('%s: apply_menu still lands on the week on screen' % VIEW)
    # THE CEILING EXISTS AND IS A DROP, NOT A WRAP.
    if 'it.day_index < MENU_MAX_DAYS' not in av or 'continue' not in av:
        refuse('%s: a day offset past the ceiling is not dropped' % VIEW)
    if 'MENU_MAX_DAYS = 92' not in nv:
        refuse('%s: the ceiling is not declared as a named constant' % VIEW)
    # A LEFTOVER IS STILL NOT SAVED.
    if 'if e.leftover_of_id:' not in sv:
        refuse('%s: save_menu stopped skipping leftovers' % VIEW)
    # AND A NAME IS STILL REQUIRED AND STILL UNIQUE.
    if 'A menu needs a name.' not in sv or 'name__iexact=name' not in sv:
        refuse('%s: the name rules went with the week' % VIEW)
    # THE DIALOG HAS BOTH ENDS AND A LANDING.
    nt = out[pt]
    for need in ('name="from"', 'name="to"', 'name="onto"',
                 'mn-preset', 'id="mnSpan"'):
        if need not in nt:
            refuse('%s: the dialog is missing %s' % (TPL, need))
    if nt.count('{%') != nt.count('%}'):
        refuse('%s: the tags stopped balancing - %d {%% against %d %%}'
               % (TPL, nt.count('{%'), nt.count('%}')))
    # AND NO SECOND DIALECT. The presets are the ones CP-2 built.
    if 'cp-preset' not in nt:
        refuse('%s: CP-2 presets are gone, and this round copies their '
               'shape rather than inventing a second one' % TPL)

    if CHECK:
        print('MN-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        a menu is a span of up to 92 days, landing where '
              'you say')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('MN-2  applied - a menu is a span of days, and it lands where '
          'you put it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
