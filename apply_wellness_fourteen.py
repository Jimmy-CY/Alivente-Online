# -*- coding: utf-8 -*-
"""apply_wellness_fourteen.py - round CY-4 / WL-10, 1 Nov 2026.

RELEASE 57 - WELLNESS: HONEST WORDING, PERIMENOPAUSE MODE, INSIGHTS.

    - Honest wording for the cycle ideas (Demetri, 1 Nov 05:21/05:26): the
      well-supported ones stay plain; the rest are general habits or "some
      people find"; the board says "Research shows people vary a lot - go
      by how you feel."
    - Perimenopause mode (05:43): a rough, wider window, never "late", no
      fertile estimate, no phases (ideas for these years instead), its
      symptoms in Log today and Patterns.
    - Insights (05:43): the last eight weeks side by side, and carefully
      what goes with what. Patterns, not proof.
    - More symptoms (05:48): 22 for everyone, 6 more in perimenopause.

New files ship beside this patcher. Stands on Release 56. Idempotent.
Edits backed up to .bak_wellness14. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness14'
MARK = 'CY-4 / WL-10, 1 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/insights.py',
    'wellness/templates/wellness/insights.html',
    'test_wellness_fourteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl13-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl14-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl13-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl14-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle.html'), [
        (r'''<section class="w-card" id="board" aria-labelledby="board-h" data-board>
  <h2 class="w-h2" id="board-h">Ideas for {% if when == 'tomorrow' %}tomorrow{% else %}today{% endif %}</h2>
  <p class="w-small w-quiet" style="margin:0">Ideas, not rules. Tap one to see why and how; hide any you do not want.</p>
  {% for g, gname, items in board %}{% if items %}
  <div class="w-label">{{ gname }}</div>
''',
         r'''<section class="w-card" id="board" aria-labelledby="board-h" data-board>
  <h2 class="w-h2" id="board-h">Ideas for {% if when == 'tomorrow' %}tomorrow{% else %}today{% endif %}</h2>
  <p class="w-small w-quiet" style="margin:0" data-board-note>Ideas, not rules. {{ board_note }} Tap one to see why and how; hide any you do not want.</p>
  {% for g, gname, items in board %}{% if items %}
  <div class="w-label">{{ gname }}</div>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_settings.html'), [
        (r'''    <label style="display:flex;align-items:center;gap:10px;min-height:44px;font-size:15px"><input type="radio" name="mode" value="{{ key }}"{% if prefs.mode == key %} checked{% endif %} style="width:20px;height:20px;accent-color:var(--w-sage-deep)"> {{ label }}</label>
    {% endfor %}
    <p class="w-small w-quiet" style="margin:0">Pregnancy and hormonal contraception switch predictions off. You can still log anything.</p>
  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
''',
         r'''    <label style="display:flex;align-items:center;gap:10px;min-height:44px;font-size:15px"><input type="radio" name="mode" value="{{ key }}"{% if prefs.mode == key %} checked{% endif %} style="width:20px;height:20px;accent-color:var(--w-sage-deep)"> {{ label }}</label>
    {% endfor %}
    <p class="w-small w-quiet" style="margin:0">In perimenopause, predictions become a rough, wider guide and the phases give way to ideas for these years; hot flushes, night sweats and more are added to Log today. Pregnancy and hormonal contraception switch predictions off. You can still log anything.</p>
  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''{% endif %}

<a class="w-btn quiet full" href="{% url 'wellness:badges' %}">Your badges</a>
{% endblock %}
''',
         r'''{% endif %}

<div class="w-btn-row">
  <a class="w-btn quiet" href="{% url 'wellness:insights' %}" data-insights-link>Your insights</a>
  <a class="w-btn quiet" href="{% url 'wellness:badges' %}">Your badges</a>
</div>
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''   behind the cog, not in the ? guide. {% endcomment %}
<div class="w-list">
  <a class="w-row" href="{% url 'wellness:badges' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Your badges</span><span class="w-row-sub">Quiet milestones, kept for good.</span></span>
''',
         r'''   behind the cog, not in the ? guide. {% endcomment %}
<div class="w-list">
  <a class="w-row" href="{% url 'wellness:insights' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Insights</span><span class="w-row-sub">Your last eight weeks, side by side.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
  <a class="w-row" href="{% url 'wellness:badges' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Your badges</span><span class="w-row-sub">Quiet milestones, kept for good.</span></span>
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-idea p b { color: var(--w-ink); font-weight: 600; margin-right: 4px; }
.w-idea-acts { display: flex; gap: 8px; align-items: center; padding-bottom: 10px; flex-wrap: wrap; }
''',
         r'''.w-idea p b { color: var(--w-ink); font-weight: 600; margin-right: 4px; }
.w-idea-acts { display: flex; gap: 8px; align-items: center; padding-bottom: 10px; flex-wrap: wrap; }

/* ---- WL-10, 1 Nov 2026 - Insights: eight small weekly bars. */
.w-ins-bars { display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 6px; height: 120px; align-items: end; }
.w-ins-bars span { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 4px; }
.w-ins-bars em { flex: 1 1 0; overflow: hidden; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.w-ins-bars i { display: block; width: 100%; max-width: 26px; border-radius: 6px 6px 3px 3px; background: var(--w-sage); }
.w-ins-bars.mood i { background: var(--w-sand-line); }
.w-ins-bars.calm i { background: var(--w-sky); }
.w-ins-bars.train i { background: var(--w-sage-deep); }
.w-ins-bars b { font-size: 11px; font-weight: 600; color: var(--w-ink); line-height: 1; }
.w-ins-bars small { font-size: 10px; color: var(--w-quiet); white-space: nowrap; }
'''),
    ]),
    (os.path.join('wellness', 'phases.py'), [
        (r'''14 days before the next period. They live only in the Cycle tab - Today's
cycle line stays as discreet as before.
"""
import datetime as dt
''',
         r'''14 days before the next period. They live only in the Cycle tab - Today's
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
'''),
        (r'''
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
''',
         r'''
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
'''),
        (r'''           'estimated': not s.get('avg_cycle'), 'late': n > L,
           'why_none': ''}
    if s['state'] in ('pregnant', 'hormonal'):
        out['why_none'] = ('Phases are paused while you are pregnant.'
''',
         r'''           'estimated': not s.get('avg_cycle'), 'late': n > L,
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
'''),
    ]),
    (os.path.join('wellness', 'cycle.py'), [
        (r'''    ('low_mood', 'Low mood'),
    ('poor_sleep', 'Poor sleep'),
]
SYMPTOM_NAMES = dict(SYMPTOMS)
''',
         r'''    ('low_mood', 'Low mood'),
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
'''),
        (r'''# before a period, and a low mood however it was logged.
PMS_KEYS = ('cramps', 'headache', 'bloating', 'tender', 'tired', 'acne',
            'cravings', 'low_mood', 'poor_sleep', 'low_energy')
PMS_BACK = 7
# The calendar looks this many months ahead.
MONTHS_AHEAD = 6

MODES = [
    ('normal', 'Tracking my cycle'),
    ('pregnant', 'Pregnant'),
    ('hormonal', 'On hormonal contraception'),
]
MODE_NAMES = dict(MODES)

DEFAULT_SETTINGS = {'on': False, 'fertile': False, 'mode': 'normal',
''',
         r'''# before a period, and a low mood however it was logged.
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
'''),
        (r'''def pattern_keys(tags=()):
    """(key, name) for everything Patterns can show."""
    return list(SYMPTOMS) + [('low_energy', 'Low energy')] + \
        [('tag:' + t, t) for t in (tags or ())]

''',
         r'''def pattern_keys(tags=()):
    """(key, name) for everything Patterns can show."""
    return list(SYMPTOMS) + list(PERI_SYMPTOMS) + \
        [('low_energy', 'Low energy')] + \
        [('tag:' + t, t) for t in (tags or ())]

'''),
        (r'''    cs = cycles(ps)
    mode = settings.get('mode', 'normal')
    out = {'state': 'empty', 'cycles': cs, 'cycle_day': None,
           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'flags': flags(cs, today, mode)}
    if not ps:
        if mode != 'normal':
            out['state'] = mode
        return out
''',
         r'''    cs = cycles(ps)
    mode = settings.get('mode', 'normal')
    out = {'state': 'empty', 'cycles': cs, 'cycle_day': None, 'soft': False,
           'window': None, 'fertile': None, 'avg_cycle': None,
           'avg_period': None, 'range': None, 'in_period': False,
           'period_day': None, 'flags': flags(cs, today, mode)}
    if not ps:
        if mode not in PREDICTING:
            out['state'] = mode
        return out
'''),
        (r'''        out['avg_cycle'] = int(round(median(lengths)))
        out['range'] = (min(lengths), max(lengths))
    if mode != 'normal':
        out['state'] = mode
        return out
    if not lengths:
        out['state'] = 'learning'
''',
         r'''        out['avg_cycle'] = int(round(median(lengths)))
        out['range'] = (min(lengths), max(lengths))
    if mode not in PREDICTING:
        out['state'] = mode
        return out
    out['soft'] = mode == 'perimenopause'
    if not lengths:
        out['state'] = 'learning'
'''),
        (r'''        spread = max(1, min(4, int((hi - lo + 1) // 2)))
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
''',
         r'''        spread = max(1, min(4, int((hi - lo + 1) // 2)))
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
'''),
        (r'''             % (len([c for c in s['cycles'] if c['length']][-RECENT:]),
                span_words(*s['range'], joint='–')))
    return ('Next period around %s' % _span(a, b), small)

''',
         r'''             % (len([c for c in s['cycles'] if c['length']][-RECENT:]),
                span_words(*s['range'], joint='–')))
    if s.get('soft'):
        # CY-4 - perimenopause: a rough guide, never "late".
        return ('Perhaps around %s' % _span(a, b),
                'In perimenopause cycles change a lot - this is a rough '
                'guide from your recent cycles.')
    return ('Next period around %s' % _span(a, b), small)

'''),
        (r'''          'Acne': ('Acne', 'is'), 'Cravings': ('Cravings', 'are'),
          'Nausea': ('Nausea', 'is'), 'Low mood': ('Low mood', 'is'),
          'Poor sleep': ('Poor sleep', 'is')}


''',
         r'''          'Acne': ('Acne', 'is'), 'Cravings': ('Cravings', 'are'),
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


'''),
    ]),
    (os.path.join('wellness', 'views_cycle.py'), [
        (r'''        s['state'] not in ('pregnant',),
        'board': PH.board(card['phase'], prefs.get('hidden_tips'))
        if card and card['phase'] else [],
        'hidden_n': len([k for k in (prefs.get('hidden_tips') or ())
                         if k in PH.ALL_KEYS]),
    })

''',
         r'''        s['state'] not in ('pregnant',),
        'board': PH.board(card['phase'], prefs.get('hidden_tips'))
        if card and card['phase'] else
        PH.board('peri', prefs.get('hidden_tips'))
        if card and card.get('peri') else [],
        'hidden_n': len([k for k in (prefs.get('hidden_tips') or ())
                         if k in PH.ALL_KEYS]),
        # CY-4 - what the ideas are, honestly (Demetri, 1 Nov 05:26).
        'board_note': PH.DISCLAIMER,
    })

'''),
        (r'''    starting = (e.get('flow') in C.BLEED and
                any(p[0] == day for p in C.periods(days)))
    return render(request, 'wellness/cycle_log.html', {
        'tab': 'cycle',
        'day': day,
        'is_today': day == today,
        'e': e,
        'flows': C.FLOWS,
        'symptoms': C.SYMPTOMS,
        'cycle_day': ((day - C.periods(days)[-1][0]).days + 1)
        if C.periods(days) and day >= C.periods(days)[-1][0] else None,
''',
         r'''    starting = (e.get('flow') in C.BLEED and
                any(p[0] == day for p in C.periods(days)))
    # CY-4 - perimenopause: its symptoms are offered too.
    symptoms = C.SYMPTOMS + (C.PERI_SYMPTOMS
                             if prefs.get('mode') == 'perimenopause' else [])
    return render(request, 'wellness/cycle_log.html', {
        'tab': 'cycle',
        'day': day,
        'is_today': day == today,
        'e': e,
        'flows': C.FLOWS,
        'symptoms': symptoms,
        'cycle_day': ((day - C.periods(days)[-1][0]).days + 1)
        if C.periods(days) and day >= C.periods(days)[-1][0] else None,
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''    return {'key': k, 'mark': mark, 'name': name, 'line': line,
            'family': BG.FAMILY[k], 'more': len(fresh) - 1}


''',
         r'''    return {'key': k, 'mark': mark, 'name': name, 'line': line,
            'family': BG.FAMILY[k], 'more': len(fresh) - 1}


@wellness_view
def insights_page(request):
    """WL-10, 1 Nov 2026 - Insights: the last eight weeks side by side,
    and carefully, what goes with what. Only sections switched on."""
    from . import insights as INS
    from . import modules as MOD
    on = MOD.on_set(request.user)
    return render(request, 'wellness/insights.html', {
        'tab': 'today', 'on': on,
        'i': INS.gather(request.user, _today(), on),
        'min_days': INS.MIN_DAYS,
    })


'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl13-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl14-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    # WL-4a, 30 Oct 2026 - badges and Wellness settings.
    path('badges/', views.badges_page, name='badges'),
    path('badges/seen/', views.badges_seen, name='badges_seen'),
    path('settings/', views.settings_page, name='settings'),
''',
         r'''    # WL-4a, 30 Oct 2026 - badges and Wellness settings.
    path('badges/', views.badges_page, name='badges'),
    # WL-10, 1 Nov 2026 - Insights.
    path('insights/', views.insights_page, name='insights'),
    path('badges/seen/', views.badges_seen, name='badges_seen'),
    path('settings/', views.settings_page, name='settings'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'every cycle reminder it only says "A Wellness reminder". You can '
          'also ask for a nudge to log once your period is due.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
     'a': 'Four stretches of a cycle: menstrual (your period), follicular '
          '(energy often rises), ovulation (often the most energetic days) '
          'and luteal (winding down before the next period). Wellness '
          'estimates them from your own averages, so they sharpen as you '
          'log. With very irregular cycles, pregnancy or hormonal '
          'contraception it shows the day only.'},
    {'q': 'What are the ideas on the cycle page?',
     'a': 'A few things to do, move and eat that suit the phase - each '
          'with why and how. They are ideas, not rules, and nothing in them '
          'is medical advice. Hide any you do not want; "Show the ideas you '
          'hid" brings them back.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
''',
         r'''          'every cycle reminder it only says "A Wellness reminder". You can '
          'also ask for a nudge to log once your period is due.'},
    # CY-4 / WL-10, 1 Nov 2026 - perimenopause mode and Insights.
    {'q': 'Is there a perimenopause mode?',
     'a': 'Yes. In Cycle settings choose In perimenopause. Predictions '
          'become a rough, wider guide and never say late, the phases give '
          'way to ideas for these years (strength, bones, cooler nights), '
          'and hot flushes, night sweats, brain fog and more are added to '
          'Log today and to Patterns.'},
    {'q': 'What is Insights?',
     'a': 'A page with your last eight weeks side by side - habits done, '
          'mood, Calm minutes, workouts and your weight trend - and, once '
          'you have added moods in the journal, what goes with your better '
          'days. Patterns, not proof. Find it at the bottom of Today or in '
          'Settings.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
     'a': 'Four stretches of a cycle: menstrual (your period), follicular '
          '(from your period to ovulation), ovulation, and luteal (from '
          'ovulation to your next period). How you feel in each varies a '
          'lot from person to person. Wellness '
          'estimates them from your own averages, so they sharpen as you '
          'log. With very irregular cycles, pregnancy or hormonal '
          'contraception it shows the day only.'},
    {'q': 'What are the ideas on the cycle page?',
     'a': 'A few things to do, move and eat, loosely matched to the phase - '
          'each with why and how. Some are well supported (heat and gentle '
          'exercise for period pain, iron while you bleed); most are simply '
          'good habits on any day. Research shows people vary a lot, so go '
          'by how you feel. They are ideas, not rules, and not medical '
          'advice. Hide any you do not want; "Show the ideas you hid" '
          'brings them back.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: things to do, move and eat for the phase. '
            'Tap one for why and how; hide any you do not want.',
            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
''',
         r'''            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: general wellbeing ideas, loosely matched to '
            'the phase. Tap one for why and how; hide any you do not want.',
            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
'''),
        (r'''        'steps': [
            'Pick the flow, or leave No bleeding.',
            'Tick anything you notice, and move the pain slider if you '
            'like.',
            'Mood, energy, sleep, discharge and your own tags appear here '
''',
         r'''        'steps': [
            'Pick the flow, or leave No bleeding.',
            'Tick anything you notice - from cramps to mood swings, with '
            'more in perimenopause mode - and move the pain slider if you '
            'like.',
            'Mood, energy, sleep, discharge and your own tags appear here '
'''),
        (r'''                   'and your log.',
        'steps': [
            'Pregnancy and hormonal contraception pause predictions.',
            'Reminders - a day before, a nudge to log, a daily pill time - '
''',
         r'''                   'and your log.',
        'steps': [
            'Perimenopause makes predictions a rough guide, adds its '
            'symptoms to Log today and shows ideas for these years.',
            'Pregnancy and hormonal contraception pause predictions.',
            'Reminders - a day before, a nudge to log, a daily pill time - '
'''),
        (r'''        'signs': [('--w-sage', 'The thin line: how far through you are.')],
    },
    'settings': {
        'title': 'Settings',
''',
         r'''        'signs': [('--w-sage', 'The thin line: how far through you are.')],
    },
    # WL-10, 1 Nov 2026 - Insights.
    'insights': {
        'title': 'Insights',
        'purpose': 'Your last eight weeks, side by side - and what goes '
                   'with your better days.',
        'steps': [
            'Each chart is a week: habits done, mood, Calm minutes, '
            'workouts.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
            'It needs moods from your journal, and at least four days on '
            'each side.',
            'Only the sections you have switched on are shown.',
        ],
        'signs': [('--w-sand', 'Patterns, not proof - other things change '
                               'from day to day too.')],
    },
    'settings': {
        'title': 'Settings',
'''),
        (r'''            'Open Your sections to switch any of the six on or off. Off '
            'hides it from Today and the bottom bar; nothing is deleted.',
            'Turn on reminders on each phone - the phone asks you first.',
            'Set times for the evening check-in and the weigh-in.',
''',
         r'''            'Open Your sections to switch any of the six on or off. Off '
            'hides it from Today and the bottom bar; nothing is deleted.',
            'Insights shows your last eight weeks side by side.',
            'Turn on reminders on each phone - the phone asks you first.',
            'Set times for the evening check-in and the weigh-in.',
'''),
    ]),
    (os.path.join('test_wellness_twelve.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def place('" in gate, '  with a sentinel on the phases')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# CY-4 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/phases.py'; Text = " in gate,
   '  with a sentinel on the phases')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/challenge.py'; Text = 'def valid_days('; What = 'WL-8/CY-3: the challenge rules are on disk, with your own number of days - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'def place('; What = 'CY-2: the cycle phases are on disk - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
''',
         r'''    @{ File = 'wellness/challenge.py'; Text = 'def valid_days('; What = 'WL-8/CY-3: the challenge rules are on disk, with your own number of days - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
'''),
        (r'''    'test_wellness_twelve.py',
    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    'test_wellness_thirteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twelve.py',
    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    'test_wellness_thirteen.py',
    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    'test_wellness_fourteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    '.bak_wellness13',
]

''',
         r'''    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    '.bak_wellness13',
    # CY-4, 1 Nov 2026 - Wellness: honest wording for the cycle ideas.
    '.bak_wellness14',
]

'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('CY-4 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_wellness_fourteen.py'" in read(pq):
        print('CY-4 already applied.')
        return 0
    if "'test_wellness_thirteen.py'" not in read(pq):
        refuse('Release 56 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('CY-4 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CY-4 applied - Wellness: honest wording, perimenopause, insights.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
