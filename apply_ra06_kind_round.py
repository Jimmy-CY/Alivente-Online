# -*- coding: utf-8 -*-
"""apply_ra06_kind_round.py - round RA06, 19 Nov 2026.

RELEASE RA06 - BY KIND IN WHOLE EUROS; A FINISHED TRIP'S BUDGET IN PLAIN
WORDS; THE WEATHER WHERE YOU ARE.

    Demetri, 19 Nov: "We need to make Daily Spending to fit on one line,
    like the other expenses. Also, for this graph, we can remove the
    decimal places and round up to the nearest Euro."; on "Under budget,
    €780": "What is it actually telling us"; and "a small box with the
    Weather for that city for the day? Rain, temperature, etc?" - "show it
    on the computer too".

    - By kind: one line each, whole euros (the totals keep their cents).
    - A finished trip: Spent (a day on average), Budget, and Result - "€780
      less than budgeted" or "€200 more than budgeted". A note when days so
      far have no spending recorded; those days greyed under the bars.
    - travel/weather.py (Open-Meteo, free, no key): the city of that
      night's hotel. Phone Today: a weather box with tomorrow's line (the
      first day's before a trip); the itinerary, computer and phone: a chip
      on each day the forecast reaches. Never from a test.
    - Help on the computer and the phone; the phone app moves to tv20-1.

The suite, weather.py and the two weather templates ship beside this
patcher. Stands on RA05. Idempotent. Edits
backed up to .bak_ra06.
"""
import os
import sys

SUFFIX = '.bak_ra06'
MARK = 'RA06, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra06_kind_round.py',
    'travel/weather.py',
    'travel/templates/travel/_weather.html',
    'travel/templates/travel/_wx_icon.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra04_key_email.py',
    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    'test_ra05_budget.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra04_key_email.py',
    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    'test_ra05_budget.py',
    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    'test_ra06_kind_round.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    '.bak_ra05',
]

''',
         r'''    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    '.bak_ra05',
    # RA06, 19 Nov 2026 - By kind on one line each, in whole euros.
    '.bak_ra06',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. Only the trip&rsquo;s owner adds spending, sets the budget or deletes spending (&times;).</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan; after it, how the whole trip came out against the budget.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong>, and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
  </article>

''',
         r'''    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. Only the trip&rsquo;s owner adds spending, sets the budget or deletes spending (&times;).</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
  </article>

'''),
        (r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
''',
         r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p data-help-weather><strong>The weather.</strong> Each day of the itinerary that the forecast reaches (today and about two weeks ahead) shows the weather where you are that day &ndash; the city of that night&rsquo;s hotel (or of the hotel you leave that morning, or where that day&rsquo;s flight lands): an icon, the high and low, and the chance of rain. Hover over it for the rest. On the phone, <strong>Today</strong> has a weather box at the top &ndash; the city, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow &ndash; and, before a trip, the first day&rsquo;s forecast once it is about two weeks away. The forecast comes from Open-Meteo, free and with nothing to set up; it is looked up once an hour, and if it cannot be reached there is simply no weather.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
'''),
    ]),
    (os.path.join('test_ra05_budget.py'), [
        (r'''   'HELP (phone): Budget and spending')
ph = read(J(TV, 'phone.py'))
ok("SW_VERSION = 'tv19-1'" in ph and '?v=tv19-1' in read(
    J(TT, 'm', 'base.html')), 'THE PHONE APP moves to tv19-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
''',
         r'''   'HELP (phone): Budget and spending')
ph = read(J(TV, 'phone.py'))
# RA06 moved it on again: tv19-1 or later.
import re as _re                                            # noqa: E402
_v = _re.search(r"SW_VERSION = 'tv(\d+)-\d+'", ph)
ok(_v and int(_v.group(1)) >= 19 and '?v=tv%s-' % _v.group(1) in read(
    J(TT, 'm', 'base.html')), 'THE PHONE APP moves to tv19-1 (or later)')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-two { display: grid; grid-template-columns: 1fr 1.3fr; gap: 8px; }
.tv-spend-day { padding-top: 6px; scroll-margin-top: 70px; }
''',
         r'''.tv-two { display: grid; grid-template-columns: 1fr 1.3fr; gap: 8px; }
.tv-spend-day { padding-top: 6px; scroll-margin-top: 70px; }
/* RA06, 19 Nov 2026 - days with nothing recorded; the weather on Today and the itinerary. */
.tv-bud-note { margin: 10px 0 0; padding: 7px 10px; border-radius: 8px; background: #FCEFD9; color: #6B3A00; font-size: .85rem; }
.tv-bud-days .is-empty { color: #B4B2A9; }
.tv-dayhead { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.tv-wx-ico { flex: none; color: #5F6B70; }
.tv-wx-ico.is-sun, .tv-wx-ico.is-part { color: #BA7517; }
.tv-wx-ico.is-rain, .tv-wx-ico.is-storm, .tv-wx-ico.is-snow { color: #185FA5; }
.tv-wx.is-compact { display: inline-flex; align-items: center; gap: 5px; padding: 2px 10px 2px 7px; border-radius: 999px; border: 1px solid #D5DDE0; background: #FFFFFF; font-size: .82rem; font-weight: 600; letter-spacing: 0; text-transform: none; color: #1D2B31; vertical-align: middle; }
.tv-wx-lo { color: #6B777C; font-weight: 500; }
.tv-wx-r { color: #185FA5; }
.tv-wx:not(.is-compact) { display: flex; gap: 12px; align-items: center; padding: 12px 14px; margin-bottom: 10px; border-radius: 14px; background: #EAF4FB; border: 1px solid #CFE3F2; color: #1D2B31; }
.tv-wx-main { min-width: 0; flex: 1; }
.tv-wx-head b { font-weight: 700; } .tv-wx-head span { color: #5B6B72; }
.tv-wx-row { display: flex; gap: 14px; flex-wrap: wrap; font-size: .9rem; margin-top: 2px; }
.tv-wx:not(.is-compact) .tv-wx-t { font-size: 1.15rem; font-weight: 700; }
.tv-wx-next { font-size: .82rem; color: #5B6B72; margin-top: 3px; }
@media (prefers-color-scheme: dark) {
  .tv-wx:not(.is-compact) { background: #1A2A33; border-color: #2B3F4A; color: #E6ECEE; }
  .tv-wx.is-compact { background: #1A2428; border-color: #2B383D; color: #E6ECEE; }
  .tv-wx-head span, .tv-wx-next, .tv-wx-lo { color: #A9B6BB; }
  .tv-bud-note { background: #3A2A10; color: #F2CF95; }
}
'''),
    ]),
    (os.path.join('travel', 'budget.py'), [
        (r'''            'pct': int(v / top * 100), 'today': d == today,
            'future': d > today,
            'over': per_day is not None and v > per_day,
            'over_by': whole(v - per_day) if per_day is not None and
            v > per_day else ''})
    return {
        'set': trip.budget is not None, 'by': trip.budget_by,
        'per_day': per_day, 'per_day_label': whole(per_day),
''',
         r'''            'pct': int(v / top * 100), 'today': d == today,
            'future': d > today,
            # RA06 - a day of the trip so far with nothing recorded.
            'empty': not v and d <= today and start is not None and
            start <= d <= (end or start),
            'over': per_day is not None and v > per_day,
            'over_by': whole(v - per_day) if per_day is not None and
            v > per_day else ''})
    # RA06, 19 Nov 2026 - days so far with no spending recorded (Demetri,
    # on "Under budget, €780" for a trip with one day filled in: "What is
    # it actually telling us?").
    so_far = [c for c in chart if not c['future'] and start and
              start <= c['day'] <= (end or start)]
    empty = [c for c in so_far if c['empty']]
    return {
        'empty_days': len(empty), 'days_so_far': len(so_far),
        'set': trip.budget is not None, 'by': trip.budget_by,
        'per_day': per_day, 'per_day_label': whole(per_day),
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''                     trips_for)
from .views import (coming_up, eur, included, money_state, requests_for,
                    shape, span,
                    totals, travel_view)
''',
         r'''                     trips_for)
from .views import (coming_up, eur, included, money_state, requests_for,
                    with_weather,
                    shape, span,
                    totals, travel_view)
'''),
        (r'''# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
SW_VERSION = 'tv19-1'
SW_ASSETS = '95a8d6229257'


''',
         r'''# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
SW_VERSION = 'tv20-1'
SW_ASSETS = '030cdeda93c3'


'''),
        (r'''            ctx['can_spend'] = budget.can_spend(trip, me)
        ctx['coming'] = coming_up(shaped, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
''',
         r'''            ctx['can_spend'] = budget.can_spend(trip, me)
        ctx['coming'] = coming_up(shaped, day)
        # RA06, 19 Nov 2026 - the weather where you are (Demetri: "a small
        # box with the Weather for that city for the day").
        from . import weather
        if now:
            ctx['wx'] = weather.for_day(shaped, day, day)
            ctx['wx_next'] = weather.for_day(shaped, day + dt.timedelta(1),
                                             day)
        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
'''),
        (r'''    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
        # my days shows on Things to do.
''',
         r'''    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': with_weather(itinerary(t, bs, pl), bs)
        if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
        # my days shows on Things to do.
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget.html'), [
        (r'''        <div class="tv-bud-k"><span>{% if bud.over %}Over the holiday&rsquo;s budget{% else %}Left for {{ bud.to_go }} day{{ bud.to_go|pluralize }}{% endif %}</span><b>{{ bud.left_label }}</b><small>{% if bud.keep_label %}{{ bud.keep_label }} a day keeps you on budget{% elif bud.over %}keep adding spending &ndash; it all counts{% else %}the last day{% endif %}</small></div>
    {% elif bud.when == 'after' %}
        <div class="tv-bud-k"><span>Spent</span><b data-bud-spent>{{ bud.spent_label }}</b><small>{% if bud.avg_label %}{{ bud.avg_label }} a day{% endif %}</small></div>
        <div class="tv-bud-k"><span>Budget</span><b>{{ bud.total_label }}</b><small>{{ bud.per_day_label }} a day</small></div>
        <div class="tv-bud-k {% if bud.over %}is-bad{% else %}is-good{% endif %}" data-bud-pace="{% if bud.over %}behind{% else %}ahead{% endif %}"><span>{% if bud.over %}Over budget{% else %}Under budget{% endif %}</span><b>{{ bud.left_label }}</b><small>the trip is over</small></div>
    {% else %}
        <div class="tv-bud-k"><span>For the holiday</span><b>{{ bud.total_label|default:"–" }}</b><small>{% if bud.days %}{{ bud.days }} days &times; {{ bud.per_day_label }}{% else %}the trip needs its dates{% endif %}</small></div>
        <div class="tv-bud-k"><span>Spent so far</span><b data-bud-spent>{{ bud.spent_label }}</b><small>the trip has not started</small></div>
    {% endif %}
    </div>
    {% if bud.total %}<div class="tv-bar tv-bud-bar is-{% if bud.over %}red{% elif bud.pct >= 90 %}amber{% else %}ok{% endif %}" aria-hidden="true" style="margin-top: 12px"><span style="width: {{ bud.pct }}%"></span></div>
    <div class="tv-sub small" style="margin-top: 4px">{{ bud.spent_label }} of {{ bud.total_label }} used &middot; {{ bud.pct }}%{% if bud.pending %} &middot; {{ bud.pending }} waiting for an exchange rate{% endif %}</div>{% endif %}
''',
         r'''        <div class="tv-bud-k"><span>{% if bud.over %}Over the holiday&rsquo;s budget{% else %}Left for {{ bud.to_go }} day{{ bud.to_go|pluralize }}{% endif %}</span><b>{{ bud.left_label }}</b><small>{% if bud.keep_label %}{{ bud.keep_label }} a day keeps you on budget{% elif bud.over %}keep adding spending &ndash; it all counts{% else %}the last day{% endif %}</small></div>
    {% elif bud.when == 'after' %}
        {% comment %} RA06, 19 Nov 2026 - the trip is over: what was spent, the budget, and the result in plain words (Demetri: "What is it actually telling us?"). {% endcomment %}
        <div class="tv-bud-k"><span>Spent</span><b data-bud-spent>{{ bud.spent_label }}</b><small>{% if bud.avg_label %}{{ bud.avg_label }} a day on average{% else %}nothing recorded{% endif %}</small></div>
        <div class="tv-bud-k"><span>Budget</span><b>{{ bud.total_label }}</b><small>{{ bud.per_day_label }} a day</small></div>
        <div class="tv-bud-k {% if bud.over %}is-bad{% else %}is-good{% endif %}" data-bud-pace="{% if bud.over %}behind{% else %}ahead{% endif %}" data-bud-result><span>Result</span><b>{{ bud.left_label }} {% if bud.over %}more{% else %}less{% endif %}</b><small>than budgeted</small></div>
    {% else %}
        <div class="tv-bud-k"><span>For the holiday</span><b>{{ bud.total_label|default:"–" }}</b><small>{% if bud.days %}{{ bud.days }} days &times; {{ bud.per_day_label }}{% else %}the trip needs its dates{% endif %}</small></div>
        <div class="tv-bud-k"><span>Spent so far</span><b data-bud-spent>{{ bud.spent_label }}</b><small>the trip has not started</small></div>
    {% endif %}
    </div>
    {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
    {% if bud.total %}<div class="tv-bar tv-bud-bar is-{% if bud.over %}red{% elif bud.pct >= 90 %}amber{% else %}ok{% endif %}" aria-hidden="true" style="margin-top: 12px"><span style="width: {{ bud.pct }}%"></span></div>
    <div class="tv-sub small" style="margin-top: 4px">{{ bud.spent_label }} of {{ bud.total_label }} used &middot; {{ bud.pct }}%{% if bud.pending %} &middot; {{ bud.pending }} waiting for an exchange rate{% endif %}</div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget_chart.html'), [
        (r'''        {% for c in bud.chart %}<a class="tv-bud-col{% if c.over %} is-over{% endif %}{% if c.today %} is-today{% endif %}{% if c.future %} is-future{% endif %}" href="#sp{{ c.day|date:'Ymd' }}" title="{{ c.day|date:'D j M' }}: {{ c.label|default:'nothing' }}{% if c.over %} - {{ c.over_by }} over{% endif %}" data-chart-day="{{ c.day|date:'Y-m-d' }}"><small>{{ c.label }}</small><i style="height: {{ c.pct }}%"></i></a>{% endfor %}
    </div>
    <div class="tv-bud-days" style="--n: {{ bud.chart|length }}">{% for c in bud.chart %}<span{% if c.today %} class="is-today"{% endif %}>{% if c.today %}<i class="w">Today</i><i class="n">{{ c.day|date:"j" }}</i>{% else %}<i class="w">{{ c.day|date:"D" }} </i>{{ c.day|date:"j" }}{% endif %}</span>{% endfor %}</div>
</div>
''',
         r'''        {% for c in bud.chart %}<a class="tv-bud-col{% if c.over %} is-over{% endif %}{% if c.today %} is-today{% endif %}{% if c.future %} is-future{% endif %}" href="#sp{{ c.day|date:'Ymd' }}" title="{{ c.day|date:'D j M' }}: {{ c.label|default:'nothing' }}{% if c.over %} - {{ c.over_by }} over{% endif %}" data-chart-day="{{ c.day|date:'Y-m-d' }}"><small>{{ c.label }}</small><i style="height: {{ c.pct }}%"></i></a>{% endfor %}
    </div>
    <div class="tv-bud-days" style="--n: {{ bud.chart|length }}">{% for c in bud.chart %}<span class="{% if c.today %}is-today{% endif %}{% if c.empty %} is-empty{% endif %}"{% if c.empty %} title="Nothing recorded"{% endif %}>{% if c.today %}<i class="w">Today</i><i class="n">{{ c.day|date:"j" }}</i>{% else %}<i class="w">{{ c.day|date:"D" }} </i>{{ c.day|date:"j" }}{% endif %}</span>{% endfor %}</div>
</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-ref { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.05rem; letter-spacing: .02em; }
.tv-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 16px; }
.tv-kindbar { display: grid; grid-template-columns: 110px minmax(0, 1fr) 90px; gap: 10px; align-items: center; font-size: 0.9rem; }
.tv-kindbar .tv-bar span { background: var(--alv-accent); }
.tv-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; max-width: 820px; }
''',
         r'''.tv-ref { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.05rem; letter-spacing: .02em; }
.tv-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 16px; }
/* RA06, 19 Nov 2026 - Daily spending on one line, like the others. */
.tv-kindbar { display: grid; grid-template-columns: 150px minmax(0, 1fr) 90px; gap: 10px; align-items: center; font-size: 0.9rem; }
.tv-kindbar > span:first-child { white-space: nowrap; }
.tv-kindbar .tv-bar span { background: var(--alv-accent); }
.tv-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; max-width: 820px; }
'''),
        (r'''  .tv-bud-days .w { display: none; } .tv-bud-days .is-today .n { display: inline; }
}
</style>
''',
         r'''  .tv-bud-days .w { display: none; } .tv-bud-days .is-today .n { display: inline; }
}
/* RA06, 19 Nov 2026 - finished-trip budget wording; days with nothing recorded; the weather on the itinerary. */
.tv-bud-note { margin: 10px 0 0; padding: 7px 10px; border-radius: 8px; background: #FCEFD9; color: #6B3A00; font-size: .85rem; }
.tv-bud-days .is-empty { color: #B4B2A9; }
.tv-dayhead { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.tv-wx-ico { flex: none; color: #5F6B70; }
.tv-wx-ico.is-sun, .tv-wx-ico.is-part { color: #BA7517; }
.tv-wx-ico.is-rain, .tv-wx-ico.is-storm, .tv-wx-ico.is-snow { color: #185FA5; }
.tv-wx.is-compact { display: inline-flex; align-items: center; gap: 5px; padding: 2px 10px 2px 7px; border-radius: 999px; border: 1px solid #D5DDE0; background: #FFFFFF; font-size: .82rem; font-weight: 600; letter-spacing: 0; text-transform: none; color: #1D2B31; vertical-align: middle; }
.tv-wx-lo { color: #6B777C; font-weight: 500; }
.tv-wx-r { color: #185FA5; }
.tv-wx:not(.is-compact) { display: flex; gap: 12px; align-items: center; padding: 12px 14px; margin-bottom: 10px; border-radius: 14px; background: #EAF4FB; border: 1px solid #CFE3F2; color: #1D2B31; }
.tv-wx-main { min-width: 0; flex: 1; }
.tv-wx-head b { font-weight: 700; } .tv-wx-head span { color: #5B6B72; }
.tv-wx-row { display: flex; gap: 14px; flex-wrap: wrap; font-size: .9rem; margin-top: 2px; }
.tv-wx:not(.is-compact) .tv-wx-t { font-size: 1.15rem; font-weight: 700; }
.tv-wx-next { font-size: .82rem; color: #5B6B72; margin-top: 3px; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv19-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv20-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv19-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv20-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'today.html'), [
        (r'''{% elif on_now %}
{% if passes_today %}<a href="{% url 'travel:m_passes' %}" class="tv-btn wide" data-passes-today><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h2M3 9h15"/></svg> Boarding passes</a>{% endif %}
{% if bud and bud.set %}{% comment %} RA05, 19 Nov 2026 - the Today line: spent today against the day's budget, ahead or behind plan. {% endcomment %}<section class="tv-card tv-bud-today" data-today-budget>
  <div class="tv-row"><a href="{% url 'travel:m_trip' trip.pk %}?tab=costs" style="color: inherit; text-decoration: none">Today <b{% if bud.today_over %} class="tv-over"{% endif %}>{{ bud.today_label }}</b> of {{ bud.per_day_label }}</a>{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-small" style="font-weight: 700" data-spend-new>+ Spending</a>{% endif %}</div>
''',
         r'''{% elif on_now %}
{% if passes_today %}<a href="{% url 'travel:m_passes' %}" class="tv-btn wide" data-passes-today><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h2M3 9h15"/></svg> Boarding passes</a>{% endif %}
{% include 'travel/_weather.html' with w=wx nxt=wx_next %}
{% if bud and bud.set %}{% comment %} RA05, 19 Nov 2026 - the Today line: spent today against the day's budget, ahead or behind plan. {% endcomment %}<section class="tv-card tv-bud-today" data-today-budget>
  <div class="tv-row"><a href="{% url 'travel:m_trip' trip.pk %}?tab=costs" style="color: inherit; text-decoration: none">Today <b{% if bud.today_over %} class="tv-over"{% endif %}>{{ bud.today_label }}</b> of {{ bud.per_day_label }}</a>{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-small" style="font-weight: 700" data-spend-new>+ Spending</a>{% endif %}</div>
'''),
        (r'''  <div class="tv-muted">{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>
</a>
<p class="tv-h3">The first day · {{ trip.start|date:"D j M" }}</p>
<section class="tv-card">{% for b in first_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked for it yet.</p>{% endfor %}</section>
''',
         r'''  <div class="tv-muted">{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>
</a>
{% include 'travel/_weather.html' with w=wx nxt_label="" %}
<p class="tv-h3">The first day · {{ trip.start|date:"D j M" }}</p>
<section class="tv-card">{% for b in first_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked for it yet.</p>{% endfor %}</section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% for day, rows in itinerary %}
{% comment %} TR-9 (16 Nov 2026) put a day in your own order; TR-10 - by dragging the grip on the right of a row (Demetri: "I am not happy how the sorting happens on the mobile. It is cumbersome and not user intuitive"). Only the grip drags, so the page still scrolls and a row still opens. {% endcomment %}{% with dkey=day|date:'Y-m-d' %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<form method="post" action="{% url 'travel:m_day_order' trip.pk %}" class="tv-small tv-muted" style="margin: -4px 0 6px" data-order-status="{{ dkey }}"{% if not rows.custom %} hidden{% endif %}>{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}">Your order &middot; <button type="submit" class="tv-linkbtn" data-order-reset>Back to automatic</button></form>
<section class="tv-card" data-itinerary-day{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:m_day_order' trip.pk %}" data-day="{{ dkey }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}{% for b in rows %}{% if rows|length > 1 %}<div class="tv-drag" data-key="{{ b.order_key }}">{% include 'travel/m/_row.html' %}<span class="tv-grip" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day" title="Drag to change the order"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg></span></div>{% else %}{% include 'travel/m/_row.html' %}{% endif %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>{% endwith %}
''',
         r'''{% for day, rows in itinerary %}
{% comment %} TR-9 (16 Nov 2026) put a day in your own order; TR-10 - by dragging the grip on the right of a row (Demetri: "I am not happy how the sorting happens on the mobile. It is cumbersome and not user intuitive"). Only the grip drags, so the page still scrolls and a row still opens. {% endcomment %}{% with dkey=day|date:'Y-m-d' %}
<p class="tv-h3 tv-dayhead" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}{% include 'travel/_weather.html' with w=rows.wx compact=True %}</p>
<form method="post" action="{% url 'travel:m_day_order' trip.pk %}" class="tv-small tv-muted" style="margin: -4px 0 6px" data-order-status="{{ dkey }}"{% if not rows.custom %} hidden{% endif %}>{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}">Your order &middot; <button type="submit" class="tv-linkbtn" data-order-reset>Back to automatic</button></form>
<section class="tv-card" data-itinerary-day{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:m_day_order' trip.pk %}" data-day="{{ dkey }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}{% for b in rows %}{% if rows|length > 1 %}<div class="tv-drag" data-key="{{ b.order_key }}">{% include 'travel/m/_row.html' %}<span class="tv-grip" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day" title="Drag to change the order"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg></span></div>{% else %}{% include 'travel/m/_row.html' %}{% endif %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>{% endwith %}
'''),
        (r'''  <div class="tv-row"><span class="tv-muted">Daily spending &middot; {{ bud.per_day_label }} a day</span>{% if can_spend %}<a href="{% url 'travel:m_budget' trip.pk %}" class="tv-small" data-budget-edit>Change</a>{% endif %}</div>
  {% if bud.when == 'on' %}<div class="tv-row"><span class="tv-bud-big {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead{% else %}behind{% endif %}</span><span class="tv-muted tv-small">{{ bud.spent_label }} of {{ bud.planned_label }} so far</span></div>
  {% elif bud.when == 'after' %}<div class="tv-row"><span class="tv-bud-big {% if bud.over %}tv-over{% else %}tv-good{% endif %}" data-bud-pace="{% if bud.over %}behind{% else %}ahead{% endif %}">{{ bud.left_label }} {% if bud.over %}over{% else %}under{% endif %}</span><span class="tv-muted tv-small">{{ bud.spent_label }} of {{ bud.total_label }}</span></div>
  {% else %}<div class="tv-row"><span class="tv-bud-big">{{ bud.total_label|default:"–" }}</span><span class="tv-muted tv-small">for the holiday{% if bud.days %} &middot; {{ bud.days }} days{% endif %}</span></div>{% endif %}
  {% if bud.total %}<div class="tv-meter{% if bud.over %} is-red{% elif bud.pct >= 90 %} is-amber{% endif %}" aria-hidden="true"><span style="width: {{ bud.pct }}%"></span></div>{% endif %}
  {% if bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
  {% if bud.when == 'on' %}<p class="tv-muted tv-small" style="margin: 6px 0 0">{% if bud.keep_label %}{{ bud.keep_label }} a day for the last {{ bud.to_go }} day{{ bud.to_go|pluralize }} keeps you on {{ bud.total_label }}{% elif bud.over %}{{ bud.left_label }} over the holiday&rsquo;s {{ bud.total_label }}{% else %}The last day{% endif %}</p>{% endif %}
''',
         r'''  <div class="tv-row"><span class="tv-muted">Daily spending &middot; {{ bud.per_day_label }} a day</span>{% if can_spend %}<a href="{% url 'travel:m_budget' trip.pk %}" class="tv-small" data-budget-edit>Change</a>{% endif %}</div>
  {% if bud.when == 'on' %}<div class="tv-row"><span class="tv-bud-big {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead{% else %}behind{% endif %}</span><span class="tv-muted tv-small">{{ bud.spent_label }} of {{ bud.planned_label }} so far</span></div>
  {% elif bud.when == 'after' %}<div class="tv-row"><span class="tv-bud-big {% if bud.over %}tv-over{% else %}tv-good{% endif %}" data-bud-pace="{% if bud.over %}behind{% else %}ahead{% endif %}" data-bud-result>{{ bud.left_label }} {% if bud.over %}more{% else %}less{% endif %} than budgeted</span></div><div class="tv-muted tv-small">Spent {{ bud.spent_label }}{% if bud.avg_label %} ({{ bud.avg_label }} a day){% endif %} of {{ bud.total_label }}</div>
  {% else %}<div class="tv-row"><span class="tv-bud-big">{{ bud.total_label|default:"–" }}</span><span class="tv-muted tv-small">for the holiday{% if bud.days %} &middot; {{ bud.days }} days{% endif %}</span></div>{% endif %}
  {% if bud.total %}<div class="tv-meter{% if bud.over %} is-red{% elif bud.pct >= 90 %} is-amber{% endif %}" aria-hidden="true"><span style="width: {{ bud.pct }}%"></span></div>{% endif %}
  {% if bud.empty_days and bud.when != 'before' %}<p class="tv-bud-note" data-bud-empty>{% if bud.when == 'after' %}{{ bud.empty_days }} of the {{ bud.days_so_far }} days ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded, so this may not be the full picture.{% else %}{{ bud.empty_days }} of the {{ bud.days_so_far }} day{{ bud.days_so_far|pluralize }} so far ha{{ bud.empty_days|pluralize:"s,ve" }} no spending recorded.{% endif %}</p>{% endif %}
  {% if bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
  {% if bud.when == 'on' %}<p class="tv-muted tv-small" style="margin: 6px 0 0">{% if bud.keep_label %}{{ bud.keep_label }} a day for the last {{ bud.to_go }} day{{ bud.to_go|pluralize }} keeps you on {{ bud.total_label }}{% elif bud.over %}{{ bud.left_label }} over the holiday&rsquo;s {{ bud.total_label }}{% else %}The last day{% endif %}</p>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><span class="small"><span data-order-status="{{ day|date:'Y-m-d' }}"{% if not rows.custom %} hidden{% endif %}><span class="tv-sub" data-custom-order>Your order &middot; </span><form method="post" action="{% url 'travel:day_order' trip.pk %}" style="display: inline">{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}#d{{ day|date:'Ymd' }}"><button type="submit" class="tv-linkbtn" title="Put this day back in time order" data-order-reset>Back to automatic</button></form> &nbsp; </span><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></span></div>
        {% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - drag a row by its grip; the order is kept for the day, for everyone on the trip. TR-10 - the rows slide as you drag, it saves without reloading, Undo for a few seconds (travel/_reorder.html). {% endcomment %}<div class="tv-dayrows"{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:day_order' trip.pk %}" data-day="{{ day|date:'Y-m-d' }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}
        {% for r in rows %}<div class="tv-drag" data-key="{{ r.order_key }}">{% if rows|length > 1 %}<span class="tv-grip" title="Drag to change the order of the day" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day"><i class="fas fa-grip-vertical" aria-hidden="true"></i></span>{% endif %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}</div>{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}</div>
''',
         r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3 class="tv-dayhead">{{ day|date:"l j F" }}{% include 'travel/_weather.html' with w=rows.wx compact=True %}</h3><span class="small"><span data-order-status="{{ day|date:'Y-m-d' }}"{% if not rows.custom %} hidden{% endif %}><span class="tv-sub" data-custom-order>Your order &middot; </span><form method="post" action="{% url 'travel:day_order' trip.pk %}" style="display: inline">{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}#d{{ day|date:'Ymd' }}"><button type="submit" class="tv-linkbtn" title="Put this day back in time order" data-order-reset>Back to automatic</button></form> &nbsp; </span><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></span></div>
        {% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - drag a row by its grip; the order is kept for the day, for everyone on the trip. TR-10 - the rows slide as you drag, it saves without reloading, Undo for a few seconds (travel/_reorder.html). {% endcomment %}<div class="tv-dayrows"{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:day_order' trip.pk %}" data-day="{{ day|date:'Y-m-d' }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}
        {% for r in rows %}<div class="tv-drag" data-key="{{ r.order_key }}">{% if rows|length > 1 %}<span class="tv-grip" title="Drag to change the order of the day" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day"><i class="fas fa-grip-vertical" aria-hidden="true"></i></span>{% endif %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}</div>{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_pdf.html'), [
        (r'''</tr></table>
{% endif %}
{% if bud %}<p class="muted" data-pdf-budget>Daily spending budget: {{ bud.per_day_label }} a day{% if bud.total_label %}, {{ bud.total_label }} for the holiday{% endif %} · spent {{ bud.spent_label }}{% if bud.when == 'on' %} · {{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan{% elif bud.when == 'after' %} · {{ bud.left_label }} {% if bud.over %}over{% else %}under{% endif %} budget{% endif %}</p>{% endif %}{# RA05 #}

<h2 class="sec">Day by day</h2>
''',
         r'''</tr></table>
{% endif %}
{% if bud %}<p class="muted" data-pdf-budget>Daily spending budget: {{ bud.per_day_label }} a day{% if bud.total_label %}, {{ bud.total_label }} for the holiday{% endif %} · spent {{ bud.spent_label }}{% if bud.when == 'on' %} · {{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan{% elif bud.when == 'after' %} · {{ bud.left_label }} {% if bud.over %}more{% else %}less{% endif %} than budgeted{% if bud.empty_days %} ({{ bud.empty_days }} of {{ bud.days_so_far }} days with nothing recorded){% endif %}{% endif %}</p>{% endif %}{# RA05 #}

<h2 class="sec">Day by day</h2>
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''import mimetypes
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django.contrib import messages
''',
         r'''import mimetypes
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.contrib import messages
'''),
        (r'''    top = max(kinds.values()) if kinds else None
    label = dict(Booking.KINDS, spend='Daily spending')
    by_kind = [{'kind': label[k], 'icon': ICONS.get(k, 'fa-wallet'),
                'eur': eur(v), 'pct': int(v / top * 100) if top else 0}
               for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])]
    return {'total': eur(total), 'paid': eur(paid),
''',
         r'''    top = max(kinds.values()) if kinds else None
    label = dict(Booking.KINDS, spend='Daily spending')
    # RA06, 19 Nov 2026 - By kind in whole euros (Demetri: "for this
    # graph, we can remove the decimal places and round up to the nearest
    # Euro"); the totals keep their cents.
    by_kind = [{'kind': label[k], 'icon': ICONS.get(k, 'fa-wallet'),
                'eur': eur(v.quantize(Decimal('1'), ROUND_HALF_UP)),
                'pct': int(v / top * 100) if top else 0}
               for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])]
    return {'total': eur(total), 'paid': eur(paid),
'''),
        (r'''        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end),
''',
         r'''        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': with_weather(itinerary(t, bs, pl), bs)
        if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end),
'''),
        (r'''        # TR-12 - Suggest things to do.
        **idea_state(t, request, tab)})


''',
         r'''        # TR-12 - Suggest things to do.
        **idea_state(t, request, tab)})


def with_weather(days, bs):
    """RA06, 19 Nov 2026 - each day of the itinerary the forecast reaches
    gets the weather where you are (travel/weather.py). Demetri: "show it
    on the computer too"."""
    from . import weather
    wx = weather.for_days(bs, [d for d, _ in days])
    for d, rows in days:
        rows.wx = wx.get(d)
    return days


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
    raise SystemExit('RA06 REFUSED: %s' % msg)


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
    if "'test_ra06_kind_round.py'" in read(pq):
        print('RA06 already applied.')
        return 0
    if "'test_ra05_budget.py'" not in read(pq):
        refuse('RA05 (apply_ra05_budget.py) is not applied - this round registers after it.')
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
        print('RA06 --check: %d file(s) would change, none written; %d '
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
    print('RA06 applied - By kind in whole euros; a finished trip in plain words; the weather.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
