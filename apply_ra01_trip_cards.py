# -*- coding: utf-8 -*-
"""apply_ra01_trip_cards.py - round RA01, 18 Nov 2026.

RELEASE RA01 (the first of the new numbering, after R100) - TRAVEL:
COMPARE IN THE TRIP CARD, PROPER DROP-DOWNS.

    Demetri, 18 Nov: "How better can better do the Compare tickboxes?
    Make it look better. Can it be in the trip box? I don't like how the
    Country dropdown looks. The year dropdown doesn't have any values? It
    had the two years just a little while back."

    - Compare moves into each trip card's own footer: a styled tick, the
      card outlined when ticked, and the Compare button counts them.
    - Year and Country open our own drop-down from anywhere on the chip
      (the browser's list only opened on its own small text, so pressing
      the chip looked empty), each choice with its number of trips; one
      open at a time, Escape or a press elsewhere closes it. The phone the
      same.
    - Help says so; the phone app's version moves (tv17-1).

The suite ships beside this patcher. Stands on TR-16
(apply_travel_sixteen.py). Idempotent. Edits backed up to .bak_ra01. No
migration.
"""
import os
import sys

SUFFIX = '.bak_ra01'
MARK = 'RA01, 18 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra01_trip_cards.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_recipe_units_null.py',
    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    'test_travel_sixteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_recipe_units_null.py',
    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    'test_travel_sixteen.py',
    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    'test_ra01_trip_cards.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    '.bak_travel16',
]

''',
         r'''    # TR-16, 18 Nov 2026 - Release 100: tidier trip filters.
    '.bak_travel16',
    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    '.bak_ra01',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Across the top are <strong>All</strong>, <strong>Upcoming</strong> and <strong>Past</strong>, each with its number of trips in a small grey badge, then two menus: <strong>Year</strong> (newest first) and <strong>Country</strong> (the countries you go to most at the top). Pick a year or a country and it becomes a highlighted chip &mdash; press its &#x2715; to clear it. They combine: Past, 2026 and Greece shows the past trips of 2026 in Greece, and the numbers in the badges follow what you picked. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Each trip also has an <strong>Itinerary</strong> and <strong>Things to do</strong> &mdash; see <strong>Itinerary &amp; Places</strong>.</p>
''',
         r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Across the top are <strong>All</strong>, <strong>Upcoming</strong> and <strong>Past</strong>, each with its number of trips in a small grey badge, then two menus: <strong>Year</strong> (newest first) and <strong>Country</strong> (the countries you go to most at the top) &mdash; press either and its list opens, each choice with its number of trips. Pick a year or a country and it becomes a highlighted chip &mdash; press its &#x2715; to clear it. They combine: Past, 2026 and Greece shows the past trips of 2026 in Greece, and the numbers in the badges follow what you picked. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> at the foot of two or more trip cards &mdash; a ticked card is outlined, and the button counts them &mdash; and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
    <p><strong>On your phone</strong>, Travel is an app of its own &mdash; see the <strong>Phone app</strong> tab. Each trip also has an <strong>Itinerary</strong> and <strong>Things to do</strong> &mdash; see <strong>Itinerary &amp; Places</strong>.</p>
'''),
    ]),
    (os.path.join('test_travel_sixteen.py'), [
        (r'''   '  styled on the computer and the phone')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv16-1'" in ph and
   read(J(TT, 'm', 'base.html')).count('?v=tv16-1') == 2,
   'THE PHONE APP fetches the new look (tv16-1)')
try:
    ok('Upcoming <span class="tv-sub">' in was(J(TT, 'trips.html')),
''',
         r'''   '  styled on the computer and the phone')
ph = read(J(TA, 'phone.py'))
# RA01, 18 Nov 2026 - tv16-1 or later (it moves with every new look).
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 16 and
   read(J(TT, 'm', 'base.html')).count('?v=tv%s-%s' % _v.groups()) == 2,
   'THE PHONE APP fetches the new look (tv16-1 or later)')
try:
    ok('Upcoming <span class="tv-sub">' in was(J(TT, 'trips.html')),
'''),
        (r'''            ok('data-trip-filters' in h and
               'All <span class="tv-count" aria-label="3 trips">3</span>' in h
               and 'name="year"' in h and 'name="country"' in h,
               'THE COMPUTER: All 3 in a badge, and the two menus')
            ok('<option value="Greece">Greece (2)</option>' in h,
               '  Greece first in the Country menu, with its 2 trips')
            h = A.get('/travel/?view=list&show=past&country=Greece'
''',
         r'''            ok('data-trip-filters' in h and
               'All <span class="tv-count" aria-label="3 trips">3</span>' in h
               and 'data-menu="year"' in h and 'data-menu="country"' in h,
               'THE COMPUTER: All 3 in a badge, and the two menus')
            # RA01 - our own drop-down: Greece first, with its count.
            pop = h.split('data-pop="country"')[1].split('</div></details>')[0]
            ok(pop.index('Greece') < pop.index('Turkey') and
               'country=Greece">Greece <span class="tv-count" '
               'aria-label="2 trips">2</span>' in pop,
               '  Greece first in the Country menu, with its 2 trips')
            h = A.get('/travel/?view=list&show=past&country=Greece'
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-chip.on .tv-count { background: rgba(255, 255, 255, .28); color: #fff; }
.tv-fsep { width: 1px; height: 22px; background: #C9D3D6; margin: 0 2px; align-self: center; }
.tv-menu { display: inline-flex; margin: 0; }
.tv-menu-chip { position: relative; padding-right: 28px; }
.tv-menu-chip select { appearance: none; -webkit-appearance: none; border: 0; background: transparent; color: inherit; font: inherit; padding: 0; min-height: 34px; }
.tv-menu-chip::after { content: ""; position: absolute; right: 12px; top: 50%; width: 6px; height: 6px; border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: translateY(-70%) rotate(45deg); pointer-events: none; }
.tv-picked { border: 1.5px solid var(--tv-teal); color: var(--tv-teal); font-weight: 600; }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
''',
         r'''.tv-chip.on .tv-count { background: rgba(255, 255, 255, .28); color: #fff; }
.tv-fsep { width: 1px; height: 22px; background: #C9D3D6; margin: 0 2px; align-self: center; }
/* RA01, 18 Nov 2026 - our own drop-downs for Year and Country. */
.tv-dd { position: relative; display: inline-flex; }
.tv-dd > summary { list-style: none; cursor: pointer; -webkit-user-select: none; user-select: none; }
.tv-dd > summary::-webkit-details-marker { display: none; }
.tv-menu-chip { position: relative; padding-right: 28px; }
.tv-menu-chip::after { content: ""; position: absolute; right: 12px; top: 50%; width: 6px; height: 6px; border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: translateY(-70%) rotate(45deg); }
.tv-dd[open] > .tv-menu-chip { border-color: var(--tv-teal); color: var(--tv-teal); }
.tv-dd[open] > .tv-menu-chip::after { transform: translateY(-25%) rotate(225deg); }
.tv-pop { position: absolute; top: calc(100% + 6px); left: 0; z-index: 30; min-width: 200px; max-height: 60vh; overflow-y: auto; padding: 6px; background: #fff; border: 1px solid var(--tv-line); border-radius: 14px; box-shadow: 0 12px 30px rgba(0, 0, 0, .16); }
.tv-dd[data-menu="country"] .tv-pop { left: auto; right: 0; }
.tv-pop-h { padding: 6px 10px 4px; font-size: 11px; font-weight: 600; letter-spacing: .03em; text-transform: uppercase; color: var(--tv-soft); }
.tv-pop a { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 44px; padding: 0 10px; border-radius: 10px; color: var(--tv-ink); text-decoration: none; font-size: 15px; }
.tv-pop a:active, .tv-pop a:hover { background: rgba(15, 116, 128, .08); color: var(--tv-teal); }
.tv-picked { border: 1.5px solid var(--tv-teal); color: var(--tv-teal); font-weight: 600; }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
'''),
        (r'''html.tv-turn-90 body.tv-holding .tv-nav, html.tv-turn-270 body.tv-holding .tv-nav { position: sticky; }
@media (prefers-color-scheme: dark) {
  .tv-count { background: rgba(255, 255, 255, .12); color: #C9D3D6; }
  .tv-picked { border-color: #5FC3CC; color: #5FC3CC; }
''',
         r'''html.tv-turn-90 body.tv-holding .tv-nav, html.tv-turn-270 body.tv-holding .tv-nav { position: sticky; }
@media (prefers-color-scheme: dark) {
  .tv-pop { background: #1A2428; border-color: #2B383D; }
  .tv-pop a { color: #E6ECEE; }
  .tv-count { background: rgba(255, 255, 255, .12); color: #C9D3D6; }
  .tv-picked { border-color: #5FC3CC; color: #5FC3CC; }
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# they change and it does not.
# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
SW_VERSION = 'tv16-1'
SW_ASSETS = '37ece7f3cd8d'


''',
         r'''# they change and it does not.
# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
# RA01, 18 Nov 2026 - their drop-downs.
SW_VERSION = 'tv17-1'
SW_ASSETS = '07328398c1b2'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-chip.is-on .tv-count { background: var(--alv-accent); color: #fff; }
.tv-fsep { width: 1px; height: 24px; background: var(--alv-line); margin: 0 4px; align-self: center; }
.tv-menu { display: inline-flex; margin: 0; }
.tv-menu-chip { position: relative; cursor: pointer; padding-right: 30px; color: var(--alv-ink-soft); }
.tv-menu-chip select { appearance: none; -webkit-appearance: none; border: 0; background: transparent; color: var(--alv-ink); font: inherit; padding: 0; cursor: pointer; min-height: 34px; }
.tv-menu-chip::after { content: ""; position: absolute; right: 13px; top: 50%; width: 7px; height: 7px; border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: translateY(-70%) rotate(45deg); pointer-events: none; }
.tv-menu-chip:focus-within { border-color: var(--alv-accent); box-shadow: 0 0 0 2px rgba(14, 124, 139, .2); }
.tv-picked { border: 1.5px solid var(--alv-accent); background: rgba(14, 124, 139, .08); color: var(--alv-accent); font-weight: 700; }
.tv-picked .tv-x { font-size: 0.8rem; }
''',
         r'''.tv-chip.is-on .tv-count { background: var(--alv-accent); color: #fff; }
.tv-fsep { width: 1px; height: 24px; background: var(--alv-line); margin: 0 4px; align-self: center; }
.tv-dd { position: relative; display: inline-flex; }
.tv-dd > summary { list-style: none; cursor: pointer; user-select: none; }
.tv-dd > summary::-webkit-details-marker { display: none; }
.tv-menu-chip { position: relative; padding-right: 30px; color: var(--alv-ink); }
.tv-menu-chip svg { color: var(--alv-ink-soft); }
.tv-menu-chip::after { content: ""; position: absolute; right: 13px; top: 50%; width: 7px; height: 7px; border-right: 1.5px solid var(--alv-ink-soft); border-bottom: 1.5px solid var(--alv-ink-soft); transform: translateY(-70%) rotate(45deg); transition: transform .15s; }
.tv-dd[open] > .tv-menu-chip { border-color: var(--alv-accent); color: var(--alv-accent); }
.tv-dd[open] > .tv-menu-chip::after { transform: translateY(-25%) rotate(225deg); }
.tv-menu-chip:focus-visible { outline: 2px solid var(--alv-accent); outline-offset: 2px; }
.tv-pop { position: absolute; top: calc(100% + 6px); left: 0; z-index: 30; min-width: 230px; max-height: 340px; overflow-y: auto; padding: 6px; background: #fff; border: 1px solid var(--alv-line); border-radius: 12px; box-shadow: 0 10px 28px rgba(0, 0, 0, .12); }
.tv-pop-h { padding: 6px 10px 4px; font-size: 0.75rem; font-weight: 600; letter-spacing: .02em; text-transform: uppercase; color: var(--alv-ink-soft); }
.tv-pop a { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 40px; padding: 0 10px; border-radius: 8px; color: var(--alv-ink); text-decoration: none; }
.tv-pop a:hover, .tv-pop a:focus-visible { background: rgba(14, 124, 139, .08); color: var(--alv-accent); text-decoration: none; outline: none; }
.tv-picked { border: 1.5px solid var(--alv-accent); background: rgba(14, 124, 139, .08); color: var(--alv-accent); font-weight: 700; }
.tv-picked .tv-x { font-size: 0.8rem; }
'''),
        (r'''.tv-steps { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 6px; }
@media screen and (max-width: 575.98px) { .tv-phone.tv-phone-wide { grid-template-columns: 1fr !important; } }
.tv-pickcard { display: flex; flex-direction: column; gap: 6px; }
.tv-pickcard > .tv-card { flex: 1; }
.tv-pick { display: inline-flex; align-items: center; gap: 8px; min-height: 32px; margin: 0; padding-left: 4px; cursor: pointer; }
.tv-pick input { width: 18px; height: 18px; }
.tv-pasttag { color: var(--alv-ink-soft); }
.tv-note { padding: 10px 14px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); background: var(--alv-surface); }
''',
         r'''.tv-steps { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 6px; }
@media screen and (max-width: 575.98px) { .tv-phone.tv-phone-wide { grid-template-columns: 1fr !important; } }
.tv-pick { display: inline-flex; align-items: center; gap: 8px; min-height: 32px; margin: 0; padding-left: 4px; cursor: pointer; }
.tv-pick input { width: 18px; height: 18px; }
/* RA01, 18 Nov 2026 (Demetri: "How better can better do the Compare tickboxes? Make it look better. Can it be in the trip box?") - the tick sits in the card's own footer; a ticked card takes the accent. */
.tv-pickcard { display: flex; flex-direction: column; padding: 0; margin: 0; overflow: hidden; transition: border-color .15s, box-shadow .15s; }
.tv-pickcard:hover { border-color: var(--alv-accent); }
.tv-pickcard > .tv-card { flex: 1; border: 0; border-radius: 0; background: transparent; }
.tv-pickcard > a.tv-card:hover { border: 0; }
.tv-pickcard .tv-pick { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 44px; margin: 0; padding: 0 16px; border-top: 1px solid var(--alv-line); cursor: pointer; color: var(--alv-ink-soft); font-size: 0.85rem; user-select: none; }
.tv-pickcard .tv-pick:hover { color: var(--alv-accent); background: rgba(14, 124, 139, .04); }
.tv-pickcard .tv-pick input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-pickcard .tv-tick { width: 20px; height: 20px; border-radius: 6px; border: 1.5px solid var(--alv-line); background: #fff; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.tv-pickcard .tv-tick svg { opacity: 0; }
.tv-pickcard .tv-pick input:checked ~ .tv-tick { background: var(--alv-accent); border-color: var(--alv-accent); }
.tv-pickcard .tv-pick input:checked ~ .tv-tick svg { opacity: 1; }
.tv-pickcard .tv-pick input:focus-visible ~ .tv-tick { outline: 2px solid var(--alv-accent); outline-offset: 2px; }
.tv-pickcard:has(input:checked) { border-color: var(--alv-accent); box-shadow: 0 0 0 2px rgba(14, 124, 139, .25), 0 4px 12px rgba(0, 0, 0, .06); }
.tv-pickcard:has(input:checked) .tv-pick { color: var(--alv-accent); font-weight: 600; background: rgba(14, 124, 139, .06); }
.tv-pickcard .tv-pick-on { display: none; }
.tv-pickcard:has(input:checked) .tv-pick-on { display: inline; }
.tv-pickcard:has(input:checked) .tv-pick-off { display: none; }
.tv-cmpbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 12px; }
.tv-cmpbar .btn[disabled] { opacity: .55; }
.tv-pasttag { color: var(--alv-ink-soft); }
.tv-note { padding: 10px 14px; border-radius: var(--alv-radius); border: 1px solid var(--alv-line); background: var(--alv-surface); }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_trip_filters.html'), [
        (r'''{% comment %} TR-16, 18 Nov 2026 (Demetri: "I don't like how the 1 is placed near the Upcoming and the Past ... Can we put the "All" first on the left ... Is there not a cleverer way to do years and countries?"). All, Upcoming and Past as chips with their counts as badges, then Year and Country as menus; picked, a menu becomes a chip with an x that clears it. They combine. Used by the computer (on="is-on") and the phone (on="on"). {% endcomment %}
<nav class="tv-chips tv-filters" aria-label="Show" data-trip-filters>
    <a class="tv-chip{% if F.show == 'all' %} {{ on }}{% endif %}" href="{{ F.link_all }}" data-chip="all"{% if F.show == 'all' %} aria-current="page"{% endif %}>All <span class="tv-count" aria-label="{{ F.n_all }} trip{{ F.n_all|pluralize }}">{{ F.n_all }}</span></a>
    <a class="tv-chip{% if F.show == 'upcoming' and not F.auto_past %} {{ on }}{% endif %}" href="{{ F.link_upcoming }}" data-chip="upcoming"{% if F.show == 'upcoming' and not F.auto_past %} aria-current="page"{% endif %}>Upcoming <span class="tv-count" aria-label="{{ F.n_upcoming }} trip{{ F.n_upcoming|pluralize }}">{{ F.n_upcoming }}</span></a>
    <a class="tv-chip{% if F.show == 'past' or F.auto_past %} {{ on }}{% endif %}" href="{{ F.link_past }}" data-chip="past"{% if F.show == 'past' or F.auto_past %} aria-current="page"{% endif %}>Past <span class="tv-count" aria-label="{{ F.n_past }} trip{{ F.n_past|pluralize }}">{{ F.n_past }}</span></a>
    {% if F.years or F.countries %}<span class="tv-fsep" aria-hidden="true"></span>{% endif %}
    {% if F.year %}<a class="tv-chip tv-picked" href="{{ F.clear_year }}" data-picked="year" title="Show every year">{{ F.year }} <span class="tv-x" aria-hidden="true">&#x2715;</span><span class="tv-sr"> - clear the year</span></a>
    {% elif F.years %}<form method="get" class="tv-menu" data-menu="year"><input type="hidden" name="show" value="{{ F.show }}">{% if F.country %}<input type="hidden" name="country" value="{{ F.country }}">{% endif %}<label class="tv-chip tv-menu-chip"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="11" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M2 6.5h12M5.5 1.5v3M10.5 1.5v3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg><select name="year" aria-label="Year" onchange="this.form.submit()"><option value="">Any year</option>{% for y, n in F.years %}<option value="{{ y }}">{{ y }} ({{ n }})</option>{% endfor %}</select></label><noscript><button type="submit" class="tv-chip">Go</button></noscript></form>{% endif %}
    {% if F.country %}<a class="tv-chip tv-picked" href="{{ F.clear_country }}" data-picked="country" title="Show every country">{{ F.country_name }} <span class="tv-x" aria-hidden="true">&#x2715;</span><span class="tv-sr"> - clear the country</span></a>
    {% elif F.countries %}<form method="get" class="tv-menu" data-menu="country"><input type="hidden" name="show" value="{{ F.show }}">{% if F.year %}<input type="hidden" name="year" value="{{ F.year }}">{% endif %}<label class="tv-chip tv-menu-chip"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1.8 8h12.4M8 1.8c-2.2 2.4-2.2 10 0 12.4M8 1.8c2.2 2.4 2.2 10 0 12.4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg><select name="country" aria-label="Country" onchange="this.form.submit()"><option value="">Any country</option>{% for c, n in F.countries %}<option value="{{ c }}">{{ c }} ({{ n }})</option>{% endfor %}</select></label><noscript><button type="submit" class="tv-chip">Go</button></noscript></form>{% endif %}
</nav>
''',
         r'''{% comment %} TR-16, 18 Nov 2026 (Demetri: "I don't like how the 1 is placed near the Upcoming and the Past ... Can we put the "All" first on the left ... Is there not a cleverer way to do years and countries?"). All, Upcoming and Past as chips with their counts as badges, then Year and Country menus; picked, a menu becomes a chip with an x that clears it. They combine. Used by the computer (on="is-on") and the phone (on="on").
RA01, 18 Nov 2026 (Demetri: "I don't like how the Country dropdown looks. The year dropdown doesn't have any values?"): the browser's own list is gone - pressing the chip anywhere opens our own drop-down, each choice with its count, styled like the rest. {% endcomment %}
<nav class="tv-chips tv-filters" aria-label="Show" data-trip-filters>
    <a class="tv-chip{% if F.show == 'all' %} {{ on }}{% endif %}" href="{{ F.link_all }}" data-chip="all"{% if F.show == 'all' %} aria-current="page"{% endif %}>All <span class="tv-count" aria-label="{{ F.n_all }} trip{{ F.n_all|pluralize }}">{{ F.n_all }}</span></a>
    <a class="tv-chip{% if F.show == 'upcoming' and not F.auto_past %} {{ on }}{% endif %}" href="{{ F.link_upcoming }}" data-chip="upcoming"{% if F.show == 'upcoming' and not F.auto_past %} aria-current="page"{% endif %}>Upcoming <span class="tv-count" aria-label="{{ F.n_upcoming }} trip{{ F.n_upcoming|pluralize }}">{{ F.n_upcoming }}</span></a>
    <a class="tv-chip{% if F.show == 'past' or F.auto_past %} {{ on }}{% endif %}" href="{{ F.link_past }}" data-chip="past"{% if F.show == 'past' or F.auto_past %} aria-current="page"{% endif %}>Past <span class="tv-count" aria-label="{{ F.n_past }} trip{{ F.n_past|pluralize }}">{{ F.n_past }}</span></a>
    {% if F.years or F.countries %}<span class="tv-fsep" aria-hidden="true"></span>{% endif %}
    {% if F.year %}<a class="tv-chip tv-picked" href="{{ F.clear_year }}" data-picked="year" title="Show every year">{{ F.year }} <span class="tv-x" aria-hidden="true">&#x2715;</span><span class="tv-sr"> - clear the year</span></a>
    {% elif F.year_menu %}<details class="tv-dd" data-menu="year"><summary class="tv-chip tv-menu-chip"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="11" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M2 6.5h12M5.5 1.5v3M10.5 1.5v3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg> Any year</summary><div class="tv-pop" data-pop="year"><div class="tv-pop-h">Year</div>{% for o in F.year_menu %}<a href="{{ o.url }}">{{ o.label }} <span class="tv-count" aria-label="{{ o.n }} trip{{ o.n|pluralize }}">{{ o.n }}</span></a>{% endfor %}</div></details>{% endif %}
    {% if F.country %}<a class="tv-chip tv-picked" href="{{ F.clear_country }}" data-picked="country" title="Show every country">{{ F.country_name }} <span class="tv-x" aria-hidden="true">&#x2715;</span><span class="tv-sr"> - clear the country</span></a>
    {% elif F.country_menu %}<details class="tv-dd" data-menu="country"><summary class="tv-chip tv-menu-chip"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1.8 8h12.4M8 1.8c-2.2 2.4-2.2 10 0 12.4M8 1.8c2.2 2.4 2.2 10 0 12.4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg> Any country</summary><div class="tv-pop" data-pop="country"><div class="tv-pop-h">Country</div>{% for o in F.country_menu %}<a href="{{ o.url }}">{{ o.label }} <span class="tv-count" aria-label="{{ o.n }} trip{{ o.n|pluralize }}">{{ o.n }}</span></a>{% endfor %}</div></details>{% endif %}
</nav>
<script>
/* RA01 - one drop-down open at a time; a press anywhere else, or Escape, closes it. */
(function () {
  if (window.tvDdBound) return; window.tvDdBound = true;
  function shut(except) { document.querySelectorAll('details.tv-dd[open]').forEach(function (d) { if (d !== except) d.removeAttribute('open'); }); }
  document.addEventListener('click', function (e) { var d = e.target.closest && e.target.closest('details.tv-dd'); shut(d); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') shut(null); });
})();
</script>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv16-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv17-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv16-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv17-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''{% comment %} TR-7, 16 Nov 2026 (Demetri: "If there are not upcoming, then it must show the past ones in descending date order (highlighting that they are Past)"; "I must be able to multi select trips for comparison"). {% endcomment %}
{% if auto_past %}<p class="tv-note" data-auto-past>Nothing coming up{% if F.year or F.country %} here{% endif %} &mdash; here are your <b>past trips</b>, newest first.</p>{% endif %}
{% if count > 1 %}<form method="get" action="{% url 'travel:compare' %}" id="tv-compare" class="tv-row" style="margin: 0 0 12px; align-items: center" data-compare-form><span class="tv-sub">Tick two or more trips to compare their costs.</span><button type="submit" class="btn action-secondary btn-sm" title="Compare the ticked trips side by side"><i class="fas fa-balance-scale"></i> Compare ticked trips</button></form>{% endif %}
<div class="tv-grid" data-trips>
{% for t in trips %}
    <div class="tv-pickcard">
    <a class="tv-card form-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p><span>{% if t.past %}<span class="tv-tag tv-pasttag" data-past>Past</span> {% endif %}{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</span></div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
''',
         r'''{% comment %} TR-7, 16 Nov 2026 (Demetri: "If there are not upcoming, then it must show the past ones in descending date order (highlighting that they are Past)"; "I must be able to multi select trips for comparison"). {% endcomment %}
{% if auto_past %}<p class="tv-note" data-auto-past>Nothing coming up{% if F.year or F.country %} here{% endif %} &mdash; here are your <b>past trips</b>, newest first.</p>{% endif %}
{% if count > 1 %}<form method="get" action="{% url 'travel:compare' %}" id="tv-compare" class="tv-cmpbar" data-compare-form><span class="tv-sub" data-compare-hint>Tick <b>Compare</b> on two or more trips to see their costs side by side.</span><button type="submit" class="btn action-secondary btn-sm" title="Compare the ticked trips side by side"><i class="fas fa-balance-scale"></i> Compare ticked trips <span class="tv-count" data-compare-n hidden>0</span></button></form>{% endif %}
<div class="tv-grid" data-trips>
{% for t in trips %}
    <div class="tv-pickcard form-card">
    <a class="tv-card" href="{% url 'travel:trip' t.pk %}" data-trip>
        <div class="tv-row"><p class="tv-name">{{ t.name }}</p><span>{% if t.past %}<span class="tv-tag tv-pasttag" data-past>Past</span> {% endif %}{% if t.shared_with.all or not t.mine %}<span class="tv-tag tv-shared"><i class="fas fa-share-alt" aria-hidden="true"></i> Shared</span>{% endif %}</span></div>
        <div class="tv-sub">{% if t.start %}{{ t.start|date:"j M" }}{% if t.end and t.end != t.start %} – {{ t.end|date:"j M Y" }}{% else %} {{ t.start|date:"Y" }}{% endif %}{% else %}No dates yet{% endif %}{% if t.where %} · {{ t.where }}{% endif %}</div>
'''),
        (r'''        {% if t.owing %}<div class="small tv-due" data-owing><b>{{ t.owing }} still To pay</b> &middot; settle up on the trip</div>{% endif %}
    </a>
    {% if count > 1 %}<label class="tv-pick small"><input type="checkbox" name="t" value="{{ t.pk }}" form="tv-compare"> Compare</label>{% endif %}
    </div>
{% empty %}
    <p class="text-muted">{% if count %}No trips match these filters. <a href="?show=all">Show all trips</a>{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>
{% endif %}{% endif %}

''',
         r'''        {% if t.owing %}<div class="small tv-due" data-owing><b>{{ t.owing }} still To pay</b> &middot; settle up on the trip</div>{% endif %}
    </a>
    {% comment %} RA01, 18 Nov 2026 - Compare lives in the card's own footer. {% endcomment %}
    {% if count > 1 %}<label class="tv-pick" data-compare-pick><span><i class="fas fa-balance-scale" aria-hidden="true"></i> <span class="tv-pick-off">Compare</span><span class="tv-pick-on">Ticked to compare</span></span><input type="checkbox" name="t" value="{{ t.pk }}" form="tv-compare" aria-label="Compare {{ t.name }}"><span class="tv-tick" aria-hidden="true"><svg width="12" height="12" viewBox="0 0 12 12"><path d="M2.5 6.2l2.3 2.3 4.7-5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span></label>{% endif %}
    </div>
{% empty %}
    <p class="text-muted">{% if count %}No trips match these filters. <a href="?show=all">Show all trips</a>{% else %}No trips yet. Start one above, or forward a booking email.{% endif %}</p>
{% endfor %}
</div>
{% if count > 1 %}<script>
/* RA01 - the Compare button counts the ticked trips. */
(function () {
  var n = document.querySelector('[data-compare-n]');
  function count() { var k = document.querySelectorAll('input[form="tv-compare"]:checked').length; n.textContent = k; n.hidden = !k; }
  document.addEventListener('change', function (e) { if (e.target.matches && e.target.matches('input[form="tv-compare"]')) count(); });
  count();
})();
</script>{% endif %}
{% endif %}{% endif %}

'''),
    ]),
    (os.path.join('travel', 'trip_filter.py'), [
        (r'''# -*- coding: utf-8 -*-
"""travel/trip_filter.py - TR-16, 18 Nov 2026. The trip list's filters, on
the computer and the phone alike.

''',
         r'''# -*- coding: utf-8 -*-
"""travel/trip_filter.py - TR-16, 18 Nov 2026 (RA01 the same day: the
menus became our own drop-downs). The trip list's filters, on
the computer and the phone alike.

'''),
        (r'''                      sorted(countries.items(),
                             key=lambda kv: (-kv[1], names[kv[0]]))],
        'link_all': link(show='all'),
        'link_upcoming': link(show='upcoming'),
''',
         r'''                      sorted(countries.items(),
                             key=lambda kv: (-kv[1], names[kv[0]]))],
        # RA01, 18 Nov 2026 - the menus are our own drop-downs now, each
        # choice a link that keeps the other picks.
        'year_menu': [{'label': str(y), 'n': years[y],
                       'url': link(year=str(y))}
                      for y in sorted(years, reverse=True)],
        'country_menu': [{'label': names[k], 'n': n,
                          'url': link(country=names[k])} for k, n in
                         sorted(countries.items(),
                                key=lambda kv: (-kv[1], names[kv[0]]))],
        'link_all': link(show='all'),
        'link_upcoming': link(show='upcoming'),
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
    raise SystemExit('RA01 REFUSED: %s' % msg)


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
    if "'test_ra01_trip_cards.py'" in read(pq):
        print('RA01 already applied.')
        return 0
    if "'test_travel_sixteen.py'" not in read(pq):
        refuse('TR-16 (apply_travel_sixteen.py, Release 100) is not applied - this round registers after it.')
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
        print('RA01 --check: %d file(s) would change, none written; %d '
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
    print('RA01 applied - Compare in the trip card, proper drop-downs.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
