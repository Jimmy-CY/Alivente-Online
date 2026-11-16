# -*- coding: utf-8 -*-
"""apply_travel_five.py - round TR-5, 16 Nov 2026.

RELEASE 86 - TRAVEL: RESTAURANTS, AND DEMETRI'S REVIEW OF STAGE 4.

    - A Restaurant kind of booking: a table at a restaurant, read from the
      restaurant's, TheFork's or OpenTable's email, with its own icon.
    - A booking for a place on the wish list takes that place onto its
      day and time; it shows once on the itinerary - as the booking.
      Cancelled or deleted, the place goes back to the wish list.
    - One PDF button with Summary and Detailed under it (computer, phone).
      The detailed itinerary gives each hotel's and restaurant's address,
      phone and check-in / check-out times on its day; what a booking is
      missing is looked up on the web once, filling blanks only.
    - The trip's countries from its bookings - also the older ones, from
      their address, airport or town - and never the home country.
    - One traveller, not two, when a boarding pass writes the name the
      other way round.
    - Add a place: generous with names; the trip's destination only breaks
      ties; two or three possible places are offered to choose from; Try
      again looks up the name now in the box.
    - Move needs a day; Back to the wish list; every place button says
      what it does on hover; the Itinerary tab loses its misleading count.

New files ship beside this patcher. Stands on Release 85. Idempotent.
Edits backed up to .bak_travel5.
MIGRATION: travel 0005 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_travel5'
MARK = 'TR-5, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/where.py',
    'travel/migrations/0005_restaurants.py',
    'test_travel_five.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - the itinerary, the
    # wish list, places; trip dates from the bookings.
    'test_travel_four.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - the itinerary, the
    # wish list, places; trip dates from the bookings.
    'test_travel_four.py',
    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, the wish list
    # matched to bookings, one PDF button, countries without home.
    'test_travel_five.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - places.
    '.bak_travel4',
]

''',
         r'''    # TR-4, 15 Nov 2026 - Release 85: Travel, stage 4 - places.
    '.bak_travel4',
    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, and the review.
    '.bak_travel5',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-info-circle">
    <h6><i class="fas fa-plane"></i> Travel</h6>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Coming next: an itinerary and wish list.</p>
  </article>

  <article data-tab-slug="tr-trips"
           data-tab-name="Trips &amp; Sharing"
           data-tab-icon="fa-share-alt">
    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong> (the form opens when you press it): give it a name, and if you like its dates and countries. <strong>The bookings set the dates</strong>: once a trip has bookings with dates, it runs from the first booking&rsquo;s start to the last one&rsquo;s end, whatever was typed &mdash; typed dates are only for planning before anything is booked. The trip&rsquo;s countries are its bookings&rsquo; countries (as read from the emails, or typed on a booking) together with any typed on the trip. The name is yours to choose.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>
''',
         r'''           data-tab-icon="fa-info-circle">
    <h6><i class="fas fa-plane"></i> Travel</h6>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Each trip also has an <strong>Itinerary</strong> and <strong>Things to do</strong> &mdash; see <strong>Itinerary &amp; Places</strong>.</p>
  </article>

  <article data-tab-slug="tr-trips"
           data-tab-name="Trips &amp; Sharing"
           data-tab-icon="fa-share-alt">
    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong> (the form opens when you press it): give it a name, and if you like its dates and countries. <strong>The bookings set the dates</strong>: once a trip has bookings with dates, it runs from the first booking&rsquo;s start to the last one&rsquo;s end, whatever was typed &mdash; typed dates are only for planning before anything is booked. <strong>The trip&rsquo;s countries come from its bookings</strong> &mdash; where each hotel, car or restaurant is and where each flight lands, read from the email, or worked out from the address, the airport or the town. Your <strong>home country (Cyprus) is left out</strong>, so flights home do not add it; it is shown only for a trip that never leaves it. Under <strong>Edit trip &rarr; Other countries</strong> type a country only if you are going there with nothing booked yet. The name is yours to choose.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>
'''),
        (r'''    <p>The trip page lists bookings by day. Open one to see everything about it &mdash; <strong>Delete</strong> is there too, next to Edit &mdash; with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>Who&rsquo;s travelling</strong>: tick the people on the trip the booking is for, and type anyone else&rsquo;s name. Bookings read from an email fill this in from the passenger and guest names.</p>
    <p>One reference with several flights (outward and back) is one booking per flight: put the flight number under <strong>Part</strong>. Tick <strong>Cancelled</strong> to keep a cancelled booking on the trip, struck through and left out of the costs.</p>
''',
         r'''    <p>The trip page lists bookings by day. Open one to see everything about it &mdash; <strong>Delete</strong> is there too, next to Edit &mdash; with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>Restaurant</strong> is a kind of its own, for a table booked at a restaurant: the time of the table, the address and phone, how many people. A forwarded confirmation from the restaurant, TheFork or OpenTable comes in as a Restaurant. If that restaurant is in the trip&rsquo;s Things to do, the booking takes its place: it moves onto the booking&rsquo;s day and time and shows once on the itinerary &mdash; as the booking. Cancel or delete the booking and the place goes back to Things to do. Tickets for a museum on Things to do (kind Activity) are matched the same way.</p>
    <p><strong>Missing details are looked up.</strong> A hotel or restaurant booking without its address, phone number or (for a hotel) check-in and check-out times has them looked up on the web, once, when it is added or the trip is opened. Only empty fields are filled &mdash; what the email or you said is never changed &mdash; and the booking&rsquo;s <strong>Changes</strong> show what came from the web. Check them before you rely on them.</p>
    <p><strong>Who&rsquo;s travelling</strong>: tick the people on the trip the booking is for, and type anyone else&rsquo;s name. Bookings read from an email fill this in from the passenger and guest names.</p>
    <p>One reference with several flights (outward and back) is one booking per flight: put the flight number under <strong>Part</strong>. Tick <strong>Cancelled</strong> to keep a cancelled booking on the trip, struck through and left out of the costs.</p>
'''),
        (r'''    <p>Enter a cost in the currency you paid in. It is kept as it is, and shown in euros as well, at the European Central Bank&rsquo;s reference rate for the day it was entered. The rate is stored with the booking, so the euro figure never moves.</p>
    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p><strong>PDF summary</strong> and <strong>PDF detailed</strong> (on the trip) make the trip into a PDF. The summary is the trip day by day &mdash; what starts each day, the places planned &mdash; with the wish list and the costs; the detailed one adds every booking in full: reference, times, address, phone, travellers, cost, cancellation and payment dates, documents and details. It opens in the PDF viewer to download or, on a phone, to share by WhatsApp or mail; in the phone app it goes straight to the phone&rsquo;s share sheet.</p>
    <p>A return flight booked together has one price: it sits on the first flight, and the other says <strong>Included in</strong> that flight rather than showing nothing.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
''',
         r'''    <p>Enter a cost in the currency you paid in. It is kept as it is, and shown in euros as well, at the European Central Bank&rsquo;s reference rate for the day it was entered. The rate is stored with the booking, so the euro figure never moves.</p>
    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p><strong>PDF</strong> (on the trip) makes the trip into a PDF &mdash; press it and choose <strong>Summary</strong> or <strong>Detailed</strong>. The summary is the trip day by day &mdash; what starts each day, the places planned &mdash; with Things to do and the costs. In the detailed one each day also gives every hotel&rsquo;s and restaurant&rsquo;s address, phone number and check-in and check-out times, and it ends with every booking in full: reference, times, address, phone, travellers, cost, cancellation and payment dates, documents and details. It opens in the PDF viewer to download or, on a phone, to share by WhatsApp or mail; in the phone app it goes straight to the phone&rsquo;s share sheet.</p>
    <p>A return flight booked together has one price: it sits on the first flight, and the other says <strong>Included in</strong> that flight rather than showing nothing.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
'''),
        (r'''           data-tab-icon="fa-envelope">
    <h6><i class="fas fa-envelope"></i> Bookings from your emails</h6>
    <p><strong>Forward</strong> a booking email &mdash; a flight, hotel, car, train or ferry confirmation, a change, a cancellation, a boarding pass &mdash; to the trips address shown on <strong>Travel &rarr; Forwarding</strong>. Forward it as it is, with its attachments. It is read in a minute or so.</p>
    <p><strong>Whose it is</strong> is decided by the address it was forwarded from: your login email, or any address you add under <strong>Forwarding</strong>. An email from an address nobody has added is ignored and not kept. To forward automatically, set up a Gmail filter or an Outlook rule &mdash; Forwarding shows how. Gmail first sends a confirmation to the trips address: it appears in To check with its code and a <strong>Confirm in Gmail</strong> button.</p>
    <p><strong>To check</strong> lists what was read. A new booking waits there: choose the trip it goes on (the trip whose dates take it in is picked for you) or <strong>A new trip</strong>, then <strong>Add</strong>. The PDFs and passes from the email are attached to the booking.</p>
''',
         r'''           data-tab-icon="fa-envelope">
    <h6><i class="fas fa-envelope"></i> Bookings from your emails</h6>
    <p><strong>Forward</strong> a booking email &mdash; a flight, hotel, car, train, ferry or restaurant confirmation, a change, a cancellation, a boarding pass &mdash; to the trips address shown on <strong>Travel &rarr; Forwarding</strong>. Forward it as it is, with its attachments. It is read in a minute or so.</p>
    <p><strong>Whose it is</strong> is decided by the address it was forwarded from: your login email, or any address you add under <strong>Forwarding</strong>. An email from an address nobody has added is ignored and not kept. To forward automatically, set up a Gmail filter or an Outlook rule &mdash; Forwarding shows how. Gmail first sends a confirmation to the trips address: it appears in To check with its code and a <strong>Confirm in Gmail</strong> button.</p>
    <p><strong>To check</strong> lists what was read. A new booking waits there: choose the trip it goes on (the trip whose dates take it in is picked for you) or <strong>A new trip</strong>, then <strong>Add</strong>. The PDFs and passes from the email are attached to the booking.</p>
'''),
        (r'''           data-tab-name="Itinerary &amp; Places"
           data-tab-icon="fa-map-marker-alt">
    <h6><i class="fas fa-map-marker-alt"></i> The itinerary, the wish list and places</h6>
    <p><strong>Add a place</strong> for somewhere with no booking &mdash; a museum, a garden, a restaurant, a viewpoint. Type its name or paste a Google Maps or website link. Claude looks it up on the web and fills in the address, opening hours, price and website, usually within half a minute (the page refreshes by itself). Check the hours before you go; anything you type wins over what was found. On the phone, in Google Maps, tap <strong>Share &rarr; Travel</strong> on a place and it opens Add a place for the trip you are on (or the next one).</p>
    <p>A place goes on a <strong>day</strong> (with a time if you like) or on the trip&rsquo;s <strong>Wish list</strong> &mdash; ideas with no day yet; <em>Put on</em> moves one to a day. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>
''',
         r'''           data-tab-name="Itinerary &amp; Places"
           data-tab-icon="fa-map-marker-alt">
    <h6><i class="fas fa-map-marker-alt"></i> The itinerary, things to do and places</h6>
    <p><strong>Add a place</strong> for somewhere with no booking &mdash; a museum, a garden, a restaurant, a viewpoint. Type its name or paste a Google Maps or website link. Claude looks it up on the web and fills in its proper name, the address, opening hours, price and website, usually within half a minute (the page refreshes by itself). The name can be short, lower case or misspelled &mdash; &ldquo;sagrada familia&rdquo; finds the Basilica de la Sagrada Familia, wherever the trip is going. If <strong>two or three places</strong> could be meant (a common name, a chain), it asks <strong>Which one did you mean?</strong> &mdash; pick one and that one is looked up, or <strong>None of these</strong> to keep it as you typed it. If nothing comes up, add the town to the name and press <strong>Try again</strong>. Check the hours before you go; anything you type wins over what was found. On the phone, in Google Maps, tap <strong>Share &rarr; Travel</strong> on a place and it opens Add a place for the trip you are on (or the next one).</p>
    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>
'''),
    ]),
    (os.path.join('test_travel_four.py'), [
        (r'''        pass
    real_call = PL.call
    PL.SYNC = True
    try:
''',
         r'''        pass
    real_call = PL.call
    # TR-5 (Release 86) looks up a stay's missing address and times when
    # its trip is opened - never on the web from this suite.
    real_details = getattr(PL, 'call_details', None)

    def _no_web(b, client=None):
        raise PL.LookupError_('not from the test suite')
    if real_details is not None:
        PL.call_details = _no_web
    PL.SYNC = True
    try:
'''),
        (r'''    finally:
        PL.call = real_call
        PL.SYNC = False

''',
         r'''    finally:
        PL.call = real_call
        if real_details is not None:
            PL.call_details = real_details
        PL.SYNC = False

'''),
    ]),
    (os.path.join('travel', 'extract.py'), [
        (r'''
KINDS = ['flight', 'stay', 'car', 'train', 'ferry', 'transfer', 'activity',
         'other']

BOOKING = {
''',
         r'''
KINDS = ['flight', 'stay', 'car', 'train', 'ferry', 'transfer', 'activity',
         'restaurant', 'other']

BOOKING = {
'''),
        (r'''- The email may be forwarded: read the forwarded booking, not the \
forwarding note."""


''',
         r'''- The email may be forwarded: read the forwarded booking, not the \
forwarding note."""
# TR-5, 16 Nov 2026 - restaurants (Demetri: "Let's do a Restaurant type"),
# and a hotel's own check-in and check-out times.
SYSTEM += """
- A table booked at a restaurant (from the restaurant itself, TheFork, \
OpenTable or the like) is kind "restaurant": the restaurant's name as \
title, the date and time of the table as start, its address and phone, \
how many people and any notes (terrace, occasion, deposit terms) in \
details. A deposit taken is paid "part" with paid_amount; nothing paid \
yet is "due" with no amount unless a price is set.
- A stay: check-in and check-out times go in start_time and end_time \
when the email gives them."""


'''),
    ]),
    (os.path.join('travel', 'inbox.py'), [
        (r'''            left.append(n.title() if n.isupper() else n)
    if left:
        have = [x.strip() for x in (b.traveller_names or '').split(',')
                if x.strip()]
        for n in left:
            if n not in have:
                have.append(n)
        b.traveller_names = ', '.join(have)[:255]
''',
         r'''            left.append(n.title() if n.isupper() else n)
    if left:
        from .views import name_key
        have = [x.strip() for x in (b.traveller_names or '').split(',')
                if x.strip()]
        # TR-5 - the same person in another order (a boarding pass's
        # MANIAS/DIMITRIOS) is not a second traveller.
        for n in left:
            if name_key(n) not in [name_key(x) for x in have]:
                have.append(n)
        b.traveller_names = ', '.join(have)[:255]
'''),
        (r'''    travellers(b, item)
    keep_pass(b, item, user)
    changes = diff(before, b)
    if was_status != b.status:
''',
         r'''    travellers(b, item)
    keep_pass(b, item, user)
    # TR-5 - a place booked for moves with its booking, or back to the
    # wish list when the booking is cancelled.
    from .places import link_booking
    link_booking(b)
    changes = diff(before, b)
    if was_status != b.status:
'''),
        (r'''    travellers(b, item)
    keep_pass(b, item, user)
    return b

''',
         r'''    travellers(b, item)
    keep_pass(b, item, user)
    # TR-5 - a table at a restaurant on the wish list takes that place;
    # a hotel's or restaurant's missing details are looked up.
    from .places import link_booking, start_details
    link_booking(b)
    start_details([b], limit=1)
    return b

'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''        ('transfer', 'Transfer'),
        ('activity', 'Activity'),
        ('other', 'Other'),
    ]
''',
         r'''        ('transfer', 'Transfer'),
        ('activity', 'Activity'),
        # TR-5, 16 Nov 2026 - a table booked at a restaurant (Demetri:
        # "Let's do a Restaurant type"), from the restaurant, TheFork or
        # OpenTable.
        ('restaurant', 'Restaurant'),
        ('other', 'Other'),
    ]
'''),
        (r'''    city = models.CharField(max_length=80, blank=True, default='')
    country = models.CharField(max_length=60, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    city = models.CharField(max_length=80, blank=True, default='')
    country = models.CharField(max_length=60, blank=True, default='')
    # TR-5, 16 Nov 2026 - when a stay's or a restaurant's missing details
    # (address, phone, check-in and check-out times) were last looked up
    # on the web (Demetri: "more details for like hotels (address, phone
    # number, check in and check out time, etc.)"). Once per booking.
    web_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''             ('activity', 'Activity'), ('other', 'Other')]
    LOOKUP = [('', 'Typed'), ('waiting', 'Looking it up'),
              ('found', 'Found'), ('failed', 'Not found')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='places')
''',
         r'''             ('activity', 'Activity'), ('other', 'Other')]
    LOOKUP = [('', 'Typed'), ('waiting', 'Looking it up'),
              ('found', 'Found'), ('failed', 'Not found'),
              # TR-5 - two or three places could be meant: the person
              # picks one (Demetri, 16 Nov: "if it finds two or three
              # options, then maybe the user must be given these options
              # to choose from").
              ('choose', 'Which one?')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='places')
'''),
        (r'''    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    # TR-5 - [{name, city, country, address, about}], at most three, while
    # lookup is 'choose'.
    options = models.JSONField(default=list, blank=True)
    # TR-5 - the booking that made it real: a table booked at a restaurant
    # on the wish list (Demetri: "Matching to the Wish List is
    # necessary"). It then sits on the booking's day and time and shows
    # once on the itinerary - as the booking.
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='places')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''    rows = [(b.when or dt.time(0, 0), 0, b) for b in on_day(bs, day)]
    for p in places:
        if p.day == day:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
''',
         r'''    rows = [(b.when or dt.time(0, 0), 0, b) for b in on_day(bs, day)]
    for p in places:
        # TR-5 - a place with its booking shows once: as the booking.
        if p.day == day and not p.booking_id:
            p.is_place = True
            rows.append((p.time or dt.time(23, 59, 59), 1, p))
'''),
    ]),
    (os.path.join('travel', 'places.py'), [
        (r'''        'properties': {
            'found': {'type': 'boolean', 'description':
                      'False if you could not tell which place is meant.'},
            'name': {'type': 'string', 'description':
                     'Its proper name, e.g. "Calouste Gulbenkian Museum".'},
''',
         r'''        'properties': {
            'found': {'type': 'boolean', 'description':
                      'False only if nothing sensible matches.'},
            'sure': {'type': 'boolean', 'description':
                     'False when two or three different places could be '
                     'meant - then give options instead of details.'},
            'options': {'type': 'array', 'maxItems': 3, 'description':
                        'When not sure: the places that could be meant.',
                        'items': {'type': 'object', 'properties': {
                            'name': {'type': 'string'},
                            'city': {'type': 'string'},
                            'country': {'type': 'string'},
                            'address': {'type': 'string'},
                            'about': {'type': 'string', 'description':
                                      'One line: what it is.'}},
                            'required': ['name']}},
            'name': {'type': 'string', 'description':
                     'Its proper name, e.g. "Calouste Gulbenkian Museum".'},
'''),
        (r'''
SYSTEM = """You help a family plan a trip. Find the place they mean with \
web search - near the trip's destination if one is given - then call \
record_place once with what you found. Use the place's official site or a \
reliable source for hours and prices; keep each field to one short line; \
never guess - leave out what you could not find. If the name could be \
several places, choose the one in or near the trip's destination."""


''',
         r'''
SYSTEM = """You help a family plan a trip. Find the place they mean with \
web search, then call record_place once with what you found.

- Be generous about the name: it may be partial, a nickname, lower case, \
in another language or misspelled ("sagrada familia" is the Basilica de la \
Sagrada Familia in Barcelona). Give its proper name.
- The trip's destination only decides between places with the same name. \
Never reject a well-known place because it is somewhere else.
- One place clearly meant: found true, sure true, and its details.
- Two or three different places could be meant (a common name, a chain, \
a name in several cities) and nothing given says which: found true, sure \
false, and up to three options - each its proper name, city, country, \
street address and one line saying what it is. Leave the details out.
- found false only when nothing sensible matches.
- A Google Maps link or an address given points at one place: that place.
- Use the place's official site or a reliable source for hours and \
prices; keep each field to one short line; never guess - leave out what \
you could not find."""


'''),
        (r'''    where = trip.where or trip.countries
    ask = ['Place: %s' % (place.query or place.name)]
    if place.address:
        ask.append('Address given: %s' % place.address)
''',
         r'''    where = trip.where or trip.countries
    ask = ['Place: %s' % (place.query or place.name)]
    if place.maps_link:
        ask.append('Google Maps link (this exact place): %s'
                   % place.maps_link)
    if place.address:
        ask.append('Address given: %s' % place.address)
'''),
        (r'''

def fill(place, found):
    """The answer onto the place - never over what someone typed."""
    if not found.get('found'):
        place.lookup = 'failed'
        place.lookup_note = 'Could not tell which place this is - add the ' \
                            'details yourself, or try a fuller name.'
        return place
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if s('name', 160):
        place.name = s('name', 160)
''',
         r'''

def edited(place):
    """Has the name been changed since it was typed or shared?"""
    typed = parse_query(place.query)[0] if place.query else ''
    return bool(typed) and place.name.strip().lower() != typed.lower()


def options(found):
    """The places that could be meant, tidied - at most three."""
    out = []
    for o in found.get('options') or []:
        if not isinstance(o, dict) or not str(o.get('name') or '').strip():
            continue
        s = lambda k, n: str(o.get(k) or '').strip()[:n]       # noqa: E731
        out.append({'name': s('name', 160), 'city': s('city', 80),
                    'country': s('country', 60),
                    'address': s('address', 255), 'about': s('about', 200)})
    return out[:3]


def fill(place, found):
    """The answer onto the place - never over what someone typed."""
    if not found.get('found'):
        place.lookup = 'failed'
        place.lookup_note = 'Could not tell which place this is - add ' \
                            'the town to the name and try again, or add ' \
                            'the details yourself.'
        return place
    # TR-5 (Demetri, 16 Nov: "if it finds two or three options, then
    # maybe the user must be given these options to choose from").
    opts = options(found)
    if found.get('sure') is False and len(opts) > 1 and \
            not place.maps_link:
        place.options = opts
        place.lookup = 'choose'
        place.lookup_note = ''
        return place
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if found.get('sure') is False and len(opts) == 1 and not s('name', 160):
        o = opts[0]
        found = dict(found, name=o['name'], address=o['address'],
                     about=found.get('about') or o['about'])
    # The proper name over the words typed to find it ("sagrada familia"
    # becomes "Basilica de la Sagrada Familia"). A name changed by hand is
    # only looked up when Try again is pressed - which makes it the words
    # to find it by (views_places.place_again).
    if s('name', 160):
        place.name = s('name', 160)
'''),
        (r'''    place.website = place.website or _https(found.get('website'))
    place.about = place.about or s('about', 300)
    place.lookup = 'found'
    place.lookup_note = ''
''',
         r'''    place.website = place.website or _https(found.get('website'))
    place.about = place.about or s('about', 300)
    place.options = []
    place.lookup = 'found'
    place.lookup_note = ''
'''),
        (r'''        place.lookup_note = str(e)[:255]
    place.save()
    return place.lookup == 'found'

''',
         r'''        place.lookup_note = str(e)[:255]
    place.save()
    if place.lookup == 'found':
        link_place(place)
    return place.lookup == 'found'

'''),
        (r'''    threading.Thread(target=run, daemon=True).start()
    return None
''',
         r'''    threading.Thread(target=run, daemon=True).start()
    return None


# ==========================================================================
# TR-5, 16 Nov 2026 - A HOTEL'S OR A RESTAURANT'S MISSING DETAILS.
#
# Demetri: "for the detailed itinerary, I think that I want more details
# for like hotels (address, phone number, check in and check out time,
# etc.) The same for restaurants." A booking email often leaves some out
# (Booking.com rarely gives the hotel's phone or its check-in hours). What
# is missing is looked up once, on the web, as a place is - and only ever
# fills a blank: what the email or a person said is never changed. The
# booking's Changes say what came from the web.
# ==========================================================================
DETAIL_KINDS = ('stay', 'restaurant')
DETAILS_SYSTEM = """You fill in the practical details of a hotel or \
restaurant a family has booked. Find that exact place with web search - \
the name, the company and the town given - then call record_details once. \
Use its official site or a reliable listing. Times as HH:MM, 24-hour. \
Never guess: leave out what you could not find."""
DETAILS_TOOL = {
    'name': 'record_details',
    'description': 'Record the practical details found for the booking.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'found': {'type': 'boolean', 'description':
                      'False if you could not tell which place it is.'},
            'address': {'type': 'string', 'description':
                        'Street address with postcode and town.'},
            'phone': {'type': 'string', 'description':
                      'The place\'s own phone number, international form.'},
            'check_in': {'type': 'string', 'description':
                         'Hotels: check-in from, HH:MM.'},
            'check_out': {'type': 'string', 'description':
                          'Hotels: check-out by, HH:MM.'},
        },
        'required': ['found'],
    },
}


def gaps(b):
    """What a stay or a restaurant booking is missing."""
    out = []
    if not (b.address or '').strip():
        out.append('address')
    if not (b.phone or '').strip():
        out.append('phone')
    if b.kind == 'stay':
        if not b.start_time:
            out.append('check_in')
        if not b.end_time:
            out.append('check_out')
    return out


def wants_details(b):
    return b.kind in DETAIL_KINDS and b.status != 'cancelled' and \
        b.web_checked is None and bool(gaps(b)) and bool(b.pk)


def call_details(b, client=None):
    if client is None:
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise LookupError_('The Anthropic key is not set on the server.')
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=90.0,
                                     max_retries=1)
    ask = ['%s: %s' % ('Hotel' if b.kind == 'stay' else 'Restaurant',
                       b.title)]
    for label, v in (('Booked with', b.provider), ('Address', b.address),
                     ('Town', b.city), ('Country', b.country),
                     ('Phone', b.phone)):
        if (v or '').strip():
            ask.append('%s: %s' % (label, v))
    ask.append('Missing: %s' % ', '.join(gaps(b)))
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=DETAILS_SYSTEM,
            tools=[{'type': 'web_search_20250305', 'name': 'web_search',
                    'max_uses': SEARCHES}, DETAILS_TOOL],
            messages=[{'role': 'user', 'content': '\n'.join(ask)}],
        )
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel booking details: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                getattr(block, 'name', '') == 'record_details':
            if isinstance(block.input, dict):
                return block.input
    raise LookupError_('Nothing came back.')


def _hhmm(v):
    try:
        return dt.time.fromisoformat(str(v or '').strip()[:5])
    except ValueError:
        return None


def add_details(b, found):
    """The web's answer into the booking's blanks. Returns what changed,
    as the Changes trail writes it."""
    out = []
    if not found.get('found'):
        return out
    s = lambda k, n: str(found.get(k) or '').strip()[:n]       # noqa: E731
    if not (b.address or '').strip() and s('address', 255):
        b.address = s('address', 255)
        out.append({'label': 'Address', 'old': '', 'new': b.address})
    if not (b.phone or '').strip() and s('phone', 40):
        b.phone = s('phone', 40)
        out.append({'label': 'Phone', 'old': '', 'new': b.phone})
    if b.kind == 'stay':
        if not b.start_time and _hhmm(found.get('check_in')):
            b.start_time = _hhmm(found.get('check_in'))
            out.append({'label': 'Start time', 'old': '',
                        'new': b.start_time.strftime('%H:%M')})
        if not b.end_time and _hhmm(found.get('check_out')):
            b.end_time = _hhmm(found.get('check_out'))
            out.append({'label': 'End time', 'old': '',
                        'new': b.end_time.strftime('%H:%M')})
    return out


def enrich(b, client=None):
    """Claim the booking, look up what it is missing, fill the blanks.
    Once per booking: web_checked is set first, found or not."""
    from .models import Booking, BookingChange
    n = Booking.objects.filter(pk=b.pk, web_checked__isnull=True).update(
        web_checked=timezone.now())
    if n != 1:
        return []
    b.refresh_from_db()
    if not gaps(b):
        return []
    try:
        found = call_details(b, client=client)
    except LookupError_:
        return []
    changed = add_details(b, found)
    if changed:
        b.save(update_fields=['address', 'phone', 'start_time', 'end_time',
                              'updated_at'])
        BookingChange.objects.create(
            booking=b, by=None, source='web', changes=changed,
            note='Filled in from the web - check before you rely on it.')
    return changed


def start_details(bookings, limit=3):
    """Look up the gaps of up to `limit` stays and restaurants - in the
    background, unless SYNC. Called when a trip is opened and when a
    booking is added, so the detailed itinerary has them."""
    ids = [b.pk for b in bookings if wants_details(b)][:limit]
    if not ids:
        return

    def fresh():
        # Its own copies - the page being drawn keeps its own.
        from .models import Booking
        return list(Booking.objects.filter(pk__in=ids,
                                           web_checked__isnull=True))
    if SYNC:
        for b in fresh():
            enrich(b)
        return

    def run():
        try:
            for b in fresh():
                enrich(b)
        except Exception:                               # noqa: BLE001
            logger.exception('travel booking details')
        finally:
            close_old_connections()
    threading.Thread(target=run, daemon=True).start()


# ==========================================================================
# TR-5, 16 Nov 2026 - A BOOKING FOR A PLACE ON THE WISH LIST.
#
# Demetri: "Matching to the Wish List is necessary." A table booked at a
# restaurant that is on the trip's wish list (or a ticket for a museum
# that is) makes that place real: it takes the booking's day and time, and
# the itinerary shows it once - as the booking. Cancel the booking, or
# delete it, and the place goes back to the wish list.
# ==========================================================================
LINK_KINDS = ('restaurant', 'activity')
GENERIC = {
    'the', 'a', 'an', 'at', 'of', 'and', 'for', 'de', 'del', 'la', 'le',
    'el', 'il', 'lo', 'los', 'las', 'les', 'di', 'da', 'du', 'des', 'to',
    'restaurant', 'restaurante', 'ristorante', 'taverna', 'tavern',
    'trattoria', 'osteria', 'brasserie', 'bistro', 'cafe', 'bar',
    'table', 'reservation', 'booking', 'ticket', 'tickets', 'entry',
    'admission', 'visit', 'tour', 'skip', 'line',
}


def _fold(text):
    import unicodedata
    t = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in t if not unicodedata.combining(c)).lower()


def name_words(text):
    return {w for w in re.findall(r'[a-z0-9]+', _fold(text))
            if w not in GENERIC and len(w) > 1}


def same_place(p, b):
    """Is this booking for this place?"""
    if p.maps_link and b.link and p.maps_link == b.link:
        return True
    a, c = name_words(p.name), name_words(b.title) | name_words(
        b.provider if b.kind == 'restaurant' else '')
    if not a or not c:
        return False
    tight = name_words(b.title)
    if a == tight:
        return True
    food = b.kind == 'restaurant' and p.kind in ('food', 'other', 'sight')
    if food and (a <= c or (tight and tight <= a)) and \
            max(len(w) for w in (a & c or {''})) >= 4:
        return True
    import difflib
    r = difflib.SequenceMatcher(None, ' '.join(sorted(a)),
                                ' '.join(sorted(tight or c))).ratio()
    if r >= 0.88:
        return True
    return bool(p.address and b.address and
                name_words(p.address) == name_words(b.address))


def link_booking(b):
    """After a booking is added or changed: link it to its place on the
    wish list, move a linked place with it, or let it go if cancelled.
    Returns the place linked, if any."""
    from .models import Place
    if not b.pk:
        return None
    mine = list(Place.objects.filter(booking=b))
    if b.status == 'cancelled' or b.kind not in LINK_KINDS:
        for p in mine:
            p.booking, p.day, p.time = None, None, None
            p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
        return None
    if not mine:
        for p in Place.objects.filter(trip_id=b.trip_id, booking__isnull=True,
                                      done=False).order_by('id'):
            if same_place(p, b):
                p.booking = b
                mine = [p]
                break
    for p in mine:
        p.day, p.time = b.start_date, b.start_time
        p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
    return mine[0] if mine else None


def link_place(p):
    """After a place is added or found: a booking on the trip already for
    it (the table was booked first)."""
    from .models import Booking
    if p.booking_id or p.done:
        return None
    for b in Booking.objects.filter(trip_id=p.trip_id, kind__in=LINK_KINDS) \
            .exclude(status='cancelled').exclude(places__isnull=False):
        if same_place(p, b):
            p.booking, p.day, p.time = b, b.start_date, b.start_time
            p.save(update_fields=['booking', 'day', 'time', 'updated_at'])
            return b
    return None


def unlink_deleted(b):
    """Before a booking is deleted: its places back to the wish list."""
    from .models import Place
    Place.objects.filter(booking=b).update(booking=None, day=None,
                                           time=None)
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_booking_row.html'), [
        (r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span></span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
''',
         r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span>{% if b.kind == 'stay' or b.kind == 'restaurant' %}{% if b.address or b.phone %}{% if b.what != 'during' %}{% comment %} TR-5 (Demetri, 16 Nov): a hotel's or restaurant's address and phone, on the day. {% endcomment %}<span class="tv-detail" data-row-detail>{% if b.address %}{{ b.address }}{% endif %}{% if b.address and b.phone %} · {% endif %}{% if b.phone %}{{ b.phone }}{% endif %}{% if b.kind == 'stay' and b.what == 'start' and b.end_time %} · check out by {{ b.end_time|time:"H:i" }}{% endif %}</span>{% endif %}{% endif %}{% endif %}</span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_place_row.html'), [
        (r'''{% comment %} TR-4 - one place on the itinerary or the wish list (computer). {% endcomment %}<div class="tv-bk tv-place{% if p.done %} tv-off{% endif %}" data-place>
  <span class="tv-ico"><i class="fas {% if p.kind == 'food' %}fa-utensils{% elif p.kind == 'museum' %}fa-landmark{% elif p.kind == 'nature' %}fa-tree{% elif p.kind == 'shop' %}fa-shopping-bag{% elif p.kind == 'activity' %}fa-hiking{% else %}fa-map-marker-alt{% endif %}" aria-hidden="true"></i></span>
  <span style="min-width: 0"><a href="{% url 'travel:place' p.pk %}" style="color: inherit"><b>{% if p.time %}{{ p.time|time:"H:i" }} &middot; {% endif %}{{ p.name }}</b></a>{% if p.lookup == 'waiting' %} <span class="tv-tag tv-shared">Looking it up&hellip;</span>{% endif %}
    <span class="tv-sub" style="display: block">{% if p.hours %}{{ p.hours }}{% endif %}{% if p.price %}{% if p.hours %} &middot; {% endif %}{{ p.price }}{% endif %}{% if p.notes %}{% if p.hours or p.price %} &middot; {% endif %}{{ p.notes|truncatechars:80 }}{% endif %}</span></span>
  <span class="tv-acts" style="margin: 0">
    <a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary btn-sm" aria-label="{{ p.name }} on the map"><i class="fas fa-map" aria-hidden="true"></i></a>
    <form method="post" action="{% url 'travel:place_done' p.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><button type="submit" class="btn action-secondary btn-sm" aria-label="{% if p.done %}Not done{% else %}Done{% endif %}: {{ p.name }}"><i class="fas {% if p.done %}fa-undo{% else %}fa-check{% endif %}" aria-hidden="true"></i></button></form>
  </span>
</div>
''',
         r'''{% comment %} TR-4 - one place on the itinerary or Things to do (computer). {% endcomment %}<div class="tv-bk tv-place{% if p.done %} tv-off{% endif %}" data-place>
  <span class="tv-ico"><i class="fas {% if p.kind == 'food' %}fa-utensils{% elif p.kind == 'museum' %}fa-landmark{% elif p.kind == 'nature' %}fa-tree{% elif p.kind == 'shop' %}fa-shopping-bag{% elif p.kind == 'activity' %}fa-hiking{% else %}fa-map-marker-alt{% endif %}" aria-hidden="true"></i></span>
  <span style="min-width: 0"><a href="{% url 'travel:place' p.pk %}" style="color: inherit"><b>{% if p.time %}{{ p.time|time:"H:i" }} &middot; {% endif %}{{ p.name }}</b></a>{% if p.lookup == 'waiting' %} <span class="tv-tag tv-shared">Looking it up&hellip;</span>{% elif p.lookup == 'choose' %} <span class="tv-tag tv-due" data-choose>Which one?</span>{% endif %}
    <span class="tv-sub" style="display: block">{% if p.hours %}{{ p.hours }}{% endif %}{% if p.price %}{% if p.hours %} &middot; {% endif %}{{ p.price }}{% endif %}{% if p.notes %}{% if p.hours or p.price %} &middot; {% endif %}{{ p.notes|truncatechars:80 }}{% endif %}</span></span>
  {% comment %} TR-5 (Demetri, 16 Nov: "We need to create hover over for those buttons"): each says what it does. {% endcomment %}<span class="tv-acts" style="margin: 0">
    <a href="{% url 'travel:place' p.pk %}" class="btn action-secondary btn-sm" title="Edit - change it, look it up again or remove it" aria-label="Edit {{ p.name }}"><i class="fas fa-pen" aria-hidden="true"></i></a>
    <a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary btn-sm" title="Map - open it in Google Maps" aria-label="{{ p.name }} on the map"><i class="fas fa-map" aria-hidden="true"></i></a>
    {% if p.day %}<form method="post" action="{% url 'travel:place_move' p.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="to_wish" value="1"><button type="submit" class="btn action-secondary btn-sm" title="Back to Things to do - take it off this day" aria-label="{{ p.name }} back to Things to do" data-to-wish><i class="fas fa-undo-alt" aria-hidden="true"></i></button></form>{% endif %}
    <form method="post" action="{% url 'travel:place_done' p.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><button type="submit" class="btn action-secondary btn-sm" title="{% if p.done %}Not done - mark it not visited yet{% else %}Done - mark it visited{% endif %}" aria-label="{% if p.done %}Not done{% else %}Done{% endif %}: {{ p.name }}"><i class="fas {% if p.done %}fa-times{% else %}fa-check{% endif %}" aria-hidden="true"></i></button></form>
  </span>
</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-wpass-grid small { display: block; font-size: 0.68rem; opacity: .8; }
.tv-wpass-foot { padding: 12px 16px 14px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
''',
         r'''.tv-wpass-grid small { display: block; font-size: 0.68rem; opacity: .8; }
.tv-wpass-foot { padding: 12px 16px 14px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
/* TR-5, 16 Nov 2026 - one PDF button with its two choices (Demetri: "I
   don't want two buttons for PDF"), opened by click, no script. */
.tv-menu { position: relative; display: inline-block; }
.tv-menu > summary { list-style: none; cursor: pointer; }
.tv-menu > summary::-webkit-details-marker { display: none; }
.tv-menu-pop { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; min-width: 260px; display: flex; flex-direction: column; padding: 6px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); background: var(--alv-paper); box-shadow: 0 6px 18px rgba(0, 0, 0, .12); }
.tv-menu-pop button { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; padding: 8px 10px; border: 0; border-radius: 8px; background: transparent; color: var(--alv-ink); text-align: left; }
.tv-menu-pop button:hover, .tv-menu-pop button:focus { background: var(--alv-surface); }
.tv-menu-pop small { color: var(--alv-ink-soft); }
.tv-detail { display: block; color: var(--alv-ink-soft); font-size: 0.85rem; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
@media screen and (max-width: 575.98px) {
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''    <section class="form-card" data-booking-detail>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas {{ b.icon }}" aria-hidden="true"></i> {{ b.title }}</h3><span>{% if b.cancelled %}<span class="tv-tag tv-due" data-cancelled>Cancelled</span> {% endif %}<span class="tv-tag tv-shared">{{ b.kind_label }}</span></span></div>
        {% if b.start_date %}
        <div class="tv-row" style="margin-top: 10px">
            <div><div class="tv-sub">{% if b.kind == 'stay' %}Check-in{% elif b.kind == 'car' %}Pick-up{% else %}Starts{% endif %}</div><b>{{ b.start_date|date:"D j M Y" }}</b>{% if b.start_time %}<div class="tv-sub">{{ b.start_time|time:"H:i" }}</div>{% endif %}</div>
            {% if nights %}<div class="tv-sub">{{ nights }} night{{ nights|pluralize }}</div>{% endif %}
            {% if b.end_date or b.end_time %}<div style="text-align: right"><div class="tv-sub">{% if b.kind == 'stay' %}Check-out{% elif b.kind == 'car' %}Drop-off{% else %}Ends{% endif %}</div><b>{{ b.end_date|default:b.start_date|date:"D j M Y" }}</b>{% if b.end_time %}<div class="tv-sub">{{ b.end_time|time:"H:i" }}</div>{% endif %}</div>{% endif %}
''',
         r'''    <section class="form-card" data-booking-detail>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas {{ b.icon }}" aria-hidden="true"></i> {{ b.title }}</h3><span>{% if b.cancelled %}<span class="tv-tag tv-due" data-cancelled>Cancelled</span> {% endif %}<span class="tv-tag tv-shared">{{ b.kind_label }}</span></span></div>
        {% for p in b.places.all %}<p class="small" style="margin: 6px 0 0" data-booked-place><i class="fas fa-map-marker-alt" aria-hidden="true"></i> For <a href="{% url 'travel:place' p.pk %}">{{ p.name }}</a> from Things to do{% if p.hours %} &middot; <span class="tv-sub">{{ p.hours }}</span>{% endif %}</p>{% endfor %}
        {% if b.start_date %}
        <div class="tv-row" style="margin-top: 10px">
            <div><div class="tv-sub">{% if b.kind == 'stay' %}Check-in{% elif b.kind == 'car' %}Pick-up{% elif b.kind == 'restaurant' %}Table{% else %}Starts{% endif %}</div><b>{{ b.start_date|date:"D j M Y" }}</b>{% if b.start_time %}<div class="tv-sub">{{ b.start_time|time:"H:i" }}</div>{% endif %}</div>
            {% if nights %}<div class="tv-sub">{{ nights }} night{{ nights|pluralize }}</div>{% endif %}
            {% if b.end_date or b.end_time %}<div style="text-align: right"><div class="tv-sub">{% if b.kind == 'stay' %}Check-out{% elif b.kind == 'car' %}Drop-off{% else %}Ends{% endif %}</div><b>{{ b.end_date|default:b.start_date|date:"D j M Y" }}</b>{% if b.end_time %}<div class="tv-sub">{{ b.end_time|time:"H:i" }}</div>{% endif %}</div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', '_icon.html'), [
        (r'''{% comment %} TR-3 - the kind of booking, drawn. {% endcomment %}{% if kind == 'flight' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 16l20-6-20-6 4 6-4 6z"/></svg>{% elif kind == 'stay' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18V8M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="2"/></svg>{% elif kind == 'car' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 16h14l-1.5-6h-11z"/><circle cx="8" cy="17" r="2"/><circle cx="16" cy="17" r="2"/></svg>{% elif kind == 'train' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="3" width="12" height="14" rx="3"/><path d="M6 11h12M9 21l1-4M15 21l-1-4"/></svg>{% elif kind == 'ferry' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18c2 1.5 4 1.5 6 0s4-1.5 6 0 4 1.5 6 0M5 15l1-5h12l1 5M9 10V6h6v4"/></svg>{% else %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>{% endif %}
''',
         r'''{% comment %} TR-3 - the kind of booking, drawn. {% endcomment %}{% if kind == 'flight' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 16l20-6-20-6 4 6-4 6z"/></svg>{% elif kind == 'stay' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18V8M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="2"/></svg>{% elif kind == 'car' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 16h14l-1.5-6h-11z"/><circle cx="8" cy="17" r="2"/><circle cx="16" cy="17" r="2"/></svg>{% elif kind == 'train' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="3" width="12" height="14" rx="3"/><path d="M6 11h12M9 21l1-4M15 21l-1-4"/></svg>{% elif kind == 'restaurant' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 21V3c-2 1.5-3 4-3 7v3h3"/></svg>{% elif kind == 'ferry' %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18c2 1.5 4 1.5 6 0s4-1.5 6 0 4 1.5 6 0M5 15l1-5h12l1 5M9 10V6h6v4"/></svg>{% else %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'booking.html'), [
        (r'''<section class="tv-card" data-when>
  <div class="tv-row" style="align-items: flex-start">
    <div><div class="tv-muted">{% if b.kind == 'stay' %}Check in{% elif b.kind == 'car' %}Pick up{% else %}Leaves{% endif %}</div><b>{{ b.start_date|date:"D j M" }}</b>{% if b.start_time %}<div class="tv-time" style="font-size: 22px">{{ b.start_time|time:"H:i" }}</div>{% endif %}{% if b.from_place %}<div class="tv-muted">{{ b.from_place }}</div>{% endif %}</div>
    {% if nights %}<span class="tv-tag sh">{{ nights }} night{{ nights|pluralize }}</span>{% endif %}
    {% if b.end_date or b.end_time or b.to_place %}<div style="text-align: right"><div class="tv-muted">{% if b.kind == 'stay' %}Check out{% elif b.kind == 'car' %}Drop off{% else %}Arrives{% endif %}</div><b>{{ b.end_date|default:b.start_date|date:"D j M" }}</b>{% if b.end_time %}<div class="tv-time" style="font-size: 22px">{{ b.end_time|time:"H:i" }}</div>{% endif %}{% if b.to_place %}<div class="tv-muted">{{ b.to_place }}</div>{% endif %}</div>{% endif %}
  </div>
</section>
''',
         r'''<section class="tv-card" data-when>
  <div class="tv-row" style="align-items: flex-start">
    <div><div class="tv-muted">{% if b.kind == 'stay' %}Check in{% elif b.kind == 'car' %}Pick up{% elif b.kind == 'restaurant' %}Table{% elif b.kind == 'flight' or b.kind == 'train' or b.kind == 'ferry' %}Leaves{% else %}Starts{% endif %}</div><b>{{ b.start_date|date:"D j M" }}</b>{% if b.start_time %}<div class="tv-time" style="font-size: 22px">{{ b.start_time|time:"H:i" }}</div>{% endif %}{% if b.from_place %}<div class="tv-muted">{{ b.from_place }}</div>{% endif %}</div>
    {% if nights %}<span class="tv-tag sh">{{ nights }} night{{ nights|pluralize }}</span>{% endif %}
    {% if b.end_date or b.end_time or b.to_place %}<div style="text-align: right"><div class="tv-muted">{% if b.kind == 'stay' %}Check out{% elif b.kind == 'car' %}Drop off{% elif b.kind == 'flight' or b.kind == 'train' or b.kind == 'ferry' %}Arrives{% else %}Ends{% endif %}</div><b>{{ b.end_date|default:b.start_date|date:"D j M" }}</b>{% if b.end_time %}<div class="tv-time" style="font-size: 22px">{{ b.end_time|time:"H:i" }}</div>{% endif %}{% if b.to_place %}<div class="tv-muted">{{ b.to_place }}</div>{% endif %}</div>{% endif %}
  </div>
</section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add a place by name (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'place.html'), [
        (r'''{% block title %}{% if p %}{{ p.name }}{% else %}Add a place{% endif %} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab={% if p and p.day %}itinerary{% else %}wish{% endif %}"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>{% if p %}{{ p.name }}{% else %}Add a place{% endif %}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if p %}{% if p.day %}{{ p.day|date:"D j M" }}{% if p.time %} · {{ p.time|time:"H:i" }}{% endif %}{% else %}On the wish list{% endif %}{% else %}No booking needed · museums, gardens, restaurants{% endif %}</div>{% endblock %}
{% block content %}
{% if p and p.lookup == 'waiting' %}<meta http-equiv="refresh" content="5"><div class="tv-msg" data-looking>Looking it up on the web&hellip; this refreshes by itself.</div>{% endif %}
''',
         r'''{% block title %}{% if p %}{{ p.name }}{% else %}Add a place{% endif %} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab={% if p and p.day %}itinerary{% else %}wish{% endif %}"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>{% if p %}{{ p.name }}{% else %}Add a place{% endif %}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if p %}{% if p.day %}{{ p.day|date:"D j M" }}{% if p.time %} · {{ p.time|time:"H:i" }}{% endif %}{% else %}In Things to do{% endif %}{% else %}No booking needed · museums, gardens, restaurants{% endif %}</div>{% endblock %}
{% block content %}
{% if p and p.lookup == 'waiting' %}<meta http-equiv="refresh" content="5"><div class="tv-msg" data-looking>Looking it up on the web&hellip; this refreshes by itself.</div>{% endif %}
'''),
        (r'''  <textarea id="q" name="q" class="tv-input" rows="{% if q %}3{% else %}1{% endif %}" style="padding: 10px" maxlength="500" required placeholder="e.g. Gulbenkian museum">{{ q }}</textarea>
  <label for="d" class="tv-muted tv-small">Where should it go?</label>
  <select id="d" name="day" class="tv-select"><option value="">The wish list</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if d|date:'Y-m-d' == day_pick %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select>
  <label for="t" class="tv-muted tv-small">Time (optional)</label><input id="t" type="time" name="time" class="tv-input">
  <label for="n" class="tv-muted tv-small">Note</label><input id="n" name="notes" class="tv-input" maxlength="500">
''',
         r'''  <textarea id="q" name="q" class="tv-input" rows="{% if q %}3{% else %}1{% endif %}" style="padding: 10px" maxlength="500" required placeholder="e.g. Gulbenkian museum">{{ q }}</textarea>
  <label for="d" class="tv-muted tv-small">Where should it go?</label>
  <select id="d" name="day" class="tv-select"><option value="">Things to do (no day yet)</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if d|date:'Y-m-d' == day_pick %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select>
  <label for="t" class="tv-muted tv-small">Time (optional)</label><input id="t" type="time" name="time" class="tv-input">
  <label for="n" class="tv-muted tv-small">Note</label><input id="n" name="notes" class="tv-input" maxlength="500">
'''),
        (r'''</form>
{% else %}
{% if p.lookup == 'failed' %}<div class="tv-msg err" data-lookup-failed>{{ p.lookup_note|default:"It could not be looked up." }}</div>{% endif %}
<div class="tv-btns">
  <a class="tv-btn sec" href="{{ p.map_url }}" target="_blank" rel="noopener">Map</a>
''',
         r'''</form>
{% else %}
{% if p.lookup == 'failed' %}<div class="tv-msg err" data-lookup-failed>{{ p.lookup_note|default:"It could not be looked up." }}</div>
<form method="post" action="{% url 'travel:m_place_again' p.pk %}" class="tv-card tv-form">{% csrf_token %}<input type="hidden" name="next" value="{{ request.path }}">
  <label for="rn" class="tv-muted tv-small">Name (add the town to help)</label><input id="rn" name="name" class="tv-input" maxlength="160" value="{{ p.name }}" required>
  <button type="submit" class="tv-btn">Look it up again</button></form>{% endif %}
{% if p.lookup == 'choose' %}{% comment %} TR-5 - which of two or three places was meant. {% endcomment %}<section class="tv-card" data-choose><p class="tv-h2">Which one did you mean?</p>
  {% for o in p.options %}<form method="post" action="{% url 'travel:m_place_pick' p.pk %}" style="margin: 0">{% csrf_token %}<input type="hidden" name="next" value="{{ request.path }}"><input type="hidden" name="pick" value="{{ forloop.counter0 }}"><button type="submit" class="tv-btn sec wide" style="text-align: left; white-space: normal; height: auto; padding: 10px" data-option><b>{{ o.name }}</b>{% if o.city or o.country %} · {{ o.city }}{% if o.city and o.country %}, {% endif %}{{ o.country }}{% endif %}{% if o.address %}<span class="tv-muted tv-small" style="display: block">{{ o.address }}</span>{% endif %}</button></form>{% endfor %}
  <form method="post" action="{% url 'travel:m_place_pick' p.pk %}" style="margin: 0">{% csrf_token %}<input type="hidden" name="next" value="{{ request.path }}"><input type="hidden" name="pick" value="none"><button type="submit" class="tv-btn sec wide" data-none>None of these</button></form>
</section>{% endif %}
{% if p.booking %}<div class="tv-msg" data-booked>Booked: <a href="{% url 'travel:m_booking' p.booking.pk %}">{{ p.booking.title }}</a> &mdash; on the itinerary as the booking.</div>{% endif %}
<div class="tv-btns">
  <a class="tv-btn sec" href="{{ p.map_url }}" target="_blank" rel="noopener">Map</a>
'''),
        (r'''<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-card tv-form" data-place-move>{% csrf_token %}<input type="hidden" name="next" value="{{ request.path }}">
  <p class="tv-h2">When</p>
  <select name="day" class="tv-select" aria-label="Day"><option value="">The wish list</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if p.day == d %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select>
  <input type="time" name="time" class="tv-input" value="{{ p.time|time:'H:i' }}" aria-label="Time (optional)">
  <button type="submit" class="tv-btn">Save</button>
''',
         r'''<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-card tv-form" data-place-move>{% csrf_token %}<input type="hidden" name="next" value="{{ request.path }}">
  <p class="tv-h2">When</p>
  <select name="day" class="tv-select" aria-label="Day"><option value="">Things to do (no day yet)</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if p.day == d %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select>
  <input type="time" name="time" class="tv-input" value="{{ p.time|time:'H:i' }}" aria-label="Time (optional)">
  <button type="submit" class="tv-btn">Save</button>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Wish list</a><a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
''',
         r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a><a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
'''),
        (r'''<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">Add a place</a></p>{% endfor %}</section>
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
''',
         r'''<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">Add a place</a></p>{% endfor %}</section>
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
{% if wish %}<p class="tv-h3" id="todo">Things to do &mdash; no day yet</p>
<section class="tv-card" data-itinerary-todo>{% for b in wish %}{% include 'travel/m/_row.html' %}{% endfor %}<a href="?tab=wish" class="tv-muted tv-small">Put them on a day</a></section>{% endif %}
{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Add a place</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
  {% include 'travel/m/_row.html' with b=p %}
  {% if trip_days %}<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-inline" data-move-form>{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="need_day" value="1">
    <select name="day" class="tv-select" style="flex: 1" aria-label="Put {{ p.name }} on a day" required><option value="" selected>Choose a day&hellip;</option>{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
    <button type="submit" class="tv-btn sec">Put on the day</button></form>{% endif %}
</section>
'''),
        (r'''{% endif %}
{% comment %} TR-4 - the trip as a PDF, straight to the phone's share sheet (WhatsApp, mail...); opened instead where sharing files is not possible. {% endcomment %}
<div class="tv-btns" data-trip-pdf-phone>
  <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=summary" data-share-name="trip_{{ trip.name|slugify }}_summary.pdf" data-share-title="{{ trip.name }}">PDF summary</button>
  <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=detailed" data-share-name="trip_{{ trip.name|slugify }}_detailed.pdf" data-share-title="{{ trip.name }}">PDF detailed</button>
</div>
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% endblock %}
''',
         r'''{% endif %}
{% comment %} TR-4 - the trip as a PDF, straight to the phone's share sheet (WhatsApp, mail...); opened instead where sharing files is not possible. {% endcomment %}
{% comment %} TR-5 (Demetri, 16 Nov): one PDF button with the choice of Summary or Detailed, as on the computer. {% endcomment %}<details class="tv-card" data-trip-pdf-phone style="padding: 0">
  <summary class="tv-btn sec wide" style="list-style: none">PDF &#9662;</summary>
  <div class="tv-btns" style="padding: 10px">
    <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=summary" data-share-name="trip_{{ trip.name|slugify }}_summary.pdf" data-share-title="{{ trip.name }}">Summary</button>
    <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=detailed" data-share-name="trip_{{ trip.name|slugify }}_detailed.pdf" data-share-title="{{ trip.name }}">Detailed</button>
  </div>
</details>
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'place_form.html'), [
        (r'''    <div class="tv-form-grid">
        <div class="tv-wide"><label for="pq">Type a name, or paste a Google Maps or website link</label><input id="pq" name="q" class="form-control" maxlength="500" required value="{{ q }}" placeholder="e.g. Gulbenkian museum" autofocus></div>
        <div><label for="pd">Where should it go?</label><select id="pd" name="day" class="form-control"><option value="">The wish list</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if d|date:'Y-m-d' == day_pick %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select></div>
        <div><label for="pt">Time (optional)</label><input id="pt" type="time" name="time" class="form-control"></div>
        <div class="tv-wide"><label for="pn">Note</label><input id="pn" name="notes" class="form-control" maxlength="500" placeholder="e.g. book the 10:30 tour"></div>
''',
         r'''    <div class="tv-form-grid">
        <div class="tv-wide"><label for="pq">Type a name, or paste a Google Maps or website link</label><input id="pq" name="q" class="form-control" maxlength="500" required value="{{ q }}" placeholder="e.g. Gulbenkian museum" autofocus></div>
        <div><label for="pd">Where should it go?</label><select id="pd" name="day" class="form-control"><option value="">Things to do (no day yet)</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if d|date:'Y-m-d' == day_pick %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select></div>
        <div><label for="pt">Time (optional)</label><input id="pt" type="time" name="time" class="form-control"></div>
        <div class="tv-wide"><label for="pn">Note</label><input id="pn" name="notes" class="form-control" maxlength="500" placeholder="e.g. book the 10:30 tour"></div>
'''),
        (r'''{% else %}
{% if p.lookup == 'waiting' %}<div class="alert alert-info" role="status" data-looking><i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Looking it up on the web&hellip; this page refreshes by itself.</div>{% endif %}
{% if p.lookup == 'failed' %}<div class="alert alert-warning" role="status" data-lookup-failed>{{ p.lookup_note|default:"It could not be looked up." }} <form method="post" action="{% url 'travel:place_again' p.pk %}" style="display: inline">{% csrf_token %}<button type="submit" class="btn btn-link btn-sm p-0">Try again</button></form></div>{% endif %}
{% if p.about %}<section class="form-card"><p style="margin: 0">{{ p.about }}</p></section>{% endif %}
<form method="post" class="form-card" data-place-edit>
    {% csrf_token %}
    <div class="tv-form-grid">
        <div class="tv-wide"><label for="en">Name</label><input id="en" name="name" class="form-control" maxlength="160" required value="{{ p.name }}"></div>
        <div><label for="ek">Kind</label><select id="ek" name="kind" class="form-control">{% for k, l in kinds %}<option value="{{ k }}"{% if p.kind == k %} selected{% endif %}>{{ l }}</option>{% endfor %}</select></div>
        <div><label for="ed">Day</label><select id="ed" name="day" class="form-control"><option value="">The wish list</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if p.day == d %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select></div>
        <div><label for="et">Time</label><input id="et" type="time" name="time" class="form-control" value="{{ p.time|time:'H:i' }}"></div>
        <div class="tv-wide"><label for="ea">Address</label><input id="ea" name="address" class="form-control" maxlength="255" value="{{ p.address }}"></div>
''',
         r'''{% else %}
{% if p.lookup == 'waiting' %}<div class="alert alert-info" role="status" data-looking><i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Looking it up on the web&hellip; this page refreshes by itself.</div>{% endif %}
{% if p.lookup == 'failed' %}<div class="alert alert-warning" role="status" data-lookup-failed>{{ p.lookup_note|default:"It could not be looked up." }} {% comment %} TR-5 - Try again looks up what is in the Name box now. {% endcomment %}<button type="submit" form="pedit" formaction="{% url 'travel:place_again' p.pk %}" class="btn btn-link btn-sm p-0" title="Look it up again by the name in the box below">Try again</button></div>{% endif %}
{% if p.lookup == 'choose' %}{% comment %} TR-5 (Demetri, 16 Nov: "if it finds two or three options, then maybe the user must be given these options to choose from"). {% endcomment %}<section class="form-card" data-choose>
    <h3 class="form-section-title">Which one did you mean?</h3>
    {% for o in p.options %}<form method="post" action="{% url 'travel:place_pick' p.pk %}" style="margin: 0 0 8px">{% csrf_token %}<input type="hidden" name="pick" value="{{ forloop.counter0 }}"><button type="submit" class="btn action-secondary" style="width: 100%; text-align: left; white-space: normal" data-option><b>{{ o.name }}</b>{% if o.city or o.country %} &middot; {{ o.city }}{% if o.city and o.country %}, {% endif %}{{ o.country }}{% endif %}{% if o.address %}<span class="tv-detail">{{ o.address }}</span>{% endif %}{% if o.about %}<span class="tv-detail">{{ o.about }}</span>{% endif %}</button></form>{% endfor %}
    <form method="post" action="{% url 'travel:place_pick' p.pk %}" style="margin: 0">{% csrf_token %}<input type="hidden" name="pick" value="none"><button type="submit" class="btn btn-link btn-sm p-0" data-none>None of these &mdash; keep it as I typed it</button></form>
</section>{% endif %}
{% if p.booking %}<section class="form-card" data-booked><p style="margin: 0"><i class="fas fa-check-circle tv-paid" aria-hidden="true"></i> Booked: <a href="{% url 'travel:booking' p.booking.pk %}">{{ p.booking.title }}</a>{% if p.booking.start_date %} &middot; {{ p.booking.start_date|date:"D j M" }}{% if p.booking.start_time %} {{ p.booking.start_time|time:"H:i" }}{% endif %}{% endif %}. It is on the itinerary as the booking; cancel or delete the booking and it goes back to Things to do.</p></section>{% endif %}
{% if p.about %}<section class="form-card"><p style="margin: 0">{{ p.about }}</p></section>{% endif %}
<form method="post" class="form-card" data-place-edit id="pedit">
    {% csrf_token %}
    <div class="tv-form-grid">
        <div class="tv-wide"><label for="en">Name</label><input id="en" name="name" class="form-control" maxlength="160" required value="{{ p.name }}"></div>
        <div><label for="ek">Kind</label><select id="ek" name="kind" class="form-control">{% for k, l in kinds %}<option value="{{ k }}"{% if p.kind == k %} selected{% endif %}>{{ l }}</option>{% endfor %}</select></div>
        <div><label for="ed">Day</label><select id="ed" name="day" class="form-control"><option value="">Things to do (no day yet)</option>{% for d in days %}<option value="{{ d|date:'Y-m-d' }}"{% if p.day == d %} selected{% endif %}>{{ d|date:"D j M" }}</option>{% endfor %}</select></div>
        <div><label for="et">Time</label><input id="et" type="time" name="time" class="form-control" value="{{ p.time|time:'H:i' }}"></div>
        <div class="tv-wide"><label for="ea">Address</label><input id="ea" name="address" class="form-control" maxlength="255" value="{{ p.address }}"></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    {% comment %} TR-4 (Demetri, 15 Nov): the trip as a PDF, summary or detailed, to download or share (WhatsApp, mail) through the house PDF viewer. {% endcomment %}
    <button type="button" class="btn action-secondary" data-trip-pdf="summary" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><i class="fas fa-file-pdf"></i> PDF summary</button>
    <button type="button" class="btn action-secondary" data-trip-pdf="detailed" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><i class="fas fa-file-pdf"></i> PDF detailed</button>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
''',
         r'''    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
    {% comment %} TR-4 (Demetri, 15 Nov): the trip as a PDF, summary or detailed, to download or share (WhatsApp, mail) through the house PDF viewer. TR-5 (16 Nov: "I don't want two buttons for PDF. It should be one, but with a choice of Summary or Detailed"). {% endcomment %}
    <details class="tv-menu" data-pdf-menu><summary class="btn action-secondary" title="Make the trip into a PDF"><i class="fas fa-file-pdf"></i> PDF <i class="fas fa-caret-down" aria-hidden="true"></i></summary>
        <div class="tv-menu-pop">
            <button type="button" data-trip-pdf="summary" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><b>Summary</b><small>Day by day, the places, the costs</small></button>
            <button type="button" data-trip-pdf="detailed" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><b>Detailed</b><small>Every day with addresses, phones and times, then every booking in full</small></button>
        </div>
    </details>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
'''),
        (r'''<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary{% if planned %} <span class="tv-sub">{{ planned }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Wish list{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>
</nav>
''',
         r'''<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>
</nav>
'''),
        (r'''    {% comment %} TR-4 - every day of the trip: the bookings (shaded) and the places planned, in time order. {% endcomment %}
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
''',
         r'''    {% comment %} TR-4 - every day of the trip: the bookings (shaded) and the places planned, in time order. {% endcomment %}
    {% if itinerary %}
    <nav class="tv-chips" aria-label="Days">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}">{{ day|date:"D j" }}</a>{% endfor %}{% if wish %}<a class="tv-chip" href="#todo">Things to do</a>{% endif %}</nav>
    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Add a place</a></div>
        {% for r in rows %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
    {% endfor %}
    {% comment %} TR-5 (Demetri, 16 Nov: "would it not make sense for the items in the wish list that have not been allocated a specific day to appear at the bottom of the itinerary just as things to do"). {% endcomment %}
    {% if wish %}<section class="form-card tv-day" id="todo" data-itinerary-todo>
        <div class="tv-row"><h3>Things to do &mdash; no day yet</h3><a href="{% url 'travel:trip_wishlist' trip.pk %}" class="small">Put them on a day</a></div>
        {% for p in wish %}{% include 'travel/_place_row.html' %}{% endfor %}
    </section>{% endif %}
    {% else %}
    <section class="form-card"><p style="margin: 0">The itinerary needs the trip&rsquo;s dates: add a booking, or set From and To under Edit trip.</p></section>
    {% endif %}
{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. {% endcomment %}
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Add a place</a></div>
        {% for p in wish %}
        <div data-wish-item>
            {% include 'travel/_place_row.html' %}
            {% if trip_days %}{% comment %} TR-5 (Demetri, 16 Nov: "To Move, you should at least need as a minimum to have a date"): no day is chosen for you. {% endcomment %}<form method="post" action="{% url 'travel:place_move' p.pk %}" class="tv-acts" style="margin: 0 0 8px 52px" data-move-form>{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="need_day" value="1">
                <label for="mv{{ p.pk }}" class="small" style="margin: 0">Put on</label>
                <select id="mv{{ p.pk }}" name="day" class="form-control form-control-sm" style="max-width: 170px" required><option value="" selected>Choose a day&hellip;</option>{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
                <input type="time" name="time" class="form-control form-control-sm" style="max-width: 120px" aria-label="Time (optional)" title="Time (optional)">
                <button type="submit" class="btn action-secondary btn-sm" title="Put it on the day chosen">Move</button></form>{% endif %}
        </div>
        {% empty %}<p class="tv-sub" style="margin: 8px 0 0">Nothing yet. Add a museum, a garden, a restaurant &mdash; type its name or paste a link, and its address, hours and price are looked up for you. On the phone, share a place from Google Maps to Travel.</p>{% endfor %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_form.html'), [
        (r'''        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control" value="{{ trip.end_date|date:'Y-m-d' }}"></div>
        {% endif %}
        <div class="tv-wide"><label for="tc">Countries</label><input id="tc" name="countries" class="form-control" maxlength="200" value="{{ trip.countries }}">{% if trip.where and trip.where != trip.countries %}<div class="tv-sub small">Shown as <b>{{ trip.where }}</b> &mdash; the bookings&rsquo; countries with any you type here.</div>{% endif %}</div>
        <div class="tv-wide"><label for="no">Notes</label><textarea id="no" name="notes" class="form-control" rows="4">{{ trip.notes }}</textarea></div>
        {% if not trip.by_bookings %}<div class="tv-wide tv-sub small">For planning before anything is booked. Once the trip has bookings with dates, its dates come from them.</div>{% endif %}
''',
         r'''        <div><label for="te">To</label><input id="te" type="date" name="end_date" class="form-control" value="{{ trip.end_date|date:'Y-m-d' }}"></div>
        {% endif %}
        <div class="tv-wide"><label for="tc">Other countries</label><input id="tc" name="countries" class="form-control" maxlength="200" value="{{ trip.countries }}" placeholder="Only countries with nothing booked yet"><div class="tv-sub small" data-countries-hint>{% comment %} TR-5, 16 Nov 2026. {% endcomment %}The countries come from the bookings &mdash; the hotels, the cars, where the flights land &mdash; and your home country is left out. Type a country here only if you are going there with nothing booked yet.{% if trip.where %} Shown now as <b>{{ trip.where }}</b>.{% endif %}</div></div>
        <div class="tv-wide"><label for="no">Notes</label><textarea id="no" name="notes" class="form-control" rows="4">{{ trip.notes }}</textarea></div>
        {% if not trip.by_bookings %}<div class="tv-wide tv-sub small">For planning before anything is booked. Once the trip has bookings with dates, its dates come from them.</div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_pdf.html'), [
        (r'''<tr><td class="t">{% if r.time %}{{ r.time|time:"H:i" }}{% endif %}</td><td class="w"><span class="place">{{ r.name }}</span>{% if r.address %} <span class="muted">· {{ r.address }}</span>{% endif %}{% if r.hours %}<br><span class="muted">{{ r.hours }}{% if r.price %} · {{ r.price }}{% endif %}</span>{% endif %}</td><td class="c">{% if r.done %}<span class="muted">done</span>{% endif %}</td></tr>
{% else %}
<tr><td class="t">{% if r.when %}{{ r.when|time:"H:i" }}{% endif %}</td><td class="w">{% if r.label %}{{ r.label }}: {% endif %}<b>{{ r.title }}</b>{% if r.cancelled %} <span class="due">CANCELLED</span>{% endif %}<br><span class="muted">{% if r.route %}{{ r.route }} · {% endif %}{% if r.what == 'start' and r.end_time and r.end_date == r.start_date %}until {{ r.end_time|time:"H:i" }} · {% endif %}{% if r.reference %}ref {{ r.reference }}{% endif %}{% if r.who %} · {{ r.who }}{% endif %}</span></td><td class="c">{% if r.what != 'during' and r.what != 'end' %}{% if r.amount is not None %}<b>{{ r.eur_label|default:"rate pending" }}</b><br><span class="{% if r.paid == 'paid' %}paid{% else %}due{% endif %}">{{ r.status_label }}</span>{% elif r.included %}<span class="muted">incl. in {{ r.included.segment|default:r.included.title }}</span>{% endif %}{% endif %}</td></tr>
{% endif %}
{% empty %}<tr><td class="t"></td><td class="w"><span class="muted">Nothing planned.</span></td><td class="c"></td></tr>
''',
         r'''<tr><td class="t">{% if r.time %}{{ r.time|time:"H:i" }}{% endif %}</td><td class="w"><span class="place">{{ r.name }}</span>{% if r.address %} <span class="muted">· {{ r.address }}</span>{% endif %}{% if r.hours %}<br><span class="muted">{{ r.hours }}{% if r.price %} · {{ r.price }}{% endif %}</span>{% endif %}</td><td class="c">{% if r.done %}<span class="muted">done</span>{% endif %}</td></tr>
{% else %}
<tr><td class="t">{% if r.when %}{{ r.when|time:"H:i" }}{% endif %}</td><td class="w">{% if r.label %}{{ r.label }}: {% endif %}<b>{{ r.title }}</b>{% if r.cancelled %} <span class="due">CANCELLED</span>{% endif %}<br><span class="muted">{% if r.route %}{{ r.route }} · {% endif %}{% if r.what == 'start' and r.end_time and r.end_date == r.start_date %}until {{ r.end_time|time:"H:i" }} · {% endif %}{% if r.reference %}ref {{ r.reference }}{% endif %}{% if r.who %} · {{ r.who }}{% endif %}</span>{% if kind == 'detailed' and r.what != 'during' %}{% if r.kind == 'stay' or r.kind == 'restaurant' %}{% comment %} TR-5 (Demetri, 16 Nov: "for the detailed itinerary ... more details for like hotels (address, phone number, check in and check out time, etc.) The same for restaurants"). {% endcomment %}{% if r.address %}<br><span class="muted">{{ r.address }}</span>{% endif %}{% if r.phone %}<br><span class="muted">Tel {{ r.phone }}</span>{% endif %}{% if r.kind == 'stay' %}<br><span class="muted">{% if r.what == 'start' %}Check in{% if r.start_time %} from {{ r.start_time|time:"H:i" }}{% endif %}{% if r.end_date %} · check out {{ r.end_date|date:"D j M" }}{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}{% else %}Check out{% if r.end_time %} by {{ r.end_time|time:"H:i" }}{% endif %}{% endif %}</span>{% endif %}{% if r.kind == 'restaurant' and r.details %}<br><span class="muted">{{ r.details|truncatechars:160 }}</span>{% endif %}{% endif %}{% endif %}</td><td class="c">{% if r.what != 'during' and r.what != 'end' %}{% if r.amount is not None %}<b>{{ r.eur_label|default:"rate pending" }}</b><br><span class="{% if r.paid == 'paid' %}paid{% else %}due{% endif %}">{{ r.status_label }}</span>{% elif r.included %}<span class="muted">incl. in {{ r.included.segment|default:r.included.title }}</span>{% endif %}{% endif %}</td></tr>
{% endif %}
{% empty %}<tr><td class="t"></td><td class="w"><span class="muted">Nothing planned.</span></td><td class="c"></td></tr>
'''),
        (r'''
{% if wish %}
<h2 class="sec">Wish list</h2>
<table class="rows">{% for p in wish %}<tr><td class="t"></td><td class="w"><span class="place">{{ p.name }}</span>{% if p.address %} <span class="muted">· {{ p.address }}</span>{% endif %}{% if p.hours or p.price %}<br><span class="muted">{{ p.hours }}{% if p.hours and p.price %} · {% endif %}{{ p.price }}</span>{% endif %}</td><td class="c"></td></tr>{% endfor %}</table>
{% endif %}
''',
         r'''
{% if wish %}
<h2 class="sec">Things to do - no day yet</h2>
<table class="rows">{% for p in wish %}<tr><td class="t"></td><td class="w"><span class="place">{{ p.name }}</span>{% if p.address %} <span class="muted">· {{ p.address }}</span>{% endif %}{% if p.hours or p.price %}<br><span class="muted">{{ p.hours }}{% if p.hours and p.price %} · {% endif %}{{ p.price }}</span>{% endif %}</td><td class="c"></td></tr>{% endfor %}</table>
{% endif %}
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('place/<int:place_id>/again/', views_places.place_again,
         name='place_again'),
    path('place/<int:place_id>/delete/', views_places.place_delete,
         name='place_delete'),
''',
         r'''    path('place/<int:place_id>/again/', views_places.place_again,
         name='place_again'),
    # TR-5 - which of two or three places was meant.
    path('place/<int:place_id>/pick/', views_places.place_pick,
         name='place_pick'),
    path('place/<int:place_id>/delete/', views_places.place_delete,
         name='place_delete'),
'''),
        (r'''    path('m/place/<int:place_id>/again/', views_places.place_again,
         name='m_place_again'),
    path('m/place/<int:place_id>/delete/', views_places.place_delete,
         name='m_place_delete'),
''',
         r'''    path('m/place/<int:place_id>/again/', views_places.place_again,
         name='m_place_again'),
    path('m/place/<int:place_id>/pick/', views_places.place_pick,
         name='m_place_pick'),
    path('m/place/<int:place_id>/delete/', views_places.place_delete,
         name='m_place_delete'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''ICONS = {'flight': 'fa-plane', 'stay': 'fa-bed', 'car': 'fa-car',
         'train': 'fa-train', 'ferry': 'fa-ship', 'transfer': 'fa-taxi',
         'activity': 'fa-ticket-alt', 'other': 'fa-map-marker-alt'}


''',
         r'''ICONS = {'flight': 'fa-plane', 'stay': 'fa-bed', 'car': 'fa-car',
         'train': 'fa-train', 'ferry': 'fa-ship', 'transfer': 'fa-taxi',
         'activity': 'fa-ticket-alt', 'restaurant': 'fa-utensils',
         'other': 'fa-map-marker-alt'}


'''),
        (r'''    else:
        start, end = trip.start_date, trip.end_date or trip.start_date
    seen = []
    for c in [getattr(b, 'country', '') for b in sorted(
            live, key=lambda b: b.start_date or dt.date.max)] + \
            trip.country_list:
        c = (c or '').strip()
        if c and c.lower() not in [x.lower() for x in seen]:
''',
         r'''    else:
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
'''),
        (r'''        names += [x.strip() for x in (b.traveller_names or '').split(',')
                  if x.strip()]
        b.who = ', '.join(names)
    else:
        b.who = ''
    return b


''',
         r'''        names += [x.strip() for x in (b.traveller_names or '').split(',')
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


'''),
        (r'''    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
''',
         r'''    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
    # TR-5 - a hotel's or a restaurant's missing details, looked up once.
    from .places import start_details
    start_details(bs)
    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
'''),
        (r'''        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'planned': len([p for p in pl if p.day]),
        'trip_days': days_of(start, end)})

''',
         r'''        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end)})

'''),
        (r'''                        changes=changed)
            add_files(request, b)
            messages.success(request, 'Booking saved.')
            return redirect('travel:booking', booking_id=b.pk)
''',
         r'''                        changes=changed)
            add_files(request, b)
            # TR-5 - a table at a restaurant on the wish list takes that
            # place onto its day; a hotel's or restaurant's missing
            # address, phone and times are looked up.
            from . import places as P
            P.link_booking(b)
            P.start_details([b], limit=1)
            messages.success(request, 'Booking saved.')
            return redirect('travel:booking', booking_id=b.pk)
'''),
        (r'''    for f in list(b.files.all()):
        drop_file(f)
    b.delete()
    messages.success(request, 'Booking deleted.')
''',
         r'''    for f in list(b.files.all()):
        drop_file(f)
    # TR-5 - a place it was booked for goes back to the wish list.
    from .places import unlink_deleted
    unlink_deleted(b)
    b.delete()
    messages.success(request, 'Booking deleted.')
'''),
    ]),
    (os.path.join('travel', 'views_places.py'), [
        (r'''phone (Share -> Travel); Claude looks it up (travel/places.py). With a day
it sits on the itinerary among the bookings; without one, on the trip's
wish list. Everyone on the trip can add, move, tick off and remove them -
the same as bookings.

''',
         r'''phone (Share -> Travel); Claude looks it up (travel/places.py). With a day
it sits on the itinerary among the bookings; without one, on the trip's
things to do. Everyone on the trip can add, move, tick off and remove them -
the same as bookings.

'''),
        (r'''        if p.lookup == 'waiting':
            P.start(p)
        messages.success(request, '%s added to %s.' % (
            p.name, 'the wish list' if not p.day else
            p.day.strftime('%a %d %b').replace(' 0', ' ')))
        if request.path.startswith('/travel/m/'):
''',
         r'''        if p.lookup == 'waiting':
            P.start(p)
        else:
            P.link_place(p)
        messages.success(request, '%s added to %s.' % (
            p.name, 'Things to do' if not p.day else
            p.day.strftime('%a %d %b').replace(' 0', ' ')))
        if request.path.startswith('/travel/m/'):
'''),
        (r'''@require_POST
def place_move(request, place_id):
    """To a day (and a time), or back to the wish list."""
    p = _place(request, place_id)
    p.day = _date(request.POST.get('day'))
    p.time = _time(request.POST.get('time')) if p.day else None
    p.save(update_fields=['day', 'time', 'updated_at'])
    messages.success(request, '%s: %s.' % (p.name, 'on the wish list'
                                           if not p.day else
                                           p.day.strftime('%a %d %b')
''',
         r'''@require_POST
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
'''),
        (r'''@require_POST
def place_again(request, place_id):
    """Look it up again."""
    p = _place(request, place_id)
    p.lookup, p.started, p.lookup_note = 'waiting', None, ''
    p.save(update_fields=['lookup', 'started', 'lookup_note',
                          'updated_at'])
    P.start(p)
    return _next(request, '/travel/place/%d/' % p.pk)

''',
         r'''@require_POST
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
    raise SystemExit('TR-5 REFUSED: %s' % msg)


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
    if "'test_travel_five.py'" in read(pq):
        print('TR-5 already applied.')
        return 0
    if "'test_travel_four.py'" not in read(pq):
        refuse('Release 85 is not applied - this round registers after it.')
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
        print('TR-5 --check: %d file(s) would change, none written; %d '
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
    print('TR-5 applied - Travel: restaurants and the review. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
