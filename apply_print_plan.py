# -*- coding: utf-8 -*-
"""apply_print_plan.py - round PP-1, 20 Oct 2026.

A MEAL PLAN YOU CAN PUT ON THE FRIDGE.

Demetri: "I would like to be able to print a month, week of day in a
presentable format. Also, I should be able to select To and From Dates
and print a Meal Plan."

THERE WAS NO PRINT SUPPORT ON THE PLANNER AT ALL. The only mention of
print in the whole template is a COMMENT about the 21 September
print-leak rule. No @media print, no print view, nothing. The shopping
list has had print rules since SL-1 on 3 October; the plan never did.

HIS TWO ANSWERS COLLAPSE INTO ONE ROUND.

    "a separate printable page"   rather than a print stylesheet over
                                  the screen layout
    "a week-grid per week"        rather than a day-by-day list

A separate page that takes from/to and draws a week-grid per week IS
the answer to both - and "print the month I am looking at" is then
that same page with the two dates filled in from the view, which SL-7
already computes. One rendering to keep in step rather than two.

WHOLE WEEKS, WITH THE EDGES DIMMED. A range starting on a Wednesday
has a ragged first week, and a seven-column grid with three empty
cells at the front reads as missing data rather than as a boundary.
So every week is drawn whole and the days outside the range are
greyed: the grid is always seven columns and you can still see where
the range begins and ends. Demetri was told this and did not ask for
the other.

THE CEILING IS THE SHOPPING LIST'S CEILING. meal_shopping_list stops
at 92 days because the aggregator walks every ingredient of every
recipe; this walks far less, but a plan of four hundred pages is not
a plan either, and two different limits on two pages that take the
same two parameters is how one of them surprises somebody.

IT CREATES ONE TEMPLATE, and says so in CREATES - PF-2 shipped a
module on the 19th only because somebody happened to type its name,
and RD-1 taught the staging tool to read this instead.

Idempotent. Every file backed up to .bak_printplan.
"""
import os
import re
import sys

SUFFIX = '.bak_printplan'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
PRINTP = os.path.join('pages', 'templates', 'meal_plan_print.html')
ME = 'test_print_plan.py'
PATCHER = 'apply_print_plan.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PP-1, 20 Oct 2026'
CHECK = False
CREATES = (PRINTP,)

# =====================================================================
# THE VIEW
# =====================================================================

VIEW_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_entry(request):"""
VIEW_NOW = '''@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plan_print(request):
    """The plan for a range of days, laid out for paper.

    PP-1, 20 Oct 2026. Demetri: "I would like to be able to print a
    month, week of day in a presentable format. Also, I should be able
    to select To and From Dates and print a Meal Plan."

    A SEPARATE PAGE, which is what he chose over a print stylesheet
    on the planner. The screen layout is three views and a switcher;
    paper is one shape, and squeezing one into the other is how both
    end up compromised.

    ?from= AND ?to=, THE SAME TWO THE SHOPPING LIST TAKES. Printing
    the view you are on is then this page with the dates SL-7 already
    computes, rather than a second idea about what a month means.

    WHOLE WEEKS, EDGES DIMMED. A range from a Wednesday has a ragged
    first week, and three empty cells at the front of a seven-column
    grid read as missing data rather than as a boundary. So the grid
    always runs Monday to Sunday and the days outside the range are
    marked out-of-range for the template to grey.

    ONE QUERY. The entries for the whole grid are fetched once and
    bucketed by date; asking per day would be up to 98 queries for a
    quarter.
    """
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    start = week_of(request.GET.get('from'), monday)
    end = week_of(request.GET.get('to'), start + timedelta(days=6))
    if end < start:
        start, end = end, start

    # THE SHOPPING LIST'S OWN CEILING, deliberately the same number.
    # Two limits on two pages that take the same two parameters is how
    # one of them surprises somebody.
    if (end - start).days > 92:
        end = start + timedelta(days=92)
        messages.info(request, 'A plan covers at most 13 weeks. '
                               'Showing the first.')

    grid_start = monday_of(start)
    grid_end = monday_of(end) + timedelta(days=6)

    by_day = defaultdict(list)
    for e in (MealEntry.objects
              .filter(date__gte=grid_start, date__lte=grid_end)
              .select_related('recipe', 'leftover_of')
              .order_by('date', 'sort_order')):
        by_day[e.date].append(e)

    weeks, cursor = [], grid_start
    while cursor <= grid_end:
        days = []
        for i in range(7):
            when = cursor + timedelta(days=i)
            days.append({
                'date': when,
                'in_range': start <= when <= end,
                'is_today': when == today,
                'entries': by_day.get(when, []),
            })
        weeks.append({'start': cursor, 'days': days})
        cursor += timedelta(days=7)

    return render(request, 'meal_plan_print.html', {
        'start': start,
        'end': end,
        'weeks': weeks,
        'day_count': (end - start).days + 1,
        'meal_count': sum(len(v) for k, v in by_day.items()
                          if start <= k <= end),
    })


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def add_meal_entry(request):'''

URL_WAS = """    path('meal_plans/shopping_list/', views.meal_shopping_list, name='meal_shopping_list'),"""
URL_NOW = """    path('meal_plans/shopping_list/', views.meal_shopping_list, name='meal_shopping_list'),
    # PP-1, 20 Oct 2026 - the plan, laid out for paper. Beside the
    # shopping list because it takes the same two parameters.
    path('meal_plans/print/', views.meal_plan_print,
         name='meal_plan_print'),"""

MENU_WAS = """                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetCopyWeek()"
                        data-toggle="modal" data-target="#copyWeekModal">
                    <i class="fas fa-copy"></i> Copy this week to...
                </button>"""
MENU_NOW = """                {# AND PRINT IS IN HERE TOO - PP-1, 20 Oct 2026.          #}
                {#                                                        #}
                {# The Print button above is an .action-secondary, and     #}
                {# base hides every secondary below 768px IN A BAR THAT    #}
                {# HAS A MORE MENU - deliberately, because the menu is     #}
                {# where they are supposed to have gone. The standard says #}
                {# it in as many words: "If you add a More menu to a bar,  #}
                {# its secondaries start hiding on phones again - that is  #}
                {# the intent, but check the menu lists them."             #}
                {#                                                         #}
                {# MEASURED, NOT ASSUMED: at 390px the Print link came     #}
                {# back display:none, height 0. He asked to print a plan;  #}
                {# a button he cannot reach on his phone is not that.      #}
                {# Only an editing user ever sees this menu, and only an   #}
                {# editing user ever loses the button to it - a read-only  #}
                {# user has no More button, so :has() does not match and   #}
                {# the bar keeps its Print.                                #}
                <a class="action-more-item" role="menuitem"
                   href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}">
                    <i class="fas fa-print"></i> Print this plan
                </a>
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetCopyWeek()"
                        data-toggle="modal" data-target="#copyWeekModal">
                    <i class="fas fa-copy"></i> Copy this week to...
                </button>"""

BTN_WAS = """        {# THE RANGE FOLLOWS THE VIEW - SL-7, 20 Oct 2026. This was  #}"""
BTN_NOW = """        {# PRINT WHAT YOU ARE LOOKING AT - PP-1, 20 Oct 2026. The    #}
        {# same two dates SL-7 computes, handed to a page built for   #}
        {# paper. There was no way to print a plan at all before this: #}
        {# the only mention of print on this screen was a comment.     #}
        <a href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-secondary">
            <i class="fas fa-print"></i> Print
        </a>
        {# THE RANGE FOLLOWS THE VIEW - SL-7, 20 Oct 2026. This was  #}"""

PRINT_TPL = '''{% extends 'base.html' %}
{# meal_plan_print.html - PP-1, 20 Oct 2026.                        #}
{#                                                                  #}
{# THE PLAN, LAID OUT FOR PAPER. Demetri asked to print a month, a  #}
{# week or a day "in a presentable format", and for a from/to range. #}
{# He chose a separate page over a print stylesheet on the planner,  #}
{# and a week-grid per week over a day-by-day list.                  #}
{#                                                                   #}
{# WHOLE WEEKS, EDGES DIMMED. A range from a Wednesday would give a   #}
{# ragged first week, and empty cells at the front of a seven-column  #}
{# grid read as missing data rather than as a boundary.               #}
{% block title %}Meal Plan{% endblock %}

{% block content %}

<style>
/* PAPER FIRST, SCREEN SECOND - PP-1, 20 Oct 2026. Every colour is a
   token; nothing here is a literal. */

/* ITS OWN CONTAINER, NOT THE PLANNER'S - PP-1, 20 Oct 2026.
   The first draft of this page wrapped itself in .calendar-container,
   because that is what meal_planner.html wraps itself in. But that
   class is DEFINED IN meal_planner.html, not in base - so on this
   page it is a name with no rules behind it, and the grid ran flush
   to both edges of the window with no padding at all. A class is not
   a style; the style is wherever the style was written. Every other
   standalone meal-plan page declares its own, and so does this one. */
.pp-page {
    max-width: 1600px;
    margin: 0 auto;
    padding: 20px;
}
.pp-head { margin-bottom: 18px; }
.pp-week {
    margin-bottom: 18px;
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    overflow: hidden;
}
.pp-week-label {
    padding: 6px 10px;
    background: var(--alv-surface);
    border-bottom: 1px solid var(--alv-line);
    font-size: 12px;
    font-weight: 600;
    color: var(--alv-ink-soft);
}
/* minmax(0, 1fr), NOT 1fr - PP-1, 20 Oct 2026. A bare `1fr` track is
   minmax(AUTO, 1fr), so it never shrinks below the widest unbreakable
   thing in the cell: seven cells holding BUTTER CHICKEN CURRY pushed
   the grid to 992px inside a 794px sheet of A4, and the Sunday column
   printed off the edge of the paper. minmax(0, ...) lets the track go
   as narrow as the column needs to be, and the wrap below decides
   what happens to the words instead. */
.pp-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.pp-day {
    min-height: 110px;
    padding: 6px 7px;
    border-right: 1px solid var(--alv-line-soft);
    vertical-align: top;
}
.pp-day:last-child { border-right: 0; }
/* OUT OF RANGE IS STILL DRAWN, so the week keeps its seven columns
   and the boundary is visible rather than implied. */
/* DIMMED BY ITS GROUND, NOT BY ILLEGIBLE INK - PP-1, 20 Oct 2026.
   This read `color: var(--alv-ink-faint)` and test_pair_contrast
   named it: ink-faint on surface measures 2.85:1, below AA, and this
   is a page that exists to be read on paper under a kitchen light.
   What marks a day as outside the range is the tinted BACKGROUND;
   the date in it still has to be readable, so the ink is ink-soft -
   5.25:1 on the same ground. */
.pp-day.is-out { background: var(--alv-surface); color: var(--alv-ink-soft); }
.pp-day.is-today .pp-date { color: var(--alv-accent); font-weight: 700; }
.pp-date {
    font-size: 11px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    margin-bottom: 4px;
}
.pp-meal {
    font-size: 11px;
    line-height: 1.35;
    color: var(--alv-ink);
    padding: 2px 0;
    border-bottom: 1px solid var(--alv-line-soft);
    /* A 137px COLUMN AND A LONG NAME. The track can now shrink, so
       something has to give in the cell rather than in the grid. */
    overflow-wrap: anywhere;
    hyphens: auto;
}
.pp-meal:last-child { border-bottom: 0; }
.pp-meal.is-note { color: var(--alv-warn-ink); font-style: italic; }
.pp-meal.is-left { color: var(--alv-ink-soft); }
.pp-tag {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    /* ink-soft, not ink-faint. LEFTOVERS is the word that tells you
       not to cook; 3.00:1 on paper is not where to put it. */
    color: var(--alv-ink-soft);
}
.pp-none { font-size: 11px; color: var(--alv-ink-faint); }

/* AND screen, NOT a bare max-width - a clause naming no media type
   matches print too, which is the 21 September print-leak rule and
   the one thing this page must not get wrong. */
@media screen and (max-width: 767px) {
    .pp-page { padding: 8px; }
    .pp-grid { grid-template-columns: repeat(2, 1fr); }
    .pp-day { min-height: 80px; border-bottom: 1px solid var(--alv-line-soft); }
}

/* LANDSCAPE, BECAUSE THE THING BEING PRINTED IS SEVEN COLUMNS WIDE.
   A4 portrait is about 794 CSS px and A4 landscape about 1123, and a
   week divided seven ways wants the wider sheet: 137px per day against
   95px decides whether a recipe name is read or guessed at. */
@page { size: landscape; margin: 10mm; }

@media print {
    /* THE CHROME GOES. SL-1 does the same on the shopping list, and
       this page exists to be printed rather than to be browsed. */
    nav, .navbar, header, footer,
    .page-action-buttons, .pp-noprint { display: none !important; }
    .pp-week { page-break-inside: avoid; break-inside: avoid; }
    .pp-day { min-height: 92px; }

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
    body { padding-top: 0; }
}
</style>

<div class="pp-page">

    <h2 class="page-title-h2">MEAL PLAN</h2>
    <h4 class="page-subtitle-h4">{{ start|date:"j M" }} &ndash; {{ end|date:"j M Y" }} &mdash; {{ day_count }} day{{ day_count|pluralize }} &mdash; {{ meal_count }} meal{{ meal_count|pluralize }}</h4>

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

    {% for week in weeks %}
    <div class="pp-week">
        <div class="pp-week-label">Week of {{ week.start|date:"j M Y" }}</div>
        <div class="pp-grid">
            {% for day in week.days %}
            <div class="pp-day{% if not day.in_range %} is-out{% endif %}{% if day.is_today %} is-today{% endif %}">
                <div class="pp-date">{{ day.date|date:"D j" }}</div>
                {% for e in day.entries %}
                <div class="pp-meal{% if not e.recipe_id %} is-note{% elif e.leftover_of_id %} is-left{% endif %}">
                    {% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}
                    {% if e.leftover_of_id %}<div class="pp-tag">Leftovers</div>{% endif %}
                </div>
                {% empty %}
                <div class="pp-none">&mdash;</div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}

</div>

{% endblock %}
'''


# =====================================================================
# THE CENSUS PINS - a round that adds a template moves them
# =====================================================================
#
# Three suites count the templates in this tree and one counts the
# pages wearing .page-title-h2. All four are measurements of the
# shape of the tree, deliberately written as literals so that a page
# appearing or disappearing is something somebody has to notice - and
# this round adds a page and gives it that class. Each is off by
# exactly one, which is this file.
#
# RD-1 moved the same four when it added the quick-look pair and left
# its arithmetic in the comment beside the number. So does this.
IB = 'test_important_base.py'
PC = 'test_pair_contrast.py'
RT = 'test_radius_token.py'
SB = 'test_surface_border.py'
JB = 'test_js_buttons.py'
RTN = 'test_recipe_tones.py'
RSB = 'test_recipe_side_b.py'
RET = 'test_retired.py'
HL = 'test_help_label.py'
# ---- AND THE BACK LABEL CENSUS.
#
# This one only appeared on the SECOND sweep, because it is a
# consequence of a repair the first sweep caused. The Print page's
# Back button wore .action-secondary and five suites said so; the
# house Back is .action-back with a <span class="action-back-label">
# that base hides on a phone, leaving a square icon. Taking the house
# treatment means joining the house census: 126 labels become 127.
HL_WAS = """LABELS_TOTAL = 126   # RT-1, 18 Oct 2026"""
HL_NOW = """LABELS_TOTAL = 127   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026"""


# ---- AND THE CONTROL THAT READS A PAST CLAIM OFF TODAY'S DISK.
#
# test_retired's MOVED control says "all 34 present-tense suites
# really did move a number", and it proves it by comparing the LIVE
# file against the backup RT-1 took before it re-aimed them. That
# evidence decays the moment a later round moves one of those numbers
# BACK, and this round does: test_tree_roots held MAIN_N = 143, RT-1
# took it to 142 when MN-1 retired four meal-plan screens, and PP-1
# takes it to 143 again because this round adds a page. The number
# moved, and moved back, and the control now reads as though RT-1 had
# never touched the file.
#
# THE FIRST REPAIR I WROTE WAS WRONG, and it is worth writing down
# why. I reached for alv_rounds.as_left_by - read the file as RT-1
# left it rather than as it is today - and it took the failure from
# one suite to four. MOVED does not hold one round's work: RT-1 put
# most of these here, RD-1 moved three more in on 19 October, and
# this round moves a fourth. Asking "as RT-1 left it" is the wrong
# question for every member RT-1 did not move.
#
# WHAT THE CONTROL REALLY MEANS is that each of these numbers is a
# census of the tree as it stands rather than a claim about the past
# - and the evidence for that is that it has MOVED AT SOME POINT, not
# that it differs from one particular backup today. So ask every
# state of the file this tree still holds: its backups, newest to
# oldest, and the live file. If none of them differs from the
# pre-RT-1 text, the number really never moved.
#
# SECTION 6 ABOVE IS LEFT ALONE, deliberately. The two halves ask
# different questions. This one is about what already happened. That
# one is about what must not happen today - nobody may quietly edit a
# historical census - and it caught a real edit in this very push.
RET_CTRL_WAS = """    if digits(old) == digits(read(p)):
        still.append(name)"""

RET_CTRL_NOW = """    # PP-1, 20 Oct 2026 - ASKED OF EVERY STATE, NOT OF TODAY.
    #
    # This compared the live file against the pre-RT-1 backup, and a
    # number that moves and moves BACK reads as a number that never
    # moved. test_tree_roots held MAIN_N = 143; RT-1 took it to 142
    # when MN-1 retired four screens; PP-1 adds a page and takes it to
    # 143 again. Nothing about RT-1's work changed - the yardstick
    # did.
    #
    # The claim is that each of these numbers is a census of the tree
    # as it stands, and the evidence for that is that it has moved at
    # some point - so every state of the file still on disk is asked,
    # and one difference anywhere is enough. A suite whose number is
    # identical in the pre-RT-1 text, in every backup since, AND
    # today, really has never moved and does not belong in this list.
    states = [read(p)] + [read(p + suf) for suf in alv_rounds.ROUNDS
                          if os.path.isfile(p + suf)]
    if all(digits(old) == digits(st) for st in states):
        still.append(name)"""

TR = 'test_tree_roots.py'
ST = 'test_subtree_tones.py'
HT = 'test_house_title.py'

# ---- THE STYLE BLOCK. Four censuses measure what pages declare, and
# this round declares a page. Each number is re-measured, never
# guessed: the figures below came off the suites themselves after the
# round was applied.
IB_WAS = """IMP_TREE = 764   # RD-3, 20 Oct 2026"""
IB_NOW = """IMP_TREE = 769   # PP-1, 20 Oct 2026 - the printable plan declares five, all of them in its @media print block and all of them beating BOOTSTRAP rather than base: Bootstrap 4's own print stylesheet sets body and .container to min-width: 992px !important, and a page that exists to be printed cannot leave its width to a grid system's idea of a small desktop. The suite's second claim - that every one is beating Bootstrap or a sibling, not base - still holds.   # (was 764)   # RD-3, 20 Oct 2026"""

PC_WAS = """EXPECT_PAIRS = 713   # RD-1 and PS-1, 19 Oct 2026 - the quick-look"""
PC_NOW = """EXPECT_PAIRS = 719   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
# is what moved. The one rule in this round that DID read below AA -
# .pp-day.is-out, ink-faint on surface at 2.85:1 - was REPAIRED to
# ink-soft at 5.25:1 rather than pinned. It is the dimmed background
# that marks a day as outside the range; the date in it still has to
# be legible, and this page is read on paper.   # (was 713)   # RD-1 and PS-1, 19 Oct 2026 - the quick-look"""

RT_WAS = """N_RETIRED = 3
N_TOTAL = N_RADIUS + N_PRE - N_RETIRED
N_STYLE, N_ATTR, N_SCRIPT = 155, 4, 9   # RT-1, 18 Oct 2026"""
RT_NOW = """N_RETIRED = 3
# PP-1, 20 Oct 2026 - AND ONE WAS ADDED AFTER THE ROUND. The total
# stopped being "this round's plus what was already there" when RT-1
# retired three of the conversions; it stops being derivable at all
# once a LATER round declares the token on a page this round never
# saw. meal_plan_print.html gives .pp-week a var(--alv-radius-sm),
# which is the house radius and not a literal - the right thing for
# it to do, and one more in the live corpus.
N_ADDED = 1
N_TOTAL = N_RADIUS + N_PRE - N_RETIRED + N_ADDED
N_STYLE, N_ATTR, N_SCRIPT = 156, 4, 9   # PP-1, 20 Oct 2026 - the printable plan's .pp-week   # (was 155, 4, 9)   # RT-1, 18 Oct 2026"""

SB_WAS = """N_GAINED = 76   # DT-1, 16 Oct 2026"""
SB_NOW = """N_GAINED = 78   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026"""


# ---- THE PAGE COUNT. A new template is a new page, and three suites
# that sweep "every page" hold the number as a literal so that a page
# appearing is something somebody has to notice. It is being noticed.
JB_WAS = """CENSUS_NARROW, CENSUS_WIDE = 117, 141   # RD-1, 19 Oct 2026 - the"""
JB_NOW = """CENSUS_NARROW, CENSUS_WIDE = 117, 142   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the"""

JB_HITS_WAS = """HITS_LOOSE, HITS_TIGHT = 675, 673   # RD-1, 19 Oct 2026 - one scanner"""
JB_HITS_NOW = """HITS_LOOSE, HITS_TIGHT = 677, 675   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner"""

RTN_WAS = """ok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 141,
   '  which is %d of %d' % (117, 141),"""
RTN_NOW = """# PP-1, 20 Oct 2026 - 142. meal_plan_print.html. The narrow half
# does not move: it is not a recipe-side page.
ok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 142,
   '  which is %d of %d' % (117, 142),"""

RSB_WAS = """GATE_WAS, GATE_NOW = 117, 141   # RD-1, 19 Oct 2026 - the quick-look"""
RSB_NOW = """GATE_WAS, GATE_NOW = 117, 142   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look"""

# AND THE NAVIGATION RULE FALLS BY ONE, which is the opposite
# direction and worth saying out loud.
#
# The rule RS-1b REFUSED is "a bar whose ONLY non-Back item is a link
# to another page is navigation, not the page's verb", and the planner
# was one of the thirteen bars it would have touched: its single link
# was Shopping List. This round puts Print beside it, so the bar now
# has two real items and the rule no longer reaches it at all.
#
# The count is read and not frozen precisely so this shows. RS-1b's
# refusal is not weakened by it - the rule would still reverse ten
# shipped decisions - and one fewer page is exposed to a rule nobody
# adopted.
RSB_NAV_WAS = """N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 13, 11   # (was 12, 10)"""
RSB_NAV_NOW = """N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)"""


# ---- AND A SUITE THAT IS NO LONGER PURELY HISTORICAL.
#
# test_retired's thesis is that a census of what a round did is a
# claim about the PAST, and the twenty-two suites in KEPT must not
# move a single integer. test_personal_heads is one of them - and
# RD-3, earlier in this same push, had to rewrite its section 3,
# because the thing that section measured (the Recipe View close
# strip's 8px padding) was DELETED by RD-3 along with the dialog it
# belonged to. Three integers went with it: 8, 16 and a [:50] slice.
#
# That is exactly the move RD-1 made for eleven suites: out of KEPT,
# into MOVED, with the reason written down. A suite that now asserts
# "the strip is gone" is making a present-tense claim about today's
# tree, not a historical one, and MOVED is where those live.
# test_personal_heads already carries RT-1's mark, which is what
# MOVED requires of its members.
RET_KEPT_WAS = """    'test_page_title.py', 'test_personal_heads.py',"""
RET_KEPT_NOW = """    'test_page_title.py',"""

RET_MOVED_WAS = """MOVED = (
    # RD-1, 19 Oct 2026 - moved out of KEPT, where RT-1 filed them."""
RET_MOVED_NOW = """MOVED = (
    # PP-1, 20 Oct 2026 - moved out of KEPT by RD-3, earlier in this
    # same push. RD-3 deleted the Recipe View dialog, and with it the
    # close strip test_personal_heads section 3 measured - so that
    # section was rewritten to assert the strip is GONE, which is a
    # claim about today's tree rather than about what CS-2 did. Three
    # integers went with the old assertion: an 8px padding, a 16px
    # shorthand and a slice. A suite whose subject a later round
    # removed cannot keep every number it had.
    'test_personal_heads.py',
    # RD-1, 19 Oct 2026 - moved out of KEPT, where RT-1 filed them."""

TR_WAS = """MAIN_N = 142   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:"""
TR_NOW = """MAIN_N = 143   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:"""

ST_WALK_WAS = """ok(len(tree) == 150, 'a WALK finds 150 templates', len(tree))"""
ST_WALK_NOW = """# PP-1, 20 Oct 2026 - 151. meal_plan_print.html is the printable
# plan, and it sits flat in pages/templates, so both numbers move.
ok(len(tree) == 151, 'a WALK finds 151 templates', len(tree))"""

ST_FLAT_WAS = """ok(len(top) == 124, '  a flat listing finds 124 - 120 was what H7 """
ST_FLAT_NOW = """ok(len(top) == 125, '  a flat listing finds 125 - 120 was what H7 """

HT_WAS = """ok(len(wearers) == 120,
   '120 templates now wear the class, which is the number base\\'s note """
HT_NOW = """# PP-1, 20 Oct 2026 - 121. meal_plan_print.html carries a
# .page-title-h2 like every other page with a title, so it joins the
# count rather than being an exception to it.
ok(len(wearers) == 121,
   '121 templates now wear the class, which is the number base\\'s note """


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
    raise SystemExit('PP-1 REFUSED: %s' % msg)


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

    if 'def meal_plan_print' in v:
        print('PP-1  already applied - a plan can be printed.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.python_code_only(v, payloads=True)

    # ---- THE GROUND. Each helper asked for by name: a view that
    # calls something which is not there fails at request time, on his
    # machine, not here.
    for probe, why in (
            ('def monday_of', 'the week a date is in'),
            ('def week_of', 'reading a date from the query string'),
            ('defaultdict', 'bucketing the entries by day'),
            ('timezone', 'today'),
            ("'sl_from': sl_from", 'the range SL-7 computes')):
        if probe not in code:
            refuse('%s: %s is missing (%s)' % (VIEW, probe, why))
    if 'meal_plan_print' in read(os.path.join(root, URLS)):
        refuse('%s: the route already exists' % URLS)
    if os.path.exists(os.path.join(root, PRINTP)):
        refuse('%s: the template already exists, and this round '
               'creates it' % PRINTP)

    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the view)' % VIEW)
    out[pv] = v

    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    pt = os.path.join(root, TPL)
    tt = swap(read(pt), BTN_WAS, BTN_NOW, '%s (the button)' % TPL)
    tt = swap(tt, MENU_WAS, MENU_NOW, '%s (the More menu)' % TPL)
    out[pt] = tt

    pcr = os.path.join(root, PRINTP)
    out[pcr] = PRINT_TPL

    # ---- THE CENSUS PINS, moved with the page that moves them
    ptr_ = os.path.join(root, TR)
    out[ptr_] = swap(read(ptr_), TR_WAS, TR_NOW, '%s (MAIN_N)' % TR)
    pst = os.path.join(root, ST)
    st = swap(read(pst), ST_WALK_WAS, ST_WALK_NOW, '%s (the walk)' % ST)
    st = swap(st, ST_FLAT_WAS, ST_FLAT_NOW, '%s (the flat listing)' % ST)
    out[pst] = st
    pht = os.path.join(root, HT)
    out[pht] = swap(read(pht), HT_WAS, HT_NOW, '%s (the wearers)' % HT)

    # ---- AND THE FOUR THAT MEASURE WHAT A PAGE DECLARES
    pib = os.path.join(root, IB)
    out[pib] = swap(read(pib), IB_WAS, IB_NOW, '%s (IMP_TREE)' % IB)
    ppc = os.path.join(root, PC)
    out[ppc] = swap(read(ppc), PC_WAS, PC_NOW, '%s (EXPECT_PAIRS)' % PC)
    prt = os.path.join(root, RT)
    out[prt] = swap(read(prt), RT_WAS, RT_NOW, '%s (the totals)' % RT)
    psb = os.path.join(root, SB)
    out[psb] = swap(read(psb), SB_WAS, SB_NOW, '%s (N_GAINED)' % SB)

    # ---- AND THE THREE THAT SWEEP EVERY PAGE
    pjb = os.path.join(root, JB)
    jb = swap(read(pjb), JB_WAS, JB_NOW, '%s (the census)' % JB)
    jb = swap(jb, JB_HITS_WAS, JB_HITS_NOW, '%s (the scanner hits)' % JB)
    out[pjb] = jb
    prn = os.path.join(root, RTN)
    out[prn] = swap(read(prn), RTN_WAS, RTN_NOW, '%s (117 of N)' % RTN)
    prs = os.path.join(root, RSB)
    rs = swap(read(prs), RSB_WAS, RSB_NOW, '%s (the gate)' % RSB)
    rs = swap(rs, RSB_NAV_WAS, RSB_NAV_NOW,
              '%s (the navigation rule)' % RSB)
    out[prs] = rs

    # ---- AND THE SUITE THAT IS NO LONGER PURELY HISTORICAL
    pre = os.path.join(root, RET)
    re_ = swap(read(pre), RET_KEPT_WAS, RET_KEPT_NOW, '%s (KEPT)' % RET)
    re_ = swap(re_, RET_MOVED_WAS, RET_MOVED_NOW, '%s (MOVED)' % RET)
    re_ = swap(re_, RET_CTRL_WAS, RET_CTRL_NOW, '%s (the control)' % RET)
    out[pre] = re_

    phl = os.path.join(root, HL)
    out[phl] = swap(read(phl), HL_WAS, HL_NOW, '%s (LABELS_TOTAL)' % HL)

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_ce_scratch.py'
)""", """    'test_ce_scratch.py',
    # PP-1, 20 Oct 2026 - the plan, laid out for paper. Section 3
    # asks the page for a ragged range and counts the columns.
    'test_print_plan.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'test_console_encoding.py'; Text = 'alv_conenc_';""",
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def meal_plan_print('; What = 'PP-1: a meal plan can be printed - there was no print support on the planner at all, and the only mention of print on that screen was a comment about the print-leak rule' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'pp-grid'; What = 'PP-1: and it is a week-grid per week, whole weeks with the days outside the range dimmed, because a ragged first week reads as missing data rather than as a boundary' },
    @{ File = 'test_console_encoding.py'; Text = 'alv_conenc_';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # CE-1, 20 Oct 2026 - a suite stops writing into the tree it is
    # being run against, which cost a whole sweep.
    'test_ce_scratch.py',
]""", """    # CE-1, 20 Oct 2026 - a suite stops writing into the tree it is
    # being run against, which cost a whole sweep.
    'test_ce_scratch.py',
    # PP-1, 20 Oct 2026 - the plan on paper, which the application
    # could not do at all.
    'test_print_plan.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # CE-1, 20 Oct 2026 - the probe writes outside the tree.
    '.bak_cescratch',
]""", """    # CE-1, 20 Oct 2026 - the probe writes outside the tree.
    '.bak_cescratch',
    # PP-1, 20 Oct 2026 - a meal plan you can put on the fridge.
    '.bak_printplan',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # PP-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    npt = out[pcr]

    # WHOLE WEEKS, which is the design decision this round turns on.
    if 'monday_of(start)' not in nv:
        refuse('%s: the grid does not begin on a Monday, so a range '
               'from a Wednesday would start ragged' % VIEW)
    # AND THE RANGE IS STILL KNOWN inside it, or nothing can be dimmed.
    if "'in_range'" not in nv:
        refuse('%s: nothing marks which days are inside the range' % VIEW)
    if 'is-out' not in npt:
        refuse('%s: the template does not dim the days outside it'
               % PRINTP)

    # ONE QUERY FOR THE WHOLE GRID. Asking per day is up to 98 for a
    # quarter, and this page is allowed thirteen weeks.
    if 'for e in (MealEntry.objects' not in nv:
        refuse('%s: the entries are not fetched in one pass' % VIEW)

    # THE SAME CEILING AS THE SHOPPING LIST.
    if '(end - start).days > 92' not in nv:
        refuse('%s: this page has a different limit from the shopping '
               'list, which takes the same two parameters' % VIEW)

    # EVERY PHONE QUERY SAYS screen. The 21 Sep print-leak rule, and
    # this is the one page where getting it wrong would be absurd.
    for m in re.finditer(r'@media([^{]*)\{', npt):
        cond = m.group(1)
        if 'max-width' in cond and 'screen' not in cond:
            refuse('%s: a width query names no media type, so it '
                   'matches print too: %r' % (PRINTP, cond.strip()))

    # IT FITS ON THE PAPER. Measured, then gated: a bare `1fr` track
    # is minmax(auto, 1fr) and will not shrink past the widest word in
    # the cell, and base's Bootstrap .container caps itself on paper
    # through a min-width query. Both were real on a 794px sheet.
    if 'repeat(7, minmax(0, 1fr))' not in npt:
        refuse('%s: the seven tracks can refuse to shrink, and the '
               'grid printed 992px wide on a 794px sheet' % PRINTP)
    pblock = npt[npt.index('@media print'):] if '@media print' in npt else ''
    if 'max-width: none !important' not in pblock:
        refuse('%s: the print block does not release the Bootstrap '
               'container base wraps the page in, whose max-width is '
               'set by a min-width query that applies to paper'
               % PRINTP)

    # EVERY CLASS THIS PAGE WEARS IS STYLED SOMEWHERE IT CAN SEE.
    #
    # The first draft wrapped itself in .calendar-container, which is
    # what meal_planner.html wraps itself in - and which meal_planner
    # DEFINES. On this page the name carried no rules at all and the
    # grid ran flush to the window edges. A class is not a style.
    #
    # ASK THE TREE, don't type a list: for every class in this page's
    # own markup, look for a rule in this page's <style>, in base, or
    # in the vendor sheets base loads. Bootstrap and Font Awesome are
    # not in the repository, so their prefixes are allowed by name -
    # everything of ours has to be findable.
    base = T.code_only(read(os.path.join(root, 'pages', 'templates',
                                         'base.html')))
    own = T.code_only(npt)
    sheets = own + '\n' + base
    VENDOR = ('btn', 'fa', 'fas', 'far', 'fab', 'col', 'row',
              'container', 'fa-', 'd-', 'ml-', 'mr-', 'mt-', 'mb-',
              'px-', 'py-', 'text-', 'bg-', 'table', 'form-', 'modal',
              'input-', 'custom-', 'badge', 'close', 'sr-only')
    homeless = []
    body = own[own.index('</style>'):]
    for attr in re.findall(r'class="([^"{}]*)"', body):
        for cls in attr.split():
            if not cls or cls in homeless:
                continue
            if cls in VENDOR or any(cls.startswith(v) for v in VENDOR
                                    if v.endswith('-')):
                continue
            if re.search(r'\.%s[\s,.:{>+~\[]' % re.escape(cls), sheets):
                continue
            homeless.append(cls)
    if homeless:
        refuse('%s: %s - no rule for it on this page, in base, or in '
               'a vendor prefix, so it is a name wearing another '
               'page style' % (PRINTP, ', '.join(homeless)))

    # AND THE BUTTON ON THE PLANNER USES SL-7's DATES rather than a
    # second idea about what a month is.
    nt = T.code_only(out[pt])
    for n, seg in enumerate(nt.split('meal_plan_print')[1:]):
        if 'sl_from' not in seg[:260] or 'sl_to' not in seg[:260]:
            refuse('%s: link %d to the print page does not use the '
                   'range SL-7 computes' % (TPL, n + 1))

    # AND IT IS REACHABLE ON A PHONE.
    #
    # base hides .action-secondary below 768px inside a bar that has a
    # More menu, by design - the menu is where the secondaries went.
    # Measured at 390px before this gate existed, the Print link came
    # back display:none and height 0 for an editing user, because the
    # bar has a menu and the menu did not list it. A button he cannot
    # press on his phone does not answer "I would like to be able to
    # print a month, week or day".
    bar = nt[nt.index('page-action-buttons'):]
    bar = bar[:bar.index('</div>', bar.index('action-more-menu'))] \
        if 'action-more-menu' in bar else bar
    if 'action-more-btn' in bar:
        menu = nt[nt.index('action-more-menu'):]
        menu = menu[:menu.index('</div>', menu.index('action-more-item'))
                    + 6] if 'action-more-item' in menu else ''
        after = nt[nt.index('action-more-menu'):]
        after = after[:after.rindex('action-more-item') + 400]
        if 'meal_plan_print' not in after:
            refuse('%s: this bar has a More menu, so base hides every '
                   '.action-secondary in it below 768px - and the menu '
                   'does not list the print page, so there is no way '
                   'to reach it on a phone' % TPL)

    if CHECK:
        print('PP-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s%s' % (os.path.relpath(k, root),
                                    '   (new)' if k == pcr else ''))
        return 0

    for k, val in sorted(out.items()):
        if k != pcr:
            backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PP-1  applied - a meal plan you can put on the fridge.')
    print('      %d file(s) written (1 new), backed up to %s'
          % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
