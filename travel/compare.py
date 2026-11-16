# -*- coding: utf-8 -*-
"""travel/compare.py - TR-7, 16 Nov 2026. Comparing trips; settling up.

Demetri, 16 Nov: "I want the ability to do some super intelligent
reporting comparing trips and their costs. I want to be able to compare
flight costs, accommodation costs (per night), car rental (per day),
trains, etc. ... I must be able to multi select trips for comparison."

On Travel, tick two or more trips and press Compare: /travel/compare/?t=..
Every figure is worked out exactly from the bookings, in euros
(amount_eur), cancelled bookings left out:

    hotel per night       stays' cost / their nights
    flight per person     flights' cost (a return's price is on its first
                          flight) / (flights x the people on each)
    car per day           car hire's cost / its days (pick-up to drop-off)
    train per journey     trains' cost / trains with a cost
    restaurant per meal   restaurants' cost / restaurants with a cost
    activities            their total
    trip per day          the trip's total / its nights (at least 1)

"What stands out" is a few sentences written from those figures - no
model is asked; the words follow the numbers.

And "Once all the trip days have passed, would it make sense for the
system to set all Reservations as paid (maybe to ask first)?" - unsettled()
says what a finished trip still has To pay; trip_settle marks the ticked
ones Paid, or leaves them, or asks again in a week.
"""
import datetime as dt
from decimal import Decimal

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Booking, BookingChange, trips_for
from .views import (ICONS, _money, diff, eur, included, shape, snapshot,
                    span, totals, travel_view)

COLOURS = ['#0F7480', '#C2410C', '#6D28D9', '#1E7A46', '#9A5B00', '#1D4ED8']
KIND_COLOURS = {'stay': '#0F7480', 'flight': '#5BA8B1', 'car': '#A9CFD4',
                'train': '#1D2B31', 'ferry': '#3F6F78', 'transfer': '#8A9BA2',
                'activity': '#B7C4C9', 'restaurant': '#D5A55A',
                'other': '#DDE3E5'}
MAX = 6


# ------------------------------------------------------------ settling up
def unsettled(t, bookings, today=None):
    """What a finished trip still has To pay or Part paid - [] while the
    trip is on or ahead, after Leave as it is, or before the week asked
    for is up."""
    today = today or timezone.localdate()
    start, end = span(t, bookings)
    if not end or end >= today or t.settle_off or \
            (t.settle_after and t.settle_after > today):
        return []
    return [b for b in bookings if b.status != 'cancelled' and
            b.amount is not None and b.paid != 'paid']


@travel_view
@require_POST
def trip_settle(request, trip_id):
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    what = request.POST.get('what')
    if what == 'leave':
        t.settle_off = True
        t.save(update_fields=['settle_off', 'updated_at'])
        messages.success(request, 'Left as it is - not asked again.')
    elif what == 'later':
        t.settle_after = timezone.localdate() + dt.timedelta(days=7)
        t.save(update_fields=['settle_after', 'updated_at'])
        messages.success(request, 'Asked again in a week.')
    else:
        picked = {int(x) for x in request.POST.getlist('b') if x.isdigit()}
        n = 0
        for b in t.bookings.filter(pk__in=picked).exclude(status='cancelled'):
            before = snapshot(b)
            paid_eur = _money(request.POST.get('eur_%d' % b.pk))
            if paid_eur is not None and paid_eur != b.amount_eur:
                if b.currency == 'EUR':
                    b.amount = b.amount_eur = paid_eur
                else:
                    b.amount_eur, b.eur_typed, b.fx_rate = paid_eur, True, \
                        None
            b.paid, b.paid_amount = 'paid', None
            b.save()
            changed = diff(before, b)
            if changed:
                BookingChange.objects.create(
                    booking=b, by=request.user, source='edit',
                    note='Settled after the trip', changes=changed)
            n += 1
        messages.success(request, '%d booking%s marked paid.' % (
            n, '' if n == 1 else 's'))
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/travel/') and '//' not in nxt:
        return redirect(nxt)
    return redirect('travel:trip', trip_id=t.pk)


# -------------------------------------------------------------- comparing
def _sum(bs):
    return sum((b.amount_eur for b in bs if b.amount_eur is not None),
               Decimal('0'))


def _pax(b):
    n = len(list(b.travellers.all())) + len(
        [x for x in (b.traveller_names or '').split(',') if x.strip()])
    return max(n, 1)


def _people(bs):
    from .views import name_key
    keys = set()
    for b in bs:
        for u in b.travellers.all():
            keys.add(('u', u.pk))
        for x in (b.traveller_names or '').split(','):
            if x.strip():
                keys.add(name_key(x))
    return max(len(keys), 1)


def _div(a, b):
    if not b or a is None:
        return None
    return (Decimal(a) / Decimal(b)).quantize(Decimal('0.01'))


def figures(t):
    """One trip's like-for-like figures, in euros."""
    bs = [shape(b) for b in t.bookings.prefetch_related('travellers')
          if b.status != 'cancelled']
    included(bs)
    start, end = span(t, bs)
    nights = (end - start).days if start and end else 0
    by = {}
    for b in bs:
        by.setdefault(b.kind, []).append(b)
    priced = lambda k: [b for b in by.get(k, [])            # noqa: E731
                        if b.amount_eur is not None]
    stays = priced('stay')
    stay_nights = sum(max((b.end_date - b.start_date).days, 1)
                      for b in stays if b.start_date and b.end_date)
    flights = by.get('flight', [])
    flight_seats = sum(_pax(b) for b in flights
                       if b.amount_eur is not None or b.included)
    cars = priced('car')
    car_days = sum(max((b.end_date - b.start_date).days, 1)
                   for b in cars if b.start_date and b.end_date)
    money = totals(bs)
    total = sum((b.amount_eur for b in bs if b.amount_eur is not None),
                Decimal('0'))
    kinds = []
    for k, label in Booking.KINDS:
        v = _sum(by.get(k, []))
        if v:
            kinds.append({'kind': k, 'label': label, 'eur': v,
                          'colour': KIND_COLOURS.get(k, '#DDE3E5'),
                          'icon': ICONS.get(k, ICONS['other'])})
    for k in kinds:
        k['pct'] = int(k['eur'] / total * 100) if total else 0
    hotels = []
    for b in stays:
        n = max((b.end_date - b.start_date).days, 1) \
            if b.start_date and b.end_date else None
        if n:
            hotels.append({'title': b.title, 'nights': n,
                           'night': _div(b.amount_eur, n)})
    people = _people(bs)
    return {
        'trip': t, 'start': start, 'end': end, 'nights': nights,
        'people': people, 'total': total, 'money': money,
        'per_day': _div(total, max(nights, 1)) if total else None,
        'per_person': _div(total, people) if total else None,
        'hotel_night': _div(_sum(stays), stay_nights),
        'flight_seat': _div(_sum(flights), flight_seats),
        'car_day': _div(_sum(cars), car_days),
        'train': _div(_sum(priced('train')), len(priced('train'))),
        'meal': _div(_sum(priced('restaurant')),
                     len(priced('restaurant'))),
        'activities': _sum(by.get('activity', [])) or None,
        'kinds': kinds, 'hotels': hotels,
        'pending': money['pending'],
    }


ROWS = [('hotel_night', 'Hotel, per night', 'all stays / their nights'),
        ('flight_seat', 'Flights, per person per flight',
         'a return counts as two flights'),
        ('car_day', 'Car hire, per day', 'pick-up to drop-off'),
        ('train', 'Trains, per journey', ''),
        ('meal', 'Restaurants booked, per meal', ''),
        ('activities', 'Activities & tickets', 'the total'),
        ('per_day', 'Whole trip, per day', 'the total / its nights')]


def table(figs):
    out = []
    for key, label, note in ROWS:
        vals = [f[key] for f in figs]
        have = [v for v in vals if v is not None]
        low = min(have) if len(have) > 1 else None
        avg = (sum(have) / len(have)).quantize(Decimal('0.01')) \
            if have else None
        cells = []
        for i, v in enumerate(vals):
            c = {'v': eur(v.quantize(Decimal('1'))) if v is not None else '',
                 'low': v is not None and v == low and key != 'activities',
                 'more': '', 'name': figs[i]['trip'].name,
                 'colour': figs[i].get('colour', '')}
            if v is not None and avg and len(have) > 1 and \
                    key != 'activities' and v != low:
                pct = int(round((v - avg) / avg * 100))
                if pct >= 20:
                    c['more'] = '+%d%%' % pct
            cells.append(c)
        out.append({'key': key, 'label': label, 'note': note,
                    'cells': cells,
                    'avg': eur(avg.quantize(Decimal('1'))) if avg else '',
                    'strong': key == 'per_day'})
    return out


def standout(figs):
    """A few sentences that follow the figures."""
    out = []
    n = lambda f: f['trip'].name                              # noqa: E731
    hn = [f for f in figs if f['hotel_night']]
    if len(hn) > 1:
        hi = max(hn, key=lambda f: f['hotel_night'])
        rest = [f for f in hn if f is not hi]
        others = sum(f['hotel_night'] for f in rest) / len(rest)
        if hi['hotel_night'] >= others * Decimal('1.25'):
            out.append('%s’s hotels cost %s a night - against %s on '
                       'average for the others.' % (
                           n(hi), eur(hi['hotel_night'].quantize(
                               Decimal('1'))),
                           eur(others.quantize(Decimal('1')))))
    pd = [f for f in figs if f['per_day']]
    if len(pd) > 1:
        lo = min(pd, key=lambda f: f['per_day'])
        out.append('%s was the cheapest per day: %s.' % (
            n(lo), eur(lo['per_day'].quantize(Decimal('1')))))
    fs = [f for f in figs if f['flight_seat']]
    if len(fs) > 1:
        lo = min(fs, key=lambda f: f['flight_seat'])
        hi = max(fs, key=lambda f: f['flight_seat'])
        if hi['flight_seat'] > lo['flight_seat']:
            out.append('Flights: %s a seat on %s, %s on %s.' % (
                eur(lo['flight_seat'].quantize(Decimal('1'))), n(lo),
                eur(hi['flight_seat'].quantize(Decimal('1'))), n(hi)))
    for f in figs:
        if f['kinds'] and f['total']:
            top = max(f['kinds'], key=lambda k: k['eur'])
            if top['pct'] >= 60:
                out.append('On %s, %s took %d%% of the money.' % (
                    n(f), top['label'].lower(), top['pct']))
    return out[:5]


def chosen(request):
    ids = []
    for x in request.GET.getlist('t'):
        if x.isdigit() and int(x) not in ids:
            ids.append(int(x))
    trips = {t.pk: t for t in trips_for(request.user).filter(pk__in=ids)}
    return [trips[i] for i in ids if i in trips][:MAX]


@travel_view
def compare(request):
    phone = (request.resolver_match.url_name or '').startswith('m_')
    picked = chosen(request)
    every = list(trips_for(request.user))
    for t in every:
        t.start, t.end = span(t, list(t.bookings.all()))
    every.sort(key=lambda t: t.start or dt.date.min, reverse=True)
    ctx = {'picked': picked, 'every': every, 'tab': 'trips',
           'ids': [t.pk for t in picked]}
    if len(picked) >= 2:
        figs = figures_for(picked)
        top = max((f['total'] for f in figs), default=Decimal('0')) or 1
        for i, f in enumerate(figs):
            f['colour'] = COLOURS[i % len(COLOURS)]
            f['bar'] = int(f['total'] / top * 100) if f['total'] else 0
        ctx.update({'figs': figs, 'rows': table(figs),
                    'notes': standout(figs),
                    'hotels': sorted(
                        [dict(h, trip=f['trip'].name, colour=f['colour'])
                         for f in figs for h in f['hotels']],
                        key=lambda h: h['night'] or 0),
                    'legend': [{'label': l, 'colour': KIND_COLOURS[k]}
                               for k, l in Booking.KINDS
                               if any(x['kind'] == k for f in figs
                                      for x in f['kinds'])]})
    elif request.GET.getlist('t'):
        messages.error(request, 'Tick two or more trips to compare.')
    if phone:
        from .phone import page
        return page(request, 'travel/m/compare.html', ctx)
    return render(request, 'travel/compare.html', ctx)


def figures_for(trips):
    from . import fx
    out = []
    for t in trips:
        fx.convert_pending(list(t.bookings.all()), limit=3)
        f = figures(t)
        f['total_label'] = eur(f['total'])
        f['per_day_label'] = eur(f['per_day'].quantize(Decimal('1'))) \
            if f['per_day'] else ''
        f['per_person_label'] = eur(f['per_person'].quantize(
            Decimal('1'))) if f['per_person'] else ''
        for h in f['hotels']:
            h['night_label'] = eur(h['night'].quantize(Decimal('1'))) \
                if h['night'] else ''
        out.append(f)
    return out
