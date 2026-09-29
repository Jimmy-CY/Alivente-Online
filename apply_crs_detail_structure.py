# -*- coding: utf-8 -*-
"""SECTION X, ROUND X9 - SUBMISSION DETAIL: THE SECTIONS, THE FORM, THE
TABLES

X8 changed everything you could see on this page and nothing structural.
X9 takes the two structural clusters Demetri agreed to split off: the
eight section cards with the form inside them, and the four validation
tables. X10 then takes the lifecycle timeline, the Excel panel and the
XML modal, and deletes the --crs-* alias X8 deliberately left standing.

THE ONE THING THAT IS NOT A STYLING CHANGE
    The validation table overflows on a phone, and it is CLIPPED rather
    than scrollable. Measured, at 390px:

        table width     414px
        viewport        390px
        overflows       yes
        page scrolls    NO

    Five columns and no media rule anywhere in the page - measured, the
    phone block never mentions .validation-table at all. So the Fix
    column, which is where a draft submission gets corrected, is simply
    unreachable on a phone. Demetri's standing rule is that every
    Add/Edit screen must work on a phone; this one does not.

    base's .alv-table turns every row into a card under 768px and reads
    data-label for the prefixes. So joining the house component is not a
    tidy-up here - it is the fix.

THE SECTIONS ARE ALREADY .form-card, UNDER ANOTHER NAME
    Eight .detail-section blocks, each with a .detail-section-title.
    Measured against base: .form-card is the titled section container and
    .form-section-title is its heading, and forty-five pages already wear
    them. The page's own pair is the same component with different words,
    so it gives them up - and .detail-section-title was also duplicating
    base's rule while painting it from --crs-dark.

.form-actions IS KEPT, AND FOUR ROUNDS DELETED ONE
    X2, X4 and X7 deleted .form-actions from the CRS entry screens,
    because a house entry screen puts its primary in the top bar and has
    no footer row. THAT DOES NOT APPLY HERE, and the difference is
    structural rather than a matter of taste.

    An entry screen is ONE form. This page is eight sections, of which
    three hold a form of their own - Message Header, Customer Data Excel,
    Actions - each with its own submit. There is no single primary to
    lift into the bar, and lifting one of three would say that one of
    them is the page's purpose when none is. So the row stays where the
    control it submits is, and only loses its hex.

    Same rule as the X5 panel decision, pointing the other way: look at
    what the house does for THIS SHAPE of page, rather than carrying a
    verdict across from a page that only looked similar.

A COMPOUND RULE THAT DUPLICATES BASE - THE SECOND ONE
        .form-field .form-control {
          padding: 7px 10px; border: 1px solid #ced4da;
          border-radius: 5px; font-size: 14px;
        }

    Character for character the rule X4 found on fi_form, and deleted
    for the same reason: base's .form-control already sets all four, and
    sets the border to 2px of --alv-line rather than 1px of a grey hex.
    Two pages carried it; test_compound_rules.py is waiting on both.

KEPT, AND WHY
    .detail-grid and its dt/dd - base owns no definition list, and this
    page uses one properly for a read-only record. Retoned.
    .ref-id-display, .validation-group, .validation-details, and the
    .fix-* family - all components base does not have. Retoned.
    .row-error and .row-correction keep their job and take the tokens
    that already mean it: --alv-bad-soft is 27 of 765 away from the hex
    they used, --alv-warn-soft is 24. Invisible shifts that put a tinted
    row on the same token as the pill that means the same thing.

Backups: .bak_crsdets. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsdets'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('X9: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    """Lesson 21."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('X9: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
SWEEP = [
    (r'<div class="detail-section">', '<div class="form-card">',
     'detail-section -> form-card', 8),
    (r'<div class="detail-section-title">([^<]*)</div>',
     r'<h3 class="form-section-title">\1</h3>',
     'the eight section titles become h3, as the house writes them', 8),
    # The full-width one carries an id and a conditional inline style,
    # so it is matched on its class attribute rather than on a whole tag.
    (r'class="form-field form-field-full"',
     'class="form-group form-group-full"',
     'form-field-full -> form-group-full', 1),
    (r'<div class="form-field">', '<div class="form-group">',
     'form-field -> form-group', 5),
    # The grid-span rule is RENAMED, not deleted - base owns no such
    # class, and the markup above has just started using the new name.
    (r'\n  \.form-field-full \{ grid-column: 1 / -1; \}',
     '\n  .form-group-full { grid-column: 1 / -1; }',
     'the grid-span rule follows its class', 1),
    (r'<span class="req">\*</span>', '<span class="alv-req">*</span>',
     'req -> alv-req', 5),
    (r'class="field-help"', 'class="form-text"',
     'field-help -> form-text', 14),

    # THE TABLE JOINS THE HOUSE COMPONENT. This is the phone fix.
    (r'<table class="validation-table">',
     '<table class="table alv-table validation-table">',
     'the four validation tables join .alv-table', 4),
]

# THE TABLE CELLS. FOUR TABLES, FOUR DIFFERENT COLUMN SETS - and the
# first draft of this round assumed two identical ones and was refused by
# its own count gate rather than labelling half of them. Each cell is
# named against the header above it, in document order.
CELLS = [
    # 1. Excel validation errors - Cell, Field, Value, Reason, Fix
    ('<td>{{ e.col }}{{ e.row }}</td>', 'Cell'),
    ('<td>{{ e.field }}</td>', 'Field'),
    ('<td><code>{{ e.value|truncatechars:40 }}</code></td>', 'Value'),
    ('<td>{{ e.reason }}</td>', 'Reason'),
    ('<td class="fix-cell">', 'Fix'),
    # 2. Corrections applied - Cell, Field, Original, Corrected, Reason
    ('<td>{{ c.col }}{{ c.row }}</td>', 'Cell'),
    ('<td>{{ c.field }}</td>', 'Field'),
    ('<td><code>{{ c.original|truncatechars:30 }}</code></td>', 'Original'),
    ('<td><code>{{ c.corrected|truncatechars:30 }}</code></td>',
     'Corrected'),
    ('<td>{{ c.reason }}</td>', 'Reason'),
    # 3. Accounts parsed - Sheet, Row, Account Number, Holder, Balance, CPs
    ('<td>{{ a.sheet }}</td>', 'Sheet'),
    ('<td>{{ a.row_number }}</td>', 'Row'),
    ('<td><code>{{ a.account_number|truncatechars:30 }}</code></td>',
     'Account Number'),
    ('<td>{{ a.balance }} {{ a.balance_currency }}</td>', 'Balance'),
    ('<td>{{ a.controlling_persons|length }}</td>', 'CPs'),
    # 4. XSD validation - Line, Domain, Message
    ('<td>{{ err.line }}</td>', 'Line'),
    ('<td>{{ err.domain_name }}</td>', 'Domain'),
    ('<td>{{ err.message }}</td>', 'Message'),
]

# The Holder cell spans several template tags, so it is anchored on its
# opening tag alone rather than on a body that would have to be quoted
# exactly.
HOLDER = ('<td>{% if a.holder_name %}', '<td data-label="Holder">'
          '{% if a.holder_name %}')

DEAD = [
    # base owns the section card and its title.
    '.detail-section',
    '.detail-section-title',
    # base owns the form group, its label, its control and its help.
    '.form-field',
    '.form-field label',
    '.form-field .req',
    '.form-field .form-control',
    '.form-field textarea.form-control',
    '.form-field .field-help',
    # base owns the table's geometry now.
    '.validation-table',
    '.validation-table th',
    '.validation-table td',
    '.validation-table tbody tr:last-child',
    # the phone block's copies of the same
    '.form-field .form-control',
]

KEPT = [
    '.form-group-full', '.detail-header', '.ref-id-display', '.ref-id-display small',
    '.ref-id-display code', '.detail-grid', '.detail-grid dt',
    '.detail-grid dd', '.detail-grid dd code', '.detail-grid dd small',
    '.form-grid', '.form-actions', '.detail-action-row', '.detail-audit',
    '.validation-group', '.validation-group-header',
    '.validation-details summary', '.row-error td', '.row-correction td',
    '.fix-cell', '.fix-form', '.fix-input', '.fix-btn', '.fix-na',
    '.validation-table code',
]

# ==========================================================================
# THE RETONE, DONE BY SCOPE RATHER THAN BY FIFTEEN WHOLE-RULE ANCHORS.
#
# Every rule this round OWNS is named below; every literal inside those
# rules is mapped once. An anchor per rule would have been fifteen exact
# quotations of CSS that must match byte for byte - and the first draft
# of this round already failed on one of them, because it quoted a
# two-line rule the page writes on one line. A map cannot make that
# mistake, and the gate afterwards proves the scope is clean.
SCOPE = [
    '.ref-id-display small', '.ref-id-display code',
    '.detail-grid dt', '.detail-grid dd', '.detail-grid dd code',
    '.detail-grid dd small', '.detail-audit',
    '.validation-details summary', '.validation-details summary:hover',
    '.validation-table code',
    '.row-error td', '.row-correction td',
    '.fix-input', '.fix-na',
    '.validation-group', '.validation-group-header',
    '.validation-group-header code', '.validation-group-count',
]

# Each literal, and the token that already means it. Distances are out of
# 765 and were measured, not eyeballed.
TOKENS = [
    # Exact - zero visible change, and `white` stops being a KEYWORD,
    # which standard 3.1 calls out by name: a keyword is invisible to a
    # hex-based audit, and that hid a defect for weeks.
    ('white', 'var(--alv-paper)'),          # #ffffff exactly
    ('#f1f3f5', 'var(--alv-line-soft)'),    # exact
    ('#f8f9fa', 'var(--alv-surface)'),      # exact
    ('#e9ecef', 'var(--alv-line)'),         # 15
    ('#dee2e6', 'var(--alv-line)'),         # 9
    ('#ced4da', 'var(--alv-line)'),         # 39, and a border is a line
    ('#6c757d', 'var(--alv-ink-soft)'),     # 42
    ('#495057', 'var(--alv-ink-strong)'),   # 16
    ('#2c3e50', 'var(--alv-ink)'),          # 41
    ('#adb5bd', 'var(--alv-ink-faint)'),    # 63, and it means faint
    # The two row tints, onto the tokens that already mean what the row
    # means. 27 and 24 - invisible, and now a tinted row and the pill
    # that means the same thing read from one place.
    ('#fff5f5', 'var(--alv-bad-soft)'),     # 27
    ('#fffbeb', 'var(--alv-warn-soft)'),    # 24
    # The validation summary hover was on the module alias. The alias
    # itself survives for X10, but this cluster stops reading it.
    ('var(--crs-dark)', 'var(--alv-accent)'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X9 - SUBMISSION DETAIL: SECTIONS, FORM, TABLES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs',
                    'submission_detail.html')
if not os.path.isfile(path):
    raise SystemExit('X9: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'action-secondary' not in text:
    raise SystemExit('X9: this page has not had X8. The colour round comes '
                     'first - X9 assumes the buttons, the badge and the '
                     'banners are already on house tones.')
if 'form-card' in text:
    print('  %-30s already on the house sections' % 'submission_detail')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for pat, rep, why, want in SWEEP:
    text, n = re.subn(pat, rep, text)
    if n != want:
        raise SystemExit('X9: %s replaced %d, expected %d' % (why, n, want))
    print('  %-30s %s  (x%d)' % ('submission_detail', why, n))

cells = 0
for was, label in CELLS:
    now = was.replace('<td>', '<td data-label="%s">' % label, 1) \
        if was.startswith('<td>') \
        else was.replace('<td ', '<td data-label="%s" ' % label, 1)
    n = text.count(was)
    if n != 1:
        raise SystemExit('X9: the %s cell (%s) is there %d time(s), not 1'
                         % (label, was[:44], n))
    text = text.replace(was, now, 1)
    cells += 1
if text.count(HOLDER[0]) != 1:
    raise SystemExit('X9: the Holder cell is there %d time(s), not 1'
                     % text.count(HOLDER[0]))
text = text.replace(HOLDER[0], HOLDER[1], 1)
cells += 1
print('  %-30s %d table cell(s) across FOUR tables gain a data-label, '
      'which is what base reads' % ('submission_detail', cells))

# Apply the map, but ONLY inside the rules this round owns.
touched = subs = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body = text[s:e]
    out, last = [], 0
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in SCOPE:
            continue
        decls = m.group(2)
        new_decls = decls
        for lit, tok in TOKENS:
            pat = (r'(?<![\w#-])' + re.escape(lit) + r'(?![\w-])'
                   if not lit.startswith('#')
                   else re.escape(lit) + r'(?![0-9a-fA-F])')
            new_decls, n = re.subn(pat, tok, new_decls)
            subs += n
        if new_decls != decls:
            touched += 1
            out.append(body[last:m.start(2)])
            out.append(new_decls)
            last = m.end(2)
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s %d literal(s) in %d owned rule(s) onto tokens'
      % ('submission_detail', subs, touched))

gone = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body, last, out = text[s:e], 0, []
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in DEAD:
            continue
        st = m.start() + (len(m.group(1)) - len(m.group(1).lstrip()))
        hd = body.rfind('\n', 0, st) + 1
        if body[hd:st].strip():
            hd = st
        en = m.end()
        while en < len(body) and body[en] in ' \t\r':
            en += 1
        if en < len(body) and body[en] == '\n':
            en += 1
        if hd < last:
            continue
        out.append(body[last:hd])
        last, gone = en, gone + 1
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s - %d rule(s) base already owns' % ('submission_detail', gone))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)


def has_class(name):
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


for cmt in re.findall(r'/\*.*?\*/', css, re.S):
    if '{' in cmt or '}' in cmt:
        raise SystemExit('X9: a CSS comment contains a brace, which breaks '
                         'the rule reader: %s' % ' '.join(cmt.split())[:80])
for d in set(DEAD):
    if d in names:
        raise SystemExit('X9: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X9: %s was removed - this round keeps it' % k)
for name in ('detail-section', 'detail-section-title', 'form-field',
             'form-field-full', 'req', 'field-help'):
    if has_class(name):
        raise SystemExit('X9: the class %r survives in the markup' % name)

if mk.count('form-card') != 8:
    raise SystemExit('X9: expected 8 .form-card sections, found %d'
                     % mk.count('form-card'))
if mk.count('<h3 class="form-section-title">') != 8:
    raise SystemExit('X9: the eight sections do not all have an h3 title')
if mk.count('class="form-group"') != 5:
    raise SystemExit('X9: expected 5 plain .form-group fields, found %d'
                     % mk.count('class="form-group"'))
if mk.count('form-group form-group-full') != 1:
    raise SystemExit('X9: the full-width field did not convert')
if mk.count('alv-req') != 5:
    raise SystemExit('X9: expected 5 required markers, found %d'
                     % mk.count('alv-req'))
if mk.count('class="form-text"') != 14:
    raise SystemExit('X9: expected 14 help lines on .form-text, found %d'
                     % mk.count('class="form-text"'))

# THE TABLE, AND THE PHONE FIX.
if mk.count('class="table alv-table validation-table"') != 4:
    raise SystemExit('X9: the four validation tables do not all wear '
                     '.alv-table')
# EVERY CELL IN EVERY TABLE, CHECKED AGAINST THE HEADER ABOVE IT.
labels = re.findall(r'<td[^>]*data-label="([^"]+)"', mk)
if len(labels) != 19:
    raise SystemExit('X9: expected 19 labelled cells across the four '
                     'tables, found %d' % len(labels))
for tb in re.finditer(r'<table class="table alv-table validation-table">'
                      r'(.*?)</table>', mk, re.S):
    seg = tb.group(1)
    ths = [' '.join(re.sub(r'<[^>]+>', '', x).split())
           for x in re.findall(r'<th>.*?</th>', seg, re.S)]
    tds = re.findall(r'<td[^>]*data-label="([^"]+)"', seg)
    if tds != ths:
        raise SystemExit('X9: a table labels its cells %r but its headers '
                         'say %r - a data-label that disagrees with its '
                         'column is worse than none, because the phone '
                         'card is the only place anyone reads it'
                         % (tds, ths))

# .form-actions IS KEPT, and this round is the one that must say so.
if '.form-actions' not in names:
    raise SystemExit('X9: .form-actions was deleted. X2, X4 and X7 removed '
                     'it from the ENTRY screens, where the house lifts the '
                     'primary into the top bar. This page is eight sections '
                     'and three separate forms - there is no single primary '
                     'to lift, so the row stays where the control it '
                     'submits is.')
fa = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1))
      == '.form-actions']
if re.search(r'#[0-9a-fA-F]{3,8}\b', ' '.join(fa)):
    raise SystemExit('X9: .form-actions is kept, but not with a hex')

# EVERY RULE THIS ROUND OWNS IS CLEAN - no hex, no keyword, no alias.
for sel in SCOPE:
    body = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]
    if not body:
        raise SystemExit('X9: %s is in this round SCOPE and has vanished'
                         % sel)
    b = body[0]
    bad = re.findall(r'#[0-9a-fA-F]{3,8}\b', b)
    if bad:
        raise SystemExit('X9: %s still carries %s' % (sel, bad))
    kw = re.findall(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|'
                    r'border(?:-\w+)?-colou?r)\s*:\s*'
                    r'(white|black|red|green|blue|grey|gray)\b', b, re.I)
    if kw:
        raise SystemExit('X9: %s still uses the colour KEYWORD %s - '
                         'standard 3.1 names keywords because a hex audit '
                         'cannot see them' % (sel, kw))
    if 'var(--crs-' in b:
        raise SystemExit('X9: %s still reads the module alias' % sel)

if '--crs-' not in nocmt(text):
    raise SystemExit('X9: the --crs-* alias has gone. X10 deletes it, when '
                     'the lifecycle, Excel and XML clusters stop reading '
                     'it - this round does not touch those.')
for keep in ('.lifecycle-event', '.excel-current, .xml-current',
             '.xml-modal-header'):
    if keep not in names:
        raise SystemExit('X9: %s was removed - it is X10' % keep)

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
