# -*- coding: utf-8 -*-
"""apply_wellness_sixteen.py - round WL-12, 1 Nov 2026.

RELEASE 59 - WELLNESS: WEEKLY CHALLENGES, THREE MARKS, EARLIER AMOUNTS.

    Demetri, 1 Nov 12:13-12:27:
    - Weekly challenges for times a week and chosen days: 4, 6, 8 or 12
      weeks or your own; every day stays in days. Choosing a challenge no
      longer turns a habit into an every-day one.
    - Three marks: Done, Missed, Rest. The first two missed days a month
      are still forgiven and never spoil a streak; the help says so.
    - Tap any of the last seven days to enter its minutes or count.

New files ship beside this patcher. Stands on Release 58. Idempotent.
Edits backed up to .bak_wellness16. MIGRATION 0011_weekly_challenges.
"""
import os
import sys

SUFFIX = '.bak_wellness16'
MARK = 'WL-12, 1 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/migrations/0011_weekly_challenges.py',
    'test_wellness_sixteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''    # For SCHEDULE_PER_WEEK: how many times in a Monday-to-Sunday week.
    per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    time_of_day = models.CharField(max_length=10, choices=TIMES,
                                   default='anytime')
''',
         r'''    # For SCHEDULE_PER_WEEK: how many times in a Monday-to-Sunday week.
    per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    # WL-12, 1 Nov 2026: a challenge counts days (every day) or weeks
    # (times a week, chosen days). See challenge.py.
    challenge_unit = models.CharField(max_length=4, default='day',
                                      blank=True)
    time_of_day = models.CharField(max_length=10, choices=TIMES,
                                   default='anytime')
'''),
    ]),
    (os.path.join('wellness', 'challenge.py'), [
        (r'''
All of it is pure here, given the habit and its done dates; the views save.
"""
import datetime as dt
''',
         r'''
All of it is pure here, given the habit and its done dates; the views save.

WEEKLY CHALLENGES - WL-12, 1 Nov 2026. Demetri, 12:13: "If I create a Habit
to Run 4 times a week for 30 minutes a time... The challenge should almost
be a weekly challenge. i.e. 8 week challenge, where I do 4 times running a
week for 30 minutes. We should be able to customise. If my challenge is
daily, then we go with what we have now." 12:20: weeks for "times a week"
and chosen days; 4, 6, 8 or 12 weeks or your own number.

    - The challenge follows the habit: every day counts DAYS (as before);
      times a week and chosen days count WEEKS (challenge_unit 'week').
    - Weeks run Monday to Sunday. A week is met when it has the habit's
      number of done days (times a week), or every chosen day done or
      forgiven (chosen days). A first week begun mid-week asks for its
      share: 4 a week begun on a Thursday asks for 2.
    - "Week 3 of 8 · 2 of 4 this week". One square per week, filling as
      the week fills.
    - A week that ends short asks, once: Carry on (the finish moves out a
      week) or Start again (week 1 is this week, from today).
    - Before WL-12 choosing a challenge silently turned the habit into an
      every-day one. It no longer does.
"""
import datetime as dt
'''),
        (r'''# Misses in a row before "Pause it for now" is offered too.
PAUSE_AFTER = 3

# Starters on the new-habit screen: (name, preset).
''',
         r'''# Misses in a row before "Pause it for now" is offered too.
PAUSE_AFTER = 3

# WL-12 - weekly challenges.
WEEKS = [4, 6, 8, 12]
OWN_W_MIN, OWN_W_MAX = 2, 52
SEVEN = dt.timedelta(days=7)
# Short weeks in a row before "Pause it for now" is offered too.
PAUSE_AFTER_WEEKS = 2

# Starters on the new-habit screen: (name, preset).
'''),
        (r'''    if not has(habit):
        return None
    total, start = habit.challenge_days, habit.challenge_from
    got_days = sorted(d for d in done if start <= d <= today)
''',
         r'''    if not has(habit):
        return None
    if is_weekly(habit):
        return week_state(habit, done, today)
    total, start = habit.challenge_days, habit.challenge_from
    got_days = sorted(d for d in done if start <= d <= today)
'''),
        (r'''    else:
        words = 'Day %d of %d' % (day, total)
    return {'days': total, 'got': min(got, total), 'day': day,
            'pct': int(round(100.0 * min(got, total) / total)),
            'today_done': today_done, 'finished': finished,
''',
         r'''    else:
        words = 'Day %d of %d' % (day, total)
    return {'unit': 'day', 'days': total, 'got': min(got, total), 'day': day,
            'pct': int(round(100.0 * min(got, total) / total)),
            'today_done': today_done, 'finished': finished,
'''),
        (r'''

def ask_words(ask, today, in_a_row):
    if not ask:
''',
         r'''

# --------------------------------------------------------------------------
# WL-12 - weekly challenges
# --------------------------------------------------------------------------
def valid_weeks(n):
    """A number of weeks a weekly challenge may have."""
    return n in WEEKS or OWN_W_MIN <= n <= OWN_W_MAX


def unit_for(habit):
    """'day' for an every-day habit, 'week' for times a week or chosen
    days."""
    return 'day' if habit.schedule == 'daily' else 'week'


def is_weekly(habit):
    return getattr(habit, 'challenge_unit', 'day') == 'week'


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def week_target(habit, week_start, start):
    """What meets the week starting week_start, for a challenge begun on
    `start`: times a week - the number, or the days left if fewer;
    chosen days - each chosen day from `start` on."""
    first = max(week_start, start)
    last = week_start + dt.timedelta(days=6)
    if first > last:
        return 0
    if habit.schedule == 'weekdays':
        chosen = habit.weekday_set()
        n, d = 0, first
        while d <= last:
            if d.weekday() in chosen:
                n += 1
            d += ONE
        return n
    # A first week begun mid-week asks for its share of the number:
    # 4 a week begun on a Thursday (4 days left) asks for 2.
    per, avail = habit.per_week or 1, (last - first).days + 1
    if avail >= 7:
        return per
    return max(1, min(avail, int(per * avail / 7.0 + 0.5)))


def week_got(habit, done, week_start, start, today, states=None):
    """Done days counted in the week (up to today). Chosen days: the
    chosen days done or forgiven; times a week: any done day."""
    first = max(week_start, start)
    last = min(week_start + dt.timedelta(days=6), today)
    if habit.schedule == 'weekdays':
        chosen = habit.weekday_set()
        n, d = 0, first
        while d <= last:
            if d.weekday() in chosen and (
                    d in done or (states or {}).get(d) == 'grace'):
                n += 1
            d += ONE
        return n
    return sum(1 for d in done if first <= d <= last)


def nice_week(w):
    return 'the week of %d %s' % (w.day, w.strftime('%b'))


def week_state(habit, done, today):
    """The weekly challenge: the same keys as state(), in weeks."""
    total, start = habit.challenge_days, habit.challenge_from
    states = None
    if habit.schedule == 'weekdays':
        from . import habits as H
        states = H.day_states(habit, done, today)
    weeks, w = [], monday(start)
    good = 0
    finished = habit.challenge_done_on
    this_w = monday(today)
    while w <= this_w:
        target = week_target(habit, w, start)
        if target:
            got = week_got(habit, done, w, start, today, states)
            ended = w + dt.timedelta(days=6) < today
            met = got >= target
            weeks.append({'monday': w, 'target': target, 'got': got,
                          'met': met, 'ended': ended})
            if met and not finished:
                good += 1
                if good >= total:
                    last = min(w + dt.timedelta(days=6), today)
                    hit = sorted(d for d in done
                                 if max(w, start) <= d <= last)
                    finished = hit[-1] if hit else last
        w += SEVEN
    short = [x for x in weeks if x['ended'] and not x['met']]
    now = weeks[-1] if weeks and weeks[-1]['monday'] == this_w else None
    now_met = bool(now and now['met'])
    left = max(0, total - good)
    # The finish if every week from now on is met: the Sunday of the last.
    if finished:
        finish = finished
    elif left:
        first_open = this_w if not now_met else this_w + SEVEN
        finish = first_open + SEVEN * (left - 1) + dt.timedelta(days=6)
    else:
        finish = today
    in_a_row = 0
    for x in reversed([x for x in weeks if x['ended']]):
        if x['met']:
            break
        in_a_row += 1
    seen = habit.challenge_seen or (start - ONE)
    ask = None
    if short and not finished:
        end = short[-1]['monday'] + dt.timedelta(days=6)
        if end > seen:
            ask = short[-1]['monday']
    week_no = min(total, good + (0 if now_met else 1))
    strip = []
    for i in range(total):
        if i < good:
            strip.append({'cls': 'done', 'pct': 100})
        elif i == good and now and not now_met and not finished:
            pct = int(round(100.0 * now['got'] / now['target']))
            strip.append({'cls': 'now', 'pct': pct})
        else:
            strip.append({'cls': 'todo', 'pct': 0})
    if finished:
        words = 'Finished: %d weeks.' % total
    else:
        words = 'Week %d of %d' % (week_no, total)
    this_words = ''
    if now and not finished:
        noun = 'day' if habit.schedule == 'weekdays' else ''
        this_words = '%d of %d%s this week' % (
            now['got'], now['target'],
            (' %s%s' % (noun, '' if now['target'] == 1 else 's'))
            if noun else '')
    if ask:
        ask_text = ('A few weeks fell short. That happens.' if in_a_row >= 2
                    else ('Last week fell short. That happens.'
                          if ask == this_w - SEVEN else
                          '%s fell short. That happens.'
                          % nice_week(ask).capitalize()))
    else:
        ask_text = ''
    return {'unit': 'week', 'days': total, 'got': min(good, total),
            'day': week_no,
            'pct': int(round(100.0 * min(good, total) / total)),
            'today_done': today in done, 'finished': finished,
            'misses': len(short), 'finish': finish,
            'finish_words': nice_date(finish),
            'ask': ask, 'ask_words': ask_text, 'in_a_row': in_a_row,
            'can_pause': bool(ask) and in_a_row >= PAUSE_AFTER_WEEKS,
            'strip': strip, 'rows': week_rows(strip), 'words': words,
            'this_words': this_words}


def week_rows(strip):
    """One square per week, at most 13 to a row."""
    if len(strip) <= 13:
        return [strip]
    return [strip[i:i + 13] for i in range(0, len(strip), 13)]


def ask_words(ask, today, in_a_row):
    if not ask:
'''),
        (r'''

def begin(habit, days, today):
    habit.challenge_days = days
    habit.challenge_from = today
    habit.challenge_seen = None
    habit.challenge_done_on = None


def clear(habit):
    habit.challenge_days = None
    habit.challenge_from = None
''',
         r'''

def begin(habit, days, today, unit='day'):
    habit.challenge_days = days
    habit.challenge_unit = unit
    habit.challenge_from = today
    habit.challenge_seen = None
    habit.challenge_done_on = None


def clear(habit):
    habit.challenge_unit = 'day'
    habit.challenge_days = None
    habit.challenge_from = None
'''),
        (r'''    kept = list(prefs.get('challenges') or [])
    kept.append({'name': habit.name, 'days': habit.challenge_days,
                 'on': s['finished'].isoformat()})
    prefs['challenges'] = kept[-200:]
    profile.prefs = prefs
''',
         r'''    kept = list(prefs.get('challenges') or [])
    kept.append({'name': habit.name, 'days': habit.challenge_days,
                 'unit': s['unit'], 'on': s['finished'].isoformat()})
    prefs['challenges'] = kept[-200:]
    profile.prefs = prefs
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''PERM = 'auth.can_access_wellness'
BACKFILL_DAYS = 7
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
ASSET_TYPES = {
''',
         r'''PERM = 'auth.can_access_wellness'
BACKFILL_DAYS = 7
# WL-12, 1 Nov 2026 - Demetri, 12:24: "I would prefer to just have 3: Done,
# Missed and Rest". A forgiven day is still forgiven behind the scenes (the
# first two missed days a month never spoil a streak) but shows as Missed;
# the comeback colour went.
SHOWN = {'grace': 'miss'}
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
ASSET_TYPES = {
'''),
        (r'''            'num': d.day,
            'state': ('before' if d < habit.started_on
                      else states.get(d, 'rest')),
            'value': values.get(d),
        })
    streak = H.week_streak(habit, done, day)
    if got >= target and target:
''',
         r'''            'num': d.day,
            'state': ('before' if d < habit.started_on
                      else SHOWN.get(states.get(d, 'rest'),
                                     states.get(d, 'rest'))),
            'value': values.get(d),
        })
    # WL-12 - Demetri, 12:13: "Why am I only able to enter the minutes for
    # Today, but not for a previous day?" Tap a day of the seven and the
    # box below is for that day.
    entry = week[-1]
    want = request.GET.get('day') or ''
    for w in week:
        if w['iso'] == want:
            entry = w
    streak = H.week_streak(habit, done, day)
    if got >= target and target:
'''),
        (r'''        'week_words': week_words,
        'week': week,
        'calendar': H.calendar(habit, done, day),
        'schedule': H.schedule_words(habit),
        'amount': H.amount_words(habit),
''',
         r'''        'week_words': week_words,
        'week': week,
        'entry': entry,
        'entry_words': ('Today' if entry['date'] == day else
                        entry['date'].strftime('%A ') +
                        str(entry['date'].day) +
                        entry['date'].strftime(' %b')),
        'calendar': [[dict(c, state=SHOWN.get(c['state'], c['state']))
                      for c in col]
                     for col in H.calendar(habit, done, day)],
        'schedule': H.schedule_words(habit),
        'amount': H.amount_words(habit),
'''),
        (r'''    if schedule not in dict(Habit.SCHEDULES):
        schedule = Habit.SCHEDULE_DAILY
    # WL-8 - a challenge is every day.
    if _challenge_choice(post):
        schedule = Habit.SCHEDULE_DAILY
    weekdays = ''.join(sorted({d for d in post.getlist('weekdays')
                               if d in '0123456' and len(d) == 1}))
''',
         r'''    if schedule not in dict(Habit.SCHEDULES):
        schedule = Habit.SCHEDULE_DAILY
    # WL-12, 1 Nov 2026 - a challenge no longer turns the habit into an
    # every-day one: times a week and chosen days get weekly challenges.
    weekdays = ''.join(sorted({d for d in post.getlist('weekdays')
                               if d in '0123456' and len(d) == 1}))
'''),
        (r'''            habit.save()
            return redirect('wellness:habit_detail', pk=habit.pk)
        values['challenge'] = _challenge_choice(request.POST)
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': True, 'v': values, 'errors': errors,
        'challenge_days': CH.DAYS,
        'challenge_starters': [(lbl, json.dumps(pr))
                               for lbl, pr in CH.STARTERS],
''',
         r'''            habit.save()
            return redirect('wellness:habit_detail', pk=habit.pk)
        values.update(_challenge_values(_challenge_choice(request.POST)))
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': True, 'v': values, 'errors': errors,
        'challenge_days': CH.DAYS, 'challenge_weeks': CH.WEEKS,
        'challenge_starters': [(lbl, json.dumps(pr))
                               for lbl, pr in CH.STARTERS],
'''),
        (r'''            _resync(habit)
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
    """7, 14, 21 or 30 from the form - or, CY-3, your own number of days
    (2 to 365) when "Own" is chosen - or None."""
    raw = post.get('challenge') or ''
    if raw == 'own':
        raw = post.get('challenge_own') or ''
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if CH.valid_days(n) else None


def _set_challenge(habit, post, day):
    """Begin, change or end the habit's challenge from the form. Editing
    anything else leaves a running (or finished) one as it is."""
    want = _challenge_choice(post)
    if want and (not CH.has(habit) or habit.challenge_days != want):
        CH.begin(habit, want, day)
    elif not want and CH.has(habit):
        CH.clear(habit)
''',
         r'''            _resync(habit)
            return redirect('wellness:habit_detail', pk=habit.pk)
        values.update(_challenge_values(_challenge_choice(request.POST)))
    else:
        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from',
            'remind_at')}
        values.update(_challenge_values(
            (habit.challenge_days, habit.challenge_unit or 'day')
            if CH.has(habit) else None))
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
        'errors': errors, 'challenge_days': CH.DAYS,
        'challenge_weeks': CH.WEEKS,
        'weekday_names': _weekday_names(values.get('weekdays') or ''),
        'tip': None, 'kinds': Habit.KINDS, 'times': Habit.TIMES,
    })


def _challenge_choice(post):
    """(number, 'day' or 'week') from the form, or None.

    Every day: 7, 14, 21 or 30 days, or (CY-3) your own 2 to 365.
    WL-12 - times a week or chosen days: 4, 6, 8 or 12 weeks, or your own
    2 to 52 - the week choices have their own names (challenge_w)."""
    sched = post.get('schedule') or Habit.SCHEDULE_DAILY
    if sched == Habit.SCHEDULE_DAILY:
        raw = post.get('challenge') or ''
        if raw == 'own':
            raw = post.get('challenge_own') or ''
        ok, unit = CH.valid_days, 'day'
    else:
        raw = post.get('challenge_w') or ''
        if raw == 'own':
            raw = post.get('challenge_own_w') or ''
        ok, unit = CH.valid_weeks, 'week'
    try:
        n = int(raw)
    except ValueError:
        return None
    return (n, unit) if ok(n) else None


def _challenge_values(choice):
    """What the form shows as chosen: v.challenge (days) or
    v.challenge_w (weeks)."""
    n, unit = choice or (None, None)
    return {'challenge': n if unit == 'day' else None,
            'challenge_w': n if unit == 'week' else None}


def _set_challenge(habit, post, day):
    """Begin, change or end the habit's challenge from the form. Editing
    anything else leaves a running (or finished) one as it is; a new
    number - or days becoming weeks - starts it again from today."""
    want = _challenge_choice(post)
    if want and (not CH.has(habit) or habit.challenge_days != want[0] or
                 (habit.challenge_unit or 'day') != want[1]):
        CH.begin(habit, want[0], day, want[1])
    elif not want and CH.has(habit):
        CH.clear(habit)
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl14-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl15-1'


'''),
    ]),
    (os.path.join('wellness', 'badges.py'), [
        (r'''    # WL-8, 31 Oct 2026 - a challenge done to the end.
    ('challenge_1', '✓', 'Challenge finished', 'You finished a challenge, '
     'every day of it.', lambda f: f['challenges'] >= 1, lambda f: None),
]
KEYS = [b[0] for b in BADGES]
''',
         r'''    # WL-8, 31 Oct 2026 - a challenge done to the end.
    ('challenge_1', '✓', 'Challenge finished', 'You finished a challenge, '
     'all the way to the end.', lambda f: f['challenges'] >= 1, lambda f: None),
]
KEYS = [b[0] for b in BADGES]
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'habit_detail': {
        'title': 'A habit',
        'purpose': 'How one habit is going: its streak, the last 12 weeks, '
                   'and the days you came back.',
        'steps': [
            'Tap any of the last seven days to fill in one you forgot.',
            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
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
''',
         r'''    'habit_detail': {
        'title': 'A habit',
        'purpose': 'How one habit is going: its streak, the last seven '
                   'days and the last 12 weeks.',
        'steps': [
            'Tap any of the last seven days to fill in one you forgot. For '
            'minutes or a count, tapping a day puts its amount in the box '
            'below - type it and Save (0 clears it).',
            'Every day has one of three marks: Done, Missed or Rest.',
            'The first two missed days each month are forgiven: they show '
            'as Missed, but never spoil your streak.',
            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
            'After 66 good days you can mark it established.',
            'A challenge on an every-day habit shows a square for each day: '
            '"Day 12 of 30". Miss one and you choose: carry on, or start '
            'again.',
            'A challenge on a times-a-week or chosen-days habit counts '
            'weeks: "Week 3 of 12 - 2 of 4 this week", with a square for '
            'each week that fills as the week fills.',
            'Fall short in a week and you choose: carry on (the finish moves '
            'out a week), or start again this week.',
        ],
        'signs': [
            ('--w-sage-deep', 'Done: green - you did it, or reached the '
                              'amount you aim for.'),
            ('--w-miss', 'Missed: a grey outline - a planned day not done. '
                         'Never red. The first two each month are forgiven '
                         'and keep your streak whole.'),
            ('--w-empty', 'Rest: faint - a day the habit was not due (or '
                          'before it began). For a challenge, faint squares '
                          'are the days or weeks still to do.'),
        ],
    },
'''),
        (r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge: 7, 14, 21 or 30 days - or your own number, '
            'from 2 to 365 - every day.',
        ],
        'signs': [],
''',
         r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge. Every day: 7, 14, 21 or 30 days, or your '
            'own number (2 to 365). Times a week or chosen days: 4, 6, 8 or '
            '12 weeks, or your own number (2 to 52).',
            'A weekly challenge, for example: Run, 30 minutes, 4 times a '
            'week, 12 weeks. Each Monday to Sunday counts once you have done '
            '4 runs of at least 30 minutes, on any days.',
            'Twelve such weeks and it is finished. Started mid-week? The '
            'first week asks for its share - begun on a Thursday, 2 runs.',
        ],
        'signs': [],
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    {'title': 'Missed a day? That is fine',
     'body': 'Nothing resets to zero and nothing turns red. Streaks are '
             'counted in weeks, two days a month are forgiven, and coming '
             'back is something we celebrate.'},
]

''',
         r'''    {'title': 'Missed a day? That is fine',
     'body': 'Nothing resets to zero and nothing turns red. Streaks are '
             'counted in weeks, and the first two missed days each month '
             'are forgiven.'},
]

'''),
        (r'''    'detail_week': 'Tap any of the last seven days to fill in one you '
                   'forgot.',
    'detail_calendar': 'Sand squares are comebacks - the days you returned '
                       'after a break. They count double in our book.',
    'new_examples': 'Tap an example to use it, or type your own.',
    # WL-2
''',
         r'''    'detail_week': 'Tap any of the last seven days to fill in one you '
                   'forgot.',
    'detail_calendar': 'Green is done, a grey outline is missed, faint is '
                       'rest. The first two missed days a month are '
                       'forgiven.',
    'new_examples': 'Tap an example to use it, or type your own.',
    # WL-2
'''),
        (r'''    {'q': 'How do streaks work here?',
     'a': 'Streaks count whole weeks, not days. A week is met when you did '
          'every planned day (allowing for grace days), or reached your '
          'number for a "times a week" habit. This week can add to your '
          'streak, but never breaks it - it is not over yet.'},
    {'q': 'What are grace days?',
     'a': 'For daily and chosen-day habits, the first two missed days in '
          'each month are forgiven automatically. They show as a soft '
          'outline on the calendar and keep your week whole. "Times a '
          'week" habits are flexible already, so they do not need them.'},
    {'q': 'What is a comeback?',
     'a': 'A day you did the habit after a real break - two or more missed '
          'days in a row, or a week or more for a "times a week" habit. It '
          'gets a sand-coloured mark, because coming back is the hardest '
          'part.'},
    {'q': 'What does "established" mean?',
     'a': 'After 66 days at 80% or better, a habit is usually part of you. '
          'We offer to mark it established; it moves to a quiet list and '
          'stops asking for attention.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days at the top takes '
          'a tap on any day.'},
    {'q': 'How do I take a break from a habit?',
     'a': 'Open the habit and choose Pause. It leaves Today and nothing '
''',
         r'''    {'q': 'How do streaks work here?',
     'a': 'Streaks count whole weeks, not days. A week is met when you did '
          'every planned day (the first two missed days a month are '
          'forgiven), or reached your '
          'number for a "times a week" habit. This week can add to your '
          'streak, but never breaks it - it is not over yet.'},
    # WL-12, 1 Nov 2026 - three marks (Demetri, 12:24).
    {'q': 'What do Done, Missed and Rest mean?',
     'a': 'You only ever tick a day or save its amount - Wellness marks the '
          'rest once each day is over. Done (green): you did it, or reached '
          'your amount. Missed (a grey outline, never red): a planned day '
          'not done. Rest (faint): a day the habit was not due - outside '
          'your chosen days, or any day of a "times a week" habit you did '
          'not use. Today is never missed; it is not over yet.'},
    {'q': 'Will a missed day spoil my streak?',
     'a': 'Not the first two each month. For every-day and chosen-day '
          'habits the first two missed days in a calendar month are '
          'forgiven automatically: they still show as Missed, but your week '
          'stays whole. From the third, a missed day ends that week\'s run. '
          '"Times a week" habits only need the number each week, so they '
          'have no missed days at all.'},
    {'q': 'What does "established" mean?',
     'a': 'After 66 days at 80% or better, a habit is usually part of you. '
          'We offer to mark it established; it moves to a quiet list and '
          'stops asking for attention.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days takes a tap on '
          'any day. For a minutes or count habit, the tap puts that day in '
          'the box below - type the amount and Save; 0 clears it. Up to '
          'seven days back.'},
    {'q': 'How do I take a break from a habit?',
     'a': 'Open the habit and choose Pause. It leaves Today and nothing '
'''),
        (r'''    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line: 7, 14, 21 or 30 days, '
          'or your own number (tap Own and type it, 2 to 365), every day. '
          'Choose "Make it a challenge" when you add or edit a habit, or '
          'tap one of the challenges to try. Only the days you do '
          'count, so Today shows "Day 12 of 30".'},
    {'q': 'What happens if I miss a day of a challenge?',
     'a': 'Nothing is lost. Wellness asks once: carry on, and the finish '
          'moves out by a day, or start again from today. Missed a few in a '
          'row? You can pause it for now too. When you finish, keep it as a '
          'habit, go again, or let it go.'},
    # WL-7, 31 Oct 2026 - Calm.
''',
         r'''    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line, and it follows how '
          'often the habit is done. Every day: 7, 14, 21 or 30 days, or '
          'your own number (2 to 365); only the days you do count, so '
          'Today shows "Day 12 of 30". Times a week or chosen days: 4, 6, '
          '8 or 12 weeks, or your own number (2 to 52), counted in weeks. '
          'Choose "Make it a challenge" when you add or edit a habit, or '
          'tap one of the challenges to try.'},
    # WL-12, 1 Nov 2026 - weekly challenges.
    {'q': 'How does a weekly challenge work?',
     'a': 'Say Run, 30 minutes, 4 times a week, for 12 weeks. Weeks run '
          'Monday to Sunday. A week counts once it has 4 runs of at least '
          '30 minutes, on any days you like - "Week 3 of 12 - 2 of 4 this '
          'week". One square per week fills as the week fills. Twelve '
          'counted weeks and it is finished. Start mid-week and the first '
          'week asks for its share (begun on a Thursday: 2 runs). For chosen days '
          '(say Mon, Wed, Fri), a week counts when each chosen day is done '
          '- the first two missed days a month are forgiven.'},
    {'q': 'What happens if I miss a day of a challenge?',
     'a': 'Nothing is lost. Wellness asks once: carry on, and the finish '
          'moves out by a day, or start again from today. Missed a few in a '
          'row? You can pause it for now too. A weekly challenge asks the '
          'same when a week falls short: carry on (the finish moves out a '
          'week) or start again this week. When you finish, keep it as a '
          'habit, go again, or let it go.'},
    # WL-7, 31 Oct 2026 - Calm.
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  --w-line: #ECE8E0;
  --w-empty: #EEEBE4;
  --w-ring-off: #B9C7BE;
  --w-on-accent: #FFFFFF;
''',
         r'''  --w-line: #ECE8E0;
  --w-empty: #EEEBE4;
  /* WL-12 - a missed day: a soft grey outline, never red. */
  --w-miss: #C3BCAF;
  --w-ring-off: #B9C7BE;
  --w-on-accent: #FFFFFF;
'''),
        (r'''    --w-line: #2F3B3F;
    --w-empty: #2A3438;
    --w-ring-off: #55665D;
    --w-on-accent: #142018;
''',
         r'''    --w-line: #2F3B3F;
    --w-empty: #2A3438;
    --w-miss: #5F6B6E;
    --w-ring-off: #55665D;
    --w-on-accent: #142018;
'''),
        (r'''.w-day.done .d-label { color: inherit; opacity: .85; }
.w-day.grace { box-shadow: inset 0 0 0 2px var(--w-sage-track); }
.w-day.before { opacity: .6; }

''',
         r'''.w-day.done .d-label { color: inherit; opacity: .85; }
.w-day.grace { box-shadow: inset 0 0 0 2px var(--w-sage-track); }
/* WL-12, 1 Nov 2026 - three marks: Done, Missed, Rest. */
.w-day.miss { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-miss); }
.w-day.picked { outline: 2px solid var(--w-ink); outline-offset: 2px; }
.w-day.before { opacity: .6; }

'''),
        (r'''.w-cell.comeback { background: #E8DCC8; box-shadow: inset 0 0 0 2px #C9A96E; }
.w-cell.open { box-shadow: inset 0 0 0 2px var(--w-ring-off); }
/* WL-1b - a new habit's calendar was a blank card: every day before it
   began was transparent. They are faint squares now, so the grid is there
''',
         r'''.w-cell.comeback { background: #E8DCC8; box-shadow: inset 0 0 0 2px #C9A96E; }
.w-cell.open { box-shadow: inset 0 0 0 2px var(--w-ring-off); }
.w-cell.miss, .w-key i.miss { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-miss); }
/* WL-1b - a new habit's calendar was a blank card: every day before it
   began was transparent. They are faint squares now, so the grid is there
'''),
        (r'''.w-strip i.done { background: var(--w-sage-deep); }
.w-strip i.today { box-shadow: inset 0 0 0 2px var(--w-sage); background: transparent; }
.w-linkbtn { background: none; border: none; padding: 0; font: inherit; color: var(--w-sage-deep); text-decoration: underline; cursor: pointer; }

''',
         r'''.w-strip i.done { background: var(--w-sage-deep); }
.w-strip i.today { box-shadow: inset 0 0 0 2px var(--w-sage); background: transparent; }
/* WL-12 - a weekly challenge: one square per week, filling from the
   bottom as the week fills. */
.w-wstrip { gap: 6px; }
.w-wstrip i { position: relative; overflow: hidden; display: block; }
.w-wstrip i b { position: absolute; left: 0; right: 0; bottom: 0; display: block; background: var(--w-sage-deep); }
.w-wstrip i.now { box-shadow: inset 0 0 0 2px var(--w-sage); }
.w-wstrip i.now b { background: var(--w-sage); }
.w-linkbtn { background: none; border: none; padding: 0; font: inherit; color: var(--w-sage-deep); text-decoration: underline; cursor: pointer; }

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  });

  // ---- WL-8: a challenge is every day; another schedule ends the choice.
  document.querySelectorAll('[data-habit-form]').forEach(function (form) {
    form.addEventListener('change', function (e) {
      var t = e.target;
      if (t.name === 'challenge' && t.value) {
        var daily = form.querySelector('[name=schedule][value=daily]');
        if (daily) daily.checked = true;
        // CY-3 - "Own": the number box takes the focus.
        if (t.value === 'own') { var box = form.querySelector('[name=challenge_own]'); if (box) box.focus(); }
      } else if (t.name === 'challenge_own' && t.value) {
        var own = form.querySelector('[name=challenge][value=own]');
        if (own) own.checked = true;
        var d2 = form.querySelector('[name=schedule][value=daily]');
        if (d2) d2.checked = true;
      } else if (t.name === 'schedule' && t.value !== 'daily') {
        var none = form.querySelector('[name=challenge][value=""]');
        if (none) none.checked = true;
      }
    }, true);
''',
         r'''  });

  // ---- WL-8 / WL-12: a challenge follows the schedule - days for every
  // day, weeks for times a week and chosen days. Choosing one no longer
  // changes the schedule (it used to turn the habit into every day).
  document.querySelectorAll('[data-habit-form]').forEach(function (form) {
    form.addEventListener('change', function (e) {
      var t = e.target;
      // CY-3 - "Own": the number box takes the focus.
      if (t.name === 'challenge' && t.value === 'own') {
        var box = form.querySelector('[name=challenge_own]'); if (box) box.focus();
      } else if (t.name === 'challenge_w' && t.value === 'own') {
        var boxw = form.querySelector('[name=challenge_own_w]'); if (boxw) boxw.focus();
      } else if (t.name === 'challenge_own' && t.value) {
        var own = form.querySelector('[name=challenge][value=own]');
        if (own) own.checked = true;
      } else if (t.name === 'challenge_own_w' && t.value) {
        var ownw = form.querySelector('[name=challenge_w][value=own]');
        if (ownw) ownw.checked = true;
      }
    }, true);
'''),
        (r'''    });
    form.querySelectorAll('[data-when-schedule]').forEach(function (el) {
      el.hidden = el.getAttribute('data-when-schedule') !== sched;
    });
  }
''',
         r'''    });
    form.querySelectorAll('[data-when-schedule]').forEach(function (el) {
      el.hidden = el.getAttribute('data-when-schedule').split(' ').indexOf(sched) < 0;
    });
  }
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_detail.html'), [
        (r'''  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <h2 class="w-h2" id="ch-h">{% if challenge.finished %}Challenge finished{% else %}{{ challenge.words }}{% endif %}</h2>
    <span class="w-small w-quiet">{{ challenge.days }}-day challenge</span>
  </div>
  {% if not challenge.rows %}<div class="w-bar" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done"><i style="width:{{ challenge.pct }}%"></i></div>{% endif %}
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
''',
         r'''  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <h2 class="w-h2" id="ch-h">{% if challenge.finished %}Challenge finished{% else %}{{ challenge.words }}{% endif %}</h2>
    <span class="w-small w-quiet">{{ challenge.days }}-{{ challenge.unit }} challenge</span>
  </div>
  {% if challenge.unit == 'week' %}
  {% comment %} WL-12, 1 Nov 2026 - a weekly challenge: a square for each week, filling as the week fills. {% endcomment %}
  {% if challenge.this_words %}<p style="margin:0;font-weight:600" data-this-week>{{ challenge.this_words }}</p>{% endif %}
  {% for row in challenge.rows %}
  <div class="w-strip w-wstrip" style="grid-template-columns:repeat({{ row|length }},minmax(0,1fr));max-width:{% widthratio row|length 13 100 %}%" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} weeks done">{% for s in row %}<i class="{{ s.cls }}"><b style="height:{{ s.pct }}%"></b></i>{% endfor %}</div>
  {% endfor %}
  <p class="w-small w-quiet" style="margin:0">{% if challenge.finished %}All {{ challenge.days }} weeks done, finished on {{ challenge.finished|date:"l j F" }}.{% else %}{{ challenge.got }} week{{ challenge.got|pluralize }} done · finishes on {{ challenge.finish_words }} if every week from now is met{% if challenge.misses %} · {{ challenge.misses }} week{{ challenge.misses|pluralize }} added{% endif %}.{% endif %}</p>
  {% else %}
  {% if not challenge.rows %}<div class="w-bar" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done"><i style="width:{{ challenge.pct }}%"></i></div>{% endif %}
  {% for row in challenge.rows %}
  <div class="w-strip" style="grid-template-columns:repeat({{ row|length }},minmax(0,1fr));max-width:{% widthratio row|length 15 100 %}%" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done">{% for s in row %}<i class="{{ s }}"></i>{% endfor %}</div>
  {% endfor %}
  <p class="w-small w-quiet" style="margin:0">{% if challenge.finished %}All {{ challenge.days }} days done, finished on {{ challenge.finished|date:"l j F" }}.{% else %}{{ challenge.got }} done · finishes on {{ challenge.finish_words }} if every day from now is done{% if challenge.misses %} · {{ challenge.misses }} day{{ challenge.misses|pluralize }} added{% endif %}.{% endif %}</p>
  {% endif %}
  {% if challenge.ask and not habit.archived_at %}
  <p style="margin:0">{{ challenge.ask_words }}</p>
  <div class="w-btn-row">
    <form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_carry' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<button type="submit" class="w-btn" style="flex:1">Carry on</button></form>
    <form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_restart' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<button type="submit" class="w-btn ghost" style="flex:1">Start again {% if challenge.unit == 'week' %}this week{% else %}today{% endif %}</button></form>
  </div>
  {% if challenge.can_pause %}<form method="post" action="{% url 'wellness:habit_action' habit.pk 'challenge_pause' %}">{% csrf_token %}<button type="submit" class="w-btn quiet">Pause it for now</button></form>{% endif %}
'''),
        (r'''  <div class="w-week">
    {% for d in week %}
    <form method="post" action="{% url 'wellness:habit_check' habit.pk %}" style="display:flex">
      {% csrf_token %}
      <input type="hidden" name="date" value="{{ d.iso }}">
      <input type="hidden" name="op" value="toggle">
      <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}">
      <button type="submit" class="w-day {{ d.state }}" style="flex:1" aria-pressed="{% if d.state == 'done' %}true{% else %}false{% endif %}" aria-label="{{ d.date|date:'l j F' }}{% if d.state == 'done' %}, done{% elif d.state == 'grace' %}, forgiven{% endif %}">
        <span class="d-label">{{ d.label }}</span>
        <span class="d-num">{{ d.num }}</span>
      </button>
    </form>
    {% endfor %}
  </div>
  {% if habit.measured %}
  <form method="post" action="{% url 'wellness:habit_check' habit.pk %}" style="display:flex;gap:10px;align-items:flex-end">
    {% csrf_token %}
    <input type="hidden" name="op" value="set">
    <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}">
    <label style="flex:1;display:flex;flex-direction:column;gap:6px">
      <span class="w-small w-quiet">Today, in {% if habit.kind == 'duration' %}minutes{% else %}{{ habit.unit|default:'times' }}{% endif %} (aim {{ habit.target }})</span>
      <input class="w-input" type="number" name="value" min="0" inputmode="numeric" value="{{ week.6.value|default_if_none:'' }}">
    </label>
    <button type="submit" class="w-btn" style="min-height:56px">Save</button>
  </form>
  {% endif %}
</section>
{% endif %}

<section class="w-card" aria-labelledby="cal-h">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <h2 class="w-h2" id="cal-h" style="font-size:16px">Last 12 weeks</h2>
    {% if comebacks %}<span class="w-small w-quiet">{{ comebacks }} comeback{{ comebacks|pluralize }}</span>{% endif %}
  </div>
  <div class="w-cal" role="img" aria-label="A calendar of the last twelve weeks, one column per week">
    {% for col in calendar %}{% for c in col %}<div class="w-cell {{ c.state }}{% if c.comeback %} comeback{% endif %}" title="{{ c.date|date:'D j M' }}"></div>{% endfor %}{% endfor %}
  </div>
  {% if days_in < 14 %}<p class="w-small w-quiet" style="margin:0">Your calendar fills in day by day. Faint squares are the days before this habit began.</p>{% endif %}
  <div class="w-key">
    <span><i style="background:var(--w-sage)"></i>Done</span>
    <span><i style="background:#E8DCC8;box-shadow:inset 0 0 0 2px #C9A96E"></i>Comeback</span>
    {% if habit.schedule != 'per_week' %}<span><i style="box-shadow:inset 0 0 0 2px var(--w-sage)"></i>Forgiven</span>{% endif %}
    <span><i style="background:var(--w-empty)"></i>Rest</span>
  </div>
</section>

''',
         r'''  <div class="w-week">
    {% for d in week %}
    {% if habit.measured %}
    {% comment %} WL-12, 1 Nov 2026 - an amount habit: tap a day and the box below is for that day. {% endcomment %}
    <a href="?day={{ d.iso }}#w-entry" class="w-day {{ d.state }}{% if d.iso == entry.iso %} picked{% endif %}" style="text-decoration:none;color:inherit" data-day-pick{% if d.iso == entry.iso %} aria-current="date"{% endif %} aria-label="{{ d.date|date:'l j F' }}{% if d.state == 'done' %}, done{% elif d.state == 'miss' %}, missed{% endif %}{% if d.value %}, {{ d.value }}{% endif %}">
      <span class="d-label">{{ d.label }}</span>
      <span class="d-num">{{ d.num }}</span>
    </a>
    {% else %}
    <form method="post" action="{% url 'wellness:habit_check' habit.pk %}" style="display:flex">
      {% csrf_token %}
      <input type="hidden" name="date" value="{{ d.iso }}">
      <input type="hidden" name="op" value="toggle">
      <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}">
      <button type="submit" class="w-day {{ d.state }}" style="flex:1" aria-pressed="{% if d.state == 'done' %}true{% else %}false{% endif %}" aria-label="{{ d.date|date:'l j F' }}{% if d.state == 'done' %}, done{% elif d.state == 'miss' %}, missed{% endif %}">
        <span class="d-label">{{ d.label }}</span>
        <span class="d-num">{{ d.num }}</span>
      </button>
    </form>
    {% endif %}
    {% endfor %}
  </div>
  {% if habit.measured %}
  <form method="post" action="{% url 'wellness:habit_check' habit.pk %}" style="display:flex;gap:10px;align-items:flex-end" id="w-entry" data-entry>
    {% csrf_token %}
    <input type="hidden" name="op" value="set">
    <input type="hidden" name="date" value="{{ entry.iso }}">
    <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}{% if entry.label != 'Today' %}?day={{ entry.iso }}{% endif %}">
    <label style="flex:1;display:flex;flex-direction:column;gap:6px">
      <span class="w-small w-quiet">{{ entry_words }}, in {% if habit.kind == 'duration' %}minutes{% else %}{{ habit.unit|default:'times' }}{% endif %} (aim {{ habit.target }})</span>
      <input class="w-input" type="number" name="value" min="0" inputmode="numeric" value="{{ entry.value|default_if_none:'' }}"{% if entry.label != 'Today' %} autofocus{% endif %}>
    </label>
    <button type="submit" class="w-btn" style="min-height:56px">Save</button>
  </form>
  {% endif %}
  {% if habit.measured %}<p class="w-small w-quiet" style="margin:0">Tap a day to enter or change its amount. 0 clears it.</p>{% endif %}
</section>
{% endif %}

<section class="w-card" aria-labelledby="cal-h">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <h2 class="w-h2" id="cal-h" style="font-size:16px">Last 12 weeks</h2>
  </div>
  <div class="w-cal" role="img" aria-label="A calendar of the last twelve weeks, one column per week">
    {% for col in calendar %}{% for c in col %}<div class="w-cell {{ c.state }}" title="{{ c.date|date:'D j M' }}"></div>{% endfor %}{% endfor %}
  </div>
  {% if days_in < 14 %}<p class="w-small w-quiet" style="margin:0">Your calendar fills in day by day. Faint squares are the days before this habit began.</p>{% endif %}
  <div class="w-key">
    <span><i style="background:var(--w-sage)"></i>Done</span>
    {% if habit.schedule != 'per_week' %}<span><i class="miss"></i>Missed</span>{% endif %}
    <span><i style="background:var(--w-empty)"></i>Rest</span>
  </div>
  {% if habit.schedule != 'per_week' %}<p class="w-small w-quiet" style="margin:0">The first two missed days each month are forgiven - they never spoil your streak.</p>{% endif %}
</section>

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {% comment %} WL-8, 31 Oct 2026 - a challenge: every day, with a finish line. {% endcomment %}
    <div style="display:flex;flex-direction:column;gap:8px" data-challenge-pick>
      <span class="w-label">Make it a challenge</span>
      <div class="w-chips">
''',
         r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {% comment %} WL-8, 31 Oct 2026 - a challenge: every day, with a finish line. WL-12, 1 Nov 2026 - times a week and chosen days get weekly challenges instead (below). {% endcomment %}
    <div style="display:flex;flex-direction:column;gap:8px" data-challenge-pick data-when-schedule="daily">
      <span class="w-label">Make it a challenge</span>
      <div class="w-chips">
'''),
        (r'''      <span class="w-small w-quiet">A challenge is every day, with a finish line. Miss a day and you choose: carry on, or start again.</span>
      {% if habit.challenge_from and v.challenge %}<span class="w-small w-quiet">Changing the number of days starts it again from today.</span>{% endif %}
    </div>
    {# WL-3, WL-7 - a habit can tick itself: a finished workout, or Calm minutes. #}
''',
         r'''      <span class="w-small w-quiet">A challenge is every day, with a finish line. Miss a day and you choose: carry on, or start again.</span>
      {% if habit.challenge_from and v.challenge %}<span class="w-small w-quiet">Changing the number of days starts it again from today.</span>{% endif %}
    </div>
    <div style="display:flex;flex-direction:column;gap:8px" data-challenge-pick-weeks data-when-schedule="per_week weekdays">
      <span class="w-label">Make it a challenge</span>
      <div class="w-chips">
        <label class="w-chip"><input type="radio" name="challenge_w" value=""{% if not v.challenge_w %} checked{% endif %}><span>No</span></label>
        {% for n in challenge_weeks %}<label class="w-chip"><input type="radio" name="challenge_w" value="{{ n }}"{% if v.challenge_w == n %} checked{% endif %}><span>{{ n }} weeks</span></label>{% endfor %}
        <label class="w-chip"><input type="radio" name="challenge_w" value="own"{% if v.challenge_w and v.challenge_w not in challenge_weeks %} checked{% endif %} data-own-pick-w><span>Own</span></label>
      </div>
      <label class="w-small w-quiet" style="display:flex;align-items:center;gap:10px">Your own number of weeks
        <input class="w-input" type="number" name="challenge_own_w" min="2" max="52" inputmode="numeric" value="{% if v.challenge_w and v.challenge_w not in challenge_weeks %}{{ v.challenge_w }}{% endif %}" placeholder="10" style="max-width:110px"></label>
      <span class="w-small w-quiet">A weekly challenge counts weeks, Monday to Sunday. A week counts when you reach your number for it - for example 4 runs of 30 minutes, on any days. A week that falls short: carry on (the finish moves out a week), or start again.</span>
      {% if habit.challenge_from and v.challenge_w %}<span class="w-small w-quiet">Changing the number of weeks starts it again this week.</span>{% endif %}
    </div>
    {# WL-3, WL-7 - a habit can tick itself: a finished workout, or Calm minutes. #}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  <div class="w-btn-row">
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_carry' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn" style="flex:1">Carry on</button></form>
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_restart' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn ghost" style="flex:1;background:var(--w-card)">Start again today</button></form>
  </div>
  <span class="w-small w-quiet">Carry on and it finishes on {{ a.c.finish_words }}.{% if a.c.can_pause %} Or <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_pause' %}" style="display:inline">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-linkbtn">pause it for now</button></form>.{% endif %}</span>
''',
         r'''  <div class="w-btn-row">
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_carry' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn" style="flex:1">Carry on</button></form>
    <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_restart' %}" style="flex:1 1 auto;display:flex">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-btn ghost" style="flex:1;background:var(--w-card)">Start again {% if a.c.unit == 'week' %}this week{% else %}today{% endif %}</button></form>
  </div>
  <span class="w-small w-quiet">Carry on and it finishes on {{ a.c.finish_words }}.{% if a.c.can_pause %} Or <form method="post" action="{% url 'wellness:habit_action' a.habit.pk 'challenge_pause' %}" style="display:inline">{% csrf_token %}<input type="hidden" name="next" value="{% url 'wellness:today' %}"><button type="submit" class="w-linkbtn">pause it for now</button></form>.{% endif %}</span>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl14-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl15-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl14-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl15-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('test_wellness_ten.py'), [
        (r'''   and 'data-challenge-ask' in today_t,
   'Today: "Day N of D", the finish card, and the missed-day question')
ok('Carry on' in today_t and 'Start again today' in today_t,
   '  the question offers Carry on and Start again')
det = read(J(WT, 'habit_detail.html'))
''',
         r'''   and 'data-challenge-ask' in today_t,
   'Today: "Day N of D", the finish card, and the missed-day question')
# WL-12, 1 Nov 2026: "Start again this week" for a weekly challenge.
ok('Carry on' in today_t and 'Start again ' in today_t and
   'today{% endif %}' in today_t,
   '  the question offers Carry on and Start again')
det = read(J(WT, 'habit_detail.html'))
'''),
        (r'''ok(not small, 'every control is still at least 44px', small)
js = read(J(APP, 'assets', 'wellness.js'))
ok("set('challenge', p.challenge || '')" in js and
   "[name=schedule][value=daily]" in js,
   'a challenge to try fills the form; a challenge is every day')
base = read(J(WT, 'base.html'))
v = re.findall(r'\?v=([\w-]+)', base)
''',
         r'''ok(not small, 'every control is still at least 44px', small)
js = read(J(APP, 'assets', 'wellness.js'))
# WL-12, 1 Nov 2026: a challenge no longer forces every day - times a
# week and chosen days get weekly challenges (test_wellness_sixteen).
ok("set('challenge', p.challenge || '')" in js,
   'a challenge to try fills the form')
base = read(J(WT, 'base.html'))
v = re.findall(r'\?v=([\w-]+)', base)
'''),
        (r'''               'the new-habit screen offers challenges to try')
            r = ca.post('/wellness/habits/new/', {
                'name': 'No sugar', 'kind': 'avoid', 'schedule': 'per_week',
                'per_week': '3', 'time_of_day': 'anytime',
                'challenge': '7'})
            h = Habit.objects.get(user=a, name='No sugar')
            ok(r.status_code == 302 and h.challenge_days == 7 and
               h.challenge_from == day and h.schedule == 'daily',
               'A 7-DAY CHALLENGE begins today - and a challenge is every '
               'day, whatever was picked', (h.challenge_days, h.schedule))
            t = ca.get('/wellness/').content.decode()
            ok('data-challenge-day>Day 1 of 7<' in t,
''',
         r'''               'the new-habit screen offers challenges to try')
            r = ca.post('/wellness/habits/new/', {
                'name': 'No sugar', 'kind': 'avoid', 'schedule': 'daily',
                'time_of_day': 'anytime',
                'challenge': '7'})
            h = Habit.objects.get(user=a, name='No sugar')
            # WL-12: an every-day habit's challenge counts days; times a
            # week and chosen days count weeks (test_wellness_sixteen).
            ok(r.status_code == 302 and h.challenge_days == 7 and
               h.challenge_from == day and h.schedule == 'daily',
               'A 7-DAY CHALLENGE on an every-day habit begins today',
               (h.challenge_days, h.schedule))
            t = ca.get('/wellness/').content.decode()
            ok('data-challenge-day>Day 1 of 7<' in t,
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def valid_days('; What = 'WL-8/CY-3: the challenge rules are on disk, with your own number of days - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
''',
         r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def week_state('; What = 'WL-8/CY-3/WL-12: the challenge rules are on disk, weekly challenges included - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
'''),
        (r'''    'test_wellness_fourteen.py',
    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    'test_wellness_fifteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_fourteen.py',
    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    'test_wellness_fifteen.py',
    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    'test_wellness_sixteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    '.bak_wellness15',
]

''',
         r'''    # WL-11, 1 Nov 2026 - Wellness: calories on a workout.
    '.bak_wellness15',
    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    '.bak_wellness16',
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
    raise SystemExit('WL-12 REFUSED: %s' % msg)


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
    if "'test_wellness_sixteen.py'" in read(pq):
        print('WL-12 already applied.')
        return 0
    if "'test_wellness_fifteen.py'" not in read(pq):
        refuse('Release 58 is not applied - this round registers after it.')
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
        print('WL-12 --check: %d file(s) would change, none written; %d '
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
    print('WL-12 applied - Wellness: weekly challenges, three marks, earlier amounts.')
    print('      MIGRATION 0011_weekly_challenges - run migrate after pushing (Railway does it on deploy).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
