# -*- coding: utf-8 -*-
"""apply_ra12_city_info_receipts.py - round RA12, 22 Nov 2026.

RELEASE RA12 - GOOD TO KNOW; + SPENDING FROM A RECEIPT PHOTO.

    Demetri, 22 Nov: "I like 11 - Receipt photo to spending. The user
    should have the option to manually capture or to take a photo." -
    "Let's not keep the receipt photo." "I like 12 - City Info card" -
    "Add which side they drive on, typical shopping hours ... the latest
    conversion rate to Euro (... just a once-off indication) ... the
    phrases, I must be able to click on them and it plays them out loud."
    - "Build it."

    - travel/receipt.py (new): Claude reads a receipt photo's total,
      currency, day and shop; + Spending comes back filled in to check
      and add (computer: From a receipt photo under Daily spending, then
      a check page; phone: Take a photo / Choose a photo above the typed
      form). The photo is read in memory and never kept. Owner only.
    - travel/cityinfo.py (new) + CityInfo (migration travel 0015): a Good
      to know card a city, written once by Claude and kept - emergency
      number, plugs (adapter from Cyprus?), driving side, money with the
      ECB rate on the day it was made (stored, never moved), tipping,
      shop hours, time from Cyprus on the trip's dates, tap water,
      language, and phrases spoken aloud by the device's own voice.
      A Good to know tab on the trip (computer and phone), the card on
      the phone's Today; Refresh writes it again.
    - test_ai_models knows the two new places Alivente calls Claude
      from (travel/cityinfo.py, travel/receipt.py).
    - Help on the computer and the phone; the phone app moves to tv25-1.
    - Migration travel 0015: run python manage.py migrate locally first.

The suite, the two modules, the migration and the templates ship beside
this patcher. Stands on RA11. Idempotent. Edits backed up to .bak_ra12.
"""
import os
import sys

SUFFIX = '.bak_ra12'
MARK = 'RA12, 22 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra12_city_info_receipts.py',
    'travel/cityinfo.py',
    'travel/receipt.py',
    'travel/migrations/0015_city_info.py',
    'travel/templates/travel/_city_info.html',
    'travel/templates/travel/spend_receipt.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra10_google_checks.py',
    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    'test_ra11_category_icons.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra10_google_checks.py',
    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    'test_ra11_category_icons.py',
    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    'test_ra12_city_info_receipts.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    '.bak_ra11',
]

''',
         r'''    # RA11, 22 Nov 2026 - an icon for each kind of thing to do.
    '.bak_ra11',
    # RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
    '.bak_ra12',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change. The pencil <i class="fas fa-pen"></i> on the budget card opens it to change; the bin <i class="fas fa-trash-alt"></i> beside it removes the budget (it asks first; your spending stays).</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> (or its pencil <i class="fas fa-pen"></i>) to change its amount, currency, day or note; the bin <i class="fas fa-trash-alt"></i> beside the pencil deletes it, and asks first. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
''',
         r'''    <h6 data-help-budget><i class="fas fa-wallet"></i> Daily spending budget</h6>
    <p>Bookings &ndash; hotels, flights, car hire, trains, activity tickets &ndash; are what they cost; they are not budgeted. The budget is for everything else: meals, taxis, tickets at the door, shopping. On the trip&rsquo;s <strong>Costs</strong> tab, set it either as <strong>a day</strong> (&euro;150) or as <strong>the holiday</strong> (&euro;1,800): type one and the other is worked out from the trip&rsquo;s days. The one you typed is kept if the trip&rsquo;s dates change. The pencil <i class="fas fa-pen"></i> on the budget card opens it to change; the bin <i class="fas fa-trash-alt"></i> beside it removes the budget (it asks first; your spending stays).</p>
    <p><strong>+ Spending</strong> adds what you spent: the amount, then Add &ndash; euros, today and an empty note are already filled in; change the currency (converted at the ECB rate for that day), the day or add a note if you like. A meal at a restaurant you booked is added here too, as the booking has no bill. <strong>Only a day of the trip</strong> can be chosen: the day starts as today while you are away, the first day before the trip and the last after it. <strong>Click a spending</strong> (or its pencil <i class="fas fa-pen"></i>) to change its amount, currency, day or note; the bin <i class="fas fa-trash-alt"></i> beside the pencil deletes it, and asks first. <strong>From a receipt photo</strong> (under the form; on the phone, <strong>Take a photo of the receipt</strong> or <strong>Choose a photo</strong>) has Claude read the total, currency, day and shop&rsquo;s name and fills the form in for you to check before adding &ndash; nothing is added until you do, and the photo is never kept. <strong>Good to know</strong>, the last tab of a trip, has a card for each city: the emergency number, plugs (and whether you need an adapter from Cyprus), which side they drive on, the money with a one-off euro rate (the ECB&rsquo;s on the day the card was made), tipping, typical shop hours, the time difference from Cyprus on your dates, tap water and the language &ndash; with everyday phrases you tap to hear spoken, in the phone&rsquo;s or computer&rsquo;s own voice. Claude writes each city&rsquo;s card once and it is kept for every trip there; <strong>Refresh</strong> writes it again. On the phone, Today shows the card for the city you are in. Spending on a day outside the trip (from before this rule, or left there when bookings moved the trip) is listed apart under <em>Outside the trip&rsquo;s dates</em> &ndash; move it to a day of the trip or delete it; until then it is left out of the budget but still counts in the trip&rsquo;s costs. Only the trip&rsquo;s owner adds, changes or deletes spending and sets the budget.</p>
    <p>The budget card shows what you have spent so far against what was <strong>planned by today</strong> (a day&rsquo;s budget for every day so far, today counted): <strong>ahead of plan</strong> in green, <strong>behind plan</strong> in red; what is left for the days still to come, and what a day keeps you on budget. <strong>Spending per day</strong> is a bar for each day of the trip, red when that day went over the day&rsquo;s budget, with the day&rsquo;s budget as a dashed line &ndash; click a bar to see what was spent. Before the trip it shows the plan. <strong>After it</strong>: what you spent (and the average a day), the budget, and the <strong>Result</strong> in plain words &ndash; <em>&euro;780 less than budgeted</em> in green, or <em>&euro;200 more than budgeted</em> in red. If any day of the trip so far has no spending recorded, a note says how many (&ldquo;8 of the 9 days have no spending recorded, so this may not be the full picture&rdquo;) and those days are greyed under the bars &ndash; so a forgotten day is easy to spot.</p>
    <p>Daily spending is part of the trip&rsquo;s costs: the <strong>Trip total</strong> is the bookings plus the daily spending, it has its own line under <strong>By kind</strong> (which shows whole euros; the totals keep the cents), and it counts in the PDFs, on the trips list and in <strong>Compare</strong> (with a <em>Daily spending, per day</em> row). On the phone: a <strong>Today</strong> line &ndash; what you spent today against the day&rsquo;s budget, ahead or behind &ndash; with <strong>+ Spending</strong> beside it, and the same card, bars and list on the Costs tab.</p>
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
/* RA12, 22 Nov 2026 - Good to know, a card a city; + Spending from a receipt photo. */
.tv-ci { margin-bottom: 14px; }
.tv-ci-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; }
.tv-ci-title { font-weight: 700; font-size: 1.02rem; }
.tv-ci-refresh { border: 0; background: none; padding: 0; color: #0F6E56; font-size: .85rem; cursor: pointer; }
.tv-ci-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; }
.tv-ci-it { background: #F3F5F6; border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.tv-ci-it b { font-weight: 600; }
.tv-ci-l { font-size: .75rem; color: #5B6B72; text-transform: none; }
.tv-ci-s { display: block; font-size: .78rem; color: #5B6B72; }
.tv-ci-wait { margin: 0; color: #5B6B72; }
.tv-ci-say { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; }
.tv-ci-btn { display: flex; align-items: flex-start; gap: 8px; text-align: left; border: 1px solid #D9E0E3; border-radius: 8px; padding: 7px 9px; background: #fff; cursor: pointer; font: inherit; color: inherit; }
.tv-ci-btn svg { width: 18px; height: 18px; flex: none; color: #0F6E56; margin-top: 2px; }
.tv-ci-btn b { display: block; font-weight: 600; }
.tv-ci-btn.is-on { background: #E1F5EE; border-color: #5DCAA5; }
.tv-receipt { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin: 8px 0 4px; }
.tv-receipt-wait { display: none; }
.tv-receipt.is-reading .tv-receipt-wait, .tv-receipt-m.is-reading .tv-receipt-wait { display: block; font-weight: 600; }
.tv-receipt.is-reading .tv-receipt-tip, .tv-receipt-m.is-reading .tv-receipt-tip, .tv-receipt-m.is-reading label { display: none; }
.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    def __str__(self):
        return '%s %s' % (self.day, self.why)
''',
         r'''    def __str__(self):
        return '%s %s' % (self.day, self.why)


# RA12, 22 Nov 2026 - Good to know: one card a city, written once by
# Claude and kept (travel/cityinfo.py). Demetri: "I like 12 - City Info
# card". The euro rate is the ECB's on the day it was made, never moved.
class CityInfo(models.Model):
    STATES = [('working', 'Being written'), ('ready', 'Ready'),
              ('failed', 'Could not be written')]
    key = models.CharField(max_length=160, unique=True)
    city = models.CharField(max_length=80)
    country = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=8, choices=STATES, default='working')
    data = models.JSONField(default=dict, blank=True)
    rate = models.DecimalField(max_digits=16, decimal_places=6, null=True,
                               blank=True)
    rate_day = models.DateField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True)
    made_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'travel_city_info'
        ordering = ['city']

    def __str__(self):
        return self.city
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# outside what you asked for, in its own section.
# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
SW_VERSION = 'tv24-1'
SW_ASSETS = 'f8bffa7bc505'


''',
         r'''# outside what you asked for, in its own section.
# RA11, 22 Nov 2026 - an icon for each kind of thing to do.
# RA12, 22 Nov 2026 - Good to know; + Spending from a receipt photo.
SW_VERSION = 'tv25-1'
SW_ASSETS = '90edbdcd1f50'


'''),
        (r'''        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day, pl)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
''',
         r'''        elif trip.start and (trip.start - day).days <= weather.AHEAD:
            ctx['wx'] = weather.for_day(shaped, trip.start, day, pl)
        # RA12, 22 Nov 2026 - Good to know for the city you are in (or
        # the first one, before the trip).
        from . import cityinfo
        at = weather.place_for(shaped, day if now else trip.start)
        if at:
            ctx['card'] = cityinfo.card_at(at[0], at[1], day if now
                                           else trip.start)
        ctx['passes_today'] = BoardingPass.objects.filter(
            booking__trip=trip, booking__start_date__in=(
'''),
        (r'''    costs = request.GET.get('tab') == 'costs'
    sub = request.GET.get('tab') if request.GET.get('tab') in (
        'costs', 'itinerary', 'wish') else 'bookings'
    pl = list(t.places.all())
    for p in pl:
        p.is_place = True
    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        'itinerary': with_weather(itinerary(t, bs, pl), bs, pl)
        if sub == 'itinerary' else [],
''',
         r'''    costs = request.GET.get('tab') == 'costs'
    sub = request.GET.get('tab') if request.GET.get('tab') in (
        'costs', 'itinerary', 'wish', 'info') else 'bookings'
    pl = list(t.places.all())
    for p in pl:
        p.is_place = True
    return page(request, 'travel/m/trip.html', {
        'sub': sub, 'wish': [p for p in pl if not p.day],
        # RA12, 22 Nov 2026 - Good to know, a card a city.
        'cards': _cards(t) if sub == 'info' else [],
        'itinerary': with_weather(itinerary(t, bs, pl), bs, pl)
        if sub == 'itinerary' else [],
'''),
        (r'''        **(ideas.page_state(t, request)
           if sub in ('wish', 'itinerary') else {})})


''',
         r'''        **(ideas.page_state(t, request)
           if sub in ('wish', 'itinerary') else {})})


def _cards(t):
    from . import cityinfo
    return cityinfo.cards_for(t, list(t.bookings.all()))


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_budget.html'), [
        (r'''        <div class="tv-spend-note"><label for="sp-n">Note (optional)</label><input id="sp-n" name="what" class="form-control" maxlength="120"></div>
        <button type="submit" class="btn action-primary" data-spend-add><i class="fas fa-plus" aria-hidden="true"></i> Spending</button>
    </form>{% else %}<p class="tv-sub" data-spend-nodates>The trip needs its dates first &ndash; add a booking, or set From and To under <b>Edit trip</b>.</p>{% endif %}{% endif %}
    {% if not bud.set and bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
''',
         r'''        <div class="tv-spend-note"><label for="sp-n">Note (optional)</label><input id="sp-n" name="what" class="form-control" maxlength="120"></div>
        <button type="submit" class="btn action-primary" data-spend-add><i class="fas fa-plus" aria-hidden="true"></i> Spending</button>
    </form>
    {% comment %} RA12, 22 Nov 2026 - or from a receipt photo: Claude reads it, the form comes back filled in; the photo is never kept. {% endcomment %}
    <form method="post" action="{% url 'travel:spend_receipt' trip.pk %}" enctype="multipart/form-data" class="tv-receipt" data-receipt-form>{% csrf_token %}
        <label class="btn action-secondary btn-sm" style="margin: 0"><i class="fas fa-camera" aria-hidden="true"></i> From a receipt photo<input type="file" name="photo" accept="image/*" hidden onchange="if (this.files.length) { this.form.classList.add('is-reading'); this.form.submit(); }" data-receipt-pick></label>
        <span class="tv-sub tv-receipt-wait">Reading the receipt&hellip;</span>
        <span class="tv-sub tv-receipt-tip">Amount, currency, day and shop filled in for you to check. The photo is not kept.</span>
    </form>{% else %}<p class="tv-sub" data-spend-nodates>The trip needs its dates first &ndash; add a booking, or set From and To under <b>Edit trip</b>.</p>{% endif %}{% endif %}
    {% if not bud.set and bud.show_chart %}{% include 'travel/_budget_chart.html' %}{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
''',
         r'''.tv-id-group .tv-id-ico { width: 24px; height: 24px; }
.tv-id-group .tv-id-ico svg { width: 13px; height: 13px; }
/* RA12, 22 Nov 2026 - Good to know, a card a city; + Spending from a receipt photo. */
.tv-ci { margin-bottom: 14px; }
.tv-ci-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; }
.tv-ci-title { font-weight: 700; font-size: 1.02rem; }
.tv-ci-refresh { border: 0; background: none; padding: 0; color: #0F6E56; font-size: .85rem; cursor: pointer; }
.tv-ci-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; }
.tv-ci-it { background: #F3F5F6; border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.tv-ci-it b { font-weight: 600; }
.tv-ci-l { font-size: .75rem; color: #5B6B72; text-transform: none; }
.tv-ci-s { display: block; font-size: .78rem; color: #5B6B72; }
.tv-ci-wait { margin: 0; color: #5B6B72; }
.tv-ci-say { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; }
.tv-ci-btn { display: flex; align-items: flex-start; gap: 8px; text-align: left; border: 1px solid #D9E0E3; border-radius: 8px; padding: 7px 9px; background: #fff; cursor: pointer; font: inherit; color: inherit; }
.tv-ci-btn svg { width: 18px; height: 18px; flex: none; color: #0F6E56; margin-top: 2px; }
.tv-ci-btn b { display: block; font-weight: 600; }
.tv-ci-btn.is-on { background: #E1F5EE; border-color: #5DCAA5; }
.tv-receipt { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin: 8px 0 4px; }
.tv-receipt-wait { display: none; }
.tv-receipt.is-reading .tv-receipt-wait, .tv-receipt-m.is-reading .tv-receipt-wait { display: block; font-weight: 600; }
.tv-receipt.is-reading .tv-receipt-tip, .tv-receipt-m.is-reading .tv-receipt-tip, .tv-receipt-m.is-reading label { display: none; }
.tv-receipt-m { display: flex; flex-direction: column; gap: 8px; }
.tv-receipt-read { background: #E1F5EE; color: #085041; }
.tv-id-meta { font-size: .8rem; color: #0B5A63; font-weight: 600; }
.tv-id-meta span { color: #5B6B72; font-weight: 400; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv24-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv25-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv24-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv25-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Only a day of the trip can be chosen; tap a spending to change or delete it. Any on a day outside the trip is listed apart &ndash; move it or delete it. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
{% comment %} RA05, 19 Nov 2026 - the daily spending budget. {% endcomment %}<section class="tv-card" data-help-budget><p class="tv-h2">Budget and spending</p><p style="margin: 0">Bookings are what they cost; the budget is for everything else &ndash; meals, taxis, tickets at the door, shopping. On a trip&rsquo;s <b>Costs</b> tab, <b>Set a daily spending budget</b>: a day&rsquo;s or the holiday&rsquo;s &ndash; type one and the other is worked out. <b>+ Spending</b> (on Costs, and on Today while you are away): type the amount and tap <b>Add</b> &ndash; euros, today and an empty note are filled in. A meal at a restaurant you booked goes here too. Only a day of the trip can be chosen; tap a spending to change or delete it. Any on a day outside the trip is listed apart &ndash; move it or delete it. Today shows what you spent today against the day&rsquo;s budget and whether you are <b>ahead</b> or <b>behind</b> plan; Costs shows a bar for each day, red when it went over, and what a day keeps you on budget for the rest of the trip. After a trip, Costs says how it came out &ndash; <b>€780 less than budgeted</b> or <b>€200 more</b> &ndash; and warns if days have no spending recorded. Daily spending is part of the trip total. Only the trip&rsquo;s owner adds spending; the others see it only if you share the costs. On + Spending, <b>Take a photo of the receipt</b> (or <b>Choose a photo</b>) and the amount, currency, day and shop are filled in for you to check before you tap Add &ndash; the photo is never kept.</p></section>
<section class="tv-card" data-help-goodtoknow><p class="tv-h2">Good to know</p><p style="margin: 0">The <b>Good to know</b> tab of a trip has a card for each city: emergency number, plugs, which side they drive on, the money with a one-off euro rate, tipping, shop hours, the time difference from Cyprus, tap water and the language. Tap a phrase to hear it spoken. Today shows the card for the city you are in.</p></section>
<section class="tv-card"><p class="tv-h2">Between trips</p><p style="margin: 0">With nothing coming up, Today shows your last trip and the ones before it, and Trips shows the past trips. Trips are always listed latest first. At the top of Trips: All, Upcoming and Past, each with its number in a small badge, and the Year and Country menus. A picked year or country shows as a chip &mdash; tap its &#x2715; to clear it. They combine, so Past with Greece shows only your past trips to Greece. A trip that has ended with something still To pay says so &mdash; settle up on the trip. <b>Trips &rarr; Compare</b>: tick two or more trips to see their costs side by side.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'spend.html'), [
        (r'''{% block content %}
{% comment %} RA07, 19 Nov 2026 - only a day of the trip; the same page changes one already added (Save, Delete). {% endcomment %}
{% if not trip_start %}<section class="tv-card" data-spend-nodates><p style="margin: 0">The trip needs its dates first &ndash; add a booking, or set From and To on the full site under Edit trip.</p></section>{% else %}
<form method="post" action="{% if s %}{% url 'travel:m_spend_edit' s.pk %}{% else %}{% url 'travel:m_spend_add' trip.pk %}{% endif %}" class="tv-card tv-form" data-spend-form>{% csrf_token %}
  <label for="a" class="tv-muted tv-small">Amount</label>
  <input id="a" name="amount" class="tv-input tv-amount" inputmode="decimal" placeholder="0.00" autocomplete="off" required{% if s %} value="{{ s.amount }}"{% else %} autofocus{% endif %}>
  <div class="tv-two">
    <div><label for="c" class="tv-muted tv-small">Currency</label><select id="c" name="currency" class="tv-select" style="width: 100%">{% for c in currencies %}<option value="{{ c }}"{% if s and c == s.currency or not s and c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
    <div><label for="d" class="tv-muted tv-small">Day</label><input id="d" type="date" name="day" class="tv-input" value="{{ today|date:'Y-m-d' }}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}" data-spend-day-pick></div>
  </div>
  <label for="n" class="tv-muted tv-small">Note (optional)</label><input id="n" name="what" class="tv-input" maxlength="120"{% if s %} value="{{ s.what }}"{% endif %}>
  <p class="tv-muted tv-small" style="margin: 0">A day of the trip: {{ trip_start|date:"D j M" }} &ndash; {{ trip_end|date:"D j M" }}.</p>
  <button type="submit" class="tv-btn wide" data-spend-add>{% if s %}Save{% else %}Add{% endif %}</button>
''',
         r'''{% block content %}
{% comment %} RA07, 19 Nov 2026 - only a day of the trip; the same page changes one already added (Save, Delete). {% endcomment %}
{% comment %} RA12, 22 Nov 2026 - or from a receipt photo (Demetri: "The user should have the option to manually capture or to take a photo"): Claude reads it and this form comes back filled in, to check and Add. The photo is never kept. {% endcomment %}
{% if trip_start and not s and not pre %}<form method="post" action="{% url 'travel:m_spend_receipt' trip.pk %}" enctype="multipart/form-data" class="tv-card tv-receipt-m" data-receipt-form>{% csrf_token %}
  <label class="tv-btn wide" data-receipt-camera><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg> Take a photo of the receipt<input type="file" name="photo" accept="image/*" capture="environment" hidden onchange="if (this.files.length) { this.form.classList.add('is-reading'); this.form.submit(); }"></label>
  <label class="tv-btn sec wide" data-receipt-choose>Choose a photo<input type="file" name="photo" accept="image/*" hidden onchange="if (this.files.length) { this.form.classList.add('is-reading'); this.form.submit(); }"></label>
  <p class="tv-muted tv-small tv-receipt-tip" style="margin: 0">Amount, currency, day and shop filled in for you to check. The photo is not kept.</p>
  <p class="tv-receipt-wait" style="margin: 0">Reading the receipt&hellip;</p>
</form>
<p class="tv-h3">Or type it in</p>{% endif %}
{% if pre %}<section class="tv-card tv-receipt-read" data-receipt-read><b>{% if pre.read %}Read from the receipt &ndash; check it, then Add.{% else %}Not everything could be read &ndash; fill in the rest.{% endif %}</b>{% for n in pre.notes %}<div class="tv-small" data-receipt-note>{{ n }}</div>{% endfor %}</section>{% endif %}
{% if not trip_start %}<section class="tv-card" data-spend-nodates><p style="margin: 0">The trip needs its dates first &ndash; add a booking, or set From and To on the full site under Edit trip.</p></section>{% else %}
<form method="post" action="{% if s %}{% url 'travel:m_spend_edit' s.pk %}{% else %}{% url 'travel:m_spend_add' trip.pk %}{% endif %}" class="tv-card tv-form" data-spend-form>{% csrf_token %}
  <label for="a" class="tv-muted tv-small">Amount</label>
  <input id="a" name="amount" class="tv-input tv-amount" inputmode="decimal" placeholder="0.00" autocomplete="off" required{% if s %} value="{{ s.amount }}"{% elif pre %} value="{{ pre.amount }}"{% else %} autofocus{% endif %}>
  <div class="tv-two">
    <div><label for="c" class="tv-muted tv-small">Currency</label><select id="c" name="currency" class="tv-select" style="width: 100%">{% for c in currencies %}<option value="{{ c }}"{% if s and c == s.currency or pre and c == pre.currency or not pre and not s and c == 'EUR' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></div>
    <div><label for="d" class="tv-muted tv-small">Day</label><input id="d" type="date" name="day" class="tv-input" value="{{ today|date:'Y-m-d' }}" min="{{ trip_start|date:'Y-m-d' }}" max="{{ trip_end|date:'Y-m-d' }}" data-spend-day-pick></div>
  </div>
  <label for="n" class="tv-muted tv-small">Note (optional)</label><input id="n" name="what" class="tv-input" maxlength="120"{% if s %} value="{{ s.what }}"{% elif pre %} value="{{ pre.what }}"{% endif %}>
  <p class="tv-muted tv-small" style="margin: 0">A day of the trip: {{ trip_start|date:"D j M" }} &ndash; {{ trip_end|date:"D j M" }}.</p>
  <button type="submit" class="tv-btn wide" data-spend-add>{% if s %}Save{% else %}Add{% endif %}</button>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'today.html'), [
        (r'''  <div class="tv-small {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan</div>
</section>{% endif %}
<p class="tv-h3">Today</p>
<section class="tv-card" data-today>{% for b in today_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked today. Enjoy it.</p>{% endfor %}</section>
''',
         r'''  <div class="tv-small {% if bud.ahead %}tv-good{% else %}tv-over{% endif %}" data-bud-pace="{% if bud.ahead %}ahead{% else %}behind{% endif %}">{{ bud.gap_label }} {% if bud.ahead %}ahead of{% else %}behind{% endif %} plan</div>
</section>{% endif %}
{% if card %}{% include 'travel/_city_info.html' with c=card phone=True %}{% endif %}
<p class="tv-h3">Today</p>
<section class="tv-card" data-today>{% for b in today_rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing booked today. Enjoy it.</p>{% endfor %}</section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a>{% endif %}</nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
''',
         r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}<nav class="tv-tabs" aria-label="Trip" style="overflow-x: auto"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}">Bookings</a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary">Itinerary</a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish">Things to do</a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs">Costs</a>{% endif %}<a class="tv-tab{% if sub == 'info' %} on{% endif %}" href="?tab=info" data-tab-info>Good to know</a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
'''),
        (r'''<section class="tv-card" data-itinerary-todo>{% for b in wish %}{% include 'travel/m/_row.html' %}{% endfor %}<a href="?tab=wish" class="tv-muted tv-small">Put them on a day</a></section>{% endif %}
{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. TR-11 - Plan my days, to spread them over the trip. {% endcomment %}
''',
         r'''<section class="tv-card" data-itinerary-todo>{% for b in wish %}{% include 'travel/m/_row.html' %}{% endfor %}<a href="?tab=wish" class="tv-muted tv-small">Put them on a day</a></section>{% endif %}
{% else %}<section class="tv-card"><p class="tv-muted" style="margin: 0">The itinerary needs the trip&rsquo;s dates &mdash; they come from its bookings.</p></section>{% endif %}
{% elif sub == 'info' %}{% comment %} RA12, 22 Nov 2026 - Good to know, a card a city. {% endcomment %}
{% for c in cards %}{% include 'travel/_city_info.html' with phone=True %}{% empty %}<section class="tv-card" data-city-none><p class="tv-muted" style="margin: 0">Good to know shows once the trip has a hotel or a flight to a city.</p></section>{% endfor %}
{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. TR-11 - Plan my days, to spread them over the trip. {% endcomment %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    {% if show_money %}<a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>{% endif %}
</nav>

''',
         r'''    <a class="tv-chip{% if tab == 'wish' %} is-on{% endif %}" href="{% url 'travel:trip_wishlist' trip.pk %}"{% if tab == 'wish' %} aria-current="page"{% endif %}>Things to do{% if wish %} <span class="tv-sub">{{ wish|length }}</span>{% endif %}</a>
    {% if show_money %}<a class="tv-chip{% if tab == 'costs' %} is-on{% endif %}" href="{% url 'travel:trip_costs' trip.pk %}"{% if tab == 'costs' %} aria-current="page"{% endif %}>Costs</a>{% endif %}
    <a class="tv-chip{% if tab == 'info' %} is-on{% endif %}" href="{% url 'travel:trip_info' trip.pk %}"{% if tab == 'info' %} aria-current="page"{% endif %} data-tab-info>Good to know</a>
</nav>

'''),
        (r'''    </section>
{% endif %}
</div>

''',
         r'''    </section>
{% endif %}
{% if tab == 'info' %}{% comment %} RA12, 22 Nov 2026 - Good to know: a card a city (Demetri: "I like 12 - City Info card"). {% endcomment %}
    {% for c in cards %}{% include 'travel/_city_info.html' %}{% empty %}<section class="form-card" data-city-none><p class="tv-sub" style="margin: 0">Good to know shows once the trip has a hotel or a flight to a city.</p></section>{% endfor %}
{% endif %}
</div>

'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('m/trip/<int:trip_id>/pdf/', report.trip_pdf, name='m_trip_pdf'),
    path('<int:trip_id>/wish-list/', views.trip, name='trip_wishlist'),
    path('<int:trip_id>/place/new/', views_places.place_new,
         name='place_new'),
''',
         r'''    path('m/trip/<int:trip_id>/pdf/', report.trip_pdf, name='m_trip_pdf'),
    path('<int:trip_id>/wish-list/', views.trip, name='trip_wishlist'),
    # RA12, 22 Nov 2026 - Good to know; a receipt photo to + Spending.
    path('<int:trip_id>/good-to-know/', views.trip, name='trip_info'),
    path('<int:trip_id>/good-to-know/<int:info_id>/refresh/',
         views_budget.city_refresh, name='city_refresh'),
    path('<int:trip_id>/spend/receipt/', views_budget.spend_receipt,
         name='spend_receipt'),
    path('m/<int:trip_id>/spend/receipt/', views_budget.spend_receipt,
         name='m_spend_receipt'),
    path('<int:trip_id>/place/new/', views_places.place_new,
         name='place_new'),
'''),
    ]),
    (os.path.join('travel', 'views.py'), [
        (r'''def travel_view(fn):
    return login_required(permission_required(PERM, raise_exception=True)(fn))


''',
         r'''def travel_view(fn):
    return login_required(permission_required(PERM, raise_exception=True)(fn))


def _cards(t):
    from . import cityinfo
    return cityinfo.cards_for(t, list(t.bookings.all()))


'''),
        (r'''    t = _trip(request, trip_id)
    tab = {'trip_costs': 'costs', 'trip_itinerary': 'itinerary',
           'trip_wishlist': 'wish'}.get(request.resolver_match.url_name,
                                        'bookings')
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
''',
         r'''    t = _trip(request, trip_id)
    tab = {'trip_costs': 'costs', 'trip_itinerary': 'itinerary',
           'trip_wishlist': 'wish', 'trip_info': 'info'}.get(
        request.resolver_match.url_name, 'bookings')
    bs = list(t.bookings.prefetch_related('travellers'))
    fx.convert_pending(bs)
'''),
        (r'''        if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
''',
         r'''        if tab == 'itinerary' else [],
        'wish': [p for p in pl if not p.day],
        # RA12, 22 Nov 2026 - Good to know, a card a city.
        'cards': _cards(t) if tab == 'info' else [],
        'trip_days': days_of(start, end),
        # TR-7 - after the trip: still To pay? (asked, never done alone)
'''),
    ]),
    (os.path.join('travel', 'views_budget.py'), [
        (r'''        'a': a, 'gq': gquota.usage(), 'used': used,
        'back': request.GET.get('back') or '/travel/'})
''',
         r'''        'a': a, 'gq': gquota.usage(), 'used': used,
        'back': request.GET.get('back') or '/travel/'})


# ------------------------------------------------- RA12 - a receipt photo
@travel_view
@require_POST
def spend_receipt(request, trip_id):
    """RA12, 22 Nov 2026 - + Spending from a receipt photo (Demetri: "The
    user should have the option to manually capture or to take a photo").
    Claude reads it; the form comes back filled in to check and Add. The
    photo is never kept ("Let's not keep the receipt photo")."""
    from django.shortcuts import render
    from . import receipt
    t = _owned(request, trip_id)
    f = request.FILES.get('photo')
    start, end = span(t, list(t.bookings.all()))
    if not start:
        messages.error(request, 'The trip needs its dates first.')
        return _back(request, t)
    end = end or start
    try:
        if f is None:
            raise receipt.LookupError_('Take or choose a photo first.')
        got = receipt.read(f.read(), getattr(f, 'content_type', ''))
    except Exception as e:                              # noqa: BLE001
        messages.error(request, 'The receipt could not be read - %s Type '
                       'it in instead.' % (str(e).rstrip('.') + '.'
                                           if str(e) else ''))
        if _phone(request):
            return redirect('travel:m_spend', trip_id=t.pk)
        return _back(request, t)
    finally:
        if f is not None:
            f.close()
    notes = []
    day = _date(got['date']) if got['date'] else None
    if day and not B.inside(day, start, end):
        notes.append('The receipt is dated %s, outside the trip - pick the '
                     'day.' % _d(day))
        day = None
    cur = got['currency'] if got['currency'] in fx.CURRENCIES else 'EUR'
    if got['currency'] and got['currency'] != cur:
        notes.append('%s cannot be converted here - pick the currency.'
                     % got['currency'])
    if got['amount'] is None:
        notes.append('The total could not be read - type it.')
    pre = {'amount': got['amount'] or '', 'currency': cur,
           'day': day or B.default_day(start, end), 'what': got['merchant'],
           'notes': notes, 'read': got['amount'] is not None}
    if _phone(request):
        from .phone import page
        return page(request, 'travel/m/spend.html', {
            'trip': t, 'tab': 'trips', 'currencies': fx.CURRENCIES,
            's': None, 'pre': pre, 'today': pre['day'],
            'trip_start': start, 'trip_end': end})
    return render(request, 'travel/spend_receipt.html', {
        'trip': t, 'pre': pre, 'currencies': fx.CURRENCIES,
        'trip_start': start, 'trip_end': end})


# ------------------------------------------------- RA12 - Good to know
@travel_view
@require_POST
def city_refresh(request, trip_id, info_id):
    """Refresh a city's Good to know card: Claude writes it again."""
    from . import cityinfo
    from .models import CityInfo
    t = _trip(request, trip_id)
    row = get_object_or_404(CityInfo, pk=info_id)
    cityinfo.refresh(row)
    messages.success(request, 'Good to know for %s is being written again '
                     '- it shows in a moment.' % row.city)
    if (request.POST.get('phone') or '') == '1':
        return redirect('/travel/m/trip/%d/?tab=info' % t.pk)
    return redirect('travel:trip_info', trip_id=t.pk)
'''),
    ]),
    (os.path.join('test_ai_models.py'), [
        (r'''    # Anthropic's web search tool) for Travel's "Add a place".
    'travel/places.py': 'looking up places for Travel',
}

''',
         r'''    # Anthropic's web search tool) for Travel's "Add a place".
    'travel/places.py': 'looking up places for Travel',
    # RA12, 22 Nov 2026 - the tenth and eleventh: Travel's Good to know card
    # for a city (TRAVEL_CITY_MODEL) and reading a receipt photo into
    # + Spending (TRAVEL_RECEIPT_MODEL), both the small model.
    'travel/cityinfo.py': 'the Good to know card for a city',
    'travel/receipt.py': 'reading a receipt photo into Travel spending',
}

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
    raise SystemExit('RA12 REFUSED: %s' % msg)


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
    if "'test_ra12_city_info_receipts.py'" in read(pq):
        print('RA12 already applied.')
        return 0
    if "'test_ra11_category_icons.py'" not in read(pq):
        refuse('RA11 (apply_ra11_category_icons.py) is not applied - this round registers after it.')
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
        print('RA12 --check: %d file(s) would change, none written; %d '
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
    print('RA12 applied - Good to know; + Spending from a receipt photo. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
