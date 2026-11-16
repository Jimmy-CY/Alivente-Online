# -*- coding: utf-8 -*-
"""apply_travel_eight.py - round TR-8, 16 Nov 2026.

RELEASE 88 - TRAVEL: BOARDING PASSES - NEXT, COMING UP, USED.

    - Three tabs at the top of Passes, phone and computer: Next, Coming
      up, Used. Your own pass first; swipe only between the people on the
      same flight.
    - Used passes kept for good, stamped USED in red, the barcode greyed;
      "Show the barcode anyway". Nothing is ever switched off.
    - Used 6 h after the scheduled landing (8 h after leaving with no
      landing time); on a connection the next pass takes over at the
      first flight's landing, "Then:" and "Earlier today" one tap away.
      "Done with this pass" / "Not flown yet" put it right by hand.
    - Add to Google Wallet goes through Alivente: before the flight on to
      the airline, after it a friendly page instead of the airline's error.

New files ship beside this patcher. Stands on TR-7 (apply_travel_seven.py).
Idempotent. Edits backed up to .bak_travel8. MIGRATION: travel 0007 - run
`python manage.py migrate`.
"""
import os
import sys

SUFFIX = '.bak_travel8'
MARK = 'TR-8, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/boarding.py',
    'travel/migrations/0007_pass_marks.py',
    'travel/templates/travel/_pass_desk.html',
    'travel/templates/travel/pass_wallet.html',
    'travel/templates/travel/m/_pass.html',
    'travel/templates/travel/m/pass_wallet.html',
    'test_travel_eight.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-7, 16 Nov 2026 - Release 88: settling up after a trip, comparing
    # trips, past trips when nothing is ahead.
    'test_travel_seven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-7, 16 Nov 2026 - Release 88: settling up after a trip, comparing
    # trips, past trips when nothing is ahead.
    'test_travel_seven.py',
    # TR-8, 16 Nov 2026 - Release 88: boarding passes - Next, Coming up,
    # Used; your own pass first; Google Wallet explained after the flight.
    'test_travel_eight.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-7, 16 Nov 2026 - Release 88: settling up, comparing trips.
    '.bak_travel7',
]

''',
         r'''    # TR-7, 16 Nov 2026 - Release 88: settling up, comparing trips.
    '.bak_travel7',
    # TR-8, 16 Nov 2026 - Release 88 (TR-6 and TR-7 shipped together as
    # R87): boarding passes - Next, Coming up, Used.
    '.bak_travel8',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>On the computer, press <strong>Phone app</strong> on the Travel page: a code and six steps. Scan the code with the phone&rsquo;s camera and tap the link (or type <strong>alivente.online/travel/m/</strong> into Chrome), sign in, tap the <strong>three dots &#8942;</strong> at the top right, scroll down to <strong>Add to Home screen</strong> (or <strong>Install app</strong>), choose <strong>Install</strong> &mdash; not <em>Create shortcut</em> &mdash; and <strong>Install</strong> again. On an iPhone: Safari&rsquo;s Share button &rarr; <strong>Add to Home Screen</strong>. It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> shows every boarding pass to come, one a screen; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed (or three hours after it left, if the booking has no arrival time), the next flight&rsquo;s pass is the one on screen; earlier ones are a swipe back. Each person&rsquo;s pass is kept separately, so the family&rsquo;s passes for one flight sit side by side. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
    <p>On the computer, <strong>Travel &rarr; Boarding passes</strong> shows the same passes, the next one needed marked, each with its barcode &mdash; and every booking shows its own passes.</p>
    <p><strong>Share &rarr; Travel</strong> (Android): share a booking email, a PDF ticket or a screenshot to Travel and it is read exactly like a forwarded email, into To check. To check works on the phone with the same buttons. Adding, editing, sharing and merging trips stay on the full site.</p>
  </article>
''',
         r'''    <p>On the computer, press <strong>Phone app</strong> on the Travel page: a code and six steps. Scan the code with the phone&rsquo;s camera and tap the link (or type <strong>alivente.online/travel/m/</strong> into Chrome), sign in, tap the <strong>three dots &#8942;</strong> at the top right, scroll down to <strong>Add to Home screen</strong> (or <strong>Install app</strong>), choose <strong>Install</strong> &mdash; not <em>Create shortcut</em> &mdash; and <strong>Install</strong> again. On an iPhone: Safari&rsquo;s Share button &rarr; <strong>Add to Home Screen</strong>. It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> has three tabs at the top. <strong>Next</strong> is the flight you need now, full screen, with your own pass first &mdash; swipe sideways for the others on the same flight. <strong>Coming up</strong> lists the flights after it; tap one to open its pass. <strong>Used</strong> keeps every pass for good, stamped <strong>USED</strong> in red with the barcode greyed; <strong>Show the barcode anyway</strong> brings it back in full, as nothing is ever switched off. A pass moves to Used six hours after the flight was due to land (eight hours after it left, if the booking has no landing time), so a delay does not take it away. On a connection &mdash; another flight of yours within a day &mdash; the next pass takes over as soon as the first flight was due to land; before then it is one tap away as <strong>Then: &hellip;</strong> under the pass, and afterwards the first is one tap away as <strong>Earlier today</strong>. Put it right by hand any time: <strong>Done with this pass</strong> moves on at once, and <strong>Not flown yet</strong> on a used pass brings it back to Next for a day. <strong>Add to Google Wallet</strong> goes to the airline until the flight is over; after that a short note explains that airlines stop offering passes to Google Wallet once the flight has flown. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
    <p>On the computer, <strong>Travel &rarr; Boarding passes</strong> has the same three tabs &mdash; Next, Coming up, Used &mdash; each pass with its barcode, and every booking shows its own passes.</p>
    <p><strong>Share &rarr; Travel</strong> (Android): share a booking email, a PDF ticket or a screenshot to Travel and it is read exactly like a forwarded email, into To check. To check works on the phone with the same buttons. Adding, editing, sharing and merging trips stay on the full site.</p>
  </article>
'''),
    ]),
    (os.path.join('test_travel_four.py'), [
        (r'''   'the Travel page: New trip and the phone code only when asked for')
ph = read(J(TA, 'phone.py'))
ok("'orientation': 'portrait'," in ph and "SW_VERSION = 'tv4-1'" in ph and
   'tv-turn-90' in read(J(TA, 'assets', 'travel.js')) and
   'class="tv-holding"' in read(J(TT, 'm', 'passes.html')),
''',
         r'''   'the Travel page: New trip and the phone code only when asked for')
ph = read(J(TA, 'phone.py'))
ok("'orientation': 'portrait'," in ph and "SW_VERSION = 'tv" in ph and
   'tv-turn-90' in read(J(TA, 'assets', 'travel.js')) and
   'class="tv-holding"' in read(J(TT, 'm', 'passes.html')),
'''),
    ]),
    (os.path.join('test_travel_seven.py'), [
        (r'''   'PDF: the Summary / Detailed choice closes once one is picked (Demetri, '
   '16 Nov)')
ok(all('{% if p.wallet_link and not p.over %}' in read(J(TT, *x))
        for x in (('passes.html',), ('m', 'passes.html'), ('booking.html',)))
   and 'p.over = flown(b,' in read(J(TA, 'phone.py')),
   'GOOGLE WALLET: the airline\'s link only before the flight - after it, '
   'the airline answers with an error (Demetri, 16 Nov)')
''',
         r'''   'PDF: the Summary / Detailed choice closes once one is picked (Demetri, '
   '16 Nov)')
# TR-8 (16 Nov) moved this on: the button now goes through Alivente's own
# page, which explains instead of hiding (test_travel_eight.py).
ok((all('{% if p.wallet_link and not p.over %}' in read(J(TT, *x))
         for x in (('passes.html',), ('m', 'passes.html'),
                   ('booking.html',)))
    and 'p.over = flown(b,' in read(J(TA, 'phone.py')))
   or ("travel:pass_wallet" in read(J(TT, 'booking.html')) and
       'boarding.settle([p]' in read(J(TA, 'phone.py'))),
   'GOOGLE WALLET: the airline\'s link only before the flight - after it, '
   'the airline answers with an error (Demetri, 16 Nov)')
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''  .tv-tab.on, .tv-nav a.on { color: #7CC9D2; }
}
''',
         r'''  .tv-tab.on, .tv-nav a.on { color: #7CC9D2; }
}
/* TR-8, 16 Nov 2026 - Passes: Next / Coming up / Used at the top
   (Demetri: "Selection is hidden at the bottom"); USED stamped in red
   diagonally, the barcode greyed, one tap shows it again. */
.tv-seg { display: flex; gap: 4px; margin: 8px 14px 0; padding: 4px; background: #E6ECEE; border-radius: 12px; }
.tv-seg a { flex: 1 1 0; text-align: center; padding: 9px 4px; border-radius: 9px; font-weight: 600; font-size: 14px; color: var(--tv-ink); text-decoration: none; }
.tv-seg a.on { background: #fff; color: var(--tv-teal); box-shadow: 0 1px 3px rgba(16,34,40,.15); }
.tv-pass-foot { position: relative; }
.tv-used-stamp { position: absolute; top: 46%; left: 50%; transform: translate(-50%, -50%) rotate(-28deg); z-index: 2; pointer-events: none; color: #C62828; border: 5px solid #C62828; border-radius: 10px; padding: 2px 18px; font-size: 54px; font-weight: 800; letter-spacing: .12em; opacity: .88; background: rgba(255,255,255,.35); }
.tv-pass.is-used .tv-code-box { opacity: .22; filter: grayscale(1); }
.tv-pass.is-used.show-anyway .tv-code-box { opacity: 1; filter: none; }
.tv-pass.is-used.show-anyway .tv-used-stamp { opacity: .25; }
.tv-pass.is-used .tv-pass-head, .tv-pass.is-used .tv-pass-route, .tv-pass.is-used .tv-pass-grid { filter: grayscale(.7); }
.tv-then { margin-top: 10px; gap: 2px; border-left: 4px solid var(--tv-teal); }
.tv-passrow { background: #fff; border: 1px solid var(--tv-line); border-radius: 14px; margin-bottom: 8px; }
.tv-passrow > summary { list-style: none; cursor: pointer; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; }
.tv-passrow > summary::-webkit-details-marker { display: none; }
.tv-passrow[open] > summary { border-bottom: 1px solid var(--tv-line); }
.tv-passrow .tv-pass { border-radius: 0 0 14px 14px; box-shadow: none; }
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.js'), [
        (r'''    }, {passive: true});
  }
  // TR-4 - a trip's PDF to the phone's share sheet; opened where the phone
  // cannot share files.
''',
         r'''    }, {passive: true});
  }
  // TR-8, 16 Nov 2026 - Passes: the three tabs at the top, a pass opened
  // from "Then" / "Earlier today", and "Show the barcode anyway" on a
  // used pass (nothing is ever switched off).
  var tabs = document.querySelectorAll('[data-tab]');
  function showTab(name) {
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-tab') === name;
      t.classList.toggle('on', on);
      if (on) { t.setAttribute('aria-selected', 'true'); } else { t.removeAttribute('aria-selected'); }
    });
    document.querySelectorAll('[data-tab-panel]').forEach(function (p) {
      p.hidden = p.getAttribute('data-tab-panel') !== name;
    });
    try { history.replaceState(null, '', '?tab=' + name + window.location.hash); } catch (e) {}
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function (e) { e.preventDefault(); showTab(t.getAttribute('data-tab')); });
  });
  document.querySelectorAll('[data-tab-link]').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); showTab(a.getAttribute('data-tab-link')); });
  });
  function openHash() {
    var m = /^#pass-(\d+)$/.exec(window.location.hash);
    if (!m) { return; }
    var card = document.getElementById('pass-' + m[1]);
    var row = card && card.closest('details');
    if (row) { row.open = true; }
    if (card) { card.scrollIntoView({block: 'start'}); }
  }
  openHash();
  window.addEventListener('hashchange', openHash);
  document.querySelectorAll('[data-show-anyway]').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('[data-pass]');
      var on = card.classList.toggle('show-anyway');
      b.textContent = on ? 'Grey it out again' : 'Show the barcode anyway';
    });
  });
  // TR-4 - a trip's PDF to the phone's share sheet; opened where the phone
  // cannot share files.
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    seat = models.CharField(max_length=8, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
''',
         r'''    seat = models.CharField(max_length=8, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    # TR-8, 16 Nov 2026 - put right by hand: 'used' ("Done with this
    # pass") or 'open' ("Not flown yet", holds a day); '' = by the clock.
    marked = models.CharField(max_length=8, blank=True, default='')
    marked_at = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import barcodes, fx, inbox
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
''',
         r'''from django.views.decorators.http import require_POST

from . import barcodes, boarding, fx, inbox
from .models import (BoardingPass, Booking, CheckItem, InboundEmail,
                     trips_for)
'''),
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv4-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv8-1'


'''),
        (r'''                ).strip() or b.segment or b.title
    p.seat_shown = p.seat or info.get('seat', '')
    # TR-7, 16 Nov 2026 - an airline's own "Add to Google Wallet" link stops
    # working once the flight is over (Cyprus Airways answers
    # CKI_BOARDINGPASS_NONEFOUND), so it is offered only before then.
    p.over = flown(b, timezone.localtime().replace(tzinfo=None))
    return p

''',
         r'''                ).strip() or b.segment or b.title
    p.seat_shown = p.seat or info.get('seat', '')
    # TR-7/TR-8, 16 Nov 2026 - an airline's own "Add to Google Wallet" link
    # stops working once the flight is over (Cyprus Airways answers
    # CKI_BOARDINGPASS_NONEFOUND). p.over says so; the Passes page settles
    # it again with every pass in view, so connections count.
    boarding.settle([p], timezone.localtime().replace(tzinfo=None), None)
    return p

'''),
        (r'''@travel_view
def passes(request):
    day = _today()
    every = request.GET.get('show') == 'all'
    qs = BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).exclude(
        booking__status='cancelled').select_related('booking__trip')
    if not every:
        # The week behind stays a swipe back; older trips under Earlier.
        qs = qs.filter(booking__start_date__gte=day - dt.timedelta(days=7))
    rows = sorted(qs, key=lambda p: (p.booking.start_date or dt.date.max,
                                     p.booking.start_time or dt.time(0),
                                     p.booking_id, p.name))
    if every:
        rows.reverse()
    cards = [pass_card(p) for p in rows]
    # DEMETRI, 15 Nov: "We don't have to hide the flights ... the next
    # required boarding pass should always show." Nothing is left out; the
    # page OPENS on the first pass whose flight is not over yet - over
    # once it has landed, by the arrival on the booking, or with no
    # arrival three hours after it left. Earlier ones are a swipe back.
    now = timezone.localtime().replace(tzinfo=None)
    first = 0
    if not every:
        first = next((i for i, p in enumerate(cards)
                      if not flown(p.booking, now)), max(len(cards) - 1, 0))
    for i, p in enumerate(cards):
        p.is_next = i == first
    ctx = {'cards': cards, 'every': every, 'tab': 'passes', 'day': day,
           'first': first}
    # TR-4 (Demetri, 15 Nov: "I want to be able to view boarding passes on
    # the desktop app as well") - the same passes, laid out for a screen.
    if request.resolver_match.url_name == 'passes':
        return render(request, 'travel/passes.html', ctx)
    return page(request, 'travel/m/passes.html', ctx)


''',
         r'''@travel_view
def passes(request):
    """TR-8, 16 Nov 2026 - three tabs at the top: Next, Coming up, Used
    (Demetri: "Selection is hidden at the bottom"). Your own pass first;
    Used ones kept for good, stamped. The rules are in boarding.py."""
    day = _today()
    rows = BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).exclude(
        booking__status='cancelled').select_related('booking__trip')
    cards = [pass_card(p) for p in rows]
    now = timezone.localtime().replace(tzinfo=None)
    nxt, coming, used, earlier, then = boarding.settle(cards, now,
                                                       request.user)
    for p in nxt:
        p.boards = boarding.boards_in(p, now)
    tab = request.GET.get('tab')
    if tab not in ('next', 'coming', 'used'):
        tab = 'next'
    ctx = {'nxt': nxt, 'coming': coming, 'used': used, 'earlier': earlier,
           'then': then, 'last': used[0] if used else None, 'tab_open': tab,
           'tab': 'passes', 'day': day, 'cards': cards}
    # TR-4 (Demetri, 15 Nov: "I want to be able to view boarding passes on
    # the desktop app as well") - the same passes, laid out for a screen.
    if request.resolver_match.url_name == 'passes':
        return render(request, 'travel/passes.html', ctx)
    return page(request, 'travel/m/passes.html', ctx)


def _back(request, phone):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt.startswith('/travel/') and '//' not in nxt:
        return nxt
    return reverse('travel:m_passes' if phone else 'travel:passes')


@require_POST
@travel_view
def pass_mark(request, pass_id, how):
    """"Done with this pass" (how='used') and "Not flown yet" (how='open')
    - Demetri, 16 Nov: nothing is ever switched off by the clock alone."""
    p = get_object_or_404(BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)), pk=pass_id)
    if how not in ('used', 'open'):
        raise Http404
    p.marked, p.marked_at = how, timezone.now()
    p.save(update_fields=['marked', 'marked_at', 'updated_at'])
    phone = request.resolver_match.url_name.startswith('m_')
    return redirect(_back(request, phone))


@travel_view
def pass_wallet(request, pass_id):
    """Add to Google Wallet, through here first (Demetri, 16 Nov: "we need
    to give a nice message explaining this to people. Not have the system
    error out"). Before the flight is over: straight on to the airline.
    After: a card that says why, instead of the airline's error."""
    p = get_object_or_404(BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).select_related(
        'booking__trip'), pk=pass_id)
    if not p.wallet_link:
        raise Http404
    mine = [pass_card(x) for x in BoardingPass.objects.filter(
        booking__trip__in=trips_for(request.user)).exclude(
        booking__status='cancelled').select_related('booking__trip')]
    boarding.settle(mine, timezone.localtime().replace(tzinfo=None),
                    request.user)
    card = next((x for x in mine if x.pk == p.pk), pass_card(p))
    phone = request.resolver_match.url_name.startswith('m_')
    if not card.over:
        return redirect(p.wallet_link)
    ctx = {'p': card, 'tab': 'passes',
           'back': reverse('travel:m_passes' if phone else 'travel:passes')}
    if phone:
        return page(request, 'travel/m/pass_wallet.html', ctx)
    return render(request, 'travel/pass_wallet.html', ctx)


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''  .tv-kv dd { margin-bottom: 8px; }
}
</style>
''',
         r'''  .tv-kv dd { margin-bottom: 8px; }
}
/* TR-8, 16 Nov 2026 - Used boarding passes: USED in red, diagonally; the barcode greyed until "Show the barcode anyway". */
.tv-wpass-foot { position: relative; }
.tv-used-stamp { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-28deg); z-index: 2; pointer-events: none; color: #C62828; border: 4px solid #C62828; border-radius: 8px; padding: 0 14px; font-size: 2.6rem; font-weight: 800; letter-spacing: .12em; opacity: .88; background: rgba(255,255,255,.35); }
.tv-wpass.is-used .tv-code-box { opacity: .22; filter: grayscale(1); }
.tv-wpass.is-used.show-anyway .tv-code-box { opacity: 1; filter: none; }
.tv-wpass.is-used.show-anyway .tv-used-stamp { opacity: .25; }
.tv-wpass.is-used .tv-wpass-top { filter: grayscale(.7); }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'booking.html'), [
        (r'''            <div class="tv-row small"><b>{{ p.name|default:"Passenger" }}</b><span>{{ p.flight }}{% if p.seat_shown %} &middot; seat {{ p.seat_shown }}{% endif %}</span></div>
            {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}">{{ p.svg|safe }}</div>{% endif %}
            {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
        </div>
        {% endfor %}
''',
         r'''            <div class="tv-row small"><b>{{ p.name|default:"Passenger" }}</b><span>{{ p.flight }}{% if p.seat_shown %} &middot; seat {{ p.seat_shown }}{% endif %}</span></div>
            {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}">{{ p.svg|safe }}</div>{% endif %}
            {% if p.wallet_link %}<a href="{% url 'travel:pass_wallet' p.pk %}" target="_blank" rel="noopener" class="small" data-wallet>Add to Google Wallet</a>{% endif %}
        </div>
        {% endfor %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv4-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv8-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv4-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv8-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'passes.html'), [
        (r'''{% extends 'travel/m/base.html' %}
{% comment %} TR-3 - boarding passes, wallet-style: one a screen, swiped sideways, the barcode drawn again from the airline's own code. Kept on the phone for when there is no signal. {% endcomment %}
{% block title %}Passes - Travel{% endblock %}
{% block body_attr %} class="tv-holding"{% endblock %}
{% block top %}<h1>Passes</h1>{% endblock %}
{% block sub %}<div class="sub">{% if every %}Every pass{% else %}The next one you need first{% endif %}</div>{% endblock %}
{% block content %}
{% if cards %}
<div class="tv-passes" data-passes>
{% for p in cards %}
  <article class="tv-pass" data-pass{% if p.is_next %} data-next{% endif %} aria-label="Boarding pass {{ forloop.counter }} of {{ cards|length }}">
    <div class="tv-pass-head"><b style="font-size: 17px">{{ p.booking.provider|default:p.booking.title }}</b><span style="font-size: 12px; opacity: .85">{{ p.booking.start_date|date:"D j M" }}</span></div>
    <div class="tv-pass-route"><div><div style="font-size: 12px; opacity: .8">From</div><div class="tv-pass-code3">{{ p.frm|default:"–" }}</div></div><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="margin-bottom: 12px"><path d="M2 16l20-6-20-6 4 6-4 6z"/></svg><div style="text-align: right"><div style="font-size: 12px; opacity: .8">To</div><div class="tv-pass-code3">{{ p.to|default:"–" }}</div></div></div>
    <div class="tv-pass-grid"><div><small>FLIGHT</small><b>{{ p.flight }}</b></div><div><small>LEAVES</small><b>{{ p.booking.start_time|time:"H:i"|default:"–" }}</b></div><div><small>SEAT</small><b>{{ p.seat_shown|default:"–" }}</b></div><div><small>REF</small><b>{{ p.info.pnr|default:p.booking.reference|default:"–" }}</b></div></div>
    <div class="tv-pass-foot">
      <div class="tv-row" style="width: 100%"><div><div class="tv-muted tv-small">Passenger</div><b>{{ p.name|default:"–" }}</b></div>{% if p.info.seq %}<div style="text-align: right"><div class="tv-muted tv-small">Seq</div><b>{{ p.info.seq }}</b></div>{% endif %}</div>
      {% if p.svg %}<div data-barcode="{{ p.format }}" style="width: 100%; display: flex; justify-content: center">{{ p.svg|safe }}</div>{% else %}<p class="tv-muted" style="margin: 0">This barcode cannot be drawn here - open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      <div class="tv-muted tv-small" style="text-align: center">Show at security and the gate · turn the screen brightness up</div>
      {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" class="tv-btn wide" style="background: #1D2B31; border-color: #1D2B31" target="_blank" rel="noopener">Add to Google Wallet</a>{% endif %}
      <a href="{% url 'travel:m_booking' p.booking.pk %}" class="tv-small">The booking</a>
    </div>
  </article>
{% endfor %}
</div>
{% if cards|length > 1 %}<div class="tv-dots" aria-hidden="true">{% for p in cards %}<span data-dot{% if p.is_next %} class="on"{% endif %}></span>{% endfor %}</div><p class="tv-muted tv-small" style="text-align: center; margin: 0">Swipe for the next pass</p>{% endif %}
{% else %}
<section class="tv-card" data-no-passes><p class="tv-h2">No boarding passes yet</p><p class="tv-muted" style="margin: 0">When the airline emails your boarding pass, forward it to the trips address (or share it to Travel) and it shows here, ready to scan &mdash; even with no signal.</p></section>
{% endif %}
<a href="{% if every %}{% url 'travel:m_passes' %}{% else %}?show=all{% endif %}" class="tv-muted tv-small" style="text-align: center">{% if every %}Only the ones to come{% else %}Earlier passes{% endif %}</a>
{% endblock %}
''',
         r'''{% extends 'travel/m/base.html' %}
{% comment %} TR-3 - boarding passes, wallet-style, the barcode drawn again from the airline's own code, kept on the phone for when there is no signal. TR-8, 16 Nov 2026 - three tabs AT THE TOP (Demetri: "Selection is hidden at the bottom"): Next, Coming up, Used. Your own pass first ("Your Boarding Pass must always come first"); swiped sideways only between the people on the same flight. The rules are in travel/boarding.py. {% endcomment %}
{% block title %}Passes - Travel{% endblock %}
{% block body_attr %} class="tv-holding"{% endblock %}
{% block top %}<h1>Passes</h1>{% endblock %}
{% block tabs %}<nav class="tv-seg" role="tablist" aria-label="Boarding passes" data-pass-tabs>
  <a href="?tab=next" role="tab" data-tab="next"{% if tab_open == 'next' %} class="on" aria-selected="true"{% endif %}>Next</a>
  <a href="?tab=coming" role="tab" data-tab="coming"{% if tab_open == 'coming' %} class="on" aria-selected="true"{% endif %}>Coming up{% if coming %} · {{ coming|length }}{% endif %}</a>
  <a href="?tab=used" role="tab" data-tab="used"{% if tab_open == 'used' %} class="on" aria-selected="true"{% endif %}>Used{% if used %} · {{ used|length }}{% endif %}</a>
</nav>{% endblock %}
{% block content %}
<section data-tab-panel="next"{% if tab_open != 'next' %} hidden{% endif %}>
{% if nxt %}
<div class="tv-passes" data-passes>
{% for p in nxt %}{% include 'travel/m/_pass.html' with lead=forloop.first %}{% endfor %}
</div>
{% if nxt|length > 1 %}<div class="tv-dots" aria-hidden="true">{% for p in nxt %}<span data-dot{% if forloop.first %} class="on"{% endif %}></span>{% endfor %}</div><p class="tv-muted tv-small" style="text-align: center; margin: 0">Swipe for the others on this flight</p>{% endif %}
{% if then %}<a href="?tab=coming#pass-{{ then.pk }}" class="tv-card tv-then" data-then><span class="tv-muted tv-small">Then{% if then.boards %} · {{ then.boards }}{% endif %}</span><b>{{ then.frm|default:"–" }} &rarr; {{ then.to|default:"–" }} {{ then.booking.start_time|time:"H:i" }}</b><span class="tv-small">{{ then.flight }} &ndash; tap to open</span></a>{% endif %}
{% if earlier %}<a href="?tab=used#pass-{{ earlier.pk }}" class="tv-card tv-then" data-earlier><span class="tv-muted tv-small">Earlier today</span><b>{{ earlier.frm|default:"–" }} &rarr; {{ earlier.to|default:"–" }}</b><span class="tv-small">{{ earlier.flight }} &ndash; tap to open</span></a>{% endif %}
{% elif cards %}
<section class="tv-card" data-no-next><p class="tv-h2">No flight coming up</p><p class="tv-muted" style="margin: 0">{% if last %}Your last pass was {{ last.flight }}, {{ last.frm }} &rarr; {{ last.to }} on {{ last.booking.start_date|date:"j M" }}. {% endif %}Every pass is kept under <a href="?tab=used" data-tab-link="used">Used</a>.</p></section>
{% else %}
<section class="tv-card" data-no-passes><p class="tv-h2">No boarding passes yet</p><p class="tv-muted" style="margin: 0">When the airline emails your boarding pass, forward it to the trips address (or share it to Travel) and it shows here, ready to scan &mdash; even with no signal.</p></section>
{% endif %}
</section>
<section data-tab-panel="coming"{% if tab_open != 'coming' %} hidden{% endif %}>
{% for p in coming %}<details class="tv-passrow" data-pass-row id="row-{{ p.pk }}"><summary><span><b>{{ p.booking.start_date|date:"D j M" }}</b> {{ p.booking.start_time|time:"H:i" }}</span><span>{{ p.frm|default:"–" }} &rarr; {{ p.to|default:"–" }} · {{ p.flight }}</span><span class="tv-muted tv-small">{{ p.name|default:"–" }}{% if p.mine %} (you){% endif %}{% if p.seat_shown %} · seat {{ p.seat_shown }}{% endif %}</span></summary>{% include 'travel/m/_pass.html' with lead=False %}</details>
{% empty %}<p class="tv-muted" data-none-coming>Nothing after the next flight.</p>{% endfor %}
</section>
<section data-tab-panel="used"{% if tab_open != 'used' %} hidden{% endif %}>
{% for p in used %}<details class="tv-passrow" data-pass-row id="row-{{ p.pk }}"><summary><span><b>{{ p.booking.start_date|date:"D j M Y" }}</b></span><span>{{ p.frm|default:"–" }} &rarr; {{ p.to|default:"–" }} · {{ p.flight }}</span><span class="tv-muted tv-small">{{ p.name|default:"–" }}{% if p.mine %} (you){% endif %}{% if p.stamped %} · <span style="color: #B3261E; font-weight: 600">USED</span>{% endif %}</span></summary>{% include 'travel/m/_pass.html' with lead=False %}</details>
{% empty %}<p class="tv-muted" data-none-used>No used passes yet. Once a flight is over its pass moves here, stamped USED, and is kept.</p>{% endfor %}
</section>
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'passes.html'), [
        (r'''{% load help_modal_tags %}
{% block title %}Boarding passes - Travel{% endblock %}
{% comment %} TRAVEL - TR-4, 15 Nov 2026. Boarding passes on the computer (Demetri: "I want to be able to view boarding passes on the desktop app as well"): the same passes as the phone, the next one needed first and marked. {% endcomment %}
{% block content %}
{% include 'travel/_style.html' %}
<h2 class="page-title-h2">TRAVEL</h2>
<h4 class="page-subtitle-h4">BOARDING PASSES</h4>
<div class="page-action-buttons">
    <a href="{% if every %}{% url 'travel:passes' %}{% else %}?show=all{% endif %}" class="btn action-secondary">{% if every %}Only the ones to come{% else %}Earlier passes{% endif %}</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
<div class="tv-wrap">
{% if cards %}
<div class="tv-passgrid" data-passes>
{% for p in cards %}
  <article class="tv-wpass{% if p.is_next %} is-next{% endif %}" data-pass{% if p.is_next %} data-next{% endif %} aria-label="Boarding pass {{ forloop.counter }} of {{ cards|length }}">
    {% if p.is_next %}<div class="tv-wpass-flag">Next</div>{% endif %}
    <div class="tv-wpass-top">
      <div class="tv-row"><b>{{ p.booking.provider|default:p.booking.title }}</b><span class="small">{{ p.booking.start_date|date:"D j M Y" }}</span></div>
      <div class="tv-row" style="align-items: flex-end"><div><div class="small">From</div><div class="tv-wpass-code">{{ p.frm|default:"–" }}</div></div><i class="fas fa-plane" aria-hidden="true" style="margin-bottom: 10px"></i><div style="text-align: right"><div class="small">To</div><div class="tv-wpass-code">{{ p.to|default:"–" }}</div></div></div>
      <div class="tv-wpass-grid"><div><small>FLIGHT</small><b>{{ p.flight }}</b></div><div><small>LEAVES</small><b>{{ p.booking.start_time|time:"H:i"|default:"–" }}</b></div><div><small>SEAT</small><b>{{ p.seat_shown|default:"–" }}</b></div><div><small>REF</small><b>{{ p.info.pnr|default:p.booking.reference|default:"–" }}</b></div></div>
    </div>
    <div class="tv-wpass-foot">
      <div class="tv-row" style="width: 100%"><div><div class="tv-sub small">Passenger</div><b>{{ p.name|default:"–" }}</b></div><a href="{% url 'travel:booking' p.booking.pk %}" class="small">The booking</a></div>
      {% if p.svg %}<div class="tv-passcode" data-barcode="{{ p.format }}" style="max-width: 240px; margin: 6px auto 0">{{ p.svg|safe }}</div>{% else %}<p class="tv-sub small" style="margin: 0">This barcode cannot be drawn here &mdash; open the airline&rsquo;s PDF on the booking.</p>{% endif %}
      {% if p.wallet_link and not p.over %}<a href="{{ p.wallet_link }}" target="_blank" rel="noopener" class="small">Add to Google Wallet</a>{% endif %}
    </div>
  </article>
{% endfor %}
</div>
<p class="tv-sub small" style="margin-top: 12px">The barcodes are drawn from the airline&rsquo;s own code and scan from a screen. On the phone, Travel &rarr; Passes shows them one a screen and keeps them for when there is no signal.</p>
{% else %}
<section class="form-card" data-no-passes><p style="margin: 0">No boarding passes yet. Forward the airline&rsquo;s boarding-pass email to <b>trips@alivente.online</b> and it shows here and on the phone.</p></section>
{% endif %}
</div>
{% render_help_modal "travel" %}
{% endblock %}
''',
         r'''{% load help_modal_tags %}
{% block title %}Boarding passes - Travel{% endblock %}
{% comment %} TRAVEL - TR-4, 15 Nov 2026. Boarding passes on the computer (Demetri: "I want to be able to view boarding passes on the desktop app as well"). TR-8, 16 Nov 2026 - the phone's three tabs at the top here too: Next, Coming up, Used; your own pass first; Used ones kept, stamped. Rules in travel/boarding.py. {% endcomment %}
{% block content %}
{% include 'travel/_style.html' %}
<h2 class="page-title-h2">TRAVEL</h2>
<h4 class="page-subtitle-h4">BOARDING PASSES</h4>
<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
</div>
<div class="tv-wrap">
<nav class="tv-chips" role="tablist" aria-label="Boarding passes" data-pass-tabs style="margin-bottom: 14px">
  <a href="?tab=next" role="tab" data-tab="next" class="tv-chip{% if tab_open == 'next' %} is-on{% endif %}">Next</a>
  <a href="?tab=coming" role="tab" data-tab="coming" class="tv-chip{% if tab_open == 'coming' %} is-on{% endif %}">Coming up{% if coming %} &middot; {{ coming|length }}{% endif %}</a>
  <a href="?tab=used" role="tab" data-tab="used" class="tv-chip{% if tab_open == 'used' %} is-on{% endif %}">Used{% if used %} &middot; {{ used|length }}{% endif %}</a>
</nav>
<section data-tab-panel="next"{% if tab_open != 'next' %} hidden{% endif %}>
{% if nxt %}
<div class="tv-passgrid" data-passes>
{% for p in nxt %}{% include 'travel/_pass_desk.html' with lead=forloop.first %}{% endfor %}
</div>
{% if then %}<p style="margin-top: 14px" data-then><a href="?tab=coming#pass-{{ then.pk }}">Then: {{ then.frm|default:"–" }} &rarr; {{ then.to|default:"–" }} {{ then.booking.start_time|time:"H:i" }} ({{ then.flight }})</a></p>{% endif %}
{% if earlier %}<p style="margin-top: 6px" data-earlier><a href="?tab=used#pass-{{ earlier.pk }}">Earlier today: {{ earlier.frm|default:"–" }} &rarr; {{ earlier.to|default:"–" }} ({{ earlier.flight }})</a></p>{% endif %}
{% elif cards %}
<section class="form-card" data-no-next><p style="margin: 0"><b>No flight coming up.</b> {% if last %}Your last pass was {{ last.flight }}, {{ last.frm }} &rarr; {{ last.to }} on {{ last.booking.start_date|date:"j M Y" }}. {% endif %}Every pass is kept under <a href="?tab=used" data-tab-link="used">Used</a>.</p></section>
{% else %}
<section class="form-card" data-no-passes><p style="margin: 0">No boarding passes yet. Forward the airline&rsquo;s boarding-pass email to <b>trips@alivente.online</b> and it shows here and on the phone.</p></section>
{% endif %}
</section>
<section data-tab-panel="coming"{% if tab_open != 'coming' %} hidden{% endif %}>
{% if coming %}<div class="tv-passgrid">{% for p in coming %}{% include 'travel/_pass_desk.html' with lead=False %}{% endfor %}</div>{% else %}<p class="tv-sub" data-none-coming>Nothing after the next flight.</p>{% endif %}
</section>
<section data-tab-panel="used"{% if tab_open != 'used' %} hidden{% endif %}>
{% if used %}<div class="tv-passgrid">{% for p in used %}{% include 'travel/_pass_desk.html' with lead=False %}{% endfor %}</div>{% else %}<p class="tv-sub" data-none-used>No used passes yet. Once a flight is over its pass moves here, stamped USED, and is kept.</p>{% endif %}
</section>
<p class="tv-sub small" style="margin-top: 12px">The barcodes are drawn from the airline&rsquo;s own code and scan from a screen. On the phone, Travel &rarr; Passes shows them one a screen and keeps them for when there is no signal.</p>
</div>
<script>
(function () {
  var tabs = document.querySelectorAll('[data-tab]');
  function show(name) {
    tabs.forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-tab') === name); });
    document.querySelectorAll('[data-tab-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-tab-panel') !== name; });
    try { history.replaceState(null, '', '?tab=' + name); } catch (e) {}
  }
  tabs.forEach(function (t) { t.addEventListener('click', function (e) { e.preventDefault(); show(t.getAttribute('data-tab')); }); });
  document.querySelectorAll('[data-tab-link]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); show(a.getAttribute('data-tab-link')); }); });
  document.querySelectorAll('[data-show-anyway]').forEach(function (b) {
    b.addEventListener('click', function () {
      var on = b.closest('[data-pass]').classList.toggle('show-anyway');
      b.textContent = on ? 'Grey it out again' : 'Show the barcode anyway';
    });
  });
})();
</script>
{% render_help_modal "travel" %}
{% endblock %}
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''    path('<int:trip_id>/itinerary/', views.trip, name='trip_itinerary'),
    path('passes/', phone.passes, name='passes'),
    path('<int:trip_id>/pdf/', report.trip_pdf, name='trip_pdf'),
    # TR-7 - settling up after a trip; comparing trips.
''',
         r'''    path('<int:trip_id>/itinerary/', views.trip, name='trip_itinerary'),
    path('passes/', phone.passes, name='passes'),
    path('pass/<int:pass_id>/wallet/', phone.pass_wallet, name='pass_wallet'),
    path('pass/<int:pass_id>/<str:how>/', phone.pass_mark, name='pass_mark'),
    path('<int:trip_id>/pdf/', report.trip_pdf, name='trip_pdf'),
    # TR-7 - settling up after a trip; comparing trips.
'''),
        (r'''    path('m/booking/<int:booking_id>/', phone.booking, name='m_booking'),
    path('m/passes/', phone.passes, name='m_passes'),
    path('m/check/', phone.check, name='m_check'),
    path('m/check/<int:item_id>/<str:action>/', phone.check_action,
''',
         r'''    path('m/booking/<int:booking_id>/', phone.booking, name='m_booking'),
    path('m/passes/', phone.passes, name='m_passes'),
    path('m/pass/<int:pass_id>/wallet/', phone.pass_wallet,
         name='m_pass_wallet'),
    path('m/pass/<int:pass_id>/<str:how>/', phone.pass_mark,
         name='m_pass_mark'),
    path('m/check/', phone.check, name='m_check'),
    path('m/check/<int:item_id>/<str:action>/', phone.check_action,
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
    raise SystemExit('TR-8 REFUSED: %s' % msg)


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
    if "'test_travel_eight.py'" in read(pq):
        print('TR-8 already applied.')
        return 0
    if "'test_travel_seven.py'" not in read(pq):
        refuse('TR-7 (apply_travel_seven.py, Release 87) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new travel files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-8 --check: %d file(s) would change, none written; %d '
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
    print('TR-8 applied - boarding passes: Next, Coming up, Used. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
