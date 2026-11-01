# -*- coding: utf-8 -*-
"""apply_wellness_thirteen.py - round CY-3, 31 Oct 2026.

RELEASE 56 - WELLNESS: DEEPER CYCLE TRACKING.

    - More to log, each switched on in Cycle settings: mood, energy,
      sleep, discharge and your own tags - in Log today and in Patterns.
    - PMS days on the calendar, which now looks six months ahead.
    - A daily pill reminder and a nudge to log - "A Wellness reminder".
    - The reminder's icon in the phone's top bar: the Wellness tick, white
      on clear, instead of a blank white block (Demetri, 31 Oct 18:23).
    - A challenge can have your own number of days, 2 to 365 (20:06).
    - Settings shows the cycle tracker once, in Your sections (21:06),
      and its heading reads "Switched on: ..." (21:07).

New files ship beside this patcher. Stands on Release 55. Idempotent.
Edits backed up to .bak_wellness13. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness13'
MARK = 'CY-3, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/assets/badge-96.png',
    'test_wellness_thirteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl12-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl13-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl12-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl13-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle.html'), [
        (r'''    {% if s.window %}<span><i class="expected"></i>Expected</span>{% endif %}
    {% if s.fertile %}<span><i class="fertile"></i>Fertile estimate</span>{% endif %}
  </div>
  {% if s.fertile %}<div class="w-small w-quiet">The fertile estimate is shown because you turned it on. {{ fertile_label }}</div>{% endif %}
  <div class="w-small w-quiet">Tap any past day to fill it in or change it.</div>
''',
         r'''    {% if s.window %}<span><i class="expected"></i>Expected</span>{% endif %}
    {% if s.fertile %}<span><i class="fertile"></i>Fertile estimate</span>{% endif %}
    {% if pms_days %}<span><i class="pms"></i>PMS days</span>{% endif %}
  </div>
  {% if pms_days %}<div class="w-small w-quiet" data-pms-line>From what you have logged, the days before a period often bring symptoms - about {{ pms_days }} day{{ pms_days|pluralize }} before.</div>{% endif %}
  {% if s.fertile %}<div class="w-small w-quiet">The fertile estimate is shown because you turned it on. {{ fertile_label }}</div>{% endif %}
  <div class="w-small w-quiet">Tap any past day to fill it in or change it.</div>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_log.html'), [
        (r'''  </section>

  <section class="w-card" aria-labelledby="pain-h">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
''',
         r'''  </section>

  {% comment %} CY-3, 31 Oct 2026 - only what is switched on in the tracker's settings. {% endcomment %}
  {% if 'mood' in track %}
  <section class="w-card" aria-labelledby="mood-h"><h2 class="w-h2" id="mood-h">Mood</h2>
    <div class="w-chips">{% for k, label in moods %}<label class="w-chip"><input type="radio" name="mood" value="{{ k }}"{% if e.mood == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'energy' in track %}
  <section class="w-card" aria-labelledby="energy-h"><h2 class="w-h2" id="energy-h">Energy</h2>
    <div class="w-chips">{% for k, label in energy %}<label class="w-chip"><input type="radio" name="energy" value="{{ k }}"{% if e.energy == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'sleep' in track %}
  <section class="w-card" aria-labelledby="sleep-h"><h2 class="w-h2" id="sleep-h">Sleep last night</h2>
    <div class="w-chips">{% for k, label in sleep %}<label class="w-chip"><input type="radio" name="sleep" value="{{ k }}"{% if e.sleep == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'discharge' in track %}
  <section class="w-card" aria-labelledby="dis-h"><h2 class="w-h2" id="dis-h">Discharge</h2>
    <div class="w-chips">{% for k, label in discharge %}<label class="w-chip"><input type="radio" name="discharge" value="{{ k }}"{% if e.discharge == k %} checked{% endif %}><span>{{ label }}</span></label>{% endfor %}</div></section>
  {% endif %}
  {% if 'tags' in track and my_tags %}
  <section class="w-card" aria-labelledby="tags-h"><h2 class="w-h2" id="tags-h">Your tags</h2>
    <div class="w-chips">{% for tg in my_tags %}<label class="w-chip"><input type="checkbox" name="tag" value="{{ tg }}"{% if tg in e.tags %} checked{% endif %}><span>{{ tg }}</span></label>{% endfor %}</div></section>
  {% endif %}

  <section class="w-card" aria-labelledby="pain-h">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'cycle_settings.html'), [
        (r'''  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="remind" value="1"{% if prefs.remind %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Remind me a day before it is expected<br><span class="w-small w-quiet">The reminder only says "A Wellness reminder". Reminders arrive with a later update.</span></span></label>
  <button type="submit" class="w-btn full">Save</button>
</form>
''',
         r'''  </fieldset>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="fertile" value="1"{% if prefs.fertile %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Show a fertile-window estimate<br><span class="w-small w-quiet">{{ fertile_label }} Never rely on it to prevent a pregnancy.</span></span></label>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="remind" value="1"{% if prefs.remind %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Remind me a day before it is expected<br><span class="w-small w-quiet">The reminder only says "A Wellness reminder", on the phones you turned reminders on for.</span></span></label>
  {% comment %} CY-3, 31 Oct 2026 - a nudge to log, a daily pill reminder, more to log, your own tags. {% endcomment %}
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="nudge" value="1"{% if prefs.nudge %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Nudge me to log once it is due<br><span class="w-small w-quiet">If the expected days have begun and nothing is logged, one gentle "A Wellness reminder" in the morning.</span></span></label>
  <label style="display:flex;flex-direction:column;gap:6px;font-size:15px"><span>A daily pill reminder at <span class="w-small w-quiet">(optional)</span></span><input class="w-input" type="time" name="pill_at" value="{{ prefs.pill_at }}" style="max-width:160px"><span class="w-small w-quiet">It says only "A Wellness reminder". Leave it empty for none.</span></label>
  <fieldset style="border:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px">
    <legend class="w-h2" style="margin-bottom:8px">More to log <span class="w-small w-quiet" style="font-weight:400">optional</span></legend>
    <p class="w-small w-quiet" style="margin:0 0 4px">Each one adds a short question to Log today, and shows in Patterns.</p>
    {% for key, label in track_opts %}
    <label class="w-toggle"><span>{{ label }}</span><input type="checkbox" name="track" value="{{ key }}"{% if key in tracked %} checked{% endif %}></label>
    {% endfor %}
    <label style="display:flex;flex-direction:column;gap:6px;font-size:15px"><span class="w-small w-quiet">Your own tags, separated by commas - things you want to see against your cycle</span><input class="w-input" name="tags" maxlength="320" value="{{ tags_line }}" placeholder="coffee, travel, late night"></label>
  </fieldset>
  <button type="submit" class="w-btn full">Save</button>
</form>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
  <a class="w-row" href="{% url 'wellness:cycle' %}" style="text-decoration:none;color:inherit">
    <span class="w-row-main"><span class="w-row-name">Cycle tracker</span><span class="w-row-sub">Optional, off until you turn it on. Private and locked.</span></span>
    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
</div>

''',
         r'''    <span class="w-row-side" aria-hidden="true">›</span>
  </a>
</div>

'''),
        (r'''{% endcomment %}
<details class="w-card" id="sections" data-sections{% if sections_open %} open{% endif %}>
  <summary class="w-voice-sum"><span>Your sections</span><span class="w-quiet w-small">{{ on_names|default:"All off" }}</span></summary>
  <form method="post" style="display:flex;flex-direction:column;gap:4px;margin-top:8px">
    {% csrf_token %}
''',
         r'''{% endcomment %}
<details class="w-card" id="sections" data-sections{% if sections_open %} open{% endif %}>
  <summary class="w-voice-sum"><span>Your sections</span><span class="w-quiet w-small" data-on-names>{% if on_names %}Switched on: {{ on_names }}{% else %}All switched off{% endif %}</span></summary>
  <form method="post" style="display:flex;flex-direction:column;gap:4px;margin-top:8px">
    {% csrf_token %}
'''),
        (r'''    {% for m in modules %}
    <label class="w-toggle" style="align-items:flex-start;padding:6px 0"><span style="display:flex;flex-direction:column;gap:2px"><span>{{ m.name }}</span><span class="w-small w-quiet">{{ m.line }}</span></span><input type="checkbox" name="module" value="{{ m.key }}"{% if m.on %} checked{% endif %} style="margin-top:2px"></label>
    {% endfor %}
    <button type="submit" class="w-btn full" style="margin-top:8px">Save my sections</button>
''',
         r'''    {% for m in modules %}
    <label class="w-toggle" style="align-items:flex-start;padding:6px 0"><span style="display:flex;flex-direction:column;gap:2px"><span>{{ m.name }}</span><span class="w-small w-quiet">{{ m.line }}</span></span><input type="checkbox" name="module" value="{{ m.key }}"{% if m.on %} checked{% endif %} style="margin-top:2px"></label>
    {% if m.key == 'cycle' %}{% comment %} CY-3, 31 Oct 2026 - Demetri, 21:06: the cycle tracker only here, not twice. {% endcomment %}<a class="w-small" href="{% url 'wellness:cycle' %}" style="color:var(--w-sage-deep);min-height:44px;display:inline-flex;align-items:center;margin-top:-6px">{% if m.on %}Open the cycle tracker ›{% else %}What is the cycle tracker? ›{% endif %}</a>{% endif %}
    {% endfor %}
    <button type="submit" class="w-btn full" style="margin-top:8px">Save my sections</button>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''        <label class="w-chip"><input type="radio" name="challenge" value=""{% if not v.challenge %} checked{% endif %}><span>No</span></label>
        {% for n in challenge_days %}<label class="w-chip"><input type="radio" name="challenge" value="{{ n }}"{% if v.challenge == n %} checked{% endif %}><span>{{ n }} days</span></label>{% endfor %}
      </div>
      <span class="w-small w-quiet">A challenge is every day, with a finish line. Miss a day and you choose: carry on, or start again.</span>
      {% if habit.challenge_from and v.challenge %}<span class="w-small w-quiet">Changing the number of days starts it again from today.</span>{% endif %}
''',
         r'''        <label class="w-chip"><input type="radio" name="challenge" value=""{% if not v.challenge %} checked{% endif %}><span>No</span></label>
        {% for n in challenge_days %}<label class="w-chip"><input type="radio" name="challenge" value="{{ n }}"{% if v.challenge == n %} checked{% endif %}><span>{{ n }} days</span></label>{% endfor %}
        <label class="w-chip"><input type="radio" name="challenge" value="own"{% if v.challenge and v.challenge not in challenge_days %} checked{% endif %} data-own-pick><span>Own</span></label>
      </div>
      {% comment %} CY-3, 31 Oct 2026 - your own number of days (Demetri, 20:06). {% endcomment %}
      <label class="w-small w-quiet" style="display:flex;align-items:center;gap:10px" data-own-days>Your own number of days
        <input class="w-input" type="number" name="challenge_own" min="2" max="365" inputmode="numeric" value="{% if v.challenge and v.challenge not in challenge_days %}{{ v.challenge }}{% endif %}" placeholder="45" style="max-width:110px"></label>
      <span class="w-small w-quiet">A challenge is every day, with a finish line. Miss a day and you choose: carry on, or start again.</span>
      {% if habit.challenge_from and v.challenge %}<span class="w-small w-quiet">Changing the number of days starts it again from today.</span>{% endif %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_detail.html'), [
        (r'''    <span class="w-small w-quiet">{{ challenge.days }}-day challenge</span>
  </div>
  {% for row in challenge.rows %}
  <div class="w-strip" style="grid-template-columns:repeat({{ row|length }},minmax(0,1fr));max-width:{% widthratio row|length 15 100 %}%" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done">{% for s in row %}<i class="{{ s }}"></i>{% endfor %}</div>
''',
         r'''    <span class="w-small w-quiet">{{ challenge.days }}-day challenge</span>
  </div>
  {% if not challenge.rows %}<div class="w-bar" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done"><i style="width:{{ challenge.pct }}%"></i></div>{% endif %}
  {% for row in challenge.rows %}
  <div class="w-strip" style="grid-template-columns:repeat({{ row|length }},minmax(0,1fr));max-width:{% widthratio row|length 15 100 %}%" role="img" aria-label="{{ challenge.got }} of {{ challenge.days }} days done">{% for s in row %}<i class="{{ s }}"></i>{% endfor %}</div>
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-legend .expected { box-shadow: inset 0 0 0 1.5px var(--w-rose); }
.w-legend .fertile { background: var(--w-sky-soft); }
.w-flow { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.w-flow label { display: flex; }
''',
         r'''.w-legend .expected { box-shadow: inset 0 0 0 1.5px var(--w-rose); }
.w-legend .fertile { background: var(--w-sky-soft); }
/* CY-3 - PMS days, the faintest rose. */
.w-month .pms, .w-legend .pms { background: var(--w-rose-wash); }
.w-flow { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.w-flow label { display: flex; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''        var daily = form.querySelector('[name=schedule][value=daily]');
        if (daily) daily.checked = true;
      } else if (t.name === 'schedule' && t.value !== 'daily') {
        var none = form.querySelector('[name=challenge][value=""]');
''',
         r'''        var daily = form.querySelector('[name=schedule][value=daily]');
        if (daily) daily.checked = true;
        // CY-3 - "Own": the number box takes the focus.
        if (t.value === 'own') { var box = form.querySelector('[name=challenge_own]'); if (box) box.focus(); }
      } else if (t.name === 'challenge_own' && t.value) {
        var own = form.querySelector('[name=challenge][value=own]');
        if (own) own.checked = true;
        var d2 = form.querySelector('[name=schedule][value=daily]');
        if (d2) d2.checked = true;
      } else if (t.name === 'schedule' && t.value !== 'daily') {
        var none = form.querySelector('[name=challenge][value=""]');
'''),
    ]),
    (os.path.join('wellness', 'challenge.py'), [
        (r'''
DAYS = [7, 14, 21, 30]
ONE = dt.timedelta(days=1)
# Misses in a row before "Pause it for now" is offered too.
''',
         r'''
DAYS = [7, 14, 21, 30]
# CY-3, 31 Oct 2026 - Demetri, 20:06: "can we also have a field to enter
# our own number of days?" Any number in this range.
OWN_MIN, OWN_MAX = 2, 365
# Longer than this shows a bar instead of a square for each day.
STRIP_MAX = 90
ONE = dt.timedelta(days=1)
# Misses in a row before "Pause it for now" is offered too.
'''),
        (r'''        words = 'Day %d of %d' % (day, total)
    return {'days': total, 'got': min(got, total), 'day': day,
            'today_done': today_done, 'finished': finished,
            'misses': len(misses), 'finish': finish,
''',
         r'''        words = 'Day %d of %d' % (day, total)
    return {'days': total, 'got': min(got, total), 'day': day,
            'pct': int(round(100.0 * min(got, total) / total)),
            'today_done': today_done, 'finished': finished,
            'misses': len(misses), 'finish': finish,
'''),
        (r'''
def rows(strip):
    """The strip in rows of at most 15, so 30 squares fit a phone."""
    if len(strip) <= 15:
        return [strip]
    half = (len(strip) + 1) // 2
    return [strip[:half], strip[half:]]


''',
         r'''
def rows(strip):
    """The strip in rows of at most 15, so 30 squares fit a phone. Longer
    than STRIP_MAX days: no squares (the page shows a bar)."""
    if len(strip) > STRIP_MAX:
        return []
    if len(strip) <= 15:
        return [strip]
    if len(strip) <= 30:
        half = (len(strip) + 1) // 2
        return [strip[:half], strip[half:]]
    return [strip[i:i + 15] for i in range(0, len(strip), 15)]


def valid_days(n):
    """A number of days a challenge may have: a preset or your own."""
    return n in DAYS or OWN_MIN <= n <= OWN_MAX


'''),
    ]),
    (os.path.join('wellness', 'cycle.py'), [
        (r'''SYMPTOM_NAMES = dict(SYMPTOMS)

MODES = [
    ('normal', 'Tracking my cycle'),
''',
         r'''SYMPTOM_NAMES = dict(SYMPTOMS)

# CY-3, 31 Oct 2026 - more to log, each switched on in the tracker's
# settings (Demetri, 15:46: mood, energy, sleep, cravings, discharge and
# your own tags; cravings is already a symptom). No fertility signs.
TRACK = [
    ('mood', 'Mood'),
    ('energy', 'Energy'),
    ('sleep', 'Sleep'),
    ('discharge', 'Discharge'),
    ('tags', 'My own tags'),
]
TRACK_KEYS = [k for k, _n in TRACK]
MOODS = [('great', 'Great'), ('good', 'Good'), ('okay', 'Okay'),
         ('low', 'Low'), ('very_low', 'Very low')]
ENERGY = [('low', 'Low'), ('steady', 'Steady'), ('high', 'High')]
SLEEP = [('poor', 'Poor'), ('okay', 'Okay'), ('good', 'Good')]
DISCHARGE = [('dry', 'Dry'), ('sticky', 'Sticky'), ('creamy', 'Creamy'),
             ('watery', 'Watery'), ('clear', 'Clear and stretchy')]
CHOICES = {'mood': dict(MOODS), 'energy': dict(ENERGY),
           'sleep': dict(SLEEP), 'discharge': dict(DISCHARGE)}
MAX_TAGS, TAG_LEN = 12, 24
# What counts towards the PMS window: the symptoms that tend to come
# before a period, and a low mood however it was logged.
PMS_KEYS = ('cramps', 'headache', 'bloating', 'tender', 'tired', 'acne',
            'cravings', 'low_mood', 'poor_sleep', 'low_energy')
PMS_BACK = 7
# The calendar looks this many months ahead.
MONTHS_AHEAD = 6

MODES = [
    ('normal', 'Tracking my cycle'),
'''),
        (r'''                    # CY-2 - a period begun with one tap and not yet
                    # ended (an ISO date), and the board ideas hidden.
                    'open_period': '', 'hidden_tips': ()}

# A gap of one dry day inside a period does not end it.
''',
         r'''                    # CY-2 - a period begun with one tap and not yet
                    # ended (an ISO date), and the board ideas hidden.
                    'open_period': '', 'hidden_tips': (),
                    # CY-3 - more to log, your own tags, the pill
                    # reminder time and the logging nudge.
                    'track': (), 'tags': (), 'pill_at': '',
                    'nudge': False}

# A gap of one dry day inside a period does not end it.
'''),
        (r'''

def clean_day(post_like):
    """A day's entry from a form: flow, symptoms, pain, relief, note.
    Returns {} when nothing was logged, which removes the day."""
    flow = post_like.get('flow') or ''
''',
         r'''

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
'''),
        (r'''    if note:
        out['note'] = note
    return out

''',
         r'''    if note:
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
    return list(SYMPTOMS) + [('low_energy', 'Low energy')] + \
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

'''),
        (r'''# The calendar and the ring
# --------------------------------------------------------------------------
def month_grid(year, month, days, s, today):
    """Weeks (Monday first) of cells: n, date, kind, today, logged."""
    first = dt.date(year, month, 1)
    start = first - dt.timedelta(days=first.weekday())
    win = s.get('window')
    fer = s.get('fertile')
    weeks = []
    d = start
''',
         r'''# The calendar and the ring
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
'''),
        (r'''            elif e.get('flow') == 'spotting':
                kind = 'spotting'
            elif win and win[0] <= d <= win[1] and d >= today:
                kind = 'expected'
            elif fer and fer[0] <= d <= fer[1]:
                kind = 'fertile'
''',
         r'''            elif e.get('flow') == 'spotting':
                kind = 'spotting'
            elif d >= today and any(w[0] <= d <= w[1] for w in wins):
                kind = 'expected'
            elif d >= today and any(p[0] <= d <= p[1] for p in pms_spans):
                kind = 'pms'
            elif fer and fer[0] <= d <= fer[1]:
                kind = 'fertile'
'''),
        (r'''

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
''',
         r'''

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
'''),
    ]),
    (os.path.join('wellness', 'views_cycle.py'), [
        (r'''    except (ValueError, TypeError):
        first = today.replace(day=1)
    if first > today.replace(day=1) + dt.timedelta(days=62):
        first = today.replace(day=1)
    prev_m = (first - dt.timedelta(days=1)).replace(day=1)
    next_m = (first + dt.timedelta(days=32)).replace(day=1)
''',
         r'''    except (ValueError, TypeError):
        first = today.replace(day=1)
    if first > today.replace(day=1) + dt.timedelta(
            days=31 * C.MONTHS_AHEAD):
        first = today.replace(day=1)
    # CY-3 - the months ahead, and the PMS days before each period.
    wins = C.future_windows(s)
    pms_days = C.pms(days, s['cycles']) if wins else None
    prev_m = (first - dt.timedelta(days=1)).replace(day=1)
    next_m = (first + dt.timedelta(days=32)).replace(day=1)
'''),
        (r'''        'small': small,
        'ring': C.ring(s),
        'weeks': C.month_grid(first.year, first.month, days, s, today),
        'month': first,
        'prev_m': prev_m,
        'next_m': next_m,
        'show_next': next_m <= today.replace(day=1) + dt.timedelta(days=40),
        'prefs': prefs,
        'fertile_label': C.FERTILE_LABEL,
''',
         r'''        'small': small,
        'ring': C.ring(s),
        'weeks': C.month_grid(first.year, first.month, days, s, today,
                              wins, pms_days),
        'pms_days': pms_days,
        'month': first,
        'prev_m': prev_m,
        'next_m': next_m,
        'show_next': next_m <= today.replace(day=1) + dt.timedelta(
            days=31 * C.MONTHS_AHEAD),
        'prefs': prefs,
        'fertile_label': C.FERTILE_LABEL,
'''),
        (r'''    key = day.isoformat()
    if request.method == 'POST':
        entry = C.clean_day(request.POST)
        if entry:
            days[key] = entry
''',
         r'''    key = day.isoformat()
    if request.method == 'POST':
        entry = C.clean_day(request.POST, prefs.get('tags'))
        if entry:
            days[key] = entry
'''),
        (r'''        if day < today else '',
        's': s,
    })


''',
         r'''        if day < today else '',
        's': s,
        # CY-3 - more to log, only what is switched on.
        'track': list(prefs.get('track') or ()),
        'moods': C.MOODS, 'energy': C.ENERGY, 'sleep': C.SLEEP,
        'discharge': C.DISCHARGE, 'my_tags': list(prefs.get('tags') or ()),
    })


def _hm_ok(v):
    try:
        h, m = [int(x) for x in v.split(':')[:2]]
        return 0 <= h < 24 and 0 <= m < 60
    except (ValueError, AttributeError):
        return False


'''),
        (r'''            return redirect('wellness:cycle')
        prefs['fertile'] = bool(request.POST.get('fertile'))
        mode = request.POST.get('mode', 'normal')
        prefs['mode'] = mode if mode in C.MODE_NAMES else 'normal'
''',
         r'''            return redirect('wellness:cycle')
        prefs['fertile'] = bool(request.POST.get('fertile'))
        # CY-3 - more to log, your own tags, the pill time, the nudge.
        prefs['track'] = [k for k in request.POST.getlist('track')
                          if k in C.TRACK_KEYS]
        prefs['tags'] = C.clean_tags(request.POST.get('tags'))
        pill = (request.POST.get('pill_at') or '').strip()
        prefs['pill_at'] = pill if _hm_ok(pill) else ''
        prefs['nudge'] = bool(request.POST.get('nudge'))
        mode = request.POST.get('mode', 'normal')
        prefs['mode'] = mode if mode in C.MODE_NAMES else 'normal'
'''),
        (r'''        'n_days': len(days),
        'fertile_label': C.FERTILE_LABEL,
    })

''',
         r'''        'n_days': len(days),
        'fertile_label': C.FERTILE_LABEL,
        'track_opts': C.TRACK,
        'tracked': list(prefs.get('track') or ()),
        'tags_line': ', '.join(prefs.get('tags') or ()),
    })

'''),
        (r'''    today = _today()
    s = C.summary(days, today, prefs)
    rows, words = C.around(days, s['cycles'])
    bars = C.bars(s['cycles'])
    lens = [b['len'] for b in bars]
''',
         r'''    today = _today()
    s = C.summary(days, today, prefs)
    rows, words = C.around(days, s['cycles'], tags=prefs.get('tags'))
    bars = C.bars(s['cycles'])
    lens = [b['len'] for b in bars]
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''    'icon-maskable-512.png': 'image/png',
    'apple-touch-icon.png': 'image/png',
}

''',
         r'''    'icon-maskable-512.png': 'image/png',
    'apple-touch-icon.png': 'image/png',
    # CY-3, 31 Oct 2026 - the small icon in the phone's top bar for a
    # reminder: white on clear, as Android requires (a coloured square
    # shows as a blank white block - Demetri, 18:23).
    'badge-96.png': 'image/png',
}

'''),
        (r'''
def _challenge_choice(post):
    """7, 14, 21 or 30 from the form, or None."""
    try:
        n = int(post.get('challenge') or 0)
    except ValueError:
        return None
    return n if n in CH.DAYS else None


''',
         r'''
def _challenge_choice(post):
    """7, 14, 21 or 30 from the form - or, CY-3, your own number of days
    (2 to 365) when "Own" is chosen - or None."""
    raw = post.get('challenge') or ''
    if raw == 'own':
        raw = post.get('challenge_own') or ''
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if CH.valid_days(n) else None


'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl12-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl13-1'


'''),
        (r'''    tag: d.tag || 'wellness',
    icon: '/wellness/app/icon-192.png',
    badge: '/wellness/app/icon-192.png',
    data: {url: (d.url && d.url.indexOf('/wellness/') === 0) ? d.url : '/wellness/'}
  }));
''',
         r'''    tag: d.tag || 'wellness',
    icon: '/wellness/app/icon-192.png',
    badge: '/wellness/app/badge-96.png',
    data: {url: (d.url && d.url.indexOf('/wellness/') === 0) ? d.url : '/wellness/'}
  }));
'''),
    ]),
    (os.path.join('wellness', 'reminders.py'), [
        (r'''                    'url': '/wellness/body/weigh/'})
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

''',
         r'''                    'url': '/wellness/body/weigh/'})
    _rec, cprefs, days = CY.load(user)
    cy_ok = cprefs.get('on') and not cprefs.get('locked') and \
        'cycle' in mods
    if cy_ok and cprefs.get('remind'):
        s = CY.summary(days, day, cprefs)
        win = s.get('window')
        if win and win[0] - dt.timedelta(days=1) == day and \
                s['state'] in ('predicted', 'first_guess'):
            out.append({'key': 'cycle', 'at': CYCLE_AT, 'title': TITLE,
                        'body': CYCLE_WORDS, 'url': '/wellness/'})
    # CY-3, 31 Oct 2026 - a daily pill reminder at the chosen time, and a
    # nudge to log once the expected days have begun and nothing is
    # logged. Both say only "A Wellness reminder".
    if cy_ok and _hm(cprefs.get('pill_at')):
        out.append({'key': 'pill', 'at': _hm(cprefs.get('pill_at')),
                    'title': TITLE, 'body': CYCLE_WORDS,
                    'url': '/wellness/'})
    if cy_ok and cprefs.get('nudge'):
        s = CY.summary(days, day, cprefs)
        win = s.get('window')
        if win and win[0] < day <= win[1] + dt.timedelta(days=3) and \
                s['state'] in ('predicted', 'first_guess', 'late') and \
                not CY.bleeding_now(s) and \
                not any(days.get((win[0] + dt.timedelta(days=i))
                                 .isoformat(), {}).get('flow') in CY.BLEED
                        for i in range((day - win[0]).days + 1)):
            out.append({'key': 'cycle_log', 'at': CYCLE_AT,
                        'title': TITLE, 'body': CYCLE_WORDS,
                        'url': '/wellness/'})
    return out

'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
''',
         r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # CY-3, 31 Oct 2026 - deeper cycle tracking.
    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
     'a': 'Yes. In Cycle settings, under More to log, switch on mood, '
          'energy, sleep, discharge or your own tags (type them, separated '
          'by commas). They appear in Log today, and Patterns shows how '
          'they follow your cycle. All of it is locked like the rest.'},
    {'q': 'What are PMS days?',
     'a': 'After three periods with symptoms logged, the calendar shades '
          'the days before each expected period when your symptoms usually '
          'begin - faint rose. The calendar looks six months ahead.'},
    {'q': 'Can Wellness remind me to take my pill?',
     'a': 'Yes. In Cycle settings set a daily pill reminder time. Like '
          'every cycle reminder it only says "A Wellness reminder". You can '
          'also ask for a nudge to log once your period is due.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
'''),
        (r'''    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line: 7, 14, 21 or 30 days, '
          'every day. Choose "Make it a challenge" when you add or edit a '
          'habit, or tap one of the challenges to try. Only the days you do '
          'count, so Today shows "Day 12 of 30".'},
    {'q': 'What happens if I miss a day of a challenge?',
''',
         r'''    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line: 7, 14, 21 or 30 days, '
          'or your own number (tap Own and type it, 2 to 365), every day. '
          'Choose "Make it a challenge" when you add or edit a habit, or '
          'tap one of the challenges to try. Only the days you do '
          'count, so Today shows "Day 12 of 30".'},
    {'q': 'What happens if I miss a day of a challenge?',
'''),
        (r'''          'you hear is sent anywhere, and only the minutes are kept.'},
    {'q': 'How do I choose the voice for Guided practices?',
     'a': 'Wellness uses your phone\'s own voice. On the Guided page tap '
          '"Voice" to pick one and hear it. On a Samsung, more voices are '
          'in the phone\'s Settings, General management, Text-to-speech: '
          'choose Google, then Install voice data, English, and pick a '
''',
         r'''          'you hear is sent anywhere, and only the minutes are kept.'},
    {'q': 'How do I choose the voice for Guided practices?',
     'a': 'Wellness uses your phone\'s own voice. First just try a '
          'practice - if the voice sounds right, there is nothing to do. '
          'If not, on the Guided page tap "Voice" to pick another and hear '
          'it. On a Samsung, more voices are '
          'in the phone\'s Settings, General management, Text-to-speech: '
          'choose Google, then Install voice data, English, and pick a '
'''),
        (r'''    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Tap the cog at the top '
          'right, then Cycle tracker. It then gets its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
''',
         r'''    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Tap the cog at the top '
          'right, open Your sections and tick Cycle tracker. It then gets '
          'its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge: 7, 14, 21 or 30 days, every day.',
        ],
        'signs': [],
''',
         r'''            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge: 7, 14, 21 or 30 days - or your own number, '
            'from 2 to 365 - every day.',
        ],
        'signs': [],
'''),
        (r'''            ('--w-sky-soft', 'Pale blue: the fertile estimate, only if you '
                             'turned it on. An estimate, not contraception.'),
        ],
    },
''',
         r'''            ('--w-sky-soft', 'Pale blue: the fertile estimate, only if you '
                             'turned it on. An estimate, not contraception.'),
            ('--w-rose-wash', 'Faint rose: PMS days - when symptoms usually '
                              'come before a period, from what you logged. '
                              'The calendar looks six months ahead.'),
        ],
    },
'''),
        (r'''            'Tick anything you notice, and move the pain slider if you '
            'like.',
            'A private note is only for you.',
        ],
        'signs': [('', 'Locked before it is saved. Never in emails.')],
    },
    'cycle_settings': {
        'title': 'Cycle settings',
        'purpose': 'Modes, the fertile estimate, reminders, and your log.',
        'steps': [
            'Pregnancy and hormonal contraception pause predictions.',
            'Download my log saves everything as a file.',
            'Turning it off keeps your log, locked. Delete everything '
''',
         r'''            'Tick anything you notice, and move the pain slider if you '
            'like.',
            'Mood, energy, sleep, discharge and your own tags appear here '
            'when you switch them on in Cycle settings.',
            'A private note is only for you.',
        ],
        'signs': [('', 'Locked before it is saved. Never in emails.')],
    },
    'cycle_settings': {
        'title': 'Cycle settings',
        'purpose': 'Modes, the fertile estimate, reminders, more to log, '
                   'and your log.',
        'steps': [
            'Pregnancy and hormonal contraception pause predictions.',
            'Reminders - a day before, a nudge to log, a daily pill time - '
            'only ever say "A Wellness reminder".',
            'More to log adds mood, energy, sleep, discharge or your own '
            'tags to Log today, and to Patterns.',
            'Download my log saves everything as a file.',
            'Turning it off keeps your log, locked. Delete everything '
'''),
        (r'''                   'period.',
        'steps': [
            'Patterns appear after three periods with symptoms logged.',
            'Make the report for a one-page summary to show a doctor.',
        ],
''',
         r'''                   'period.',
        'steps': [
            'Patterns appear after three periods with symptoms logged. '
            'Mood, sleep, energy and your own tags count too.',
            'Make the report for a one-page summary to show a doctor.',
        ],
'''),
    ]),
    (os.path.join('test_wellness_seven.py'), [
        (r'''               'WL-5' not in ca.get('/wellness/').content.decode(),
               'and no note of ours is printed on a page')
            ok('href="/wellness/badges/"' in t and
               'href="/wellness/cycle/"' in t,
''',
         r'''               'WL-5' not in ca.get('/wellness/').content.decode(),
               'and no note of ours is printed on a page')
            # CY-3 (Release 56, Demetri 31 Oct 21:06): the cycle tracker
            # is reached from Your sections only, not a row of its own.
            ok('href="/wellness/badges/"' in t and
               'href="/wellness/cycle/"' in t,
'''),
    ]),
    (os.path.join('test_wellness_ten.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def carry_on('" in gate, '  with a sentinel on the challenges')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# CY-3 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/challenge.py'; Text = " in gate,
   '  with a sentinel on the challenges')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'def place('; What = 'CY-2: the cycle phases are on disk - without them the cycle tracker cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def valid_days('; What = 'WL-8/CY-3: the challenge rules are on disk, with your own number of days - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'def place('; What = 'CY-2: the cycle phases are on disk - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_eleven.py',
    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    'test_wellness_twelve.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_eleven.py',
    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    'test_wellness_twelve.py',
    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    'test_wellness_thirteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    '.bak_wellness12',
]

''',
         r'''    # CY-2, 31 Oct 2026 - Wellness: cycle phases.
    '.bak_wellness12',
    # CY-3, 31 Oct 2026 - Wellness: deeper cycle tracking.
    '.bak_wellness13',
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
    raise SystemExit('CY-3 REFUSED: %s' % msg)


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
    if "'test_wellness_thirteen.py'" in read(pq):
        print('CY-3 already applied.')
        return 0
    if "'test_wellness_twelve.py'" not in read(pq):
        refuse('Release 55 is not applied - this round registers after it.')
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
        print('CY-3 --check: %d file(s) would change, none written; %d '
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
    print('CY-3 applied - Wellness: deeper cycle tracking.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
