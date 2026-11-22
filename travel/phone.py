# -*- coding: utf-8 -*-
"""travel/phone.py - TR-3, 15 Nov 2026. Travel, stage 3: the phone app.

Demetri, 15 Nov: a separate installable Travel app for the phone, "like
Wellness" - a 30-day login on the phone, the boarding passes there and
working without a signal, "Share -> Alivente Travel".

    /travel/m/            Today - what is on today and next, or the
                          countdown to the next trip
    /travel/m/trips/      the trips, as on the desktop
    /travel/m/passes/     every boarding pass to come, wallet-style, its
                          barcode drawn from the airline's own code
    /travel/m/check/      To check, with the same buttons
    /travel/m/share/      where "Share -> Travel" on the phone lands
    /travel/app/...       the installable shell: manifest, service worker,
                          style, script, icons (no login - a phone fetches
                          them before anyone is signed in; nothing personal)

The pages are the same data through the same doors as the desktop:
every trip through trips_for(user), every booking through its trip.
"""
import copy
import datetime as dt
import json
import os
from collections import OrderedDict
from email.message import EmailMessage
from email.utils import make_msgid

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import barcodes, boarding, budget, dayorder, fx, ideas, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
from .views import (coming_up, eur, included, money_state, requests_for,
                    with_weather,
                    shape, span,
                    totals, travel_view)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
ASSET_TYPES = {
    'travel.css': 'text/css; charset=utf-8',
    'travel.js': 'application/javascript; charset=utf-8',
    'icon-192.png': 'image/png',
    'icon-512.png': 'image/png',
    'icon-maskable-512.png': 'image/png',
    'apple-touch-icon.png': 'image/png',
}
# Bump this AND the ?v= in travel/m/base.html together whenever the style
# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
# TR-15, 17 Nov 2026 (R95 changed travel.css but not this, and the phone
# app kept its old copy - the calendar came out unstyled): the version
# moves whenever travel.css or travel.js does. SW_ASSETS is the fingerprint
# of the two it was moved for; test_travel_fifteen.py fails the gate when
# they change and it does not.
# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
# RA01, 18 Nov 2026 - their drop-downs.
# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
# RA09, 21 Nov 2026 - Google checks left.
# RA10, 21 Nov 2026 - Not found on Google; the distance note's own class;
# outside what you asked for, in its own section.
# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
# RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
# RA13, 22 Nov 2026 - the trip tabs: icons and short names.
SW_VERSION = 'tv26-1'
SW_ASSETS = '10dd4084105c'


def page(request, template, ctx):
    """Every phone page shows To check's count on its tab."""
    ctx.setdefault('checks', inbox.open_count(request.user))
    ctx.setdefault('address', inbox.inbox_address())
    return render(request, template, ctx)


def _today():
    return timezone.localdate()


def _bookings(user):
    return Booking.objects.filter(trip__in=trips_for(user)).select_related(
        'trip').prefetch_related('travellers')


def _trip_list(user):
    out = []
    for t in trips_for(user).prefetch_related('bookings', 'spends',
                                              'shared_with'):
        bs = list(t.bookings.all())
        t.start, t.end = span(t, bs)
        t.n = len(bs)
        t.show_money = budget.money_ok(t, user)               # RA05
        t.money = totals(bs, list(t.spends.all())) if t.show_money \
            else totals([])
        t.people = [t.owner] + list(t.shared_with.all())
        out.append(t)
    return out


def on_day(bs, day):
    """What a day holds: what starts that day, the stay you wake up in,
    and the check-outs and drop-offs - each once, in time order."""
    rows = []
    for b in bs:
        if b.status == 'cancelled':
            continue
        if b.start_date == day:
            rows.append((b.start_time or dt.time(0, 0), 'start', b))
        elif b.end_date == day and b.kind in ('stay', 'car'):
            rows.append((b.end_time or dt.time(11, 0), 'end', b))
        elif b.kind == 'stay' and b.start_date and b.end_date and \
                b.start_date < day < b.end_date:
            rows.append((dt.time(0, 0), 'during', b))
    rows.sort(key=lambda r: (r[0], r[2].pk))
    out = []
    for when, what, b in rows:
        # A copy: a stay is on several days - check in, staying, check out
        # - and each day's row says its own thing (TR-4, the itinerary).
        b = copy.copy(b)
        shape(b)
        b.what = what
        b.label = {'start': {'stay': 'Check in', 'car': 'Pick up'}.get(
            b.kind, ''), 'end': {'stay': 'Check out', 'car': 'Drop off'}.get(
            b.kind, ''), 'during': 'Staying at'}[what]
        b.when = '' if what == 'during' else (
            (b.start_time if what == 'start' else b.end_time) or '')
        # TR-6, 16 Nov 2026 - which night of the stay this is (Demetri:
        # the stay's cost on all three days "looks deceiving").
        b.nights = (b.end_date - b.start_date).days \
            if b.kind == 'stay' and b.start_date and b.end_date else None
        b.night = (day - b.start_date).days + 1 \
            if what == 'during' and b.nights else None
        out.append(b)
    # TR-9, 16 Nov 2026 - a check-in or a car pick-up waits for the flight
    # that gets you there (Demetri: "the order on the 9th should be
    # Checkout, Drop off car, Fly on Ryan Air and then check in").
    dayorder.smart(out, day)
    out.sort(key=lambda r: (r.sort_at, r.rank, r.pk))
    return out


class DayRows(list):
    """A day's rows; .custom when they are in an order someone chose."""
    custom = False


def day_rows(bs, places, day, saved=None):
    """TR-4 - a day of the itinerary: its bookings (as on_day) and the
    places planned for it, in time order; places with no time at the end.
    TR-9 - then the order chosen for the day (saved: {day: keys}), if any."""
    rows = [(b.sort_at, 0, b) for b in on_day(bs, day)]
    for p in places:
        # TR-5 - a place with its booking shows once: as the booking.
        if p.day == day and not p.booking_id:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
    rows.sort(key=lambda r: (r[0], r[1]))
    out, custom = dayorder.ordered([r[2] for r in rows],
                                   (saved or {}).get(day))
    for r in out:
        r.order_key = dayorder.key(r)
    out = DayRows(out)
    out.custom = custom
    return out


def itinerary(trip, bs, places):
    """Every day of the trip, first to last, each with its rows - empty
    days too, so there is somewhere to put a place. (At most 60 days.)"""
    start, end = span(trip, bs)
    saved = dayorder.saved_for(trip)
    days = []
    if start:
        end = end or start
        if (end - start).days > 60:
            end = start + dt.timedelta(days=60)
        d = start
        while d <= end:
            days.append((d, day_rows(bs, places, d, saved)))
            d += dt.timedelta(days=1)
    return days


# ------------------------------------------------------------------ Today
@travel_view
def today(request):
    inbox.kick()
    me = request.user
    day = _today()
    trips = _trip_list(me)
    now = [t for t in trips if t.start and t.start <= day <=
           (t.end or t.start)]
    nxt = sorted([t for t in trips if t.start and t.start > day],
                 key=lambda t: t.start)
    trip = now[0] if now else (nxt[0] if nxt else None)
    ctx = {'day': day, 'trip': trip, 'on_now': bool(now),
           'checks': inbox.open_count(me),
           'requests': requests_for(me), 'tab': 'today'}
    if trip:
        bs = list(trip.bookings.prefetch_related('travellers'))
        fx.convert_pending(bs, limit=2)
        pl = list(trip.places.all())
        saved = dayorder.saved_for(trip)                    # TR-9
        if now:
            ctx['day_no'] = (day - trip.start).days + 1
            ctx['days'] = ((trip.end or trip.start) - trip.start).days + 1
            ctx['today_rows'] = day_rows(bs, pl, day, saved)
            ctx['tomorrow_rows'] = day_rows(bs, pl,
                                            day + dt.timedelta(days=1), saved)
            ctx['tomorrow'] = day + dt.timedelta(days=1)
        else:
            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start, saved)
        # RA05, 19 Nov 2026 - the Today line: spent today, a day left.
        shaped = [shape(b) for b in bs]
        start, end = span(trip, shaped)
        if budget.hide(trip, me, shaped):
            spends = list(trip.spends.all())
            budget.convert_pending(spends, limit=2)
            ctx['bud'] = budget.summary(trip, spends, start, end, day)
            ctx['can_spend'] = budget.can_spend(trip, me)
        ctx['coming'] = coming_up(shaped, day)
        # RA06, 19 Nov 2026 - the weather where you are (Demetri: "a small
        # box with the Weather for that city for the day").
        from . import weather
        if now:
            ctx['wx'] = weather.for_day(shaped, day, day, pl)
            ctx['wx_next'] = weather.for_day(shaped, day + dt.timedelta(1),
                                             day, pl)
        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day, pl)
        # RA12, 22 Nov 2026 - Good to know for the city you are in (or
        # the first one, before the trip).
        from . import cityinfo
        at = weather.place_for(shaped, day if now else trip.start)
        if at:
            ctx['card'] = cityinfo.card_at(at[0], at[1], day if now
                                           else trip.start)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
                day, day + dt.timedelta(days=1))).count()
    if not trip:
        # TR-7, 16 Nov 2026 (Demetri: "on the Today Page of the App, I
        # don't like that it is blank. The same principle must apply"):
        # nothing on or ahead - the last trip, then the ones before it.
        past = sorted([t for t in trips if t.end and t.end < day],
                      key=lambda t: t.start, reverse=True)
        if past:
            from .compare import unsettled
            last = past[0]
            due = unsettled(last, list(last.bookings.all()), day) \
                if last.show_money else []
            last.owing = eur(sum((b.due_eur or 0) for b in due)) \
                if due else ''
            ctx['last'], ctx['earlier'] = last, past[1:6]
    return page(request, 'travel/m/today.html', ctx)


# ------------------------------------------------------------------ Trips
@travel_view
def trips(request):
    day = _today()
    rows = _trip_list(request.user)
    # TR-16, 18 Nov 2026 - the same chips and menus as the computer: All,
    # Upcoming and Past with their counts, Year and Country menus, and
    # they combine (travel/trip_filter.py, where TR-7 and TR-13 live on).
    from . import trip_filter as TF
    F = TF.apply(request, rows, day)
    sel, auto_past = F['trips'], F['auto_past']
    past = F['show'] == 'past'
    # TR-14, 17 Nov 2026 - List | Calendar, as on the computer.
    from . import calendar_view as CV
    view, asked = CV.view_of(request)
    for t in rows:
        t.where = getattr(t, 'where', '')
    cal = CV.build(rows, CV.month_of(request.GET.get('month'), day), day) \
        if view == 'calendar' else None
    return CV.remember(page(request, 'travel/m/trips.html', {
        'view': view, 'cal': cal,
        'trips': sel, 'past': past, 'tab': 'trips', 'auto_past': auto_past,
        'F': F,
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)}), view, asked)


@travel_view
def trip(request, trip_id):
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs, limit=3)
    bs = included([shape(b) for b in bs])
    t.start, t.end = span(t, bs)
    # RA05, 19 Nov 2026 - the budget, and who sees the money.
    show_money = budget.hide(t, request.user, bs)
    if request.GET.get('tab') == 'costs' and not show_money:
        return redirect('travel:m_trip', trip_id=t.pk)
    days = OrderedDict()
    undated = []
    for b in bs:
        if b.start_date:
            days.setdefault(b.start_date, []).append(b)
        else:
            undated.append(b)
    costs = request.GET.get('tab') == 'costs'
    sub = request.GET.get('tab') if request.GET.get('tab') in (
        'costs', 'itinerary', 'wish', 'info') else 'bookings'
    pl = list(t.places.all())
    for p in pl:
        p.is_place = True
    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        # RA12, 22 Nov 2026 - Good to know, a card a city.
        'cards': _cards(t) if sub == 'info' else [],
        'itinerary': with_weather(itinerary(t, bs, pl), bs, pl)
        if sub == 'itinerary' else [],
        # TR-11 - the trip's own days (its bookings decide them), so Plan
        # my days shows on Things to do.
        'trip_days': _days_of(t) if sub == 'wish' else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'costs': costs,
        'money': totals(bs, list(t.spends.all()) if show_money else ()),
        **money_state(t, request, bs, t.start, t.end, show_money,
                      'costs' if costs else sub),
        'people': [t.owner] + list(t.shared_with.all()), 'tab': 'trips',
        'coming': coming_up(bs, _today()),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **(planner.page_state(t, request)
           if sub in ('itinerary', 'wish') else {}),
        # TR-12 - Suggest things to do.
        **(ideas.page_state(t, request)
           if sub in ('wish', 'itinerary') else {})})


def _cards(t):
    from . import cityinfo
    return cityinfo.cards_for(t, list(t.bookings.all()))


def _days_of(t):
    from .views_places import trip_days
    return trip_days(t)


def pass_card(p):
    """One boarding pass, ready to draw: what the barcode says first,
    what the booking says where the barcode is silent."""
    b = p.booking
    info = barcodes.bcbp(p.code, b.start_date.year if b.start_date else None)
    p.info = info
    p.svg = barcodes.svg(p.code, p.format,
                         'Boarding pass barcode for %s' % (p.name or
                                                           'this flight'))
    frm = info.get('from') or (b.from_place or '')
    to = info.get('to') or (b.to_place or '')
    p.frm = frm[-4:].strip('() ') if len(frm) > 4 else frm
    p.to = to[-4:].strip('() ') if len(to) > 4 else to
    p.flight = ('%s %s' % (info.get('carrier', ''), info.get('flight', ''))
                ).strip() or b.segment or b.title
    p.seat_shown = p.seat or info.get('seat', '')
    # TR-7/TR-8, 16 Nov 2026 - an airline's own "Add to Google Wallet" link
    # stops working once the flight is over (Cyprus Airways answers
    # CKI_BOARDINGPASS_NONEFOUND). p.over says so; the Passes page settles
    # it again with every pass in view, so connections count.
    boarding.settle([p], timezone.localtime().replace(tzinfo=None), None)
    return p


@travel_view
def booking(request, booking_id):
    b = get_object_or_404(_bookings(request.user), pk=booking_id)
    shape(b)
    if b.amount is None:
        included([x for x in b.trip.bookings.all() if x.pk != b.pk] + [b])
    else:
        b.included = None
    budget.hide(b.trip, request.user, [b])                  # RA05
    passes = [pass_card(p) for p in b.passes.all()]
    nights = ((b.end_date - b.start_date).days
              if b.kind == 'stay' and b.start_date and b.end_date else None)
    return page(request, 'travel/m/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'passes': passes, 'nights': nights, 'tab': 'trips',
        'paid_label': eur(b.paid_eur), 'due_label': eur(b.due_eur)})


# ----------------------------------------------------------------- Passes
def flown(b, now):
    """Is this flight over? Times are the booking's local times, read
    against the time here - near enough for a pass to step aside."""
    if not b.start_date:
        return False
    if b.end_time:
        end = dt.datetime.combine(b.end_date or b.start_date, b.end_time)
        if b.start_time and not b.end_date and b.end_time < b.start_time:
            end += dt.timedelta(days=1)         # lands after midnight
        return end + dt.timedelta(minutes=30) < now
    leaves = dt.datetime.combine(b.start_date, b.start_time or dt.time(23,
                                                                      59))
    return leaves + dt.timedelta(hours=3) < now


@travel_view
def passes(request):
    """TR-8, 16 Nov 2026 - three tabs at the top: Next, Coming up, Used
    (Demetri: "Selection is hidden at the bottom"). Your own pass first;
    Used ones kept for good, stamped. The rules are in boarding.py."""
    day = _today()
    rows = BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).exclude(
        booking__status='cancelled').select_related('booking__trip')
    cards = [pass_card(p) for p in rows]
    now = timezone.localtime().replace(tzinfo=None)
    nxt, coming, used, earlier, then = boarding.settle(cards, now,
                                                       request.user)
    for p in nxt:
        p.boards = boarding.boards_in(p, now)
    tab = request.GET.get('tab')
    if tab not in ('next', 'coming', 'used'):
        tab = 'next'
    ctx = {'nxt': nxt, 'coming': coming, 'used': used, 'earlier': earlier,
           'then': then, 'last': used[0] if used else None, 'tab_open': tab,
           'tab': 'passes', 'day': day, 'cards': cards}
    # TR-4 (Demetri, 15 Nov: "I want to be able to view boarding passes on
    # the desktop app as well") - the same passes, laid out for a screen.
    if request.resolver_match.url_name == 'passes':
        return render(request, 'travel/passes.html', ctx)
    return page(request, 'travel/m/passes.html', ctx)


def _back(request, phone):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt.startswith('/travel/') and '//' not in nxt:
        return nxt
    return reverse('travel:m_passes' if phone else 'travel:passes')


@require_POST
@travel_view
def pass_mark(request, pass_id, how):
    """"Done with this pass" (how='used') and "Not flown yet" (how='open')
    - Demetri, 16 Nov: nothing is ever switched off by the clock alone."""
    p = get_object_or_404(BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)), pk=pass_id)
    if how not in ('used', 'open'):
        raise Http404
    p.marked, p.marked_at = how, timezone.now()
    p.save(update_fields=['marked', 'marked_at', 'updated_at'])
    phone = request.resolver_match.url_name.startswith('m_')
    return redirect(_back(request, phone))


@travel_view
def pass_wallet(request, pass_id):
    """Add to Google Wallet, through here first (Demetri, 16 Nov: "we need
    to give a nice message explaining this to people. Not have the system
    error out"). Before the flight is over: straight on to the airline.
    After: a card that says why, instead of the airline's error."""
    p = get_object_or_404(BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).select_related(
        'booking__trip'), pk=pass_id)
    if not p.wallet_link:
        raise Http404
    mine = [pass_card(x) for x in BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).exclude(
        booking__status='cancelled').select_related('booking__trip')]
    boarding.settle(mine, timezone.localtime().replace(tzinfo=None),
                    request.user)
    card = next((x for x in mine if x.pk == p.pk), pass_card(p))
    phone = request.resolver_match.url_name.startswith('m_')
    if not card.over:
        return redirect(p.wallet_link)
    ctx = {'p': card, 'tab': 'passes',
           'back': reverse('travel:m_passes' if phone else 'travel:passes')}
    if phone:
        return page(request, 'travel/m/pass_wallet.html', ctx)
    return render(request, 'travel/pass_wallet.html', ctx)


# --------------------------------------------------------------- To check
@travel_view
def check(request):
    from .views_inbox import show, suggest
    inbox.kick()
    me = request.user
    items = suggest([show(i) for i in CheckItem.objects.filter(
        user=me, state__in=('open', 'asked')).select_related(
        'booking', 'trip', 'other_trip__owner')], me)
    trips = [t for t in _trip_list(me)]
    waiting = InboundEmail.objects.filter(user=me, state__in=(
        'new', 'reading')).count()
    return page(request, 'travel/m/check.html', {
        'items': items, 'trips': trips, 'waiting': waiting,
        'requests': requests_for(me), 'tab': 'check',
        'address': inbox.inbox_address()})


ACTIONS = ('add', 'merge', 'dismiss', 'ask')


@travel_view
@require_POST
def check_action(request, item_id, action):
    from . import views_inbox as VI
    if action not in ACTIONS:
        raise Http404
    return {'add': VI.check_add, 'merge': VI.check_merge,
            'dismiss': VI.check_dismiss, 'ask': VI.check_ask}[action](
        request, item_id)


@travel_view
@require_POST
def answer(request, request_id):
    from . import views_inbox as VI
    return VI.answer(request, request_id)


@travel_view
def booking_file(request, file_id):
    from .views import booking_file as desk
    return desk(request, file_id)


@travel_view
def help_page(request):
    return page(request, 'travel/m/help.html', {
        'tab': '', 'address': inbox.inbox_address()})


# ------------------------------------------------------------------ Share
SHARE_FILES = ('application/pdf', 'image/jpeg', 'image/png', 'image/webp',
               'image/gif', 'application/vnd.apple.pkpass', 'message/rfc822')


def received_for(user, raw):
    """An email (or what was shared) from someone signed in: theirs, and
    trusted - they handed it over themselves."""
    from django.core.files.base import ContentFile
    from . import inbound
    msg = inbound.parse(raw)
    mid = inbound.message_id(msg, raw)
    old = InboundEmail.objects.filter(message_id=mid).first()
    if old:
        return old, False
    e = InboundEmail(message_id=mid, user=user, sender='shared on the phone',
                     subject=str(msg.get('Subject') or '')[:255],
                     sent=inbound.sent_at(msg) or timezone.now(),
                     trusted=True)
    e.raw.save('email.eml', ContentFile(raw), save=False)
    e.save()
    return e, True


@csrf_exempt
@travel_view
def share(request):
    """Share -> Travel on the phone (the manifest's share_target): an
    email, a PDF ticket, a screenshot or a link becomes an email to read,
    exactly as if it had been forwarded. Signed in, so it is yours."""
    if request.method != 'POST':
        return redirect('travel:m_check')
    files = request.FILES.getlist('files')
    title = (request.POST.get('title') or '').strip()
    text = (request.POST.get('text') or '').strip()
    link = (request.POST.get('url') or '').strip()
    # TR-4 - A PLACE FROM GOOGLE MAPS ("Share -> Travel" in Maps): not an
    # email to read but somewhere to go - Add a place, on the trip that is
    # on now or the next one, with what Maps shared already filled in.
    from . import places as PL
    shared = '\n'.join(x for x in (title, text, link) if x)
    if not files and PL.is_maps(shared):
        day = _today()
        rows = _trip_list(request.user)
        now = [t for t in rows if t.start and t.start <= day <=
               (t.end or t.start)]
        nxt = sorted([t for t in rows if t.start and t.start > day],
                     key=lambda t: t.start)
        t = (now or nxt or [None])[0]
        if t is None:
            messages.error(request, 'Make a trip first - then share the '
                           'place again.')
            return redirect('travel:m_trips')
        from urllib.parse import urlencode
        q = text or title
        if link and link not in q:
            q = (q + '\n' + link).strip()
        return redirect('%s?%s' % (reverse('travel:m_place_new',
                                           args=[t.pk]),
                                   urlencode({'q': q[:500]})))
    done = 0
    rest = []
    for f in files[:6]:
        if f.size > 15 * 1024 * 1024:
            continue
        name = (f.name or '').lower()
        data = f.read()
        if name.endswith('.eml') or f.content_type == 'message/rfc822':
            received_for(request.user, data)
            done += 1
        elif f.content_type in SHARE_FILES or name.endswith(
                ('.pdf', '.pkpass', '.jpg', '.jpeg', '.png')):
            rest.append((f.name or 'shared', f.content_type, data))
    if rest or text or link:
        m = EmailMessage()
        m['Subject'] = title or (rest[0][0] if rest else 'Shared to Travel')
        m['From'] = request.user.email or 'phone@travel'
        m['Message-ID'] = make_msgid(domain='travel.share')
        m['Date'] = timezone.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        m.set_content('\n\n'.join(x for x in (text, link) if x) or ' ')
        for name, ctype, data in rest:
            if name.lower().endswith('.pkpass'):
                ctype = 'application/vnd.apple.pkpass'
            mt, st = (ctype or 'application/octet-stream').split('/', 1)
            m.add_attachment(data, maintype=mt, subtype=st, filename=name)
        received_for(request.user, m.as_bytes())
        done += 1
    if done:
        inbox.kick()
        messages.success(request, 'Got it - reading it now. It will be '
                         'here in a minute.')
    else:
        messages.error(request, 'Nothing to read in that - share an email, '
                       'a PDF ticket or a screenshot.')
    return redirect('travel:m_check')


# ------------------------------------------------------------- the shell
def manifest(request):
    data = {
        'name': 'Alivente Travel',
        'short_name': 'Travel',
        'description': 'Your trips, bookings and boarding passes.',
        'id': '/travel/m/',
        'start_url': '/travel/m/?source=app',
        'scope': '/travel/m/',
        'display': 'standalone',
        # TR-4 (Demetri, 15 Nov: "if I turn my phone, the pass flips. I
        # don't want that.") - the installed app stays upright.
        'orientation': 'portrait',
        'background_color': '#F3F5F6',
        'theme_color': '#0F7480',
        'icons': [
            {'src': '/travel/app/icon-192.png', 'sizes': '192x192',
             'type': 'image/png'},
            {'src': '/travel/app/icon-512.png', 'sizes': '512x512',
             'type': 'image/png'},
            {'src': '/travel/app/icon-maskable-512.png', 'sizes': '512x512',
             'type': 'image/png', 'purpose': 'maskable'},
        ],
        'shortcuts': [
            {'name': 'Boarding passes', 'short_name': 'Passes',
             'url': '/travel/m/passes/'},
            {'name': 'To check', 'short_name': 'To check',
             'url': '/travel/m/check/'},
        ],
        # "Share -> Alivente Travel": an email, a PDF ticket, a screenshot.
        'share_target': {
            'action': '/travel/m/share/',
            'method': 'POST',
            'enctype': 'multipart/form-data',
            'params': {'title': 'title', 'text': 'text', 'url': 'url',
                       'files': [{'name': 'files', 'accept': [
                           'application/pdf', 'image/*', 'message/rfc822',
                           '.eml', '.pkpass',
                           'application/vnd.apple.pkpass']}]},
        },
    }
    return HttpResponse(json.dumps(data),
                        content_type='application/manifest+json')


def service_worker(request):
    """Pages come fresh when there is a signal, and the last copy of each
    is kept on the phone for when there is not - the passes above all,
    fetched ahead each time the app opens. Signed out, the copies go."""
    body = r"""// Alivente Travel service worker - TR-3, 15 Nov 2026. Version %(v)s.
const SHELL = 'travel-shell-%(v)s';
const PAGES = 'travel-pages';
const FILES = ['/travel/app/travel.css?v=%(v)s', '/travel/app/travel.js?v=%(v)s',
               '/travel/app/icon-192.png'];
const AHEAD = ['/travel/m/passes/', '/travel/m/'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k.startsWith('travel-shell-') && k !== SHELL).map(k => caches.delete(k))
  )).then(() => self.clients.claim()));
});
function keep(req, r) {
  if (r.redirected && r.url.indexOf('/login/') !== -1) {
    // Signed out: nothing personal stays on the phone.
    caches.delete(PAGES);
    return r;
  }
  if (r.ok && !r.redirected) {
    const copy = r.clone();
    caches.open(PAGES).then(c => c.put(new URL(req.url).pathname + new URL(req.url).search, copy));
  }
  return r;
}
self.addEventListener('message', e => {
  if (e.data === 'ahead') {
    AHEAD.forEach(u => fetch(u, {credentials: 'same-origin'}).then(r => keep(new Request(u), r)).catch(() => null));
  }
  if (e.data === 'forget') { caches.delete(PAGES); }
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== 'GET') return;
  if (url.pathname.startsWith('/travel/app/')) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
    return;
  }
  if (url.pathname.startsWith('/travel/m/')) {
    e.respondWith(fetch(e.request).then(r => keep(e.request, r)).catch(() =>
      caches.open(PAGES).then(c => c.match(url.pathname + url.search).then(r =>
        r || c.match(url.pathname)).then(r => r || offline()))));
  }
});
function offline() {
  return new Response(
    '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<body style="margin:0;font-family:system-ui,sans-serif;background:#F3F5F6;color:#1D2B31;' +
    'display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;padding:24px">' +
    '<div><p style="font-size:22px;margin:0 0 8px">No signal</p>' +
    '<p style="color:#5B6B72;margin:0">This page has not been opened on this phone yet.</p>' +
    '<p style="margin:20px 0 0"><a href="/travel/m/passes/" style="color:#0F7480">Your boarding passes work offline</a></p></div>',
    {headers: {'Content-Type': 'text/html; charset=utf-8'}});
}
""" % {'v': SW_VERSION}
    resp = HttpResponse(body, content_type='application/javascript')
    resp['Service-Worker-Allowed'] = '/travel/m/'
    resp['Cache-Control'] = 'no-cache'
    return resp


def asset(request, name):
    if name not in ASSET_TYPES:
        raise Http404
    path = os.path.join(ASSETS, name)
    if not os.path.isfile(path):
        raise Http404
    with open(path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=ASSET_TYPES[name])
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp
