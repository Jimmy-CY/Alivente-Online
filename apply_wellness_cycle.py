# -*- coding: utf-8 -*-
"""apply_wellness_cycle.py - round CY-1, 30 Oct 2026.

RELEASE 46 - WELLNESS: THE CYCLE TRACKER (opt-in).

    - Off by default; turned on from the Wellness guide. Then a Cycle tab,
      a discreet Today line, the overview (cycle-day ring, next period as
      a window, month calendar), a day log (flow, symptoms, pain, a
      private note), patterns, a printable doctor report, gentle doctor
      flags, pregnancy and hormonal-contraception modes, download and
      delete.
    - The fertile-window estimate is off by default and always labelled
      "an estimate, not contraception".
    - The WHOLE record is encrypted with the journal key - every day and
      every setting, and no plain date column.

New files ship beside this patcher. Stands on Release 45. Idempotent.
Edits backed up to .bak_cycle1.
MIGRATION: wellness 0005 - run  python manage.py migrate.
"""
import os
import sys

SUFFIX = '.bak_cycle1'
MARK = 'CY-1, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/cycle.py',
    'wellness/views_cycle.py',
    'wellness/migrations/0005_cycle.py',
    'wellness/templatetags/__init__.py',
    'wellness/templatetags/wellness_cycle.py',
    'wellness/templates/wellness/cycle_intro.html',
    'wellness/templates/wellness/cycle.html',
    'wellness/templates/wellness/cycle_log.html',
    'wellness/templates/wellness/cycle_settings.html',
    'wellness/templates/wellness/cycle_patterns.html',
    'wellness/templates/wellness/cycle_report.html',
    'test_wellness_cycle.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''        db_table = 'wellness_workout_set'
        ordering = ['position', 'set_no']
''',
         r'''        db_table = 'wellness_workout_set'
        ordering = ['position', 'set_no']


class CycleRecord(models.Model):
    """CY-1, 30 Oct 2026 - the cycle tracker's whole record, one row per
    person who has turned it on.

    EVERYTHING IS LOCKED (decision 3 of 30 Oct, "encrypt the whole
    record"). `prefs` is a Fernet token of {"on", "fertile", "mode",
    "remind"}; `days` is a Fernet token of {"days": {"2026-10-07": {"flow",
    "sym", "pain", "relief", "note"}}}. There is deliberately no date
    column: a plain list of dates would give a period away on its own.
    Only wellness/cycle.py opens or closes these.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='wellness_cycle')
    prefs = models.TextField(blank=True)
    days = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_cycle_record'

    def __str__(self):
        return 'Cycle record of %s' % self.user
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
''',
         r'''        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day),
        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
'''),
        (r'''def _workout_card(user, day):
    from .views_workouts import today_card
    return today_card(user, day)

''',
         r'''def _workout_card(user, day):
    from .views_workouts import today_card
    return today_card(user, day)


def _cycle_card(user, day):
    from .views_cycle import today_card
    return today_card(user, day)

'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl3-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'cy1-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''
from . import views
from . import views_workouts as W

''',
         r'''
from . import views
from . import views_cycle as CY
from . import views_workouts as W

'''),
        (r'''    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
''',
         r'''    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
    # CY-1, 30 Oct 2026 - the cycle tracker (opt-in). No pk anywhere:
    # every page is the signed-in person's own record.
    path('cycle/', CY.home, name='cycle'),
    path('cycle/log/', CY.log_day, name='cycle_log'),
    path('cycle/settings/', CY.settings_page, name='cycle_settings'),
    path('cycle/patterns/', CY.patterns, name='cycle_patterns'),
    path('cycle/report/', CY.report, name='cycle_report'),
    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    'workout_previous': 'The grey numbers are last time. Beat them by a rep '
                        'or a little weight and you are making progress.',
}

''',
         r'''    'workout_previous': 'The grey numbers are last time. Beat them by a rep '
                        'or a little weight and you are making progress.',
    # CY-1
    'cycle_private': 'Your cycle log is locked before it is saved - every '
                     'day and every setting. Only you can open it.',
    'cycle_log': 'Log the first day you bleed, then each day after. '
                 'Symptoms are optional - log only what helps you.',
}

'''),
        (r'''          'still asks you to log in again after an hour - property and '
          'finance stay as protected as they were.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
''',
         r'''          'still asks you to log in again after an hour - property and '
          'finance stay as protected as they were.'},
    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Open the Cycle tracker '
          'link at the bottom of this guide. It then gets its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
     'a': 'Only you. The whole log - every day, every symptom, every '
          'setting - is locked before it is saved. It never appears in an '
          'email, and a reminder only ever says "A Wellness reminder".'},
    {'q': 'How does Wellness predict my next period?',
     'a': 'From the middle of your last six cycles, shown as a window of '
          'a few days that widens when your cycles vary. It needs two '
          'cycles before it guesses. Pregnancy and hormonal-contraception '
          'modes switch predictions off.'},
    {'q': 'What is the fertile estimate?',
     'a': 'A rough window of days counted back from your next expected '
          'period. It is off unless you turn it on, and it is an estimate, '
          'not contraception - never rely on it to prevent a pregnancy.'},
    {'q': 'How do I keep or delete my cycle log?',
     'a': 'In the cycle tracker\'s settings: Download my log saves it all '
          'as a file, and Delete everything removes every day and setting '
          'at once.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  --w-tint-afternoon: #F6F4EE;
  --w-tint-evening: #F1F0EC;
  --w-radius: 20px;
  --w-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
''',
         r'''  --w-tint-afternoon: #F6F4EE;
  --w-tint-evening: #F1F0EC;
  /* CY-1 - soft rose for period days, a pale sky for the fertile
     estimate. Still no red anywhere. */
  --w-rose: #C9A6A0;
  --w-rose-deep: #A9776F;
  --w-rose-soft: #E9D3CF;
  --w-rose-wash: #EFE3E0;
  --w-sky: #9FB8C9;
  --w-sky-soft: #E3EBF1;
  --w-radius: 20px;
  --w-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
'''),
        (r'''    --w-tint-afternoon: #1C2427;
    --w-tint-evening: #192124;
    color-scheme: dark;
  }
''',
         r'''    --w-tint-afternoon: #1C2427;
    --w-tint-evening: #192124;
    --w-rose: #B98D86;
    --w-rose-deep: #D1A39B;
    --w-rose-soft: #4A3633;
    --w-rose-wash: #3A2E2C;
    --w-sky: #7F9CB0;
    --w-sky-soft: #2C3A44;
    color-scheme: dark;
  }
'''),
        (r'''.w-effort input:checked + span { background: var(--w-sage-deep); color: var(--w-on-accent); }
.w-select { appearance: auto; }
''',
         r'''.w-effort input:checked + span { background: var(--w-sage-deep); color: var(--w-on-accent); }
.w-select { appearance: auto; }

/* CY-1, 30 Oct 2026 - the cycle tracker. */
.w-cy-dot { width: 48px; height: 48px; border-radius: 24px; background: var(--w-rose-wash); color: var(--w-rose-deep); display: flex; align-items: center; justify-content: center; flex: none; }
.w-private { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--w-quiet); }
.w-cy-head { display: flex; align-items: center; gap: 18px; }
.w-cy-ring .track { stroke: var(--w-empty); }
.w-cy-ring .per { stroke: var(--w-rose); }
.w-cy-ring .now { stroke: var(--w-sage-deep); }
.w-cy-ring text { fill: var(--w-ink); }
.w-cy-ring text.sub { fill: var(--w-quiet); }
.w-cy-big { font-family: var(--w-serif); font-size: 22px; line-height: 1.25; }
.w-month { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; text-align: center; }
.w-month .dow { font-size: 12px; color: var(--w-quiet); padding-bottom: 2px; }
.w-month a, .w-month span.day { min-height: 44px; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 14px; color: var(--w-ink); text-decoration: none; position: relative; }
.w-month .out { color: var(--w-ring-off); }
.w-month .period { background: var(--w-rose-soft); }
.w-month .spotting { background: var(--w-rose-wash); }
.w-month .expected { box-shadow: inset 0 0 0 1.5px var(--w-rose); }
.w-month .fertile { background: var(--w-sky-soft); }
.w-month .today { box-shadow: inset 0 0 0 2px var(--w-sage-deep); font-weight: 600; }
.w-month .logged::after { content: ''; position: absolute; bottom: 5px; width: 4px; height: 4px; border-radius: 2px; background: var(--w-rose-deep); }
.w-legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--w-quiet); }
.w-legend span { display: inline-flex; align-items: center; gap: 6px; }
.w-legend i { width: 12px; height: 12px; border-radius: 4px; display: inline-block; }
.w-legend .period { background: var(--w-rose-soft); }
.w-legend .expected { box-shadow: inset 0 0 0 1.5px var(--w-rose); }
.w-legend .fertile { background: var(--w-sky-soft); }
.w-flow { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.w-flow label { display: flex; }
.w-flow input { position: absolute; opacity: 0; pointer-events: none; }
.w-flow span { flex: 1; min-height: 56px; border-radius: 14px; border: 1px solid var(--w-line); background: var(--w-card); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; font-size: 13px; cursor: pointer; }
.w-flow span i { display: flex; gap: 2px; }
.w-flow span i b { width: 8px; height: 8px; border-radius: 4px; background: var(--w-rose); }
.w-flow input:checked + span { background: var(--w-rose-deep); border-color: var(--w-rose-deep); color: var(--w-on-accent); font-weight: 600; }
.w-flow input:checked + span i b { background: var(--w-on-accent); }
.w-flow input:focus-visible + span, .w-sym input:focus-visible + span { outline: 2px solid var(--w-sage-deep); outline-offset: 2px; }
.w-sym input:checked + span { background: var(--w-rose-wash); box-shadow: inset 0 0 0 1.5px var(--w-rose-deep); color: var(--w-ink); }
.w-pain { width: 100%; accent-color: var(--w-rose-deep); min-height: 44px; }
.w-bars { display: flex; align-items: flex-end; gap: 10px; height: 130px; padding-top: 8px; }
.w-bars > div { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; justify-content: flex-end; }
.w-bars .bar { width: 100%; border-radius: 8px 8px 4px 4px; background: var(--w-sage-track); display: flex; flex-direction: column; justify-content: flex-end; overflow: hidden; }
.w-bars .bar i { display: block; background: var(--w-rose); }
.w-around { display: grid; grid-template-columns: 88px repeat(9, minmax(0, 1fr)); gap: 4px; align-items: center; font-size: 11px; color: var(--w-quiet); }
.w-around .cell { height: 22px; border-radius: 6px; background: var(--w-rose-deep); }
.w-around .d1 { color: var(--w-rose-deep); font-weight: 600; }
.w-around .name { font-size: 13px; color: var(--w-ink); }
.w-note-flag { background: var(--w-soft); border-radius: 20px; padding: 16px 18px; display: flex; gap: 12px; align-items: flex-start; font-size: 14px; line-height: 1.5; }
.w-report { background: #FFFFFF; color: #2F3A3F; border-radius: 16px; padding: 20px; font-size: 14px; }
.w-report table { width: 100%; border-collapse: collapse; min-width: 560px; }
.w-report .scroll { overflow-x: auto; }
@media print { .w-report table { min-width: 0; } }
.w-report th, .w-report td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #ECE8E0; vertical-align: top; }
.w-report th { font-size: 12px; color: #5E6A6E; font-weight: 600; }
@media print {
  .w-tabs, .w-top, .w-noprint, .w-tip { display: none !important; }
  body { background: #FFFFFF !important; }
  .w-wrap { padding: 0 !important; max-width: none !important; }
  .w-report { padding: 0; border-radius: 0; }
}
.w-radio { width: 20px; height: 20px; accent-color: var(--w-sage-deep); }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  }

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  }

  // ---- CY-1, 30 Oct 2026 - the cycle log's pain number, and Print.
  var pain = document.querySelector('[data-pain]');
  var painOut = document.querySelector('[data-pain-out]');
  if (pain && painOut) {
    pain.addEventListener('input', function () { painOut.textContent = pain.value; });
  }
  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-print]')) window.print();
  });

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}<!doctype html>
<html lang="en" class="no-js">
<head>
''',
         r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}{% load wellness_cycle %}<!doctype html>
<html lang="en" class="no-js">
<head>
'''),
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl3-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=cy1-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''    Body
  </a>
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl3-1" defer></script>
</body>
</html>
''',
         r'''    Body
  </a>
  {% cycle_on as cy_on %}{% if cy_on %}
  {# CY-1, 30 Oct 2026 - only for a person who turned the tracker on. #}
  <a class="w-tab{% if tab == 'cycle' %} is-on{% endif %}" href="{% url 'wellness:cycle' %}"{% if tab == 'cycle' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-dasharray="36 14"/><circle cx="12" cy="4" r="1.6" fill="currentColor"/></svg>
    Cycle
  </a>
  {% endif %}
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=cy1-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''{% endfor %}{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
''',
         r'''{% endfor %}{% endif %}

{# CY-1 - one discreet line, only for a person who turned the tracker on. #}
{% if cycle %}
<a class="w-card" href="{% if cycle.logged %}{% url 'wellness:cycle' %}{% else %}{% url 'wellness:cycle_log' %}{% endif %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit" data-cycle-card>
  <span class="w-cy-dot" aria-hidden="true"><svg width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-dasharray="36 14"/><circle cx="12" cy="4" r="1.6" fill="currentColor"/></svg></span>
  <span style="display:flex;flex-direction:column;gap:2px;flex:1;min-width:0">
    <span style="font-size:17px;font-weight:600">Cycle</span>
    <span class="w-small w-quiet">{{ cycle.line }}</span>
  </span>
</a>
{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'guide.html'), [
        (r'''</div>

<form method="post" action="{% url 'wellness:tip_seen' %}">
  {% csrf_token %}
''',
         r'''</div>

{# CY-1, 30 Oct 2026 - the optional cycle tracker starts here. #}
<a class="w-list" href="{% url 'wellness:cycle' %}" style="text-decoration:none;color:inherit">
  <span class="w-row" style="border-bottom:none">
    <span class="w-row-main"><span class="w-row-name">Cycle tracker</span><span class="w-row-sub">Optional, off until you turn it on. Private and locked.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </span>
</a>

<form method="post" action="{% url 'wellness:tip_seen' %}">
  {% csrf_token %}
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_two.py',
    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    'test_wellness_three.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_two.py',
    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    'test_wellness_three.py',
    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    'test_wellness_cycle.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    '.bak_wellness3',
]

''',
         r'''    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    '.bak_wellness3',
    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    '.bak_cycle1',
]

'''),
    ]),
    (os.path.join('test_wellness_three.py'), [
        (r'''   '  and reversing it never removes an exercise somebody used')
base = read(J(WT, 'base.html'))
ok("wellness:workouts" in base and base.count('class="w-tab{%') == 5,
   'the bottom bar has Workouts: five tabs', base.count('class="w-tab{%'))
v = read(J(APP, 'views_workouts.py'))
''',
         r'''   '  and reversing it never removes an exercise somebody used')
base = read(J(WT, 'base.html'))
# CY-1 (Release 46) adds a sixth tab, Cycle, shown only to a person who
# turned the tracker on - so at least five.
ok("wellness:workouts" in base and base.count('class="w-tab{%') >= 5,
   'the bottom bar has Workouts: five tabs', base.count('class="w-tab{%'))
v = read(J(APP, 'views_workouts.py'))
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
    raise SystemExit('CY-1 REFUSED: %s' % msg)


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
    if "'test_wellness_cycle.py'" in read(pq):
        print('CY-1 already applied.')
        return 0
    if "'test_wellness_three.py'" not in read(pq):
        refuse('Release 45 is not applied - this round registers after it.')
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
        print('CY-1 --check: %d file(s) would change, none written; %d '
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
    print('CY-1 applied - Wellness: the cycle tracker.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0005).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
