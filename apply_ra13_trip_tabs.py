# -*- coding: utf-8 -*-
"""apply_ra13_trip_tabs.py - round RA13, 22 Nov 2026.

RELEASE RA13 - THE TRIP TABS: ICONS; SHORT NAMES ON THE PHONE.

    Demetri, 22 Nov: "I am not happy with how the way Bookings, Itinerary,
    etc show on mobile" - "Lets go with Option B with full names on
    computer and short ones on mobile."

    - travel/_tab_icon.html (new): a bed, a calendar, a pin, a wallet and
      an i - drawn, so the phone app needs no icon font.
    - The phone: the five tabs share one line, an icon over a short name
      (Bookings, Plan, To do, Costs, Info; read aloud by their full
      names). The computer: the same icons before the full names.
    - test_travel_five checks the phone's Things to do tab by its name
      read aloud (the label on screen is now To do).
    - Help on the computer and the phone; the phone app moves to tv26-1.
    - No migration.

The suite and the icon template ship beside this patcher. Stands on RA12.
Idempotent. Edits backed up to .bak_ra13.
"""
import os
import sys

SUFFIX = '.bak_ra13'
MARK = 'RA13, 22 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra13_trip_tabs.py',
    'travel/templates/travel/_tab_icon.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra11_category_icons.py',
    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    'test_ra12_city_info_receipts.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra11_category_icons.py',
    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    'test_ra12_city_info_receipts.py',
    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    'test_ra13_trip_tabs.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    '.bak_ra12',
]

''',
         r'''    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    '.bak_ra12',
    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    '.bak_ra13',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change. The pencil <i class="fas fa-pen"></i> on the budget card opens it to change; the bin <i class="fas fa-trash-alt"></i> beside it removes the budget (it asks first; your spending stays).</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> (or its pencil <i class="fas fa-pen"></i>) to change its amount, currency, day or note; the bin <i class="fas fa-trash-alt"></i> beside the pencil deletes it, and asks first. <strong>From a receipt photo</strong> (under the form; on the phone, <strong>Take a photo of the receipt</strong> or <strong>Choose a photo</strong>) has Claude read the total, currency, day and shop&rsquo;s name and fills the form in for you to check before adding &ndash; nothing is added until you do, and the photo is never kept. <strong>Good to know</strong>, the last tab of a trip, has a card for each city: the emergency number, plugs (and whether you need an adapter from Cyprus), which side they drive on, the money with a one-off euro rate (the ECB&rsquo;s on the day the card was made), tipping, typical shop hours, the time difference from Cyprus on your dates, tap water and the language &ndash; with everyday phrases you tap to hear spoken, in the phone&rsquo;s or computer&rsquo;s own voice. Claude writes each city&rsquo;s card once and it is kept for every trip there; <strong>Refresh</strong> writes it again. On the phone, Today shows the card for the city you are in. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
''',
         r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change. The pencil <i class="fas fa-pen"></i> on the budget card opens it to change; the bin <i class="fas fa-trash-alt"></i> beside it removes the budget (it asks first; your spending stays).</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> (or its pencil <i class="fas fa-pen"></i>) to change its amount, currency, day or note; the bin <i class="fas fa-trash-alt"></i> beside the pencil deletes it, and asks first. <strong>From a receipt photo</strong> (under the form; on the phone, <strong>Take a photo of the receipt</strong> or <strong>Choose a photo</strong>) has Claude read the total, currency, day and shop&rsquo;s name and fills the form in for you to check before adding &ndash; nothing is added until you do, and the photo is never kept. A trip&rsquo;s tabs each have an icon &ndash; a bed for Bookings, a calendar for Itinerary, a pin for Things to do, a wallet for Costs and an <em>i</em> for Good to know; the phone shows the same icons with short names (Bookings, Plan, To do, Costs, Info), all on one line. <strong>Good to know</strong>, the last tab of a trip, has a card for each city: the emergency number, plugs (and whether you need an adapter from Cyprus), which side they drive on, the money with a one-off euro rate (the ECB&rsquo;s on the day the card was made), tipping, typical shop hours, the time difference from Cyprus on your dates, tap water and the language &ndash; with everyday phrases you tap to hear spoken, in the phone&rsquo;s or computer&rsquo;s own voice. Claude writes each city&rsquo;s card once and it is kept for every trip there; <strong>Refresh</strong> writes it again. On the phone, Today shows the card for the city you are in. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
'''),
    ]),
    (os.path.join('test_travel_five.py'), [
        (r'''            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('>Things to do' in h and '>Wish list' not in h and
               'Things to do</a>' in M.get('/travel/m/trip/%d/' % t.pk)
               .content.decode(),
               'THE TAB IS "Things to do", on the computer and the phone')
            raise Rollback
''',
         r'''            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('>Things to do' in h and '>Wish list' not in h and
               'aria-label="Things to do"' in M.get(
                   '/travel/m/trip/%d/' % t.pk).content.decode(),
               'THE TAB IS "Things to do", on the computer and the phone')
            raise Rollback
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
/* RA13, 22 Nov 2026 - the trip tabs: an icon over a short name, all on one line. */
.tv-tabs.is-icons { padding: 0; gap: 0; }
.tv-tabs.is-icons .tv-tab { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 9px 2px 7px; font-size: 12px; line-height: 1.2; text-align: center; white-space: nowrap; }
.tv-tabs.is-icons .tv-tab svg { width: 21px; height: 21px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
# RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
SW_VERSION = 'tv25-1'
SW_ASSETS = '90edbdcd1f50'


''',
         r'''# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
# RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
# RA13, 22 Nov 2026 - the trip tabs: icons and short names.
SW_VERSION = 'tv26-1'
SW_ASSETS = '10dd4084105c'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
/* RA13, 22 Nov 2026 - the trip tabs' icons (travel/_tab_icon.html), as on the phone. */
.tv-chip > svg { width: 16px; height: 16px; flex: none; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv25-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv26-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv25-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv26-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. These are kept apart at the end of the city, under <b>Outside what you asked for</b> &ndash; tap it to open. The round icon at the top right of each suggestion, and beside each heading, shows what kind it is &ndash; a star for must-sees, a palette for museums, a tree for parks, a signpost for streets, binoculars for viewpoints, a cup for caf&eacute;s and so on. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>. One Google can&rsquo;t find at all says <b>Not found on Google</b> in grey &ndash; you can still tick it.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Only a day of the trip can be chosen; tap a spending to change or delete it. Any on a day outside the trip is listed apart &ndash; move it or delete it. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs. On + Spending, <b>Take a photo of the receipt</b> (or <b>Choose a photo</b>) and the amount, currency, day and shop are filled in for you to check before you tap Add &ndash; the photo is never kept.</p></section>
<section class="tv-card" data-help-goodtoknow><p class="tv-h2">Good to know</p><p style="margin: 0">The <b>Good to know</b> tab of a trip has a card for each city: emergency number, plugs, which side they drive on, the money with a one-off euro rate, tipping, shop hours, the time difference from Cyprus, tap water and the language. Tap a phrase to hear it spoken. Today shows the card for the city you are in.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. These are kept apart at the end of the city, under <b>Outside what you asked for</b> &ndash; tap it to open. The round icon at the top right of each suggestion, and beside each heading, shows what kind it is &ndash; a star for must-sees, a palette for museums, a tree for parks, a signpost for streets, binoculars for viewpoints, a cup for caf&eacute;s and so on. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>. One Google can&rsquo;t find at all says <b>Not found on Google</b> in grey &ndash; you can still tick it.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">A trip&rsquo;s tabs are along the top: <b>Bookings</b>, <b>Plan</b> (the itinerary), <b>To do</b> (things to do), <b>Costs</b> and <b>Info</b> (good to know). On a trip, <b>Itinerary</b> (Plan) is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Only a day of the trip can be chosen; tap a spending to change or delete it. Any on a day outside the trip is listed apart &ndash; move it or delete it. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs. On + Spending, <b>Take a photo of the receipt</b> (or <b>Choose a photo</b>) and the amount, currency, day and shop are filled in for you to check before you tap Add &ndash; the photo is never kept.</p></section>
<section class="tv-card" data-help-goodtoknow><p class="tv-h2">Good to know</p><p style="margin: 0">The <b>Info</b> tab (Good to know) of a trip has a card for each city: emergency number, plugs, which side they drive on, the money with a one-off euro rate, tipping, shop hours, the time difference from Cyprus, tap water and the language. Tap a phrase to hear it spoken. Today shows the card for the city you are in.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a>{% endif %}<a class="tv-tab{% if sub == 'info' %} on{% endif %}" href="?tab=info" data-tab-info>Good to know</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
''',
         r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}{% comment %} RA13, 22 Nov 2026 - icon tabs, all on one line, short names (the computer keeps the full ones). {% endcomment %}<nav class="tv-tabs is-icons" aria-label="Trip"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}" data-tab="bookings"{% if sub == 'bookings' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='bookings' %}<span>Bookings</span></a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary" data-tab="itinerary" aria-label="Itinerary"{% if sub == 'itinerary' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='itinerary' %}<span>Plan</span></a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish" data-tab="wish" aria-label="Things to do"{% if sub == 'wish' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='wish' %}<span>To do</span></a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs" data-tab="costs"{% if sub == 'costs' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='costs' %}<span>Costs</span></a>{% endif %}<a class="tv-tab{% if sub == 'info' %} on{% endif %}" href="?tab=info" data-tab="info" data-tab-info aria-label="Good to know"{% if sub == 'info' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='info' %}<span>Info</span></a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</p>

<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    {% if show_money %}<a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>{% endif %}
    <a class="tv-chip{% if tab == 'info' %} is-on{% endif %}" href="{% url 'travel:trip_info' trip.pk %}"{% if tab == 'info' %} aria-current="page"{% endif %} data-tab-info>Good to know</a>
</nav>

''',
         r'''<p class="tv-sub" data-trip-span>{% if start %}{{ start|date:"D j M" }}{% if end and end != start %} – {{ end|date:"D j M Y" }}{% if nights %} · {{ nights }} night{{ nights|pluralize }}{% endif %}{% else %} {{ start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</p>

{% comment %} RA13, 22 Nov 2026 - each tab has its icon, the same as on the phone; full names here, short ones on the phone. {% endcomment %}
<nav class="tv-tabs" aria-label="Trip">
    <a class="tv-chip{% if tab == 'bookings' %} is-on{% endif %}" href="{% url 'travel:trip' trip.pk %}"{% if tab == 'bookings' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='bookings' %}Bookings <span class="tv-sub">{{ bookings|length }}</span></a>
    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='itinerary' %}Itinerary</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='wish' %}Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    {% if show_money %}<a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='costs' %}Costs</a>{% endif %}
    <a class="tv-chip{% if tab == 'info' %} is-on{% endif %}" href="{% url 'travel:trip_info' trip.pk %}"{% if tab == 'info' %} aria-current="page"{% endif %} data-tab-info>{% include 'travel/_tab_icon.html' with k='info' %}Good to know</a>
</nav>

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
    raise SystemExit('RA13 REFUSED: %s' % msg)


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
    if "'test_ra13_trip_tabs.py'" in read(pq):
        print('RA13 already applied.')
        return 0
    if "'test_ra12_city_info_receipts.py'" not in read(pq):
        refuse('RA12 (apply_ra12_city_info_receipts.py) is not applied - this round registers after it.')
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
        print('RA13 --check: %d file(s) would change, none written; %d '
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
    print('RA13 applied - the trip tabs: icons, short names on the phone. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
