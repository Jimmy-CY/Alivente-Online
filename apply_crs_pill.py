# -*- coding: utf-8 -*-
"""SECTION C, ROUND C3 - THE CRS PILL TAKES THE MODEL'S WORD

Two CRS screens draw a submission's lifecycle state as a pill. The pill's
geometry has been base's .alv-pill since X6. Its COLOUR was not: each page
carried five rules of its own -

    .status-draft                { background: var(--alv-neutral-soft); ... }
    .status-closed               { background: var(--alv-info-soft);    ... }
    .status-submitted_externally { background: var(--alv-warn-soft);    ... }
    .status-acknowledged         { background: var(--alv-good-soft);    ... }
    .status-rejected             { background: var(--alv-bad-soft);     ... }

- ten rules across two files, and base already says all five:

    .alv-pill-neutral .alv-pill-info .alv-pill-attn .alv-pill-good
    .alv-pill-bad

Measured today, the page rules and base's rules set the SAME background
and the SAME colour, one for one. The only thing base adds is the border
every other pill in the system wears; these five were transparent.

WHY THEY WERE KEPT, AND WHY THAT REASON IS NOW GONE. X6 wrote the reason
into the page and it was a good one:

    the class is built from the model's status key - a template variable
    appended to `status-` in the markup, and in the modal's JS - so
    writing a mapping to .alv-pill-good in both places would be two
    mappings in two languages, which drift.

Both mappings would have drifted. The answer is not to write it twice,
it is to write it WHERE THE STATUS ALREADY LIVES: one property on the
model, which the template and the JS both read. CelebrationEvent has had
exactly this shape since C1 (pages/models.py, tone_class), and Demetri
approved the same for CRS on 29 Sep.

    Submission.pill_class  ->  "alv-pill alv-pill-good"

THE MODEL CHANGE ADDS NO MIGRATION. A property is not a field: nothing
about the database changes, so there is nothing for a deploy to migrate.

AND THE TWO CAN NO LONGER DISAGREE. Before this round, the table's badge
and the same submission's badge in the View modal were built by two
different pieces of code in two different languages, both concatenating
the status key onto a prefix. Now both emit one string that one property
returned.

Backups: .bak_crspill. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_crspill'
CRLF = {}

MODEL = os.path.join(os.getcwd(), 'crs', 'models.py')
LIST = 'crs/submission_list.html'
DETAIL = 'crs/submission_detail.html'

# THE MAPPING, ONCE. Each page rule is named beside the base class that
# replaces it, and the suite proves the two paint the same colour.
PAIRS = [
    ('draft',                'neutral', '--alv-neutral-soft', '--alv-neutral'),
    ('closed',               'info',    '--alv-info-soft',    '--alv-accent-ink'),
    ('submitted_externally', 'attn',    '--alv-warn-soft',    '--alv-warn'),
    ('acknowledged',         'good',    '--alv-good-soft',    '--alv-good'),
    ('rejected',             'bad',     '--alv-bad-soft',     '--alv-bad'),
]


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
            raise SystemExit('C3: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label, count=1):
    a = eol(path, was)
    if text.count(a) != count:
        raise SystemExit('C3: %s - %s is there %d time(s), not %d'
                         % (label, what, text.count(a), count))
    print('     %s' % what)
    return text.replace(a, eol(path, now))


# ==========================================================================
# 1. THE MODEL - where the status already lives
# ==========================================================================
MODEL_WAS = '''    @property
    def reporting_period(self):
        """ReportingPeriod for the OECD Message Header - Dec 31 of self.year."""
        return date(self.year, 12, 31)'''

MODEL_NOW = '''    @property
    def reporting_period(self):
        """ReportingPeriod for the OECD Message Header - Dec 31 of self.year."""
        return date(self.year, 12, 31)

    # ===== How the lifecycle is DRAWN ======================================
    # Ten CSS rules across two templates used to say this - five on the
    # list and the same five on the detail page - because the class was
    # built by appending self.status to "status-" in the markup, and
    # again in the View modal's JavaScript. Two concatenations in two
    # languages, and a mapping that would have had to be written in both.
    #
    # It belongs here instead, where the status is. The template asks for
    # sub.pill_class and the modal's payload carries the same string, so
    # the table badge and the modal badge cannot disagree about a colour
    # the way two hand-written mappings eventually would.
    #
    # A PROPERTY IS NOT A FIELD: no migration, nothing in the database
    # changes. The same shape CelebrationEvent.tone_class uses.
    PILL_CLASSES = {
        "draft":                "alv-pill-neutral",
        "closed":               "alv-pill-info",
        "submitted_externally": "alv-pill-attn",
        "acknowledged":         "alv-pill-good",
        "rejected":             "alv-pill-bad",
    }

    @property
    def pill_class(self):
        """The house pill classes for this submission's lifecycle state.

        Neutral for an unknown status, which is the honest answer: a
        state nobody has given a meaning to must not borrow one."""
        return "alv-pill %s" % self.PILL_CLASSES.get(
            self.status, "alv-pill-neutral")'''

# ==========================================================================
# 2. THE TWO TEMPLATES
# ==========================================================================
OPEN = '/* THE FIVE LIFECYCLE TONES'
LAST = '.status-rejected'


def five_block(text, path, label):
    """The note that explains the five rules AND the five rules, as one
    region - located by its two ends instead of quoted in full.

    The list page's note runs to twenty-five lines. Pasting it into this
    file would make this round's own source a second copy of prose that
    exists only to be deleted, and the two copies would have to match
    character for character or the round would refuse. Two ends and a
    count of what lies between them says the same thing and cannot
    disagree with itself."""
    o = eol(path, OPEN)
    if text.count(o) != 1:
        raise SystemExit('C3: %s - the lifecycle note is there %d time(s), '
                         'not 1' % (label, text.count(o)))
    i = text.index(o)
    k = text.find(eol(path, LAST), i)
    if k < 0:
        raise SystemExit('C3: %s - the note is not followed by %s'
                         % (label, LAST))
    j = text.find('\n', k)
    if j < 0:
        raise SystemExit('C3: %s - %s is the last line of the file'
                         % (label, LAST))
    block = text[i:j]
    # WHAT IS BETWEEN THE TWO ENDS MUST BE THE FIVE RULES AND NOTHING
    # ELSE. A region matched by its ends is only as safe as the check on
    # its middle.
    rules = re.findall(r'^\s*(\.status-[a-z_]+)\s*\{([^{}]*)\}\s*$',
                       block, re.M)
    if len(rules) != 5:
        raise SystemExit('C3: %s - the region holds %d status rules, not 5: '
                         '%s' % (label, len(rules), [r[0] for r in rules]))
    for (sel, body), (st, _, bg, fg) in zip(rules, PAIRS):
        if sel != '.status-%s' % st:
            raise SystemExit('C3: %s - expected .status-%s and found %s'
                             % (label, st, sel))
        if bg not in body or fg not in body:
            raise SystemExit('C3: %s - %s is %s, not %s / %s; this round '
                             'must not change a colour by accident'
                             % (label, sel, ' '.join(body.split()), bg, fg))
    if re.sub(r'/\*.*?\*/', '', block, flags=re.S).strip().count('{') != 5:
        raise SystemExit('C3: %s - the region carries something besides the '
                         'note and the five rules' % label)
    return i, j


GONE = """/* THE FIVE LIFECYCLE TONES WERE HERE - taken 30 Sep.
     They were kept, correctly, while the class was built by appending
     the status key to a prefix in two languages: a mapping to
     .alv-pill-good would then have had to be written twice, and two
     mappings drift. Submission.pill_class writes it once, on the model,
     and the markup and the modal JS both read that.

     Each of the five set the same background and the same colour as the
     base class that now replaces it; what they did NOT set is the
     border, so these five pills were the only ones in the system without
     one. They have it now.
                                                    [test_crs_pill.py] */"""

# ==========================================================================
print('=' * 74)
print('SECTION C, ROUND C3 - THE CRS PILL TAKES THE MODEL\'S WORD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- the model ----------------------------------------------------------
print('  crs/models.py')
t, raw = read(MODEL)
if 'pill_class' in t:
    print('     already carries pill_class')
else:
    # The docstring in the file may carry an em dash; match on what is
    # there rather than on what this file can type.
    was = MODEL_WAS
    if eol(MODEL, was) not in t:
        was = MODEL_WAS.replace(
            'Message Header - Dec', 'Message Header — Dec')
    t = swap(t, MODEL, was,
             MODEL_NOW.replace(
                 'Message Header - Dec',
                 'Message Header — Dec' if '— Dec' in was
                 else 'Message Header - Dec'),
             'Submission gains PILL_CLASSES and pill_class - no migration, '
             'a property is not a field', 'crs/models.py')
    for st, name, _, _ in PAIRS:
        if '"%s":' % st not in t:
            raise SystemExit('C3: crs/models.py - the mapping does not name '
                             'the status %s' % st)
        if 'alv-pill-%s' % name not in t:
            raise SystemExit('C3: crs/models.py - the mapping does not name '
                             'alv-pill-%s' % name)
    if not CHECK:
        back_up(MODEL, raw)
        write(MODEL, t)

# ---- the two templates --------------------------------------------------
for name, mk_was, mk_now in (
        (LIST,
         '<span class="alv-pill status-{{ sub.status }}">',
         '<span class="{{ sub.pill_class }}">'),
        (DETAIL,
         '<span class="alv-pill status-{{ submission.status }}">',
         '<span class="{{ submission.pill_class }}">')):
    p = alv_tree.path_of(name)
    t, raw = read(p)
    print('  %s' % name)
    # ASK THE NARROW QUESTION. "pill_class in t" was true before this
    # round ever ran: X6's own note says a pill_class property WOULD let
    # both emit the house class, and that sentence is prose, not markup.
    # A round that reads the explanation of the thing it came to build
    # decides it has already built it. Lesson 21, in the one place it can
    # do the most damage - the idempotency guard.
    if eol(p, mk_now) in t:
        print('     already reads the model')
        continue
    i, j = five_block(t, p, name)
    print('     the note and the five rules go - %d characters' % (j - i))
    t = t[:i] + eol(p, GONE) + t[j:]
    t = swap(t, p, mk_was, mk_now,
             '  the badge asks the model for its class', name)

    if name == LIST:
        t = swap(t, p,
                 """      status_key:     "{{ sub.status }}",""",
                 """      status_key:     "{{ sub.status }}",
      pill_class:     "{{ sub.pill_class }}",""",
                 '  the modal payload carries the same string', name)
        t = swap(t, p,
                 """    badge.className = 'alv-pill status-' + s.status_key;""",
                 """    badge.className = s.pill_class;""",
                 '  and the modal stops building the class a second time',
                 name)

    # GATES.
    css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))
    bare = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    for st, _, _, _ in PAIRS:
        if '.status-%s' % st in bare:
            raise SystemExit('C3: %s still carries a .status-%s rule'
                             % (name, st))
    nocom = re.sub(r'/\*.*?\*/|<!--.*?-->|\{#.*?#\}', '', t, flags=re.S)
    if re.search(r"""['"]status-['"]|status-\{\{""", nocom):
        raise SystemExit('C3: %s still builds a class by appending the '
                         'status key' % name)
    # FOUR ON THE LIST: the badge in the table, the payload key AND its
    # value on one line, and the modal's one reader. One on the detail
    # page, which has no modal.
    want = 4 if name == LIST else 1
    if nocom.count('pill_class') != want:
        raise SystemExit('C3: %s names pill_class %d time(s), not %d'
                         % (name, nocom.count('pill_class'), want))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- base really does say all five --------------------------------------
print('  base.html')
b = read(alv_tree.path_of('base.html'))[0]
bbare = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
for st, cls, bg, fg in PAIRS:
    m = re.search(r'\.alv-pill-%s\s*\{([^}]*)\}' % cls, bbare)
    if not m:
        raise SystemExit('C3: base has no .alv-pill-%s, so the page rule '
                         'cannot go' % cls)
    body = m.group(1)
    if bg not in body or fg not in body:
        raise SystemExit('C3: .alv-pill-%s is %s, and the rule it replaces '
                         'was %s / %s - this round must not change a colour'
                         % (cls, ' '.join(body.split()), bg, fg))
    print('     .alv-pill-%-8s == the old .status-%s, and adds the border'
          % (cls, st))

print('-' * 74)
print('  ten CSS rules in two files become one property on the model, and')
print('  the table badge and the modal badge read the same string.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
