# -*- coding: utf-8 -*-
"""apply_wellness_fifteen.py - round WL-11, 1 Nov 2026.

RELEASE 58 - WELLNESS: CALORIES ON A WORKOUT.

    Demetri, 1 Nov 11:27: "When I do a workout I want to be able to
    optionally capture the Calories that I burnt during that workout."
    11:28: "Perfect. Go for it."

    - Typed in from the watch on the finished workout: a fourth figure,
      "+ Add calories", then "285 kcal". Optional; can be changed later.
    - Adds up on the Workouts page, Recent workouts, the Monday email and
      Insights. Help and the general questions explain it.

New files ship beside this patcher. Stands on Release 57. Idempotent.
Edits backed up to .bak_wellness15. MIGRATION 0010_workout_calories.
"""
import os
import sys

SUFFIX = '.bak_wellness15'
MARK = 'WL-11, 1 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/migrations/0010_workout_calories.py',
    'test_wellness_fifteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''    effort = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.CharField(max_length=280, blank=True)

    class Meta:
''',
         r'''    effort = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.CharField(max_length=280, blank=True)
    # WL-11, 1 Nov 2026: calories burnt, typed in from the watch. Optional.
    calories = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
'''),
    ]),
    (os.path.join('wellness', 'views_workouts.py'), [
        (r'''from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
''',
         r'''from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
'''),
        (r'''        user=request.user, finished_at__isnull=False,
        date__gte=week_start).count()
    prs = WorkoutSet.objects.filter(session__user=request.user,
                                    is_pr=True).select_related(
''',
         r'''        user=request.user, finished_at__isnull=False,
        date__gte=week_start).count()
    week_cal = sum(WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=False,
        date__gte=week_start, calories__isnull=False)
        .values_list('calories', flat=True))
    prs = WorkoutSet.objects.filter(session__user=request.user,
                                    is_pr=True).select_related(
'''),
        (r'''        'today_routines': today_routines, 'open_session': open_session,
        'recent': recent, 'this_week': this_week, 'prs': prs,
        'weekday_names': WEEKDAYS,
        'tip': _tip(profile, ['workout_routine']) if not routines else None,
''',
         r'''        'today_routines': today_routines, 'open_session': open_session,
        'recent': recent, 'this_week': this_week, 'prs': prs,
        'week_cal': week_cal,
        'weekday_names': WEEKDAYS,
        'tip': _tip(profile, ['workout_routine']) if not routines else None,
'''),
        (r'''        'volume': int(TR.volume([(x.weight, x.reps) for x in sets])),
        'records': [x for x in sets if x.is_pr],
    })


''',
         r'''        'volume': int(TR.volume([(x.weight, x.reps) for x in sets])),
        'records': [x for x in sets if x.is_pr],
        'cal_open': request.GET.get('calories') == '1' or bool(
            request.GET.get('cal_error')),
        'cal_error': request.GET.get('cal_error') == '1',
        'cal_max': CAL_MAX,
    })


# WL-11, 1 Nov 2026. Demetri: "When I do a workout I want to be able to
# optionally capture the Calories that I burnt during that workout."
# Typed in from the watch (a web app cannot read the watch, and an estimate
# from weight and time is far rougher than the watch's heart-rate figure).
# Blank clears it. Can be added or changed any time after.
CAL_MAX = 5000


def clean_calories(raw):
    """'285' -> 285, '' -> None; ValueError for anything else."""
    raw = (raw or '').strip().replace(',', '').replace(' ', '')
    if raw.lower().endswith('kcal'):
        raw = raw[:-4]
    if not raw:
        return None
    if not raw.isdigit():
        raise ValueError('not a whole number')
    n = int(raw)
    if n < 1 or n > CAL_MAX:
        raise ValueError('out of range')
    return n


@wellness_view
@require_POST
def session_calories(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    try:
        s.calories = clean_calories(request.POST.get('calories'))
    except ValueError:
        return redirect(reverse('wellness:session_detail', args=[s.pk]) +
                        '?cal_error=1#w-cal')
    s.save(update_fields=['calories'])
    return redirect('wellness:session_detail', pk=s.pk)


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('workouts/<int:pk>/finish/', W.session_finish,
         name='session_finish'),
    path('workouts/<int:pk>/delete/', W.session_delete,
         name='session_delete'),
''',
         r'''    path('workouts/<int:pk>/finish/', W.session_finish,
         name='session_finish'),
    path('workouts/<int:pk>/calories/', W.session_calories,
         name='session_calories'),
    path('workouts/<int:pk>/delete/', W.session_delete,
         name='session_delete'),
'''),
    ]),
    (os.path.join('wellness', 'weekly.py'), [
        (r'''        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=sunday).order_by('date')) if 'workouts' in mods else []
    minutes = 0
    for s in sessions:
''',
         r'''        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=sunday).order_by('date')) if 'workouts' in mods else []
    # WL-11: calories typed in from the watch, where there are any.
    calories = sum(s.calories for s in sessions if s.calories)
    minutes = 0
    for s in sessions:
'''),
        (r'''            'sessions': [{'name': s.name, 'date': s.date} for s in sessions],
            'minutes': minutes, 'records': records, 'weight': weight,
            'badges': new_badges}

''',
         r'''            'sessions': [{'name': s.name, 'date': s.date} for s in sessions],
            'minutes': minutes, 'records': records, 'weight': weight,
            'calories': calories,
            'badges': new_badges}

'''),
        (r'''        if s['minutes']:
            head += ', %d minutes' % s['minutes']
        if s['records']:
            head += ', %d new record%s' % (s['records'],
''',
         r'''        if s['minutes']:
            head += ', %d minutes' % s['minutes']
        if s.get('calories'):
            head += ', %d kcal' % s['calories']
        if s['records']:
            head += ', %d new record%s' % (s['records'],
'''),
    ]),
    (os.path.join('wellness', 'insights.py'), [
        (r'''and says, carefully, what goes with what:

    - week by week: habits done, Calm minutes, workouts, mood;
    - the weight trend over the eight weeks;
    - findings such as "On days you did Calm, your mood averaged 3.9,
''',
         r'''and says, carefully, what goes with what:

    - week by week: habits done, Calm minutes, workouts, mood, and
      (WL-11) the calories typed in for workouts, once there are any;
    - the weight trend over the eight weeks;
    - findings such as "On days you did Calm, your mood averaged 3.9,
'''),
        (r'''

def weekly(today, mood_by_day, habit_days, calm_secs, workout_days):
    """Rows per week, oldest first. habit_days: date -> (done, due)."""
    out = []
''',
         r'''

def weekly(today, mood_by_day, habit_days, calm_secs, workout_days,
           workout_cal=None):
    """Rows per week, oldest first. habit_days: date -> (done, due)."""
    out = []
'''),
        (r'''            'calm_min': sum(calm_secs.get(d, 0) for d in days) // 60,
            'workouts': sum(1 for d in days if d in workout_days),
            'mood': round(avg(moods), 1) if moods else None,
        })
''',
         r'''            'calm_min': sum(calm_secs.get(d, 0) for d in days) // 60,
            'workouts': sum(1 for d in days if d in workout_days),
            'kcal': sum((workout_cal or {}).get(d, 0) for d in days),
            'mood': round(avg(moods), 1) if moods else None,
        })
'''),
        (r'''            calm_secs[d] = calm_secs.get(d, 0) + s
    workout_days = set()
    if 'workouts' in on:
        workout_days = set(WorkoutSession.objects.filter(
            user=user, finished_at__isnull=False, date__gte=since)
            .values_list('date', flat=True))
    rows = weekly(today, mood_by_day, habit_days, calm_secs, workout_days)
    weight = None
    if 'body' in on:
''',
         r'''            calm_secs[d] = calm_secs.get(d, 0) + s
    workout_days = set()
    workout_cal = {}
    if 'workouts' in on:
        for d, c in WorkoutSession.objects.filter(
                user=user, finished_at__isnull=False, date__gte=since
        ).values_list('date', 'calories'):
            workout_days.add(d)
            if c:
                workout_cal[d] = workout_cal.get(d, 0) + c
    rows = weekly(today, mood_by_day, habit_days, calm_secs, workout_days,
                  workout_cal)
    weight = None
    if 'body' in on:
'''),
        (r'''        'calm': bars(rows, 'calm_min') if 'calm' in on else None,
        'workouts': bars(rows, 'workouts') if 'workouts' in on else None,
        'mood': bars(rows, 'mood', 5) if 'journal' in on else None,
        'findings': findings(mood_by_day, habit_days, set(calm_secs),
''',
         r'''        'calm': bars(rows, 'calm_min') if 'calm' in on else None,
        'workouts': bars(rows, 'workouts') if 'workouts' in on else None,
        'kcal': bars(rows, 'kcal') if workout_cal else None,
        'mood': bars(rows, 'mood', 5) if 'journal' in on else None,
        'findings': findings(mood_by_day, habit_days, set(calm_secs),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'session_detail': {
        'title': 'A finished workout',
        'purpose': 'What you did, how long it took and any records.',
        'steps': ['Delete removes the whole workout.'],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
''',
         r'''    'session_detail': {
        'title': 'A finished workout',
        'purpose': 'What you did, how long it took, any records and, if '
                   'you add them, the calories you burnt.',
        'steps': ['Tap + Add calories and type the number your watch shows '
                  'for this workout. It is optional, and you can add or '
                  'change it later from Recent workouts.',
                  'Your calories add up on the Workouts page, in the '
                  'Monday email and on Insights.',
                  'Delete removes the whole workout.'],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
'''),
        (r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done', 'cycle_quick',
}

''',
         r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done', 'cycle_quick', 'session_calories',
}

'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'The first time you do an exercise sets the bar; after that, '
          'beating it gets a star.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
''',
         r'''          'The first time you do an exercise sets the bar; after that, '
          'beating it gets a star.'},
    # WL-11, 1 Nov 2026 - workout calories.
    {'q': 'Can I record the calories I burnt in a workout?',
     'a': 'Yes. When you finish, tap + Add calories at the top and type '
          'the number your watch shows. It is optional; you can add or '
          'change it later by opening the workout from Recent workouts. '
          'Wellness does not estimate calories itself - a guess from weight '
          'and time is far rougher than your watch, which measures your '
          'heart rate.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'session_detail.html'), [
        (r'''  <div><div class="w-big" style="font-size:26px">{{ volume }}</div><div class="w-small w-quiet">kg lifted</div></div>
  <div><div class="w-big" style="font-size:26px">{{ records|length }}</div><div class="w-small w-quiet">record{{ records|length|pluralize }}</div></div>
</section>
{% for r in records %}
<div class="w-card sand" style="flex-direction:row;align-items:center;gap:12px;padding:14px 18px">
''',
         r'''  <div><div class="w-big" style="font-size:26px">{{ volume }}</div><div class="w-small w-quiet">kg lifted</div></div>
  <div><div class="w-big" style="font-size:26px">{{ records|length }}</div><div class="w-small w-quiet">record{{ records|length|pluralize }}</div></div>
  {% if s.finished_at %}<a href="?calories=1#w-cal" data-cal-tile style="color:inherit;text-decoration:none;min-height:44px">{% if s.calories %}<div class="w-big" style="font-size:26px">{{ s.calories }}</div><div class="w-small w-quiet">kcal</div>{% else %}<div class="w-big" style="font-size:26px;color:var(--w-sage-deep)">+ Add</div><div class="w-small w-quiet">calories</div>{% endif %}</a>{% endif %}
</section>
{% if s.finished_at and cal_open %}
<details class="w-card" id="w-cal" open>
  <summary style="cursor:pointer;min-height:44px;display:flex;align-items:center">{% if s.calories %}Calories burnt: {{ s.calories }} kcal - change{% else %}Add calories from your watch{% endif %}</summary>
  <form method="post" action="{% url 'wellness:session_calories' s.pk %}" style="display:flex;flex-direction:column;gap:10px">{% csrf_token %}
    <label for="w-cal-in" class="w-small w-quiet">The calories your watch shows for this workout. Optional - leave it empty to clear it.</label>
    <div style="display:flex;gap:10px;align-items:center">
      <input id="w-cal-in" name="calories" type="number" inputmode="numeric" min="1" max="{{ cal_max }}" step="1" value="{{ s.calories|default_if_none:'' }}" placeholder="e.g. 285" style="flex:1;min-height:48px;font-size:18px"{% if cal_open %} autofocus{% endif %}>
      <span class="w-quiet">kcal</span>
    </div>
    {% if cal_error %}<p class="w-small" role="alert" style="margin:0;color:var(--w-rose-deep, #9A4A4A)">Please type a whole number from 1 to {{ cal_max }}.</p>{% endif %}
    <button class="w-btn" type="submit">Save</button>
  </form>
</details>
{% endif %}
{% for r in records %}
<div class="w-card sand" style="flex-direction:row;align-items:center;gap:12px;padding:14px 18px">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'workouts.html'), [
        (r'''<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
  <h1 class="w-title">Workouts</h1>
  <span class="w-small w-quiet">{{ this_week }} this week</span>
</div>

''',
         r'''<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
  <h1 class="w-title">Workouts</h1>
  <span class="w-small w-quiet">{{ this_week }} this week{% if week_cal %} · {{ week_cal }} kcal{% endif %}</span>
</div>

'''),
        (r'''  {% for s in recent %}
  <a class="w-row" href="{% url 'wellness:session_detail' s.pk %}">
    <span class="w-row-main"><span class="w-row-name">{{ s.name }}</span><span class="w-row-sub">{{ s.date|date:"D j M" }}{% if s.effort %} · effort {{ s.effort }}/10{% endif %}</span></span>
    <span class="w-quiet">›</span>
  </a>
''',
         r'''  {% for s in recent %}
  <a class="w-row" href="{% url 'wellness:session_detail' s.pk %}">
    <span class="w-row-main"><span class="w-row-name">{{ s.name }}</span><span class="w-row-sub">{{ s.date|date:"D j M" }}{% if s.effort %} · effort {{ s.effort }}/10{% endif %}{% if s.calories %} · {{ s.calories }} kcal{% endif %}</span></span>
    <span class="w-quiet">›</span>
  </a>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'insights.html'), [
        (r'''  <div class="w-ins-bars train">{% for b in i.workouts %}<span title="{{ b.label }}: {{ b.v }}"><b>{{ b.v }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div></section>
{% endif %}
{% if i.weight %}
<section class="w-card" style="gap:6px" data-ins-weight><h2 class="w-h2">Weight trend</h2>
''',
         r'''  <div class="w-ins-bars train">{% for b in i.workouts %}<span title="{{ b.label }}: {{ b.v }}"><b>{{ b.v }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div></section>
{% endif %}
{% if i.kcal %}
<section class="w-card" aria-labelledby="ins-k" data-ins-kcal><h2 class="w-h2" id="ins-k">Workout calories</h2>
  <div class="w-ins-bars train">{% for b in i.kcal %}<span title="{{ b.label }}: {{ b.v }} kcal"><b>{% if b.v %}{{ b.v }}{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: the calories you typed in from your watch.</p></section>
{% endif %}
{% if i.weight %}
<section class="w-card" style="gap:6px" data-ins-weight><h2 class="w-h2">Weight trend</h2>
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
'''),
        (r'''    'test_wellness_thirteen.py',
    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    'test_wellness_fourteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_thirteen.py',
    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    'test_wellness_fourteen.py',
    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    'test_wellness_fifteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    '.bak_wellness14',
]

''',
         r'''    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    '.bak_wellness14',
    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    '.bak_wellness15',
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
    raise SystemExit('WL-11 REFUSED: %s' % msg)


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
    if "'test_wellness_fifteen.py'" in read(pq):
        print('WL-11 already applied.')
        return 0
    if "'test_wellness_fourteen.py'" not in read(pq):
        refuse('Release 57 is not applied - this round registers after it.')
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
        print('WL-11 --check: %d file(s) would change, none written; %d '
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
    print('WL-11 applied - Wellness: calories on a workout.')
    print('      MIGRATION 0010_workout_calories - run migrate after pushing (Railway does it on deploy).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
