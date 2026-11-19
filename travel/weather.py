# -*- coding: utf-8 -*-
"""travel/weather.py - RA06, 19 Nov 2026. The day's weather where you are.

Demetri, 19 Nov: "on the Today section on the mobile, is it possible to
include a small box with the Weather for that city for the day? Rain,
temperature, etc?" - and "Yes, show it on the computer too."

  Where     the city you sleep in that night (its hotel); the morning of
            check-out, the hotel you leave; else the town a flight or train
            lands in that day. Nothing typed.
  Source    Open-Meteo - free, no key, no account: its place search, then
            its daily forecast (16 days ahead). Kept an hour per city.
  Shows     conditions, high / low, chance of rain and how much, wind.
  Never     from a test (every suite is a test_*.py script), and a slow or
            failed answer only means no weather box.
"""
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

GEO = 'https://geocoding-api.open-meteo.com/v1/search?%s'
FORECAST = 'https://api.open-meteo.com/v1/forecast?%s'
DAILY = ('weather_code,temperature_2m_max,temperature_2m_min,'
         'precipitation_probability_max,precipitation_sum,'
         'wind_speed_10m_max')
TIMEOUT = 4
KEEP = 3600            # an hour per city
KEEP_FAIL = 600        # a failed look, ten minutes
AHEAD = 15             # days the forecast reaches past today

# WMO weather codes, as Open-Meteo gives them: (words, icon).
CODES = [
    ((0,), 'Sunny', 'sun'),
    ((1,), 'Mostly sunny', 'sun'),
    ((2,), 'Partly cloudy', 'part'),
    ((3,), 'Cloudy', 'cloud'),
    ((45, 48), 'Fog', 'fog'),
    ((51, 53, 55, 56, 57), 'Drizzle', 'rain'),
    ((61, 63, 66), 'Rain', 'rain'),
    ((65, 67), 'Heavy rain', 'rain'),
    ((71, 73, 75, 77), 'Snow', 'snow'),
    ((80, 81), 'Showers', 'rain'),
    ((82,), 'Heavy showers', 'rain'),
    ((85, 86), 'Snow showers', 'snow'),
    ((95, 96, 99), 'Thunderstorms', 'storm'),
]


def words(code):
    for codes, w, icon in CODES:
        if code in codes:
            return w, icon
    return 'Mixed', 'part'


def off():
    """Never from a test."""
    return os.path.basename(sys.argv[0] or '').startswith('test_')


def fetch(url):
    """The service's answer as JSON. Kept apart so tests replace it."""
    req = urllib.request.Request(url, headers={'User-Agent':
                                               'Alivente-Travel/1'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode('utf-8'))


# ----------------------------------------------------------- where you are
def place_for(bookings, day):
    """(city, country) you are in on `day`, from the bookings - or None."""
    from .ideas import city_of
    from .where import AIRPORTS, country_of
    live = [b for b in bookings if getattr(b, 'status', 'ok') != 'cancelled']
    stays = [b for b in live if b.kind == 'stay' and b.start_date]
    for b in stays:
        end = b.end_date or b.start_date
        if b.start_date <= day < end or b.start_date == day:
            c = city_of(b)
            if c:
                return c, country_of(b)
    for b in stays:
        if b.end_date == day:
            c = city_of(b)
            if c:
                return c, country_of(b)
    for b in live:
        if b.kind in ('flight', 'train', 'ferry') and \
                (b.end_date or b.start_date) == day:
            import re
            for code in re.findall(r'\b([A-Z]{3})\b', b.to_place or ''):
                if code in AIRPORTS:
                    return AIRPORTS[code]
            if (b.city or '').strip():
                return b.city.strip(), country_of(b)
    return None


# ------------------------------------------------------------ the forecast
def _cache():
    from django.core.cache import cache
    return cache


def _where(city, country):
    """(lat, lng) for a city, or None."""
    key = 'tv-wx-geo:%s|%s' % (city.lower(), (country or '').lower())
    c = _cache()
    got = c.get(key)
    if got is not None:
        return got or None
    found = None
    try:
        data = fetch(GEO % urllib.parse.urlencode(
            {'name': city, 'count': 5, 'language': 'en', 'format': 'json'}))
        rows = data.get('results') or []
        pick = [r for r in rows if country and
                (r.get('country') or '').lower() == country.lower()]
        r = (pick or rows or [None])[0]
        if r:
            found = (r['latitude'], r['longitude'])
    except Exception:                                   # noqa: BLE001
        c.set(key, '', KEEP_FAIL)
        return None
    c.set(key, found or '', 30 * 86400 if found else KEEP_FAIL)
    return found


def days_for(city, country=''):
    """{date: day} for a city's next 16 days, or {}."""
    if off() or not city:
        return {}
    key = 'tv-wx:%s|%s' % (city.lower(), (country or '').lower())
    c = _cache()
    got = c.get(key)
    if got is not None:
        return got
    out = {}
    at = _where(city, country)
    if at:
        try:
            data = fetch(FORECAST % urllib.parse.urlencode({
                'latitude': at[0], 'longitude': at[1], 'daily': DAILY,
                'timezone': 'auto', 'forecast_days': 16}))
            d = data.get('daily') or {}
            for i, day in enumerate(d.get('time') or []):
                out[dt.date.fromisoformat(day)] = shape(d, i)
        except Exception:                               # noqa: BLE001
            out = {}
    c.set(key, out, KEEP if out else KEEP_FAIL)
    return out


def _n(d, k, i):
    try:
        v = d[k][i]
    except (KeyError, IndexError, TypeError):
        return None
    return v


def shape(d, i):
    w, icon = words(_n(d, 'weather_code', i))
    hi, lo = _n(d, 'temperature_2m_max', i), _n(d, 'temperature_2m_min', i)
    p, mm = _n(d, 'precipitation_probability_max', i), \
        _n(d, 'precipitation_sum', i)
    wind = _n(d, 'wind_speed_10m_max', i)
    return {
        'words': w, 'icon': icon,
        'hi': round(hi) if hi is not None else None,
        'lo': round(lo) if lo is not None else None,
        'rain': p, 'mm': round(mm, 1) if mm else 0,
        'wind': round(wind) if wind is not None else None,
        'rain_label': ('%d%%' % p if p is not None else '') + (
            ' · %s mm' % ('{:g}'.format(round(mm, 1))) if mm else ''),
    }


def for_day(bookings, day, today=None):
    """The weather where you are on `day`, with the city - or None."""
    today = today or dt.date.today()
    if day < today or day > today + dt.timedelta(days=AHEAD):
        return None
    where = place_for(bookings, day)
    if not where:
        return None
    w = days_for(*where).get(day)
    if not w:
        return None
    return dict(w, city=where[0], day=day)


def for_days(bookings, days, today=None):
    """{day: weather} for those of `days` the forecast reaches."""
    out = {}
    for d in days:
        w = for_day(bookings, d, today)
        if w:
            out[d] = w
    return out
