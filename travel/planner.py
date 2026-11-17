"""TR-11, 17 Nov 2026 - Plan my days.

Demetri, 17 Nov: "I go to Things to Do and I add all my activities ... I
want to add a button which will do a whole lot of thinking using AI, to
optimise these activities/things to do across the days of my trip" -
asking first which days, mornings or afternoons to keep free, then looking
at "opening hours, peak periods, proximity to other activities to reduce
travel/walking time".

THE SPLIT. The AI knows things (travel/places.py: weekly hours, how long a
visit takes, when it is quiet, whether to book - kept on the place). This
file fits them into the days by rules it always keeps: nothing on a day it
is closed, nothing in a slot kept free or taken by a booking, never more
than the pace allows. Then it prefers - the quiet time, what is near what,
the hotel to start from. The AI writes one line about each day at the end.

Nothing here changes a place until the plan is accepted (apply), and Undo
(undo) puts back only what is still exactly where the plan left it.
"""
import datetime as dt
import json
import logging
import math
import os
import threading
import urllib.parse
import urllib.request

from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

SYNC = False
SLOTS = (('m', dt.time(9, 0), dt.time(13, 0), 'morning'),
         ('a', dt.time(13, 0), dt.time(18, 0), 'afternoon'),
         ('e', dt.time(18, 0), dt.time(22, 0), 'evening'))
SLOT_NAMES = {s[0]: s[3] for s in SLOTS}
PACE = {'relaxed': 2, 'normal': 4, 'packed': 6}
MODES = ('walk', 'transit', 'car')
TRANSPORT = ('flight', 'train', 'ferry', 'transfer')
DEFAULT_MINUTES = {'museum': 120, 'sight': 75, 'food': 75, 'nature': 120,
                   'shop': 60, 'activity': 120, 'other': 60}
NEAR_KM = 60          # a place this far from the day's hotel is not that day
FREE_ENOUGH = 90      # a slot with less free than this is shown as taken
OPEN_DAY = 10         # what starting an empty day costs, in km-ish points
DAYS7 = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')


# ------------------------------------------------------------ small things
def mins(t):
    return t.hour * 60 + t.minute


def hhmm(m):
    m = max(0, min(int(m), 24 * 60 - 1))
    return '%02d:%02d' % (m // 60, m % 60)


def parse_ranges(text):
    """'09:00-13:00,16:00-20:00' -> [(540, 780), (960, 1200)];
    'closed' -> []; '' or nonsense -> None (not known)."""
    text = (text or '').strip().lower()
    if not text:
        return None
    if text.startswith('closed'):
        return []
    out = []
    for part in text.replace(' ', '').split(','):
        try:
            a, b = part.split('-')
            ha, ma = [int(x) for x in a.split(':')]
            hb, mb = [int(x) for x in b.split(':')]
        except (ValueError, TypeError):
            continue
        s, e = ha * 60 + ma, hb * 60 + mb
        if e <= s:
            e = 24 * 60 - 1          # open past midnight
        out.append((s, e))
    return out or None


def km(a, b):
    """Great-circle distance between (lat, lng) pairs."""
    if not a or not b or None in a or None in b:
        return None
    r = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2 +
         math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(h))


def hop(a, b, mode):
    """(minutes, words) to get from a to b - by the streets, roughly."""
    d = km(a, b)
    if d is None:
        return 20, ''
    road = d * 1.3
    walk = road / 4.5 * 60
    if walk <= 25 or (mode == 'walk' and walk <= 45):
        m = max(3, int(round(walk)))
        return m, '%d min walk' % m
    if mode == 'car':
        m = int(round(road / 30 * 60 + 8))
        return m, '%d min drive' % m
    m = int(round(road / 18 * 60 + 8))
    return m, '%d min by metro or bus' % m


# ------------------------------------------------------------ geocoding
def geocode(text):
    """(lat, lng) for an address, from Geoapify - the map service the app
    already uses. GEOAPIFY_SERVER_KEY if set (a key locked to the site's
    address in the browser cannot be used from the server), else
    GEOAPIFY_KEY. None when it cannot say."""
    key = (os.environ.get('GEOAPIFY_SERVER_KEY') or
           os.environ.get('GEOAPIFY_KEY') or '').strip()
    text = (text or '').strip()
    if not key or not text:
        return None
    url = ('https://api.geoapify.com/v1/geocode/search?format=json&limit=1'
           '&text=%s&apiKey=%s' % (urllib.parse.quote(text), key))
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
        top = (data.get('results') or [None])[0]
        if top and top.get('lat') is not None:
            return float(top['lat']), float(top['lon'])
    except Exception as e:                              # noqa: BLE001
        logger.info('travel plan geocode: %s', e)
    return None


# ------------------------------------------------------------ preparing
def kind_minutes(p):
    f = p.facts or {}
    try:
        m = int(f.get('minutes') or 0)
    except (TypeError, ValueError):
        m = 0
    return max(30, min(m or DEFAULT_MINUTES.get(p.kind, 75), 300))


def prepare(p, start=None, client=None):
    """What the planner needs about one place, worked out once: facts from
    the AI, a position from the map service (else the AI's). Saves."""
    from .places import LookupError_, call_facts
    changed = []
    if not p.facts:
        try:
            f = call_facts(p, start=start, client=client)
        except LookupError_ as e:
            f = {'_error': str(e)[:120]}
        p.facts = f
        p.facts_at = timezone.now()
        changed += ['facts', 'facts_at']
    if p.lat is None:
        pos = geocode(', '.join(x for x in (p.name, p.address) if x))
        if pos is None:
            f = p.facts or {}
            try:
                pos = (float(f['lat']), float(f['lng']))
            except (KeyError, TypeError, ValueError):
                pos = None
        if pos:
            p.lat, p.lng = pos
            changed += ['lat', 'lng']
    if changed:
        p.save(update_fields=changed + ['updated_at'])
    return p


def open_on(p, day):
    """Opening ranges on that day: [] closed, None not known."""
    f = (p.facts or {}).get('open') or {}
    return parse_ranges(f.get(DAYS7[day.weekday()], ''))


# ------------------------------------------------------------ the days
def busy_of(bookings, day):
    """Minutes of the day taken by bookings: [(start, end, why)]."""
    out = []
    for b in bookings:
        if b.status == 'cancelled' or not b.start_date:
            continue
        st = mins(b.start_time) if b.start_time else None
        en = mins(b.end_time) if b.end_time else None
        end_day = b.end_date or b.start_date
        if b.kind in TRANSPORT:
            before = 150 if b.kind == 'flight' else 45
            after = 75 if b.kind == 'flight' else 30
            if b.start_date == day and st is not None:
                if end_day == day and en is not None and en >= st:
                    out.append((st - before, en + after, b))
                else:
                    out.append((st - before, 24 * 60, b))
            elif b.start_date < day <= end_day:
                stop = (en + after) if (end_day == day and en is not None) \
                    else 24 * 60
                out.append((0, stop, b))
        elif b.kind == 'restaurant' and b.start_date == day and \
                st is not None:
            # getting ready and getting there: a 21:00 dinner takes the
            # evening (the canvas Demetri approved shows "Dinner 21:00")
            out.append((st - 120, (en if en and en > st else st + 105), b))
        elif b.kind in ('activity', 'other') and \
                b.start_date == day and st is not None:
            out.append((st - 30, (en if en and en > st else st + 105), b))
        elif b.kind == 'car' and st is not None and b.start_date == day:
            out.append((st - 15, st + 30, b))
        elif b.kind == 'car' and en is not None and end_day == day:
            out.append((en - 30, en + 15, b))
    return out


def hotel_of(stays, day):
    """The stay you wake up in, or arrive at, that day."""
    for s in stays:
        if s.start_date and s.end_date and s.start_date <= day < s.end_date:
            return s
    for s in stays:
        if s.end_date == day:
            return s
    return None


def free_of(day, busy, off):
    """{slot: [(start, end), ...]} - each slot minus bookings and minus a
    slot kept free."""
    out = {}
    for key, a, b, _n in SLOTS:
        if '%s-%s' % (day.isoformat(), key) in off:
            out[key] = []
            continue
        parts = [(mins(a), mins(b))]
        for s, e, _b in busy:
            nxt = []
            for x, y in parts:
                if e <= x or s >= y:
                    nxt.append((x, y))
                    continue
                if s > x:
                    nxt.append((x, s))
                if e < y:
                    nxt.append((e, y))
            parts = nxt
        out[key] = [(x, y) for x, y in parts if y - x >= 30]
    return out


def taken_label(day, busy, key, first=False):
    """What a slot taken by a booking says on the grid. On the first day
    a flight is the one that brings you: it says when it lands."""
    a, b = [(mins(x), mins(y)) for k, x, y, _n in SLOTS if k == key][0]
    for s, e, bk in busy:
        if s < b and e > a:
            if bk.kind == 'flight':
                if first and bk.end_time and \
                        (bk.end_date or bk.start_date) == day:
                    return 'Flight lands %s' % bk.end_time.strftime('%H:%M')
                if bk.start_date == day and bk.start_time:
                    return 'Flight %s' % bk.start_time.strftime('%H:%M')
                if bk.end_time:
                    return 'Flight lands %s' % bk.end_time.strftime('%H:%M')
                return 'Flight'
            if bk.kind == 'restaurant' and bk.start_time:
                return 'Dinner %s' % bk.start_time.strftime('%H:%M') \
                    if bk.start_time.hour >= 17 else \
                    'Lunch %s' % bk.start_time.strftime('%H:%M')
            return bk.get_kind_display()
    return 'Taken'


def grid(trip, bookings, days, off=()):
    """The days x slots grid for step 2: each cell free / off / taken."""
    rows = []
    for d in days:
        busy = busy_of(bookings, d)
        free = free_of(d, busy, ())
        cells = []
        for key, _a, _b, name in SLOTS:
            have = sum(y - x for x, y in free[key])
            code = '%s-%s' % (d.isoformat(), key)
            if have < FREE_ENOUGH:
                cells.append({'key': key, 'code': code, 'state': 'taken',
                              'label': taken_label(d, busy, key,
                                                   d == days[0]),
                              'name': name})
            else:
                cells.append({'key': key, 'code': code, 'name': name,
                              'state': 'off' if code in off else 'free'})
        rows.append({'day': d, 'cells': cells})
    return rows


# ------------------------------------------------------------ where you are
# TR-13, 17 Nov 2026 - Demetri: "It put the Parthenon on Monday 9th, but the
# flight from Dublin to Athens is at night and I would land on midnight on
# Monday". A free morning is only free where you are: a place goes on a
# day only while you are in its country - before the flight that takes you
# there has landed, or after the one that takes you away has left, it
# cannot. Where you are comes from the flights, trains and ferries (when
# each leaves and lands); a trip with none of those goes by its hotels.
def country_of_place(p):
    """The place's country: its address, else its town, else what the AI
    said ('' if none of them says)."""
    from .where import CITIES, named_city, named_country
    f = p.facts or {}
    addr = getattr(p, 'address', '') or ''
    for text in (addr, f.get('city'), f.get('area')):
        c = named_country(text or '')
        if c:
            return c
    for text in (addr, f.get('city')):
        c = named_city(text or '')
        if c:
            return c
    c = str(f.get('country') or '').strip()
    if c:
        return named_country(c) or c
    return ''


def _at(day, t, default):
    return dt.datetime.combine(day, t or default)


def whereabouts(bookings):
    """[(when, country)] in time order - None while travelling."""
    from .where import (airport_country, country_of, named_city,
                        named_country)
    live = [b for b in bookings if b.status != 'cancelled' and b.start_date]
    moves = [b for b in live if b.kind in TRANSPORT]
    out = []
    if moves:
        for b in moves:
            src = getattr(b, 'from_place', '') or ''
            frm = (named_country(src) or airport_country(src) or
                   named_city(src))
            dep = _at(b.start_date, b.start_time, dt.time(0))
            if b.end_date and b.end_time:
                arr = _at(b.end_date, b.end_time, dt.time(0))
            elif b.end_time and b.start_time and b.end_time >= b.start_time:
                arr = _at(b.start_date, b.end_time, dt.time(0))
            else:
                arr = dep + dt.timedelta(hours=3)
            if arr < dep:
                arr += dt.timedelta(days=1)
            if frm:
                out.append((dep - dt.timedelta(minutes=1), frm))
            out.append((dep, None))
            out.append((arr, country_of(b) or ''))
    else:
        for b in live:
            if b.kind in ('stay', 'car'):
                out.append((_at(b.start_date, None, dt.time(0)),
                            country_of(b) or ''))
    out.sort(key=lambda x: x[0])
    return out


def where_at(points, day, minute):
    """Your country at that minute of that day: '' when it cannot be told
    (before anything is booked), None while travelling."""
    when = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(
        minutes=minute)
    here = ''
    for at, c in points:
        if at <= when:
            here = c
        else:
            break
    return here


def there(points, country, day, start, minutes):
    """Are you in the place's country for the whole visit? Unknown either
    way is not a reason to say no."""
    if not country or not points:
        return True
    want = country.lower()
    for m in (start, start + minutes):
        c = where_at(points, day, m)
        if c is None:
            return False
        if c and c.lower() != want:
            return False
    return True


# ------------------------------------------------------------ fitting
class Item(object):
    def __init__(self, p, must):
        self.p = p
        self.pk = p.pk
        self.must = must
        self.minutes = kind_minutes(p)
        self.pos = (p.lat, p.lng) if p.lat is not None else None
        f = p.facts or {}
        self.best = f.get('best') if f.get('best') in (
            'morning', 'afternoon', 'evening') else 'any'
        self.food = p.kind == 'food'
        self.meal = f.get('meal') or 'either'
        self.country = country_of_place(p)


def fits(it, day, key, free, used):
    """The earliest start (minutes) for the item in that slot, or None."""
    left = [(x, y) for x, y in free.get(key, [])]
    for s, e in used.get(key, []):
        nxt = []
        for x, y in left:
            if e <= x or s >= y:
                nxt.append((x, y))
            else:
                if s > x:
                    nxt.append((x, s))
                if e < y:
                    nxt.append((e, y))
        left = nxt
    opens = open_on(it.p, day)
    if opens == []:
        return None
    if opens is None:
        opens = [(mins(dt.time(9)), mins(dt.time(22)))] if it.food else \
            [(mins(dt.time(9, 30)), mins(dt.time(19)))]
    need = it.minutes
    if it.food:
        want = mins(dt.time(13)) if key == 'a' else \
            mins(dt.time(20)) if key == 'e' else None
        if want is None or (it.meal == 'lunch' and key != 'a') or \
                (it.meal == 'dinner' and key != 'e'):
            return None
    for x, y in left:
        for o, c in opens:
            a, b = max(x, o), min(y, c)
            if it.food:
                a = max(a, min(want, b - need))
            a = int(math.ceil(a / 15.0) * 15)
            if b - a >= need:
                return a
    return None


def plan(trip, places, bookings, days, answers, client=None,
         progress=None):
    """The proposal: {'days': [...], 'unfit': [...], 'notes': [...]}."""
    off = set(answers.get('off') or [])
    pace = PACE.get(answers.get('pace'), 4)
    mode = answers.get('mode') if answers.get('mode') in MODES else 'transit'
    musts = set(int(x) for x in answers.get('must') or [])
    keep = {int(k): v for k, v in (answers.get('keep') or {}).items()}
    stays = [b for b in bookings if b.kind == 'stay' and
             b.status != 'cancelled']

    def tell(step, note='', done=0, total=0):
        if progress:
            progress(step, note, done, total)

    # 1. what is planned: no day yet, or on a day and "Can move" - never a
    # place a booking holds.
    todo = [p for p in places if not p.booking_id and not p.done and
            (not p.day or keep.get(p.pk) == 'move')]
    fixed = [p for p in places if p.day and p not in todo]
    start = days[0] if days else None
    for i, p in enumerate(todo):
        tell(1, p.name, i, len(todo))
        prepare(p, start=start, client=client)
    tell(2, '', len(todo), len(todo))

    # 2. the days: free time, the hotel, what is already there.
    hotels = {}
    for d in days:
        h = hotel_of(stays, d)
        if h and h.pk not in hotels:
            pos = geocode(h.address or '%s %s' % (h.title, h.provider))
            hotels[h.pk] = pos
        hotels[d] = hotels.get(h.pk) if h else None
    free = {d: free_of(d, busy_of(bookings, d), off) for d in days}
    points = whereabouts(bookings)
    used = {d: {} for d in days}
    count = {d: 0 for d in days}
    on_day = {d: [] for d in days}
    for p in fixed:
        if p.day in count:
            count[p.day] += 1
            if p.time:
                m = mins(p.time)
                for key, a, b, _n in SLOTS:
                    if mins(a) <= m < mins(b):
                        used[p.day].setdefault(key, []).append(
                            (m, m + kind_minutes(p)))
            if p.lat is not None:
                on_day[p.day].append((p.lat, p.lng))

    items = [Item(p, p.pk in musts) for p in todo]

    def options(it):
        out = []
        for d in days:
            hp = hotels.get(d)
            if hp and it.pos and km(hp, it.pos) > NEAR_KM:
                continue
            for key, _a, _b, _n in SLOTS:
                t = fits(it, d, key, free[d], used[d])
                if t is not None and there(points, it.country, d, t,
                                           it.minutes):
                    out.append((d, key, t))
        return out

    def cost(it, d, key):
        # Lower is better. Near what is already on the day beats a day of
        # its own (OPEN_DAY); a far one does not. The quiet time matters,
        # and a fuller day costs a little, so days fill evenly otherwise.
        c = 0.0
        if it.best != 'any' and SLOT_NAMES[key] != it.best:
            c += 6
        here = on_day[d]
        if it.pos and here:
            c += min(km(it.pos, x) for x in here) * 5
        elif here:
            c += OPEN_DAY / 2.0
        else:
            c += OPEN_DAY
            if it.pos and hotels.get(d):
                c += km(it.pos, hotels[d]) * 0.5
        c += count[d] * 1.5
        return c

    tell(3)
    placed = {}
    unfit = []
    order = sorted(items, key=lambda it: (not it.must, len(options(it))))
    for it in order:
        best = None
        for d, key, t in options(it):
            if count[d] >= pace:
                continue
            c = cost(it, d, key)
            if best is None or c < best[0]:
                best = (c, d, key, t)
        if best is None:
            unfit.append(it)
            continue
        _c, d, key, t = best
        placed[it.pk] = (d, key, t)
        used[d].setdefault(key, []).append((t, t + it.minutes + 20))
        count[d] += 1
        if it.pos:
            on_day[d].append(it.pos)

    # 3. a second look: would anything sit better beside its neighbours?
    for _round in range(2):
        for it in items:
            if it.pk not in placed:
                continue
            d0, k0, t0 = placed[it.pk]
            used[d0][k0].remove((t0, t0 + it.minutes + 20))
            count[d0] -= 1
            if it.pos:
                on_day[d0].remove(it.pos)
            here = (cost(it, d0, k0), d0, k0, t0)
            for d, key, t in options(it):
                if count[d] >= pace:
                    continue
                c = cost(it, d, key)
                if c + 3 < here[0]:
                    here = (c, d, key, t)
            _c, d, key, t = here
            placed[it.pk] = (d, key, t)
            used[d].setdefault(key, []).append((t, t + it.minutes + 20))
            count[d] += 1
            if it.pos:
                on_day[d].append(it.pos)

    tell(4)
    out = sequence(trip, items, placed, days, hotels, mode, fixed,
                   bookings, fit=bool(answers.get('fit')))
    out['fit'] = bool(answers.get('fit'))
    out['unfit'] = [{'place': it.pk, 'name': it.p.name,
                     'why': why_unfit(it, days, free, hotels, pace,
                                      points)}
                    for it in unfit]
    out['notes'] = notes_of(out, items)
    out['mode'] = mode
    return out


def why_unfit(it, days, free, hotels, pace, points=()):
    shut = [d for d in days if open_on(it.p, d) == []]
    if shut and len(shut) == len(days):
        return 'closed on every day of the trip'
    if it.country and points and not any(
            there(points, it.country, d, m, 60) for d in days
            for m in range(9 * 60, 21 * 60, 60)):
        return 'you are not in %s on any day with time free' % it.country
    if it.pos and days and all(hotels.get(d) and km(hotels[d], it.pos) >
                               NEAR_KM for d in days):
        return 'too far from where you are staying'
    if shut:
        return 'closed on %s, and the other days were full or kept free' \
            % ', '.join(d.strftime('%a') for d in shut)
    return 'no free slot long enough at your pace (%d a day)' % pace


def sequence(trip, items, placed, days, hotels, mode, fixed, bookings,
             fit=False):
    """Each day in visiting order, with times and the way between."""
    by_pk = {it.pk: it for it in items}
    out = []
    for d in days:
        mine = [(placed[pk][2], placed[pk][1], by_pk[pk])
                for pk in placed if placed[pk][0] == d]
        rows = []
        prev = hotels.get(d)
        end_prev = None
        for key, _a, _b, _n in SLOTS:
            group = [x for x in mine if x[1] == key]
            # nearest next, from where the day has got to
            left = sorted(group, key=lambda x: x[0])
            while left:
                if prev and all(x[2].pos for x in left):
                    left.sort(key=lambda x: (km(prev, x[2].pos), x[0]))
                t, _k, it = left.pop(0)
                way, words = hop(prev, it.pos, mode) if (prev and it.pos) \
                    else (0, '')
                if end_prev is not None:
                    t = max(t, end_prev + way)
                    t = int(math.ceil(t / 15.0) * 15)
                f = it.p.facts or {}
                rows.append({
                    'place': it.pk, 'name': it.p.name, 'time': hhmm(t),
                    'minutes': it.minutes,
                    'hop': words if rows else '',
                    'moved_from': it.p.day.isoformat()
                    if it.p.day and it.p.day != d else '',
                    'book': bool(f.get('book')),
                    'book_note': str(f.get('book_note') or '')[:80],
                    'quiet': str(f.get('quiet') or '')[:60],
                    'must': it.must,
                    'new': fit,
                    'unknown': not f.get('open'),
                })
                end_prev = t + it.minutes
                if it.pos:
                    prev = it.pos
        fixed_rows = fixed_of(d, fixed, bookings, days[0] if days else None)
        out.append({'day': d.isoformat(), 'items': rows, 'fixed': fixed_rows,
                    'why': '', 'minutes': sum(r['minutes'] for r in rows)})
    return {'days': out}


def fixed_of(d, fixed, bookings, first=None):
    """What is already on the day and stays: bookings and kept places.
    On the trip's first day a flight is shown landing."""
    rows = []
    for b in bookings:
        if b.status == 'cancelled' or b.kind == 'stay':
            continue
        if b.kind in TRANSPORT and d == first and b.start_date == d and \
                b.end_time and (b.end_date or d) == d:
            rows.append({'time': b.end_time.strftime('%H:%M'),
                         'name': '%s lands' % b.title, 'booked': True})
        elif b.start_date == d and b.start_time:
            rows.append({'time': b.start_time.strftime('%H:%M'),
                         'name': b.title, 'booked': True})
        elif b.kind in TRANSPORT and b.end_date == d and b.end_time and \
                b.start_date != d:
            rows.append({'time': b.end_time.strftime('%H:%M'),
                         'name': '%s lands' % b.title, 'booked': True})
    for p in fixed:
        if p.day == d:
            rows.append({'time': p.time.strftime('%H:%M') if p.time else '',
                         'name': p.name, 'booked': bool(p.booking_id)})
    rows.sort(key=lambda r: r['time'] or '99')
    return rows


def notes_of(out, items):
    by_pk = {it.pk: it for it in items}
    notes = []
    book = [r['name'] for day in out['days'] for r in day['items']
            if r['book']]
    if book:
        notes.append('%s usually need%s tickets booked ahead - book the '
                     'times in this plan.' % (_and(book),
                                              's' if len(book) == 1 else ''))
    for day in out['days']:
        if day['minutes'] >= 300:
            notes.append('%s is the fullest day - about %d hours of visits.'
                         % (dt.date.fromisoformat(day['day']).strftime('%A'),
                            round(day['minutes'] / 60.0)))
    unknown = [r['name'] for day in out['days'] for r in day['items']
               if r['unknown']]
    if unknown:
        notes.append('Opening hours not known for %s - worth checking.'
                     % _and(unknown))
    del by_pk
    return notes


def _and(names):
    names = list(names)
    return names[0] if len(names) == 1 else \
        ', '.join(names[:-1]) + ' and ' + names[-1]


def reasons(out, client=None):
    """One line per day from the AI; a plain line of our own if not."""
    from .places import LookupError_, call_reasons
    lines = []
    for day in out['days']:
        if not day['items']:
            continue
        lines.append('%s (%s): %s' % (
            day['day'], dt.date.fromisoformat(day['day']).strftime('%A'),
            '; '.join('%s %s%s' % (r['time'], r['name'],
                                   (' (quiet: %s)' % r['quiet'])
                                   if r['quiet'] else '')
                      for r in day['items'])))
    got = {}
    if lines:
        try:
            got = call_reasons('\n'.join(lines), client=client)
        except LookupError_:
            got = {}
    for day in out['days']:
        if day['items']:
            day['why'] = got.get(day['day']) or plain_why(day)
    return out


def plain_why(day):
    n = len(day['items'])
    hops = [r['hop'] for r in day['items'] if r['hop']]
    walk = all('walk' in h for h in hops)
    return '%d thing%s%s.' % (n, '' if n == 1 else 's',
                              ', all on foot' if hops and walk else '')


# ------------------------------------------------------------ running it
def run(tp, client=None):
    """Work the plan out and save it on the TripPlan."""
    from .views import span
    trip = tp.trip
    bookings = list(trip.bookings.all())
    places = list(trip.places.all())
    start, end = span(trip, bookings)
    days = []
    if start and end:
        d = start
        while d <= end and len(days) < 60:
            days.append(d)
            d += dt.timedelta(days=1)

    def progress(step, note='', done=0, total=0):
        tp.progress = {'step': step, 'note': note[:80], 'done': done,
                       'total': total}
        tp.save(update_fields=['progress', 'updated_at'])

    try:
        out = plan(trip, places, bookings, days, tp.answers, client=client,
                   progress=progress)
        progress(5)
        out = reasons(out, client=client)
        tp.result = out
        tp.status = 'ready'
        tp.progress = {'step': 6}
    except Exception as e:                              # noqa: BLE001
        logger.exception('travel plan %s', tp.pk)
        tp.status = 'failed'
        tp.error = ('Something went wrong while planning (%s).'
                    % type(e).__name__)[:255]
    tp.save()
    return tp


def start(tp):
    """Plan in the background, unless SYNC."""
    if SYNC:
        return run(tp)

    def go():
        try:
            run(tp)
        except Exception:                               # noqa: BLE001
            logger.exception('travel plan %s', tp.pk)
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()
    return None


# ------------------------------------------------------------ the review
def move(tp, place_pk, day_iso):
    """Before accepting: put one planned place on another day; that day is
    put in order again around it."""
    res = tp.result or {}
    days = res.get('days') or []
    row = None
    for d in days:
        for r in d['items']:
            if r['place'] == place_pk:
                row = r
                d['items'].remove(r)
    target = [d for d in days if d['day'] == day_iso]
    if row is None or not target:
        return False
    row['moved_by_you'] = True
    row['hop'] = ''
    target[0]['items'].append(row)
    target[0]['items'].sort(key=lambda r: r['time'])
    for d in days:
        for i, r in enumerate(d['items']):
            if i == 0:
                r['hop'] = ''
        d['minutes'] = sum(r['minutes'] for r in d['items'])
    tp.result = res
    tp.save(update_fields=['result', 'updated_at'])
    return True


# ------------------------------------------------------------ accept, undo
def apply(tp, user=None):
    """Put the plan on the trip: each planned place on its day at its time.
    What was there before is kept for Undo plan; the day orders of the
    planned days are cleared so the times decide the order."""
    from .models import DayOrder, Place
    trip = tp.trip
    rows = [(d['day'], r) for d in (tp.result or {}).get('days', [])
            for r in d['items']]
    pks = [r['place'] for _d, r in rows]
    places = {p.pk: p for p in Place.objects.filter(trip=trip, pk__in=pks)}
    before, after = {}, {}
    for day, r in rows:
        p = places.get(r['place'])
        if p is None:
            continue
        before[str(p.pk)] = [p.day.isoformat() if p.day else None,
                             p.time.strftime('%H:%M') if p.time else None]
        p.day = dt.date.fromisoformat(day)
        p.time = dt.datetime.strptime(r['time'], '%H:%M').time()
        p.save(update_fields=['day', 'time', 'updated_at'])
        after[str(p.pk)] = [day, r['time']]
    days = sorted(set(d for d, _ in rows))
    orders = {}
    for o in DayOrder.objects.filter(trip=trip,
                                     day__in=[dt.date.fromisoformat(d)
                                              for d in days]):
        orders[o.day.isoformat()] = o.keys
        o.delete()
    # Undo plan undoes the latest run only: an older applied plan stays on
    # the trip as it is (Demetri chose "Undo always undoes the latest run").
    trip.plans.filter(status='applied').exclude(pk=tp.pk).update(
        status='replaced')
    tp.before = {'places': before, 'orders': orders,
                 'at': timezone.now().isoformat()}
    tp.applied = after
    tp.status = 'applied'
    tp.save()
    return len(after)


def undo(tp):
    """Put back what the plan changed - only where nothing has moved since.
    Returns (put back, left alone)."""
    from .models import DayOrder, Place
    back, kept = 0, []
    for pk, (day, time) in (tp.applied or {}).items():
        p = Place.objects.filter(pk=int(pk), trip=tp.trip).first()
        if p is None:
            continue
        now = [p.day.isoformat() if p.day else None,
               p.time.strftime('%H:%M') if p.time else None]
        if now != [day, time]:
            kept.append(p.name)
            continue
        was = (tp.before or {}).get('places', {}).get(pk) or [None, None]
        p.day = dt.date.fromisoformat(was[0]) if was[0] else None
        p.time = dt.datetime.strptime(was[1], '%H:%M').time() \
            if was[1] else None
        p.save(update_fields=['day', 'time', 'updated_at'])
        back += 1
    for day, keys in ((tp.before or {}).get('orders') or {}).items():
        DayOrder.objects.get_or_create(
            trip=tp.trip, day=dt.date.fromisoformat(day),
            defaults={'keys': keys})
    tp.status = 'undone'
    tp.save(update_fields=['status', 'updated_at'])
    return back, kept


def undoable(trip, today=None):
    """The plan Undo plan would undo: the last one applied, while the trip
    has not ended (Demetri: "Undo plan must stay available for longer")."""
    from .views import span
    tp = trip.plans.filter(status='applied').first()
    if tp is None:
        return None
    _s, end = span(trip, list(trip.bookings.all()))
    today = today or timezone.localdate()
    if end and end < today:
        return None
    return tp


# ------------------------------------------------------------ fitting in
def last_applied(trip):
    return trip.plans.filter(status='applied').first()


def new_since(trip, tp=None):
    """Things to do added since the last accepted plan, still with no day
    (Demetri, 17 Nov: "after ... I accept the plan, I then add additional
    things to do to my list. What happens in that scenario?")."""
    tp = tp or last_applied(trip)
    if tp is None:
        return []
    at = (tp.before or {}).get('at')
    try:
        when = dt.datetime.fromisoformat(at) if at else tp.updated_at
    except ValueError:
        when = tp.updated_at
    return [p for p in trip.places.filter(day__isnull=True, done=False,
                                          booking__isnull=True)
            if p.created_at and p.created_at > when]


def fit_answers(trip, tp):
    """Fit them in: the last answers again, everything on a day kept."""
    a = dict(tp.answers or {})
    a['keep'] = {}
    a['fit'] = True
    return a


def page_state(trip, request):
    """What the itinerary and Things to do show about plans: Undo plan,
    "N new things since your plan", a plan waiting to be reviewed, and a
    line after accepting or undoing."""
    tp = undoable(trip)
    out = {'plan_undo': tp,
           'plan_new': new_since(trip, tp) if tp else [],
           'plan_open': trip.plans.filter(
               status__in=('working', 'ready')).first()}
    g = request.GET
    if (g.get('planned') or '').isdigit():
        out['plan_msg'] = 'accepted'
    if (g.get('undone') or '').isdigit():
        out['plan_msg'] = 'undone'
        out['plan_back'] = int(g.get('undone'))
        out['plan_kept'] = int(g.get('kept') or 0) \
            if (g.get('kept') or '').isdigit() else 0
    return out
