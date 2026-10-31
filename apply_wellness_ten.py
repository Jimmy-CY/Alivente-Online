# -*- coding: utf-8 -*-
"""apply_wellness_ten.py - round WL-8, 31 Oct 2026.

RELEASE 53 - WELLNESS: CHALLENGES.

    - A habit with a finish line: 7, 14, 21 or 30 days, every day.
      "Day 12 of 30" on Today; a square for each day on the habit.
    - A missed day is asked about once: Carry on (the finish moves out a
      day) or Start again today (Demetri, 31 Oct 14:26); after three in a
      row, Pause it too. No word of blame.
    - The finish: keep it as a habit, go again, or let it go; a
      "Challenge finished" badge. Challenges to try on the new-habit screen.

New files ship beside this patcher. Stands on Release 52. Idempotent.
Edits backed up to .bak_wellness10. MIGRATION: wellness 0009_challenges.
"""
import os
import sys

SUFFIX = '.bak_wellness10'
MARK = 'WL-8, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/challenge.py',
    'wellness/migrations/0009_challenges.py',
    'test_wellness_ten.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl9-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl10-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl9-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl10-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

{# WL-4a - a badge just earned, one at a time, until it is seen. #}
''',
         r'''  <h1 class="w-hello">{{ hello }}, {{ name }}</h1>
</header>

{% comment %}
  WL-8, 31 Oct 2026 - a challenge finished: keep it, go again, or let it
  go. A missed day: carry on (the finish moves out a day) or start again -
  Demetri's choice of 31 Oct 14:26. No word of blame.
{% endcomment %}
{% for f in finishes %}
<section class="w-card sand" data-challenge-finish>
  <span class="w-label">Challenge finished</span>
  <h2 class="w-h2" style="font-size:20px">You finished {{ f.c.days }} days of {{ f.habit.name }}</h2>
  <p class="w-small w-quiet" style="margin:0">Every one of them done. What next?</p>
  <div class="w-btn-row">
    {% for act, label in challenge_finish_actions %}
    <form method="post" action="{% url 'wellness:habit_action' f.habit.pk act %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn{% if not forloop.first %} ghost{% endif %}" style="flex:1;background-color:{% if forloop.first %}var(--w-sage-deep){% else %}var(--w-card){% endif %}">{{ label }}</button></form>
    {% endfor %}
  </div>
</section>
{% endfor %}
{% for a in asks %}
<section class="w-card soft" data-challenge-ask>
  <span class="w-label">{{ a.habit.name }} · {{ a.c.words }}</span>
  <p style="margin:0">{{ a.c.ask_words }}</p>
  <div class="w-btn-row">
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_carry' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn" style="flex:1">Carry on</button></form>
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_restart' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn ghost" style="flex:1;background:var(--w-card)">Start again today</button></form>
  </div>
  <span class="w-small w-quiet">Carry on and it finishes on {{ a.c.finish_words }}.{% if a.c.can_pause %} Or <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_pause' %}" style="display:inline">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-linkbtn">pause it for now</button></form>.{% endif %}</span>
</section>
{% endfor %}

{# WL-4a - a badge just earned, one at a time, until it is seen. #}
'''),
        (r'''        <span class="w-check"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        <span class="w-habit-name">{{ c.habit.name }}</span>
        {% if c.flexible %}
        <span class="w-habit-meta" data-week>{{ c.week_got }} of {{ c.week_target }} this week</span>
        {% elif c.amount %}
''',
         r'''        <span class="w-check"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        <span class="w-habit-name">{{ c.habit.name }}</span>
        {% if c.challenge and not c.challenge.finished %}
        <span class="w-habit-meta" data-challenge-day>{{ c.challenge.words }}</span>
        {% elif c.flexible %}
        <span class="w-habit-meta" data-week>{{ c.week_got }} of {{ c.week_target }} this week</span>
        {% elif c.amount %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''      <button type="button" class="w-chip" data-preset='{"name":"Read","kind":"count","target":10,"unit":"pages","schedule":"daily","time_of_day":"evening"}'>Read</button>
      <button type="button" class="w-chip" data-preset='{"name":"Drink water","kind":"count","target":8,"unit":"glasses","schedule":"daily","time_of_day":"anytime"}'>Drink water</button>
      <button type="button" class="w-chip" data-preset='{"name":"Meditate","kind":"duration","target":10,"schedule":"daily","time_of_day":"morning"}'>Meditate</button>
      <button type="button" class="w-chip" data-preset='{"name":"No sugar","kind":"avoid","schedule":"daily","time_of_day":"anytime"}'>No sugar</button>
    </div>
    {% endif %}
''',
         r'''      <button type="button" class="w-chip" data-preset='{"name":"Read","kind":"count","target":10,"unit":"pages","schedule":"daily","time_of_day":"evening"}'>Read</button>
      <button type="button" class="w-chip" data-preset='{"name":"Drink water","kind":"count","target":8,"unit":"glasses","schedule":"daily","time_of_day":"anytime"}'>Drink water</button>
      <button type="button" class="w-chip" data-preset='{"name":"Meditate","kind":"duration","target":10,"schedule":"daily","time_of_day":"morning","auto_from":"calm"}'>Meditate</button>
      <button type="button" class="w-chip" data-preset='{"name":"No sugar","kind":"avoid","schedule":"daily","time_of_day":"anytime"}'>No sugar</button>
    </div>
    {% comment %} WL-8 - or a challenge to try: each sets the habit and its days. {% endcomment %}
    <span class="w-label">Or try a challenge</span>
    <div class="w-chips" aria-label="Challenges to try">
      {% for label, preset in challenge_starters %}<button type="button" class="w-chip" data-preset="{{ preset }}">{{ label }}</button>{% endfor %}
    </div>
    {% endif %}
'''),
        (r'''      </div>
      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {# WL-3, WL-7 - a habit can tick itself: a finished workout, or Calm minutes. #}
''',
         r'''      </div>
      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {% comment %} WL-8, 31 Oct 2026 - a challenge: every day, with a finish line. {% endcomment %}
    <div style="display:flex;flex-direction:column;gap:8px" data-challenge-pick>
      <span class="w-label">Make it a challenge</span>
      <div class="w-chips">
        <label class="w-chip"><input type="radio" name="challenge" value=""{% if not v.challenge %} checked{% endif %}><span>No</span></label>
        {% for n in challenge_days %}<label class="w-chip"><input type="radio" name="challenge" value="{{ n }}"{% if v.challenge == n %} checked{% endif %}><span>{{ n }} days</span></label>{% endfor %}
      </div>
      <span class="w-small w-quiet">A challenge is every day, with a finish line. Miss a day and you choose: carry on, or start again.</span>
      {% if habit.challenge_from and v.challenge %}<span class="w-small w-quiet">Changing the number of days starts it again from today.</span>{% endif %}
    </div>
    {# WL-3, WL-7 - a habit can tick itself: a finished workout, or Calm minutes. #}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_detail.html'), [
        (r'''{% elif habit.paused %}
<section class="w-card soft"><p style="margin:0">Paused. It stays off Today and nothing counts against it until you resume.</p></section>
{% endif %}

''',
         r'''{% elif habit.paused %}
<section class="w-card soft"><p style="margin:0">Paused. It stays off Today and nothing counts against it until you resume.</p></section>
{% endif %}

{% if challenge %}
{% comment %} WL-8, 31 Oct 2026 - the challenge: a square for each day to do. {% endcomment %}
<section class="w-card" aria-labelledby="ch-h" data-challenge-card>
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <h2 class="w-h2" id="ch-h">{% if challenge.finished %}Challenge finished{% else %}{{ challenge.words }}{% endif %}</h2>
    <span class="w-small w-quiet">{{ challenge.days }}-day challenge</span>
  </div>
  {% for row in challenge.rows %}
  <div class="w-strip" style="grid-template-columns:repeat({{ row|length }},minmax(0,1fr));max-width:{% widthratio row|length 15 100 %}%" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done">{% for s in row %}<i class="{{ s }}"></i>{% endfor %}</div>
  {% endfor %}
  <p class="w-small w-quiet" style="margin:0">{% if challenge.finished %}All {{ challenge.days }} days done, finished on {{ challenge.finished|date:"l j F" }}.{% else %}{{ challenge.got }} done · finishes on {{ challenge.finish_words }} if every day from now is done{% if challenge.misses %} · {{ challenge.misses }} day{{ challenge.misses|pluralize }} added{% endif %}.{% endif %}</p>
  {% if challenge.ask and not habit.archived_at %}
  <p style="margin:0">{{ challenge.ask_words }}</p>
  <div class="w-btn-row">
    <form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_carry' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<button type="submit" class="w-btn" style="flex:1">Carry on</button></form>
    <form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_restart' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<button type="submit" class="w-btn ghost" style="flex:1">Start again today</button></form>
  </div>
  {% if challenge.can_pause %}<form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_pause' %}">{% csrf_token %}<button type="submit" class="w-btn quiet">Pause it for now</button></form>{% endif %}
  {% elif challenge.finished and not habit.archived_at %}
  <div class="w-btn-row">
    {% for act, label in challenge_finish_actions %}
    <form method="post" action="{% url 'wellness:habit_action' habit.pk act %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<button type="submit" class="w-btn{% if not forloop.first %} ghost{% endif %}" style="flex:1">{{ label }}</button></form>
    {% endfor %}
  </div>
  {% endif %}
</section>
{% endif %}

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  .w-breath-orb { background: radial-gradient(circle at 40% 35%, #8FB39A, #5E8A6E); }
}
''',
         r'''  .w-breath-orb { background: radial-gradient(circle at 40% 35%, #8FB39A, #5E8A6E); }
}

/* ---- WL-8, 31 Oct 2026 - challenges: a square for each day to do. */
.w-strip { display: grid; grid-template-columns: repeat(15, minmax(0, 1fr)); gap: 4px; }
.w-strip i { aspect-ratio: 1; border-radius: 4px; background: var(--w-empty); }
.w-strip i.done { background: var(--w-sage-deep); }
.w-strip i.today { box-shadow: inset 0 0 0 2px var(--w-sage); background: transparent; }
.w-linkbtn { background: none; border: none; padding: 0; font: inherit; color: var(--w-sage-deep); text-decoration: underline; cursor: pointer; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    if (p.per_week) set('per_week', p.per_week);
    if (p.time_of_day) set('time_of_day', p.time_of_day);
    form.dispatchEvent(new Event('change', {bubbles: true}));
  });

''',
         r'''    if (p.per_week) set('per_week', p.per_week);
    if (p.time_of_day) set('time_of_day', p.time_of_day);
    // WL-7, WL-8 - an example can tick itself, or be a challenge.
    set('auto_from', p.auto_from || '');
    set('challenge', p.challenge || '');
    form.dispatchEvent(new Event('change', {bubbles: true}));
  });

  // ---- WL-8: a challenge is every day; another schedule ends the choice.
  document.querySelectorAll('[data-habit-form]').forEach(function (form) {
    form.addEventListener('change', function (e) {
      var t = e.target;
      if (t.name === 'challenge' && t.value) {
        var daily = form.querySelector('[name=schedule][value=daily]');
        if (daily) daily.checked = true;
      } else if (t.name === 'schedule' && t.value !== 'daily') {
        var none = form.querySelector('[name=challenge][value=""]');
        if (none) none.checked = true;
      }
    }, true);
  });

'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''from django.views.decorators.http import require_POST

from . import guide
from . import habits as H
''',
         r'''from django.views.decorators.http import require_POST

from . import challenge as CH
from . import guide
from . import habits as H
'''),
        (r'''        'week_target': target,
        'flexible': H.is_flexible(habit),
    }

''',
         r'''        'week_target': target,
        'flexible': H.is_flexible(habit),
        # WL-8 - "Day 12 of 30" for a challenge.
        'challenge': CH.state(habit, done, today) if CH.has(habit) else None,
    }

'''),
        (r'''    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    for habit in active:
        done = _done_dates(habit)
        if not H.due_today(habit, done, day):
            continue
''',
         r'''    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    finishes, asks = [], []
    for habit in active:
        done = _done_dates(habit)
        # WL-8 - a challenge just finished is noted once; a missed day is
        # asked about once.
        if CH.has(habit):
            CH.note_finished(habit, done, day, profile)
            cs = CH.state(habit, done, day)
            if habit.challenge_done_on:
                finishes.append({'habit': habit, 'c': cs})
            elif cs and cs['ask']:
                asks.append({'habit': habit, 'c': cs})
        if not H.due_today(habit, done, day):
            continue
'''),
        (r'''        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        # WL-7 - Calm minutes today, for the "Take a breath" card.
        'calm_today': _calm_today(request.user, day),
''',
         r'''        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        # WL-8 - challenges finished (keep, again, let go) and missed days.
        'finishes': finishes,
        'challenge_finish_actions': CH.FINISH_ACTIONS,
        'asks': asks,
        # WL-7 - Calm minutes today, for the "Take a breath" card.
        'calm_today': _calm_today(request.user, day),
'''),
        (r'''        'comebacks': len(H.comebacks(habit, done, day)),
        'tip': _tip(profile, ['detail_week', 'detail_calendar']),
    })

''',
         r'''        'comebacks': len(H.comebacks(habit, done, day)),
        'tip': _tip(profile, ['detail_week', 'detail_calendar']),
        # WL-8 - the challenge, if it is one.
        'challenge': CH.state(habit, done, day) if CH.has(habit) else None,
        'challenge_finish_actions': CH.FINISH_ACTIONS,
    })

'''),
        (r'''    schedule = post.get('schedule') or Habit.SCHEDULE_DAILY
    if schedule not in dict(Habit.SCHEDULES):
        schedule = Habit.SCHEDULE_DAILY
    weekdays = ''.join(sorted({d for d in post.getlist('weekdays')
''',
         r'''    schedule = post.get('schedule') or Habit.SCHEDULE_DAILY
    if schedule not in dict(Habit.SCHEDULES):
        schedule = Habit.SCHEDULE_DAILY
    # WL-8 - a challenge is every day.
    if _challenge_choice(post):
        schedule = Habit.SCHEDULE_DAILY
    weekdays = ''.join(sorted({d for d in post.getlist('weekdays')
'''),
        (r'''                                         started_on=_today(), position=pos,
                                         **values)
            return redirect('wellness:habit_detail', pk=habit.pk)
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': True, 'v': values, 'errors': errors,
        'weekday_names': _weekday_names(values.get('weekdays', '')),
        'tip': _tip(profile, ['new_examples']),
''',
         r'''                                         started_on=_today(), position=pos,
                                         **values)
            _set_challenge(habit, request.POST, _today())
            habit.save()
            return redirect('wellness:habit_detail', pk=habit.pk)
        values['challenge'] = _challenge_choice(request.POST)
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': True, 'v': values, 'errors': errors,
        'challenge_days': CH.DAYS,
        'challenge_starters': [(lbl, json.dumps(pr))
                               for lbl, pr in CH.STARTERS],
        'weekday_names': _weekday_names(values.get('weekdays', '')),
        'tip': _tip(profile, ['new_examples']),
'''),
        (r'''            for k, v in values.items():
                setattr(habit, k, v)
            habit.save()
            _resync(habit)
            return redirect('wellness:habit_detail', pk=habit.pk)
    else:
        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from',
            'remind_at')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
        'errors': errors,
        'weekday_names': _weekday_names(values.get('weekdays') or ''),
        'tip': None, 'kinds': Habit.KINDS, 'times': Habit.TIMES,
    })


''',
         r'''            for k, v in values.items():
                setattr(habit, k, v)
            _set_challenge(habit, request.POST, _today())
            habit.save()
            _resync(habit)
            return redirect('wellness:habit_detail', pk=habit.pk)
        values['challenge'] = _challenge_choice(request.POST)
    else:
        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from',
            'remind_at')}
        values['challenge'] = habit.challenge_days if CH.has(habit) else None
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
        'errors': errors, 'challenge_days': CH.DAYS,
        'weekday_names': _weekday_names(values.get('weekdays') or ''),
        'tip': None, 'kinds': Habit.KINDS, 'times': Habit.TIMES,
    })


def _challenge_choice(post):
    """7, 14, 21 or 30 from the form, or None."""
    try:
        n = int(post.get('challenge') or 0)
    except ValueError:
        return None
    return n if n in CH.DAYS else None


def _set_challenge(habit, post, day):
    """Begin, change or end the habit's challenge from the form. Editing
    anything else leaves a running (or finished) one as it is."""
    want = _challenge_choice(post)
    if want and (not CH.has(habit) or habit.challenge_days != want):
        CH.begin(habit, want, day)
    elif not want and CH.has(habit):
        CH.clear(habit)


'''),
        (r'''        habit.delete()
        return redirect('wellness:habit_list')
    else:
        raise Http404
    habit.save()
    if action in ('archive',):
        return redirect('wellness:habit_list')
    return redirect('wellness:habit_detail', pk=habit.pk)
''',
         r'''        habit.delete()
        return redirect('wellness:habit_list')
    elif action.startswith('challenge_') and CH.has(habit):
        # WL-8 - the answers a challenge asks for. Never "failed".
        day = _today()
        if action == 'challenge_carry':
            CH.carry_on(habit, day)
        elif action == 'challenge_restart':
            CH.start_again(habit, day)
        elif action == 'challenge_pause':
            CH.carry_on(habit, day)
            habit.paused = True
        elif action == 'challenge_keep':
            CH.clear(habit)
        elif action == 'challenge_again':
            CH.start_again(habit, day)
        elif action == 'challenge_letgo':
            CH.clear(habit)
            habit.archived_at = timezone.now()
        else:
            raise Http404
    else:
        raise Http404
    habit.save()
    nxt = request.POST.get('next') or ''
    if nxt.startswith('/wellness/') and '//' not in nxt:
        return redirect(nxt)
    if action in ('archive', 'challenge_letgo'):
        return redirect('wellness:habit_list')
    return redirect('wellness:habit_detail', pk=habit.pk)
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl9-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl10-1'


'''),
    ]),
    (os.path.join('wellness', 'models.py'), [
        (r'''    # the person has turned reminders on for a phone. Empty means none.
    remind_at = models.TimeField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
''',
         r'''    # the person has turned reminders on for a phone. Empty means none.
    remind_at = models.TimeField(null=True, blank=True)
    # WL-8, 31 Oct 2026 - a challenge: this many done days from
    # challenge_from (7, 14, 21 or 30). challenge_seen is the last missed
    # day the person answered ("Carry on"); challenge_done_on the day the
    # last one was done. See challenge.py.
    challenge_days = models.PositiveSmallIntegerField(null=True, blank=True)
    challenge_from = models.DateField(null=True, blank=True)
    challenge_seen = models.DateField(null=True, blank=True)
    challenge_done_on = models.DateField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
'''),
    ]),
    (os.path.join('wellness', 'badges.py'), [
        (r'''     'given to yourself.', lambda f: f['calm_minutes'] >= 100,
     lambda f: (f['calm_minutes'], 100, 'minute')),
]
KEYS = [b[0] for b in BADGES]
''',
         r'''     'given to yourself.', lambda f: f['calm_minutes'] >= 100,
     lambda f: (f['calm_minutes'], 100, 'minute')),
    # WL-8, 31 Oct 2026 - a challenge done to the end.
    ('challenge_1', '✓', 'Challenge finished', 'You finished a challenge, '
     'every day of it.', lambda f: f['challenges'] >= 1, lambda f: None),
]
KEYS = [b[0] for b in BADGES]
'''),
        (r'''         'progress': None, 'kg_done': 0.0, 'kg_half': 0.0, 'kg_total': 0.0,
         'sessions': 0, 'records': 0, 'calm_sessions': 0,
         'calm_minutes': 0}


''',
         r'''         'progress': None, 'kg_done': 0.0, 'kg_half': 0.0, 'kg_total': 0.0,
         'sessions': 0, 'records': 0, 'calm_sessions': 0,
         'calm_minutes': 0, 'challenges': 0}


'''),
        (r'''    f['calm_minutes'] = CALM.total_minutes(user) if f['calm_sessions'] \
        else 0
    return f

''',
         r'''    f['calm_minutes'] = CALM.total_minutes(user) if f['calm_sessions'] \
        else 0
    f['challenges'] = len(((prof.prefs if prof else None) or {})
                          .get('challenges') or [])
    return f

'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-7, 31 Oct 2026 - Calm.
    {'q': 'What is Calm?',
''',
         r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line: 7, 14, 21 or 30 days, '
          'every day. Choose "Make it a challenge" when you add or edit a '
          'habit, or tap one of the challenges to try. Only the days you do '
          'count, so Today shows "Day 12 of 30".'},
    {'q': 'What happens if I miss a day of a challenge?',
     'a': 'Nothing is lost. Wellness asks once: carry on, and the finish '
          'moves out by a day, or start again from today. Missed a few in a '
          'row? You can pause it for now too. When you finish, keep it as a '
          'habit, go again, or let it go.'},
    # WL-7, 31 Oct 2026 - Calm.
    {'q': 'What is Calm?',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Pause takes it off Today for a while without losing anything.',
            'After 66 good days you can mark it established.',
        ],
        'signs': [
            ('--w-sage-deep', 'Sage squares: done.'),
            ('--w-sand', 'Sand squares: comebacks - the days you returned '
                         'after a break. They count more than a perfect run.'),
            ('--w-empty', 'Faint squares: days before the habit began, or '
                          'days it was not planned.'),
        ],
    },
''',
         r'''            'Pause takes it off Today for a while without losing anything.',
            'After 66 good days you can mark it established.',
            'A challenge shows a square for each day to do. Miss one and '
            'you choose: carry on, or start again.',
        ],
        'signs': [
            ('--w-sage-deep', 'Sage squares: done.'),
            ('--w-sand', 'Sand squares: comebacks - the days you returned '
                         'after a break. They count more than a perfect run.'),
            ('--w-empty', 'Faint squares: days before the habit began, or '
                          'days it was not planned - or, for a challenge, '
                          'the days still to do.'),
        ],
    },
'''),
        (r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
        ],
        'signs': [],
''',
         r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge: 7, 14, 21 or 30 days, every day.',
        ],
        'signs': [],
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_eight.py',
    # WL-7, 31 Oct 2026 - Wellness: Calm.
    'test_wellness_nine.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_eight.py',
    # WL-7, 31 Oct 2026 - Wellness: Calm.
    'test_wellness_nine.py',
    # WL-8, 31 Oct 2026 - Wellness: challenges.
    'test_wellness_ten.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-7, 31 Oct 2026 - Wellness: Calm.
    '.bak_wellness9',
]

''',
         r'''    # WL-7, 31 Oct 2026 - Wellness: Calm.
    '.bak_wellness9',
    # WL-8, 31 Oct 2026 - Wellness: challenges.
    '.bak_wellness10',
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
    raise SystemExit('WL-8 REFUSED: %s' % msg)


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
    if "'test_wellness_ten.py'" in read(pq):
        print('WL-8 already applied.')
        return 0
    if "'test_wellness_nine.py'" not in read(pq):
        refuse('Release 52 is not applied - this round registers after it.')
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
        print('WL-8 --check: %d file(s) would change, none written; %d '
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
    print('WL-8 applied - Wellness: challenges.')
    print('      MIGRATION: python manage.py migrate wellness  (0009_challenges)')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
