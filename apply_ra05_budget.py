# -*- coding: utf-8 -*-
"""apply_ra05_budget.py - round RA05, 19 Nov 2026.

RELEASE RA05 - TRAVEL: THE DAILY SPENDING BUDGET, + SPENDING, AND SHARING
THE COSTS OR NOT. Pushed together with RA04.

    Demetri, 19 Nov: "we only had the ability to set a budget for total
    holiday spend (which would be a calculation based on average daily
    spend). Then it keeps track of my actual daily spend vs. the budgeted
    one and shows me if I am ahead or behind the schedule. Obviously these
    daily spends get added to the trip costs so that I can analyse my
    complete trip costs. Also I can see where I have spent more on a day";
    "Let's have both options - Add Total and calculate daily or vice
    versa"; "+Spending should default to Euros, today's date, and optional
    note blank - for quick entry"; restaurant meals added by hand, booked
    activity tickets stay with the bookings; and "I must have the option to
    either share or not share costs and budget information with other
    travellers ... shared travellers should be able to see the budget and
    the costs, but should not be able to add spending."

    - Costs tab: the daily spending budget (a day's or the holiday's),
      ahead or behind plan, what a day keeps you on budget, a bar for each
      day (red when over), + Spending and the spending by day. The trip
      total is the bookings plus the spending - also in By kind, the PDFs,
      the trips list and Compare (Daily spending, per day).
    - Phone: the Today line, the Costs card, + Spending and budget pages.
    - Share: Share costs and budget. Off: no money at all for the others,
      and their booking edits never touch the costs.
    - Help on the computer and the phone; the phone app moves to tv19-1.
    - Migration travel 0012: run python manage.py migrate locally first.

The suite, budget.py, views_budget.py, the migration and the new templates
ship beside this patcher. Stands on RA04. Idempotent. Edits backed up to
.bak_ra05.
"""
import os
import sys

SUFFIX = '.bak_ra05'
MARK = 'RA05, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra05_budget.py',
    'travel/budget.py',
    'travel/views_budget.py',
    'travel/migrations/0012_budget.py',
    'travel/templates/travel/_budget.html',
    'travel/templates/travel/_budget_chart.html',
    'travel/templates/travel/_budget_form.html',
    'travel/templates/travel/_budget_js.html',
    'travel/templates/travel/m/budget.html',
    'travel/templates/travel/m/spend.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra03_suggestions.py',
    # RA04, 19 Nov 2026 - an email when a key stops working.
    'test_ra04_key_email.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra03_suggestions.py',
    # RA04, 19 Nov 2026 - an email when a key stops working.
    'test_ra04_key_email.py',
    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    'test_ra05_budget.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA04, 19 Nov 2026 - an email when a key stops working.
    '.bak_ra04',
]

''',
         r'''    # RA04, 19 Nov 2026 - an email when a key stops working.
    '.bak_ra04',
    # RA05, 19 Nov 2026 - the daily spending budget; sharing the costs.
    '.bak_ra05',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong> (the form opens when you press it): give it a name, and if you like its dates and countries. <strong>The bookings set the dates</strong>: once a trip has bookings with dates, it runs from the first booking&rsquo;s start to the last one&rsquo;s end, whatever was typed &mdash; typed dates are only for planning before anything is booked. <strong>The trip&rsquo;s countries come from its bookings</strong> &mdash; where each hotel, car or restaurant is and where each flight lands, read from the email, or worked out from the address, the airport or the town. Your <strong>home country (Cyprus) is left out</strong>, so flights home do not add it; it is shown only for a trip that never leaves it. Under <strong>Edit trip &rarr; Other countries</strong> type a country only if you are going there with nothing booked yet. The name is yours to choose.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>

''',
         r'''    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong> (the form opens when you press it): give it a name, and if you like its dates and countries. <strong>The bookings set the dates</strong>: once a trip has bookings with dates, it runs from the first booking&rsquo;s start to the last one&rsquo;s end, whatever was typed &mdash; typed dates are only for planning before anything is booked. <strong>The trip&rsquo;s countries come from its bookings</strong> &mdash; where each hotel, car or restaurant is and where each flight lands, read from the email, or worked out from the address, the airport or the town. Your <strong>home country (Cyprus) is left out</strong>, so flights home do not add it; it is shown only for a trip that never leaves it. Under <strong>Edit trip &rarr; Other countries</strong> type a country only if you are going there with nothing booked yet. The name is yours to choose.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and, if you choose, the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
    <p data-help-share-money><strong>Share costs and budget</strong> (on the Share page, under the names): ticked, the people on the trip see the daily spending budget and every cost, but cannot add spending or change the budget. Not ticked, they see no money at all &ndash; no Costs tab, no amounts on bookings, on the trips list, in the PDFs or in Compare &ndash; and when they edit a booking there is no Cost section, so your amounts stay exactly as they are. Trips already shared start ticked.</p>
  </article>

'''),
        (r'''    <p><strong>After a trip.</strong> The day after a trip ends, if any booking still says To pay or Part paid, the trip asks whether everything is paid: the bookings are listed, ticked, with the amount paid in euros (change it if the card statement says otherwise). <strong>Mark ticked ones paid</strong>, <strong>Leave as it is</strong> (not asked again) or <strong>Ask me again in a week</strong>. Nothing is marked paid without you; each change is in the booking&rsquo;s Changes. The trip&rsquo;s card on Travel and the phone&rsquo;s Today show what is still to pay until then.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>

''',
         r'''    <p><strong>After a trip.</strong> The day after a trip ends, if any booking still says To pay or Part paid, the trip asks whether everything is paid: the bookings are listed, ticked, with the amount paid in euros (change it if the card statement says otherwise). <strong>Mark ticked ones paid</strong>, <strong>Leave as it is</strong> (not asked again) or <strong>Ask me again in a week</strong>. Nothing is marked paid without you; each change is in the booking&rsquo;s Changes. The trip&rsquo;s card on Travel and the phone&rsquo;s Today show what is still to pay until then.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change.</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. Only the trip&rsquo;s owner adds spending, sets the budget or deletes spending (&times;).</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan; after it, how the whole trip came out against the budget.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong>, and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
  </article>

'''),
    ]),
    (os.path.join('test_travel_seven.py'), [
        (r'''            h = M.get('/travel/m/compare/?t=%d&t=%d' % (g.pk, sw.pk)) \
                .content.decode()
            ok(h.count('data-compare-row') == 7, 'PHONE: the figures, row by row')
            h = A.get('/travel/?show=all').content.decode()
            ok('data-compare-form' in h and h.count('name="t"') == 3,
''',
         r'''            h = M.get('/travel/m/compare/?t=%d&t=%d' % (g.pk, sw.pk)) \
                .content.decode()
            # RA05, 19 Nov 2026 - and Daily spending, per day: eight rows.
            ok(h.count('data-compare-row') == 8, 'PHONE: the figures, row by row')
            h = A.get('/travel/?show=all').content.decode()
            ok('data-compare-form' in h and h.count('name="t"') == 3,
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
''',
         r'''  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
/* RA05, 19 Nov 2026 - the daily spending budget on the phone: the Today line, the Costs card and its day chart, + Spending. */
.tv-ink { color: var(--tv-ink); }
.tv-over { color: #A32D2D; font-weight: 600; }
.tv-good { color: var(--tv-good); font-weight: 600; }
.tv-bud-today { border: 1.5px solid var(--tv-teal); }
.tv-bud-big { font-size: 20px; font-weight: 700; }
.tv-meter.is-amber span { background: #BA7517; } .tv-meter.is-red span { background: #C0392B; }
.tv-bud-bars { position: relative; display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 3px; height: 90px; border-bottom: 1px solid #C9D3D6; }
.tv-bud-col { position: relative; z-index: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; color: inherit; text-decoration: none; min-width: 0; }
.tv-bud-col i { display: block; width: 100%; border-radius: 3px 3px 0 0; background: #2E9A6B; }
.tv-bud-col.is-over i { background: #D64545; }
.tv-bud-col.is-today i { outline: 2px solid var(--tv-ink); outline-offset: 1px; }
.tv-bud-col small { display: none; }
.tv-bud-line { position: absolute; left: 0; right: 0; border-top: 2px dashed var(--tv-teal); pointer-events: none; }
.tv-bud-days { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 3px; margin-top: 3px; font-size: 9px; color: var(--tv-soft); text-align: center; overflow: hidden; }
.tv-bud-days span { white-space: nowrap; overflow: hidden; }
.tv-bud-days .is-today { color: var(--tv-ink); font-weight: 700; }
.tv-bud-days i { font-style: normal; } .tv-bud-days .w { display: none; }
.tv-amount { font-size: 26px !important; min-height: 56px !important; }
.tv-two { display: grid; grid-template-columns: 1fr 1.3fr; gap: 8px; }
.tv-spend-day { padding-top: 6px; scroll-margin-top: 70px; }
'''),
    ]),
    (os.path.join('travel', 'compare.py'), [
        (r'''                'train': '#1D2B31', 'ferry': '#3F6F78', 'transfer': '#8A9BA2',
                'activity': '#B7C4C9', 'restaurant': '#D5A55A',
                'other': '#DDE3E5'}
MAX = 6

''',
         r'''                'train': '#1D2B31', 'ferry': '#3F6F78', 'transfer': '#8A9BA2',
                'activity': '#B7C4C9', 'restaurant': '#D5A55A',
                'other': '#DDE3E5', 'spend': '#9A5B00'}
MAX = 6

'''),
        (r'''def trip_settle(request, trip_id):
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    what = request.POST.get('what')
    if what == 'leave':
''',
         r'''def trip_settle(request, trip_id):
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    from .budget import money_ok
    if not money_ok(t, request.user):       # RA05 - nor settle them up
        raise Http404
    what = request.POST.get('what')
    if what == 'leave':
'''),
        (r'''    car_days = sum(max((b.end_date - b.start_date).days, 1)
                   for b in cars if b.start_date and b.end_date)
    money = totals(bs)
    total = sum((b.amount_eur for b in bs if b.amount_eur is not None),
                Decimal('0'))
    kinds = []
    for k, label in Booking.KINDS:
''',
         r'''    car_days = sum(max((b.end_date - b.start_date).days, 1)
                   for b in cars if b.start_date and b.end_date)
    # RA05, 19 Nov 2026 - daily spending is part of the trip's costs.
    spends = [s for s in t.spends.all() if s.amount_eur is not None]
    money = totals(bs, spends)
    total = sum((b.amount_eur for b in bs if b.amount_eur is not None),
                Decimal('0')) + _sum(spends)
    kinds = []
    for k, label in Booking.KINDS:
'''),
        (r'''                          'colour': KIND_COLOURS.get(k, '#DDE3E5'),
                          'icon': ICONS.get(k, ICONS['other'])})
    for k in kinds:
        k['pct'] = int(k['eur'] / total * 100) if total else 0
''',
         r'''                          'colour': KIND_COLOURS.get(k, '#DDE3E5'),
                          'icon': ICONS.get(k, ICONS['other'])})
    if spends:
        kinds.append({'kind': 'spend', 'label': 'Daily spending',
                      'eur': _sum(spends),
                      'colour': KIND_COLOURS['spend'],
                      'icon': ICONS['spend']})
    for k in kinds:
        k['pct'] = int(k['eur'] / total * 100) if total else 0
'''),
        (r'''                     len(priced('restaurant'))),
        'activities': _sum(by.get('activity', [])) or None,
        'kinds': kinds, 'hotels': hotels,
        'pending': money['pending'],
''',
         r'''                     len(priced('restaurant'))),
        'activities': _sum(by.get('activity', [])) or None,
        # RA05 - what was spent a day, besides the bookings.
        'spend_day': _div(_sum(spends), max(nights + 1, 1))
        if spends else None,
        'kinds': kinds, 'hotels': hotels,
        'pending': money['pending'],
'''),
        (r'''        ('meal', 'Restaurants booked, per meal', ''),
        ('activities', 'Activities & tickets', 'the total'),
        ('per_day', 'Whole trip, per day', 'the total / its nights')]

''',
         r'''        ('meal', 'Restaurants booked, per meal', ''),
        ('activities', 'Activities & tickets', 'the total'),
        ('spend_day', 'Daily spending, per day', 'meals, taxis, tickets '
         'at the door'),
        ('per_day', 'Whole trip, per day', 'the total / its nights')]

'''),
        (r'''        if x.isdigit() and int(x) not in ids:
            ids.append(int(x))
    trips = {t.pk: t for t in trips_for(request.user).filter(pk__in=ids)}
    return [trips[i] for i in ids if i in trips][:MAX]

''',
         r'''        if x.isdigit() and int(x) not in ids:
            ids.append(int(x))
    from .budget import money_ok
    trips = {t.pk: t for t in trips_for(request.user).filter(pk__in=ids)
             if money_ok(t, request.user)}
    return [trips[i] for i in ids if i in trips][:MAX]

'''),
        (r'''    phone = (request.resolver_match.url_name or '').startswith('m_')
    picked = chosen(request)
    every = list(trips_for(request.user))
    for t in every:
        t.start, t.end = span(t, list(t.bookings.all()))
''',
         r'''    phone = (request.resolver_match.url_name or '').startswith('m_')
    picked = chosen(request)
    # RA05, 19 Nov 2026 - comparing is all costs: only the trips whose
    # costs this person may see.
    from .budget import money_ok
    every = [t for t in trips_for(request.user) if money_ok(t, request.user)]
    for t in every:
        t.start, t.end = span(t, list(t.bookings.all()))
'''),
        (r'''                        key=lambda h: h['night'] or 0),
                    'legend': [{'label': l, 'colour': KIND_COLOURS[k]}
                               for k, l in Booking.KINDS
                               if any(x['kind'] == k for f in figs
                                      for x in f['kinds'])]})
''',
         r'''                        key=lambda h: h['night'] or 0),
                    'legend': [{'label': l, 'colour': KIND_COLOURS[k]}
                               for k, l in Booking.KINDS +
                               [('spend', 'Daily spending')]
                               if any(x['kind'] == k for f in figs
                                      for x in f['kinds'])]})
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    settle_off = models.BooleanField(default=False)
    settle_after = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    settle_off = models.BooleanField(default=False)
    settle_after = models.DateField(null=True, blank=True)
    # RA05, 19 Nov 2026 - THE DAILY SPENDING BUDGET (travel/budget.py).
    # Demetri: "What if our budget didn't include budgeting for Hotel, Car
    # Rental and Flights. These were just actuals that came in from the
    # Booking ... Then we only had the ability to set a budget for total
    # holiday spend (which would be a calculation based on average daily
    # spend)"; "Let's have both options - Add Total and calculate daily or
    # vice versa." budget is in euros - a day's when budget_by is 'day',
    # the holiday's when 'total'; the other is worked out from the days.
    # share_money - "I must have the option to either share or not share
    # costs and budget information with other travellers". On: they see
    # the budget and the costs, never add spending. Off: no money at all.
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                 blank=True)
    budget_by = models.CharField(max_length=5, default='day')
    share_money = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''    def __str__(self):
        return self.title

    def eur_of(self, value):
''',
         r'''    def __str__(self):
        return self.title

    def save(self, *a, **kw):
        # RA05 - a booking whose costs were blanked for someone who may not
        # see them (travel/budget.py) is for showing only, never saving.
        if getattr(self, '_money_hidden', False):
            raise RuntimeError('A booking with its costs hidden is not saved.')
        return super().save(*a, **kw)

    def eur_of(self, value):
'''),
        (r'''    def __str__(self):
        return '%s (%s)' % (self.name, self.city)
''',
         r'''    def __str__(self):
        return '%s (%s)' % (self.name, self.city)


# RA05, 19 Nov 2026 - DAILY SPENDING: what is not a booking. Demetri:
# "it keeps track of my actual daily spend vs. the budgeted one and shows me
# if I am ahead or behind the schedule. Obviously these daily spends get
# added to the trip costs"; restaurant meals are added here by hand, booked
# activity tickets stay with the bookings.
class Spend(models.Model):
    """Money spent on the trip that is not a booking: a meal, a taxi,
    tickets at the door. Added by the trip's owner only."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='spends')
    day = models.DateField()
    what = models.CharField(max_length=120, blank=True, default='')
    currency = models.CharField(max_length=3, default='EUR')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True)
    fx_rate = models.DecimalField(max_digits=14, decimal_places=6, null=True,
                                  blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_spends'
        ordering = ['-day', '-id']

    def __str__(self):
        return '%s %s %s' % (self.day, self.amount, self.currency)
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, dayorder, fx, ideas, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
from .views import (coming_up, eur, included, requests_for, shape, span,
                    totals, travel_view)

''',
         r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, budget, dayorder, fx, ideas, inbox, planner
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
from .views import (coming_up, eur, included, money_state, requests_for,
                    shape, span,
                    totals, travel_view)

'''),
        (r'''# RA01, 18 Nov 2026 - their drop-downs.
# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
SW_VERSION = 'tv18-1'
SW_ASSETS = 'c666f896f51c'


''',
         r'''# RA01, 18 Nov 2026 - their drop-downs.
# RA03, 19 Nov 2026 - greyed out suggestions; Select to delete.
# RA05, 19 Nov 2026 - the daily spending budget, + Spending.
SW_VERSION = 'tv19-1'
SW_ASSETS = '95a8d6229257'


'''),
        (r'''def _trip_list(user):
    out = []
    for t in trips_for(user).prefetch_related('bookings', 'shared_with'):
        bs = list(t.bookings.all())
        t.start, t.end = span(t, bs)
        t.n = len(bs)
        t.money = totals(bs)
        t.people = [t.owner] + list(t.shared_with.all())
        out.append(t)
''',
         r'''def _trip_list(user):
    out = []
    for t in trips_for(user).prefetch_related('bookings', 'spends',
                                              'shared_with'):
        bs = list(t.bookings.all())
        t.start, t.end = span(t, bs)
        t.n = len(bs)
        t.show_money = budget.money_ok(t, user)               # RA05
        t.money = totals(bs, list(t.spends.all())) if t.show_money \
            else totals([])
        t.people = [t.owner] + list(t.shared_with.all())
        out.append(t)
'''),
        (r'''            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start, saved)
        ctx['coming'] = coming_up(bs, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
''',
         r'''            ctx['in_days'] = (trip.start - day).days
            ctx['first_rows'] = day_rows(bs, pl, trip.start, saved)
        # RA05, 19 Nov 2026 - the Today line: spent today, a day left.
        shaped = [shape(b) for b in bs]
        start, end = span(trip, shaped)
        if budget.hide(trip, me, shaped):
            spends = list(trip.spends.all())
            budget.convert_pending(spends, limit=2)
            ctx['bud'] = budget.summary(trip, spends, start, end, day)
            ctx['can_spend'] = budget.can_spend(trip, me)
        ctx['coming'] = coming_up(shaped, day)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
'''),
        (r'''            from .compare import unsettled
            last = past[0]
            due = unsettled(last, list(last.bookings.all()), day)
            last.owing = eur(sum((b.due_eur or 0) for b in due)) \
                if due else ''
''',
         r'''            from .compare import unsettled
            last = past[0]
            due = unsettled(last, list(last.bookings.all()), day) \
                if last.show_money else []
            last.owing = eur(sum((b.due_eur or 0) for b in due)) \
                if due else ''
'''),
        (r'''    bs = included([shape(b) for b in bs])
    t.start, t.end = span(t, bs)
    days = OrderedDict()
    undated = []
''',
         r'''    bs = included([shape(b) for b in bs])
    t.start, t.end = span(t, bs)
    # RA05, 19 Nov 2026 - the budget, and who sees the money.
    show_money = budget.hide(t, request.user, bs)
    if request.GET.get('tab') == 'costs' and not show_money:
        return redirect('travel:m_trip', trip_id=t.pk)
    days = OrderedDict()
    undated = []
'''),
        (r'''        'trip_days': _days_of(t) if sub == 'wish' else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'money': totals(bs), 'costs': costs,
        'people': [t.owner] + list(t.shared_with.all()), 'tab': 'trips',
        'coming': coming_up(bs, _today()),
''',
         r'''        'trip_days': _days_of(t) if sub == 'wish' else [],
        'trip': t, 'days': list(days.items()), 'undated': undated,
        'bookings': bs, 'costs': costs,
        'money': totals(bs, list(t.spends.all()) if show_money else ()),
        **money_state(t, request, bs, t.start, t.end, show_money,
                      'costs' if costs else sub),
        'people': [t.owner] + list(t.shared_with.all()), 'tab': 'trips',
        'coming': coming_up(bs, _today()),
'''),
        (r'''    else:
        b.included = None
    passes = [pass_card(p) for p in b.passes.all()]
    nights = ((b.end_date - b.start_date).days
''',
         r'''    else:
        b.included = None
    budget.hide(b.trip, request.user, [b])                  # RA05
    passes = [pass_card(p) for p in b.passes.all()]
    nights = ((b.end_date - b.start_date).days
'''),
    ]),
    (os.path.join('travel', 'report.py'), [
        (r'''

def context(t, kind):
    bs = list(t.bookings.prefetch_related('travellers', 'files', 'passes'))
    fx.convert_pending(bs, limit=5)
    bs = included([shape(b) for b in bs])
    for b in bs:
        b.route = plain(b.route)
''',
         r'''

def budget_for(t, start, end):
    from .budget import summary
    b = summary(t, list(t.spends.all()), start, end)
    return b if b['set'] else None


def context(t, kind, user=None):
    bs = list(t.bookings.prefetch_related('travellers', 'files', 'passes'))
    fx.convert_pending(bs, limit=5)
    bs = included([shape(b) for b in bs])
    # RA05, 19 Nov 2026 - no costs for someone they are not shared with.
    from .budget import hide
    show_money = hide(t, user, bs) if user is not None else True
    for b in bs:
        b.route = plain(b.route)
'''),
        (r'''                                              b.start_time or dt.time(0))),
        'wish': [p for p in pl if not p.day],
        'money': totals(bs),
        'people': [t.owner] + list(t.shared_with.all()),
        'made': timezone.localtime(),
''',
         r'''                                              b.start_time or dt.time(0))),
        'wish': [p for p in pl if not p.day],
        # RA05 - the daily spending is part of the trip's costs.
        'money': totals(bs, list(t.spends.all())) if show_money
        else totals([]),
        'bud': budget_for(t, start, end) if show_money else None,
        'people': [t.owner] + list(t.shared_with.all()),
        'made': timezone.localtime(),
'''),
        (r'''    if kind not in KINDS:
        kind = 'summary'
    html = get_template('travel/trip_pdf.html').render(context(t, kind))
    name = 'trip_%s_%s.pdf' % (slugify(t.name) or t.pk, kind)
    resp = HttpResponse(content_type='application/pdf')
''',
         r'''    if kind not in KINDS:
        kind = 'summary'
    html = get_template('travel/trip_pdf.html').render(context(t, kind, request.user))
    name = 'trip_%s_%s.pdf' % (slugify(t.name) or t.pk, kind)
    resp = HttpResponse(content_type='application/pdf')
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
</style>
''',
         r'''  .tv-cal-bar { font-size: 10px; line-height: 20px; padding: 0 4px; margin: 0 1px; border-radius: 4px; }
}
/* RA05, 19 Nov 2026 - the daily spending budget: ahead or behind plan, spending per day against the day's budget, + Spending. */
.tv-ink { color: var(--alv-ink); }
.tv-over { color: #A32D2D; font-weight: 600; }
.tv-bud { border-top: 3px solid var(--alv-accent); }
.tv-bud-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.tv-bud-k { background: #F3F5F6; border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; }
.tv-bud-k span { font-size: .8rem; color: var(--alv-ink-soft); }
.tv-bud-k b { font-size: 1.3rem; line-height: 1.2; }
.tv-bud-k small { font-size: .78rem; color: var(--alv-ink-soft); }
.tv-bud-k.is-good { background: #E6F4EC; } .tv-bud-k.is-good span, .tv-bud-k.is-good b, .tv-bud-k.is-good small { color: #1E6B3E; }
.tv-bud-k.is-bad { background: #FCEBEB; } .tv-bud-k.is-bad span, .tv-bud-k.is-bad b, .tv-bud-k.is-bad small { color: #8E2626; }
.tv-bud-bar.is-amber span { background: #BA7517; } .tv-bud-bar.is-red span { background: #C0392B; }
.tv-bud-bars { position: relative; display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 6px; height: 150px; border-bottom: 1px solid #C9D3D6; }
.tv-bud-col { position: relative; z-index: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; color: inherit; text-decoration: none; min-width: 0; }
.tv-bud-col:hover { text-decoration: none; }
.tv-bud-col i { display: block; width: 100%; min-height: 0; border-radius: 4px 4px 0 0; background: #2E9A6B; }
.tv-bud-col.is-over i { background: #D64545; }
.tv-bud-col.is-today i { outline: 2px solid var(--alv-ink); outline-offset: 1px; }
.tv-bud-col small { font-size: 11px; color: var(--alv-ink-soft); white-space: nowrap; }
.tv-bud-col.is-over small { color: #A32D2D; font-weight: 600; }
.tv-bud-line { position: absolute; left: 0; right: 0; border-top: 2px dashed var(--alv-accent); pointer-events: none; z-index: 1; }
.tv-bud-days { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 6px; margin-top: 4px; font-size: 11px; color: var(--alv-ink-soft); text-align: center; }
.tv-bud-days span { white-space: nowrap; overflow: hidden; text-overflow: clip; }
.tv-bud-days .is-today { color: var(--alv-ink); font-weight: 700; }
.tv-bud-days i { font-style: normal; } .tv-bud-days .is-today .n { display: none; }
.tv-bud-form { margin-top: 14px; padding: 12px; background: #F3F5F6; border-radius: 10px; }
.tv-bud-opts { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.tv-bud-opt { display: flex; align-items: center; gap: 8px; margin: 0; font-weight: 600; }
.tv-bud-opt .form-control { width: 120px; }
.tv-spend-add { display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-end; padding: 10px; background: #F3F5F6; border-radius: 10px; margin-bottom: 12px; }
.tv-spend-add > div { flex: 0 0 auto; min-width: 0; }
.tv-spend-add > div:nth-child(2) { width: 130px; } .tv-spend-add > div:nth-child(3) { width: 100px; } .tv-spend-add > div:nth-child(4) { width: 170px; }
.tv-spend-add .tv-spend-note { flex: 1 1 180px; }
.tv-spend-add .form-control { width: 100%; min-width: 0; height: 38px; box-sizing: border-box; }
.tv-spend-add button { height: 38px; white-space: nowrap; }
.tv-spend-add label { font-size: .8rem; color: var(--alv-ink-soft); margin: 0 0 2px; }
.tv-spend-day { padding: 8px 0 4px; border-top: 1px solid var(--alv-line-soft); scroll-margin-top: 80px; }
.tv-spend-row { padding: 4px 0 4px 10px; font-size: .92rem; }
.tv-spend-row .tv-linkbtn { margin-left: 12px; color: var(--alv-ink-soft); text-decoration: none; }
@media screen and (max-width: 768px) {
  .tv-spend-add > div:nth-child(n) { flex: 1 1 40%; width: auto; }
  .tv-spend-add .tv-spend-note, .tv-spend-add button { flex: 1 1 100%; }
  .tv-bud-col small { font-size: 9px; }
  .tv-bud-days { font-size: 9px; }
  .tv-bud-days .w { display: none; } .tv-bud-days .is-today .n { display: inline; }
}
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''</div>
<aside class="tv-side">
    <section class="form-card" data-booking-cost>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Cost</h3>{% if b.amount is not None %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% endif %}</div>
        {% if b.amount is not None %}
''',
         r'''</div>
<aside class="tv-side">
    {% if show_money %}{# RA05 - not for someone the costs are not shared with #}<section class="form-card" data-booking-cost>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Cost</h3>{% if b.amount is not None %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% endif %}</div>
        {% if b.amount is not None %}
'''),
        (r'''        {% elif b.included %}<p class="tv-sub" style="margin: 0" data-included>Included in the price of <a href="{% url 'travel:booking' b.included.pk %}">{{ b.included.segment|default:b.included.title }}</a> &mdash; one booking, one price.</p>
        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>
    {% if passes %}
    <section class="form-card" data-boarding-pass>
''',
         r'''        {% elif b.included %}<p class="tv-sub" style="margin: 0" data-included>Included in the price of <a href="{% url 'travel:booking' b.included.pk %}">{{ b.included.segment|default:b.included.title }}</a> &mdash; one booking, one price.</p>
        {% else %}<p class="tv-sub" style="margin: 0">No cost entered.</p>{% endif %}
    </section>{% endif %}
    {% if passes %}
    <section class="form-card" data-boarding-pass>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking_form.html'), [
        (r'''</section>

<section class="form-card">
    <h3 class="form-section-title">Cost</h3>
    <div class="tv-form-grid">
''',
         r'''</section>

{% if show_money %}{# RA05 - no Cost section for someone the costs are not shared with: theirs stay as they are #}<section class="form-card">
    <h3 class="form-section-title">Cost</h3>
    <div class="tv-form-grid">
'''),
        (r'''        <div><label for="cn">Free cancellation until</label><input id="cn" type="date" name="cancel_until" class="form-control" value="{{ b.cancel_until|date:'Y-m-d' }}"></div>
    </div>
</section>

<section class="form-card">
''',
         r'''        <div><label for="cn">Free cancellation until</label><input id="cn" type="date" name="cancel_until" class="form-control" value="{{ b.cancel_until|date:'Y-m-d' }}"></div>
    </div>
</section>{% endif %}

<section class="form-card">
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv18-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv19-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv18-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv19-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'today.html'), [
        (r'''{% elif on_now %}
{% if passes_today %}<a href="{% url 'travel:m_passes' %}" class="tv-btn wide" data-passes-today><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h2M3 9h15"/></svg> Boarding passes</a>{% endif %}
<p class="tv-h3">Today</p>
<section class="tv-card" data-today>{% for b in today_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked today. Enjoy it.</p>{% endfor %}</section>
''',
         r'''{% elif on_now %}
{% if passes_today %}<a href="{% url 'travel:m_passes' %}" class="tv-btn wide" data-passes-today><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h2M3 9h15"/></svg> Boarding passes</a>{% endif %}
{% if bud and bud.set %}{% comment %} RA05, 19 Nov 2026 - the Today line: spent today against the day's budget, ahead or behind plan. {% endcomment %}<section class="tv-card tv-bud-today" data-today-budget>
  <div class="tv-row"><a href="{% url 'travel:m_trip' trip.pk %}?tab=costs" style="color: inherit; text-decoration: none">Today <b{% if bud.today_over %} class="tv-over"{% endif %}>{{ bud.today_label }}</b> of {{ bud.per_day_label }}</a>{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-small" style="font-weight: 700" data-spend-new>+ Spending</a>{% endif %}</div>
  <div class="tv-small {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan</div>
</section>{% endif %}
<p class="tv-h3">Today</p>
<section class="tv-card" data-today>{% for b in today_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked today. Enjoy it.</p>{% endfor %}</section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a><a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
''',
         r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a>{% endif %}</nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
'''),
        (r'''</div>
{% elif costs %}
<section class="tv-card" data-costs>
  <div class="tv-row"><span class="tv-muted">Total</span><b style="font-size: 20px">{{ money.total|default:"€0" }}</b></div>
  <div class="tv-row"><span class="tv-muted">Paid</span><b style="color: var(--tv-good)">{{ money.paid|default:"€0" }}</b></div>
  <div class="tv-row"><span class="tv-muted">Still to pay</span><b style="color: var(--tv-warn)">{{ money.due|default:"€0" }}</b></div>
''',
         r'''</div>
{% elif costs %}
{% comment %} RA05, 19 Nov 2026 - the daily spending budget: ahead or behind plan, spending per day, + Spending; then the whole trip's costs, daily spending included. {% endcomment %}
{% if bud.set %}<section class="tv-card" data-budget>
  <div class="tv-row"><span class="tv-muted">Daily spending &middot; {{ bud.per_day_label }} a day</span>{% if can_spend %}<a href="{% url 'travel:m_budget' trip.pk %}" class="tv-small" data-budget-edit>Change</a>{% endif %}</div>
  {% if bud.when == 'on' %}<div class="tv-row"><span class="tv-bud-big {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead{% else %}behind{% endif %}</span><span class="tv-muted tv-small">{{ bud.spent_label }} of {{ bud.planned_label }} so far</span></div>
  {% elif bud.when == 'after' %}<div class="tv-row"><span class="tv-bud-big {% if bud.over %}tv-over{% else %}tv-good{% endif %}" data-bud-pace="{% if bud.over %}behind{% else %}ahead{% endif %}">{{ bud.left_label }} {% if bud.over %}over{% else %}under{% endif %}</span><span class="tv-muted tv-small">{{ bud.spent_label }} of {{ bud.total_label }}</span></div>
  {% else %}<div class="tv-row"><span class="tv-bud-big">{{ bud.total_label|default:"–" }}</span><span class="tv-muted tv-small">for the holiday{% if bud.days %} &middot; {{ bud.days }} days{% endif %}</span></div>{% endif %}
  {% if bud.total %}<div class="tv-meter{% if bud.over %} is-red{% elif bud.pct >= 90 %} is-amber{% endif %}" aria-hidden="true"><span style="width: {{ bud.pct }}%"></span></div>{% endif %}
  {% if bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
  {% if bud.when == 'on' %}<p class="tv-muted tv-small" style="margin: 6px 0 0">{% if bud.keep_label %}{{ bud.keep_label }} a day for the last {{ bud.to_go }} day{{ bud.to_go|pluralize }} keeps you on {{ bud.total_label }}{% elif bud.over %}{{ bud.left_label }} over the holiday&rsquo;s {{ bud.total_label }}{% else %}The last day{% endif %}</p>{% endif %}
</section>
{% elif can_spend %}<a href="{% url 'travel:m_budget' trip.pk %}" class="tv-card" data-budget-none style="display: block; color: inherit; text-decoration: none"><b>Set a daily spending budget</b><span class="tv-muted tv-small" style="display: block">A day&rsquo;s or the holiday&rsquo;s &ndash; then see each day whether you are ahead or behind.</span></a>{% endif %}
{% if can_spend %}<a href="{% url 'travel:m_spend' trip.pk %}" class="tv-btn wide" data-spend-new style="margin-bottom: 10px">+ Spending</a>{% endif %}
{% if not bud.set and bud.show_chart %}<section class="tv-card">{% include 'travel/_budget_chart.html' %}</section>{% endif %}
{% if spend_days %}<section class="tv-card" data-spending>{% for d in spend_days %}<div class="tv-spend-day" id="sp{{ d.day|date:'Ymd' }}" data-spend-day="{{ d.day|date:'Y-m-d' }}"><div class="tv-row tv-small"><b>{% if d.day == today %}Today · {% endif %}{{ d.day|date:"D j M" }}</b><span class="{% if d.over %}tv-over{% else %}tv-muted{% endif %}">{{ d.label }}{% if d.over %} · {{ d.over_by }} over{% endif %}</span></div>{% for s in d.rows %}<div class="tv-row" data-spend="{{ s.pk }}"><span>{{ s.what|default:"Spending" }}{% if s.orig_label %} <span class="tv-muted tv-small">· {{ s.orig_label }}</span>{% endif %}</span><span>{{ s.eur_label }}{% if can_spend %}<form method="post" action="{% url 'travel:m_spend_delete' s.pk %}" style="display: inline">{% csrf_token %}<button type="submit" class="tv-linkbtn" aria-label="Delete {{ s.what|default:'this spending' }}" onclick="return confirm('Delete this spending?')" style="margin-left: 8px">✕</button></form>{% endif %}</span></div>{% endfor %}</div>{% endfor %}</section>{% endif %}
<section class="tv-card" data-costs>
  {% if money.has_spend %}<div class="tv-row tv-small" data-costs-split><span class="tv-muted">Bookings</span><b>{{ money.booked|default:"€0" }}</b></div><div class="tv-row tv-small"><span class="tv-muted">Daily spending</span><b>{{ money.spent|default:"€0" }}</b></div>{% endif %}
  <div class="tv-row"><span class="tv-muted">Trip total</span><b style="font-size: 20px">{{ money.total|default:"€0" }}</b></div>
  <div class="tv-row"><span class="tv-muted">Paid</span><b style="color: var(--tv-good)">{{ money.paid|default:"€0" }}</b></div>
  <div class="tv-row"><span class="tv-muted">Still to pay</span><b style="color: var(--tv-warn)">{{ money.due|default:"€0" }}</b></div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'share.html'), [
        (r'''<form method="post" class="form-card" style="max-width: 620px" data-share>
    {% csrf_token %}
    <p class="small">Everyone you tick sees the whole trip &mdash; bookings, costs, documents &mdash; and can add and change bookings. Only you can delete the trip or change who it is shared with.</p>
    {% for p in people %}
    <label style="display: flex; align-items: center; gap: 10px; min-height: 44px; border-top: 1px solid var(--alv-line-soft); margin: 0">
''',
         r'''<form method="post" class="form-card" style="max-width: 620px" data-share>
    {% csrf_token %}
    <p class="small">Everyone you tick sees the whole trip &mdash; bookings, documents and, if you share them, the costs &mdash; and can add and change bookings. Only you can delete the trip or change who it is shared with.</p>
    {% for p in people %}
    <label style="display: flex; align-items: center; gap: 10px; min-height: 44px; border-top: 1px solid var(--alv-line-soft); margin: 0">
'''),
        (r'''    <p class="tv-sub">Nobody else has Travel yet. Give someone the Travel permission in User Administration first.</p>
    {% endfor %}
    {% if people %}<button type="submit" class="btn action-primary" style="margin-top: 12px">Save sharing</button>{% endif %}
</form>
</div>
''',
         r'''    <p class="tv-sub">Nobody else has Travel yet. Give someone the Travel permission in User Administration first.</p>
    {% endfor %}
    {% if people %}
    {% comment %} RA05, 19 Nov 2026 - Demetri: "I must have the option to either share or not share costs and budget information with other travellers". {% endcomment %}
    <label style="display: flex; align-items: flex-start; gap: 10px; border-top: 2px solid var(--alv-line-soft); margin: 8px 0 0; padding-top: 12px" data-share-money>
        <input type="checkbox" name="share_money" value="1"{% if trip.share_money %} checked{% endif %} style="width: 20px; height: 20px; margin-top: 2px">
        <span><b>Share costs and budget</b><br><span class="tv-sub small">Ticked: they see the budget and every cost, but cannot add spending or change the budget. Not ticked: they see no money at all &ndash; no Costs tab, no amounts on bookings, trips, PDFs or Compare; and your amounts stay as they are when they edit a booking.</span></span>
    </label>
    <button type="submit" class="btn action-primary" style="margin-top: 12px">Save sharing</button>{% endif %}
</form>
</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    <a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>
</nav>

''',
         r'''    <a class="tv-chip{% if tab == 'itinerary' %} is-on{% endif %}" href="{% url 'travel:trip_itinerary' trip.pk %}"{% if tab == 'itinerary' %} aria-current="page"{% endif %}>Itinerary</a>
    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    {% if show_money %}<a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>{% endif %}
</nav>

'''),
        (r'''    </section>
{% else %}
    <section class="form-card" data-costs>
        <div class="tv-row">
            <div><div class="tv-sub">Total</div><b style="font-size: 1.5rem">{{ money.total|default:"€0" }}</b></div>
            <div><div class="tv-sub">Paid</div><b style="font-size: 1.5rem" class="tv-paid">{{ money.paid|default:"€0" }}</b></div>
            <div><div class="tv-sub">Still to pay</div><b style="font-size: 1.5rem" class="tv-due">{{ money.due|default:"€0" }}</b></div>
''',
         r'''    </section>
{% else %}
    {% comment %} RA05, 19 Nov 2026 - the daily spending budget and the spending, first; then the trip's whole costs, its daily spending included. {% endcomment %}
    {% include 'travel/_budget.html' %}
    <section class="form-card" data-costs>
        {% if money.has_spend %}<div class="tv-row tv-sub small" style="margin-bottom: 8px" data-costs-split><span>Bookings <b class="tv-ink">{{ money.booked|default:"€0" }}</b></span><span>+ Daily spending <b class="tv-ink">{{ money.spent|default:"€0" }}</b></span><span>= the whole trip</span></div>{% endif %}
        <div class="tv-row">
            <div><div class="tv-sub">Trip total</div><b style="font-size: 1.5rem">{{ money.total|default:"€0" }}</b></div>
            <div><div class="tv-sub">Paid</div><b style="font-size: 1.5rem" class="tv-paid">{{ money.paid|default:"€0" }}</b></div>
            <div><div class="tv-sub">Still to pay</div><b style="font-size: 1.5rem" class="tv-due">{{ money.due|default:"€0" }}</b></div>
'''),
        (r'''
<aside class="tv-side">
    {% if tab == 'bookings' and money.any %}
    <section class="form-card">
''',
         r'''
<aside class="tv-side">
    {% if tab == 'bookings' and show_money and bud.set and bud.when != 'none' %}
    {% comment %} RA05 - the budget at a glance, beside the bookings. {% endcomment %}
    <section class="form-card" data-budget-side>
        <h3 class="form-section-title">Daily spending</h3>
        {% if bud.when == 'on' %}<div class="tv-row"><span class="tv-sub">Today</span><b>{{ bud.today_label }} <span class="tv-sub">of {{ bud.per_day_label }}</span></b></div>
        <div class="{% if bud.ahead %}tv-paid{% else %}tv-over{% endif %} small" style="font-weight: 700">{{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan</div>{% elif bud.when == 'after' %}<div class="{% if bud.over %}tv-over{% else %}tv-paid{% endif %} small" style="font-weight: 700">{{ bud.left_label }} {% if bud.over %}over{% else %}under{% endif %} budget</div>{% else %}<div class="tv-row"><span class="tv-sub">Budget</span><b>{{ bud.per_day_label }} a day</b></div>{% endif %}
        {% if can_spend %}<a href="{% url 'travel:trip_costs' trip.pk %}#spend" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Spending</a>{% else %}<a href="{% url 'travel:trip_costs' trip.pk %}" class="small">See the budget</a>{% endif %}
    </section>
    {% endif %}
    {% if tab == 'bookings' and money.any %}
    <section class="form-card">
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip_pdf.html'), [
        (r'''</tr></table>
{% endif %}

<h2 class="sec">Day by day</h2>
''',
         r'''</tr></table>
{% endif %}
{% if bud %}<p class="muted" data-pdf-budget>Daily spending budget: {{ bud.per_day_label }} a day{% if bud.total_label %}, {{ bud.total_label }} for the holiday{% endif %} · spent {{ bud.spent_label }}{% if bud.when == 'on' %} · {{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan{% elif bud.when == 'after' %} · {{ bud.left_label }} {% if bud.over %}over{% else %}under{% endif %} budget{% endif %}</p>{% endif %}{# RA05 #}

<h2 class="sec">Day by day</h2>
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''from django.urls import path

from . import (compare, phone, report, views, views_ideas, views_inbox,
               views_places, views_plan)

''',
         r'''from django.urls import path

from . import (compare, phone, report, views, views_budget, views_ideas,
               views_inbox,
               views_places, views_plan)

'''),
        (r'''    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
    path('<int:trip_id>/share/', views.trip_share, name='trip_share'),
    path('<int:trip_id>/booking/new/', views.booking_form,
         name='booking_new'),
''',
         r'''    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
    path('<int:trip_id>/share/', views.trip_share, name='trip_share'),
    # RA05, 19 Nov 2026 - the daily spending budget and + Spending.
    path('<int:trip_id>/budget/', views_budget.budget_save,
         name='budget_save'),
    path('<int:trip_id>/spend/', views_budget.spend_add, name='spend_add'),
    path('spend/<int:spend_id>/delete/', views_budget.spend_delete,
         name='spend_delete'),
    path('m/<int:trip_id>/budget/', views_budget.budget_save,
         name='m_budget_save'),
    path('m/<int:trip_id>/budget/edit/', views_budget.m_budget_form,
         name='m_budget'),
    path('m/<int:trip_id>/spend/', views_budget.spend_add,
         name='m_spend_add'),
    path('m/<int:trip_id>/spend/new/', views_budget.m_spend_form,
         name='m_spend'),
    path('m/spend/<int:spend_id>/delete/', views_budget.spend_delete,
         name='m_spend_delete'),
    path('<int:trip_id>/booking/new/', views.booking_form,
         name='booking_new'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import fx
from .models import (Booking, BookingChange, BookingFile, InboundFile,
                     JoinRequest, Trip, trips_for)
''',
         r'''from django.views.decorators.http import require_POST

from . import budget, fx
from .models import (Booking, BookingChange, BookingFile, InboundFile,
                     JoinRequest, Trip, trips_for)
'''),
        (r'''         'train': 'fa-train', 'ferry': 'fa-ship', 'transfer': 'fa-taxi',
         'activity': 'fa-ticket-alt', 'restaurant': 'fa-utensils',
         'other': 'fa-map-marker-alt'}


''',
         r'''         'train': 'fa-train', 'ferry': 'fa-ship', 'transfer': 'fa-taxi',
         'activity': 'fa-ticket-alt', 'restaurant': 'fa-utensils',
         'other': 'fa-map-marker-alt',
         # RA05 - daily spending, beside the bookings in the costs.
         'spend': 'fa-wallet'}


'''),
        (r'''

def totals(bookings):
    total = paid = Decimal('0')
    pending = 0
''',
         r'''

def totals(bookings, spends=()):
    """The trip's costs. RA05, 19 Nov 2026 - its daily spending too
    (Demetri: "these daily spends get added to the trip costs so that I
    can analyse my complete trip costs"): spent, so paid."""
    total = paid = Decimal('0')
    pending = 0
'''),
        (r'''        paid += b.paid_eur or Decimal('0')
        kinds[b.kind] = kinds.get(b.kind, Decimal('0')) + b.amount_eur
    top = max(kinds.values()) if kinds else None
    by_kind = [{'kind': dict(Booking.KINDS)[k], 'icon': ICONS[k],
                'eur': eur(v), 'pct': int(v / top * 100) if top else 0}
               for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])]
    return {'total': eur(total), 'paid': eur(paid),
            'due': eur(total - paid), 'pending': pending,
            'pct': int(paid / total * 100) if total else 0,
            'by_kind': by_kind, 'any': bool(kinds or pending)}

''',
         r'''        paid += b.paid_eur or Decimal('0')
        kinds[b.kind] = kinds.get(b.kind, Decimal('0')) + b.amount_eur
    booked = total
    for s in spends:
        if s.amount_eur is None:
            pending += 1
            continue
        total += s.amount_eur
        paid += s.amount_eur
        kinds['spend'] = kinds.get('spend', Decimal('0')) + s.amount_eur
    top = max(kinds.values()) if kinds else None
    label = dict(Booking.KINDS, spend='Daily spending')
    by_kind = [{'kind': label[k], 'icon': ICONS.get(k, 'fa-wallet'),
                'eur': eur(v), 'pct': int(v / top * 100) if top else 0}
               for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])]
    return {'total': eur(total), 'paid': eur(paid),
            'due': eur(total - paid), 'pending': pending,
            'pct': int(paid / total * 100) if total else 0,
            'booked': eur(booked), 'spent': eur(total - booked),
            'has_spend': bool(spends),
            'by_kind': by_kind, 'any': bool(kinds or pending)}

'''),
        (r'''    today = dt.date.today()
    rows = []
    for t in trips_for(request.user).prefetch_related('bookings',
                                                      'shared_with'):
        bs = list(t.bookings.all())
        start, end = span(t, bs)
        t.start, t.end = start, end
        t.n = len(bs)
        t.money = totals(bs)
        t.people = [t.owner] + list(t.shared_with.all())
        t.mine = t.owner_id == request.user.id
''',
         r'''    today = dt.date.today()
    rows = []
    for t in trips_for(request.user).prefetch_related('bookings', 'spends',
                                                      'shared_with'):
        bs = list(t.bookings.all())
        start, end = span(t, bs)
        t.start, t.end = start, end
        t.n = len(bs)
        # RA05 - no money for someone the costs are not shared with.
        t.show_money = budget.money_ok(t, request.user)
        t.money = totals(bs, list(t.spends.all())) if t.show_money \
            else totals([])
        t.people = [t.owner] + list(t.shared_with.all())
        t.mine = t.owner_id == request.user.id
'''),
        (r'''    from .compare import unsettled
    for t in sel:
        due = unsettled(t, list(t.bookings.all()), today) if t.past else []
        t.owing = eur(sum((b.due_eur or Decimal('0')) for b in due)) \
            if due else ''
''',
         r'''    from .compare import unsettled
    for t in sel:
        due = unsettled(t, list(t.bookings.all()), today) \
            if t.past and t.show_money else []
        t.owing = eur(sum((b.due_eur or Decimal('0')) for b in due)) \
            if due else ''
'''),
        (r'''    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
    pl = list(t.places.all())
    from .phone import itinerary
''',
         r'''    bs = included([shape(b) for b in bs])
    start, end = span(t, bs)
    # RA05, 19 Nov 2026 - the budget, and who sees the money.
    show_money = budget.hide(t, request.user, bs)
    if tab == 'costs' and not show_money:
        return redirect('travel:trip', trip_id=t.pk)
    pl = list(t.places.all())
    from .phone import itinerary
'''),
        (r'''                   'icon': ICONS[k]} for k, n in kinds.items()],
        'want': want if want in kinds else '',
        'money': totals(bs), 'coming': coming_up(bs, dt.date.today()),
        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
''',
         r'''                   'icon': ICONS[k]} for k, n in kinds.items()],
        'want': want if want in kinds else '',
        'money': totals(bs, list(t.spends.all()) if show_money else ()),
        'coming': coming_up(bs, dt.date.today()),
        'people': [t.owner] + list(t.shared_with.all()),
        'is_owner': t.owner_id == request.user.id,
'''),
        (r'''        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **plan_state(t, request, tab),
        # TR-12 - Suggest things to do.
        **idea_state(t, request, tab)})


''',
         r'''        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
        'settle': settle_rows(t, bs) if show_money else [],
        **money_state(t, request, bs, start, end, show_money, tab),
        # TR-11 - Plan my days: Undo plan, Fit them in, a plan to review.
        **plan_state(t, request, tab),
        # TR-12 - Suggest things to do.
        **idea_state(t, request, tab)})


def money_state(t, request, bs, start, end, show_money, tab, spends=None):
    """RA05 - the daily spending budget, the spending, and what this person
    may do."""
    if not show_money:
        return {'show_money': False}
    spends = list(t.spends.all()) if spends is None else spends
    budget.convert_pending(spends)
    bud = budget.summary(t, spends, start, end)
    out = {'show_money': True, 'can_spend': budget.can_spend(t, request.user),
           'bud': bud, 'today': dt.date.today()}
    if tab == 'costs':
        out.update({'spend_days': budget.spend_days(spends, bud['per_day']),
                    'currencies': fx.CURRENCIES})
    return out


'''),
        (r'''                  if x.isdigit()}
        t.shared_with.set([u for u in people if u.pk in picked])
        messages.success(request, 'Sharing saved.')
        return redirect('travel:trip', trip_id=t.pk)
''',
         r'''                  if x.isdigit()}
        t.shared_with.set([u for u in people if u.pk in picked])
        # RA05 - share the costs and budget, or not.
        t.share_money = bool(request.POST.get('share_money'))
        t.save(update_fields=['share_money'])
        messages.success(request, 'Sharing saved.')
        return redirect('travel:trip', trip_id=t.pk)
'''),
        (r'''    b.end_date = _date(P.get('end_date'))
    b.end_time = _time(P.get('end_time'))
    cur = (P.get('currency') or 'EUR').upper()
    b.currency = cur if cur in fx.CURRENCIES else 'EUR'
''',
         r'''    b.end_date = _date(P.get('end_date'))
    b.end_time = _time(P.get('end_time'))
    b.status = 'cancelled' if P.get('cancelled') else 'ok'
    if not getattr(request, 'travel_money', True):
        # RA05 - the form had no Cost section for this person: the costs
        # stay exactly as they were.
        if not b.title:
            problems.append('Say what the booking is.')
        if b.end_date and b.start_date and b.end_date < b.start_date:
            problems.append('The end is before the start.')
        return problems
    cur = (P.get('currency') or 'EUR').upper()
    b.currency = cur if cur in fx.CURRENCIES else 'EUR'
'''),
        (r'''    dupe = None
    people = [t.owner] + list(t.shared_with.all())
    on = set(b.travellers.values_list('pk', flat=True)) if b.pk else set()
    for u in people:
''',
         r'''    dupe = None
    people = [t.owner] + list(t.shared_with.all())
    # RA05 - no Cost section, and the costs left as they are, for someone
    # the costs are not shared with.
    request.travel_money = show_money = budget.money_ok(t, request.user)
    on = set(b.travellers.values_list('pk', flat=True)) if b.pk else set()
    for u in people:
'''),
        (r'''    return render(request, 'travel/booking_form.html', {
        'trip': t, 'b': b, 'problems': problems, 'dupe': dupe,
        'kinds': Booking.KINDS,
        'paids': Booking.PAID, 'currencies': fx.CURRENCIES,
        'files': list(b.files.all()) if b.pk else [], 'people': people})


''',
         r'''    return render(request, 'travel/booking_form.html', {
        'trip': t, 'b': b, 'problems': problems, 'dupe': dupe,
        'kinds': Booking.KINDS, 'show_money': show_money,
        'paids': Booking.PAID, 'currencies': fx.CURRENCIES,
        'files': list(b.files.all()) if b.pk else [], 'people': people})


MONEY_LABELS = {l for f, l in TRACKED if f in (
    'currency', 'amount', 'amount_eur', 'paid', 'paid_amount', 'pay_by')}


def money_free(changes, show_money):
    """RA05 - a booking's change trail, without the costs for someone they
    are not shared with."""
    if show_money:
        return changes
    out = []
    for c in changes:
        c.changes = [x for x in (c.changes or [])
                     if x.get('label') not in MONEY_LABELS]
        if c.changes:
            out.append(c)
    return out


'''),
        (r'''    else:
        b.included = None
    return render(request, 'travel/booking.html', {
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'passes': [pass_card(p) for p in b.passes.all()],
        'nights': nights, 'paid_label': eur(b.paid_eur),
        'due_label': eur(b.due_eur),
        'changes': list(b.changes.select_related('by')),
        'today': dt.date.today()})

''',
         r'''    else:
        b.included = None
    show_money = budget.hide(b.trip, request.user, [b])        # RA05
    return render(request, 'travel/booking.html', {
        'show_money': show_money,
        'b': b, 'trip': b.trip, 'files': list(b.files.all()),
        'passes': [pass_card(p) for p in b.passes.all()],
        'nights': nights, 'paid_label': eur(b.paid_eur),
        'due_label': eur(b.due_eur),
        'changes': money_free(list(b.changes.select_related('by')),
                              show_money),
        'today': dt.date.today()})

'''),
    ]),
    (os.path.join('test_travel_four.py'), [
        (r'''               'own days')
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok(h.count('data-wish-item') == 1 and 'Jardim da Estrela' in h,
               'WISH LIST: the place with no day')
            A.post('/travel/place/%d/move/' % j.pk, {
''',
         r'''               'own days')
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            # RA05, 19 Nov 2026 - RA03's Select styles name data-wish-item
            # too: count the items themselves.
            ok(h.count('<div data-wish-item>') == 1 and 'Jardim da Estrela' in h,
               'WISH LIST: the place with no day')
            A.post('/travel/place/%d/move/' % j.pk, {
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
    raise SystemExit('RA05 REFUSED: %s' % msg)


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
    if "'test_ra05_budget.py'" in read(pq):
        print('RA05 already applied.')
        return 0
    if "'test_ra04_key_email.py'" not in read(pq):
        refuse('RA04 (apply_ra04_key_email.py) is not applied - this round registers after it.')
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
        print('RA05 --check: %d file(s) would change, none written; %d '
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
    print('RA05 applied - the daily spending budget; sharing the costs. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
