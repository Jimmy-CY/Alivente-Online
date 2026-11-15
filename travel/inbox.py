# -*- coding: utf-8 -*-
"""travel/inbox.py - TR-2, 15 Nov 2026. From a forwarded email to a booking.

    receive()   the raw email arrives: whose is it, have we had it before?
    process()   Claude reads it; each booking in it is routed
    route()     ... to an update of a booking you already have, or to your
                To check list - new, looks like one you have, or belongs
                with someone else's trip

DEMETRI'S RULES, 15 Nov 2026, each a line below:
  - the same email twice is taken once (Message-ID);
  - the same reference is an UPDATE: the latest email wins, and every
    change goes in the booking's Changes trail;
  - a boarding pass or receipt attaches to its booking;
  - a cancellation marks the booking Cancelled - never deletes it;
  - no reference, but the same day, kind and place: "Merge or keep both?";
  - two family members' emails for one trip are matched within the
    household only, and THE OWNER IS ALWAYS ASKED before anyone joins.

Reading happens off the request: the inbound view answers Cloudflare at
once and kick() reads in a background thread. Anything a restart
interrupts is picked up the next time someone opens Travel, or by
`python manage.py travel_inbox`.
"""
import datetime as dt
import logging
import os
import re
import threading
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from . import extract, fx, inbound
from .models import (Booking, BookingChange, BookingFile, CheckItem,
                     InboundEmail, InboundFile, TravelAddress, Trip,
                     trips_for)

logger = logging.getLogger(__name__)

# Tests and the management command read in the same thread.
SYNC = False
STALE = dt.timedelta(minutes=10)
TRIES = 3
NEAR = dt.timedelta(days=3)


# ------------------------------------------------------------- the people
def household():
    """Everyone with Travel. Matching never looks beyond them."""
    q = Q(user_permissions__codename='can_access_travel') | \
        Q(groups__permissions__codename='can_access_travel') | \
        Q(is_superuser=True)
    return User.objects.filter(q, is_active=True).distinct()


def address_book():
    """address -> user: each person's login email and the addresses they
    added under Forwarding."""
    book = {}
    for u in household():
        if u.email:
            book[inbound.plain(u.email)] = u
    for a in TravelAddress.objects.select_related('user'):
        if a.user.is_active:
            book.setdefault(inbound.plain(a.email), a.user)
    return book


def whose(msg, envelope_from=''):
    book = address_book()
    for a in inbound.candidates(msg, envelope_from):
        if a in book:
            return book[a], a
    return None, ''


# --------------------------------------------------------------- receive
def receive(raw, envelope_from=''):
    """Store one raw email. Returns (InboundEmail, created)."""
    msg = inbound.parse(raw)
    mid = inbound.message_id(msg, raw)
    old = InboundEmail.objects.filter(message_id=mid).first()
    if old:
        return old, False
    subject = str(msg.get('Subject') or '')[:255]
    body = ''
    gm = None
    if inbound.plain(str(msg.get('From') or '')).endswith(
            inbound.GMAIL_FROM) or inbound.GMAIL_FROM in str(
            msg.get('From') or '').lower():
        info = inbound.read(raw)
        body = info['body']
        gm = inbound.gmail_confirmation(msg, body)
    if gm:
        user = address_book().get(gm['who'] or '')
        e = InboundEmail.objects.create(
            message_id=mid, user=user, sender=inbound.GMAIL_FROM,
            subject=subject, sent=inbound.sent_at(msg),
            state='done' if user else 'ignored',
            note='Gmail forwarding confirmation for %s' % (gm['who'] or '?'))
        if user:
            CheckItem.objects.create(user=user, email=e, what='gmail',
                                     data=gm)
        return e, True
    user, addr = whose(msg, envelope_from)
    e = InboundEmail(message_id=mid, user=user, sender=addr or
                     inbound.plain(envelope_from)[:190], subject=subject,
                     sent=inbound.sent_at(msg))
    if not user:
        # NOT FROM ANYONE IN TRAVEL. Nothing of it is kept but the line in
        # the log - not the text, not the attachments.
        e.state = 'ignored'
        e.note = 'Not from anyone with Travel'
        e.save()
        return e, True
    e.trusted = inbound.trusted(msg, addr)
    e.raw.save('email.eml', ContentFile(raw), save=False)
    e.save()
    return e, True


# --------------------------------------------------------------- process
def claim(e):
    """Take one email to read, so two threads never read it twice."""
    now = timezone.now()
    n = InboundEmail.objects.filter(pk=e.pk).filter(
        Q(state='new') | Q(state='reading', started__lt=now - STALE)
    ).update(state='reading', started=now, tries=e.tries + 1)
    return n == 1


def own_phones(user):
    out = []
    prof = getattr(user, 'profile', None)
    for f in ('phone', 'mobile', 'phone_number', 'mobile_phone'):
        v = getattr(prof, f, '') if prof else ''
        if v:
            out.append(str(v))
    return out


def forget_raw(e):
    if e.raw:
        try:
            e.raw.delete(save=False)
        except Exception:                               # noqa: BLE001
            pass
        e.raw = ''


def process(e, client=None):
    """Read one email and route every booking in it. True if read."""
    if not claim(e):
        return False
    e.refresh_from_db()
    try:
        with e.raw.open('rb') as fh:
            raw = fh.read()
    except Exception:                                   # noqa: BLE001
        e.state, e.note = 'failed', 'The stored email is missing.'
        e.save()
        CheckItem.objects.create(user=e.user, email=e, what='failed',
                                 data={'subject': e.subject}, note=e.note)
        return False
    info = inbound.read(raw)
    try:
        answer = extract.call(info, client=client)
    except extract.ExtractError as err:
        e.note = str(err)[:255]
        if e.tries >= TRIES:
            e.state = 'failed'
            forget_raw(e)
            CheckItem.objects.create(user=e.user, email=e, what='failed',
                                     data={'subject': e.subject},
                                     note=e.note)
        else:
            e.state = 'new'
        e.save()
        return False
    items = extract.clean(answer, own_phones(e.user))
    files = []
    for f in info['files']:
        files.append(InboundFile.objects.create(
            email=e, name=f['name'][:160],
            file=ContentFile(f['data'], name=f['name'])))
    code = info.get('pass')
    wallet = (info.get('wallet') or [''])[0]
    with transaction.atomic():
        if not items or answer.get('is_travel') is False:
            CheckItem.objects.create(user=e.user, email=e, what='none',
                                     data={'subject': e.subject})
        flights = [i for i in items if i['kind'] == 'flight']
        for it in items:
            if code and it['kind'] == 'flight' and (
                    it['boarding_pass'] or len(flights) == 1):
                it['pass_code'] = code['text'][:2000]
                it['pass_format'] = code['format'][:12]
                if wallet:
                    it['wallet_link'] = wallet[:1000]
            route(e, it, files)
        forget_raw(e)
        e.state = 'done'
        e.note = '%d booking%s' % (len(items), '' if len(items) == 1 else 's')
        e.save()
    return True


def pending():
    now = timezone.now()
    return InboundEmail.objects.filter(
        Q(state='new') | Q(state='reading', started__lt=now - STALE))


def process_pending(limit=5, client=None):
    done = 0
    for e in list(pending()[:limit]):
        try:
            if process(e, client=client):
                done += 1
        except Exception:                               # noqa: BLE001
            logger.exception('travel inbox: email %s', e.pk)
            InboundEmail.objects.filter(pk=e.pk, state='reading').update(
                state='new')
    return done


_lock = threading.Lock()


def kick():
    """Read what is waiting - now, in the background."""
    if SYNC:
        return process_pending()
    if not pending().exists():
        return 0

    def run():
        if not _lock.acquire(blocking=False):
            return
        try:
            process_pending(limit=10)
        finally:
            _lock.release()
            close_old_connections()
    threading.Thread(target=run, daemon=True).start()
    return None


# ----------------------------------------------------------------- route
def norm_ref(v):
    return re.sub(r'[\s.\-/]', '', (v or '')).upper()


def norm_seg(v):
    return re.sub(r'[\s\-]', '', (v or '')).upper()


def words(*vals):
    w = set()
    for v in vals:
        w.update(x for x in re.findall(r'[a-z0-9]{3,}', (v or '').lower())
                 if x not in ('the', 'and', 'hotel', 'airport', 'airlines',
                              'booking', 'com'))
    return w


def same_booking(item, pool):
    """The booking this item is about, from its reference (and segment,
    when one reference holds several). (booking, 'ref') or (None, '')."""
    ref = norm_ref(item.get('reference'))
    if not ref:
        return None, ''
    same = [b for b in pool if norm_ref(b.reference) == ref]
    if not same:
        return None, ''
    seg = norm_seg(item.get('segment'))
    if seg:
        hit = [b for b in same if norm_seg(b.segment) == seg]
        if hit:
            return hit[0], 'ref'
        if any(b.segment for b in same):
            return None, 'sibling'
    if len(same) == 1:
        return same[0], 'ref'
    day = item.get('start_date')
    hit = [b for b in same if b.start_date and b.start_date.isoformat() ==
           day]
    return (hit or same)[0], 'ref'


def looks_like(item, pool):
    """No reference to go on, but the same kind on the same day at the
    same place - Demetri: "Merge or keep both?"."""
    day = item.get('start_date')
    if not day:
        return None
    mine = words(item.get('title'), item.get('provider'),
                 item.get('to_place'), item.get('address'))
    for b in pool:
        if b.kind != item.get('kind') or not b.start_date or \
                b.start_date.isoformat() != day or b.status == 'cancelled':
            continue
        theirs = words(b.title, b.provider, b.to_place, b.address)
        if not mine or not theirs or mine & theirs:
            return b
    return None


def trip_span(t):
    from .views import span
    return span(t, list(t.bookings.all()))


def overlaps(t, day):
    if not day:
        return False
    s, e = trip_span(t)
    if not s:
        return False
    d = dt.date.fromisoformat(day)
    return s - NEAR <= d <= (e or s) + NEAR


def same_place(t, item):
    want = words(item.get('city'), item.get('country'), item.get('to_place'))
    have = words(t.name, t.countries,
                 *[x for b in t.bookings.all() for x in
                   (b.to_place, b.address, b.title)])
    return bool(want & have)


def suggest_trip(user, item):
    """Which of your trips this belongs on: the one holding its sibling
    parts, else one whose dates take it in."""
    pool = list(trips_for(user))
    for t in pool:
        if overlaps(t, item.get('start_date')):
            return t
    return None


def household_trip(user, item):
    """Someone else's trip - not shared with you - that this belongs with:
    the same reference, or overlapping dates at the same place."""
    mine = set(trips_for(user).values_list('pk', flat=True))
    others = Trip.objects.filter(owner__in=household()).exclude(
        pk__in=mine).exclude(owner=user).prefetch_related('bookings')
    ref = norm_ref(item.get('reference'))
    if ref:
        for t in others:
            if any(norm_ref(b.reference) == ref for b in t.bookings.all()):
                return t
    for t in others:
        if overlaps(t, item.get('start_date')) and same_place(t, item):
            return t
    return None


def route(e, item, files):
    """One booking from one email, to wherever it belongs."""
    user = e.user
    pool = list(Booking.objects.filter(trip__in=trips_for(user)))
    b, how = same_booking(item, pool)
    data = dict(item, subject=e.subject, sent=e.sent.isoformat()
                if e.sent else '', files=[f.pk for f in files])
    if b:
        if e.trusted:
            changed = apply(b, item, user, e, files)
            if item['status'] == 'cancelled':
                note = 'Marked cancelled'
            elif changed:
                note = 'Updated: ' + ', '.join(changed)
            else:
                note = 'Already up to date'
            return CheckItem.objects.create(
                user=user, email=e, what='update', data=data, booking=b,
                trip=b.trip, state='done', note=note[:255])
        return CheckItem.objects.create(
            user=user, email=e, what='update', data=data, booking=b,
            trip=b.trip, note='The sender could not be confirmed, so this '
                              'waits for you.')
    if item['status'] == 'cancelled':
        return CheckItem.objects.create(
            user=user, email=e, what='none', data=data,
            note='A cancellation for a booking that is not on your trips.')
    sibling = None
    if how == 'sibling':
        ref = norm_ref(item.get('reference'))
        sibling = next((x.trip for x in pool if norm_ref(x.reference) == ref),
                       None)
    if not sibling:
        like = looks_like(item, pool)
        if like:
            return CheckItem.objects.create(
                user=user, email=e, what='maybe', data=data, booking=like,
                trip=like.trip)
        other = household_trip(user, item)
        if other:
            return CheckItem.objects.create(
                user=user, email=e, what='join', data=data,
                trip=suggest_trip(user, item), other_trip=other)
    return CheckItem.objects.create(
        user=user, email=e, what='new', data=data,
        trip=sibling or suggest_trip(user, item))


# ----------------------------------------------------------------- apply
FIELDS = ['kind', 'title', 'provider', 'reference', 'segment', 'start_date',
          'start_time', 'end_date', 'end_time', 'from_place', 'to_place',
          'address', 'phone', 'link', 'details', 'pay_by', 'cancel_until']


def _val(f, v):
    if v in (None, ''):
        return None
    if f in ('start_date', 'end_date', 'pay_by', 'cancel_until'):
        return dt.date.fromisoformat(v)
    if f in ('start_time', 'end_time'):
        return dt.time.fromisoformat(v)
    return v


def fill(b, item, sent=None, fresh=False):
    """Copy an email's booking onto b. A later email wins field by field;
    what it leaves out is kept. `fresh` for a new booking."""
    for f in FIELDS:
        v = _val(f, item.get(f))
        if v is not None:
            setattr(b, f, v)
    cur = (item.get('currency') or 'EUR').upper()
    amt = item.get('amount')
    if amt is not None:
        if cur in fx.CURRENCIES:
            if Decimal(amt) != b.amount or cur != b.currency:
                b.amount, b.currency = Decimal(amt), cur
                if not b.eur_typed:
                    b.amount_eur = None
                    b.fx_date = sent.date() if sent else None
        else:
            line = 'Price: %s %s' % (amt, cur)
            if line not in (b.details or ''):
                b.details = ((b.details or '') + '\n' + line).strip()
    if item.get('paid'):
        b.paid = item['paid']
        b.paid_amount = Decimal(item['paid_amount']) if \
            item['paid'] == 'part' and item.get('paid_amount') else None
    for f in ('pass_code', 'pass_format', 'wallet_link'):
        if item.get(f):
            setattr(b, f, item[f])
    if item.get('status') == 'cancelled':
        b.status = 'cancelled'
    elif item.get('status') in ('confirmed', 'changed') and not fresh:
        b.status = 'ok'
    if b.link and not b.link.startswith('https://'):
        b.link = ''
    if not b.eur_typed and b.amount is not None and b.amount_eur is None:
        fx.convert(b)
    return b


def travellers(b, item):
    """Names from the email, matched to people with Travel; the rest kept
    as written."""
    names = item.get('travellers') or []
    if not names:
        return
    people = list(household())
    left = []
    for n in names:
        key = ' '.join(re.findall(r'[a-z]+', n.lower()))
        hit = None
        for u in people:
            full = ' '.join(re.findall(r'[a-z]+', ('%s %s' % (
                u.first_name, u.last_name)).lower()))
            if full and (full == key or (key.startswith(full)) or
                         set(full.split()) <= set(key.split())):
                hit = u
                break
        if hit:
            b.travellers.add(hit)
        else:
            left.append(n.title() if n.isupper() else n)
    if left:
        have = [x.strip() for x in (b.traveller_names or '').split(',')
                if x.strip()]
        for n in left:
            if n not in have:
                have.append(n)
        b.traveller_names = ', '.join(have)[:255]
        b.save(update_fields=['traveller_names'])


def attach(b, files, user):
    """The email's tickets and passes onto the booking - the same stored
    file, once per name."""
    have = set(b.files.values_list('name', flat=True))
    for f in files:
        if f.name in have:
            continue
        BookingFile.objects.create(booking=b, file=f.file.name, name=f.name,
                                   uploaded_by=user)
        have.add(f.name)


def apply(b, item, user, e, files):
    """A later email about a booking already on a trip. Returns the
    labels of what changed."""
    from .views import diff, snapshot
    before = snapshot(b)
    was_status = b.status
    older = bool(e.sent and b.email_date and e.sent < b.email_date)
    if not older:
        fill(b, item, e.sent)
        if e.sent:
            b.email_date = e.sent
    elif item.get('status') == 'cancelled':
        b.status = 'cancelled'
    b.save()
    attach(b, files, user)
    travellers(b, item)
    changes = diff(before, b)
    if was_status != b.status:
        changes.append({'label': 'Status',
                        'old': dict(Booking.STATUSES)[was_status],
                        'new': dict(Booking.STATUSES)[b.status]})
    note = ('From an email: %s' % e.subject)[:200]
    if older:
        note = ('An older email, not applied: %s' % e.subject)[:200]
    if changes or files or older:
        BookingChange.objects.create(booking=b, by=user, source='email',
                                     note=note, changes=changes)
    return [c['label'] for c in changes]


def create(trip, item, user, e=None, files=()):
    """A new booking from an email, on the trip the person chose."""
    b = Booking(trip=trip, added_by=user, source='email')
    sent = None
    if e is not None and e.sent:
        sent = e.sent
    elif item.get('sent'):
        try:
            sent = dt.datetime.fromisoformat(item['sent'])
        except ValueError:
            sent = None
    fill(b, item, sent, fresh=True)
    b.email_date = sent
    if not b.paid:
        b.paid = 'due'
    b.save()
    attach(b, files, user)
    travellers(b, item)
    return b


def files_of(item):
    ids = (item.data or {}).get('files') or []
    return list(InboundFile.objects.filter(pk__in=ids))


def trip_name(item):
    """A name for a new trip: the place and the month."""
    d = item.get('start_date')
    place = item.get('city') or item.get('country') or \
        (item.get('to_place') or '').split('(')[0].strip() or 'New trip'
    if d:
        return '%s %s' % (place, dt.date.fromisoformat(d).strftime('%b %Y'))
    return place


def tidy_files(e):
    """When nothing open is left from an email, its files that no booking
    took are deleted."""
    if e is None or CheckItem.objects.filter(email=e, state__in=(
            'open', 'asked')).exists():
        return
    used = set(BookingFile.objects.values_list('file', flat=True))
    for f in e.files.all():
        if f.file.name not in used:
            try:
                f.file.delete(save=False)
            except Exception:                           # noqa: BLE001
                pass
            f.delete()


def open_count(user):
    """How many wait in this person's To check."""
    return CheckItem.objects.filter(user=user, state='open').count()


def inbox_address():
    return os.environ.get('TRAVEL_INBOX_ADDRESS', 'trips@alivente.online')
