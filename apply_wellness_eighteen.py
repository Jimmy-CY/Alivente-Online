# -*- coding: utf-8 -*-
"""apply_wellness_eighteen.py - round WL-14, 2 Nov 2026.

RELEASE 61 - WELLNESS: INSIGHTS WITHOUT EMPTY CHARTS.

    Demetri, 2 Nov 05:18: "if a graph has NO data, should that graph not be
    hidden (like mood in this case)?" 05:19: "Build it".
    - Charts start at the first week with anything in it.
    - A chart with nothing in it is one line saying how to fill it.
    - No "0" over an empty week.

New files ship beside this patcher. Stands on Release 60. Idempotent.
Edits backed up to .bak_wellness18. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness18'
MARK = 'WL-14, 2 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_wellness_eighteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'insights.py'), [
        (r'''PATTERNS, NOT PROOF: the page says so. Only sections switched on are
shown. Everything here is pure; the view gathers the data.
"""
import datetime as dt
''',
         r'''PATTERNS, NOT PROOF: the page says so. Only sections switched on are
shown. Everything here is pure; the view gathers the data.

WL-14, 2 Nov 2026 - Demetri, 05:18: "if a graph has NO data, should that
graph not be hidden (like mood in this case)?" 05:19: "Build it".
    - The charts start at the first week with anything in it, not eight
      weeks back (up to eight as time goes on).
    - A chart with nothing in it at all becomes one line saying how to
      fill it - Mood above all, since the findings need moods.
    - No "0" over an empty week: an empty bar already says it.
"""
import datetime as dt
'''),
        (r'''        })
    return out


''',
         r'''        })
    return out


def has_data(row):
    """Anything at all in this week?"""
    return (row['habits_pct'] is not None or row['mood'] is not None or
            row['calm_min'] > 0 or row['workouts'] > 0 or
            row.get('kcal', 0) > 0)


def trim(rows):
    """From the first week with anything in it (the last week if none)."""
    for i, r in enumerate(rows):
        if has_data(r):
            return rows[i:]
    return rows[-1:]


EMPTY_KEYS = {'habits': 'habits_pct', 'mood': 'mood', 'calm': 'calm_min',
              'workouts': 'workouts'}


def empty(rows):
    """{chart: True} for each chart with nothing in any week."""
    # Habits at 0% is something to see; only "nothing due" is empty.
    return {name: not any((r[key] is not None) if name in ('habits', 'mood')
                          else r[key] for r in rows)
            for name, key in EMPTY_KEYS.items()}


'''),
        (r'''            if c:
                workout_cal[d] = workout_cal.get(d, 0) + c
    rows = weekly(today, mood_by_day, habit_days, calm_secs, workout_days,
                  workout_cal)
    weight = None
    if 'body' in on:
''',
         r'''            if c:
                workout_cal[d] = workout_cal.get(d, 0) + c
    rows = trim(weekly(today, mood_by_day, habit_days, calm_secs,
                       workout_days, workout_cal))
    weight = None
    if 'body' in on:
'''),
        (r'''    return {
        'rows': rows,
        'habits': bars(rows, 'habits_pct', 100) if 'habits' in on else None,
        'calm': bars(rows, 'calm_min') if 'calm' in on else None,
''',
         r'''    return {
        'rows': rows,
        'weeks': len(rows),
        'empty': empty(rows),
        'habits': bars(rows, 'habits_pct', 100) if 'habits' in on else None,
        'calm': bars(rows, 'calm_min') if 'calm' in on else None,
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''    from . import modules as MOD
    on = MOD.on_set(request.user)
    return render(request, 'wellness/insights.html', {
        'tab': 'today', 'on': on,
        'i': INS.gather(request.user, _today(), on),
        'min_days': INS.MIN_DAYS,
    })

''',
         r'''    from . import modules as MOD
    on = MOD.on_set(request.user)
    i = INS.gather(request.user, _today(), on)
    return render(request, 'wellness/insights.html', {
        'tab': 'today', 'on': on, 'i': i,
        'min_days': INS.MIN_DAYS,
        # WL-14 - as many columns as weeks shown.
        'cols': 'grid-template-columns:repeat(%d,minmax(0,1fr))' % i['weeks'],
    })

'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''                   'with your better days.',
        'steps': [
            'Each chart is a week: habits done, mood, Calm minutes, '
            'workouts - and workout calories, once you have typed some in.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
''',
         r'''                   'with your better days.',
        'steps': [
            'Each chart shows one thing week by week: habits done, mood, '
            'Calm minutes, workouts - and workout calories, once you have '
            'typed some in.',
            'The charts start from your first week and grow to eight weeks. '
            'A chart with nothing in it yet says how to fill it.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'Log today and to Patterns.'},
    {'q': 'What is Insights?',
     'a': 'A page with your last eight weeks side by side - habits done, '
          'mood, Calm minutes, workouts, workout calories, your weight trend '
          'and, with the cycle tracker on, mood by phase - and, once '
''',
         r'''          'Log today and to Patterns.'},
    {'q': 'What is Insights?',
     'a': 'A page with up to eight weeks side by side (from your first '
          'week, growing to eight) - habits done, '
          'mood, Calm minutes, workouts, workout calories, your weight trend '
          'and, with the cycle tracker on, mood by phase - and, once '
'''),
        (r'''          'or when you write - most days for a couple of weeks. A finding '
          'appears once there are at least four days on each side and a '
          'real difference. Calories appear once you have typed some in.'},
    # ---- Cycle
    {'q': 'Set up: the cycle tracker',
''',
         r'''          'or when you write - most days for a couple of weeks. A finding '
          'appears once there are at least four days on each side and a '
          'real difference. Calories appear once you have typed some in. A '
          'chart with nothing in it yet shows one line saying how to fill '
          'it.'},
    # ---- Cycle
    {'q': 'Set up: the cycle tracker',
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'insights.html'), [
        (r'''<div>
  <h1 class="w-title">Insights</h1>
  <p class="w-quiet" style="margin:6px 0 0">Your last eight weeks, side by side.</p>
</div>

''',
         r'''<div>
  <h1 class="w-title">Insights</h1>
  <p class="w-quiet" style="margin:6px 0 0">{% if i.weeks < 8 %}Week by week since you started - up to eight weeks, side by side.{% else %}Your last eight weeks, side by side.{% endif %}</p>
</div>

'''),
        (r'''
{% if i.habits %}
<section class="w-card" aria-labelledby="ins-h"><h2 class="w-h2" id="ins-h">Habits done</h2>
  <div class="w-ins-bars">{% for b in i.habits %}<span title="{{ b.label }}: {% if b.v is not None %}{{ b.v }}%{% else %}none due{% endif %}"><b>{% if b.v is not None %}{{ b.v }}%{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: the share of planned days done.</p></section>
{% endif %}
{% if i.mood %}
<section class="w-card" aria-labelledby="ins-m"><h2 class="w-h2" id="ins-m">Mood</h2>
  <div class="w-ins-bars mood">{% for b in i.mood %}<span title="{{ b.label }}: {{ b.v|default:'no moods' }}"><b>{{ b.v|default:'' }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: your average mood, 1 to 5, from the journal.</p></section>
{% endif %}
{% if i.calm %}
<section class="w-card" aria-labelledby="ins-c"><h2 class="w-h2" id="ins-c">Calm minutes</h2>
  <div class="w-ins-bars calm">{% for b in i.calm %}<span title="{{ b.label }}: {{ b.v }} min"><b>{{ b.v }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div></section>
{% endif %}
{% if i.workouts %}
<section class="w-card" aria-labelledby="ins-w"><h2 class="w-h2" id="ins-w">Workouts</h2>
  <div class="w-ins-bars train">{% for b in i.workouts %}<span title="{{ b.label }}: {{ b.v }}"><b>{{ b.v }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div></section>
{% endif %}
{% if i.kcal %}
<section class="w-card" aria-labelledby="ins-k" data-ins-kcal><h2 class="w-h2" id="ins-k">Workout calories</h2>
  <div class="w-ins-bars train">{% for b in i.kcal %}<span title="{{ b.label }}: {{ b.v }} kcal"><b>{% if b.v %}{{ b.v }}{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: the calories you typed in from your watch.</p></section>
{% endif %}
''',
         r'''
{% if i.habits %}
{% comment %} WL-14, 2 Nov 2026 - a chart with nothing in it is one line saying how to fill it. {% endcomment %}
<section class="w-card" aria-labelledby="ins-h"><h2 class="w-h2" id="ins-h">Habits done</h2>
  {% if i.empty.habits %}<p class="w-quiet" style="margin:0" data-ins-empty>No habits due in these weeks yet. Add one under Habits and it appears here.</p>{% else %}
  <div class="w-ins-bars" style="{{ cols }}">{% for b in i.habits %}<span title="{{ b.label }}: {% if b.v is not None %}{{ b.v }}%{% else %}none due{% endif %}"><b>{% if b.v is not None %}{{ b.v }}%{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: the share of planned days done.</p>{% endif %}</section>
{% endif %}
{% if i.mood %}
<section class="w-card" aria-labelledby="ins-m"><h2 class="w-h2" id="ins-m">Mood</h2>
  {% if i.empty.mood %}<p class="w-quiet" style="margin:0" data-ins-empty>No moods yet. Add one in the evening check-in, or when you write, and it appears here - and What goes with what can start.</p>{% else %}
  <div class="w-ins-bars mood" style="{{ cols }}">{% for b in i.mood %}<span title="{{ b.label }}: {{ b.v|default:'no moods' }}"><b>{{ b.v|default:'' }}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: your average mood, 1 to 5, from the journal.</p>{% endif %}</section>
{% endif %}
{% if i.calm %}
<section class="w-card" aria-labelledby="ins-c"><h2 class="w-h2" id="ins-c">Calm minutes</h2>
  {% if i.empty.calm %}<p class="w-quiet" style="margin:0" data-ins-empty>No Calm minutes yet. A minute of Breathe is enough to start.</p>{% else %}
  <div class="w-ins-bars calm" style="{{ cols }}">{% for b in i.calm %}<span title="{{ b.label }}: {{ b.v }} min"><b>{% if b.v %}{{ b.v }}{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>{% endif %}</section>
{% endif %}
{% if i.workouts %}
<section class="w-card" aria-labelledby="ins-w"><h2 class="w-h2" id="ins-w">Workouts</h2>
  {% if i.empty.workouts %}<p class="w-quiet" style="margin:0" data-ins-empty>No workouts yet. Finish one and it appears here.</p>{% else %}
  <div class="w-ins-bars train" style="{{ cols }}">{% for b in i.workouts %}<span title="{{ b.label }}: {{ b.v }}"><b>{% if b.v %}{{ b.v }}{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>{% endif %}</section>
{% endif %}
{% if i.kcal %}
<section class="w-card" aria-labelledby="ins-k" data-ins-kcal><h2 class="w-h2" id="ins-k">Workout calories</h2>
  <div class="w-ins-bars train" style="{{ cols }}">{% for b in i.kcal %}<span title="{{ b.label }}: {{ b.v }} kcal"><b>{% if b.v %}{{ b.v }}{% endif %}</b><em><i style="height:{{ b.h }}%"></i></em><small>{{ b.label }}</small></span>{% endfor %}</div>
  <p class="w-small w-quiet" style="margin:0">Each week: the calories you typed in from your watch.</p></section>
{% endif %}
'''),
    ]),
    (os.path.join('test_wellness_fourteen.py'), [
        (r'''               'THE CYCLE PAGE shows the note above the ideas')
            ins = ca.get('/wellness/insights/').content.decode()
            ok('Your last eight weeks' in ins and 'w-ins-bars' in ins and
               '<h3 class="w-sheet-title">Insights</h3>' in ins,
               'INSIGHTS opens, with its charts and its help')
''',
         r'''               'THE CYCLE PAGE shows the note above the ideas')
            ins = ca.get('/wellness/insights/').content.decode()
            # WL-14, 2 Nov 2026: from the first week with data, and an
            # empty chart is one line (test_wellness_eighteen).
            ok(('Your last eight weeks' in ins or
                'Week by week since you started' in ins) and
               ('w-ins-bars' in ins or 'data-ins-empty' in ins) and
               '<h3 class="w-sheet-title">Insights</h3>' in ins,
               'INSIGHTS opens, with its charts and its help')
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/guide.py'; Text = 'def grouped('; What = 'WL-13: the guide questions are on disk in their topics - without them the help sheet on every Wellness page fails' },
    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/insights.py'; Text = 'def trim('; What = 'WL-14: Insights starts at your first week and drops empty charts - without it the Insights page cannot open' },
    @{ File = 'wellness/guide.py'; Text = 'def grouped('; What = 'WL-13: the guide questions are on disk in their topics - without them the help sheet on every Wellness page fails' },
    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
'''),
        (r'''    'test_wellness_sixteen.py',
    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    'test_wellness_seventeen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_sixteen.py',
    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    'test_wellness_seventeen.py',
    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    'test_wellness_eighteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    '.bak_wellness17',
]

''',
         r'''    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    '.bak_wellness17',
    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    '.bak_wellness18',
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
    raise SystemExit('WL-14 REFUSED: %s' % msg)


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
    if "'test_wellness_eighteen.py'" in read(pq):
        print('WL-14 already applied.')
        return 0
    if "'test_wellness_seventeen.py'" not in read(pq):
        refuse('Release 60 is not applied - this round registers after it.')
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
        print('WL-14 --check: %d file(s) would change, none written; %d '
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
    print('WL-14 applied - Wellness: Insights without empty charts.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
