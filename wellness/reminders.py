# -*- coding: utf-8 -*-
"""wellness/reminders.py - WL-4b, 30 Oct 2026. What reminds whom, when.

Run every 15 minutes by the wellness_reminders command (a Railway cron
service of its own). Each reminder is sent at most ONCE A DAY, at or
after its time and no more than LATE after it - so a slow or missed run
never sends a pile of stale nudges, and a run every five minutes would
send nothing twice. What was sent today is kept in the profile's prefs.

Only the phones a person allowed get anything, and only for:
    - a habit given a reminder time, on a day it is due and not yet done;
    - the evening check-in, at the person's chosen time, if not written;
    - the weigh-in, at the person's chosen time, if not weighed today;
    - the cycle tracker, a day before the expected window, only if its own
      setting is on - and then the words are only "A Wellness reminder"
      (approved design: discreet, never the word period).

Kind words, no guilt, nothing about missing. `due()` is pure.
"""
import datetime as dt

LATE = dt.timedelta(hours=2)
CYCLE_AT = dt.time(9, 0)
TITLE = 'Wellness'
CYCLE_WORDS = 'A Wellness reminder'


def due(now, items, sent):
    """The items to send now. `items` are dicts with key, at (a time),
    title, body, url; `sent` is the set of keys already sent today."""
    out = []
    for it in items:
        if it['key'] in sent or it['at'] is None:
            continue
        at = dt.datetime.combine(now.date(), it['at'], tzinfo=now.tzinfo)
        if at <= now < at + LATE:
            out.append(it)
    return out


def _hm(v):
    if not v:
        return None
    try:
        h, m = [int(x) for x in str(v).split(':')[:2]]
        return dt.time(h, m)
    except (TypeError, ValueError):
        return None


def items_for(user, now):
    """Everything that could remind this person today, with its time."""
    from . import cycle as CY
    from . import habits as H
    from .models import BodyMetric, Habit, JournalEntry, WellnessProfile
    day = now.date()
    out = []
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False,
                                      remind_at__isnull=False):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
        if day in done or not H.due_today(habit, done, day):
            continue
        out.append({'key': 'habit:%d' % habit.pk, 'at': habit.remind_at,
                    'title': TITLE,
                    'body': '%s - whenever you are ready.' % habit.name,
                    'url': '/wellness/'})
    prof = WellnessProfile.objects.filter(user=user).first()
    prefs = (prof.prefs if prof else None) or {}
    at = _hm(prefs.get('remind_checkin'))
    if at and not JournalEntry.objects.filter(user=user, date=day,
                                              kind='checkin').exists():
        out.append({'key': 'checkin', 'at': at, 'title': TITLE,
                    'body': 'How was today? Three questions, about a '
                            'minute.',
                    'url': '/wellness/journal/new/?kind=checkin'})
    at = _hm(prefs.get('remind_weigh'))
    if at and not BodyMetric.objects.filter(user=user, date=day,
                                            kind='weight').exists():
        out.append({'key': 'weigh', 'at': at, 'title': TITLE,
                    'body': 'Time to weigh in - before food is steadiest.',
                    'url': '/wellness/body/weigh/'})
    _rec, cprefs, days = CY.load(user)
    if cprefs.get('on') and cprefs.get('remind') and \
            not cprefs.get('locked'):
        s = CY.summary(days, day, cprefs)
        win = s.get('window')
        if win and win[0] - dt.timedelta(days=1) == day and \
                s['state'] in ('predicted', 'first_guess'):
            out.append({'key': 'cycle', 'at': CYCLE_AT, 'title': TITLE,
                        'body': CYCLE_WORDS, 'url': '/wellness/'})
    return out


def sent_today(prof, day):
    r = (prof.prefs or {}).get('reminded') or {}
    return set(r.get('keys') or []) if r.get('date') == day.isoformat() \
        else set()


def mark_sent(prof, day, keys):
    prefs = dict(prof.prefs or {})
    r = prefs.get('reminded') or {}
    have = set(r.get('keys') or []) if r.get('date') == day.isoformat() \
        else set()
    prefs['reminded'] = {'date': day.isoformat(),
                         'keys': sorted(have | set(keys))}
    prof.prefs = prefs
    prof.save(update_fields=['prefs', 'updated_at'])


def run(now, dry_run=False, write=print):
    """One pass for everybody with a phone allowed. Returns (sent, people)."""
    from . import push as P
    from .models import PushDevice, WellnessProfile
    users = {d.user for d in PushDevice.objects.select_related('user')
             if d.user.is_active}
    sent = 0
    for user in users:
        prof, _ = WellnessProfile.objects.get_or_create(user=user)
        todo = due(now, items_for(user, now), sent_today(prof, now.date()))
        if not todo:
            continue
        done = []
        for it in todo:
            if dry_run:
                write('DRY RUN: would remind user %s (%s)' % (user.pk,
                                                             it['key']))
                continue
            if P.send_to_user(user, it['title'], it['body'], it['url'],
                              tag=it['key']):
                sent += 1
            # Marked either way: a phone that cannot be reached now is
            # not tried again every quarter of an hour all day.
            done.append(it['key'])
        if done:
            mark_sent(prof, now.date(), done)
    return sent, len(users)
