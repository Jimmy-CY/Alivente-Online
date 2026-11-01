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

CY-4, 1 Nov 2026 - HONEST WORDING. Demetri, 05:21: "Are these ideas
scientifically or generally solid suggestions?" Mostly general good
habits; the phase-matching ("energy rises", "strength peaks at
ovulation") goes beyond the research - a 2020 meta-analysis (McNulty et
al., Sports Medicine) found only trivial performance differences across
the cycle, and people vary a lot. 05:26: reword for Release 57. So:
    - well supported, kept plainly: heat and gentle exercise for period
      pain, iron while bleeding, rest and sleep;
    - everything else is said as a general habit or as "some people
      find", never as what the phase does to the body;
    - the board says so under its heading (DISCLAIMER).
test_wellness_fourteen holds the words to this.
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
    ('menstrual', 'Menstrual phase', 'Your period.'),
    ('follicular', 'Follicular phase', 'From your period to ovulation.'),
    ('ovulation', 'Ovulation phase', 'Around ovulation - an estimate.'),
    ('luteal', 'Luteal phase', 'From ovulation to your next period.'),
]
PHASE_NAMES = {k: n for k, n, _w in PHASES}
DISCLAIMER = ('General wellbeing ideas, loosely matched to the phase. '
              'Research shows people vary a lot - go by how you feel.')

# A line for the day: a few per phase, chosen by the day of the cycle.
LINES = {
    'menstrual': [
        ('New cycle, new you', 'The first days often come with mixed '
         'feelings. Be as kind to yourself as you would be to a friend.'),
        ('Slow is fine', 'If you feel tired, rest counts. Gentle movement '
         'and warmth can ease cramps.'),
        ('Warmth helps', 'A warm drink, a warm bath, an early night - '
         'small comforts go a long way.'),
    ],
    'follicular': [
        ('A fresh page', 'Some people feel lighter after their period. If '
         'you do, it can be a good time to begin something.'),
        ('Plan ahead', 'A few minutes setting up the weeks ahead can make '
         'them easier.'),
        ('Try something new', 'A new route, a new recipe, a new class - '
         'small changes keep things interesting.'),
    ],
    'ovulation': [
        ('However you feel', 'Some people feel more sociable around now, '
         'others notice nothing different. Both are normal.'),
        ('Go by your body', 'If you feel strong, enjoy it. If not, a '
         'steady day is just as good.'),
    ],
    # CY-4 - perimenopause mode: no phases, these lines instead.
    'peri': [
        ('One day at a time', 'Perimenopause can bring changes in sleep, '
         'mood and cycles. Be patient with yourself.'),
        ('You are not alone', 'Most women go through this. Talking about it '
         '- with friends or a doctor - helps.'),
        ('Notice what helps', 'Your own tags can show what goes with your '
         'better and harder days.'),
    ],
    'luteal': [
        ('Steady days', 'Regular meals, gentle movement and good sleep '
         'help the days feel even.'),
        ('Notice and allow', 'Some people notice mood or energy shift '
         'before a period. Name it, and give yourself some room.'),
        ('Finish something', 'Tying up one loose end can feel good on any '
         'day.'),
    ],
}

# The board: phase -> group -> [(key, name, why, how, link)]. link is a
# Wellness page or ''. Ideas, not rules - nothing medical, no targets.
# CY-4: the why says what is generally true or what some people find -
# never what the phase does to the body.
BOARD = {
    'menstrual': {
        'do': [
            ('m_rest', 'An early night', 'Good sleep helps with tiredness '
             'and low mood on any day.', 'Dim the lights an hour before bed '
             'and put the phone in another room.', ''),
            ('m_warm', 'A warm bath or heat pack', 'Heat is one of the '
             'best-studied ways to ease period cramps.', 'Twenty minutes, '
             'warm not hot - a bath, a hot water bottle or a heat pad.', ''),
            ('m_breathe', 'Breathe for two minutes', 'Slow breathing helps '
             'many people feel calmer when things feel heavy.', 'Calm, in 4 '
             'and out 6.', '/wellness/calm/breathe/'),
            ('m_write', 'Write a few lines', 'A new cycle is a natural '
             'moment to look back and look ahead.', 'What do you want '
             'more of this month?', '/wellness/journal/new/'),
        ],
        'move': [
            ('m_walk', 'Walking', 'Regular gentle exercise is shown to '
             'reduce period pain for many people.', 'An easy pace, outdoors '
             'if you can.', ''),
            ('m_yin', 'Yin or gentle yoga', 'Gentle stretching and yoga can '
             'ease cramps and tension.', 'Five or ten minutes on the floor '
             'is enough.', ''),
            ('m_stretch', 'Stretching', 'Loosens the back and hips.',
             'Child\'s pose, a gentle twist, knees to chest.', ''),
        ],
        'eat': [
            ('m_iron', 'Iron-rich foods', 'You lose some iron while you '
             'bleed, and low iron is common - especially with heavy '
             'periods.', 'Lentils, beans, spinach, red meat if you eat it.',
             ''),
            ('m_soup', 'Warm, simple meals', 'Easy to make and comforting '
             'when you are tired.', 'Soups, stews, porridge.', ''),
            ('m_water', 'Water and herbal tea', 'Staying hydrated is good '
             'for headaches and energy on any day.', 'Keep a bottle nearby; '
             'ginger or peppermint tea if you like them.', ''),
            ('m_choc', 'A little dark chocolate', 'A comfort many people '
             'enjoy, with no guilt attached.', 'A square or two, enjoyed '
             'slowly.', ''),
        ],
    },
    'follicular': {
        'do': [
            ('f_plan', 'Plan the month', 'A few minutes of planning makes '
             'the weeks ahead easier.', 'Three things you would like to do '
             'before your next period.', ''),
            ('f_new', 'Start something new', 'Some people find it easier to '
             'begin things after their period.', 'A class, a book, a habit '
             '- or a challenge.', '/wellness/habits/new/'),
            ('f_social', 'See a friend', 'Time with people you like is good '
             'for mood on any day.', 'A walk and a coffee counts.', ''),
        ],
        'move': [
            ('f_cardio', 'Something brisk', 'Regular aerobic exercise is '
             'good for heart, mood and sleep.', 'A brisk walk, a jog, a swim '
             'or a bike ride.', ''),
            ('f_strength', 'Strength training', 'Strength training builds '
             'muscle and bone at any point in your cycle.', 'A routine from '
             'Workouts, at your own pace.', '/wellness/workouts/'),
            ('f_dance', 'Dance', 'Fun, and a mood lifter.', 'One song in the '
             'kitchen is enough.', ''),
        ],
        'eat': [
            ('f_fresh', 'Fresh, colourful food', 'Variety brings a spread '
             'of goodness.', 'Salads, fruit, crunchy vegetables.', ''),
            ('f_ferment', 'Fermented foods', 'Many people find them good for '
             'digestion.', 'Yoghurt, kefir, sauerkraut.', ''),
            ('f_grains', 'Whole grains', 'Fibre and steady energy through '
             'the day.', 'Oats, brown rice, wholemeal bread.', ''),
        ],
    },
    'ovulation': {
        'do': [
            ('o_talk', 'Have the conversation', 'If you have been putting '
             'something off, today is as good a day as any.', 'The call or '
             'the ask you have been saving.', ''),
            ('o_out', 'Get out and about', 'Time outdoors and with others '
             'is good for mood.', 'Say yes to the invitation, if you feel '
             'like it.', ''),
            ('o_gratitude', 'A gratitude pause', 'Noticing what is going '
             'well can lift the day.', 'Five minutes, guided.',
             '/wellness/calm/guided/gratitude/'),
        ],
        'move': [
            ('o_hard', 'A harder workout, if you feel strong', 'Some people '
             'feel strong around now; research finds little difference '
             'across the cycle on average, so go by how you feel.', 'Warm '
             'up well and add a little weight or distance.',
             '/wellness/workouts/'),
            ('o_class', 'A group class', 'Exercise with company is more fun '
             'for many people.', 'Spin, dance, a team game.', ''),
            ('o_hike', 'A long walk or hike', 'Time in green places is good '
             'for body and mind.', 'Somewhere green, with a friend.', ''),
        ],
        'eat': [
            ('o_fibre', 'Plenty of fibre', 'Keeps digestion easy on any '
             'day.', 'Vegetables, fruit, beans and seeds.', ''),
            ('o_light', 'Lighter meals, if you prefer them', 'Some people '
             'like lighter food on busy days.', 'Grilled fish or chicken, '
             'big salads.', ''),
            ('o_berries', 'Berries', 'Colourful and full of goodness.',
             'On yoghurt, oats, or on their own.', ''),
        ],
    },
    'luteal': {
        'do': [
            ('l_finish', 'Finish things', 'Tying up loose ends feels good '
             'on any day.', 'Pick one loose end and tie it.', ''),
            ('l_candle', 'A cosy evening', 'Comfort helps if your mood '
             'dips.', 'A candle, a blanket, a film.', ''),
            ('l_less', 'Ask a little less of yourself', 'If you feel tired '
             'or low before your period, lighten the load where you can.',
             'Drop one thing from the list this week.', ''),
            ('l_sleep', 'Wind down for sleep', 'Some people sleep less well '
             'before a period; a calm wind-down helps.', 'Sleep breathing, '
             'in 4, hold 7, out 8.', '/wellness/calm/breathe/'),
        ],
        'move': [
            ('l_pilates', 'Pilates or gentle strength', 'Steady, controlled '
             'movement is good on any day.', 'Slower, with good form.', ''),
            ('l_walk', 'A daily walk', 'Gentle and good for mood.',
             'Twenty minutes, outdoors if you can.', ''),
            ('l_yoga', 'Restorative yoga', 'A calm way to move when energy '
             'is low.', 'Legs up the wall for five minutes.', ''),
        ],
        'eat': [
            ('l_complex', 'Slow, satisfying meals', 'Regular meals can help '
             'with cravings and steady energy.', 'Sweet potato, brown rice, '
             'oats, beans.', ''),
            ('l_nuts', 'Nuts and seeds', 'A good snack when cravings come.',
             'A handful of almonds, pumpkin or sunflower seeds.', ''),
            ('l_greens', 'Leafy greens', 'Bring magnesium and calcium - '
             'there is some evidence these help with PMS.', 'Spinach, kale, '
             'broccoli.', ''),
            ('l_salt', 'Go easy on salt and caffeine', 'Some people find it '
             'eases bloating and helps sleep; the evidence is mixed.',
             'Herbal tea in the afternoon.', ''),
        ],
    },
}
# CY-4 - perimenopause mode: ideas for the years, not for a phase. The
# well-supported ones: strength training and calcium/vitamin D for bone,
# a cool bedroom and layers for night sweats and flushes.
BOARD['peri'] = {
    'do': [
        ('p_layers', 'Dress in layers', 'Easy to cool down when a hot '
         'flush comes.', 'Layers you can take off, and a fan nearby.', ''),
        ('p_cool', 'A cool bedroom', 'A cooler room helps many people with '
         'night sweats.', 'Light bedding, a window open or a fan.', ''),
        ('p_breathe', 'Slow breathing', 'Some people find slow breathing '
         'helps them ride out a hot flush; the evidence is mixed.',
         'Calm, in 4 and out 6.', '/wellness/calm/breathe/'),
        ('p_doctor', 'Talk to your doctor', 'There is good help for '
         'perimenopause symptoms today - you do not have to put up with '
         'them.', 'Take the one-page report from Patterns with you.',
         '/wellness/cycle/patterns/'),
    ],
    'move': [
        ('p_strength', 'Strength training', 'Helps keep muscle and bone '
         'strong, which matters more as oestrogen falls.', 'Two or three '
         'short sessions a week, at your own pace.', '/wellness/workouts/'),
        ('p_walk', 'Brisk walking', 'Good for heart, bones and mood.',
         'Most days, outdoors if you can.', ''),
        ('p_yoga', 'Yoga or stretching', 'Some people find it helps with '
         'sleep and mood.', 'Ten minutes in the evening.', ''),
    ],
    'eat': [
        ('p_calcium', 'Calcium-rich foods', 'Bone health matters more in '
         'these years.', 'Dairy, fortified plant milks, tinned fish with '
         'bones, leafy greens.', ''),
        ('p_vitd', 'Vitamin D', 'It helps your body use calcium, and many '
         'people are low in winter.', 'Oily fish and eggs; ask your doctor '
         'whether a supplement suits you.', ''),
        ('p_triggers', 'Notice your triggers', 'Some people find alcohol, '
         'caffeine or spicy food set off hot flushes.', 'Add them as your '
         'own tags and watch Patterns.', ''),
    ],
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
    if s.get('soft'):
        # CY-4 - perimenopause: the day only, its own lines and ideas.
        title, line = LINES['peri'][(n - 1) % len(LINES['peri'])]
        out.update({'why_none': 'In perimenopause cycles change a lot, so '
                    'phases would be guesses. The day is still counted.',
                    'peri': True, 'title': title, 'line': line})
        return out
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
