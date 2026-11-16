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
