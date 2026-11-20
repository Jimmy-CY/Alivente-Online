# -*- coding: utf-8 -*-
"""apply_ra07_trip_days.py - round RA07, 19 Nov 2026.

RELEASE RA07 - WEATHER BEFORE ANYTHING IS BOOKED; SPENDING ONLY ON THE
TRIP'S DAYS, AND CHANGED WHEN NEEDED; A STEADIER WELLNESS TEST.

    Demetri, 19 Nov, on a trip with no bookings: "Why can't i see any
    weather??"; "Should I be able to add Spending to days outside of my
    trip dates? I don't think so..."; "Group all of these changes
    together." (Plan: claude/ra07_plan_weather_spending_dates_19_nov.md.)

    - Weather: with no booking city for a day, the Things to do planned
      that day, else where most of the trip's are (their own position).
    - + Spending: only a day of the trip (picker and server); the day is
      today while away, the first day before, the last after. Spending
      outside the dates listed apart, out of the plan, still in the costs.
    - Change a spending: click it (computer) or tap it (phone).
    - test_wellness_six compares the quote as the page shows it, escaped.
    - Help on the computer and the phone; the phone app moves to tv21-1.

The suite ships beside this patcher. Stands on RA06. Idempotent. Edits
backed up to .bak_ra07.
"""
import os
import sys

SUFFIX = '.bak_ra07'
MARK = 'RA07, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra07_trip_days.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra05_budget.py',
    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    'test_ra06_kind_round.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra05_budget.py',
    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    'test_ra06_kind_round.py',
    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    'test_ra07_trip_days.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    '.bak_ra06',
]

''',
         r'''    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    '.bak_ra06',
    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    '.bak_ra07',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. Only the trip&rsquo;s owner adds spending, sets the budget or deletes spending (&times;).</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
''',
         r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> to change its amount, currency, day or note, or to delete it. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
'''),
        (r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p data-help-weather><strong>The weather.</strong> Each day of the itinerary that the forecast reaches (today and about two weeks ahead) shows the weather where you are that day &ndash; the city of that night&rsquo;s hotel (or of the hotel you leave that morning, or where that day&rsquo;s flight lands): an icon, the high and low, and the chance of rain. Hover over it for the rest. On the phone, <strong>Today</strong> has a weather box at the top &ndash; the city, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow &ndash; and, before a trip, the first day&rsquo;s forecast once it is about two weeks away. The forecast comes from Open-Meteo, free and with nothing to set up; it is looked up once an hour, and if it cannot be reached there is simply no weather.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
''',
         r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p data-help-weather><strong>The weather.</strong> Each day of the itinerary that the forecast reaches (today and about two weeks ahead) shows the weather where you are that day &ndash; the city of that night&rsquo;s hotel (or of the hotel you leave that morning, or where that day&rsquo;s flight lands): an icon, the high and low, and the chance of rain. Hover over it for the rest. On the phone, <strong>Today</strong> has a weather box at the top &ndash; the city, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow &ndash; and, before a trip, the first day&rsquo;s forecast once it is about two weeks away. Before anything is booked, the weather follows your <strong>Things to do</strong>: those planned that day, else where most of the trip&rsquo;s are. The forecast comes from Open-Meteo, free and with nothing to set up; it is looked up once an hour, and if it cannot be reached there is simply no weather.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
'''),
    ]),
    (os.path.join('test_ra05_budget.py'), [
        (r'''   in md, 'A BOOKING WITH ITS COSTS BLANKED CAN NEVER BE SAVED')
vb = read(J(TV, 'views_budget.py'))
ok('def _owned' in vb and vb.count('= _owned(request') == 5,
   'ONLY THE OWNER sets the budget, adds or deletes spending (5 doors)')
ok("dt.date.today()" in vb and
   "{% if c == 'EUR' %} selected" in read(J(TT, 'm', 'spend.html')),
   '+ SPENDING: euros and today by default; the note blank')
try:
''',
         r'''   in md, 'A BOOKING WITH ITS COSTS BLANKED CAN NEVER BE SAVED')
vb = read(J(TV, 'views_budget.py'))
# RA07 added a sixth door (changing a spending) - the owner's too.
ok('def _owned' in vb and vb.count('= _owned(request') >= 5,
   'ONLY THE OWNER sets the budget, adds or deletes spending (5 doors)')
# RA07: today while you are away; only a day of the trip.
ok(("dt.date.today()" in vb or "B.default_day(start, end)" in vb) and
   ("{% if c == 'EUR' %} selected" in read(J(TT, 'm', 'spend.html')) or
    "not s and c == 'EUR' %} selected" in read(J(TT, 'm', 'spend.html'))),
   '+ SPENDING: euros and today by default; the note blank')
try:
'''),
    ]),
    (os.path.join('test_ra06_kind_round.py'), [
        (r'''   '  further than the forecast reaches: none')
WX.off, WX.fetch = _off, _fetch
ok("with_weather(itinerary(t, bs, pl), bs)" in read(J(ROOT, 'travel',
                                                      'views.py')) and
   "weather.for_day(shaped, day, day)" in read(J(ROOT, 'travel',
                                                 'phone.py')),
   'ON THE COMPUTER\'S ITINERARY and the phone\'s Today')
ok("{% include 'travel/_weather.html' with w=wx nxt=wx_next %}" in read(
''',
         r'''   '  further than the forecast reaches: none')
WX.off, WX.fetch = _off, _fetch
# RA07 passes the Things to do as well: ", pl)" may follow.
ok("with_weather(itinerary(t, bs, pl), bs" in read(J(ROOT, 'travel',
                                                     'views.py')) and
   "weather.for_day(shaped, day, day" in read(J(ROOT, 'travel',
                                                'phone.py')),
   'ON THE COMPUTER\'S ITINERARY and the phone\'s Today')
ok("{% include 'travel/_weather.html' with w=wx nxt=wx_next %}" in read(
'''),
    ]),
    (os.path.join('test_wellness_six.py'), [
        (r'''from wellness import daily_line as DL                       # noqa: E402
from wellness import quotes as Q                            # noqa: E402
ok(DL.parse('{"quote": 3, "line": "A gentle start is still a start."}') ==
   {'quote': 3, 'line': 'A gentle start is still a start.'},
''',
         r'''from wellness import daily_line as DL                       # noqa: E402
from wellness import quotes as Q                            # noqa: E402
# RA07, 19 Nov 2026 - the page shows a quote HTML-escaped: 13 of the 240
# have an apostrophe, a quotation mark or an ampersand, and which one a
# person gets depends on their id - so a pool run sometimes failed.
from django.utils.html import escape as _esc                # noqa: E402
ok(DL.parse('{"quote": 3, "line": "A gentle start is still a start."}') ==
   {'quote': 3, 'line': 'A gentle start is still a start.'},
'''),
        (r'''            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               Q.for_day(a.pk, today)['text'] in t,
               'no line yet: the date\'s own quote and no line - Today '
               'did not wait')
''',
         r'''            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               _esc(Q.for_day(a.pk, today)['text']) in t,
               'no line yet: the date\'s own quote and no line - Today '
               'did not wait')
'''),
        (r'''               'nothing private')
            t = ca.get('/wellness/').content.decode()
            ok(Q.BY_ID[fid]['text'] in t and 'A short walk counts, Alex.'
               in t and 'A line from Claude' in t,
               "Today: Claude's pick from the library, and its line, "
''',
         r'''               'nothing private')
            t = ca.get('/wellness/').content.decode()
            ok(_esc(Q.BY_ID[fid]['text']) in t and 'A short walk counts, Alex.'
               in t and 'A line from Claude' in t,
               "Today: Claude's pick from the library, and its line, "
'''),
        (r'''            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               Q.for_day(a.pk, today)['text'] in t,
               '  and Today simply shows the date\'s quote')
            ca.post('/wellness/settings/', {})
''',
         r'''            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               _esc(Q.for_day(a.pk, today)['text']) in t,
               '  and Today simply shows the date\'s quote')
            ca.post('/wellness/settings/', {})
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''  .tv-bud-note { background: #3A2A10; color: #F2CF95; }
}
''',
         r'''  .tv-bud-note { background: #3A2A10; color: #F2CF95; }
}
/* RA07, 19 Nov 2026 - spending outside the trip's dates; click a spending to change it. */
.tv-spend-out { margin: 12px 0 2px; padding: 8px 10px; border-radius: 8px; background: #FCEFD9; color: #6B3A00; font-size: .85rem; }
.tv-spend-day.is-outside { opacity: .85; }
details.tv-spend-row > summary { list-style: none; cursor: pointer; }
details.tv-spend-row > summary::-webkit-details-marker { display: none; }
details.tv-spend-row[open] > summary { font-weight: 600; }
.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
@media (prefers-color-scheme: dark) { .tv-spend-out { background: #3A2A10; color: #F2CF95; } }
'''),
    ]),
    (os.path.join('travel', 'budget.py'), [
        (r'''    by_day = {}
    pending = 0
    for s in spends:
        if s.amount_eur is None:
            pending += 1
            continue
        by_day[s.day] = by_day.get(s.day, ZERO) + s.amount_eur
''',
         r'''    by_day = {}
    pending = 0
    # RA07, 19 Nov 2026 - spending on a day outside the trip (added before
    # RA07, or left there when bookings moved the trip) is shown apart and
    # kept out of the plan; it still counts in the trip's costs.
    outside = ZERO
    n_out = 0
    for s in spends:
        if s.amount_eur is None:
            pending += 1
            continue
        if not inside(s.day, start, end):
            outside += s.amount_eur
            n_out += 1
            continue
        by_day[s.day] = by_day.get(s.day, ZERO) + s.amount_eur
'''),
        (r'''    empty = [c for c in so_far if c['empty']]
    return {
        'empty_days': len(empty), 'days_so_far': len(so_far),
        'set': trip.budget is not None, 'by': trip.budget_by,
''',
         r'''    empty = [c for c in so_far if c['empty']]
    return {
        'outside': n_out, 'outside_label': whole(outside) if n_out else '',
        'empty_days': len(empty), 'days_so_far': len(so_far),
        'set': trip.budget is not None, 'by': trip.budget_by,
'''),
        (r'''

def spend_days(spends, per_day=None):
    """Spending by day, the latest first: [{day, rows, label, over}]."""
    out = {}
    for s in spends:
''',
         r'''

def inside(day, start, end):
    """RA07 - is `day` one of the trip's days? (A trip with no dates yet
    has none.)"""
    return bool(start) and start <= day <= (end or start)


def default_day(start, end, today=None):
    """RA07 - + Spending's day: today while you are away, the first day
    before the trip, the last after it (Demetri: "Should I be able to add
    Spending to days outside of my trip dates? I don't think so...")."""
    today = today or dt.date.today()
    if not start:
        return None
    end = end or start
    return min(max(today, start), end)


def spend_days(spends, per_day=None, start=None, end=None):
    """Spending by day, the latest first: [{day, rows, label, over,
    outside}] - RA07: the trip's days first, then any outside them."""
    out = {}
    for s in spends:
'''),
        (r'''                '%s %s' % ('{:,.2f}'.format(s.amount), s.currency)
        rows.append({'day': d, 'rows': out[d], 'label': eur(tot) or '€0',
                     'over': per_day is not None and tot > per_day,
                     'over_by': whole(tot - per_day)
                     if per_day is not None and tot > per_day else ''})
    return rows
''',
         r'''                '%s %s' % ('{:,.2f}'.format(s.amount), s.currency)
        rows.append({'day': d, 'rows': out[d], 'label': eur(tot) or '€0',
                     'outside': start is not None and
                     not inside(d, start, end),
                     'over': per_day is not None and tot > per_day,
                     'over_by': whole(tot - per_day)
                     if per_day is not None and tot > per_day else ''})
    return [r for r in rows if not r['outside']] + \
        [r for r in rows if r['outside']]
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
SW_VERSION = 'tv20-1'
SW_ASSETS = '030cdeda93c3'


''',
         r'''# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
SW_VERSION = 'tv21-1'
SW_ASSETS = '362b7b2560da'


'''),
        (r'''        from . import weather
        if now:
            ctx['wx'] = weather.for_day(shaped, day, day)
            ctx['wx_next'] = weather.for_day(shaped, day + dt.timedelta(1),
                                             day)
        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
''',
         r'''        from . import weather
        if now:
            ctx['wx'] = weather.for_day(shaped, day, day, pl)
            ctx['wx_next'] = weather.for_day(shaped, day + dt.timedelta(1),
                                             day, pl)
        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day, pl)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
'''),
        (r'''    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': with_weather(itinerary(t, bs, pl), bs)
        if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
''',
         r'''    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': with_weather(itinerary(t, bs, pl), bs, pl)
        if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget.html'), [
        (r'''    {% endif %}
    </div>
    {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
    {% if bud.total %}<div class="tv-bar tv-bud-bar is-{% if bud.over %}red{% elif bud.pct >= 90 %}amber{% else %}ok{% endif %}" aria-hidden="true" style="margin-top: 12px"><span style="width: {{ bud.pct }}%"></span></div>
''',
         r'''    {% endif %}
    </div>
    {% if bud.outside %}<p class="tv-bud-note" data-bud-outside>{{ bud.outside_label }} of spending is on {{ bud.outside|pluralize:"a day,days" }} outside the trip&rsquo;s dates and is not counted here &ndash; <a href="#spending-outside">move or delete {{ bud.outside|pluralize:"it,them" }}</a>.</p>{% endif %}
    {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
    {% if bud.total %}<div class="tv-bar tv-bud-bar is-{% if bud.over %}red{% elif bud.pct >= 90 %}amber{% else %}ok{% endif %}" aria-hidden="true" style="margin-top: 12px"><span style="width: {{ bud.pct }}%"></span></div>
'''),
        (r'''
<section class="form-card" data-spending>
    <h3 class="form-section-title">Daily spending</h3>
    {% if can_spend %}<form method="post" action="{% url 'travel:spend_add' trip.pk %}" class="tv-spend-add" data-spend-form>{% csrf_token %}
        <div><label for="sp-a">Amount</label><input id="sp-a" name="amount" class="form-control tv-money" inputmode="decimal" placeholder="0.00" required></div>
        <div><label for="sp-c">Currency</label><select id="sp-c" name="currency" class="form-control">{% for c in currencies %}<option value="{{ c }}"{% if c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
        <div><label for="sp-d">Day</label><input id="sp-d" type="date" name="day" class="form-control" value="{{ today|date:'Y-m-d' }}"></div>
        <div class="tv-spend-note"><label for="sp-n">Note (optional)</label><input id="sp-n" name="what" class="form-control" maxlength="120"></div>
        <button type="submit" class="btn action-primary" data-spend-add><i class="fas fa-plus" aria-hidden="true"></i> Spending</button>
    </form>{% endif %}
    {% if not bud.set and bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
    {% for d in spend_days %}
    <div class="tv-spend-day" data-spend-day="{{ d.day|date:'Y-m-d' }}" id="sp{{ d.day|date:'Ymd' }}">
        <div class="tv-row"><b>{% if d.day == today %}Today &middot; {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over %}tv-over{% else %}tv-sub{% endif %}">{{ d.label }}{% if bud.per_day_label %}{% if d.over %} &middot; {{ d.over_by }} over{% else %} of {{ bud.per_day_label }}{% endif %}{% endif %}</span></div>
        {% for s in d.rows %}<div class="tv-row tv-spend-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }}{% if can_spend %}<form method="post" action="{% url 'travel:spend_delete' s.pk %}" style="display: inline" data-spend-del>{% csrf_token %}<button type="submit" class="tv-linkbtn" title="Delete this spending" aria-label="Delete {{ s.what|default:'this spending' }}" onclick="return confirm('Delete this spending?')"><i class="fas fa-times" aria-hidden="true"></i></button></form>{% endif %}</span></div>{% endfor %}
    </div>
    {% empty %}<p class="tv-sub" style="margin: 8px 0 0">{% if can_spend %}Nothing yet. Add a meal, a taxi or tickets at the door with <b>+ Spending</b> &ndash; euros and today are already filled in.{% else %}No spending added yet.{% endif %}</p>{% endfor %}
</section>
{% if can_spend %}{% include 'travel/_budget_js.html' %}{% endif %}
''',
         r'''
<section class="form-card" data-spending>
    {% comment %} RA07, 19 Nov 2026 - only a day of the trip; click a spending to change it; any outside the trip's dates listed apart. {% endcomment %}
    <h3 class="form-section-title">Daily spending</h3>
    {% if can_spend %}{% if trip_start %}<form method="post" action="{% url 'travel:spend_add' trip.pk %}" class="tv-spend-add" data-spend-form>{% csrf_token %}
        <div><label for="sp-a">Amount</label><input id="sp-a" name="amount" class="form-control tv-money" inputmode="decimal" placeholder="0.00" required></div>
        <div><label for="sp-c">Currency</label><select id="sp-c" name="currency" class="form-control">{% for c in currencies %}<option value="{{ c }}"{% if c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
        <div><label for="sp-d">Day</label><input id="sp-d" type="date" name="day" class="form-control" value="{{ spend_day|date:'Y-m-d' }}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}" data-spend-day-pick title="A day of the trip: {{ trip_start|date:'D j M' }} – {{ trip_end|date:'D j M' }}"></div>
        <div class="tv-spend-note"><label for="sp-n">Note (optional)</label><input id="sp-n" name="what" class="form-control" maxlength="120"></div>
        <button type="submit" class="btn action-primary" data-spend-add><i class="fas fa-plus" aria-hidden="true"></i> Spending</button>
    </form>{% else %}<p class="tv-sub" data-spend-nodates>The trip needs its dates first &ndash; add a booking, or set From and To under <b>Edit trip</b>.</p>{% endif %}{% endif %}
    {% if not bud.set and bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
    {% for d in spend_days %}
    {% if d.outside %}{% ifchanged d.outside %}<div class="tv-spend-out" id="spending-outside" data-spend-outside><b>Outside the trip&rsquo;s dates</b> &ndash; {% if can_spend %}click one to move it to a day of the trip, or delete it.{% else %}not part of the trip&rsquo;s days.{% endif %} Not counted against the budget; still in the trip&rsquo;s costs.</div>{% endifchanged %}{% endif %}
    <div class="tv-spend-day{% if d.outside %} is-outside{% endif %}" data-spend-day="{{ d.day|date:'Y-m-d' }}" id="sp{{ d.day|date:'Ymd' }}">
        <div class="tv-row"><b>{% if d.day == today %}Today &middot; {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over and not d.outside %}tv-over{% else %}tv-sub{% endif %}">{{ d.label }}{% if bud.per_day_label and not d.outside %}{% if d.over %} &middot; {{ d.over_by }} over{% else %} of {{ bud.per_day_label }}{% endif %}{% endif %}</span></div>
        {% for s in d.rows %}{% if can_spend %}<details class="tv-spend-row" data-spend="{{ s.pk }}"><summary class="tv-row" title="Change or delete"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }} <i class="fas fa-pen tv-sub" aria-hidden="true"></i></span></summary>
            <form method="post" action="{% url 'travel:spend_edit' s.pk %}" class="tv-spend-add tv-spend-edit" data-spend-edit>{% csrf_token %}
                <div><label for="se-a{{ s.pk }}">Amount</label><input id="se-a{{ s.pk }}" name="amount" class="form-control tv-money" inputmode="decimal" value="{{ s.amount }}" required></div>
                <div><label for="se-c{{ s.pk }}">Currency</label><select id="se-c{{ s.pk }}" name="currency" class="form-control">{% for c in currencies %}<option value="{{ c }}"{% if c == s.currency %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
                <div><label for="se-d{{ s.pk }}">Day</label><input id="se-d{{ s.pk }}" type="date" name="day" class="form-control" value="{% if d.outside %}{{ spend_day|date:'Y-m-d' }}{% else %}{{ s.day|date:'Y-m-d' }}{% endif %}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}"></div>
                <div class="tv-spend-note"><label for="se-n{{ s.pk }}">Note (optional)</label><input id="se-n{{ s.pk }}" name="what" class="form-control" maxlength="120" value="{{ s.what }}"></div>
                <button type="submit" class="btn action-primary btn-sm">Save</button>
                <button type="submit" form="sd{{ s.pk }}" class="btn action-secondary action-danger btn-sm" onclick="return confirm('Delete this spending?')" data-spend-del>Delete</button>
            </form><form method="post" action="{% url 'travel:spend_delete' s.pk %}" id="sd{{ s.pk }}" hidden>{% csrf_token %}</form>
        </details>{% else %}<div class="tv-row tv-spend-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }}</span></div>{% endif %}{% endfor %}
    </div>
    {% empty %}<p class="tv-sub" style="margin: 8px 0 0">{% if can_spend %}Nothing yet. Add a meal, a taxi or tickets at the door with <b>+ Spending</b> &ndash; euros and the day are already filled in.{% else %}No spending added yet.{% endif %}</p>{% endfor %}
</section>
{% if can_spend %}{% include 'travel/_budget_js.html' %}{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-wx:not(.is-compact) .tv-wx-t { font-size: 1.15rem; font-weight: 700; }
.tv-wx-next { font-size: .82rem; color: #5B6B72; margin-top: 3px; }
</style>
''',
         r'''.tv-wx:not(.is-compact) .tv-wx-t { font-size: 1.15rem; font-weight: 700; }
.tv-wx-next { font-size: .82rem; color: #5B6B72; margin-top: 3px; }
/* RA07, 19 Nov 2026 - spending outside the trip's dates; click a spending to change it. */
.tv-spend-out { margin: 12px 0 2px; padding: 8px 10px; border-radius: 8px; background: #FCEFD9; color: #6B3A00; font-size: .85rem; }
.tv-spend-day.is-outside { opacity: .85; }
details.tv-spend-row > summary { list-style: none; cursor: pointer; }
details.tv-spend-row > summary::-webkit-details-marker { display: none; }
details.tv-spend-row[open] > summary { font-weight: 600; }
.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv20-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv21-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv20-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv21-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Only a day of the trip can be chosen; tap a spending to change or delete it. Any on a day outside the trip is listed apart &ndash; move it or delete it. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'spend.html'), [
        (r'''{% extends 'travel/m/base.html' %}
{% comment %} RA05, 19 Nov 2026 - + Spending on the phone. Demetri: "+Spending should default to Euros, today's date, and optional note blank - for quick entry": the number pad opens on the amount; Add. {% endcomment %}
{% block title %}+ Spending - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab=costs"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>Add spending</h1></div>{% endblock %}
{% block sub %}<div class="sub">Meals, taxis, tickets at the door, shopping</div>{% endblock %}
{% block content %}
<form method="post" action="{% url 'travel:m_spend_add' trip.pk %}" class="tv-card tv-form" data-spend-form>{% csrf_token %}
  <label for="a" class="tv-muted tv-small">Amount</label>
  <input id="a" name="amount" class="tv-input tv-amount" inputmode="decimal" placeholder="0.00" autocomplete="off" required autofocus>
  <div class="tv-two">
    <div><label for="c" class="tv-muted tv-small">Currency</label><select id="c" name="currency" class="tv-select" style="width: 100%">{% for c in currencies %}<option value="{{ c }}"{% if c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
    <div><label for="d" class="tv-muted tv-small">Day</label><input id="d" type="date" name="day" class="tv-input" value="{{ today|date:'Y-m-d' }}"></div>
  </div>
  <label for="n" class="tv-muted tv-small">Note (optional)</label><input id="n" name="what" class="tv-input" maxlength="120">
  <button type="submit" class="tv-btn wide" data-spend-add>Add</button>
</form>
{% endblock %}
''',
         r'''{% extends 'travel/m/base.html' %}
{% comment %} RA05, 19 Nov 2026 - + Spending on the phone. Demetri: "+Spending should default to Euros, today's date, and optional note blank - for quick entry": the number pad opens on the amount; Add. {% endcomment %}
{% block title %}{% if s %}Spending{% else %}+ Spending{% endif %} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab=costs"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>{% if s %}Change spending{% else %}Add spending{% endif %}</h1></div>{% endblock %}
{% block sub %}<div class="sub">Meals, taxis, tickets at the door, shopping</div>{% endblock %}
{% block content %}
{% comment %} RA07, 19 Nov 2026 - only a day of the trip; the same page changes one already added (Save, Delete). {% endcomment %}
{% if not trip_start %}<section class="tv-card" data-spend-nodates><p style="margin: 0">The trip needs its dates first &ndash; add a booking, or set From and To on the full site under Edit trip.</p></section>{% else %}
<form method="post" action="{% if s %}{% url 'travel:m_spend_edit' s.pk %}{% else %}{% url 'travel:m_spend_add' trip.pk %}{% endif %}" class="tv-card tv-form" data-spend-form>{% csrf_token %}
  <label for="a" class="tv-muted tv-small">Amount</label>
  <input id="a" name="amount" class="tv-input tv-amount" inputmode="decimal" placeholder="0.00" autocomplete="off" required{% if s %} value="{{ s.amount }}"{% else %} autofocus{% endif %}>
  <div class="tv-two">
    <div><label for="c" class="tv-muted tv-small">Currency</label><select id="c" name="currency" class="tv-select" style="width: 100%">{% for c in currencies %}<option value="{{ c }}"{% if s and c == s.currency or not s and c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
    <div><label for="d" class="tv-muted tv-small">Day</label><input id="d" type="date" name="day" class="tv-input" value="{{ today|date:'Y-m-d' }}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}" data-spend-day-pick></div>
  </div>
  <label for="n" class="tv-muted tv-small">Note (optional)</label><input id="n" name="what" class="tv-input" maxlength="120"{% if s %} value="{{ s.what }}"{% endif %}>
  <p class="tv-muted tv-small" style="margin: 0">A day of the trip: {{ trip_start|date:"D j M" }} &ndash; {{ trip_end|date:"D j M" }}.</p>
  <button type="submit" class="tv-btn wide" data-spend-add>{% if s %}Save{% else %}Add{% endif %}</button>
</form>
{% if s %}<form method="post" action="{% url 'travel:m_spend_delete' s.pk %}" style="margin: 0 0 12px">{% csrf_token %}<button type="submit" class="tv-btn sec wide" onclick="return confirm('Delete this spending?')" data-spend-del>Delete</button></form>{% endif %}
{% endif %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''  {% else %}<div class="tv-row"><span class="tv-bud-big">{{ bud.total_label|default:"–" }}</span><span class="tv-muted tv-small">for the holiday{% if bud.days %} &middot; {{ bud.days }} days{% endif %}</span></div>{% endif %}
  {% if bud.total %}<div class="tv-meter{% if bud.over %} is-red{% elif bud.pct >= 90 %} is-amber{% endif %}" aria-hidden="true"><span style="width: {{ bud.pct }}%"></span></div>{% endif %}
  {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
  {% if bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
''',
         r'''  {% else %}<div class="tv-row"><span class="tv-bud-big">{{ bud.total_label|default:"–" }}</span><span class="tv-muted tv-small">for the holiday{% if bud.days %} &middot; {{ bud.days }} days{% endif %}</span></div>{% endif %}
  {% if bud.total %}<div class="tv-meter{% if bud.over %} is-red{% elif bud.pct >= 90 %} is-amber{% endif %}" aria-hidden="true"><span style="width: {{ bud.pct }}%"></span></div>{% endif %}
  {% if bud.outside %}<p class="tv-bud-note" data-bud-outside>{{ bud.outside_label }} is on {{ bud.outside|pluralize:"a day,days" }} outside the trip&rsquo;s dates and not counted here &ndash; move or delete {{ bud.outside|pluralize:"it,them" }} below.</p>{% endif %}
  {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
  {% if bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
'''),
        (r'''{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-btn wide" data-spend-new style="margin-bottom: 10px">+ Spending</a>{% endif %}
{% if not bud.set and bud.show_chart %}<section class="tv-card">{% include 'travel/_budget_chart.html' %}</section>{% endif %}
{% if spend_days %}<section class="tv-card" data-spending>{% for d in spend_days %}<div class="tv-spend-day" id="sp{{ d.day|date:'Ymd' }}" data-spend-day="{{ d.day|date:'Y-m-d' }}"><div class="tv-row tv-small"><b>{% if d.day == today %}Today · {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over %}tv-over{% else %}tv-muted{% endif %}">{{ d.label }}{% if d.over %} · {{ d.over_by }} over{% endif %}</span></div>{% for s in d.rows %}<div class="tv-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-muted tv-small">· {{ s.orig_label }}</span>{% endif %}</span><span>{{ s.eur_label }}{% if can_spend %}<form method="post" action="{% url 'travel:m_spend_delete' s.pk %}" style="display: inline">{% csrf_token %}<button type="submit" class="tv-linkbtn" aria-label="Delete {{ s.what|default:'this spending' }}" onclick="return confirm('Delete this spending?')" style="margin-left: 8px">✕</button></form>{% endif %}</span></div>{% endfor %}</div>{% endfor %}</section>{% endif %}
<section class="tv-card" data-costs>
  {% if money.has_spend %}<div class="tv-row tv-small" data-costs-split><span class="tv-muted">Bookings</span><b>{{ money.booked|default:"€0" }}</b></div><div class="tv-row tv-small"><span class="tv-muted">Daily spending</span><b>{{ money.spent|default:"€0" }}</b></div>{% endif %}
''',
         r'''{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-btn wide" data-spend-new style="margin-bottom: 10px">+ Spending</a>{% endif %}
{% if not bud.set and bud.show_chart %}<section class="tv-card">{% include 'travel/_budget_chart.html' %}</section>{% endif %}
{% comment %} RA07, 19 Nov 2026 - tap one to change it; spending on a day outside the trip listed apart. {% endcomment %}{% if spend_days %}<section class="tv-card" data-spending>{% for d in spend_days %}{% if d.outside %}{% ifchanged d.outside %}<div class="tv-spend-out" data-spend-outside><b>Outside the trip&rsquo;s dates</b><br>Move {{ bud.outside|pluralize:"it,them" }} to a day of the trip, or delete {{ bud.outside|pluralize:"it,them" }}. Not counted against the budget.</div>{% endifchanged %}{% endif %}<div class="tv-spend-day{% if d.outside %} is-outside{% endif %}" id="sp{{ d.day|date:'Ymd' }}" data-spend-day="{{ d.day|date:'Y-m-d' }}"><div class="tv-row tv-small"><b>{% if d.day == today %}Today · {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over and not d.outside %}tv-over{% else %}tv-muted{% endif %}">{{ d.label }}{% if d.over and not d.outside %} · {{ d.over_by }} over{% endif %}</span></div>{% for s in d.rows %}{% if can_spend %}<a href="{% url 'travel:m_spend_open' trip.pk s.pk %}" class="tv-row tv-spend-link" data-spend="{{ s.pk }}">{% else %}<div class="tv-row" data-spend="{{ s.pk }}">{% endif %}<span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-muted tv-small">· {{ s.orig_label }}</span>{% endif %}</span><span>{{ s.eur_label }}{% if can_spend %} <span class="tv-muted" aria-hidden="true">›</span>{% endif %}</span>{% if can_spend %}</a>{% else %}</div>{% endif %}{% endfor %}</div>{% endfor %}</section>{% endif %}
<section class="tv-card" data-costs>
  {% if money.has_spend %}<div class="tv-row tv-small" data-costs-split><span class="tv-muted">Bookings</span><b>{{ money.booked|default:"€0" }}</b></div><div class="tv-row tv-small"><span class="tv-muted">Daily spending</span><b>{{ money.spent|default:"€0" }}</b></div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('m/spend/<int:spend_id>/delete/', views_budget.spend_delete,
         name='m_spend_delete'),
    path('<int:trip_id>/booking/new/', views.booking_form,
         name='booking_new'),
''',
         r'''    path('m/spend/<int:spend_id>/delete/', views_budget.spend_delete,
         name='m_spend_delete'),
    # RA07, 19 Nov 2026 - change a spending entry.
    path('spend/<int:spend_id>/edit/', views_budget.spend_edit,
         name='spend_edit'),
    path('m/spend/<int:spend_id>/edit/', views_budget.spend_edit,
         name='m_spend_edit'),
    path('m/<int:trip_id>/spend/<int:spend_id>/', views_budget.m_spend_form,
         name='m_spend_open'),
    path('<int:trip_id>/booking/new/', views.booking_form,
         name='booking_new'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': with_weather(itinerary(t, bs, pl), bs)
        if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
''',
         r'''        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': with_weather(itinerary(t, bs, pl), bs, pl)
        if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
'''),
        (r'''

def with_weather(days, bs):
    """RA06, 19 Nov 2026 - each day of the itinerary the forecast reaches
    gets the weather where you are (travel/weather.py). Demetri: "show it
    on the computer too"."""
    from . import weather
    wx = weather.for_days(bs, [d for d, _ in days])
    for d, rows in days:
        rows.wx = wx.get(d)
''',
         r'''

def with_weather(days, bs, places=None):
    """RA06, 19 Nov 2026 - each day of the itinerary the forecast reaches
    gets the weather where you are (travel/weather.py). Demetri: "show it
    on the computer too"."""
    from . import weather
    # RA07 - and the Things to do, before anything is booked.
    wx = weather.for_days(bs, [d for d, _ in days], places=places)
    for d, rows in days:
        rows.wx = wx.get(d)
'''),
        (r'''           'bud': bud, 'today': dt.date.today()}
    if tab == 'costs':
        out.update({'spend_days': budget.spend_days(spends, bud['per_day']),
                    'currencies': fx.CURRENCIES})
    return out
''',
         r'''           'bud': bud, 'today': dt.date.today()}
    if tab == 'costs':
        # RA07 - only the trip's days; those outside listed apart.
        out.update({'spend_days': budget.spend_days(spends, bud['per_day'],
                                                    start, end),
                    'spend_day': budget.default_day(start, end),
                    'trip_start': start, 'trip_end': end or start,
                    'currencies': fx.CURRENCIES})
    return out
'''),
    ]),
    (os.path.join('travel', 'views_budget.py'), [
        (r'''may see the budget and the costs when the owner shares them, but never
add spending (Demetri, 19 Nov)."""
import datetime as dt

from django.contrib import messages
from django.http import Http404
''',
         r'''may see the budget and the costs when the owner shares them, but never
add spending (Demetri, 19 Nov)."""
from django.contrib import messages
from django.http import Http404
'''),
        (r'''

@travel_view
@require_POST
def spend_add(request, trip_id):
    t = _owned(request, trip_id)
    P = request.POST
    amount = _money(P.get('amount'))
    if not amount:
        messages.error(request, 'Type how much was spent.')
        return _back(request, t)
    cur = (P.get('currency') or 'EUR').upper()
    s = Spend(trip=t, added_by=request.user, amount=amount,
              currency=cur if cur in fx.CURRENCIES else 'EUR',
              day=_date(P.get('day')) or dt.date.today(),
              what=(P.get('what') or '').strip()[:120])
    B.convert(s)
    s.save()
    messages.success(request, '%s added to daily spending.' % (
        B.eur(s.amount_eur) if s.amount_eur is not None else
        '%s %s' % (s.amount, s.currency)))
    return _back(request, t)

''',
         r'''

def _read_spend(request, t, s):
    """Fill a Spend from the form; '' or the problem. RA07, 19 Nov 2026 -
    only a day of the trip (Demetri: "Should I be able to add Spending to
    days outside of my trip dates? I don't think so...")."""
    P = request.POST
    amount = _money(P.get('amount'))
    if not amount:
        return 'Type how much was spent.'
    start, end = span(t, list(t.bookings.all()))
    if not start:
        return ('The trip needs its dates first - add a booking, or set '
                'From and To under Edit trip.')
    end = end or start
    day = _date(P.get('day')) or B.default_day(start, end)
    if not B.inside(day, start, end):
        return 'Pick a day of the trip (%s - %s).' % (_d(start), _d(end))
    cur = (P.get('currency') or 'EUR').upper()
    s.amount, s.day = amount, day
    s.currency = cur if cur in fx.CURRENCIES else 'EUR'
    s.what = (P.get('what') or '').strip()[:120]
    B.convert(s)
    return ''


def _d(day):
    return '%s %d %s' % (day.strftime('%a'), day.day, day.strftime('%b'))


@travel_view
@require_POST
def spend_add(request, trip_id):
    t = _owned(request, trip_id)
    s = Spend(trip=t, added_by=request.user)
    problem = _read_spend(request, t, s)
    if problem:
        messages.error(request, problem)
        return _back(request, t)
    s.save()
    messages.success(request, '%s added to daily spending.' % (
        B.eur(s.amount_eur) if s.amount_eur is not None else
        '%s %s' % (s.amount, s.currency)))
    return _back(request, t)


@travel_view
@require_POST
def spend_edit(request, spend_id):
    """RA07 - change a spending entry's amount, currency, day or note."""
    s = get_object_or_404(Spend.objects.select_related('trip'), pk=spend_id)
    t = _owned(request, s.trip_id)
    problem = _read_spend(request, t, s)
    if problem:
        messages.error(request, problem)
        return _back(request, t)
    s.save()
    messages.success(request, 'Spending saved.')
    return _back(request, t)

'''),
        (r'''# ------------------------------------------------------------- the phone
@travel_view
def m_spend_form(request, trip_id):
    """+ Spending on the phone: the amount first, euros and today already
    there (Demetri: "+Spending should default to Euros, today's date, and
    optional note blank - for quick entry")."""
    from .phone import page
    t = _owned(request, trip_id)
    return page(request, 'travel/m/spend.html', {
        'trip': t, 'tab': 'trips', 'currencies': fx.CURRENCIES,
        'today': dt.date.today()})


''',
         r'''# ------------------------------------------------------------- the phone
@travel_view
def m_spend_form(request, trip_id, spend_id=None):
    """+ Spending on the phone: the amount first, euros and today already
    there (Demetri: "+Spending should default to Euros, today's date, and
    optional note blank - for quick entry"). RA07 - only the trip's days,
    and the same page changes one already added."""
    from .phone import page
    t = _owned(request, trip_id)
    s = get_object_or_404(Spend, pk=spend_id, trip=t) if spend_id else None
    start, end = span(t, list(t.bookings.all()))
    return page(request, 'travel/m/spend.html', {
        'trip': t, 'tab': 'trips', 'currencies': fx.CURRENCIES, 's': s,
        'today': (s.day if s else B.default_day(start, end)),
        'trip_start': start, 'trip_end': end or start})


'''),
    ]),
    (os.path.join('travel', 'weather.py'), [
        (r'''  Where     the city you sleep in that night (its hotel); the morning of
            check-out, the hotel you leave; else the town a flight or train
            lands in that day. Nothing typed.
  Source    Open-Meteo - free, no key, no account: its place search, then
            its daily forecast (16 days ahead). Kept an hour per city.
''',
         r'''  Where     the city you sleep in that night (its hotel); the morning of
            check-out, the hotel you leave; else the town a flight or train
            lands in that day. Nothing typed. RA07, 19 Nov 2026 - before
            anything is booked, the Things to do planned that day, else
            where most of the trip's Things to do are (Demetri, on a trip
            with no bookings: "Why can't i see any weather??").
  Source    Open-Meteo - free, no key, no account: its place search, then
            its daily forecast (16 days ahead). Kept an hour per city.
'''),
        (r'''

def days_for(city, country=''):
    """{date: day} for a city's next 16 days, or {}."""
''',
         r'''

def days_at(lat, lng):
    """RA07 - {date: day} for a map position (a Thing to do's), or {}."""
    if off() or lat is None or lng is None:
        return {}
    lat, lng = round(lat, 1), round(lng, 1)
    key = 'tv-wx-at:%s,%s' % (lat, lng)
    c = _cache()
    got = c.get(key)
    if got is not None:
        return got
    out = _forecast(lat, lng)
    c.set(key, out, KEEP if out else KEEP_FAIL)
    return out


def _forecast(lat, lng):
    out = {}
    try:
        data = fetch(FORECAST % urllib.parse.urlencode({
            'latitude': lat, 'longitude': lng, 'daily': DAILY,
            'timezone': 'auto', 'forecast_days': 16}))
        d = data.get('daily') or {}
        for i, day in enumerate(d.get('time') or []):
            out[dt.date.fromisoformat(day)] = shape(d, i)
    except Exception:                                   # noqa: BLE001
        out = {}
    return out


def days_for(city, country=''):
    """{date: day} for a city's next 16 days, or {}."""
'''),
        (r'''    if got is not None:
        return got
    out = {}
    at = _where(city, country)
    if at:
        try:
            data = fetch(FORECAST % urllib.parse.urlencode({
                'latitude': at[0], 'longitude': at[1], 'daily': DAILY,
                'timezone': 'auto', 'forecast_days': 16}))
            d = data.get('daily') or {}
            for i, day in enumerate(d.get('time') or []):
                out[dt.date.fromisoformat(day)] = shape(d, i)
        except Exception:                               # noqa: BLE001
            out = {}
    c.set(key, out, KEEP if out else KEEP_FAIL)
    return out
''',
         r'''    if got is not None:
        return got
    at = _where(city, country)
    out = _forecast(*at) if at else {}
    c.set(key, out, KEEP if out else KEEP_FAIL)
    return out
'''),
        (r'''

def for_day(bookings, day, today=None):
    """The weather where you are on `day`, with the city - or None."""
    today = today or dt.date.today()
    if day < today or day > today + dt.timedelta(days=AHEAD):
        return None
    where = place_for(bookings, day)
    if not where:
        return None
    w = days_for(*where).get(day)
    if not w:
        return None
    return dict(w, city=where[0], day=day)


def for_days(bookings, days, today=None):
    """{day: weather} for those of `days` the forecast reaches."""
    out = {}
    for d in days:
        w = for_day(bookings, d, today)
        if w:
            out[d] = w
''',
         r'''

# ------------------------------------------- RA07: before any booking
def _placed(p):
    return getattr(p, 'lat', None) is not None and \
        getattr(p, 'lng', None) is not None


def place_name(p):
    """A name for where a Thing to do is: a known city its address names,
    else "near" the place itself."""
    from .where import CITIES, _words
    w = _words(getattr(p, 'address', '') or '')
    best, at = '', -1
    for name in CITIES:
        i = w.rfind(' %s ' % name)
        if i > at:
            best, at = name, i
    if best:
        return ' '.join(x[:1].upper() + x[1:] for x in best.split())
    return 'near %s' % (getattr(p, 'name', '') or 'your things to do')


def spot_for(places, day):
    """(lat, lng, name) from the Things to do: those planned that day,
    else where most of the trip's are - or None."""
    placed = [p for p in places or [] if _placed(p)]
    if not placed:
        return None
    that_day = [p for p in placed if getattr(p, 'day', None) == day]
    pool = that_day or placed
    groups = {}
    for p in pool:
        groups.setdefault((round(p.lat, 1), round(p.lng, 1)), []).append(p)
    best = max(groups.values(), key=len)
    p = best[0]
    return p.lat, p.lng, place_name(p)


def for_day(bookings, day, today=None, places=None):
    """The weather where you are on `day`, with the city - or None. The
    bookings say where first; RA07 - else the Things to do."""
    today = today or dt.date.today()
    if day < today or day > today + dt.timedelta(days=AHEAD):
        return None
    where = place_for(bookings, day)
    if where:
        w = days_for(*where).get(day)
        return dict(w, city=where[0], day=day) if w else None
    spot = spot_for(places, day)
    if not spot:
        return None
    w = days_at(spot[0], spot[1]).get(day)
    return dict(w, city=spot[2], day=day) if w else None


def for_days(bookings, days, today=None, places=None):
    """{day: weather} for those of `days` the forecast reaches."""
    out = {}
    for d in days:
        w = for_day(bookings, d, today, places)
        if w:
            out[d] = w
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('RA07 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_ra07_trip_days.py'" in read(pq):
        print('RA07 already applied.')
        return 0
    if "'test_ra06_kind_round.py'" not in read(pq):
        refuse('RA06 (apply_ra06_kind_round.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA07 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RA07 applied - weather from Things to do; spending on the trip days only.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
