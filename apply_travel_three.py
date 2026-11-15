# -*- coding: utf-8 -*-
"""apply_travel_three.py - round TR-3, 15 Nov 2026.

RELEASE 84 - TRAVEL, STAGE 3: THE PHONE APP.

    - /travel/m/: Today, Trips, To check and Passes, installable on the
      phone (manifest, service worker and icons under /travel/app/, open
      to a phone before sign-in, nothing personal there).
    - 30 days signed in on the phone, as Wellness (wellness/session.py now
      serves both apps); the main app keeps its hour.
    - Boarding passes wallet-style, the barcode drawn again (Aztec, PDF417,
      QR - pure Python, two encoders vendored under travel/barcodes/), one
      pass per passenger (BoardingPass), kept on the phone for no signal.
    - Share -> Travel (Android): an email, PDF ticket or screenshot is read
      like a forwarded email, into To check.
    - The desktop booking shows the passes; the Travel page a code to open
      the app on the phone. Help: a Phone app tab.

New files ship beside this patcher. Stands on Release 83. Idempotent.
Edits backed up to .bak_travel3.
MIGRATION: travel 0003 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_travel3'
MARK = 'TR-3, 15 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/assets/apple-touch-icon.png',
    'travel/assets/icon-192.png',
    'travel/assets/icon-512.png',
    'travel/assets/icon-maskable-512.png',
    'travel/assets/travel.css',
    'travel/assets/travel.js',
    'travel/barcodes/__init__.py',
    'travel/barcodes/aztec.py',
    'travel/barcodes/pdf417/__init__.py',
    'travel/barcodes/pdf417/codes.py',
    'travel/barcodes/pdf417/compaction/__init__.py',
    'travel/barcodes/pdf417/compaction/byte.py',
    'travel/barcodes/pdf417/compaction/numeric.py',
    'travel/barcodes/pdf417/compaction/optimizations.py',
    'travel/barcodes/pdf417/compaction/text.py',
    'travel/barcodes/pdf417/data.py',
    'travel/barcodes/pdf417/encoding.py',
    'travel/barcodes/pdf417/error_correction.py',
    'travel/barcodes/pdf417/util.py',
    'travel/templates/travel/m/_icon.html',
    'travel/templates/travel/m/_requests.html',
    'travel/templates/travel/m/_row.html',
    'travel/templates/travel/m/base.html',
    'travel/templates/travel/m/booking.html',
    'travel/templates/travel/m/check.html',
    'travel/templates/travel/m/help.html',
    'travel/templates/travel/m/passes.html',
    'travel/templates/travel/m/today.html',
    'travel/templates/travel/m/trip.html',
    'travel/templates/travel/m/trips.html',
    'travel/phone.py',
    'travel/migrations/0003_boarding_passes.py',
    'test_travel_three.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - bookings read from
    # forwarded emails.
    'test_travel_two.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - bookings read from
    # forwarded emails.
    'test_travel_two.py',
    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    'test_travel_three.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - emails.
    '.bak_travel2',
]

''',
         r'''    # TR-2, 15 Nov 2026 - Release 83: Travel, stage 2 - emails.
    '.bak_travel2',
    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    '.bak_travel3',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p>Coming next: a Travel app for your phone with your boarding passes, then an itinerary and wish list.</p>
  </article>

''',
         r'''    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Coming next: an itinerary and wish list.</p>
  </article>

'''),
        (r'''    <p><strong>The rules for a second email.</strong> The same email twice is taken once. A later email with the same booking reference updates that booking &mdash; the latest email wins, field by field, and every change is in the booking&rsquo;s <strong>Changes</strong>. A boarding pass attaches to its flight. A cancellation marks the booking <strong>Cancelled</strong>; it is never deleted. An older email arriving after a newer one changes nothing. With no reference to go on, a booking on the same day, of the same kind, at the same place asks <strong>Merge into it</strong> or <strong>Keep both</strong>. If the sender of an update could not be confirmed, it waits in To check instead of changing anything by itself.</p>
    <p><strong>What is never kept</strong>: PINs, card numbers or card digits, and your own email address or phone number. The email itself is deleted as soon as it has been read; only the booking details and the attachments stay.</p>
  </article>

''',
         r'''    <p><strong>The rules for a second email.</strong> The same email twice is taken once. A later email with the same booking reference updates that booking &mdash; the latest email wins, field by field, and every change is in the booking&rsquo;s <strong>Changes</strong>. A boarding pass attaches to its flight. A cancellation marks the booking <strong>Cancelled</strong>; it is never deleted. An older email arriving after a newer one changes nothing. With no reference to go on, a booking on the same day, of the same kind, at the same place asks <strong>Merge into it</strong> or <strong>Keep both</strong>. If the sender of an update could not be confirmed, it waits in To check instead of changing anything by itself.</p>
    <p><strong>What is never kept</strong>: PINs, card numbers or card digits, and your own email address or phone number. The email itself is deleted as soon as it has been read; only the booking details and the attachments stay.</p>
  </article>

  <article data-tab-slug="tr-phone"
           data-tab-name="Phone app"
           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>Open <strong>alivente.online/travel/m/</strong> on the phone &mdash; or point the phone&rsquo;s camera at the code on the Travel page &mdash; and choose <strong>Add to Home screen</strong> (Android: Chrome&rsquo;s menu; iPhone: Safari&rsquo;s Share button). It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on and does not turn sideways while it is shown (in the installed app on Android). Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
    <p><strong>Share &rarr; Travel</strong> (Android): share a booking email, a PDF ticket or a screenshot to Travel and it is read exactly like a forwarded email, into To check. To check works on the phone with the same buttons. Adding, editing, sharing and merging trips stay on the full site.</p>
  </article>

'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            # every other page under travel/ keeps its permission check.
            'travel/inbound/',
            'media/',  # Media files
            'static/',  # Static files
''',
         r'''            # every other page under travel/ keeps its permission check.
            'travel/inbound/',
            # TR-3, 15 Nov 2026 - TRAVEL'S PHONE-APP SHELL, as wellness/app/
            # above: the manifest, service worker, style, script and icons,
            # fetched by a phone before anyone is signed in. Nothing
            # personal is served under it; the pages are under travel/m/
            # and keep their check.
            'travel/app/',
            'media/',  # Media files
            'static/',  # Static files
'''),
    ]),
    (os.path.join('wellness', 'session.py'), [
        (r'''FREE = ('/wellness/', '/login/', '/logout/', '/static/', '/media/',
        '/version/', '/forgot-password/', '/set-password/', '/sign/',
        '/robots.txt', '/favicon.ico')


''',
         r'''FREE = ('/wellness/', '/login/', '/logout/', '/static/', '/media/',
        '/version/', '/forgot-password/', '/set-password/', '/sign/',
        '/robots.txt', '/favicon.ico',
        # TR-3, 15 Nov 2026 - the Travel phone app is the second app with
        # the phone's 30 days (Demetri: "like Wellness"): its pages, its
        # shell, and the door the email Worker uses.
        '/travel/m/', '/travel/app/', '/travel/inbound/')

# The apps whose pages, opened on a phone, give the session its 30 days.
LONG_APPS = ('/wellness/', '/travel/m/')


'''),
        (r'''            path = request.path
            s = request.session
            if path.startswith('/wellness/'):
                if is_phone(request):
                    if MAIN_UNTIL not in s:
''',
         r'''            path = request.path
            s = request.session
            if path.startswith(LONG_APPS):
                if is_phone(request):
                    if MAIN_UNTIL not in s:
'''),
    ]),
    (os.path.join('travel', 'inbox.py'), [
        (r'''
from . import extract, fx, inbound
from .models import (Booking, BookingChange, BookingFile, CheckItem,
                     InboundEmail, InboundFile, TravelAddress, Trip,
                     trips_for)

logger = logging.getLogger(__name__)
''',
         r'''
from . import extract, fx, inbound
from .models import (BoardingPass, Booking, BookingChange, BookingFile,
                     CheckItem, InboundEmail, InboundFile, TravelAddress,
                     Trip, trips_for)

logger = logging.getLogger(__name__)
'''),
        (r'''

def attach(b, files, user):
    """The email's tickets and passes onto the booking - the same stored
''',
         r'''

def keep_pass(b, item, user):
    """TR-3 - the boarding pass as its passenger's own row: a second
    passenger's pass for the same flight is added beside the first, and
    the same passenger's again replaces theirs."""
    code = item.get('pass_code')
    if not code:
        return None
    from .barcodes import bcbp
    info = bcbp(code, b.start_date.year if b.start_date else None)
    name = (info.get('name') or '')[:80]
    p = BoardingPass.objects.filter(booking=b, name=name).first() or \
        BoardingPass(booking=b, name=name, added_by=user)
    p.code = code
    p.format = (item.get('pass_format') or 'aztec')[:12]
    p.seat = (info.get('seat') or '')[:8]
    if item.get('wallet_link'):
        p.wallet_link = item['wallet_link'][:1000]
    p.save()
    return p


def attach(b, files, user):
    """The email's tickets and passes onto the booking - the same stored
'''),
        (r'''    attach(b, files, user)
    travellers(b, item)
    changes = diff(before, b)
    if was_status != b.status:
''',
         r'''    attach(b, files, user)
    travellers(b, item)
    keep_pass(b, item, user)
    changes = diff(before, b)
    if was_status != b.status:
'''),
        (r'''    attach(b, files, user)
    travellers(b, item)
    return b

''',
         r'''    attach(b, files, user)
    travellers(b, item)
    keep_pass(b, item, user)
    return b

'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''        up - the trip joined, or for a merge the trip merged away."""
        return self.from_trip.owner if self.from_trip_id else self.trip.owner
''',
         r'''        up - the trip joined, or for a merge the trip merged away."""
        return self.from_trip.owner if self.from_trip_id else self.trip.owner


class BoardingPass(models.Model):
    """TR-3, 15 Nov 2026 - one passenger's boarding pass for one flight.

    A family flies on one booking reference, but each person has a pass of
    their own: Alexandra's must not overwrite Demetri's when her email
    comes in second. So the pass is its own row, one per passenger (the
    name the barcode itself carries), and Booking.pass_code keeps only the
    latest as stage 2 left it."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='passes')
    name = models.CharField(max_length=80, blank=True, default='')
    code = models.TextField()
    format = models.CharField(max_length=12, default='aztec')
    seat = models.CharField(max_length=8, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_boarding_passes'
        ordering = ['name', 'id']

    def __str__(self):
        return '%s %s' % (self.booking, self.name)
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import views, views_inbox

app_name = 'travel'
''',
         r'''from django.urls import path

from . import phone, views, views_inbox

app_name = 'travel'
'''),
        (r'''    path('forwarding/', views_inbox.forwarding, name='forwarding'),
    path('<int:trip_id>/merge/', views_inbox.trip_merge, name='trip_merge'),
]
''',
         r'''    path('forwarding/', views_inbox.forwarding, name='forwarding'),
    path('<int:trip_id>/merge/', views_inbox.trip_merge, name='trip_merge'),
    # TR-3, 15 Nov 2026 - stage 3: the phone app (m/) and its shell (app/).
    path('m/', phone.today, name='m_today'),
    path('m/trips/', phone.trips, name='m_trips'),
    path('m/trip/<int:trip_id>/', phone.trip, name='m_trip'),
    path('m/booking/<int:booking_id>/', phone.booking, name='m_booking'),
    path('m/passes/', phone.passes, name='m_passes'),
    path('m/check/', phone.check, name='m_check'),
    path('m/check/<int:item_id>/<str:action>/', phone.check_action,
         name='m_check_action'),
    path('m/request/<int:request_id>/', phone.answer, name='m_answer'),
    path('m/file/<int:file_id>/', phone.booking_file, name='m_file'),
    path('m/share/', phone.share, name='m_share'),
    path('m/help/', phone.help_page, name='m_help'),
    path('app/manifest.webmanifest', phone.manifest, name='manifest'),
    path('app/sw.js', phone.service_worker, name='service_worker'),
    path('app/<str:name>', phone.asset, name='asset'),
]
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''

def requests_for(user, trip=None):
    """Join and merge requests waiting for this person's answer."""
''',
         r'''

def phone_qr(request):
    from .barcodes import svg
    return svg(request.build_absolute_uri('/travel/m/'), 'qr',
               'Scan to open Travel on your phone')


def requests_for(user, trip=None):
    """Join and merge requests waiting for this person's answer."""
'''),
        (r'''        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        'requests': requests_for(request.user)})

''',
         r'''        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        # TR-3 - point the phone's camera at this to open the phone app.
        'phone_qr': phone_qr(request),
        'requests': requests_for(request.user)})

'''),
        (r'''    nights = (b.end_date - b.start_date).days \
        if b.kind == 'stay' and b.start_date and b.end_date else None
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'nights': nights, 'paid_label': eur(b.paid_eur),
        'due_label': eur(b.due_eur),
''',
         r'''    nights = (b.end_date - b.start_date).days \
        if b.kind == 'stay' and b.start_date and b.end_date else None
    from .phone import pass_card
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'passes': [pass_card(p) for p in b.passes.all()],
        'nights': nights, 'paid_label': eur(b.paid_eur),
        'due_label': eur(b.due_eur),
'''),
    ]),
    (os.path.join('travel', 'views_inbox.py'), [
        (r'''        '%s %s' % ('{:,.2f}'.format(a), d.get('currency')))
    item.suggested_name = inbox.trip_name(d) if d.get('kind') else ''
    return item


''',
         r'''        '%s %s' % ('{:,.2f}'.format(a), d.get('currency')))
    item.suggested_name = inbox.trip_name(d) if d.get('kind') else ''
    # TR-3 - the dates as people read them: "Thu 19 Nov 2026, 06:40".
    item.when = ''
    try:
        import datetime as _dt
        s = _dt.date.fromisoformat(d['start_date']) if d.get('start_date') \
            else None
        e = _dt.date.fromisoformat(d['end_date']) if d.get('end_date') \
            else None
    except (TypeError, ValueError):
        s = e = None
    if s:
        item.when = s.strftime('%a %d %b %Y').replace(' 0', ' ')
        if d.get('start_time'):
            item.when += ', ' + d['start_time']
        if e and e != s:
            item.when += ' – ' + e.strftime('%a %d %b').replace(' 0', ' ')
    return item


def suggest(items, user):
    """TR-3 - the trip each waiting booking would go on, worked out again
    each time To check opens: once the first of a holiday's emails has made
    its trip, the rest of them offer that trip, not a new one each. Shown
    in date order, so the first one added is the first day."""
    for i in items:
        if i.state == 'open' and i.what in ('new', 'join') and \
                not i.trip_id and (i.data or {}).get('start_date'):
            i.trip = inbox.suggest_trip(user, i.data)
    far = '9999'
    items.sort(key=lambda i: (i.what in ('new', 'join', 'maybe', 'update'),
                              (i.data or {}).get('start_date') or far,
                              (i.data or {}).get('start_time') or ''))
    return items


'''),
        (r'''    inbox.kick()
    me = request.user
    items = [show(i) for i in CheckItem.objects.filter(
        user=me, state__in=('open', 'asked')).select_related(
        'booking', 'trip', 'other_trip__owner')]
    since = timezone.now() - timezone.timedelta(days=14)
    done = [show(i) for i in CheckItem.objects.filter(
''',
         r'''    inbox.kick()
    me = request.user
    items = suggest([show(i) for i in CheckItem.objects.filter(
        user=me, state__in=('open', 'asked')).select_related(
        'booking', 'trip', 'other_trip__owner')], me)
    since = timezone.now() - timezone.timedelta(days=14)
    done = [show(i) for i in CheckItem.objects.filter(
'''),
        (r'''        'trips': trips, 'requests': my_requests(me),
        'address': inbox.inbox_address()})


''',
         r'''        'trips': trips, 'requests': my_requests(me),
        'address': inbox.inbox_address()})


def _back(request):
    """TR-3 - back to To check: the desktop page, or the phone app's when
    the action was taken there (it posts next=/travel/m/...)."""
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/travel/') and '//' not in nxt:
        return redirect(nxt)
    return redirect('travel:check')


'''),
        (r'''        t = get_object_or_404(trips_for(request.user), pk=pick or 0)
    with transaction.atomic():
        b = inbox.create(t, item.data, request.user, item.email,
                         inbox.files_of(item))
        item.booking, item.trip = b, t
        _finish(item, note='Added to %s' % t.name)
    messages.success(request, '%s added to %s.' % (b.title, t.name))
    return redirect('travel:check')


''',
         r'''        t = get_object_or_404(trips_for(request.user), pk=pick or 0)
    with transaction.atomic():
        # TR-3 (his first real run, 15 Nov): the confirmation and the
        # boarding pass for CY 313 both waited as new bookings. Whichever
        # is added second finds the first on the trip by its reference and
        # flight, and goes onto it - the pass attached - not beside it.
        same = None
        if item.what != 'maybe' or request.POST.get('keep') != 'both':
            same, _ = inbox.same_booking(item.data, list(t.bookings.all()))
        if same and item.what != 'maybe':
            e = item.email or InboundEmail(subject=item.data.get('subject',
                                                                 ''))
            inbox.apply(same, item.data, request.user, e,
                        inbox.files_of(item))
            b = same
            note = 'Went onto %s, already on %s' % (b.title, t.name)
        else:
            b = inbox.create(t, item.data, request.user, item.email,
                             inbox.files_of(item))
            note = 'Added to %s' % t.name
        item.booking, item.trip = b, t
        _finish(item, note=note)
    messages.success(request, '%s: %s.' % (b.title, note[0].lower() +
                                           note[1:]))
    return _back(request)


'''),
        (r'''                else 'Already up to date')
    messages.success(request, '%s updated.' % item.booking.title)
    return redirect('travel:check')


''',
         r'''                else 'Already up to date')
    messages.success(request, '%s updated.' % item.booking.title)
    return _back(request)


'''),
        (r'''    _finish(item, state='dismissed')
    messages.success(request, 'Dismissed.')
    return redirect('travel:check')


''',
         r'''    _finish(item, state='dismissed')
    messages.success(request, 'Dismissed.')
    return _back(request)


'''),
        (r'''    messages.success(request, 'Asked %s. It stays here until they answer.'
                     % name_of(t.owner))
    return redirect('travel:check')


''',
         r'''    messages.success(request, 'Asked %s. It stays here until they answer.'
                     % name_of(t.owner))
    return _back(request)


'''),
        (r'''                             inbox.files_of(item))
        item.booking, item.trip = b, t
        _finish(item, note='Added to %s' % t.name)
    messages.success(request, '%s added to %s.' % (b.title, t.name))
    return redirect('travel:check')


@travel_view
@require_POST
''',
         r'''                             inbox.files_of(item))
        item.booking, item.trip = b, t
        _finish(item, note='Added to %s' % t.name)
    messages.success(request, '%s added to %s.' % (b.title, t.name))
    return _back(request)


@travel_view
@require_POST
'''),
        (r'''                messages.success(request, 'Said no. %s can keep it as '
                                 'their own trip.' % name_of(r.by))
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/travel/'):
        return redirect(nxt)
    return redirect('travel:check')


''',
         r'''                messages.success(request, 'Said no. %s can keep it as '
                                 'their own trip.' % name_of(r.by))
    return _back(request)


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-acts form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0; }
.tv-acts select, .tv-acts input[type=text] { max-width: 260px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
''',
         r'''.tv-acts form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0; }
.tv-acts select, .tv-acts input[type=text] { max-width: 260px; }
.tv-passcode { background: #fff; padding: 8px; border-radius: 8px; margin-top: 6px; max-width: 220px; }
.tv-passcode svg, .tv-phone svg { display: block; width: 100%; height: auto; }
.tv-phone { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 14px; align-items: center; max-width: 560px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
    {% if b.pass_code or b.wallet_link %}
    <section class="form-card" data-boarding-pass>
        <h3 class="form-section-title"><i class="fas fa-qrcode" aria-hidden="true"></i> Boarding pass</h3>
        <p class="tv-sub small" style="margin: 0 0 6px">Received{% if b.pass_format %} ({{ b.pass_format|upper }} code){% endif %}. It will show, ready to scan, in the Travel app for your phone. Until then, open the airline&rsquo;s PDF below.</p>
        {% if b.wallet_link %}<a href="{{ b.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
    </section>
    {% endif %}
''',
         r'''        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
    {% if passes %}
    <section class="form-card" data-boarding-pass>
        <h3 class="form-section-title"><i class="fas fa-qrcode" aria-hidden="true"></i> Boarding pass{{ passes|length|pluralize }}</h3>
        {% for p in passes %}
        <div style="border-top: 1px solid var(--alv-line-soft); padding-top: 8px; margin-top: 8px">
            <div class="tv-row small"><b>{{ p.name|default:"Passenger" }}</b><span>{{ p.flight }}{% if p.seat_shown %} &middot; seat {{ p.seat_shown }}{% endif %}</span></div>
            {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}">{{ p.svg|safe }}</div>{% endif %}
            {% if p.wallet_link %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
        </div>
        {% endfor %}
        <p class="tv-sub small" style="margin: 8px 0 0">On the phone, Travel &rarr; Passes shows them one a screen, and keeps them for when there is no signal.</p>
    </section>
    {% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''</div>

<section class="form-card" id="new-trip" style="margin-top: 22px; max-width: 820px">
    <h3 class="form-section-title">New trip</h3>
''',
         r'''</div>

{% if phone_qr %}
<section class="form-card tv-phone" data-phone-app style="margin-top: 22px">
    <div class="tv-passcode" style="margin: 0">{{ phone_qr|safe }}</div>
    <div><h3 class="form-section-title" style="margin: 0 0 4px">Travel on your phone</h3><p class="small" style="margin: 0">Point your phone&rsquo;s camera here, or open <b>alivente.online/travel/m/</b>, then <em>Add to Home screen</em>. Today, your boarding passes (even with no signal) and To check &mdash; and on Android, <em>Share &rarr; Travel</em> sends a ticket or an email straight in.</p></div>
</section>
{% endif %}

<section class="form-card" id="new-trip" style="margin-top: 22px; max-width: 820px">
    <h3 class="form-section-title">New trip</h3>
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
    raise SystemExit('TR-3 REFUSED: %s' % msg)


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
    if "'test_travel_three.py'" in read(pq):
        print('TR-3 already applied.')
        return 0
    if "'test_travel_two.py'" not in read(pq):
        refuse('Release 83 is not applied - this round registers after it.')
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
        print('TR-3 --check: %d file(s) would change, none written; %d '
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
    print('TR-3 applied - Travel, stage 3. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
