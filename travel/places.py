# -*- coding: utf-8 -*-
"""travel/places.py - TR-4, 15 Nov 2026. "Add a place": Claude looks it up.

Demetri chose (15 Nov): Claude searches the web for a place typed, pasted
as a link or shared from Google Maps - its address, opening hours, price
and website - with the Anthropic key already on Railway. No new account.

One call per place: Anthropic's own web search tool (server side, at most
three searches) and a tool of ours, record_place, whose schema is the
Place model's fields - so what comes back is checked by shape. It runs in
a background thread, as reading an email does; the page shows "Looking
it up..." until it is done. A failed look-up leaves the place as typed,
with a Map button that searches Google Maps for it.

The model is read once, from TRAVEL_AI_MODEL, with a current default - the
census in test_ai_models.py checks it.
"""
import datetime as dt
import logging
import os
import re
import threading
from urllib.parse import unquote_plus

from django.db import close_old_connections
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

MODEL = os.environ.get('TRAVEL_AI_MODEL', 'claude-sonnet-4-6')
MAX_TOKENS = 2500
SEARCHES = 3
SYNC = False
STALE = dt.timedelta(minutes=5)

KINDS = ['sight', 'museum', 'food', 'nature', 'shop', 'activity', 'other']

TOOL = {
    'name': 'record_place',
    'description': 'Record what you found about the place.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'found': {'type': 'boolean', 'description':
                      'False only if nothing sensible matches.'},
            'sure': {'type': 'boolean', 'description':
                     'False when two or three different places could be '
                     'meant - then give options instead of details.'},
            'options': {'type': 'array', 'maxItems': 3, 'description':
                        'When not sure: the places that could be meant.',
                        'items': {'type': 'object', 'properties': {
                            'name': {'type': 'string'},
                            'city': {'type': 'string'},
                            'country': {'type': 'string'},
                            'address': {'type': 'string'},
                            'about': {'type': 'string', 'description':
                                      'One line: what it is.'}},
                            'required': ['name']}},
            'name': {'type': 'string', 'description':
                     'Its proper name, e.g. "Calouste Gulbenkian Museum".'},
            'kind': {'type': 'string', 'enum': KINDS},
            'address': {'type': 'string', 'description':
                        'Street address with postcode and city.'},
            'hours': {'type': 'string', 'description':
                      'Opening hours in one short line, e.g. "10:00-18:00, '
                      'closed Tuesdays". Say if they vary by season.'},
            'price': {'type': 'string', 'description':
                      'Entry or typical price in one short line, e.g. '
                      '"about EUR 14 each, under 12s free" or "mains '
                      'EUR 15-25". "Free" if free.'},
            'website': {'type': 'string', 'description':
                        'Its official website (https).'},
            'about': {'type': 'string', 'description':
                      'One sentence worth knowing before going: book ahead, '
                      'best time, how long it takes.'},
        },
        'required': ['found'],
    },
}

SYSTEM = """You help a family plan a trip. Find the place they mean with \
web search, then call record_place once with what you found.

- Be generous about the name: it may be partial, a nickname, lower case, \
in another language or misspelled ("sagrada familia" is the Basilica de la \
Sagrada Familia in Barcelona). Give its proper name.
- The trip's destination only decides between places with the same name. \
Never reject a well-known place because it is somewhere else.
- One place clearly meant: found true, sure true, and its details.
- Two or three different places could be meant (a common name, a chain, \
a name in several cities) and nothing given says which: found true, sure \
false, and up to three options - each its proper name, city, country, \
street address and one line saying what it is. Leave the details out.
- found false only when nothing sensible matches.
- A Google Maps link or an address given points at one place: that place.
- Use the place's official site or a reliable source for hours and \
prices; keep each field to one short line; never guess - leave out what \
you could not find."""


class LookupError_(Exception):
    pass


# ------------------------------------------------------------ the query
MAPS = re.compile(r'https?://(?:maps\.app\.goo\.gl|goo\.gl/maps|'
                  r'(?:www\.)?google\.[a-z.]+/maps)\S*', re.I)
URL = re.compile(r'https?://\S+', re.I)


def parse_query(text):
    """What was typed or shared, made into (name, address, link).

    Google Maps on a phone shares "Name\\nAddress\\nhttps://maps.app.goo.gl/
    ..."; a desktop Maps link carries the name in /place/<Name>/; anything
    else is a name, or a website link."""
    text = (text or '').strip()
    links = URL.findall(text)
    link = links[0].rstrip(').,') if links else ''
    lines = [ln.strip() for ln in URL.sub('', text).splitlines()
             if ln.strip()]
    name = lines[0] if lines else ''
    address = lines[1] if len(lines) > 1 else ''
    if not name and link:
        m = re.search(r'/maps/place/([^/@?]+)', link)
        if m:
            name = unquote_plus(m.group(1))
    return name[:160], address[:255], link[:500]


def is_maps(text):
    return bool(MAPS.search(text or ''))


# ------------------------------------------------------------ the call
def call(place, client=None):
    """Ask Claude, with web search. Returns record_place's input."""
    if client is None:
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise LookupError_('The Anthropic key is not set on the server.')
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=90.0,
                                     max_retries=1)
    trip = place.trip
    from .views import span
    span(trip, list(trip.bookings.all()))
    where = trip.where or trip.countries
    ask = ['Place: %s' % (place.query or place.name)]
    if place.maps_link:
        ask.append('Google Maps link (this exact place): %s'
                   % place.maps_link)
    if place.address:
        ask.append('Address given: %s' % place.address)
    if where:
        ask.append('The trip is to: %s' % where)
    ask.append('Trip name: %s' % trip.name)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=[{'type': 'web_search_20250305', 'name': 'web_search',
                    'max_uses': SEARCHES}, TOOL],
            messages=[{'role': 'user', 'content': '\n'.join(ask)}],
        )
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel place lookup: %s', e)
        txt = str(e).lower()
        if 'web_search' in txt or 'web search' in txt:
            raise LookupError_('Web search is not switched on for the '
                               'Anthropic account.')
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                getattr(block, 'name', '') == 'record_place':
            if isinstance(block.input, dict):
                return block.input
    raise LookupError_('Nothing came back.')


def _https(v):
    v = str(v or '').strip()
    return v[:500] if v.startswith('https://') else ''


def edited(place):
    """Has the name been changed since it was typed or shared?"""
    typed = parse_query(place.query)[0] if place.query else ''
    return bool(typed) and place.name.strip().lower() != typed.lower()


def options(found):
    """The places that could be meant, tidied - at most three."""
    out = []
    for o in found.get('options') or []:
        if not isinstance(o, dict) or not str(o.get('name') or '').strip():
            continue
        s = lambda k, n: str(o.get(k) or '').strip()[:n]       # noqa: E731
        out.append({'name': s('name', 160), 'city': s('city', 80),
                    'country': s('country', 60),
                    'address': s('address', 255), 'about': s('about', 200)})
    return out[:3]


def fill(place, found):
    """The answer onto the place - never over what someone typed."""
    if not found.get('found'):
        place.lookup = 'failed'
        place.lookup_note = 'Could not tell which place this is - add ' \
                            'the town to the name and try again, or add ' \
                            'the details yourself.'
        return place
    # TR-5 (Demetri, 16 Nov: "if it finds two or three options, then
    # maybe the user must be given these options to choose from").
    opts = options(found)
    if found.get('sure') is False and len(opts) > 1 and \
            not place.maps_link:
        place.options = opts
        place.lookup = 'choose'
        place.lookup_note = ''
        return place
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if found.get('sure') is False and len(opts) == 1 and not s('name', 160):
        o = opts[0]
        found = dict(found, name=o['name'], address=o['address'],
                     about=found.get('about') or o['about'])
    # The proper name over the words typed to find it ("sagrada familia"
    # becomes "Basilica de la Sagrada Familia"). A name changed by hand is
    # only looked up when Try again is pressed - which makes it the words
    # to find it by (views_places.place_again).
    if s('name', 160):
        place.name = s('name', 160)
    if found.get('kind') in KINDS:
        place.kind = found['kind']
    place.address = place.address or s('address', 255)
    place.hours = place.hours or s('hours', 255)
    place.price = place.price or s('price', 120)
    place.website = place.website or _https(found.get('website'))
    place.about = place.about or s('about', 300)
    place.options = []
    place.lookup = 'found'
    place.lookup_note = ''
    return place


def look_up(place, client=None):
    """Claim the place, look it up, save. True if found."""
    from .models import Place
    now = timezone.now()
    n = Place.objects.filter(pk=place.pk).filter(
        Q(lookup='waiting', started__isnull=True) |
        Q(lookup='waiting', started__lt=now - STALE)).update(started=now)
    if n != 1:
        return False
    place.refresh_from_db()
    try:
        found = call(place, client=client)
        fill(place, found)
    except LookupError_ as e:
        place.lookup = 'failed'
        place.lookup_note = str(e)[:255]
    place.save()
    if place.lookup == 'found':
        link_place(place)
    return place.lookup == 'found'


def start(place):
    """Look it up now - in the background, unless SYNC."""
    if SYNC:
        return look_up(place)

    def run():
        try:
            look_up(place)
        except Exception:                               # noqa: BLE001
            logger.exception('travel place lookup %s', place.pk)
        finally:
            close_old_connections()
    threading.Thread(target=run, daemon=True).start()
    return None


# ==========================================================================
# TR-5, 16 Nov 2026 - A HOTEL'S OR A RESTAURANT'S MISSING DETAILS.
#
# Demetri: "for the detailed itinerary, I think that I want more details
# for like hotels (address, phone number, check in and check out time,
# etc.) The same for restaurants." A booking email often leaves some out
# (Booking.com rarely gives the hotel's phone or its check-in hours). What
# is missing is looked up once, on the web, as a place is - and only ever
# fills a blank: what the email or a person said is never changed. The
# booking's Changes say what came from the web.
# ==========================================================================
DETAIL_KINDS = ('stay', 'restaurant')
DETAILS_SYSTEM = """You fill in the practical details of a hotel or \
restaurant a family has booked. Find that exact place with web search - \
the name, the company and the town given - then call record_details once. \
Use its official site or a reliable listing. Times as HH:MM, 24-hour. \
Never guess: leave out what you could not find."""
DETAILS_TOOL = {
    'name': 'record_details',
    'description': 'Record the practical details found for the booking.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'found': {'type': 'boolean', 'description':
                      'False if you could not tell which place it is.'},
            'address': {'type': 'string', 'description':
                        'Street address with postcode and town.'},
            'phone': {'type': 'string', 'description':
                      'The place\'s own phone number, international form.'},
            'check_in': {'type': 'string', 'description':
                         'Hotels: check-in from, HH:MM.'},
            'check_out': {'type': 'string', 'description':
                          'Hotels: check-out by, HH:MM.'},
        },
        'required': ['found'],
    },
}


def gaps(b):
    """What a stay or a restaurant booking is missing."""
    out = []
    if not (b.address or '').strip():
        out.append('address')
    if not (b.phone or '').strip():
        out.append('phone')
    if b.kind == 'stay':
        if not b.start_time:
            out.append('check_in')
        if not b.end_time:
            out.append('check_out')
    return out


def wants_details(b):
    return b.kind in DETAIL_KINDS and b.status != 'cancelled' and \
        b.web_checked is None and bool(gaps(b)) and bool(b.pk)


def call_details(b, client=None):
    if client is None:
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise LookupError_('The Anthropic key is not set on the server.')
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=90.0,
                                     max_retries=1)
    ask = ['%s: %s' % ('Hotel' if b.kind == 'stay' else 'Restaurant',
                       b.title)]
    for label, v in (('Booked with', b.provider), ('Address', b.address),
                     ('Town', b.city), ('Country', b.country),
                     ('Phone', b.phone)):
        if (v or '').strip():
            ask.append('%s: %s' % (label, v))
    ask.append('Missing: %s' % ', '.join(gaps(b)))
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=DETAILS_SYSTEM,
            tools=[{'type': 'web_search_20250305', 'name': 'web_search',
                    'max_uses': SEARCHES}, DETAILS_TOOL],
            messages=[{'role': 'user', 'content': '\n'.join(ask)}],
        )
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel booking details: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                getattr(block, 'name', '') == 'record_details':
            if isinstance(block.input, dict):
                return block.input
    raise LookupError_('Nothing came back.')


def _hhmm(v):
    try:
        return dt.time.fromisoformat(str(v or '').strip()[:5])
    except ValueError:
        return None


def add_details(b, found):
    """The web's answer into the booking's blanks. Returns what changed,
    as the Changes trail writes it."""
    out = []
    if not found.get('found'):
        return out
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if not (b.address or '').strip() and s('address', 255):
        b.address = s('address', 255)
        out.append({'label': 'Address', 'old': '', 'new': b.address})
    if not (b.phone or '').strip() and s('phone', 40):
        b.phone = s('phone', 40)
        out.append({'label': 'Phone', 'old': '', 'new': b.phone})
    if b.kind == 'stay':
        if not b.start_time and _hhmm(found.get('check_in')):
            b.start_time = _hhmm(found.get('check_in'))
            out.append({'label': 'Start time', 'old': '',
                        'new': b.start_time.strftime('%H:%M')})
        if not b.end_time and _hhmm(found.get('check_out')):
            b.end_time = _hhmm(found.get('check_out'))
            out.append({'label': 'End time', 'old': '',
                        'new': b.end_time.strftime('%H:%M')})
    return out


def enrich(b, client=None):
    """Claim the booking, look up what it is missing, fill the blanks.
    Once per booking: web_checked is set first, found or not."""
    from .models import Booking, BookingChange
    n = Booking.objects.filter(pk=b.pk, web_checked__isnull=True).update(
        web_checked=timezone.now())
    if n != 1:
        return []
    b.refresh_from_db()
    if not gaps(b):
        return []
    try:
        found = call_details(b, client=client)
    except LookupError_:
        return []
    changed = add_details(b, found)
    if changed:
        b.save(update_fields=['address', 'phone', 'start_time', 'end_time',
                              'updated_at'])
        BookingChange.objects.create(
            booking=b, by=None, source='web', changes=changed,
            note='Filled in from the web - check before you rely on it.')
    return changed


def start_details(bookings, limit=3):
    """Look up the gaps of up to `limit` stays and restaurants - in the
    background, unless SYNC. Called when a trip is opened and when a
    booking is added, so the detailed itinerary has them."""
    ids = [b.pk for b in bookings if wants_details(b)][:limit]
    if not ids:
        return

    def fresh():
        # Its own copies - the page being drawn keeps its own.
        from .models import Booking
        return list(Booking.objects.filter(pk__in=ids,
                                           web_checked__isnull=True))
    if SYNC:
        for b in fresh():
            enrich(b)
        return

    def run():
        try:
            for b in fresh():
                enrich(b)
        except Exception:                               # noqa: BLE001
            logger.exception('travel booking details')
        finally:
            close_old_connections()
    threading.Thread(target=run, daemon=True).start()


# ==========================================================================
# TR-5, 16 Nov 2026 - A BOOKING FOR A PLACE ON THE WISH LIST.
#
# Demetri: "Matching to the Wish List is necessary." A table booked at a
# restaurant that is on the trip's wish list (or a ticket for a museum
# that is) makes that place real: it takes the booking's day and time, and
# the itinerary shows it once - as the booking. Cancel the booking, or
# delete it, and the place goes back to the wish list.
# ==========================================================================
LINK_KINDS = ('restaurant', 'activity')
GENERIC = {
    'the', 'a', 'an', 'at', 'of', 'and', 'for', 'de', 'del', 'la', 'le',
    'el', 'il', 'lo', 'los', 'las', 'les', 'di', 'da', 'du', 'des', 'to',
    'restaurant', 'restaurante', 'ristorante', 'taverna', 'tavern',
    'trattoria', 'osteria', 'brasserie', 'bistro', 'cafe', 'bar',
    'table', 'reservation', 'booking', 'ticket', 'tickets', 'entry',
    'admission', 'visit', 'tour', 'skip', 'line',
}


def _fold(text):
    import unicodedata
    t = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in t if not unicodedata.combining(c)).lower()


def name_words(text):
    return {w for w in re.findall(r'[a-z0-9]+', _fold(text))
            if w not in GENERIC and len(w) > 1}


def same_place(p, b):
    """Is this booking for this place?"""
    if p.maps_link and b.link and p.maps_link == b.link:
        return True
    a, c = name_words(p.name), name_words(b.title) | name_words(
        b.provider if b.kind == 'restaurant' else '')
    if not a or not c:
        return False
    tight = name_words(b.title)
    if a == tight:
        return True
    food = b.kind == 'restaurant' and p.kind in ('food', 'other', 'sight')
    if food and (a <= c or (tight and tight <= a)) and \
            max(len(w) for w in (a & c or {''})) >= 4:
        return True
    import difflib
    r = difflib.SequenceMatcher(None, ' '.join(sorted(a)),
                                ' '.join(sorted(tight or c))).ratio()
    if r >= 0.88:
        return True
    return bool(p.address and b.address and
                name_words(p.address) == name_words(b.address))


def link_booking(b):
    """After a booking is added or changed: link it to its place on the
    wish list, move a linked place with it, or let it go if cancelled.
    Returns the place linked, if any."""
    from .models import Place
    if not b.pk:
        return None
    mine = list(Place.objects.filter(booking=b))
    if b.status == 'cancelled' or b.kind not in LINK_KINDS:
        for p in mine:
            p.booking, p.day, p.time = None, None, None
            p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
        return None
    if not mine:
        for p in Place.objects.filter(trip_id=b.trip_id, booking__isnull=True,
                                      done=False).order_by('id'):
            if same_place(p, b):
                p.booking = b
                mine = [p]
                break
    for p in mine:
        p.day, p.time = b.start_date, b.start_time
        p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
    return mine[0] if mine else None


def link_place(p):
    """After a place is added or found: a booking on the trip already for
    it (the table was booked first)."""
    from .models import Booking
    if p.booking_id or p.done:
        return None
    for b in Booking.objects.filter(trip_id=p.trip_id, kind__in=LINK_KINDS) \
            .exclude(status='cancelled').exclude(places__isnull=False):
        if same_place(p, b):
            p.booking, p.day, p.time = b, b.start_date, b.start_time
            p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
            return b
    return None


def unlink_deleted(b):
    """Before a booking is deleted: its places back to the wish list."""
    from .models import Place
    Place.objects.filter(booking=b).update(booking=None, day=None,
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
            # TR-13 - its country, so it only goes on a day you are there.
            'country': {'type': 'string', 'description': 'Its country.'},
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


# ==========================================================================
# TR-12, 17 Nov 2026 - SUGGEST THINGS TO DO.
#
# Demetri: "based on the city where you are going to be ... the system must
# do a search and identify the top Things to Do for that destination", with
# what you like asked first, then "a short blurb" for each to tick. Agreed:
# from the AI's own knowledge, no web search (quick, and the web look-up
# still checks every one that is added); no restaurants; about 10 - 12 a
# city with Show me more; and never one already in Things to do (Demetri:
# "It must also not repeat suggestions, if these are already in the Things
# to Do"). travel/ideas.py keeps them and filters again by name.
# ==========================================================================
SUGGEST_MODEL = os.environ.get('TRAVEL_SUGGEST_MODEL', MODEL)
SUGGEST_SYSTEM = """You suggest things to do in one city for a family \
trip, as a well-travelled local friend would. Call record_ideas once.

- Suggest only what fits the interests given; spread the ideas across \
them. Each idea's interest is one of the keys given.
- Real, well-established places, streets, areas or day trips you are sure \
still exist and are open to visitors. Never invent one.
- No restaurants, bars or places to eat a meal. Food markets and famous \
cafes are allowed only under the markets interest.
- Never suggest anything in the list of what to leave out, nor the same \
place under another name or language.
- blurb: two or three plain sentences - what it is and why it is worth \
going. No exclamation marks, no emoji.
- area: its neighbourhood, or how far it is from the centre.
- visit: a typical visit ("1 - 2 h", "half a day"). price: "free", \
"about EUR 15", or "" if you do not know.
- book: true only if tickets usually need booking ahead.
- note: at most one short line, only when useful for the trip's dates - \
an event on during the stay, a closing day ("Closed Mon"), or the best \
time to go. Otherwise "".
- famous: the classics; mix: some of each; local: fewer of the obvious \
sights, more that locals love."""
# RA03, 19 Nov 2026 - Demetri: "two new categories - 1. Cafes and 2.
# Restaurants ... from a list of top 10 restaurants or top 10 cafes within
# the city". Asked for on their own, with their own rules; the sights
# above still never include a place to eat.
FOOD_SYSTEM = """You suggest the best %s in one city for a family \
trip, as a well-travelled local friend would. Call record_ideas once.

- The city's top ones: real, well-established places you are sure still \
exist and are open. Never invent one. Every idea's interest is "%s" and \
its kind is "food".
- Never suggest anything in the list of what to leave out, nor the same \
place under another name.
- blurb: two plain sentences - what it is known for and what to have. No \
exclamation marks, no emoji.
- area: its neighbourhood.
- price: typical spend, e.g. "mains EUR 15 - 25" or "coffee EUR 3"; "" if \
you do not know. visit: "" . book: true only if a table usually needs \
booking ahead.
- note: at most one short line, only when useful - a closing day, or \
"cash only". Otherwise "".
- famous: the best known; mix: some of each; local: more that locals \
love, fewer that guidebooks list."""
FOOD_SAYS = {'restaurants': 'restaurants', 'cafes': 'cafes and coffee places'}
SUGGEST_TOOL = {
    'name': 'record_ideas',
    'description': 'Record the things to do suggested for the city.',
    'input_schema': {
        'type': 'object',
        'properties': {'ideas': {'type': 'array', 'items': {
            'type': 'object', 'properties': {
                'name': {'type': 'string', 'description':
                         'Its proper name, as on a map.'},
                'interest': {'type': 'string'},
                'kind': {'type': 'string', 'enum': KINDS},
                'area': {'type': 'string'},
                'blurb': {'type': 'string'},
                'visit': {'type': 'string'},
                'price': {'type': 'string'},
                'book': {'type': 'boolean'},
                'note': {'type': 'string'}},
            'required': ['name', 'interest', 'blurb']}}},
        'required': ['ideas'],
    },
}


def call_ideas(city, country, dates, interests, style, extra, leave_out,
               count=12, client=None, km=None, food=''):
    """record_ideas for one city: a list of dicts (see SUGGEST_TOOL).
    interests: [(key, label)]; leave_out: names not to suggest. RA03: km,
    keep within that of the centre (day trips excepted); food, ask for
    the city's top restaurants or cafes instead (FOOD_SYSTEM)."""
    client = _client(client)
    ask = ['City: %s%s' % (city, ', %s' % country if country else ''),
           'Dates: %s' % dates if dates else 'Dates: not known',
           'Interests (key: what): %s' % '; '.join(
               '%s: %s' % kv for kv in interests),
           'Famous or local: %s' % style,
           'How many: about %d' % count]
    if km:
        ask.append('Distance: keep to places within about %d km of the '
                   'city centre%s.' % (km, '' if food else
                                       ' (day trips excepted)'))
    if extra:
        ask.append('They also said: %s' % extra[:200])
    if leave_out:
        ask.append('Leave out (already on their list or already shown): '
                   '%s' % '; '.join(leave_out[:120]))
    try:
        msg = client.messages.create(
            model=SUGGEST_MODEL, max_tokens=4000,
            system=(FOOD_SYSTEM % (FOOD_SAYS.get(food, food), food)
                    if food else SUGGEST_SYSTEM),
            tools=[SUGGEST_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_ideas'},
            messages=[{'role': 'user', 'content': '\n'.join(ask)}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel ideas: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    got = _tool_input(msg, 'record_ideas')
    return [i for i in got.get('ideas') or [] if isinstance(i, dict)]


def start_many(ids):
    """Look up several places one after another - in the background,
    unless SYNC (adding suggestions: one look-up at a time, not ten at
    once)."""
    from .models import Place

    def run():
        for pk in ids:
            try:
                p = Place.objects.filter(pk=pk).first()
                if p is not None:
                    look_up(p)
            except Exception:                           # noqa: BLE001
                logger.exception('travel place lookup %s', pk)
    if SYNC:
        return run()

    def go():
        try:
            run()
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()
    return None
