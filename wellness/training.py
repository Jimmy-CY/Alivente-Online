# -*- coding: utf-8 -*-
"""wellness/training.py - WL-3, 30 Oct 2026. The rules of the workout log.

From the proposal's research (Hevy, Strong and the progressive-overload
literature): show last time's numbers beside every set, rest between
sets, celebrate a record the moment it happens, and nudge the weight up
only when the top of the rep range is reached on every set (double
progression) - rounded to weights the person actually owns.

Pure functions where it matters, so the suite drives them without a
database.
"""
from decimal import Decimal

# Epley's estimate of a one-rep max. Past 12 reps the estimate stops
# meaning much, so none is given.
E1RM_MAX_REPS = 12

DEFAULT_DUMBBELLS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22.5, 25]
DEFAULT_KETTLEBELLS = [8, 12, 16, 20, 24]


def e1rm(weight, reps):
    if weight is None or not reps or reps > E1RM_MAX_REPS:
        return None
    w = float(weight)
    return w if reps == 1 else w * (1 + reps / 30.0)


def owned_weights(equipment_kind, kit):
    """The weights this person can actually load, ascending."""
    kit = kit or {}
    if equipment_kind == 'dumbbell':
        ws = kit.get('dumbbells') or DEFAULT_DUMBBELLS
    elif equipment_kind == 'kettlebell':
        ws = kit.get('kettlebells') or DEFAULT_KETTLEBELLS
    elif equipment_kind == 'barbell':
        top = float(kit.get('barbell_max') or 100)
        step = float(kit.get('plate_step') or 2.5)
        ws, w = [], step
        while w <= top + 1e-9:
            ws.append(round(w, 2))
            w += step
    else:
        return []
    return sorted({float(w) for w in ws})


def next_weight(current, equipment_kind, kit):
    """The next weight up that is owned, or None at the top of the rack."""
    ws = owned_weights(equipment_kind, kit)
    cur = float(current or 0)
    for w in ws:
        if w > cur + 1e-9:
            return w
    return None


def suggest(rep_min, rep_max, last_sets, equipment_kind, kit):
    """Double progression. `last_sets` = [(weight, reps), ...] of the last
    session's done working sets. Returns {'weight', 'reps', 'why'}.

    WL-17, 12 Nov 2026 - one number works too (rep_min == rep_max: "3 sets
    of 10"): every rep on every set and the next weight up is suggested.
    With no weight (reps only), every rep on every set suggests one more."""
    done = [(w, r) for w, r in last_sets if r]
    if not done:
        return {'weight': None, 'reps': rep_min, 'why': 'first'}
    weight = max((w for w, _ in done if w is not None), default=None)
    at_top = [r for w, r in done if w == weight]
    if at_top and all(r >= rep_max for r in at_top):
        if weight is None:
            return {'weight': None, 'reps': max(at_top) + 1,
                    'why': 'more_reps'}
        up = next_weight(weight, equipment_kind, kit) if weight else None
        if up:
            return {'weight': up, 'reps': rep_min, 'why': 'up'}
        return {'weight': weight, 'reps': rep_max, 'why': 'top'}
    return {'weight': weight, 'reps': min(rep_max, max(at_top or [0]) + 1),
            'why': 'reps'}


# --------------------------------------------------------------------------
# WL-17, 12 Nov 2026 - time in the units people use. Demetri, 08:01: "For
# Zumba or other dances, would we would not measure in seconds?? Maybe 3
# sets of 15 minutes with 5 minute rest between??"
# --------------------------------------------------------------------------
HOLD_STEP = 5      # seconds longer, once every set was held in full


def in_minutes(exercise):
    """Cardio, dance and sports are timed in minutes; a hold (a plank) in
    seconds."""
    return exercise.kind in ('time', 'distance') and \
        exercise.muscle in ('cardio', 'sport')


def suggest_hold(target, last_seconds):
    """A hold: every set held for the whole target last time - a little
    longer today. Returns (seconds, why)."""
    done = [s for s in last_seconds if s]
    if target and done and all(s >= target for s in done):
        return max(done) + HOLD_STEP, 'longer'
    return target, ''


def item_words(item):
    """'3 × 10', '3 × 8–12', '3 × 45 s', '1 × 45 min' - a routine line."""
    ex = item.exercise
    if ex.kind in ('time', 'distance'):
        secs = item.seconds or 0
        if in_minutes(ex):
            return '%d × %d min' % (item.sets, secs // 60)
        return '%d × %d s' % (item.sets, secs)
    if item.rep_min == item.rep_max:
        reps = '%d' % item.rep_max
    else:
        reps = '%d–%d' % (item.rep_min, item.rep_max)
    return '%d × %s' % (item.sets, reps)


def rest_words(seconds, minutes=False):
    if minutes or (seconds and seconds >= 120 and seconds % 60 == 0):
        return '%d min' % (seconds // 60)
    return '%d s' % seconds


def records(sets):
    """Best-ever numbers from done sets [(weight, reps, seconds, metres)]."""
    best = {'weight': None, 'e1rm': None, 'reps_at': {}, 'seconds': None,
            'metres': None, 'reps': None}
    for w, r, s, m in sets:
        if w is not None and r:
            wf = float(w)
            if best['weight'] is None or wf > best['weight']:
                best['weight'] = wf
            e = e1rm(wf, r)
            if e and (best['e1rm'] is None or e > best['e1rm']):
                best['e1rm'] = e
            if r > best['reps_at'].get(wf, 0):
                best['reps_at'][wf] = r
        elif r and w is None:
            if best['reps'] is None or r > best['reps']:
                best['reps'] = r
        if s and (best['seconds'] is None or s > best['seconds']):
            best['seconds'] = s
        if m and (best['metres'] is None or m > best['metres']):
            best['metres'] = m
    return best


def is_record(set_, best):
    """Did (weight, reps, seconds, metres) beat `best`? A first-ever set is
    not a record - there is nothing to beat yet. Returns the reason or ''."""
    w, r, s, m = set_
    if w is not None and r:
        wf = float(w)
        if best['weight'] is None and not best['reps_at']:
            return ''
        if best['weight'] is not None and wf > best['weight']:
            return 'Heaviest yet: %s kg' % _kg(wf)
        if r > best['reps_at'].get(wf, 0) and wf in best['reps_at']:
            return 'Most reps at %s kg: %d' % (_kg(wf), r)
        e = e1rm(wf, r)
        if e and best['e1rm'] and e > best['e1rm'] + 1e-9:
            return 'Best estimated one-rep max: %s kg' % _kg(round(e, 1))
        return ''
    if r and w is None and best['reps'] and r > best['reps']:
        return 'Most reps yet: %d' % r
    if s and best['seconds'] and s > best['seconds']:
        return 'Longest yet: %s' % duration(s)
    if m and best['metres'] and m > best['metres']:
        return 'Furthest yet: %.2f km' % (m / 1000.0)
    return ''


def volume(sets):
    """Total kilos lifted: weight x reps over done weighted sets."""
    return sum(float(w) * r for w, r in sets if w is not None and r)


def duration(seconds):
    seconds = int(seconds or 0)
    if seconds >= 3600:
        return '%d:%02d:%02d' % (seconds // 3600, seconds % 3600 // 60,
                                 seconds % 60)
    return '%d:%02d' % (seconds // 60, seconds % 60)


def _kg(v):
    v = float(v)
    return ('%d' % v) if v == int(v) else ('%s' % Decimal(str(v)).normalize())
