# -*- coding: utf-8 -*-
"""apply_wellness_six.py - round WL-4c, 30 Oct 2026.

RELEASE 49 - WELLNESS W-4c: A LINE FROM CLAUDE UNDER THE DAILY QUOTE.

    - Claude picks the day's quote from the curated library, by number,
      and writes one short line beneath it, labelled "A line from Claude".
      It is told only the first name, today's habit names and how the
      week has gone - never the journal, the weight or the cycle log.
    - Made ahead by the reminder job (every 15 minutes) with the house
      ANTHROPIC_API_KEY; Today never waits on Claude. Can be turned off
      in Wellness settings.

New files ship beside this patcher. Stands on Release 48. Idempotent.
Edits backed up to .bak_wellness6. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness6'
MARK = 'WL-4c, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/daily_line.py',
    'test_wellness_six.py',
)

SWAPS = [
    (os.path.join('wellness', 'views.py'), [
        (r'''                for k, label in Habit.TIMES if groups[k]]
    hello, part = _greeting(now)
    left = total - done_n
    if total == 0:
''',
         r'''                for k, label in Habit.TIMES if groups[k]]
    hello, part = _greeting(now)
    from . import daily_line as DL
    DL.seen(profile, day)
    quote, claude_line = DL.for_today(request.user, day, profile)
    left = total - done_n
    if total == 0:
'''),
        (r'''        'name': _first_name(request.user),
        'date': day,
        'quote': for_day(request.user.pk, day),
        'sections': sections,
        'total': total,
''',
         r'''        'name': _first_name(request.user),
        'date': day,
        'quote': quote,
        # WL-4c - Claude's line under the quote, when one was made today.
        'claude_line': claude_line,
        'sections': sections,
        'total': total,
'''),
        (r'''    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
''',
         r'''    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
        # WL-4c - the line from Claude is on unless turned off here.
        prefs['line_off'] = not request.POST.get('claude_line')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
'''),
        (r'''        'tab': 'today',
        'weekly': bool(prefs.get('weekly_email')),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
''',
         r'''        'tab': 'today',
        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl5-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl6-1'


'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'once a day at most. On iPhone, use the Wellness app on your '
          'home screen.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
''',
         r'''          'once a day at most. On iPhone, use the Wellness app on your '
          'home screen.'},
    {'q': 'Where does the line under the quote come from?',
     'a': 'Claude picks one quote from the same library of real quotes and '
          'writes one short line under it, labelled "A line from Claude". '
          'It sees only your first name, today\'s habit names and how the '
          'week has gone - never your journal, weight or cycle log. Turn '
          'it off in Settings.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-badge.slate { background: var(--w-badge-slate); }
.w-badge.todo { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-ring-off); color: var(--w-quiet); width: 40px; height: 40px; font-size: 13px; }
''',
         r'''.w-badge.slate { background: var(--w-badge-slate); }
.w-badge.todo { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-ring-off); color: var(--w-quiet); width: 40px; height: 40px; font-size: 13px; }

/* WL-4c, 30 Oct 2026 - Claude's line under the quote: quieter than the
   quote, clearly labelled, never mistaken for it. */
.w-claude-line { margin: 4px 0 0; padding-top: 12px; border-top: 1px solid var(--w-sand-line); font-size: 15px; line-height: 1.5; display: flex; flex-direction: column; gap: 4px; }
.w-claude-line .w-label { color: var(--w-sand-ink); }
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl5-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl6-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl5-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl6-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  <p class="w-quote">“{{ quote.text }}”</p>
  <div class="w-quote-by">{{ quote.author }}{% if quote.source %} · {{ quote.source }}{% endif %}</div>
</section>

''',
         r'''  <p class="w-quote">“{{ quote.text }}”</p>
  <div class="w-quote-by">{{ quote.author }}{% if quote.source %} · {{ quote.source }}{% endif %}</div>
  {# WL-4c - one labelled line from Claude, who picked the quote above from the library. #}
  {% if claude_line %}<p class="w-claude-line" data-claude-line><span class="w-label">A line from Claude</span>{{ claude_line }}</p>{% endif %}
</section>

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  <p class="w-small w-quiet" style="margin:0">Leave a time empty for no reminder. A habit gets its own reminder time when you edit it.{% if reminded_habits %} Now: {% for h in reminded_habits %}{{ h.name }} at {{ h.remind_at|time:"H:i" }}{% if not forloop.last %}, {% endif %}{% endfor %}.{% endif %} Nothing is sent once it is done.</p>

  <h2 class="w-h2">Weekly summary</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="weekly_email" value="1"{% if weekly %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Email me a summary every Monday morning<br><span class="w-small w-quiet">Your habits, workouts, weight trend and any new badges. Never your journal, and never your cycle log.</span></span></label>
''',
         r'''  <p class="w-small w-quiet" style="margin:0">Leave a time empty for no reminder. A habit gets its own reminder time when you edit it.{% if reminded_habits %} Now: {% for h in reminded_habits %}{{ h.name }} at {{ h.remind_at|time:"H:i" }}{% if not forloop.last %}, {% endif %}{% endfor %}.{% endif %} Nothing is sent once it is done.</p>

  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="claude_line" value="1"{% if claude_line %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Let Claude pick the quote and add a line for me<br><span class="w-small w-quiet">Claude chooses from the same library of real quotes and writes one short line under it. It sees only your first name, today's habit names and how the week has gone - never your journal, your weight or your cycle log.</span></span></label>
  <h2 class="w-h2">Weekly summary</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="weekly_email" value="1"{% if weekly %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Email me a summary every Monday morning<br><span class="w-small w-quiet">Your habits, workouts, weight trend and any new badges. Never your journal, and never your cycle log.</span></span></label>
'''),
    ]),
    (os.path.join('wellness', 'management', 'commands', 'wellness_reminders.py'), [
        (r'''time (wellness/reminders.py). Without the two push keys in Railway it says
so and sends nothing. --dry-run writes what it would send.
"""
from django.core.management.base import BaseCommand
''',
         r'''time (wellness/reminders.py). Without the two push keys in Railway it says
so and sends nothing. --dry-run writes what it would send.

WL-4c, 30 Oct 2026 - each run also makes the day's line from Claude for
anyone still without one (wellness/daily_line.py), before the reminders.
"""
from django.core.management.base import BaseCommand
'''),
        (r'''
    def handle(self, *args, **opts):
        if not P.configured() and not opts['dry_run']:
            self.stdout.write('Wellness reminders: the push keys are not '
''',
         r'''
    def handle(self, *args, **opts):
        # WL-4c - first, the day's line from Claude for anyone who has
        # none yet. Guarded: a failure here never stops the reminders.
        if not opts['dry_run']:
            try:
                from wellness import daily_line as DL
                made = DL.run(timezone.localtime())
                if made:
                    self.stdout.write('Wellness daily line: %d made.' % made)
            except Exception as exc:                      # noqa: BLE001
                self.stdout.write('Wellness daily line failed: %s' % exc)
        if not P.configured() and not opts['dry_run']:
            self.stdout.write('Wellness reminders: the push keys are not '
'''),
    ]),
    (os.path.join('test_wellness_five.py'), [
        (r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
ok(_v == ['wl5-1', 'wl5-1'] and "SW_VERSION = 'wl5-1'" in views,
   'the asset version moved together (wl5-1): phones fetch the new worker',
   _v)
ok('name="remind_at"' in read(J(WT, 'habit_form.html')),
   'the habit form has a reminder time')
''',
         r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
# Later rounds move the version on (WL-4c: wl6-1); what must hold is that
# the page and the service worker always name the same one.
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in views, 'the asset version moved together (wl5-1): phones fetch the '
   'new worker', _v)
ok('name="remind_at"' in read(J(WT, 'habit_form.html')),
   'the habit form has a reminder time')
'''),
    ]),
    (os.path.join('test_ai_models.py'), [
        (r'''    # exactly what the list is for.
    'pages/translation_service.py': 'English to Greek translation',
}

''',
         r'''    # exactly what the list is for.
    'pages/translation_service.py': 'English to Greek translation',
    # WL-4c, 30 Oct 2026 - the sixth: one short line under the Wellness
    # quote, made ahead by the reminder job. Same small model as invoice
    # verification, changeable through WELLNESS_LINE_MODEL.
    'wellness/daily_line.py': 'the line under the Wellness daily quote',
}

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def parse('; What = 'WL-4c: the line rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_four.py',
    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    'test_wellness_five.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_four.py',
    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    'test_wellness_five.py',
    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    'test_wellness_six.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    '.bak_wellness5',
]

''',
         r'''    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    '.bak_wellness5',
    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    '.bak_wellness6',
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
    raise SystemExit('WL-4c REFUSED: %s' % msg)


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
    if "'test_wellness_six.py'" in read(pq):
        print('WL-4c already applied.')
        return 0
    if "'test_wellness_five.py'" not in read(pq):
        refuse('Release 48 is not applied - this round registers after it.')
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
        print('WL-4c --check: %d file(s) would change, none written; %d '
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
    print('WL-4c applied - Wellness: a line from Claude under the quote.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
