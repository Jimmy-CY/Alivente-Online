# -*- coding: utf-8 -*-
"""apply_ra10_google_checks.py - round RA10, 21 Nov 2026.

RELEASE RA10 - NOT FOUND ON GOOGLE; WHO USED EACH CHECK.

    Demetri, 21 Nov: "Can we check which user used the 35 so far for
    today?" - and "Yes, why not" to the fix for suggestions Google cannot
    find.

    - travel/gquota.py: every Google check is also logged - who, what for
      (Suggest things to do, Show me more, Check them now, the morning
      catch-up, the key check) and trip; kept 13 months. Travel > Google
      allowance lists them, today and this month ("Who used them").
    - A suggestion Google cannot find is marked Not found on Google (a
      grey note; still tickable, not greyed out) instead of being tried
      again every morning and stopping the catch-up for the rest.
    - The distance note's class is is-far: Font Awesome's .far gave it
      the icon font (squashed capitals).
    - Daily spending (computer): a bin beside the pencil deletes, asking
      first; the Delete button under the amount is gone. Demetri: "Can we
      not rather just put a trash can next to the pencil?"
    - Suggestions outside what you asked for (further than your km,
      closed on your days, temporarily closed) go to their own section at
      the end of the city, "Outside what you asked for (n)", closed to
      start and grouped by why; still tickable; it opens when one in it is
      ticked. Show me more says how many new ones are outside. Demetri:
      "Let's put this in RA10. Let's start it closed for now."
    - Change what you like keeps what Google said about the suggestions
      it replaces: one that comes back is not checked again (its distance
      is measured against the new km); only new ones use Google checks.
    - The budget card: the pencil is only a pencil; a bin beside it
      removes the budget (asks first); Remove budget under the form is
      gone. Demetri: "The Pencil should only be a pencil, add the trash
      can."
    - Daily spending: the Currency drop-down is as tall as the other
      fields (base.html's select height: auto outranked it).
    - Help on the computer and the phone; the phone app moves to tv23-1.
    - test_ra03_suggestions expects Not found on Google.
    - Migration travel 0014: run python manage.py migrate locally first.

The suite and the migration ship beside this patcher. Stands on RA09.
Idempotent. Edits backed up to .bak_ra10.
"""
import os
import sys

SUFFIX = '.bak_ra10'
MARK = 'RA10, 21 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra10_google_checks.py',
    'travel/migrations/0014_google_checks.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra08_google_quota.py',
    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    'test_ra09_google_allowance.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra08_google_quota.py',
    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    'test_ra09_google_allowance.py',
    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    'test_ra10_google_checks.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    '.bak_ra09',
]

''',
         r'''    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    '.bak_ra09',
    # RA10, 21 Nov 2026 - Not found on Google; who used each check.
    '.bak_ra10',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> to change its amount, currency, day or note, or to delete it. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
''',
         r'''    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change. The pencil <i class="fas fa-pen"></i> on the budget card opens it to change; the bin <i class="fas fa-trash-alt"></i> beside it removes the budget (it asks first; your spending stays).</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> (or its pencil <i class="fas fa-pen"></i>) to change its amount, currency, day or note; the bin <i class="fas fa-trash-alt"></i> beside the pencil deletes it, and asks first. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
'''),
        (r'''    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. Greyed-out cards can still be ticked and added; they sit at the bottom of their group, and <strong>Show me more</strong> counts them like the rest. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
    <p data-help-gquota><strong>Google checks left.</strong> Each suggestion checked on Google (opening days, distance, rating, price) is one Google search, and so is finding each city&rsquo;s centre &ndash; about 33 for one city with sights, Restaurants and Caf&eacute;s. Google caps the key&rsquo;s project at 100 a day, so Alivente keeps its own <strong>monthly</strong> allowance too (1,000 to start &ndash; about Google&rsquo;s free amount): the Suggest page shows what is left this month and today. When either is used up, suggestions still come, just not checked on Google, until tomorrow or the 1st. Those waiting are <strong>checked automatically the next morning</strong> (after 10:00, when Google&rsquo;s day starts, using at most half of the day&rsquo;s allowance, trips starting soonest first), or straight away with <strong>Check them now</strong> on the suggestions page when there is allowance left. You get one email when 80% of the month is used. A superuser changes the numbers under <strong>Change the allowance</strong> on that page (Travel &rsaquo; Google allowance). Nothing else in Alivente uses Google searches &ndash; not the weather, nor bookings, nor looking up hotels.</p>
  </article>

''',
         r'''    <p><strong>Plan my days.</strong> On a trip&rsquo;s <strong>Things to do</strong>, once things have no day yet, <strong>Plan my days</strong> spreads them over the trip. It asks three things first: whether what is already on a day may move (<strong>Keep</strong> or <strong>Can move</strong>; a booked ticket always stays, and what the last plan placed can be kept or freed in one go), which mornings, afternoons and evenings to keep free (flights and other bookings are already greyed out), and your pace, how you get around and your must-dos. It then looks each place up once &ndash; where it is, its hours on each day, how long a visit takes, when it is usually quiet or busy (general knowledge, not live figures) and whether to book ahead &ndash; and fits everything in: never on a day it is closed, never in a slot you kept free or one a booking takes, never more than your pace; near what is already on the day, from your hotel, at the quiet time. <strong>Your plan</strong> shows each day with times, the walk or ride between, a line about the day, what was <strong>MOVED</strong> and a <strong>Before you go</strong> list (tickets to book, a long day, what could not fit and why). Move anything to another day first if you like &ndash; drag it on the computer, <strong>Move</strong> on the phone &ndash; then <strong>Accept plan</strong>. Nothing changes before that. <strong>Undo plan</strong> stays on the itinerary and Things to do until the trip ends or you plan again; it puts back only what is still where the plan put it. Add more things after accepting and Things to do offers <strong>Fit them in</strong>: the same answers again, everything on a day kept, the new things into the gaps. It also knows where you are: a place only goes on a day while you are in its country &ndash; from when your flight, train or ferry there lands until the one that takes you away leaves &ndash; so the Parthenon never lands on the morning you are still in Dublin.</p>
    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. These go in their own section at the end of the city, <strong>Outside what you asked for</strong> (with how many), closed to start &ndash; click it to open; inside they are grouped by why (further from the centre, closed on your days, temporarily closed). They can still be ticked and added, the section opens by itself when one in it is ticked, and <strong>Show me more</strong> counts them like the rest (its line says how many of the new ones are outside). Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden &ndash; a place that comes back is not checked on Google again: what Google said is kept, and only its distance is measured against your new km, so only the new ones use Google checks. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
    <p data-help-gquota><strong>Google checks left.</strong> Each suggestion checked on Google (opening days, distance, rating, price) is one Google search, and so is finding each city&rsquo;s centre &ndash; about 33 for one city with sights, Restaurants and Caf&eacute;s. Google caps the key&rsquo;s project at 100 a day, so Alivente keeps its own <strong>monthly</strong> allowance too (1,000 to start &ndash; about Google&rsquo;s free amount): the Suggest page shows what is left this month and today. When either is used up, suggestions still come, just not checked on Google, until tomorrow or the 1st. Those waiting are <strong>checked automatically the next morning</strong> (after 10:00, when Google&rsquo;s day starts, using at most half of the day&rsquo;s allowance, trips starting soonest first), or straight away with <strong>Check them now</strong> on the suggestions page when there is allowance left. You get one email when 80% of the month is used. A superuser changes the numbers under <strong>Change the allowance</strong> on that page (Travel &rsaquo; Google allowance), which also shows <strong>Who used them</strong>: every check today and this month by person, what for (Suggest things to do, Show me more, Check them now, the morning catch-up, the key check) and trip &ndash; <em>Alivente itself</em> is the morning catch-up and the key check. A suggestion Google cannot find at all says <strong>Not found on Google &ndash; check the name and place yourself</strong> in grey; it is not greyed out, can still be ticked, and is not checked again. Nothing else in Alivente uses Google searches &ndash; not the weather, nor bookings, nor looking up hotels.</p>
  </article>

'''),
    ]),
    (os.path.join('pages', 'key_health.py'), [
        (r'''    try:                    # RA09 - counted in Alivente's Google allowance
        from travel import gquota
        gquota.note()
    except Exception:                                   # noqa: BLE001
        pass
''',
         r'''    try:                    # RA09 - counted in Alivente's Google allowance
        from travel import gquota
        with gquota.purpose('key'):                     # RA10 - why
            gquota.note()
    except Exception:                                   # noqa: BLE001
        pass
'''),
    ]),
    (os.path.join('test_ra03_suggestions.py'), [
        (r'''   'A RESTAURANT: rating, price level, distance')
i = idea('Nowhere')
ok(ID.check(i, CENTRE, days, 5) and not i.checked and i.flag == '',
   'NOT FOUND ON GOOGLE: shown as it came, unchecked')

# ==========================================================================
''',
         r'''   'A RESTAURANT: rating, price level, distance')
i = idea('Nowhere')
ok(ID.check(i, CENTRE, days, 5) and i.checked and i.flag == 'nf',
   'NOT FOUND ON GOOGLE: shown, marked Not found on Google (RA10)')

# ==========================================================================
'''),
        (r'''               'own groups')
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok(h.count('data-idea-flag=') == 2 and
               'Closed on Mondays and Tuesdays' in h and
               'outside your 5 km' in h and
''',
         r'''               'own groups')
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok(h.count('data-idea-flag=') -
               h.count('data-idea-flag="nf"') == 2 and
               'Closed on Mondays and Tuesdays' in h and
               'outside your 5 km' in h and
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.far { color: #0C447C; background: #E6F1FB; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.is-far { color: #0C447C; background: #E6F1FB; }
.tv-id-flag.is-nf { color: #45545A; background: #EEF1F2; }
.tv-id-out { grid-column: 1 / -1; border: 1px solid #D9E0E3; border-radius: 12px; background: #F7F9FA; padding: 0 12px; }
.tv-id-out > summary { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; padding: 12px 0; cursor: pointer; list-style: none; }
.tv-id-out > summary::-webkit-details-marker { display: none; }
.tv-id-out > summary::before { content: "\25B8"; color: #5B6B72; }
.tv-id-out[open] > summary::before { content: "\25BE"; }
.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'gquota.py'), [
        (r'''The day and month are Cyprus time (the site's time zone). Never from a
test unless a test asks (every suite is a test_*.py script).
"""
import logging

logger = logging.getLogger(__name__)
WARN_AT = 80


''',
         r'''The day and month are Cyprus time (the site's time zone). Never from a
test unless a test asks (every suite is a test_*.py script).

RA10, 21 Nov 2026 - who used each check (Demetri: "Can we check which user
used the 35 so far for today?"): every search counted is also logged with
why (Suggest, Show me more, Check them now, the morning catch-up, the key
check), who and for which trip - set around the work with purpose().
Kept 13 months.
"""
import contextlib
import contextvars
import logging

logger = logging.getLogger(__name__)
WARN_AT = 80
KEEP_DAYS = 400
_who = contextvars.ContextVar('travel_google_who', default=None)


@contextlib.contextmanager
def purpose(why=None, user=None, trip=None):
    """Searches made inside are logged with why, who and the trip; what is
    not given is kept from an outer purpose()."""
    was = _who.get() or {}
    now = dict(was)
    for k, v in (('why', why), ('user', user), ('trip', trip)):
        if v is not None:
            now[k] = getattr(v, 'pk', v)
    tok = _who.set(now)
    try:
        yield
    finally:
        _who.reset(tok)


def _log(today):
    from .models import GoogleCheck
    w = _who.get() or {}
    GoogleCheck.objects.create(day=today, why=w.get('why') or 'other',
                               user_id=w.get('user'), trip_id=w.get('trip'))


def used_by(today=None):
    """Today's checks and this month's, by who, why and trip - most first."""
    from django.db.models import Count
    from .models import GoogleCheck
    today = today or _today()

    def rows(qs):
        out = []
        for r in qs.values('user__first_name', 'user__last_name',
                           'user__username', 'why', 'trip__name') \
                .annotate(n=Count('id')).order_by('-n'):
            who = ('%s %s' % (r['user__first_name'] or '',
                              r['user__last_name'] or '')).strip() or \
                r['user__username'] or 'Alivente itself'
            out.append({'who': who, 'n': r['n'],
                        'why': dict(GoogleCheck.WHY).get(r['why'], 'Other'),
                        'trip': r['trip__name'] or ''})
        return out
    return {'today': rows(GoogleCheck.objects.filter(day=today)),
            'month': rows(GoogleCheck.objects.filter(
                day__gte=today.replace(day=1), day__lte=today))}


'''),
        (r'''    except Exception:                                   # noqa: BLE001
        logger.exception('google allowance count')


''',
         r'''    except Exception:                                   # noqa: BLE001
        logger.exception('google allowance count')
    try:                                                # RA10 - who
        _log(today)
    except Exception:                                   # noqa: BLE001
        logger.exception('google check log')


'''),
        (r'''            rechecked_on=today).update(rechecked_on=today):
        return None
    u = usage(today)
    limit = min(u['day_left'] // SHARE, u['month_left'])
    trips = Trip.objects.filter(ideas__checked=False,
                                ideas__state='').distinct()
    if limit <= 0 or not trips.exists():
        return 0
    used, done = ID.recheck(list(trips), limit, today)
    logger.info('travel ideas checked later: %d (%d searches)', done, used)
    return done
''',
         r'''            rechecked_on=today).update(rechecked_on=today):
        return None
    try:                                # RA10 - the log keeps 13 months
        import datetime as _dt
        from .models import GoogleCheck
        GoogleCheck.objects.filter(
            day__lt=today - _dt.timedelta(KEEP_DAYS)).delete()
    except Exception:                                   # noqa: BLE001
        logger.exception('google check log tidy')
    u = usage(today)
    limit = min(u['day_left'] // SHARE, u['month_left'])
    trips = Trip.objects.filter(ideas__checked=False,
                                ideas__state='').distinct()
    if limit <= 0 or not trips.exists():
        return 0
    with purpose('morning'):                            # RA10
        used, done = ID.recheck(list(trips), limit, today)
    logger.info('travel ideas checked later: %d (%d searches)', done, used)
    return done
'''),
    ]),
    (os.path.join('travel', 'ideas.py'), [
        (r'''def check(i, centre, days, km):
    """Look the suggestion up on Google and mark it. False: closed for
    good - not shown. Unchecked (no key, nothing found, Google down) is
    shown as it came."""
    if not G.enabled():
        return True
''',
         r'''def check(i, centre, days, km):
    """Look the suggestion up on Google and mark it. False: closed for
    good - not shown. Unchecked (no key, Google down) is shown as it came.
    RA10, 21 Nov 2026 - nothing found is checked too, marked Not found on
    Google: not tried again every morning, and it no longer stops the
    morning catch-up for everything behind it."""
    if not G.enabled():
        return True
'''),
        (r'''        return True
    if not f:
        return True
    if f['status'] == 'CLOSED_PERMANENTLY':
''',
         r'''        return True
    if not f:
        i.checked = True
        i.flag = 'nf'
        i.flag_text = 'Not found on Google - check the name and place yourself'
        return True
    if f['status'] == 'CLOSED_PERMANENTLY':
'''),
        (r'''

def _num(x):
    return ('%.1f' % x).rstrip('0').rstrip('.') if x < 10 else '%d' % round(x)


def run(job, client=None):
    """Ask for each city still waiting; keep the new ones."""
    from .models import Idea
    from .views import span
''',
         r'''

def reused(i, known, km, cw=None):
    """RA10, 21 Nov 2026 - fill the suggestion from what Google said about
    it before Change what you like, without asking again: True when it was
    known. Closed on your days, temporarily closed and not found stay; the
    distance is measured against the km asked for now."""
    for k in known or []:
        if (k.get('city') or '').lower() != i.city.lower() or \
                not same(i.name, k.get('name') or '', cw or set()):
            continue
        i.checked = True
        i.gid = k.get('gid') or ''
        i.lat, i.lng = k.get('lat'), k.get('lng')
        i.dist_km = k.get('dist_km')
        i.rating, i.ratings = k.get('rating'), k.get('ratings')
        i.price_level = k.get('price_level') or ''
        i.flag, i.flag_text = '', ''
        if k.get('flag') in ('closed', 'temp', 'nf'):
            i.flag, i.flag_text = k['flag'], k.get('flag_text') or ''
        elif km and i.dist_km is not None and i.dist_km > km:
            i.flag = 'far'
            i.flag_text = ('Day trip - %s km from the centre'
                           % _num(i.dist_km) if i.interest == 'daytrips'
                           else '%s km from the centre - outside your %d km'
                           % (_num(i.dist_km), km))
        return True
    return False


def _num(x):
    return ('%.1f' % x).rstrip('0').rstrip('.') if x < 10 else '%d' % round(x)


def run(job, client=None):
    """Ask for each city still waiting; keep the new ones. RA10 - its
    Google checks are logged as this run's (Suggest or Show me more)."""
    from . import gquota
    with gquota.purpose('more' if job.more else 'suggest',
                        user=job.created_by_id, trip=job.trip_id):
        return _run(job, client)


def _run(job, client=None):
    from .models import Idea
    from .views import span
'''),
        (r'''                        visit=s('visit', 40), price=s('price', 60),
                        book=bool(g.get('book')), note=s('note', 160))
                    if not check(i, centre, days, km):
                        continue
                    pos += 1
''',
         r'''                        visit=s('visit', 40), price=s('price', 60),
                        book=bool(g.get('book')), note=s('note', 160))
                    if not reused(i, a.get('reuse'), km, cw) and \
                            not check(i, centre, days, km):
                        continue
                    pos += 1
'''),
        (r'''    else:
        cities = answers.get('cities') or []
        trip.ideas.filter(state='').delete()
    return IdeaRun.objects.create(
''',
         r'''    else:
        cities = answers.get('cities') or []
        # RA10, 21 Nov 2026 - what Google already said about the ones that
        # go is kept with the run: one that comes back is not checked again
        # (Demetri: "I am happy with your suggestion for reusing Google
        # checks").
        answers = dict(answers, reuse=[{
            'name': i.name, 'city': i.city, 'gid': i.gid, 'lat': i.lat,
            'lng': i.lng, 'dist_km': i.dist_km, 'rating': i.rating,
            'ratings': i.ratings, 'price_level': i.price_level,
            'flag': i.flag, 'flag_text': i.flag_text}
            for i in trip.ideas.filter(state='', checked=True)])
        trip.ideas.filter(state='').delete()
    return IdeaRun.objects.create(
'''),
        (r'''    rows.sort(key=lambda r: r[0])
    used = done = 0
    for _start, t, bookings in rows:
        centres = {}
        for i in waiting(t).select_related('run').order_by('city',
                                                           'position'):
            if used >= limit or not G.enabled():
                return used, done
            c = {'name': i.city, 'country': ''}
            if i.city not in centres:
                centres[i.city] = None
                if used + 2 > limit:
                    return used, done
                used += 1
                try:
                    f = G.search('%s%s' % (i.city, ', %s' % t.where
                                           if t.where else ''))
                    if f and f['lat'] is not None:
                        centres[i.city] = (f['lat'], f['lng'])
                except G.GoogleError as e:
                    logger.warning('travel recheck centre %s: %s', i.city, e)
                    return used, done
            km = ((i.run.answers or {}) if i.run else {}).get('km')
            used += 1
            keep = check(i, centres[i.city], days_in(t, bookings, c),
                         km if isinstance(km, int) else None)
            if not keep:
                i.delete()
                done += 1
                continue
            if not i.checked:           # Google said no: try another day
                return used, done
            i.save()
            done += 1
    return used, done
''',
         r'''    rows.sort(key=lambda r: r[0])
    used = done = 0
    from . import gquota
    for _start, t, bookings in rows:
        with gquota.purpose(trip=t.pk):               # RA10 - the trip
            centres = {}
            for i in waiting(t).select_related('run').order_by('city',
                                                               'position'):
                if used >= limit or not G.enabled():
                    return used, done
                c = {'name': i.city, 'country': ''}
                if i.city not in centres:
                    centres[i.city] = None
                    if used + 2 > limit:
                        return used, done
                    used += 1
                    try:
                        f = G.search('%s%s' % (i.city, ', %s' % t.where
                                               if t.where else ''))
                        if f and f['lat'] is not None:
                            centres[i.city] = (f['lat'], f['lng'])
                    except G.GoogleError as e:
                        logger.warning('travel recheck centre %s: %s',
                                       i.city, e)
                        return used, done
                km = ((i.run.answers or {}) if i.run else {}).get('km')
                used += 1
                keep = check(i, centres[i.city], days_in(t, bookings, c),
                             km if isinstance(km, int) else None)
                if not keep:
                    i.delete()
                    done += 1
                    continue
                if not i.checked:   # Google down or refused: another day
                    return used, done
                i.save()
                done += 1
    return used, done
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    price_level = models.CharField(max_length=8, blank=True, default='')
    FLAGS = [('', 'Fine'), ('closed', 'Closed on your days'),
             ('far', 'Too far'), ('temp', 'Temporarily closed')]
    flag = models.CharField(max_length=8, choices=FLAGS, blank=True,
                            default='')
''',
         r'''    price_level = models.CharField(max_length=8, blank=True, default='')
    FLAGS = [('', 'Fine'), ('closed', 'Closed on your days'),
             ('far', 'Too far'), ('temp', 'Temporarily closed'),
             # RA10, 21 Nov 2026 - Google found nothing: checked, not
             # tried again every morning, still tickable.
             ('nf', 'Not found on Google')]
    flag = models.CharField(max_length=8, choices=FLAGS, blank=True,
                            default='')
'''),
        (r'''    class Meta:
        db_table = 'travel_google_allowance'
''',
         r'''    class Meta:
        db_table = 'travel_google_allowance'


# RA10, 21 Nov 2026 - who used each Google check (Demetri: "Can we check
# which user used the 35 so far for today?"). One row a search; shown to a
# superuser under Travel > Google allowance; kept 13 months.
class GoogleCheck(models.Model):
    WHY = [('suggest', 'Suggest things to do'), ('more', 'Show me more'),
           ('now', 'Check them now'), ('morning', 'Morning catch-up'),
           ('key', 'Key check'), ('other', 'Other')]
    at = models.DateTimeField(auto_now_add=True)
    day = models.DateField(db_index=True)
    why = models.CharField(max_length=8, choices=WHY, default='other')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')

    class Meta:
        db_table = 'travel_google_checks'
        ordering = ['-at', '-id']

    def __str__(self):
        return '%s %s' % (self.day, self.why)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
# RA09, 21 Nov 2026 - Google checks left.
SW_VERSION = 'tv22-1'
SW_ASSETS = '14fa92f850f2'


''',
         r'''# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
# RA09, 21 Nov 2026 - Google checks left.
# RA10, 21 Nov 2026 - Not found on Google; the distance note's own class;
# outside what you asked for, in its own section.
SW_VERSION = 'tv23-1'
SW_ASSETS = '1af680bf37b8'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_card.html'), [
        (r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
{% comment %} RA03, 19 Nov 2026 - checked on Google: greyed out (still tickable) when closed on every day you are in the city or further than your km, with why; rating, price level and distance for the ones found. {% endcomment %}<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}{% if i.flag %} is-dim{% endif %}" data-idea="{{ i.pk }}"{% if i.flag %} data-idea-flag="{{ i.flag }}"{% endif %}{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.flag %}<span class="tv-id-flag{% if i.flag == 'far' %} far{% endif %}" data-idea-why>{{ i.flag_text }}</span>{% endif %}
  {% if i.rating or i.price_level or i.dist_km is not None and i.flag != 'far' %}<span class="tv-id-meta" data-idea-meta>{% if i.rating %}&#9733; {{ i.rating|floatformat:1 }}{% if i.ratings %} <span>({{ i.ratings }})</span>{% endif %}{% endif %}{% if i.price_level %}{% if i.rating %} &middot; {% endif %}{{ i.price_level }}{% endif %}{% if i.dist_km is not None and i.flag != 'far' %}{% if i.rating or i.price_level %} &middot; {% endif %}{{ i.dist_km|floatformat:"-1" }} km from the centre{% endif %}</span>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
''',
         r'''{% comment %} TR-12 - one suggestion (TR-14: New when the latest Show me more brought it): tick it to add it; its blurb, how long, what it costs, book ahead, a note for the dates; Google Maps; Not interested (or Bring it back). {% endcomment %}
{% comment %} RA10, 21 Nov 2026 - Not found on Google: a grey note, not greyed out; the blue note's class is is-far (Font Awesome owns .far). {% endcomment %}
{% comment %} RA03, 19 Nov 2026 - checked on Google: greyed out (still tickable) when closed on every day you are in the city or further than your km, with why; rating, price level and distance for the ones found. {% endcomment %}<div class="tv-id-card{% if i.state == 'hidden' %} is-hidden{% endif %}{% if i.new %} is-new{% endif %}{% if i.flag and i.flag != 'nf' %} is-dim{% endif %}" data-idea="{{ i.pk }}"{% if i.flag %} data-idea-flag="{{ i.flag }}"{% endif %}{% if i.pk == first_new %} id="new"{% endif %}>
  {% if i.state == 'hidden' %}<div class="tv-id-pick"><span><b>{{ i.name }}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></div>
  {% else %}<label class="tv-id-pick"><input type="checkbox" name="idea" value="{{ i.pk }}"{% if i.ticked %} checked{% endif %} aria-label="Add {{ i.name }}"><span><b>{{ i.name }}{% if i.new %} <span class="tv-id-new" data-idea-new>New</span>{% endif %}</b>{% if i.area %}<small>{{ i.area }}</small>{% endif %}</span></label>{% endif %}
  {% if i.blurb %}<p class="tv-id-blurb">{{ i.blurb }}</p>{% endif %}
  {% if i.flag %}<span class="tv-id-flag{% if i.flag == 'far' %} is-far{% elif i.flag == 'nf' %} is-nf{% endif %}" data-idea-why>{{ i.flag_text }}</span>{% endif %}
  {% if i.rating or i.price_level or i.dist_km is not None and i.flag != 'far' %}<span class="tv-id-meta" data-idea-meta>{% if i.rating %}&#9733; {{ i.rating|floatformat:1 }}{% if i.ratings %} <span>({{ i.ratings }})</span>{% endif %}{% endif %}{% if i.price_level %}{% if i.rating %} &middot; {% endif %}{{ i.price_level }}{% endif %}{% if i.dist_km is not None and i.flag != 'far' %}{% if i.rating or i.price_level %} &middot; {% endif %}{{ i.dist_km|floatformat:"-1" }} km from the centre{% endif %}</span>{% endif %}
  {% if i.visit or i.price or i.book or i.note %}<div class="tv-id-tags">{% if i.visit %}<span class="tv-id-tag">{{ i.visit }}</span>{% endif %}{% if i.price %}<span class="tv-id-tag">{{ i.price }}</span>{% endif %}{% if i.book %}<span class="tv-id-tag book">Book ahead</span>{% endif %}{% if i.note %}<span class="tv-id-tag note">{{ i.note }}</span>{% endif %}</div>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.far { color: #0C447C; background: #E6F1FB; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-card.is-dim .tv-id-pick b, .tv-id-card.is-dim .tv-id-blurb, .tv-id-card.is-dim .tv-id-tags { opacity: .62; }
.tv-id-flag { align-self: flex-start; font-size: .78rem; font-weight: 600; color: #6B3A00; background: #FCEFD9; border-radius: 999px; padding: 3px 10px; }
.tv-id-flag.is-far { color: #0C447C; background: #E6F1FB; }
.tv-id-flag.is-nf { color: #45545A; background: #EEF1F2; }
.tv-id-out { grid-column: 1 / -1; border: 1px solid #D9E0E3; border-radius: 12px; background: #F7F9FA; padding: 0 12px; }
.tv-id-out > summary { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; padding: 12px 0; cursor: pointer; list-style: none; }
.tv-id-out > summary::-webkit-details-marker { display: none; }
.tv-id-out > summary::before { content: "\25B8"; color: #5B6B72; }
.tv-id-out[open] > summary::before { content: "\25BE"; }
.tv-id-out > summary span { font-size: .85rem; color: #5B6B72; }
.tv-id-out-body { padding: 0 0 12px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
        (r'''.tv-spend-add .form-control { width: 100%; min-width: 0; height: 38px; box-sizing: border-box; }
.tv-spend-add button { height: 38px; white-space: nowrap; }
.tv-spend-add label { font-size: .8rem; color: var(--alv-ink-soft); margin: 0 0 2px; }
.tv-spend-day { padding: 8px 0 4px; border-top: 1px solid var(--alv-line-soft); scroll-margin-top: 80px; }
''',
         r'''.tv-spend-add .form-control { width: 100%; min-width: 0; height: 38px; box-sizing: border-box; }
.tv-spend-add button { height: 38px; white-space: nowrap; }
/* RA10, 21 Nov 2026 - the Currency drop-down was taller than the rest: base.html's select.form-control:not([size]):not([multiple]) { height: auto } outranks .tv-spend-add .form-control, so match its shape. */
.tv-spend-add select.form-control:not([size]):not([multiple]) { height: 38px; padding-top: 0; padding-bottom: 0; }
.tv-spend-add label { font-size: .8rem; color: var(--alv-ink-soft); margin: 0 0 2px; }
.tv-spend-day { padding: 8px 0 4px; border-top: 1px solid var(--alv-line-soft); scroll-margin-top: 80px; }
'''),
        (r'''details.tv-spend-row[open] > summary { font-weight: 600; }
.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
/* RA09, 21 Nov 2026 - Google checks left. */
''',
         r'''details.tv-spend-row[open] > summary { font-weight: 600; }
.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-trash { border: 0; background: none; padding: 0 2px 0 10px; color: #B4433A; cursor: pointer; font-size: .9em; line-height: 1; }
.tv-spend-trash:hover, .tv-spend-trash:focus { color: #8A2A22; }
.tv-bud-tools { display: inline-flex; gap: 6px; align-items: center; }
.tv-bud-tools .btn { min-width: 34px; }
.tv-bud-trash, .tv-bud-trash:hover { color: #B4433A; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
/* RA09, 21 Nov 2026 - Google checks left. */
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'google_allowance.html'), [
        (r'''    <button type="submit" class="btn action-primary">Save</button>
</form>
</div>
{% render_help_modal "travel" %}
''',
         r'''    <button type="submit" class="btn action-primary">Save</button>
</form>
{# RA10, 21 Nov 2026 - who used the checks. Demetri: "Can we check which user used the 35 so far for today?" #}
<div class="form-card" style="max-width: 640px; margin-top: 16px" data-google-used>
    <p style="font-weight: 700; margin: 0 0 4px">Who used them</p>
    <p class="small tv-sub" style="margin: 0 0 10px">Every Google check, by person, what for and trip. <b>Alivente itself</b> is the morning catch-up and the key check.</p>
    <p class="small" style="font-weight: 700; margin: 8px 0 4px">Today</p>
    {% if used.today %}<table class="table table-sm small" style="margin: 0" data-google-used-today><thead><tr><th>Who</th><th>What for</th><th>Trip</th><th style="text-align: right">Checks</th></tr></thead><tbody>{% for r in used.today %}<tr><td>{{ r.who }}</td><td>{{ r.why }}</td><td>{{ r.trip|default:"&ndash;" }}</td><td style="text-align: right">{{ r.n }}</td></tr>{% endfor %}</tbody></table>{% else %}<p class="small tv-sub" style="margin: 0">None yet today.</p>{% endif %}
    <p class="small" style="font-weight: 700; margin: 14px 0 4px">This month</p>
    {% if used.month %}<table class="table table-sm small" style="margin: 0" data-google-used-month><thead><tr><th>Who</th><th>What for</th><th>Trip</th><th style="text-align: right">Checks</th></tr></thead><tbody>{% for r in used.month %}<tr><td>{{ r.who }}</td><td>{{ r.why }}</td><td>{{ r.trip|default:"&ndash;" }}</td><td style="text-align: right">{{ r.n }}</td></tr>{% endfor %}</tbody></table>{% else %}<p class="small tv-sub" style="margin: 0">None yet this month.</p>{% endif %}
    <p class="small tv-sub" style="margin: 10px 0 0">Listed from late November 2026; earlier checks are in the totals above but not listed here.</p>
</div>
</div>
{% render_help_modal "travel" %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv22-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv23-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv22-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv23-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. These are kept apart at the end of the city, under <b>Outside what you asked for</b> &ndash; tap it to open. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>. One Google can&rsquo;t find at all says <b>Not found on Google</b> in grey &ndash; you can still tick it.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
'''),
    ]),
    (os.path.join('travel', 'views_budget.py'), [
        (r'''                             '%d a day.' % (m, d))
            return redirect('travel:google_allowance')
    return render(request, 'travel/google_allowance.html', {
        'a': a, 'gq': gquota.usage(),
        'back': request.GET.get('back') or '/travel/'})
''',
         r'''                             '%d a day.' % (m, d))
            return redirect('travel:google_allowance')
    try:                                # RA10 - who used them
        used = gquota.used_by()
    except Exception:                                   # noqa: BLE001
        used = {'today': [], 'month': []}
    return render(request, 'travel/google_allowance.html', {
        'a': a, 'gq': gquota.usage(), 'used': used,
        'back': request.GET.get('back') or '/travel/'})
'''),
    ]),
    (os.path.join('travel', 'views_ideas.py'), [
        (r'''from .views import span, travel_view
from .views_places import _trip


''',
         r'''from .views import span, travel_view
from .views_places import _trip


# RA10, 21 Nov 2026 - the reasons a suggestion is outside what you asked
# for, in the order their groups are shown. Not found on Google is not one:
# it stays with the rest, with its note.
OUTSIDE = {'far': 'Further from the centre than you asked',
           'closed': 'Closed on your days',
           'temp': 'Temporarily closed'}


'''),
        (r'''    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
        if i.new and i.state == '' and first_new is None:
            first_new = i.pk
''',
         r'''    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
    # RA10, 21 Nov 2026 - outside what you asked for (too far, closed on
    # your days, temporarily closed) goes to its own closed section at the
    # end of the city (Demetri: "Let's put this in RA10. Let's start it
    # closed for now."), so Go to the first goes to one that fits if any.
    for i in sorted(all_ideas, key=lambda i: i.flag in OUTSIDE):
        if i.new and i.state == '' and first_new is None:
            first_new = i.pk
'''),
        (r'''        mine = [i for i in all_ideas if i.city == c and (
            i.state == '' or (show_hidden and i.state == 'hidden'))]
        by = []
        for k, n, _w in ID.INTERESTS + [('', 'Other', '')]:
            these = [i for i in mine if (i.interest or '') == k or (
                k == '' and i.interest not in ID.LABEL)]
            for i in these:
                i.ticked = str(i.pk) in ticked
            # RA03 - the greyed out ones last in their group.
            these.sort(key=lambda i: bool(i.flag))
            if these:
                by.append({'name': n, 'ideas': these})
        groups.append({'city': c, 'by': by,
                       'n': sum(1 for i in mine if i.state == ''),
                       'added': sum(1 for i in all_ideas if i.city == c
''',
         r'''        mine = [i for i in all_ideas if i.city == c and (
            i.state == '' or (show_hidden and i.state == 'hidden'))]
        for i in mine:
            i.ticked = str(i.pk) in ticked
        fits = [i for i in mine if i.flag not in OUTSIDE]
        by = []
        for k, n, _w in ID.INTERESTS + [('', 'Other', '')]:
            these = [i for i in fits if (i.interest or '') == k or (
                k == '' and i.interest not in ID.LABEL)]
            if these:
                by.append({'name': n, 'ideas': these})
        out = []                        # RA10 - grouped by why
        for f, n in OUTSIDE.items():
            these = [i for i in mine if i.flag == f]
            if these:
                out.append({'name': n, 'ideas': these})
        n_out = sum(len(b['ideas']) for b in out)
        groups.append({'city': c, 'by': by, 'out': out, 'n_out': n_out,
                       'out_open': any(i.ticked for b in out
                                       for i in b['ideas']) or any(
                           i.pk == first_new for b in out
                           for i in b['ideas']),
                       'n': sum(1 for i in mine if i.state == ''),
                       'added': sum(1 for i in all_ideas if i.city == c
'''),
        (r'''        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        # RA03 - said when the opening days and distances were not
        # checked on Google (no key yet).
''',
         r'''        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        'n_new_out': sum(1 for i in shown if i.new and i.flag in OUTSIDE),
        # RA03 - said when the opening days and distances were not
        # checked on Google (no key yet).
'''),
        (r'''    cities = ID.waiting(t).values('city').distinct().count()
    limit = min(n + cities, u['day_left'], u['month_left'], 60)
    used, done = ID.recheck([t], limit)
    left = ID.waiting(t).count()
    messages.success(request, '%d suggestion%s checked on Google%s.' % (
''',
         r'''    cities = ID.waiting(t).values('city').distinct().count()
    limit = min(n + cities, u['day_left'], u['month_left'], 60)
    with gquota.purpose('now', user=request.user.pk):  # RA10 - who
        used, done = ID.recheck([t], limit)
    left = ID.waiting(t).count()
    messages.success(request, '%d suggestion%s checked on Google%s.' % (
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget.html'), [
        (r'''{% if bud.set %}
<section class="form-card tv-bud" data-budget>
    <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas fa-wallet" aria-hidden="true"></i> Daily spending budget</h3>{% if can_spend %}<button type="button" class="btn action-secondary btn-sm" data-budget-edit aria-expanded="false"><i class="fas fa-pen" aria-hidden="true"></i> Change</button>{% endif %}</div>
    <p class="tv-sub" style="margin: 2px 0 12px" data-budget-sum>{% if bud.by == 'total' %}<b class="tv-ink">{{ bud.total_label }}</b> for the holiday{% if bud.days %} &divide; {{ bud.days }} day{{ bud.days|pluralize }} = {{ bud.per_day_label }} a day{% endif %}{% else %}{{ bud.per_day_label }} a day{% if bud.days %} &times; {{ bud.days }} day{{ bud.days|pluralize }} = <b class="tv-ink">{{ bud.total_label }}</b> for the holiday{% endif %}{% endif %}. Bookings are not part of it.</p>
    <div class="tv-bud-grid">
''',
         r'''{% if bud.set %}
<section class="form-card tv-bud" data-budget>
    <div class="tv-row"><h3 class="form-section-title" style="margin: 0"><i class="fas fa-wallet" aria-hidden="true"></i> Daily spending budget</h3>{% if can_spend %}<span class="tv-bud-tools"><button type="button" class="btn action-secondary btn-sm" data-budget-edit aria-expanded="false" title="Change the budget" aria-label="Change the budget"><i class="fas fa-pen" aria-hidden="true"></i></button>{% if bud.set %}<form method="post" action="{% url 'travel:budget_save' trip.pk %}" style="margin: 0">{% csrf_token %}<button type="submit" name="clear" value="1" class="btn action-secondary btn-sm tv-bud-trash" title="Remove the budget" aria-label="Remove the budget" onclick="return confirm('Remove the budget? Your spending stays.')" data-budget-clear><i class="fas fa-trash-alt" aria-hidden="true"></i></button></form>{% endif %}</span>{% endif %}</div>
    <p class="tv-sub" style="margin: 2px 0 12px" data-budget-sum>{% if bud.by == 'total' %}<b class="tv-ink">{{ bud.total_label }}</b> for the holiday{% if bud.days %} &divide; {{ bud.days }} day{{ bud.days|pluralize }} = {{ bud.per_day_label }} a day{% endif %}{% else %}{{ bud.per_day_label }} a day{% if bud.days %} &times; {{ bud.days }} day{{ bud.days|pluralize }} = <b class="tv-ink">{{ bud.total_label }}</b> for the holiday{% endif %}{% endif %}. Bookings are not part of it.</p>
    <div class="tv-bud-grid">
'''),
        (r'''
<section class="form-card" data-spending>
    {% comment %} RA07, 19 Nov 2026 - only a day of the trip; click a spending to change it; any outside the trip's dates listed apart. {% endcomment %}
    <h3 class="form-section-title">Daily spending</h3>
    {% if can_spend %}{% if trip_start %}<form method="post" action="{% url 'travel:spend_add' trip.pk %}" class="tv-spend-add" data-spend-form>{% csrf_token %}
''',
         r'''
<section class="form-card" data-spending>
    {% comment %} RA10, 21 Nov 2026 - Demetri: "Can we not rather just put a trash can next to the pencil? Then remove the Delete button from under the amount?" {% endcomment %}
{% comment %} RA07, 19 Nov 2026 - only a day of the trip; click a spending to change it; any outside the trip's dates listed apart. {% endcomment %}
    <h3 class="form-section-title">Daily spending</h3>
    {% if can_spend %}{% if trip_start %}<form method="post" action="{% url 'travel:spend_add' trip.pk %}" class="tv-spend-add" data-spend-form>{% csrf_token %}
'''),
        (r'''    <div class="tv-spend-day{% if d.outside %} is-outside{% endif %}" data-spend-day="{{ d.day|date:'Y-m-d' }}" id="sp{{ d.day|date:'Ymd' }}">
        <div class="tv-row"><b>{% if d.day == today %}Today &middot; {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over and not d.outside %}tv-over{% else %}tv-sub{% endif %}">{{ d.label }}{% if bud.per_day_label and not d.outside %}{% if d.over %} &middot; {{ d.over_by }} over{% else %} of {{ bud.per_day_label }}{% endif %}{% endif %}</span></div>
        {% for s in d.rows %}{% if can_spend %}<details class="tv-spend-row" data-spend="{{ s.pk }}"><summary class="tv-row" title="Change or delete"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }} <i class="fas fa-pen tv-sub" aria-hidden="true"></i></span></summary>
            <form method="post" action="{% url 'travel:spend_edit' s.pk %}" class="tv-spend-add tv-spend-edit" data-spend-edit>{% csrf_token %}
                <div><label for="se-a{{ s.pk }}">Amount</label><input id="se-a{{ s.pk }}" name="amount" class="form-control tv-money" inputmode="decimal" value="{{ s.amount }}" required></div>
                <div><label for="se-c{{ s.pk }}">Currency</label><select id="se-c{{ s.pk }}" name="currency" class="form-control">{% for c in currencies %}<option value="{{ c }}"{% if c == s.currency %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
                <div><label for="se-d{{ s.pk }}">Day</label><input id="se-d{{ s.pk }}" type="date" name="day" class="form-control" value="{% if d.outside %}{{ spend_day|date:'Y-m-d' }}{% else %}{{ s.day|date:'Y-m-d' }}{% endif %}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}"></div>
                <div class="tv-spend-note"><label for="se-n{{ s.pk }}">Note (optional)</label><input id="se-n{{ s.pk }}" name="what" class="form-control" maxlength="120" value="{{ s.what }}"></div>
                <button type="submit" class="btn action-primary btn-sm">Save</button>
                <button type="submit" form="sd{{ s.pk }}" class="btn action-secondary action-danger btn-sm" onclick="return confirm('Delete this spending?')" data-spend-del>Delete</button>
            </form><form method="post" action="{% url 'travel:spend_delete' s.pk %}" id="sd{{ s.pk }}" hidden>{% csrf_token %}</form>
        </details>{% else %}<div class="tv-row tv-spend-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }}</span></div>{% endif %}{% endfor %}
''',
         r'''    <div class="tv-spend-day{% if d.outside %} is-outside{% endif %}" data-spend-day="{{ d.day|date:'Y-m-d' }}" id="sp{{ d.day|date:'Ymd' }}">
        <div class="tv-row"><b>{% if d.day == today %}Today &middot; {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over and not d.outside %}tv-over{% else %}tv-sub{% endif %}">{{ d.label }}{% if bud.per_day_label and not d.outside %}{% if d.over %} &middot; {{ d.over_by }} over{% else %} of {{ bud.per_day_label }}{% endif %}{% endif %}</span></div>
        {% for s in d.rows %}{% if can_spend %}<details class="tv-spend-row" data-spend="{{ s.pk }}"><summary class="tv-row" title="Change or delete"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }} <i class="fas fa-pen tv-sub" aria-hidden="true"></i><button type="submit" form="sd{{ s.pk }}" class="tv-spend-trash" title="Delete" aria-label="Delete this spending" onclick="return confirm('Delete this spending?')" data-spend-del><i class="fas fa-trash-alt" aria-hidden="true"></i></button></span></summary>
            <form method="post" action="{% url 'travel:spend_edit' s.pk %}" class="tv-spend-add tv-spend-edit" data-spend-edit>{% csrf_token %}
                <div><label for="se-a{{ s.pk }}">Amount</label><input id="se-a{{ s.pk }}" name="amount" class="form-control tv-money" inputmode="decimal" value="{{ s.amount }}" required></div>
                <div><label for="se-c{{ s.pk }}">Currency</label><select id="se-c{{ s.pk }}" name="currency" class="form-control">{% for c in currencies %}<option value="{{ c }}"{% if c == s.currency %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
                <div><label for="se-d{{ s.pk }}">Day</label><input id="se-d{{ s.pk }}" type="date" name="day" class="form-control" value="{% if d.outside %}{{ spend_day|date:'Y-m-d' }}{% else %}{{ s.day|date:'Y-m-d' }}{% endif %}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}"></div>
                <div class="tv-spend-note"><label for="se-n{{ s.pk }}">Note (optional)</label><input id="se-n{{ s.pk }}" name="what" class="form-control" maxlength="120" value="{{ s.what }}"></div>
                <button type="submit" class="btn action-primary btn-sm">Save</button>
            </form><form method="post" action="{% url 'travel:spend_delete' s.pk %}" id="sd{{ s.pk }}" hidden>{% csrf_token %}</form>
        </details>{% else %}<div class="tv-row tv-spend-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-sub">&middot; {{ s.orig_label }}</span>{% endif %}</span><span class="tv-money">{{ s.eur_label }}</span></div>{% endif %}{% endfor %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget_form.html'), [
        (r'''{% comment %} RA05 - set the daily spending budget: a day's or the holiday's, the other worked out (Demetri: "Let's have both options - Add Total and calculate daily or vice versa"). {% endcomment %}
<form method="post" action="{% url 'travel:budget_save' trip.pk %}" class="tv-bud-form" data-budget-form data-days="{{ bud.days }}"{% if hidden %} hidden{% endif %}>{% csrf_token %}
''',
         r'''{% comment %} RA10, 21 Nov 2026 - Remove budget is the bin beside the pencil now (Demetri: "The Pencil should only be a pencil, add the trash can"). {% endcomment %}
{% comment %} RA05 - set the daily spending budget: a day's or the holiday's, the other worked out (Demetri: "Let's have both options - Add Total and calculate daily or vice versa"). {% endcomment %}
<form method="post" action="{% url 'travel:budget_save' trip.pk %}" class="tv-bud-form" data-budget-form data-days="{{ bud.days }}"{% if hidden %} hidden{% endif %}>{% csrf_token %}
'''),
        (r'''    </div>
    <p class="tv-sub small" style="margin: 6px 0 10px">Type either one &ndash; the other is worked out from the trip&rsquo;s {% if bud.days %}{{ bud.days }} days{% else %}days, once it has dates{% endif %}. The one ticked is kept if the trip&rsquo;s dates change.</p>
    <div style="display: flex; gap: 8px; flex-wrap: wrap"><button type="submit" class="btn action-primary btn-sm" data-budget-save>Save budget</button>{% if bud.set %}<button type="submit" name="clear" value="1" class="btn action-secondary action-danger btn-sm" style="margin-left: auto" onclick="return confirm('Remove the budget? Your spending stays.')" data-budget-clear>Remove budget</button>{% endif %}</div>
</form>
''',
         r'''    </div>
    <p class="tv-sub small" style="margin: 6px 0 10px">Type either one &ndash; the other is worked out from the trip&rsquo;s {% if bud.days %}{{ bud.days }} days{% else %}days, once it has dates{% endif %}. The one ticked is kept if the trip&rsquo;s dates change.</p>
    <div style="display: flex; gap: 8px; flex-wrap: wrap"><button type="submit" class="btn action-primary btn-sm" data-budget-save>Save budget</button></div>
</form>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_list.html'), [
        (r'''{% comment %} TR-12 - the suggestions, by city and then by what you like, inside the Add form; desk=True lays them out as a grid. {% endcomment %}
{% for g in groups %}<div class="{% if desk %}tv-id-grid{% else %}tv-id-list{% endif %}" data-idea-cityblock>
  <div class="tv-id-cityhead"><b>{{ g.city }}</b><span style="font-size: .85rem; color: #5B6B72">{{ g.n }} idea{{ g.n|pluralize }}{% if g.added %} &middot; {{ g.added }} added{% endif %}</span></div>
  {% for b in g.by %}<div class="tv-id-group">{{ b.name }}</div>
  {% for i in b.ideas %}{% include 'travel/_ideas_card.html' %}{% endfor %}{% endfor %}
  {% if not g.n %}<p class="tv-id-group" style="text-transform: none; letter-spacing: 0; font-weight: 400; font-size: .9rem">Nothing left to look at for {{ g.city }}.</p>{% endif %}
  <div class="tv-id-more"><button type="submit" formaction="{{ more_url }}" formnovalidate name="more" value="{{ g.city }}" data-idea-more>Show me more for {{ g.city }}</button><span style="font-size: .8rem; color: #5B6B72; text-align: center">About {{ per_city }} more &ndash; never one already shown, hidden or on your list</span></div>
''',
         r'''{% comment %} RA10, 21 Nov 2026 - what is outside what you asked for goes to its own section at the end of the city, closed to start, grouped by why (Demetri: "Let's put this in RA10. Let's start it closed for now."); open when one in it is ticked or is the first new one. {% endcomment %}
{% comment %} TR-12 - the suggestions, by city and then by what you like, inside the Add form; desk=True lays them out as a grid. {% endcomment %}
{% for g in groups %}<div class="{% if desk %}tv-id-grid{% else %}tv-id-list{% endif %}" data-idea-cityblock>
  <div class="tv-id-cityhead"><b>{{ g.city }}</b><span style="font-size: .85rem; color: #5B6B72">{{ g.n }} idea{{ g.n|pluralize }}{% if g.added %} &middot; {{ g.added }} added{% endif %}</span></div>
  {% for b in g.by %}<div class="tv-id-group">{{ b.name }}</div>
  {% for i in b.ideas %}{% include 'travel/_ideas_card.html' %}{% endfor %}{% endfor %}
  {% if g.out %}<details class="tv-id-out" data-idea-outside{% if g.out_open %} open{% endif %}><summary><b>Outside what you asked for ({{ g.n_out }})</b><span>Further than your km, closed on your days or temporarily closed &ndash; you can still tick them.</span></summary>
    <div class="{% if desk %}tv-id-grid{% else %}tv-id-list{% endif %} tv-id-out-body">{% for b in g.out %}<div class="tv-id-group">{{ b.name }}</div>
    {% for i in b.ideas %}{% include 'travel/_ideas_card.html' %}{% endfor %}{% endfor %}</div>
  </details>{% endif %}
  {% if not g.n %}<p class="tv-id-group" style="text-transform: none; letter-spacing: 0; font-weight: 400; font-size: .9rem">Nothing left to look at for {{ g.city }}.</p>{% endif %}
  <div class="tv-id-more"><button type="submit" formaction="{{ more_url }}" formnovalidate name="more" value="{{ g.city }}" data-idea-more>Show me more for {{ g.city }}</button><span style="font-size: .8rem; color: #5B6B72; text-align: center">About {{ per_city }} more &ndash; never one already shown, hidden or on your list</span></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_top.html'), [
        (r'''<p style="margin: 0; font-size: .88rem; color: #4A5A61">{% if saved %}Saved on the trip &middot; come back any time{% endif %}{% if hidden %} &middot; {{ hidden }} hidden as Not interested &middot; {% if show_hidden %}<a href="?{% if city %}city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Hide them</a>{% else %}<a href="?hidden=1{% if city %}&amp;city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Show them</a>{% endif %}{% endif %}</p>
{% comment %} TR-14 - what Show me more just brought. {% endcomment %}
{% if n_new %}<p style="margin: 0; font-size: .9rem" data-idea-newline><span class="tv-id-new">New</span> {{ n_new }} more idea{{ n_new|pluralize }}{% if new_city %} for {{ new_city }}{% endif %} &ndash; marked New. What you had ticked is still ticked.{% if first_new %} <a href="#new">Go to the first</a>{% endif %}</p>{% endif %}
''',
         r'''<p style="margin: 0; font-size: .88rem; color: #4A5A61">{% if saved %}Saved on the trip &middot; come back any time{% endif %}{% if hidden %} &middot; {{ hidden }} hidden as Not interested &middot; {% if show_hidden %}<a href="?{% if city %}city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Hide them</a>{% else %}<a href="?hidden=1{% if city %}&amp;city={{ city|urlencode }}{% endif %}" data-idea-showhidden>Show them</a>{% endif %}{% endif %}</p>
{% comment %} TR-14 - what Show me more just brought. {% endcomment %}
{% if n_new %}<p style="margin: 0; font-size: .9rem" data-idea-newline><span class="tv-id-new">New</span> {{ n_new }} more idea{{ n_new|pluralize }}{% if new_city %} for {{ new_city }}{% endif %}{% if n_new_out %} ({{ n_new_out }} of them outside what you asked for){% endif %} &ndash; marked New. What you had ticked is still ticked.{% if first_new %} <a href="#new">Go to the first</a>{% endif %}</p>{% endif %}
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
    raise SystemExit('RA10 REFUSED: %s' % msg)


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
    if "'test_ra10_google_checks.py'" in read(pq):
        print('RA10 already applied.')
        return 0
    if "'test_ra09_google_allowance.py'" not in read(pq):
        refuse('RA09 (apply_ra09_google_allowance.py) is not applied - this round registers after it.')
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
        print('RA10 --check: %d file(s) would change, none written; %d '
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
    print('RA10 applied - Not found on Google; who used each check. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
