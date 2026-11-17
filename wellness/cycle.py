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
    # CY-5, 17 Nov 2026 - a fifth, darkest shade (the approved redesign).
    ('very_heavy', 'Very heavy'),
]
FLOW_NAMES = dict(FLOWS)
# Spotting alone does not start a period.
BLEED = ('light', 'medium', 'heavy', 'very_heavy')
FLOW_RANK = {'spotting': 0, 'light': 1, 'medium': 2, 'heavy': 3,
             'very_heavy': 4}
HEAVY = ('heavy', 'very_heavy')

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
    # CY-4, 1 Nov 2026 - Demetri, 05:48: "let's add more symptoms to ours
    # as well." Twenty-two in all, and six more in perimenopause.
    ('mood_swings', 'Mood swings'),
    ('irritable', 'Irritable'),
    ('anxious', 'Anxious'),
    ('tearful', 'Tearful'),
    ('focus', 'Hard to focus'),
    ('dizzy', 'Dizziness'),
    ('pelvic_pain', 'Pelvic pain'),
    ('constipation', 'Constipation'),
    ('diarrhoea', 'Diarrhoea'),
    ('swelling', 'Swollen hands or feet'),
    ('hungry', 'Hungrier than usual'),
]
SYMPTOM_NAMES = dict(SYMPTOMS)

# CY-3, 31 Oct 2026 - more to log, each switched on in the tracker's
# settings (Demetri, 15:46: mood, energy, sleep, cravings, discharge and
# your own tags; cravings is already a symptom). No fertility signs.
TRACK = [
    ('mood', 'Mood'),
    ('energy', 'Energy'),
    ('sleep', 'Sleep'),
    ('discharge', 'Discharge'),
    # CY-5, 17 Nov 2026 - Demetri: "including sex tracking (as
    # suggested)". Off until switched on; never in the day's summary
    # line, the doctor report or anything sent.
    ('sex', 'Sex'),
    ('tags', 'My own tags'),
]
TRACK_KEYS = [k for k, _n in TRACK]
MOODS = [('great', 'Great'), ('good', 'Good'), ('okay', 'Okay'),
         ('low', 'Low'), ('very_low', 'Very low')]
ENERGY = [('low', 'Low'), ('steady', 'Steady'), ('high', 'High')]
SLEEP = [('poor', 'Poor'), ('okay', 'Okay'), ('good', 'Good')]
DISCHARGE = [('dry', 'Dry'), ('sticky', 'Sticky'), ('creamy', 'Creamy'),
             ('watery', 'Watery'), ('clear', 'Clear and stretchy')]
# CY-5 - more than one can be true of a day, so these are ticks.
SEX = [('protected', 'Protected'), ('unprotected', 'Unprotected'),
       ('none', 'No sex'), ('high_drive', 'High drive'),
       ('low_drive', 'Low drive')]
SEX_NAMES = dict(SEX)
CHOICES = {'mood': dict(MOODS), 'energy': dict(ENERGY),
           'sleep': dict(SLEEP), 'discharge': dict(DISCHARGE)}
MAX_TAGS, TAG_LEN = 12, 24
# What counts towards the PMS window: the symptoms that tend to come
# before a period, and a low mood however it was logged.
PMS_KEYS = ('cramps', 'headache', 'bloating', 'tender', 'tired', 'acne',
            'cravings', 'low_mood', 'poor_sleep', 'low_energy',
            'mood_swings', 'irritable', 'anxious', 'tearful', 'hungry',
            'swelling')
PMS_BACK = 7
# The calendar looks this many months ahead.
MONTHS_AHEAD = 6

MODES = [
    ('normal', 'Tracking my cycle'),
    # CY-4, 1 Nov 2026 - Demetri, 05:43: "Can we add a Perimenopause mode".
    # Irregular cycles expected: predictions are a rough, wider window,
    # never "late", no fertile estimate and no phases; the perimenopause
    # symptoms are offered when logging.
    ('perimenopause', 'In perimenopause'),
    ('pregnant', 'Pregnant'),
    ('hormonal', 'On hormonal contraception'),
]
# The symptoms offered in perimenopause mode, as well as the usual ones.
PERI_SYMPTOMS = [
    ('hot_flush', 'Hot flushes'),
    ('night_sweats', 'Night sweats'),
    ('brain_fog', 'Brain fog'),
    ('joint_aches', 'Joint aches'),
    ('dryness', 'Vaginal dryness'),
    ('palpitations', 'Palpitations'),
]
# Perimenopause: the expected window is at least this many days either side.
PERI_SPREAD = 6
MODE_NAMES = dict(MODES)
SYMPTOM_NAMES.update(dict(PERI_SYMPTOMS))
PREDICTING = ('normal', 'perimenopause')

DEFAULT_SETTINGS = {'on': False, 'fertile': False, 'mode': 'normal',
                    'remind': False,
                    # CY-2 - a period begun with one tap and not yet
                    # ended (an ISO date), and the board ideas hidden.
                    'open_period': '', 'hidden_tips': (),
                    # CY-3 - more to log, your own tags, the pill
                    # reminder time and the logging nudge.
                    'track': (), 'tags': (), 'pill_at': '',
                    'nudge': False,
                    # CY-5 - the likely ovulation day, shown only with
                    # the fertile estimate. Off by default.
                    'ovulation': False}

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


def clean_tags(raw):
    """Your own tags from a comma-separated line: short, unique, at most
    MAX_TAGS, in the order typed."""
    out = []
    for t in (raw or '').split(','):
        t = ' '.join(t.split())[:TAG_LEN]
        if t and t.lower() not in [x.lower() for x in out]:
            out.append(t)
    return out[:MAX_TAGS]


def clean_day(post_like, tags=()):
    """A day's entry from a form: flow, symptoms, pain, relief, note -
    and, CY-3, mood, energy, sleep, discharge and your own tags.
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
    for k, names in CHOICES.items():
        v = post_like.get(k) or ''
        if v in names:
            out[k] = v
    got = post_like.getlist('tag') if hasattr(post_like, 'getlist') \
        else post_like.get('tag', [])
    mine = [t for t in got if t in set(tags or ())]
    if mine:
        out['tags'] = mine
    sx = post_like.getlist('sex') if hasattr(post_like, 'getlist') \
        else post_like.get('sex', [])
    sx = [k for k, _n in SEX if k in set(sx or ())]
    if sx:
        out['sex'] = sx
    return out


def has(e, key):
    """Does the day e show key? A symptom, a low mood or poor sleep however
    logged, low energy, or 'tag:<name>' for your own tags."""
    if key.startswith('tag:'):
        return key[4:] in e.get('tags', [])
    if key in e.get('sym', []):
        return True
    if key == 'low_mood':
        return e.get('mood') in ('low', 'very_low')
    if key == 'poor_sleep':
        return e.get('sleep') == 'poor'
    if key == 'low_energy':
        return e.get('energy') == 'low'
    return False


def pattern_keys(tags=()):
    """(key, name) for everything Patterns can show."""
    return list(SYMPTOMS) + list(PERI_SYMPTOMS) + \
        [('low_energy', 'Low energy')] + \
        [('tag:' + t, t) for t in (tags or ())]


def pms(days, cs, n=RECENT):
    """How many days before a period the usual signs begin: the earliest
    day (up to PMS_BACK before) from which, every day up to the period,
    at least half of the last periods had one. None without three."""
    starts = [c['start'] for c in cs][-n:]
    if len(starts) < 3:
        return None
    first = None
    for back in range(1, PMS_BACK + 1):
        hit = 0
        for a in starts:
            e = days.get((a - dt.timedelta(days=back)).isoformat(), {})
            if any(has(e, k) for k in PMS_KEYS):
                hit += 1
        if hit * 2 >= len(starts):
            first = back
        else:
            break
    return first


def bleeding_now(s):
    """From a summary: is today a bleeding day? (A function, so the
    reminder code never names it - test_wellness_five holds reminders.py
    to that.)"""
    return bool(s.get('in_period'))


def future_windows(s, months=MONTHS_AHEAD):
    """The expected windows from now on, months ahead, each one usual
    cycle after the last. Only with a prediction."""
    win, med = s.get('window'), s.get('avg_cycle')
    if not win or not med or s['state'] not in ('predicted', 'first_guess',
                                                 'late'):
        return []
    out, i = [], 0
    while i <= int(months * 31 / med) + 1:
        step = dt.timedelta(days=med * i)
        out.append((win[0] + step, win[1] + step))
        i += 1
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
    out = {'state': 'empty', 'cycles': cs, 'cycle_day': None, 'soft': False,
           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'ovulation': None,
           'flags': flags(cs, today, mode)}
    if not ps:
        if mode not in PREDICTING:
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
    if mode not in PREDICTING:
        out['state'] = mode
        return out
    out['soft'] = mode == 'perimenopause'
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
    if out['soft']:
        spread = max(spread, PERI_SPREAD)
    start = last_a + dt.timedelta(days=int(round(med)) - spread)
    end = last_a + dt.timedelta(days=int(round(med)) + spread)
    if today > end and not out['in_period'] and not out['soft']:
        out['state'] = 'late'
        out['late_by'] = (today - (last_a + dt.timedelta(
            days=int(round(med))))).days
    out['window'] = (start, end)
    if settings.get('fertile') and not out['soft'] and \
            out['state'] in ('predicted', 'first_guess'):
        mid = last_a + dt.timedelta(days=int(round(med)))
        ov = mid - dt.timedelta(days=14)
        out['fertile'] = (ov - dt.timedelta(days=5),
                          ov + dt.timedelta(days=1))
        # CY-5 - the likely day itself, only if asked for as well.
        if settings.get('ovulation'):
            out['ovulation'] = ov
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
    if s.get('soft'):
        # CY-4 - perimenopause: a rough guide, never "late".
        return ('Perhaps around %s' % _span(a, b),
                'In perimenopause cycles change a lot - this is a rough '
                'guide from your recent cycles.')
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
def month_grid(year, month, days, s, today, windows=None, pms_days=None):
    """Weeks (Monday first) of cells: n, date, kind, today, logged.
    CY-3: windows (months ahead) and the PMS days before each."""
    first = dt.date(year, month, 1)
    start = first - dt.timedelta(days=first.weekday())
    win = s.get('window')
    fer = s.get('fertile')
    wins = windows or ([win] if win else [])
    pms_spans = [(w[0] - dt.timedelta(days=pms_days), w[0] -
                  dt.timedelta(days=1)) for w in wins] if pms_days else []
    weeks = []
    d = start
    while True:
        week = []
        for _ in range(7):
            e = days.get(d.isoformat(), {})
            kind = ''
            ov = s.get('ovulation')
            if e.get('flow') in BLEED:
                kind = 'period'
            elif e.get('flow') == 'spotting':
                kind = 'spotting'
            elif d >= today and any(w[0] <= d <= w[1] for w in wins):
                kind = 'expected'
            elif d >= today and any(p[0] <= d <= p[1] for p in pms_spans):
                kind = 'pms'
            elif fer and fer[0] <= d <= fer[1]:
                kind = 'fertile'
            week.append({'n': d.day, 'date': d, 'in': d.month == month,
                         'kind': kind, 'today': d == today,
                         'logged': bool(e), 'future': d > today,
                         # CY-5 - the flow's own shade, the ovulation
                         # day, and a dot for each kind of thing logged.
                         'flow': e.get('flow', ''),
                         'ov': bool(ov and d == ov and not e.get('flow')),
                         'dots': dots(e)})
            d += dt.timedelta(days=1)
        weeks.append(week)
        if d.month != month and d > first:
            break
    return weeks


DOTS = (('body', ('sym', 'pain', 'relief')),
        ('feel', ('mood', 'energy')),
        ('sleep', ('sleep',)),
        ('more', ('note', 'discharge', 'tags', 'sex')))


def dots(e):
    """CY-5 - which small dots a calendar day shows: body (symptoms or
    pain), feelings, sleep, and one for anything else."""
    return [k for k, keys in DOTS if any(e.get(x) for x in keys)]


def day_words(e):
    """CY-5 - one line for a day: 'Medium flow · Cramps · Tired · Slept
    poorly'. Never mentions sex - it stays inside Log a day."""
    out = []
    if e.get('flow'):
        out.append('%s flow' % FLOW_NAMES[e['flow']] if e['flow'] !=
                   'spotting' else 'Spotting')
    out += [SYMPTOM_NAMES[k] for k in e.get('sym', []) if k in
            SYMPTOM_NAMES]
    if e.get('pain'):
        out.append('Pain %d of 10' % e['pain'])
    if e.get('mood'):
        out.append('Mood: %s' % CHOICES['mood'][e['mood']].lower())
    if e.get('energy'):
        out.append('Energy: %s' % CHOICES['energy'][e['energy']].lower())
    if e.get('sleep'):
        out.append('Slept %s' % {'poor': 'poorly', 'okay': 'okay',
                                 'good': 'well'}[e['sleep']])
    if e.get('discharge'):
        out.append('Discharge: %s'
                   % CHOICES['discharge'][e['discharge']].lower())
    out += e.get('tags', [])
    if e.get('note'):
        out.append('A note')
    return ' · '.join(out)


def _when(d):
    """'Tue 17 Nov' without %-d."""
    return '%s %d %s' % (d.strftime('%a'), d.day, d.strftime('%b'))


def _arc(c, r, a0, a1):
    import math
    x0, y0 = c + r * math.sin(a0), c - r * math.cos(a0)
    x1, y1 = c + r * math.sin(a1), c - r * math.cos(a1)
    large = 1 if a1 - a0 > math.pi else 0
    return 'M%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f' % (x0, y0, r, r, large,
                                                       x1, y1)


def wheel(s, days, today, pms_days=None, size=280):
    """CY-5 - the big ring of the approved redesign (17 Nov): one bead
    per day of the cycle - the period in its logged shades, the fertile
    estimate, the likely ovulation day, the PMS days, the expected next
    period - with today marked and a dot outside each logged day. None
    without a cycle day."""
    import math
    n_today = s.get('cycle_day')
    if not n_today or not s['cycles']:
        return None
    start = s['cycles'][-1]['start']
    usual = s.get('avg_cycle') or 28
    L = max(usual, n_today if n_today <= PREDICT_MAX else usual)
    c = size / 2.0
    sw = 20
    r = c - sw / 2.0 - 12
    gap = min(0.035, math.pi / L / 4)
    fer, ov, win = s.get('fertile'), s.get('ovulation'), s.get('window')
    pms_from = L - pms_days + 1 if pms_days else None
    beads, marks = [], []
    for n in range(1, L + 1):
        d = start + dt.timedelta(days=n - 1)
        e = days.get(d.isoformat(), {})
        f = e.get('flow')
        if f:
            cls = 'f-' + f
        elif ov and d == ov:
            cls = 'ov'
        elif fer and fer[0] <= d <= fer[1]:
            cls = 'fert'
        elif win and d > today and win[0] <= d <= win[1]:
            cls = 'pred'
        elif pms_from and n >= pms_from and d > today:
            cls = 'pms'
        else:
            cls = 'rest'
        a0 = 2 * math.pi * (n - 1) / L + gap
        a1 = 2 * math.pi * n / L - gap
        beads.append({'d': _arc(c, r, a0, a1), 'cls': cls})
        if e:
            am = 2 * math.pi * (n - 0.5) / L
            ro = r + sw / 2.0 + 7
            marks.append({'x': '%.1f' % (c + ro * math.sin(am)),
                          'y': '%.1f' % (c - ro * math.cos(am))})
    out = {'size': size, 'c': '%.1f' % c, 'r': '%.1f' % r, 'sw': sw,
           'beads': beads, 'marks': marks, 'of': L, 'day': n_today,
           'when': 'Today, ' + _when(today)}
    if n_today <= L:
        at = 2 * math.pi * (n_today - 0.5) / L
        out['tx'] = '%.1f' % (c + r * math.sin(at))
        out['ty'] = '%.1f' % (c - r * math.cos(at))
    if ov and start <= ov < start + dt.timedelta(days=L):
        ao = 2 * math.pi * ((ov - start).days + 0.5) / L
        out['ox'] = '%.1f' % (c + r * math.sin(ao))
        out['oy'] = '%.1f' % (c - r * math.cos(ao))
    # The words in the middle.
    big, small, line = 'Day %d' % n_today, 'of your cycle', ''
    if s.get('in_period'):
        big, small = 'Day %d' % s['period_day'], 'of your period'
    elif win and s['state'] in ('predicted', 'first_guess'):
        to = (win[0] - today).days
        if to > 1:
            big, small = '%d days' % to, 'until your next period'
        elif to == 1:
            big, small = '1 day', 'until your next period'
        elif win[0] <= today <= win[1]:
            big, small = 'Any day now', 'your period is due'
    if ov and s['state'] in ('predicted', 'first_guess'):
        k = (ov - today).days
        if k > 1:
            line = 'Ovulation likely in %d days' % k
        elif k == 1:
            line = 'Ovulation likely tomorrow'
        elif k == 0:
            line = 'Ovulation likely today'
    out.update({'big': big, 'small': small, 'line': line})
    return out


def history(days, cs, s, n=RECENT, fertile=False):
    """CY-5 - Cycle history: the current cycle and the last n before
    it, newest first, each a row of day cells in the period's shades
    (and, with the estimate on, the fertile days and the likely
    ovulation day, counted back 14 days from the next start)."""
    rows = []
    top = max([c['length'] or 0 for c in cs[-n - 1:]] +
              [s.get('cycle_day') or 0, 28])
    top = min(top, PREDICT_MAX)
    for c in cs[-n - 1:][::-1]:
        length = c['length'] or (s.get('cycle_day') or 1)
        if length > PREDICT_MAX:
            continue
        ov_n = length - 14 if fertile and c['length'] else None
        cells = []
        for i in range(length):
            d = c['start'] + dt.timedelta(days=i)
            f = days.get(d.isoformat(), {}).get('flow')
            if f:
                cls = 'f-' + f
            elif ov_n and i + 1 == ov_n:
                cls = 'ov'
            elif ov_n and ov_n - 5 <= i + 1 <= ov_n + 1:
                cls = 'fert'
            else:
                cls = 'rest'
            cells.append(cls)
        if c['length']:
            last = c['start'] + dt.timedelta(days=c['length'] - 1)
            label = '%d %s – %d %s' % (c['start'].day,
                                       c['start'].strftime('%b'),
                                       last.day, last.strftime('%b'))
            side = '%d days' % c['length']
        else:
            label = 'Now · from %d %s' % (c['start'].day,
                                          c['start'].strftime('%b'))
            side = 'day %d' % length
        rows.append({'label': label, 'side': side, 'cells': cells,
                     'w': '%.2f' % (100.0 * length / top)})
    return rows


def stats(cs):
    """CY-5 - the three tiles over Cycle history: cycle length, period
    length and how much the cycles vary. None until one cycle is done."""
    lengths = recent_lengths(cs)
    if not lengths:
        return None
    pers = [c['period'] for c in cs[-RECENT:]]
    spread = max(lengths) - min(lengths)
    return {'cycle': int(round(median(lengths))),
            'cycle_usual': span_words(min(lengths), max(lengths), ' – '),
            'period': int(round(median(pers))),
            'period_usual': span_words(min(pers), max(pers), ' – '),
            'vary': (spread + 1) // 2,
            'vary_word': 'regular' if spread <= 7 else 'varies more'}


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


def around(days, cs, n=RECENT, tags=()):
    """Symptoms around day 1 of the last n periods. Needs three periods.
    Rows of (name, [share 0..1 per AROUND offset]) plus one plain line.
    CY-3: mood, sleep, energy and your own tags count too."""
    starts = [c['start'] for c in cs][-n:]
    if len(starts) < 3:
        return [], ''
    rows = []
    for key, name in pattern_keys(tags):
        cells = []
        for off in AROUND:
            delta = off if off < 0 else off - 1
            hit = 0
            for a in starts:
                e = days.get((a + dt.timedelta(days=delta)).isoformat(), {})
                if has(e, key):
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
          'Poor sleep': ('Poor sleep', 'is'),
          # CY-4 - the new ones.
          'Mood swings': ('Mood swings', 'are'),
          'Irritable': ('Feeling irritable', 'is'),
          'Anxious': ('Feeling anxious', 'is'),
          'Tearful': ('Feeling tearful', 'is'),
          'Hard to focus': ('Trouble focusing', 'is'),
          'Swollen hands or feet': ('Swelling', 'is'),
          'Hungrier than usual': ('Extra hunger', 'is'),
          'Hot flushes': ('Hot flushes', 'are'),
          'Night sweats': ('Night sweats', 'are'),
          'Joint aches': ('Joint aches', 'are'),
          'Palpitations': ('Palpitations', 'are')}


def _noun(name):
    return _NOUNS.get(name, (name, 'is'))


def report(days, cs, n, notes=False):
    """The printable page: one row per cycle, newest first."""
    rows = []
    for c in [c for c in cs][-n:][::-1]:
        span = [c['start'] + dt.timedelta(days=i)
                for i in range(c['period'])]
        flows = [days.get(d.isoformat(), {}).get('flow') for d in span]
        heavy = sum(1 for f in flows if f in HEAVY)
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
                     'heaviest_name': FLOW_NAMES[[k for k, v in
                                                  FLOW_RANK.items()
                                                  if v == top][0]]
                     if top >= 0 else '',
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
