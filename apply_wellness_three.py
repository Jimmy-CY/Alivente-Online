# -*- coding: utf-8 -*-
"""apply_wellness_three.py - round WL-3, 30 Oct 2026.

RELEASE 45 - WELLNESS, PART THREE: WORKOUTS.

    - An exercise library (seeded by migration 0004), your own exercises,
      and My equipment, so suggestions only offer weights you own.
    - Routines with sets, a rep range and rest, shown on Today on chosen
      days; the live logger with last time's numbers, a rest timer and the
      record moment; double progression; records, history and a chart per
      exercise; a habit can tick itself when a workout is finished.
    - The bottom bar gains Workouts; Today gains the workout card.

New files ship beside this patcher. Stands on Release 44. Idempotent.
Edits backed up to .bak_wellness3.
MIGRATION: wellness 0003 and 0004 - run  python manage.py migrate.
"""
import os
import sys

SUFFIX = '.bak_wellness3'
MARK = 'WL-3, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/training.py',
    'wellness/views_workouts.py',
    'wellness/migrations/0003_workouts.py',
    'wellness/migrations/0004_exercise_library.py',
    'wellness/templates/wellness/workouts.html',
    'wellness/templates/wellness/routine_form.html',
    'wellness/templates/wellness/session_live.html',
    'wellness/templates/wellness/session_detail.html',
    'wellness/templates/wellness/exercise_detail.html',
    'wellness/templates/wellness/exercise_form.html',
    'wellness/templates/wellness/kit.html',
    'test_wellness_three.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''                                      null=True, blank=True)
    goal_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''                                      null=True, blank=True)
    goal_date = models.DateField(null=True, blank=True)
    # WL-3 - the kit this person trains with, so suggestions only offer
    # weights they own: {"barbell_max": 30, "dumbbells": [1, 2, 4, 6, 8],
    # "kettlebells": [], "plate_step": 2.5}.
    equipment = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''    time_of_day = models.CharField(max_length=10, choices=TIMES,
                                   default='anytime')
    cue = models.CharField('After I...', max_length=120, blank=True)
    tiny_version = models.CharField('On a hard day, just...',
''',
         r'''    time_of_day = models.CharField(max_length=10, choices=TIMES,
                                   default='anytime')
    # WL-3, 30 Oct 2026 - a habit that ticks itself: 'workout' is done on
    # any day a workout is finished.
    auto_from = models.CharField(max_length=10, blank=True, default='',
                                 choices=[('', 'Ticked by hand'),
                                          ('workout', 'A finished workout')])
    cue = models.CharField('After I...', max_length=120, blank=True)
    tiny_version = models.CharField('On a hard day, just...',
'''),
        (r'''    def unit(self):
        return self.UNITS.get(self.kind, 'cm')
''',
         r'''    def unit(self):
        return self.UNITS.get(self.kind, 'cm')


class Exercise(models.Model):
    """WL-3, 30 Oct 2026. user=None is the shared library (seeded by
    migration 0003); a row with a user is that person's own exercise."""
    TYPES = [
        ('weight', 'Weight and reps'),
        ('reps', 'Reps only'),
        ('time', 'Time'),
        ('distance', 'Distance and time'),
    ]
    MUSCLES = [
        ('chest', 'Chest'), ('back', 'Back'), ('shoulders', 'Shoulders'),
        ('arms', 'Arms'), ('legs', 'Legs'), ('core', 'Core'),
        ('full', 'Full body'), ('cardio', 'Cardio'),
    ]
    EQUIPMENT = [
        ('dumbbell', 'Dumbbells'), ('barbell', 'Barbell'),
        ('kettlebell', 'Kettlebell'), ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine or cable'), ('band', 'Band'),
        ('none', 'Nothing'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.CASCADE,
                             related_name='wellness_exercises')
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=TYPES, default='weight')
    muscle = models.CharField(max_length=10, choices=MUSCLES)
    equipment = models.CharField(max_length=12, choices=EQUIPMENT)

    class Meta:
        db_table = 'wellness_exercise'
        ordering = ['name']

    def __str__(self):
        return self.name


class Routine(models.Model):
    """A saved workout: its exercises, targets and rest. `weekdays` puts it
    on Today on those days (Monday = 0)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_routines')
    name = models.CharField(max_length=80)
    weekdays = models.CharField(max_length=7, blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_routine'
        ordering = ['name']

    def __str__(self):
        return self.name

    def weekday_set(self):
        return {int(c) for c in self.weekdays if c.isdigit()}


class RoutineItem(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE,
                                related_name='items')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(default=0)
    sets = models.PositiveSmallIntegerField(default=3)
    rep_min = models.PositiveSmallIntegerField(default=8)
    rep_max = models.PositiveSmallIntegerField(default=12)
    seconds = models.PositiveIntegerField(null=True, blank=True)
    rest = models.PositiveSmallIntegerField(default=60)

    class Meta:
        db_table = 'wellness_routine_item'
        ordering = ['position', 'id']


class WorkoutSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_sessions')
    routine = models.ForeignKey(Routine, null=True, blank=True,
                                on_delete=models.SET_NULL)
    name = models.CharField(max_length=80)
    date = models.DateField()
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    effort = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.CharField(max_length=280, blank=True)

    class Meta:
        db_table = 'wellness_workout_session'
        ordering = ['-started_at']

    def __str__(self):
        return '%s on %s' % (self.name, self.date)


class WorkoutSet(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE,
                                related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(default=0)
    set_no = models.PositiveSmallIntegerField(default=1)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True,
                                 blank=True)
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    done = models.BooleanField(default=False)
    is_pr = models.BooleanField(default=False)

    class Meta:
        db_table = 'wellness_workout_set'
        ordering = ['position', 'set_no']
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # WL-2 - the weigh-in card, the evening card, On this day.
        'body': body_summary(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
''',
         r'''        # WL-2 - the weigh-in card, the evening card, On this day.
        'body': body_summary(request.user, day),
        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
'''),
        (r'''                            request.user, day), day)],
    })


''',
         r'''                            request.user, day), day)],
    })


def _workout_card(user, day):
    from .views_workouts import today_card
    return today_card(user, day)


'''),
        (r'''            weekdays=s.get('weekdays', ''), time_of_day=s['time_of_day'],
            cue=s.get('cue', ''), tiny_version=s.get('tiny_version', ''),
            started_on=day, position=pos)
        pos += 1
''',
         r'''            weekdays=s.get('weekdays', ''), time_of_day=s['time_of_day'],
            cue=s.get('cue', ''), tiny_version=s.get('tiny_version', ''),
            auto_from=s.get('auto_from', ''),
            started_on=day, position=pos)
        pos += 1
'''),
        (r'''        'per_week': per_week, 'time_of_day': tod,
        'cue': (post.get('cue') or '').strip()[:120],
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
    }
''',
         r'''        'per_week': per_week, 'time_of_day': tod,
        'cue': (post.get('cue') or '').strip()[:120],
        'auto_from': 'workout' if post.get('auto_from') == 'workout' else '',
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
    }
'''),
        (r'''        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
''',
         r'''        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl2-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl3-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''
from . import views

app_name = 'wellness'
''',
         r'''
from . import views
from . import views_workouts as W

app_name = 'wellness'
'''),
        (r'''    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
''',
         r'''    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
    path('workouts/kit/', W.kit, name='kit'),
    path('workouts/routines/new/', W.routine_edit, name='routine_new'),
    path('workouts/routines/<int:pk>/', W.routine_edit, name='routine_edit'),
    path('workouts/routines/<int:pk>/delete/', W.routine_delete,
         name='routine_delete'),
    path('workouts/start/', W.session_start, name='session_start'),
    path('workouts/<int:pk>/live/', W.session_live, name='session_live'),
    path('workouts/<int:pk>/', W.session_detail, name='session_detail'),
    path('workouts/<int:pk>/add/', W.set_add, name='set_add'),
    path('workouts/<int:pk>/finish/', W.session_finish,
         name='session_finish'),
    path('workouts/<int:pk>/delete/', W.session_delete,
         name='session_delete'),
    path('workouts/sets/<int:pk>/', W.set_save, name='set_save'),
    path('workouts/sets/<int:pk>/delete/', W.set_delete, name='set_delete'),
    path('workouts/exercises/new/', W.exercise_new, name='exercise_new'),
    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    {'key': 'strength', 'name': 'Strength training', 'kind': 'duration',
     'target': 15, 'schedule': 'per_week', 'per_week': 3,
     'time_of_day': 'morning', 'tiny_version': 'one set'},
]

''',
         r'''    {'key': 'strength', 'name': 'Strength training', 'kind': 'duration',
     'target': 15, 'schedule': 'per_week', 'per_week': 3,
     'time_of_day': 'morning', 'tiny_version': 'one set',
     'auto_from': 'workout'},
]

'''),
        (r'''    'body_trend': 'The big number is your trend, not today\'s scale. A '
                  'heavy morning barely moves it - that is the point.',
}

''',
         r'''    'body_trend': 'The big number is your trend, not today\'s scale. A '
                  'heavy morning barely moves it - that is the point.',
    # WL-3
    'workout_routine': 'Start with a routine: a saved workout you can '
                       'start in one tap, with last time\'s numbers waiting.',
    'workout_previous': 'The grey numbers are last time. Beat them by a rep '
                        'or a little weight and you are making progress.',
}

'''),
        (r'''          'What matters most is the same conditions: morning, after the '
          'bathroom, before food.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
''',
         r'''          'What matters most is the same conditions: morning, after the '
          'bathroom, before food.'},
    {'q': 'How does Wellness suggest the next weight?',
     'a': 'Each exercise in a routine has a rep range, say 8 to 12. When you '
          'reach the top of the range on every set, the next workout suggests '
          'the next weight up that you own (set your kit under My '
          'equipment). Until then it suggests the same weight and one more '
          'rep. This is called double progression.'},
    {'q': 'What counts as a record?',
     'a': 'Your heaviest weight on an exercise, the most reps at a weight, '
          'your best estimated one-rep max, or your longest time or distance. '
          'The first time you do an exercise sets the bar; after that, '
          'beating it gets a star.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit and tick "Tick it for me '
          'when I finish a workout". Finishing any workout then ticks it for '
          'that day.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  align-items: center;
  gap: 2px;
  min-width: 64px;
  min-height: 48px;
  padding-top: 4px;
''',
         r'''  align-items: center;
  gap: 2px;
  min-width: 58px;
  min-height: 48px;
  padding-top: 4px;
'''),
        (r'''.w-locked { color: var(--w-quiet); font-style: italic; }
.w-notice { background: var(--w-sand); border-radius: 16px; padding: 14px 16px; font-size: 14px; }
''',
         r'''.w-locked { color: var(--w-quiet); font-style: italic; }
.w-notice { background: var(--w-sand); border-radius: 16px; padding: 14px 16px; font-size: 14px; }

/* ---- WL-3: workouts --------------------------------------------------- */
.w-sets { display: flex; flex-direction: column; gap: 6px; }
.w-set {
  display: grid; grid-template-columns: 28px minmax(0, 1fr) 70px 58px 48px;
  gap: 6px; align-items: center; min-height: 56px; border-radius: 12px; padding: 0 4px;
}
.w-set.head { min-height: 0; height: 28px; font-size: 11px; font-weight: 600; color: var(--w-quiet); letter-spacing: .04em; text-transform: uppercase; }
.w-set.is-done { background: var(--w-soft); }
.w-set .n { text-align: center; font-weight: 600; }
.w-set .prev { font-size: 13px; color: var(--w-quiet); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.w-set input {
  width: 100%; height: 44px; border: 1.5px solid var(--w-line); border-radius: 10px;
  text-align: center; font: inherit; font-size: 17px; font-weight: 600;
  background: var(--w-card); color: var(--w-ink);
}
.w-set input:focus { border-color: var(--w-sage); outline: none; }
.w-tick {
  width: 44px; height: 44px; border-radius: 22px; border: 2px solid var(--w-ring-off);
  background: var(--w-card); display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.w-tick svg { opacity: 0; }
.is-done .w-tick { background: var(--w-sage-deep); border-color: var(--w-sage-deep); }
.is-done .w-tick svg { opacity: 1; }
.w-tick svg path { stroke: var(--w-on-accent); }
.w-rest {
  position: fixed; left: 16px; right: 16px; bottom: calc(env(safe-area-inset-bottom, 0px) + 96px);
  max-width: 528px; margin: 0 auto; z-index: 15;
  background: var(--w-card); border-radius: 20px; padding: 14px 16px;
  box-shadow: 0 8px 28px rgba(0,0,0,.14); display: flex; flex-direction: column; gap: 10px;
}
.w-rest[hidden] { display: none; }
.w-rest .clock { font-size: 26px; font-weight: 600; font-variant-numeric: tabular-nums; }
.w-record {
  position: fixed; left: 16px; right: 16px; top: calc(env(safe-area-inset-top, 0px) + 16px);
  max-width: 528px; margin: 0 auto; z-index: 25;
  background: var(--w-sand); border-radius: 18px; padding: 14px 16px; font-weight: 600;
  display: flex; align-items: center; gap: 12px; box-shadow: 0 8px 28px rgba(0,0,0,.12);
  animation: w-rise .4s ease;
}
.w-record[hidden] { display: none; }
.w-clock { font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; }
.w-effort { display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 4px; }
.w-effort label { display: flex; }
.w-effort input { position: absolute; opacity: 0; pointer-events: none; }
.w-effort span { flex: 1; min-height: 44px; border-radius: 10px; background: var(--w-bg); display: flex; align-items: center; justify-content: center; font-weight: 600; cursor: pointer; }
.w-effort input:checked + span { background: var(--w-sage-deep); color: var(--w-on-accent); }
.w-select { appearance: auto; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  });

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  });

  // ---- WL-3: the live workout logger.
  var live = document.querySelector('[data-live]');
  if (live) {
    var started = parseInt(live.getAttribute('data-started'), 10);
    var clock = live.querySelector('[data-elapsed]');
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function fmt(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + pad(s % 60); }
    setInterval(function () { clock.textContent = fmt((Date.now() - started) / 1000); }, 1000);
    // Keep the screen awake while training, where the phone allows it.
    var lock = null;
    function wake() { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { lock = l; }).catch(function () {}); }
    wake();
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') wake(); });

    var bar = document.querySelector('[data-rest-bar]');
    var rclock = bar.querySelector('[data-rest-clock]');
    var fill = bar.querySelector('[data-rest-fill]');
    var restEnd = 0, restTotal = 0, timer = null;
    function tick() {
      var left = (restEnd - Date.now()) / 1000;
      if (left <= 0) {
        clearInterval(timer); timer = null; bar.hidden = true;
        if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
        return;
      }
      rclock.textContent = fmt(left);
      fill.style.width = (100 * (1 - left / restTotal)).toFixed(1) + '%';
    }
    function rest(seconds) {
      if (!seconds) return;
      restTotal = seconds; restEnd = Date.now() + seconds * 1000;
      bar.hidden = false; tick();
      if (!timer) timer = setInterval(tick, 250);
    }
    bar.addEventListener('click', function (e) {
      var a = e.target.closest('[data-rest-add]');
      if (a) { var d = parseInt(a.getAttribute('data-rest-add'), 10); restEnd += d * 1000; restTotal = Math.max(1, restTotal + d); tick(); }
      if (e.target.closest('[data-rest-skip]')) { restEnd = Date.now(); tick(); }
    });
    var rec = document.querySelector('[data-record]');
    function celebrate(text) {
      rec.querySelector('[data-record-text]').textContent = 'New record! ' + text;
      rec.hidden = false;
      setTimeout(function () { rec.hidden = true; }, 4500);
    }
    live.addEventListener('submit', function (e) {
      var f = e.target;
      if (!f.matches('[data-set]')) return;
      e.preventDefault();
      var flag = f.querySelector('input[name=done]');
      var nowDone = flag.value === '1';
      f.classList.toggle('is-done', nowDone);
      post(f).then(function (res) {
        f.classList.toggle('is-done', res.done);
        flag.value = res.done ? '0' : '1';
        f.querySelector('.w-tick').setAttribute('aria-pressed', String(res.done));
        if (res.done) {
          if (res.record) celebrate(res.record);
          rest(parseInt(f.getAttribute('data-rest'), 10) || res.rest);
        }
      }).catch(function () { f.classList.toggle('is-done', !nowDone); f.submit(); });
    });
  }

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl2-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl3-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''    Journal
  </a>
  <a class="w-tab{% if tab == 'body' %} is-on{% endif %}" href="{% url 'wellness:body' %}"{% if tab == 'body' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l5-6 4 3 7-8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Body
  </a>
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl2-1" defer></script>
</body>
</html>
''',
         r'''    Journal
  </a>
  <a class="w-tab{% if tab == 'workouts' %} is-on{% endif %}" href="{% url 'wellness:workouts' %}"{% if tab == 'workouts' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M6 8v8M18 8v8M3.5 10v4M20.5 10v4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    Workouts
  </a>
  <a class="w-tab{% if tab == 'body' %} is-on{% endif %}" href="{% url 'wellness:body' %}"{% if tab == 'body' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l5-6 4 3 7-8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Body
  </a>
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl3-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
''',
         r'''{% endif %}

{# WL-3 - the planned or open workout. #}
{% if workout.open %}
<a class="w-card sand" href="{% url 'wellness:session_live' workout.open.pk %}" style="gap:6px;text-decoration:none;color:inherit">
  <span class="w-label">Workout in progress</span>
  <span style="font-size:17px;font-weight:600">{{ workout.open.name }}</span>
  <span class="w-small w-quiet">Tap to carry on.</span>
</a>
{% elif workout.done %}
<a class="w-card soft" href="{% url 'wellness:session_detail' workout.done.pk %}" style="gap:6px;text-decoration:none;color:inherit">
  <span style="font-size:17px;font-weight:600">Trained today: {{ workout.done.name }}</span>
  <span class="w-small w-quiet">Nice work. See how it went.</span>
</a>
{% else %}{% for r in workout.planned %}
<section class="w-card" style="gap:12px">
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <h2 class="w-h2">{{ r.name }}</h2>
    <span class="w-small w-quiet">{{ r.items.count }} exercise{{ r.items.count|pluralize }}</span>
  </div>
  <form method="post" action="{% url 'wellness:session_start' %}">{% csrf_token %}<input type="hidden" name="routine" value="{{ r.pk }}"><button class="w-btn full" type="submit">Start workout</button></form>
</section>
{% endfor %}{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn ghost" data-back>Back</button><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
  </section>
''',
         r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {# WL-3 - a training habit can tick itself when a workout is finished. #}
    <label style="display:flex;gap:10px;align-items:center;min-height:44px" data-when-kind="yes_no count duration">
      <input type="checkbox" name="auto_from" value="workout"{% if v.auto_from == 'workout' %} checked{% endif %} style="width:22px;height:22px">
      <span>Tick it for me when I finish a workout</span>
    </label>
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn ghost" data-back>Back</button><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
  </section>
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_passkeys.py',
    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    'test_wellness_two.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_passkeys.py',
    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    'test_wellness_two.py',
    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    'test_wellness_three.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    '.bak_wellness2',
]

''',
         r'''    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    '.bak_wellness2',
    # WL-3, 30 Oct 2026 - Wellness, part three: Workouts.
    '.bak_wellness3',
]

'''),
    ]),
    (os.path.join('test_wellness_two.py'), [
        (r'''ok(all(u in base for u in ("wellness:journal_list", "wellness:body")),
   'the bottom bar has Journal and Body')
ok(base.count('class="w-tab{%') == 4, '  four tabs: Today, Habits, '
   'Journal, Body', base.count('class="w-tab{%'))
bad = [f for f in NEW_FILES if f.endswith('.html') and 'includes' not in f
       and '{% extends "wellness/base.html" %}' not in read(J(APP, f))]
''',
         r'''ok(all(u in base for u in ("wellness:journal_list", "wellness:body")),
   'the bottom bar has Journal and Body')
# WL-3 added Workouts as a fifth; this round's claim is that Journal and
# Body are there, not how many others sit beside them.
ok(base.count('class="w-tab{%') >= 4, '  at least four tabs: Today, '
   'Habits, Journal, Body', base.count('class="w-tab{%'))
bad = [f for f in NEW_FILES if f.endswith('.html') and 'includes' not in f
       and '{% extends "wellness/base.html" %}' not in read(J(APP, f))]
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
    raise SystemExit('WL-3 REFUSED: %s' % msg)


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
    if "'test_wellness_three.py'" in read(pq):
        print('WL-3 already applied.')
        return 0
    if "'test_wellness_two.py'" not in read(pq):
        refuse('Release 44 is not applied - this round registers after it.')
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
        print('WL-3 --check: %d file(s) would change, none written; %d '
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
    print('WL-3 applied - Wellness, part three: Workouts.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0003, 0004).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
