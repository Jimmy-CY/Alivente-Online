# -*- coding: utf-8 -*-
"""apply_travel_twelve.py - round TR-12, 17 Nov 2026.

RELEASE 93 - TRAVEL: SUGGEST THINGS TO DO.

    Demetri, 17 Nov: "Can we add another button to Things to Do.
    Basically, based on the city where you are going to be ... the system
    must do a search and identify the top Things to Do for that
    destination ... The user must then read up on these (short blurb) and
    then tick which ones they want to add to their Things to Do."

    - Things to do: Suggest things to do, beside + Things to do.
    - Which cities (from the hotel stays, all ticked; + Another city) and
      what you like (nine interests; best known, a mix or more local;
      anything else). Phone: two steps; computer: one page.
    - About 12 ideas a city from the AI's own knowledge (travel/places.py,
      call_ideas): a blurb, how long, the price, Book ahead, a note for
      the dates. No restaurants. Never one already in Things to do - told
      to the AI and checked again by name (travel/ideas.py).
    - Tick, Add to Things to do: each is looked up on the web as one typed
      in. Not interested hides one; Show me more never repeats one. Kept
      on the trip: Your suggestions, N left to look at.

New files ship beside this patcher. Stands on TR-11 (apply_travel_eleven.py).
Idempotent. Edits backed up to .bak_travel12. MIGRATION: travel 0010 - run
`python manage.py migrate`.
"""
import os
import sys

SUFFIX = '.bak_travel12'
MARK = 'TR-12, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_twelve.py',
    'travel/ideas.py',
    'travel/migrations/0010_suggestions.py',
    'travel/templates/travel/_ideas_added.html',
    'travel/templates/travel/_ideas_card.html',
    'travel/templates/travel/_ideas_choices.html',
    'travel/templates/travel/_ideas_js.html',
    'travel/templates/travel/_ideas_list.html',
    'travel/templates/travel/_ideas_top.html',
    'travel/templates/travel/_ideas_working_body.html',
    'travel/templates/travel/ideas.html',
    'travel/templates/travel/ideas_setup.html',
    'travel/templates/travel/ideas_working.html',
    'travel/templates/travel/m/ideas.html',
    'travel/templates/travel/m/ideas_setup.html',
    'travel/templates/travel/m/ideas_working.html',
    'travel/views_ideas.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-11, 17 Nov 2026 - Release 92: Plan my days - spread Things to do
    # over the trip; Undo plan; Fit them in.
    'test_travel_eleven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-11, 17 Nov 2026 - Release 92: Plan my days - spread Things to do
    # over the trip; Undo plan; Fit them in.
    'test_travel_eleven.py',
    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do - ideas for
    # each city, ticked into Things to do.
    'test_travel_twelve.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-11, 17 Nov 2026 - Release 92: Plan my days.
    '.bak_travel11',
]

''',
         r'''    # TR-11, 17 Nov 2026 - Release 92: Plan my days.
    '.bak_travel11',
    # TR-12, 17 Nov 2026 - Release 93: Suggest things to do.
    '.bak_travel12',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps.</p>
  </article>

''',
         r'''    <p><strong>The order of a day.</strong> Each day is in time order, with one exception: a hotel&rsquo;s check-in time is only the earliest you may arrive, so on a day you travel a <strong>check-in</strong> &mdash; and a <strong>car pick-up</strong> &mdash; goes after the flight, train or ferry that gets you there and says <em>After you land, about 23:45</em> (with the hotel&rsquo;s own check-in time beside it). The flight chosen is the one landing in the hotel&rsquo;s town, or else the last one to land that day. To put a day in your own order, drag a row by its grip <i class="fas fa-grip-vertical"></i> &mdash; on the left of the row on the computer, on the right on the phone. The row lifts and the others slide out of the way; near the top or bottom of the screen the page scrolls along. Only the grip drags, so the rest of the row still scrolls the page and opens the booking. Letting go saves the order at once, and <strong>Order saved &middot; Undo</strong> shows for a few seconds. On the computer you can also press Tab to a grip and use the arrow keys. Your order is kept for that day, for everyone on the trip, and the PDFs follow it; anything added to the day later goes in its time place. <strong>Your order &middot; Back to automatic</strong> under the day&rsquo;s name puts it back in time order. Moving something to another day is still <strong>Move</strong>, as it changes its date.</p>
    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Restaurants are left out. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-pl-stephead span.on { background: #0F7480; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
''',
         r'''.tv-pl-stephead span.on { background: #0F7480; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
/* TR-12, 17 Nov 2026 - Suggest things to do: the cities, the interests, the cards to tick. */
.tv-id-city { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid #E1E6E8; min-height: 44px; margin: 0; cursor: pointer; font-weight: 400; }
.tv-id-city input { width: 22px; height: 22px; accent-color: #0F7480; flex: none; margin: 0; }
.tv-id-input { box-sizing: border-box; width: 100%; min-height: 44px; border-radius: 10px; border: 1px solid #C9D3D6; padding: 0 12px; font: inherit; background: #FFFFFF; color: #1D2B31; }
.tv-id-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.tv-id-chip { position: relative; display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 12px; border-radius: 999px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1D2B31; font-weight: 600; font-size: .9rem; cursor: pointer; margin: 0; text-decoration: none; }
.tv-id-chip input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-id-chip .tick { display: none; }
.tv-id-chip:has(input:checked), .tv-id-chip.on { border: 2px solid #0F7480; background: #E3F1F3; color: #0B5A63; }
.tv-id-chip:has(input:checked) .tick { display: inline; }
.tv-id-chip:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-id-chip .n { font-weight: 400; color: #4A5A61; }
.tv-id-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 12px; align-items: start; }
.tv-id-list { display: flex; flex-direction: column; gap: 10px; }
.tv-id-cityhead { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; grid-column: 1 / -1; margin-top: 8px; }
.tv-id-cityhead b { font-size: 1.3rem; }
.tv-id-group { grid-column: 1 / -1; font-size: .76rem; font-weight: 700; letter-spacing: .05em; color: #5B6B72; text-transform: uppercase; padding-top: 4px; }
.tv-id-card { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
.tv-id-card:has(input[name=idea]:checked) { border: 2px solid #0F7480; padding: 11px; }
.tv-id-card.is-hidden { opacity: .75; background: #F3F5F6; }
.tv-id-pick { display: flex; gap: 10px; align-items: flex-start; cursor: pointer; margin: 0; font-weight: 400; }
.tv-id-pick input { width: 24px; height: 24px; accent-color: #0F7480; flex: none; margin: 0; }
.tv-id-pick b { font-size: 1rem; display: block; }
.tv-id-pick small { font-size: .8rem; color: #5B6B72; }
.tv-id-blurb { font-size: .92rem; line-height: 1.4; color: #33444B; margin: 0; }
.tv-id-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.tv-id-tag { font-size: .75rem; color: #4A5A61; border: 1px solid #D5DDE0; border-radius: 999px; padding: 2px 8px; }
.tv-id-tag.book { color: #0B5A63; border-color: #9CC9CF; }
.tv-id-tag.note { color: #8A4500; border-color: #E8C29C; }
.tv-id-acts { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.tv-id-acts a { font-size: .85rem; font-weight: 600; text-decoration: none; color: #0F7480; min-height: 36px; display: inline-flex; align-items: center; }
.tv-id-acts button { background: none; border: 0; color: #4A5A61; font: inherit; font-size: .85rem; min-height: 36px; padding: 0 2px; cursor: pointer; }
.tv-id-more { display: flex; flex-direction: column; align-items: center; gap: 4px; grid-column: 1 / -1; padding: 4px 0 8px; }
.tv-id-more button { min-height: 46px; padding: 0 20px; border: 1px solid #0F7480; color: #0F7480; background: #FFFFFF; border-radius: 10px; font: inherit; font-weight: 700; cursor: pointer; }
.tv-id-bar { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 14px; padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; align-items: center; margin-top: 12px; box-shadow: 0 1px 3px rgba(16,34,40,.06); }
.tv-id-bar button[disabled] { opacity: .5; cursor: default; }
.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''        return 'Plan %s for trip %s (%s)' % (self.pk, self.trip_id,
                                             self.status)
''',
         r'''        return 'Plan %s for trip %s (%s)' % (self.pk, self.trip_id,
                                             self.status)


class IdeaRun(models.Model):
    """TR-12, 17 Nov 2026 - Suggest things to do (Demetri: "based on the
    city where you are going to be ... the system must do a search and
    identify the top Things to Do for that destination").

    answers   cities [names], interests [keys], style (known / mix /
              local), extra (a line of their own).
    progress  {city: 'waiting' | 'working' | 'done' | 'failed'}.
    One run asks for every city chosen; Show me more is a run for one."""
    STATUS = [('working', 'Finding ideas'), ('ready', 'Ready'),
              ('failed', 'Could not suggest')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='idea_runs')
    status = models.CharField(max_length=10, choices=STATUS,
                              default='working')
    answers = models.JSONField(default=dict, blank=True)
    progress = models.JSONField(default=dict, blank=True)
    more = models.BooleanField(default=False)
    error = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return 'Ideas %s for trip %s (%s)' % (self.pk, self.trip_id,
                                              self.status)


class Idea(models.Model):
    """TR-12 - one suggestion, kept on the trip (Demetri: "Let's save
    suggestions"). Never one already in Things to do, and Show me more
    never repeats one shown, hidden or added. Hidden (Not interested)
    stays hidden; added becomes a place, looked up on the web as any
    other."""
    STATE = [('', 'Suggested'), ('hidden', 'Not interested'),
             ('added', 'Added to Things to do')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='ideas')
    run = models.ForeignKey(IdeaRun, on_delete=models.SET_NULL, null=True,
                            blank=True, related_name='ideas')
    city = models.CharField(max_length=80)
    interest = models.CharField(max_length=20, blank=True, default='')
    name = models.CharField(max_length=160)
    area = models.CharField(max_length=120, blank=True, default='')
    blurb = models.CharField(max_length=400, blank=True, default='')
    kind = models.CharField(max_length=10, default='sight')
    visit = models.CharField(max_length=40, blank=True, default='')
    price = models.CharField(max_length=60, blank=True, default='')
    book = models.BooleanField(default=False)
    note = models.CharField(max_length=160, blank=True, default='')
    state = models.CharField(max_length=8, choices=STATE, blank=True,
                             default='')
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True,
                              blank=True, related_name='+')
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.city)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
''',
         r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, ideas, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
'''),
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv11-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv12-1'


'''),
        (r'''        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **(planner.page_state(t, request)
           if sub in ('itinerary', 'wish') else {})})


''',
         r'''        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **(planner.page_state(t, request)
           if sub in ('itinerary', 'wish') else {}),
        # TR-12 - Suggest things to do.
        **(ideas.page_state(t, request) if sub == 'wish' else {})})


'''),
    ]),
    (os.path.join('travel', 'places.py'), [
        (r'''            out[str(d['day'])[:10]] = str(d['why']).strip()[:200]
    return out
''',
         r'''            out[str(d['day'])[:10]] = str(d['why']).strip()[:200]
    return out


# ==========================================================================
# TR-12, 17 Nov 2026 - SUGGEST THINGS TO DO.
#
# Demetri: "based on the city where you are going to be ... the system must
# do a search and identify the top Things to Do for that destination", with
# what you like asked first, then "a short blurb" for each to tick. Agreed:
# from the AI's own knowledge, no web search (quick, and the web look-up
# still checks every one that is added); no restaurants; about 10 - 12 a
# city with Show me more; and never one already in Things to do (Demetri:
# "It must also not repeat suggestions, if these are already in the Things
# to Do"). travel/ideas.py keeps them and filters again by name.
# ==========================================================================
SUGGEST_MODEL = os.environ.get('TRAVEL_SUGGEST_MODEL', MODEL)
SUGGEST_SYSTEM = """You suggest things to do in one city for a family \
trip, as a well-travelled local friend would. Call record_ideas once.

- Suggest only what fits the interests given; spread the ideas across \
them. Each idea's interest is one of the keys given.
- Real, well-established places, streets, areas or day trips you are sure \
still exist and are open to visitors. Never invent one.
- No restaurants, bars or places to eat a meal. Food markets and famous \
cafes are allowed only under the markets interest.
- Never suggest anything in the list of what to leave out, nor the same \
place under another name or language.
- blurb: two or three plain sentences - what it is and why it is worth \
going. No exclamation marks, no emoji.
- area: its neighbourhood, or how far it is from the centre.
- visit: a typical visit ("1 - 2 h", "half a day"). price: "free", \
"about EUR 15", or "" if you do not know.
- book: true only if tickets usually need booking ahead.
- note: at most one short line, only when useful for the trip's dates - \
an event on during the stay, a closing day ("Closed Mon"), or the best \
time to go. Otherwise "".
- famous: the classics; mix: some of each; local: fewer of the obvious \
sights, more that locals love."""
SUGGEST_TOOL = {
    'name': 'record_ideas',
    'description': 'Record the things to do suggested for the city.',
    'input_schema': {
        'type': 'object',
        'properties': {'ideas': {'type': 'array', 'items': {
            'type': 'object', 'properties': {
                'name': {'type': 'string', 'description':
                         'Its proper name, as on a map.'},
                'interest': {'type': 'string'},
                'kind': {'type': 'string', 'enum': KINDS},
                'area': {'type': 'string'},
                'blurb': {'type': 'string'},
                'visit': {'type': 'string'},
                'price': {'type': 'string'},
                'book': {'type': 'boolean'},
                'note': {'type': 'string'}},
            'required': ['name', 'interest', 'blurb']}}},
        'required': ['ideas'],
    },
}


def call_ideas(city, country, dates, interests, style, extra, leave_out,
               count=12, client=None):
    """record_ideas for one city: a list of dicts (see SUGGEST_TOOL).
    interests: [(key, label)]; leave_out: names not to suggest."""
    client = _client(client)
    ask = ['City: %s%s' % (city, ', %s' % country if country else ''),
           'Dates: %s' % dates if dates else 'Dates: not known',
           'Interests (key: what): %s' % '; '.join(
               '%s: %s' % kv for kv in interests),
           'Famous or local: %s' % style,
           'How many: about %d' % count]
    if extra:
        ask.append('They also said: %s' % extra[:200])
    if leave_out:
        ask.append('Leave out (already on their list or already shown): '
                   '%s' % '; '.join(leave_out[:120]))
    try:
        msg = client.messages.create(
            model=SUGGEST_MODEL, max_tokens=4000, system=SUGGEST_SYSTEM,
            tools=[SUGGEST_TOOL],
            tool_choice={'type': 'tool', 'name': 'record_ideas'},
            messages=[{'role': 'user', 'content': '\n'.join(ask)}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel ideas: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    got = _tool_input(msg, 'record_ideas')
    return [i for i in got.get('ideas') or [] if isinstance(i, dict)]


def start_many(ids):
    """Look up several places one after another - in the background,
    unless SYNC (adding suggestions: one look-up at a time, not ten at
    once)."""
    from .models import Place

    def run():
        for pk in ids:
            try:
                p = Place.objects.filter(pk=pk).first()
                if p is not None:
                    look_up(p)
            except Exception:                           # noqa: BLE001
                logger.exception('travel place lookup %s', pk)
    if SYNC:
        return run()

    def go():
        try:
            run()
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()
    return None
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-pl-cards3 > .tv-pl-part > legend { float: left; width: 100%; display: flex; gap: 10px; align-items: center; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
</style>
''',
         r'''.tv-pl-cards3 > .tv-pl-part > legend { float: left; width: 100%; display: flex; gap: 10px; align-items: center; }
[data-plan-step][hidden], [data-plan-next][hidden], [data-plan-back][hidden], [data-plan-go][hidden] { display: none !important; }
/* TR-12, 17 Nov 2026 - Suggest things to do: the cities, the interests, the cards to tick. */
.tv-id-city { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid #E1E6E8; min-height: 44px; margin: 0; cursor: pointer; font-weight: 400; }
.tv-id-city input { width: 22px; height: 22px; accent-color: #0F7480; flex: none; margin: 0; }
.tv-id-input { box-sizing: border-box; width: 100%; min-height: 44px; border-radius: 10px; border: 1px solid #C9D3D6; padding: 0 12px; font: inherit; background: #FFFFFF; color: #1D2B31; }
.tv-id-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.tv-id-chip { position: relative; display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 12px; border-radius: 999px; border: 1px solid #C9D3D6; background: #FFFFFF; color: #1D2B31; font-weight: 600; font-size: .9rem; cursor: pointer; margin: 0; text-decoration: none; }
.tv-id-chip input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.tv-id-chip .tick { display: none; }
.tv-id-chip:has(input:checked), .tv-id-chip.on { border: 2px solid #0F7480; background: #E3F1F3; color: #0B5A63; }
.tv-id-chip:has(input:checked) .tick { display: inline; }
.tv-id-chip:focus-within { outline: 2px solid #0F7480; outline-offset: 2px; }
.tv-id-chip .n { font-weight: 400; color: #4A5A61; }
.tv-id-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 12px; align-items: start; }
.tv-id-list { display: flex; flex-direction: column; gap: 10px; }
.tv-id-cityhead { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; grid-column: 1 / -1; margin-top: 8px; }
.tv-id-cityhead b { font-size: 1.3rem; }
.tv-id-group { grid-column: 1 / -1; font-size: .76rem; font-weight: 700; letter-spacing: .05em; color: #5B6B72; text-transform: uppercase; padding-top: 4px; }
.tv-id-card { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
.tv-id-card:has(input[name=idea]:checked) { border: 2px solid #0F7480; padding: 11px; }
.tv-id-card.is-hidden { opacity: .75; background: #F3F5F6; }
.tv-id-pick { display: flex; gap: 10px; align-items: flex-start; cursor: pointer; margin: 0; font-weight: 400; }
.tv-id-pick input { width: 24px; height: 24px; accent-color: #0F7480; flex: none; margin: 0; }
.tv-id-pick b { font-size: 1rem; display: block; }
.tv-id-pick small { font-size: .8rem; color: #5B6B72; }
.tv-id-blurb { font-size: .92rem; line-height: 1.4; color: #33444B; margin: 0; }
.tv-id-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.tv-id-tag { font-size: .75rem; color: #4A5A61; border: 1px solid #D5DDE0; border-radius: 999px; padding: 2px 8px; }
.tv-id-tag.book { color: #0B5A63; border-color: #9CC9CF; }
.tv-id-tag.note { color: #8A4500; border-color: #E8C29C; }
.tv-id-acts { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.tv-id-acts a { font-size: .85rem; font-weight: 600; text-decoration: none; color: #0F7480; min-height: 36px; display: inline-flex; align-items: center; }
.tv-id-acts button { background: none; border: 0; color: #4A5A61; font: inherit; font-size: .85rem; min-height: 36px; padding: 0 2px; cursor: pointer; }
.tv-id-more { display: flex; flex-direction: column; align-items: center; gap: 4px; grid-column: 1 / -1; padding: 4px 0 8px; }
.tv-id-more button { min-height: 46px; padding: 0 20px; border: 1px solid #0F7480; color: #0F7480; background: #FFFFFF; border-radius: 10px; font: inherit; font-weight: 700; cursor: pointer; }
.tv-id-bar { background: #FFFFFF; border: 1px solid #E1E6E8; border-radius: 14px; padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; align-items: center; margin-top: 12px; box-shadow: 0 1px 3px rgba(16,34,40,.06); }
.tv-id-bar button[disabled] { opacity: .5; cursor: default; }
.tv-id-sugg { display: flex; align-items: center; justify-content: center; gap: 8px; }
[data-idea-step][hidden], [data-idea-next][hidden], [data-idea-back][hidden], [data-idea-go][hidden] { display: none !important; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv11-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv12-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv11-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv12-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other and never when closed. <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other and never when closed. <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Restaurants are left out, and nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats. Your suggestions stay on the trip to come back to.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips, newest first. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. TR-11 - Plan my days, to spread them over the trip. {% endcomment %}
<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px">{% include 'travel/_plan_banner.html' with phone=True %}
{% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: 13px">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:m_plan_setup' trip.pk %}">Plan my days</a></section>{% endif %}</div>
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
''',
         r'''{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. TR-11 - Plan my days, to spread them over the trip. {% endcomment %}
<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px">{% include 'travel/_ideas_added.html' with phone=True %}{% include 'travel/_plan_banner.html' with phone=True %}
{% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: 13px">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:m_plan_setup' trip.pk %}">Plan my days</a></section>{% endif %}</div>
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% comment %} TR-12, 17 Nov 2026 - Suggest things to do, under + Things to do. {% endcomment %}
<a href="{% url 'travel:m_ideas' trip.pk %}" class="tv-btn sec wide tv-id-sugg" style="margin: 8px 0 10px; border-width: 2px" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. TR-11 - and Plan my days, to spread them over the trip. {% endcomment %}
    <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px">{% include 'travel/_plan_banner.html' %}
    {% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: .9rem">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:plan_setup' trip.pk %}" style="max-width: 260px">Plan my days</a></section>{% endif %}</div>
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></div>
        {% for p in wish %}
        <div data-wish-item>
''',
         r'''{% elif tab == 'wish' %}
    {% comment %} TR-4 - places with no day yet. TR-11 - and Plan my days, to spread them over the trip. {% endcomment %}
    <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px">{% include 'travel/_ideas_added.html' %}{% include 'travel/_plan_banner.html' %}
    {% if wish and trip_days and not plan_open and not plan_new %}<section class="tv-pl-cta" data-plan-cta><div><b>{{ wish|length }} thing{{ wish|length|pluralize }} to do ha{{ wish|length|pluralize:"s,ve" }} no day yet</b><br><span style="opacity: .92; font-size: .9rem">Let Alivente spread {{ wish|length|pluralize:"it,them" }} over your trip &ndash; by opening hours, busy times and what is near what.</span></div><a class="go" href="{% url 'travel:plan_setup' trip.pk %}" style="max-width: 260px">Plan my days</a></section>{% endif %}</div>
    <section class="form-card" data-wishlist>
        {% comment %} TR-12, 17 Nov 2026 - Suggest things to do, beside + Things to do (Demetri: "Can we add another button to Things to Do"). {% endcomment %}
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><span style="display: flex; gap: 8px; flex-wrap: wrap"><a href="{% url 'travel:ideas' trip.pk %}" class="btn action-secondary btn-sm tv-id-sugg" data-idea-suggest><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg> {% if ideas_open %}Finding ideas&hellip;{% elif ideas_left %}Your suggestions &middot; {{ ideas_left }} left to look at{% else %}Suggest things to do{% endif %}</a><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></span></div>
        {% for p in wish %}
        <div data-wish-item>
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import (compare, phone, report, views, views_inbox, views_places,
               views_plan)

app_name = 'travel'
''',
         r'''from django.urls import path

from . import (compare, phone, report, views, views_ideas, views_inbox,
               views_places, views_plan)

app_name = 'travel'
'''),
        (r'''    path('m/trip/<int:trip_id>/plan/<int:plan_id>/discard/',
         views_plan.discard, name='m_plan_discard'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
''',
         r'''    path('m/trip/<int:trip_id>/plan/<int:plan_id>/discard/',
         views_plan.discard, name='m_plan_discard'),
    # TR-12, 17 Nov 2026 - Suggest things to do.
    path('<int:trip_id>/ideas/new/', views_ideas.setup, name='ideas_setup'),
    path('<int:trip_id>/ideas/', views_ideas.ideas, name='ideas'),
    path('<int:trip_id>/ideas/add/', views_ideas.add, name='ideas_add'),
    path('<int:trip_id>/ideas/hide/', views_ideas.hide, name='ideas_hide'),
    path('<int:trip_id>/ideas/more/', views_ideas.more, name='ideas_more'),
    path('m/trip/<int:trip_id>/ideas/new/', views_ideas.setup,
         name='m_ideas_setup'),
    path('m/trip/<int:trip_id>/ideas/', views_ideas.ideas, name='m_ideas'),
    path('m/trip/<int:trip_id>/ideas/add/', views_ideas.add,
         name='m_ideas_add'),
    path('m/trip/<int:trip_id>/ideas/hide/', views_ideas.hide,
         name='m_ideas_hide'),
    path('m/trip/<int:trip_id>/ideas/more/', views_ideas.more,
         name='m_ideas_more'),
    path('place/<int:place_id>/done/', views_places.place_done,
         name='place_done'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''        'settle': settle_rows(t, bs),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **plan_state(t, request, tab)})


def plan_state(t, request, tab):
    if tab not in ('itinerary', 'wish'):
        return {}
    from .planner import page_state
    return page_state(t, request)

''',
         r'''        'settle': settle_rows(t, bs),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **plan_state(t, request, tab),
        # TR-12 - Suggest things to do.
        **idea_state(t, request, tab)})


def plan_state(t, request, tab):
    if tab not in ('itinerary', 'wish'):
        return {}
    from .planner import page_state
    return page_state(t, request)


def idea_state(t, request, tab):
    """TR-12 - Suggest things to do: suggestions left, one being found,
    the line after adding."""
    if tab != 'wish':
        return {}
    from .ideas import page_state
    return page_state(t, request)

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
    raise SystemExit('TR-12 REFUSED: %s' % msg)


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
    if "'test_travel_twelve.py'" in read(pq):
        print('TR-12 already applied.')
        return 0
    if "'test_travel_eleven.py'" not in read(pq):
        refuse('TR-11 (apply_travel_eleven.py, Release 92) is not applied - this round registers after it.')
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
        print('TR-12 --check: %d file(s) would change, none written; %d '
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
    print('TR-12 applied - Suggest things to do. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
