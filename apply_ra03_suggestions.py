# -*- coding: utf-8 -*-
"""apply_ra03_suggestions.py - round RA03, 19 Nov 2026.

RELEASE RA03 - TRAVEL: RESTAURANTS AND CAFES; EVERY SUGGESTION CHECKED ON
GOOGLE AND GREYED OUT WHEN YOU CANNOT GO; SELECT AND DELETE SEVERAL
THINGS TO DO. Pushed together with RA02.

    Demetri, 19 Nov: "I need two new categories - 1. Cafes and 2.
    Restaurants ... from a list of top 10 restaurants or top 10 cafes";
    "closed or unavailable on a Tuesday should display, but should be
    greyed out"; "how many km from the city centre ... must be greyed out
    ... All greyed out things to do should still be selectable"; and:
    check on Google; from the city centre; day trips never limited but
    greyed out past the km; greyed only when every day is closed; ten of
    each with rating and price; Show me more counts the grey ones; "if I
    wanted to do a multi-select and delete of the things to do".

    - Restaurants and Cafes, asked for on their own: the city's top ten.
    - How far from the centre? (km) before searching.
    - travel/gplaces.py: Google Places API (New), GOOGLE_PLACES_KEY on
      Railway; never from a test. Closed for good left out; greyed out
      (still tickable, last in their group) when closed every day you are
      there, temporarily closed, or past your km; rating, price level and
      distance shown.
    - Things to do: Select, tick, Delete (asks first); computer and phone.
    - Help on the computer and the phone; the phone app moves to tv18-1.
    - Migration travel 0011: run python manage.py migrate locally first.

The suite, gplaces.py, the migration and _wish_select.html ship beside
this patcher. Stands on RA02. Idempotent. Edits backed up to .bak_ra03.
"""
import os
import sys

SUFFIX = '.bak_ra03'
MARK = 'RA03, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra03_suggestions.py',
    'travel/gplaces.py',
    'travel/migrations/0011_idea_google.py',
    'travel/templates/travel/_wish_select.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra01_trip_cards.py',
    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    'test_ra02_travel_more.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra01_trip_cards.py',
    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    'test_ra02_travel_more.py',
    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google;
    # Select and Delete.
    'test_ra03_suggestions.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    '.bak_ra02',
]

''',
         r'''    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    '.bak_ra02',
    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google.
    '.bak_ra03',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

''',
         r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. Greyed-out cards can still be ticked and added; they sit at the bottom of their group, and <strong>Show me more</strong> counts them like the rest. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

'''),
    ]),
    (os.path.join('test_ra01_trip_cards.py'), [
        (r'''   'own visible boxes')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv17-1'" in ph and
   read(J(TT, 'm', 'base.html')).count('?v=tv17-1') == 2,
   'THE PHONE APP fetches the new look (tv17-1)')
try:
    ok('<select name="year"' in was(J(TT, '_trip_filters.html')),
''',
         r'''   'own visible boxes')
ph = read(J(TA, 'phone.py'))
# RA03, 19 Nov 2026 - tv17-1 or later (it moves with every new look).
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 17 and
   read(J(TT, 'm', 'base.html')).count('?v=tv%s-%s' % _v.groups()) == 2,
   'THE PHONE APP fetches the new look (tv17-1 or later)')
try:
    ok('<select name="year"' in was(J(TT, '_trip_filters.html')),
'''),
    ]),
    (os.path.join('test_travel_five.py'), [
        (r'''   'two or three options when unsure')
tr = read(J(TT, 'trip.html'))
ok(tr.count('data-trip-pdf=') == 2 and 'data-pdf-menu' in tr and
   tr.count('fa-file-pdf') == 1 and '> PDF summary<' not in tr,
   'ONE PDF BUTTON on the trip, with Summary and Detailed under it')
ok('Itinerary{% if planned %}' not in tr and 'Itinerary</a>' in tr,
''',
         r'''   'two or three options when unsure')
tr = read(J(TT, 'trip.html'))
# RA02, 19 Nov 2026 - the phone's More menu repeats PDF - summary and PDF -
# detailed; the one PDF BUTTON is counted outside it.
_desk = tr.split('<div class="action-more-wrapper"')[0] + \
    tr.split('<div class="action-more-wrapper"')[-1].split('</div>', 2)[-1]
ok(tr.count('data-trip-pdf=') == 2 and 'data-pdf-menu' in tr and
   _desk.count('fa-file-pdf') == 1 and '> PDF summary<' not in tr,
   'ONE PDF BUTTON on the trip, with Summary and Detailed under it')
ok('Itinerary{% if planned %}' not in tr and 'Itinerary</a>' in tr,
'''),
    ]),
    (os.path.join('test_travel_twelve.py'), [
        (r'''               'STEP 1: Lisbon (4 nights) and Porto (2 nights) from the '
               'hotels, + Another city')
            ok(h.count('data-idea-interest') == 9 and 'name="style"' in h
               and 'name="extra"' in h and 'Restaurants are left out' in h,
               'STEP 2: nine interests, famous or local, anything else; '
               'restaurants left out')
            hm = M.get('/travel/m/trip/%d/ideas/new/' % t.pk
                       ).content.decode()
''',
         r'''               'STEP 1: Lisbon (4 nights) and Porto (2 nights) from the '
               'hotels, + Another city')
            # RA03, 19 Nov 2026 - eleven: Restaurants and Cafes, each
            # the city's top ten, asked for on their own.
            ok(h.count('data-idea-interest') == 11 and 'name="style"' in h
               and 'name="extra"' in h and 'top ten of each' in h,
               'STEP 2: eleven interests, famous or local, anything else; '
               'restaurants and cafes their own top ten')
            hm = M.get('/travel/m/trip/%d/ideas/new/' % t.pk
                       ).content.decode()
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
''',
         r'''/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
/* RA03, 19 Nov 2026 - greyed out suggestions (still tickable), why, and Google's rating, price and distance; the km field. */
.tv-id-card.is-dim { background: #F3F5F6; }
.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.far { color: #0C447C; background: #E6F1FB; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
.tv-id-km { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: .95rem; }
.tv-id-km input { width: 84px; }
.tv-id-kmpick { min-width: 44px; min-height: 36px; padding: 0 12px; border-radius: 999px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1F2D33; font: inherit; font-size: .9rem; cursor: pointer; }
.tv-id-kmpick[aria-pressed="true"] { border: 2px solid #0F7480; color: #0B5A63; font-weight: 700; background: #EAF5F6; }
/* RA03 - Things to do: Select, then Delete the ticked ones. */
.tv-sel { display: none; align-items: center; justify-content: center; width: 44px; min-height: 44px; flex: none; cursor: pointer; }
.tv-sel input { width: 20px; height: 20px; accent-color: #0F7480; }
[data-selecting] .tv-sel { display: flex; }
[data-selecting] [data-wish-item] { display: flex; flex-direction: row; align-items: center; gap: 4px; }
[data-selecting] [data-wish-item] > .tv-sel-body { flex: 1; min-width: 0; }
[data-selecting] [data-move-form] { display: none !important; }
[data-selecting] [data-wish-item]:has(.tv-sel input:checked) { background: #EAF5F6; border-radius: 10px; }
.tv-selbar { display: none; position: sticky; bottom: 0; z-index: 6; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 10px; padding: 10px 12px; background: #FFFFFF; border: 1px solid #D5DDE0; border-radius: 12px; box-shadow: 0 -6px 18px rgba(0, 0, 0, .08); }
[data-selecting] .tv-selbar { display: flex; }
.tv-selbar .go { display: flex; gap: 8px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
'''),
    ]),
    (os.path.join('travel', 'ideas.py'), [
        (r'''named to the AI as what to leave out, and every answer is checked again
here by name before it is shown.
"""
import datetime as dt
''',
         r'''named to the AI as what to leave out, and every answer is checked again
here by name before it is shown.

RA03, 19 Nov 2026 - Demetri: "I need two new categories - 1. Cafes and 2.
Restaurants ... (from a list of top 10 restaurants or top 10 cafes)
within the city"; "any things to do that are closed or unavailable on a
Tuesday should display, but should be greyed out"; "how many km from the
city centre ... Any things to do which fall out of this parameter must be
greyed out ... All greyed out things to do should still be selectable".
Decided the same morning: check every suggestion on Google
(travel/gplaces.py); measure from the city centre; day trips are never
held to the km but are greyed out past it; greyed out only when EVERY
day you are in the city is closed; ten restaurants and ten cafes a city,
with the Google rating and price level; Show me more counts the greyed
ones too.
"""
import datetime as dt
'''),
        (r'''from django.db.models import Max

from . import places as P

logger = logging.getLogger(__name__)

SYNC = False
PER_CITY = 12
INTERESTS = [
    ('musts', 'Must-sees', 'the famous sights and landmarks'),
''',
         r'''from django.db.models import Max

from . import gplaces as G
from . import places as P

logger = logging.getLogger(__name__)

SYNC = False
PER_CITY = 12
PER_FOOD = 10
FOOD = ('restaurants', 'cafes')
KM_PICKS = (2, 5, 10, 25)
INTERESTS = [
    ('musts', 'Must-sees', 'the famous sights and landmarks'),
'''),
        (r'''     'churches, monasteries, castles, ruins and historic sites'),
    ('daytrips', 'Day trips', 'day trips from the city'),
]
LABEL = {k: n for k, n, _w in INTERESTS}
''',
         r'''     'churches, monasteries, castles, ruins and historic sites'),
    ('daytrips', 'Day trips', 'day trips from the city'),
    # RA03, 19 Nov 2026 - each asked for on its own: the city's top ten.
    ('restaurants', 'Restaurants', 'the best restaurants in the city'),
    ('cafes', 'Cafés', 'the best cafes and coffee places in the city'),
]
LABEL = {k: n for k, n, _w in INTERESTS}
'''),
        (r'''
# ------------------------------------------------------------ running it
def run(job, client=None):
    """Ask for each city still waiting; keep the new ones."""
''',
         r'''
# ------------------------------------------------------------ running it
# ------------------------------------------------------------ RA03 checks
DAYNAMES = ['Mondays', 'Tuesdays', 'Wednesdays', 'Thursdays', 'Fridays',
            'Saturdays', 'Sundays']


def days_in(trip, bookings, c):
    """The dates you are in the city: every stay there, check-in to
    check-out; or the city's own dates; [] when not known."""
    out = set()
    for b in bookings:
        if b.kind == 'stay' and b.status != 'cancelled' and b.start_date \
                and city_of(b).lower() == c['name'].lower():
            d, end = b.start_date, b.end_date or b.start_date
            while d <= end:
                out.add(d)
                d += dt.timedelta(days=1)
    if not out and c.get('start'):
        d, end = c['start'], c.get('end') or c['start']
        while d <= end and len(out) < 60:
            out.add(d)
            d += dt.timedelta(days=1)
    return sorted(out)


def _and(words):
    return words[0] if len(words) == 1 else '%s and %s' % (
        ', '.join(words[:-1]), words[-1])


def closed_words(days, city):
    """"Closed on Tuesdays - you're in Athens only on Tue 10 Nov"."""
    names = []
    for d in days:
        n = DAYNAMES[d.weekday()]
        if n not in names:
            names.append(n)
    if len(days) == 1:
        d = days[0]
        return 'Closed on %s - you\'re in %s only on %s %d %s' % (
            names[0], city, d.strftime('%a'), d.day, d.strftime('%b'))
    return 'Closed on %s - the only days you\'re in %s' % (
        _and(names), city)


def check(i, centre, days, km):
    """Look the suggestion up on Google and mark it. False: closed for
    good - not shown. Unchecked (no key, nothing found, Google down) is
    shown as it came."""
    if not G.enabled():
        return True
    try:
        f = G.search('%s, %s' % (i.name, i.city), near=centre)
    except G.GoogleError as e:
        logger.warning('travel ideas check %s: %s', i.name, e)
        return True
    if not f:
        return True
    if f['status'] == 'CLOSED_PERMANENTLY':
        return False
    i.checked = True
    i.gid, i.lat, i.lng = f['gid'], f['lat'], f['lng']
    i.rating, i.ratings = f['rating'], f['ratings']
    i.price_level = f['price'] or ''
    if centre and f['lat'] is not None:
        i.dist_km = round(G.km(centre, (f['lat'], f['lng'])), 1)
    gdays = set((d.weekday() + 1) % 7 for d in days)
    if f['status'] == 'CLOSED_TEMPORARILY':
        i.flag, i.flag_text = 'temp', 'Temporarily closed, Google says'
    elif days and f['open_days'] is not None and \
            not (f['open_days'] & gdays):
        i.flag, i.flag_text = 'closed', closed_words(days, i.city)[:160]
    elif km and i.dist_km is not None and i.dist_km > km:
        i.flag = 'far'
        i.flag_text = ('Day trip - %s km from the centre' % _num(i.dist_km)
                       if i.interest == 'daytrips' else
                       '%s km from the centre - outside your %d km'
                       % (_num(i.dist_km), km))
    return True


def _num(x):
    return ('%.1f' % x).rstrip('0').rstrip('.') if x < 10 else '%d' % round(x)


def run(job, client=None):
    """Ask for each city still waiting; keep the new ones."""
'''),
        (r'''                 for k in keys]
    style = STYLE_SAYS.get(a.get('style'), STYLE_SAYS['mix'])
    prog = dict(job.progress or {})
    ok_any = False
''',
         r'''                 for k in keys]
    style = STYLE_SAYS.get(a.get('style'), STYLE_SAYS['mix'])
    km = a.get('km') if isinstance(a.get('km'), int) else None
    if a.get('checked') is None:
        a['checked'] = G.enabled()
        job.answers = a
        job.save(update_fields=['answers', 'updated_at'])
    prog = dict(job.progress or {})
    ok_any = False
'''),
        (r'''        try:
            names = taken(trip)
            got = P.call_ideas(c['name'], c.get('country') or trip.where,
                               _dates(c, t_start, t_end), interests, style,
                               a.get('extra') or '', names,
                               count=PER_CITY, client=client)
            pos = (Idea.objects.filter(trip=trip).aggregate(
                m=Max('position'))['m'] or 0)
            kept = 0
            for g in got:
                s = lambda k, n: str(g.get(k) or '').strip()[:n]  # noqa
                name = s('name', 160)
                if not name or any(same(name, n, cw) for n in names):
                    continue
                if g.get('kind') == 'food' and g.get('interest') != \
                        'markets':
                    continue
                pos += 1
                kept += 1
                names.append(name)
                Idea.objects.create(
                    trip=trip, run=job, city=c['name'][:80],
                    interest=g.get('interest') if g.get('interest') in
                    LABEL else keys[0],
                    name=name, area=s('area', 120), blurb=s('blurb', 400),
                    kind=g.get('kind') if g.get('kind') in P.KINDS
                    else 'sight',
                    visit=s('visit', 40), price=s('price', 60),
                    book=bool(g.get('book')), note=s('note', 160),
                    position=pos)
                if kept >= PER_CITY:
                    break
            if kept:
                prog[city] = 'done'
''',
         r'''        try:
            names = taken(trip)
            pos = (Idea.objects.filter(trip=trip).aggregate(
                m=Max('position'))['m'] or 0)
            # RA03 - the centre, and the days you are in the city, for
            # the Google check.
            centre, days = None, days_in(trip, bookings, c)
            if G.enabled():
                try:
                    f = G.search('%s%s' % (c['name'], ', %s' % (
                        c.get('country') or trip.where or '')
                        if (c.get('country') or trip.where) else ''))
                    if f and f['lat'] is not None:
                        centre = (f['lat'], f['lng'])
                except G.GoogleError as e:
                    logger.warning('travel ideas centre %s: %s', city, e)
            sights = [kv for kv in interests if kv[0] not in FOOD]
            asks = []
            if sights:
                asks.append((sights, PER_CITY, ''))
            for k, w in interests:
                if k in FOOD:
                    asks.append(([(k, w)], PER_FOOD, k))
            kept = 0
            for these, count, food in asks:
                got = P.call_ideas(
                    c['name'], c.get('country') or trip.where,
                    _dates(c, t_start, t_end), these, style,
                    a.get('extra') or '', names, count=count,
                    client=client, km=km, food=food)
                these_keys = [k for k, _w in these]
                n = 0
                for g in got:
                    s = lambda k, n: str(g.get(k) or '').strip()[:n]  # noqa
                    name = s('name', 160)
                    if not name or any(same(name, x, cw) for x in names):
                        continue
                    interest = food or (g.get('interest') if
                                        g.get('interest') in these_keys
                                        else these_keys[0])
                    if g.get('kind') == 'food' and interest not in \
                            ('markets',) + FOOD:
                        continue
                    i = Idea(
                        trip=trip, run=job, city=c['name'][:80],
                        interest=interest, name=name, area=s('area', 120),
                        blurb=s('blurb', 400),
                        kind='food' if food else (
                            g.get('kind') if g.get('kind') in P.KINDS
                            else 'sight'),
                        visit=s('visit', 40), price=s('price', 60),
                        book=bool(g.get('book')), note=s('note', 160))
                    if not check(i, centre, days, km):
                        continue
                    pos += 1
                    i.position = pos
                    i.save()
                    names.append(name)
                    n += 1
                    if n >= count:
                        break
                kept += n
            if kept:
                prog[city] = 'done'
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
''',
         r'''    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # RA03, 19 Nov 2026 - checked on Google before it is shown (Demetri:
    # "Yes. Check on Google"): where it is, how far from the centre, its
    # rating and price level, and why it is greyed out - closed on every
    # day you are in the city, or further than the km you asked for.
    # Google lets its place ID be kept; the rest is refreshed by the next
    # search.
    checked = models.BooleanField(default=False)
    gid = models.CharField(max_length=300, blank=True, default='')
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    dist_km = models.FloatField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    ratings = models.PositiveIntegerField(null=True, blank=True)
    price_level = models.CharField(max_length=8, blank=True, default='')
    FLAGS = [('', 'Fine'), ('closed', 'Closed on your days'),
             ('far', 'Too far'), ('temp', 'Temporarily closed')]
    flag = models.CharField(max_length=8, choices=FLAGS, blank=True,
                            default='')
    flag_text = models.CharField(max_length=160, blank=True, default='')

    class Meta:
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
# RA01, 18 Nov 2026 - their drop-downs.
SW_VERSION = 'tv17-1'
SW_ASSETS = '07328398c1b2'


''',
         r'''# TR-16, 18 Nov 2026 - the trip filters' badges and menus.
# RA01, 18 Nov 2026 - their drop-downs.
# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
SW_VERSION = 'tv18-1'
SW_ASSETS = 'c666f896f51c'


'''),
    ]),
    (os.path.join('travel', 'places.py'), [
        (r'''- famous: the classics; mix: some of each; local: fewer of the obvious \
sights, more that locals love."""
SUGGEST_TOOL = {
    'name': 'record_ideas',
''',
         r'''- famous: the classics; mix: some of each; local: fewer of the obvious \
sights, more that locals love."""
# RA03, 19 Nov 2026 - Demetri: "two new categories - 1. Cafes and 2.
# Restaurants ... from a list of top 10 restaurants or top 10 cafes within
# the city". Asked for on their own, with their own rules; the sights
# above still never include a place to eat.
FOOD_SYSTEM = """You suggest the best %s in one city for a family \
trip, as a well-travelled local friend would. Call record_ideas once.

- The city's top ones: real, well-established places you are sure still \
exist and are open. Never invent one. Every idea's interest is "%s" and \
its kind is "food".
- Never suggest anything in the list of what to leave out, nor the same \
place under another name.
- blurb: two plain sentences - what it is known for and what to have. No \
exclamation marks, no emoji.
- area: its neighbourhood.
- price: typical spend, e.g. "mains EUR 15 - 25" or "coffee EUR 3"; "" if \
you do not know. visit: "" . book: true only if a table usually needs \
booking ahead.
- note: at most one short line, only when useful - a closing day, or \
"cash only". Otherwise "".
- famous: the best known; mix: some of each; local: more that locals \
love, fewer that guidebooks list."""
FOOD_SAYS = {'restaurants': 'restaurants', 'cafes': 'cafes and coffee places'}
SUGGEST_TOOL = {
    'name': 'record_ideas',
'''),
        (r'''
def call_ideas(city, country, dates, interests, style, extra, leave_out,
               count=12, client=None):
    """record_ideas for one city: a list of dicts (see SUGGEST_TOOL).
    interests: [(key, label)]; leave_out: names not to suggest."""
    client = _client(client)
    ask = ['City: %s%s' % (city, ', %s' % country if country else ''),
''',
         r'''
def call_ideas(city, country, dates, interests, style, extra, leave_out,
               count=12, client=None, km=None, food=''):
    """record_ideas for one city: a list of dicts (see SUGGEST_TOOL).
    interests: [(key, label)]; leave_out: names not to suggest. RA03: km,
    keep within that of the centre (day trips excepted); food, ask for
    the city's top restaurants or cafes instead (FOOD_SYSTEM)."""
    client = _client(client)
    ask = ['City: %s%s' % (city, ', %s' % country if country else ''),
'''),
        (r'''           'Famous or local: %s' % style,
           'How many: about %d' % count]
    if extra:
        ask.append('They also said: %s' % extra[:200])
''',
         r'''           'Famous or local: %s' % style,
           'How many: about %d' % count]
    if km:
        ask.append('Distance: keep to places within about %d km of the '
                   'city centre%s.' % (km, '' if food else
                                       ' (day trips excepted)'))
    if extra:
        ask.append('They also said: %s' % extra[:200])
'''),
        (r'''    try:
        msg = client.messages.create(
            model=SUGGEST_MODEL, max_tokens=4000, system=SUGGEST_SYSTEM,
            tools=[SUGGEST_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_ideas'},
''',
         r'''    try:
        msg = client.messages.create(
            model=SUGGEST_MODEL, max_tokens=4000,
            system=(FOOD_SYSTEM % (FOOD_SAYS.get(food, food), food)
                    if food else SUGGEST_SYSTEM),
            tools=[SUGGEST_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_ideas'},
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_card.html'), [
        (r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}" data-idea="{{ i.pk }}"{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
  <div class="tv-id-acts"><a href="https://www.google.com/maps/search/?api=1&amp;query={{ i.name|urlencode }}%2C%20{{ i.city|urlencode }}" target="_blank" rel="noopener">View on Google Maps</a>{% if i.state == 'hidden' %}<button type="submit" formaction="{{ hide_url }}" formnovalidate name="unhide" value="{{ i.pk }}" data-idea-unhide>Bring it back</button>{% else %}<button type="submit" formaction="{{ hide_url }}" formnovalidate name="hide" value="{{ i.pk }}" data-idea-hide>Not interested</button>{% endif %}</div>
''',
         r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
{% comment %} RA03, 19 Nov 2026 - checked on Google: greyed out (still tickable) when closed on every day you are in the city or further than your km, with why; rating, price level and distance for the ones found. {% endcomment %}<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}{% if i.flag %} is-dim{% endif %}" data-idea="{{ i.pk }}"{% if i.flag %} data-idea-flag="{{ i.flag }}"{% endif %}{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.flag %}<span class="tv-id-flag{% if i.flag == 'far' %} far{% endif %}" data-idea-why>{{ i.flag_text }}</span>{% endif %}
  {% if i.rating or i.price_level or i.dist_km is not None and i.flag != 'far' %}<span class="tv-id-meta" data-idea-meta>{% if i.rating %}&#9733; {{ i.rating|floatformat:1 }}{% if i.ratings %} <span>({{ i.ratings }})</span>{% endif %}{% endif %}{% if i.price_level %}{% if i.rating %} &middot; {% endif %}{{ i.price_level }}{% endif %}{% if i.dist_km is not None and i.flag != 'far' %}{% if i.rating or i.price_level %} &middot; {% endif %}{{ i.dist_km|floatformat:"-1" }} km from the centre{% endif %}</span>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
  <div class="tv-id-acts"><a href="https://www.google.com/maps/search/?api=1&amp;query={{ i.name|urlencode }}%2C%20{{ i.city|urlencode }}" target="_blank" rel="noopener">View on Google Maps</a>{% if i.state == 'hidden' %}<button type="submit" formaction="{{ hide_url }}" formnovalidate name="unhide" value="{{ i.pk }}" data-idea-unhide>Bring it back</button>{% else %}<button type="submit" formaction="{{ hide_url }}" formnovalidate name="hide" value="{{ i.pk }}" data-idea-hide>Not interested</button>{% endif %}</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_choices.html'), [
        (r'''  <legend style="font-size: 1.05rem; font-weight: 700; margin-bottom: 4px">{% if desk %}<span class="tv-pl-num">2</span> {% endif %}What you like</legend>
  <div class="tv-id-chips" role="group" aria-label="What interests you">{% for i in interests %}<label class="tv-id-chip" data-idea-interest><input type="checkbox" name="interest" value="{{ i.key }}"{% if i.on %} checked{% endif %}><svg class="tick" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>{{ i.name }}</label>{% endfor %}</div>
  <span style="font-size: .8rem; color: #5B6B72">Restaurants are left out &ndash; book those as usual. Food markets and famous caf&eacute;s come under Markets &amp; shopping.</span>
  <b style="font-size: .95rem; margin-top: 4px">Famous or off the beaten track?</b>
  <div class="tv-pl-seg" role="radiogroup" aria-label="Famous or off the beaten track">{% for k, n, s in styles %}<label class="tv-pl-opt"><input type="radio" name="style" value="{{ k }}"{% if k == style %} checked{% endif %}><b>{{ n }}</b><span>{{ s }}</span></label>{% endfor %}</div>
''',
         r'''  <legend style="font-size: 1.05rem; font-weight: 700; margin-bottom: 4px">{% if desk %}<span class="tv-pl-num">2</span> {% endif %}What you like</legend>
  <div class="tv-id-chips" role="group" aria-label="What interests you">{% for i in interests %}<label class="tv-id-chip" data-idea-interest><input type="checkbox" name="interest" value="{{ i.key }}"{% if i.on %} checked{% endif %}><svg class="tick" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>{{ i.name }}</label>{% endfor %}</div>
  <span style="font-size: .8rem; color: #5B6B72">Restaurants and Caf&eacute;s bring the city&rsquo;s top ten of each, with their Google rating and price.</span>
  {% comment %} RA03, 19 Nov 2026 (Demetri: "a field where the user (just before searching for things to do) can insert how many km from the city centre"). {% endcomment %}
  <label for="id-km" style="font-weight: 700; font-size: .95rem; margin: 4px 0 0">How far from the centre? <span style="font-weight: 400; color: #5B6B72">optional</span></label>
  <div class="tv-id-km" data-idea-km><span>Within</span><input id="id-km" name="km" type="number" inputmode="numeric" min="1" max="500" step="1" class="tv-id-input" value="{{ km }}" placeholder="any" aria-describedby="id-km-help"><span>km</span>{% for k in km_picks %}<button type="button" class="tv-id-kmpick" data-km="{{ k }}"{% if km == k %} aria-pressed="true"{% endif %}>{{ k }}</button>{% endfor %}<button type="button" class="tv-id-kmpick" data-km=""{% if not km %} aria-pressed="true"{% endif %}>Any</button></div>
  <span id="id-km-help" style="font-size: .8rem; color: #5B6B72">Further than this still shows, greyed out &ndash; day trips too.</span>
  <b style="font-size: .95rem; margin-top: 4px">Famous or off the beaten track?</b>
  <div class="tv-pl-seg" role="radiogroup" aria-label="Famous or off the beaten track">{% for k, n, s in styles %}<label class="tv-pl-opt"><input type="radio" name="style" value="{{ k }}"{% if k == style %} checked{% endif %}><b>{{ n }}</b><span>{{ s }}</span></label>{% endfor %}</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_js.html'), [
        (r'''  show();
})();
</script>
''',
         r'''  show();
})();
(function () {
  /* RA03 - the km quick picks fill the box. */
  document.querySelectorAll('[data-idea-km]').forEach(function (w) {
    var box = w.querySelector('input[name=km]');
    var picks = w.querySelectorAll('[data-km]');
    function mark() { picks.forEach(function (p) { p.setAttribute('aria-pressed', String((p.getAttribute('data-km') || '') === (box.value || ''))); }); }
    picks.forEach(function (p) { p.addEventListener('click', function () { box.value = p.getAttribute('data-km'); mark(); }); });
    box.addEventListener('input', mark);
  });
})();
</script>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
''',
         r'''/* TR-14, 17 Nov 2026 - what the latest Show me more brought. */
.tv-id-new { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #FFFFFF; background: #B85C00; border-radius: 999px; padding: 1px 8px; vertical-align: 2px; }
/* RA03, 19 Nov 2026 - greyed out suggestions (still tickable), why, and Google's rating, price and distance; the km field. */
.tv-id-card.is-dim { background: #F3F5F6; }
.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.far { color: #0C447C; background: #E6F1FB; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
.tv-id-km { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: .95rem; }
.tv-id-km input { width: 84px; }
.tv-id-kmpick { min-width: 44px; min-height: 36px; padding: 0 12px; border-radius: 999px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1F2D33; font: inherit; font-size: .9rem; cursor: pointer; }
.tv-id-kmpick[aria-pressed="true"] { border: 2px solid #0F7480; color: #0B5A63; font-weight: 700; background: #EAF5F6; }
/* RA03 - Things to do: Select, then Delete the ticked ones. */
.tv-sel { display: none; align-items: center; justify-content: center; width: 44px; min-height: 44px; flex: none; cursor: pointer; }
.tv-sel input { width: 20px; height: 20px; accent-color: #0F7480; }
[data-selecting] .tv-sel { display: flex; }
[data-selecting] [data-wish-item] { display: flex; flex-direction: row; align-items: center; gap: 4px; }
[data-selecting] [data-wish-item] > .tv-sel-body { flex: 1; min-width: 0; }
[data-selecting] [data-move-form] { display: none !important; }
[data-selecting] [data-wish-item]:has(.tv-sel input:checked) { background: #EAF5F6; border-radius: 10px; }
.tv-selbar { display: none; position: sticky; bottom: 0; z-index: 6; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 10px; padding: 10px 12px; background: #FFFFFF; border: 1px solid #D5DDE0; border-radius: 12px; box-shadow: 0 -6px 18px rgba(0, 0, 0, .08); }
[data-selecting] .tv-selbar { display: flex; }
.tv-selbar .go { display: flex; gap: 8px; }
.tv-id-card.is-new { background: #FFFBF6; }
.tv-id-card[id] { scroll-margin-top: 80px; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv17-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv18-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv17-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv18-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px">{% include 'travel/_ideas_added.html' with phone=True %}{% include 'travel/_plan_banner.html' with phone=True %}
{% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: 13px">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:m_plan_setup' trip.pk %}">Plan my days</a></section>{% endif %}</div>
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% comment %} TR-12, 17 Nov 2026 - Suggest things to do, under + Things to do. {% endcomment %}
<a href="{% url 'travel:m_ideas' trip.pk %}" class="tv-btn sec wide tv-id-sugg" style="margin: 8px 0 10px; border-width: 2px" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
  {% include 'travel/m/_row.html' with b=p %}
  {% if trip_days %}<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-inline" data-move-form>{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="need_day" value="1">
    <select name="day" class="tv-select" style="flex: 1" aria-label="Put {{ p.name }} on a day" required><option value="" selected>Choose a day&hellip;</option>{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
    <button type="submit" class="tv-btn sec">Put on the day</button></form>{% endif %}
</section>
{% empty %}
<section class="tv-card"><p class="tv-muted" style="margin: 0">Nothing yet. Add a museum, a garden or a restaurant &mdash; or in Google Maps tap <b>Share &rarr; Travel</b>.</p></section>
{% endfor %}
{% elif costs %}
<section class="tv-card" data-costs>
''',
         r'''<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px">{% include 'travel/_ideas_added.html' with phone=True %}{% include 'travel/_plan_banner.html' with phone=True %}
{% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: 13px">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:m_plan_setup' trip.pk %}">Plan my days</a></section>{% endif %}</div>
<div data-wishlist>
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% comment %} TR-12, 17 Nov 2026 - Suggest things to do, under + Things to do. {% endcomment %}
<a href="{% url 'travel:m_ideas' trip.pk %}" class="tv-btn sec wide tv-id-sugg" style="margin: 8px 0 10px; border-width: 2px" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a>
{% if wish %}<button type="button" class="tv-btn sec wide" style="margin: 0 0 10px" aria-pressed="false" data-select-start>Select to delete</button>{% endif %}
{% for p in wish %}
<section class="tv-card" data-wish-item>
  <label class="tv-sel"><input type="checkbox" name="p" value="{{ p.pk }}" form="tv-del-places" aria-label="Select {{ p.name }}"></label><div class="tv-sel-body">
  {% include 'travel/m/_row.html' with b=p %}
  {% if trip_days %}<form method="post" action="{% url 'travel:m_place_move' p.pk %}" class="tv-inline" data-move-form>{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="need_day" value="1">
    <select name="day" class="tv-select" style="flex: 1" aria-label="Put {{ p.name }} on a day" required><option value="" selected>Choose a day&hellip;</option>{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
    <button type="submit" class="tv-btn sec">Put on the day</button></form>{% endif %}
</div></section>
{% empty %}
<section class="tv-card"><p class="tv-muted" style="margin: 0">Nothing yet. Add a museum, a garden or a restaurant &mdash; or in Google Maps tap <b>Share &rarr; Travel</b>.</p></section>
{% endfor %}
{% if wish %}{% url 'travel:m_places_delete' trip.pk as del_url %}{% include 'travel/_wish_select.html' with url=del_url phone=True %}{% endif %}
</div>
{% elif costs %}
<section class="tv-card" data-costs>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    <section class="form-card" data-wishlist>
        {% comment %} TR-12, 17 Nov 2026 - Suggest things to do, beside + Things to do (Demetri: "Can we add another button to Things to Do"). {% endcomment %}
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><span style="display: flex; gap: 8px; flex-wrap: wrap"><a href="{% url 'travel:ideas' trip.pk %}" class="btn action-secondary btn-sm tv-id-sugg" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></span></div>
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
    </section>
{% else %}
''',
         r'''    <section class="form-card" data-wishlist>
        {% comment %} TR-12, 17 Nov 2026 - Suggest things to do, beside + Things to do (Demetri: "Can we add another button to Things to Do"). {% endcomment %}
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><span style="display: flex; gap: 8px; flex-wrap: wrap"><a href="{% url 'travel:ideas' trip.pk %}" class="btn action-secondary btn-sm tv-id-sugg" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a>{% if wish %}<button type="button" class="btn action-secondary btn-sm" aria-pressed="false" data-select-start title="Tick several to delete them together"><i class="far fa-check-square" aria-hidden="true"></i> Select</button>{% endif %}<a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></span></div>
        {% for p in wish %}
        <div data-wish-item>
            <label class="tv-sel" title="Select {{ p.name }}"><input type="checkbox" name="p" value="{{ p.pk }}" form="tv-del-places" aria-label="Select {{ p.name }}"></label><div class="tv-sel-body">
            {% include 'travel/_place_row.html' %}
            {% if trip_days %}{% comment %} TR-5 (Demetri, 16 Nov: "To Move, you should at least need as a minimum to have a date"): no day is chosen for you. {% endcomment %}<form method="post" action="{% url 'travel:place_move' p.pk %}" class="tv-acts" style="margin: 0 0 8px 52px" data-move-form>{% csrf_token %}<input type="hidden" name="next" value="{{ request.get_full_path }}"><input type="hidden" name="need_day" value="1">
                <label for="mv{{ p.pk }}" class="small" style="margin: 0">Put on</label>
                <select id="mv{{ p.pk }}" name="day" class="form-control form-control-sm" style="max-width: 170px" required><option value="" selected>Choose a day&hellip;</option>{% for d in trip_days %}<option value="{{ d|date:'Y-m-d' }}">{{ d|date:"D j M" }}</option>{% endfor %}</select>
                <input type="time" name="time" class="form-control form-control-sm" style="max-width: 120px" aria-label="Time (optional)" title="Time (optional)">
                <button type="submit" class="btn action-secondary btn-sm" title="Put it on the day chosen">Move</button></form>{% endif %}
        </div></div>
        {% empty %}<p class="tv-sub" style="margin: 8px 0 0">Nothing yet. Add a museum, a garden, a restaurant &mdash; type its name or paste a link, and its address, hours and price are looked up for you. On the phone, share a place from Google Maps to Travel.</p>{% endfor %}
        {% if wish %}{% url 'travel:places_delete' trip.pk as del_url %}{% include 'travel/_wish_select.html' with url=del_url %}{% endif %}
    </section>
{% else %}
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('place/<int:place_id>/delete/', views_places.place_delete,
         name='place_delete'),
    path('m/trip/<int:trip_id>/place/new/', views_places.place_new,
         name='m_place_new'),
''',
         r'''    path('place/<int:place_id>/delete/', views_places.place_delete,
         name='place_delete'),
    # RA03, 19 Nov 2026 - Select, then Delete several Things to do.
    path('<int:trip_id>/places/delete/', views_places.places_delete,
         name='places_delete'),
    path('m/trip/<int:trip_id>/place/new/', views_places.place_new,
         name='m_place_new'),
'''),
        (r'''    path('m/place/<int:place_id>/delete/', views_places.place_delete,
         name='m_place_delete'),
    path('<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
''',
         r'''    path('m/place/<int:place_id>/delete/', views_places.place_delete,
         name='m_place_delete'),
    path('m/<int:trip_id>/places/delete/', views_places.places_delete,
         name='m_places_delete'),
    path('<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
'''),
    ]),
    (os.path.join('travel', 'views_ideas.py'), [
        (r'''

@travel_view
def setup(request, trip_id):
''',
         r'''

def _km(v):
    v = (v or '').strip().lower().replace('km', '').strip()
    try:
        n = int(float(v))
    except ValueError:
        return None
    return n if 1 <= n <= 500 else None


@travel_view
def setup(request, trip_id):
'''),
        (r'''                (k, n) for k, n, _s in ID.STYLES) else 'mix',
            'extra': ' '.join((P.get('extra') or '').split())[:200],
        }
        if not answers['cities']:
''',
         r'''                (k, n) for k, n, _s in ID.STYLES) else 'mix',
            'extra': ' '.join((P.get('extra') or '').split())[:200],
            # RA03 - how far from the centre; blank is any distance.
            'km': _km(P.get('km')),
        }
        if not answers['cities']:
'''),
        (r'''        'styles': ID.STYLES, 'style': last.get('style') or 'mix',
        'extra': last.get('extra') or '',
        'again': bool(last),
        'trip_start': start, 'trip_end': end})
''',
         r'''        'styles': ID.STYLES, 'style': last.get('style') or 'mix',
        'extra': last.get('extra') or '',
        'km': last.get('km') or '', 'km_picks': ID.KM_PICKS,
        'again': bool(last),
        'trip_start': start, 'trip_end': end})
'''),
        (r'''            for i in these:
                i.ticked = str(i.pk) in ticked
            if these:
                by.append({'name': n, 'ideas': these})
''',
         r'''            for i in these:
                i.ticked = str(i.pk) in ticked
            # RA03 - the greyed out ones last in their group.
            these.sort(key=lambda i: bool(i.flag))
            if these:
                by.append({'name': n, 'ideas': these})
'''),
        (r'''        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        'new_city': (latest.answers or {}).get('more') or
        next(iter(latest.progress or {}), '') if fresh else ''})
''',
         r'''        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        # RA03 - said when the opening days and distances were not
        # checked on Google (no key yet).
        'unchecked': bool(last) and (last.answers or {}).get(
            'checked') is False,
        'km': (ID.last_answers(t) or {}).get('km'),
        'new_city': (latest.answers or {}).get('more') or
        next(iter(latest.progress or {}), '') if fresh else ''})
'''),
    ]),
    (os.path.join('travel', 'views_places.py'), [
        (r'''@travel_view
@require_POST
def day_order(request, trip_id):
    """TR-9, 16 Nov 2026 - the order of one day of the itinerary (Demetri:
''',
         r'''@travel_view
@require_POST
def places_delete(request, trip_id):
    """RA03, 19 Nov 2026 - several Things to do at once (Demetri: "if I
    wanted to do a multi-select and delete of the things to do, how would
    I do this?"): Select, tick, Delete. Only this trip's own; one that came
    from a suggestion may be suggested again."""
    from .models import Idea
    t = _trip(request, trip_id)
    ids = [int(x) for x in request.POST.getlist('p') if x.isdigit()]
    gone = list(t.places.filter(pk__in=ids))
    if gone:
        Idea.objects.filter(trip=t, place__in=gone).delete()
        for p in gone:
            p.delete()
        messages.success(request, '%d thing%s to do deleted.' % (
            len(gone), '' if len(gone) == 1 else 's'))
    else:
        messages.error(request, 'Tick the ones to delete first.')
    phone = request.resolver_match.url_name.startswith('m_')
    return redirect('/travel/m/trip/%d/?tab=wish' % t.pk if phone else
                    '/travel/%d/wish-list/' % t.pk)


@travel_view
@require_POST
def day_order(request, trip_id):
    """TR-9, 16 Nov 2026 - the order of one day of the itinerary (Demetri:
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
    raise SystemExit('RA03 REFUSED: %s' % msg)


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
    if "'test_ra03_suggestions.py'" in read(pq):
        print('RA03 already applied.')
        return 0
    if "'test_ra02_travel_more.py'" not in read(pq):
        refuse('RA02 (apply_ra02_travel_more.py) is not applied - this round registers after it.')
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
        print('RA03 --check: %d file(s) would change, none written; %d '
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
    print('RA03 applied - restaurants and cafes, checked on Google; Select and Delete. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
