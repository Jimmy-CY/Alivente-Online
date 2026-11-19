# -*- coding: utf-8 -*-
"""travel/gplaces.py - RA03, 19 Nov 2026. Google's own place data for the
suggestions (Demetri: "Yes. Check on Google").

One call per place - Places API (New), Text Search, the first match - for
what the AI's memory cannot be trusted with: the real opening days, where
it is (so how far from the centre), whether it is still open, and for
restaurants and cafes the Google rating and price level. The fields asked
for are the Enterprise tier: 1,000 free a month, then about USD 0.035
each.

The key is GOOGLE_PLACES_KEY on Railway, created by Demetri - never in a
chat, never printed. Without it nothing is asked and nothing is greyed
out; the suggestions say they were not checked. OFF is for tests: a test
never makes a real, paid call.
"""
import json
import logging
import math
import os
import sys
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

KEY_ENV = 'GOOGLE_PLACES_KEY'
OFF = False
URL = 'https://places.googleapis.com/v1/places:searchText'
FIELDS = ','.join('places.%s' % f for f in (
    'id', 'displayName', 'formattedAddress', 'location', 'businessStatus',
    'rating', 'userRatingCount', 'priceLevel', 'regularOpeningHours'))
TIMEOUT = 10
PRICE = {'PRICE_LEVEL_FREE': 'Free', 'PRICE_LEVEL_INEXPENSIVE': '€',
         'PRICE_LEVEL_MODERATE': '€€', 'PRICE_LEVEL_EXPENSIVE': '€€€',
         'PRICE_LEVEL_VERY_EXPENSIVE': '€€€€'}


class GoogleError(Exception):
    pass


def key():
    # Never from a test: OFF, and every suite the gate runs is a
    # test_*.py script - with a key in the local .env, no test may make a
    # real, paid call (Demetri, 17 Nov: "Please stub those out").
    if OFF or os.path.basename(sys.argv[0] or '').startswith('test_'):
        return ''
    return (os.environ.get(KEY_ENV) or '').strip()


def enabled():
    return bool(key())


def open_days(hours):
    """Google's days a place opens (0 = Sunday ... 6 = Saturday), or None
    when Google does not say. Open around the clock counts as every day."""
    periods = (hours or {}).get('periods')
    if not periods:
        return None
    days = set()
    for p in periods:
        o = p.get('open') or {}
        if 'day' in o:
            days.add(int(o['day']))
        if not p.get('close') and o.get('hour', 0) == 0 and \
                o.get('minute', 0) == 0:
            return set(range(7))
    return days


def shape(p):
    loc = p.get('location') or {}
    return {
        'gid': str(p.get('id') or '')[:300],
        'name': ((p.get('displayName') or {}).get('text') or '')[:160],
        'address': (p.get('formattedAddress') or '')[:255],
        'lat': loc.get('latitude'), 'lng': loc.get('longitude'),
        'status': p.get('businessStatus') or '',
        'rating': p.get('rating'), 'ratings': p.get('userRatingCount'),
        'price': PRICE.get(p.get('priceLevel') or '', ''),
        'open_days': open_days(p.get('regularOpeningHours')),
    }


def search(text, near=None, opener=None):
    """The first place Google finds for text (near = (lat, lng) to prefer
    that area), shaped; None when nothing matches."""
    k = key()
    if not k:
        raise GoogleError('No Google key.')
    body = {'textQuery': text[:300], 'maxResultCount': 1,
            'languageCode': 'en'}
    if near and near[0] is not None:
        body['locationBias'] = {'circle': {
            'center': {'latitude': near[0], 'longitude': near[1]},
            'radius': 50000.0}}
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode('utf-8'), method='POST',
        headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': k,
                 'X-Goog-FieldMask': FIELDS})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        # The key never goes into a log - only what went wrong. RA04 -
        # and the key's health hears of it (pages/key_health.py).
        _health(False, e.code)
        raise GoogleError('Google said %s.' % e.code)
    except Exception as e:                              # noqa: BLE001
        _health(False, None)
        raise GoogleError('Google could not be reached (%s).'
                          % type(e).__name__)
    _health(True)
    found = data.get('places') or []
    return shape(found[0]) if found else None


def _health(ok, status=None):
    try:
        from pages import key_health as KH
        if ok:
            KH.record('google_places', True)
        else:
            p, d = KH.classify_google(status)
            KH.record('google_places', False, p, d)
    except Exception:                                   # noqa: BLE001
        pass


def km(a, b):
    """Kilometres between two (lat, lng) - as the crow flies."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) *
         math.sin((lo2 - lo1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(h))
