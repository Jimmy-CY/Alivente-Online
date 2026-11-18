# -*- coding: utf-8 -*-
"""apply_travel_sixteen.py - round TR-16, 18 Nov 2026.

RELEASE 100 - TRAVEL: TIDIER TRIP FILTERS.

    Demetri, 18 Nov: "I don't like how the 1 is placed near the Upcoming
    and the Past. It look like part of the name. We need to differentiate
    it. Also, Can we put the "All" first on the left. What happens when we
    have additional years and countries. Are our filters not going to look
    messy? Is there not a cleverer way to do years and countries? We leave
    All, Upcoming and Past as is." - and to the proposal: "Yes. Let's go
    ahead and build it."

    - All, Upcoming and Past stay chips, All first; each count is its own
      small badge.
    - Years and countries become two menus: Year (newest first) and
      Country (most trips first, with counts). A pick shows as a chip
      with an x that clears it.
    - They combine: Past + 2026 + Greece. The badges follow the picks.
    - One filter for the computer and the phone (travel/trip_filter.py);
      old ?show=2026 and ?show=c:Greece links still work.
    - Help on the computer and the phone; the phone app's version moves
      (tv16-1) so it fetches the new look.

The suite, trip_filter.py and _trip_filters.html ship beside this
patcher. Stands on RU-1 (apply_recipe_units_null.py). Idempotent. Edits
backed up to .bak_travel16. No migration.
"""
import os
import sys

SUFFIX = '.bak_travel16'
MARK = 'TR-16, 18 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_sixteen.py',
    'travel/trip_filter.py',
    'travel/templates/travel/_trip_filters.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_cycle_look.py',
    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    'test_recipe_units_null.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_cycle_look.py',
    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    'test_recipe_units_null.py',
    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    'test_travel_sixteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    '.bak_units1',
]

''',
         r'''    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    '.bak_units1',
    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    '.bak_travel16',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
''',
         r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Across the top are <strong>All</strong>, <strong>Upcoming</strong> and <strong>Past</strong>, each with its number of trips in a small grey badge, then two menus: <strong>Year</strong> (newest first) and <strong>Country</strong> (the countries you go to most at the top). Pick a year or a country and it becomes a highlighted chip &mdash; press its &#x2715; to clear it. They combine: Past, 2026 and Greece shows the past trips of 2026 in Greece, and the numbers in the badges follow what you picked. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
'''),
    ]),
    (os.path.join('test_travel_seven.py'), [
        (r'''               'NOTHING COMING UP: Travel shows the past trips, newest first, '
               'each marked Past')
            ok('Upcoming <span class="tv-sub">0</span>' in h and
               'Past <span class="tv-sub">2</span>' in h,
               '  the chips say how many')
            ok('data-owing' in h.split('TV7 Swiss')[0],
               '  a finished trip still owing says so')
''',
         r'''               'NOTHING COMING UP: Travel shows the past trips, newest first, '
               'each marked Past')
            # TR-16, 18 Nov 2026 - the count is its own badge now.
            ok('Upcoming <span class="tv-count" aria-label="0 trips">0'
               '</span>' in h and
               'Past <span class="tv-count" aria-label="2 trips">2</span>'
               in h, '  the chips say how many')
            ok('data-owing' in h.split('TV7 Swiss')[0],
               '  a finished trip still owing says so')
'''),
    ]),
    (os.path.join('test_travel_thirteen.py'), [
        (r'''# ==========================================================================
v = read(J(TA, 'views.py'))
ok('sel.sort(key=lambda t: (t.start or far), reverse=True)' in v and
   "reverse=(show == 'past' or auto_past)" not in v,
   'COMPUTER: every list sorted latest first')
ph = read(J(TA, 'phone.py'))
ok(ph.count('key=lambda t: t.start or far, reverse=True)') == 3,
   'PHONE: Upcoming too, as Past already was')
pl = read(J(TA, 'planner.py'))
''',
         r'''# ==========================================================================
v = read(J(TA, 'views.py'))
# TR-16, 18 Nov 2026 - the computer and the phone share one filter
# (travel/trip_filter.py), and it sorts every list latest first.
tf = read(J(TA, 'trip_filter.py'))
ok('sel.sort(key=lambda t: (t.start or FAR), reverse=True)' in tf and
   'TF.apply(request, rows, today)' in v and
   "reverse=(show == 'past' or auto_past)" not in v,
   'COMPUTER: every list sorted latest first')
ph = read(J(TA, 'phone.py'))
ok('TF.apply(request, rows, day)' in ph,
   'PHONE: Upcoming too, as Past already was')
pl = read(J(TA, 'planner.py'))
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-chip { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 14px; border-radius: 999px; border: 1px solid #C9D3D6; background: #fff; color: var(--tv-ink); font-size: 13px; text-decoration: none; }
.tv-chip.on { background: var(--tv-teal); border-color: var(--tv-teal); color: #fff; font-weight: 600; }
.tv-tag { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid currentColor; white-space: nowrap; }
.tv-tag.paid { color: var(--tv-good); } .tv-tag.due { color: var(--tv-warn); } .tv-tag.sh { color: var(--tv-teal); }
''',
         r'''.tv-chip { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 14px; border-radius: 999px; border: 1px solid #C9D3D6; background: #fff; color: var(--tv-ink); font-size: 13px; text-decoration: none; }
.tv-chip.on { background: var(--tv-teal); border-color: var(--tv-teal); color: #fff; font-weight: 600; }
/* TR-16, 18 Nov 2026 - the count as its own badge; Year and Country as menus. */
.tv-count { display: inline-flex; align-items: center; justify-content: center; min-width: 20px; height: 18px; padding: 0 6px; border-radius: 9px; background: rgba(0, 0, 0, .07); color: var(--tv-soft); font-size: 11.5px; font-weight: 600; }
.tv-chip.on .tv-count { background: rgba(255, 255, 255, .28); color: #fff; }
.tv-fsep { width: 1px; height: 22px; background: #C9D3D6; margin: 0 2px; align-self: center; }
.tv-menu { display: inline-flex; margin: 0; }
.tv-menu-chip { position: relative; padding-right: 28px; }
.tv-menu-chip select { appearance: none; -webkit-appearance: none; border: 0; background: transparent; color: inherit; font: inherit; padding: 0; min-height: 34px; }
.tv-menu-chip::after { content: ""; position: absolute; right: 12px; top: 50%; width: 6px; height: 6px; border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: translateY(-70%) rotate(45deg); pointer-events: none; }
.tv-picked { border: 1.5px solid var(--tv-teal); color: var(--tv-teal); font-weight: 600; }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
/* on the phone the menus start their own row */
.tv-filters .tv-fsep { flex-basis: 100%; width: auto; height: 0; margin: 0; background: none; }
.tv-tag { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid currentColor; white-space: nowrap; }
.tv-tag.paid { color: var(--tv-good); } .tv-tag.due { color: var(--tv-warn); } .tv-tag.sh { color: var(--tv-teal); }
'''),
        (r'''html.tv-turn-90 body.tv-holding .tv-nav, html.tv-turn-270 body.tv-holding .tv-nav { position: sticky; }
@media (prefers-color-scheme: dark) {
  body, .tv-app { background: #11191C; color: #E6ECEE; }
  .tv-card, .tv-tabs, .tv-nav, .tv-select, .tv-input, .tv-chip { background: #1A2428; border-color: #2B383D; color: #E6ECEE; }
''',
         r'''html.tv-turn-90 body.tv-holding .tv-nav, html.tv-turn-270 body.tv-holding .tv-nav { position: sticky; }
@media (prefers-color-scheme: dark) {
  .tv-count { background: rgba(255, 255, 255, .12); color: #C9D3D6; }
  .tv-picked { border-color: #5FC3CC; color: #5FC3CC; }
  body, .tv-app { background: #11191C; color: #E6ECEE; }
  .tv-card, .tv-tabs, .tv-nav, .tv-select, .tv-input, .tv-chip { background: #1A2428; border-color: #2B383D; color: #E6ECEE; }
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# of the two it was moved for; test_travel_fifteen.py fails the gate when
# they change and it does not.
SW_VERSION = 'tv15-1'
SW_ASSETS = 'aace7b3e2c05'


''',
         r'''# of the two it was moved for; test_travel_fifteen.py fails the gate when
# they change and it does not.
# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
SW_VERSION = 'tv16-1'
SW_ASSETS = '37ece7f3cd8d'


'''),
        (r'''    day = _today()
    rows = _trip_list(request.user)
    past = request.GET.get('show') == 'past'
    far = dt.date(9999, 1, 1)
    if past:
        sel = sorted([t for t in rows if t.end and t.end < day],
                     key=lambda t: t.start or far, reverse=True)
    else:
        # TR-13 - the latest trip first, as on the computer.
        sel = sorted([t for t in rows if not (t.end and t.end < day)],
                     key=lambda t: t.start or far, reverse=True)
    # TR-7 - nothing ahead: the past trips, newest first, said so.
    auto_past = not past and not sel and any(t.end and t.end < day
                                             for t in rows)
    if auto_past:
        sel = sorted([t for t in rows if t.end and t.end < day],
                     key=lambda t: t.start or far, reverse=True)
    for t in sel:
        t.past = bool(t.end and t.end < day)
    # TR-14, 17 Nov 2026 - List | Calendar, as on the computer.
    from . import calendar_view as CV
''',
         r'''    day = _today()
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
'''),
        (r'''        'view': view, 'cal': cal,
        'trips': sel, 'past': past, 'tab': 'trips', 'auto_past': auto_past,
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)}), view, asked)
''',
         r'''        'view': view, 'cal': cal,
        'trips': sel, 'past': past, 'tab': 'trips', 'auto_past': auto_past,
        'F': F,
        'can_compare': len(rows) > 1,
        'checks': inbox.open_count(request.user)}), view, asked)
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-chip:hover { color: var(--alv-accent); text-decoration: none; }
.tv-chip.is-on { border-color: var(--alv-accent); color: var(--alv-accent); font-weight: 700; }
.tv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.tv-card { display: flex; flex-direction: column; gap: 8px; padding: 16px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); color: var(--alv-ink); text-decoration: none; }
''',
         r'''.tv-chip:hover { color: var(--alv-accent); text-decoration: none; }
.tv-chip.is-on { border-color: var(--alv-accent); color: var(--alv-accent); font-weight: 700; }
/* TR-16, 18 Nov 2026 - the count as its own badge; Year and Country as menus. */
.tv-count { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 20px; padding: 0 7px; border-radius: 10px; background: rgba(0, 0, 0, .07); color: var(--alv-ink-soft); font-size: 0.78rem; font-weight: 600; }
.tv-chip.is-on .tv-count { background: var(--alv-accent); color: #fff; }
.tv-fsep { width: 1px; height: 24px; background: var(--alv-line); margin: 0 4px; align-self: center; }
.tv-menu { display: inline-flex; margin: 0; }
.tv-menu-chip { position: relative; cursor: pointer; padding-right: 30px; color: var(--alv-ink-soft); }
.tv-menu-chip select { appearance: none; -webkit-appearance: none; border: 0; background: transparent; color: var(--alv-ink); font: inherit; padding: 0; cursor: pointer; min-height: 34px; }
.tv-menu-chip::after { content: ""; position: absolute; right: 13px; top: 50%; width: 7px; height: 7px; border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: translateY(-70%) rotate(45deg); pointer-events: none; }
.tv-menu-chip:focus-within { border-color: var(--alv-accent); box-shadow: 0 0 0 2px rgba(14, 124, 139, .2); }
.tv-picked { border: 1.5px solid var(--alv-accent); background: rgba(14, 124, 139, .08); color: var(--alv-accent); font-weight: 700; }
.tv-picked .tv-x { font-size: 0.8rem; }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.tv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.tv-card { display: flex; flex-direction: column; gap: 8px; padding: 16px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); color: var(--alv-ink); text-decoration: none; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv15-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv16-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv15-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv16-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trips.html'), [
        (r'''<nav class="tv-view" aria-label="View" data-view-switch style="align-self: flex-start; margin-bottom: 10px"><a href="?view=list"{% if view == 'list' %} class="on" aria-current="page"{% endif %}>List</a><a href="?view=calendar"{% if view == 'calendar' %} class="on" aria-current="page"{% endif %} data-view-calendar>Calendar</a></nav>
{% if view == 'calendar' %}{% include 'travel/_calendar.html' with phone=True %}{% else %}
<nav class="tv-chips" aria-label="Show"><a class="tv-chip{% if not past and not auto_past %} on{% endif %}" href="{% url 'travel:m_trips' %}">Upcoming</a><a class="tv-chip{% if past or auto_past %} on{% endif %}" href="?show=past">Past</a>{% if can_compare %}<a class="tv-chip" href="{% url 'travel:m_compare' %}" data-compare-link>Compare</a>{% endif %}</nav>
{% if auto_past %}<section class="tv-card" data-auto-past><p class="tv-muted" style="margin: 0">Nothing coming up &mdash; your past trips, newest first.</p></section>{% endif %}
{% for t in trips %}
''',
         r'''<nav class="tv-view" aria-label="View" data-view-switch style="align-self: flex-start; margin-bottom: 10px"><a href="?view=list"{% if view == 'list' %} class="on" aria-current="page"{% endif %}>List</a><a href="?view=calendar"{% if view == 'calendar' %} class="on" aria-current="page"{% endif %} data-view-calendar>Calendar</a></nav>
{% if view == 'calendar' %}{% include 'travel/_calendar.html' with phone=True %}{% else %}
{% include 'travel/_trip_filters.html' with on='on' %}
{% if can_compare %}<nav class="tv-chips" aria-label="Compare" style="margin-top: 8px"><a class="tv-chip" href="{% url 'travel:m_compare' %}" data-compare-link>Compare trips</a></nav>{% endif %}
{% if auto_past %}<section class="tv-card" data-auto-past><p class="tv-muted" style="margin: 0">Nothing coming up &mdash; your past trips, newest first.</p></section>{% endif %}
{% for t in trips %}
'''),
        (r'''</a>
{% empty %}
<section class="tv-card"><p class="tv-muted" style="margin: 0">{% if past %}No past trips.{% else %}No trips coming up. New trips are made on the computer, or from To check.{% endif %}</p></section>
{% endfor %}
{% endif %}
''',
         r'''</a>
{% empty %}
<section class="tv-card"><p class="tv-muted" style="margin: 0">{% if F.year or F.country %}No trips match these filters. <a href="?show=all">Show all trips</a>{% elif past %}No past trips.{% else %}No trips coming up. New trips are made on the computer, or from To check.{% endif %}</p></section>
{% endfor %}
{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''{% if view == 'calendar' %}{% include 'travel/_calendar.html' %}{% else %}
{% if count %}
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
''',
         r'''{% if view == 'calendar' %}{% include 'travel/_calendar.html' %}{% else %}
{% if count %}
{% include 'travel/_trip_filters.html' with on='is-on' %}
{% endif %}

{% comment %} TR-7, 16 Nov 2026 (Demetri: "If there are not upcoming, then it must show the past ones in descending date order (highlighting that they are Past)"; "I must be able to multi select trips for comparison"). {% endcomment %}
{% if auto_past %}<p class="tv-note" data-auto-past>Nothing coming up{% if F.year or F.country %} here{% endif %} &mdash; here are your <b>past trips</b>, newest first.</p>{% endif %}
{% if count > 1 %}<form method="get" action="{% url 'travel:compare' %}" id="tv-compare" class="tv-row" style="margin: 0 0 12px; align-items: center" data-compare-form><span class="tv-sub">Tick two or more trips to compare their costs.</span><button type="submit" class="btn action-secondary btn-sm" title="Compare the ticked trips side by side"><i class="fas fa-balance-scale"></i> Compare ticked trips</button></form>{% endif %}
<div class="tv-grid" data-trips>
'''),
        (r'''    </div>
{% empty %}
    <p class="text-muted">{% if count %}No trips here.{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>
''',
         r'''    </div>
{% empty %}
    <p class="text-muted">{% if count %}No trips match these filters. <a href="?show=all">Show all trips</a>{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''    inbox.kick()
    today = dt.date.today()
    show = request.GET.get('show') or 'upcoming'
    rows = []
    years, countries = set(), set()
    for t in trips_for(request.user).prefetch_related('bookings',
                                                      'shared_with'):
''',
         r'''    inbox.kick()
    today = dt.date.today()
    rows = []
    for t in trips_for(request.user).prefetch_related('bookings',
                                                      'shared_with'):
'''),
        (r'''        t.people = [t.owner] + list(t.shared_with.all())
        t.mine = t.owner_id == request.user.id
        if start:
            years.add(start.year)
        countries.update(t.where_list)
        t.past = bool(end and end < today)
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
    elif show.isdigit():
        sel = [t for t in rows if t.start and t.start.year == int(show)]
    elif show.startswith('c:'):
        sel = [t for t in rows if show[2:] in t.where_list]
    else:
        show, sel = 'all', rows
    far = dt.date(9999, 1, 1)
    # TR-13, 17 Nov 2026 (Demetri: "When trips are listed, they should be
    # sorted from the latest one, to the oldest one"): every list, the
    # latest trip first. A trip with no dates yet is newest of all.
    sel.sort(key=lambda t: (t.start or far), reverse=True)
    # TR-7 - a finished trip with something still To pay says so.
    from .compare import unsettled
''',
         r'''        t.people = [t.owner] + list(t.shared_with.all())
        t.mine = t.owner_id == request.user.id
        rows.append(t)
    # TR-16, 18 Nov 2026 - All, Upcoming and Past as chips with their
    # counts as badges; Year and Country as menus; the three combine
    # (travel/trip_filter.py). TR-7 and TR-13 live on inside it: nothing
    # ahead shows the past ones, and every list is the latest trip first.
    from . import trip_filter as TF
    F = TF.apply(request, rows, today)
    sel, auto_past = F['trips'], F['auto_past']
    # TR-7 - a finished trip with something still To pay says so.
    from .compare import unsettled
'''),
        (r'''    return CV.remember(render(request, 'travel/trips.html', {
        'view': view, 'cal': cal,
        'trips': sel, 'show': show, 'years': sorted(years, reverse=True),
        'auto_past': auto_past,
        'n_upcoming': len([t for t in rows if not t.past]),
        'n_past': len([t for t in rows if t.past]),
        'countries': sorted(countries), 'count': len(rows),
        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
''',
         r'''    return CV.remember(render(request, 'travel/trips.html', {
        'view': view, 'cal': cal,
        'trips': sel, 'F': F, 'show': F['show'],
        'auto_past': auto_past, 'count': len(rows),
        'checks': inbox.open_count(request.user),
        'address': inbox.inbox_address(),
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
    raise SystemExit('TR-16 REFUSED: %s' % msg)


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
    if "'test_travel_sixteen.py'" in read(pq):
        print('TR-16 already applied.')
        return 0
    if "'test_recipe_units_null.py'" not in read(pq):
        refuse('RU-1 (apply_recipe_units_null.py, Release 99) is not applied - this round registers after it.')
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
        print('TR-16 --check: %d file(s) would change, none written; %d '
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
    print('TR-16 applied - tidier trip filters.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
