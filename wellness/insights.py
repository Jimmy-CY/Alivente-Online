# -*- coding: utf-8 -*-
"""wellness/insights.py - WL-10, 1 Nov 2026. Insights.

Demetri, 1 Nov 05:43, after comparing Wellness with other wellness apps:
"can we add an Insights section/area" (sleep comes from the watch, so not
here for now).

One page that puts the sections side by side over the last eight weeks
and says, carefully, what goes with what:

    - week by week: habits done, Calm minutes, workouts, mood, and
      (WL-11) the calories typed in for workouts, once there are any;
    - the weight trend over the eight weeks;
    - findings such as "On days you did Calm, your mood averaged 3.9,
      against 3.4 on other days" - only with enough days on both sides
      and a difference worth mentioning;
    - with the cycle tracker on and moods logged: mood by cycle phase.

PATTERNS, NOT PROOF: the page says so. Only sections switched on are
shown. Everything here is pure; the view gathers the data.
"""
import datetime as dt

WEEKS = 8
# A finding needs this many days on each side, and this big a difference.
MIN_DAYS = 4
MIN_DIFF = 0.3
MOOD_WORDS = {1: 'low', 2: 'a bit low', 3: 'okay', 4: 'good', 5: 'great'}


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def week_starts(today, n=WEEKS):
    m = monday(today)
    return [m - dt.timedelta(days=7 * i) for i in range(n - 1, -1, -1)]


def avg(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / float(len(xs))) if xs else None


def compare(mood_by_day, flag_days, what):
    """A finding about mood on days with `what` against days without, or
    None when there is not enough to say."""
    with_ = [m for d, m in mood_by_day.items() if d in flag_days]
    without = [m for d, m in mood_by_day.items() if d not in flag_days]
    if len(with_) < MIN_DAYS or len(without) < MIN_DAYS:
        return None
    a, b = avg(with_), avg(without)
    if abs(a - b) < MIN_DIFF:
        return None
    return {'what': what, 'with': round(a, 1), 'without': round(b, 1),
            'n_with': len(with_), 'n_without': len(without),
            'words': 'On days %s, your mood averaged %.1f, against %.1f on '
                     'other days.' % (what, a, b),
            'up': a > b}


def weekly(today, mood_by_day, habit_days, calm_secs, workout_days,
           workout_cal=None):
    """Rows per week, oldest first. habit_days: date -> (done, due)."""
    out = []
    for m in week_starts(today):
        days = [m + dt.timedelta(days=i) for i in range(7)
                if m + dt.timedelta(days=i) <= today]
        done = sum(habit_days.get(d, (0, 0))[0] for d in days)
        due = sum(habit_days.get(d, (0, 0))[1] for d in days)
        moods = [mood_by_day[d] for d in days if d in mood_by_day]
        out.append({
            'monday': m,
            'label': '%d %s' % (m.day, m.strftime('%b')),
            'habits_pct': int(round(100.0 * done / due)) if due else None,
            'calm_min': sum(calm_secs.get(d, 0) for d in days) // 60,
            'workouts': sum(1 for d in days if d in workout_days),
            'kcal': sum((workout_cal or {}).get(d, 0) for d in days),
            'mood': round(avg(moods), 1) if moods else None,
        })
    return out


def bars(rows, key, top=None):
    """Heights 0..100 for a little bar chart of one measure."""
    vals = [r[key] for r in rows]
    hi = top or max([v for v in vals if v is not None] or [0]) or 1
    return [{'v': v, 'h': int(round(100.0 * (v or 0) / hi)) if v else 0,
             'label': r['label']} for v, r in zip(vals, rows)]


def findings(mood_by_day, habit_days, calm_days, workout_days, on):
    """The careful sentences, strongest difference first."""
    out = []
    if 'calm' in on:
        out.append(compare(mood_by_day, calm_days, 'you did Calm'))
    if 'workouts' in on:
        out.append(compare(mood_by_day, workout_days, 'you trained'))
    if 'habits' in on:
        good = {d for d, (done, due) in habit_days.items()
                if due and done * 2 >= due}
        out.append(compare(mood_by_day, good,
                           'you did at least half your habits'))
    out = [f for f in out if f]
    out.sort(key=lambda f: -abs(f['with'] - f['without']))
    return out


def mood_by_phase(mood_by_day, starts, cycle_len, period_len):
    """[(phase name, average, days)] for phases with three or more moods.
    starts: the period start dates, oldest first."""
    from . import phases as PH
    got = {}
    for d, m in mood_by_day.items():
        before = [s for s in starts if s <= d]
        if not before:
            continue
        n = (d - before[-1]).days + 1
        if n > cycle_len + 7:
            continue
        key = 'luteal' if n > cycle_len else PH.phase_on(n, cycle_len,
                                                         period_len)
        got.setdefault(key, []).append(m)
    out = []
    for k, name, _w in PH.PHASES:
        if len(got.get(k, [])) >= 3:
            out.append((name, round(avg(got[k]), 1), len(got[k])))
    return out


# --------------------------------------------------------------------------
# The database side
# --------------------------------------------------------------------------
def gather(user, today, on):
    """Everything the page shows, for the sections switched on."""
    from . import body as B
    from . import cycle as CY
    from . import habits as H
    from .models import (BodyMetric, CalmSession, Habit, JournalEntry,
                         WorkoutSession)
    since = week_starts(today)[0]
    mood_by_day = {}
    if 'journal' in on:
        per = {}
        for d, m in JournalEntry.objects.filter(
                user=user, date__gte=since, date__lte=today,
                mood__isnull=False).values_list('date', 'mood'):
            per.setdefault(d, []).append(m)
        mood_by_day = {d: avg(ms) for d, ms in per.items()}
    habit_days = {}
    if 'habits' in on:
        for h in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False):
            if H.is_flexible(h):
                continue
            done = set(h.logs.filter(done=True, date__gte=since)
                       .values_list('date', flat=True))
            d = max(since, h.started_on)
            while d <= today:
                if H.scheduled(h, d):
                    a, b = habit_days.get(d, (0, 0))
                    habit_days[d] = (a + (1 if d in done else 0), b + 1)
                d += dt.timedelta(days=1)
    calm_secs = {}
    if 'calm' in on:
        for d, s in CalmSession.objects.filter(
                user=user, date__gte=since).values_list('date', 'seconds'):
            calm_secs[d] = calm_secs.get(d, 0) + s
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
        readings = {m.date: float(m.value) for m in BodyMetric.objects.filter(
            user=user, kind='weight')}
        tr = B.trend(readings) if readings else {}
        inside = sorted(d for d in tr if d >= since)
        if len(inside) >= 2:
            change = tr[inside[-1]] - tr[inside[0]]
            weight = {'start': B.kg(tr[inside[0]]), 'end': B.kg(tr[inside[-1]]),
                      'change': B.kg(abs(change)),
                      'dir': 'down' if change < -0.05 else
                      'up' if change > 0.05 else 'steady'}
    phase_moods = []
    if 'cycle' in on and mood_by_day:
        _r, prefs, days = CY.load(user)
        if not prefs.get('locked') and prefs.get('mode') == 'normal':
            s = CY.summary(days, today, prefs)
            if s.get('avg_cycle'):
                starts = [c['start'] for c in s['cycles']]
                phase_moods = mood_by_phase(mood_by_day, starts,
                                            s['avg_cycle'],
                                            s.get('avg_period') or 5)
    return {
        'rows': rows,
        'habits': bars(rows, 'habits_pct', 100) if 'habits' in on else None,
        'calm': bars(rows, 'calm_min') if 'calm' in on else None,
        'workouts': bars(rows, 'workouts') if 'workouts' in on else None,
        'kcal': bars(rows, 'kcal') if workout_cal else None,
        'mood': bars(rows, 'mood', 5) if 'journal' in on else None,
        'findings': findings(mood_by_day, habit_days, set(calm_secs),
                             workout_days, on),
        'weight': weight,
        'phase_moods': phase_moods,
        'mood_days': len(mood_by_day),
    }
