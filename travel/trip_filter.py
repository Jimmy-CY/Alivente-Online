# -*- coding: utf-8 -*-
"""travel/trip_filter.py - TR-16, 18 Nov 2026 (RA01 the same day: the
menus became our own drop-downs). The trip list's filters, on
the computer and the phone alike.

Demetri, 18 Nov: "I don't like how the 1 is placed near the Upcoming and
the Past. It look like part of the name. We need to differentiate it.
Also, Can we put the "All" first on the left. What happens when we have
additional years and countries. Are our filters not going to look messy?
Is there not a cleverer way to do years and countries? We leave All,
Upcoming and Past as is." - and, to the proposal: "Yes. Let's go ahead
and build it."

So: All, Upcoming and Past stay chips (All first), each with its count
as a separate badge. Years and countries become two menus - Year (newest
first) and Country (most trips first) - whatever the number of trips.
The three combine: Past, 2026, Greece = the past trips of 2026 in Greece.

The address: ?show=all|upcoming|past&year=2026&country=Greece. The old
?show=2026 and ?show=c:Greece still work - they become the year or the
country, with All.
"""
import datetime as dt
from collections import Counter
from urllib.parse import urlencode

SHOWS = ('all', 'upcoming', 'past')
FAR = dt.date(9999, 1, 1)


def _is_past(t, today):
    return bool(t.end and t.end < today)


def read(request):
    """(show, year, country) from the address; old links understood."""
    g = request.GET
    show = (g.get('show') or 'upcoming').strip()
    year = (g.get('year') or '').strip()
    country = (g.get('country') or '').strip()
    if show.isdigit():
        show, year = 'all', year or show
    elif show.startswith('c:'):
        show, country = 'all', country or show[2:]
    if show not in SHOWS:
        show = 'all'
    if not year.isdigit():
        year = ''
    return show, year, country


def apply(request, rows, today):
    """Everything the chips and menus need, and the trips they pick,
    latest first. rows are trips with .start, .end and .where_list
    (travel.views.span)."""
    show, year, country = read(request)
    for t in rows:
        t.past = _is_past(t, today)

    def by_year(t):
        return not year or (t.start and t.start.year == int(year))

    def by_country(t):
        return not country or country.lower() in [
            c.lower() for c in (getattr(t, 'where_list', None) or [])]

    narrowed = [t for t in rows if by_year(t) and by_country(t)]
    auto_past = False
    if show == 'upcoming':
        sel = [t for t in narrowed if not t.past]
        # TR-7 - nothing ahead: the past ones, said so.
        if not sel and any(t.past for t in narrowed):
            sel, auto_past = [t for t in narrowed if t.past], True
    elif show == 'past':
        sel = [t for t in narrowed if t.past]
    else:
        sel = list(narrowed)
    sel.sort(key=lambda t: (t.start or FAR), reverse=True)

    years = Counter(t.start.year for t in rows if t.start)
    countries = Counter()
    names = {}
    for t in rows:
        for c in set(getattr(t, 'where_list', None) or []):
            countries[c.lower()] += 1
            names.setdefault(c.lower(), c)

    def link(**change):
        q = {'show': show, 'year': year, 'country': country}
        q.update(change)
        return '?' + urlencode([(k, v) for k, v in q.items() if v])
    return {
        'show': show, 'year': year, 'country': country,
        'trips': sel, 'auto_past': auto_past,
        # The counts on the chips follow the year and country picked.
        'n_all': len(narrowed),
        'n_upcoming': len([t for t in narrowed if not t.past]),
        'n_past': len([t for t in narrowed if t.past]),
        'years': [(y, years[y]) for y in sorted(years, reverse=True)],
        'countries': [(names[k], n) for k, n in
                      sorted(countries.items(),
                             key=lambda kv: (-kv[1], names[kv[0]]))],
        # RA01, 18 Nov 2026 - the menus are our own drop-downs now, each
        # choice a link that keeps the other picks.
        'year_menu': [{'label': str(y), 'n': years[y],
                       'url': link(year=str(y))}
                      for y in sorted(years, reverse=True)],
        'country_menu': [{'label': names[k], 'n': n,
                          'url': link(country=names[k])} for k, n in
                         sorted(countries.items(),
                                key=lambda kv: (-kv[1], names[kv[0]]))],
        'link_all': link(show='all'),
        'link_upcoming': link(show='upcoming'),
        'link_past': link(show='past'),
        'clear_year': link(year=''),
        'clear_country': link(country=''),
        'country_name': names.get(country.lower(), country),
    }
