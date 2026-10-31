# -*- coding: utf-8 -*-
"""apply_wellness_twelve.py - round CY-2, 31 Oct 2026.

RELEASE 55 - WELLNESS: CYCLE PHASES.

    - The phase card on the cycle page: the day of the cycle and its phase
      on a soft wave, Today or Tomorrow (Demetri, sharing Lively, 31 Oct
      15:41).
    - One tap: "My period started" and "My period ended".
    - Do - Move - Eat: ideas for each phase, with why and how; any can be
      hidden (15:46). A short line for the day.
    - Long-press shortcuts on the app icon: Breathe, check-in, weigh-in.

New files ship beside this patcher. Stands on Release 54. Idempotent.
Edits backed up to .bak_wellness12. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness12'
MARK = 'CY-2, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/phases.py',
    'test_wellness_twelve.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl11-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl12-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl11-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl12-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle.html'), [
        (r'''</section>

<a class="w-btn full" href="{% url 'wellness:cycle_log' %}">{% if logged_today %}Change today{% else %}Log today{% endif %}</a>

''',
         r'''</section>

{% comment %}
  CY-2, 31 Oct 2026 - the phase card (Demetri, sharing Lively, 15:41): the
  day of the cycle and its phase on a soft wave, Today or Tomorrow; one tap
  for "My period started" and "My period ended"; a line for the day; and
  the Do - Move - Eat board (15:46). Ideas, not rules. Phases are estimates.
{% endcomment %}
{% if card %}
<section class="w-card w-phase" data-phase-card>
  <nav class="w-seg" aria-label="Which day">
    <a href="{% url 'wellness:cycle' %}"{% if when == 'today' %} class="is-on" aria-current="true"{% endif %}>Today</a>
    <a href="{% url 'wellness:cycle' %}?when=tomorrow"{% if when == 'tomorrow' %} class="is-on" aria-current="true"{% endif %}>Tomorrow</a>
  </nav>
  <p class="w-quiet" style="margin:0;text-align:center">{% if when == 'tomorrow' %}Tomorrow is day {{ card.day }}{% else %}Day {{ card.day }}{% endif %} of your cycle{% if open_day and when == 'today' %} · day {{ open_day }} of your period{% endif %}</p>
  {% if card.phase %}
  <h2 class="w-phase-name">{{ card.name }}</h2>
  <svg class="w-wave" viewBox="0 0 {{ wave.w }} {{ wave.h }}" role="img" aria-label="{{ card.name }}, day {{ card.day }}"><path d="{{ wave.d }}"/><circle cx="{{ wave.cx }}" cy="{{ wave.cy }}" r="8"/></svg>
  {% if card.estimated %}<p class="w-small w-quiet" style="margin:0;text-align:center">An estimate until a couple of cycles are logged.</p>{% elif card.late %}<p class="w-small w-quiet" style="margin:0;text-align:center">Longer than your usual cycle - your period may be on its way.</p>{% endif %}
  {% else %}
  <p class="w-small w-quiet" style="margin:0;text-align:center">{{ card.why_none }}</p>
  {% endif %}
  {% if when == 'today' and not locked %}
  {% if open_from %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}" class="w-btn-row">{% csrf_token %}<input type="hidden" name="do" value="end"><button type="submit" class="w-btn w-sand-btn" style="flex:1">My period ended</button></form>
  <form method="post" action="{% url 'wellness:cycle_quick' %}" style="text-align:center">{% csrf_token %}<input type="hidden" name="do" value="end"><input type="hidden" name="on" value="yesterday"><button type="submit" class="w-linkbtn w-small">It ended yesterday</button></form>
  {% elif can_start %}
  <form method="post" action="{% url 'wellness:cycle_quick' %}" class="w-btn-row">{% csrf_token %}<input type="hidden" name="do" value="start"><button type="submit" class="w-btn w-sand-btn" style="flex:1">My period started</button></form>
  {% endif %}
  {% endif %}
</section>
{% if card.title %}
<section class="w-card soft" style="gap:6px" data-phase-line>
  <span class="w-label">{{ card.title }}</span>
  <p style="margin:0">{{ card.line }}</p>
</section>
{% endif %}
{% if board %}
<section class="w-card" id="board" aria-labelledby="board-h" data-board>
  <h2 class="w-h2" id="board-h">Ideas for {% if when == 'tomorrow' %}tomorrow{% else %}today{% endif %}</h2>
  <p class="w-small w-quiet" style="margin:0">Ideas, not rules. Tap one to see why and how; hide any you do not want.</p>
  {% for g, gname, items in board %}{% if items %}
  <div class="w-label">{{ gname }}</div>
  <div class="w-ideas">
    {% for it in items %}
    <details class="w-idea">
      <summary>{{ it.name }}</summary>
      <p><b>Why</b> {{ it.why }}</p>
      <p><b>How</b> {{ it.how }}</p>
      <div class="w-idea-acts">
        {% if it.link %}<a class="w-btn ghost" href="{{ it.link }}">Open</a>{% endif %}
        <form method="post" action="{% url 'wellness:cycle_quick' %}">{% csrf_token %}<input type="hidden" name="do" value="hide"><input type="hidden" name="tip" value="{{ it.key }}"><input type="hidden" name="when" value="{{ when }}"><button type="submit" class="w-btn quiet">Hide this idea</button></form>
      </div>
    </details>
    {% endfor %}
  </div>
  {% endif %}{% endfor %}
  {% if hidden_n %}<form method="post" action="{% url 'wellness:cycle_quick' %}">{% csrf_token %}<input type="hidden" name="do" value="unhide"><input type="hidden" name="when" value="{{ when }}"><button type="submit" class="w-linkbtn w-small">Show the {{ hidden_n }} idea{{ hidden_n|pluralize }} you hid</button></form>{% endif %}
</section>
{% endif %}
{% endif %}

<a class="w-btn full" href="{% url 'wellness:cycle_log' %}">{% if logged_today %}Change today{% else %}Log today{% endif %}</a>

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-strip i.today { box-shadow: inset 0 0 0 2px var(--w-sage); background: transparent; }
.w-linkbtn { background: none; border: none; padding: 0; font: inherit; color: var(--w-sage-deep); text-decoration: underline; cursor: pointer; }
''',
         r'''.w-strip i.today { box-shadow: inset 0 0 0 2px var(--w-sage); background: transparent; }
.w-linkbtn { background: none; border: none; padding: 0; font: inherit; color: var(--w-sage-deep); text-decoration: underline; cursor: pointer; }

/* ---- CY-2, 31 Oct 2026 - cycle phases: the card, the wave, the board. */
.w-phase { align-items: stretch; }
.w-phase-name { margin: 0; text-align: center; font-family: var(--w-serif); font-weight: 400; font-size: 30px; line-height: 1.2; }
.w-wave { width: 100%; height: auto; display: block; }
.w-wave path { fill: none; stroke: var(--w-rose-soft); stroke-width: 5; stroke-linecap: round; }
.w-wave circle { fill: var(--w-card); stroke: var(--w-rose-deep); stroke-width: 3; }
.w-sand-btn { background: var(--w-sand); color: var(--w-sand-ink); }
.w-ideas { display: flex; flex-direction: column; gap: 8px; }
.w-idea { background: var(--w-bg); border-radius: 14px; padding: 0 14px; }
.w-idea summary { min-height: 48px; display: flex; align-items: center; cursor: pointer; font-size: 16px; list-style: none; }
.w-idea summary::-webkit-details-marker { display: none; }
.w-idea summary::after { content: '+'; margin-left: auto; color: var(--w-quiet); font-size: 20px; }
.w-idea[open] summary::after { content: '–'; }
.w-idea p { margin: 0 0 8px; font-size: 14px; color: var(--w-quiet); }
.w-idea p b { color: var(--w-ink); font-weight: 600; margin-right: 4px; }
.w-idea-acts { display: flex; gap: 8px; align-items: center; padding-bottom: 10px; flex-wrap: wrap; }
'''),
    ]),
    (os.path.join('wellness', 'cycle.py'), [
        (r'''
DEFAULT_SETTINGS = {'on': False, 'fertile': False, 'mode': 'normal',
                    'remind': False}

# A gap of one dry day inside a period does not end it.
''',
         r'''
DEFAULT_SETTINGS = {'on': False, 'fertile': False, 'mode': 'normal',
                    'remind': False,
                    # CY-2 - a period begun with one tap and not yet
                    # ended (an ISO date), and the board ideas hidden.
                    'open_period': '', 'hidden_tips': ()}

# A gap of one dry day inside a period does not end it.
'''),
    ]),
    (os.path.join('wellness', 'views_cycle.py'), [
        (r'''@wellness_view
def home(request):
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return render(request, 'wellness/cycle_intro.html', {
            'tab': 'cycle', 'had': bool(days)})
    today = _today()
    s = C.summary(days, today, prefs)
    month = request.GET.get('m', '')
    try:
''',
         r'''@wellness_view
def home(request):
    from . import phases as PH
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return render(request, 'wellness/cycle_intro.html', {
            'tab': 'cycle', 'had': bool(days)})
    today = _today()
    s = C.summary(days, today, prefs)
    # CY-2 - a period begun with one tap closes itself if nobody ends it.
    if not prefs.get('locked') and PH.tidy(prefs, days, today,
                                           s.get('avg_period')):
        C.save(request.user, prefs, days)
        s = C.summary(days, today, prefs)
    when = 'tomorrow' if request.GET.get('when') == 'tomorrow' else 'today'
    card = PH.place(s, when)
    open_from = PH.open_start(prefs)
    month = request.GET.get('m', '')
    try:
'''),
        (r'''        'logged_today': today.isoformat() in days,
        'locked': prefs.get('locked'),
    })


''',
         r'''        'logged_today': today.isoformat() in days,
        'locked': prefs.get('locked'),
        # CY-2 - the phase card, the one-tap buttons and the board.
        'when': when,
        'card': card,
        'wave': PH.wave(card['frac']) if card else None,
        'open_from': open_from,
        'open_day': (today - open_from).days + 1 if open_from else None,
        'can_start': not open_from and not s.get('in_period') and
        s['state'] not in ('pregnant',),
        'board': PH.board(card['phase'], prefs.get('hidden_tips'))
        if card and card['phase'] else [],
        'hidden_n': len([k for k in (prefs.get('hidden_tips') or ())
                         if k in PH.ALL_KEYS]),
    })


@wellness_view
@require_POST
def quick(request):
    """CY-2 - one tap: started, ended (today or yesterday), hide or show
    an idea on the board."""
    from . import phases as PH
    rec, prefs, days = C.load(request.user)
    if not prefs['on'] or prefs.get('locked'):
        return _off()
    today = _today()
    what = request.POST.get('do', '')
    if what == 'start':
        PH.start(prefs, days, today)
    elif what == 'end':
        on = today - dt.timedelta(days=1) \
            if request.POST.get('on') == 'yesterday' else today
        PH.end(prefs, days, today, on)
    elif what == 'hide' and request.POST.get('tip') in PH.ALL_KEYS:
        hidden = list(prefs.get('hidden_tips') or ())
        if request.POST['tip'] not in hidden:
            hidden.append(request.POST['tip'])
        prefs['hidden_tips'] = hidden
    elif what == 'unhide':
        prefs['hidden_tips'] = []
    C.save(request.user, prefs, days)
    back = reverse('wellness:cycle')
    if request.POST.get('when') == 'tomorrow':
        back += '?when=tomorrow'
    return redirect(back + ('#board' if what in ('hide', 'unhide') else ''))


'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''             'purpose': 'maskable'},
        ],
    }
    return HttpResponse(json.dumps(data),
''',
         r'''             'purpose': 'maskable'},
        ],
        # CY-2, 31 Oct 2026 - long-press the Wellness icon. (Android does
        # not let web apps add home-screen widgets; these are the nearest.)
        # Nothing about the cycle here: anyone can long-press a phone.
        'shortcuts': [
            {'name': 'Breathe', 'short_name': 'Breathe',
             'url': '/wellness/calm/breathe/?source=shortcut'},
            {'name': 'Evening check-in', 'short_name': 'Check-in',
             'url': '/wellness/journal/new/?kind=checkin'},
            {'name': 'Weigh in', 'short_name': 'Weigh in',
             'url': '/wellness/body/weigh/'},
        ],
    }
    return HttpResponse(json.dumps(data),
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl11-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl12-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('cycle/', CY.home, name='cycle'),
    path('cycle/log/', CY.log_day, name='cycle_log'),
    path('cycle/settings/', CY.settings_page, name='cycle_settings'),
    path('cycle/patterns/', CY.patterns, name='cycle_patterns'),
''',
         r'''    path('cycle/', CY.home, name='cycle'),
    path('cycle/log/', CY.log_day, name='cycle_log'),
    # CY-2, 31 Oct 2026 - one tap: started, ended, hide an idea.
    path('cycle/quick/', CY.quick, name='cycle_quick'),
    path('cycle/settings/', CY.settings_page, name='cycle_settings'),
    path('cycle/patterns/', CY.patterns, name='cycle_patterns'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
''',
         r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
     'a': 'Four stretches of a cycle: menstrual (your period), follicular '
          '(energy often rises), ovulation (often the most energetic days) '
          'and luteal (winding down before the next period). Wellness '
          'estimates them from your own averages, so they sharpen as you '
          'log. With very irregular cycles, pregnancy or hormonal '
          'contraception it shows the day only.'},
    {'q': 'What are the ideas on the cycle page?',
     'a': 'A few things to do, move and eat that suit the phase - each '
          'with why and how. They are ideas, not rules, and nothing in them '
          'is medical advice. Hide any you do not want; "Show the ideas you '
          'hid" brings them back.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'cycle': {
        'title': 'Cycle',
        'purpose': 'Where you are in your cycle, and when the next period '
                   'is likely.',
        'steps': [
            'Tap Log today on the first day you bleed, and each day after.',
            'Tap any past day on the calendar to fill it in or change it.',
            'Predictions start after two cycles, as a window of a few days.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
        ],
        'signs': [
            ('--w-rose-soft', 'Rose days: your period.'),
            ('--w-rose', 'Outlined days: when the next one is expected.'),
''',
         r'''    'cycle': {
        'title': 'Cycle',
        'purpose': 'Where you are in your cycle, its phase, and when the '
                   'next period is likely.',
        'steps': [
            'The card at the top shows the day of your cycle and its phase '
            'on a soft wave. Tomorrow shows the next day.',
            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: things to do, move and eat for the phase. '
            'Tap one for why and how; hide any you do not want.',
            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
            'Predictions start after two cycles, as a window of a few days.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
        ],
        'signs': [
            ('--w-rose-deep', 'The dot on the wave: where you are. The '
                              'phases are estimates from your own '
                              'averages.'),
            ('--w-rose-soft', 'Rose days: your period.'),
            ('--w-rose', 'Outlined days: when the next one is expected.'),
'''),
        (r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done',
}

''',
         r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done', 'cycle_quick',
}

'''),
    ]),
    (os.path.join('test_wellness_cycle.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def summary('" in gate, '  with a sentinel on the predictions')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# CY-2 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/cycle.py'; Text = " in gate,
   '  with a sentinel on the predictions')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'MOD.checkin_on(mods)'; What = 'WL-4b/WL-9: the reminder rules are on disk, skipping switched-off sections - without them the reminder job cannot run' },
''',
         r'''    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'open_period'; What = 'CY-1/CY-2: the cycle rules are on disk, with the one-tap period - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'MOD.checkin_on(mods)'; What = 'WL-4b/WL-9: the reminder rules are on disk, skipping switched-off sections - without them the reminder job cannot run' },
'''),
        (r'''    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'def place('; What = 'CY-2: the cycle phases are on disk - without them the cycle tracker cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_ten.py',
    # WL-9, 31 Oct 2026 - Wellness: your sections.
    'test_wellness_eleven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_ten.py',
    # WL-9, 31 Oct 2026 - Wellness: your sections.
    'test_wellness_eleven.py',
    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    'test_wellness_twelve.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-9, 31 Oct 2026 - Wellness: your sections.
    '.bak_wellness11',
]

''',
         r'''    # WL-9, 31 Oct 2026 - Wellness: your sections.
    '.bak_wellness11',
    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    '.bak_wellness12',
]

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
    raise SystemExit('CY-2 REFUSED: %s' % msg)


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
    if "'test_wellness_twelve.py'" in read(pq):
        print('CY-2 already applied.')
        return 0
    if "'test_wellness_eleven.py'" not in read(pq):
        refuse('Release 54 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('CY-2 --check: %d file(s) would change, none written; %d '
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
    print('CY-2 applied - Wellness: cycle phases.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
