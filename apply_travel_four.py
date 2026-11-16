# -*- coding: utf-8 -*-
"""apply_travel_four.py - round TR-4, 15 Nov 2026.

RELEASE 85 - TRAVEL, STAGE 4: THE ITINERARY, THE WISH LIST, PLACES.

    - Add a place (a museum, a garden, a restaurant): typed, pasted as a
      link, or shared from Google Maps on the phone; Claude looks it up on
      the web (travel/places.py, Anthropic web search) for the address,
      hours, price and website. On a day, or on the trip's wish list.
    - The Itinerary tab (computer and phone): every day, bookings and
      places in time order. Today on the phone shows places too.
    - Trip dates come from the bookings once there are any (Demetri); the
      trip's countries from the bookings' countries plus typed ones.
    - New trip form and the phone code only when their buttons are pressed.
    - A trip as a PDF, summary or detailed (travel/report.py), shared via
      the house PDF viewer / the phone's share sheet. Delete on the booking
      page; boarding passes on the computer; "Included in ..." for the
      second leg of a return; the installed phone app stays upright.

New files ship beside this patcher. Stands on Release 84. Idempotent.
Edits backed up to .bak_travel4.
MIGRATION: travel 0004 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_travel4'
MARK = 'TR-4, 15 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/report.py',
    'travel/templates/travel/trip_pdf.html',
    'travel/templates/travel/passes.html',
    'travel/places.py',
    'travel/views_places.py',
    'travel/migrations/0004_places.py',
    'travel/templates/travel/_place_row.html',
    'travel/templates/travel/place_form.html',
    'travel/templates/travel/m/place.html',
    'test_travel_four.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_two.py',
    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    'test_travel_three.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_two.py',
    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    'test_travel_three.py',
    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - the itinerary, the
    # wish list, places; trip dates from the bookings.
    'test_travel_four.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    '.bak_travel3',
]

''',
         r'''    # TR-3, 15 Nov 2026 - Release 84: Travel, stage 3 - the phone app.
    '.bak_travel3',
    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - places.
    '.bak_travel4',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-share-alt">
    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong>: give it a name, and if you like its dates and countries. Leave the dates empty and they follow the bookings.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>
''',
         r'''           data-tab-icon="fa-share-alt">
    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong> (the form opens when you press it): give it a name, and if you like its dates and countries. <strong>The bookings set the dates</strong>: once a trip has bookings with dates, it runs from the first booking&rsquo;s start to the last one&rsquo;s end, whatever was typed &mdash; typed dates are only for planning before anything is booked. The trip&rsquo;s countries are its bookings&rsquo; countries (as read from the emails, or typed on a booking) together with any typed on the trip. The name is yours to choose.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>
'''),
        (r'''    <h6><i class="fas fa-ticket-alt"></i> Bookings</h6>
    <p>On a trip, <strong>Add booking</strong>. Choose the kind, name it (&ldquo;TAP TP 1307&rdquo;, &ldquo;Casa do Largo&rdquo;), and fill in what you have: who it is with, the booking reference, when it starts and ends, from and to, the address, the phone number and the manage-booking link. Times are the local times on the booking.</p>
    <p>The trip page lists bookings by day. Open one to see everything about it, with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>Who&rsquo;s travelling</strong>: tick the people on the trip the booking is for, and type anyone else&rsquo;s name. Bookings read from an email fill this in from the passenger and guest names.</p>
''',
         r'''    <h6><i class="fas fa-ticket-alt"></i> Bookings</h6>
    <p>On a trip, <strong>Add booking</strong>. Choose the kind, name it (&ldquo;TAP TP 1307&rdquo;, &ldquo;Casa do Largo&rdquo;), and fill in what you have: who it is with, the booking reference, when it starts and ends, from and to, the address, the phone number and the manage-booking link. Times are the local times on the booking.</p>
    <p>The trip page lists bookings by day. Open one to see everything about it &mdash; <strong>Delete</strong> is there too, next to Edit &mdash; with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>Who&rsquo;s travelling</strong>: tick the people on the trip the booking is for, and type anyone else&rsquo;s name. Bookings read from an email fill this in from the passenger and guest names.</p>
'''),
        (r'''    <p>Enter a cost in the currency you paid in. It is kept as it is, and shown in euros as well, at the European Central Bank&rsquo;s reference rate for the day it was entered. The rate is stored with the booking, so the euro figure never moves.</p>
    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
''',
         r'''    <p>Enter a cost in the currency you paid in. It is kept as it is, and shown in euros as well, at the European Central Bank&rsquo;s reference rate for the day it was entered. The rate is stored with the booking, so the euro figure never moves.</p>
    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p><strong>PDF summary</strong> and <strong>PDF detailed</strong> (on the trip) make the trip into a PDF. The summary is the trip day by day &mdash; what starts each day, the places planned &mdash; with the wish list and the costs; the detailed one adds every booking in full: reference, times, address, phone, travellers, cost, cancellation and payment dates, documents and details. It opens in the PDF viewer to download or, on a phone, to share by WhatsApp or mail; in the phone app it goes straight to the phone&rsquo;s share sheet.</p>
    <p>A return flight booked together has one price: it sits on the first flight, and the other says <strong>Included in</strong> that flight rather than showing nothing.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
'''),
        (r'''  </article>

  <article data-tab-slug="tr-phone"
           data-tab-name="Phone app"
           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>Open <strong>alivente.online/travel/m/</strong> on the phone &mdash; or point the phone&rsquo;s camera at the code on the Travel page &mdash; and choose <strong>Add to Home screen</strong> (Android: Chrome&rsquo;s menu; iPhone: Safari&rsquo;s Share button). It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on and does not turn sideways while it is shown (in the installed app on Android). Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
    <p><strong>Share &rarr; Travel</strong> (Android): share a booking email, a PDF ticket or a screenshot to Travel and it is read exactly like a forwarded email, into To check. To check works on the phone with the same buttons. Adding, editing, sharing and merging trips stay on the full site.</p>
  </article>
''',
         r'''  </article>

  <article data-tab-slug="tr-plan"
           data-tab-name="Itinerary &amp; Places"
           data-tab-icon="fa-map-marker-alt">
    <h6><i class="fas fa-map-marker-alt"></i> The itinerary, the wish list and places</h6>
    <p><strong>Add a place</strong> for somewhere with no booking &mdash; a museum, a garden, a restaurant, a viewpoint. Type its name or paste a Google Maps or website link. Claude looks it up on the web and fills in the address, opening hours, price and website, usually within half a minute (the page refreshes by itself). Check the hours before you go; anything you type wins over what was found. On the phone, in Google Maps, tap <strong>Share &rarr; Travel</strong> on a place and it opens Add a place for the trip you are on (or the next one).</p>
    <p>A place goes on a <strong>day</strong> (with a time if you like) or on the trip&rsquo;s <strong>Wish list</strong> &mdash; ideas with no day yet; <em>Put on</em> moves one to a day. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>

  <article data-tab-slug="tr-phone"
           data-tab-name="Phone app"
           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>Open <strong>alivente.online/travel/m/</strong> on the phone &mdash; or press <strong>Phone app</strong> on the Travel page and point the phone&rsquo;s camera at the code &mdash; and choose <strong>Add to Home screen</strong> (Android: Chrome&rsquo;s menu; iPhone: Safari&rsquo;s Share button). It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
    <p>On the computer, <strong>Travel &rarr; Boarding passes</strong> shows the same passes, the next one needed marked, each with its barcode &mdash; and every booking shows its own passes.</p>
    <p><strong>Share &rarr; Travel</strong> (Android): share a booking email, a PDF ticket or a screenshot to Travel and it is read exactly like a forwarded email, into To check. To check works on the phone with the same buttons. Adding, editing, sharing and merging trips stay on the full site.</p>
  </article>
'''),
    ]),
    (os.path.join('test_ai_models.py'), [
        (r'''    # importer, for reading documents; changeable through TRAVEL_AI_MODEL.
    'travel/extract.py': 'reading booking emails into Travel',
}

''',
         r'''    # importer, for reading documents; changeable through TRAVEL_AI_MODEL.
    'travel/extract.py': 'reading booking emails into Travel',
    # TR-4, 15 Nov 2026 - the ninth: looking a place up on the web (with
    # Anthropic's web search tool) for Travel's "Add a place".
    'travel/places.py': 'looking up places for Travel',
}

'''),
    ]),
    (os.path.join('test_travel_three.py'), [
        (r'''               '  CONTROL: opened on a computer, the session is left alone')

            t.start_date = day
            t.end_date = day + dt.timedelta(days=5)
            t.save()
            fl.start_date = day + dt.timedelta(days=1)
            fl.save()
''',
         r'''               '  CONTROL: opened on a computer, the session is left alone')

            # TR-4: a trip's dates now come from its bookings - the stay
            # from today to day 5 makes it a six-day trip on now.
            Booking.objects.filter(title='TV3 Parea').update(
                start_date=day, end_date=day + dt.timedelta(days=5))
            fl.start_date = day + dt.timedelta(days=1)
            fl.save()
'''),
        (r'''            ok(hd.count('data-barcode=') == 2,
               'THE DESKTOP booking shows both passes too')
            ht = dk.get('/travel/').content.decode()
            ok('data-phone-app' in ht and 'Scan to open Travel' in ht,
               '  and the Travel page a code to open the app on the phone')
''',
         r'''            ok(hd.count('data-barcode=') == 2,
               'THE DESKTOP booking shows both passes too')
            ht = dk.get('/travel/?phone=1').content.decode()
            ok('data-phone-app' in ht and 'Scan to open Travel' in ht,
               '  and the Travel page a code to open the app on the phone')
'''),
    ]),
    (os.path.join('travel', 'inbox.py'), [
        (r'''FIELDS = ['kind', 'title', 'provider', 'reference', 'segment', 'start_date',
          'start_time', 'end_date', 'end_time', 'from_place', 'to_place',
          'address', 'phone', 'link', 'details', 'pay_by', 'cancel_until']


''',
         r'''FIELDS = ['kind', 'title', 'provider', 'reference', 'segment', 'start_date',
          'start_time', 'end_date', 'end_time', 'from_place', 'to_place',
          'address', 'phone', 'link', 'details', 'pay_by', 'cancel_until',
          # TR-4 - where it is: the trip's countries come from these.
          'city', 'country']


'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    traveller_names = models.CharField(max_length=255, blank=True,
                                       default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    traveller_names = models.CharField(max_length=255, blank=True,
                                       default='')
    # TR-4, 15 Nov 2026 - where it is, as the email said: the trip's
    # countries come from its bookings (Demetri: "Should the Trip Name and
    # the From and To Dates be based on uploaded reservations?").
    city = models.CharField(max_length=80, blank=True, default='')
    country = models.CharField(max_length=60, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''    def __str__(self):
        return '%s %s' % (self.booking, self.name)
''',
         r'''    def __str__(self):
        return '%s %s' % (self.booking, self.name)


class Place(models.Model):
    """TR-4, 15 Nov 2026 - somewhere to go with no booking: a museum, a
    garden, a restaurant, a viewpoint. Typed, pasted as a link, or shared
    from Google Maps on the phone; Claude looks it up on the web for the
    address, hours, price and website. With a day it is on the itinerary;
    without one it is on the trip's wish list."""
    KINDS = [('sight', 'Sight'), ('museum', 'Museum'), ('food', 'Food & drink'),
             ('nature', 'Park & nature'), ('shop', 'Shopping'),
             ('activity', 'Activity'), ('other', 'Other')]
    LOOKUP = [('', 'Typed'), ('waiting', 'Looking it up'),
              ('found', 'Found'), ('failed', 'Not found')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='places')
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=10, choices=KINDS, default='sight')
    address = models.CharField(max_length=255, blank=True, default='')
    website = models.URLField(max_length=500, blank=True, default='')
    maps_link = models.URLField(max_length=500, blank=True, default='')
    hours = models.CharField(max_length=255, blank=True, default='')
    price = models.CharField(max_length=120, blank=True, default='')
    about = models.CharField(max_length=300, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    day = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    done = models.BooleanField(default=False)
    query = models.CharField(max_length=500, blank=True, default='')
    lookup = models.CharField(max_length=8, choices=LOOKUP, blank=True,
                              default='')
    lookup_note = models.CharField(max_length=255, blank=True, default='')
    started = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_places'
        ordering = ['day', 'time', 'id']

    def __str__(self):
        return self.name

    @property
    def map_url(self):
        """The place on Google Maps: its own link, else a search."""
        if self.maps_link:
            return self.maps_link
        from urllib.parse import quote
        q = ', '.join(x for x in (self.name, self.address) if x)
        return 'https://www.google.com/maps/search/?api=1&query=' + quote(q)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''every trip through trips_for(user), every booking through its trip.
"""
import datetime as dt
import json
''',
         r'''every trip through trips_for(user), every booking through its trip.
"""
import copy
import datetime as dt
import json
'''),
        (r'''from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
''',
         r'''from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
'''),
        (r'''from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
from .views import (coming_up, eur, requests_for, shape, span, totals,
                    travel_view)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
''',
         r'''from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
from .views import (coming_up, eur, included, requests_for, shape, span,
                    totals, travel_view)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
'''),
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv3-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv4-1'


'''),
        (r'''    out = []
    for when, what, b in rows:
        shape(b)
        b.what = what
''',
         r'''    out = []
    for when, what, b in rows:
        # A copy: a stay is on several days - check in, staying, check out
        # - and each day's row says its own thing (TR-4, the itinerary).
        b = copy.copy(b)
        shape(b)
        b.what = what
'''),
        (r'''        out.append(b)
    return out


''',
         r'''        out.append(b)
    return out


def day_rows(bs, places, day):
    """TR-4 - a day of the itinerary: its bookings (as on_day) and the
    places planned for it, in time order; places with no time at the end."""
    rows = [(b.when or dt.time(0, 0), 0, b) for b in on_day(bs, day)]
    for p in places:
        if p.day == day:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [r[2] for r in rows]


def itinerary(trip, bs, places):
    """Every day of the trip, first to last, each with its rows - empty
    days too, so there is somewhere to put a place. (At most 60 days.)"""
    start, end = span(trip, bs)
    days = []
    if start:
        end = end or start
        if (end - start).days > 60:
            end = start + dt.timedelta(days=60)
        d = start
        while d <= end:
            days.append((d, day_rows(bs, places, d)))
            d += dt.timedelta(days=1)
    return days


'''),
        (r'''        bs = list(trip.bookings.prefetch_related('travellers'))
        fx.convert_pending(bs, limit=2)
        if now:
            ctx['day_no'] = (day - trip.start).days + 1
            ctx['days'] = ((trip.end or trip.start) - trip.start).days + 1
            ctx['today_rows'] = on_day(bs, day)
            ctx['tomorrow_rows'] = on_day(bs, day + dt.timedelta(days=1))
            ctx['tomorrow'] = day + dt.timedelta(days=1)
        else:
            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = on_day(bs, trip.start)
        ctx['coming'] = coming_up(bs, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
''',
         r'''        bs = list(trip.bookings.prefetch_related('travellers'))
        fx.convert_pending(bs, limit=2)
        pl = list(trip.places.all())
        if now:
            ctx['day_no'] = (day - trip.start).days + 1
            ctx['days'] = ((trip.end or trip.start) - trip.start).days + 1
            ctx['today_rows'] = day_rows(bs, pl, day)
            ctx['tomorrow_rows'] = day_rows(bs, pl,
                                            day + dt.timedelta(days=1))
            ctx['tomorrow'] = day + dt.timedelta(days=1)
        else:
            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start)
        ctx['coming'] = coming_up(bs, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
'''),
        (r'''    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs, limit=3)
    bs = [shape(b) for b in bs]
    t.start, t.end = span(t, bs)
    days = OrderedDict()
''',
         r'''    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs, limit=3)
    bs = included([shape(b) for b in bs])
    t.start, t.end = span(t, bs)
    days = OrderedDict()
'''),
        (r'''            undated.append(b)
    costs = request.GET.get('tab') == 'costs'
    return page(request, 'travel/m/trip.html', {
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'money': totals(bs), 'costs': costs,
''',
         r'''            undated.append(b)
    costs = request.GET.get('tab') == 'costs'
    sub = request.GET.get('tab') if request.GET.get('tab') in (
        'costs', 'itinerary', 'wish') else 'bookings'
    pl = list(t.places.all())
    for p in pl:
        p.is_place = True
    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'money': totals(bs), 'costs': costs,
'''),
        (r'''    b = get_object_or_404(_bookings(request.user), pk=booking_id)
    shape(b)
    passes = [pass_card(p) for p in b.passes.all()]
    nights = (b.end_date - b.start_date).days \
        if b.kind == 'stay' and b.start_date and b.end_date else None
    return page(request, 'travel/m/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
''',
         r'''    b = get_object_or_404(_bookings(request.user), pk=booking_id)
    shape(b)
    if b.amount is None:
        included([x for x in b.trip.bookings.all() if x.pk != b.pk] + [b])
    else:
        b.included = None
    passes = [pass_card(p) for p in b.passes.all()]
    nights = ((b.end_date - b.start_date).days
              if b.kind == 'stay' and b.start_date and b.end_date else None)
    return page(request, 'travel/m/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
'''),
        (r'''    for i, p in enumerate(cards):
        p.is_next = i == first
    return page(request, 'travel/m/passes.html', {
        'cards': cards, 'every': every, 'tab': 'passes', 'day': day,
        'first': first})


''',
         r'''    for i, p in enumerate(cards):
        p.is_next = i == first
    ctx = {'cards': cards, 'every': every, 'tab': 'passes', 'day': day,
           'first': first}
    # TR-4 (Demetri, 15 Nov: "I want to be able to view boarding passes on
    # the desktop app as well") - the same passes, laid out for a screen.
    if request.resolver_match.url_name == 'passes':
        return render(request, 'travel/passes.html', ctx)
    return page(request, 'travel/m/passes.html', ctx)


'''),
        (r'''    text = (request.POST.get('text') or '').strip()
    link = (request.POST.get('url') or '').strip()
    done = 0
    rest = []
''',
         r'''    text = (request.POST.get('text') or '').strip()
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
'''),
        (r'''        'scope': '/travel/m/',
        'display': 'standalone',
        'background_color': '#F3F5F6',
        'theme_color': '#0F7480',
''',
         r'''        'scope': '/travel/m/',
        'display': 'standalone',
        # TR-4 (Demetri, 15 Nov: "if I turn my phone, the pass flips. I
        # don't want that.") - the installed app stays upright.
        'orientation': 'portrait',
        'background_color': '#F3F5F6',
        'theme_color': '#0F7480',
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import phone, views, views_inbox

app_name = 'travel'
''',
         r'''from django.urls import path

from . import phone, report, views, views_inbox, views_places

app_name = 'travel'
'''),
        (r'''    path('<int:trip_id>/', views.trip, name='trip'),
    path('<int:trip_id>/costs/', views.trip, name='trip_costs'),
    path('<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
''',
         r'''    path('<int:trip_id>/', views.trip, name='trip'),
    path('<int:trip_id>/costs/', views.trip, name='trip_costs'),
    # TR-4, 15 Nov 2026 - stage 4: the itinerary, the wish list, places.
    path('<int:trip_id>/itinerary/', views.trip, name='trip_itinerary'),
    path('passes/', phone.passes, name='passes'),
    path('<int:trip_id>/pdf/', report.trip_pdf, name='trip_pdf'),
    path('m/trip/<int:trip_id>/pdf/', report.trip_pdf, name='m_trip_pdf'),
    path('<int:trip_id>/wish-list/', views.trip, name='trip_wishlist'),
    path('<int:trip_id>/place/new/', views_places.place_new,
         name='place_new'),
    path('place/<int:place_id>/', views_places.place, name='place'),
    path('place/<int:place_id>/move/', views_places.place_move,
         name='place_move'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
    path('place/<int:place_id>/again/', views_places.place_again,
         name='place_again'),
    path('place/<int:place_id>/delete/', views_places.place_delete,
         name='place_delete'),
    path('m/trip/<int:trip_id>/place/new/', views_places.place_new,
         name='m_place_new'),
    path('m/place/<int:place_id>/', views_places.place, name='m_place'),
    # The phone posts under m/: its 30-day session covers only /travel/m/.
    path('m/place/<int:place_id>/move/', views_places.place_move,
         name='m_place_move'),
    path('m/place/<int:place_id>/done/', views_places.place_done,
         name='m_place_done'),
    path('m/place/<int:place_id>/again/', views_places.place_again,
         name='m_place_again'),
    path('m/place/<int:place_id>/delete/', views_places.place_delete,
         name='m_place_delete'),
    path('<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''
def span(trip, bookings):
    """The trip's dates: as set, else from its bookings."""
    days = [d for b in bookings for d in (b.start_date, b.end_date) if d]
    start = trip.start_date or (min(days) if days else None)
    end = trip.end_date or (max(days) if days else None)
    return start, end

''',
         r'''
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
    seen = []
    for c in [getattr(b, 'country', '') for b in sorted(
            live, key=lambda b: b.start_date or dt.date.max)] + \
            trip.country_list:
        c = (c or '').strip()
        if c and c.lower() not in [x.lower() for x in seen]:
            seen.append(c)
    trip.where = ', '.join(seen)
    trip.where_list = seen
    return start, end

'''),
        (r'''

def phone_qr(request):
    from .barcodes import svg
''',
         r'''

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
'''),
        (r'''        if start:
            years.add(start.year)
        countries.update(t.country_list)
        t.past = bool(end and end < today)
        rows.append(t)
''',
         r'''        if start:
            years.add(start.year)
        countries.update(t.where_list)
        t.past = bool(end and end < today)
        rows.append(t)
'''),
        (r'''        sel = [t for t in rows if t.start and t.start.year == int(show)]
    elif show.startswith('c:'):
        sel = [t for t in rows if show[2:] in t.country_list]
    else:
        show, sel = 'all', rows
''',
         r'''        sel = [t for t in rows if t.start and t.start.year == int(show)]
    elif show.startswith('c:'):
        sel = [t for t in rows if show[2:] in t.where_list]
    else:
        show, sel = 'all', rows
'''),
        (r'''        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        # TR-3 - point the phone's camera at this to open the phone app.
        'phone_qr': phone_qr(request),
        'requests': requests_for(request.user)})

''',
         r'''        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
        'new_open': request.GET.get('new') == '1' or not rows,
        # TR-3 - point the phone's camera at this to open the phone app.
        # TR-4 - only when the Phone app button is pressed.
        'phone_qr': phone_qr(request) if request.GET.get('phone') == '1'
        else '',
        'requests': requests_for(request.user)})

'''),
        (r'''def trip(request, trip_id):
    t = _trip(request, trip_id)
    tab = 'costs' if request.resolver_match.url_name == 'trip_costs' \
        else 'bookings'
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    bs = [shape(b) for b in bs]
    start, end = span(t, bs)
    days = OrderedDict()
    undated = []
''',
         r'''def trip(request, trip_id):
    t = _trip(request, trip_id)
    tab = {'trip_costs': 'costs', 'trip_itinerary': 'itinerary',
           'trip_wishlist': 'wish'}.get(request.resolver_match.url_name,
                                        'bookings')
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
    pl = list(t.places.all())
    from .phone import itinerary
    days = OrderedDict()
    undated = []
'''),
        (r'''        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
        'requests': requests_for(request.user, t)})


''',
         r'''        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
        'requests': requests_for(request.user, t),
        # TR-4 - the itinerary (every day, bookings and places) and the
        # wish list (places with no day yet).
        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'planned': len([p for p in pl if p.day]),
        'trip_days': days_of(start, end)})


'''),
        (r'''            return redirect('travel:trip', trip_id=t.pk)
        messages.error(request, 'Give the trip a name.')
    return render(request, 'travel/trip_form.html', {
        'trip': t, 'is_owner': t.owner_id == request.user.id})
''',
         r'''            return redirect('travel:trip', trip_id=t.pk)
        messages.error(request, 'Give the trip a name.')
    t.start, t.end = span(t, list(t.bookings.all()))
    return render(request, 'travel/trip_form.html', {
        'trip': t, 'is_owner': t.owner_id == request.user.id})
'''),
        (r'''               ('segment', 40), ('from_place', 120), ('to_place', 120),
               ('address', 255), ('phone', 40), ('link', 500),
               ('traveller_names', 255))


''',
         r'''               ('segment', 40), ('from_place', 120), ('to_place', 120),
               ('address', 255), ('phone', 40), ('link', 500),
               ('traveller_names', 255), ('city', 80), ('country', 60))


'''),
        (r'''        if b.kind == 'stay' and b.start_date and b.end_date else None
    from .phone import pass_card
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
''',
         r'''        if b.kind == 'stay' and b.start_date and b.end_date else None
    from .phone import pass_card
    if b.amount is None:
        others = [x for x in b.trip.bookings.all() if x.pk != b.pk]
        included(others + [b])
    else:
        b.included = None
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_booking_row.html'), [
        (r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span></span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% endif %}</span>
</a>
''',
         r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span></span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-passcode svg, .tv-phone svg { display: block; width: 100%; height: auto; }
.tv-phone { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 14px; align-items: center; max-width: 560px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
''',
         r'''.tv-passcode svg, .tv-phone svg { display: block; width: 100%; height: auto; }
.tv-phone { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 14px; align-items: center; max-width: 560px; }
.tv-place .tv-ico { background: transparent; border: 1px dashed var(--alv-line); }
.tv-passgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 340px)); gap: 18px; align-items: start; }
.tv-wpass { position: relative; border-radius: 18px; overflow: hidden; border: 1px solid var(--alv-line); }
.tv-wpass.is-next { outline: 3px solid var(--alv-accent); outline-offset: 2px; }
.tv-wpass-flag { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); padding: 1px 10px; border-radius: 999px; border: 1px solid #fff; color: #fff; font-size: 0.72rem; font-weight: 700; }
.tv-wpass-top { background: #123B5C; color: #fff; padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 6px; }
.tv-wpass-code { font-size: 2.1rem; font-weight: 700; letter-spacing: .02em; line-height: 1.1; }
.tv-wpass-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; }
.tv-wpass-grid small { display: block; font-size: 0.68rem; opacity: .8; }
.tv-wpass-foot { padding: 12px 16px 14px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking_form.html'), [
        (r'''        <div><label for="tp">To</label><input id="tp" name="to_place" class="form-control" maxlength="120" value="{{ b.to_place }}" placeholder="e.g. Lisbon (LIS)"></div>
        <div class="tv-wide"><label for="ad">Address</label><input id="ad" name="address" class="form-control" maxlength="255" value="{{ b.address }}"></div>
        <div><label for="ph">Phone</label><input id="ph" name="phone" class="form-control" maxlength="40" value="{{ b.phone }}" inputmode="tel"></div>
        <div><label for="lk">Manage-booking link</label><input id="lk" name="link" class="form-control" maxlength="500" value="{{ b.link }}" inputmode="url"></div>
''',
         r'''        <div><label for="tp">To</label><input id="tp" name="to_place" class="form-control" maxlength="120" value="{{ b.to_place }}" placeholder="e.g. Lisbon (LIS)"></div>
        <div class="tv-wide"><label for="ad">Address</label><input id="ad" name="address" class="form-control" maxlength="255" value="{{ b.address }}"></div>
        <div><label for="cy">City</label><input id="cy" name="city" class="form-control" maxlength="80" value="{{ b.city }}"></div>
        <div><label for="cn">Country</label><input id="cn" name="country" class="form-control" maxlength="60" value="{{ b.country }}" placeholder="The trip&rsquo;s countries come from these"></div>
        <div><label for="ph">Phone</label><input id="ph" name="phone" class="form-control" maxlength="40" value="{{ b.phone }}" inputmode="tel"></div>
        <div><label for="lk">Manage-booking link</label><input id="lk" name="link" class="form-control" maxlength="500" value="{{ b.link }}" inputmode="url"></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_new' trip.pk %}" class="btn action-primary"><i class="fas fa-plus"></i> Add booking</a>
    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
''',
         r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_new' trip.pk %}" class="btn action-primary"><i class="fas fa-plus"></i> Add booking</a>
    <a href="{% url 'travel:place_new' trip.pk %}" class="btn action-secondary"><i class="fas fa-map-marker-alt"></i> Add a place</a>
    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    {% comment %} TR-4 (Demetri, 15 Nov): the trip as a PDF, summary or detailed, to download or share (WhatsApp, mail) through the house PDF viewer. {% endcomment %}
    <button type="button" class="btn action-secondary" data-trip-pdf="summary" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><i class="fas fa-file-pdf"></i> PDF summary</button>
    <button type="button" class="btn action-secondary" data-trip-pdf="detailed" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><i class="fas fa-file-pdf"></i> PDF detailed</button>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
'''),
        (r'''<div class="tv-wrap">
{% include 'travel/_requests.html' %}
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.countries %} · {{ trip.countries }}{% endif %}</p>

<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>
</nav>
''',
         r'''<div class="tv-wrap">
{% include 'travel/_requests.html' %}
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</p>

<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary{% if planned %} <span class="tv-sub">{{ planned }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Wish list{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>
</nav>
'''),
        (r'''    </section>
    {% endif %}
{% else %}
    <section class="form-card" data-costs>
''',
         r'''    </section>
    {% endif %}
{% elif tab == 'itinerary' %}
    {% comment %} TR-4 - every day of the trip: the bookings (shaded) and the places planned, in time order. {% endcomment %}
    {% if itinerary %}
    <nav class="tv-chips" aria-label="Days">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}">{{ day|date:"D j" }}</a>{% endfor %}</nav>
    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Add a place</a></div>
        {% for r in rows %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">wish list</a>{% endif %}.</p>{% endfor %}
    </section>
    {% endfor %}
    {% else %}
    <section class="form-card"><p style="margin: 0">The itinerary needs the trip&rsquo;s dates: add a booking, or set From and To under Edit trip.</p></section>
    {% endif %}
{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. {% endcomment %}
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Wish list</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Add a place</a></div>
        {% for p in wish %}
        <div data-wish-item>
            {% include 'travel/_place_row.html' %}
            {% if trip_days %}<form method="post" action="{% url 'travel:place_move' p.pk %}" class="tv-acts" style="margin: 0 0 8px 52px">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}">
                <label for="mv{{ p.pk }}" class="small" style="margin: 0">Put on</label>
                <select id="mv{{ p.pk }}" name="day" class="form-control form-control-sm" style="max-width: 170px">{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
                <input type="time" name="time" class="form-control form-control-sm" style="max-width: 120px" aria-label="Time (optional)">
                <button type="submit" class="btn action-secondary btn-sm">Move</button></form>{% endif %}
        </div>
        {% empty %}<p class="tv-sub" style="margin: 8px 0 0">Nothing yet. Add a museum, a garden, a restaurant &mdash; type its name or paste a link, and its address, hours and price are looked up for you. On the phone, share a place from Google Maps to Travel.</p>{% endfor %}
    </section>
{% else %}
    <section class="form-card" data-costs>
'''),
        (r'''</div>
</div>
{% render_help_modal "travel" %}
{% endblock %}
''',
         r'''</div>
</div>
{% include 'components/pdf_viewer.html' %}
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_form.html'), [
        (r'''    <div class="tv-form-grid">
        <div class="tv-wide"><label for="tn">Name <span class="req-marker" aria-hidden="true">*</span></label><input id="tn" name="name" class="form-control" maxlength="120" required value="{{ trip.name }}"></div>
        <div><label for="ts">From</label><input id="ts" type="date" name="start_date" class="form-control" value="{{ trip.start_date|date:'Y-m-d' }}"></div>
        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control" value="{{ trip.end_date|date:'Y-m-d' }}"></div>
        <div class="tv-wide"><label for="tc">Countries</label><input id="tc" name="countries" class="form-control" maxlength="200" value="{{ trip.countries }}"></div>
        <div class="tv-wide"><label for="no">Notes</label><textarea id="no" name="notes" class="form-control" rows="4">{{ trip.notes }}</textarea></div>
        <div class="tv-wide tv-sub small">Leave the dates empty and they follow the bookings.</div>
        <div class="tv-wide"><button type="submit" class="btn action-primary">Save trip</button>
        {% if is_owner %}<button type="submit" form="del-trip" class="btn action-secondary action-danger">Delete trip</button>{% endif %}</div>
''',
         r'''    <div class="tv-form-grid">
        <div class="tv-wide"><label for="tn">Name <span class="req-marker" aria-hidden="true">*</span></label><input id="tn" name="name" class="form-control" maxlength="120" required value="{{ trip.name }}"></div>
        {% if trip.by_bookings %}
        <div class="tv-wide" data-dates-by-bookings><label>Dates</label><p class="form-control-plaintext" style="margin: 0"><b>{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}</b> <span class="tv-sub small">&middot; set by its bookings, first to last. They change when the bookings do.</span></p>
        <input type="hidden" name="start_date" value="{{ trip.start_date|date:'Y-m-d' }}"><input type="hidden" name="end_date" value="{{ trip.end_date|date:'Y-m-d' }}"></div>
        {% else %}
        <div><label for="ts">From</label><input id="ts" type="date" name="start_date" class="form-control" value="{{ trip.start_date|date:'Y-m-d' }}"></div>
        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control" value="{{ trip.end_date|date:'Y-m-d' }}"></div>
        {% endif %}
        <div class="tv-wide"><label for="tc">Countries</label><input id="tc" name="countries" class="form-control" maxlength="200" value="{{ trip.countries }}">{% if trip.where and trip.where != trip.countries %}<div class="tv-sub small">Shown as <b>{{ trip.where }}</b> &mdash; the bookings&rsquo; countries with any you type here.</div>{% endif %}</div>
        <div class="tv-wide"><label for="no">Notes</label><textarea id="no" name="notes" class="form-control" rows="4">{{ trip.notes }}</textarea></div>
        {% if not trip.by_bookings %}<div class="tv-wide tv-sub small">For planning before anything is booked. Once the trip has bookings with dates, its dates come from them.</div>{% endif %}
        <div class="tv-wide"><button type="submit" class="btn action-primary">Save trip</button>
        {% if is_owner %}<button type="submit" form="del-trip" class="btn action-secondary action-danger">Delete trip</button>{% endif %}</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''
<div class="page-action-buttons">
    <a href="#new-trip" class="btn action-primary" data-new-trip><i class="fas fa-plus"></i> New trip</a>
    <a href="{% url 'travel:check' %}" class="btn action-secondary" data-to-check><i class="fas fa-inbox"></i> To check{% if checks %} <span class="tv-count">{{ checks }}</span>{% endif %}</a>
    <a href="{% url 'travel:forwarding' %}" class="btn action-secondary"><i class="fas fa-envelope"></i> Forwarding</a>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''
<div class="page-action-buttons">
    <a href="?show={{ show }}&amp;new=1#new-trip" class="btn action-primary" data-new-trip><i class="fas fa-plus"></i> New trip</a>
    <a href="{% url 'travel:check' %}" class="btn action-secondary" data-to-check><i class="fas fa-inbox"></i> To check{% if checks %} <span class="tv-count">{{ checks }}</span>{% endif %}</a>
    <a href="{% url 'travel:forwarding' %}" class="btn action-secondary"><i class="fas fa-envelope"></i> Forwarding</a>
    <a href="{% url 'travel:passes' %}" class="btn action-secondary" data-passes-button><i class="fas fa-qrcode"></i> Boarding passes</a>
    <a href="?show={{ show }}&amp;phone=1" class="btn action-secondary" data-phone-button><i class="fas fa-mobile-alt"></i> Phone app</a>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included. Forward booking emails to <b>{{ address }}</b> and they wait for you under <a href="{% url 'travel:check' %}">To check</a>.</p>

{% if count %}
<nav class="tv-chips" aria-label="Show">
''',
         r'''<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included. Forward booking emails to <b>{{ address }}</b> and they wait for you under <a href="{% url 'travel:check' %}">To check</a>.</p>

{% comment %} TR-4 (Demetri, 15 Nov): used once per person, so it sits behind the Phone app button, not on the page all the time. {% endcomment %}
{% if phone_qr %}
<section class="form-card tv-phone" data-phone-app style="margin: 4px 0 18px">
    <div class="tv-passcode" style="margin: 0">{{ phone_qr|safe }}</div>
    <div><h3 class="form-section-title" style="margin: 0 0 4px">Travel on your phone</h3><p class="small" style="margin: 0">Point your phone&rsquo;s camera here, or open <b>alivente.online/travel/m/</b>, then <em>Add to Home screen</em>. Today, your boarding passes (even with no signal) and To check &mdash; and on Android, <em>Share &rarr; Travel</em> sends a ticket or an email straight in.</p><div class="small" style="margin-top: 8px"><a href="?show={{ show }}">Close</a></div></div>
</section>
{% endif %}
{% comment %} TR-4 (Demetri, 15 Nov): the New trip form shows only when + New trip is pressed - or when there is no trip yet. {% endcomment %}
{% if new_open %}
<section class="form-card" id="new-trip" style="margin: 4px 0 18px; max-width: 820px">
    <h3 class="form-section-title">New trip</h3>
    <form method="post" action="{% url 'travel:trip_new' %}" class="tv-form-grid">
        {% csrf_token %}
        <div class="tv-wide"><label for="tn">Name</label><input id="tn" name="name" class="form-control" maxlength="120" required placeholder="e.g. Lisbon &amp; Porto"></div>
        <div><label for="ts">From</label><input id="ts" type="date" name="start_date" class="form-control"></div>
        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control"></div>
        <div class="tv-wide"><label for="tc">Countries</label><input id="tc" name="countries" class="form-control" maxlength="200" placeholder="e.g. Portugal, Spain"></div>
        <div class="tv-wide tv-sub small">The dates are for planning: once the trip has bookings, its dates come from them.</div>
        <div class="tv-wide"><button type="submit" class="btn action-primary"><i class="fas fa-plus"></i> Create trip</button> <a href="?show={{ show }}" class="btn action-secondary">Cancel</a></div>
    </form>
</section>
{% endif %}
{% if count %}
<nav class="tv-chips" aria-label="Show">
'''),
        (r'''    <a class="tv-card form-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p>{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.countries %} · {{ t.countries }}{% endif %}</div>
        <div class="tv-row small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span class="tv-people">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
        {% if t.money.any %}
''',
         r'''    <a class="tv-card form-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p>{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
        <div class="tv-row small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span class="tv-people">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
        {% if t.money.any %}
'''),
        (r'''    </a>
{% empty %}
    <p class="text-muted">{% if count %}No trips here.{% else %}No trips yet. Start one below.{% endif %}</p>
{% endfor %}
</div>

{% if phone_qr %}
<section class="form-card tv-phone" data-phone-app style="margin-top: 22px">
    <div class="tv-passcode" style="margin: 0">{{ phone_qr|safe }}</div>
    <div><h3 class="form-section-title" style="margin: 0 0 4px">Travel on your phone</h3><p class="small" style="margin: 0">Point your phone&rsquo;s camera here, or open <b>alivente.online/travel/m/</b>, then <em>Add to Home screen</em>. Today, your boarding passes (even with no signal) and To check &mdash; and on Android, <em>Share &rarr; Travel</em> sends a ticket or an email straight in.</p></div>
</section>
{% endif %}

<section class="form-card" id="new-trip" style="margin-top: 22px; max-width: 820px">
    <h3 class="form-section-title">New trip</h3>
    <form method="post" action="{% url 'travel:trip_new' %}" class="tv-form-grid">
        {% csrf_token %}
        <div class="tv-wide"><label for="tn">Name</label><input id="tn" name="name" class="form-control" maxlength="120" required placeholder="e.g. Lisbon &amp; Porto"></div>
        <div><label for="ts">From</label><input id="ts" type="date" name="start_date" class="form-control"></div>
        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control"></div>
        <div class="tv-wide"><label for="tc">Countries</label><input id="tc" name="countries" class="form-control" maxlength="200" placeholder="e.g. Portugal, Spain"></div>
        <div class="tv-wide"><button type="submit" class="btn action-primary"><i class="fas fa-plus"></i> Create trip</button></div>
    </form>
</section>
</div>
{% render_help_modal "travel" %}
''',
         r'''    </a>
{% empty %}
    <p class="text-muted">{% if count %}No trips here.{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>




</div>
{% render_help_modal "travel" %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', '_row.html'), [
        (r'''{% comment %} TR-3 - one booking as a row on the phone. {% endcomment %}<a href="{% url 'travel:m_booking' b.pk %}" class="tv-item{% if b.cancelled %} tv-off{% endif %}" data-booking>
  <span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span>
  <span style="min-width: 0"><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag due">Cancelled</span>{% endif %}
    <span class="tv-muted" style="display: block">{% if b.when %}<span class="tv-time">{{ b.when|time:"H:i" }}</span>{% elif b.start_time and not b.label %}<span class="tv-time">{{ b.start_time|time:"H:i" }}</span>{% endif %}{% if b.route %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.route }}{% elif b.address %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.address|truncatechars:40 }}{% endif %}{% if b.reference %}{% if b.when or b.route or b.address or b.start_time and not b.label %} · {% endif %}{{ b.reference }}{% endif %}</span></span>
  <span class="tv-muted" aria-hidden="true">›</span>
</a>
''',
         r'''{% comment %} TR-3 - one booking as a row on the phone; TR-4 - or a place. {% endcomment %}{% if b.is_place %}<a href="{% url 'travel:m_place' b.pk %}" class="tv-item{% if b.done %} tv-off{% endif %}" data-place>
  <span class="tv-ico" style="background: transparent; border: 1px dashed currentColor">{% include 'travel/m/_icon.html' with kind='other' %}</span>
  <span style="min-width: 0"><b>{{ b.name }}</b>{% if b.lookup == 'waiting' %} <span class="tv-tag sh">Looking it up</span>{% endif %}
    <span class="tv-muted" style="display: block">{% if b.time %}<span class="tv-time">{{ b.time|time:"H:i" }}</span>{% if b.hours or b.price %} · {% endif %}{% endif %}{% if b.hours %}{{ b.hours|truncatechars:40 }}{% endif %}{% if b.price %}{% if b.hours %} · {% endif %}{{ b.price|truncatechars:30 }}{% endif %}</span></span>
  <span class="tv-muted" aria-hidden="true">›</span>
</a>{% else %}<a href="{% url 'travel:m_booking' b.pk %}" class="tv-item{% if b.cancelled %} tv-off{% endif %}" data-booking>
  <span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span>
  <span style="min-width: 0"><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag due">Cancelled</span>{% endif %}
    <span class="tv-muted" style="display: block">{% if b.when %}<span class="tv-time">{{ b.when|time:"H:i" }}</span>{% elif b.start_time and not b.label %}<span class="tv-time">{{ b.start_time|time:"H:i" }}</span>{% endif %}{% if b.route %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.route }}{% elif b.address %}{% if b.when or b.start_time and not b.label %} · {% endif %}{{ b.address|truncatechars:40 }}{% endif %}{% if b.reference %}{% if b.when or b.route or b.address or b.start_time and not b.label %} · {% endif %}{{ b.reference }}{% endif %}</span></span>
  <span class="tv-muted" aria-hidden="true">›</span>
</a>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'today.html'), [
        (r'''<a href="{% url 'travel:m_trip' trip.pk %}" class="tv-card" data-next-trip>
  <div class="tv-row"><p class="tv-h2">{{ trip.name }}</p><span class="tv-tag sh">{% if in_days == 1 %}Tomorrow{% else %}In {{ in_days }} days{% endif %}</span></div>
  <div class="tv-muted">{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% if trip.countries %} · {{ trip.countries }}{% endif %}</div>
</a>
<p class="tv-h3">The first day · {{ trip.start|date:"D j M" }}</p>
''',
         r'''<a href="{% url 'travel:m_trip' trip.pk %}" class="tv-card" data-next-trip>
  <div class="tv-row"><p class="tv-h2">{{ trip.name }}</p><span class="tv-tag sh">{% if in_days == 1 %}Tomorrow{% else %}In {{ in_days }} days{% endif %}</span></div>
  <div class="tv-muted">{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>
</a>
<p class="tv-h3">The first day · {{ trip.start|date:"D j M" }}</p>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block title %}{{ trip.name }} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.countries %} · {{ trip.countries }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip"><a class="tv-tab{% if not costs %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if costs %} on{% endif %}" href="?tab=costs">Costs</a></nav>{% endblock %}
{% block content %}
{% if costs %}
<section class="tv-card" data-costs>
  <div class="tv-row"><span class="tv-muted">Total</span><b style="font-size: 20px">{{ money.total|default:"€0" }}</b></div>
''',
         r'''{% block title %}{{ trip.name }} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Wish list</a><a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
{% comment %} TR-4 - the itinerary: every day, bookings and places in time order. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Add a place</a>
{% if itinerary %}
<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">Add a place</a></p>{% endfor %}</section>
{% endfor %}
{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - the wish list: places with no day yet. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Add a place</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
  {% include 'travel/m/_row.html' with b=p %}
  {% if trip_days %}<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-inline">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}">
    <select name="day" class="tv-select" style="flex: 1" aria-label="Put {{ p.name }} on a day">{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
    <button type="submit" class="tv-btn sec">Put on the day</button></form>{% endif %}
</section>
{% empty %}
<section class="tv-card"><p class="tv-muted" style="margin: 0">Nothing yet. Add a museum, a garden or a restaurant &mdash; or in Google Maps tap <b>Share &rarr; Travel</b>.</p></section>
{% endfor %}
{% elif costs %}
<section class="tv-card" data-costs>
  <div class="tv-row"><span class="tv-muted">Total</span><b style="font-size: 20px">{{ money.total|default:"€0" }}</b></div>
'''),
        (r'''</section>
{% if money.by_kind %}<section class="tv-card">{% for k in money.by_kind %}<div class="tv-row"><span>{{ k.kind }}</span><b>{{ k.eur }}</b></div>{% endfor %}</section>{% endif %}
<section class="tv-card">{% for b in bookings %}{% if b.amount is not None %}<a href="{% url 'travel:m_booking' b.pk %}" class="tv-item{% if b.cancelled %} tv-off{% endif %}"><span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span><span style="min-width: 0"><b>{{ b.title }}</b><span class="tv-muted" style="display: block">{% if b.orig_label %}{{ b.orig_label }} · {% endif %}{{ b.status_label }}</span></span><b>{{ b.eur_label|default:"…" }}</b></a>{% endif %}{% endfor %}</section>
{% else %}
{% if coming %}<section class="tv-card" data-coming>{% for c in coming %}<div class="tv-small"><b style="color: var(--tv-warn)">{{ c.what }}</b> · {{ c.day|date:"D j M" }} · {{ c.sub }}</div>{% endfor %}</section>{% endif %}
''',
         r'''</section>
{% if money.by_kind %}<section class="tv-card">{% for k in money.by_kind %}<div class="tv-row"><span>{{ k.kind }}</span><b>{{ k.eur }}</b></div>{% endfor %}</section>{% endif %}
<section class="tv-card">{% for b in bookings %}{% if b.included %}<a href="{% url 'travel:m_booking' b.pk %}" class="tv-item"><span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span><span style="min-width: 0"><b>{{ b.title }}</b></span><span class="tv-muted tv-small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span></a>{% endif %}{% if b.amount is not None %}<a href="{% url 'travel:m_booking' b.pk %}" class="tv-item{% if b.cancelled %} tv-off{% endif %}"><span class="tv-ico">{% include 'travel/m/_icon.html' with kind=b.kind %}</span><span style="min-width: 0"><b>{{ b.title }}</b><span class="tv-muted" style="display: block">{% if b.orig_label %}{{ b.orig_label }} · {% endif %}{{ b.status_label }}</span></span><b>{{ b.eur_label|default:"…" }}</b></a>{% endif %}{% endfor %}</section>
{% else %}
{% if coming %}<section class="tv-card" data-coming>{% for c in coming %}<div class="tv-small"><b style="color: var(--tv-warn)">{{ c.what }}</b> · {{ c.day|date:"D j M" }} · {{ c.sub }}</div>{% endfor %}</section>{% endif %}
'''),
        (r'''{% if not bookings %}<section class="tv-card"><p class="tv-muted" style="margin: 0">No bookings yet.</p></section>{% endif %}
{% endif %}
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% endblock %}
''',
         r'''{% if not bookings %}<section class="tv-card"><p class="tv-muted" style="margin: 0">No bookings yet.</p></section>{% endif %}
{% endif %}
{% comment %} TR-4 - the trip as a PDF, straight to the phone's share sheet (WhatsApp, mail...); opened instead where sharing files is not possible. {% endcomment %}
<div class="tv-btns" data-trip-pdf-phone>
  <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=summary" data-share-name="trip_{{ trip.name|slugify }}_summary.pdf" data-share-title="{{ trip.name }}">PDF summary</button>
  <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=detailed" data-share-name="trip_{{ trip.name|slugify }}_detailed.pdf" data-share-title="{{ trip.name }}">PDF detailed</button>
</div>
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trips.html'), [
        (r'''<a href="{% url 'travel:m_trip' t.pk %}" class="tv-card" data-trip>
  <div class="tv-row"><p class="tv-h2">{{ t.name }}</p>{% if t.people|length > 1 %}<span class="tv-tag sh">Shared</span>{% endif %}</div>
  <div class="tv-muted">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.countries %} · {{ t.countries }}{% endif %}</div>
  <div class="tv-row tv-small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span style="display: flex; padding-left: 6px">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
  {% if t.money.any %}<div class="tv-meter" aria-hidden="true"><span style="width: {{ t.money.pct }}%"></span></div>
''',
         r'''<a href="{% url 'travel:m_trip' t.pk %}" class="tv-card" data-trip>
  <div class="tv-row"><p class="tv-h2">{{ t.name }}</p>{% if t.people|length > 1 %}<span class="tv-tag sh">Shared</span>{% endif %}</div>
  <div class="tv-muted">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
  <div class="tv-row tv-small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span style="display: flex; padding-left: 6px">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
  {% if t.money.any %}<div class="tv-meter" aria-hidden="true"><span style="width: {{ t.money.pct }}%"></span></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_edit' b.pk %}" class="btn action-primary"><i class="fas fa-pen"></i> Edit</a>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_edit' b.pk %}" class="btn action-primary"><i class="fas fa-pen"></i> Edit</a>
    {% comment %} TR-4 (Demetri, 15 Nov): delete without going into Edit first. {% endcomment %}
    <button type="submit" form="del-booking-view" class="btn action-secondary action-danger" data-delete-booking><i class="fas fa-trash-alt"></i> Delete</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''        {% if b.paid != 'paid' %}<div class="tv-row"><span class="tv-sub">Still to pay</span><b class="tv-due">{{ due_label|default:"–" }}</b></div>{% endif %}
        {% if b.pay_by and b.paid != 'paid' %}<div class="tv-sub small">Pay by {{ b.pay_by|date:"D j M Y" }}</div>{% endif %}
        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
''',
         r'''        {% if b.paid != 'paid' %}<div class="tv-row"><span class="tv-sub">Still to pay</span><b class="tv-due">{{ due_label|default:"–" }}</b></div>{% endif %}
        {% if b.pay_by and b.paid != 'paid' %}<div class="tv-sub small">Pay by {{ b.pay_by|date:"D j M Y" }}</div>{% endif %}
        {% elif b.included %}<p class="tv-sub" style="margin: 0" data-included>Included in the price of <a href="{% url 'travel:booking' b.included.pk %}">{{ b.included.segment|default:b.included.title }}</a> &mdash; one booking, one price.</p>
        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
'''),
        (r'''</aside>
</div>
{% endblock %}
''',
         r'''</aside>
</div>
<form id="del-booking-view" method="post" action="{% url 'travel:booking_delete' b.pk %}" onsubmit="return confirm('Delete {{ b.title|escapejs }} and its documents? This cannot be undone.');">{% csrf_token %}</form>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-dots span.on { background: var(--tv-teal); }
.tv-in-app .tv-out { display: none; }
@media (prefers-color-scheme: dark) {
  body, .tv-app { background: #11191C; color: #E6ECEE; }
''',
         r'''.tv-dots span.on { background: var(--tv-teal); }
.tv-in-app .tv-out { display: none; }
/* TR-4 - Passes held upright when the phone is turned and the screen
   rotated anyway: the page is turned back by the same angle. */
html.tv-turn-90 body.tv-holding .tv-app, html.tv-turn-270 body.tv-holding .tv-app { position: fixed; top: 50%; left: 50%; width: 100vh; height: 100vw; max-width: none; overflow: auto; transform-origin: center center; }
html.tv-turn-90 body.tv-holding .tv-app { transform: translate(-50%, -50%) rotate(-90deg); }
html.tv-turn-270 body.tv-holding .tv-app { transform: translate(-50%, -50%) rotate(90deg); }
html.tv-turn-90 body.tv-holding .tv-nav, html.tv-turn-270 body.tv-holding .tv-nav { position: sticky; }
@media (prefers-color-scheme: dark) {
  body, .tv-app { background: #11191C; color: #E6ECEE; }
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.js'), [
        (r'''      if (document.visibilityState === 'visible') { upright(); }
    });
    window.addEventListener('pagehide', function () {
      try { if (screen.orientation && screen.orientation.unlock) { screen.orientation.unlock(); } } catch (e) {}
''',
         r'''      if (document.visibilityState === 'visible') { upright(); }
    });
    // Where the phone will not hold the screen upright (a browser tab, an
    // iPhone), turn the passes back the other way, so the pass stays
    // where it was in the hand however the phone is turned.
    function counter() {
      var a = (screen.orientation && typeof screen.orientation.angle === 'number')
        ? screen.orientation.angle : (window.orientation || 0);
      a = ((a % 360) + 360) % 360;
      html.classList.toggle('tv-turn-90', a === 90);
      html.classList.toggle('tv-turn-270', a === 270);
    }
    counter();
    if (screen.orientation && screen.orientation.addEventListener) {
      screen.orientation.addEventListener('change', counter);
    }
    window.addEventListener('orientationchange', counter);
    window.addEventListener('resize', counter);
    window.addEventListener('pagehide', function () {
      try { if (screen.orientation && screen.orientation.unlock) { screen.orientation.unlock(); } } catch (e) {}
'''),
        (r'''    }, {passive: true});
  }
  // Confirm before a destructive button.
  document.querySelectorAll('[data-confirm]').forEach(function (b) {
''',
         r'''    }, {passive: true});
  }
  // TR-4 - a trip's PDF to the phone's share sheet; opened where the phone
  // cannot share files.
  document.querySelectorAll('[data-share-pdf]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = b.getAttribute('data-share-pdf');
      var label = b.textContent;
      b.disabled = true;
      b.textContent = 'Making the PDF…';
      fetch(url, {credentials: 'same-origin'}).then(function (r) {
        if (!r.ok) { throw new Error('pdf'); }
        return r.blob();
      }).then(function (blob) {
        var file = new File([blob], b.getAttribute('data-share-name'), {type: 'application/pdf'});
        if (navigator.canShare && navigator.share && navigator.canShare({files: [file]})) {
          return navigator.share({files: [file], title: b.getAttribute('data-share-title')});
        }
        window.location.href = url;
      }).catch(function (e) {
        if (!e || e.name !== 'AbortError') { window.location.href = url; }
      }).then(function () { b.disabled = false; b.textContent = label; });
    });
  });
  // Confirm before a destructive button.
  document.querySelectorAll('[data-confirm]').forEach(function (b) {
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv3-1">
</head>
<body>
<div class="tv-app">
  <header class="tv-top">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv4-1">
</head>
<body{% block body_attr %}{% endblock %}>
<div class="tv-app">
  <header class="tv-top">
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv3-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv4-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'booking.html'), [
        (r'''  </dl>
</section>
{% if b.amount is not None %}
<section class="tv-card" data-cost>
''',
         r'''  </dl>
</section>
{% if b.included and b.amount is None %}<section class="tv-card" data-included><p class="tv-muted" style="margin: 0">Included in the price of <a href="{% url 'travel:m_booking' b.included.pk %}">{{ b.included.segment|default:b.included.title }}</a>.</p></section>{% endif %}
{% if b.amount is not None %}
<section class="tv-card" data-cost>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on and does not turn sideways (in the installed app on Android). Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'passes.html'), [
        (r'''{% comment %} TR-3 - boarding passes, wallet-style: one a screen, swiped sideways, the barcode drawn again from the airline's own code. Kept on the phone for when there is no signal. {% endcomment %}
{% block title %}Passes - Travel{% endblock %}
{% block top %}<h1>Passes</h1>{% endblock %}
{% block sub %}<div class="sub">{% if every %}Every pass{% else %}The next one you need first{% endif %}</div>{% endblock %}
''',
         r'''{% comment %} TR-3 - boarding passes, wallet-style: one a screen, swiped sideways, the barcode drawn again from the airline's own code. Kept on the phone for when there is no signal. {% endcomment %}
{% block title %}Passes - Travel{% endblock %}
{% block body_attr %} class="tv-holding"{% endblock %}
{% block top %}<h1>Passes</h1>{% endblock %}
{% block sub %}<div class="sub">{% if every %}Every pass{% else %}The next one you need first{% endif %}</div>{% endblock %}
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
    raise SystemExit('TR-4 REFUSED: %s' % msg)


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
    if "'test_travel_four.py'" in read(pq):
        print('TR-4 already applied.')
        return 0
    if "'test_travel_three.py'" not in read(pq):
        refuse('Release 84 is not applied - this round registers after it.')
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
        print('TR-4 --check: %d file(s) would change, none written; %d '
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
    print('TR-4 applied - Travel, stage 4. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
