# -*- coding: utf-8 -*-
"""apply_wellness_four.py - round WL-4a, 30 Oct 2026.

RELEASE 47 - WELLNESS W-4a: BADGES AND THE MONDAY SUMMARY.

    - Twenty-two quiet badges, kept for good once earned (never taken
      away; none for the cycle tracker). A new one shows on Today until
      seen; Your badges lists earned and up next.
    - Wellness settings: the Monday summary email, off by default, to the
      person's own address, once a week, never with the journal or the
      cycle log. Sent by the daily job through wellness_weekly.
    - Recent weigh-ins lists 30, so a wrong one can be found and deleted.

New files ship beside this patcher. Stands on Release 46. Idempotent.
Edits backed up to .bak_wellness4.
MIGRATION: wellness 0006 - run  python manage.py migrate.
"""
import os
import sys

SUFFIX = '.bak_wellness4'
MARK = 'WL-4a, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/badges.py',
    'wellness/weekly.py',
    'wellness/migrations/0006_profile_prefs.py',
    'wellness/management/__init__.py',
    'wellness/management/commands/__init__.py',
    'wellness/management/commands/wellness_weekly.py',
    'wellness/templates/wellness/badges.html',
    'wellness/templates/wellness/settings.html',
    'test_wellness_four.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''    # "kettlebells": [], "plate_step": 2.5}.
    equipment = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    # "kettlebells": [], "plate_step": 2.5}.
    equipment = models.JSONField(default=dict, blank=True)
    # WL-4a - small personal settings and kept milestones:
    # {"weekly_email": false, "weekly_sent": "2026-11-02",
    #  "badges": {"first_step": "2026-10-30"}, "badges_seen": [...]}.
    prefs = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
''',
         r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
'''),
        (r'''    from .views_workouts import today_card
    return today_card(user, day)


''',
         r'''    from .views_workouts import today_card
    return today_card(user, day)


def _new_badge(profile, user, day):
    from . import badges as BG
    try:
        fresh = BG.update(profile, BG.facts(user, day), day)
    except Exception:  # noqa: BLE001 - a badge must never break Today
        return None
    if not fresh:
        return None
    k, mark, name, line = BG.BY_KEY[fresh[0]][:4]
    return {'key': k, 'mark': mark, 'name': name, 'line': line,
            'family': BG.FAMILY[k], 'more': len(fresh) - 1}


@wellness_view
def badges_page(request):
    """WL-4a - Your badges: earned (kept for good) and up next."""
    from . import badges as BG
    profile = _profile(request.user)
    day = _today()
    f = BG.facts(request.user, day)
    fresh = BG.update(profile, f, day)
    kept = (profile.prefs or {}).get('badges') or {}
    earned = [{'key': k, 'mark': BG.BY_KEY[k][1], 'name': BG.BY_KEY[k][2],
               'line': BG.BY_KEY[k][3], 'family': BG.FAMILY[k],
               'on': kept[k], 'new': k in fresh}
              for k in BG.KEYS if k in kept]
    newest = [e for e in earned if e['new']]
    if fresh:
        BG.mark_seen(profile)
    return render(request, 'wellness/badges.html', {
        'tab': 'today',
        'earned': earned,
        'newest': newest[:1],
        'total': len(BG.KEYS),
        'next': BG.up_next(f, set(kept)),
    })


@wellness_view
@require_POST
def badges_seen(request):
    from . import badges as BG
    BG.mark_seen(_profile(request.user))
    return redirect(request.POST.get('next') or reverse('wellness:today'))


@wellness_view
def settings_page(request):
    """WL-4a - Wellness settings: the weekly summary (off by default)."""
    profile = _profile(request.user)
    prefs = dict(profile.prefs or {})
    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
        profile.prefs = prefs
        profile.save(update_fields=['prefs', 'updated_at'])
        return redirect('%s?saved=1' % reverse('wellness:settings'))
    return render(request, 'wellness/settings.html', {
        'tab': 'today',
        'weekly': bool(prefs.get('weekly_email')),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
    })


'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'cy1-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl4-1'


'''),
        (r'''        whtr = (latest['waist'].value / profile.height_cm).quantize(
            Decimal('0.01'))
    history = list(BodyMetric.objects.filter(user=request.user,
                                             kind='weight')[:14])
    return render(request, 'wellness/body.html', {
        'tab': 'body', 's': body_summary(request.user, day),
''',
         r'''        whtr = (latest['waist'].value / profile.height_cm).quantize(
            Decimal('0.01'))
    # WL-4a - Demetri, 30 Oct: a wrong weigh-in must be findable to
    # delete; 14 rows was too few. Thirty, about a month of daily ones.
    history = list(BodyMetric.objects.filter(user=request.user,
                                             kind='weight')[:30])
    return render(request, 'wellness/body.html', {
        'tab': 'body', 's': body_summary(request.user, day),
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
''',
         r'''    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    # WL-4a, 30 Oct 2026 - badges and Wellness settings.
    path('badges/', views.badges_page, name='badges'),
    path('badges/seen/', views.badges_seen, name='badges_seen'),
    path('settings/', views.settings_page, name='settings'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'as a file, and Delete everything removes every day and setting '
          'at once.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
''',
         r'''          'as a file, and Delete everything removes every day and setting '
          'at once.'},
    {'q': 'How do badges work?',
     'a': 'A badge marks something you did - a first tick, four good '
          'weeks, ten workouts. Once earned it is yours for good: missing '
          'a day never takes one away. See them all under Your badges.'},
    {'q': 'What is in the Monday email?',
     'a': 'If you turn it on in Settings: last week\'s habits, workouts, '
          'your weight trend and any new badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  --w-sky: #9FB8C9;
  --w-sky-soft: #E3EBF1;
  --w-radius: 20px;
  --w-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
''',
         r'''  --w-sky: #9FB8C9;
  --w-sky-soft: #E3EBF1;
  /* WL-4a - the badge families: habits sage, journal slate, body and
     workouts sand. */
  --w-badge-sage: #E3ECE5;
  --w-badge-sand: #EFE6D6;
  --w-badge-slate: #E6E9EE;
  --w-radius: 20px;
  --w-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
'''),
        (r'''    --w-tint-afternoon: #1C2427;
    --w-tint-evening: #192124;
    --w-rose: #B98D86;
    --w-rose-deep: #D1A39B;
''',
         r'''    --w-tint-afternoon: #1C2427;
    --w-tint-evening: #192124;
    --w-badge-sage: #2F3D38;
    --w-badge-sand: #3A352C;
    --w-badge-slate: #2C343C;
    --w-rose: #B98D86;
    --w-rose-deep: #D1A39B;
'''),
        (r'''}
.w-radio { width: 20px; height: 20px; accent-color: var(--w-sage-deep); }
''',
         r'''}
.w-radio { width: 20px; height: 20px; accent-color: var(--w-sage-deep); }

/* WL-4a, 30 Oct 2026 - badges. */
.w-badges { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.w-badge-cell { background: var(--w-card); border-radius: 18px; padding: 14px 8px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }
.w-badge { width: 48px; height: 48px; border-radius: 24px; display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 15px; flex: none; color: var(--w-ink); background: var(--w-badge-sage); }
.w-badge.big { width: 60px; height: 60px; border-radius: 30px; font-size: 18px; }
.w-badge.sand { background: var(--w-badge-sand); }
.w-badge.slate { background: var(--w-badge-slate); }
.w-badge.todo { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-ring-off); color: var(--w-quiet); width: 40px; height: 40px; font-size: 13px; }
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=cy1-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl4-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=cy1-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl4-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

<section class="w-card sand" aria-label="Today's quote">
''',
         r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

{# WL-4a - a badge just earned, one at a time, until it is seen. #}
{% if new_badge %}
<section class="w-card sand" style="flex-direction:row;align-items:center;gap:14px" data-new-badge>
  <span class="w-badge {{ new_badge.family }}" aria-hidden="true">{{ new_badge.mark }}</span>
  <a href="{% url 'wellness:badges' %}" style="display:flex;flex-direction:column;gap:2px;flex:1;min-width:0;text-decoration:none;color:inherit">
    <span class="w-label">New badge{% if new_badge.more %} · and {{ new_badge.more }} more{% endif %}</span>
    <span style="font-size:17px;font-weight:600">{{ new_badge.name }}</span>
    <span class="w-small w-quiet">{{ new_badge.line }}</span>
  </a>
  <form method="post" action="{% url 'wellness:badges_seen' %}">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn ghost" style="min-width:64px;background:var(--w-card)">Nice</button></form>
</section>
{% endif %}

<section class="w-card sand" aria-label="Today's quote">
'''),
        (r'''</a>
{% endfor %}
{% endblock %}
''',
         r'''</a>
{% endfor %}

<a class="w-btn quiet full" href="{% url 'wellness:badges' %}">Your badges</a>
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'guide.html'), [
        (r'''</div>

{# CY-1, 30 Oct 2026 - the optional cycle tracker starts here. #}
<a class="w-list" href="{% url 'wellness:cycle' %}" style="text-decoration:none;color:inherit">
''',
         r'''</div>

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
'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'check_lease_renewal_and_invoices.py'), [
        (r'''                self.stdout.write(f'\u26a0\ufe0f  lease_signing_tick failed: {e}')
                logger.error(f'lease_signing_tick failed: {e}', exc_info=True)

            # Then get all the data with property details
''',
         r'''                self.stdout.write(f'\u26a0\ufe0f  lease_signing_tick failed: {e}')
                logger.error(f'lease_signing_tick failed: {e}', exc_info=True)

            # WELLNESS WEEKLY - WL-4a, 30 Oct 2026. The Monday summary for
            # the people who turned it on; it does nothing on other days.
            # Guarded like the jobs above, so a failure here never stops
            # the property reports below.
            try:
                call_command('wellness_weekly', dry_run=self.dry_run)
            except Exception as e:
                self.stdout.write(f'\u26a0\ufe0f  wellness_weekly failed: {e}')
                logger.error(f'wellness_weekly failed: {e}', exc_info=True)

            # Then get all the data with property details
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_three.py',
    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    'test_wellness_cycle.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_three.py',
    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    'test_wellness_cycle.py',
    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    'test_wellness_four.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    '.bak_cycle1',
]

''',
         r'''    # CY-1, 30 Oct 2026 - Wellness: the cycle tracker.
    '.bak_cycle1',
    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    '.bak_wellness4',
]

'''),
    ]),
    (os.path.join('test_wellness_cycle.py'), [
        (r'''ok('{% cycle_on as cy_on %}{% if cy_on %}' in base,
   'the bottom bar shows Cycle only when it is on')
ok('?v=cy1-1' in base and base.count('?v=cy1-1') == 2 and
   "SW_VERSION = 'cy1-1'" in read(J(APP, 'views.py')),
   'the asset version moved together (cy1-1): phones fetch the new css')
today = read(J(WT, 'today.html'))
ok('{% if cycle %}' in today and 'data-cycle-card' in today,
''',
         r'''ok('{% cycle_on as cy_on %}{% if cy_on %}' in base,
   'the bottom bar shows Cycle only when it is on')
# Later rounds move the version on (WL-4a: wl4-1); what must hold is that
# the page and the service worker always name the same one.
_v = re.findall(r'\?v=([\w-]+)', base)
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in read(J(APP, 'views.py')),
   'the asset version moved together (cy1-1): phones fetch the new css', _v)
today = read(J(WT, 'today.html'))
ok('{% if cycle %}' in today and 'data-cycle-card' in today,
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
    raise SystemExit('WL-4a REFUSED: %s' % msg)


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
    if "'test_wellness_four.py'" in read(pq):
        print('WL-4a already applied.')
        return 0
    if "'test_wellness_cycle.py'" not in read(pq):
        refuse('Release 46 is not applied - this round registers after it.')
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
        print('WL-4a --check: %d file(s) would change, none written; %d '
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
    print('WL-4a applied - Wellness: badges and the Monday summary.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0006).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
