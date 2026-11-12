# -*- coding: utf-8 -*-
"""apply_wellness_twentyfour.py - round PT-1, 12 Nov 2026.

RELEASE 70 - PERSONAL TODAY INSIDE WELLNESS, AND LOG A PAST WORKOUT.

    Demetri, 14:32-14:38: At home today on Wellness Today - his own
    celebrations, today's meals from his plans, his own documents - and
    See all for the page. Off in Settings if not wanted. No CRS.
    17:33: Log a past workout - the day, when it started, how long.

New files ship beside this patcher. Stands on Release 69. Idempotent.
Edits backed up to .bak_wellness24. MIGRATION 0015_session_minutes.
"""
import os
import sys

SUFFIX = '.bak_wellness24'
MARK = 'PT-1, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/home.py',
    'wellness/migrations/0015_session_minutes.py',
    'wellness/templates/wellness/home.html',
    'wellness/templates/wellness/session_past.html',
    'test_wellness_twentyfour.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
''',
         r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/home.py'; Text = 'def card_lines(g):'; What = 'PT-1: At home today on Wellness Today - without it Today cannot be drawn' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
'''),
        (r'''    'test_wellness_twentythree.py',
    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    'test_meal_share.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentythree.py',
    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    'test_meal_share.py',
    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    'test_wellness_twentyfour.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    '.bak_mealshare',
]

''',
         r'''    # MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they choose.
    '.bak_mealshare',
    # PT-1, 12 Nov 2026 - Personal Today inside Wellness; log a past workout.
    '.bak_wellness24',
]

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-opt { display: flex; align-items: flex-start; gap: 10px; min-height: 44px; }
.w-opt input { width: 20px; height: 20px; margin-top: 2px; accent-color: var(--w-sage-deep); flex: none; }
''',
         r'''.w-opt { display: flex; align-items: flex-start; gap: 10px; min-height: 44px; }
.w-opt input { width: 20px; height: 20px; margin-top: 2px; accent-color: var(--w-sage-deep); flex: none; }

/* PT-1, 12 Nov 2026 - At home today. */
.w-home-card { text-decoration: none; color: inherit; gap: 2px; }
.w-home-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.w-home-all { font-size: 13px; font-weight: 600; color: var(--w-sage-deep); text-decoration: none; }
.w-home-row { display: flex; align-items: center; gap: 12px; min-height: 44px; border-top: 1px solid var(--w-line); text-decoration: none; color: inherit; }
.w-home-head + .w-home-row { border-top: 0; }
.w-home-row.big { min-height: 56px; }
.w-home-ico { width: 32px; height: 32px; border-radius: 16px; flex: none; display: flex; align-items: center; justify-content: center; }
.w-home-ico.cel { background: #F4E6D8; color: #8A4B1C; }
.w-home-ico.meal { background: #EAF0E6; color: #3F6B3A; }
.w-home-ico.doc { background: #E4EEF4; color: #2E5B78; }
.w-home-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.w-home-text b { font-weight: 600; }
.w-home-text span { font-size: 13px; color: var(--w-quiet); }
.w-home-when { font-size: 13px; font-weight: 600; white-space: nowrap; }
.w-home-when.soon { color: #9A5B10; }
@media (prefers-color-scheme: dark) {
  .w-home-ico.cel { background: #4A3626; color: #F1C9A5; }
  .w-home-ico.meal { background: #2F3F2C; color: #BFD9B5; }
  .w-home-ico.doc { background: #263845; color: #B5D2E6; }
  .w-home-when.soon { color: #E9B56A; }
}
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function fmt(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + pad(s % 60); }
    setInterval(function () { clock.textContent = fmt((Date.now() - started) / 1000); }, 1000);
    // Keep the screen awake while training, where the phone allows it.
    var lock = null;
''',
         r'''    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function fmt(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + pad(s % 60); }
    // PT-1 - a workout logged afterwards has its length, not a clock.
    if (clock) setInterval(function () { clock.textContent = fmt((Date.now() - started) / 1000); }, 1000);
    // Keep the screen awake while training, where the phone allows it.
    var lock = null;
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''         'after two weeks of weigh-ins whether you are on track.',
         'More than a kilo a week? Body says so - a later date is kinder.']},
    # WL-19, 12 Nov 2026 - progress photos and the download.
    {'q': 'Set up: progress photos',
''',
         r'''         'after two weeks of weigh-ins whether you are on track.',
         'More than a kilo a week? Body says so - a later date is kinder.']},
    # PT-1, 12 Nov 2026 - Personal Today; a workout logged afterwards.
    {'q': 'What is At home today?',
     'a': 'A small card at the top of Today with the rest of your Alivente: '
          'your next celebration, today\'s meals and any of your documents '
          'about to expire. It only appears when there is something to say. '
          'See all opens the whole page. Turn it off under the cog, At home '
          'today.'},
    {'q': 'Set up: log a workout you already did',
     'a': 'For a run this morning, or a session yesterday you forgot to '
          'log.',
     'steps': [
         'Workouts > Log a past workout.',
         'Pick the day, when it started and how many minutes it took. '
         'Choose a routine if it was one.',
         'Tap Next, tick what you did - a run is one line with its km and '
         'minutes - and Finish.',
         'Add your watch\'s calories afterwards as usual.']},
    # WL-19, 12 Nov 2026 - progress photos and the download.
    {'q': 'Set up: progress photos',
'''),
        (r'''               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work',
               'turn the sounds off', 'time zone')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight', 'progress photos')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
''',
         r'''               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work',
               'turn the sounds off', 'time zone', 'At home today')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight', 'progress photos')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'already did',
                  'workout', 'exercise', 'sports and dance')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'My equipment tells Wellness which weights you own.',
            'The heading shows workouts this week, and their calories if you '
            'added them.',
        ],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
    'routine_form': {
''',
         r'''            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'Did one earlier, or another day? Log a past workout.',
            'My equipment tells Wellness which weights you own.',
            'The heading shows workouts this week, and their calories if you '
            'added them.',
        ],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
    # PT-1, 12 Nov 2026 - a workout logged afterwards; Personal Today.
    'session_past': {
        'title': 'Log a past workout',
        'purpose': 'A workout you already did, on any day this year.',
        'steps': [
            'Pick the day, when it started and how many minutes it took.',
            'Choose a routine, or none and add exercises next.',
            'Tick what you did, then Finish. It keeps the length you typed.',
        ],
        'signs': [],
    },
    'home': {
        'title': 'At home today',
        'purpose': 'Your celebrations, today\'s meals and your documents.',
        'steps': [
            'Coming up: your celebrations in the next two weeks, with the age '
            'or years where the year is known.',
            'Today\'s meals: from your meal plan and any shared with you.',
            'Your documents: yours only, expiring in the next 90 days.',
            'Tap a line to open it in Alivente.',
        ],
        'signs': [('', 'Each part shows only if you can open it in '
                       'Alivente.')],
    },
    'routine_form': {
'''),
        (r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
        ],
        'signs': [],
''',
         r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
            'At home today: turn the card on Today on or off.',
        ],
        'signs': [],
'''),
    ]),
    (os.path.join('wellness', 'models.py'), [
        (r'''    # WL-11, 1 Nov 2026: calories burnt, typed in from the watch. Optional.
    calories = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
''',
         r'''    # WL-11, 1 Nov 2026: calories burnt, typed in from the watch. Optional.
    calories = models.PositiveSmallIntegerField(null=True, blank=True)
    # PT-1, 12 Nov 2026: a workout logged afterwards says how long it took;
    # finishing it then keeps that length rather than the minutes it took
    # to type it in.
    minutes = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl22-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl23-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl22-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl23-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'session_live.html'), [
        (r'''  Every tick is saved as it happens, so leaving the page loses nothing.
{% endcomment %}
<div data-live data-started="{{ started_ms }}" style="display:flex;flex-direction:column;gap:16px">
<header style="display:flex;justify-content:space-between;align-items:center;gap:12px">
  <h1 class="w-title" style="font-size:26px">{{ s.name }}</h1>
  <span class="w-clock" data-elapsed>0:00</span>
</header>

{% for b in blocks %}
''',
         r'''  Every tick is saved as it happens, so leaving the page loses nothing.
{% endcomment %}
<div data-live data-started="{{ started_ms }}"{% if s.minutes %} data-past{% endif %} style="display:flex;flex-direction:column;gap:16px">
<header style="display:flex;justify-content:space-between;align-items:center;gap:12px">
  <h1 class="w-title" style="font-size:26px">{{ s.name }}</h1>
  {% if s.minutes %}<span class="w-clock">{{ s.minutes }} min</span>{% else %}<span class="w-clock" data-elapsed>0:00</span>{% endif %}
</header>
{% if s.minutes %}<p class="w-small w-quiet" style="margin:-8px 0 0" data-past-note>Logging a workout from {{ s.started_at|date:"l j F, H:i" }}. Tick what you did, then Finish.</p>{% endif %}

{% for b in blocks %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  <h2 class="w-h2">Sounds and vibration</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="sounds" value="1"{% if sounds %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-fx-switch> <span>A soft sound and a short vibration when you tick a habit, earn a badge or finish your day<br><span class="w-small w-quiet">Quiet, and at media volume. Vibration works on Android phones. If your phone is set to reduce motion, the animations become a simple fade.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
''',
         r'''  <h2 class="w-h2">Sounds and vibration</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="sounds" value="1"{% if sounds %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-fx-switch> <span>A soft sound and a short vibration when you tick a habit, earn a badge or finish your day<br><span class="w-small w-quiet">Quiet, and at media volume. Vibration works on Android phones. If your phone is set to reduce motion, the animations become a simple fade.</span></span></label>
  {# PT-1, 12 Nov 2026 - the rest of Alivente, on Today. #}
  <h2 class="w-h2">At home today</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="home" value="1"{% if home_on %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-home-switch> <span>Show my celebrations, today's meals and my documents on Today<br><span class="w-small w-quiet">A small card at the top, only when there is something to say - and See all for the whole page.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

{% comment %}
''',
         r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

{% comment %} PT-1, 12 Nov 2026 - At home today: the rest of Alivente in three lines at most, only when there is something to say. See all opens Personal Today inside Wellness. {% endcomment %}
{% if home_lines %}
<a class="w-card w-home-card" href="{% url 'wellness:home' %}" data-home-card>
  <span class="w-home-head"><span class="w-h2" style="font-size:16px">At home today</span><span class="w-home-all">See all ›</span></span>
  {% for l in home_lines %}
  <span class="w-home-row"><span class="w-home-ico {{ l.kind }}">{% if l.kind == 'cel' %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="9" width="16" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 9v11M4 13h16M12 9c-2-4-6-4-6-1.5S12 9 12 9zm0 0c2-4 6-4 6-1.5S12 9 12 9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>{% elif l.kind == 'meal' %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3v8a2 2 0 0 0 2 2v8M10 3v8M8 3v6M16 21V3c2.5 1.5 3 5 3 8h-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>{% else %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8.5 17h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>{% endif %}</span><span class="w-home-text">{{ l.text }}</span><span class="w-home-when{% if l.soon %} soon{% endif %}">{{ l.when }}</span></span>
  {% endfor %}
</a>
{% endif %}

{% comment %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'workouts.html'), [
        (r'''{% if not open_session %}
<form method="post" action="{% url 'wellness:session_start' %}">{% csrf_token %}<button class="w-btn ghost full" type="submit">Start an empty workout</button></form>
{% endif %}

''',
         r'''{% if not open_session %}
<form method="post" action="{% url 'wellness:session_start' %}">{% csrf_token %}<button class="w-btn ghost full" type="submit">Start an empty workout</button></form>
{# PT-1, 12 Nov 2026 - a workout already done, on any day this year. #}
<a class="w-btn quiet full" href="{% url 'wellness:session_past' %}" data-past-link>Log a past workout</a>
{% endif %}

'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''         name='photo_delete'),
    path('settings/export/', PH.export_page, name='export'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
''',
         r'''         name='photo_delete'),
    path('settings/export/', PH.export_page, name='export'),
    # PT-1, 12 Nov 2026 - Personal Today, inside Wellness.
    path('home/', views.home_page, name='home'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
'''),
        (r'''         name='routine_delete'),
    path('workouts/start/', W.session_start, name='session_start'),
    path('workouts/<int:pk>/live/', W.session_live, name='session_live'),
    path('workouts/<int:pk>/', W.session_detail, name='session_detail'),
''',
         r'''         name='routine_delete'),
    path('workouts/start/', W.session_start, name='session_start'),
    # PT-1, 12 Nov 2026 - log a workout you already did.
    path('workouts/past/', W.session_past, name='session_past'),
    path('workouts/<int:pk>/live/', W.session_live, name='session_live'),
    path('workouts/<int:pk>/', W.session_detail, name='session_detail'),
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
''',
         r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # PT-1, 12 Nov 2026 - "At home today", unless turned off.
        'home_lines': _home_lines(request.user, day, profile),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
'''),
        (r'''    return sum(CalmSession.objects.filter(user=user, date=day)
               .values_list('seconds', flat=True)) // 60


''',
         r'''    return sum(CalmSession.objects.filter(user=user, date=day)
               .values_list('seconds', flat=True)) // 60


def _home_lines(user, day, profile):
    """PT-1 - at most three lines from the rest of Alivente. Never lets
    a fault there stop Today."""
    if (profile.prefs or {}).get('home_off'):
        return []
    from . import home as HM
    try:
        return HM.card_lines(HM.gather(user, day))
    except Exception:  # noqa: BLE001 - Today must always open
        return []


@wellness_view
def home_page(request):
    """PT-1, 12 Nov 2026 - Personal Today: celebrations, meals and your
    documents, inside Wellness."""
    from . import home as HM
    day = _today()
    g = HM.gather(request.user, day)
    return render(request, 'wellness/home.html', {
        'tab': 'today', 'date': day, 'g': g,
        'nothing': not ((g['cel'] and (g['cel']['rows'] or
                                       g['cel']['next'])) or g['meals']
                        or g['docs']),
        'cel_days': HM.CEL_DAYS, 'doc_days': HM.DOC_DAYS,
    })


'''),
        (r'''        # WL-15 - sounds and vibration are on unless turned off here.
        prefs['sounds_off'] = not request.POST.get('sounds')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
''',
         r'''        # WL-15 - sounds and vibration are on unless turned off here.
        prefs['sounds_off'] = not request.POST.get('sounds')
        # PT-1 - "At home today" on Today, on unless turned off here.
        prefs['home_off'] = not request.POST.get('home')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
'''),
        (r'''        'claude_line': not prefs.get('line_off'),
        'sounds': not prefs.get('sounds_off'),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
''',
         r'''        'claude_line': not prefs.get('line_off'),
        'sounds': not prefs.get('sounds_off'),
        'home_on': not prefs.get('home_off'),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl22-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl23-1'


'''),
    ]),
    (os.path.join('wellness', 'views_workouts.py'), [
        (r'''    if open_s:
        return redirect('wellness:session_live', pk=open_s.pk)
    profile = _profile(request.user)
    routine = None
    if request.POST.get('routine'):
        routine = get_object_or_404(Routine, pk=request.POST['routine'],
                                    user=request.user)
    now = timezone.now()
    s = WorkoutSession.objects.create(
        user=request.user, routine=routine,
        name=routine.name if routine else 'Workout',
        date=timezone.localdate(), started_at=now)
    if routine:
        for pos, item in enumerate(routine.items.select_related('exercise')):
            last = _last_sets(request.user, item.exercise, s)
            sug = TR.suggest(item.rep_min, item.rep_max,
                             [(x.weight, x.reps) for x in last],
''',
         r'''    if open_s:
        return redirect('wellness:session_live', pk=open_s.pk)
    routine = None
    if request.POST.get('routine'):
        routine = get_object_or_404(Routine, pk=request.POST['routine'],
                                    user=request.user)
    s = _new_session(request.user, routine, timezone.localdate(),
                     timezone.now())
    return redirect('wellness:session_live', pk=s.pk)


def _new_session(user, routine, day, start):
    """PT-1 - a session, with the routine's sets laid out and last time's
    numbers suggested. Starting now and logging afterwards share it."""
    profile = _profile(user)
    s = WorkoutSession.objects.create(
        user=user, routine=routine,
        name=routine.name if routine else 'Workout',
        date=day, started_at=start)
    if routine:
        for pos, item in enumerate(routine.items.select_related('exercise')):
            last = _last_sets(user, item.exercise, s)
            sug = TR.suggest(item.rep_min, item.rep_max,
                             [(x.weight, x.reps) for x in last],
'''),
        (r'''                    seconds=secs if item.exercise.kind == 'time'
                    else None)
    return redirect('wellness:session_live', pk=s.pk)


''',
         r'''                    seconds=secs if item.exercise.kind == 'time'
                    else None)
    return s


'''),
        (r'''
@wellness_view
@require_POST
def session_finish(request, pk):
''',
         r'''
@wellness_view
def session_past(request):
    """PT-1, 12 Nov 2026 - log a workout you already did: the day, the
    time it started and how long it took; then tick the sets as usual."""
    open_s = WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=True).first()
    if open_s:
        return redirect('wellness:session_live', pk=open_s.pk)
    day = timezone.localdate()
    routines = list(Routine.objects.filter(user=request.user))
    error = ''
    if request.method == 'POST':
        try:
            d = dt.date.fromisoformat(request.POST.get('date') or '')
            hh, mm = (int(x) for x in
                      (request.POST.get('time') or '').split(':')[:2])
            mins = int(request.POST.get('minutes') or 0)
        except ValueError:
            d, hh, mm, mins = None, 0, 0, 0
        if d is None or d > day or d < day - dt.timedelta(days=365):
            error = 'Pick a day in the last year, up to today.'
        elif not 1 <= mins <= 600:
            error = 'How long did it take? Type the minutes, 1 to 600.'
        else:
            start = timezone.make_aware(dt.datetime(
                d.year, d.month, d.day, max(0, min(hh, 23)),
                max(0, min(mm, 59))))
            if start > timezone.now():
                error = 'That time has not come yet today.'
            else:
                routine = None
                if request.POST.get('routine'):
                    routine = get_object_or_404(
                        Routine, pk=request.POST['routine'],
                        user=request.user)
                s = _new_session(request.user, routine, d, start)
                s.minutes = mins
                s.save(update_fields=['minutes'])
                return redirect('wellness:session_live', pk=s.pk)
    return render(request, 'wellness/session_past.html', {
        'tab': 'workouts', 'routines': routines, 'error': error,
        'date': request.POST.get('date') or day.isoformat(),
        'max': day.isoformat(),
        'time': request.POST.get('time') or '07:00',
        'minutes': request.POST.get('minutes') or '',
        'routine_pk': request.POST.get('routine') or '',
    })


@wellness_view
@require_POST
def session_finish(request, pk):
'''),
        (r'''        return redirect('wellness:workouts')
    s.sets.filter(done=False).delete()
    s.finished_at = timezone.now()
    try:
        s.effort = _num(request.POST.get('effort'), int, 1, 10)
''',
         r'''        return redirect('wellness:workouts')
    s.sets.filter(done=False).delete()
    # PT-1 - logged afterwards: it ends when it really ended.
    s.finished_at = (s.started_at + dt.timedelta(minutes=s.minutes)
                     if s.minutes else timezone.now())
    try:
        s.effort = _num(request.POST.get('effort'), int, 1, 10)
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
    raise SystemExit('PT-1 REFUSED: %s' % msg)


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
    if "'test_wellness_twentyfour.py'" in read(pq):
        print('PT-1 already applied.')
        return 0
    if "'test_meal_share.py'" not in read(pq):
        refuse('Release 69 is not applied - this round registers after it.')
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
        print('PT-1 --check: %d file(s) would change, none written; %d '
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
    print('PT-1 applied - Personal Today inside Wellness; log a past workout.')
    print('      MIGRATION 0015_session_minutes - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
