# -*- coding: utf-8 -*-
"""travel/views_inbox.py - TR-2, 15 Nov 2026. Travel, stage 2: the emails.

    inbound      Cloudflare's Worker posts each email here (no login: a
                 shared key, TRAVEL_INBOUND_KEY, set by Demetri on Railway
                 and in the Worker - never written anywhere else)
    check        To check: what was read, waiting for its person
    forwarding   where to forward to, and from which addresses
    trip_merge   merge another trip into this one - preview first, and
                 the other trip's owner asked when it is not yours
"""
import hmac
import os

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import inbound, inbox
from .models import (BookingChange, BookingFile, CheckItem,
                     InboundEmail, JoinRequest, TravelAddress, Trip,
                     trips_for)
from .views import ICONS, eur, shape, span, travel_view


def name_of(u):
    return (u.get_full_name() or u.username) if u else 'someone'


# ---------------------------------------------------------------- inbound
@csrf_exempt
def inbound_view(request):
    """The one door for email. Answers fast; reading happens after."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    key = os.environ.get('TRAVEL_INBOUND_KEY', '')
    given = request.headers.get('X-Travel-Key', '')
    if not key:
        return JsonResponse({'ok': False, 'error': 'not configured'},
                            status=503)
    if not hmac.compare_digest(key.encode(), given.encode()):
        return JsonResponse({'ok': False, 'error': 'key'}, status=401)
    raw = request.read(inbound.MAX_RAW + 1)
    if len(raw) > inbound.MAX_RAW:
        return JsonResponse({'ok': False, 'error': 'too big'}, status=413)
    if not raw.strip():
        return JsonResponse({'ok': False, 'error': 'empty'}, status=400)
    e, created = inbox.receive(raw, request.headers.get('X-Envelope-From',
                                                        ''))
    if created and e.state == 'new':
        inbox.kick()
    return JsonResponse({'ok': True, 'state': e.state,
                         'duplicate': not created})


# --------------------------------------------------------------- to check
LABELS = {
    'new': 'New booking',
    'maybe': 'Looks like one you have',
    'update': 'Change to a booking',
    'join': 'Belongs with someone else\'s trip',
    'gmail': 'Gmail forwarding',
    'none': 'No booking found',
    'failed': 'Could not be read',
}


def show(item):
    d = item.data or {}
    item.d = d
    item.label = LABELS.get(item.what, item.what)
    item.icon = ICONS.get(d.get('kind') or 'other', ICONS['other'])
    item.route = ' → '.join(x for x in (d.get('from_place'),
                                         d.get('to_place')) if x)
    try:
        from decimal import Decimal
        a = Decimal(d['amount']) if d.get('amount') else None
    except Exception:                                   # noqa: BLE001
        a = None
    item.cost = '' if a is None else (
        eur(a) if (d.get('currency') or 'EUR') == 'EUR' else
        '%s %s' % ('{:,.2f}'.format(a), d.get('currency')))
    item.suggested_name = inbox.trip_name(d) if d.get('kind') else ''
    return item


def my_requests(user):
    """Requests waiting for this person's yes or no."""
    out = []
    for r in JoinRequest.objects.filter(state='open').select_related(
            'trip__owner', 'from_trip__owner', 'by', 'item'):
        if r.asks.pk == user.pk:
            r.title = (r.item.data or {}).get('title') if r.item else ''
            out.append(r)
    return out


@travel_view
def check(request):
    inbox.kick()
    me = request.user
    items = [show(i) for i in CheckItem.objects.filter(
        user=me, state__in=('open', 'asked')).select_related(
        'booking', 'trip', 'other_trip__owner')]
    since = timezone.now() - timezone.timedelta(days=14)
    done = [show(i) for i in CheckItem.objects.filter(
        user=me, state='done', created_at__gte=since).select_related(
        'booking', 'trip')[:20]]
    waiting = InboundEmail.objects.filter(user=me, state__in=(
        'new', 'reading')).count()
    trips = list(trips_for(me))
    for t in trips:
        t.start, t.end = span(t, list(t.bookings.all()))
    return render(request, 'travel/check.html', {
        'items': items, 'done': done, 'waiting': waiting,
        'trips': trips, 'requests': my_requests(me),
        'address': inbox.inbox_address()})


def _item(request, item_id, states=('open',)):
    return get_object_or_404(CheckItem, pk=item_id, user=request.user,
                             state__in=states)


def _finish(item, state='done', note=None):
    item.state = state
    if note is not None:
        item.note = note[:255]
    item.save()
    inbox.tidy_files(item.email)


@travel_view
@require_POST
def check_add(request, item_id):
    """Add a new booking: onto a trip you pick, or a new trip."""
    item = _item(request, item_id)
    if item.what not in ('new', 'maybe', 'join'):
        raise Http404
    pick = request.POST.get('trip') or ''
    if pick == 'new':
        name = (request.POST.get('name') or '').strip()[:120] or \
            inbox.trip_name(item.data)
        # No dates on the new trip: they follow its bookings.
        t = Trip.objects.create(owner=request.user, name=name,
                                countries=(item.data.get('country') or
                                           '')[:200])
    else:
        t = get_object_or_404(trips_for(request.user), pk=pick or 0)
    with transaction.atomic():
        b = inbox.create(t, item.data, request.user, item.email,
                         inbox.files_of(item))
        item.booking, item.trip = b, t
        _finish(item, note='Added to %s' % t.name)
    messages.success(request, '%s added to %s.' % (b.title, t.name))
    return redirect('travel:check')


@travel_view
@require_POST
def check_merge(request, item_id):
    """It IS the booking you have: the email's details go onto it."""
    item = _item(request, item_id)
    if item.what not in ('maybe', 'update') or not item.booking or \
            not item.booking.trip.can_see(request.user):
        raise Http404
    with transaction.atomic():
        e = item.email or InboundEmail(subject=item.data.get('subject', ''))
        changed = inbox.apply(item.booking, item.data, request.user, e,
                              inbox.files_of(item))
        _finish(item, note=('Updated: ' + ', '.join(changed)) if changed
                else 'Already up to date')
    messages.success(request, '%s updated.' % item.booking.title)
    return redirect('travel:check')


@travel_view
@require_POST
def check_dismiss(request, item_id):
    item = _item(request, item_id)
    _finish(item, state='dismissed')
    messages.success(request, 'Dismissed.')
    return redirect('travel:check')


@travel_view
@require_POST
def check_ask(request, item_id):
    """Ask the owner of the other trip to let you join it with this."""
    item = _item(request, item_id)
    t = item.other_trip
    if item.what != 'join' or not t:
        raise Http404
    if t.can_see(request.user):
        # Already shared with you since it was read: no need to ask.
        return check_add_to(request, item, t)
    JoinRequest.objects.get_or_create(trip=t, by=request.user, item=item,
                                      state='open')
    item.state = 'asked'
    item.note = 'Asked %s' % name_of(t.owner)
    item.save()
    messages.success(request, 'Asked %s. It stays here until they answer.'
                     % name_of(t.owner))
    return redirect('travel:check')


def check_add_to(request, item, t):
    with transaction.atomic():
        pool = list(t.bookings.all())
        same, _ = inbox.same_booking(item.data, pool)
        if same:
            e = item.email or InboundEmail(subject=item.data.get('subject',
                                                                 ''))
            inbox.apply(same, item.data, item.user, e, inbox.files_of(item))
            b = same
        else:
            b = inbox.create(t, item.data, item.user, item.email,
                             inbox.files_of(item))
        item.booking, item.trip = b, t
        _finish(item, note='Added to %s' % t.name)
    messages.success(request, '%s added to %s.' % (b.title, t.name))
    return redirect('travel:check')


@travel_view
@require_POST
def answer(request, request_id):
    """The owner's yes or no."""
    r = get_object_or_404(JoinRequest.objects.select_related(
        'trip', 'from_trip', 'by', 'item'), pk=request_id, state='open')
    if r.asks.pk != request.user.pk:
        raise Http404
    yes = request.POST.get('answer') == 'yes'
    r.state = 'yes' if yes else 'no'
    r.answered_at = timezone.now()
    with transaction.atomic():
        r.save()
        if r.from_trip_id:
            if yes:
                merge(r.trip, r.from_trip, request.user)
                messages.success(request, 'Merged into %s.' % r.trip.name)
            else:
                messages.success(request, 'Kept apart.')
        elif r.item:
            item = r.item
            if yes:
                r.trip.shared_with.add(r.by)
                pool = list(r.trip.bookings.all())
                same, _ = inbox.same_booking(item.data, pool)
                e = item.email or InboundEmail(
                    subject=item.data.get('subject', ''))
                if same:
                    inbox.apply(same, item.data, r.by, e,
                                inbox.files_of(item))
                    b = same
                else:
                    b = inbox.create(r.trip, item.data, r.by, item.email,
                                     inbox.files_of(item))
                item.booking, item.trip = b, r.trip
                _finish(item, note='%s said yes: added to %s' % (
                    name_of(request.user), r.trip.name))
                messages.success(request, '%s is on %s now, with %s.' % (
                    name_of(r.by), r.trip.name, b.title))
            else:
                item.state, item.what, item.other_trip = 'open', 'new', None
                item.note = ('%s kept the trip to themselves - add it to '
                             'a trip of your own.' % name_of(request.user)
                             )[:255]
                item.save()
                messages.success(request, 'Said no. %s can keep it as '
                                 'their own trip.' % name_of(r.by))
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/travel/'):
        return redirect(nxt)
    return redirect('travel:check')


# ------------------------------------------------------------------ merge
def merge(target, source, by):
    """Every booking of `source` onto `target`; the same booking from two
    people becomes one (the target's, with the other's tickets added);
    who added each booking is kept; everyone on either trip is on the
    merged one. Then `source` goes."""
    moved = joined = 0
    for b in list(source.bookings.all()):
        pool = list(target.bookings.all())
        same, _ = inbox.same_booking({'reference': b.reference,
                                      'segment': b.segment,
                                      'start_date': b.start_date.isoformat()
                                      if b.start_date else ''}, pool)
        if same:
            BookingFile.objects.filter(booking=b).exclude(
                name__in=list(same.files.values_list('name', flat=True))
            ).update(booking=same)
            for u in b.travellers.all():
                same.travellers.add(u)
            BookingChange.objects.create(
                booking=same, by=by, source='edit',
                note=('Merged with the same booking from %s'
                      % source.name)[:200], changes=[])
            for f in BookingFile.objects.filter(booking=b):
                f.delete()          # the row only; the file stays shared
            b.delete()
            joined += 1
        else:
            b.trip = target
            b.save(update_fields=['trip'])
            moved += 1
    people = set(source.shared_with.values_list('pk', flat=True))
    people.add(source.owner_id)
    people.discard(target.owner_id)
    for pk in people:
        target.shared_with.add(pk)
    if source.notes:
        target.notes = (target.notes + '\n\n' + source.notes).strip()
    if source.countries:
        have = target.country_list
        for c in source.country_list:
            if c not in have:
                have.append(c)
        target.countries = ', '.join(have)[:200]
    target.save()
    source.delete()
    return moved, joined


@travel_view
def trip_merge(request, trip_id):
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    if t.owner_id != request.user.id:
        raise Http404
    others = [o for o in trips_for(request.user).exclude(pk=t.pk)]
    for o in others:
        o.start, o.end = span(o, list(o.bookings.all()))
    src = None
    preview = []
    pick = request.GET.get('from') or request.POST.get('from')
    if pick:
        src = next((o for o in others if str(o.pk) == pick), None)
    if src:
        pool = list(t.bookings.all())
        for b in src.bookings.all():
            same, _ = inbox.same_booking({
                'reference': b.reference, 'segment': b.segment,
                'start_date': b.start_date.isoformat() if b.start_date
                else ''}, pool)
            shape(b)
            b.same = same
            preview.append(b)
    if request.method == 'POST' and src:
        if src.owner_id == request.user.id:
            with transaction.atomic():
                moved, joined = merge(t, src, request.user)
            messages.success(request, 'Merged: %d moved, %d were already '
                             'here.' % (moved, joined))
            return redirect('travel:trip', trip_id=t.pk)
        JoinRequest.objects.get_or_create(trip=t, by=request.user,
                                          from_trip=src, state='open')
        messages.success(request, '%s is %s\'s trip, so they have been '
                         'asked. Nothing moves until they say yes.'
                         % (src.name, name_of(src.owner)))
        return redirect('travel:trip', trip_id=t.pk)
    return render(request, 'travel/merge.html', {
        'trip': t, 'others': others, 'src': src, 'preview': preview})


# -------------------------------------------------------------- forwarding
@travel_view
def forwarding(request):
    me = request.user
    if request.method == 'POST':
        if request.POST.get('remove'):
            TravelAddress.objects.filter(user=me,
                                         pk=request.POST['remove']).delete()
            messages.success(request, 'Address removed.')
            return redirect('travel:forwarding')
        a = inbound.plain((request.POST.get('email') or '').strip())
        if not a or not inbound.ADDR.fullmatch(a):
            messages.error(request, 'That is not an email address.')
        elif a == inbound.plain(me.email or ''):
            messages.error(request, 'That is already your login email.')
        elif User.objects.filter(email__iexact=a).exclude(pk=me.pk).exists() \
                or TravelAddress.objects.filter(email__iexact=a).exists():
            messages.error(request, 'That address already belongs to '
                           'someone in Alivente.')
        else:
            TravelAddress.objects.create(user=me, email=a)
            messages.success(request, 'Added. Emails forwarded from %s '
                             'now come to you.' % a)
        return redirect('travel:forwarding')
    gmail = [show(i) for i in CheckItem.objects.filter(
        user=me, what='gmail', state='open')]
    recent = InboundEmail.objects.filter(user=me)[:8]
    return render(request, 'travel/forwarding.html', {
        'address': inbox.inbox_address(),
        'login': me.email, 'extra': TravelAddress.objects.filter(user=me),
        'gmail': gmail, 'recent': recent,
        'ready': bool(os.environ.get('TRAVEL_INBOUND_KEY'))})
