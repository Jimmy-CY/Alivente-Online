# -*- coding: utf-8 -*-
"""apply_travel_fourteen.py - round TR-14, 17 Nov 2026.

RELEASE 95 - TRAVEL: THE TRIPS ON A CALENDAR; SHOW ME MORE KEEPS THE
TICKS, MARKS THE NEW.

    Demetri, 17 Nov: "If I tick a few suggested things to do and then
    select 'Show me more for Athens', the ones I ticked must remain
    ticked, even though new ones are added. Also, it is not clear which
    ones are new? Maybe we should always mark the new ones added with a
    new label each time?" And: "if Show More has been pressed twice, only
    the ones that are new from the second press must show New".

    - Show me more comes back with what was ticked still ticked, at the
      first new one.
    - What the latest Show me more brought is marked New (a label on the
      card, a line at the top); the next press moves New on.
    - Help says so.

    And Plan my days: "How can both Monday and Wednesday be the fullest
    day?? Maybe it should say that Wednesday is the fullest day. and maybe
    that Monday is a very full day?" - one fullest day, the one with the
    most hours; any other long day "also very full".

    And: "This page needs to keep refreshing, so that I know when the
    'Looking it up' is complete" - while a place on the trip page is being
    looked up, it asks again every 5 seconds (never while you choose a
    day, type, drag or have a menu open); the line after adding says
    "all looked up" when it is done.

    And: "Would it make sense to have a monthly calendar view with the
    trips being displayed on the calendar. It should default to today on
    opening and then the user should the ability to scroll month and
    year? The calendar should just be another view that the user can
    activate." Decided: bars and a plane icon; a bar opens the itinerary;
    a month at a time.

    - List | Calendar on Travel and on the phone's Trips, remembered.
    - travel/calendar_view.py and _calendar.html: this month first,
      today marked; arrows, a month and a year box, Today; swipe on the
      phone. Each trip a bar (stacked when they overlap, paler when
      past), a plane on each day it flies; a bar opens the itinerary.

    And the gate, 17 Nov (R94's push): test_travel_twelve.py opened a
    trip with a hotel, and the hotel's missing details were looked up on
    the web for real - 31.7s with the Anthropic key, and the connection
    guard broke the test. The suites now never make that call - and
    (Demetri: "Please stub those out") no Travel suite looks anything up
    on the web for real: the hotel details and the place look-up are
    stubbed in each one that did not already.

New files ship beside this patcher. Stands on TR-13
(apply_travel_thirteen.py). Idempotent. Edits backed up to .bak_travel14.
No migration.
"""
import os
import sys

SUFFIX = '.bak_travel14'
MARK = 'TR-14, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_fourteen.py',
    'travel/calendar_view.py',
    'travel/templates/travel/_calendar.html',
    'travel/templates/travel/_lookup_refresh.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_twelve.py',
    # TR-13, 17 Nov 2026 - Release 94: trips listed latest first.
    'test_travel_thirteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_twelve.py',
    # TR-13, 17 Nov 2026 - Release 94: trips listed latest first.
    'test_travel_thirteen.py',
    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks and
    # marks the new ones.
    'test_travel_fourteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-13, 17 Nov 2026 - Release 94: trips latest first.
    '.bak_travel13',
]

''',
         r'''    # TR-13, 17 Nov 2026 - Release 94: trips latest first.
    '.bak_travel13',
    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks.
    '.bak_travel14',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
''',
         r'''    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
'''),
        (r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

''',
         r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

'''),
    ]),
    (os.path.join('test_travel_eight.py'), [
        (r'''

if have_db:
    from django.conf import settings as _dj
''',
         r'''

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    from django.conf import settings as _dj
'''),
    ]),
    (os.path.join('test_travel_eleven.py'), [
        (r'''         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
''',
         r'''         'Chrome/131.0 Mobile Safari/537.36')

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    from django.conf import settings as _dj
'''),
    ]),
    (os.path.join('test_travel_nine.py'), [
        (r'''         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
''',
         r'''         'Chrome/131.0 Mobile Safari/537.36')

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    from django.conf import settings as _dj
'''),
    ]),
    (os.path.join('test_travel_one.py'), [
        (r'''except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
''',
         r'''except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
'''),
    ]),
    (os.path.join('test_travel_ten.py'), [
        (r'''D9, D10 = dt.date(2026, 11, 9), dt.date(2026, 11, 10)

if have_db:
    from django.conf import settings as _dj
''',
         r'''D9, D10 = dt.date(2026, 11, 9), dt.date(2026, 11, 10)

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    from django.conf import settings as _dj
'''),
    ]),
    (os.path.join('test_travel_thirteen.py'), [
        (r'''         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
''',
         r'''         'Chrome/131.0 Mobile Safari/537.36')

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    from django.conf import settings as _dj
'''),
    ]),
    (os.path.join('test_travel_three.py'), [
        (r'''         'Chrome/131.0 Mobile Safari/537.36')
DESK = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0'

if have_db:
''',
         r'''         'Chrome/131.0 Mobile Safari/537.36')
DESK = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0'

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
'''),
    ]),
    (os.path.join('test_travel_twelve.py'), [
        (r'''    PP.SYNC = True
    ID.SYNC = True

    class Rollback(Exception):
''',
         r'''    PP.SYNC = True
    ID.SYNC = True
    # TR-14 (17 Nov): a hotel on the trip has its missing details looked
    # up on the web when the trip opens - a real, slow, paid call on a
    # machine with the Anthropic key (31.7s in the gate's pool, and the
    # connection guard closed the test's transaction). Never from a test.
    def _no_details(b, client=None):
        raise PP.LookupError_('not in tests')
    PP.call_details = _no_details

    class Rollback(Exception):
'''),
    ]),
    (os.path.join('test_travel_two.py'), [
        (r'''    return d


if have_db:
''',
         r'''    return d


# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
''',
         r'''.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
/* TR-14, 17 Nov 2026 - the trips on a calendar; List | Calendar. */
.tv-view { display: inline-flex; border: 1px solid #C9D3D6; border-radius: 999px; overflow: hidden; background: #FFFFFF; }
.tv-view a { min-height: 36px; padding: 0 14px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: .9rem; color: #1D2B31; text-decoration: none; }
.tv-view a.on { background: #0F7480; color: #FFFFFF; }
.tv-cal { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 12px; padding: 12px; }
.tv-cal-head { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 10px; }
.tv-cal-title { font-size: 1.35rem; font-weight: 700; margin: 0; min-width: 9.5em; text-align: center; }
.tv-cal-arrow { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; border: 1px solid #C9D3D6; font-size: 1.5rem; line-height: 1; color: #0F7480; text-decoration: none; background: #FFFFFF; }
.tv-cal-pick { display: inline-flex; gap: 6px; align-items: center; margin: 0 0 0 auto; }
.tv-cal-pick select { min-height: 38px; border: 1px solid #C9D3D6; border-radius: 8px; padding: 0 8px; font: inherit; background: #FFFFFF; }
.tv-cal-go { min-height: 38px; border: 1px solid #0F7480; color: #0F7480; background: #FFFFFF; border-radius: 8px; padding: 0 10px; font: inherit; font-weight: 600; }
.tv-cal-today { min-height: 38px; display: inline-flex; align-items: center; padding: 0 12px; border-radius: 8px; background: #0F7480; color: #FFFFFF; font-weight: 600; text-decoration: none; }
.tv-cal-sr { position: absolute; left: -9999px; }
.tv-cal-dow { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); font-size: .72rem; font-weight: 700; color: #5B6B72; text-transform: uppercase; letter-spacing: .04em; text-align: center; padding-bottom: 4px; }
.tv-cal-week { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); row-gap: 3px; min-height: 92px; border-top: 1px solid #E1E6E8; align-content: start; }
.tv-cal-day { border-left: 1px solid #EEF1F2; padding: 4px 6px 6px; display: flex; flex-wrap: wrap; align-items: center; gap: 3px; align-content: flex-start; min-height: 88px; }
.tv-cal-day:first-child { border-left: 0; }
.tv-cal-day .n { font-size: .85rem; font-weight: 600; color: #1D2B31; width: 1.9em; height: 1.9em; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; }
.tv-cal-day.out .n { color: #8A9BA2; font-weight: 400; }
.tv-cal-day.out { background: #FAFBFB; }
.tv-cal-day.today .n { background: #0F7480; color: #FFFFFF; }
.tv-cal-plane { flex: none; }
.tv-cal-bar { position: relative; z-index: 1; margin: 0 3px; border-radius: 6px; color: #FFFFFF; font-size: .8rem; font-weight: 700; line-height: 26px; padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-decoration: none; align-self: stretch; }
.tv-cal-bar:hover, .tv-cal-bar:focus { color: #FFFFFF; text-decoration: none; filter: brightness(1.1); }
.tv-cal-bar.ml { margin-left: 0; border-top-left-radius: 0; border-bottom-left-radius: 0; }
.tv-cal-bar.mr { margin-right: 0; border-top-right-radius: 0; border-bottom-right-radius: 0; }
.tv-cal-bar.past { opacity: .5; }
.tv-cal-none { margin: 10px 2px 0; font-size: .88rem; color: #4A5A61; }
.tv-cal-list { display: flex; flex-direction: column; margin-top: 10px; border-top: 1px solid #E1E6E8; }
.tv-cal-item { display: flex; gap: 10px; align-items: center; padding: 10px 2px; border-bottom: 1px solid #EEF1F2; color: #1D2B31; text-decoration: none; min-height: 44px; }
.tv-cal-item i { flex: none; width: 12px; height: 32px; border-radius: 4px; }
.tv-cal-item span { display: flex; flex-direction: column; }
.tv-cal-item small { color: #5B6B72; font-size: 12px; }
.tv-cal-item.past { opacity: .6; }
@media (max-width: 560px) {
  .tv-cal { padding: 10px 6px; }
  .tv-cal-title { font-size: 1.1rem; min-width: 0; flex: 1; }
  .tv-cal-pick { margin: 0; width: 100%; }
  .tv-cal-pick select { flex: 1; }
  .tv-cal-week { min-height: 64px; }
  .tv-cal-day { min-height: 60px; padding: 2px 2px 4px; gap: 1px; }
  .tv-cal-day .n { font-size: 12px; }
  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
'''),
    ]),
    (os.path.join('travel', 'ideas.py'), [
        (r'''    """What Things to do shows: how many suggestions are left to look at,
    one still being worked out, and a line after adding."""
    out = {'ideas_left': trip.ideas.filter(state='').count(),
           'ideas_open': trip.idea_runs.filter(status='working').exists()}
    n = request.GET.get('added') or ''
    if n.isdigit():
''',
         r'''    """What Things to do shows: how many suggestions are left to look at,
    one still being worked out, and a line after adding."""
    from django.utils import timezone
    out = {'ideas_left': trip.ideas.filter(state='').count(),
           'ideas_open': trip.idea_runs.filter(status='working').exists(),
           # TR-14 (Demetri, 17 Nov: "This page needs to keep refreshing, so
           # that I know when the 'Looking it up' is complete"): places
           # still being looked up - the page asks again until there are
           # none. One stuck for ten minutes (a restart) stops it asking.
           'looking': trip.places.filter(
               lookup='waiting', updated_at__gte=timezone.now() -
               dt.timedelta(minutes=10)).count()}
    n = request.GET.get('added') or ''
    if n.isdigit():
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''    for t in sel:
        t.past = bool(t.end and t.end < day)
    return page(request, 'travel/m/trips.html', {
        'trips': sel, 'past': past, 'tab': 'trips', 'auto_past': auto_past,
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)})


''',
         r'''    for t in sel:
        t.past = bool(t.end and t.end < day)
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
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)}), view, asked)


'''),
        (r'''           if sub in ('itinerary', 'wish') else {}),
        # TR-12 - Suggest things to do.
        **(ideas.page_state(t, request) if sub == 'wish' else {})})


''',
         r'''           if sub in ('itinerary', 'wish') else {}),
        # TR-12 - Suggest things to do.
        **(ideas.page_state(t, request)
           if sub in ('wish', 'itinerary') else {})})


'''),
    ]),
    (os.path.join('travel', 'planner.py'), [
        (r'''                     'times in this plan.' % (_and(book),
                                              's' if len(book) == 1 else ''))
    for day in out['days']:
        if day['minutes'] >= 300:
            notes.append('%s is the fullest day - about %d hours of visits.'
                         % (dt.date.fromisoformat(day['day']).strftime('%A'),
                            round(day['minutes'] / 60.0)))
    unknown = [r['name'] for day in out['days'] for r in day['items']
               if r['unknown']]
''',
         r'''                     'times in this plan.' % (_and(book),
                                              's' if len(book) == 1 else ''))
    # TR-14 (Demetri, 17 Nov: "How can both Monday and Wednesday be the
    # fullest day?? Maybe it should say that Wednesday is the fullest day.
    # and maybe that Monday is a very full day?"): one fullest day - the
    # one with the most hours - and any other long one "also very full".
    full = sorted([d for d in out['days'] if d['minutes'] >= 300],
                  key=lambda d: (-d['minutes'], d['day']))
    if full:
        name = lambda d: dt.date.fromisoformat(d['day']).strftime(  # noqa
            '%A %d').replace(' 0', ' ')
        hours = lambda d: round(d['minutes'] / 60.0)               # noqa
        line = '%s is the fullest day - about %d hours of visits.' % (
            name(full[0]), hours(full[0]))
        rest = sorted(full[1:], key=lambda d: d['day'])
        if rest:
            line += ' %s %s also very full (%s).' % (
                _and([name(d) for d in rest]),
                'is' if len(rest) == 1 else 'are',
                ', '.join('about %d hours' % hours(d) for d in rest))
        notes.append(line)
    unknown = [r['name'] for day in out['days'] for r in day['items']
               if r['unknown']]
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_added.html'), [
        (r'''{% comment %} TR-12, 17 Nov 2026 - after adding suggestions: each is being looked up; back to the rest. Plan my days says "N new things since your plan" by itself. phone=True on the phone. {% endcomment %}
{% if ideas_added %}<section class="tv-pl-banner" role="status" data-idea-added><span><b>{{ ideas_added }} added to Things to do</b> &middot; their addresses and opening hours are being looked up</span>{% if ideas_left %}<a href="{% if phone %}{% url 'travel:m_ideas' trip.pk %}{% else %}{% url 'travel:ideas' trip.pk %}{% endif %}" style="color: #7FD3DA; font-weight: 700; min-height: 44px; display: flex; align-items: center">Back to suggestions</a>{% endif %}</section>{% endif %}
''',
         r'''{% comment %} TR-12, 17 Nov 2026 - after adding suggestions: each is being looked up; back to the rest. Plan my days says "N new things since your plan" by itself. phone=True on the phone. {% endcomment %}
{% if ideas_added %}<section class="tv-pl-banner" role="status" data-idea-added><span><b>{{ ideas_added }} added to Things to do</b> &middot; {% if looking %}their addresses and opening hours are being looked up &ndash; this page updates by itself{% else %}all looked up{% endif %}</span>{% if ideas_left %}<a href="{% if phone %}{% url 'travel:m_ideas' trip.pk %}{% else %}{% url 'travel:ideas' trip.pk %}{% endif %}" style="color: #7FD3DA; font-weight: 700; min-height: 44px; display: flex; align-items: center">Back to suggestions</a>{% endif %}</section>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_card.html'), [
        (r'''{% comment %} TR-12 - one suggestion: tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}" data-idea="{{ i.pk }}">
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
''',
         r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}" data-idea="{{ i.pk }}"{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_top.html'), [
        (r'''{% if counts|length > 1 %}<nav class="tv-id-chips" aria-label="Cities"><a class="tv-id-chip{% if not city %} on{% endif %}" href="?{% if show_hidden %}hidden=1{% endif %}"{% if not city %} aria-current="page"{% endif %}>All</a>{% for c in counts %}<a class="tv-id-chip{% if city == c.city %} on{% endif %}" href="?city={{ c.city|urlencode }}{% if show_hidden %}&amp;hidden=1{% endif %}"{% if city == c.city %} aria-current="page"{% endif %}>{{ c.city }} <span class="n">{{ c.n }}</span></a>{% endfor %}</nav>{% endif %}
<p style="margin: 0; font-size: .88rem; color: #4A5A61">{% if saved %}Saved on the trip &middot; come back any time{% endif %}{% if hidden %} &middot; {{ hidden }} hidden as Not interested &middot; {% if show_hidden %}<a href="?{% if city %}city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Hide them</a>{% else %}<a href="?hidden=1{% if city %}&amp;city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Show them</a>{% endif %}{% endif %}</p>
''',
         r'''{% if counts|length > 1 %}<nav class="tv-id-chips" aria-label="Cities"><a class="tv-id-chip{% if not city %} on{% endif %}" href="?{% if show_hidden %}hidden=1{% endif %}"{% if not city %} aria-current="page"{% endif %}>All</a>{% for c in counts %}<a class="tv-id-chip{% if city == c.city %} on{% endif %}" href="?city={{ c.city|urlencode }}{% if show_hidden %}&amp;hidden=1{% endif %}"{% if city == c.city %} aria-current="page"{% endif %}>{{ c.city }} <span class="n">{{ c.n }}</span></a>{% endfor %}</nav>{% endif %}
<p style="margin: 0; font-size: .88rem; color: #4A5A61">{% if saved %}Saved on the trip &middot; come back any time{% endif %}{% if hidden %} &middot; {{ hidden }} hidden as Not interested &middot; {% if show_hidden %}<a href="?{% if city %}city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Hide them</a>{% else %}<a href="?hidden=1{% if city %}&amp;city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Show them</a>{% endif %}{% endif %}</p>
{% comment %} TR-14 - what Show me more just brought. {% endcomment %}
{% if n_new %}<p style="margin: 0; font-size: .9rem" data-idea-newline><span class="tv-id-new">New</span> {{ n_new }} more idea{{ n_new|pluralize }}{% if new_city %} for {{ new_city }}{% endif %} &ndash; marked New. What you had ticked is still ticked.{% if first_new %} <a href="#new">Go to the first</a>{% endif %}</p>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
</style>
''',
         r'''.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
/* TR-14, 17 Nov 2026 - the trips on a calendar; List | Calendar. */
.tv-view { display: inline-flex; border: 1px solid #C9D3D6; border-radius: 999px; overflow: hidden; background: #FFFFFF; }
.tv-view a { min-height: 36px; padding: 0 14px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: .9rem; color: #1D2B31; text-decoration: none; }
.tv-view a.on { background: #0F7480; color: #FFFFFF; }
.tv-cal { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 12px; padding: 12px; }
.tv-cal-head { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 10px; }
.tv-cal-title { font-size: 1.35rem; font-weight: 700; margin: 0; min-width: 9.5em; text-align: center; }
.tv-cal-arrow { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; border: 1px solid #C9D3D6; font-size: 1.5rem; line-height: 1; color: #0F7480; text-decoration: none; background: #FFFFFF; }
.tv-cal-pick { display: inline-flex; gap: 6px; align-items: center; margin: 0 0 0 auto; }
.tv-cal-pick select { min-height: 38px; border: 1px solid #C9D3D6; border-radius: 8px; padding: 0 8px; font: inherit; background: #FFFFFF; }
.tv-cal-go { min-height: 38px; border: 1px solid #0F7480; color: #0F7480; background: #FFFFFF; border-radius: 8px; padding: 0 10px; font: inherit; font-weight: 600; }
.tv-cal-today { min-height: 38px; display: inline-flex; align-items: center; padding: 0 12px; border-radius: 8px; background: #0F7480; color: #FFFFFF; font-weight: 600; text-decoration: none; }
.tv-cal-sr { position: absolute; left: -9999px; }
.tv-cal-dow { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); font-size: .72rem; font-weight: 700; color: #5B6B72; text-transform: uppercase; letter-spacing: .04em; text-align: center; padding-bottom: 4px; }
.tv-cal-week { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); row-gap: 3px; min-height: 92px; border-top: 1px solid #E1E6E8; align-content: start; }
.tv-cal-day { border-left: 1px solid #EEF1F2; padding: 4px 6px 6px; display: flex; flex-wrap: wrap; align-items: center; gap: 3px; align-content: flex-start; min-height: 88px; }
.tv-cal-day:first-child { border-left: 0; }
.tv-cal-day .n { font-size: .85rem; font-weight: 600; color: #1D2B31; width: 1.9em; height: 1.9em; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; }
.tv-cal-day.out .n { color: #8A9BA2; font-weight: 400; }
.tv-cal-day.out { background: #FAFBFB; }
.tv-cal-day.today .n { background: #0F7480; color: #FFFFFF; }
.tv-cal-plane { flex: none; }
.tv-cal-bar { position: relative; z-index: 1; margin: 0 3px; border-radius: 6px; color: #FFFFFF; font-size: .8rem; font-weight: 700; line-height: 26px; padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-decoration: none; align-self: stretch; }
.tv-cal-bar:hover, .tv-cal-bar:focus { color: #FFFFFF; text-decoration: none; filter: brightness(1.1); }
.tv-cal-bar.ml { margin-left: 0; border-top-left-radius: 0; border-bottom-left-radius: 0; }
.tv-cal-bar.mr { margin-right: 0; border-top-right-radius: 0; border-bottom-right-radius: 0; }
.tv-cal-bar.past { opacity: .5; }
.tv-cal-none { margin: 10px 2px 0; font-size: .88rem; color: #4A5A61; }
.tv-cal-list { display: flex; flex-direction: column; margin-top: 10px; border-top: 1px solid #E1E6E8; }
.tv-cal-item { display: flex; gap: 10px; align-items: center; padding: 10px 2px; border-bottom: 1px solid #EEF1F2; color: #1D2B31; text-decoration: none; min-height: 44px; }
.tv-cal-item i { flex: none; width: 12px; height: 32px; border-radius: 4px; }
.tv-cal-item span { display: flex; flex-direction: column; }
.tv-cal-item small { color: #5B6B72; font-size: 12px; }
.tv-cal-item.past { opacity: .6; }
@media (max-width: 560px) {
  .tv-cal { padding: 10px 6px; }
  .tv-cal-title { font-size: 1.1rem; min-width: 0; flex: 1; }
  .tv-cal-pick { margin: 0; width: 100%; }
  .tv-cal-pick select { flex: 1; }
  .tv-cal-week { min-height: 64px; }
  .tv-cal-day { min-height: 60px; padding: 2px 2px 4px; gap: 1px; }
  .tv-cal-day .n { font-size: 12px; }
  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% if sub == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% endblock %}
''',
         r'''<p class="tv-muted tv-small" style="text-align: center; margin: 0">On this trip: {% for p in people %}{{ p.get_full_name|default:p.username }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
{% if sub == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% include 'travel/_lookup_refresh.html' %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trips.html'), [
        (r'''{% block sub %}<div class="sub">Yours and the ones shared with you</div>{% endblock %}
{% block content %}
<nav class="tv-chips" aria-label="Show"><a class="tv-chip{% if not past and not auto_past %} on{% endif %}" href="{% url 'travel:m_trips' %}">Upcoming</a><a class="tv-chip{% if past or auto_past %} on{% endif %}" href="?show=past">Past</a>{% if can_compare %}<a class="tv-chip" href="{% url 'travel:m_compare' %}" data-compare-link>Compare</a>{% endif %}</nav>
{% if auto_past %}<section class="tv-card" data-auto-past><p class="tv-muted" style="margin: 0">Nothing coming up &mdash; your past trips, newest first.</p></section>{% endif %}
''',
         r'''{% block sub %}<div class="sub">Yours and the ones shared with you</div>{% endblock %}
{% block content %}
{% comment %} TR-14, 17 Nov 2026 - List | Calendar (Demetri: "The calendar should just be another view that the user can activate"). {% endcomment %}
<nav class="tv-view" aria-label="View" data-view-switch style="align-self: flex-start; margin-bottom: 10px"><a href="?view=list"{% if view == 'list' %} class="on" aria-current="page"{% endif %}>List</a><a href="?view=calendar"{% if view == 'calendar' %} class="on" aria-current="page"{% endif %} data-view-calendar>Calendar</a></nav>
{% if view == 'calendar' %}{% include 'travel/_calendar.html' with phone=True %}{% else %}
<nav class="tv-chips" aria-label="Show"><a class="tv-chip{% if not past and not auto_past %} on{% endif %}" href="{% url 'travel:m_trips' %}">Upcoming</a><a class="tv-chip{% if past or auto_past %} on{% endif %}" href="?show=past">Past</a>{% if can_compare %}<a class="tv-chip" href="{% url 'travel:m_compare' %}" data-compare-link>Compare</a>{% endif %}</nav>
{% if auto_past %}<section class="tv-card" data-auto-past><p class="tv-muted" style="margin: 0">Nothing coming up &mdash; your past trips, newest first.</p></section>{% endif %}
'''),
        (r'''<section class="tv-card"><p class="tv-muted" style="margin: 0">{% if past %}No past trips.{% else %}No trips coming up. New trips are made on the computer, or from To check.{% endif %}</p></section>
{% endfor %}
<a href="{% url 'travel:trips' %}" class="tv-muted tv-out" style="text-align: center">Open Travel on the full site</a>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-muted" style="margin: 0">{% if past %}No past trips.{% else %}No trips coming up. New trips are made on the computer, or from To check.{% endif %}</p></section>
{% endfor %}
{% endif %}
<a href="{% url 'travel:trips' %}" class="tv-muted tv-out" style="text-align: center">Open Travel on the full site</a>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''{% if tab == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% render_help_modal "travel" %}
{% endblock %}
''',
         r'''{% if tab == 'itinerary' %}{% include 'travel/_reorder.html' %}{% endif %}
{% render_help_modal "travel" %}
{% include 'travel/_lookup_refresh.html' %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''</section>
{% endif %}
{% if count %}
<nav class="tv-chips" aria-label="Show">
''',
         r'''</section>
{% endif %}
{% comment %} TR-14, 17 Nov 2026 (Demetri: "The calendar should just be another view that the user can activate"). {% endcomment %}
{% if count %}<div class="tv-row" style="margin: 0 0 12px; align-items: center"><nav class="tv-view" aria-label="View" data-view-switch><a href="?view=list"{% if view == 'list' %} class="on" aria-current="page"{% endif %}><i class="fas fa-th-large" aria-hidden="true"></i> List</a><a href="?view=calendar"{% if view == 'calendar' %} class="on" aria-current="page"{% endif %} data-view-calendar><i class="far fa-calendar-alt" aria-hidden="true"></i> Calendar</a></nav></div>{% endif %}
{% if view == 'calendar' %}{% include 'travel/_calendar.html' %}{% else %}
{% if count %}
<nav class="tv-chips" aria-label="Show">
'''),
        (r'''{% endfor %}
</div>
{% endif %}


''',
         r'''{% endfor %}
</div>
{% endif %}{% endif %}


'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        t.owing = eur(sum((b.due_eur or Decimal('0')) for b in due)) \
            if due else ''
    return render(request, 'travel/trips.html', {
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'auto_past': auto_past,
''',
         r'''        t.owing = eur(sum((b.due_eur or Decimal('0')) for b in due)) \
            if due else ''
    # TR-14, 17 Nov 2026 - List | Calendar; the calendar is every trip,
    # on the month asked for (this one first), and the choice is kept.
    from . import calendar_view as CV
    view, asked = CV.view_of(request)
    cal = CV.build(rows, CV.month_of(request.GET.get('month'), today),
                   today) if view == 'calendar' else None
    return CV.remember(render(request, 'travel/trips.html', {
        'view': view, 'cal': cal,
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'auto_past': auto_past,
'''),
        (r'''        'phone_qr': phone_qr(request) if request.GET.get('phone') == '1'
        else '',
        'requests': requests_for(request.user)})


''',
         r'''        'phone_qr': phone_qr(request) if request.GET.get('phone') == '1'
        else '',
        'requests': requests_for(request.user)}), view, asked)


'''),
        (r'''    """TR-12 - Suggest things to do: suggestions left, one being found,
    the line after adding."""
    if tab != 'wish':
        return {}
    from .ideas import page_state
''',
         r'''    """TR-12 - Suggest things to do: suggestions left, one being found,
    the line after adding."""
    if tab not in ('wish', 'itinerary'):
        return {}
    from .ideas import page_state
'''),
    ]),
    (os.path.join('travel', 'views_ideas.py'), [
        (r'''            order.append(i.city)
    shown = [i for i in all_ideas if i.state == '']
    counts = [{'city': c, 'n': sum(1 for i in shown if i.city == c)}
              for c in order]
''',
         r'''            order.append(i.city)
    shown = [i for i in all_ideas if i.state == '']
    # TR-14 (Demetri, 17 Nov: "it is not clear which ones are new? Maybe we
    # should always mark the new ones added with a new label each time"):
    # what the latest Show me more brought is marked New - until the next.
    latest = t.idea_runs.first()
    fresh = latest.pk if latest and latest.more else None
    first_new = None
    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
        if i.new and i.state == '' and first_new is None:
            first_new = i.pk
    counts = [{'city': c, 'n': sum(1 for i in shown if i.city == c)}
              for c in order]
'''),
        (r'''        'failed': failed, 'error': last.error if last and failed else '',
        'saved': last.created_at if last else None,
        'ticked_n': len(ticked)})
    return _show(request, 'ideas.html', ctx)


def _back(request, t, extra=''):
    q = []
    c = request.POST.get('city_f') or ''
''',
         r'''        'failed': failed, 'error': last.error if last and failed else '',
        'saved': last.created_at if last else None,
        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        'new_city': (latest.answers or {}).get('more') or
        next(iter(latest.progress or {}), '') if fresh else ''})
    return _show(request, 'ideas.html', ctx)


def _back(request, t, extra='', anchor=''):
    q = []
    c = request.POST.get('city_f') or ''
'''),
        (r'''        q.append(extra)
    return redirect(_url(request, 'ideas', t.pk) + ('?' + '&'.join(q)
                                                    if q else ''))


''',
         r'''        q.append(extra)
    return redirect(_url(request, 'ideas', t.pk) + ('?' + '&'.join(q)
                                                    if q else '') +
                    ('#' + anchor if anchor else ''))


'''),
        (r'''    job = ID.begin(t, request.user, answers, more=city)
    ID.start(job)
    return redirect(_url(request, 'ideas', t.pk))
''',
         r'''    job = ID.begin(t, request.user, answers, more=city)
    ID.start(job)
    # TR-14 (Demetri, 17 Nov: "the ones I ticked must remain ticked, even
    # though new ones are added"): back with what was ticked, at the new.
    return _back(request, t, anchor='new')
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
    raise SystemExit('TR-14 REFUSED: %s' % msg)


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
    if "'test_travel_fourteen.py'" in read(pq):
        print('TR-14 already applied.')
        return 0
    if "'test_travel_thirteen.py'" not in read(pq):
        refuse('TR-13 (apply_travel_thirteen.py, Release 94) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-14 --check: %d file(s) would change, none written; %d '
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
    print('TR-14 applied - the trips on a calendar; Show me more keeps the ticks.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
