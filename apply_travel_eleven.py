# -*- coding: utf-8 -*-
"""apply_travel_eleven.py - round TR-11, 17 Nov 2026.

RELEASE 92 - TRAVEL: PLAN MY DAYS.

    Demetri, 17 Nov: "I want to add a button which will do a whole lot of
    thinking using AI, to optimise these activities/things to do across
    the days of my trip."

    - Things to do: "N things to do have no day yet - Plan my days".
    - Three questions (phone: three steps; computer: one page): can what is
      on a day move (booked: never); which mornings, afternoons, evenings
      to keep free (bookings greyed); pace, getting around, must-dos.
    - The AI looks each place up once (hours per weekday, visit length,
      quiet and busy times, book ahead, position) - travel/places.py, the
      small model. travel/planner.py fits them in by rules: never closed,
      never in a slot kept free or taken, never over the pace; near goes
      with near; from the hotel; the quiet time. A line about each day.
    - Your plan: a timeline per day, MOVED, Before you go, Move, Accept.
      Undo plan until the trip ends or you plan again - only what is still
      where the plan put it. Fit them in for things added afterwards.

New files ship beside this patcher. Stands on GS-4 (apply_gate_retry.py).
Idempotent. Edits backed up to .bak_travel11. MIGRATION: travel 0009 - run
`python manage.py migrate`.
"""
import os
import sys

SUFFIX = '.bak_travel11'
MARK = 'TR-11, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_eleven.py',
    'travel/migrations/0009_plan_my_days.py',
    'travel/planner.py',
    'travel/templates/travel/_plan_banner.html',
    'travel/templates/travel/_plan_choices.html',
    'travel/templates/travel/_plan_fit_body.html',
    'travel/templates/travel/_plan_js.html',
    'travel/templates/travel/_plan_notes.html',
    'travel/templates/travel/_plan_working_body.html',
    'travel/templates/travel/m/plan_failed.html',
    'travel/templates/travel/m/plan_fit.html',
    'travel/templates/travel/m/plan_review.html',
    'travel/templates/travel/m/plan_setup.html',
    'travel/templates/travel/m/plan_working.html',
    'travel/templates/travel/plan_failed.html',
    'travel/templates/travel/plan_fit.html',
    'travel/templates/travel/plan_review.html',
    'travel/templates/travel/plan_setup.html',
    'travel/templates/travel/plan_working.html',
    'travel/views_plan.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_ten.py',
    # GS-4, 16 Nov 2026 - Release 91: a timing ratio measured twice.
    'test_gate_retry.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_ten.py',
    # GS-4, 16 Nov 2026 - Release 91: a timing ratio measured twice.
    'test_gate_retry.py',
    # TR-11, 17 Nov 2026 - Release 92: Plan my days - spread Things to do
    # over the trip; Undo plan; Fit them in.
    'test_travel_eleven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # ratio twice before it stops a push.
    '.bak_gateretry',
]

''',
         r'''    # ratio twice before it stops a push.
    '.bak_gateretry',
    # TR-11, 17 Nov 2026 - Release 92: Plan my days.
    '.bak_travel11',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
  </article>

''',
         r'''    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps.</p>
  </article>

'''),
    ]),
    (os.path.join('test_travel_ten.py'), [
        (r'''   'the server says whether the day still differs from automatic')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv10-1'" in ph and '?v=tv10-1' in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new script and style (tv10-1)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
''',
         r'''   'the server says whether the day still differs from automatic')
ph = read(J(TA, 'phone.py'))
# TR-11 (17 Nov) moved the version on again: tv10-1 or later, worker and
# page agreeing.
import re                                                   # noqa: E402
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 10 and
   '?v=tv%s-%s' % _v.groups() in read(J(TT, 'm', 'base.html')),
   'the phone fetches the new script and style (tv10-1 or later)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-toast.on { transform: translate(-50%, 0); }
.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; font-size: 15px; padding: 0; }
''',
         r'''.tv-toast.on { transform: translate(-50%, 0); }
.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; font-size: 15px; padding: 0; }

/* TR-11, 17 Nov 2026 - Plan my days on the phone: three steps, the free-slot grid, the proposal. */
.tv-pl-grid { display: grid; grid-template-columns: 4.2rem repeat(3, minmax(0, 1fr)); gap: 6px; align-items: stretch; }
.tv-pl-grid .tv-pl-head { font-size: 11px; font-weight: 700; color: #5B6B72; text-align: center; letter-spacing: .04em; align-self: end; }
.tv-pl-grid .tv-pl-day { font-weight: 700; align-self: center; font-size: .9rem; }
.tv-pl-cell { position: relative; display: flex; align-items: center; justify-content: center; text-align: center; min-height: 48px; border-radius: 9px; font-size: .8rem; font-weight: 700; line-height: 1.15; padding: 4px; margin: 0; cursor: pointer; border: 1px solid #9CC9CF; background: #E3F1F3; color: #0B5A63; }
.tv-pl-cell input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-cell .tv-pl-off { display: none; }
.tv-pl-cell input:checked ~ .tv-pl-free { display: none; }
.tv-pl-cell input:checked ~ .tv-pl-off { display: inline; }
.tv-pl-cell:has(input:checked) { border: 2px solid #B85C00; background: #FFF1E3; color: #8A4500; }
.tv-pl-cell:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-pl-taken { display: flex; align-items: center; justify-content: center; text-align: center; min-height: 48px; border-radius: 9px; font-size: .74rem; font-weight: 600; line-height: 1.15; padding: 4px; border: 1px solid #C9D3D6; background: #E9EDEF; color: #4A5A61; }
.tv-pl-key { display: flex; flex-wrap: wrap; gap: 12px; font-size: .8rem; color: #4A5A61; }
.tv-pl-key i { display: inline-block; width: 13px; height: 13px; border-radius: 4px; vertical-align: -2px; margin-right: 5px; }
.tv-pl-seg { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); grid-auto-flow: column; gap: 6px; }
.tv-pl-opt { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; min-height: 52px; border-radius: 9px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1D2B31; margin: 0; cursor: pointer; padding: 4px; }
.tv-pl-opt input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-opt b { font-size: .95rem; }
.tv-pl-opt span { font-size: .74rem; color: #4A5A61; }
.tv-pl-opt:has(input:checked) { border: 2px solid #0F7480; background: #E3F1F3; color: #0B5A63; }
.tv-pl-opt:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-pl-star { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E1E6E8; min-height: 44px; margin: 0; cursor: pointer; font-weight: 400; }
.tv-pl-star input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-star svg { fill: none; stroke: #8A9BA2; }
.tv-pl-star:has(input:checked) svg { fill: #B85C00; stroke: #B85C00; }
.tv-pl-star:focus-within { outline: 2px solid #0F7480; outline-offset: -2px; }
.tv-pl-lock { display: flex; gap: 8px; align-items: center; background: #EEF5F6; border-radius: 9px; padding: 9px 10px; font-size: .88rem; }
.tv-pl-tag { display: inline-flex; gap: 3px; align-items: center; font-size: .68rem; font-weight: 700; border-radius: 999px; padding: 1px 7px; border: 1px solid #8A9BA2; color: #4A5A61; white-space: nowrap; }
.tv-pl-tag.moved { border-color: #B85C00; color: #8A4500; }
.tv-pl-tag.must { border-color: #0F7480; color: #0B5A63; }
.tv-pl-why { font-size: .86rem; background: #EEF5F6; border-radius: 8px; padding: 7px 9px; }
.tv-pl-hop { font-size: .76rem; color: #5B6B72; padding-left: 4px; }
.tv-pl-notes { background: #FFF6EC; border: 1px solid #E8C9A3; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.tv-pl-notes b.h { color: #8A4500; }
.tv-pl-steps { display: flex; flex-direction: column; }
.tv-pl-step { display: flex; gap: 12px; align-items: flex-start; padding: 9px 0; }
.tv-pl-step.now { font-weight: 700; }
.tv-pl-step.todo { color: #5B6B72; }
.tv-pl-bar { height: 8px; border-radius: 8px; background: #D5DDE0; overflow: hidden; }
.tv-pl-bar span { display: block; height: 8px; background: #0F7480; }
.tv-pl-banner { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; background: #1D2B31; color: #FFFFFF; border-radius: 12px; padding: 8px 14px; }
.tv-pl-banner button { background: none; border: 0; color: #7FD3DA; font-weight: 700; min-height: 44px; padding: 0 4px; cursor: pointer; font: inherit; font-weight: 700; }
.tv-pl-cta { background: #0F7480; color: #FFFFFF; border-radius: 14px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.tv-pl-cta a.go { background: #FFFFFF; color: #0F7480; border-radius: 10px; min-height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; text-decoration: none; }

.tv-pl-dayrow { display: grid; grid-template-columns: 46px 1fr; gap: 8px; padding: 7px 0; }
.tv-pl-dayrow .t { font-weight: 700; color: #0B5A63; font-size: 14px; }
.tv-pl-move summary { list-style: none; cursor: pointer; color: var(--tv-teal); font-size: 13px; font-weight: 600; min-height: 32px; display: flex; align-items: center; }
.tv-pl-move summary::-webkit-details-marker { display: none; }
.tv-pl-move form { display: flex; gap: 6px; align-items: center; margin: 4px 0 2px; }
.tv-pl-move select { flex: 1; min-height: 44px; border: 1px solid var(--tv-line); border-radius: 10px; padding: 0 8px; font: inherit; background: #fff; }
.tv-pl-bottom { background: #FFFFFF; border-top: 1px solid var(--tv-line); border-radius: 14px; padding: 12px 14px; margin: 12px 0 0; display: flex; gap: 10px; }
.tv-pl-bottom .tv-btn { flex: 1; }
.tv-pl-stephead { display: flex; gap: 6px; margin: 4px 0 2px; }
.tv-pl-stephead span { flex: 1; height: 4px; border-radius: 4px; background: #D5DDE0; }
.tv-pl-stephead span.on { background: #0F7480; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''                                null=True, blank=True, related_name='places')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_places'
''',
         r'''                                null=True, blank=True, related_name='places')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TR-11, 17 Nov 2026 - for Plan my days: where it is, and what the
    # planner needs to know about it (weekly hours, how long a visit
    # takes, when it is quiet, whether to book), worked out once and kept.
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    facts = models.JSONField(default=dict, blank=True)
    facts_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'travel_places'
'''),
        (r'''    def __str__(self):
        return '%s %s' % (self.trip_id, self.day)
''',
         r'''    def __str__(self):
        return '%s %s' % (self.trip_id, self.day)


class TripPlan(models.Model):
    """TR-11, 17 Nov 2026 - Plan my days (Demetri: "I want to add a button
    which will do a whole lot of thinking using AI, to optimise these
    activities/things to do across the days of my trip").

    answers   what was asked: per place on a day 'keep' or 'move', the
              slots kept free ['2027-03-15-m', ...], pace, getting around,
              must-dos.
    result    the proposal: days with their planned places, times, the
              way between them and a line about each day; notes; what did
              not fit.
    before    each planned place's day and time before the plan, and the
              day orders it cleared - what Undo plan puts back.
    applied   each planned place's day and time as the plan left it: Undo
              only touches a place still exactly there."""
    STATUS = [('working', 'Working it out'), ('ready', 'Ready to review'),
              ('failed', 'Could not plan'), ('applied', 'Applied'),
              ('undone', 'Undone'), ('discarded', 'Discarded'),
              # A later plan was accepted: this one stays on the trip, but
              # Undo plan undoes only the latest run.
              ('replaced', 'Replaced by a later plan')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='plans')
    status = models.CharField(max_length=10, choices=STATUS,
                              default='working')
    answers = models.JSONField(default=dict, blank=True)
    progress = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    before = models.JSONField(default=dict, blank=True)
    applied = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return 'Plan %s for trip %s (%s)' % (self.pk, self.trip_id,
                                             self.status)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, inbox
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
''',
         r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
'''),
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv10-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv11-1'


'''),
        (r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'money': totals(bs), 'costs': costs,
        'people': [t.owner] + list(t.shared_with.all()), 'tab': 'trips',
        'coming': coming_up(bs, _today())})


''',
         r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
        # my days shows on Things to do.
        'trip_days': _days_of(t) if sub == 'wish' else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'money': totals(bs), 'costs': costs,
        'people': [t.owner] + list(t.shared_with.all()), 'tab': 'trips',
        'coming': coming_up(bs, _today()),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **(planner.page_state(t, request)
           if sub in ('itinerary', 'wish') else {})})


def _days_of(t):
    from .views_places import trip_days
    return trip_days(t)


'''),
    ]),
    (os.path.join('travel', 'places.py'), [
        (r'''    Place.objects.filter(booking=b).update(booking=None, day=None,
                                           time=None)
''',
         r'''    Place.objects.filter(booking=b).update(booking=None, day=None,
                                           time=None)


# ==========================================================================
# TR-11, 17 Nov 2026 - PLAN MY DAYS: WHAT THE PLANNER NEEDS TO KNOW.
#
# Demetri: "It needs to look at opening hours, peak periods, proximity to
# other activities to reduce travel/walking time". The AI does the knowing
# (this file); travel/planner.py does the fitting, by rules it always
# keeps. Busy times are the AI's general knowledge and say so (Demetri:
# "Busy times based on AI's knowledge is enough"). The small model, no web
# search: the place's own looked-up hours go in as what to trust.
# ==========================================================================
PLAN_MODEL = os.environ.get('TRAVEL_PLAN_MODEL', 'claude-haiku-4-5')
DAYS7 = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
FACTS_SYSTEM = """You help plan a family trip. For the one place given, \
call record_facts once with what a careful local guide would know.

- Opening hours per weekday as "HH:MM-HH:MM", two ranges joined by a comma \
("09:00-13:00,16:00-20:00"), "closed", or "" when you do not know. The \
hours given with the place are what to trust; use the trip's dates for \
season.
- lat and lng: the place's position to 4 decimals; leave them out if you \
are not sure of the place.
- minutes: a typical visit, not the longest one.
- best: when to go to avoid the crowds or for the light - morning, \
afternoon, evening or any.
- busy and quiet: a few words each ("late morning, cruise days"; "first \
hour, after 17:00"). This is general knowledge, not live data.
- book: true only when tickets usually need booking ahead (timed entry, \
sells out); book_note says how, in a few words.
- For a restaurant or cafe, meal: lunch, dinner or either.
- Never invent: leave out what you do not know."""
FACTS_TOOL = {
    'name': 'record_facts',
    'description': 'Record what the planner needs to know about the place.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'lat': {'type': 'number'}, 'lng': {'type': 'number'},
            'city': {'type': 'string', 'description': 'Its town or city.'},
            'area': {'type': 'string', 'description':
                     'Its neighbourhood, in a few words.'},
            'open': {'type': 'object', 'description':
                     'mon..sun, each "HH:MM-HH:MM", ranges joined by a '
                     'comma, "closed", or "".',
                     'properties': {d: {'type': 'string'} for d in DAYS7}},
            'minutes': {'type': 'integer'},
            'best': {'type': 'string', 'enum': ['morning', 'afternoon',
                                                'evening', 'any']},
            'busy': {'type': 'string'}, 'quiet': {'type': 'string'},
            'book': {'type': 'boolean'}, 'book_note': {'type': 'string'},
            'meal': {'type': 'string', 'enum': ['lunch', 'dinner',
                                               'either']},
            'outdoors': {'type': 'boolean'},
        },
        'required': ['minutes', 'best'],
    },
}
REASONS_SYSTEM = """You write one short line for each day of a trip plan \
that has already been made - why the day is shaped as it is (what is near \
what, when it is quiet, what is closed on another day). At most 22 words a \
line, plain and friendly, no exclamation marks, no emoji. Never change the \
plan or add places. Call record_reasons once."""
REASONS_TOOL = {
    'name': 'record_reasons',
    'description': 'One line per day of the plan.',
    'input_schema': {
        'type': 'object',
        'properties': {'days': {'type': 'array', 'items': {
            'type': 'object', 'properties': {
                'day': {'type': 'string', 'description': 'YYYY-MM-DD'},
                'why': {'type': 'string'}},
            'required': ['day', 'why']}}},
        'required': ['days'],
    },
}


def _client(client):
    if client is not None:
        return client
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise LookupError_('The Anthropic key is not set on the server.')
    import anthropic
    return anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1)


def _tool_input(msg, name):
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                getattr(block, 'name', '') == name and \
                isinstance(block.input, dict):
            return block.input
    raise LookupError_('Nothing came back.')


def call_facts(place, start=None, client=None):
    """record_facts for one place: a dict (see FACTS_TOOL)."""
    client = _client(client)
    ask = ['Place: %s' % place.name, 'Kind: %s' % place.kind]
    for label, v in (('Address', place.address), ('Hours', place.hours),
                     ('About', place.about), ('Website', place.website)):
        if v:
            ask.append('%s: %s' % (label, v))
    trip = place.trip
    where = getattr(trip, 'where', '') or trip.countries
    if where:
        ask.append('The trip is to: %s' % where)
    if start:
        ask.append('The trip starts: %s' % start.isoformat())
    try:
        msg = client.messages.create(
            model=PLAN_MODEL, max_tokens=700, system=FACTS_SYSTEM,
            tools=[FACTS_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_facts'},
            messages=[{'role': 'user', 'content': '\n'.join(ask)}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel plan facts: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    return _tool_input(msg, 'record_facts')


def call_reasons(summary, client=None):
    """record_reasons for a finished plan: {day: why}."""
    client = _client(client)
    try:
        msg = client.messages.create(
            model=PLAN_MODEL, max_tokens=900, system=REASONS_SYSTEM,
            tools=[REASONS_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_reasons'},
            messages=[{'role': 'user', 'content': summary}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel plan reasons: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    got = _tool_input(msg, 'record_reasons')
    out = {}
    for d in got.get('days') or []:
        if isinstance(d, dict) and d.get('day') and d.get('why'):
            out[str(d['day'])[:10]] = str(d['why']).strip()[:200]
    return out
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; padding: 0; cursor: pointer; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: #0F6E77; text-decoration: underline; cursor: pointer; font: inherit; }
</style>
''',
         r'''.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; padding: 0; cursor: pointer; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: #0F6E77; text-decoration: underline; cursor: pointer; font: inherit; }
/* TR-11, 17 Nov 2026 - Plan my days: the free-slot grid, the choices, the proposal. */
.tv-pl-grid { display: grid; grid-template-columns: 4.2rem repeat(3, minmax(0, 1fr)); gap: 6px; align-items: stretch; }
.tv-pl-grid .tv-pl-head { font-size: .72rem; font-weight: 700; color: #5B6B72; text-align: center; letter-spacing: .04em; align-self: end; }
.tv-pl-grid .tv-pl-day { font-weight: 700; align-self: center; font-size: .9rem; }
.tv-pl-cell { position: relative; display: flex; align-items: center; justify-content: center; text-align: center; min-height: 48px; border-radius: 9px; font-size: .8rem; font-weight: 700; line-height: 1.15; padding: 4px; margin: 0; cursor: pointer; border: 1px solid #9CC9CF; background: #E3F1F3; color: #0B5A63; }
.tv-pl-cell input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-cell .tv-pl-off { display: none; }
.tv-pl-cell input:checked ~ .tv-pl-free { display: none; }
.tv-pl-cell input:checked ~ .tv-pl-off { display: inline; }
.tv-pl-cell:has(input:checked) { border: 2px solid #B85C00; background: #FFF1E3; color: #8A4500; }
.tv-pl-cell:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-pl-taken { display: flex; align-items: center; justify-content: center; text-align: center; min-height: 48px; border-radius: 9px; font-size: .74rem; font-weight: 600; line-height: 1.15; padding: 4px; border: 1px solid #C9D3D6; background: #E9EDEF; color: #4A5A61; }
.tv-pl-key { display: flex; flex-wrap: wrap; gap: 12px; font-size: .8rem; color: #4A5A61; }
.tv-pl-key i { display: inline-block; width: 13px; height: 13px; border-radius: 4px; vertical-align: -2px; margin-right: 5px; }
.tv-pl-seg { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); grid-auto-flow: column; gap: 6px; }
.tv-pl-opt { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; min-height: 52px; border-radius: 9px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1D2B31; margin: 0; cursor: pointer; padding: 4px; }
.tv-pl-opt input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-opt b { font-size: .95rem; }
.tv-pl-opt span { font-size: .74rem; color: #4A5A61; }
.tv-pl-opt:has(input:checked) { border: 2px solid #0F7480; background: #E3F1F3; color: #0B5A63; }
.tv-pl-opt:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-pl-star { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E1E6E8; min-height: 44px; margin: 0; cursor: pointer; font-weight: 400; }
.tv-pl-star input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pl-star svg { fill: none; stroke: #8A9BA2; }
.tv-pl-star:has(input:checked) svg { fill: #B85C00; stroke: #B85C00; }
.tv-pl-star:focus-within { outline: 2px solid #0F7480; outline-offset: -2px; }
.tv-pl-lock { display: flex; gap: 8px; align-items: center; background: #EEF5F6; border-radius: 9px; padding: 9px 10px; font-size: .88rem; }
.tv-pl-tag { display: inline-flex; gap: 3px; align-items: center; font-size: .68rem; font-weight: 700; border-radius: 999px; padding: 1px 7px; border: 1px solid #8A9BA2; color: #4A5A61; white-space: nowrap; }
.tv-pl-tag.moved { border-color: #B85C00; color: #8A4500; }
.tv-pl-tag.must { border-color: #0F7480; color: #0B5A63; }
.tv-pl-why { font-size: .86rem; background: #EEF5F6; border-radius: 8px; padding: 7px 9px; }
.tv-pl-hop { font-size: .76rem; color: #5B6B72; padding-left: 4px; }
.tv-pl-notes { background: #FFF6EC; border: 1px solid #E8C9A3; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.tv-pl-notes b.h { color: #8A4500; }
.tv-pl-steps { display: flex; flex-direction: column; }
.tv-pl-step { display: flex; gap: 12px; align-items: flex-start; padding: 9px 0; }
.tv-pl-step.now { font-weight: 700; }
.tv-pl-step.todo { color: #5B6B72; }
.tv-pl-bar { height: 8px; border-radius: 8px; background: #D5DDE0; overflow: hidden; }
.tv-pl-bar span { display: block; height: 8px; background: #0F7480; }
.tv-pl-banner { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; background: #1D2B31; color: #FFFFFF; border-radius: 12px; padding: 8px 14px; }
.tv-pl-banner button { background: none; border: 0; color: #7FD3DA; font-weight: 700; min-height: 44px; padding: 0 4px; cursor: pointer; font: inherit; font-weight: 700; }
.tv-pl-cta { background: #0F7480; color: #FFFFFF; border-radius: 14px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.tv-pl-cta a.go { background: #FFFFFF; color: #0F7480; border-radius: 10px; min-height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; text-decoration: none; }

.tv-pl-cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; align-items: start; }
.tv-pl-col { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 8px; min-height: 120px; }
.tv-pl-col.tv-pl-over { outline: 2px dashed #0F7480; outline-offset: 2px; }
.tv-pl-card { border: 1px solid #E1E6E8; border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; background: #FFFFFF; }
.tv-pl-card[draggable="true"] { cursor: grab; }
.tv-pl-card.fixed { background: #F1F3F4; }
.tv-pl-card .t { color: #0B5A63; font-weight: 700; font-size: .85rem; }
.tv-pl-cards3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; align-items: start; }
.tv-pl-num { display: inline-flex; width: 26px; height: 26px; border-radius: 50%; background: #0F7480; color: #FFFFFF; font-size: .85rem; font-weight: 700; align-items: center; justify-content: center; flex: none; }
.tv-pl-cards3 > .tv-pl-part { background: #FFFFFF; border: 1px solid #E1E6E8 !important; border-radius: 12px; padding: 18px !important; box-shadow: 0 1px 3px rgba(16,34,40,.06); }
.tv-pl-cards3 > .tv-pl-part > legend { float: left; width: 100%; display: flex; gap: 10px; align-items: center; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv10-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv11-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv10-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv11-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other and never when closed. <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% comment %} TR-4 - the itinerary: every day, bookings and places in time order. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% if itinerary %}
<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
''',
         r'''{% comment %} TR-4 - the itinerary: every day, bookings and places in time order. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
<div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px">{% include 'travel/_plan_banner.html' with phone=True %}</div>
{% if itinerary %}
<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
'''),
        (r'''{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% for p in wish %}
''',
         r'''{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. TR-11 - Plan my days, to spread them over the trip. {% endcomment %}
<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px">{% include 'travel/_plan_banner.html' with phone=True %}
{% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: 13px">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:m_plan_setup' trip.pk %}">Plan my days</a></section>{% endif %}</div>
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% for p in wish %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''{% elif tab == 'itinerary' %}
    {% comment %} TR-4 - every day of the trip: the bookings (shaded) and the places planned, in time order. {% endcomment %}
    {% if itinerary %}
    <nav class="tv-chips" aria-label="Days">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}">{{ day|date:"D j" }}</a>{% endfor %}{% if wish %}<a class="tv-chip" href="#todo">Things to do</a>{% endif %}</nav>
''',
         r'''{% elif tab == 'itinerary' %}
    {% comment %} TR-4 - every day of the trip: the bookings (shaded) and the places planned, in time order. {% endcomment %}
    <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px">{% include 'travel/_plan_banner.html' %}</div>
    {% if itinerary %}
    <nav class="tv-chips" aria-label="Days">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}">{{ day|date:"D j" }}</a>{% endfor %}{% if wish %}<a class="tv-chip" href="#todo">Things to do</a>{% endif %}</nav>
'''),
        (r'''    {% endif %}
{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. {% endcomment %}
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></div>
''',
         r'''    {% endif %}
{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. TR-11 - and Plan my days, to spread them over the trip. {% endcomment %}
    <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px">{% include 'travel/_plan_banner.html' %}
    {% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: .9rem">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:plan_setup' trip.pk %}" style="max-width: 260px">Plan my days</a></section>{% endif %}</div>
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></div>
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import compare, phone, report, views, views_inbox, views_places

app_name = 'travel'
''',
         r'''from django.urls import path

from . import (compare, phone, report, views, views_inbox, views_places,
               views_plan)

app_name = 'travel'
'''),
        (r'''    path('m/trip/<int:trip_id>/day-order/', views_places.day_order,
         name='m_day_order'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
''',
         r'''    path('m/trip/<int:trip_id>/day-order/', views_places.day_order,
         name='m_day_order'),
    # TR-11, 17 Nov 2026 - Plan my days.
    path('<int:trip_id>/plan/', views_plan.setup, name='plan_setup'),
    path('<int:trip_id>/plan/<int:plan_id>/', views_plan.view,
         name='plan_view'),
    path('<int:trip_id>/plan/<int:plan_id>/move/', views_plan.move,
         name='plan_move'),
    path('<int:trip_id>/plan/<int:plan_id>/accept/', views_plan.accept,
         name='plan_accept'),
    path('<int:trip_id>/plan/<int:plan_id>/undo/', views_plan.undo,
         name='plan_undo'),
    path('<int:trip_id>/plan/<int:plan_id>/discard/', views_plan.discard,
         name='plan_discard'),
    path('m/trip/<int:trip_id>/plan/', views_plan.setup,
         name='m_plan_setup'),
    path('m/trip/<int:trip_id>/plan/<int:plan_id>/', views_plan.view,
         name='m_plan_view'),
    path('m/trip/<int:trip_id>/plan/<int:plan_id>/move/', views_plan.move,
         name='m_plan_move'),
    path('m/trip/<int:trip_id>/plan/<int:plan_id>/accept/',
         views_plan.accept, name='m_plan_accept'),
    path('m/trip/<int:trip_id>/plan/<int:plan_id>/undo/', views_plan.undo,
         name='m_plan_undo'),
    path('m/trip/<int:trip_id>/plan/<int:plan_id>/discard/',
         views_plan.discard, name='m_plan_discard'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs)})


''',
         r'''        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **plan_state(t, request, tab)})


def plan_state(t, request, tab):
    if tab not in ('itinerary', 'wish'):
        return {}
    from .planner import page_state
    return page_state(t, request)


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
    raise SystemExit('TR-11 REFUSED: %s' % msg)


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
    if "'test_travel_eleven.py'" in read(pq):
        print('TR-11 already applied.')
        return 0
    if "'test_gate_retry.py'" not in read(pq):
        refuse('GS-4 (apply_gate_retry.py, Release 91) is not applied - this round registers after it.')
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
        print('TR-11 --check: %d file(s) would change, none written; %d '
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
    print('TR-11 applied - Plan my days. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
