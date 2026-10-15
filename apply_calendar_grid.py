# -*- coding: utf-8 -*-
"""apply_calendar_grid.py - round CC-1, 15 Oct 2026.

A MONTH GRID THAT SHOWS EACH EVENT ONCE IS A LIST WEARING A CALENDAR'S
CLOTHES.

Demetri, after a full check of the Celebrations module, in one message:

  "Why is the Celebrations Calendar cutting off on the right (the
   Saturday)?  It seems to only be November."

  "Is there somewhere else that we could put the key ... so that it always
   shows, without scrolling?"

  "I think that the heights of the calendar days need to be standardised,
   and not adjust with more celebrations ... the user must be able to see
   that there are many celebrations, and must be able to click to open up
   a list of all the celebrations for that day."

  "Why is November 2027 blank?  If we only display 1 year of celebrations
   going ahead, then we need to state this and not show a blank calendar."

  "In the Timeline view, would it not make sense to Show one box per date,
   and then group all the members in that box?"

Five findings. Four were right as stated. The first one was right about
the symptom and wrong about the cause, and the fourth is bigger than it
looks.


ONE - THE CUT-OFF IS NOT NOVEMBER. IT IS THE WINDOW WIDTH.      MEASURED
============================================================================
.calendar-table set no table-layout, so it was `auto` and the table had a
MIN-CONTENT FLOOR OF 1021px. .calendar-container set `overflow: hidden`.

That pair is the defect. Below the floor the overflow is not scrolled -
there is no scrollbar to drag - it is CLIPPED AWAY. The Saturday column
does not exist on screen.

Rendered with his own November names, inside .main-content.with-sidebar:

    viewport   table   container   clipped
    1440px     1160    1160         +0
    1366px     1086    1086         +0
    1280px     1021    1000        +21
    1180px     1021     900       +121
    1024px     1021     744       +277
     992px     1021     712       +309

His October screenshot is a ~1740px window and is whole; the November one
is narrower. ANY MONTH CLIPS BELOW ROUGHLY 1300px. The month is a red
herring, and this round says so rather than quietly fixing it.

    table-layout: fixed with seven 14.2857% columns gives +0 OVERFLOW AT
    EVERY WIDTH TESTED, and makes the text-overflow: ellipsis already
    sitting on .event-dot actually engage - today it cannot, because the
    cell is free to grow. overflow-x: auto replaces overflow: hidden as a
    backstop, so a future overflow SCROLLS instead of vanishing.


TWO - NOVEMBER 2027 IS BLANK BECAUSE EVERY EVENT IS DRAWN EXACTLY ONCE
============================================================================
CelebrationEvent.get_next_occurrence() returns ONE date - this year's if
it is still ahead, otherwise next year's. The view kept only events whose
single next occurrence fell in the month on screen:

    if next_occurrence and next_occurrence.month == month \\
            and next_occurrence.year == year:

So a birthday on 20 November appears in NOVEMBER 2026 AND IN NO OTHER
NOVEMBER, EVER. Forward to November 2027: blank. Back to November 2025:
blank.

    AND IT IS ALREADY WRONG IN THE PRESENT, which he did not ask about.
    October 2026 is missing the 1st to the 14th. Today is the 15th, so
    those dates resolved to October 2027.

It is not a year limit. The grid was rendering a slice of a rolling
twelve-month LIST. This round computes occurrences FOR THE MONTH BEING
DISPLAYED, which is what a calendar means.

    THE TRAP INSIDE THAT CHANGE. get_age() and get_years() are both
    derived from get_next_occurrence(). Once any month can show any year,
    the age has to be taken AT THE OCCURRENCE BEING DRAWN or November
    2027 repeats November 2026's ages. Hence age_at(d) and years_at(d);
    the originals keep working and are left alone.


THREE - height ON A <td> IS A MINIMUM, NOT A HEIGHT
=====================================================
.calendar-table td { height: 120px } is a floor; the row takes its tallest
cell. 25 December 2026 carries 7 chips and 15 August 2027 carries 15,
which is why those weeks balloon. The cell is now clamped, about three
chips show, and a +N more chip opens a day sheet listing everything.

    THE DAY SHEETS ARE REAL MARKUP, NOT BUILT IN SCRIPT. One hidden div
    per day inside the modal body; the script only unhides the right one
    and writes the title. base offers two pop-up patterns and the other
    one - .modal-overlay, used by home and notifications - is a div built
    as a STRING in JavaScript. This round takes the Bootstrap one
    deliberately: VB-1 spent a day on four controls that sat
    three-quarters wrong for weeks because no census could see them, and
    markup a gate can read is worth more than markup that is convenient
    to generate.


FOUR - THE KEY, AND THE TIMELINE
==================================
The legend sat after the table, so a 700px calendar had to be scrolled
past to reach the key to it. It moves to a slim row between the month bar
and the grid.

The timeline emitted one card per EVENT, each repeating the full date and
its own countdown; 25 December renders as seven near-identical cards
saying "Thursday, December 25, 2026". It becomes one box per DATE with the
people grouped inside.

    AND THE COUNTDOWNS LOSE THEIR EMOJI. They read "Today!", "Tomorrow",
    "N days" through the page's own .timeline-event-countdown classes,
    which already carry the imminent and soon tones. The rest of the
    application has no emoji in its chrome.

WHAT THIS ROUND DOES NOT TOUCH
--------------------------------
  the contacts compact view   Demetri chose a modal over expand-in-place.
                              A form and an interaction change should not
                              share a backup suffix with a layout fix.
                              CC-2.
  the mobile timeline-only    The phone has always shown the timeline and
                              hidden the grid. Unchanged, and the timeline
                              it shows is the one this round regroups.

See test_calendar_grid.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_calgrid'
SUITE = 'test_calendar_grid.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
PAGE = 'celebration_calendar.html'
MODELS = os.path.join('pages', 'models.py')
VIEW = os.path.join('pages', 'views', 'celebrations.py')
CHECK = False

MIN_CONTENT_FLOOR = 1021   # measured, the width below which it clipped
CAP = 3                    # chips visible before the +N more chip

CONVERTED_WAS, CONVERTED_NOW = 79, 80
ALIAS_WAS, ALIAS_NOW = 69, 71
ALIAS_P_WAS, ALIAS_P_NOW = 34, 35
ALIAS_S_WAS, ALIAS_S_NOW = 35, 36

# ---------------------------------------------------------------------------
# pages/models.py - occurrences for a MONTH, and an age AT one
# ---------------------------------------------------------------------------
MODEL_WAS = """    def days_until(self):
        \"\"\"Days until next occurrence\"\"\""""

MODEL_NOW = '''    # ---------------------------------------------------------------
    # CC-1, 15 Oct 2026 - A CALENDAR ASKS A DIFFERENT QUESTION.
    #
    # get_next_occurrence() answers "when is this next?" and returns ONE
    # date. A month grid needs "does this fall in THIS month?", and the
    # two are not the same question: asked the first way, a birthday on
    # 20 November exists in November 2026 and in no other November ever,
    # and the 1st to the 14th of the current month vanish the moment the
    # 15th arrives. Demetri found the first half of that as a blank
    # November 2027; the second half nobody had noticed.
    #
    # get_next_occurrence is LEFT ALONE. The dashboard, the timeline
    # countdown and the notification scheduler all want "when is this
    # next?" and are right to.
    def occurrences_in(self, year, month):
        """Every occurrence of this event inside the given month."""
        if not self.is_recurring:
            d = self.event_date
            return [d] if (d.year == year and d.month == month) else []
        if self.event_date.month != month:
            return []
        try:
            return [self.event_date.replace(year=year)]
        except ValueError:
            # 29 February in a non-leap year, handled the same way
            # get_next_occurrence handles it - on the 28th.
            return [self.event_date.replace(year=year, day=28)]

    # AND THE AGE HAS TO BE TAKEN AT THE OCCURRENCE BEING DRAWN.
    # get_age() derives from get_next_occurrence(), so once a grid can
    # show any year it would print November 2026's ages in November 2027.
    def age_at(self, when):
        """Age at a given occurrence, for birthdays with a known year."""
        if self.event_type == 'birthday' and self.event_date.year != 1900 \\
                and when:
            return when.year - self.event_date.year
        return None

    def years_at(self, when):
        """Years at a given occurrence, for anniversaries."""
        if self.event_type == 'anniversary' and self.event_date.year != 1900 \\
                and when:
            return when.year - self.event_date.year
        return None

    def days_until(self):
        """Days until next occurrence"""'''

# ---------------------------------------------------------------------------
# pages/views/celebrations.py
# ---------------------------------------------------------------------------
VIEW_WAS = """    # Build calendar
    cal = monthcalendar(year, month)

    # Map events to calendar days
    events_by_day = {}
    for event in events:
        next_occurrence = event.get_next_occurrence()
        if next_occurrence and next_occurrence.month == month and next_occurrence.year == year:
            day = next_occurrence.day
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

    # Get all upcoming events for timeline view (next 365 days) — workspace-scoped
    all_events = []
    contacts = Contact.objects.for_user(request.user).prefetch_related('celebration_events')

    for contact in contacts:
        for event in contact.celebration_events.all():
            next_date = event.get_next_occurrence()
            if next_date:
                days_until = (next_date - today).days
                if days_until <= 365:  # Show events in next year
                    all_events.append({
                        'contact': contact,
                        'event': event,
                        'next_date': next_date,
                        'days_until': days_until
                    })

    # Sort by next occurrence date
    all_events.sort(key=lambda x: x['next_date'])
"""

VIEW_NOW = '''    # Build calendar
    cal = monthcalendar(year, month)

    # ---------------------------------------------------------------- CC-1
    # OCCURRENCES FOR THE MONTH ON SCREEN, not one "next occurrence" each.
    #
    # This loop used to ask every event for its single next occurrence and
    # keep it only if it landed in the displayed month. A recurring
    # birthday therefore appeared in exactly ONE November for all time,
    # and - because "next" is measured from today - the days already past
    # in the current month resolved to next year and left the current
    # month looking half empty.
    #
    # Demetri: "Why is November 2027 blank? If we only display 1 year of
    # celebrations going ahead, then we need to state this and not show a
    # blank calendar." It was never a one-year limit.
    events_by_day = {}
    for event in events:
        for occ in event.occurrences_in(year, month):
            events_by_day.setdefault(occ.day, []).append({
                'event': event,
                'contact': event.contact,
                'date': occ,
                # AGE AT THIS OCCURRENCE. get_age() reads
                # get_next_occurrence() and would print the same number in
                # every year the grid can now reach.
                'age': event.age_at(occ),
                'years': event.years_at(occ),
            })

    # A STABLE ORDER INSIDE A DAY, so the three chips a cell shows are the
    # same three on every render: type first, then the person.
    for day in events_by_day:
        events_by_day[day].sort(
            key=lambda r: (r['event'].event_type, r['contact'].name or ''))

    # The day sheets the +N more chip opens - an ordered list, because a
    # dict's order is not a promise a template should rely on.
    day_sheets = [(d, events_by_day[d]) for d in sorted(events_by_day)]

    # HOW MANY A CELL IS NOT SHOWING, COUNTED HERE. Django's template
    # language has no subtraction - `add` takes a literal - and a chain
    # of filters pretending otherwise is the kind of thing that returns
    # an empty string and prints "+" with nothing after it.
    day_more = {d: len(rows) - CALENDAR_CHIP_CAP
                for d, rows in events_by_day.items()
                if len(rows) > CALENDAR_CHIP_CAP}

    # ---------------------------------------------------------------- CC-1
    # The timeline is still "what is coming", so it still asks
    # get_next_occurrence - that IS its question. What changes is the
    # shape: one box per DATE with the people grouped inside, rather than
    # one card per event each repeating the same date.
    all_events = []
    contacts = Contact.objects.for_user(request.user).prefetch_related('celebration_events')

    for contact in contacts:
        for event in contact.celebration_events.all():
            next_date = event.get_next_occurrence()
            if next_date:
                days_until = (next_date - today).days
                if days_until <= 365:  # Show events in next year
                    all_events.append({
                        'contact': contact,
                        'event': event,
                        'next_date': next_date,
                        'days_until': days_until,
                        'age': event.age_at(next_date),
                        'years': event.years_at(next_date),
                    })

    # Sort by next occurrence date
    all_events.sort(key=lambda x: (x['next_date'],
                                   x['event'].event_type,
                                   x['contact'].name or ''))

    # Grouped month -> date -> people. Built here rather than with two
    # nested {% regroup %} tags, because the month header needs a count of
    # EVENTS while the boxes under it are counted in DATES.
    timeline_months = []
    for row in all_events:
        d = row['next_date']
        if not timeline_months or timeline_months[-1]['key'] != (d.year, d.month):
            timeline_months.append({'key': (d.year, d.month), 'label': d,
                                    'count': 0, 'dates': []})
        mg = timeline_months[-1]
        mg['count'] += 1
        if not mg['dates'] or mg['dates'][-1]['date'] != d:
            mg['dates'].append({'date': d, 'days_until': row['days_until'],
                                'rows': []})
        mg['dates'][-1]['rows'].append(row)
'''

VIEW_CTX_WAS = """        'events_by_day': events_by_day,
        'all_events': all_events,"""

VIEW_CTX_NOW = """        'events_by_day': events_by_day,
        'day_sheets': day_sheets,
        'day_more': day_more,
        'all_events': all_events,
        'timeline_months': timeline_months,
        'cap': CALENDAR_CHIP_CAP,"""

VIEW_CAP_WAS = """@login_required
@permission_required('auth.can_access_celebrations', raise_exception=True)
def celebration_calendar(request):"""

VIEW_CAP_NOW = """# CC-1, 15 Oct 2026 - how many chips a day cell shows before it says
# "+N more". Three is what fits the clamped cell at the house chip size,
# measured; it lives here rather than in the template so the suite can
# read one number and the cell height can be tuned against it.
CALENDAR_CHIP_CAP = 3


@login_required
@permission_required('auth.can_access_celebrations', raise_exception=True)
def celebration_calendar(request):"""


# ---------------------------------------------------------------------------
# celebration_calendar.html - the grid
# ---------------------------------------------------------------------------
# THE TWO DECLARATIONS THAT CAUSED THE CLIPPING, AND THEIR REPLACEMENTS.
# overflow: hidden on the container turns an overflow into a DELETION -
# there is no scrollbar, the column simply is not there. table-layout:
# fixed removes the min-content floor entirely so there is nothing to
# overflow; overflow-x: auto is the backstop for the day something else
# grows, so that it SCROLLS rather than vanishing.
CSS_CONTAINER_WAS = """.calendar-container {
    background: var(--alv-paper);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.calendar-table {
    width: 100%;
    border-collapse: collapse;
}"""

CSS_CONTAINER_NOW = """.calendar-container {
    background: var(--alv-paper);
    border-radius: 12px;
    /* CC-1, 15 Oct 2026 - WAS overflow: hidden, which does not hide a
       scrollbar, it hides the CONTENT. Measured inside
       .main-content.with-sidebar, the table had a min-content floor of
       1021px and this container clipped everything past it: +21px at a
       1280 viewport, +121 at 1180, +277 at 1024. Demetri saw the
       Saturday column cut off and reasonably read it as a November
       problem; it was any month below roughly 1300px. */
    overflow-x: auto;
    overflow-y: visible;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.calendar-table {
    width: 100%;
    border-collapse: collapse;
    /* THE FLOOR IS GONE. Seven equal columns that never consult their
       content: +0 overflow at every width tested, 992px to 1440px. It
       also makes the text-overflow: ellipsis already on .event-dot
       finally engage - with an auto layout the cell simply grew. */
    table-layout: fixed;
}

.calendar-table th,
.calendar-table td { width: 14.2857%; }"""

CSS_TD_WAS = """.calendar-table td {
    height: 120px;
    vertical-align: top;
    padding: 8px;
    border: 1px solid var(--alv-line);
    position: relative;
}"""

CSS_TD_NOW = """.calendar-table td {
    /* CC-1: height on a <td> is a MINIMUM, not a height - the row takes
       its tallest cell, which is why 25 December (7 chips) and 15 August
       2027 (15) ballooned. The cell is fixed now and .day-events is
       clamped to three chips plus the +N more chip. */
    height: 150px;
    vertical-align: top;
    padding: 8px;
    border: 1px solid var(--alv-line);
    position: relative;
}

/* THE CLAMP IS ARITHMETIC, NOT A GUESS. Measured in Chromium at the
   house sizes:

       day number        21px + 5px margin
       a chip            23px, and three of them 76px
       the +N more chip  23px + 2px margin
       cell padding      8px top and bottom

   so the worst case a cell must hold is 26 + 76 + 2 + 23 + 16 = 143,
   and the cell is 150 rather than 146 because the day number rounds to
   21.5 and a cell that is exactly its content is a cell that grows by a
   pixel the first time a font does.
   The first draft clamped at 92px, which was between the two cases: tall
   enough to push the cell from 128 to 135 when the button appeared, and
   short enough to clip the button if it had not. A clamp has to be
   larger than the content it is clamping or it is a crop. */
.calendar-table td .day-events {
    max-height: 104px;
    overflow: hidden;
}

/* The chip that says there is more, and opens the day. Deliberately not
   a .btn: it sits inside a 14% column at 11px and the house button sizes
   do not belong in a calendar cell. It is a real <button> so it is
   focusable and reachable from the keyboard. */
.day-more {
    all: unset;
    display: block;
    box-sizing: border-box;
    width: 100%;
    margin-top: 2px;
    padding: 2px 6px;
    border-radius: 10px;
    border: 1px dashed var(--alv-accent-line);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    font-size: 11px;
    font-weight: 600;
    text-align: center;
    cursor: pointer;
}
.day-more:hover { background: var(--alv-accent); color: var(--alv-on-accent); }
.day-more:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: 2px;
}

/* THE KEY, ABOVE THE GRID. Demetri: "Is there somewhere else that we
   could put the key ... so that it always shows, without scrolling?
   Maybe under the month, but much smaller?" It was after the table, so a
   700px calendar had to be scrolled past to reach the key to it. */
.event-legend.cal-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 18px;
    margin: 0 0 10px 0;
    padding: 7px 12px;
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    border-radius: 8px;
    font-size: 12px;
}
.cal-legend .legend-color { width: 11px; height: 11px; border-radius: 3px; }

/* One box per DATE in the timeline, with the people inside it. */
.timeline-date-card {
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius);
    background: var(--alv-paper);
    margin-bottom: 10px;
    overflow: hidden;
}
.timeline-date-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    padding: 10px 14px;
    background: var(--alv-surface);
    border-bottom: 1px solid var(--alv-line);
}
.timeline-date-people {
    display: flex;
    flex-direction: column;
}
.timeline-person {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 9px 14px;
    border-left: 4px solid transparent;
}
.timeline-person + .timeline-person { border-top: 1px solid var(--alv-line); }
.timeline-person.birthday    { border-left-color: var(--alv-tag-sky-ink); }
.timeline-person.nameday     { border-left-color: var(--alv-tag-moss-ink); }
.timeline-person.anniversary { border-left-color: var(--alv-tag-clay-ink); }
.timeline-person.custom      { border-left-color: var(--alv-tag-plum-ink); }

/* The day sheet inside the pop-up - one per day, rendered as markup and
   unhidden by id. Nothing here is built in a script. */
.day-sheet-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 9px 2px;
}
.day-sheet-row + .day-sheet-row { border-top: 1px solid var(--alv-line); }"""


# ---------------------------------------------------------------------------
# the markup
# ---------------------------------------------------------------------------
# THE LEGEND MOVES ABOVE THE GRID, and the day cell learns to stop.
GRID_WAS = """<div class="calendar-view-container active" id="calendarView">
    <div class="calendar-container">"""

GRID_NOW = """<div class="calendar-view-container active" id="calendarView">

    <!-- CC-1: the key, between the month bar and the grid it explains. -->
    <div class="event-legend cal-legend">
        <div class="legend-item">
            <div class="legend-color birthday"></div>
            <span>Birthday</span>
        </div>
        <div class="legend-item">
            <div class="legend-color nameday"></div>
            <span>Nameday</span>
        </div>
        <div class="legend-item">
            <div class="legend-color anniversary"></div>
            <span>Anniversary</span>
        </div>
        <div class="legend-item">
            <div class="legend-color custom"></div>
            <span>Custom</span>
        </div>
    </div>

    <div class="calendar-container">"""

LEGEND_WAS = """
    <!-- Legend -->
    <div class="event-legend">
        <div class="legend-item">
            <div class="legend-color birthday"></div>
            <span>Birthday</span>
        </div>
        <div class="legend-item">
            <div class="legend-color nameday"></div>
            <span>Nameday</span>
        </div>
        <div class="legend-item">
            <div class="legend-color anniversary"></div>
            <span>Anniversary</span>
        </div>
        <div class="legend-item">
            <div class="legend-color custom"></div>
            <span>Custom</span>
        </div>
    </div>
</div>"""

LEGEND_NOW = """
</div>"""

CELL_WAS = """                            {% if day in events_by_day %}
                            <div class="day-events">
                                {% for event in events_by_day|dict_get:day %}
                                <div class="event-dot {{ event.event_type }}"
                                     title="{{ event.contact.name }} - {{ event.get_event_type_display }}">
                                    <i class="fas {{ event.get_icon }}"></i> {{ event.contact.name }}
                                </div>
                                {% endfor %}
                            </div>
                            {% endif %}"""

CELL_NOW = """                            {% if day in events_by_day %}
                            {% comment %}
                               CC-1: the cell shows `cap` chips and then
                               says how many it is not showing. The
                               number comes from the view so the suite
                               can read one value and the cell height can
                               be tuned against it.
                            {% endcomment %}
                            <div class="day-events">
                                {% for row in events_by_day|dict_get:day %}
                                {% if forloop.counter <= cap %}
                                <div class="event-dot {{ row.event.event_type }}"
                                     title="{{ row.contact.name }} - {{ row.event.get_event_type_display }}">
                                    <i class="fas {{ row.event.get_icon }}"></i> {{ row.contact.name }}
                                </div>
                                {% endif %}
                                {% endfor %}
                                {% with more=day_more|dict_get:day %}
                                {% if more %}
                                <button type="button" class="day-more"
                                        data-day="{{ day }}"
                                        data-label="{{ month_name }} {{ day }}, {{ year }}">
                                    +{{ more }} more
                                </button>
                                {% endif %}
                                {% endwith %}
                            </div>
                            {% endif %}"""

# THE POP-UP, AND THE SHEETS IT SHOWS.
MODAL_ANCHOR = """<!-- Timeline/List View -->"""

MODAL_NEW = """<!-- CC-1, 15 Oct 2026 - THE DAY SHEET.
     Demetri: "On days where there are multiple celebrations, the user
     must be able to see that there are many celebrations, and must be
     able to click to open up a list of all the celebrations for that
     day."

     ONE HIDDEN DIV PER DAY, RENDERED AS MARKUP. base offers two pop-up
     patterns; the other one - .modal-overlay, used by home and
     notifications - is a div built as a STRING in JavaScript. This takes
     the Bootstrap one on purpose. VB-1 spent a round on four controls
     that sat three-quarters wrong for weeks because they carried no
     house class and no census could see them; markup a gate can read is
     worth more than markup that is convenient to generate. The script
     below unhides one div and writes a title. That is all it does. -->
<div class="modal fade" id="dayModal" tabindex="-1" role="dialog"
     aria-labelledby="dayModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="dayModalLabel">Celebrations</h5>
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body" id="dayModalBody">
                {% for day, rows in day_sheets %}
                <div class="day-sheet" id="day-sheet-{{ day }}" hidden>
                    {% for row in rows %}
                    <div class="day-sheet-row">
                        <span class="timeline-event-name">
                            <i class="fas {{ row.event.get_icon }}"></i>
                            {{ row.contact.name }}
                        </span>
                        <span class="alv-tag {{ row.event.tone_class }} timeline-event-badge">
                            {{ row.event.get_event_type_display }}
                        </span>
                        {% if row.age %}
                            <span class="text-muted">(Turning {{ row.age }})</span>
                        {% elif row.years %}
                            <span class="text-muted">({{ row.years }} years)</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
            <div class="modal-footer">
                <button type="button" class="btn action-secondary"
                        data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- Timeline/List View -->"""

SCRIPT_ANCHOR = """function toggleCalendarView() {"""

SCRIPT_NEW = """// CC-1, 15 Oct 2026 - the day sheet. Every sheet is already in the page
// as markup; this shows the one that was asked for and hides it again on
// close, so the pop-up never holds two days at once.
document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.day-more') : null;
    if (!btn) { return; }
    var sheet = document.getElementById('day-sheet-' + btn.dataset.day);
    if (!sheet) { return; }
    var sheets = document.querySelectorAll('.day-sheet');
    for (var i = 0; i < sheets.length; i++) { sheets[i].hidden = true; }
    sheet.hidden = false;
    document.getElementById('dayModalLabel').textContent =
        btn.dataset.label || 'Celebrations';
    $('#dayModal').modal('show');
});

function toggleCalendarView() {"""

# THE TIMELINE - one box per DATE.
TIMELINE_WAS_HEAD = """    {% regroup all_events by next_date.month as events_by_month %}

    {% if all_events %}
        {% for month_group in events_by_month %}
        <div class="timeline-month">
            <div class="timeline-month-header">
                <h4>
                    <i class="fas fa-calendar"></i>
                    {{ month_group.list.0.next_date|date:"F Y" }}
                </h4>
                <span class="timeline-event-count">{{ month_group.list|length }} event{{ month_group.list|length|pluralize }}</span>
            </div>

            <div class="timeline-events">"""

TIMELINE_NOW_HEAD = """    {% comment %}
       CC-1, 15 Oct 2026 - Demetri: "In the Timeline view, would it not
       make sense to Show one box per date, and then group all the
       members in that box?" It did. 25 December rendered as seven
       near-identical cards each repeating "Thursday, December 25, 2026"
       and its own countdown.

       The grouping is built in the VIEW, because the month header counts
       EVENTS while the boxes under it are counted in DATES, and two
       nested regroup tags cannot say that.

       AND THIS IS A comment TAG, NOT A {-# #-} ONE. Django's hash
       comment is single-line; written across several lines it stops
       being a comment, and the regroup named above was parsed as a real
       tag - "regroup tag takes five arguments" - which is how this was
       found.
    {% endcomment %}
    {% if timeline_months %}
        {% for month_group in timeline_months %}
        <div class="timeline-month">
            <div class="timeline-month-header">
                <h4>
                    <i class="fas fa-calendar"></i>
                    {{ month_group.label|date:"F Y" }}
                </h4>
                <span class="timeline-event-count">{{ month_group.count }} event{{ month_group.count|pluralize }}</span>
            </div>

            <div class="timeline-events">"""

TIMELINE_WAS_BODY = """                {% for event_data in month_group.list %}
                <div class="timeline-event-item {{ event_data.event.event_type }}">
                    <div class="timeline-event-info">
                        <div class="timeline-event-date">
                            {{ event_data.next_date|date:"l, F j, Y" }}
                        </div>
                        <div class="timeline-event-details">
                            <span class="timeline-event-name">
                                <i class="fas fa-user-circle"></i> {{ event_data.contact.name }}
                            </span>
                            <span class="alv-tag {{ event_data.event.tone_class }} timeline-event-badge">
                                {{ event_data.event.get_event_type_display }}
                            </span>
                            {% if event_data.event.get_age %}
                                <span class="text-muted">(Turning {{ event_data.event.get_age }})</span>
                            {% elif event_data.event.get_years %}
                                <span class="text-muted">({{ event_data.event.get_years }} years)</span>
                            {% endif %}
                        </div>
                    </div>

                    <div class="timeline-event-meta">
                        <div class="timeline-event-countdown {% if event_data.days_until <= 1 %}imminent{% elif event_data.days_until <= 7 %}soon{% endif %}">
                            {% if event_data.days_until == 0 %}
                                \U0001f389 Today!
                            {% elif event_data.days_until == 1 %}
                                \U0001f4c5 Tomorrow
                            {% elif event_data.days_until <= 7 %}
                                \u26a1 {{ event_data.days_until }} days
                            {% else %}
                                \U0001f4c6 {{ event_data.days_until }} days
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}"""

TIMELINE_NOW_BODY = """                {% for date_group in month_group.dates %}
                <div class="timeline-date-card">
                    <div class="timeline-date-head">
                        <div class="timeline-event-date">
                            {{ date_group.date|date:"l, F j, Y" }}
                        </div>
                        {% comment %}
                           THE COUNTDOWN LOSES ITS EMOJI. It read
                           party-popper Today, calendar Tomorrow,
                           lightning N days. Nothing else in this
                           application puts an emoji in its chrome, and
                           the imminent and soon tones already say the
                           same thing in the house palette.
                        {% endcomment %}
                        <div class="timeline-event-countdown {% if date_group.days_until <= 1 %}imminent{% elif date_group.days_until <= 7 %}soon{% endif %}">
                            {% if date_group.days_until == 0 %}
                                Today
                            {% elif date_group.days_until == 1 %}
                                Tomorrow
                            {% else %}
                                {{ date_group.days_until }} days
                            {% endif %}
                        </div>
                    </div>

                    <div class="timeline-date-people">
                        {% for row in date_group.rows %}
                        <div class="timeline-person {{ row.event.event_type }}">
                            <span class="timeline-event-name">
                                <i class="fas {{ row.event.get_icon }}"></i> {{ row.contact.name }}
                            </span>
                            <span class="alv-tag {{ row.event.tone_class }} timeline-event-badge">
                                {{ row.event.get_event_type_display }}
                            </span>
                            {% if row.age %}
                                <span class="text-muted">(Turning {{ row.age }})</span>
                            {% elif row.years %}
                                <span class="text-muted">({{ row.years }} years)</span>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}"""

TIMELINE_EMPTY_WAS = """    {% else %}
        <div class="no-events-timeline">"""

TIMELINE_EMPTY_NOW = """    {% else %}
        <div class="no-events-timeline">"""

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
TREE_WAS = """    'test_pdf_viewer.py',
]"""
TREE_NOW = """    'test_pdf_viewer.py',
    # CC-1, 15 Oct 2026 - the celebration grid. A month that showed each
    # event once, a table that clipped its own Saturday, cells that grew
    # with their content, and a key below the thing it explains.
    'test_calendar_grid.py',
]"""

ROUNDS_WAS = """    '.bak_pdfview',
]"""
ROUNDS_NOW = """    '.bak_pdfview',
    # CC-1, 15 Oct 2026 - occurrences for the month displayed, a fixed
    # table layout, clamped day cells with a +N more sheet, the key above
    # the grid, and one timeline box per date.
    '.bak_calgrid',
]"""

SUITE_WAS = """    'test_pdf_viewer.py'
)"""
SUITE_NOW = """    'test_pdf_viewer.py',
    'test_calendar_grid.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'pages\\templates\\asset_detail.html'; Text = ':not(.pdf-viewer-modal-dialog)'; What = 'and 963px of buttons stop being laid out on a 390px screen' },"""

CLAIMS = """    @{ File = 'pages\\templates\\asset_detail.html'; Text = ':not(.pdf-viewer-modal-dialog)'; What = 'and 963px of buttons stop being laid out on a 390px screen' },
    # ------------------------------------------------- CC-1, 15 Oct 2026
    # Five findings from a full check of the Celebrations module. The
    # blank November was never a one-year limit - every event was drawn
    # exactly once, so a birthday existed in one November for all time.
    @{ File = 'pages\\models.py'; Text = 'def occurrences_in'; What = 'an event can be asked which days it falls on in a given month' },
    @{ File = 'pages\\models.py'; Text = 'def age_at'; What = 'and the age is taken at the occurrence being drawn, not the next one' },
    @{ File = 'pages\\templates\\celebration_calendar.html'; Text = 'table-layout: fixed'; What = 'the calendar stops clipping its own Saturday column below 1300px' },
    @{ File = 'pages\\templates\\celebration_calendar.html'; Text = 'class="day-more"'; What = 'a busy day says how many it is not showing, and opens a sheet' },
    @{ File = 'pages\\templates\\celebration_calendar.html'; Text = 'cal-legend'; What = 'and the key sits above the grid it explains' },"""

# ---------------------------------------------------------------------------
# THE RULES THAT HAVE NOTHING LEFT TO STYLE
# ---------------------------------------------------------------------------
# .timeline-event-item was the per-event card. Nothing wears it now, and a
# rule with no element is dead weight exactly as an element with no rule is
# a bug - so it goes with the markup rather than sitting behind it. Its
# four tone variants are replaced by .timeline-person's, which do the same
# job one level in; leaving both would be two places to keep one decision.
DEAD_DESK_WAS = """.timeline-event-item {
    background: var(--alv-paper);
    border: 2px solid var(--alv-line);
    border-left: 4px solid;
    border-radius: 8px;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
    gap: 12px;
}

.timeline-event-item:hover {
    transform: translateX(5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.timeline-event-item.birthday {
    border-left-color: var(--alv-tag-sky-ink);
    background: var(--alv-tag-sky-soft);
}

.timeline-event-item.nameday {
    border-left-color: var(--alv-tag-moss-ink);
    background: var(--alv-tag-moss-soft);
}

.timeline-event-item.anniversary {
    border-left-color: var(--alv-tag-clay-ink);
    background: var(--alv-tag-clay-soft);
}

.timeline-event-item.custom {
    border-left-color: var(--alv-tag-plum-ink);
    background: var(--alv-tag-plum-soft);
}

.timeline-event-info {
    flex: 1;
    min-width: 0;
}
"""

DEAD_DESK_NOW = """/* CC-1: .timeline-event-item and .timeline-event-info went with the
   per-event card they styled. The four tone variants live on
   .timeline-person now - one level in, inside the date box. */
"""

DEAD_META_WAS = """.timeline-event-meta {
    display: flex;
    align-items: center;
    gap: 15px;
    flex-shrink: 0;
}
"""
DEAD_META_NOW = """"""

DEAD_PHONE_WAS = """    /* Timeline event items stack info above countdown */
    .timeline-event-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
        padding: 12px 14px;
    }
    .timeline-event-item:hover {
        transform: none;
    }
"""
DEAD_PHONE_NOW = """"""

DEAD_PHONE_META_WAS = """    .timeline-event-meta {
        width: 100%;
        justify-content: flex-start;
        gap: 8px;
    }
"""
DEAD_PHONE_META_NOW = """"""

# ---------------------------------------------------------------------------
# THE TWO SUITES THIS ROUND MOVES
# ---------------------------------------------------------------------------
# RC-2's rule: a pinned COUNT moves when a later round owns part of it; a
# pinned DECISION does not move because a later round finds it convenient.
# Both of these are the first kind.
SB = 'test_surface_border.py'

# ONE CONSTANT WAS DOING TWO JOBS, AND THEY HAVE COME APART.
#
#     before == N_CONVERT   what the BACKUPS carry - a historical fact
#     gained == N_CONVERT   what the live tree gained - a live count
#
# They were the same number for as long as nothing else touched those 43
# pages. CC-1 touches one of them and adds four more borders on
# var(--alv-line) - the key's edge, the timeline date box and two
# hairlines - so `gained` is 82 while `before` stays 78 forever. Raising
# the single constant made the first check fail in order to make the
# second pass, which is not a repair.
SB_CONST_WAS = 'N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 96'
SB_CONST_NOW = (
    '# CC-1, 15 Oct 2026 - N_GAINED SPLIT OFF FROM N_CONVERT. The first\n'
    '# is what the backups carry and can never move; the second is what\n'
    '# the live tree has gained and moves whenever a later round adds a\n'
    '# border to one of these 43 pages. CC-1 adds four to\n'
    '# celebration_calendar: the key edge, the timeline date box, and the\n'
    '# hairlines between people and between day-sheet rows.\n'
    'N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 96\n'
    'N_GAINED = 82')

SB_GAINED_WAS = """ok(gained == N_CONVERT,
   '  and exactly %d gained the border token' % N_CONVERT, gained)"""
SB_GAINED_NOW = """ok(gained == N_GAINED,
   '  and exactly %d gained the border token' % N_GAINED, gained)"""



# FOUR MORE BORDERS ON THE PANEL-WASH TOKEN, net: the key's own edge, the
# date box, and the hairlines between people and between sheet rows -
# less the 2px border the retired per-event card used to draw. Every one
# of them is var(--alv-line), which is what this suite exists to hold.
SB_WAS, SB_NOW = 78, 82

PC = 'test_pair_contrast.py'

# TWO MORE RULES SET BOTH A FILL AND AN INK: .day-more and its hover. Both
# are house pairs - accent-ink on accent-soft, and on-accent on accent -
# which is why this suite's AA check passes unchanged and only the census
# count moves.
PC_WAS, PC_NOW = 704, 706

DR = 'test_drift_root.py'
ET = 'test_event_tones.py'

# ONE MORE .modal-footer, and it is the day sheet's. Both matchers rise by
# the same one, which is the point: the wrapper that arrived is an
# ordinary one. PV-1 took these from 89/88 to 87/86 by retiring two.
DR_WAS = 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 87, 86'
DR_NOW = ('N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 88, 87'
          '   # CC-1, 15 Oct 2026 - the celebration day sheet adds one'
          ' .modal-footer. Both matchers rise by the same one.'
          '   # (was 87, 86)')

# AND A PIN ON A VARIABLE NAME, NOT ON A BADGE. This counted
# `{{ event_data.event.tone_class }}` exactly once. CC-1 regroups the
# timeline, so the loop variable is `row` and the badge now appears TWICE
# on that page - once in the day sheet, once in the timeline person. The
# claim it was making - every badge reads tone_class and nothing reads the
# retired get_color_class - is unchanged and is asked of the TOKEN rather
# than of the name a loop happened to use.
ET_WAS = """ok(mgmt.count('{{ event.tone_class }}') == 1
   and cal.count('{{ event_data.event.tone_class }}') == 1,
   'both badges read tone_class, once each')"""

ET_NOW = """# CC-1, 15 Oct 2026 - RE-POINTED, NOT RETIRED. This pinned the loop
# variable `event_data`, which the timeline regroup renamed to `row`, and
# the calendar now draws the badge twice: the day sheet and the timeline
# person. Asked of the token instead of the name.
ok(mgmt.count('{{ event.tone_class }}') == 1
   and cal.count('tone_class') == 2
   and 'get_color_class' not in cal,
   'every badge reads tone_class - once on management, twice on the '
   'calendar since CC-1 gave it a day sheet')"""

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
    raise SystemExit('CC-1 REFUSED: %s' % msg)


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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the TREE.
    if 'occurrences_in' in read(os.path.join(root, MODELS)):
        print('CC-1  already applied - the model answers for a month.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    p = os.path.join(root, MODELS)
    out[p] = swap(read(p), MODEL_WAS, MODEL_NOW,
                  '%s (occurrences_in / age_at)' % MODELS)

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, VIEW)
    s = read(p)
    s = swap(s, VIEW_CAP_WAS, VIEW_CAP_NOW, '%s (the chip cap)' % VIEW)
    s = swap(s, VIEW_WAS, VIEW_NOW, '%s (the month build)' % VIEW)
    s = swap(s, VIEW_CTX_WAS, VIEW_CTX_NOW, '%s (the context)' % VIEW)
    out[p] = s

    # ---------------------------------------------------------------- 3
    # the template
    p = alv_tree.path_of(PAGE)
    s = read(p)
    for was, now, what in (
            (CSS_CONTAINER_WAS, CSS_CONTAINER_NOW, 'the container and the table'),
            (CSS_TD_WAS, CSS_TD_NOW, 'the cell, the chip and the key'),
            (GRID_WAS, GRID_NOW, 'the key, above the grid'),
            (LEGEND_WAS, LEGEND_NOW, 'the key, gone from below it'),
            (CELL_WAS, CELL_NOW, 'the day cell'),
            (MODAL_ANCHOR, MODAL_NEW, 'the day sheet pop-up'),
            (TIMELINE_WAS_HEAD, TIMELINE_NOW_HEAD, 'the timeline grouping'),
            (TIMELINE_WAS_BODY, TIMELINE_NOW_BODY, 'one box per date'),
            (SCRIPT_ANCHOR, SCRIPT_NEW, 'the day sheet script'),
            (DEAD_DESK_WAS, DEAD_DESK_NOW, 'the dead per-event card'),
            (DEAD_META_WAS, DEAD_META_NOW, 'its dead meta column'),
            (DEAD_PHONE_WAS, DEAD_PHONE_NOW, 'its dead phone rules'),
            (DEAD_PHONE_META_WAS, DEAD_PHONE_META_NOW,
             'its dead phone meta rules')):
        s = swap(s, was, now, '%s (%s)' % (PAGE, what))
    out[p] = s

    # ---------------------------------------------------------------- 4
    # GATES. Each is a thing the survey measured, asserted rather than
    # assumed, and each refuses the whole round rather than writing half.
    body = code_only(s)
    if 'overflow: hidden' in body.split('.calendar-container')[1][:260]:
        refuse('%s: .calendar-container still clips instead of scrolling'
               % PAGE)
    if 'table-layout: fixed' not in body:
        refuse('%s: the table still has no fixed layout - the min-content '
               'floor of %dpx is what clipped the Saturday column'
               % (PAGE, MIN_CONTENT_FLOOR))
    if s.count('class="event-legend') != 1:
        refuse('%s: expected exactly one legend, found %d'
               % (PAGE, s.count('class="event-legend')))
    # ASKED OF THE MARKUP, NOT OF THE FILE. `.calendar-container` is a CSS
    # rule hundreds of lines above the div of the same name, so comparing
    # raw positions compares a stylesheet against a template.
    _leg = s.find('class="event-legend cal-legend"')
    _grid = s.find('<div class="calendar-container">')
    if _leg < 0 or _grid < 0 or _leg > _grid:
        refuse('%s: the key is not above the grid it explains (key at %d, '
               'grid at %d)' % (PAGE, _leg, _grid))
    # NOTHING IN THE POP-UP IS BUILT IN A SCRIPT. The whole argument for
    # the Bootstrap pattern over .modal-overlay is that a census can read
    # this markup, and a round that quietly generated it would have taken
    # the cost of the choice without the benefit.
    for frag in ('day-sheet-row', 'innerHTML'):
        there = frag in body
        if (frag == 'innerHTML') and there:
            refuse('%s: something in this page builds markup as a string'
                   % PAGE)
        if (frag == 'day-sheet-row') and not there:
            refuse('%s: the day sheets are not in the markup' % PAGE)
    for emoji in ('\U0001f389', '\U0001f4c5', '\u26a1', '\U0001f4c6'):
        if emoji in s:
            refuse('%s: an emoji countdown survived' % PAGE)

    # ---------------------------------------------------------------- 5
    # the two suites this round moves, each with its owner named
    p = os.path.join(root, DR)
    out[p] = swap(read(p), DR_WAS, DR_NOW, '%s (the footer wrappers)' % DR)

    p = os.path.join(root, SB)
    s = read(p)
    if 'N_GAINED' in s:
        refuse('%s already separates the two numbers' % SB)
    s = swap(s, SB_CONST_WAS, SB_CONST_NOW, '%s (the two counts)' % SB)
    s = swap(s, SB_GAINED_WAS, SB_GAINED_NOW,
             '%s (the gained check)' % SB)
    out[p] = s

    p = os.path.join(root, PC)
    out[p] = bump(read(p), 'EXPECT_PAIRS = %d', PC_WAS, PC_NOW,
                  'CC-1, 15 Oct 2026 - .day-more and .day-more:hover, the '
                  'chip that opens a busy day. Both are house pairs, so '
                  'the AA check below is unchanged.',
                  '%s (the pair census)' % PC)

    p = os.path.join(root, ET)
    s = read(p)
    if "cal.count('tone_class')" in s:
        refuse('%s already asks the token' % ET)
    out[p] = swap(s, ET_WAS, ET_NOW, '%s (the badge count)' % ET)

    # ---------------------------------------------------------------- 6
    # the registers and the two counters these rounds keep by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_calendar_grid.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, CLAIMS_ANCHOR, CLAIMS, '%s (the claims)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'CC-1, 15 Oct 2026 - this round own suite. The '
                  'celebration grid, after Demetri asked why November '
                  '2027 was blank and why the Saturday column was cut '
                  'off.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'CC-1, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('CC-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('CC-1 applied.')
    print('   a month grid asks for THIS month, not for one next')
    print('         occurrence each - no month is ever falsely blank, and')
    print('         the current month stops losing its first fortnight')
    print('   the age is taken at the occurrence being drawn')
    print('   table-layout: fixed - the %dpx min-content floor that' % MIN_CONTENT_FLOOR)
    print('         clipped the Saturday column below ~1300px is gone')
    print('   day cells are fixed; %d chips then a +N more sheet' % CAP)
    print('   the key sits above the grid it explains')
    print('   the timeline groups one box per DATE, and loses its emoji')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
