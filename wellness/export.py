# -*- coding: utf-8 -*-
"""wellness/export.py - WL-19, 12 Nov 2026. Everything, as one ZIP.

Demetri, 12 Nov: "as well as an export function".

One spreadsheet (CSV, opens in Excel) per part of Wellness, plus a short
README. The journal is opened so it can be read - that file is NOT locked,
and the page says so before the download. Progress photos come too, if
asked for, as ordinary JPEGs. The cycle tracker's own download stays where
it is; its days come here as well when it is switched on.

Built in memory: a person's whole Wellness is a few hundred KB of text, and
photos at most a few MB each.
"""
import csv
import io
import zipfile

from . import journal as JN
from . import photos as PH
from .models import (BodyMetric, CalmSession, Habit, HabitLog, JournalEntry,
                     ProgressPhoto, WorkoutSession, WorkoutSet)


def _csv(rows, head):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(head)
    for r in rows:
        w.writerow(['' if v is None else v for v in r])
    # A BOM so Excel opens accents and Greek correctly.
    return '﻿' + buf.getvalue()


def files(user, journal=True, photos=False, cycle=True):
    """{name in the zip: text or bytes}."""
    out = {}
    habits = list(Habit.objects.filter(user=user).order_by('position', 'id'))
    out['habits.csv'] = _csv(
        [(h.name, h.get_kind_display(), h.target, h.unit,
          h.get_schedule_display(), h.started_on,
          'archived' if h.archived_at else ('paused' if h.paused else
                                            'active'))
         for h in habits],
        ['Habit', 'Kind', 'Target', 'Unit', 'Schedule', 'Started', 'Status'])
    out['habit_days.csv'] = _csv(
        [(l.date, l.habit.name, 'yes' if l.done else 'no', l.value)
         for l in HabitLog.objects.filter(habit__user=user)
         .select_related('habit').order_by('date', 'habit__position')],
        ['Date', 'Habit', 'Done', 'Amount'])
    out['body.csv'] = _csv(
        [(m.date, m.get_kind_display(), m.value, m.unit)
         for m in BodyMetric.objects.filter(user=user).order_by('date',
                                                                  'kind')],
        ['Date', 'Measure', 'Value', 'Unit'])
    sessions = list(WorkoutSession.objects.filter(user=user)
                    .order_by('date', 'started_at'))
    out['workouts.csv'] = _csv(
        [(s.date, s.name,
          int((s.finished_at - s.started_at).total_seconds() // 60)
          if s.finished_at else '', s.effort, s.calories, s.note)
         for s in sessions],
        ['Date', 'Workout', 'Minutes', 'Effort (1-10)', 'Calories', 'Note'])
    out['workout_sets.csv'] = _csv(
        [(x.session.date, x.session.name, x.exercise.name, x.set_no,
          x.weight, x.reps, x.seconds, x.distance_m,
          'yes' if x.is_pr else '')
         for x in WorkoutSet.objects.filter(session__user=user, done=True)
         .select_related('session', 'exercise')
         .order_by('session__date', 'session_id', 'position', 'set_no')],
        ['Date', 'Workout', 'Exercise', 'Set', 'Kg', 'Reps', 'Seconds',
         'Metres', 'Record'])
    out['calm.csv'] = _csv(
        [(c.date, c.get_kind_display(), c.practice, c.seconds)
         for c in CalmSession.objects.filter(user=user).order_by('date')],
        ['Date', 'Kind', 'Practice', 'Seconds'])
    if journal:
        rows = []
        for e in JournalEntry.objects.filter(user=user).order_by('date',
                                                                 'id'):
            w = JN.words(e)
            rows.append((e.date, e.get_kind_display(),
                         e.get_mood_display() if e.mood else '',
                         e.get_energy_display() if e.energy else '',
                         ' '.join('#' + t for t in (e.tags or [])),
                         w.get('preview') if w.get('locked') else
                         w.get('all_text', '')))
        out['journal.csv'] = _csv(
            rows, ['Date', 'Kind', 'Mood', 'Energy', 'Tags', 'Words'])
    if cycle:
        try:
            from . import cycle as C
            rec, prefs, days = C.load(user)
            if rec is not None and days:
                keys = sorted({k for d in days.values() for k in d})
                out['cycle.csv'] = _csv(
                    [[day] + [_flat(days[day].get(k)) for k in keys]
                     for day in sorted(days)], ['Date'] + keys)
        except Exception:                                # noqa: BLE001
            pass
    if photos:
        for p in ProgressPhoto.objects.filter(user=user).order_by('date',
                                                                   'id'):
            data = PH.read(p.stem, 'full')
            if data:
                out['photos/%s-%s-%d.jpg' % (p.date.isoformat(), p.pose,
                                             p.pk)] = data
    out['README.txt'] = README
    return out


def _flat(v):
    if isinstance(v, (list, tuple)):
        return '; '.join(str(x) for x in v)
    if isinstance(v, dict):
        return '; '.join('%s=%s' % kv for kv in sorted(v.items()))
    return v


def zipped(user, **kw):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files(user, **kw).items():
            z.writestr('wellness/' + name, data)
    return buf.getvalue()


README = '''Your Wellness, downloaded from Alivente Online.

Each .csv file opens in Excel or Google Sheets:
  habits.csv         your habits
  habit_days.csv     every day you ticked (or typed an amount for) a habit
  body.csv           weigh-ins and measurements
  workouts.csv       each workout: minutes, effort, calories, note
  workout_sets.csv   every set you ticked
  calm.csv           breathing, guided practice and quiet time
  journal.csv        your journal, opened so you can read it
  cycle.csv          your cycle days, if the tracker is on
  photos/            your progress photos, if you chose to include them

THIS FILE IS NOT LOCKED. Inside Wellness your journal and photos are
encrypted; here they are ordinary files. Keep it somewhere private.
'''
