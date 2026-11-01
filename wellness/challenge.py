# -*- coding: utf-8 -*-
"""wellness/challenge.py - WL-8, 31 Oct 2026. Challenges: a habit with a
finish line.

Demetri, 31 Oct 14:26, on the spec: when a day is missed, "give the option
of continuing, but extending by a day, or restarting". 15:46: Challenges
before the cycle-tracker work.

A challenge is an every-day habit with 7, 14, 21 or 30 days to do. Only
DONE days count: "Day 12 of 30" is the day being worked on. A missed day
never fails it. It asks, once, gently:

    Carry on              - the finish moves out by a day (the default:
                            nothing restarts unless the person asks)
    Start again today     - day 1 is today
    Pause it for now      - offered only after three misses in a row

The words "failed" and "lost" are never used. When the last day is done a
finish card offers: keep it as a habit, go again, or let it go (archived,
with its history kept). Each finished challenge is kept in the profile's
prefs for the "Challenge finished" badge.

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

DAYS = [7, 14, 21, 30]
# CY-3, 31 Oct 2026 - Demetri, 20:06: "can we also have a field to enter
# our own number of days?" Any number in this range.
OWN_MIN, OWN_MAX = 2, 365
# Longer than this shows a bar instead of a square for each day.
STRIP_MAX = 90
ONE = dt.timedelta(days=1)
# Misses in a row before "Pause it for now" is offered too.
PAUSE_AFTER = 3

# WL-12 - weekly challenges.
WEEKS = [4, 6, 8, 12]
OWN_W_MIN, OWN_W_MAX = 2, 52
SEVEN = dt.timedelta(days=7)
# Short weeks in a row before "Pause it for now" is offered too.
PAUSE_AFTER_WEEKS = 2

# Starters on the new-habit screen: (name, preset).
STARTERS = [
    ('30 days of no sugar', {'name': 'No sugar', 'kind': 'avoid',
                             'schedule': 'daily', 'time_of_day': 'anytime',
                             'challenge': 30}),
    ('A 30-day 10-minute walk', {'name': 'Walk 10 minutes',
                                 'kind': 'duration', 'target': 10,
                                 'schedule': 'daily',
                                 'time_of_day': 'afternoon',
                                 'challenge': 30}),
    ('21 days of writing', {'name': 'Write a few lines', 'kind': 'yes_no',
                            'schedule': 'daily', 'time_of_day': 'evening',
                            'challenge': 21}),
    ('14 days of screens off by 22:30', {'name': 'Screens off by 22:30',
                                         'kind': 'yes_no',
                                         'schedule': 'daily',
                                         'time_of_day': 'evening',
                                         'challenge': 14}),
    ('7 days of calm', {'name': 'Calm minutes', 'kind': 'duration',
                        'target': 5, 'schedule': 'daily',
                        'time_of_day': 'anytime', 'challenge': 7,
                        'auto_from': 'calm'}),
]


# The finish card's three choices: (habit action, words).
FINISH_ACTIONS = [
    ('challenge_keep', 'Keep it as a habit'),
    ('challenge_again', 'Go again'),
    ('challenge_letgo', 'Let it go'),
]


def is_on(habit):
    """A challenge still running (not yet finished)."""
    return bool(habit.challenge_days and habit.challenge_from and
                not habit.challenge_done_on)


def has(habit):
    return bool(habit.challenge_days and habit.challenge_from)


def nice_date(d):
    return '%s %d %s' % (d.strftime('%a'), d.day, d.strftime('%b'))


def state(habit, done, today):
    """Everything the screens show about a challenge, or None.

    done is the set of done dates. Keys: days, got, day (being worked on),
    today_done, finished (date or None), misses (count), finish (the date
    it should finish if every day from now is done), ask (the missed date
    still to be answered, or None), in_a_row, can_pause, strip, words.
    """
    if not has(habit):
        return None
    if is_weekly(habit):
        return week_state(habit, done, today)
    total, start = habit.challenge_days, habit.challenge_from
    got_days = sorted(d for d in done if start <= d <= today)
    got = len(got_days)
    finished = habit.challenge_done_on or (got_days[total - 1]
                                           if got >= total else None)
    today_done = today in done
    # WL-13 - a paused day is never a miss.
    from .habits import is_paused_on
    misses, d = [], start
    while d < today:
        if d not in done and not is_paused_on(habit, d):
            misses.append(d)
        d += ONE
    left = max(0, total - got)
    # The finish if every day from now on is done.
    first_todo = today + (ONE if today_done else dt.timedelta(0))
    finish = finished or (first_todo + dt.timedelta(days=left - 1)
                          if left else today)
    in_a_row, d = 0, today - ONE
    while d >= start and d not in done:
        if not is_paused_on(habit, d):
            in_a_row += 1
        d -= ONE
    seen = habit.challenge_seen or (start - ONE)
    ask = misses[-1] if (misses and misses[-1] > seen and not finished) \
        else None
    day = min(total, got + (0 if today_done else 1))
    strip = []
    for i in range(total):
        if i < got:
            strip.append('done')
        elif i == got and not today_done and not finished:
            strip.append('today')
        else:
            strip.append('todo')
    if finished:
        words = 'Finished: %d days.' % total
    else:
        words = 'Day %d of %d' % (day, total)
    return {'unit': 'day', 'days': total, 'got': min(got, total), 'day': day,
            'pct': int(round(100.0 * min(got, total) / total)),
            'today_done': today_done, 'finished': finished,
            'misses': len(misses), 'finish': finish,
            'finish_words': nice_date(finish),
            'ask': ask, 'ask_words': ask_words(ask, today, in_a_row),
            'in_a_row': in_a_row,
            'can_pause': bool(ask) and in_a_row >= PAUSE_AFTER,
            'strip': strip, 'rows': rows(strip), 'words': words}


def rows(strip):
    """The strip in rows of at most 15, so 30 squares fit a phone. Longer
    than STRIP_MAX days: no squares (the page shows a bar)."""
    if len(strip) > STRIP_MAX:
        return []
    if len(strip) <= 15:
        return [strip]
    if len(strip) <= 30:
        half = (len(strip) + 1) // 2
        return [strip[:half], strip[half:]]
    return [strip[i:i + 15] for i in range(0, len(strip), 15)]


def valid_days(n):
    """A number of days a challenge may have: a preset or your own."""
    return n in DAYS or OWN_MIN <= n <= OWN_MAX


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
    from .habits import is_paused_on
    first = max(week_start, start)
    last = week_start + dt.timedelta(days=6)
    if first > last:
        return 0
    if habit.schedule == 'weekdays':
        chosen = habit.weekday_set()
        n, d = 0, first
        while d <= last:
            if d.weekday() in chosen and not is_paused_on(habit, d):
                n += 1
            d += ONE
        return n
    # A first week begun mid-week asks for its share of the number:
    # 4 a week begun on a Thursday (4 days left) asks for 2. WL-13 -
    # paused days are not available either.
    per, avail = habit.per_week or 1, 0
    d = first
    while d <= last:
        if not is_paused_on(habit, d):
            avail += 1
        d += ONE
    if avail == 0:
        return 0
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
    elif now_met:
        # WL-13 - Demetri, 17:43, on "Week 1 of 8" with the week already
        # met: say it is done and when the next one begins.
        words = 'Week %d of %d done' % (good, total)
    else:
        words = 'Week %d of %d' % (week_no, total)
    this_words = ''
    if now and not finished:
        noun = 'day' if habit.schedule == 'weekdays' else ''
        this_words = '%d of %d%s this week' % (
            now['got'], now['target'],
            (' %s%s' % (noun, '' if now['target'] == 1 else 's'))
            if noun else '')
        if now_met:
            this_words += ' - week %d starts on Monday' % (good + 1)
        full = (habit.per_week or 1) if habit.schedule != 'weekdays' \
            else len(habit.weekday_set())
        if now['target'] < full and now['monday'] < start:
            this_words += ' (a short first week: you began on a %s)' \
                % start.strftime('%A')
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
        return ''
    if in_a_row >= 2:
        return 'A few days slipped by. That happens.'
    if ask == today - ONE:
        return 'Yesterday slipped by. That happens.'
    return '%s slipped by. That happens.' % ask.strftime('%A')


def carry_on(habit, today):
    """Keep going: the missed days are answered; the finish moves out."""
    habit.challenge_seen = today - ONE


def start_again(habit, today):
    habit.challenge_from = today
    habit.challenge_seen = None
    habit.challenge_done_on = None


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
    habit.challenge_seen = None
    habit.challenge_done_on = None


def note_finished(habit, done, today, profile):
    """Save the finish once: on the habit, and in the profile's list of
    finished challenges (for the badge). Returns True when it is new."""
    if not is_on(habit):
        return False
    s = state(habit, done, today)
    if not s or not s['finished']:
        return False
    habit.challenge_done_on = s['finished']
    habit.save(update_fields=['challenge_done_on', 'updated_at'])
    prefs = dict(profile.prefs or {})
    kept = list(prefs.get('challenges') or [])
    kept.append({'name': habit.name, 'days': habit.challenge_days,
                 'unit': s['unit'], 'on': s['finished'].isoformat()})
    prefs['challenges'] = kept[-200:]
    profile.prefs = prefs
    profile.save(update_fields=['prefs', 'updated_at'])
    return True
