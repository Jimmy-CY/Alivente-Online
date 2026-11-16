# -*- coding: utf-8 -*-
"""apply_travel_nine.py - round TR-9, 16 Nov 2026.

RELEASE 89 - TRAVEL: THE ORDER OF A DAY ON THE ITINERARY.

    Demetri, 16 Nov: "On my itinerary, should i have the ability to drag
    and drop items (within a day). Like the order on the 9th should be
    Checkout, Dop off car, Fly on Ryan Air and then check in."

    - Smart order: a hotel check-in or a car pick-up on a day you travel
      goes after the flight, train or ferry that gets you there, and says
      "After you land, about 00:35" (travel/dayorder.py).
    - Your own order: drag a row by its grip on the computer; "Change
      order" then up / down on the phone. Kept per trip and day for
      everyone on the trip (DayOrder); the PDFs follow it; "Back to
      automatic" undoes it.

New files ship beside this patcher. Stands on TR-8 (apply_travel_eight.py).
Idempotent. Edits backed up to .bak_travel9. MIGRATION: travel 0008 - run
`python manage.py migrate`.
"""
import os
import sys

SUFFIX = '.bak_travel9'
MARK = 'TR-9, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/dayorder.py',
    'travel/migrations/0008_day_order.py',
    'test_travel_nine.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-8, 16 Nov 2026 - Release 88: boarding passes - Next, Coming up,
    # Used; your own pass first; Google Wallet explained after the flight.
    'test_travel_eight.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-8, 16 Nov 2026 - Release 88: boarding passes - Next, Coming up,
    # Used; your own pass first; Google Wallet explained after the flight.
    'test_travel_eight.py',
    # TR-9, 16 Nov 2026 - Release 89: the order of a day on the itinerary.
    'test_travel_nine.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # R87): boarding passes - Next, Coming up, Used.
    '.bak_travel8',
]

''',
         r'''    # R87): boarding passes - Next, Coming up, Used.
    '.bak_travel8',
    # TR-9, 16 Nov 2026 - Release 89: the order of a day on the itinerary
    # (smart order; dragged, or up / down on the phone).
    '.bak_travel9',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>

''',
         r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> on the left; on the phone, press <strong>Change order</strong> beside the day and use the &uarr; / &darr; buttons, then <strong>Done</strong>. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
  </article>

'''),
    ]),
    (os.path.join('test_travel_eight.py'), [
        (r'''   'straight to the airline\'s link')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv8-1'" in ph and 'travel.js\' %}?v=tv8-1' in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new script (worker and page agree on tv8-1)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
''',
         r'''   'straight to the airline\'s link')
ph = read(J(TA, 'phone.py'))
_v = re.search(r"SW_VERSION = '(tv\d+-\d+)'", ph)
ok(_v and int(_v.group(1)[2:].split('-')[0]) >= 8 and
   'travel.js\' %%}?v=%s' % _v.group(1) in read(J(TT, 'm', 'base.html')),
   'the phone fetches the new script (worker and page agree, tv8-1 or '
   'later)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-passrow[open] > summary { border-bottom: 1px solid var(--tv-line); }
.tv-passrow .tv-pass { border-radius: 0 0 14px 14px; box-shadow: none; }
''',
         r'''.tv-passrow[open] > summary { border-bottom: 1px solid var(--tv-line); }
.tv-passrow .tv-pass { border-radius: 0 0 14px 14px; box-shadow: none; }
/* TR-9, 16 Nov 2026 - a day of the itinerary put in order on the phone: up / down. */
.tv-order-row { display: flex; align-items: center; gap: 6px; padding: 8px 0; border-bottom: 1px solid var(--tv-line); }
.tv-order-row:last-child { border-bottom: 0; }
.tv-order-row form { margin: 0; }
.tv-order-row .tv-btn { min-width: 44px; padding: 8px 0; }
.tv-order-row .tv-btn[disabled] { opacity: .35; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: var(--tv-teal); text-decoration: underline; font: inherit; cursor: pointer; }
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''        q = ', '.join(x for x in (self.name, self.address) if x)
        return 'https://www.google.com/maps/search/?api=1&query=' + quote(q)
''',
         r'''        q = ', '.join(x for x in (self.name, self.address) if x)
        return 'https://www.google.com/maps/search/?api=1&query=' + quote(q)


class DayOrder(models.Model):
    """TR-9, 16 Nov 2026 - the order you chose for one day of a trip's
    itinerary (Demetri: "should i have the ability to drag and drop items
    (within a day)"). keys lists the day's rows - 'b<booking>-<start|end|
    during>' and 'p<place>' - first to last; a row added later keeps the
    place the automatic order gives it. Shared with everyone on the trip;
    deleted by "Back to automatic"."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='day_orders')
    day = models.DateField()
    keys = models.TextField(blank=True, default='')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('trip', 'day')]

    def __str__(self):
        return '%s %s' % (self.trip_id, self.day)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, fx, inbox
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
''',
         r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, inbox
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
'''),
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv8-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv9-1'


'''),
        (r'''            if what == 'during' and b.nights else None
        out.append(b)
    return out


def day_rows(bs, places, day):
    """TR-4 - a day of the itinerary: its bookings (as on_day) and the
    places planned for it, in time order; places with no time at the end."""
    rows = [(b.when or dt.time(0, 0), 0, b) for b in on_day(bs, day)]
    for p in places:
        # TR-5 - a place with its booking shows once: as the booking.
        if p.day == day and not p.booking_id:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [r[2] for r in rows]


def itinerary(trip, bs, places):
    """Every day of the trip, first to last, each with its rows - empty
    days too, so there is somewhere to put a place. (At most 60 days.)"""
    start, end = span(trip, bs)
    days = []
    if start:
''',
         r'''            if what == 'during' and b.nights else None
        out.append(b)
    # TR-9, 16 Nov 2026 - a check-in or a car pick-up waits for the flight
    # that gets you there (Demetri: "the order on the 9th should be
    # Checkout, Drop off car, Fly on Ryan Air and then check in").
    dayorder.smart(out, day)
    out.sort(key=lambda r: (r.sort_at, r.rank, r.pk))
    return out


class DayRows(list):
    """A day's rows; .custom when they are in an order someone chose."""
    custom = False


def day_rows(bs, places, day, saved=None):
    """TR-4 - a day of the itinerary: its bookings (as on_day) and the
    places planned for it, in time order; places with no time at the end.
    TR-9 - then the order chosen for the day (saved: {day: keys}), if any."""
    rows = [(b.sort_at, 0, b) for b in on_day(bs, day)]
    for p in places:
        # TR-5 - a place with its booking shows once: as the booking.
        if p.day == day and not p.booking_id:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
    rows.sort(key=lambda r: (r[0], r[1]))
    out, custom = dayorder.ordered([r[2] for r in rows],
                                   (saved or {}).get(day))
    for r in out:
        r.order_key = dayorder.key(r)
    out = DayRows(out)
    out.custom = custom
    return out


def itinerary(trip, bs, places):
    """Every day of the trip, first to last, each with its rows - empty
    days too, so there is somewhere to put a place. (At most 60 days.)"""
    start, end = span(trip, bs)
    saved = dayorder.saved_for(trip)
    days = []
    if start:
'''),
        (r'''        d = start
        while d <= end:
            days.append((d, day_rows(bs, places, d)))
            d += dt.timedelta(days=1)
    return days
''',
         r'''        d = start
        while d <= end:
            days.append((d, day_rows(bs, places, d, saved)))
            d += dt.timedelta(days=1)
    return days
'''),
        (r'''        fx.convert_pending(bs, limit=2)
        pl = list(trip.places.all())
        if now:
            ctx['day_no'] = (day - trip.start).days + 1
            ctx['days'] = ((trip.end or trip.start) - trip.start).days + 1
            ctx['today_rows'] = day_rows(bs, pl, day)
            ctx['tomorrow_rows'] = day_rows(bs, pl,
                                            day + dt.timedelta(days=1))
            ctx['tomorrow'] = day + dt.timedelta(days=1)
        else:
            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start)
        ctx['coming'] = coming_up(bs, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
''',
         r'''        fx.convert_pending(bs, limit=2)
        pl = list(trip.places.all())
        saved = dayorder.saved_for(trip)                    # TR-9
        if now:
            ctx['day_no'] = (day - trip.start).days + 1
            ctx['days'] = ((trip.end or trip.start) - trip.start).days + 1
            ctx['today_rows'] = day_rows(bs, pl, day, saved)
            ctx['tomorrow_rows'] = day_rows(bs, pl,
                                            day + dt.timedelta(days=1), saved)
            ctx['tomorrow'] = day + dt.timedelta(days=1)
        else:
            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start, saved)
        ctx['coming'] = coming_up(bs, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
'''),
        (r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
''',
         r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        # TR-9 - the day being put in order (?order=YYYY-MM-DD): up / down.
        'order_day': (request.GET.get('order') or '')[:10],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_booking_row.html'), [
        (r'''{% comment %} One booking as a row. TR-6, 16 Nov 2026 (Demetri: "I don't think that we should have the cost (e.g. for PAREA 270.28) showing three times for three nights. This is the total for the 3 nights, and this looks deceiving"): on the itinerary a stay's or a car's cost is on the day it starts only; the days after say which night it is, or the check-out time. {% endcomment %}<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.what == 'during' %}{% if b.night %}Night {{ b.night }} of {{ b.nights }} · {% endif %}until {{ b.end_date|date:"D j M" }}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% elif b.what == 'end' %}{% if b.kind == 'stay' %}Check out{% else %}Drop off{% endif %}{% if b.end_time %} by {{ b.end_time|time:"H:i" }}{% endif %}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% else %}{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}{% endif %}</span>{% if b.kind == 'stay' or b.kind == 'restaurant' %}{% if b.address or b.phone %}{% if b.what != 'during' %}{% comment %} TR-5 (Demetri, 16 Nov): a hotel's or restaurant's address and phone, on the day. {% endcomment %}<span class="tv-detail" data-row-detail>{% if b.address %}{{ b.address }}{% endif %}{% if b.address and b.phone %} · {% endif %}{% if b.phone %}{{ b.phone }}{% endif %}{% if b.kind == 'stay' and b.what == 'start' and b.end_time %} · check out by {{ b.end_time|time:"H:i" }}{% endif %}</span>{% endif %}{% endif %}{% endif %}</span>
    <span class="tv-amt">{% if b.what == 'during' or b.what == 'end' %}{% elif b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}{% if b.nights and b.what == 'start' %}<span class="tv-orig" style="display: block" data-stay-total>for {{ b.nights }} night{{ b.nights|pluralize }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
''',
         r'''{% comment %} One booking as a row. TR-6, 16 Nov 2026 (Demetri: "I don't think that we should have the cost (e.g. for PAREA 270.28) showing three times for three nights. This is the total for the 3 nights, and this looks deceiving"): on the itinerary a stay's or a car's cost is on the day it starts only; the days after say which night it is, or the check-out time. TR-9, 16 Nov 2026 - a check-in or pick-up that waits for a flight says when you land (Demetri: the 9th should be "Checkout, Drop off car, Fly on Ryan Air and then check in"). {% endcomment %}<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.what == 'during' %}{% if b.night %}Night {{ b.night }} of {{ b.nights }} · {% endif %}until {{ b.end_date|date:"D j M" }}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% elif b.what == 'end' %}{% if b.kind == 'stay' %}Check out{% else %}Drop off{% endif %}{% if b.end_time %} by {{ b.end_time|time:"H:i" }}{% endif %}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% else %}{% if b.arrive %}<span data-arrive>After you land, about {{ b.arrive|time:"H:i" }}{% if b.arrive_next %} (after midnight){% endif %}{% if b.start_time %} &middot; {% if b.kind == 'stay' %}check-in{% else %}pick up{% endif %} from {{ b.start_time|time:"H:i" }}{% endif %}</span> · {% elif b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}{% endif %}</span>{% if b.kind == 'stay' or b.kind == 'restaurant' %}{% if b.address or b.phone %}{% if b.what != 'during' %}{% comment %} TR-5 (Demetri, 16 Nov): a hotel's or restaurant's address and phone, on the day. {% endcomment %}<span class="tv-detail" data-row-detail>{% if b.address %}{{ b.address }}{% endif %}{% if b.address and b.phone %} · {% endif %}{% if b.phone %}{{ b.phone }}{% endif %}{% if b.kind == 'stay' and b.what == 'start' and b.end_time %} · check out by {{ b.end_time|time:"H:i" }}{% endif %}</span>{% endif %}{% endif %}{% endif %}</span>
    <span class="tv-amt">{% if b.what == 'during' or b.what == 'end' %}{% elif b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}{% if b.nights and b.what == 'start' %}<span class="tv-orig" style="display: block" data-stay-total>for {{ b.nights }} night{{ b.nights|pluralize }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-wpass.is-used.show-anyway .tv-used-stamp { opacity: .25; }
.tv-wpass.is-used .tv-wpass-top { filter: grayscale(.7); }
</style>
''',
         r'''.tv-wpass.is-used.show-anyway .tv-used-stamp { opacity: .25; }
.tv-wpass.is-used .tv-wpass-top { filter: grayscale(.7); }
/* TR-9, 16 Nov 2026 - the itinerary's own order: a grip to drag by, where it will land. */
.tv-drag { position: relative; display: flex; align-items: stretch; }
.tv-drag > .tv-bk { flex: 1 1 auto; min-width: 0; }
.tv-grip { flex: none; display: flex; align-items: center; padding: 0 8px 0 0; color: #9AA9AE; cursor: grab; }
.tv-grip:hover { color: #0F6E77; }
.tv-drag.is-dragging { opacity: .45; }
.tv-drag.tv-drop-above { box-shadow: inset 0 3px 0 #0F6E77; }
.tv-drag.tv-drop-below { box-shadow: inset 0 -3px 0 #0F6E77; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: #0F6E77; text-decoration: underline; cursor: pointer; font: inherit; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', '_row.html'), [
        (r'''  <span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span>
  <span style="min-width: 0"><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag due">Cancelled</span>{% endif %}
    <span class="tv-muted" style="display: block">{% if b.when %}<span class="tv-time">{{ b.when|time:"H:i" }}</span>{% elif b.start_time and not b.label %}<span class="tv-time">{{ b.start_time|time:"H:i" }}</span>{% endif %}{% if b.route %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.route }}{% elif b.address %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.address|truncatechars:40 }}{% endif %}{% if b.reference %}{% if b.when or b.route or b.address or b.start_time and not b.label %} · {% endif %}{{ b.reference }}{% endif %}</span></span>
  <span class="tv-muted" aria-hidden="true">›</span>
</a>{% endif %}
''',
         r'''  <span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span>
  <span style="min-width: 0"><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag due">Cancelled</span>{% endif %}
    <span class="tv-muted" style="display: block">{% if b.arrive %}<span class="tv-time" data-arrive>After you land, ~{{ b.arrive|time:"H:i" }}</span>{% elif b.when %}<span class="tv-time">{{ b.when|time:"H:i" }}</span>{% elif b.start_time and not b.label %}<span class="tv-time">{{ b.start_time|time:"H:i" }}</span>{% endif %}{% if b.route %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.route }}{% elif b.address %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.address|truncatechars:40 }}{% endif %}{% if b.reference %}{% if b.when or b.route or b.address or b.start_time and not b.label %} · {% endif %}{{ b.reference }}{% endif %}</span></span>
  <span class="tv-muted" aria-hidden="true">›</span>
</a>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv8-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv9-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv8-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv9-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). <b>Change order</b> beside a day gives &uarr; / &darr; buttons to put it in your own order, kept for everyone on the trip; <b>Back to automatic</b> undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
''',
         r'''<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
{% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - on the phone dragging fights the scrolling, so "Change order" turns the day's rows into up / down buttons; the order is kept for everyone on the trip. {% endcomment %}{% with dkey=day|date:'Y-m-d' %}
<div class="tv-row" style="align-items: baseline"><p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>{% if rows|length > 1 %}{% if order_day == dkey %}<a href="?tab=itinerary#d{{ day|date:'Ymd' }}" class="tv-small" data-order-done>Done</a>{% else %}<a href="?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}" class="tv-small" data-order-change>Change order</a>{% endif %}{% endif %}</div>
{% if rows.custom %}<form method="post" action="{% url 'travel:m_day_order' trip.pk %}" class="tv-small tv-muted" style="margin: -4px 0 6px">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}">Your order &middot; <button type="submit" class="tv-linkbtn" data-order-reset>Back to automatic</button></form>{% endif %}
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% if order_day == dkey %}<div class="tv-order-row" data-key="{{ b.order_key }}"><span style="flex: 1 1 auto; min-width: 0"><b>{% if b.is_place %}{{ b.name }}{% else %}{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}{% endif %}</b></span><form method="post" action="{% url 'travel:m_day_order' trip.pk %}">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="move" value="{{ b.order_key }}"><input type="hidden" name="dir" value="up"><input type="hidden" name="next" value="{% url 'travel:m_trip' trip.pk %}?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}"><button class="tv-btn sec" aria-label="Move {% if b.is_place %}{{ b.name }}{% else %}{{ b.title }}{% endif %} up"{% if forloop.first %} disabled{% endif %} data-order-up>&uarr;</button></form><form method="post" action="{% url 'travel:m_day_order' trip.pk %}">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="move" value="{{ b.order_key }}"><input type="hidden" name="dir" value="down"><input type="hidden" name="next" value="{% url 'travel:m_trip' trip.pk %}?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}"><button class="tv-btn sec" aria-label="Move {% if b.is_place %}{{ b.name }}{% else %}{{ b.title }}{% endif %} down"{% if forloop.last %} disabled{% endif %} data-order-down>&darr;</button></form></div>{% else %}{% include 'travel/m/_row.html' %}{% endif %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>{% endwith %}
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></div>
        {% for r in rows %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
    {% endfor %}
''',
         r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><span class="small">{% if rows.custom %}<span class="tv-sub" data-custom-order>Your order &middot; </span><form method="post" action="{% url 'travel:day_order' trip.pk %}" style="display: inline">{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}#d{{ day|date:'Ymd' }}"><button type="submit" class="tv-linkbtn" title="Put this day back in time order" data-order-reset>Back to automatic</button></form> &nbsp; {% endif %}<a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></span></div>
        {% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - drag a row by its grip; the order is kept for the day, for everyone on the trip. {% endcomment %}<form method="post" action="{% url 'travel:day_order' trip.pk %}" data-order-form hidden>{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"></form>
        {% for r in rows %}<div class="tv-drag" data-key="{{ r.order_key }}">{% if rows|length > 1 %}<span class="tv-grip" title="Drag to change the order of the day" data-grip><i class="fas fa-grip-vertical" aria-hidden="true"></i></span>{% endif %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}</div>{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
    {% endfor %}
'''),
        (r'''</div>
{% include 'components/pdf_viewer.html' %}
{% render_help_modal "travel" %}
{% endblock %}
''',
         r'''</div>
{% include 'components/pdf_viewer.html' %}
{% if tab == 'itinerary' %}<script>
/* TR-9, 16 Nov 2026 - drag a row of a day by its grip (Demetri: "should i
   have the ability to drag and drop items (within a day)"). Dropping
   saves the day's order and reloads the page, so the PDFs follow it. */
(function () {
  var dragging = null;
  document.querySelectorAll('section.tv-day').forEach(function (day) {
    day.querySelectorAll('.tv-drag').forEach(function (row) {
      var grip = row.querySelector('[data-grip]');
      if (!grip) { return; }
      grip.addEventListener('mousedown', function () { row.setAttribute('draggable', 'true'); });
      row.addEventListener('dragstart', function (e) {
        dragging = row; row.classList.add('is-dragging');
        e.dataTransfer.effectAllowed = 'move';
        try { e.dataTransfer.setData('text/plain', row.getAttribute('data-key')); } catch (x) {}
      });
      row.addEventListener('dragend', function () {
        row.classList.remove('is-dragging'); row.removeAttribute('draggable');
        day.querySelectorAll('.tv-drop-above, .tv-drop-below').forEach(function (r) { r.classList.remove('tv-drop-above', 'tv-drop-below'); });
      });
      row.addEventListener('dragover', function (e) {
        if (!dragging || dragging === row || dragging.parentNode !== row.parentNode) { return; }
        e.preventDefault();
        var box = row.getBoundingClientRect(), below = e.clientY > box.top + box.height / 2;
        row.classList.toggle('tv-drop-below', below); row.classList.toggle('tv-drop-above', !below);
      });
      row.addEventListener('dragleave', function () { row.classList.remove('tv-drop-above', 'tv-drop-below'); });
      row.addEventListener('drop', function (e) {
        if (!dragging || dragging === row || dragging.parentNode !== row.parentNode) { return; }
        e.preventDefault();
        var below = row.classList.contains('tv-drop-below');
        row.classList.remove('tv-drop-above', 'tv-drop-below');
        row.parentNode.insertBefore(dragging, below ? row.nextSibling : row);
        var keys = Array.prototype.map.call(day.querySelectorAll('.tv-drag'), function (r) { return r.getAttribute('data-key'); });
        var form = day.querySelector('[data-order-form]'), data = new FormData(form);
        data.append('keys', keys.join(','));
        fetch(form.action, {method: 'POST', body: data, credentials: 'same-origin', headers: {'X-Requested-With': 'fetch'}})
          .then(function (r) { if (!r.ok) { throw new Error(r.status); } window.location.hash = day.id; window.location.reload(); })
          .catch(function () { alert('The new order could not be saved - please try again.'); window.location.reload(); });
      });
    });
  });
})();
</script>{% endif %}
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_pdf.html'), [
        (r'''<tr><td class="t">{% if r.time %}{{ r.time|time:"H:i" }}{% endif %}</td><td class="w"><span class="place">{{ r.name }}</span>{% if r.address %} <span class="muted">· {{ r.address }}</span>{% endif %}{% if r.hours %}<br><span class="muted">{{ r.hours }}{% if r.price %} · {{ r.price }}{% endif %}</span>{% endif %}</td><td class="c">{% if r.done %}<span class="muted">done</span>{% endif %}</td></tr>
{% else %}
<tr><td class="t">{% if r.when %}{{ r.when|time:"H:i" }}{% endif %}</td><td class="w">{% if r.label %}{{ r.label }}: {% endif %}<b>{{ r.title }}</b>{% if r.cancelled %} <span class="due">CANCELLED</span>{% endif %}<br><span class="muted">{% if r.route %}{{ r.route }} · {% endif %}{% if r.what == 'start' and r.end_time and r.end_date == r.start_date %}until {{ r.end_time|time:"H:i" }} · {% endif %}{% if r.reference %}ref {{ r.reference }}{% endif %}{% if r.who %} · {{ r.who }}{% endif %}</span>{% if kind == 'detailed' and r.what != 'during' %}{% if r.kind == 'stay' or r.kind == 'restaurant' %}{% comment %} TR-5 (Demetri, 16 Nov: "for the detailed itinerary ... more details for like hotels (address, phone number, check in and check out time, etc.) The same for restaurants"). {% endcomment %}{% if r.address %}<br><span class="muted">{{ r.address }}</span>{% endif %}{% if r.phone %}<br><span class="muted">Tel {{ r.phone }}</span>{% endif %}{% if r.kind == 'stay' %}<br><span class="muted">{% if r.what == 'start' %}Check in{% if r.start_time %} from {{ r.start_time|time:"H:i" }}{% endif %}{% if r.end_date %} · check out {{ r.end_date|date:"D j M" }}{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}{% else %}Check out{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}</span>{% endif %}{% if r.kind == 'restaurant' and r.details %}<br><span class="muted">{{ r.details|truncatechars:160 }}</span>{% endif %}{% endif %}{% endif %}</td><td class="c">{% if r.what != 'during' and r.what != 'end' %}{% if r.amount is not None %}<b>{{ r.eur_label|default:"rate pending" }}</b><br><span class="{% if r.paid == 'paid' %}paid{% else %}due{% endif %}">{{ r.status_label }}</span>{% elif r.included %}<span class="muted">incl. in {{ r.included.segment|default:r.included.title }}</span>{% endif %}{% endif %}</td></tr>
{% endif %}
{% empty %}<tr><td class="t"></td><td class="w"><span class="muted">Nothing planned.</span></td><td class="c"></td></tr>
''',
         r'''<tr><td class="t">{% if r.time %}{{ r.time|time:"H:i" }}{% endif %}</td><td class="w"><span class="place">{{ r.name }}</span>{% if r.address %} <span class="muted">· {{ r.address }}</span>{% endif %}{% if r.hours %}<br><span class="muted">{{ r.hours }}{% if r.price %} · {{ r.price }}{% endif %}</span>{% endif %}</td><td class="c">{% if r.done %}<span class="muted">done</span>{% endif %}</td></tr>
{% else %}
<tr><td class="t">{% if r.arrive %}~{{ r.arrive|time:"H:i" }}{% elif r.when %}{{ r.when|time:"H:i" }}{% endif %}</td><td class="w">{% if r.label %}{{ r.label }}: {% endif %}<b>{{ r.title }}</b>{% if r.cancelled %} <span class="due">CANCELLED</span>{% endif %}<br><span class="muted">{% if r.arrive %}after you land{% if r.start_time %} (from {{ r.start_time|time:"H:i" }}){% endif %} · {% endif %}{% if r.route %}{{ r.route }} · {% endif %}{% if r.what == 'start' and r.end_time and r.end_date == r.start_date %}until {{ r.end_time|time:"H:i" }} · {% endif %}{% if r.reference %}ref {{ r.reference }}{% endif %}{% if r.who %} · {{ r.who }}{% endif %}</span>{% if kind == 'detailed' and r.what != 'during' %}{% if r.kind == 'stay' or r.kind == 'restaurant' %}{% comment %} TR-5 (Demetri, 16 Nov: "for the detailed itinerary ... more details for like hotels (address, phone number, check in and check out time, etc.) The same for restaurants"). {% endcomment %}{% if r.address %}<br><span class="muted">{{ r.address }}</span>{% endif %}{% if r.phone %}<br><span class="muted">Tel {{ r.phone }}</span>{% endif %}{% if r.kind == 'stay' %}<br><span class="muted">{% if r.what == 'start' %}Check in{% if r.start_time %} from {{ r.start_time|time:"H:i" }}{% endif %}{% if r.end_date %} · check out {{ r.end_date|date:"D j M" }}{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}{% else %}Check out{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}</span>{% endif %}{% if r.kind == 'restaurant' and r.details %}<br><span class="muted">{{ r.details|truncatechars:160 }}</span>{% endif %}{% endif %}{% endif %}</td><td class="c">{% if r.what != 'during' and r.what != 'end' %}{% if r.amount is not None %}<b>{{ r.eur_label|default:"rate pending" }}</b><br><span class="{% if r.paid == 'paid' %}paid{% else %}due{% endif %}">{{ r.status_label }}</span>{% elif r.included %}<span class="muted">incl. in {{ r.included.segment|default:r.included.title }}</span>{% endif %}{% endif %}</td></tr>
{% endif %}
{% empty %}<tr><td class="t"></td><td class="w"><span class="muted">Nothing planned.</span></td><td class="c"></td></tr>
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('place/<int:place_id>/move/', views_places.place_move,
         name='place_move'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
''',
         r'''    path('place/<int:place_id>/move/', views_places.place_move,
         name='place_move'),
    path('<int:trip_id>/day-order/', views_places.day_order,
         name='day_order'),
    path('m/trip/<int:trip_id>/day-order/', views_places.day_order,
         name='m_day_order'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
'''),
    ]),
    (os.path.join('travel', 'views_places.py'), [
        (r'''        return redirect(nxt)
    return redirect('/travel/%d/itinerary/' % tid)
''',
         r'''        return redirect(nxt)
    return redirect('/travel/%d/itinerary/' % tid)


@travel_view
@require_POST
def day_order(request, trip_id):
    """TR-9, 16 Nov 2026 - the order of one day of the itinerary (Demetri:
    "should i have the ability to drag and drop items (within a day)").

    keys=b12-start,p7,...  the whole day, as dragged on the computer;
    move=<key>&dir=up|down  one row, on the phone;
    reset=1                 back to the automatic order.
    Only the day's own rows count - anything else sent is dropped."""
    from django.http import JsonResponse
    from .dayorder import key, saved_for
    from .models import DayOrder
    from .phone import day_rows
    t = _trip(request, trip_id)
    day = _date(request.POST.get('day'))
    if not day:
        return JsonResponse({'ok': False, 'error': 'day'}, status=400)
    if request.POST.get('reset'):
        DayOrder.objects.filter(trip=t, day=day).delete()
        keys = None
    else:
        rows = day_rows(list(t.bookings.prefetch_related('travellers')),
                        list(t.places.all()), day, saved_for(t))
        have = [key(r) for r in rows]
        if request.POST.get('move'):
            k, i = request.POST.get('move'), None
            if k in have:
                i = have.index(k)
            j = None if i is None else (
                i - 1 if request.POST.get('dir') == 'up' else i + 1)
            if i is not None and 0 <= j < len(have):
                have[i], have[j] = have[j], have[i]
            keys = have
        else:
            sent = [k for k in (request.POST.get('keys') or '').split(',')
                    if k in have]
            keys = sent + [k for k in have if k not in sent]
        DayOrder.objects.update_or_create(
            trip=t, day=day, defaults={'keys': ','.join(keys),
                                       'updated_by': request.user})
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({'ok': True, 'keys': keys or []})
    if request.resolver_match.url_name.startswith('m_'):
        return _next(request, '/travel/m/trip/%d/?tab=itinerary' % t.pk)
    return _next(request, '/travel/%d/itinerary/' % t.pk)
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
    raise SystemExit('TR-9 REFUSED: %s' % msg)


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
    if "'test_travel_nine.py'" in read(pq):
        print('TR-9 already applied.')
        return 0
    if "'test_travel_eight.py'" not in read(pq):
        refuse('TR-8 (apply_travel_eight.py, Release 88) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new travel files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-9 --check: %d file(s) would change, none written; %d '
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
    print('TR-9 applied - the order of a day on the itinerary. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
