# -*- coding: utf-8 -*-
"""wellness/cycle.py - CY-1, 30 Oct 2026. The rules of the cycle tracker.

Demetri's decisions of 30 Oct (08:49):
  1. Opt-in per person, OFF by default.
  2. The fertile-window estimate is offered but OFF by default, and is
     always labelled "an estimate, not contraception".
  3. The WHOLE record is encrypted - not just the notes. Every logged day
     and every setting lives inside two Fernet tokens on one row
     (models.CycleRecord); there is no plain date column to give a period
     away. Only load() and save() below open or close them.
  4. Placed after Workouts, before W-4.

Predictions are a WINDOW, never a single day: the median of the last six
cycles, widened by how much they vary. Until two cycles are logged the
page says it is still learning. The doctor flags are gentle, follow the
adult ranges in common clinical use (cycles of 21 to 35 days, periods of
up to 7 days, three months without one), and only ever suggest mentioning
it to a doctor. Pregnancy and hormonal-contraception modes switch the
predictions and the flags off, because neither means anything then.

Pure functions where it matters, so the suite drives them without a
database.
"""
import datetime as dt

from . import crypto

FLOWS = [
    ('spotting', 'Spotting'),
    ('light', 'Light'),
    ('medium', 'Medium'),
    ('heavy', 'Heavy'),
]
FLOW_NAMES = dict(FLOWS)
# Spotting alone does not start a period.
BLEED = ('light', 'medium', 'heavy')
FLOW_RANK = {'spotting': 0, 'light': 1, 'medium': 2, 'heavy': 3}

SYMPTOMS = [
    ('cramps', 'Cramps'),
    ('headache', 'Headache'),
    ('bloating', 'Bloating'),
    ('tender', 'Tender breasts'),
    ('back', 'Back pain'),
    ('tired', 'Tired'),
    ('acne', 'Acne'),
    ('cravings', 'Cravings'),
    ('nausea', 'Nausea'),
    ('low_mood', 'Low mood'),
    ('poor_sleep', 'Poor sleep'),
]
SYMPTOM_NAMES = dict(SYMPTOMS)

MODES = [
    ('normal', 'Tracking my cycle'),
    ('pregnant', 'Pregnant'),
    ('hormonal', 'On hormonal contraception'),
]
MODE_NAMES = dict(MODES)

DEFAULT_SETTINGS = {'on': False, 'fertile': False, 'mode': 'normal',
                    'remind': False}

# A gap of one dry day inside a period does not end it.
JOIN_GAP = 2
# Cycles outside this are almost always a missed log, not a cycle, so
# they never feed a prediction (they still count for the flags).
PREDICT_MIN, PREDICT_MAX = 15, 60
RECENT = 6
SHORT, LONG, LONG_PERIOD, MISSED_DAYS = 21, 35, 7, 90
FERTILE_LABEL = 'An estimate, not contraception.'
# The doctor-visit grid: four days before day 1 to day 5.
AROUND = [-4, -3, -2, -1, 1, 2, 3, 4, 5]


# --------------------------------------------------------------------------
# The locked record
# --------------------------------------------------------------------------
def load(user):
    """(record or None, settings, days). Nothing is created by looking."""
    from .models import CycleRecord
    rec = CycleRecord.objects.filter(user=user).first()
    settings = dict(DEFAULT_SETTINGS)
    days = {}
    if rec is not None:
        s = crypto.open_(rec.prefs)
        if s.get('locked'):
            settings['locked'] = True
        else:
            settings.update({k: s[k] for k in DEFAULT_SETTINGS if k in s})
        d = crypto.open_(rec.days)
        if d.get('locked'):
            settings['locked'] = True
        else:
            days = d.get('days', {})
    return rec, settings, days


def save(user, settings=None, days=None):
    from .models import CycleRecord
    rec, old_s, old_d = load(user)
    if rec is None:
        rec = CycleRecord(user=user)
    s = dict(old_s if settings is None else settings)
    s.pop('locked', None)
    rec.prefs = crypto.seal({k: s.get(k, v)
                                for k, v in DEFAULT_SETTINGS.items()})
    rec.days = crypto.seal({'days': old_d if days is None else days})
    rec.save()
    return rec


def is_on(user):
    """For the bottom bar. Opens only the small settings token."""
    from .models import CycleRecord
    rec = CycleRecord.objects.filter(user=user).only('prefs').first()
    if rec is None:
        return False
    return bool(crypto.open_(rec.prefs).get('on'))


# --------------------------------------------------------------------------
# Reading the days
# --------------------------------------------------------------------------
def _d(s):
    return dt.date.fromisoformat(s)


def clean_day(post_like):
    """A day's entry from a form: flow, symptoms, pain, relief, note.
    Returns {} when nothing was logged, which removes the day."""
    flow = post_like.get('flow') or ''
    flow = flow if flow in FLOW_NAMES else ''
    sym = [s for s in post_like.getlist('sym') if s in SYMPTOM_NAMES] \
        if hasattr(post_like, 'getlist') else \
        [s for s in post_like.get('sym', []) if s in SYMPTOM_NAMES]
    pain = post_like.get('pain')
    try:
        pain = int(pain)
        pain = pain if 0 <= pain <= 10 else None
    except (TypeError, ValueError):
        pain = None
    relief = bool(post_like.get('relief'))
    note = (post_like.get('note') or '').strip()[:1000]
    out = {}
    if flow:
        out['flow'] = flow
    if sym:
        out['sym'] = sym
    if pain:
        out['pain'] = pain
    if relief:
        out['relief'] = True
    if note:
        out['note'] = note
    return out


def periods(days):
    """[(first_day, last_day)] of each period, oldest first."""
    dates = sorted(_d(k) for k, v in days.items()
                   if v.get('flow') in BLEED)
    runs = []
    for d in dates:
        if runs and (d - runs[-1][1]).days <= JOIN_GAP:
            runs[-1][1] = d
        else:
            runs.append([d, d])
    return [(a, b) for a, b in runs]


def cycles(ps):
    """One dict per period: start, its period length, and the cycle length
    to the next start (None for the current one)."""
    out = []
    for i, (a, b) in enumerate(ps):
        nxt = ps[i + 1][0] if i + 1 < len(ps) else None
        out.append({'start': a, 'end': b,
                    'period': (b - a).days + 1,
                    'length': (nxt - a).days if nxt else None})
    return out


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    m = n // 2
    return xs[m] if n % 2 else (xs[m - 1] + xs[m]) / 2.0


def recent_lengths(cs, n=RECENT):
    done = [c['length'] for c in cs if c['length']]
    return [x for x in done if PREDICT_MIN <= x <= PREDICT_MAX][-n:]


def summary(days, today, settings):
    """Everything the overview needs. state is one of
    empty, learning, first_guess, predicted, late, pregnant, hormonal."""
    ps = periods(days)
    cs = cycles(ps)
    mode = settings.get('mode', 'normal')
    out = {'state': 'empty', 'cycles': cs, 'cycle_day': None,
           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'flags': flags(cs, today, mode)}
    if not ps:
        if mode != 'normal':
            out['state'] = mode
        return out
    last_a, last_b = ps[-1]
    out['cycle_day'] = (today - last_a).days + 1
    if (today - last_b).days <= 1 and today >= last_a:
        logged_today = days.get(today.isoformat(), {}).get('flow') in BLEED
        if logged_today or today == last_b:
            out['in_period'] = True
            out['period_day'] = (today - last_a).days + 1
    lengths = recent_lengths(cs)
    periods_n = [c['period'] for c in cs[-RECENT:]]
    out['avg_period'] = int(round(median(periods_n)))
    if lengths:
        out['avg_cycle'] = int(round(median(lengths)))
        out['range'] = (min(lengths), max(lengths))
    if mode != 'normal':
        out['state'] = mode
        return out
    if not lengths:
        out['state'] = 'learning'
        return out
    med = median(lengths)
    if len(lengths) == 1:
        spread = 3
        out['state'] = 'first_guess'
    else:
        lo, hi = min(lengths), max(lengths)
        spread = max(1, min(4, int((hi - lo + 1) // 2)))
        out['state'] = 'predicted'
    start = last_a + dt.timedelta(days=int(round(med)) - spread)
    end = last_a + dt.timedelta(days=int(round(med)) + spread)
    if today > end and not out['in_period']:
        out['state'] = 'late'
        out['late_by'] = (today - (last_a + dt.timedelta(
            days=int(round(med))))).days
    out['window'] = (start, end)
    if settings.get('fertile') and out['state'] in ('predicted',
                                                     'first_guess'):
        mid = last_a + dt.timedelta(days=int(round(med)))
        ov = mid - dt.timedelta(days=14)
        out['fertile'] = (ov - dt.timedelta(days=5),
                          ov + dt.timedelta(days=1))
    return out


def flags(cs, today, mode='normal'):
    """Gentle notes, each ending in the doctor suggestion. Off outside
    the normal mode."""
    if mode != 'normal' or not cs:
        return []
    out = []
    recent = [c for c in cs[-RECENT - 1:] if c['length']][-RECENT:]
    odd = [c for c in recent if c['length'] < SHORT or
           LONG < c['length'] <= PREDICT_MAX]
    if len(recent) >= 3 and len(odd) >= 2:
        out.append('Several recent cycles were shorter than %d or longer '
                   'than %d days.' % (SHORT, LONG))
    if any(c['period'] > LONG_PERIOD for c in cs[-RECENT:]):
        out.append('A recent period lasted more than %d days.'
                   % LONG_PERIOD)
    if (today - cs[-1]['start']).days > MISSED_DAYS:
        out.append('It has been more than three months since your last '
                   'logged period.')
    return out


# --------------------------------------------------------------------------
# Words
# --------------------------------------------------------------------------
def _span(a, b):
    if a.month == b.month:
        return '%d – %d %s' % (a.day, b.day, b.strftime('%B'))
    return '%d %s – %d %s' % (a.day, a.strftime('%b'), b.day,
                              b.strftime('%b'))


def span_words(lo, hi, joint=' to '):
    """'29' when every value was the same, else '28 to 31'."""
    return '%d' % lo if lo == hi else '%d%s%d' % (lo, joint, hi)


def headline(s):
    """(big line, small line) for the overview card."""
    st = s['state']
    if st == 'empty':
        return ('Log your next period',
                'Tap Log today on the first day. Predictions start after '
                'two cycles.')
    if st == 'pregnant':
        return ('Pregnancy mode', 'Predictions are paused. You can still '
                'log symptoms and notes.')
    if st == 'hormonal':
        return ('Hormonal contraception', 'Predictions are paused - '
                'bleeds on the pill are not periods. Log anything you '
                'like.')
    if s['in_period']:
        return ('Period, day %d' % s['period_day'],
                'Log each day you bleed, and how heavy.')
    if st == 'learning':
        return ('Learning your cycle', 'After your next period starts, '
                'Wellness can estimate the one after.')
    a, b = s['window']
    if st == 'late':
        return ('A few days later than usual',
                'Cycles vary - stress, travel and illness all move them. '
                'Log the day it starts.')
    small = ('A first guess from one cycle.' if st == 'first_guess' else
             'From your last %d cycles. Usually %s days.'
             % (len([c for c in s['cycles'] if c['length']][-RECENT:]),
                span_words(*s['range'], joint='–')))
    return ('Next period around %s' % _span(a, b), small)


def today_line(s, today):
    """The discreet Today card, or None. Never says the word period."""
    if s['state'] in ('empty',):
        return None
    if s['in_period']:
        return 'Day %d - tap to log today' % s['period_day']
    if s['window']:
        a, b = s['window']
        to = (a - today).days
        if 0 < to <= 3:
            return 'Expected in about %d day%s' % (to, '' if to == 1 else 's')
        if a <= today <= b:
            return 'Expected around now'
    if s['cycle_day']:
        return 'Cycle day %d' % s['cycle_day']
    return None


# --------------------------------------------------------------------------
# The calendar and the ring
# --------------------------------------------------------------------------
def month_grid(year, month, days, s, today):
    """Weeks (Monday first) of cells: n, date, kind, today, logged."""
    first = dt.date(year, month, 1)
    start = first - dt.timedelta(days=first.weekday())
    win = s.get('window')
    fer = s.get('fertile')
    weeks = []
    d = start
    while True:
        week = []
        for _ in range(7):
            e = days.get(d.isoformat(), {})
            kind = ''
            if e.get('flow') in BLEED:
                kind = 'period'
            elif e.get('flow') == 'spotting':
                kind = 'spotting'
            elif win and win[0] <= d <= win[1] and d >= today:
                kind = 'expected'
            elif fer and fer[0] <= d <= fer[1]:
                kind = 'fertile'
            week.append({'n': d.day, 'date': d, 'in': d.month == month,
                         'kind': kind, 'today': d == today,
                         'logged': bool(e), 'future': d > today})
            d += dt.timedelta(days=1)
        weeks.append(week)
        if d.month != month and d > first:
            break
    return weeks


def ring(s, r=46):
    """Arc lengths for the overview ring: the period part and the
    position of today."""
    import math
    c = 2 * math.pi * r
    length = s.get('avg_cycle') or 28
    day = s.get('cycle_day') or 0
    per = s.get('avg_period') or 5
    return {'circ': '%.1f' % c,
            'period': '%.1f %.1f' % (c * min(per, length) / float(length), c),
            'today': '%.1f %.1f' % (c * min(day, length) / float(length), c),
            'of': length}


# --------------------------------------------------------------------------
# Patterns and the doctor report
# --------------------------------------------------------------------------
def bars(cs, n=RECENT):
    """The last n complete cycles for the bar chart."""
    done = [c for c in cs if c['length']][-n:]
    if not done:
        return []
    top = max(c['length'] for c in done)
    out = []
    for c in done:
        h = int(round(c['length'] / float(top) * 96))
        out.append({'len': c['length'], 'period': c['period'],
                    'm': c['start'].strftime('%b'), 'h': h,
                    'p': int(round(c['period'] / float(c['length']) * h))})
    return out


def around(days, cs, n=RECENT):
    """Symptoms around day 1 of the last n periods. Needs three periods.
    Rows of (name, [share 0..1 per AROUND offset]) plus one plain line."""
    starts = [c['start'] for c in cs][-n:]
    if len(starts) < 3:
        return [], ''
    rows = []
    for key, name in SYMPTOMS:
        cells = []
        for off in AROUND:
            delta = off if off < 0 else off - 1
            hit = 0
            for a in starts:
                e = days.get((a + dt.timedelta(days=delta)).isoformat(), {})
                if key in e.get('sym', []):
                    hit += 1
            cells.append(hit / float(len(starts)))
        if any(cells):
            rows.append((name, cells))
    rows.sort(key=lambda r: -sum(r[1]))
    rows = rows[:5]
    words = []
    for name, cells in rows[:3]:
        peak = max(cells)
        if peak < 0.5:
            continue
        off = AROUND[cells.index(peak)]
        noun, verb = _noun(name)
        if off < 0:
            words.append('%s often start%s %d day%s before your period.'
                         % (noun, '' if verb == 'are' else 's', -off,
                            '' if off == -1 else 's'))
        else:
            words.append('%s %s most common on day %d.' % (noun, verb, off))
    return rows, ' '.join(words)


# How each symptom reads at the start of a sentence.
_NOUNS = {'Cramps': ('Cramps', 'are'), 'Headache': ('Headaches', 'are'),
          'Bloating': ('Bloating', 'is'),
          'Tender breasts': ('Tender breasts', 'are'),
          'Back pain': ('Back pain', 'is'), 'Tired': ('Tiredness', 'is'),
          'Acne': ('Acne', 'is'), 'Cravings': ('Cravings', 'are'),
          'Nausea': ('Nausea', 'is'), 'Low mood': ('Low mood', 'is'),
          'Poor sleep': ('Poor sleep', 'is')}


def _noun(name):
    return _NOUNS.get(name, (name, 'is'))


def report(days, cs, n, notes=False):
    """The printable page: one row per cycle, newest first."""
    rows = []
    for c in [c for c in cs][-n:][::-1]:
        span = [c['start'] + dt.timedelta(days=i)
                for i in range(c['period'])]
        flows = [days.get(d.isoformat(), {}).get('flow') for d in span]
        heavy = sum(1 for f in flows if f == 'heavy')
        top = max((FLOW_RANK.get(f, -1) for f in flows), default=-1)
        sym = {}
        pains = []
        last = c['start'] + dt.timedelta(days=(c['length'] or 1) - 1)
        d = c['start']
        while d <= last:
            e = days.get(d.isoformat(), {})
            for k in e.get('sym', []):
                sym[k] = sym.get(k, 0) + 1
            if e.get('pain'):
                pains.append(e['pain'])
            d += dt.timedelta(days=1)
        common = [SYMPTOM_NAMES[k] for k, _ in
                  sorted(sym.items(), key=lambda kv: -kv[1])[:3]]
        rows.append({'start': c['start'], 'length': c['length'],
                     'period': c['period'], 'heavy': heavy,
                     'heaviest': [k for k, v in FLOW_RANK.items()
                                  if v == top][0] if top >= 0 else '',
                     'pain': max(pains) if pains else None,
                     'common': common})
    lengths = [r['length'] for r in rows if r['length']]
    note_rows = []
    if notes and cs:
        since = cs[-n:][0]['start'] if cs[-n:] else None
        for k in sorted(days):
            e = days[k]
            if e.get('note') and since and _d(k) >= since:
                note_rows.append((_d(k), e['note']))
    return {'rows': rows,
            'avg_cycle': int(round(median(lengths))) if lengths else None,
            'range': (min(lengths), max(lengths)) if lengths else None,
            'avg_period': int(round(median([r['period'] for r in rows])))
            if rows else None,
            'notes': note_rows}
