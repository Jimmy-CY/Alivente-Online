"""TR-9, 16 Nov 2026 - the order of a day on the itinerary.

Demetri, 16 Nov: "On my itinerary, should i have the ability to drag and
drop items (within a day). Like the order on the 9th should be Checkout,
Drop off car, Fly on Ryan Air and then check in."

Two parts:

1. Smart order. A hotel's check-in time (15:00) is the earliest you may
   arrive, not when you do: on a day you travel, a check-in - and a car
   pick-up - goes after the flight, train or ferry that gets you there, and
   says when you land. Which one: the transport arriving in the place's own
   town if the words match; otherwise the last one to arrive that day (not
   one leaving from the hotel's own town - that is the way out).

2. Your own order. Dragged on the computer, moved up and down on the
   phone, kept per trip and day (DayOrder) for everyone on the trip, undone
   by "Back to automatic". A row added later keeps its automatic place.
"""
import datetime as dt
import re

TRANSPORT = ('flight', 'train', 'ferry', 'transfer')
_PLAIN = {'airport', 'international', 'intl', 'station', 'central', 'port',
          'terminal', 'the', 'and', 'hotel', 'street', 'road', 'greece',
          'ireland', 'cyprus', 'spain', 'apartments', 'apartment', 'rooms',
          'car', 'hire', 'rental', 'rent', 'desk'}
LATE = dt.time(23, 59, 59)


def words(*texts):
    out = set()
    for t in texts:
        for w in re.findall(r'[^\W\d_]+', (t or '').lower()):
            if len(w) >= 4 and w not in _PLAIN:
                out.add(w)
    return out


def arrival(b, day):
    """When a transport leaving on `day` gets in: (datetime, next_day)."""
    if b.kind not in TRANSPORT or b.start_date != day or not b.end_time:
        return None
    end_day = b.end_date or b.start_date
    end = dt.datetime.combine(end_day, b.end_time)
    if (not b.end_date and b.start_time and b.end_time < b.start_time):
        end += dt.timedelta(days=1)                   # lands after midnight
    return end


def key(r):
    """A row's name in a saved order."""
    if getattr(r, 'is_place', False):
        return 'p%d' % r.pk
    return 'b%d-%s' % (r.pk, r.what)


def smart(rows, day):
    """rows: on_day's bookings for `day` (each with .what and .when).
    Sets .arrive (the landing time), .arrive_next (lands after midnight),
    .after (the transport) and .sort_at on check-ins and pick-ups that wait
    for a transport; .sort_at = .when on the rest."""
    gets_in = [(arrival(b, day), b) for b in rows if b.what == 'start']
    gets_in = [(a, b) for a, b in gets_in if a]
    for r in rows:
        r.sort_at = r.when or dt.time(0, 0)
        r.arrive = r.after = None
        r.arrive_next = False
        r.rank = 0 if r.kind in TRANSPORT else 1
        if r.what != 'start' or r.kind not in ('stay', 'car') or not gets_in:
            continue
        own = r.start_time or dt.time(0, 0)
        here = words(r.address, r.title, r.provider, r.from_place,
                     r.to_place)
        later = [(a, b) for a, b in gets_in
                 if a > dt.datetime.combine(day, own) and b is not r and
                 not (here & words(b.from_place))]
        if not later:
            continue
        match = [(a, b) for a, b in later if here & words(b.to_place)]
        a, b = max(match or later, key=lambda x: x[0])
        r.after, r.arrive = b, a.time()
        r.arrive_next = a.date() > day
        r.sort_at = LATE if r.arrive_next else a.time()
        r.rank = 2 if r.kind == 'stay' else 1
    return rows


def ordered(rows, saved):
    """The automatic order with the saved one laid over it: rows the saved
    list knows take its order, in the slots they hold; the others stay
    where the automatic order put them."""
    if not saved:
        return rows, False
    pos = {k: i for i, k in enumerate(saved)}
    known = [r for r in rows if key(r) in pos]
    if len(known) < 2:
        return rows, False
    known.sort(key=lambda r: pos[key(r)])
    it = iter(known)
    out = [next(it) if key(r) in pos else r for r in rows]
    return out, [key(r) for r in out] != [key(r) for r in rows]


def saved_for(trip):
    """{day: [key, ...]} for a trip."""
    from .models import DayOrder
    if trip is None or not getattr(trip, 'pk', None):
        return {}
    return {o.day: [k for k in o.keys.split(',') if k]
            for o in DayOrder.objects.filter(trip=trip)}
