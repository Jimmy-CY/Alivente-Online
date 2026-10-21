# -*- coding: utf-8 -*-
"""apply_print_shape.py - round RG-1, 21 Oct 2026.

THE PRINTED PLAN HAD ONE SHAPE FOR THREE DIFFERENT THINGS.

Demetri, 21 October:

    "I don't like the look of the Monthly Print or the weekly .. I
     don't know. Can't we make this prettier?? Give some suggestions.
     Can the Month fit on one A4 page?"

    "Day view Print, prints a Week view."

BOTH ARE THE SAME FAULT. PP-1 built one layout - a stack of week
grids, each with a `Week of 19 Oct` strip above it - and handed every
range to it. A single day became a seven-column grid with six of the
columns greyed out, which is why pressing Print on the day view
printed a week: it WAS a week, with one day lit.

AND A MONTH DID NOT FIT. Five week strips at 110px plus five labels
is 700px of grid under a 60px heading on a 726px sheet, before the
sixth week that February 2027 and August 2026 both have.

THE SHAPE OF THE SHEET IS NOW THE SHAPE OF THE RANGE, which is the
only rule that cannot disagree with itself:

    one day              -> a portrait day sheet, agenda and notes
    Monday to Sunday     -> one landscape week, columns to write in
    a whole month        -> one landscape month, on ONE sheet
    anything else        -> the month grid, dated across its edges

He was shown five renders at real A4 and chose: "Month looks good.
Let's go with B2 and C2..." - the ruled week and the agenda day.

ONE SHEET IS A MEASUREMENT, NOT A HOPE. The month grid is a flex
column of week rows inside a fixed 166mm box, so five weeks and six
weeks both fill the same sheet: a six-week month is tighter, not
spilled onto a second page. Section 3 of the suite prints four months
to real A4 through Chromium and reads the page count back out of the
PDF.

NOTHING TRUNCATES. `Amygdalopita` came out `Amygdalo...` in a 130px
column at 16px while this was being drawn. On a screen an ellipsis is
a promise you can hover; on paper it is a name you cannot read. Every
meal wraps and nothing is clipped, at every one of the three sizes.

EVERY COLOUR IS A TOKEN. The renders were built with literals to move
fast; not one of them survives into the page.

THE WEEKEND TINT DID NOT SURVIVE EITHER. #fbfcfd against #ffffff
measures dE 0.9 in CIE Lab - invisible on a screen and more so on
paper, and WT-1 spent this morning on exactly that mistake. A stripe
nobody can see is not a quiet stripe, it is a dead rule.

Idempotent. Every file backed up to .bak_printshape.
"""
import os
import re
import sys

SUFFIX = '.bak_printshape'
TPL = os.path.join('pages', 'templates', 'meal_plan_print.html')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
PRINTT = 'test_print_plan.py'
ME = 'test_print_shape.py'
PATCHER = 'apply_print_shape.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RG-1, 21 Oct 2026'
CHECK = False
CREATES = ()


# =====================================================================
# THE VIEW - the range decides the sheet
# =====================================================================
DAYS_WAS = """            days.append({
                'date': when,
                'in_range': start <= when <= end,
                'is_today': when == today,
                'entries': by_day.get(when, []),
            })"""

DAYS_NOW = """            days.append({
                'date': when,
                'in_range': start <= when <= end,
                'is_today': when == today,
                # RG-1, 21 Oct 2026 - the week sheet heads each column
                # with its own weekday, so the template needs to know
                # which day of the week this is without doing date
                # arithmetic in a filter.
                'weekday': when.weekday(),
                'entries': by_day.get(when, []),
            })"""

TAIL_WAS = """        weeks.append({'start': cursor, 'days': days})
        cursor += timedelta(days=7)

    return render(request, 'meal_plan_print.html', {
        'start': start,
        'end': end,
        'weeks': weeks,
        'day_count': (end - start).days + 1,
        'meal_count': sum(len(v) for k, v in by_day.items()
                          if start <= k <= end),
    })"""

TAIL_NOW = '''        weeks.append({'start': cursor, 'days': days})
        cursor += timedelta(days=7)

    # THE SHAPE OF THE SHEET IS THE SHAPE OF THE RANGE - RG-1,
    # 21 Oct 2026.
    #
    # PP-1 had one layout and gave every range to it, so a single day
    # printed as a seven-column grid with six columns greyed out -
    # which is precisely what Demetri reported as "Day view Print,
    # prints a Week view". It was a week. It had one day in it.
    #
    # NOT A ?shape= PARAMETER. The planner already sends the two
    # dates SL-7 computes for the view you are on; a second parameter
    # saying what those dates MEAN is a thing that can disagree with
    # them. A day is a range of one. A week is a Monday and six days
    # after it. A month is the first to the last. Nothing else needs
    # to be passed and nothing else can go stale.
    last_of_month = (date(start.year + (start.month == 12),
                          start.month % 12 + 1, 1) - timedelta(days=1))
    if start == end:
        sheet = 'day'
    elif start.weekday() == 0 and (end - start).days == 6:
        sheet = 'week'
    elif start.day == 1 and end == last_of_month:
        sheet = 'month'
    else:
        sheet = 'range'

    # THE BIG LINE ON THE SHEET, built here rather than in four
    # template branches - and built with day_label's arithmetic
    # rather than strftime's %-d, which Windows does not have and
    # this project runs on Windows and on Railway both.
    if sheet == 'day':
        period = '%s %d %s' % (start.strftime('%A'), start.day,
                               start.strftime('%B'))
    elif sheet == 'month':
        period = start.strftime('%B %Y')
    else:
        period = '%s - %s %d' % (day_label(start), day_label(end),
                                 end.year)

    return render(request, 'meal_plan_print.html', {
        'start': start,
        'end': end,
        'weeks': weeks,
        'sheet': sheet,
        'period': period,
        'day_entries': by_day.get(start, []),
        'day_count': (end - start).days + 1,
        'meal_count': sum(len(v) for k, v in by_day.items()
                          if start <= k <= end),
    })'''


# =====================================================================
# THE PAGE
# =====================================================================
CSS = '''<style>
/* PAPER FIRST, SCREEN SECOND - PP-1, 20 Oct 2026, redrawn by RG-1 on
   21 Oct 2026. Every colour is a token; nothing here is a literal.
   The five renders Demetri chose from were built with hex values to
   move fast, and not one of those values survived into this page. */

/* ITS OWN CONTAINER, NOT THE PLANNER'S - PP-1, 20 Oct 2026.
   The first draft of this page wrapped itself in .calendar-container,
   because that is what meal_planner.html wraps itself in. But that
   class is DEFINED IN meal_planner.html, not in base - so on this
   page it is a name with no rules behind it, and the grid ran flush
   to both edges of the window with no padding at all. A class is not
   a style; the style is wherever the style was written. Every other
   standalone meal-plan page declares its own, and so does this one. */
.pp-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* THE SHEET. -webkit-print-color-adjust, because the pills ARE the
   layout here: a browser that drops background colour to save ink
   leaves seven columns of identical grey text. */
.pp-sheet {
    background: var(--alv-paper);
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* ---- THE MASTHEAD -------------------------------------------------
   THE SHEET'S OWN, IN ITS OWN CLASSES. The first draft restyled
   base's .page-title-h2 and .page-subtitle-h4 inside .pp-sheet, and
   test_heading_components named it at once: NO page may carry a rule
   whose selector mentions either class. That is the whole point of a
   shared heading component - a page that restyles it has forked it -
   and the suite says so about every one of the hundred and fifty.

   So the house heading stays above the bar where test_bar_top wants
   it, untouched and unstyled by this page, and the printed sheet
   carries a masthead of its own that base has never seen. */
.pp-title {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    border-bottom: 2px solid var(--alv-accent);
    padding-bottom: 7px;
    margin-bottom: 12px;
}
.pp-eyebrow {
    margin: 0 0 2px 0;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--alv-accent);
}
.pp-period {
    font-size: 21px;
    font-weight: 700;
    line-height: 1.04;
    letter-spacing: -0.01em;
    text-transform: uppercase;
    color: var(--alv-ink);
}
.pp-count {
    margin: 0;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    /* ink-soft, NOT ink-faint. ink-faint on paper measures 3.00:1
       and test_verb_colours names every rule that takes its ground
       from an ancestor and reads below AA. PP-1 had to lift two of
       this page's greys for the same reason, and this page is read
       under a kitchen light. */
    color: var(--alv-ink-soft);
    text-align: right;
}

/* ---- A MEAL ------------------------------------------------------
   One pill, three sizes. NEVER TRUNCATED: `Amygdalopita` came out
   `Amygdalo...` in a 130px column while this was being drawn. On a
   screen an ellipsis is a promise you can hover; on paper it is a
   name you cannot read, so it wraps instead. */
.pp-meal {
    display: block;
    width: fit-content;
    max-width: 100%;
    line-height: 1.25;
    border-radius: 999px;
    border: 1px solid var(--alv-accent-line);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    overflow-wrap: anywhere;
    hyphens: auto;
}
.pp-meal.is-note {
    background: var(--alv-warn-soft);
    border-color: var(--alv-warn-line);
    color: var(--alv-warn-ink);
    font-style: italic;
}
/* LEFTOVERS WEAR THE RECYCLE MARK, not a 9px LEFTOVERS tag under the
   name. PP-1 set that tag in ink-faint, measured 3.00:1 and had to
   lift it to ink-soft; a glyph in front of the name says the same
   thing inside the pill and costs no second line in a 130px cell. */
.pp-meal.is-left {
    background: var(--alv-surface-deep);
    border-color: var(--alv-line);
    color: var(--alv-ink-soft);
}
.pp-meal.is-left::before { content: "\\21BB\\00A0"; }

/* ---- THE GRID, SHARED BY WEEK, MONTH AND RANGE -------------------
   minmax(0, 1fr), NOT 1fr - PP-1, 20 Oct 2026. A bare `1fr` track is
   minmax(AUTO, 1fr), so it never shrinks below the widest unbreakable
   thing in the cell: seven cells holding BUTTER CHICKEN CURRY pushed
   the grid to 992px inside a 794px sheet of A4, and the Sunday column
   printed off the edge of the paper. */
.pp-sheet-grid {
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    overflow: hidden;
}
.pp-dow-row,
.pp-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.pp-dow {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--alv-ink-soft);
    background: var(--alv-surface);
    padding: 5px 7px;
    border-bottom: 1px solid var(--alv-line);
    border-right: 1px solid var(--alv-line-soft);
}
.pp-dow:last-child { border-right: 0; }
.pp-day {
    padding: 4px 6px 5px;
    border-right: 1px solid var(--alv-line-soft);
    border-top: 1px solid var(--alv-line-soft);
    min-width: 0;
}
.pp-day:last-child { border-right: 0; }
/* OUT OF RANGE IS STILL DRAWN, so the week keeps its seven columns
   and the boundary is visible rather than implied. TWO SIGNALS, not
   one: the ground is tinted AND the number drops to ink-faint. One
   pale fill against another is the mistake WT-1 corrected this
   morning - the month view marked the current week with a tint that
   measured dE 0.0 against the pills sitting on it. */
.pp-day.is-out { background: var(--alv-surface); }
/* ink-soft, NOT ink-faint - PP-1's lesson, re-learned. ink-faint on
   the surface wash measures 2.85:1, below AA, and the first draft of
   this round put it back on the one page in the application that
   exists to be read on paper. The in-range date takes the full ink
   instead, so the two states are still two signals apart. */
.pp-day.is-out .pp-date { color: var(--alv-ink-soft); }
.pp-date {
    font-size: 10px;
    font-weight: 700;
    color: var(--alv-ink);
    margin-bottom: 3px;
    display: block;
}
.pp-day.is-today .pp-date {
    color: var(--alv-on-accent);
    background: var(--alv-accent);
    border-radius: 999px;
    padding: 0 6px;
    width: fit-content;
}

/* ---- THE MONTH AND THE RANGE -------------------------------------- */
.is-month .pp-day,
.is-range .pp-day { min-height: 104px; }
.is-month .pp-meal,
.is-range .pp-meal {
    font-size: 9px;
    padding: 1px 7px;
    margin-bottom: 2px;
}

/* ---- THE WEEK: SEVEN COLUMNS YOU CAN WRITE IN ---------------------
   B2, which is the one he chose. The pills are legible across a
   kitchen, each column is headed with its own date, and the space
   under them is ruled rather than blank - the sheet is meant to be
   taken off the fridge and written on. */
.is-week .pp-day {
    display: flex;
    flex-direction: column;
    padding: 0;
    border-top: 0;
}
.is-week .pp-colhead {
    padding: 9px 10px 8px;
    border-bottom: 1px solid var(--alv-line);
    background: var(--alv-surface);
}
.pp-dow-s {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--alv-ink-soft);
}
.pp-num {
    font-size: 18px;
    font-weight: 700;
    line-height: 1.05;
    color: var(--alv-ink);
}
.is-week .pp-day.is-today .pp-colhead { background: var(--alv-accent-soft); }
.is-week .pp-day.is-today .pp-num,
.is-week .pp-day.is-today .pp-dow-s { color: var(--alv-accent-ink); }
.is-week .pp-meals { padding: 10px 10px 0; }
.is-week .pp-meal {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 11px;
    margin-bottom: 5px;
}
.pp-rule {
    flex: 1;
    min-height: 0;
    margin: 6px 10px 10px;
    background-image: repeating-linear-gradient(to bottom,
        transparent 0 25px, var(--alv-line-soft) 25px 26px);
}
.is-week .pp-grid { min-height: 520px; }

/* ---- THE DAY: ONE DAY, FILLING THE PAGE ---------------------------
   C2, the agenda. He was offered a big-type day and this, and took
   this: the meals as a list with their servings, and the rest of the
   sheet given over to Notes, because a printed day is a thing people
   write on. */
.is-day .pp-period { font-size: 38px; text-transform: none; }
.is-day .pp-body { display: flex; flex-direction: column; }
.pp-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 11px 0;
}
.pp-row + .pp-row { border-top: 1px solid var(--alv-line-soft); }
.is-day .pp-meal {
    font-size: 16px;
    font-weight: 600;
    padding: 6px 16px;
}
.pp-srv {
    font-size: 11px;
    color: var(--alv-ink-soft);
    margin-left: auto;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
}
.pp-empty {
    font-size: 13px;
    color: var(--alv-ink-soft);
    padding: 14px 0;
}
.pp-notes {
    flex: 1;
    min-height: 240px;
    margin-top: 22px;
    border-top: 1px solid var(--alv-line);
    padding-top: 10px;
    display: flex;
    flex-direction: column;
}
.pp-notes-label {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--alv-ink-soft);
    margin-bottom: 8px;
}
.pp-notes-lines {
    flex: 1;
    min-height: 0;
    background-image: repeating-linear-gradient(to bottom,
        transparent 0 26px, var(--alv-line-soft) 26px 27px);
}
.pp-foot {
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid var(--alv-line-soft);
    font-size: 10px;
    color: var(--alv-ink-soft);
    display: flex;
    justify-content: space-between;
}

/* AND screen, NOT a bare max-width - a clause naming no media type
   matches print too, which is the 21 September print-leak rule and
   the one thing this page must not get wrong. */
@media screen and (max-width: 767px) {
    .pp-page { padding: 8px; }
    .pp-dow-row { display: none; }
    .pp-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .is-month .pp-day,
    .is-range .pp-day { min-height: 80px; }
    .is-week .pp-grid { min-height: 0; }
    .pp-rule { display: none; }
    .pp-count { text-align: left; }
}

/* THE SHEET IS LANDSCAPE UNLESS IT IS ONE DAY. A week divided seven
   ways wants the wider sheet - 137px per day against 95px decides
   whether a recipe name is read or guessed at - and a single day
   wants the taller one, because what fills it is the Notes block. */
{% if sheet == 'day' %}@page { size: A4 portrait; margin: 18mm; }
{% else %}@page { size: A4 landscape; margin: 11mm 12mm; }
{% endif %}

@media print {
    /* THE CHROME GOES. SL-1 does the same on the shopping list, and
       this page exists to be printed rather than to be browsed. */
    nav, .navbar, header, footer,
    /* .alv-message - MG-1, 21 Oct 2026. This page can show a message
       now, and a dismissible alert on paper is a coloured box with a
       close cross in it. */
    .alv-message,
    .page-action-buttons, .pp-noprint { display: none !important; }

    /* AND SO DOES THE BOOTSTRAP CONTAINER - PP-1, 20 Oct 2026.
       base wraps every page in a .container, and Bootstrap sets that
       class's max-width inside `@media (min-width: ...)` queries,
       which name no media type and therefore apply to PAPER as well
       as to screens. Measured on a 794px sheet: max-width 720px, with
       the grid overflowing to 992px and the document scrolling 198px
       wider than the page - the Sunday column printed off the edge.
       A page that exists to be printed cannot leave its own width to
       a grid system's idea of a small desktop. */
    .main-content > .container,
    .main-content { max-width: none !important; width: auto !important;
                    margin: 0 !important; padding: 0 !important; }
    .pp-page { max-width: none; padding: 0; }
    /* AND THE THREE THINGS base PUTS AROUND THE CONTAINER - RG-1,
       21 Oct 2026, every one of them found by printing the page and
       counting the sheets that came out.

       Three <br> at 17px each and a centred copyright line: 68px of
       screen furniture, which on A4 landscape is a tenth of the
       sheet and, more to the point, is 68px MORE than the sheet has.
       Every single shape printed on two pages - the first the plan,
       the second the word Copyright - until these went. The body
       margin is the UA's own 8px and goes for the same reason.

       SCOPED TO THIS PAGE's PRINT BLOCK. base's own chrome is right
       for every screen it is on; it is paper that does not want it,
       and this is the only page in the application that is paper. */
    .main-content > br,
    .main-content > center { display: none !important; }
    body { padding-top: 0; margin: 0 !important; }

    /* ONE SHEET, MEASURED. A month is five week rows or six - August
       2026 and February 2027 are six - and a fixed cell height fits
       one of those and spills the other onto a second page. So the
       SHEET is a fixed box the height of the printable area and the
       grid is a flex column inside it: both months fill exactly one
       sheet, the six-week one tighter. Fixing the sheet rather than
       the grid also means the masthead can change height without
       anybody having to re-measure the number below it.

       A4 landscape is 210mm tall and the margin is 11mm each way, so
       the printable band is 188mm; A4 portrait is 297mm with 18mm
       margins, so 261mm. The two numbers below sit just inside those
       - a sheet exactly as tall as its page rounds onto a second one
       on some printers, which is the fault this block exists to fix.

       test_print_shape prints five of these to real A4 through
       Chromium and reads the page count out of the PDF. */
    .is-month .pp-sheet,
    .is-week .pp-sheet { height: 186mm; display: flex;
                         flex-direction: column; }
    .is-day .pp-sheet { height: 258mm; display: flex;
                        flex-direction: column; }
    .is-month .pp-sheet-grid,
    .is-week .pp-sheet-grid { flex: 1; min-height: 0; display: flex;
                              flex-direction: column; }
    .is-month .pp-week,
    .is-week .pp-week { flex: 1; min-height: 0; display: flex; }
    .is-month .pp-grid,
    .is-week .pp-grid { flex: 1; min-height: 0; height: auto; }
    .is-day .pp-body { flex: 1; min-height: 0; }
    .pp-day, .pp-row { break-inside: avoid; }
    .is-range .pp-week { break-inside: avoid; }
}
</style>'''

BODY = '''<div class="pp-page is-{{ sheet }}">

    {# THE HOUSE HEADING, ABOVE THE BAR - RG-1, 21 Oct 2026.       #}
    {#                                                             #}
    {# test_bar_top reads every page in the tree and asserts that   #}
    {# none of them puts its action bar above its title. The first  #}
    {# draft of this round folded the title into the printed        #}
    {# sheet's masthead, below the bar, and that suite named this   #}
    {# page by itself.                                              #}
    {#                                                              #}
    {# AND IT DOES NOT GO ON THE PAPER. The sheet below carries a    #}
    {# masthead laid out for A4; printing both would say MEAL PLAN   #}
    {# twice. The wrapper is what carries pp-noprint - a print rule  #}
    {# naming .page-title-h2 would be a page restating a shared      #}
    {# component, which test_heading_components forbids outright.    #}
    <div class="pp-noprint">
        <h2 class="page-title-h2">MEAL PLAN</h2>
        <h4 class="page-subtitle-h4">{{ start|date:"j M" }} &ndash; {{ end|date:"j M Y" }} &mdash; {{ day_count }} day{{ day_count|pluralize }} &mdash; {{ meal_count }} meal{{ meal_count|pluralize }}</h4>
    </div>

    {# ONE BAR, and Back is LAST and carries no colour - test_bar_top. #}
    <div class="page-action-buttons pp-noprint">
        <button type="button" class="btn action-primary" onclick="window.print()">
            <i class="fas fa-print"></i> Print
        </button>
        {# .action-back, NOT .action-secondary - PP-1, 20 Oct 2026.   #}
        {# The first draft wore action-secondary and five suites said  #}
        {# so at once: test_vocabulary's classifier put this button in #}
        {# the action-back bucket by its WORD, and the button gate on  #}
        {# four other suites reported one drifting control across the  #}
        {# whole tree - this one. The standard is explicit: "Back is   #}
        {# quiet, sits right, and keeps a 44px target on a phone", and #}
        {# base gives .action-back the square phone treatment and the  #}
        {# hideable label. A page that invents its own Back is a page  #}
        {# that will drift away from the other hundred and forty.      #}
        <a href="{% url 'meal_planner' %}" class="btn action-back"
           aria-label="Back to the planner">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>

    <div class="pp-sheet">

        {# THE SHEET'S OWN MASTHEAD, in classes base has never seen. #}
        {# Restyling .page-title-h2 here is what the first draft did, #}
        {# and test_heading_components forbids any page from carrying #}
        {# a rule that names a shared heading component.              #}
        <div class="pp-title">
            <div>
                <div class="pp-eyebrow">Meal Plan</div>
                <div class="pp-period">{{ period }}</div>
            </div>
            <div class="pp-count">{{ day_count }} day{{ day_count|pluralize }} &middot; {{ meal_count }} meal{{ meal_count|pluralize }}</div>
        </div>

        {% if sheet == 'day' %}
        {# C2, THE AGENDA - his choice of the two day sheets. The    #}
        {# meals as a list with their servings, and the rest of the  #}
        {# page given to Notes, because a printed day gets written   #}
        {# on. PP-1 printed this as a week with six columns greyed   #}
        {# out, which is what he reported.                           #}
        <div class="pp-body">
            {% for e in day_entries %}
            <div class="pp-row">
                <div class="pp-meal{% if not e.recipe_id %} is-note{% elif e.leftover_of_id %} is-left{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</div>
                {# A NOTE HAS NO SERVINGS. The column defaults to a #}
                {# number for every row, so `Dinner at Mums` came   #}
                {# off the first proof reading SERVES 4.            #}
                {% if e.recipe_id and e.servings %}<div class="pp-srv">serves {{ e.servings }}</div>{% endif %}
            </div>
            {% empty %}
            <div class="pp-empty">Nothing planned for this day.</div>
            {% endfor %}
            <div class="pp-notes">
                <div class="pp-notes-label">Notes</div>
                <div class="pp-notes-lines"></div>
            </div>
        </div>
        <div class="pp-foot">
            <span>Alivente &middot; Meal Plan</span>
            <span>{{ start|date:"l j F Y" }}</span>
        </div>

        {% else %}
        <div class="pp-sheet-grid">
            {% if sheet != 'week' %}
            {# ONE WEEKDAY ROW FOR THE WHOLE SHEET, not a `Week of   #}
            {# 19 Oct` strip above every row. Five of those strips   #}
            {# were a third of why a month would not fit.            #}
            <div class="pp-dow-row">
                <div class="pp-dow">Mon</div>
                <div class="pp-dow">Tue</div>
                <div class="pp-dow">Wed</div>
                <div class="pp-dow">Thu</div>
                <div class="pp-dow">Fri</div>
                <div class="pp-dow">Sat</div>
                <div class="pp-dow">Sun</div>
            </div>
            {% endif %}
            {% for week in weeks %}
            <div class="pp-week">
                <div class="pp-grid">
                    {% for day in week.days %}
                    <div class="pp-day{% if not day.in_range %} is-out{% endif %}{% if day.is_today %} is-today{% endif %}">
                        {% if sheet == 'week' %}
                        <div class="pp-colhead">
                            <div class="pp-dow-s">{{ day.date|date:"D" }}</div>
                            <div class="pp-num">{{ day.date|date:"j" }}</div>
                        </div>
                        {% else %}
                        {# A BARE NUMBER INSIDE ONE MONTH, THE MONTH  #}
                        {# NAMED WHEN THE RANGE CROSSES ONE: `1` is   #}
                        {# not a date when the sheet runs 19 Oct to   #}
                        {# 14 Nov.                                    #}
                        <span class="pp-date">{% if sheet == 'month' %}{{ day.date|date:"j" }}{% else %}{{ day.date|date:"j M" }}{% endif %}</span>
                        {% endif %}
                        <div class="pp-meals">
                            {% for e in day.entries %}
                            <div class="pp-meal{% if not e.recipe_id %} is-note{% elif e.leftover_of_id %} is-left{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</div>
                            {% endfor %}
                        </div>
                        {% if sheet == 'week' %}<div class="pp-rule"></div>{% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

    </div>

</div>'''


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
    raise SystemExit('RG-1 REFUSED: %s' % msg)


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


def region(text, open_at, close_at, where):
    """The text from `open_at` to the end of `close_at`, both unique."""
    once(text, open_at, where)
    once(text, close_at, where)
    i = text.index(fit(text, open_at))
    j = text.index(fit(text, close_at)) + len(fit(text, close_at))
    if j <= i:
        refuse('%s: the region closes before it opens' % where)
    return i, j


# =====================================================================
# THE SUITE PP-1 LEFT BEHIND
# =====================================================================
# test_print_plan's driven section counts weeks, cells and dimmed
# cells for six ranges. Five of the six are unchanged by this round;
# the sixth is the fault it fixes. A round that changes a shape has to
# move the pin that measures the shape, in the same patcher, or the
# next sweep reports yesterday's design as a regression.
PPT_WAS = """    def grid(qs):
        h = cl.get(url, qs).content.decode('utf-8')
        return {
            'weeks': h.count('class="pp-week"'),
            'cells': len(re.findall(r'class="pp-day(?:[ \"])', h)),
            'out': len(re.findall(r'class="pp-day is-out', h)),
            'html': h,
        }"""

PPT_NOW = """    def grid(qs):
        h = cl.get(url, qs).content.decode('utf-8')
        return {
            'weeks': h.count('class="pp-week"'),
            'cells': len(re.findall(r'class="pp-day(?:[ \"])', h)),
            'out': len(re.findall(r'class="pp-day is-out', h)),
            # RG-1, 21 Oct 2026 - which of the four sheets came back.
            # A day is no longer a week with six columns greyed out,
            # so the count of cells is not on its own a description of
            # what was printed.
            'sheet': (re.findall(r'class="pp-page is-(\\w+)"', h) or
                      ['?'])[0],
            'html': h,
        }"""

PPT_DAY_WAS = """    ok(seen.get('day') == (1, 7, 6),
       'A DAY is one week of grid with one day lit and six dimmed',
       seen.get('day'))"""

PPT_DAY_NOW = """    # RG-1, 21 Oct 2026 - THIS CLAIM IS THE FAULT, INVERTED.
    #
    # It read: "A DAY is one week of grid with one day lit and six
    # dimmed" - (1, 7, 6) - and it passed, every time, because that
    # is exactly what the page did. Demetri reported it as "Day view
    # Print, prints a Week view", and he was right: it was a week.
    # The suite measured the thing and agreed with it.
    #
    # A day is now a day sheet: no grid, no cells, nothing dimmed.
    ok(seen.get('day') == (0, 0, 0),
       'A DAY DRAWS NO GRID AT ALL - RG-1. It was (1, 7, 6): one '
       'week of grid with six columns greyed out, which is what '
       '"Day view Print, prints a Week view" was',
       seen.get('day'))
    ok(sheets_seen.get('day') == 'day',
       '  and the page says which sheet it is', sheets_seen.get('day'))
    ok(sheets_seen.get('week') == 'week'
       and sheets_seen.get('month') == 'month'
       and sheets_seen.get('range') == 'range',
       '  as do the other three - the range decides the sheet',
       sheets_seen)"""

PPT_SEEN_WAS = """        g = grid(qs)
        seen[name] = (g['weeks'], g['cells'], g['out'])"""

PPT_SEEN_NOW = """        g = grid(qs)
        seen[name] = (g['weeks'], g['cells'], g['out'])
        sheets_seen[name] = g['sheet']   # RG-1, 21 Oct 2026"""

PPT_INIT_WAS = "seen, shapes, planner = {}, None, {}"
PPT_INIT_NOW = ("seen, shapes, planner = {}, None, {}\n"
                "sheets_seen = {}          # RG-1, 21 Oct 2026")

PPT_PAGE_WAS = """    c['  and it styles its own container'] = (
        'class="pp-page"' in page
        and 'class="calendar-container"' not in page)"""

PPT_PAGE_NOW = """    c['  and it styles its own container'] = (
        # RG-1, 21 Oct 2026 - the attribute reads `pp-page is-month`
        # now, so the exact-string form stopped matching a page that
        # is still doing the right thing. A word boundary asks the
        # question PP-1 meant: is this page wearing its OWN container
        # rather than one meal_planner.html defines?
        bool(re.search(r'class="pp-page\\b', page))
        and 'class="calendar-container"' not in page)"""

PPT_RANGE_WAS = """            ('ragged', {'from': '2026-10-21', 'to': '2026-11-03'}),"""
PPT_RANGE_NOW = """            ('ragged', {'from': '2026-10-21', 'to': '2026-11-03'}),
            # RG-1, 21 Oct 2026 - the same dates under the name the
            # page now gives that shape.
            ('range', {'from': '2026-10-21', 'to': '2026-11-03'}),"""


# =====================================================================
# THE CENSUSES THIS ROUND MOVES
# =====================================================================
# THREE SUITES COUNT THE WHOLE TREE, and this round redraws a page's
# entire stylesheet. Every one of these was MEASURED by running the
# suite against the applied tree, never typed from an estimate - the
# same four that PP-1 moved when it created the page.
CENSUS = (
    ('test_pair_contrast.py',
     'EXPECT_PAIRS = 719   # PP-1, 20 Oct 2026',
     'EXPECT_PAIRS = 724   # RG-1, 21 Oct 2026 - the printed sheet is '
     'drawn again from four layouts, and five more of its rules set a '
     'fill and an ink together: the pill in its three states, the '
     'today marker and the dimmed cell. Every one is a token pair '
     'this table already knows.   # (was 719)   # PP-1, 20 Oct 2026'),
    ('test_surface_border.py',
     'N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 94',
     'N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   '
     '# RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is '
     'filled with the panel wash, which is a BACKGROUND use of the '
     'token and so one more of the uses F2a settled and this suite '
     'refuses to re-open.'),
    ('test_surface_border.py',
     'N_GAINED = 78   # PP-1, 20 Oct 2026',
     'N_GAINED = 79   # RG-1, 21 Oct 2026 - one more: the frame round '
     'the whole sheet. PP-1 drew a frame per week and a rule under '
     'each week label; this draws one frame and one weekday row, and '
     'the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026'),
    ('test_important_base.py',
     'IMP_TREE = 769   # PP-1, 20 Oct 2026',
     'IMP_TREE = 771   # RG-1, 21 Oct 2026 - two more in the same '
     'print block: the one that takes base three <br> and its centred '
     'copyright line off the paper, and the one that zeroes the user '
     'agent own body margin. 68px of screen furniture, which on A4 '
     'landscape is a tenth of the sheet and was why every shape '
     'printed on two pages. The suite second claim - that every '
     'declaration is beating Bootstrap or a sibling rather than base '
     '- was re-run and still holds.   # (was 769)   '
     '# PP-1, 20 Oct 2026'),
)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'RG-1' in t:
        print('RG-1  already applied - the sheet follows the range.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, MEASURED RATHER THAN NAMED. One layout, given
    # every range. If the page already branched, this round is aimed
    # at a tree that has moved.
    code = T.code_only(t)
    if '{% if sheet' in code or 'is-day' in code:
        refuse('%s: the page already chooses a shape' % TPL)
    if code.count('class="pp-week"') != 1:
        refuse('%s: expected exactly one week block to redraw, found %d'
               % (TPL, code.count('class="pp-week"')))

    pv = os.path.join(root, VIEW)
    v = read(pv)
    vcode = T.python_code_only(v, payloads=True)
    for probe, why in (('def meal_plan_print', 'the page this redraws'),
                       ('def day_label', 'how a date is spoken'),
                       ('def monday_of', 'where a week starts')):
        if probe not in vcode:
            refuse('%s: %s is missing (%s)' % (VIEW, probe, why))
    if "'sheet'" in vcode:
        refuse('%s: a sheet is already chosen somewhere' % VIEW)

    # ---- THE VIEW
    v = swap(v, DAYS_WAS, DAYS_NOW, '%s (the weekday)' % VIEW)
    v = swap(v, TAIL_WAS, TAIL_NOW, '%s (the sheet)' % VIEW)
    out[pv] = v

    # ---- THE PAGE. Two regions, both anchored and both unique.
    i, j = region(t, '<style>', '</style>', '%s (the stylesheet)' % TPL)
    t = t[:i] + fit(t, CSS) + t[j:]
    i, j = region(t, '<div class="pp-page">', '</div>\n\n{% endblock %}',
                  '%s (the sheet)' % TPL)
    t = t[:i] + fit(t, BODY) + t[j - len(fit(t, '\n\n{% endblock %}')):]
    out[pt] = t

    # ---- THE PIN PP-1 LEFT, MOVED IN THE SAME PATCHER
    pp = os.path.join(root, PRINTT)
    s = read(pp)
    s = swap(s, PPT_INIT_WAS, PPT_INIT_NOW, '%s (the dict)' % PRINTT)
    s = swap(s, PPT_WAS, PPT_NOW, '%s (the reader)' % PRINTT)
    s = swap(s, PPT_PAGE_WAS, PPT_PAGE_NOW, '%s (the container)' % PRINTT)
    s = swap(s, PPT_RANGE_WAS, PPT_RANGE_NOW, '%s (the ranges)' % PRINTT)
    s = swap(s, PPT_SEEN_WAS, PPT_SEEN_NOW, '%s (the record)' % PRINTT)
    s = swap(s, PPT_DAY_WAS, PPT_DAY_NOW, '%s (the day)' % PRINTT)
    out[pp] = s

    # ---- THE CENSUSES, MOVED IN THE SAME PATCHER
    for name, old, new in CENSUS:
        pc = os.path.join(root, name)
        out[pc] = swap(out.get(pc, read(pc)), old, new,
                       '%s (the census)' % name)

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_copy_menus.py'
)""", """    'test_copy_menus.py',
    # RG-1, 21 Oct 2026 - the printed plan has four shapes now, and a
    # month fits on one sheet of A4.
    'test_print_shape.py'
)""", '%s (the suites)' % PS1)
    # PP-1's SENTINEL ON THIS PAGE IS SUPERSEDED. It pointed at
    # 'pp-grid', which this round keeps - so it can no longer tell one
    # version of the file from another, and test_sentinels reports a
    # sentinel that never discriminates. RG-1's own line below does
    # the job PP-1's was written to do.
    g = swap(g, """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'pp-grid'; What = 'PP-1: and it is a week-grid per week, whole weeks with the days outside the range dimmed, because a ragged first week reads as missing data rather than as a boundary' },
""", '', '%s (the PP-1 sentinel)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'BACK ON THE BAR - CP-2';""",
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'is-{{ sheet }}'; What = 'RG-1: the printed sheet follows the range - a day prints a day, a week prints seven columns you can write in, and a month fits on one sheet of A4. Day view used to print a week with six columns greyed out' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'BACK ON THE BAR - CP-2';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # CP-2, 21 Oct 2026 - Copy and Saved Menus, reachable at last.
    'test_copy_menus.py',
]""", """    # CP-2, 21 Oct 2026 - Copy and Saved Menus, reachable at last.
    'test_copy_menus.py',
    # RG-1, 21 Oct 2026 - a printed day that was a week.
    'test_print_shape.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # CP-2, 21 Oct 2026 - a copy of any span, and menus with a door.
    '.bak_copymenus',
]""", """    # CP-2, 21 Oct 2026 - a copy of any span, and menus with a door.
    '.bak_copymenus',
    # RG-1, 21 Oct 2026 - four sheets, and a month on one of them.
    '.bak_printshape',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # RG-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    for cls in ('pp-sheet-grid', 'pp-dow-row', 'pp-dow', 'pp-day',
                'pp-meal', 'pp-date', 'pp-colhead', 'pp-dow-s',
                'pp-num', 'pp-rule', 'pp-row', 'pp-srv', 'pp-notes',
                'pp-notes-label', 'pp-notes-lines', 'pp-foot',
                'pp-period', 'pp-meals', 'pp-empty', 'pp-body',
                'pp-eyebrow', 'pp-count'):
        if ('class="%s"' % cls not in nc
                and 'class="%s ' % cls not in nc
                and '%s{%%' % cls not in nc):
            refuse('%s: .%s is styled and never worn' % (TPL, cls))
        if not re.search(r'\.%s[\s,.:{>+~\[]' % re.escape(cls), nc):
            refuse('%s: .%s is worn and never styled - which is the '
                   'PP-1 fault exactly' % (TPL, cls))
    # NOT ONE LITERAL COLOUR. The renders were built with hex; the
    # page is built with tokens.
    style = nc[nc.index('<style>'):nc.index('</style>')]
    hexes = [h for h in re.findall(r'#[0-9a-fA-F]{3,8}\b', style)]
    if hexes:
        refuse('%s: %d literal colour(s) in the stylesheet: %r'
               % (TPL, len(hexes), hexes[:6]))
    # EVERY WIDTH QUERY NAMES screen - the 21 September print-leak
    # rule, on the one page in this project that exists to be printed.
    naked = [m.group(1).strip()
             for m in re.finditer(r'@media([^{]*)\{', out[pt])
             if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
    if naked:
        refuse('%s: a width query that does not name screen: %r'
               % (TPL, naked))
    # THE TRACKS CAN STILL SHRINK, which is what kept the Sunday
    # column on the paper.
    if 'repeat(7, minmax(0, 1fr))' not in style:
        refuse('%s: the seven tracks are not minmax(0, 1fr)' % TPL)
    # BOTH ORIENTATIONS, EACH BEHIND ITS OWN BRANCH.
    if style.count('@page') != 2 or 'A4 portrait' not in style \
            or 'A4 landscape' not in style:
        refuse('%s: the two @page rules are not both there' % TPL)
    # ONE BAR, ONE PRIMARY, BACK LAST - base 3.4, unchanged by this
    # round and checked because the whole body was rewritten.
    roles = re.findall(r'class="btn (action-[a-z]+)"', nc)
    if roles != ['action-primary', 'action-back']:
        refuse('%s: the bar reads %r, expected primary then back'
               % (TPL, roles))
    if nc.count('page-action-buttons') != 2:
        refuse('%s: %d mentions of the bar, expected 2 - the element '
               'and the print rule' % (TPL, nc.count('page-action-buttons')))
    # AND THE HOUSE HEADING ELEMENTS SURVIVED THE REWRITE.
    for probe in ('<h2 class="page-title-h2">MEAL PLAN</h2>',
                  'class="page-subtitle-h4"'):
        if probe not in out[pt]:
            refuse('%s: the rewrite dropped %r' % (TPL, probe))
    # AND NO RULE ON THIS PAGE NAMES EITHER OF THEM. A shared heading
    # component a page restyles is a component that page has forked;
    # test_heading_components says so about all 151.
    for cls in ('page-title-h2', 'page-subtitle-h4'):
        if re.search(r'\.%s[\s,.:{>+~\[]' % cls, style):
            refuse('%s: a rule on this page names .%s' % (TPL, cls))
    # THE TITLE IS ABOVE THE BAR - test_bar_top, which reads every
    # page in the tree and found this one when the title moved into
    # the sheet.
    # ASKED OF THE MARKUP, NOT THE FILE. The print block names
    # .page-action-buttons to hide it, and that mention is above
    # everything in the body - the first spelling of this gate
    # refused its own output over it.
    mk = nc[nc.index('</style>'):]
    if mk.index('page-title-h2') > mk.index('page-action-buttons'):
        refuse('%s: the bar sits above the title' % TPL)
    # THE VIEW NAMES ALL FOUR SHEETS AND NOTHING ELSE.
    nv = T.python_code_only(out[pv], payloads=True)
    seg = nv[nv.index('def meal_plan_print'):]
    seg = seg[:seg.index('\ndef ', 1)]
    got = sorted(set(re.findall(r"sheet = '(\w+)'", seg)))
    if got != ['day', 'month', 'range', 'week']:
        refuse('%s: the shapes are %r' % (VIEW, got))
    if 'strftime(\'%-d' in seg or 'strftime("%-d' in seg:
        refuse('%s: %%-d is not portable, and day_label exists for '
               'exactly this' % VIEW)

    if CHECK:
        print('RG-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        sheets: %s' % ', '.join(got))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RG-1  applied - the sheet follows the range.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
