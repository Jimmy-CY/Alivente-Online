# -*- coding: utf-8 -*-
"""apply_travel_two.py - round TR-2, 15 Nov 2026.

RELEASE 83 - TRAVEL, STAGE 2: BOOKINGS READ FROM FORWARDED EMAILS.

    - Forward a booking email to the trips address; Cloudflare's Email
      Worker posts it to /travel/inbound/ (a shared key, TRAVEL_INBOUND_KEY,
      set on Railway and in the Worker).
    - Whose it is: the address it was forwarded from (login email, or one
      added under Travel -> Forwarding). Unknown senders ignored, not kept.
    - Claude reads it (travel/extract.py, TRAVEL_AI_MODEL); each booking
      goes to To check, or - a later email about a booking you have -
      updates it: latest wins, Changes trail, boarding passes attach,
      cancellations mark Cancelled.
    - Two people, one trip: Ask to join / Merge - the owner always asked.
    - Who's travelling on each booking; a booking can be Cancelled.

New files ship beside this patcher. Stands on Release 82. Idempotent.
Edits backed up to .bak_travel2.
MIGRATION: travel 0002 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_travel2'
MARK = 'TR-2, 15 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/inbound.py',
    'travel/extract.py',
    'travel/inbox.py',
    'travel/views_inbox.py',
    'travel/migrations/0002_email_reading.py',
    'travel/management/__init__.py',
    'travel/management/commands/__init__.py',
    'travel/management/commands/travel_inbox.py',
    'travel/templates/travel/_requests.html',
    'travel/templates/travel/check.html',
    'travel/templates/travel/forwarding.html',
    'travel/templates/travel/merge.html',
    'test_travel_two.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_gift_tidy.py',
    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    'test_travel_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_gift_tidy.py',
    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    'test_travel_one.py',
    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - bookings read from
    # forwarded emails.
    'test_travel_two.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    '.bak_travel1',
]

''',
         r'''    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    '.bak_travel1',
    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - emails.
    '.bak_travel2',
]

'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            # pages themselves are under wellness/ and keep their check.
            'wellness/app/',
            'media/',  # Media files
            'static/',  # Static files
''',
         r'''            # pages themselves are under wellness/ and keep their check.
            'wellness/app/',
            # TR-2, 15 Nov 2026 - TRAVEL'S EMAIL DOOR. Cloudflare's Email
            # Worker posts each forwarded booking email here, with no
            # session - it is a machine, not a person. The shared key in
            # the X-Travel-Key header is the credential and the view checks
            # it; nothing is ever served from here. Only this one path:
            # every other page under travel/ keeps its permission check.
            'travel/inbound/',
            'media/',  # Media files
            'static/',  # Static files
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p>Coming next: bookings read straight from your forwarded emails, an itinerary and wish list, and a Travel app for your phone with your boarding passes.</p>
  </article>

''',
         r'''    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p>Coming next: a Travel app for your phone with your boarding passes, then an itinerary and wish list.</p>
  </article>

'''),
        (r'''    <p>The trip page lists bookings by day. Open one to see everything about it, with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>No duplicates.</strong> Add a booking whose reference is already on the trip and you are stopped, with a link to the one it matches &mdash; change that one, or choose <strong>Save it as a second booking</strong>. Every change to a booking is kept: open <strong>Changes</strong> on the booking to see what changed, when and by whom; the booking itself always shows the latest.</p>
  </article>
''',
         r'''    <p>The trip page lists bookings by day. Open one to see everything about it, with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>Who&rsquo;s travelling</strong>: tick the people on the trip the booking is for, and type anyone else&rsquo;s name. Bookings read from an email fill this in from the passenger and guest names.</p>
    <p>One reference with several flights (outward and back) is one booking per flight: put the flight number under <strong>Part</strong>. Tick <strong>Cancelled</strong> to keep a cancelled booking on the trip, struck through and left out of the costs.</p>
    <p><strong>No duplicates.</strong> Add a booking whose reference is already on the trip and you are stopped, with a link to the one it matches &mdash; change that one, or choose <strong>Save it as a second booking</strong>. Every change to a booking is kept: open <strong>Changes</strong> on the booking to see what changed, when and by whom; the booking itself always shows the latest.</p>
  </article>
'''),
        (r'''    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
</section>
''',
         r'''    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>

  <article data-tab-slug="tr-email"
           data-tab-name="Emails"
           data-tab-icon="fa-envelope">
    <h6><i class="fas fa-envelope"></i> Bookings from your emails</h6>
    <p><strong>Forward</strong> a booking email &mdash; a flight, hotel, car, train or ferry confirmation, a change, a cancellation, a boarding pass &mdash; to the trips address shown on <strong>Travel &rarr; Forwarding</strong>. Forward it as it is, with its attachments. It is read in a minute or so.</p>
    <p><strong>Whose it is</strong> is decided by the address it was forwarded from: your login email, or any address you add under <strong>Forwarding</strong>. An email from an address nobody has added is ignored and not kept. To forward automatically, set up a Gmail filter or an Outlook rule &mdash; Forwarding shows how. Gmail first sends a confirmation to the trips address: it appears in To check with its code and a <strong>Confirm in Gmail</strong> button.</p>
    <p><strong>To check</strong> lists what was read. A new booking waits there: choose the trip it goes on (the trip whose dates take it in is picked for you) or <strong>A new trip</strong>, then <strong>Add</strong>. The PDFs and passes from the email are attached to the booking.</p>
    <p><strong>The rules for a second email.</strong> The same email twice is taken once. A later email with the same booking reference updates that booking &mdash; the latest email wins, field by field, and every change is in the booking&rsquo;s <strong>Changes</strong>. A boarding pass attaches to its flight. A cancellation marks the booking <strong>Cancelled</strong>; it is never deleted. An older email arriving after a newer one changes nothing. With no reference to go on, a booking on the same day, of the same kind, at the same place asks <strong>Merge into it</strong> or <strong>Keep both</strong>. If the sender of an update could not be confirmed, it waits in To check instead of changing anything by itself.</p>
    <p><strong>What is never kept</strong>: PINs, card numbers or card digits, and your own email address or phone number. The email itself is deleted as soon as it has been read; only the booking details and the attachments stay.</p>
  </article>

  <article data-tab-slug="tr-join"
           data-tab-name="Joining &amp; Merging"
           data-tab-icon="fa-object-group">
    <h6><i class="fas fa-object-group"></i> Two people, one trip</h6>
    <p>When your email belongs with a trip someone else in the family made, and it is not shared with you, To check says so: <strong>Ask to join</strong>, or <strong>Keep as my own</strong>. The owner is always asked first &mdash; they see the request on Travel and on the trip, and choose <strong>Share the trip and add it</strong> or <strong>No</strong>. Until they answer, nothing changes. If the trip is already shared with you, the booking simply goes on it.</p>
    <p><strong>Merge</strong> (on a trip of yours) brings another trip&rsquo;s bookings onto it. Pick the trip and see a preview first: what moves across, and what is already there &mdash; the same booking from two people becomes one. Who added each booking is kept, and everyone on either trip is on the merged one. If the other trip is not yours, its owner is asked, and nothing moves until they say yes.</p>
  </article>
</section>
'''),
    ]),
    (os.path.join('test_ai_models.py'), [
        (r'''    # model as the daily line, changeable through GREETING_MODEL.
    'pages/views/celebration_gifts.py': 'the celebration greeting',
}

''',
         r'''    # model as the daily line, changeable through GREETING_MODEL.
    'pages/views/celebration_gifts.py': 'the celebration greeting',
    # TR-2, 15 Nov 2026 - the eighth: reading a forwarded booking email
    # (and its PDF tickets) into Travel bookings. Sonnet, as the recipe
    # importer, for reading documents; changeable through TRAVEL_AI_MODEL.
    'travel/extract.py': 'reading booking emails into Travel',
}

'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    cancel_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=10, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    cancel_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=10, default='manual')
    # TR-2, 15 Nov 2026 - read from emails. A cancellation marks a booking
    # Cancelled rather than deleting it (Demetri's rule); it stays on the
    # trip, struck through, and out of the totals.
    STATUSES = [('ok', 'Booked'), ('cancelled', 'Cancelled')]
    status = models.CharField(max_length=10, choices=STATUSES, default='ok')
    # One part of a booking that has several under one reference - a
    # flight number ("CY 326") or a leg ("LCA-ATH"). Two flights on one
    # booking reference are two bookings; this tells them apart.
    segment = models.CharField(max_length=40, blank=True, default='')
    # The Date of the latest email applied. An older email arriving later
    # (forwarded out of order) never overwrites what a newer one said.
    email_date = models.DateTimeField(null=True, blank=True)
    # A boarding pass: the barcode's own text (BCBP for a flight) and its
    # symbology, kept for the Travel phone app to draw; the airline's own
    # wallet link where the email had one.
    pass_code = models.TextField(blank=True, default='')
    pass_format = models.CharField(max_length=12, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    # WHO IS TRAVELLING (Demetri, 15 Nov). People with Travel, ticked; and
    # names from an email that matched nobody, kept as written.
    travellers = models.ManyToManyField(User, blank=True,
                                        related_name='travel_bookings')
    traveller_names = models.CharField(max_length=255, blank=True,
                                       default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''        db_table = 'travel_booking_changes'
        ordering = ['-when', '-id']
''',
         r'''        db_table = 'travel_booking_changes'
        ordering = ['-when', '-id']


# ==========================================================================
# TR-2, 15 Nov 2026 - STAGE 2: BOOKINGS READ FROM FORWARDED EMAILS.
#
# The road: a family member forwards a booking email to the trips address;
# Cloudflare hands it to the app (travel:inbound); the sender decides whose
# it is; Claude reads it; each booking in it becomes a CheckItem in that
# person's To check list - or, when it is a later email about a booking
# already on one of their trips, it updates that booking directly and the
# change trail says so.
# ==========================================================================
class TravelAddress(models.Model):
    """An email address someone forwards from, beyond their login email.
    An address belongs to one person only, and never to another user's
    login email."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='travel_addresses')
    email = models.EmailField(max_length=190, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_addresses'
        ordering = ['email']

    def __str__(self):
        return self.email


def inbox_path(instance, filename):
    base = os.path.basename(filename)[-120:] or 'file'
    return 'travel/inbox/%s/%s' % (uuid.uuid4().hex, base)


class InboundEmail(models.Model):
    STATES = [('new', 'Waiting to be read'), ('reading', 'Being read'),
              ('done', 'Read'), ('failed', 'Could not be read'),
              ('ignored', 'Ignored')]
    received = models.DateTimeField(auto_now_add=True)
    # Unique, so the same email forwarded twice is taken once. Hashed when
    # longer than the column.
    message_id = models.CharField(max_length=190, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')
    sender = models.CharField(max_length=190, blank=True, default='')
    subject = models.CharField(max_length=255, blank=True, default='')
    sent = models.DateTimeField(null=True, blank=True)
    # Cloudflare's own check of the sender (SPF / DKIM / DMARC). An email
    # that did not pass changes nothing by itself - every booking in it
    # waits in To check.
    trusted = models.BooleanField(default=False)
    state = models.CharField(max_length=8, choices=STATES, default='new')
    started = models.DateTimeField(null=True, blank=True)
    tries = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True, default='')
    # The email itself, only until it has been read. It can carry a PIN or
    # the last digits of a card, so it is deleted as soon as it is read.
    raw = models.FileField(upload_to=inbox_path, max_length=255, blank=True)

    class Meta:
        db_table = 'travel_inbound_emails'
        ordering = ['-received', '-id']

    def __str__(self):
        return self.subject or self.message_id


class InboundFile(models.Model):
    """A ticket, confirmation or pass that came attached to an email. It
    becomes a BookingFile (the same stored file) when its booking is
    added or updated."""
    email = models.ForeignKey(InboundEmail, on_delete=models.CASCADE,
                              related_name='files')
    file = models.FileField(upload_to=inbox_path, max_length=255)
    name = models.CharField(max_length=160)

    class Meta:
        db_table = 'travel_inbound_files'
        ordering = ['id']


class CheckItem(models.Model):
    """One booking read from an email, waiting for its person in To check.

    what:  new     - a booking not on any of your trips
           maybe   - no reference to go on, but it looks like one you have
           update  - a later email about a booking you have (held only
                     when the sender could not be confirmed)
           join    - it belongs with someone else's trip you are not on
           gmail   - Gmail asks to confirm forwarding to the trips address
           none    - the email had no booking in it
           failed  - the email could not be read
    """
    WHATS = ['new', 'maybe', 'update', 'join', 'gmail', 'none', 'failed']
    STATES = [('open', 'To check'), ('asked', 'Asked the owner'),
              ('done', 'Done'), ('dismissed', 'Dismissed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='travel_checks')
    email = models.ForeignKey(InboundEmail, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='items')
    what = models.CharField(max_length=8, default='new')
    data = models.JSONField(default=dict)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='+')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')
    other_trip = models.ForeignKey(Trip, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    state = models.CharField(max_length=10, choices=STATES, default='open')
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_check_items'
        ordering = ['-created_at', '-id']


class JoinRequest(models.Model):
    """THE OWNER IS ALWAYS ASKED (Demetri, 15 Nov: "An owner should be
    asked before merging" ... "or before somebody joins their trip").

    Either a person asks to join `trip` with a booking from their To check
    (item), or the owner of `trip` asks to merge `from_trip` - someone
    else's - into it. Nothing moves until the owner of the trip that gives
    something up says yes."""
    STATES = [('open', 'Waiting'), ('yes', 'Agreed'), ('no', 'Declined')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='join_requests')
    by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    item = models.ForeignKey(CheckItem, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='requests')
    from_trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True,
                                  blank=True, related_name='merge_requests')
    state = models.CharField(max_length=4, choices=STATES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'travel_join_requests'
        ordering = ['-created_at', '-id']

    @property
    def asks(self):
        """Who has to say yes: the owner of the trip that gives something
        up - the trip joined, or for a merge the trip merged away."""
        return self.from_trip.owner if self.from_trip_id else self.trip.owner
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''
from . import fx
from .models import Booking, BookingChange, BookingFile, Trip, trips_for

PERM = 'auth.can_access_travel'
''',
         r'''
from . import fx
from .models import (Booking, BookingChange, BookingFile, InboundFile,
                     JoinRequest, Trip, trips_for)

PERM = 'auth.can_access_travel'
'''),
        (r'''

def eur(v):
    """€1,234.50 - or '' for nothing."""
''',
         r'''

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
'''),
        (r'''    kinds = OrderedDict()
    for b in bookings:
        if b.amount is None:
            continue
        if b.amount_eur is None:
''',
         r'''    kinds = OrderedDict()
    for b in bookings:
        if b.amount is None or b.status == 'cancelled':
            continue
        if b.amount_eur is None:
'''),
        (r'''    out = []
    for b in bookings:
        if b.cancel_until and b.cancel_until >= today:
            out.append({'day': b.cancel_until, 'what': 'Free cancellation ends',
''',
         r'''    out = []
    for b in bookings:
        if b.status == 'cancelled':
            continue
        if b.cancel_until and b.cancel_until >= today:
            out.append({'day': b.cancel_until, 'what': 'Free cancellation ends',
'''),
        (r'''    b.status_label = dict(Booking.PAID).get(b.paid, '')
    b.route = ' → '.join(x for x in (b.from_place, b.to_place) if x)
    return b


# ---------------------------------------------------------------- trips
@travel_view
def trips(request):
    today = dt.date.today()
    show = request.GET.get('show') or 'upcoming'
''',
         r'''    b.status_label = dict(Booking.PAID).get(b.paid, '')
    b.route = ' → '.join(x for x in (b.from_place, b.to_place) if x)
    b.cancelled = b.status == 'cancelled'
    if b.pk:
        names = [u.get_full_name() or u.username for u in b.travellers.all()]
        names += [x.strip() for x in (b.traveller_names or '').split(',')
                  if x.strip()]
        b.who = ', '.join(names)
    else:
        b.who = ''
    return b


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
'''),
        (r'''    return render(request, 'travel/trips.html', {
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'countries': sorted(countries), 'count': len(rows)})


''',
         r'''    return render(request, 'travel/trips.html', {
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'countries': sorted(countries), 'count': len(rows),
        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        'requests': requests_for(request.user)})


'''),
        (r'''    tab = 'costs' if request.resolver_match.url_name == 'trip_costs' \
        else 'bookings'
    bs = list(t.bookings.all())
    fx.convert_pending(bs)
    bs = [shape(b) for b in bs]
''',
         r'''    tab = 'costs' if request.resolver_match.url_name == 'trip_costs' \
        else 'bookings'
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    bs = [shape(b) for b in bs]
'''),
        (r'''        'money': totals(bs), 'coming': coming_up(bs, dt.date.today()),
        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id})


''',
         r'''        'money': totals(bs), 'coming': coming_up(bs, dt.date.today()),
        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
        'requests': requests_for(request.user, t)})


'''),
        (r'''        raise Http404
    for f in BookingFile.objects.filter(booking__trip=t):
        f.file.delete(save=False)
    t.delete()
    messages.success(request, 'Trip deleted.')
''',
         r'''        raise Http404
    for f in BookingFile.objects.filter(booking__trip=t):
        drop_file(f)
    t.delete()
    messages.success(request, 'Trip deleted.')
'''),
        (r'''# What the change trail watches, and how it names each field.
TRACKED = [('kind', 'Kind'), ('title', 'Name'), ('provider', 'With'),
           ('reference', 'Reference'), ('start_date', 'Starts'),
           ('start_time', 'Start time'), ('end_date', 'Ends'),
           ('end_time', 'End time'), ('from_place', 'From'),
''',
         r'''# What the change trail watches, and how it names each field.
TRACKED = [('kind', 'Kind'), ('title', 'Name'), ('provider', 'With'),
           ('reference', 'Reference'), ('segment', 'Part'),
           ('start_date', 'Starts'),
           ('start_time', 'Start time'), ('end_date', 'Ends'),
           ('end_time', 'End time'), ('from_place', 'From'),
'''),
        (r'''           ('amount_eur', 'In euros'), ('paid', 'Paid?'),
           ('paid_amount', 'Part paid'), ('pay_by', 'Pay by'),
           ('cancel_until', 'Free cancellation until')]


''',
         r'''           ('amount_eur', 'In euros'), ('paid', 'Paid?'),
           ('paid_amount', 'Part paid'), ('pay_by', 'Pay by'),
           ('cancel_until', 'Free cancellation until'),
           ('status', 'Status'), ('traveller_names', 'Also travelling')]


'''),
        (r'''    if f == 'paid':
        return dict(Booking.PAID).get(v, v)
    if isinstance(v, dt.date):
        return v.strftime('%a %d %b %Y').replace(' 0', ' ')
''',
         r'''    if f == 'paid':
        return dict(Booking.PAID).get(v, v)
    if f == 'status':
        return dict(Booking.STATUSES).get(v, v)
    if isinstance(v, dt.date):
        return v.strftime('%a %d %b %Y').replace(' 0', ' ')
'''),
        (r'''
FIELDS_TEXT = (('title', 160), ('provider', 120), ('reference', 60),
               ('from_place', 120), ('to_place', 120), ('address', 255),
               ('phone', 40), ('link', 500))


''',
         r'''
FIELDS_TEXT = (('title', 160), ('provider', 120), ('reference', 60),
               ('segment', 40), ('from_place', 120), ('to_place', 120),
               ('address', 255), ('phone', 40), ('link', 500),
               ('traveller_names', 255))


'''),
        (r'''    b.pay_by = _date(P.get('pay_by'))
    b.cancel_until = _date(P.get('cancel_until'))
    if not b.title:
        problems.append('Say what the booking is.')
''',
         r'''    b.pay_by = _date(P.get('pay_by'))
    b.cancel_until = _date(P.get('cancel_until'))
    b.status = 'cancelled' if P.get('cancelled') else 'ok'
    if not b.title:
        problems.append('Say what the booking is.')
'''),
        (r'''    problems = []
    dupe = None
    if request.method == 'POST':
        before = snapshot(b) if b.pk else None
''',
         r'''    problems = []
    dupe = None
    people = [t.owner] + list(t.shared_with.all())
    on = set(b.travellers.values_list('pk', flat=True)) if b.pk else set()
    for u in people:
        u.on = u.pk in on
    if request.method == 'POST':
        before = snapshot(b) if b.pk else None
'''),
        (r'''        if not problems:
            b.save()
            if before is not None:
                changed = diff(before, b)
''',
         r'''        if not problems:
            b.save()
            # WHO IS TRAVELLING: ticked from the trip's people.
            picked = {int(x) for x in request.POST.getlist('travellers')
                      if x.isdigit()}
            b.travellers.set([u for u in people if u.pk in picked])
            if before is not None:
                changed = diff(before, b)
'''),
        (r'''        'kinds': Booking.KINDS,
        'paids': Booking.PAID, 'currencies': fx.CURRENCIES,
        'files': list(b.files.all()) if b.pk else []})


''',
         r'''        'kinds': Booking.KINDS,
        'paids': Booking.PAID, 'currencies': fx.CURRENCIES,
        'files': list(b.files.all()) if b.pk else [], 'people': people})


'''),
        (r'''    b = _booking(request, booking_id)
    t = b.trip
    for f in b.files.all():
        f.file.delete(save=False)
    b.delete()
    messages.success(request, 'Booking deleted.')
''',
         r'''    b = _booking(request, booking_id)
    t = b.trip
    for f in list(b.files.all()):
        drop_file(f)
    b.delete()
    messages.success(request, 'Booking deleted.')
'''),
        (r'''        raise Http404
    bid = f.booking_id
    f.file.delete(save=False)
    f.delete()
    messages.success(request, 'File removed.')
    return redirect(reverse('travel:booking_edit', args=[bid]))
''',
         r'''        raise Http404
    bid = f.booking_id
    drop_file(f)
    messages.success(request, 'File removed.')
    return redirect(reverse('travel:booking_edit', args=[bid]))
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import views

app_name = 'travel'
''',
         r'''from django.urls import path

from . import views, views_inbox

app_name = 'travel'
'''),
        (r'''    path('file/<int:file_id>/delete/', views.booking_file_delete,
         name='file_delete'),
]
''',
         r'''    path('file/<int:file_id>/delete/', views.booking_file_delete,
         name='file_delete'),
    # TR-2, 15 Nov 2026 - stage 2: bookings read from forwarded emails.
    path('inbound/', views_inbox.inbound_view, name='inbound'),
    path('check/', views_inbox.check, name='check'),
    path('check/<int:item_id>/add/', views_inbox.check_add,
         name='check_add'),
    path('check/<int:item_id>/merge/', views_inbox.check_merge,
         name='check_merge'),
    path('check/<int:item_id>/dismiss/', views_inbox.check_dismiss,
         name='check_dismiss'),
    path('check/<int:item_id>/ask/', views_inbox.check_ask,
         name='check_ask'),
    path('request/<int:request_id>/', views_inbox.answer, name='answer'),
    path('forwarding/', views_inbox.forwarding, name='forwarding'),
    path('<int:trip_id>/merge/', views_inbox.trip_merge, name='trip_merge'),
]
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-files { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.tv-files li { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
@media screen and (max-width: 575.98px) {
  .tv-form-grid { grid-template-columns: 1fr; }
''',
         r'''.tv-files { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.tv-files li { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.tv-off b, .tv-off .tv-sub { text-decoration: line-through; }
.tv-off .tv-tag { text-decoration: none; }
.tv-count { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 22px; padding: 0 6px; margin-left: 4px; border-radius: 999px; border: 1px solid currentColor; font-size: 0.75rem; font-weight: 700; }
.tv-ask { border-left: 4px solid var(--alv-accent); }
.tv-item { display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 12px; }
.tv-acts { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px; }
.tv-acts form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0; }
.tv-acts select, .tv-acts input[type=text] { max-width: 260px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
  .tv-form-grid { grid-template-columns: 1fr; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_booking_row.html'), [
        (r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{{ b.title }}</b><span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}</span></span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% endif %}</span>
</a>
''',
         r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span></span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% endif %}</span>
</a>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''<div class="tv-main">
    <section class="form-card" data-booking-detail>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas {{ b.icon }}" aria-hidden="true"></i> {{ b.title }}</h3><span class="tv-tag tv-shared">{{ b.kind_label }}</span></div>
        {% if b.start_date %}
        <div class="tv-row" style="margin-top: 10px">
''',
         r'''<div class="tv-main">
    <section class="form-card" data-booking-detail>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas {{ b.icon }}" aria-hidden="true"></i> {{ b.title }}</h3><span>{% if b.cancelled %}<span class="tv-tag tv-due" data-cancelled>Cancelled</span> {% endif %}<span class="tv-tag tv-shared">{{ b.kind_label }}</span></span></div>
        {% if b.start_date %}
        <div class="tv-row" style="margin-top: 10px">
'''),
        (r'''    <section class="form-card">
        <dl class="tv-kv">
            {% if b.reference %}<dt>Reference</dt><dd class="tv-ref">{{ b.reference }}</dd>{% endif %}
            {% if b.provider %}<dt>With</dt><dd>{{ b.provider }}</dd>{% endif %}
            {% if b.route %}<dt>Route</dt><dd>{{ b.route }}</dd>{% endif %}
''',
         r'''    <section class="form-card">
        <dl class="tv-kv">
            {% if b.reference %}<dt>Reference</dt><dd class="tv-ref">{{ b.reference }}{% if b.segment %} <span class="tv-sub">&middot; {{ b.segment }}</span>{% endif %}</dd>{% endif %}
            {% if b.who %}<dt>Travelling</dt><dd data-who>{{ b.who }}</dd>{% endif %}
            {% if b.provider %}<dt>With</dt><dd>{{ b.provider }}</dd>{% endif %}
            {% if b.route %}<dt>Route</dt><dd>{{ b.route }}</dd>{% endif %}
'''),
        (r'''        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
    <section class="form-card" data-booking-files>
        <h3 class="form-section-title">Tickets &amp; documents</h3>
''',
         r'''        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
    {% if b.pass_code or b.wallet_link %}
    <section class="form-card" data-boarding-pass>
        <h3 class="form-section-title"><i class="fas fa-qrcode" aria-hidden="true"></i> Boarding pass</h3>
        <p class="tv-sub small" style="margin: 0 0 6px">Received{% if b.pass_format %} ({{ b.pass_format|upper }} code){% endif %}. It will show, ready to scan, in the Travel app for your phone. Until then, open the airline&rsquo;s PDF below.</p>
        {% if b.wallet_link %}<a href="{{ b.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
    </section>
    {% endif %}
    <section class="form-card" data-booking-files>
        <h3 class="form-section-title">Tickets &amp; documents</h3>
'''),
        (r'''    </details>
    {% endif %}
    <p class="tv-sub small">Added by {{ b.added_by.get_full_name|default:b.added_by.username|default:"someone" }} &middot; {{ b.created_at|date:"j M Y" }}</p>
</aside>
</div>
''',
         r'''    </details>
    {% endif %}
    <p class="tv-sub small">Added by {{ b.added_by.get_full_name|default:b.added_by.username|default:"someone" }}{% if b.source == 'email' %} from an email{% endif %} &middot; {{ b.created_at|date:"j M Y" }}</p>
</aside>
</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking_form.html'), [
        (r'''        <div><label for="bp">With</label><input id="bp" name="provider" class="form-control" maxlength="120" value="{{ b.provider }}" placeholder="Airline, hotel, Booking.com&hellip;"></div>
        <div><label for="br">Booking reference</label><input id="br" name="reference" class="form-control" maxlength="60" value="{{ b.reference }}"></div>
    </div>
</section>

''',
         r'''        <div><label for="bp">With</label><input id="bp" name="provider" class="form-control" maxlength="120" value="{{ b.provider }}" placeholder="Airline, hotel, Booking.com&hellip;"></div>
        <div><label for="br">Booking reference</label><input id="br" name="reference" class="form-control" maxlength="60" value="{{ b.reference }}"></div>
        <div><label for="bs">Part (flight or train number)</label><input id="bs" name="segment" class="form-control" maxlength="40" value="{{ b.segment }}" placeholder="e.g. CY 326, when one reference has several"></div>
        <div style="align-self: end"><div class="form-check"><input class="form-check-input" type="checkbox" id="bx" name="cancelled" value="1"{% if b.status == 'cancelled' %} checked{% endif %}><label class="form-check-label" for="bx">Cancelled</label></div></div>
    </div>
</section>

<section class="form-card" data-travellers>
    <h3 class="form-section-title">Who&rsquo;s travelling</h3>
    <div class="tv-chips" style="margin-bottom: 8px">{% for p in people %}<div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" id="tr{{ p.pk }}" name="travellers" value="{{ p.pk }}"{% if p.on %} checked{% endif %}><label class="form-check-label" for="tr{{ p.pk }}">{{ p.get_full_name|default:p.username }}</label></div>{% endfor %}</div>
    <label for="tw">Anyone else</label><input id="tw" name="traveller_names" class="form-control" maxlength="255" value="{{ b.traveller_names }}" placeholder="Names, separated by commas">
</section>

'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
</div>

<div class="tv-wrap">
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.countries %} · {{ trip.countries }}{% endif %}</p>

''',
         r'''    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
</div>

<div class="tv-wrap">
{% include 'travel/_requests.html' %}
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.countries %} · {{ trip.countries }}{% endif %}</p>

'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''<div class="page-action-buttons">
    <a href="#new-trip" class="btn action-primary" data-new-trip><i class="fas fa-plus"></i> New trip</a>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
</div>

<div class="tv-wrap">
<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included.</p>

{% if count %}
''',
         r'''<div class="page-action-buttons">
    <a href="#new-trip" class="btn action-primary" data-new-trip><i class="fas fa-plus"></i> New trip</a>
    <a href="{% url 'travel:check' %}" class="btn action-secondary" data-to-check><i class="fas fa-inbox"></i> To check{% if checks %} <span class="tv-count">{{ checks }}</span>{% endif %}</a>
    <a href="{% url 'travel:forwarding' %}" class="btn action-secondary"><i class="fas fa-envelope"></i> Forwarding</a>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
</div>

<div class="tv-wrap">
{% include 'travel/_requests.html' %}
<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included. Forward booking emails to <b>{{ address }}</b> and they wait for you under <a href="{% url 'travel:check' %}">To check</a>.</p>

{% if count %}
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('TR-2 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_travel_two.py'" in read(pq):
        print('TR-2 already applied.')
        return 0
    if "'test_travel_one.py'" not in read(pq):
        refuse('Release 82 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new travel files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-2 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('TR-2 applied - Travel, stage 2. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
