# -*- coding: utf-8 -*-
"""travel/views.py - TR-1, 15 Nov 2026. Travel, stage 1: trips, bookings,
sharing and the costs in two currencies - the desktop side, under Personal.

EVERY TRIP IS FETCHED THROUGH trips_for(request.user): another person's
unshared trip is a 404, for a superuser too. Owner-only actions (share,
delete the trip) check trip.owner as well.
"""
import datetime as dt
import mimetypes
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import fx
from .models import (Booking, BookingChange, BookingFile, InboundFile,
                     JoinRequest, Trip, trips_for)

PERM = 'auth.can_access_travel'
MAX_FILE = 15 * 1024 * 1024
ICONS = {'flight': 'fa-plane', 'stay': 'fa-bed', 'car': 'fa-car',
         'train': 'fa-train', 'ferry': 'fa-ship', 'transfer': 'fa-taxi',
         'activity': 'fa-ticket-alt', 'restaurant': 'fa-utensils',
         'other': 'fa-map-marker-alt'}


def travel_view(fn):
    return login_required(permission_required(PERM, raise_exception=True)(fn))


def _trip(request, trip_id):
    return get_object_or_404(trips_for(request.user), pk=trip_id)


def _booking(request, booking_id):
    b = get_object_or_404(Booking.objects.select_related('trip'),
                          pk=booking_id)
    if not b.trip.can_see(request.user):
        raise Http404
    return b


def _date(v):
    v = (v or '').strip()
    if not v:
        return None
    try:
        return dt.date.fromisoformat(v)
    except ValueError:
        return None


def _time(v):
    v = (v or '').strip()
    if not v:
        return None
    try:
        return dt.time.fromisoformat(v[:5])
    except ValueError:
        return None


def _money(v):
    v = (v or '').strip().replace(',', '').replace('€', '')
    if not v:
        return None
    try:
        d = Decimal(v).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return d if d >= 0 else None


def drop_file(f):
    """Delete a booking file's row, and the stored file only when nothing
    else uses it - TR-2: one emailed e-ticket can sit on both flights of a
    return booking, and on the email it came with."""
    name = f.file.name
    f.delete()
    if name and not BookingFile.objects.filter(file=name).exists() and \
            not InboundFile.objects.filter(file=name).exists():
        try:
            f.file.storage.delete(name)
        except Exception:                               # noqa: BLE001
            pass


def eur(v):
    """€1,234.50 - or '' for nothing."""
    if v is None:
        return ''
    s = '{:,.2f}'.format(v)
    return '€' + (s[:-3] if s.endswith('.00') else s)


def span(trip, bookings):
    """The trip's dates. TR-4 (Demetri, 15 Nov: "Should the Trip Name and
    the From and To Dates be based on uploaded reservations?"): once it has
    bookings with dates, THEY are the trip - first start to last end,
    cancelled ones left out. The dates typed on the trip count only while
    it has none, for planning before anything is booked.

    Also sets trip.where: its countries - the bookings' and the typed ones -
    and trip.by_bookings, for the form to say so."""
    live = [b for b in bookings if getattr(b, 'status', 'ok') != 'cancelled']
    days = [d for b in live for d in (b.start_date, b.end_date) if d]
    trip.by_bookings = bool(days)
    if days:
        start, end = min(days), max(days)
    else:
        start, end = trip.start_date, trip.end_date or trip.start_date
    # TR-5, 16 Nov 2026 (Demetri, looking at "Greece, Cyprus, Paphos" on
    # his Greece - Ireland trip): a booking with no country of its own -
    # every one from before Release 85 - says where it is through its
    # address, its airport or its city (travel/where.py); and "Don't keep
    # home countries in" - Cyprus only came from the flights home. Home is
    # kept only when the trip has nowhere else (a weekend in Paphos).
    from .where import country_of, is_home
    found = []
    for b in sorted(live, key=lambda b: b.start_date or dt.date.max):
        c = country_of(b)
        if c and c.lower() not in [x.lower() for x in found]:
            found.append(c)
    away = [c for c in found if not is_home(c)]
    seen = away or found
    for c in trip.country_list:
        c = (c or '').strip()
        if c and c.lower() not in [x.lower() for x in seen]:
            seen.append(c)
    trip.where = ', '.join(seen)
    trip.where_list = seen
    return start, end


def totals(bookings):
    total = paid = Decimal('0')
    pending = 0
    kinds = OrderedDict()
    for b in bookings:
        if b.amount is None or b.status == 'cancelled':
            continue
        if b.amount_eur is None:
            pending += 1
            continue
        total += b.amount_eur
        paid += b.paid_eur or Decimal('0')
        kinds[b.kind] = kinds.get(b.kind, Decimal('0')) + b.amount_eur
    top = max(kinds.values()) if kinds else None
    by_kind = [{'kind': dict(Booking.KINDS)[k], 'icon': ICONS[k],
                'eur': eur(v), 'pct': int(v / top * 100) if top else 0}
               for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])]
    return {'total': eur(total), 'paid': eur(paid),
            'due': eur(total - paid), 'pending': pending,
            'pct': int(paid / total * 100) if total else 0,
            'by_kind': by_kind, 'any': bool(kinds or pending)}


def coming_up(bookings, today):
    out = []
    for b in bookings:
        if b.status == 'cancelled':
            continue
        if b.cancel_until and b.cancel_until >= today:
            out.append({'day': b.cancel_until, 'what': 'Free cancellation ends',
                        'sub': b.title, 'warn': True, 'id': b.pk})
        if b.pay_by and b.pay_by >= today and b.paid != 'paid':
            out.append({'day': b.pay_by, 'what': 'Pay the balance',
                        'sub': b.title, 'warn': True, 'id': b.pk})
    return sorted(out, key=lambda x: x['day'])[:6]


def shape(b):
    """What the templates show for one booking."""
    b.icon = ICONS.get(b.kind, ICONS['other'])
    b.kind_label = dict(Booking.KINDS).get(b.kind, 'Other')
    b.eur_label = eur(b.amount_eur)
    b.orig_label = '' if b.amount is None or b.currency == 'EUR' else \
        '%s %s' % ('{:,.2f}'.format(b.amount), b.currency)
    b.status_label = dict(Booking.PAID).get(b.paid, '')
    b.route = ' → '.join(x for x in (b.from_place, b.to_place) if x)
    b.cancelled = b.status == 'cancelled'
    if b.pk:
        names = [u.get_full_name() or u.username for u in b.travellers.all()]
        names += [x.strip() for x in (b.traveller_names or '').split(',')
                  if x.strip()]
        b.who = ', '.join(same_people(names))
    else:
        b.who = ''
    return b


def name_key(n):
    """A person's name as a set of words, any order, any case: a boarding
    pass writes MANIAS/DIMITRIOS for the Dimitrios Manias of the
    confirmation (TR-5, 16 Nov: "Dimitrios Manias, Manias Dimitrios" on
    one flight)."""
    import re
    return frozenset(re.findall(r'[^\W\d_]+', (n or '').lower()))


def same_people(names):
    """The names, each person once - the first spelling kept."""
    out, keys = [], set()
    for n in names:
        k = name_key(n)
        if k and k not in keys:
            keys.add(k)
            out.append(n)
    return out


def included(bs):
    """TR-4 (Demetri, 15 Nov): a return flight's price is on its first
    flight; the others under the same reference say "Included in CY 310"
    instead of nothing. Sets b.included on each booking (or None)."""
    from .inbox import norm_ref
    payer = {}
    for b in sorted(bs, key=lambda b: (b.start_date or dt.date.max,
                                       b.start_time or dt.time(0))):
        r = norm_ref(b.reference)
        if r and b.amount is not None and r not in payer:
            payer[r] = b
    for b in bs:
        o = payer.get(norm_ref(b.reference)) if b.amount is None else None
        b.included = o if o is not None and o.pk != b.pk else None
    return bs


def days_of(start, end):
    out = []
    if start:
        d, end = start, min(end or start, start + dt.timedelta(days=60))
        while d <= end:
            out.append(d)
            d += dt.timedelta(days=1)
    return out


def phone_qr(request):
    from .barcodes import svg
    return svg(request.build_absolute_uri('/travel/m/'), 'qr',
               'Scan to open Travel on your phone')


def requests_for(user, trip=None):
    """Join and merge requests waiting for this person's answer."""
    out = []
    qs = JoinRequest.objects.filter(state='open').select_related(
        'trip__owner', 'from_trip__owner', 'by', 'item')
    if trip is not None:
        qs = qs.filter(Q(trip=trip) | Q(from_trip=trip))
    for r in qs:
        if r.asks.pk == user.pk:
            r.title = (r.item.data or {}).get('title') if r.item else ''
            out.append(r)
    return out


# ---------------------------------------------------------------- trips
@travel_view
def trips(request):
    from . import inbox
    inbox.kick()
    today = dt.date.today()
    show = request.GET.get('show') or 'upcoming'
    rows = []
    years, countries = set(), set()
    for t in trips_for(request.user).prefetch_related('bookings',
                                                      'shared_with'):
        bs = list(t.bookings.all())
        start, end = span(t, bs)
        t.start, t.end = start, end
        t.n = len(bs)
        t.money = totals(bs)
        t.people = [t.owner] + list(t.shared_with.all())
        t.mine = t.owner_id == request.user.id
        if start:
            years.add(start.year)
        countries.update(t.where_list)
        t.past = bool(end and end < today)
        rows.append(t)
    auto_past = False
    if show == 'upcoming':
        sel = [t for t in rows if not t.past]
        # TR-7, 16 Nov 2026 (Demetri: "I don't like that Personal ->
        # Travel is blank until I press Past. If there are not upcoming,
        # then it must show the past ones in descending date order
        # (highlighting that they are Past).")
        if not sel and any(t.past for t in rows):
            sel, auto_past = [t for t in rows if t.past], True
    elif show == 'past':
        sel = [t for t in rows if t.past]
    elif show.isdigit():
        sel = [t for t in rows if t.start and t.start.year == int(show)]
    elif show.startswith('c:'):
        sel = [t for t in rows if show[2:] in t.where_list]
    else:
        show, sel = 'all', rows
    far = dt.date(9999, 1, 1)
    sel.sort(key=lambda t: (t.start or far),
             reverse=(show == 'past' or auto_past))
    # TR-7 - a finished trip with something still To pay says so.
    from .compare import unsettled
    for t in sel:
        due = unsettled(t, list(t.bookings.all()), today) if t.past else []
        t.owing = eur(sum((b.due_eur or Decimal('0')) for b in due)) \
            if due else ''
    return render(request, 'travel/trips.html', {
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'auto_past': auto_past,
        'n_upcoming': len([t for t in rows if not t.past]),
        'n_past': len([t for t in rows if t.past]),
        'countries': sorted(countries), 'count': len(rows),
        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        'new_open': request.GET.get('new') == '1' or not rows,
        # TR-3 - point the phone's camera at this to open the phone app.
        # TR-4 - only when the Phone app button is pressed.
        'phone_qr': phone_qr(request) if request.GET.get('phone') == '1'
        else '',
        'requests': requests_for(request.user)})


@travel_view
@require_POST
def trip_new(request):
    name = (request.POST.get('name') or '').strip()[:120]
    if not name:
        messages.error(request, 'Give the trip a name.')
        return redirect('travel:trips')
    t = Trip.objects.create(
        owner=request.user, name=name,
        start_date=_date(request.POST.get('start_date')),
        end_date=_date(request.POST.get('end_date')),
        countries=(request.POST.get('countries') or '').strip()[:200])
    return redirect('travel:trip', trip_id=t.pk)


@travel_view
def trip(request, trip_id):
    t = _trip(request, trip_id)
    tab = {'trip_costs': 'costs', 'trip_itinerary': 'itinerary',
           'trip_wishlist': 'wish'}.get(request.resolver_match.url_name,
                                        'bookings')
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    # TR-5 - a hotel's or a restaurant's missing details, looked up once.
    from .places import start_details
    start_details(bs)
    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
    pl = list(t.places.all())
    from .phone import itinerary
    days = OrderedDict()
    undated = []
    for b in bs:
        if b.start_date:
            days.setdefault(b.start_date, []).append(b)
        else:
            undated.append(b)
    kinds = OrderedDict()
    for b in bs:
        kinds[b.kind] = kinds.get(b.kind, 0) + 1
    want = request.GET.get('kind')
    if want in kinds:
        days = OrderedDict((d, [b for b in l if b.kind == want])
                           for d, l in days.items())
        days = OrderedDict((d, l) for d, l in days.items() if l)
        undated = [b for b in undated if b.kind == want]
    return render(request, 'travel/trip.html', {
        'trip': t, 'tab': tab, 'start': start, 'end': end,
        'nights': (end - start).days if start and end else None,
        'days': list(days.items()), 'undated': undated, 'bookings': bs,
        'kinds': [{'key': k, 'label': dict(Booking.KINDS)[k], 'n': n,
                   'icon': ICONS[k]} for k, n in kinds.items()],
        'want': want if want in kinds else '',
        'money': totals(bs), 'coming': coming_up(bs, dt.date.today()),
        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
        'requests': requests_for(request.user, t),
        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs)})


def settle_rows(t, bs):
    from .compare import unsettled
    return unsettled(t, bs)


@travel_view
def trip_edit(request, trip_id):
    t = _trip(request, trip_id)
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:120]
        if name:
            t.name = name
            t.start_date = _date(request.POST.get('start_date'))
            t.end_date = _date(request.POST.get('end_date'))
            t.countries = (request.POST.get('countries') or '').strip()[:200]
            t.notes = (request.POST.get('notes') or '').strip()
            t.save()
            messages.success(request, 'Trip saved.')
            return redirect('travel:trip', trip_id=t.pk)
        messages.error(request, 'Give the trip a name.')
    t.start, t.end = span(t, list(t.bookings.all()))
    return render(request, 'travel/trip_form.html', {
        'trip': t, 'is_owner': t.owner_id == request.user.id})


@travel_view
@require_POST
def trip_delete(request, trip_id):
    t = _trip(request, trip_id)
    if t.owner_id != request.user.id:
        raise Http404
    for f in BookingFile.objects.filter(booking__trip=t):
        drop_file(f)
    t.delete()
    messages.success(request, 'Trip deleted.')
    return redirect('travel:trips')


def sharable(owner):
    """Everyone with Travel, except the owner - a trip can only be shared
    with people who can open it."""
    q = Q(user_permissions__codename='can_access_travel') | \
        Q(groups__permissions__codename='can_access_travel') | \
        Q(is_superuser=True)
    return User.objects.filter(q, is_active=True).exclude(
        pk=owner.pk).distinct().order_by('first_name', 'username')


@travel_view
def trip_share(request, trip_id):
    t = _trip(request, trip_id)
    if t.owner_id != request.user.id:
        raise Http404
    people = list(sharable(request.user))
    if request.method == 'POST':
        picked = {int(x) for x in request.POST.getlist('people')
                  if x.isdigit()}
        t.shared_with.set([u for u in people if u.pk in picked])
        messages.success(request, 'Sharing saved.')
        return redirect('travel:trip', trip_id=t.pk)
    on = set(t.shared_with.values_list('pk', flat=True))
    for u in people:
        u.on = u.pk in on
    return render(request, 'travel/share.html', {'trip': t,
                                                 'people': people})


# ------------------------------------------------------------- bookings
# What the change trail watches, and how it names each field.
TRACKED = [('kind', 'Kind'), ('title', 'Name'), ('provider', 'With'),
           ('reference', 'Reference'), ('segment', 'Part'),
           ('start_date', 'Starts'),
           ('start_time', 'Start time'), ('end_date', 'Ends'),
           ('end_time', 'End time'), ('from_place', 'From'),
           ('to_place', 'To'), ('address', 'Address'), ('phone', 'Phone'),
           ('link', 'Link'), ('details', 'Details'),
           ('currency', 'Currency'), ('amount', 'Amount'),
           ('amount_eur', 'In euros'), ('paid', 'Paid?'),
           ('paid_amount', 'Part paid'), ('pay_by', 'Pay by'),
           ('cancel_until', 'Free cancellation until'),
           ('status', 'Status'), ('traveller_names', 'Also travelling')]


def _shown(b, f):
    v = getattr(b, f)
    if v is None or v == '':
        return ''
    if f == 'kind':
        return dict(Booking.KINDS).get(v, v)
    if f == 'paid':
        return dict(Booking.PAID).get(v, v)
    if f == 'status':
        return dict(Booking.STATUSES).get(v, v)
    if isinstance(v, dt.date):
        return v.strftime('%a %d %b %Y').replace(' 0', ' ')
    if isinstance(v, dt.time):
        return v.strftime('%H:%M')
    return str(v)


def snapshot(b):
    return {f: _shown(b, f) for f, _ in TRACKED}


def diff(before, b):
    """[{label, old, new}] for each tracked field that changed."""
    after = snapshot(b)
    out = []
    for f, label in TRACKED:
        if f == 'amount_eur' and not b.eur_typed:
            continue
        if before.get(f, '') != after[f]:
            old, new = before.get(f, ''), after[f]
            if f == 'details':
                old, new = ('(was set)' if old else ''), 'changed'
            out.append({'label': label, 'old': old, 'new': new})
    return out


FIELDS_TEXT = (('title', 160), ('provider', 120), ('reference', 60),
               ('segment', 40), ('from_place', 120), ('to_place', 120),
               ('address', 255), ('phone', 40), ('link', 500),
               ('traveller_names', 255), ('city', 80), ('country', 60))


def save_booking(request, b):
    """Fill a booking from the form. Returns the list of problems."""
    P = request.POST
    problems = []
    kind = P.get('kind')
    b.kind = kind if kind in dict(Booking.KINDS) else 'other'
    for f, n in FIELDS_TEXT:
        setattr(b, f, (P.get(f) or '').strip()[:n])
    if b.link and not b.link.startswith(('http://', 'https://')):
        b.link = 'https://' + b.link
    b.details = (P.get('details') or '').strip()
    b.start_date = _date(P.get('start_date'))
    b.start_time = _time(P.get('start_time'))
    b.end_date = _date(P.get('end_date'))
    b.end_time = _time(P.get('end_time'))
    cur = (P.get('currency') or 'EUR').upper()
    b.currency = cur if cur in fx.CURRENCIES else 'EUR'
    old = (b.amount, b.currency, b.amount_eur)
    b.amount = _money(P.get('amount'))
    typed = _money(P.get('amount_eur'))
    if b.currency == 'EUR':
        b.eur_typed = False
    elif typed is not None and (typed != old[2] or b.eur_typed):
        # Typed from the card statement - it wins over any rate.
        b.amount_eur, b.eur_typed, b.fx_rate = typed, True, None
    elif typed is None:
        b.eur_typed = False
    paid = P.get('paid')
    b.paid = paid if paid in dict(Booking.PAID) else 'due'
    b.paid_amount = _money(P.get('paid_amount')) if b.paid == 'part' else None
    b.pay_by = _date(P.get('pay_by'))
    b.cancel_until = _date(P.get('cancel_until'))
    b.status = 'cancelled' if P.get('cancelled') else 'ok'
    if not b.title:
        problems.append('Say what the booking is.')
    if b.end_date and b.start_date and b.end_date < b.start_date:
        problems.append('The end is before the start.')
    if not b.eur_typed:
        if (b.amount, b.currency) != old[:2] or b.amount_eur is None:
            b.fx_date = None
        fx.convert(b)
    return problems


def add_files(request, b):
    n = 0
    for f in request.FILES.getlist('files'):
        if f.size > MAX_FILE:
            messages.error(request, '%s is over 15 MB - not added.' % f.name)
            continue
        BookingFile.objects.create(booking=b, file=f, name=f.name[:160],
                                   uploaded_by=request.user)
        n += 1
    return n


@travel_view
def booking_form(request, trip_id=None, booking_id=None):
    if booking_id:
        b = _booking(request, booking_id)
        t = b.trip
    else:
        t = _trip(request, trip_id)
        b = Booking(trip=t, added_by=request.user,
                    kind=request.GET.get('kind') or 'flight')
    problems = []
    dupe = None
    people = [t.owner] + list(t.shared_with.all())
    on = set(b.travellers.values_list('pk', flat=True)) if b.pk else set()
    for u in people:
        u.on = u.pk in on
    if request.method == 'POST':
        before = snapshot(b) if b.pk else None
        problems = save_booking(request, b)
        # A SECOND COPY OF ONE BOOKING (Demetri, 15 Nov: "put safeties in
        # place"). The same reference twice on a trip is stopped once, with
        # the one it matches, and saved only when the person says so.
        if b.reference and not request.POST.get('dupe_ok'):
            dupe = t.bookings.exclude(pk=b.pk).filter(
                reference__iexact=b.reference).first()
            if dupe:
                problems.append('Booking reference %s is already on this '
                                'trip.' % b.reference)
        if not problems:
            b.save()
            # WHO IS TRAVELLING: ticked from the trip's people.
            picked = {int(x) for x in request.POST.getlist('travellers')
                      if x.isdigit()}
            b.travellers.set([u for u in people if u.pk in picked])
            if before is not None:
                changed = diff(before, b)
                if changed:
                    BookingChange.objects.create(
                        booking=b, by=request.user, source='edit',
                        changes=changed)
            add_files(request, b)
            # TR-5 - a table at a restaurant on the wish list takes that
            # place onto its day; a hotel's or restaurant's missing
            # address, phone and times are looked up.
            from . import places as P
            P.link_booking(b)
            P.start_details([b], limit=1)
            messages.success(request, 'Booking saved.')
            return redirect('travel:booking', booking_id=b.pk)
    return render(request, 'travel/booking_form.html', {
        'trip': t, 'b': b, 'problems': problems, 'dupe': dupe,
        'kinds': Booking.KINDS,
        'paids': Booking.PAID, 'currencies': fx.CURRENCIES,
        'files': list(b.files.all()) if b.pk else [], 'people': people})


@travel_view
def booking(request, booking_id):
    b = shape(_booking(request, booking_id))
    if b.amount is not None and b.amount_eur is None and not b.eur_typed:
        fx.convert_pending([b], limit=1)
        shape(b)
    nights = (b.end_date - b.start_date).days \
        if b.kind == 'stay' and b.start_date and b.end_date else None
    from .phone import pass_card
    if b.amount is None:
        others = [x for x in b.trip.bookings.all() if x.pk != b.pk]
        included(others + [b])
    else:
        b.included = None
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'passes': [pass_card(p) for p in b.passes.all()],
        'nights': nights, 'paid_label': eur(b.paid_eur),
        'due_label': eur(b.due_eur),
        'changes': list(b.changes.select_related('by')),
        'today': dt.date.today()})


@travel_view
@require_POST
def booking_delete(request, booking_id):
    b = _booking(request, booking_id)
    t = b.trip
    for f in list(b.files.all()):
        drop_file(f)
    # TR-5 - a place it was booked for goes back to the wish list.
    from .places import unlink_deleted
    unlink_deleted(b)
    b.delete()
    messages.success(request, 'Booking deleted.')
    return redirect('travel:trip', trip_id=t.pk)


@travel_view
def booking_file(request, file_id):
    f = get_object_or_404(BookingFile.objects.select_related('booking__trip'),
                          pk=file_id)
    if not f.booking.trip.can_see(request.user):
        raise Http404
    try:
        fh = f.file.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404
    kind = mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
    return FileResponse(fh, content_type=kind, filename=f.name,
                        as_attachment=not kind.startswith(('image/',
                                                           'application/pdf')))


@travel_view
@require_POST
def booking_file_delete(request, file_id):
    f = get_object_or_404(BookingFile.objects.select_related('booking__trip'),
                          pk=file_id)
    if not f.booking.trip.can_see(request.user):
        raise Http404
    bid = f.booking_id
    drop_file(f)
    messages.success(request, 'File removed.')
    return redirect(reverse('travel:booking_edit', args=[bid]))
