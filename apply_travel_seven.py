# -*- coding: utf-8 -*-
"""apply_travel_seven.py - round TR-7, 16 Nov 2026.

RELEASE 87 (with TR-6) - TRAVEL: SETTLING UP, COMPARING TRIPS, PAST TRIPS.

    - After a trip: still To pay? The trip asks - Mark ticked ones paid
      (at the euro amount typed), Leave as it is, or Ask me again in a
      week. Never marked paid by itself.
    - Compare trips (travel/compare.py): tick two or more on Travel; like
      for like - hotel per night, flights per person per flight, car hire
      per day, trains, restaurants, activities, per day; where the money
      went; what stands out; every hotel per night. On the phone too.
    - Nothing coming up: Travel and the phone's Trips show the past
      trips, newest first, marked Past; Today shows the last trip and the
      ones before it.

New files ship beside this patcher. Stands on TR-6 (apply_travel_six.py),
which ships in the same release. Idempotent. Edits backed up to
.bak_travel7. MIGRATION: travel 0006 - run `python manage.py migrate`.
"""
import os
import sys

SUFFIX = '.bak_travel7'
MARK = 'TR-7, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/compare.py',
    'travel/migrations/0006_settle_up.py',
    'travel/templates/travel/compare.html',
    'travel/templates/travel/m/compare.html',
    'test_travel_seven.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_five.py',
    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    'test_travel_six.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_five.py',
    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    'test_travel_six.py',
    # TR-7, 16 Nov 2026 - Release 88: settling up after a trip, comparing
    # trips, past trips when nothing is ahead.
    'test_travel_seven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    '.bak_travel6',
]

''',
         r'''    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    '.bak_travel6',
    # TR-7, 16 Nov 2026 - Release 88: settling up, comparing trips.
    '.bak_travel7',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-info-circle">
    <h6><i class="fas fa-plane"></i> Travel</h6>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Each trip also has an <strong>Itinerary</strong> and <strong>Things to do</strong> &mdash; see <strong>Itinerary &amp; Places</strong>.</p>
''',
         r'''           data-tab-icon="fa-info-circle">
    <h6><i class="fas fa-plane"></i> Travel</h6>
    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, newest first, each marked <em>Past</em>. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Each trip also has an <strong>Itinerary</strong> and <strong>Things to do</strong> &mdash; see <strong>Itinerary &amp; Places</strong>.</p>
'''),
        (r'''    <p><strong>PDF</strong> (on the trip) makes the trip into a PDF &mdash; press it and choose <strong>Summary</strong> or <strong>Detailed</strong>. The summary is the trip day by day &mdash; what starts each day, the places planned &mdash; with Things to do and the costs. In the detailed one each day also gives every hotel&rsquo;s and restaurant&rsquo;s address, phone number and check-in and check-out times, and it ends with every booking in full: reference, times, address, phone, travellers, cost, cancellation and payment dates, documents and details. It opens in the PDF viewer to download or, on a phone, to share by WhatsApp or mail; in the phone app it goes straight to the phone&rsquo;s share sheet.</p>
    <p>A return flight booked together has one price: it sits on the first flight, and the other says <strong>Included in</strong> that flight rather than showing nothing.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
''',
         r'''    <p><strong>PDF</strong> (on the trip) makes the trip into a PDF &mdash; press it and choose <strong>Summary</strong> or <strong>Detailed</strong>. The summary is the trip day by day &mdash; what starts each day, the places planned &mdash; with Things to do and the costs. In the detailed one each day also gives every hotel&rsquo;s and restaurant&rsquo;s address, phone number and check-in and check-out times, and it ends with every booking in full: reference, times, address, phone, travellers, cost, cancellation and payment dates, documents and details. It opens in the PDF viewer to download or, on a phone, to share by WhatsApp or mail; in the phone app it goes straight to the phone&rsquo;s share sheet.</p>
    <p>A return flight booked together has one price: it sits on the first flight, and the other says <strong>Included in</strong> that flight rather than showing nothing.</p>
    <p><strong>After a trip.</strong> The day after a trip ends, if any booking still says To pay or Part paid, the trip asks whether everything is paid: the bookings are listed, ticked, with the amount paid in euros (change it if the card statement says otherwise). <strong>Mark ticked ones paid</strong>, <strong>Leave as it is</strong> (not asked again) or <strong>Ask me again in a week</strong>. Nothing is marked paid without you; each change is in the booking&rsquo;s Changes. The trip&rsquo;s card on Travel and the phone&rsquo;s Today show what is still to pay until then.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
'''),
        (r'''           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>Open <strong>alivente.online/travel/m/</strong> on the phone &mdash; or press <strong>Phone app</strong> on the Travel page and point the phone&rsquo;s camera at the code &mdash; and choose <strong>Add to Home screen</strong> (Android: Chrome&rsquo;s menu; iPhone: Safari&rsquo;s Share button). It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
''',
         r'''           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>On the computer, press <strong>Phone app</strong> on the Travel page: a code and six steps. Scan the code with the phone&rsquo;s camera and tap the link (or type <strong>alivente.online/travel/m/</strong> into Chrome), sign in, tap the <strong>three dots &#8942;</strong> at the top right, scroll down to <strong>Add to Home screen</strong> (or <strong>Install app</strong>), choose <strong>Install</strong> &mdash; not <em>Create shortcut</em> &mdash; and <strong>Install</strong> again. On an iPhone: Safari&rsquo;s Share button &rarr; <strong>Add to Home Screen</strong>. It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    shared_with = models.ManyToManyField(User, blank=True,
                                         related_name='shared_trips')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    shared_with = models.ManyToManyField(User, blank=True,
                                         related_name='shared_trips')
    # TR-7, 16 Nov 2026 - SETTLING UP AFTER A TRIP (Demetri: "Once all the
    # trip days have passed, would it make sense for the system to set all
    # Reservations as paid (maybe to ask first)?"). Asked, never done by
    # itself: settle_off once someone says Leave as it is; settle_after
    # for Ask me again in a week.
    settle_off = models.BooleanField(default=False)
    settle_after = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''            booking__trip=trip, booking__start_date__in=(
                day, day + dt.timedelta(days=1))).count()
    return page(request, 'travel/m/today.html', ctx)

''',
         r'''            booking__trip=trip, booking__start_date__in=(
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
            due = unsettled(last, list(last.bookings.all()), day)
            last.owing = eur(sum((b.due_eur or 0) for b in due)) \
                if due else ''
            ctx['last'], ctx['earlier'] = last, past[1:6]
    return page(request, 'travel/m/today.html', ctx)

'''),
        (r'''        sel = sorted([t for t in rows if not (t.end and t.end < day)],
                     key=lambda t: t.start or far)
    return page(request, 'travel/m/trips.html', {
        'trips': sel, 'past': past, 'tab': 'trips',
        'checks': inbox.open_count(request.user)})

''',
         r'''        sel = sorted([t for t in rows if not (t.end and t.end < day)],
                     key=lambda t: t.start or far)
    # TR-7 - nothing ahead: the past trips, newest first, said so.
    auto_past = not past and not sel and any(t.end and t.end < day
                                             for t in rows)
    if auto_past:
        sel = sorted([t for t in rows if t.end and t.end < day],
                     key=lambda t: t.start or far, reverse=True)
    for t in sel:
        t.past = bool(t.end and t.end < day)
    return page(request, 'travel/m/trips.html', {
        'trips': sel, 'past': past, 'tab': 'trips', 'auto_past': auto_past,
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)})

'''),
        (r'''                ).strip() or b.segment or b.title
    p.seat_shown = p.seat or info.get('seat', '')
    return p

''',
         r'''                ).strip() or b.segment or b.title
    p.seat_shown = p.seat or info.get('seat', '')
    # TR-7, 16 Nov 2026 - an airline's own "Add to Google Wallet" link stops
    # working once the flight is over (Cyprus Airways answers
    # CKI_BOARDINGPASS_NONEFOUND), so it is offered only before then.
    p.over = flown(b, timezone.localtime().replace(tzinfo=None))
    return p

'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-menu-pop button:hover, .tv-menu-pop button:focus { background: var(--alv-surface); }
.tv-menu-pop small { color: var(--alv-ink-soft); }
.tv-detail { display: block; color: var(--alv-ink-soft); font-size: 0.85rem; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
''',
         r'''.tv-menu-pop button:hover, .tv-menu-pop button:focus { background: var(--alv-surface); }
.tv-menu-pop small { color: var(--alv-ink-soft); }
/* TR-7, 16 Nov 2026 - past trips, ticking trips to compare, settling up. */
.tv-steps { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 6px; }
@media screen and (max-width: 575.98px) { .tv-phone.tv-phone-wide { grid-template-columns: 1fr !important; } }
.tv-pickcard { display: flex; flex-direction: column; gap: 6px; }
.tv-pickcard > .tv-card { flex: 1; }
.tv-pick { display: inline-flex; align-items: center; gap: 8px; min-height: 32px; margin: 0; padding-left: 4px; cursor: pointer; }
.tv-pick input { width: 18px; height: 18px; }
.tv-pasttag { color: var(--alv-ink-soft); }
.tv-note { padding: 10px 14px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); background: var(--alv-surface); }
.tv-settle { border: 2px solid var(--alv-warn-ink); }
.tv-settle-row { display: grid; grid-template-columns: 28px minmax(0, 1fr) 110px 130px; gap: 8px 12px; align-items: center; padding: 8px 0; border-top: 1px solid var(--alv-line-soft); }
.tv-cmp { width: 100%; border-collapse: collapse; min-width: 640px; }
.tv-cmp th, .tv-cmp td { padding: 9px 8px; text-align: left; vertical-align: top; border-top: 1px solid var(--alv-line-soft); }
.tv-cmp thead th { border-top: 0; color: var(--alv-ink-soft); font-weight: 600; font-size: 0.85rem; }
.tv-cmp tr.is-strong td, .tv-cmp tr.is-strong th { border-top: 2px solid var(--alv-ink); font-weight: 700; }
.tv-low { color: var(--alv-good); font-weight: 700; font-size: 0.78rem; }
.tv-more { color: var(--alv-warn-ink); font-weight: 700; font-size: 0.78rem; }
.tv-split { display: flex; height: 22px; border-radius: 6px; overflow: hidden; min-width: 4px; }
.tv-split span { display: block; height: 100%; }
.tv-key { display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -1px; }
@media screen and (max-width: 575.98px) {
  .tv-settle-row { grid-template-columns: 28px minmax(0, 1fr); }
}
.tv-detail { display: block; color: var(--alv-ink-soft); font-size: 0.85rem; }
.tv-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1.2rem; font-weight: 700; letter-spacing: .06em; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''{% extends 'base.html' %}
{% block title %}{{ b.title }} - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. One booking, everything about it. #}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}{{ b.title }} - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. One booking, everything about it. #}
'''),
        (r'''    {% comment %} TR-4 (Demetri, 15 Nov): delete without going into Edit first. {% endcomment %}
    <button type="submit" form="del-booking-view" class="btn action-secondary action-danger" data-delete-booking><i class="fas fa-trash-alt"></i> Delete</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''    {% comment %} TR-4 (Demetri, 15 Nov): delete without going into Edit first. {% endcomment %}
    <button type="submit" form="del-booking-view" class="btn action-secondary action-danger" data-delete-booking><i class="fas fa-trash-alt"></i> Delete</button>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''            <div class="tv-row small"><b>{{ p.name|default:"Passenger" }}</b><span>{{ p.flight }}{% if p.seat_shown %} &middot; seat {{ p.seat_shown }}{% endif %}</span></div>
            {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}">{{ p.svg|safe }}</div>{% endif %}
            {% if p.wallet_link %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
        </div>
        {% endfor %}
''',
         r'''            <div class="tv-row small"><b>{{ p.name|default:"Passenger" }}</b><span>{{ p.flight }}{% if p.seat_shown %} &middot; seat {{ p.seat_shown }}{% endif %}</span></div>
            {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}">{{ p.svg|safe }}</div>{% endif %}
            {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
        </div>
        {% endfor %}
'''),
        (r'''</div>
<form id="del-booking-view" method="post" action="{% url 'travel:booking_delete' b.pk %}" onsubmit="return confirm('Delete {{ b.title|escapejs }} and its documents? This cannot be undone.');">{% csrf_token %}</form>
{% endblock %}
''',
         r'''</div>
<form id="del-booking-view" method="post" action="{% url 'travel:booking_delete' b.pk %}" onsubmit="return confirm('Delete {{ b.title|escapejs }} and its documents? This cannot be undone.');">{% csrf_token %}</form>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking_form.html'), [
        (r'''{% extends 'base.html' %}
{% block title %}{% if b.pk %}Edit booking{% else %}Add booking{% endif %} - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. Add or change a booking. #}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}{% if b.pk %}Edit booking{% else %}Add booking{% endif %} - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. Add or change a booking. #}
'''),
        (r'''
<div class="page-action-buttons">
    <a href="{% if b.pk %}{% url 'travel:booking' b.pk %}{% else %}{% url 'travel:trip' trip.pk %}{% endif %}" class="btn action-back" aria-label="Back">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''
<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% if b.pk %}{% url 'travel:booking' b.pk %}{% else %}{% url 'travel:trip' trip.pk %}{% endif %}" class="btn action-back" aria-label="Back">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''{% endif %}
</div>
{% endblock %}
''',
         r'''{% endif %}
</div>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'check.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% url 'travel:forwarding' %}" class="btn action-secondary"><i class="fas fa-envelope"></i> Forwarding</a>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''<div class="page-action-buttons">
    <a href="{% url 'travel:forwarding' %}" class="btn action-secondary"><i class="fas fa-envelope"></i> Forwarding</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'forwarding.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% url 'travel:check' %}" class="btn action-secondary"><i class="fas fa-inbox"></i> To check</a>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''<div class="page-action-buttons">
    <a href="{% url 'travel:check' %}" class="btn action-secondary"><i class="fas fa-inbox"></i> To check</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'today.html'), [
        (r'''
{% if not trip %}
<section class="tv-card" data-no-trip><p class="tv-h2">No trip coming up</p><p class="tv-muted" style="margin: 0">Forward a booking email to <b>{{ address|default:"the trips address" }}</b>, or share a ticket to Travel, and it will be waiting under To check.</p></section>
{% elif on_now %}
''',
         r'''
{% if not trip %}
{% if last %}{% comment %} TR-7, 16 Nov 2026 - nothing ahead: the last trip, then the earlier ones. {% endcomment %}
<a href="{% url 'travel:m_trip' last.pk %}" class="tv-card" data-last-trip>
  <div class="tv-row"><p class="tv-h2">{{ last.name }}</p><span class="tv-tag">Last trip</span></div>
  <div class="tv-muted">{{ last.start|date:"j M" }}{% if last.end and last.end != last.start %} – {{ last.end|date:"j M Y" }}{% endif %}{% if last.where %} · {{ last.where }}{% endif %}</div>
  {% if last.money.any %}<div class="tv-row"><span>Total</span><b>{{ last.money.total }}</b></div>{% endif %}
  {% if last.owing %}<div style="color: var(--tv-warn); font-weight: 600" data-owing>{{ last.owing }} still To pay &middot; settle up on the trip</div>{% endif %}
</a>
{% if earlier %}<p class="tv-h3">Earlier trips</p>
<section class="tv-card" data-earlier>{% for t in earlier %}<a href="{% url 'travel:m_trip' t.pk %}" class="tv-item" style="grid-template-columns: minmax(0, 1fr) auto"><span><b>{{ t.name }}</b><span class="tv-muted" style="display: block">{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% endif %}</span></span><span class="tv-muted" aria-hidden="true">›</span></a>{% endfor %}</section>{% endif %}
{% endif %}
<section class="tv-card" data-no-trip><p class="tv-h2">No trip coming up</p><p class="tv-muted" style="margin: 0">Forward a booking email to <b>{{ address|default:"the trips address" }}</b>, or share a ticket to Travel, and it will be waiting under To check.</p></section>
{% elif on_now %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trips.html'), [
        (r'''{% block sub %}<div class="sub">Yours and the ones shared with you</div>{% endblock %}
{% block content %}
<nav class="tv-chips" aria-label="Show"><a class="tv-chip{% if not past %} on{% endif %}" href="{% url 'travel:m_trips' %}">Upcoming</a><a class="tv-chip{% if past %} on{% endif %}" href="?show=past">Past</a></nav>
{% for t in trips %}
<a href="{% url 'travel:m_trip' t.pk %}" class="tv-card" data-trip>
  <div class="tv-row"><p class="tv-h2">{{ t.name }}</p>{% if t.people|length > 1 %}<span class="tv-tag sh">Shared</span>{% endif %}</div>
  <div class="tv-muted">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
  <div class="tv-row tv-small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span style="display: flex; padding-left: 6px">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
''',
         r'''{% block sub %}<div class="sub">Yours and the ones shared with you</div>{% endblock %}
{% block content %}
<nav class="tv-chips" aria-label="Show"><a class="tv-chip{% if not past and not auto_past %} on{% endif %}" href="{% url 'travel:m_trips' %}">Upcoming</a><a class="tv-chip{% if past or auto_past %} on{% endif %}" href="?show=past">Past</a>{% if can_compare %}<a class="tv-chip" href="{% url 'travel:m_compare' %}" data-compare-link>Compare</a>{% endif %}</nav>
{% if auto_past %}<section class="tv-card" data-auto-past><p class="tv-muted" style="margin: 0">Nothing coming up &mdash; your past trips, newest first.</p></section>{% endif %}
{% for t in trips %}
<a href="{% url 'travel:m_trip' t.pk %}" class="tv-card" data-trip>
  <div class="tv-row"><p class="tv-h2">{{ t.name }}</p><span>{% if t.past %}<span class="tv-tag" data-past>Past</span> {% endif %}{% if t.people|length > 1 %}<span class="tv-tag sh">Shared</span>{% endif %}</span></div>
  <div class="tv-muted">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
  <div class="tv-row tv-small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span style="display: flex; padding-left: 6px">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'merge.html'), [
        (r'''{% extends 'base.html' %}
{% block title %}Merge trips - Travel{% endblock %}
{% comment %} TRAVEL - TR-2, 15 Nov 2026. Merge another trip into this one: a preview first; the other trip's owner is asked when it is not yours. {% endcomment %}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}Merge trips - Travel{% endblock %}
{% comment %} TRAVEL - TR-2, 15 Nov 2026. Merge another trip into this one: a preview first; the other trip's owner is asked when it is not yours. {% endcomment %}
'''),
        (r'''
<div class="page-action-buttons">
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''
<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''{% endif %}
</div>
{% endblock %}
''',
         r'''{% endif %}
</div>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'passes.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% if every %}{% url 'travel:passes' %}{% else %}?show=all{% endif %}" class="btn action-secondary">{% if every %}Only the ones to come{% else %}Earlier passes{% endif %}</a>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
''',
         r'''<div class="page-action-buttons">
    <a href="{% if every %}{% url 'travel:passes' %}{% else %}?show=all{% endif %}" class="btn action-secondary">{% if every %}Only the ones to come{% else %}Earlier passes{% endif %}</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
'''),
        (r'''      <div class="tv-row" style="width: 100%"><div><div class="tv-sub small">Passenger</div><b>{{ p.name|default:"–" }}</b></div><a href="{% url 'travel:booking' p.booking.pk %}" class="small">The booking</a></div>
      {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}" style="max-width: 240px; margin: 6px auto 0">{{ p.svg|safe }}</div>{% else %}<p class="tv-sub small" style="margin: 0">This barcode cannot be drawn here &mdash; open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      {% if p.wallet_link %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
    </div>
  </article>
''',
         r'''      <div class="tv-row" style="width: 100%"><div><div class="tv-sub small">Passenger</div><b>{{ p.name|default:"–" }}</b></div><a href="{% url 'travel:booking' p.booking.pk %}" class="small">The booking</a></div>
      {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}" style="max-width: 240px; margin: 6px auto 0">{{ p.svg|safe }}</div>{% else %}<p class="tv-sub small" style="margin: 0">This barcode cannot be drawn here &mdash; open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
    </div>
  </article>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'place_form.html'), [
        (r'''<div class="page-action-buttons">
    {% if p %}<a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-map"></i> Map</a>{% if p.website %}<a href="{{ p.website }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-globe"></i> Website</a>{% endif %}{% endif %}
    <a href="{% if p and not p.day %}{% url 'travel:trip_wishlist' trip.pk %}{% else %}{% url 'travel:trip_itinerary' trip.pk %}{% endif %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
''',
         r'''<div class="page-action-buttons">
    {% if p %}<a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-map"></i> Map</a>{% if p.website %}<a href="{{ p.website }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-globe"></i> Website</a>{% endif %}{% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% if p and not p.day %}{% url 'travel:trip_wishlist' trip.pk %}{% else %}{% url 'travel:trip_itinerary' trip.pk %}{% endif %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'share.html'), [
        (r'''{% extends 'base.html' %}
{% block title %}Share - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. Who else is on this trip - like a meal plan. #}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}Share - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. Who else is on this trip - like a meal plan. #}
'''),
        (r'''<h4 class="page-subtitle-h4">SHARE {{ trip.name|upper }}</h4>
<div class="page-action-buttons">
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
''',
         r'''<h4 class="page-subtitle-h4">SHARE {{ trip.name|upper }}</h4>
<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
'''),
        (r'''</form>
</div>
{% endblock %}
''',
         r'''</form>
</div>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    <details class="tv-menu" data-pdf-menu><summary class="btn action-secondary" title="Make the trip into a PDF"><i class="fas fa-file-pdf"></i> PDF <i class="fas fa-caret-down" aria-hidden="true"></i></summary>
        <div class="tv-menu-pop">
            <button type="button" data-trip-pdf="summary" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><b>Summary</b><small>Day by day, the places, the costs</small></button>
            <button type="button" data-trip-pdf="detailed" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><b>Detailed</b><small>Every day with addresses, phones and times, then every booking in full</small></button>
        </div>
    </details>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''    <details class="tv-menu" data-pdf-menu><summary class="btn action-secondary" title="Make the trip into a PDF"><i class="fas fa-file-pdf"></i> PDF <i class="fas fa-caret-down" aria-hidden="true"></i></summary>
        <div class="tv-menu-pop">
            <button type="button" data-trip-pdf="summary" onclick="this.closest('details').open = false; openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><b>Summary</b><small>Day by day, the places, the costs</small></button>
            <button type="button" data-trip-pdf="detailed" onclick="this.closest('details').open = false; openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><b>Detailed</b><small>Every day with addresses, phones and times, then every booking in full</small></button>
        </div>
    </details>
    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''<div class="tv-wrap">
{% include 'travel/_requests.html' %}
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</p>

''',
         r'''<div class="tv-wrap">
{% include 'travel/_requests.html' %}
{% if settle %}{% comment %} TR-7, 16 Nov 2026 (Demetri: "Once all the trip days have passed, would it make sense for the system to set all Reservations as paid (maybe to ask first)?"). Asked - never done by itself. {% endcomment %}
<section class="form-card tv-settle" data-settle style="margin-bottom: 14px">
    <h3 class="form-section-title" style="margin: 0 0 6px">This trip ended on {{ end|date:"D j M" }} &mdash; is everything paid?</h3>
    <p style="margin: 0 0 6px">{{ settle|length }} booking{{ settle|pluralize }} still say{{ settle|length|pluralize:"s," }} <b>To pay</b>. Marking them paid makes the trip&rsquo;s costs final, so it compares fairly with your other trips.</p>
    <form method="post" action="{% url 'travel:trip_settle' trip.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}">
        {% for b in settle %}<div class="tv-settle-row">
            <input type="checkbox" name="b" value="{{ b.pk }}" checked aria-label="{{ b.title }} paid" style="width: 18px; height: 18px">
            <span><b>{{ b.title }}</b><span class="tv-sub" style="display: block">{{ b.kind_label }}{% if b.start_date %} &middot; {{ b.start_date|date:"j M" }}{% endif %} &middot; {{ b.status_label }}</span></span>
            <b style="text-align: right">{{ b.eur_label|default:"rate pending" }}</b>
            <label class="small" style="margin: 0">Paid in euros<input name="eur_{{ b.pk }}" value="{{ b.amount_eur|default_if_none:'' }}" inputmode="decimal" class="form-control form-control-sm" aria-label="{{ b.title }} - amount paid in euros"></label>
        </div>{% endfor %}
        <div class="tv-acts">
            <button type="submit" name="what" value="paid" class="btn action-primary" title="Mark the ticked bookings Paid">Mark ticked ones paid</button>
            <button type="submit" name="what" value="leave" class="btn action-secondary" title="Keep them as they are and do not ask again">Leave as it is</button>
            <button type="submit" name="what" value="later" class="btn btn-link" title="Ask again in seven days">Ask me again in a week</button>
        </div>
    </form>
</section>
{% endif %}
<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</p>

'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_form.html'), [
        (r'''{% extends 'base.html' %}
{% block title %}Edit trip - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. A trip's name, dates and countries. #}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}Edit trip - Travel{% endblock %}
{# TRAVEL - TR-1, 15 Nov 2026. A trip's name, dates and countries. #}
'''),
        (r'''<h4 class="page-subtitle-h4">EDIT TRIP</h4>
<div class="page-action-buttons">
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
''',
         r'''<h4 class="page-subtitle-h4">EDIT TRIP</h4>
<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trip' trip.pk %}" class="btn action-back" aria-label="Back to the trip"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
'''),
        (r'''{% if is_owner %}<form id="del-trip" method="post" action="{% url 'travel:trip_delete' trip.pk %}" onsubmit="return confirm('Delete this trip, every booking in it and their documents? This cannot be undone.');">{% csrf_token %}</form>{% endif %}
</div>
{% endblock %}
''',
         r'''{% if is_owner %}<form id="del-trip" method="post" action="{% url 'travel:trip_delete' trip.pk %}" onsubmit="return confirm('Delete this trip, every booking in it and their documents? This cannot be undone.');">{% csrf_token %}</form>{% endif %}
</div>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''    <a href="{% url 'travel:passes' %}" class="btn action-secondary" data-passes-button><i class="fas fa-qrcode"></i> Boarding passes</a>
    <a href="?show={{ show }}&amp;phone=1" class="btn action-secondary" data-phone-button><i class="fas fa-mobile-alt"></i> Phone app</a>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''    <a href="{% url 'travel:passes' %}" class="btn action-secondary" data-passes-button><i class="fas fa-qrcode"></i> Boarding passes</a>
    <a href="?show={{ show }}&amp;phone=1" class="btn action-secondary" data-phone-button><i class="fas fa-mobile-alt"></i> Phone app</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
        (r'''<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included. Forward booking emails to <b>{{ address }}</b> and they wait for you under <a href="{% url 'travel:check' %}">To check</a>.</p>

{% comment %} TR-4 (Demetri, 15 Nov): used once per person, so it sits behind the Phone app button, not on the page all the time. {% endcomment %}
{% if phone_qr %}
<section class="form-card tv-phone" data-phone-app style="margin: 4px 0 18px">
    <div class="tv-passcode" style="margin: 0">{{ phone_qr|safe }}</div>
    <div><h3 class="form-section-title" style="margin: 0 0 4px">Travel on your phone</h3><p class="small" style="margin: 0">Point your phone&rsquo;s camera here, or open <b>alivente.online/travel/m/</b>, then <em>Add to Home screen</em>. Today, your boarding passes (even with no signal) and To check &mdash; and on Android, <em>Share &rarr; Travel</em> sends a ticket or an email straight in.</p><div class="small" style="margin-top: 8px"><a href="?show={{ show }}">Close</a></div></div>
</section>
{% endif %}
{% comment %} TR-4 (Demetri, 15 Nov): the New trip form shows only when + New trip is pressed - or when there is no trip yet. {% endcomment %}
{% if new_open %}
''',
         r'''<p class="text-muted small">Your trips, and the ones shared with you. Everyone on a shared trip sees everything in it, costs included. Forward booking emails to <b>{{ address }}</b> and they wait for you under <a href="{% url 'travel:check' %}">To check</a>.</p>

{% comment %} TR-4 (Demetri, 15 Nov): used once per person, so it sits behind the Phone app button. TR-7 (16 Nov: "When I press Phone App.... why does it list all of my trips below. Also, the Text next to the QR Code is not clear ... It needs to explain that after I scan the QR code, I need to press the three dots and then I need to scroll down and select Install and Create Shortcut, and finally choose Install"): on its own, step by step. {% endcomment %}
{% if phone_qr %}
<section class="form-card tv-phone tv-phone-wide" data-phone-app style="margin: 4px 0 18px; max-width: 860px; grid-template-columns: 200px minmax(0, 1fr); align-items: start">
    <div class="tv-passcode" style="margin: 0; max-width: 200px">{{ phone_qr|safe }}</div>
    <div>
        <h3 class="form-section-title" style="margin: 0 0 8px">Put Travel on your phone</h3>
        <ol class="tv-steps" data-phone-steps>
            <li><b>Scan the code</b> with your phone&rsquo;s camera and tap the link that appears. (Or type <b>alivente.online/travel/m/</b> into Chrome on the phone.)</li>
            <li><b>Sign in</b> if it asks &mdash; with your usual Alivente email and password.</li>
            <li>In Chrome, tap the <b>three dots &#8942;</b> at the top right.</li>
            <li><b>Scroll down</b> and tap <b>Add to Home screen</b> (on some phones it says <b>Install app</b>).</li>
            <li>Choose <b>Install</b> (not <i>Create shortcut</i>), then <b>Install</b> again to confirm.</li>
            <li>Open <b>Travel</b> from your home screen. It stays signed in for 30 days.</li>
        </ol>
        <p class="tv-sub small" style="margin: 8px 0 0"><b>iPhone:</b> open the link in Safari, tap <b>Share</b> (the square with the arrow), then <b>Add to Home Screen</b>.</p>
        <div style="margin-top: 12px"><a href="{% url 'travel:trips' %}" class="btn action-secondary btn-sm">Done &mdash; back to my trips</a></div>
    </div>
</section>
{% else %}
{% comment %} TR-4 (Demetri, 15 Nov): the New trip form shows only when + New trip is pressed - or when there is no trip yet. {% endcomment %}
{% if new_open %}
'''),
        (r'''{% if count %}
<nav class="tv-chips" aria-label="Show">
    <a class="tv-chip{% if show == 'upcoming' %} is-on{% endif %}" href="?show=upcoming">Upcoming</a>
    <a class="tv-chip{% if show == 'past' %} is-on{% endif %}" href="?show=past">Past</a>
    {% for y in years %}<a class="tv-chip{% if show == y|stringformat:'d' %} is-on{% endif %}" href="?show={{ y }}">{{ y }}</a>{% endfor %}
    {% for c in countries %}<a class="tv-chip{% if show == 'c:'|add:c %} is-on{% endif %}" href="?show=c:{{ c|urlencode }}">{{ c }}</a>{% endfor %}
    <a class="tv-chip{% if show == 'all' %} is-on{% endif %}" href="?show=all">All</a>
</nav>
{% endif %}

<div class="tv-grid" data-trips>
{% for t in trips %}
    <a class="tv-card form-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p>{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
        <div class="tv-row small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span class="tv-people">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
        {% if t.money.any %}
        <div class="tv-bar" aria-hidden="true"><span style="width: {{ t.money.pct }}%"></span></div>
        <div class="tv-row small"><span><b>{{ t.money.total }}</b> total</span><span class="tv-paid">{{ t.money.paid }} paid</span><span class="tv-due">{{ t.money.due }} to pay</span></div>
        {% endif %}
    </a>
{% empty %}
    <p class="text-muted">{% if count %}No trips here.{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>


''',
         r'''{% if count %}
<nav class="tv-chips" aria-label="Show">
    <a class="tv-chip{% if show == 'upcoming' and not auto_past %} is-on{% endif %}" href="?show=upcoming">Upcoming <span class="tv-sub">{{ n_upcoming }}</span></a>
    <a class="tv-chip{% if show == 'past' or auto_past %} is-on{% endif %}" href="?show=past">Past <span class="tv-sub">{{ n_past }}</span></a>
    {% for y in years %}<a class="tv-chip{% if show == y|stringformat:'d' %} is-on{% endif %}" href="?show={{ y }}">{{ y }}</a>{% endfor %}
    {% for c in countries %}<a class="tv-chip{% if show == 'c:'|add:c %} is-on{% endif %}" href="?show=c:{{ c|urlencode }}">{{ c }}</a>{% endfor %}
    <a class="tv-chip{% if show == 'all' %} is-on{% endif %}" href="?show=all">All</a>
</nav>
{% endif %}

{% comment %} TR-7, 16 Nov 2026 (Demetri: "If there are not upcoming, then it must show the past ones in descending date order (highlighting that they are Past)"; "I must be able to multi select trips for comparison"). {% endcomment %}
{% if auto_past %}<p class="tv-note" data-auto-past>Nothing coming up &mdash; here are your <b>past trips</b>, newest first.</p>{% endif %}
{% if count > 1 %}<form method="get" action="{% url 'travel:compare' %}" id="tv-compare" class="tv-row" style="margin: 0 0 12px; align-items: center" data-compare-form><span class="tv-sub">Tick two or more trips to compare their costs.</span><button type="submit" class="btn action-secondary btn-sm" title="Compare the ticked trips side by side"><i class="fas fa-balance-scale"></i> Compare ticked trips</button></form>{% endif %}
<div class="tv-grid" data-trips>
{% for t in trips %}
    <div class="tv-pickcard">
    <a class="tv-card form-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p><span>{% if t.past %}<span class="tv-tag tv-pasttag" data-past>Past</span> {% endif %}{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</span></div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
        <div class="tv-row small"><span>{{ t.n }} booking{{ t.n|pluralize }}</span><span class="tv-people">{% for p in t.people %}<span class="tv-av" title="{{ p.get_full_name|default:p.username }}">{{ p.first_name|default:p.username|slice:":1"|upper }}{{ p.last_name|slice:":1"|upper }}</span>{% endfor %}</span></div>
        {% if t.money.any %}
        <div class="tv-bar" aria-hidden="true"><span style="width: {{ t.money.pct }}%"></span></div>
        <div class="tv-row small"><span><b>{{ t.money.total }}</b> total</span><span class="tv-paid">{{ t.money.paid }} paid</span><span class="tv-due">{{ t.money.due }} to pay</span></div>
        {% endif %}
        {% if t.owing %}<div class="small tv-due" data-owing><b>{{ t.owing }} still To pay</b> &middot; settle up on the trip</div>{% endif %}
    </a>
    {% if count > 1 %}<label class="tv-pick small"><input type="checkbox" name="t" value="{{ t.pk }}" form="tv-compare"> Compare</label>{% endif %}
    </div>
{% empty %}
    <p class="text-muted">{% if count %}No trips here.{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>
{% endif %}


'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import phone, report, views, views_inbox, views_places

app_name = 'travel'
''',
         r'''from django.urls import path

from . import compare, phone, report, views, views_inbox, views_places

app_name = 'travel'
'''),
        (r'''    path('passes/', phone.passes, name='passes'),
    path('<int:trip_id>/pdf/', report.trip_pdf, name='trip_pdf'),
    path('m/trip/<int:trip_id>/pdf/', report.trip_pdf, name='m_trip_pdf'),
    path('<int:trip_id>/wish-list/', views.trip, name='trip_wishlist'),
''',
         r'''    path('passes/', phone.passes, name='passes'),
    path('<int:trip_id>/pdf/', report.trip_pdf, name='trip_pdf'),
    # TR-7 - settling up after a trip; comparing trips.
    path('<int:trip_id>/settle/', compare.trip_settle, name='trip_settle'),
    path('compare/', compare.compare, name='compare'),
    path('m/compare/', compare.compare, name='m_compare'),
    path('m/trip/<int:trip_id>/pdf/', report.trip_pdf, name='m_trip_pdf'),
    path('<int:trip_id>/wish-list/', views.trip, name='trip_wishlist'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        t.past = bool(end and end < today)
        rows.append(t)
    if show == 'upcoming':
        sel = [t for t in rows if not t.past]
    elif show == 'past':
        sel = [t for t in rows if t.past]
''',
         r'''        t.past = bool(end and end < today)
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
'''),
        (r'''        show, sel = 'all', rows
    far = dt.date(9999, 1, 1)
    sel.sort(key=lambda t: (t.start or far), reverse=(show == 'past'))
    return render(request, 'travel/trips.html', {
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'countries': sorted(countries), 'count': len(rows),
        'checks': inbox.open_count(request.user),
''',
         r'''        show, sel = 'all', rows
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
'''),
        (r'''        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end)})


''',
         r'''        'itinerary': itinerary(t, bs, pl) if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs)})


def settle_rows(t, bs):
    from .compare import unsettled
    return unsettled(t, bs)


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''  <summary class="tv-btn sec wide" style="list-style: none">PDF &#9662;</summary>
  <div class="tv-btns" style="padding: 10px">
    <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=summary" data-share-name="trip_{{ trip.name|slugify }}_summary.pdf" data-share-title="{{ trip.name }}">Summary</button>
    <button type="button" class="tv-btn sec" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=detailed" data-share-name="trip_{{ trip.name|slugify }}_detailed.pdf" data-share-title="{{ trip.name }}">Detailed</button>
  </div>
</details>
''',
         r'''  <summary class="tv-btn sec wide" style="list-style: none">PDF &#9662;</summary>
  <div class="tv-btns" style="padding: 10px">
    <button type="button" class="tv-btn sec" onclick="this.closest('details').open = false" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=summary" data-share-name="trip_{{ trip.name|slugify }}_summary.pdf" data-share-title="{{ trip.name }}">Summary</button>
    <button type="button" class="tv-btn sec" onclick="this.closest('details').open = false" data-share-pdf="{% url 'travel:m_trip_pdf' trip.pk %}?kind=detailed" data-share-name="trip_{{ trip.name|slugify }}_detailed.pdf" data-share-title="{{ trip.name }}">Detailed</button>
  </div>
</details>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'passes.html'), [
        (r'''      {% if p.svg %}<div data-barcode="{{ p.format }}" style="width: 100%; display: flex; justify-content: center">{{ p.svg|safe }}</div>{% else %}<p class="tv-muted" style="margin: 0">This barcode cannot be drawn here - open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      <div class="tv-muted tv-small" style="text-align: center">Show at security and the gate · turn the screen brightness up</div>
      {% if p.wallet_link %}<a href="{{ p.wallet_link }}" class="tv-btn wide" style="background: #1D2B31; border-color: #1D2B31" target="_blank" rel="noopener">Add to Google Wallet</a>{% endif %}
      <a href="{% url 'travel:m_booking' p.booking.pk %}" class="tv-small">The booking</a>
    </div>
''',
         r'''      {% if p.svg %}<div data-barcode="{{ p.format }}" style="width: 100%; display: flex; justify-content: center">{{ p.svg|safe }}</div>{% else %}<p class="tv-muted" style="margin: 0">This barcode cannot be drawn here - open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      <div class="tv-muted tv-small" style="text-align: center">Show at security and the gate · turn the screen brightness up</div>
      {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" class="tv-btn wide" style="background: #1D2B31; border-color: #1D2B31" target="_blank" rel="noopener">Add to Google Wallet</a>{% endif %}
      <a href="{% url 'travel:m_booking' p.booking.pk %}" class="tv-small">The booking</a>
    </div>
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
    raise SystemExit('TR-7 REFUSED: %s' % msg)


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
    if "'test_travel_seven.py'" in read(pq):
        print('TR-7 already applied.')
        return 0
    if "'test_travel_six.py'" not in read(pq):
        refuse('TR-6 (apply_travel_six.py) is not applied - this round registers after it.')
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
        print('TR-7 --check: %d file(s) would change, none written; %d '
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
    print('TR-7 applied - settling up, comparing trips. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
