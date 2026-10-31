# -*- coding: utf-8 -*-
"""wellness/phases.py - CY-2, 31 Oct 2026. Cycle phases.

Demetri, 31 Oct 15:41, sharing the Lively app ("Our new favorite Lively
app feature"): a phase card with the day of the cycle, "My period ended",
and a board of things to do, move and eat. 15:46: "Do, Move and Eat".

    - The phase card: "Day 12 of your cycle - Follicular phase", with a
      soft wave showing where you are across the four phases. Today or
      Tomorrow.
    - A cycle too irregular to place (recent lengths more than nine days
      apart), pregnancy or hormonal contraception: the day only, no phase.
    - One tap: "My period started" and "My period ended".
    - The Do - Move - Eat board: a few ideas for the phase, each with why
      and how. Ideas, not rules: nothing medical, no diet targets, no
      numbers to hit. Any idea can be hidden.
    - A short line for the day.

THE PHASES ARE ESTIMATES from the person's own averages: ovulation about
14 days before the next period. They live only in the Cycle tab - Today's
cycle line stays as discreet as before.
"""
import datetime as dt

DEFAULT_CYCLE = 28
DEFAULT_PERIOD = 5
# Recent cycle lengths further apart than this are too irregular to place.
IRREGULAR = 9
# An open period ("My period started", not yet ended) closes itself after
# its usual length and this many days more.
OPEN_GRACE = 3
OPEN_MAX = 10

PHASES = [
    ('menstrual', 'Menstrual phase', 'Rest and go gently.'),
    ('follicular', 'Follicular phase', 'Energy often starts to rise.'),
    ('ovulation', 'Ovulation phase', 'Often the most energetic days.'),
    ('luteal', 'Luteal phase', 'Winding down towards the next period.'),
]
PHASE_NAMES = {k: n for k, n, _w in PHASES}

# A line for the day: a few per phase, chosen by the day of the cycle.
LINES = {
    'menstrual': [
        ('New cycle, new you', 'The first days often come with mixed '
         'feelings. Be as kind to yourself as you would be to a friend.'),
        ('Slow is fine', 'Your body is doing real work. Rest counts.'),
        ('Warmth helps', 'A warm drink, a warm bath, an early night - '
         'small comforts go a long way this week.'),
    ],
    'follicular': [
        ('Fresh start', 'Many people feel lighter and more curious now. '
         'A good time to begin something.'),
        ('Plan ahead', 'If energy is rising, use it to set up the weeks '
         'ahead.'),
        ('Try something new', 'A new route, a new recipe, a new class - '
         'novelty often feels easier now.'),
    ],
    'ovulation': [
        ('In your stride', 'Often a sociable, confident time. Say yes to '
         'the call you have been putting off.'),
        ('Lots to give', 'If you feel strong, enjoy it - and leave a '
         'little in reserve.'),
    ],
    'luteal': [
        ('Turning inward', 'Energy often eases now. Finishing things can '
         'feel better than starting them.'),
        ('Steady wins', 'Regular meals, gentle movement and good sleep '
         'help the days feel even.'),
        ('Notice and allow', 'If moods shift, that is common. Name it, '
         'and give yourself some room.'),
    ],
}

# The board: phase -> group -> [(key, name, why, how, link)]. link is a
# Wellness page or ''. Ideas, not rules - nothing medical, no targets.
BOARD = {
    'menstrual': {
        'do': [
            ('m_rest', 'An early night', 'Sleep often feels more needed '
             'in these days.', 'Dim the lights an hour before bed and put '
             'the phone in another room.', ''),
            ('m_warm', 'A warm bath', 'Warmth can ease tension and '
             'cramps for many people.', 'Twenty minutes, warm not hot, '
             'with a book or music.', ''),
            ('m_breathe', 'Breathe for two minutes', 'Slow breathing '
             'settles the body when things feel heavy.', 'Calm, in 4 and '
             'out 6.', '/wellness/calm/breathe/'),
            ('m_write', 'Write a few lines', 'A new cycle is a natural '
             'moment to look back and look ahead.', 'What do you want '
             'more of this month?', '/wellness/journal/new/'),
        ],
        'move': [
            ('m_walk', 'Walking', 'Gentle movement can lift mood and '
             'ease cramps.', 'An easy pace, outdoors if you can.', ''),
            ('m_yin', 'Yin or gentle yoga', 'Slow, held stretches suit '
             'lower-energy days.', 'Five or ten minutes on the floor is '
             'enough.', ''),
            ('m_stretch', 'Stretching', 'Loosens the back and hips.',
             'Child\'s pose, a gentle twist, knees to chest.', ''),
        ],
        'eat': [
            ('m_iron', 'Iron-rich foods', 'You lose some iron while you '
             'bleed.', 'Lentils, beans, spinach, red meat if you eat it.',
             ''),
            ('m_soup', 'Warm, simple meals', 'Easy on the stomach and '
             'comforting.', 'Soups, stews, porridge.', ''),
            ('m_water', 'Water and herbal tea', 'Staying hydrated can '
             'ease bloating and headaches.', 'Keep a bottle nearby; ginger '
             'or peppermint tea.', ''),
            ('m_choc', 'A little dark chocolate', 'Comforting, and it '
             'brings some magnesium.', 'A square or two, enjoyed slowly.',
             ''),
        ],
    },
    'follicular': {
        'do': [
            ('f_plan', 'Plan the month', 'Rising energy often makes '
             'planning feel easy.', 'Three things you would like to do '
             'before your next period.', ''),
            ('f_new', 'Start something new', 'Curiosity often runs high '
             'now.', 'A class, a book, a habit - or a challenge.',
             '/wellness/habits/new/'),
            ('f_social', 'See a friend', 'Many feel more sociable as '
             'energy rises.', 'A walk and a coffee counts.', ''),
        ],
        'move': [
            ('f_cardio', 'Something brisk', 'Many people feel ready for '
             'more effort now.', 'A brisk walk, a jog, a swim or a bike '
             'ride.', ''),
            ('f_strength', 'Strength training', 'A good time to build.',
             'A routine from Workouts, at your own pace.',
             '/wellness/workouts/'),
            ('f_dance', 'Dance', 'Fun, and it lifts the mood.', 'One song '
             'in the kitchen is enough.', ''),
        ],
        'eat': [
            ('f_fresh', 'Fresh, colourful food', 'Variety brings a '
             'spread of goodness.', 'Salads, fruit, crunchy vegetables.',
             ''),
            ('f_ferment', 'Fermented foods', 'Many find them good for '
             'digestion.', 'Yoghurt, kefir, sauerkraut.', ''),
            ('f_grains', 'Whole grains', 'Steady energy through the day.',
             'Oats, brown rice, wholemeal bread.', ''),
        ],
    },
    'ovulation': {
        'do': [
            ('o_talk', 'Have the conversation', 'Confidence often peaks '
             'now.', 'The call or the ask you have been saving.', ''),
            ('o_out', 'Get out and about', 'A sociable time for many.',
             'Say yes to the invitation.', ''),
            ('o_gratitude', 'A gratitude pause', 'Notice what is going '
             'well while it is going well.', 'Five minutes, guided.',
             '/wellness/calm/guided/gratitude/'),
        ],
        'move': [
            ('o_hard', 'Your hardest workout', 'Strength and stamina are '
             'often at their best.', 'Go for the heavier weight or the '
             'longer run - warm up well.', '/wellness/workouts/'),
            ('o_class', 'A group class', 'Energy and company go well '
             'together.', 'Spin, dance, a team game.', ''),
            ('o_hike', 'A long walk or hike', 'Make the most of the good '
             'days.', 'Somewhere green, with a friend.', ''),
        ],
        'eat': [
            ('o_fibre', 'Plenty of fibre', 'Keeps digestion easy.',
             'Vegetables, fruit, beans and seeds.', ''),
            ('o_light', 'Lighter meals', 'Many prefer them on high-energy '
             'days.', 'Grilled fish or chicken, big salads.', ''),
            ('o_berries', 'Berries', 'Colourful and full of goodness.',
             'On yoghurt, oats, or on their own.', ''),
        ],
    },
    'luteal': {
        'do': [
            ('l_finish', 'Finish things', 'Wrapping up often feels '
             'better than starting now.', 'Pick one loose end and tie '
             'it.', ''),
            ('l_candle', 'A cosy evening', 'Comfort helps if moods dip.',
             'A candle, a blanket, a film.', ''),
            ('l_less', 'Ask a little less of yourself', 'Energy often '
             'eases before a period.', 'Drop one thing from the list this '
             'week.', ''),
            ('l_sleep', 'Wind down for sleep', 'Sleep can feel lighter in '
             'these days.', 'Sleep breathing, in 4, hold 7, out 8.',
             '/wellness/calm/breathe/'),
        ],
        'move': [
            ('l_pilates', 'Pilates or gentle strength', 'Steady, '
             'controlled movement suits these days.', 'Slower, with good '
             'form.', ''),
            ('l_walk', 'A daily walk', 'Gentle and good for mood.',
             'Twenty minutes, outdoors if you can.', ''),
            ('l_yoga', 'Restorative yoga', 'Calms the body before a '
             'period.', 'Legs up the wall for five minutes.', ''),
        ],
        'eat': [
            ('l_complex', 'Slow, satisfying meals', 'Can help with '
             'cravings and steady energy.', 'Sweet potato, brown rice, '
             'oats, beans.', ''),
            ('l_nuts', 'Nuts and seeds', 'A good snack when cravings '
             'come.', 'A handful of almonds, pumpkin or sunflower seeds.',
             ''),
            ('l_greens', 'Leafy greens', 'Bring magnesium and calcium.',
             'Spinach, kale, broccoli.', ''),
            ('l_salt', 'Go easy on salt and caffeine', 'Many find it '
             'eases bloating and helps sleep.', 'Herbal tea in the '
             'afternoon.', ''),
        ],
    },
}
GROUPS = [('do', 'Do'), ('move', 'Move'), ('eat', 'Eat')]
ALL_KEYS = {item[0] for p in BOARD.values() for g in p.values()
            for item in g}


def lengths_irregular(s):
    rng = s.get('range')
    return bool(rng and rng[1] - rng[0] > IRREGULAR)


def phase_on(day_n, cycle_len, period_len):
    """The phase key for cycle day day_n (1-based)."""
    ov = max(period_len + 2, cycle_len - 14)
    if day_n <= period_len:
        return 'menstrual'
    if day_n <= ov - 2:
        return 'follicular'
    if day_n <= ov + 1:
        return 'ovulation'
    return 'luteal'


def place(s, when):
    """The phase card for `when` (a date), from the cycle summary s of
    TODAY. Returns None when there is no cycle day yet. Keys: day,
    phase (or None: day only), name, line, title, frac, estimated,
    late, why_none."""
    if not s.get('cycle_day'):
        return None
    today_n = s['cycle_day']
    shift = 1 if when == 'tomorrow' else 0
    n = today_n + shift
    L = s.get('avg_cycle') or DEFAULT_CYCLE
    P = s.get('avg_period') or DEFAULT_PERIOD
    out = {'day': n, 'phase': None, 'name': '', 'title': '', 'line': '',
           'frac': min(1.0, (n - 1) / float(max(L, 1))),
           'estimated': not s.get('avg_cycle'), 'late': n > L,
           'why_none': ''}
    if s['state'] in ('pregnant', 'hormonal'):
        out['why_none'] = ('Phases are paused while you are pregnant.'
                           if s['state'] == 'pregnant' else
                           'With hormonal contraception there are no '
                           'natural phases to show.')
        return out
    if lengths_irregular(s):
        out['why_none'] = ('Your recent cycles vary quite a bit, so a '
                           'phase would be a guess. The day is still '
                           'counted.')
        return out
    key = 'luteal' if n > L else phase_on(n, L, P)
    title, line = LINES[key][(n - 1) % len(LINES[key])]
    out.update({'phase': key, 'name': PHASE_NAMES[key], 'title': title,
                'line': line})
    return out


def board(phase, hidden=()):
    """[(group key, group name, [item dicts])] for a phase, without the
    hidden ideas."""
    if phase not in BOARD:
        return []
    hidden = set(hidden or ())
    out = []
    for g, gname in GROUPS:
        items = [{'key': k, 'name': n, 'why': w, 'how': h, 'link': ln}
                 for k, n, w, h, ln in BOARD[phase][g] if k not in hidden]
        out.append((g, gname, items))
    return out


def wave(frac, w=300, h=56):
    """An SVG path for the soft wave and the dot's position on it."""
    import math
    pts = []
    for i in range(0, 61):
        x = w * i / 60.0
        y = h / 2 + (h / 2 - 6) * math.sin(2 * math.pi * i / 60.0
                                           - math.pi / 2) * -0.6
        pts.append('%s%.1f %.1f' % ('M' if i == 0 else 'L', x, y))
    i = frac * 60
    cx = w * i / 60.0
    cy = h / 2 + (h / 2 - 6) * math.sin(2 * math.pi * i / 60.0
                                        - math.pi / 2) * -0.6
    return {'d': ' '.join(pts), 'cx': '%.1f' % cx, 'cy': '%.1f' % cy,
            'w': w, 'h': h}


# --- one tap: started / ended ---------------------------------------------

def open_start(prefs):
    v = prefs.get('open_period')
    try:
        return dt.date.fromisoformat(v) if v else None
    except ValueError:
        return None


def start(prefs, days, today):
    """'My period started' today: today is logged as a bleeding day, and
    the period stays open until 'My period ended'."""
    from . import cycle as C
    e = dict(days.get(today.isoformat()) or {})
    if e.get('flow') not in C.BLEED:
        e['flow'] = 'medium'
    days[today.isoformat()] = e
    prefs['open_period'] = today.isoformat()


def fill(days, first, last):
    """Every day from first to last becomes a bleeding day, keeping what
    was logged (a heavier or lighter flow stays as it was)."""
    from . import cycle as C
    d = first
    while d <= last:
        e = dict(days.get(d.isoformat()) or {})
        if e.get('flow') not in C.BLEED:
            e['flow'] = 'medium'
        days[d.isoformat()] = e
        d += dt.timedelta(days=1)


def end(prefs, days, today, on=None):
    """'My period ended' (on today, or yesterday): the days between are
    filled in, and nothing stays open."""
    first = open_start(prefs)
    last = on or today
    if first and last >= first:
        fill(days, first, last)
    prefs.pop('open_period', None)


def tidy(prefs, days, today, usual):
    """An open period nobody ended closes itself after its usual length
    and a few days more, filled to its usual length. Returns True when
    something changed."""
    first = open_start(prefs)
    if not first:
        return False
    usual = max(1, min(usual or DEFAULT_PERIOD, OPEN_MAX))
    if (today - first).days + 1 > usual + OPEN_GRACE:
        fill(days, first, first + dt.timedelta(days=usual - 1))
        prefs.pop('open_period', None)
        return True
    return False
