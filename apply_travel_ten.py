# -*- coding: utf-8 -*-
"""apply_travel_ten.py - round TR-10, 16 Nov 2026.

RELEASE 90 - TRAVEL: DRAG A DAY INTO ORDER, ON THE PHONE TOO.

    Demetri, 16 Nov: "I am not happy how the sorting happens on the
    mobile. It is cumbersome and not user intuitive."

    - A grip on every row of a day (right on the phone, left on the
      computer). Drag it: the row lifts and follows the finger, the others
      slide aside, the page scrolls at the top and bottom edge. Only the
      grip drags - the rest of the row still scrolls and opens.
    - Saved on release, no reload; "Order saved - Undo" for a few seconds.
      "Your order - Back to automatic" shows and hides by itself.
    - "Change order" and the up / down buttons are gone. One shared script:
      travel/templates/travel/_reorder.html.

New files ship beside this patcher. Stands on TR-9 (apply_travel_nine.py).
Idempotent. Edits backed up to .bak_travel10. No migration.
"""
import os
import sys

SUFFIX = '.bak_travel10'
MARK = 'TR-10, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/templates/travel/_reorder.html',
    'test_travel_ten.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_eight.py',
    # TR-9, 16 Nov 2026 - Release 89: the order of a day on the itinerary.
    'test_travel_nine.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_eight.py',
    # TR-9, 16 Nov 2026 - Release 89: the order of a day on the itinerary.
    'test_travel_nine.py',
    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    'test_travel_ten.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # (smart order; dragged, or up / down on the phone).
    '.bak_travel9',
]

''',
         r'''    # (smart order; dragged, or up / down on the phone).
    '.bak_travel9',
    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    '.bak_travel10',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> on the left; on the phone, press <strong>Change order</strong> beside the day and use the &uarr; / &darr; buttons, then <strong>Done</strong>. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
  </article>

''',
         r'''    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
  </article>

'''),
    ]),
    (os.path.join('test_travel_nine.py'), [
        (r'''   'routes: the day\'s order, computer and phone')
tp = read(J(TT, 'trip.html'))
ok('data-grip' in tp and 'data-order-form' in tp and
   "'X-Requested-With': 'fetch'" in tp and 'data-order-reset' in tp,
   'COMPUTER: a grip to drag by; the order saved on drop; Back to automatic')
mt = read(J(TT, 'm', 'trip.html'))
ok('data-order-change' in mt and 'data-order-up' in mt and
   'data-order-down' in mt and 'data-order-done' in mt,
   'PHONE: Change order -> up / down buttons -> Done')
ok('data-arrive' in read(J(TT, '_booking_row.html')) and
   'data-arrive' in read(J(TT, 'm', '_row.html')) and
''',
         r'''   'routes: the day\'s order, computer and phone')
tp = read(J(TT, 'trip.html'))
# TR-10 (16 Nov) moved the dragging into travel/_reorder.html, shared with
# the phone; the up / down buttons are gone (test_travel_ten.py).
ok('data-grip' in tp and 'data-order-reset' in tp and
   ('data-order-form' in tp or "include 'travel/_reorder.html'" in tp) and
   "'X-Requested-With': 'fetch'" in (tp + read(J(TT, '_reorder.html'))
                                      if os.path.isfile(J(TT, '_reorder.html'))
                                      else tp),
   'COMPUTER: a grip to drag by; the order saved on drop; Back to automatic')
mt = read(J(TT, 'm', 'trip.html'))
ok(('data-order-change' in mt and 'data-order-up' in mt and
    'data-order-down' in mt and 'data-order-done' in mt) or
   ('data-grip' in mt and 'data-reorder' in mt),
   'PHONE: a way to put a day in order (TR-10: drag the grip)')
ok('data-arrive' in read(J(TT, '_booking_row.html')) and
   'data-arrive' in read(J(TT, 'm', '_row.html')) and
'''),
        (r'''ok('<strong>The order of a day.</strong>' in hp and
   'Back to automatic</strong>' in hp and
   '<b>Change order</b>' in mh,
   'HELP: smart order, dragging, Change order, Back to automatic')

''',
         r'''ok('<strong>The order of a day.</strong>' in hp and
   'Back to automatic</strong>' in hp and
   ('<b>Change order</b>' in mh or 'grip' in mh),
   'HELP: smart order, dragging, Change order, Back to automatic')

'''),
        (r'''            ok('After you land, about 00:35 (after midnight)' in h and
               'check-in from 15:00' in h, '  "After you land, about 00:35"')
            ok(h.count('data-grip') == 5 and 'data-custom-order' not in h,
               '  a grip on every row; not "Your order" yet')
            keys = [k.split('"')[0] for k in h.split('data-key="')[1:]]
''',
         r'''            ok('After you land, about 00:35 (after midnight)' in h and
               'check-in from 15:00' in h, '  "After you land, about 00:35"')
            ok(h.count('data-grip') == 5 and ('data-custom-order' not in h or
                'data-order-status="2026-11-09" hidden' in h),
               '  a grip on every row; not "Your order" yet')
            keys = [k.split('"')[0] for k in h.split('data-key="')[1:]]
'''),
        (r'''            h = day9(A.get(url).content.decode())
            ok(h.index('PAREA') < h.index('Kylemore') < h.index('Clybaun')
               and 'data-custom-order' in h and 'data-order-reset' in h,
               '  the itinerary in that order, "Your order · Back to '
               'automatic"')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk
                       ).content.decode()
            m9 = hm.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(m9.index('PAREA') < m9.index('Clybaun') and
               'data-order-change' in hm and 'data-order-reset' in hm,
               'THE PHONE shows the same order, with Change order')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary&order=2026-11-09'
                       % t.pk).content.decode()
            ok(hm.count('data-order-up') == 5 and 'data-order-done' in hm,
               '  Change order: up / down on each row of the day, Done')
            k_parea = 'b%d-start' % parea.pk
            r = M.post('/travel/m/trip/%d/day-order/' % t.pk,
''',
         r'''            h = day9(A.get(url).content.decode())
            ok(h.index('PAREA') < h.index('Kylemore') < h.index('Clybaun')
               and 'data-custom-order' in h and
               'data-order-status="2026-11-09" hidden' not in h and 'data-order-reset' in h,
               '  the itinerary in that order, "Your order · Back to '
               'automatic"')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk
                       ).content.decode()
            m9 = hm.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(m9.index('PAREA') < m9.index('Clybaun') and
               ('data-order-change' in hm or 'data-grip' in hm) and
               'data-order-reset' in hm,
               'THE PHONE shows the same order, with a way to change it')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary&order=2026-11-09'
                       % t.pk).content.decode()
            m9 = hm.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(m9.count('data-order-up') == 5 or m9.count('data-grip') == 5,
               '  every row of the day can be moved')
            k_parea = 'b%d-start' % parea.pk
            r = M.post('/travel/m/trip/%d/day-order/' % t.pk,
'''),
        (r'''            ok(not DayOrder.objects.filter(trip=t, day=D9).exists() and
               h.index('Clybaun') < h.index('PAREA') and
               'data-custom-order' not in h,
               'BACK TO AUTOMATIC: the order gone, time order again')
            other = User.objects.create_user('tv9b', 'tv9b@example.com', 'x')
''',
         r'''            ok(not DayOrder.objects.filter(trip=t, day=D9).exists() and
               h.index('Clybaun') < h.index('PAREA') and
               ('data-custom-order' not in h or
                'data-order-status="2026-11-09" hidden' in h),
               'BACK TO AUTOMATIC: the order gone, time order again')
            other = User.objects.create_user('tv9b', 'tv9b@example.com', 'x')
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-order-row .tv-btn[disabled] { opacity: .35; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: var(--tv-teal); text-decoration: underline; font: inherit; cursor: pointer; }
''',
         r'''.tv-order-row .tv-btn[disabled] { opacity: .35; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: var(--tv-teal); text-decoration: underline; font: inherit; cursor: pointer; }
/* TR-10, 16 Nov 2026 - a day put in order by dragging the grip on the right of a row (Demetri: "cumbersome and not user intuitive" - the up / down buttons are gone). Only the grip drags; the rest of the row scrolls and opens as before. */
.tv-drag { display: flex; align-items: center; gap: 2px; border-top: 1px solid var(--tv-line); transition: transform .16s ease; position: relative; }
.tv-drag:first-of-type { border-top: 0; }
.tv-drag > .tv-item { flex: 1 1 auto; min-width: 0; border-top: 0; padding: 10px 0; }
.tv-drag:first-of-type > .tv-item { padding-top: 0; }
.tv-grip { flex: none; display: flex; align-items: center; justify-content: center; width: 44px; height: 48px; margin-right: -10px; color: #9AA9AE; touch-action: none; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; cursor: grab; }
.tv-grip svg { fill: currentColor; }
.tv-grip:focus-visible { outline: 2px solid var(--tv-teal); border-radius: 8px; }
[data-reorder].tv-still .tv-drag { transition: none; }
.tv-drag.is-lifted { transition: none; z-index: 5; background: #fff; border-radius: 12px; box-shadow: 0 10px 26px rgba(16,34,40,.25); border-top-color: transparent; }
.tv-drag.is-lifted .tv-grip { color: var(--tv-teal); }
[data-reorder].is-sorting { user-select: none; -webkit-user-select: none; }
.tv-toast { position: fixed; left: 50%; bottom: calc(84px + env(safe-area-inset-bottom)); transform: translate(-50%, 220%); display: flex; gap: 18px; align-items: center; background: #1D2B31; color: #fff; padding: 12px 18px; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,.25); z-index: 50; transition: transform .2s ease; font-size: 15px; white-space: nowrap; }
.tv-toast.on { transform: translate(-50%, 0); }
.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; font-size: 15px; padding: 0; }
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv9-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv10-1'


'''),
        (r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        # TR-9 - the day being put in order (?order=YYYY-MM-DD): up / down.
        'order_day': (request.GET.get('order') or '')[:10],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
''',
         r'''        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': itinerary(t, bs, pl) if sub == 'itinerary' else [],
        'trip_days': [d for d, _ in itinerary(t, [], [])] if sub == 'wish'
        else [],
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-grip { flex: none; display: flex; align-items: center; padding: 0 8px 0 0; color: #9AA9AE; cursor: grab; }
.tv-grip:hover { color: #0F6E77; }
.tv-drag.is-dragging { opacity: .45; }
.tv-drag.tv-drop-above { box-shadow: inset 0 3px 0 #0F6E77; }
.tv-drag.tv-drop-below { box-shadow: inset 0 -3px 0 #0F6E77; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: #0F6E77; text-decoration: underline; cursor: pointer; font: inherit; }
</style>
''',
         r'''.tv-grip { flex: none; display: flex; align-items: center; padding: 0 8px 0 0; color: #9AA9AE; cursor: grab; }
.tv-grip:hover { color: #0F6E77; }
/* TR-10 - the row lifts and follows the pointer; the others slide aside; "Order saved - Undo". */
.tv-grip { touch-action: none; user-select: none; -webkit-user-select: none; }
.tv-grip:focus-visible { outline: 2px solid #0F6E77; outline-offset: 2px; border-radius: 4px; }
[data-reorder] .tv-drag { transition: transform .16s ease; }
[data-reorder].tv-still .tv-drag { transition: none; }
.tv-drag.is-lifted { transition: none; z-index: 5; background: #fff; border-radius: 10px; box-shadow: 0 8px 22px rgba(16,34,40,.22); }
.tv-drag.is-lifted .tv-grip { cursor: grabbing; color: #0F6E77; }
[data-reorder].is-sorting { user-select: none; -webkit-user-select: none; }
.tv-toast { position: fixed; left: 50%; bottom: 24px; transform: translate(-50%, 140%); display: flex; gap: 16px; align-items: center; background: #1D2B31; color: #fff; padding: 10px 16px; border-radius: 10px; box-shadow: 0 6px 18px rgba(0,0,0,.25); z-index: 2000; transition: transform .2s ease; font-size: .95rem; }
.tv-toast.on { transform: translate(-50%, 0); }
.tv-toast button { background: none; border: 0; color: #7FD3DA; font-weight: 700; padding: 0; cursor: pointer; }
.tv-linkbtn { background: none; border: 0; padding: 0; color: #0F6E77; text-decoration: underline; cursor: pointer; font: inherit; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv9-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv10-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv9-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv10-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). <b>Change order</b> beside a day gives &uarr; / &darr; buttons to put it in your own order, kept for everyone on the trip; <b>Back to automatic</b> undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
{% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - on the phone dragging fights the scrolling, so "Change order" turns the day's rows into up / down buttons; the order is kept for everyone on the trip. {% endcomment %}{% with dkey=day|date:'Y-m-d' %}
<div class="tv-row" style="align-items: baseline"><p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>{% if rows|length > 1 %}{% if order_day == dkey %}<a href="?tab=itinerary#d{{ day|date:'Ymd' }}" class="tv-small" data-order-done>Done</a>{% else %}<a href="?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}" class="tv-small" data-order-change>Change order</a>{% endif %}{% endif %}</div>
{% if rows.custom %}<form method="post" action="{% url 'travel:m_day_order' trip.pk %}" class="tv-small tv-muted" style="margin: -4px 0 6px">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}">Your order &middot; <button type="submit" class="tv-linkbtn" data-order-reset>Back to automatic</button></form>{% endif %}
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% if order_day == dkey %}<div class="tv-order-row" data-key="{{ b.order_key }}"><span style="flex: 1 1 auto; min-width: 0"><b>{% if b.is_place %}{{ b.name }}{% else %}{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}{% endif %}</b></span><form method="post" action="{% url 'travel:m_day_order' trip.pk %}">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="move" value="{{ b.order_key }}"><input type="hidden" name="dir" value="up"><input type="hidden" name="next" value="{% url 'travel:m_trip' trip.pk %}?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}"><button class="tv-btn sec" aria-label="Move {% if b.is_place %}{{ b.name }}{% else %}{{ b.title }}{% endif %} up"{% if forloop.first %} disabled{% endif %} data-order-up>&uarr;</button></form><form method="post" action="{% url 'travel:m_day_order' trip.pk %}">{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="move" value="{{ b.order_key }}"><input type="hidden" name="dir" value="down"><input type="hidden" name="next" value="{% url 'travel:m_trip' trip.pk %}?tab=itinerary&amp;order={{ dkey }}#d{{ day|date:'Ymd' }}"><button class="tv-btn sec" aria-label="Move {% if b.is_place %}{{ b.name }}{% else %}{{ b.title }}{% endif %} down"{% if forloop.last %} disabled{% endif %} data-order-down>&darr;</button></form></div>{% else %}{% include 'travel/m/_row.html' %}{% endif %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>{% endwith %}
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
''',
         r'''<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
{% comment %} TR-9 (16 Nov 2026) put a day in your own order; TR-10 - by dragging the grip on the right of a row (Demetri: "I am not happy how the sorting happens on the mobile. It is cumbersome and not user intuitive"). Only the grip drags, so the page still scrolls and a row still opens. {% endcomment %}{% with dkey=day|date:'Y-m-d' %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<form method="post" action="{% url 'travel:m_day_order' trip.pk %}" class="tv-small tv-muted" style="margin: -4px 0 6px" data-order-status="{{ dkey }}"{% if not rows.custom %} hidden{% endif %}>{% csrf_token %}<input type="hidden" name="day" value="{{ dkey }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}">Your order &middot; <button type="submit" class="tv-linkbtn" data-order-reset>Back to automatic</button></form>
<section class="tv-card" data-itinerary-day{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:m_day_order' trip.pk %}" data-day="{{ dkey }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}{% for b in rows %}{% if rows|length > 1 %}<div class="tv-drag" data-key="{{ b.order_key }}">{% include 'travel/m/_row.html' %}<span class="tv-grip" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day" title="Drag to change the order"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg></span></div>{% else %}{% include 'travel/m/_row.html' %}{% endif %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>{% endwith %}
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
'''),
        (r'''</details>
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% endblock %}
''',
         r'''</details>
<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% if sub == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><span class="small">{% if rows.custom %}<span class="tv-sub" data-custom-order>Your order &middot; </span><form method="post" action="{% url 'travel:day_order' trip.pk %}" style="display: inline">{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}#d{{ day|date:'Ymd' }}"><button type="submit" class="tv-linkbtn" title="Put this day back in time order" data-order-reset>Back to automatic</button></form> &nbsp; {% endif %}<a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></span></div>
        {% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - drag a row by its grip; the order is kept for the day, for everyone on the trip. {% endcomment %}<form method="post" action="{% url 'travel:day_order' trip.pk %}" data-order-form hidden>{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"></form>
        {% for r in rows %}<div class="tv-drag" data-key="{{ r.order_key }}">{% if rows|length > 1 %}<span class="tv-grip" title="Drag to change the order of the day" data-grip><i class="fas fa-grip-vertical" aria-hidden="true"></i></span>{% endif %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}</div>{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
    {% endfor %}
''',
         r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><span class="small"><span data-order-status="{{ day|date:'Y-m-d' }}"{% if not rows.custom %} hidden{% endif %}><span class="tv-sub" data-custom-order>Your order &middot; </span><form method="post" action="{% url 'travel:day_order' trip.pk %}" style="display: inline">{% csrf_token %}<input type="hidden" name="day" value="{{ day|date:'Y-m-d' }}"><input type="hidden" name="reset" value="1"><input type="hidden" name="next" value="{{ request.get_full_path }}#d{{ day|date:'Ymd' }}"><button type="submit" class="tv-linkbtn" title="Put this day back in time order" data-order-reset>Back to automatic</button></form> &nbsp; </span><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></span></div>
        {% comment %} TR-9, 16 Nov 2026 (Demetri: "should i have the ability to drag and drop items (within a day)") - drag a row by its grip; the order is kept for the day, for everyone on the trip. TR-10 - the rows slide as you drag, it saves without reloading, Undo for a few seconds (travel/_reorder.html). {% endcomment %}<div class="tv-dayrows"{% if rows|length > 1 %} data-reorder data-url="{% url 'travel:day_order' trip.pk %}" data-day="{{ day|date:'Y-m-d' }}" data-custom="{% if rows.custom %}1{% endif %}"{% endif %}>{% if rows|length > 1 %}{% csrf_token %}{% endif %}
        {% for r in rows %}<div class="tv-drag" data-key="{{ r.order_key }}">{% if rows|length > 1 %}<span class="tv-grip" title="Drag to change the order of the day" data-grip role="button" tabindex="0" aria-label="Drag to change the order of the day"><i class="fas fa-grip-vertical" aria-hidden="true"></i></span>{% endif %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}</div>{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}</div>
    </section>
    {% endfor %}
'''),
        (r'''</div>
{% include 'components/pdf_viewer.html' %}
{% if tab == 'itinerary' %}<script>
/* TR-9, 16 Nov 2026 - drag a row of a day by its grip (Demetri: "should i
   have the ability to drag and drop items (within a day)"). Dropping
   saves the day's order and reloads the page, so the PDFs follow it. */
(function () {
  var dragging = null;
  document.querySelectorAll('section.tv-day').forEach(function (day) {
    day.querySelectorAll('.tv-drag').forEach(function (row) {
      var grip = row.querySelector('[data-grip]');
      if (!grip) { return; }
      grip.addEventListener('mousedown', function () { row.setAttribute('draggable', 'true'); });
      row.addEventListener('dragstart', function (e) {
        dragging = row; row.classList.add('is-dragging');
        e.dataTransfer.effectAllowed = 'move';
        try { e.dataTransfer.setData('text/plain', row.getAttribute('data-key')); } catch (x) {}
      });
      row.addEventListener('dragend', function () {
        row.classList.remove('is-dragging'); row.removeAttribute('draggable');
        day.querySelectorAll('.tv-drop-above, .tv-drop-below').forEach(function (r) { r.classList.remove('tv-drop-above', 'tv-drop-below'); });
      });
      row.addEventListener('dragover', function (e) {
        if (!dragging || dragging === row || dragging.parentNode !== row.parentNode) { return; }
        e.preventDefault();
        var box = row.getBoundingClientRect(), below = e.clientY > box.top + box.height / 2;
        row.classList.toggle('tv-drop-below', below); row.classList.toggle('tv-drop-above', !below);
      });
      row.addEventListener('dragleave', function () { row.classList.remove('tv-drop-above', 'tv-drop-below'); });
      row.addEventListener('drop', function (e) {
        if (!dragging || dragging === row || dragging.parentNode !== row.parentNode) { return; }
        e.preventDefault();
        var below = row.classList.contains('tv-drop-below');
        row.classList.remove('tv-drop-above', 'tv-drop-below');
        row.parentNode.insertBefore(dragging, below ? row.nextSibling : row);
        var keys = Array.prototype.map.call(day.querySelectorAll('.tv-drag'), function (r) { return r.getAttribute('data-key'); });
        var form = day.querySelector('[data-order-form]'), data = new FormData(form);
        data.append('keys', keys.join(','));
        fetch(form.action, {method: 'POST', body: data, credentials: 'same-origin', headers: {'X-Requested-With': 'fetch'}})
          .then(function (r) { if (!r.ok) { throw new Error(r.status); } window.location.hash = day.id; window.location.reload(); })
          .catch(function () { alert('The new order could not be saved - please try again.'); window.location.reload(); });
      });
    });
  });
})();
</script>{% endif %}
{% render_help_modal "travel" %}
{% endblock %}
''',
         r'''</div>
{% include 'components/pdf_viewer.html' %}
{% if tab == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'views_places.py'), [
        (r'''                                       'updated_by': request.user})
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({'ok': True, 'keys': keys or []})
    if request.resolver_match.url_name.startswith('m_'):
        return _next(request, '/travel/m/trip/%d/?tab=itinerary' % t.pk)
''',
         r'''                                       'updated_by': request.user})
    if request.headers.get('x-requested-with') == 'fetch':
        # TR-10 - whether the day now differs from the automatic order, so
        # the page shows or hides "Your order" without reloading.
        rows = day_rows(list(t.bookings.prefetch_related('travellers')),
                        list(t.places.all()), day, saved_for(t))
        return JsonResponse({'ok': True, 'keys': keys or [],
                             'custom': bool(rows.custom)})
    if request.resolver_match.url_name.startswith('m_'):
        return _next(request, '/travel/m/trip/%d/?tab=itinerary' % t.pk)
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
    raise SystemExit('TR-10 REFUSED: %s' % msg)


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
    if "'test_travel_ten.py'" in read(pq):
        print('TR-10 already applied.')
        return 0
    if "'test_travel_nine.py'" not in read(pq):
        refuse('TR-9 (apply_travel_nine.py, Release 89) is not applied - this round registers after it.')
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
        print('TR-10 --check: %d file(s) would change, none written; %d '
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
    print('TR-10 applied - drag a day into order, on the phone too. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
