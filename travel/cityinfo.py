# -*- coding: utf-8 -*-
"""travel/cityinfo.py - RA12, 22 Nov 2026. Good to know, one card a city.

Demetri, 22 Nov: "I like 12 - City Info card" - "Add which side they drive
on, typical shopping hours. Can we insert the latest conversion rate to
Euro (doesn't need to keep updating - just a once-off indication). For the
phrases, I must be able to click on them and it plays them out loud."

Claude writes the card once for a city (CityInfo, one row a city and
country, shared by every trip that goes there) and it is kept; Refresh
asks again. The euro rate is the ECB's for the day the card was made
(travel/fx.py), stored with it and never moved. The time difference and
whether an adapter is needed are worked out against home (Cyprus) when the
card is shown, for the trip's own dates. The phrases are spoken by the
phone's or computer's own voice (speechSynthesis) - nothing to pay.

Never from a test unless a test hands in its own client (every suite is a
test_*.py script).
"""
import datetime as dt
import logging
import os
import sys
import threading
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, close_old_connections

logger = logging.getLogger(__name__)
MODEL = os.environ.get('TRAVEL_CITY_MODEL', 'claude-haiku-4-5')
HOME_TZ = os.environ.get('TRAVEL_HOME_TZ', 'Asia/Nicosia')
HOME_PLUG = 'G'                 # Cyprus: the UK's three square pins
HOME_DRIVES = 'left'
MOST = 4                        # cities written at one look at a trip
SYNC = False                    # tests: in the request, not a thread
RETRY = dt.timedelta(hours=6)   # a failed card is asked again after this


class LookupError_(Exception):
    pass


def off():
    """Never from a test."""
    return os.path.basename(sys.argv[0] or '').startswith('test_')


SYSTEM = (
    "You write a short, practical 'good to know' card for a traveller from "
    "Cyprus visiting one city. Be accurate and conservative; where a thing "
    "varies, give the common case in a few words. Never give visa or entry "
    "rules. Phrases: 6 short everyday ones in the city's main language, "
    "written in that language's own script, with a plain English meaning "
    "and, for a non-Latin script, a simple Latin spelling to read aloud.")

TOOL = {
    'name': 'record_city',
    'description': 'The good-to-know card for the city.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'country': {'type': 'string'},
            'timezone': {'type': 'string',
                         'description': 'IANA, e.g. Europe/Istanbul'},
            'emergency': {'type': 'string',
                          'description': 'The main number, e.g. 112'},
            'emergency_note': {'type': 'string',
                               'description': 'e.g. Police, ambulance, fire'},
            'plugs': {'type': 'string',
                      'description': 'Plug type letters, e.g. C/F'},
            'voltage': {'type': 'string', 'description': 'e.g. 230 V'},
            'drives': {'type': 'string', 'enum': ['left', 'right']},
            'currency_code': {'type': 'string',
                              'description': 'ISO 4217, e.g. TRY'},
            'currency_name': {'type': 'string'},
            'money_note': {'type': 'string',
                           'description': 'Cards or cash, in a few words'},
            'tipping': {'type': 'string'},
            'tipping_note': {'type': 'string'},
            'shops': {'type': 'string',
                      'description': 'Typical shop hours, e.g. 10:00-22:00 '
                      'daily'},
            'shops_note': {'type': 'string',
                           'description': 'Siesta, Sunday closing, etc.'},
            'water': {'type': 'string',
                      'enum': ['drinkable', 'bottled', 'boil']},
            'water_note': {'type': 'string'},
            'language': {'type': 'string',
                         'description': 'The main language, in English'},
            'language_note': {'type': 'string',
                              'description': 'e.g. English common in '
                              'tourist areas'},
            'lang': {'type': 'string',
                     'description': 'BCP-47 code for speech, e.g. tr-TR'},
            'phrases': {'type': 'array', 'items': {
                'type': 'object', 'properties': {
                    'text': {'type': 'string'},
                    'means': {'type': 'string'},
                    'say': {'type': 'string'}},
                'required': ['text', 'means']}},
        },
        'required': ['country', 'timezone', 'emergency', 'plugs', 'drives',
                     'currency_code', 'currency_name', 'tipping', 'shops',
                     'water', 'language', 'lang', 'phrases'],
    },
}


def key_for(city, country=''):
    return ('%s|%s' % ((city or '').strip().lower(),
                       (country or '').strip().lower()))[:160]


def _client(client):
    if client is not None:
        return client
    if off():
        raise LookupError_('Not from a test.')
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise LookupError_('The Anthropic key is not set on the server.')
    import anthropic
    return anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1)


def call(city, country='', client=None):
    """record_city for one city: a dict (see TOOL)."""
    client = _client(client)
    ask = 'City: %s' % city + ('\nCountry: %s' % country if country else '')
    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=1200, system=SYSTEM, tools=[TOOL],
            tool_choice={'type': 'tool', 'name': 'record_city'},
            messages=[{'role': 'user', 'content': ask}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel city info: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                isinstance(getattr(block, 'input', None), dict):
            return block.input
    raise LookupError_('Nothing came back.')


def _s(d, k, n=120):
    return str(d.get(k) or '').strip()[:n]


def clean(d):
    """Only what the card shows, trimmed."""
    out = {k: _s(d, k) for k in (
        'country', 'timezone', 'emergency', 'emergency_note', 'plugs',
        'voltage', 'currency_name', 'money_note', 'tipping', 'tipping_note',
        'shops', 'shops_note', 'water_note', 'language', 'language_note')}
    out['drives'] = 'left' if _s(d, 'drives').lower() == 'left' else 'right'
    w = _s(d, 'water').lower()
    out['water'] = w if w in ('drinkable', 'bottled', 'boil') else 'bottled'
    out['currency_code'] = _s(d, 'currency_code', 3).upper()
    out['lang'] = _s(d, 'lang', 20)
    out['phrases'] = [{'text': _s(p, 'text', 80), 'means': _s(p, 'means', 80),
                       'say': _s(p, 'say', 80)}
                      for p in (d.get('phrases') or [])[:8]
                      if isinstance(p, dict) and _s(p, 'text')]
    return out


def make(row, client=None, today=None):
    """Write the card for the row now; True when ready."""
    from . import fx
    from .models import CityInfo
    try:
        data = clean(call(row.city, row.country, client))
    except Exception as e:                              # noqa: BLE001
        CityInfo.objects.filter(pk=row.pk).update(
            state='failed', error=str(e)[:200],
            made_at=dt.datetime.now(dt.timezone.utc))
        return False
    rate, day = None, None
    code = data['currency_code']
    if code and code != 'EUR' and code in fx.CURRENCIES:
        day = today or dt.date.today()
        try:
            rate = fx.rate_for(day, code)
        except Exception:                               # noqa: BLE001
            rate = None
        if rate is None:
            day = None
    CityInfo.objects.filter(pk=row.pk).update(
        state='ready', data=data, error='', rate=rate, rate_day=day,
        made_at=dt.datetime.now(dt.timezone.utc))
    return True


def start(row, client=None):
    """Write it - in the background, unless SYNC."""
    if SYNC or client is not None:
        return make(row, client)

    def go():
        try:
            make(row)
        except Exception:                               # noqa: BLE001
            logger.exception('travel city info %s', row.pk)
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()
    return None


def ensure(cities, client=None):
    """The CityInfo rows for the trip's cities ({name, country} dicts),
    asking for any not written yet - and again for a failed one after a
    while. Never more than MOST at one look."""
    from .models import CityInfo
    rows, asked = [], 0
    now = dt.datetime.now(dt.timezone.utc)
    for c in cities:
        name = (c.get('name') or '').strip()
        if not name:
            continue
        key = key_for(name, c.get('country'))
        row = CityInfo.objects.filter(key=key).first()
        if row is None and asked < MOST:
            try:
                row = CityInfo.objects.create(
                    key=key, city=name[:80],
                    country=(c.get('country') or '')[:80], state='working')
            except IntegrityError:
                row = CityInfo.objects.filter(key=key).first()
            else:
                asked += 1
                start(row, client)
                row.refresh_from_db()
        elif row is not None and row.state == 'failed' and asked < MOST \
                and (not row.made_at or now - row.made_at > RETRY):
            if CityInfo.objects.filter(pk=row.pk, state='failed').update(
                    state='working'):
                asked += 1
                start(row, client)
                row.refresh_from_db()
        if row is not None:
            rows.append(row)
    return rows


def refresh(row, client=None):
    """Refresh: ask Claude again for this city."""
    from .models import CityInfo
    CityInfo.objects.filter(pk=row.pk).update(state='working', error='')
    return start(row, client)


# ------------------------------------------------------------- shown
def _offset(tz, day):
    from zoneinfo import ZoneInfo
    when = dt.datetime.combine(day, dt.time(12))
    return when.replace(tzinfo=ZoneInfo(tz)).utcoffset()


def time_vs_home(tz, day):
    """'1 hour ahead of Cyprus', 'Same time as Cyprus' ... or ''."""
    try:
        diff = _offset(tz, day) - _offset(HOME_TZ, day)
    except Exception:                                   # noqa: BLE001
        return ''
    h = diff.total_seconds() / 3600
    if not h:
        return 'Same time as Cyprus'
    n = abs(h)
    txt = ('%d' % n) if n == int(n) else ('%.1f' % n)
    return '%s hour%s %s Cyprus' % (txt, '' if n == 1 else 's',
                                    'ahead of' if h > 0 else 'behind')


def _q(x, places='0.01'):
    return Decimal(x).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def shown(row, day=None):
    """The card as the template shows it."""
    d = dict(row.data or {})
    day = day or dt.date.today()
    plugs = d.get('plugs') or ''
    letters = {p.strip().upper() for p in plugs.replace(',', '/').split('/')}
    d['adapter'] = bool(plugs) and HOME_PLUG not in letters
    d['same_side'] = d.get('drives') == HOME_DRIVES
    d['time'] = time_vs_home(d.get('timezone') or '', day)
    d['euro'] = (d.get('currency_code') or '') == 'EUR'
    if row.rate:
        d['per_eur'] = _q(row.rate, '0.01' if row.rate < 1000 else '1')
        d['per_100'] = _q(Decimal(100) / row.rate)
        d['rate_day'] = row.rate_day
    return {'row': row, 'd': d}


def cards_for(trip, bookings=None, client=None):
    """The trip's cities' cards, first city first - each with the time
    difference on that city's own first day."""
    from .ideas import cities_of
    cities = cities_of(trip, bookings)
    rows = {r.key: r for r in ensure(cities, client)}
    out = []
    for c in cities:
        row = rows.get(key_for(c.get('name'), c.get('country')))
        if row is not None:
            out.append(shown(row, c.get('start')))
    return out


def card_at(city, country='', day=None, client=None):
    """One city's card (the phone's Today), or None."""
    if not city:
        return None
    rows = ensure([{'name': city, 'country': country}], client)
    return shown(rows[0], day) if rows else None
