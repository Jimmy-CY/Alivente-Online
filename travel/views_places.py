# -*- coding: utf-8 -*-
"""travel/views_places.py - TR-4, 15 Nov 2026. Travel, stage 4: places.

A place is somewhere to go with no booking - a museum, a garden, a
restaurant. It is added by name, by link, or from Google Maps on the
phone (Share -> Travel); Claude looks it up (travel/places.py). With a day
it sits on the itinerary among the bookings; without one, on the trip's
things to do. Everyone on the trip can add, move, tick off and remove them -
the same as bookings.

The same views serve the computer and the phone: a form posted from the
phone carries next=/travel/m/... and comes back there.
"""
import datetime as dt

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import places as P
from .models import Place, trips_for
from .views import span, travel_view


def _trip(request, trip_id):
    return get_object_or_404(trips_for(request.user), pk=trip_id)


def _place(request, place_id):
    return get_object_or_404(Place.objects.filter(
        trip__in=trips_for(request.user)).select_related('trip'),
        pk=place_id)


def _next(request, default):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt.startswith('/travel/') and '//' not in nxt:
        return redirect(nxt)
    return redirect(default)


def _date(v):
    try:
        return dt.date.fromisoformat((v or '').strip()[:10])
    except ValueError:
        return None


def _time(v):
    try:
        return dt.time.fromisoformat((v or '').strip()[:5])
    except ValueError:
        return None


def trip_days(t):
    """The days a place can go on: the trip's, first to last (60 at most)."""
    start, end = span(t, list(t.bookings.all()))
    out = []
    if start:
        d, end = start, min(end or start, start + dt.timedelta(days=60))
        while d <= end:
            out.append(d)
            d += dt.timedelta(days=1)
    return out


def _fields(place, post, new=False):
    """The typed fields onto a place. A typed value always wins over a
    looked-up one."""
    s = lambda k, n: (post.get(k) or '').strip()[:n]            # noqa: E731
    if not new:
        if s('name', 160):
            place.name = s('name', 160)
        kind = post.get('kind')
        if kind in dict(Place.KINDS):
            place.kind = kind
        place.address = s('address', 255)
        place.hours = s('hours', 255)
        place.price = s('price', 120)
        w = s('website', 500)
        place.website = w if w.startswith(('https://', 'http://')) else ''
    place.notes = (post.get('notes') or '').strip()[:2000]
    if 'day' in post:
        place.day = _date(post.get('day'))
        place.time = _time(post.get('time')) if place.day else None
    return place


@travel_view
def place_new(request, trip_id):
    """Add a place: a name, a pasted link, or what Google Maps shared."""
    t = _trip(request, trip_id)
    if request.method == 'POST':
        q = (request.POST.get('q') or '').strip()[:500]
        name, address, link = P.parse_query(q)
        if not name and not link:
            messages.error(request, 'Type a name, or paste a link.')
            return redirect('travel:place_new', trip_id=t.pk)
        p = Place(trip=t, name=name or link[:160], address=address,
                  query=q, added_by=request.user)
        if link:
            if P.is_maps(link):
                p.maps_link = link
            elif link.startswith('https://'):
                p.website = link
        _fields(p, request.POST, new=True)
        # Looked up unless they asked not to (a name of their own).
        if request.POST.get('lookup', '1') == '1':
            p.lookup = 'waiting'
        p.save()
        if p.lookup == 'waiting':
            P.start(p)
        else:
            P.link_place(p)
        messages.success(request, '%s added to %s.' % (
            p.name, 'Things to do' if not p.day else
            p.day.strftime('%a %d %b').replace(' 0', ' ')))
        if request.path.startswith('/travel/m/'):
            return redirect('travel:m_place', place_id=p.pk)
        return redirect('travel:place', place_id=p.pk)
    return render(request, _tpl(request), {
        'trip': t, 'p': None, 'tab': 'trips', 'days': trip_days(t),
        'q': request.GET.get('q', ''), 'kinds': Place.KINDS,
        'day_pick': request.GET.get('day', '')})


@travel_view
def place(request, place_id):
    """One place: what is known about it, and changing it."""
    p = _place(request, place_id)
    if p.lookup == 'waiting' and (p.started is None or p.started <
                                  _stale()):
        P.start(p)
    if request.method == 'POST':
        _fields(p, request.POST)
        p.save()
        messages.success(request, 'Saved.')
        if request.path.startswith('/travel/m/'):
            return _next(request, '/travel/m/trip/%d/?tab=itinerary'
                         % p.trip_id)
        return _next(request, '/travel/%d/itinerary/' % p.trip_id)
    return render(request, _tpl(request), {
        'trip': p.trip, 'p': p, 'tab': 'trips', 'days': trip_days(p.trip),
        'kinds': Place.KINDS})


def _tpl(request):
    """The phone's page under /travel/m/, the computer's otherwise."""
    m = (request.resolver_match.url_name or '').startswith('m_')
    return 'travel/m/place.html' if m else 'travel/place_form.html'


def _stale():
    from django.utils import timezone
    return timezone.now() - P.STALE


@travel_view
@require_POST
def place_move(request, place_id):
    """To a day (and a time), or back to the wish list.

    TR-5 (Demetri, 16 Nov: "To Move, you should at least need as a minimum
    to have a date"): Things to do's Move sends need_day, and is refused
    without one - the day list starts on "Choose a day..." and is
    required. Back to Things to do is its own button (to_wish)."""
    p = _place(request, place_id)
    if request.POST.get('need_day') and not _date(request.POST.get('day')):
        messages.error(request, 'Choose a day first.')
        return _next(request, '/travel/%d/wish-list/' % p.trip_id)
    if request.POST.get('to_wish'):
        p.day, p.time = None, None
        p.save(update_fields=['day', 'time', 'updated_at'])
        messages.success(request, '%s: in Things to do.' % p.name)
        return _next(request, '/travel/%d/wish-list/' % p.trip_id)
    p.day = _date(request.POST.get('day'))
    p.time = _time(request.POST.get('time')) if p.day else None
    p.save(update_fields=['day', 'time', 'updated_at'])
    messages.success(request, '%s: %s.' % (p.name, 'in Things to do'
                                           if not p.day else
                                           p.day.strftime('%a %d %b')
                                           .replace(' 0', ' ')))
    return _next(request, '/travel/%d/itinerary/' % p.trip_id)


@travel_view
@require_POST
def place_done(request, place_id):
    p = _place(request, place_id)
    p.done = not p.done
    p.save(update_fields=['done', 'updated_at'])
    return _next(request, '/travel/%d/itinerary/' % p.trip_id)


@travel_view
@require_POST
def place_again(request, place_id):
    """Look it up again - TR-5: by what is in the Name box now, so a name
    with the town added is the one searched for."""
    p = _place(request, place_id)
    if 'address' in request.POST:
        # Pressed on the place's own form: what is in its boxes now.
        _fields(p, request.POST)
    elif (request.POST.get('name') or '').strip():
        p.name = request.POST['name'].strip()[:160]
    if P.edited(p) or not p.query:
        p.query = ', '.join(x for x in (p.name, p.address) if x)[:500] \
            if not p.maps_link else p.query
    p.options = []
    p.lookup, p.started, p.lookup_note = 'waiting', None, ''
    p.save()
    P.start(p)
    return _next(request, '/travel/place/%d/' % p.pk)


@travel_view
@require_POST
def place_pick(request, place_id):
    """TR-5 - which of the two or three places was meant (Demetri: "if
    it finds two or three options, then maybe the user must be given
    these options to choose from"). Picking one looks THAT place up;
    None of these keeps the place as it was typed."""
    p = _place(request, place_id)
    opts = p.options or []
    pick = request.POST.get('pick', '')
    if pick.isdigit() and int(pick) < len(opts):
        o = opts[int(pick)]
        p.name = o['name'][:160]
        p.address = o.get('address', '')[:255]
        p.query = ', '.join(x for x in (o['name'], o.get('address'),
                                         o.get('city'), o.get('country'))
                            if x)[:500]
        p.options = []
        p.lookup, p.started, p.lookup_note = 'waiting', None, ''
        p.save()
        P.start(p)
    else:
        p.options = []
        p.lookup = ''
        p.lookup_note = ''
        p.save(update_fields=['options', 'lookup', 'lookup_note',
                              'updated_at'])
        messages.success(request, 'Kept as you typed it - add the town to '
                         'the name and look it up again if you like.')
    return _next(request, '/travel/place/%d/' % p.pk)


@travel_view
@require_POST
def place_delete(request, place_id):
    p = _place(request, place_id)
    tid = p.trip_id
    name = p.name
    p.delete()
    messages.success(request, '%s removed.' % name)
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/travel/') and '/place/' not in nxt:
        return redirect(nxt)
    return redirect('/travel/%d/itinerary/' % tid)
