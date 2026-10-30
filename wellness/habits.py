# -*- coding: utf-8 -*-
"""wellness/habits.py - WL-1, 30 Oct 2026. The rules of a kind habit tracker.

Pure functions over (habit, set of done dates, today), so the suite can
drive every rule without a database. The proposal's research is the
reason for each rule:

    - Missing a day does not break habit formation (UCL, 2009), so a
      missed day is never red and never resets anything to zero.
    - TWO GRACE DAYS A MONTH for daily and chosen-day habits: the first
      two misses in a calendar month are forgiven automatically.
      "Times a week" habits are flexible already and get none.
    - STREAKS COUNT WEEKS, NOT DAYS. A week is met when every scheduled
      day was done or graced (daily / chosen days) or the weekly number
      was reached (times a week). The current week can add to a streak
      but never breaks one - it is not over yet.
    - A COMEBACK is a done day after a real break: two or more unforgiven
      misses in a row (daily / chosen days), or a week or more with
      nothing (times a week). It earns its own mark.
    - ESTABLISHED: 66 days in, at 80% or better over those 66 days,
      the habit is offered the "established" mark (UCL's average).

TODAY IS NEVER A MISS. The day is not over; it is "open".
"""
import datetime as dt

GRACE_PER_MONTH = 2
COMEBACK_MISSES = 2
COMEBACK_GAP_DAYS = 7
ESTABLISHED_DAYS = 66
ESTABLISHED_RATE = 0.8

ONE = dt.timedelta(days=1)


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def is_flexible(habit):
    return habit.schedule == 'per_week'


def scheduled(habit, d):
    """Is d one of the habit's days? Times-a-week habits: every day is."""
    if d < habit.started_on:
        return False
    if habit.schedule == 'weekdays':
        return d.weekday() in habit.weekday_set()
    return True


def weekly_target(habit, week_start, upto=None):
    """How many done days make the week starting week_start met."""
    first = max(week_start, habit.started_on)
    last = week_start + dt.timedelta(days=6)
    if upto is not None:
        last = min(last, upto)
    if first > last:
        return 0
    if is_flexible(habit):
        available = (last - first).days + 1
        return min(habit.per_week or 1, available)
    n, d = 0, first
    while d <= last:
        if scheduled(habit, d):
            n += 1
        d += ONE
    return n


def day_states(habit, done, today, since=None):
    """{date: state} from `since` (default the start) to today.

    state is one of: 'done', 'grace', 'miss', 'rest', 'open' (today, not
    done yet). Days before the habit started are left out. Grace is
    worked out from the start, month by month, so a window that begins
    mid-month still forgives the right two days.
    """
    out = {}
    used = {}
    d = habit.started_on
    while d <= today:
        if d in done:
            st = 'done'
        elif d == today:
            st = 'open' if scheduled(habit, d) else 'rest'
        elif not scheduled(habit, d) or is_flexible(habit):
            # A times-a-week habit has no missed DAYS - only weeks short.
            st = 'rest'
        else:
            key = (d.year, d.month)
            if used.get(key, 0) < GRACE_PER_MONTH:
                used[key] = used.get(key, 0) + 1
                st = 'grace'
            else:
                st = 'miss'
        if since is None or d >= since:
            out[d] = st
        d += ONE
    return out


def comebacks(habit, done, today):
    """The set of done days that came after a real break."""
    out = set()
    days = sorted(x for x in done if habit.started_on <= x <= today)
    if is_flexible(habit):
        for prev, cur in zip(days, days[1:]):
            if (cur - prev).days > COMEBACK_GAP_DAYS:
                out.add(cur)
        return out
    states = day_states(habit, done, today)
    seen_done = False
    run = 0
    d = habit.started_on
    while d <= today:
        st = states.get(d)
        if st == 'done':
            if seen_done and run >= COMEBACK_MISSES:
                out.add(d)
            seen_done = True
            run = 0
        elif st == 'miss':
            run += 1
        elif st == 'grace':
            # A forgiven day neither breaks nor builds the run: two
            # misses with a grace day between them are still a break.
            pass
        d += ONE
    return out


def week_met(habit, done, week_start, today, states=None):
    """Was the week starting week_start met? None if it had no days."""
    if is_flexible(habit):
        target = weekly_target(habit, week_start)
        if target == 0:
            return None
        last = week_start + dt.timedelta(days=6)
        n = sum(1 for x in done if week_start <= x <= last
                and x >= habit.started_on)
        return n >= target
    states = states if states is not None else day_states(habit, done,
                                                          today)
    any_day = False
    d = week_start
    for _ in range(7):
        if d > today:
            break
        st = states.get(d)
        if st in ('done', 'grace'):
            any_day = True
        elif st in ('miss',):
            return False
        elif st == 'open':
            return False
        d += ONE
    if not any_day:
        return None
    return True


def week_streak(habit, done, today):
    """Whole weeks met in a row, ending with last week - plus this week
    once it is met. This week not met yet does not break anything."""
    states = None if is_flexible(habit) else day_states(habit, done, today)
    this_week = monday(today)
    n = 0
    w = this_week - dt.timedelta(days=7)
    while w + dt.timedelta(days=6) >= habit.started_on:
        met = week_met(habit, done, w, today, states)
        if met is None:
            w -= dt.timedelta(days=7)
            continue
        if not met:
            break
        n += 1
        w -= dt.timedelta(days=7)
    if is_flexible(habit):
        if week_met(habit, done, this_week, today):
            n += 1
    else:
        target = weekly_target(habit, this_week)
        got = sum(1 for x in done if this_week <= x <= today)
        if target and got >= target:
            n += 1
    return n


def this_week(habit, done, today):
    """(done so far, the week's number) for 'x of y this week'."""
    w = monday(today)
    got = sum(1 for x in done if w <= x <= w + dt.timedelta(days=6)
              and x >= habit.started_on)
    return got, weekly_target(habit, w)


def consistency(habit, done, today, days=30):
    """0..1 over the last `days` days (or since the start), None when
    there is nothing to measure yet. Today counts only once done."""
    since = max(habit.started_on, today - dt.timedelta(days=days - 1))
    if since > today:
        return None
    if is_flexible(habit):
        span = (today - since).days + 1
        expected = (habit.per_week or 1) * span / 7.0
        got = sum(1 for x in done if since <= x <= today)
        if expected <= 0:
            return None
        return min(1.0, got / expected)
    states = day_states(habit, done, today, since=since)
    good = sum(1 for s in states.values() if s in ('done', 'grace'))
    bad = sum(1 for s in states.values() if s == 'miss')
    if good + bad == 0:
        return None
    return good / float(good + bad)


def can_establish(habit, done, today):
    if habit.established_at:
        return False
    if (today - habit.started_on).days + 1 < ESTABLISHED_DAYS:
        return False
    rate = consistency(habit, done, today, days=ESTABLISHED_DAYS)
    return rate is not None and rate >= ESTABLISHED_RATE


def due_today(habit, done, today):
    """Should Today list this habit? Paused and archived never are."""
    if habit.paused or habit.archived_at or habit.started_on > today:
        return False
    if today in done:
        return True
    if is_flexible(habit):
        got, target = this_week(habit, done, today)
        return got < target
    return scheduled(habit, today)


def calendar(habit, done, today, weeks=12):
    """Columns of 7 cells (Monday first) for the last `weeks` weeks,
    oldest first. Each cell: {'date', 'state', 'comeback'}; state is
    'before' for days before the start and 'future' after today."""
    start = monday(today) - dt.timedelta(days=7 * (weeks - 1))
    states = day_states(habit, done, today)
    back = comebacks(habit, done, today)
    cols = []
    for w in range(weeks):
        col = []
        for i in range(7):
            d = start + dt.timedelta(days=7 * w + i)
            if d > today:
                st = 'future'
            elif d < habit.started_on:
                st = 'before'
            else:
                st = states.get(d, 'rest')
            col.append({'date': d, 'state': st, 'comeback': d in back})
        cols.append(col)
    return cols


def schedule_words(habit):
    if habit.schedule == 'per_week':
        n = habit.per_week or 1
        return '%d× a week' % n
    if habit.schedule == 'weekdays':
        names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        days = sorted(habit.weekday_set())
        if days == [0, 1, 2, 3, 4]:
            return 'Weekdays'
        if days == [5, 6]:
            return 'Weekends'
        return ', '.join(names[i] for i in days)
    return 'Every day'


def amount_words(habit):
    if habit.kind == 'duration' and habit.target:
        return '%d min' % habit.target
    if habit.kind == 'count' and habit.target:
        return ('%d %s' % (habit.target, habit.unit)).strip()
    return ''
