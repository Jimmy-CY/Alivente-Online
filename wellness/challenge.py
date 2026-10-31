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
"""
import datetime as dt

DAYS = [7, 14, 21, 30]
ONE = dt.timedelta(days=1)
# Misses in a row before "Pause it for now" is offered too.
PAUSE_AFTER = 3

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
    total, start = habit.challenge_days, habit.challenge_from
    got_days = sorted(d for d in done if start <= d <= today)
    got = len(got_days)
    finished = habit.challenge_done_on or (got_days[total - 1]
                                           if got >= total else None)
    today_done = today in done
    misses, d = [], start
    while d < today:
        if d not in done:
            misses.append(d)
        d += ONE
    left = max(0, total - got)
    # The finish if every day from now on is done.
    first_todo = today + (ONE if today_done else dt.timedelta(0))
    finish = finished or (first_todo + dt.timedelta(days=left - 1)
                          if left else today)
    in_a_row, d = 0, today - ONE
    while d >= start and d not in done:
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
    return {'days': total, 'got': min(got, total), 'day': day,
            'today_done': today_done, 'finished': finished,
            'misses': len(misses), 'finish': finish,
            'finish_words': nice_date(finish),
            'ask': ask, 'ask_words': ask_words(ask, today, in_a_row),
            'in_a_row': in_a_row,
            'can_pause': bool(ask) and in_a_row >= PAUSE_AFTER,
            'strip': strip, 'rows': rows(strip), 'words': words}


def rows(strip):
    """The strip in rows of at most 15, so 30 squares fit a phone."""
    if len(strip) <= 15:
        return [strip]
    half = (len(strip) + 1) // 2
    return [strip[:half], strip[half:]]


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


def begin(habit, days, today):
    habit.challenge_days = days
    habit.challenge_from = today
    habit.challenge_seen = None
    habit.challenge_done_on = None


def clear(habit):
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
                 'on': s['finished'].isoformat()})
    prefs['challenges'] = kept[-200:]
    profile.prefs = prefs
    profile.save(update_fields=['prefs', 'updated_at'])
    return True
