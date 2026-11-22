# -*- coding: utf-8 -*-
"""apply_ra11_category_icons.py - round RA11, 22 Nov 2026.

RELEASE RA11 - AN ICON FOR EACH KIND OF THING TO DO.

    Demetri, 22 Nov: "Can we create an icon for each type of Things to Do
    category ... place that Icon on the top right of each Things to Do
    suggestion", "could we also show the icon, next to the category
    name" - "That's great. Build it."

    - travel/_idea_icon.html (new): one icon a category, drawn (the phone
      app has no icon font offline): star, palette, tree, signpost,
      columns, binoculars, basket, church, route, knife and fork,
      cup; a pin for Other.
    - Each suggestion has its icon at the top right (named on hover) -
      greyed with the card in Outside what you asked for - and each
      category heading has it beside the name. Computer and phone.
    - Help on the computer and the phone; the phone app moves to tv24-1.
    - No migration.

The suite and the icon template ship beside this patcher. Stands on RA10.
Idempotent. Edits backed up to .bak_ra11.
"""
import os
import sys

SUFFIX = '.bak_ra11'
MARK = 'RA11, 22 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra11_category_icons.py',
    'travel/templates/travel/_idea_icon.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra09_google_allowance.py',
    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    'test_ra10_google_checks.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra09_google_allowance.py',
    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    'test_ra10_google_checks.py',
    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    'test_ra11_category_icons.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    '.bak_ra10',
]

''',
         r'''    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    '.bak_ra10',
    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    '.bak_ra11',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. These go in their own section at the end of the city, <strong>Outside what you asked for</strong> (with how many), closed to start &ndash; click it to open; inside they are grouped by why (further from the centre, closed on your days, temporarily closed). They can still be ticked and added, the section opens by itself when one in it is ticked, and <strong>Show me more</strong> counts them like the rest (its line says how many of the new ones are outside). Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden &ndash; a place that comes back is not checked on Google again: what Google said is kept, and only its distance is measured against your new km, so only the new ones use Google checks. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
    <p data-help-gquota><strong>Google checks left.</strong> Each suggestion checked on Google (opening days, distance, rating, price) is one Google search, and so is finding each city&rsquo;s centre &ndash; about 33 for one city with sights, Restaurants and Caf&eacute;s. Google caps the key&rsquo;s project at 100 a day, so Alivente keeps its own <strong>monthly</strong> allowance too (1,000 to start &ndash; about Google&rsquo;s free amount): the Suggest page shows what is left this month and today. When either is used up, suggestions still come, just not checked on Google, until tomorrow or the 1st. Those waiting are <strong>checked automatically the next morning</strong> (after 10:00, when Google&rsquo;s day starts, using at most half of the day&rsquo;s allowance, trips starting soonest first), or straight away with <strong>Check them now</strong> on the suggestions page when there is allowance left. You get one email when 80% of the month is used. A superuser changes the numbers under <strong>Change the allowance</strong> on that page (Travel &rsaquo; Google allowance), which also shows <strong>Who used them</strong>: every check today and this month by person, what for (Suggest things to do, Show me more, Check them now, the morning catch-up, the key check) and trip &ndash; <em>Alivente itself</em> is the morning catch-up and the key check. A suggestion Google cannot find at all says <strong>Not found on Google &ndash; check the name and place yourself</strong> in grey; it is not greyed out, can still be ticked, and is not checked again. Nothing else in Alivente uses Google searches &ndash; not the weather, nor bookings, nor looking up hotels.</p>
  </article>
''',
         r'''    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. Each suggestion has its category&rsquo;s icon at the top right, and the same icon is beside the category heading (hover over it for the name): a star for must-sees, a palette for museums and galleries, a tree for parks and nature, a signpost for neighbourhoods and streets, columns for architecture, binoculars for viewpoints, a basket for markets and shopping, a church for churches and historic sites, a route for day trips, a knife and fork for restaurants and a cup for caf&eacute;s. Those outside what you asked for go in their own section at the end of the city, <strong>Outside what you asked for</strong> (with how many), closed to start &ndash; click it to open; inside they are grouped by why (further from the centre, closed on your days, temporarily closed). They can still be ticked and added, the section opens by itself when one in it is ticked, and <strong>Show me more</strong> counts them like the rest (its line says how many of the new ones are outside). Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden &ndash; a place that comes back is not checked on Google again: what Google said is kept, and only its distance is measured against your new km, so only the new ones use Google checks. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
    <p data-help-gquota><strong>Google checks left.</strong> Each suggestion checked on Google (opening days, distance, rating, price) is one Google search, and so is finding each city&rsquo;s centre &ndash; about 33 for one city with sights, Restaurants and Caf&eacute;s. Google caps the key&rsquo;s project at 100 a day, so Alivente keeps its own <strong>monthly</strong> allowance too (1,000 to start &ndash; about Google&rsquo;s free amount): the Suggest page shows what is left this month and today. When either is used up, suggestions still come, just not checked on Google, until tomorrow or the 1st. Those waiting are <strong>checked automatically the next morning</strong> (after 10:00, when Google&rsquo;s day starts, using at most half of the day&rsquo;s allowance, trips starting soonest first), or straight away with <strong>Check them now</strong> on the suggestions page when there is allowance left. You get one email when 80% of the month is used. A superuser changes the numbers under <strong>Change the allowance</strong> on that page (Travel &rsaquo; Google allowance), which also shows <strong>Who used them</strong>: every check today and this month by person, what for (Suggest things to do, Show me more, Check them now, the morning catch-up, the key check) and trip &ndash; <em>Alivente itself</em> is the morning catch-up and the key check. A suggestion Google cannot find at all says <strong>Not found on Google &ndash; check the name and place yourself</strong> in grey; it is not greyed out, can still be ticked, and is not checked again. Nothing else in Alivente uses Google searches &ndash; not the weather, nor bookings, nor looking up hotels.</p>
  </article>
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
/* RA11, 22 Nov 2026 - the category's icon: top right of each suggestion, and beside its heading. */
.tv-id-card { position: relative; }
.tv-id-card .tv-id-pick { padding-right: 34px; }
.tv-id-ico { width: 30px; height: 30px; border-radius: 50%; background: #E1F5EE; color: #085041; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.tv-id-ico svg { width: 16px; height: 16px; }
.tv-id-card > .tv-id-ico { position: absolute; top: 10px; right: 10px; }
.tv-id-card.is-dim > .tv-id-ico { background: #E6E9EB; color: #45545A; }
.tv-id-group.has-ico { display: flex; align-items: center; gap: 8px; }
.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# RA10, 21 Nov 2026 - Not found on Google; the distance note's own class;
# outside what you asked for, in its own section.
SW_VERSION = 'tv23-1'
SW_ASSETS = '1af680bf37b8'


''',
         r'''# RA10, 21 Nov 2026 - Not found on Google; the distance note's own class;
# outside what you asked for, in its own section.
# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
SW_VERSION = 'tv24-1'
SW_ASSETS = 'f8bffa7bc505'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_card.html'), [
        (r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
{% comment %} RA10, 21 Nov 2026 - Not found on Google: a grey note, not greyed out; the blue note's class is is-far (Font Awesome owns .far). {% endcomment %}
{% comment %} RA03, 19 Nov 2026 - checked on Google: greyed out (still tickable) when closed on every day you are in the city or further than your km, with why; rating, price level and distance for the ones found. {% endcomment %}<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}{% if i.flag and i.flag != 'nf' %} is-dim{% endif %}" data-idea="{{ i.pk }}"{% if i.flag %} data-idea-flag="{{ i.flag }}"{% endif %}{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
''',
         r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
{% comment %} RA11, 22 Nov 2026 - the category's icon at the top right (travel/_idea_icon.html), so each one shows what kind it is - in Outside what you asked for too. {% endcomment %}
{% comment %} RA10, 21 Nov 2026 - Not found on Google: a grey note, not greyed out; the blue note's class is is-far (Font Awesome owns .far). {% endcomment %}
{% comment %} RA03, 19 Nov 2026 - checked on Google: greyed out (still tickable) when closed on every day you are in the city or further than your km, with why; rating, price level and distance for the ones found. {% endcomment %}<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}{% if i.flag and i.flag != 'nf' %} is-dim{% endif %}" data-idea="{{ i.pk }}"{% if i.flag %} data-idea-flag="{{ i.flag }}"{% endif %}{% if i.pk == first_new %} id="new"{% endif %}>
  <span class="tv-id-ico" title="{{ i.cat }}" aria-label="{{ i.cat }}" role="img" data-idea-icon="{{ i.icon }}">{% include 'travel/_idea_icon.html' with k=i.icon %}</span>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_list.html'), [
        (r'''{% comment %} RA10, 21 Nov 2026 - what is outside what you asked for goes to its own section at the end of the city, closed to start, grouped by why (Demetri: "Let's put this in RA10. Let's start it closed for now."); open when one in it is ticked or is the first new one. {% endcomment %}
{% comment %} TR-12 - the suggestions, by city and then by what you like, inside the Add form; desk=True lays them out as a grid. {% endcomment %}
{% for g in groups %}<div class="{% if desk %}tv-id-grid{% else %}tv-id-list{% endif %}" data-idea-cityblock>
  <div class="tv-id-cityhead"><b>{{ g.city }}</b><span style="font-size: .85rem; color: #5B6B72">{{ g.n }} idea{{ g.n|pluralize }}{% if g.added %} &middot; {{ g.added }} added{% endif %}</span></div>
  {% for b in g.by %}<div class="tv-id-group">{{ b.name }}</div>
  {% for i in b.ideas %}{% include 'travel/_ideas_card.html' %}{% endfor %}{% endfor %}
  {% if g.out %}<details class="tv-id-out" data-idea-outside{% if g.out_open %} open{% endif %}><summary><b>Outside what you asked for ({{ g.n_out }})</b><span>Further than your km, closed on your days or temporarily closed &ndash; you can still tick them.</span></summary>
''',
         r'''{% comment %} RA11, 22 Nov 2026 - each category heading has its icon, the same as on its suggestions. {% endcomment %}
{% comment %} RA10, 21 Nov 2026 - what is outside what you asked for goes to its own section at the end of the city, closed to start, grouped by why (Demetri: "Let's put this in RA10. Let's start it closed for now."); open when one in it is ticked or is the first new one. {% endcomment %}
{% comment %} TR-12 - the suggestions, by city and then by what you like, inside the Add form; desk=True lays them out as a grid. {% endcomment %}
{% for g in groups %}<div class="{% if desk %}tv-id-grid{% else %}tv-id-list{% endif %}" data-idea-cityblock>
  <div class="tv-id-cityhead"><b>{{ g.city }}</b><span style="font-size: .85rem; color: #5B6B72">{{ g.n }} idea{{ g.n|pluralize }}{% if g.added %} &middot; {{ g.added }} added{% endif %}</span></div>
  {% for b in g.by %}<div class="tv-id-group has-ico" data-idea-group="{{ b.k }}"><span class="tv-id-ico" aria-hidden="true">{% include 'travel/_idea_icon.html' with k=b.k %}</span>{{ b.name }}</div>
  {% for i in b.ideas %}{% include 'travel/_ideas_card.html' %}{% endfor %}{% endfor %}
  {% if g.out %}<details class="tv-id-out" data-idea-outside{% if g.out_open %} open{% endif %}><summary><b>Outside what you asked for ({{ g.n_out }})</b><span>Further than your km, closed on your days or temporarily closed &ndash; you can still tick them.</span></summary>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
/* RA11, 22 Nov 2026 - the category's icon: top right of each suggestion, and beside its heading. */
.tv-id-card { position: relative; }
.tv-id-card .tv-id-pick { padding-right: 34px; }
.tv-id-ico { width: 30px; height: 30px; border-radius: 50%; background: #E1F5EE; color: #085041; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.tv-id-ico svg { width: 16px; height: 16px; }
.tv-id-card > .tv-id-ico { position: absolute; top: 10px; right: 10px; }
.tv-id-card.is-dim > .tv-id-ico { background: #E6E9EB; color: #45545A; }
.tv-id-group.has-ico { display: flex; align-items: center; gap: 8px; }
.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv23-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv24-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv23-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv24-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. These are kept apart at the end of the city, under <b>Outside what you asked for</b> &ndash; tap it to open. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>. One Google can&rsquo;t find at all says <b>Not found on Google</b> in grey &ndash; you can still tick it.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. These are kept apart at the end of the city, under <b>Outside what you asked for</b> &ndash; tap it to open. The round icon at the top right of each suggestion, and beside each heading, shows what kind it is &ndash; a star for must-sees, a palette for museums, a tree for parks, a signpost for streets, binoculars for viewpoints, a cup for caf&eacute;s and so on. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>. One Google can&rsquo;t find at all says <b>Not found on Google</b> in grey &ndash; you can still tick it.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
'''),
    ]),
    (os.path.join('travel', 'views_ideas.py'), [
        (r'''    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
    # RA10, 21 Nov 2026 - outside what you asked for (too far, closed on
    # your days, temporarily closed) goes to its own closed section at the
''',
         r'''    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
        # RA11, 22 Nov 2026 - the kind of thing to do, as an icon.
        i.icon = i.interest if i.interest in ID.LABEL else 'other'
        i.cat = ID.LABEL.get(i.interest, 'Other')
    # RA10, 21 Nov 2026 - outside what you asked for (too far, closed on
    # your days, temporarily closed) goes to its own closed section at the
'''),
        (r'''                k == '' and i.interest not in ID.LABEL)]
            if these:
                by.append({'name': n, 'ideas': these})
        out = []                        # RA10 - grouped by why
        for f, n in OUTSIDE.items():
''',
         r'''                k == '' and i.interest not in ID.LABEL)]
            if these:
                by.append({'name': n, 'ideas': these, 'k': k or 'other'})
        out = []                        # RA10 - grouped by why
        for f, n in OUTSIDE.items():
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
    raise SystemExit('RA11 REFUSED: %s' % msg)


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
    if "'test_ra11_category_icons.py'" in read(pq):
        print('RA11 already applied.')
        return 0
    if "'test_ra10_google_checks.py'" not in read(pq):
        refuse('RA10 (apply_ra10_google_checks.py) is not applied - this round registers after it.')
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
        print('RA11 --check: %d file(s) would change, none written; %d '
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
    print('RA11 applied - an icon for each kind of thing to do. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
