# -*- coding: utf-8 -*-
"""SECTION C, ROUND C1 - AN EVENT TYPE IS A CATEGORY, NOT A VERDICT

Demetri, on three screens in a row: the Detailed Contacts view, the
timeline, and the calendar. Anniversary is bright red. And on the
calendar, Birthday and Nameday are the same colour with a different
symbol.

Both are true, and both come from one method:

    def get_color_class(self):
        colors = {
            'birthday':    'info',      # Blue
            'nameday':     'primary',   # Purple/Blue
            'anniversary': 'danger',    # Red
            'custom':      'success',   # Green
        }

Bootstrap's names. `danger` is the red this system uses for a failure and
`success` is the green it uses for one that worked, so an anniversary was
painted in the error colour and a custom event in the success colour. The
same fault as the CRS IN count in X3 and the row actions in D3: one
colour saying two things.

AND THE CALENDAR'S TWO IDENTICAL DOTS

    .event-dot.birthday { background: #0e7c8b; }
    .event-dot.nameday  { background: var(--alv-accent); }

--alv-accent IS #0e7c8b. The same colour, written two ways, on two
different types - so the type was carried entirely by the icon. Three
pages repeat that pair: the dots, the legend beside them, and the
timeline rows.

WHAT IT BECOMES, AND WHY IT IS NOT A NEW PALETTE
    base already owns a categorical chip set, added for exactly this kind
    of thing: .alv-tag-sky, -moss, -clay, -slate, -plum, each with an ink
    token and a soft ground. Five hues that mean nothing but themselves.
    So the event types map onto what exists:

        Birthday      alv-tag-sky     #2b6a86
        Nameday       alv-tag-moss    #4a6b3c
        Anniversary   alv-tag-clay    #8a5a34
        Custom Event  alv-tag-plum    #6b4a72

    MEASURED: white on each ink is 5.85 to 7.37, and each ink on its own
    soft ground is 5.14 to 6.41. All five clear AA comfortably.

    THEY DIFFER BY HUE AND NOT BY WEIGHT - the ratios between any two of
    them run 1.01 to 1.26, which is the point of a categorical set: no
    member reads as more important than another. It also means hue is
    doing the work, so every event keeps its ICON and its WORD as well.
    Nobody has to tell clay from moss to use this screen.

THE ONE THING BASE GAINS is four token names for four values it already
writes as literals inside the .alv-tag rules - the same reasoning base's
own comment gives for the ink tokens two lines above them. Nothing
changes appearance: the tokens hold the identical values.

Backups: .bak_evtone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_evtone'
CRLF = {}

BASE = 'base.html'
MGMT = 'celebration_management.html'
CAL = 'celebration_calendar.html'
MODELS = os.path.join('pages', 'models.py')

TONES = [('birthday', 'sky'), ('nameday', 'moss'),
         ('anniversary', 'clay'), ('custom', 'plum')]

SOFTS = [('sky', '#e8f1f5', '#d3e4ec'), ('moss', '#eef4e9', '#dde8d6'),
         ('clay', '#f7efe7', '#ecdfd2'), ('slate', '#eef1f3', '#e0e5e9'),
         ('plum', '#f3edf5', '#e5dae8')]


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('C1: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('C1: %s - %s is there %d time(s), not 1'
                         % (label, what, text.count(a)))
    print('     %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# 1. base - name the four grounds it already writes
# ==========================================================================
TOK_WAS = "        --alv-tag-plum-ink:  #6b4a72;"
TOK_NOW = """        --alv-tag-plum-ink:  #6b4a72;

        /* AND THEIR GROUNDS, NAMED - 29 Sep. The five .alv-tag rules
           below already wrote these exact values as literals; the inks
           two lines up were pulled out for the reason the comment
           above gives, and the grounds were left behind. Celebrations
           needs them outside a chip - a row's background and a stripe
           take the same tone as the chip on that row - and a page
           cannot reach into a rule to borrow a literal. Same values,
           so nothing changes appearance. */
        --alv-tag-sky-soft:   #e8f1f5;  --alv-tag-sky-line:   #d3e4ec;
        --alv-tag-moss-soft:  #eef4e9;  --alv-tag-moss-line:  #dde8d6;
        --alv-tag-clay-soft:  #f7efe7;  --alv-tag-clay-line:  #ecdfd2;
        --alv-tag-slate-soft: #eef1f3;  --alv-tag-slate-line: #e0e5e9;
        --alv-tag-plum-soft:  #f3edf5;  --alv-tag-plum-line:  #e5dae8;"""

RULE_WAS = """      .alv-tag-sky   { color: var(--alv-tag-sky-ink);   background: #e8f1f5; border-color: #d3e4ec; }
      .alv-tag-moss  { color: var(--alv-tag-moss-ink);  background: #eef4e9; border-color: #dde8d6; }
      .alv-tag-clay  { color: var(--alv-tag-clay-ink);  background: #f7efe7; border-color: #ecdfd2; }
      .alv-tag-slate { color: var(--alv-tag-slate-ink); background: #eef1f3; border-color: #e0e5e9; }
      .alv-tag-plum  { color: var(--alv-tag-plum-ink);  background: #f3edf5; border-color: #e5dae8; }"""

RULE_NOW = '\n'.join(
    '      .alv-tag-%-5s { color: var(--alv-tag-%s-ink); '
    'background: var(--alv-tag-%s-soft); '
    'border-color: var(--alv-tag-%s-line); }' % (n, n, n, n)
    for n, _s, _l in SOFTS)

# ==========================================================================
# 2. the model - a categorical tone, not a Bootstrap verdict
# ==========================================================================
MODEL_WAS = '''    def get_color_class(self):
        """Get Bootstrap color class based on event type"""
        colors = {
            'birthday': 'info',      # Blue
            'nameday': 'primary',    # Purple/Blue
            'anniversary': 'danger', # Red
            'custom': 'success',     # Green
        }
        return colors.get(self.event_type, 'secondary')'''

MODEL_NOW = '''    #: An event TYPE is a category, not a verdict. This used to be
    #: get_color_class(), returning Bootstrap names - and 'danger' is the
    #: red this system uses for a failure, 'success' the green it uses
    #: for one that worked. An anniversary was painted in the error
    #: colour and a custom event in the success colour, on three screens.
    #:
    #: base owns a categorical chip set for exactly this: five hues that
    #: mean nothing but themselves. The four types map onto four of them.
    #: The value is a class name, used as-is - not a Bootstrap suffix, so
    #: a template writes `class="alv-tag {{ event.tone_class }}"`.
    TONE_CLASSES = {
        'birthday': 'alv-tag-sky',
        'nameday': 'alv-tag-moss',
        'anniversary': 'alv-tag-clay',
        'custom': 'alv-tag-plum',
    }

    @property
    def tone_class(self):
        """The categorical chip class for this event's type."""
        return self.TONE_CLASSES.get(self.event_type, 'alv-tag-slate')'''

# ==========================================================================
# 3. Celebration Management - the rows and the badge
# ==========================================================================
MGMT_ROWS_WAS = """.event-item.birthday {
    border-left-color: #0e7c8b;
    background: #e7f6f8;
}

.event-item.nameday {
    border-left-color: var(--alv-accent);
    background: #f0ebf8;
}

.event-item.anniversary {
    border-left-color: #dc3545;
    background: #f8e7e9;
}

.event-item.custom {
    border-left-color: #28a745;
    background: #e7f4e9;
}"""

MGMT_ROWS_NOW = """/* ONE TONE PER TYPE, and the row takes the same one as its chip.
   Anniversary was #dc3545 - the error red - and custom was #28a745, the
   success green. Both now name a tone that means nothing but itself. */
""" + '\n\n'.join(
    """.event-item.%s {
    border-left-color: var(--alv-tag-%s-ink);
    background: var(--alv-tag-%s-soft);
}""" % (t, tone, tone) for t, tone in TONES)

MGMT_BADGE_WAS = """                                <span class="badge badge-{{ event.get_color_class }} event-type-badge">"""
MGMT_BADGE_NOW = """                                <span class="alv-tag {{ event.tone_class }} event-type-badge">"""

# ==========================================================================
# 4. The Calendar - dots, legend, timeline rows, timeline badge
# ==========================================================================
CAL_DOT_WAS = """.event-dot.birthday {
    background: #0e7c8b;
    color: white;
}

.event-dot.nameday {
    background: var(--alv-accent);
    color: white;
}

.event-dot.anniversary {
    background: #dc3545;
    color: white;
}

.event-dot.custom {
    background: #28a745;
    color: white;
}"""

CAL_DOT_NOW = """/* THESE TWO WERE THE SAME COLOUR. birthday was #0e7c8b and nameday was
   var(--alv-accent), which IS #0e7c8b - so on the month grid the type was
   carried entirely by the icon. Four tones now, and the icon stays,
   because a categorical set differs by hue and hue alone is not enough
   on its own. */
""" + '\n\n'.join(
    """.event-dot.%s {
    background: var(--alv-tag-%s-ink);
    color: var(--alv-on-accent);
}""" % (t, tone) for t, tone in TONES)

CAL_LEGEND_WAS = """.legend-color.birthday { background: #0e7c8b; }
.legend-color.nameday { background: var(--alv-accent); }
.legend-color.anniversary { background: #dc3545; }
.legend-color.custom { background: #28a745; }"""

CAL_LEGEND_NOW = '\n'.join(
    '.legend-color.%s { background: var(--alv-tag-%s-ink); }' % (t, tone)
    for t, tone in TONES)

CAL_ROWS_WAS = """.timeline-event-item.birthday {
    border-left-color: #0e7c8b;
    background: #f8fdff;
}

.timeline-event-item.nameday {
    border-left-color: var(--alv-accent);
    background: #faf8fc;
}

.timeline-event-item.anniversary {
    border-left-color: #dc3545;
    background: #fff8f9;
}

.timeline-event-item.custom {
    border-left-color: #28a745;
    background: #f8fcf9;
}"""

CAL_ROWS_NOW = '\n\n'.join(
    """.timeline-event-item.%s {
    border-left-color: var(--alv-tag-%s-ink);
    background: var(--alv-tag-%s-soft);
}""" % (t, tone, tone) for t, tone in TONES)

CAL_BADGE_WAS = """                            <span class="badge badge-{{ event_data.event.get_color_class }} timeline-event-badge">"""
CAL_BADGE_NOW = """                            <span class="alv-tag {{ event_data.event.tone_class }} timeline-event-badge">"""

# ==========================================================================
print('=' * 74)
print('SECTION C, ROUND C1 - AN EVENT TYPE IS A CATEGORY, NOT A VERDICT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

done = 0

# ---- base --------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if '--alv-tag-sky-soft' in t:
    print('     the grounds are already named')
else:
    t = swap(t, p, TOK_WAS, TOK_NOW, 'five grounds and five lines, named',
             BASE)
    t = swap(t, p, RULE_WAS, RULE_NOW, '  and the five chip rules use them',
             BASE)
    # SCOPED TO THE CHIP RULES. The first version asked the whole
    # stylesheet and refused - on the TOKEN DEFINITIONS this round had
    # just written, which are the one place those literals are supposed
    # to live now. The fourth gate today to fire on its own round's
    # text; the shape is always the same, and so is the fix: ask the
    # narrowest thing that answers the question.
    chips = '\n'.join(l for l in t.split('\n')
                      if l.strip().startswith('.alv-tag-'))
    for n, s, l in SOFTS:
        if s in chips or l in chips:
            raise SystemExit('C1: %s still writes a literal - the value was '
                             'meant to move into the token' % n)
        if ('--alv-tag-%s-soft' % n) not in t:
            raise SystemExit('C1: --alv-tag-%s-soft was not defined' % n)

    # THE BLOCK THAT COUNTS ITSELF. base's standards block opens with
    # "N design tokens", and test_standards_doc.py measures the real
    # number against it - so a round that adds tokens updates the
    # sentence, or that suite fails with nothing wrong. It caught this
    # one at 76 against 66.
    toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', t)))
    said = re.search(r'(\d+) design tokens', t)
    if not said:
        raise SystemExit('C1: the standards block no longer states a token '
                         'count')
    if int(said.group(1)) != toks:
        t = t.replace('%s design tokens' % said.group(1),
                      '%d design tokens' % toks, 1)
        print('     the standards block: %s design tokens -> %d'
              % (said.group(1), toks))
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    done += 1

# ---- the model ---------------------------------------------------------
p = os.path.join(os.getcwd(), MODELS)
t, raw = read(p)
print('  %s' % MODELS)
if 'tone_class' in t:
    print('     tone_class is already there')
else:
    t = swap(t, p, MODEL_WAS, MODEL_NOW,
             'get_color_class becomes tone_class, on the tag set', MODELS)
    # THE DEFINITION, NOT THE WORD. The replacement's own note names
    # get_color_class while explaining what it replaced, so asking
    # whether the string is present answers yes forever. Ask whether the
    # METHOD is still defined.
    if re.search(r'^\s*def get_color_class\b', t, re.M):
        raise SystemExit('C1: get_color_class is still defined in models.py')
    if 'get_color_class' not in t:
        raise SystemExit('C1: the note explaining what tone_class replaced '
                         'has lost the name it replaced')
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    done += 1

# ---- the two pages -----------------------------------------------------
for name, pairs in ((MGMT, [(MGMT_ROWS_WAS, MGMT_ROWS_NOW, 'the event rows'),
                            (MGMT_BADGE_WAS, MGMT_BADGE_NOW, 'the badge')]),
                    (CAL, [(CAL_DOT_WAS, CAL_DOT_NOW,
                            'the month-grid dots - and birthday and nameday '
                            'stop being the same colour'),
                           (CAL_LEGEND_WAS, CAL_LEGEND_NOW, 'the legend'),
                           (CAL_ROWS_WAS, CAL_ROWS_NOW, 'the timeline rows'),
                           (CAL_BADGE_WAS, CAL_BADGE_NOW,
                            'the timeline badge')])):
    p = alv_tree.path_of(name)
    t, raw = read(p)
    print('  %s' % name)
    if 'tone_class' in t:
        print('     already on the tag set')
        continue
    for was, now, what in pairs:
        t = swap(t, p, was, now, what, name)
    # In a TEMPLATE the word only appears if the page calls it, so here
    # the plain question is the right one.
    if 'get_color_class' in t:
        raise SystemExit('C1: %s still reads get_color_class' % name)
    # SCOPED TO WHAT THIS ROUND WROTE. The page keeps two other reds -
    # .event-countdown.urgent and .timeline-event-countdown.soon - and
    # those are about URGENCY, not about a type. Red for "this is
    # happening very soon" is a colour meaning one thing, which is the
    # rule this round is enforcing, not breaking. They are literals and
    # the hex sweep will name them; they are not this round's to take.
    for was, now, what in pairs:
        for gone in ('#dc3545', '#28a745'):
            if gone in re.sub(r'/\*.*?\*/', '', now, flags=re.S):
                raise SystemExit('C1: %s wrote %s back into %s'
                                 % (name, gone, what))
        if was in t:
            raise SystemExit('C1: %s - %s did not take' % (name, what))
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    done += 1

# ==========================================================================
# 5. P4's SUITE MUST KEEP JUDGING P4 - lesson 17, and this round is what
#    revealed it.
#
#    test_filter_box.py's section 4 diffs base against its OWN backup and
#    requires that P4 added exactly one declaration. True the moment P4
#    landed; false the moment ANY later round edits base - which this one
#    does, ten tokens' worth. It failed with nothing wrong.
#
#    alv_rounds.as_left_by() is the answer the programme already has:
#    base as P4 left it is the FIRST LATER ROUND'S BACKUP of it, which is
#    .bak_evtone, written by this round a moment ago. The suite then goes
#    on judging its own round however many rounds land on base after it.
# ==========================================================================
FB = 'test_filter_box.py'
FB_WAS = """if os.path.isfile(b):
    # DIFF THE RULES, NOT THE FILE."""
FB_NOW = """if os.path.isfile(b):
    # AND THE FILE AS THIS ROUND LEFT IT, NOT AS IT IS NOW. C1 added ten
    # tokens to base on 29 Sep and this diff called every one of them a
    # change of P4's - which it is not. as_left_by() hands back base as
    # P4 left it: the first later round's backup of it, or the file
    # itself while no later round has touched it.
    try:
        from alv_rounds import as_left_by
        mine = as_left_by(alv_tree.path_of(BASE), SUFFIX, read)
    except Exception:
        mine = base

    # DIFF THE RULES, NOT THE FILE."""

p_fb = os.path.join(os.getcwd(), FB)
t_fb, raw_fb = read(p_fb)
print('  %s' % FB)
if 'as_left_by' in t_fb:
    print('     already judges base as P4 left it')
else:
    t_fb = swap(t_fb, p_fb, FB_WAS, FB_NOW,
                'section 4 diffs base as P4 left it', FB)
    t_fb = swap(t_fb, p_fb, 'rules(read(b)), rules(base),',
                'rules(read(b)), rules(mine),',
                '  and compares against that, not against base now', FB)
    if not CHECK:
        back_up(p_fb, raw_fb)
        write(p_fb, t_fb)
    done += 1

# ---- nobody else asks --------------------------------------------------
left = []
for q in alv_tree.templates():
    if 'get_color_class' in open(q, encoding='utf-8', errors='replace').read():
        left.append(alv_tree.rel(q))
if left and not CHECK:
    raise SystemExit('C1: get_color_class is gone from the model but %s '
                     'still calls it - those pages would render an empty '
                     'class' % left)

print('-' * 74)
print('  %d file(s) changed. Birthday sky, Nameday moss, Anniversary clay,'
      % done)
print('  Custom plum - four hues that mean nothing but themselves.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
