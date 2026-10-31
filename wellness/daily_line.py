# -*- coding: utf-8 -*-
"""wellness/daily_line.py - WL-4c, 30 Oct 2026. Claude's line under the quote.

DECISION 4 OF 30 OCT: the quotes are a curated library kept in the app
(quotes.py). Claude PICKS one of them for each person each day, by its
number, and writes ONE short labelled line beneath it. Claude never writes
the quote - a quote it returned that is not in the library is refused.

WHAT CLAUDE IS TOLD, AND NOTHING MORE: the person's first name, the names
of today's habits, how many habits were done yesterday out of how many,
the longest run of good weeks, and how many workouts this week. NEVER the
journal (decision 5), never the weight or any body number, never the cycle
tracker. The settings page says exactly this, and a person can turn the
line off there.

WHEN: the reminder job (every 15 minutes) makes the day's line for anyone
who has used Wellness lately and does not have one yet - so it is waiting
before they wake. Today never waits on Claude: without a line for today it
shows the date's own quote and no line. Once made, a day's quote holds all
day. At most three tries a day; a failure costs nothing but the line.

The house key, ANTHROPIC_API_KEY, already in Railway. The model is
WELLNESS_LINE_MODEL, defaulting to the house's small model.
"""
import datetime as dt
import json
import logging
import os
import re

from . import quotes as Q

logger = logging.getLogger(__name__)

MODEL = os.environ.get('WELLNESS_LINE_MODEL', 'claude-haiku-4-5')
MAX_WORDS = 28
MAX_TRIES = 3
ACTIVE_DAYS = 14
LABEL = 'A line from Claude'

SYSTEM = (
    "You write one short line for a calm personal wellness app. You are "
    "given a numbered list of real quotes and a few facts about the "
    "person's day. Choose the ONE quote that fits today best, by its "
    "number, and write ONE line of at most %d words to go beneath it. "
    "Be warm and plain, like a kind friend - no exclamation marks, no "
    "emojis, no hashtags, no guilt, no pressure, no medical or diet "
    "advice, and never invent facts. You may use the first name once. "
    "Do not quote or restate the quote. Reply with JSON only: "
    '{"quote": <number>, "line": "<your line>"}' % MAX_WORDS)


def facts(user, day):
    """The few plain facts Claude may see. Never journal, body or cycle."""
    from . import habits as H
    from .models import Habit, WorkoutSession
    name = (user.first_name or user.get_username()).split(' ')[0]
    today_names, y_due, y_done, best = [], 0, 0, 0
    yesterday = day - dt.timedelta(days=1)
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
        if H.due_today(habit, done, day):
            today_names.append(habit.name)
        if habit.started_on <= yesterday and \
                not H.is_flexible(habit) and H.scheduled(habit, yesterday):
            y_due += 1
            y_done += 1 if yesterday in done else 0
        best = max(best, H.week_streak(habit, done, day) if done else 0)
    monday = day - dt.timedelta(days=day.weekday())
    workouts = WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=day).count()
    return {'name': name, 'weekday': day.strftime('%A'),
            'today': today_names[:6], 'yesterday_done': y_done,
            'yesterday_due': y_due, 'good_weeks': best,
            'workouts_this_week': workouts}


def prompt(f):
    lines = ['%d. "%s" - %s' % (i, q['text'], q['author'])
             for i, q in enumerate(Q.QUOTES)]
    about = [
        'First name: %s' % f['name'],
        'Today is %s.' % f['weekday'],
        "Today's habits: %s" % (', '.join(f['today']) or 'none planned'),
        'Yesterday: %d of %d planned habits done.' % (
            f['yesterday_done'], f['yesterday_due'])
        if f['yesterday_due'] else 'Yesterday: nothing was planned.',
        'Good weeks in a row: %d' % f['good_weeks'],
        'Workouts so far this week: %d' % f['workouts_this_week'],
    ]
    return ('Quotes:\n%s\n\nAbout today:\n%s'
            % ('\n'.join(lines), '\n'.join(about)))


def parse(text):
    """{"quote", "line"} from Claude's reply, or None if it is not a fair
    answer: a quote outside the library, a long or empty line, a link."""
    m = re.search(r'\{.*\}', text or '', re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        q = int(d.get('quote'))
        line = ' '.join(str(d.get('line') or '').split())
    except (ValueError, TypeError, AttributeError):
        return None
    if not 0 <= q < len(Q.QUOTES):
        return None
    if not line or len(line.split()) > MAX_WORDS + 4 or len(line) > 240:
        return None
    if re.search(r'https?://|www\.|[<>]', line):
        return None
    if Q.QUOTES[q]['text'].lower()[:40] in line.lower():
        return None
    return {'quote': q, 'line': line}


def ask(f, client=None):
    """One call to Claude. Returns the parsed answer or None."""
    if client is None:
        from django.conf import settings
        key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not key:
            return None
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=30.0)
    msg = client.messages.create(
        model=MODEL, max_tokens=200, system=SYSTEM,
        messages=[{'role': 'user', 'content': prompt(f)}])
    text = ''.join(getattr(b, 'text', '') for b in msg.content)
    return parse(text)


def for_today(user, day, profile=None):
    """(quote dict, line or None) for Today. Never calls Claude."""
    from .models import WellnessProfile
    p = profile or WellnessProfile.objects.filter(user=user).first()
    prefs = (p.prefs if p else None) or {}
    d = prefs.get('daily_line') or {}
    if not prefs.get('line_off') and d.get('date') == day.isoformat() and \
            isinstance(d.get('quote'), int) and \
            0 <= d['quote'] < len(Q.QUOTES):
        return Q.QUOTES[d['quote']], d.get('line') or None
    return Q.for_day(user.pk, day), None


def make(profile, day, client=None):
    """Make today's line for one person if they want one and have none.
    Returns True when a line was made."""
    prefs = dict(profile.prefs or {})
    if prefs.get('line_off'):
        return False
    if (prefs.get('daily_line') or {}).get('date') == day.isoformat():
        return False
    tries = prefs.get('daily_line_try') or {}
    n = tries.get('n', 0) if tries.get('date') == day.isoformat() else 0
    if n >= MAX_TRIES:
        return False
    prefs['daily_line_try'] = {'date': day.isoformat(), 'n': n + 1}
    answer = None
    try:
        answer = ask(facts(profile.user, day), client=client)
    except Exception as exc:                              # noqa: BLE001
        logger.warning('Wellness daily line failed: %s', exc)
    if answer:
        prefs['daily_line'] = {'date': day.isoformat(),
                               'quote': answer['quote'],
                               'line': answer['line']}
    profile.prefs = prefs
    profile.save(update_fields=['prefs', 'updated_at'])
    return bool(answer)


def seen(profile, day):
    """Today notes the day it was last opened - once a day, one small
    write - so lines are made only for people still using Wellness. (Not
    last_login: a phone stays signed in for 30 days.)"""
    prefs = dict(profile.prefs or {})
    if prefs.get('seen') != day.isoformat():
        prefs['seen'] = day.isoformat()
        profile.prefs = prefs
        profile.save(update_fields=['prefs', 'updated_at'])


def due_people(now):
    """Profiles of active people who opened Wellness in the last two weeks
    and may see it."""
    from .models import WellnessProfile
    since = (now.date() - dt.timedelta(days=ACTIVE_DAYS)).isoformat()
    out = []
    for p in WellnessProfile.objects.select_related('user').filter(
            onboarded=True, user__is_active=True):
        seen_on = (p.prefs or {}).get('seen', '')
        # WL-5, 31 Oct - a recent login counts too, so the first night
        # after a release does not wait for Today to be opened once.
        login = p.user.last_login
        recent_login = bool(login and login.date().isoformat() >= since)
        if (seen_on >= since or recent_login) and \
                p.user.has_perm('auth.can_access_wellness'):
            out.append(p)
    return out


def key_present():
    from django.conf import settings
    return bool(getattr(settings, 'ANTHROPIC_API_KEY', None))


def run(now, client=None, write=print):
    """One pass: make the lines that are missing for today. Says plainly
    when the key is missing rather than spending the day's tries."""
    if client is None and not key_present():
        write('Wellness daily line: ANTHROPIC_API_KEY is not set on this '
              'service - no lines made.')
        return 0
    made = waiting = 0
    for p in due_people(now):
        if (p.prefs or {}).get('daily_line', {}).get('date') == \
                now.date().isoformat() or (p.prefs or {}).get('line_off'):
            continue
        waiting += 1
        if make(p, now.date(), client=client):
            made += 1
    if waiting:
        write('Wellness daily line: %d made, %d waiting for one.'
              % (made, waiting))
    return made
