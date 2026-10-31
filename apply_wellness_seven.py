# -*- coding: utf-8 -*-
"""apply_wellness_seven.py - round WL-5, 31 Oct 2026.

RELEASE 50 - WELLNESS: THE COG.

    - A cog beside the ?, top right on every Wellness page, opens
      Settings; Settings lists Your badges and the Cycle tracker. The ?
      guide is help only (Demetri, 31 Oct 06:18).
    - The reminder job says plainly when ANTHROPIC_API_KEY or the push
      keys are missing on its service, and a recent login counts as
      using Wellness for the daily line.

The suite ships beside this patcher. Stands on Release 49. Idempotent.
Edits backed up to .bak_wellness7. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness7'
MARK = 'WL-5, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_wellness_seven.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl6-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl7-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''    </a>
    {% endblock %}
    <a class="w-icon-btn" href="{% url 'wellness:guide' %}" aria-label="Guide and help">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.6 8.6a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.5v.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="11" cy="15.4" r="1" fill="currentColor"/></svg>
    </a>
  </div>
  {% block content %}{% endblock %}
''',
         r'''    </a>
    {% endblock %}
    {% comment %} WL-5, 31 Oct 2026 - Demetri: settings get their own cog beside the ?;
       the ? is help only. Both stay top right on every page. {% endcomment %}
    <span class="w-top-icons">
    <a class="w-icon-btn" href="{% url 'wellness:settings' %}" aria-label="Settings">
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M19.4 13.5a7.6 7.6 0 0 0 0-3l2-1.6-2-3.4-2.4 1a7.5 7.5 0 0 0-2.6-1.5L14 2.5h-4l-.4 2.5A7.5 7.5 0 0 0 7 6.5l-2.4-1-2 3.4 2 1.6a7.6 7.6 0 0 0 0 3l-2 1.6 2 3.4 2.4-1a7.5 7.5 0 0 0 2.6 1.5l.4 2.5h4l.4-2.5a7.5 7.5 0 0 0 2.6-1.5l2.4 1 2-3.4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
    </a>
    <a class="w-icon-btn" href="{% url 'wellness:guide' %}" aria-label="Guide and help">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.6 8.6a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.5v.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="11" cy="15.4" r="1" fill="currentColor"/></svg>
    </a>
    </span>
  </div>
  {% block content %}{% endblock %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl6-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl7-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'guide.html'), [
        (r'''</div>

{# WL-4a - badges and settings. #}
<a class="w-list" href="{% url 'wellness:badges' %}" style="text-decoration:none;color:inherit">
  <span class="w-row" style="border-bottom:none">
    <span class="w-row-main"><span class="w-row-name">Your badges</span><span class="w-row-sub">Quiet milestones, kept for good.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </span>
</a>
<a class="w-list" href="{% url 'wellness:settings' %}" style="text-decoration:none;color:inherit">
  <span class="w-row" style="border-bottom:none">
    <span class="w-row-main"><span class="w-row-name">Settings</span><span class="w-row-sub">The Monday summary email - off unless you turn it on.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </span>
</a>

{# CY-1, 30 Oct 2026 - the optional cycle tracker starts here. #}
<a class="w-list" href="{% url 'wellness:cycle' %}" style="text-decoration:none;color:inherit">
  <span class="w-row" style="border-bottom:none">
    <span class="w-row-main"><span class="w-row-name">Cycle tracker</span><span class="w-row-sub">Optional, off until you turn it on. Private and locked.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </span>
</a>

<form method="post" action="{% url 'wellness:tip_seen' %}">
  {% csrf_token %}
''',
         r'''</div>

<form method="post" action="{% url 'wellness:tip_seen' %}">
  {% csrf_token %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''{% comment %} WL-4a, 30 Oct 2026 - Wellness settings. The weekly summary is off by default and never carries the journal or the cycle tracker. {% endcomment %}
{% block title %}Settings · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:guide' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Guide</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
<h1 class="w-title">Settings</h1>
{% if saved %}<div class="w-card soft" role="status" style="padding:12px 16px">Saved.</div>{% endif %}
{% if tested %}<div class="w-card soft" role="status" style="padding:12px 16px">{% if tested == '0' %}The test could not reach a phone. Turn reminders on again on the phone, then try once more.{% else %}Test sent - it should arrive in a few seconds.{% endif %}</div>{% endif %}

''',
         r'''{% comment %} WL-4a, 30 Oct 2026 - Wellness settings. The weekly summary is off by default and never carries the journal or the cycle tracker. {% endcomment %}
{% block title %}Settings · Wellness{% endblock %}
{% block top_left %}<a class="w-home" href="{% url 'wellness:today' %}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg> Today</a>{% endblock %}
{% block tabs %}{% endblock %}
{% block content %}
<h1 class="w-title">Settings</h1>
{% if saved %}<div class="w-card soft" role="status" style="padding:12px 16px">Saved.</div>{% endif %}
{% comment %} WL-5, 31 Oct 2026 - Demetri: badges and the cycle tracker live here,
   behind the cog, not in the ? guide. {% endcomment %}
<div class="w-list">
  <a class="w-row" href="{% url 'wellness:badges' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Your badges</span><span class="w-row-sub">Quiet milestones, kept for good.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
  <a class="w-row" href="{% url 'wellness:cycle' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Cycle tracker</span><span class="w-row-sub">Optional, off until you turn it on. Private and locked.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
</div>

{% if tested %}<div class="w-card soft" role="status" style="padding:12px 16px">{% if tested == '0' %}The test could not reach a phone. Turn reminders on again on the phone, then try once more.{% else %}Test sent - it should arrive in a few seconds.{% endif %}</div>{% endif %}

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''   ? slid over; pinned to the right it stays where help is expected. */
.w-top > .w-icon-btn:last-child { margin-left: auto; }
.w-icon-btn {
  width: 44px; height: 44px;
''',
         r'''   ? slid over; pinned to the right it stays where help is expected. */
.w-top > .w-icon-btn:last-child { margin-left: auto; }
/* WL-5 - the cog and the ? together, top right. */
.w-top-icons { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; }
.w-icon-btn {
  width: 44px; height: 44px;
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl6-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl7-1'


'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'finance stay as protected as they were.'},
    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Open the Cycle tracker '
          'link at the bottom of this guide. It then gets its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
''',
         r'''          'finance stay as protected as they were.'},
    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Tap the cog at the top '
          'right, then Cycle tracker. It then gets its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
'''),
        (r'''          'It sees only your first name, today\'s habit names and how the '
          'week has gone - never your journal, weight or cycle log. Turn '
          'it off in Settings.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
''',
         r'''          'It sees only your first name, today\'s habit names and how the '
          'week has gone - never your journal, weight or cycle log. Turn '
          'it off in Settings (the cog at the top right).'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
'''),
    ]),
    (os.path.join('wellness', 'daily_line.py'), [
        (r'''    for p in WellnessProfile.objects.select_related('user').filter(
            onboarded=True, user__is_active=True):
        if (p.prefs or {}).get('seen', '') >= since and \
                p.user.has_perm('auth.can_access_wellness'):
            out.append(p)
    return out


def run(now, client=None, write=print):
    """One pass: make the lines that are missing for today."""
    made = 0
    for p in due_people(now):
        if make(p, now.date(), client=client):
            made += 1
    return made
''',
         r'''    for p in WellnessProfile.objects.select_related('user').filter(
            onboarded=True, user__is_active=True):
        seen_on = (p.prefs or {}).get('seen', '')
        # WL-5, 31 Oct - a recent login counts too, so the first night
        # after a release does not wait for Today to be opened once.
        login = p.user.last_login
        recent_login = bool(login and login.date().isoformat() >= since)
        if (seen_on >= since or recent_login) and \
                p.user.has_perm('auth.can_access_wellness'):
            out.append(p)
    return out


def key_present():
    from django.conf import settings
    return bool(getattr(settings, 'ANTHROPIC_API_KEY', None))


def run(now, client=None, write=print):
    """One pass: make the lines that are missing for today. Says plainly
    when the key is missing rather than spending the day's tries."""
    if client is None and not key_present():
        write('Wellness daily line: ANTHROPIC_API_KEY is not set on this '
              'service - no lines made.')
        return 0
    made = waiting = 0
    for p in due_people(now):
        if (p.prefs or {}).get('daily_line', {}).get('date') == \
                now.date().isoformat() or (p.prefs or {}).get('line_off'):
            continue
        waiting += 1
        if make(p, now.date(), client=client):
            made += 1
    if waiting:
        write('Wellness daily line: %d made, %d waiting for one.'
              % (made, waiting))
    return made
'''),
    ]),
    (os.path.join('wellness', 'management', 'commands', 'wellness_reminders.py'), [
        (r'''            try:
                from wellness import daily_line as DL
                made = DL.run(timezone.localtime())
                if made:
                    self.stdout.write('Wellness daily line: %d made.' % made)
            except Exception as exc:                      # noqa: BLE001
                self.stdout.write('Wellness daily line failed: %s' % exc)
        if not P.configured() and not opts['dry_run']:
            self.stdout.write('Wellness reminders: the push keys are not '
                              'set - nothing sent.')
            return
        sent, people = R.run(timezone.localtime(), dry_run=opts['dry_run'],
''',
         r'''            try:
                from wellness import daily_line as DL
                DL.run(timezone.localtime(), write=self.stdout.write)
            except Exception as exc:                      # noqa: BLE001
                self.stdout.write('Wellness daily line failed: %s' % exc)
        if not P.configured() and not opts['dry_run']:
            self.stdout.write('Wellness reminders: WELLNESS_VAPID_PUBLIC and '
                              'WELLNESS_VAPID_PRIVATE are not set on this '
                              'service - nothing sent.')
            return
        sent, people = R.run(timezone.localtime(), dry_run=opts['dry_run'],
'''),
    ]),
    (os.path.join('test_wellness_four.py'), [
        (r'''         and m != '0']
ok(not small, 'every control is still at least 44px', small)
ok("url 'wellness:settings'" in read(J(WT, 'guide.html')) and
   "url 'wellness:badges'" in read(J(WT, 'guide.html')),
   'the guide leads to badges and settings')
for p in EDITED:
''',
         r'''         and m != '0']
ok(not small, 'every control is still at least 44px', small)
# WL-5 (Release 50) moved both behind the cog: settings is in the top bar
# on every page, and badges is listed in settings.
ok("url 'wellness:settings'" in read(J(WT, 'base.html')) and
   "url 'wellness:badges'" in read(J(WT, 'settings.html')),
   'the guide leads to badges and settings')
for p in EDITED:
'''),
    ]),
    (os.path.join('test_wellness_cycle.py'), [
        (r'''   'What is the fertile estimate?' in guide,
   'the guide answers who can see it and what the estimate is')
ok("url 'wellness:cycle'" in read(J(WT, 'guide.html')),
   '  and the guide is where it is turned on')
for p in EDITED:
''',
         r'''   'What is the fertile estimate?' in guide,
   'the guide answers who can see it and what the estimate is')
# WL-5 (Release 50) moved it behind the cog, into settings.
ok("url 'wellness:cycle'" in read(J(WT, 'settings.html')),
   '  and the guide is where it is turned on')
for p in EDITED:
'''),
    ]),
    (os.path.join('test_wellness_six.py'), [
        (r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
ok(_v == ['wl6-1', 'wl6-1'] and "SW_VERSION = 'wl6-1'" in views,
   'the asset version moved together (wl6-1)', _v)
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
''',
         r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
# Later rounds move the version on (WL-5: wl7-1); what must hold is that
# the page and the service worker always name the same one.
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in views, 'the asset version moved together (wl6-1)', _v)
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
'''),
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def parse('" in gate, '  with a sentinel on the answer check')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-5 (Release 50) moved the sentinel to 'def key_present(': once
# daily_line.py had a backup, 'def parse(' was in it too and could no
# longer fail (test_sentinels, section 4).
ok("File = 'wellness/daily_line.py'" in gate,
   '  with a sentinel on the line rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def parse('; What = 'WL-4c: the line rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_five.py',
    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    'test_wellness_six.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_five.py',
    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    'test_wellness_six.py',
    # WL-5, 31 Oct 2026 - Wellness: the cog.
    'test_wellness_seven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    '.bak_wellness6',
]

''',
         r'''    # WL-4c, 30 Oct 2026 - Wellness: a line from Claude under the quote.
    '.bak_wellness6',
    # WL-5, 31 Oct 2026 - Wellness: the cog.
    '.bak_wellness7',
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
    raise SystemExit('WL-5 REFUSED: %s' % msg)


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
    if "'test_wellness_seven.py'" in read(pq):
        print('WL-5 already applied.')
        return 0
    if "'test_wellness_six.py'" not in read(pq):
        refuse('Release 49 is not applied - this round registers after it.')
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
        print('WL-5 --check: %d file(s) would change, none written; %d '
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
    print('WL-5 applied - Wellness: the cog.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
