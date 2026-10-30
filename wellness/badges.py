# -*- coding: utf-8 -*-
"""wellness/badges.py - WL-4a, 30 Oct 2026. Quiet milestones.

From the proposal and the approved Badges screen (canvas, row 1): a badge
marks something done, never something missed. No badge is ever taken
away - once earned it is kept, with the day it was earned, in the
profile's prefs. There is nothing to lose and no countdown.

The cycle tracker has NO badges and no streaks (approved design, 30 Oct):
nothing here reads it.

`facts()` asks the database once per page; `earned()` and `up_next()` are
pure, so the suite drives them without one.
"""
import datetime as dt

# (key, mark, name, the line shown when it is new, test, progress)
# progress(f) -> (have, need, unit) for "Up next", or None.
BADGES = [
    ('first_step', '1', 'First step', 'Your first tick. Every habit starts '
     'with one.', lambda f: f['ticks'] >= 1, lambda f: None),
    ('week_1', '1w', 'A good week', 'A whole week met. That is how habits '
     'take root.', lambda f: f['streak'] >= 1, lambda f: (f['streak'], 1,
                                                           'week')),
    ('weeks_4', '4w', 'Four good weeks', 'Four weeks in a row. This is '
     'becoming who you are.', lambda f: f['streak'] >= 4,
     lambda f: (f['streak'], 4, 'week')),
    ('weeks_12', '12w', 'Twelve good weeks', 'Twelve weeks in a row - '
     'a season of showing up.', lambda f: f['streak'] >= 12,
     lambda f: (f['streak'], 12, 'week')),
    ('comeback', '↺', 'Comeback', 'You came back after a quiet spell. '
     'That counts more than a perfect run.', lambda f: f['comebacks'] >= 1,
     lambda f: None),
    ('established', '66', 'Established', 'A habit that is part of your '
     'days now.', lambda f: f['established'] >= 1,
     lambda f: (f['habit_days'], 66, 'day')),
    ('ticks_100', '100', '100 ticks', 'A hundred small things done.',
     lambda f: f['ticks'] >= 100, lambda f: (f['ticks'], 100, 'tick')),
    ('entry_1', '✎', 'First entry', 'Your first journal entry.',
     lambda f: f['entries'] >= 1, lambda f: None),
    ('entries_10', '10', '10 entries', 'Ten entries in your journal.',
     lambda f: f['entries'] >= 10, lambda f: (f['entries'], 10, 'entry')),
    ('entries_50', '50', '50 entries', 'Fifty entries - a real record of '
     'your days.', lambda f: f['entries'] >= 50,
     lambda f: (f['entries'], 50, 'entry')),
    ('checkins_30', '30', '30 check-ins', 'Thirty evening check-ins.',
     lambda f: f['checkins'] >= 30, lambda f: (f['checkins'], 30,
                                               'check-in')),
    ('checkins_100', '100', '100 check-ins', 'A hundred evenings looked '
     'back on.', lambda f: f['checkins'] >= 100,
     lambda f: (f['checkins'], 100, 'check-in')),
    ('weigh_1', 'kg', 'First weigh-in', 'Your first weigh-in. The trend '
     'starts here.', lambda f: f['weighins'] >= 1, lambda f: None),
    ('weigh_30', '30', '30 weigh-ins', 'Thirty weigh-ins - enough for a '
     'trend you can trust.', lambda f: f['weighins'] >= 30,
     lambda f: (f['weighins'], 30, 'weigh-in')),
    ('halfway', '½', 'Halfway', 'Halfway to your goal weight.',
     lambda f: (f['progress'] or 0) >= 0.5,
     lambda f: (round(f['kg_done'], 1), round(f['kg_half'], 1), 'kg')
     if f['kg_half'] else None),
    ('goal', '★', 'Goal reached', 'You reached the goal you set.',
     lambda f: (f['progress'] or 0) >= 1.0,
     lambda f: (round(f['kg_done'], 1), round(f['kg_total'], 1), 'kg')
     if f['kg_total'] else None),
    ('session_1', '1', 'First workout', 'Your first workout logged.',
     lambda f: f['sessions'] >= 1, lambda f: None),
    ('sessions_10', '10', '10 workouts', 'Ten workouts done.',
     lambda f: f['sessions'] >= 10, lambda f: (f['sessions'], 10,
                                               'workout')),
    ('sessions_25', '25', '25 workouts', 'Twenty-five workouts. Strong.',
     lambda f: f['sessions'] >= 25, lambda f: (f['sessions'], 25,
                                               'workout')),
    ('sessions_50', '50', '50 workouts', 'Fifty workouts - this is a '
     'habit now.', lambda f: f['sessions'] >= 50,
     lambda f: (f['sessions'], 50, 'workout')),
    ('record_1', 'PR', 'First record', 'Your first personal record.',
     lambda f: f['records'] >= 1, lambda f: None),
    ('records_10', '10', '10 records', 'Ten personal records.',
     lambda f: f['records'] >= 10, lambda f: (f['records'], 10, 'record')),
]
KEYS = [b[0] for b in BADGES]
BY_KEY = {b[0]: b for b in BADGES}
# The colour family of each mark: habits sage, journal slate, body and
# workouts sand - as on the approved screen.
FAMILY = {}
for _k in KEYS:
    if _k.startswith(('entry', 'entries', 'checkins')):
        FAMILY[_k] = 'slate'
    elif _k.startswith(('weigh', 'halfway', 'goal', 'record', 'comeback')):
        FAMILY[_k] = 'sand'
    else:
        FAMILY[_k] = 'sage'

EMPTY = {'ticks': 0, 'streak': 0, 'comebacks': 0, 'established': 0,
         'habit_days': 0, 'entries': 0, 'checkins': 0, 'weighins': 0,
         'progress': None, 'kg_done': 0.0, 'kg_half': 0.0, 'kg_total': 0.0,
         'sessions': 0, 'records': 0}


def earned(f):
    """The keys whose test passes on these facts, in list order."""
    return [k for k, _m, _n, _l, test, _p in BADGES if test(f)]


def _plural(n, unit):
    if n == 1:
        return unit
    if unit.endswith('y') and unit != 'day':
        return unit[:-1] + 'ies'
    return unit + 's'


def up_next(f, have, n=3):
    """The closest few not yet earned that can show progress."""
    out = []
    for k, mark, name, _l, _t, prog in BADGES:
        if k in have:
            continue
        p = prog(f)
        if not p:
            continue
        got, need, unit = p
        if got >= need:
            # Reached but waiting on the person (an established habit is
            # confirmed on its page) - not a countdown to show.
            continue
        if unit == 'kg':
            left = max(0.0, need - got)
            words = '%s kg to go' % (('%.1f' % left).rstrip('0').rstrip('.'))
        else:
            left = max(0, need - got)
            words = '%d %s to go' % (left, _plural(left, unit))
        frac = (float(got) / need) if need else 0
        out.append((frac, {'key': k, 'mark': mark, 'name': name,
                           'need': words}))
    out.sort(key=lambda t: -t[0])
    return [d for _f, d in out[:n]]


# --------------------------------------------------------------------------
# The database side
# --------------------------------------------------------------------------
def facts(user, today):
    from . import body as B
    from . import habits as H
    from .models import (BodyMetric, Habit, HabitLog, JournalEntry,
                         WellnessProfile, WorkoutSession, WorkoutSet)
    f = dict(EMPTY)
    f['ticks'] = HabitLog.objects.filter(habit__user=user, done=True).count()
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
        if not done:
            continue
        f['streak'] = max(f['streak'], H.week_streak(habit, done, today))
        if H.comebacks(habit, done, today):
            f['comebacks'] += 1
        if habit.established_at:
            f['established'] += 1
        else:
            f['habit_days'] = max(f['habit_days'],
                                  (today - habit.started_on).days + 1)
    entries = JournalEntry.objects.filter(user=user)
    f['entries'] = entries.count()
    f['checkins'] = entries.filter(kind='checkin').count()
    readings = {m.date: float(m.value) for m in
                BodyMetric.objects.filter(user=user, kind='weight')}
    f['weighins'] = len(readings)
    prof = WellnessProfile.objects.filter(user=user).first()
    tr = B.trend(readings) if readings else {}
    if tr and prof and prof.weight_goal:
        start, current = tr[min(tr)], tr[max(tr)]
        goal = float(prof.weight_goal)
        f['progress'] = B.progress(start, current, goal)
        f['kg_total'] = abs(goal - start)
        f['kg_half'] = f['kg_total'] / 2.0
        f['kg_done'] = abs(current - start) if f['progress'] else 0.0
    f['sessions'] = WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False).count()
    f['records'] = WorkoutSet.objects.filter(
        session__user=user, is_pr=True, done=True).count()
    return f


def update(profile, f, today):
    """Keep every badge ever earned, with its day. Returns the new ones
    (earned now, not seen yet), in list order. Saves only on a change."""
    prefs = dict(profile.prefs or {})
    kept = dict(prefs.get('badges') or {})
    changed = False
    for k in earned(f):
        if k not in kept:
            kept[k] = today.isoformat()
            changed = True
    if changed:
        prefs['badges'] = kept
        profile.prefs = prefs
        profile.save(update_fields=['prefs', 'updated_at'])
    seen = set(prefs.get('badges_seen') or [])
    return [k for k in KEYS if k in kept and k not in seen]


def mark_seen(profile):
    prefs = dict(profile.prefs or {})
    prefs['badges_seen'] = sorted(set(prefs.get('badges_seen') or []) |
                                  set((prefs.get('badges') or {}).keys()))
    profile.prefs = prefs
    profile.save(update_fields=['prefs', 'updated_at'])


def earned_between(profile, since, until):
    """Badges kept with a day from `since` to `until` - the weekly email's
    week, so a badge is reported once and only once."""
    kept = (profile.prefs or {}).get('badges') or {}
    out = []
    for k in KEYS:
        d = kept.get(k)
        if d and since <= dt.date.fromisoformat(d) <= until:
            out.append(BY_KEY[k][2])
    return out
