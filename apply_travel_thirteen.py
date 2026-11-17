# -*- coding: utf-8 -*-
"""apply_travel_thirteen.py - round TR-13, 17 Nov 2026.

RELEASE 94 - TRAVEL: TRIPS LISTED LATEST FIRST; PLAN MY DAYS KNOWS WHERE
YOU ARE.

    Demetri, 17 Nov: "When trips are listed, they should be sorted from
    the latest one, to the oldest one."

    - Travel on the computer: Upcoming, Past, a year, a country and All -
      the latest trip at the top (Upcoming and All were oldest first).
    - Trips on the phone: Upcoming the same; Past already was.

    And: "It put the Parthenon on Monday 9th, but the flight from Dublin
    to Athens is at night and I would land on midnight on Monday."

    - travel/planner.py: where you are, minute by minute, from the
      flights, trains and ferries (a trip with none goes by its hotels).
      A place only goes in a slot while you are in its country; one you
      are never near says so. The AI now gives a place's country too.
    - Help says both.

The suite ships beside this patcher. Stands on TR-12
(apply_travel_twelve.py). Idempotent. Edits backed up to .bak_travel13.
No migration.
"""
import os
import sys

SUFFIX = '.bak_travel13'
MARK = 'TR-13, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_thirteen.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do - ideas for
    # each city, ticked into Things to do.
    'test_travel_twelve.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do - ideas for
    # each city, ticked into Things to do.
    'test_travel_twelve.py',
    # TR-13, 17 Nov 2026 - Release 94: trips listed latest first.
    'test_travel_thirteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do.
    '.bak_travel12',
]

''',
         r'''    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do.
    '.bak_travel12',
    # TR-13, 17 Nov 2026 - Release 94: trips latest first.
    '.bak_travel13',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, newest first, each marked <em>Past</em>. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
''',
         r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> under two or more trips and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
    <p><strong>Forward your booking emails</strong> to the trips address and they are read for you &mdash; see the <strong>Emails</strong> tab. New bookings wait under <strong>To check</strong>; changes, cancellations and boarding passes for bookings you already have update them by themselves.</p>
'''),
        (r'''    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>
''',
         r'''    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''                     key=lambda t: t.start or far, reverse=True)
    else:
        sel = sorted([t for t in rows if not (t.end and t.end < day)],
                     key=lambda t: t.start or far)
    # TR-7 - nothing ahead: the past trips, newest first, said so.
    auto_past = not past and not sel and any(t.end and t.end < day
''',
         r'''                     key=lambda t: t.start or far, reverse=True)
    else:
        # TR-13 - the latest trip first, as on the computer.
        sel = sorted([t for t in rows if not (t.end and t.end < day)],
                     key=lambda t: t.start or far, reverse=True)
    # TR-7 - nothing ahead: the past trips, newest first, said so.
    auto_past = not past and not sel and any(t.end and t.end < day
'''),
    ]),
    (os.path.join('travel', 'places.py'), [
        (r'''            'lat': {'type': 'number'}, 'lng': {'type': 'number'},
            'city': {'type': 'string', 'description': 'Its town or city.'},
            'area': {'type': 'string', 'description':
                     'Its neighbourhood, in a few words.'},
''',
         r'''            'lat': {'type': 'number'}, 'lng': {'type': 'number'},
            'city': {'type': 'string', 'description': 'Its town or city.'},
            # TR-13 - its country, so it only goes on a day you are there.
            'country': {'type': 'string', 'description': 'Its country.'},
            'area': {'type': 'string', 'description':
                     'Its neighbourhood, in a few words.'},
'''),
    ]),
    (os.path.join('travel', 'planner.py'), [
        (r'''

# ------------------------------------------------------------ fitting
class Item(object):
''',
         r'''

# ------------------------------------------------------------ where you are
# TR-13, 17 Nov 2026 - Demetri: "It put the Parthenon on Monday 9th, but the
# flight from Dublin to Athens is at night and I would land on midnight on
# Monday". A free morning is only free where you are: a place goes on a
# day only while you are in its country - before the flight that takes you
# there has landed, or after the one that takes you away has left, it
# cannot. Where you are comes from the flights, trains and ferries (when
# each leaves and lands); a trip with none of those goes by its hotels.
def country_of_place(p):
    """The place's country: its address, else its town, else what the AI
    said ('' if none of them says)."""
    from .where import CITIES, named_city, named_country
    f = p.facts or {}
    addr = getattr(p, 'address', '') or ''
    for text in (addr, f.get('city'), f.get('area')):
        c = named_country(text or '')
        if c:
            return c
    for text in (addr, f.get('city')):
        c = named_city(text or '')
        if c:
            return c
    c = str(f.get('country') or '').strip()
    if c:
        return named_country(c) or c
    return ''


def _at(day, t, default):
    return dt.datetime.combine(day, t or default)


def whereabouts(bookings):
    """[(when, country)] in time order - None while travelling."""
    from .where import (airport_country, country_of, named_city,
                        named_country)
    live = [b for b in bookings if b.status != 'cancelled' and b.start_date]
    moves = [b for b in live if b.kind in TRANSPORT]
    out = []
    if moves:
        for b in moves:
            src = getattr(b, 'from_place', '') or ''
            frm = (named_country(src) or airport_country(src) or
                   named_city(src))
            dep = _at(b.start_date, b.start_time, dt.time(0))
            if b.end_date and b.end_time:
                arr = _at(b.end_date, b.end_time, dt.time(0))
            elif b.end_time and b.start_time and b.end_time >= b.start_time:
                arr = _at(b.start_date, b.end_time, dt.time(0))
            else:
                arr = dep + dt.timedelta(hours=3)
            if arr < dep:
                arr += dt.timedelta(days=1)
            if frm:
                out.append((dep - dt.timedelta(minutes=1), frm))
            out.append((dep, None))
            out.append((arr, country_of(b) or ''))
    else:
        for b in live:
            if b.kind in ('stay', 'car'):
                out.append((_at(b.start_date, None, dt.time(0)),
                            country_of(b) or ''))
    out.sort(key=lambda x: x[0])
    return out


def where_at(points, day, minute):
    """Your country at that minute of that day: '' when it cannot be told
    (before anything is booked), None while travelling."""
    when = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(
        minutes=minute)
    here = ''
    for at, c in points:
        if at <= when:
            here = c
        else:
            break
    return here


def there(points, country, day, start, minutes):
    """Are you in the place's country for the whole visit? Unknown either
    way is not a reason to say no."""
    if not country or not points:
        return True
    want = country.lower()
    for m in (start, start + minutes):
        c = where_at(points, day, m)
        if c is None:
            return False
        if c and c.lower() != want:
            return False
    return True


# ------------------------------------------------------------ fitting
class Item(object):
'''),
        (r'''        self.food = p.kind == 'food'
        self.meal = f.get('meal') or 'either'


''',
         r'''        self.food = p.kind == 'food'
        self.meal = f.get('meal') or 'either'
        self.country = country_of_place(p)


'''),
        (r'''        hotels[d] = hotels.get(h.pk) if h else None
    free = {d: free_of(d, busy_of(bookings, d), off) for d in days}
    used = {d: {} for d in days}
    count = {d: 0 for d in days}
''',
         r'''        hotels[d] = hotels.get(h.pk) if h else None
    free = {d: free_of(d, busy_of(bookings, d), off) for d in days}
    points = whereabouts(bookings)
    used = {d: {} for d in days}
    count = {d: 0 for d in days}
'''),
        (r'''            for key, _a, _b, _n in SLOTS:
                t = fits(it, d, key, free[d], used[d])
                if t is not None:
                    out.append((d, key, t))
        return out
''',
         r'''            for key, _a, _b, _n in SLOTS:
                t = fits(it, d, key, free[d], used[d])
                if t is not None and there(points, it.country, d, t,
                                           it.minutes):
                    out.append((d, key, t))
        return out
'''),
        (r'''    out['fit'] = bool(answers.get('fit'))
    out['unfit'] = [{'place': it.pk, 'name': it.p.name,
                     'why': why_unfit(it, days, free, hotels, pace)}
                    for it in unfit]
    out['notes'] = notes_of(out, items)
    out['mode'] = mode
    return out


def why_unfit(it, days, free, hotels, pace):
    shut = [d for d in days if open_on(it.p, d) == []]
    if shut and len(shut) == len(days):
        return 'closed on every day of the trip'
    if it.pos and days and all(hotels.get(d) and km(hotels[d], it.pos) >
                               NEAR_KM for d in days):
''',
         r'''    out['fit'] = bool(answers.get('fit'))
    out['unfit'] = [{'place': it.pk, 'name': it.p.name,
                     'why': why_unfit(it, days, free, hotels, pace,
                                      points)}
                    for it in unfit]
    out['notes'] = notes_of(out, items)
    out['mode'] = mode
    return out


def why_unfit(it, days, free, hotels, pace, points=()):
    shut = [d for d in days if open_on(it.p, d) == []]
    if shut and len(shut) == len(days):
        return 'closed on every day of the trip'
    if it.country and points and not any(
            there(points, it.country, d, m, 60) for d in days
            for m in range(9 * 60, 21 * 60, 60)):
        return 'you are not in %s on any day with time free' % it.country
    if it.pos and days and all(hotels.get(d) and km(hotels[d], it.pos) >
                               NEAR_KM for d in days):
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other and never when closed. <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        show, sel = 'all', rows
    far = dt.date(9999, 1, 1)
    sel.sort(key=lambda t: (t.start or far),
             reverse=(show == 'past' or auto_past))
    # TR-7 - a finished trip with something still To pay says so.
    from .compare import unsettled
''',
         r'''        show, sel = 'all', rows
    far = dt.date(9999, 1, 1)
    # TR-13, 17 Nov 2026 (Demetri: "When trips are listed, they should be
    # sorted from the latest one, to the oldest one"): every list, the
    # latest trip first. A trip with no dates yet is newest of all.
    sel.sort(key=lambda t: (t.start or far), reverse=True)
    # TR-7 - a finished trip with something still To pay says so.
    from .compare import unsettled
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
    raise SystemExit('TR-13 REFUSED: %s' % msg)


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
    if "'test_travel_thirteen.py'" in read(pq):
        print('TR-13 already applied.')
        return 0
    if "'test_travel_twelve.py'" not in read(pq):
        refuse('TR-12 (apply_travel_twelve.py, Release 93) is not applied - this round registers after it.')
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
        print('TR-13 --check: %d file(s) would change, none written; %d '
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
    print('TR-13 applied - trips latest first; Plan my days knows where you are.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
