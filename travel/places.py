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
                      'False if you could not tell which place is meant.'},
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
web search - near the trip's destination if one is given - then call \
record_place once with what you found. Use the place's official site or a \
reliable source for hours and prices; keep each field to one short line; \
never guess - leave out what you could not find. If the name could be \
several places, choose the one in or near the trip's destination."""


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


def fill(place, found):
    """The answer onto the place - never over what someone typed."""
    if not found.get('found'):
        place.lookup = 'failed'
        place.lookup_note = 'Could not tell which place this is - add the ' \
                            'details yourself, or try a fuller name.'
        return place
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if s('name', 160):
        place.name = s('name', 160)
    if found.get('kind') in KINDS:
        place.kind = found['kind']
    place.address = place.address or s('address', 255)
    place.hours = place.hours or s('hours', 255)
    place.price = place.price or s('price', 120)
    place.website = place.website or _https(found.get('website'))
    place.about = place.about or s('about', 300)
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
