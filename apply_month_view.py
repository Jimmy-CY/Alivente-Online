# -*- coding: utf-8 -*-
"""apply_month_view.py - round MV-2, 19 Oct 2026.

RELEASE 4, PUSH 1. THE MONTH IS THE VIEW.

Demetri, testing the live planner: "why does this still have the time
calendar?" - about the 320px mini calendar beside the week. And on the
design: "Monthly Calendar first - full page."

MV-1 built the switcher. This is the view it lands on.

THE MEASUREMENT THAT DECIDED IT, taken before a line was written:

    a seven-column month cell at 1200px
        with the mini calendar kept      113px   ~15 characters
        full page                        162px   ~23 characters
        at 390px, full page               47px   ~5 characters

So the mini calendar is not merely redundant with this grid - A CELL
CANNOT CARRY A RECIPE NAME WHILE IT IS THERE. It had to go for the
month to become a view at all, and it goes here.

AND FIVE CHARACTERS IS NOT A NAME. Below 768px the cells draw marks
and a count instead, which is Demetri's own answer: "I am happy that
the mobile gets dots. All three view everywhere." Both are in the
markup and the stylesheet picks one, because a rule about screen size
belongs in CSS and not in a view.

WHAT A CELL SHOWS. Three names, then "+n more" - his answer to Q1:
"if there are more recipes than can fit in the square, then include +x
more". Three is what 162px holds at the cell's own line height without
the row outgrowing its siblings.

CLICKING A DAY OPENS THE PICKER ON IT - his Q2, in his own words: "I
want it to go straight to the Picker, when I click a day." Removing a
meal is RD-1's chip menu, in the second push of this release.

ONE QUERY FOR THE MONTH. The old mini calendar asked for a set of
DATES THAT HAVE A MEAL; a cell that draws names needs the meals, and
asking per day would be thirty-one queries to paint one screen. [E29]

A NOTE ON THE RECORD. The release plan said the mini calendar would be
"retired into alv_tree.RETIRED". It cannot be: RETIRED is keyed by
retired PAGE, and this is a component inside a page that survives. The
record of its removal is this docstring, this round's entry in
alv_rounds, and the suite that refuses to let the markup come back.

Idempotent. Every file backed up to .bak_monthview.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_monthview'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_month_view.py'
PATCHER = 'apply_month_view.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MV-2, 19 Oct 2026'
CHECK = False


VIEW_WAS = "    # THE MINI MONTH. One query for the dots, not one per plan.\n    first_of_month = date(year, month, 1)\n    if month == 12:\n        month_end = date(year + 1, 1, 1) - timedelta(days=1)\n    else:\n        month_end = date(year, month + 1, 1) - timedelta(days=1)\n    dates_with_meals = set(\n        MealEntry.objects.filter(date__gte=first_of_month,\n                                 date__lte=month_end)\n        .values_list('date', flat=True).distinct())\n\n    calendar_weeks = []\n    for week in monthcalendar(year, month):\n        days, dates = [], []\n        for day_num in week:\n            if day_num == 0:\n                days.append(None)\n                continue\n            d = date(year, month, day_num)\n            dates.append(d)\n            days.append({'day': day_num, 'date': d,\n                         'has_meal': d in dates_with_meals,\n                         'is_today': d == today})\n        row_start = (dates[0] - timedelta(days=dates[0].weekday())\n                     if dates else None)\n        calendar_weeks.append({'days': days, 'week_start': row_start})\n"

VIEW_NOW = '    # ---- THE MONTH - MV-2, 19 Oct 2026. IT IS THE VIEW NOW.\n    #\n    # It was a 320px navigation strip beside the week, carrying one\n    # boolean per day: does this day have a meal. Demetri, testing the\n    # live page: "why does this still have the time calendar?" - and\n    # then, on the design, "Monthly Calendar first - full page".\n    #\n    # MEASURED BEFORE IT WAS BUILT. A seven-column cell at 1200px is\n    # 162px with the sidebar gone and 113px with it kept - twenty-three\n    # characters against fifteen. That measurement is why the mini\n    # calendar is not merely redundant: a cell cannot carry a recipe\n    # name while it is there.\n    first_of_month = date(year, month, 1)\n    if month == 12:\n        month_end = date(year + 1, 1, 1) - timedelta(days=1)\n    else:\n        month_end = date(year, month + 1, 1) - timedelta(days=1)\n\n    # ONE QUERY FOR THE MONTH, and it fetches the MEALS rather than a\n    # set of dates that have one. A cell draws names now, so a boolean\n    # per day is not enough - and asking per day would be thirty-one\n    # queries to paint one screen. [E29]\n    month_by_date = {}\n    for e in (MealEntry.objects\n              .filter(date__gte=first_of_month, date__lte=month_end)\n              .select_related(\'recipe\', \'leftover_of\')\n              .order_by(\'date\', \'sort_order\', \'meal_entry_id\')):\n        month_by_date.setdefault(e.date, []).append(e)\n\n    # THREE SHOWN, THE REST COUNTED. Demetri\'s answer to Q1: "if there\n    # are more recipes than can fit in the square, then include +x\n    # more". Three is what a 162px cell holds at its own line height\n    # without the row outgrowing its siblings, and the fourth line is\n    # the count rather than a fourth name.\n    MONTH_SHOWN = 3\n    month_weeks = []\n    for week in monthcalendar(year, month):\n        row = []\n        for day_num in week:\n            if day_num == 0:\n                row.append(None)\n                continue\n            d = date(year, month, day_num)\n            mine = month_by_date.get(d, [])\n            row.append({\n                \'day\': day_num,\n                \'date\': d,\n                \'is_today\': d == today,\n                \'in_week\': week_start <= d <= week_end,\n                \'entries\': mine[:MONTH_SHOWN],\n                \'more\': max(0, len(mine) - MONTH_SHOWN),\n                \'count\': len(mine),\n            })\n        month_weeks.append(row)\n'

CTX_WAS = "        'calendar_weeks': calendar_weeks,"

CTX_NOW = "        # MV-2, 19 Oct 2026 - month_weeks replaces calendar_weeks.\n        # The old one carried one boolean a day for the mini\n        # calendar's dots; this one carries the meals, because the\n        # month is the view and a cell draws names.\n        'month_weeks': month_weeks,"

LEFT_WAS = '        {# ------------------------------------------------- left panel #}\n        <div class="left-panel">\n            <div class="mini-calendar">\n                <div class="mini-calendar-header">\n                    <button type="button" class="mini-calendar-nav"\n                            onclick="goMonth({{ prev_month.year }}, {{ prev_month.month }})"\n                            aria-label="Previous month">\n                        <i class="fas fa-chevron-left"></i>\n                    </button>\n                    <strong>{{ month_name }}</strong>\n                    <button type="button" class="mini-calendar-nav"\n                            onclick="goMonth({{ next_month.year }}, {{ next_month.month }})"\n                            aria-label="Next month">\n                        <i class="fas fa-chevron-right"></i>\n                    </button>\n                </div>\n\n                <div class="mini-calendar-grid">\n                    <div class="mini-calendar-day-header">Mo</div>\n                    <div class="mini-calendar-day-header">Tu</div>\n                    <div class="mini-calendar-day-header">We</div>\n                    <div class="mini-calendar-day-header">Th</div>\n                    <div class="mini-calendar-day-header">Fr</div>\n                    <div class="mini-calendar-day-header">Sa</div>\n                    <div class="mini-calendar-day-header">Su</div>\n\n                {# THE WEEKS GO INSIDE THE GRID - MC-4, 19 Oct 2026, and  #}\n                {# the grid used to close on the line above this one.     #}\n                {# Each row wears display: contents so that a whole week  #}\n                {# can be painted by one rule while its seven cells still #}\n                {# sit in one seven-column grid - and display: contents   #}\n                {# hands the cells to the row\'s PARENT. With the grid     #}\n                {# closed above, that parent was .mini-calendar, which is #}\n                {# not a grid, so thirty-five day cells stacked in one    #}\n                {# column. Demetri found it on the live site.             #}\n                {% for week in calendar_weeks %}\n                {# MD-1\'s D26: the row you are looking at is marked, and  #}\n                {# it can only match because the view normalises the week #}\n                {# to a Monday before it gets here.                       #}\n                <div class="mini-calendar-week{% if week.week_start and week.week_start == week_start %} selected{% endif %}"\n                     {% if week.week_start %}onclick="goWeek(\'{{ week.week_start|date:\'Y-m-d\'|escapejs }}\')"{% endif %}\n                     data-week-start="{{ week.week_start|date:\'Y-m-d\' }}">\n                    {% for day in week.days %}\n                    <div class="mini-calendar-day {% if not day %}empty{% endif %} {% if day.is_today %}today{% endif %} {% if day.has_meal %}has-meal{% endif %}"\n                         {% if day.date %}data-date="{{ day.date|date:\'Y-m-d\' }}"{% endif %}>\n                        {{ day.day|default_if_none:\'\' }}\n                    </div>\n                    {% endfor %}\n                </div>\n                {% endfor %}\n                </div>{# .mini-calendar-grid - MC-4, 19 Oct 2026 #}\n\n                <div class="calendar-legend">\n                    <div class="legend-item"><span class="legend-dot has-meal"></span> Has a meal</div>\n                    <div class="legend-item"><span class="legend-dot today"></span> Today</div>\n                </div>\n            </div>\n        </div>\n\n'

MONTH_NOW = '        {# ------------------------------------------------ the month #}\n        {#                                                             #}\n        {# MV-2, 19 Oct 2026. Demetri, testing the live planner: "why  #}\n        {# does this still have the time calendar?" - and then, on the #}\n        {# design: "Monthly Calendar first - full page".               #}\n        {#                                                             #}\n        {# THE MINI CALENDAR WAS HERE, a 320px strip carrying one dot  #}\n        {# a day. It is gone, and not merely because it duplicated     #}\n        {# this grid. MEASURED: a seven-column cell at 1200px is 113px #}\n        {# with that strip beside it and 162px without - fifteen       #}\n        {# characters against twenty-three. A cell cannot carry a      #}\n        {# recipe name while the strip is there, so the strip had to   #}\n        {# go for the month to become a view at all.                   #}\n        {#                                                             #}\n        {# CLICKING A DAY OPENS THE PICKER ON IT - Demetri\'s Q2, in    #}\n        {# his own words: "I want it to go straight to the Picker,     #}\n        {# when I click a day."                                        #}\n        {% if view_mode == \'month\' %}\n        <div class="month-panel">\n            <div class="month-header">\n                <div class="week-nav">\n                    <button type="button" class="week-nav-btn"\n                            onclick="goMonth({{ prev_month.year }}, {{ prev_month.month }})"\n                            aria-label="The month before">\n                        <i class="fas fa-chevron-left"></i>\n                    </button>\n                    <span class="week-title">{{ month_name }}</span>\n                    <button type="button" class="week-nav-btn"\n                            onclick="goMonth({{ next_month.year }}, {{ next_month.month }})"\n                            aria-label="The month after">\n                        <i class="fas fa-chevron-right"></i>\n                    </button>\n                    <button type="button" class="week-nav-btn"\n                            onclick="goDay(\'{{ today|date:\'Y-m-d\'|escapejs }}\', \'month\')">\n                        Today\n                    </button>\n                </div>\n                <span class="month-count">{{ month_count }} meal{{ month_count|pluralize }}</span>\n            </div>\n\n            <div class="month-grid">\n                {# THE HEADINGS ARE INSIDE THE GRID. MC-4 is the round #}\n                {# where they were not: the grid closed after them and #}\n                {# thirty-five cells stacked in one column, on the     #}\n                {# live site, because display:contents handed them to  #}\n                {# a plain div. One seven-column grid, one child per   #}\n                {# cell, and no row wrapper to lose.                   #}\n                <div class="month-dow">Mon</div>\n                <div class="month-dow">Tue</div>\n                <div class="month-dow">Wed</div>\n                <div class="month-dow">Thu</div>\n                <div class="month-dow">Fri</div>\n                <div class="month-dow">Sat</div>\n                <div class="month-dow">Sun</div>\n                {% for week in month_weeks %}{% for cell in week %}{% if cell %}\n                <div class="month-cell{% if cell.is_today %} is-today{% endif %}{% if cell.in_week %} in-week{% endif %}"\n                     {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"\n                     aria-label="{{ cell.count }} meal{{ cell.count|pluralize }} on {{ cell.date|date:\'l j F\' }} - add one"\n                     onclick="openPicker(\'{{ cell.date|date:\'Y-m-d\'|escapejs }}\', \'{{ cell.date|date:\'l j F\'|escapejs }}\')"{% endif %}>\n                    <span class="month-daynum">{{ cell.day }}</span>\n                    {# NAMES AT 768px AND UP, MARKS BELOW IT. Five     #}\n                    {# characters is not a name, it is noise - which   #}\n                    {# is why both are in the markup and the CSS picks #}\n                    {# one. Demetri: "I am happy that the mobile gets  #}\n                    {# dots. All three view everywhere."               #}\n                    {% for e in cell.entries %}\n                    <span class="month-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</span>\n                    {% endfor %}\n                    {% if cell.more %}<span class="month-more">+{{ cell.more }} more</span>{% endif %}\n                    {% if cell.dots %}<span class="month-dots" aria-hidden="true">{% for d in cell.dots %}<span class="month-dot {{ d }}"></span>{% endfor %}</span>{% endif %}\n                </div>\n                {% else %}\n                <div class="month-cell is-out"></div>\n                {% endif %}{% endfor %}{% endfor %}\n            </div>\n        </div>\n        {% endif %}\n\n'


# ============================================ THE DOTS, AND THE COUNT
# A DOT PER MEAL, COLOURED BY WHAT IT IS, and computed in the view
# rather than in the template - a template cannot loop a number, and a
# cell below 768px needs one mark per meal rather than one per name
# shown.
DOTS_WAS = """                'entries': mine[:MONTH_SHOWN],
                'more': max(0, len(mine) - MONTH_SHOWN),
                'count': len(mine),
            })
        month_weeks.append(row)
"""
DOTS_NOW = """                'entries': mine[:MONTH_SHOWN],
                'more': max(0, len(mine) - MONTH_SHOWN),
                'count': len(mine),
                # ONE MARK PER MEAL, not one per name shown, and
                # carrying WHAT it is so the phone keeps the
                # distinction the names make at full size. Built here
                # because a template cannot loop a number.
                'dots': ['is-note' if not e.recipe_id
                         else 'is-leftover' if e.leftover_of_id
                         else '' for e in mine[:MONTH_DOTS]],
            })
        month_weeks.append(row)
"""

COUNT_WAS = """    MONTH_SHOWN = 3
"""
COUNT_NOW = """    MONTH_SHOWN = 3
    # FOUR MARKS AND THEN NOTHING. At 47px a cell holds four dots on
    # one line; a fifth wraps and the row grows. The count in the
    # header is what says how many the month really holds.
    MONTH_DOTS = 4
"""

CTXN_WAS = """        'month_weeks': month_weeks,"""
CTXN_NOW = """        'month_weeks': month_weeks,
        # HOW MANY THE MONTH HOLDS. meal_count is the WEEK's, and the
        # month header asking the week's number would be a quiet lie.
        'month_count': sum(len(v) for v in month_by_date.values()),"""


# =================================== THE WEEK IS NOT THE ONLY VIEW NOW
WEEKON_WAS = """        {# ------------------------------------------------ the week #}
        <div class="week-detail-panel">"""
WEEKON_NOW = """        {# ------------------------------------------------ the week #}
        {# SHOWN WHEN THE MONTH IS NOT - MV-2, 19 Oct 2026. This body #}
        {# is still the vertical day-card list Demetri said was not   #}
        {# required; MV-3 and MV-4 are what replace it. Until then it #}
        {# is what Week and Day render, and the Month no longer has   #}
        {# to share the screen with it.                               #}
        {% if view_mode != 'month' %}
        <div class="week-detail-panel">"""

WEEKOFF_WAS = """        </div>
    </div>
</div>

{# ===================================================== the picker #}"""
WEEKOFF_NOW = """        </div>
        {% endif %}{# view_mode != 'month' - MV-2, 19 Oct 2026 #}
    </div>
</div>

{# ===================================================== the picker #}"""


# =============================================================== THE CSS
LAYOUT_WAS = """.calendar-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 25px;
}"""
LAYOUT_NOW = """/* ONE COLUMN - MV-2, 19 Oct 2026. This was `320px 1fr`: a mini
   calendar beside a week. The strip is gone and the month is the
   view, so there is nothing to put in a first column.

   MEASURED, which is why the strip went rather than merely being
   bypassed: a seven-column month cell at 1200px is 113px with it and
   162px without - fifteen characters against twenty-three. */
.calendar-layout {
    display: block;
}

/* ==================== THE MONTH ==================== */
.month-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.month-count {
    margin-left: auto;
    font-size: 13px;
    color: var(--alv-ink-soft);
}

/* SEVEN COLUMNS, AND THE HEADINGS ARE IN THE SAME GRID. MC-4 is the
   round where they were not - the grid closed after them, every week
   row became a sibling, and display:contents handed thirty-five cells
   to a plain div. One grid, one child per cell, no row wrapper. */
.month-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    overflow: hidden;
    background: var(--alv-line-soft);
    gap: 1px;
}

.month-dow {
    background: var(--alv-surface);
    padding: 7px 4px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    /* --alv-ink-soft, NOT --alv-ink-faint. The faint token reads
       2.85:1 on this ground; AA wants 4.5 and ink-soft reads 5.25.
       A weekday heading is a WORD somebody reads. test_pair_contrast
       caught this one - it is the only rule in this round that sets
       both a ground and an ink, so it is the only one that suite
       could see. */
    color: var(--alv-ink-soft);
}

.month-cell {
    background: var(--alv-paper);
    min-height: 104px;
    padding: 5px 5px 6px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    text-align: left;
}

/* A CELL IS A BUTTON - Demetri's Q2: "I want it to go straight to the
   Picker, when I click a day." So it must look live and take the
   keyboard, and the day it opens on is in its aria-label. */
.month-cell[role="button"] {
    cursor: pointer;
}

.month-cell[role="button"]:hover {
    background: var(--alv-surface);
}

.month-cell[role="button"]:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}

.month-cell.is-out {
    background: var(--alv-surface);
}

.month-cell.in-week {
    background: var(--alv-accent-soft);
}

.month-daynum {
    font-size: 12px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    font-variant-numeric: tabular-nums;
    min-width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.month-cell.is-today .month-daynum {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    border-radius: 50%;
}

/* THE NAME, TRUNCATED. 162px holds about twenty-three characters and
   a recipe called "Salad - Butternut Squash Quinoa" is thirty-one, so
   the cell says as much as it can and stops. The full name is one
   click away in the Day view. */
.month-chip {
    display: block;
    width: 100%;
    font-size: 11px;
    line-height: 1.35;
    padding: 1px 5px;
    border-radius: 3px;
    border-left: 2px solid var(--alv-accent);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* THE SAME THREE COLOURS THE DAY CARD USES. A note is MO-1's amber
   and a leftover is the quietest thing on the page, here as there,
   so the month does not teach a second vocabulary. */
.month-chip.is-note {
    background: var(--alv-warn-soft);
    color: var(--alv-warn-ink);
    border-left-color: var(--alv-warn);
}

.month-chip.is-leftover {
    background: var(--alv-surface-deep);
    color: var(--alv-ink-soft);
    border-left-color: var(--alv-neutral);
}

.month-more {
    font-size: 10.5px;
    /* "+3 more" is a word too, and it is the one thing in the cell
       that says there is something you cannot see. */
    color: var(--alv-ink-soft);
    padding-left: 5px;
}

/* THE MARKS ARE FOR THE PHONE and are hidden here - both are in the
   markup and this stylesheet picks one, because which to draw is a
   question about the screen. */
.month-dots {
    display: none;
}

.month-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--alv-accent);
    display: inline-block;
}

.month-dot.is-note {
    background: var(--alv-warn);
}

.month-dot.is-leftover {
    background: var(--alv-neutral);
}

@media screen and (max-width: 767px) {
    /* FIVE CHARACTERS IS NOT A NAME, IT IS NOISE. At 390px a cell is
       47px. Demetri: "I am happy that the mobile gets dots. All three
       view everywhere." So the names go and the marks arrive, in the
       chip's own colours, and tapping the day still opens the picker
       on it. */
    .month-chip,
    .month-more {
        display: none;
    }

    .month-dots {
        display: flex;
        gap: 2px;
        flex-wrap: nowrap;
        padding-left: 2px;
    }

    .month-cell {
        min-height: 54px;
        align-items: center;
        padding: 3px 2px;
        gap: 1px;
    }

    .month-dow {
        font-size: 9px;
        padding: 5px 0;
    }

    .month-daynum {
        font-size: 11px;
        min-width: 18px;
        height: 18px;
    }
}
"""
MINI_WAS = '/* ==================== LEFT PANEL ==================== */\n.left-panel {\n    display: flex;\n    flex-direction: column;\n    gap: 20px;\n}\n\n/* Mini Calendar */\n.mini-calendar {\n    background: var(--alv-paper);\n    border-radius: 12px;\n    padding: 20px;\n    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);\n}\n\n.mini-calendar-header {\n    display: flex;\n    justify-content: space-between;\n    align-items: center;\n    margin-bottom: 15px;\n}\n\n.mini-calendar-header h3 {\n    font-size: 18px;\n    font-weight: 600;\n    color: var(--alv-ink);\n    margin: 0;\n}\n\n.mini-calendar-nav {\n    display: flex;\n    gap: 8px;\n}\n\n.mini-calendar-nav button {\n    background: var(--alv-line-soft);\n    border: none;\n    width: 32px;\n    height: 32px;\n    border-radius: var(--alv-radius-sm);\n    cursor: pointer;\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    transition: all 0.2s;\n}\n\n.mini-calendar-nav button:hover {\n    background: var(--alv-accent);\n    color: var(--alv-on-accent);\n}\n\n.mini-calendar-grid {\n    display: grid;\n    grid-template-columns: repeat(7, 1fr);\n    gap: 2px;\n}\n\n.mini-calendar-day-header {\n    text-align: center;\n    font-size: 11px;\n    font-weight: 600;\n    color: var(--alv-ink-soft);\n    padding: 8px 0;\n}\n\n.mini-calendar-day {\n    text-align: center;\n    padding: 8px 4px;\n    font-size: 13px;\n    border-radius: var(--alv-radius-sm);\n    position: relative;\n    transition: all 0.2s;\n}\n\n/* display: contents, AND THE ROW MUST BE INSIDE THE GRID - MC-4,\n   19 Oct 2026. This rule dissolves the row so its seven day cells\n   become children of the row\'s PARENT, which is what lets one grid\n   lay out every week while .mini-calendar-week.selected still paints\n   a whole row. It is also why the row is not optional furniture: move\n   it out of .mini-calendar-grid and the cells are handed to whatever\n   is outside, which for four weeks on the live site was a plain div -\n   thirty-five cells in one column.\n\n   cursor: pointer belongs to the ROW even though the row draws\n   nothing, because the row is what carries the onclick. */\n.mini-calendar-week {\n    display: contents;\n    cursor: pointer;\n}\n\n.mini-calendar-week:hover .mini-calendar-day:not(.empty) {\n    background: var(--alv-surface-deep);\n}\n\n.mini-calendar-week.selected .mini-calendar-day:not(.empty) {\n    background: var(--alv-accent);\n    color: var(--alv-on-accent);\n}\n\n.mini-calendar-day.empty {\n    color: var(--alv-ink-faint);\n}\n\n.mini-calendar-day.today {\n    font-weight: 700;\n    border: 2px solid var(--alv-accent);\n}\n\n.mini-calendar-day.has-meal::after {\n    content: \'\';\n    position: absolute;\n    bottom: 3px;\n    left: 50%;\n    transform: translateX(-50%);\n    width: 6px;\n    height: 6px;\n    /* A STATUS, NOT A VERB - MC-3. This dot and the legend swatch below\n       say "there is a meal on this day". They keep a green because that\n       is what Demetri reads them by, but it is the palette\'s green. */\n    background: var(--alv-good);\n    border-radius: 50%;\n}\n\n.mini-calendar-day.in-meal-plan {\n    background: var(--alv-accent);\n    color: var(--alv-on-accent);\n}\n\n.mini-calendar-day.in-meal-plan.has-meal::after {\n    background: var(--alv-paper);\n}\n\n.mini-calendar-day.in-meal-plan.today {\n    border-color: var(--alv-paper);\n}\n\n'

MINI_NOW = '/* THE MINI CALENDAR WAS HERE - MV-2, 19 Oct 2026.\n\n   A 320px strip of thirty-one numbers with a dot on the days that\n   had a meal, beside the week. Demetri, testing the live page:\n   "why does this still have the time calendar?"\n\n   IT WENT BECAUSE OF A MEASUREMENT, not because it duplicated the\n   month grid. A seven-column cell at 1200px is 113px with this\n   strip beside it and 162px without - fifteen characters against\n   twenty-three. A cell cannot carry a recipe name while it is\n   there, so the month could not become a view until it went.\n\n   MC-4 lived here too: this grid closed after its seven weekday\n   headers, so every week row was a sibling of it, and a row with\n   display:contents hands its cells to its PARENT. Thirty-five\n   cells in one column, on the live site, for four weeks. The\n   month grid that replaced it has no row wrapper at all. */\n'

P2_WAS = '    .left-panel {\n        flex-direction: row;\n        flex-wrap: wrap;\n    }\n    \n    .mini-calendar {\n        flex: 1;\n        min-width: 280px;\n    }\n    \n'

P2_NOW = ''

P3_WAS = '    /* Left panel - stack the mini calendar above the week */\n    .left-panel {\n        flex-direction: column;\n    }\n\n    /* Mini calendar - tighter */\n    .mini-calendar {\n        padding: 14px;\n        min-width: 0 !important;\n    }\n    .mini-calendar-header h3 {\n        font-size: 16px;\n    }\n    .mini-calendar-day {\n        padding: 7px 2px;\n        font-size: 12px;\n    }\n    .mini-calendar-day-header {\n        font-size: 10px;\n        padding: 6px 0;\n    }\n    .calendar-legend {\n        flex-wrap: wrap;\n        gap: 12px;\n    }\n\n'

P3_NOW = ''


# ============================== A CELL IS A BUTTON, SO THE KEYBOARD
# ROLE=BUTTON IS A PROMISE. A div that says it is a button and only
# answers a mouse is a worse control than a div that says nothing:
# it is announced as pressable and then is not.
#
# DELEGATED, not an onkeydown on each of thirty-one cells. The cells
# are rebuilt on every page load and the handler is one line either
# way, but thirty-one copies of it in the markup is thirty-one places
# for the next round to miss one.
KEY_WAS = """function say(html) {"""
KEY_NOW = """// A MONTH CELL IS A BUTTON - MV-2, 19 Oct 2026, and role="button"
// is a promise that the keyboard can reach it. Delegated, so the
// markup carries the role and nothing else.
document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') { return; }
    var cell = e.target.closest
        && e.target.closest('.month-cell[role="button"]');
    if (!cell) { return; }
    e.preventDefault();
    cell.click();
});

function say(html) {"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'ONE ANCHOR DATE FOR THREE VIEWS'; What = 'MV-1: and the three zoom levels travel on one ?date=, so switching keeps the day you were looking at' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'ONE ANCHOR DATE FOR THREE VIEWS'; What = 'MV-1: and the three zoom levels travel on one ?date=, so switching keeps the day you were looking at' },
    # ------------------------------------------------- MV-2, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="month-grid"'; What = 'MV-2: the month is the view, full page - a cell is 162px without the mini calendar and 113px with it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MINI CALENDAR WAS HERE'; What = 'MV-2: and the 320px strip Demetri asked about is gone, with the record of why it went' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'THREE SHOWN, THE REST COUNTED'; What = 'MV-2: a cell shows three names then +n more - his own answer to what a full day looks like' },"""

SUITE_WAS = """    'test_view_switch.py'
)"""
SUITE_NOW = """    'test_view_switch.py',
    # MV-2, 19 Oct 2026 - the month grid. It RENDERS the thing,
    # because MC-4 is the round where every class name was right
    # and the calendar drew one column.
    'test_month_view.py'
)"""

TREE_WAS = """    'test_view_switch.py',
]"""
TREE_NOW = """    'test_view_switch.py',
    # MV-2, 19 Oct 2026 - the month is the view. Section 4 walks every
    # page in both roots asking whether any other one still names a
    # mini-calendar class, because this round deleted the component.
    'test_month_view.py',
]"""

RD_WAS = """    '.bak_viewswitch',
]"""
RD_NOW = """    '.bak_viewswitch',
    # MV-2, 19 Oct 2026 - the month grid, full page, and the mini
    # calendar deleted. Demetri: "why does this still have the time
    # calendar?" and "Monthly Calendar first - full page". It went on
    # a measurement: a cell is 113px with that strip and 162px
    # without, which is fifteen characters against twenty-three.
    '.bak_monthview',
]"""

WD_WAS = """CONVERTED_N = 116   # MV-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 116   # MV-2, 19 Oct 2026 - one suite in and one retired with the component it judged, so the number does not move   # (was 116)   # MV-1, 19 Oct 2026 - this round own suite"""


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
    raise SystemExit('MV-2 REFUSED: %s' % msg)


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



# ------------------------------- AND THE LEGEND THAT EXPLAINED IT
# "Has a meal" and "Today", under the mini calendar. The strip
# they described is gone, so they describe nothing. The month
# grid needs no legend: a cell carries the names themselves at
# full size, and below 768px the marks are the same three
# colours the chips use.
LEGEND_WAS = '/* Legend */\n.calendar-legend {\n    display: flex;\n    gap: 20px;\n    margin-top: 15px;\n    padding-top: 15px;\n    border-top: 1px solid var(--alv-line);\n    font-size: 12px;\n    color: var(--alv-ink-soft);\n}\n\n.legend-item {\n    display: flex;\n    align-items: center;\n    gap: 6px;\n}\n\n.legend-dot {\n    width: 8px;\n    height: 8px;\n    border-radius: 50%;\n}\n\n.legend-dot.meal {\n    background: var(--alv-good);\n}\n\n.legend-dot.today {\n    border: 2px solid var(--alv-accent);\n    background: var(--alv-paper);\n}\n\n'

LEGEND_NOW = ''


# ========================== MC-4 IS SUPERSEDED, NOT WRONG - RETIRED
# MC-4 FIXED THE MINI CALENDAR. This round deletes it.
#
# That is a different case from PF-2 and PK-1 three hours ago, where
# the SCREEN survived and only the control changed, so the claims were
# rewritten. Here the subject itself is gone: test_mini_grid renders a
# component that no longer exists, and 28 of its 59 checks fail the
# moment this round lands. A suite retires with the thing it judged -
# MN-1 retired two the same way on 18 October.
#
# ITS LESSON IS NOT RETIRED. MC-4 found that the grid closed BEFORE
# the loop that filled it, so every week row was a sibling and
# display:contents handed thirty-five cells to a plain div - one
# column, on the live site, for four weeks. test_month_view carries
# that forward in three places: the headings must be inside the grid,
# there must be no row wrapper at all, and section 3 COUNTS COLUMNS in
# a browser rather than reading class names.
#
# AND ITS SENTINELS GO WITH IT. Both pin strings in markup this round
# deletes. test_bar_order audits all 497 rows against the tree and
# refused the sweep at suite 32 this morning over exactly this, in
# PF-2 - the lesson is three hours old and it is being applied rather
# than re-learned.
GONE_SUITE = 'test_mini_grid.py'

MCSENT_WAS = """    # ------------------------------------------------- MC-4, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEKS GO INSIDE THE GRID'; What = 'MC-4: the mini calendar draws seven columns, not one - Demetri found it on the live site' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'mini-calendar-grid - MC-4'; What = 'MC-4: and the grid closes AFTER the loop that fills it' },
"""
MCSENT_NOW = """    # ---------------------------- MC-4, 19 Oct 2026 - RETIRED by MV-2
    # Both rows pinned strings in the mini calendar's markup, and MV-2
    # deleted the component. The claim they defended - a grid must
    # contain the loop that fills it - is now test_month_view's, which
    # counts COLUMNS in a browser rather than reading a class name.
"""

MCSUITE_WAS = """    # MC-4, 19 Oct 2026 - the mini calendar is a calendar. The
    # first suite in this project that RENDERS it: every check
    # before this one read its class names, and a layout fault
    # is only visible in the picture.
    'test_mini_grid.py',
"""
MCSUITE_NOW = """    # MC-4's test_mini_grid.py was HERE, and is retired by MV-2,
    # 19 Oct 2026 - it rendered the mini calendar and MV-2 deletes
    # it. Its lesson moved to test_month_view.py, which counts
    # columns in a browser for the same reason MC-4 had to.
"""

MCTREE_WAS = """    # MC-4, 19 Oct 2026 - the mini calendar is a calendar. Wide from
    # birth: section 4 asks every page in both roots whether any other
    # one has a row of display: contents outside its grid.
    'test_mini_grid.py',
"""
MCTREE_NOW = """    # MC-4's test_mini_grid.py was HERE - retired by MV-2, 19 Oct
    # 2026, with the component it judged.
"""

# AND MN-1'S ONE CLAIM ABOUT THE STRIP.
#
# test_planner asserts the mini calendar marks the selected week's
# row. The row is gone; the FACT it was defending is not, and it is
# the same fact: looking at a Wednesday should show you which week you
# are in. The month grid tints that week across all seven cells, so
# the claim is repointed rather than dropped.
MNSEL_WAS = """    ok('mini-calendar-week selected' in r.content.decode('utf-8', 'replace'),
       '  and that row is marked selected')"""
MNSEL_NOW = """    # REPOINTED BY MV-2, 19 Oct 2026. This read
    # 'mini-calendar-week selected' - the strip MV-2 deleted. The
    # fact it defends is unchanged: opening a Wednesday must SHOW you
    # which week you are in. The month grid tints that week across all
    # seven of its cells, so the claim moved to the thing that marks
    # it now rather than being dropped with the thing that did.
    _page = r.content.decode('utf-8', 'replace')
    # AS MANY AS THE MONTH HOLDS, WHICH IS NOT ALWAYS SEVEN. A week
    # straddles two months five times a year, and the grid draws only
    # the days of the month it is showing - the first cut of this
    # repair asked for seven and measured six.
    _in = sum(1 for _i in range(7)
              if (r.context['week_start']
                  + _dt.timedelta(days=_i)).month == r.context['month'])
    # COUNTED ON THE CLASS, NOT ON A PREFIX. A cell that is also
    # today reads `month-cell is-today in-week`, so counting
    # 'month-cell in-week' missed exactly one - the first cut of this
    # repair measured six of seven and the odd one out was today.
    _marked = _page.count(' in-week')
    ok(_marked == _in,
       "  and all %d of that week days that this month holds are "
       "marked" % _in, _marked)
    ok(_in >= 1, '    and the week really is in this month', _in)"""


# ============================================== TWO TREE-WIDE RE-PINS
# BOTH ARE REAL MOVEMENT, MEASURED WITH ONLY THIS ROUND APPLIED, and
# neither is a fault being papered over.
#
# EXPECT_PAIRS 700 -> 702. The month grid adds two rules that set both
# a ground and an ink: .month-dow and .month-chip. Both are house
# pairs off base's own tokens.
#
#   It was THREE until the sweep. .month-dow took --alv-ink-faint,
#   which reads 2.85:1 where AA wants 4.5, and test_pair_contrast
#   named it. That was a REPAIR - ink-soft, 5.25:1 - not a pin. A
#   weekday heading is a word somebody reads.
#
# IMP_TREE 804 -> 803, DOWNWARD. The mini calendar's phone block
# carried `min-width: 0 !important` and this round deletes it. A count
# of the live corpus falls with the corpus.
PAIR = 'test_pair_contrast.py'
PAIR_WAS = """EXPECT_PAIRS = 700   # PF-2, 19 Oct 2026"""
PAIR_NOW = """EXPECT_PAIRS = 702   # MV-2, 19 Oct 2026 - the month grid adds .month-dow and .month-chip, both house pairs off base tokens, so the AA table below is untouched. A third rule took --alv-ink-faint at 2.85:1 and was REPAIRED to ink-soft rather than pinned.   # (was 700)   # PF-2, 19 Oct 2026"""

IMP = 'test_important_base.py'

def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    pt = os.path.join(root, TPL)
    v = read(pv)
    t = read(pt)
    t_before = t

    # ---------------------------------------------------------------- 0
    if 'month_weeks' in v:
        print('MV-2  already applied - the month is the view.')
        return 0

    # ---------------------------------------------------------------- 1
    # MV-1 FIRST. This round renders a view the switcher chooses, and
    # without the switcher there is nothing to choose it.
    sys.path.insert(0, root)
    import alv_tree as T
    if 'view_mode' not in T.python_code_only(v, payloads=True):
        refuse('%s has no view_mode - MV-1 has not been applied, and '
               'this round renders the view MV-1 chooses' % VIEW)
    if 'mini-calendar' not in T.code_only(t):
        refuse('%s has no mini calendar to remove' % TPL)

    # ---------------------------------------------------------------- 2
    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the month)' % VIEW)
    v = swap(v, COUNT_WAS, COUNT_NOW, '%s (the dot cap)' % VIEW)
    v = swap(v, DOTS_WAS, DOTS_NOW, '%s (the dots)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    v = swap(v, CTXN_WAS, CTXN_NOW, '%s (the month count)' % VIEW)
    out[pv] = v

    t = swap(t, LEFT_WAS, MONTH_NOW, '%s (the month markup)' % TPL)
    t = swap(t, WEEKON_WAS, WEEKON_NOW, '%s (the week opens)' % TPL)
    t = swap(t, WEEKOFF_WAS, WEEKOFF_NOW, '%s (the week closes)' % TPL)
    t = swap(t, LAYOUT_WAS, LAYOUT_NOW, '%s (the layout)' % TPL)
    t = swap(t, MINI_WAS, MINI_NOW, '%s (the mini calendar CSS)' % TPL)
    t = swap(t, P2_WAS, P2_NOW, '%s (the 1200px overrides)' % TPL)
    t = swap(t, P3_WAS, P3_NOW, '%s (the phone overrides)' % TPL)
    t = swap(t, LEGEND_WAS, LEGEND_NOW, '%s (the legend)' % TPL)
    t = swap(t, KEY_WAS, KEY_NOW, '%s (the keyboard)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, MCSENT_WAS, MCSENT_NOW, "%s (MC-4's sentinels)" % PS1)
    s = swap(s, MCSUITE_WAS, MCSUITE_NOW, "%s (MC-4's suite)" % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    tr = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    tr = swap(tr, MCTREE_WAS, MCTREE_NOW, "%s (MC-4 retired)" % TREE)
    out[ptr] = tr

    pmn = os.path.join(root, 'test_planner.py')
    out[pmn] = swap(read(pmn), MNSEL_WAS, MNSEL_NOW,
                    "test_planner.py (MN-1's selected-week claim)")

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- 3b
    ppc = os.path.join(root, PAIR)
    out[ppc] = swap(read(ppc), PAIR_WAS, PAIR_NOW,
                    '%s (EXPECT_PAIRS)' % PAIR)

    pim = os.path.join(root, IMP)
    im = read(pim)
    m = re.search(r'IMP_TREE = (\d+)', im)
    if not m or m.group(1) != '804':
        refuse('%s: IMP_TREE reads %s, expected 804 - this round takes '
               'exactly one !important out of the tree with the mini '
               "calendar's phone block" % (IMP, m.group(1) if m else '?'))
    out[pim] = im.replace(
        'IMP_TREE = 804',
        'IMP_TREE = 803   # MV-2, 19 Oct 2026 - the mini calendar phone '
        'block carried min-width: 0 !important and this round deletes '
        'the component. A count of the live corpus falls with the '
        'corpus.   # (was 804)', 1)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nt = out[pt]
    markup = T.code_only(nt)
    nv = T.python_code_only(out[pv], payloads=True)

    # THE COMPONENT IS GONE, MARKUP AND STYLE. A class whose rules
    # survive the element is the drift this round itself tripped over
    # an hour ago, in PF-2's dead .picker-filter .alv-seg.
    for dead in ('mini-calendar', 'left-panel', 'calendar_weeks',
                 'calendar-legend', 'legend-dot'):
        if dead in markup:
            refuse('%s: %r survives the removal - a selector that '
                   'matches nothing is a claim about the page that has '
                   'stopped being true' % (TPL, dead))
    if 'calendar_weeks' in nv:
        refuse('%s: calendar_weeks survives' % VIEW)

    # MC-4 IS RETIRED, EVERYWHERE IT WAS REGISTERED. A suite removed
    # from one list and left in another is a suite the gate still
    # tries to run against a component that is gone.
    # THE QUOTED ENTRY, NOT THE NAME. Both files keep a comment
    # saying the suite was retired and where its lesson went - that
    # record is the point - and the first cut of this gate matched its
    # own comment. A comment about a thing is not the thing; this
    # project has paid for that confusion five times in two days and
    # here it is a sixth, inside the gate written to prevent it.
    for where, txt in ((PS1, out[pp]), (TREE, out[ptr])):
        if "'%s'" % GONE_SUITE in txt:
            refuse('%s still REGISTERS %s after the retirement'
                   % (where, GONE_SUITE))
        if GONE_SUITE not in txt:
            refuse('%s does not say where %s went - a suite that '
                   'vanishes without a note is a suite the next reader '
                   'thinks was never there' % (where, GONE_SUITE))
    if 'MC-4' in out[pp] and "RETIRED by MV-2" not in out[pp]:
        refuse('%s: MC-4 is named without saying it was retired' % PS1)

    # ONE GRID, AND THE HEADINGS ARE IN IT - MC-4's whole lesson. The
    # grid must hold seven headings plus one child per cell, with no
    # row wrapper to lose them to.
    # FROM THE OPENING TAG, NOT FROM THE ATTRIBUTE. Starting the walk
    # at `class="month-grid"` leaves the grid's own <div> behind it,
    # so the first heading's </div> took the depth to zero and the
    # slice was one heading long.
    at = markup.find('class="month-grid"')
    if at < 0:
        refuse('%s: there is no month grid' % TPL)
    g = markup.rfind('<div', 0, at)
    depth, end = 0, g
    for m in re.finditer(r'<div\b|</div>', markup[g:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            end = g + m.end()
            break
    grid = markup[g:end]
    if grid.count('class="month-dow"') != 7:
        refuse('%s: the grid holds %d weekday headings, expected 7'
               % (TPL, grid.count('class="month-dow"')))
    if 'month-week' in grid or re.search(r'display:\s*contents', markup):
        refuse('%s: the grid has a row wrapper. MC-4 is the round where '
               'one of those, carrying display:contents, handed '
               'thirty-five cells to a plain div.' % TPL)

    # ONE QUERY FOR THE MONTH, and it fetches meals.
    if 'month_by_date.setdefault' not in nv:
        refuse('%s: the month is not gathered in one pass' % VIEW)
    if 'values_list' in nv.split('month_by_date')[0][-400:]:
        refuse('%s: the month still asks for dates rather than meals'
               % VIEW)

    # BOTH PICTURES ARE IN THE MARKUP AND THE STYLESHEET PICKS ONE.
    if 'month-chip' not in markup or 'month-dots' not in markup:
        refuse('%s: the cell does not carry both a name and a mark'
               % TPL)
    if '@media screen and (max-width: 767px)' not in nt:
        refuse('%s: nothing chooses between them by screen size' % TPL)

    # A CELL IS A BUTTON AND THE KEYBOARD REACHES IT.
    if 'role="button" tabindex="0"' not in markup:
        refuse('%s: the cell is not reachable' % TPL)
    if ".month-cell[role=\"button\"]" not in T.code_only_js(nt):
        refuse('%s: nothing answers the keyboard on a cell' % TPL)

    # TEMPLATE TAGS AND BRACES BALANCE.
    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        da = nt.count(a) - t_before.count(a)
        db = nt.count(b) - t_before.count(b)
        if da != db:
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, da, a, db, b))
    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    if nt.count('{') - nt.count('}') != t_before.count('{') \
            - t_before.count('}'):
        refuse('%s: the braces do not balance as they did' % TPL)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MV-2 --check')
        print('  month grid : 7 headings + one child per cell, no row '
              'wrapper')
        print('  removed    : the mini calendar, markup and %d chars of '
              'CSS' % (len(MINI_WAS) + len(P2_WAS) + len(P3_WAS)))
        print('  layout     : 320px + 1fr  ->  one column')
        print('  cell       : 3 names then +n more; marks below 768px')
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))

    # AND THE RETIRED SUITE LEAVES THE DISK.
    #
    # Deregistering it was not enough: the standards block says every
    # suite ON DISK is on the gate, and test_standards_doc checks it.
    # A suite file sitting there unregistered is one somebody runs by
    # hand, gets 28 failures from, and spends an hour on.
    #
    # BACKED UP FIRST, like every other file this round touches, so
    # revert_all.sh can put it back. MN-1 deleted two the same way.
    gp = os.path.join(root, GONE_SUITE)
    if os.path.isfile(gp):
        backup(gp)
        os.remove(gp)
        print('  retired %s (its backup is beside it)' % GONE_SUITE)
    print('MV-2  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_month_view.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
