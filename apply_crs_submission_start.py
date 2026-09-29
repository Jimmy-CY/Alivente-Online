# -*- coding: utf-8 -*-
"""SECTION X, ROUND X7 - THE START SUBMISSION SCREEN

Demetri: "all of the same need to apply to the Submissions." X6 did the
list; this is the second of the three, and it is the entry-screen shape
for the third time - X2 and X4 again, on a smaller form.

    the green panel                 deleted, because a house entry screen
                                    has none
    a footer holding Cancel AND     replaced by a primary in the top bar,
    Create Draft                    which means the form opens above it
    .form-section                   -> .form-card
    .form-section-title             the page OVERRODE base's own class
                                    with green; the override goes
    .form-field                     -> .form-group
    .req                            -> .alv-req
    .field-help                     -> .form-text
    the title                       loses <center> and the brand prefix,
                                    and gains the subtitle every house
                                    entry screen carries

WHAT IS THIS PAGE'S OWN
    .nil-checkbox-label input[type="checkbox"] - a Bootstrap
    .form-check-input pulled back into the flow so the row's own flex
    layout can place it. base does not own a checkbox row, so it stays.

    Three inline `style=` attributes sit on the nil-return row and its
    help text - flex layout and two 10px indents. They are NOT touched
    here. An inline style is a real deviation and it wants its own sweep
    across the system rather than a fix on the one page a CRS round
    happens to be looking at; there is no house rule to move them to yet.
    Written down, and left.

Backups: .bak_crsstart. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsstart'
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
            raise SystemExit('X7: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70 - country_form.html is CRLF."""
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
        raise SystemExit('X7: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# ONE-OFF MARKUP
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'START CRS SUBMISSION</center></h2>',
     '<h2 class="page-title-h2">CRS SUBMISSIONS</h2>\r\n'
     '<h4 class="page-subtitle-h4">START A SUBMISSION</h4>',
     'the title, and the subtitle every house entry screen carries'),

    ('<!-- Action Buttons -->\r\n'
     '<div class="page-action-buttons">\r\n'
     '  <a href="{% url \'crs:submission_list\' %}" '
     'class="btn btn-success action-back" role="button" '
     'aria-label="Back to list">\r\n'
     '    <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back</span>\r\n'
     '  </a>\r\n'
     '</div>\r\n'
     '\r\n'
     '<!-- Form Panel -->\r\n'
     '<div class="crs-panel-container">\r\n'
     '  <div class="crs-panel">\r\n'
     '\r\n'
     '    {% if form.non_field_errors %}\r\n'
     '    <div class="alert alert-danger">{{ form.non_field_errors }}</div>'
     '\r\n'
     '    {% endif %}\r\n'
     '\r\n'
     '    <form method="post" novalidate id="submissionStartForm">\r\n'
     '      {% csrf_token %}',

     '{% if form.non_field_errors %}\r\n'
     '<div class="alert alert-danger">{{ form.non_field_errors }}</div>\r\n'
     '{% endif %}\r\n'
     '\r\n'
     '<form method="post" novalidate id="submissionStartForm">\r\n'
     '  {% csrf_token %}\r\n'
     '\r\n'
     '  <!-- Action Buttons. The primary lives HERE, beside Back, which is\r\n'
     '       why the form has to open above it - it is a submit. The house\r\n'
     '       has no footer row on an entry screen, and this page used to\r\n'
     '       have one holding a second control to the same place. -->\r\n'
     '  <div class="page-action-buttons">\r\n'
     '    <button type="submit" class="btn action-primary" id="submitBtn">'
     '\r\n'
     '      <i class="fas fa-play"></i> Create Draft\r\n'
     '    </button>\r\n'
     '    <a href="{% url \'crs:submission_list\' %}" '
     'class="btn action-back" role="button" aria-label="Back to list">\r\n'
     '      <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back</span>\r\n'
     '    </a>\r\n'
     '  </div>',
     'the bar, the form open, and the panel'),

    ('      <!-- Submit Row -->\r\n'
     '      <div class="form-actions">\r\n'
     '        <a href="{% url \'crs:submission_list\' %}" '
     'class="btn btn-secondary">Cancel</a>\r\n'
     '        <button type="submit" class="btn btn-success" id="submitBtn">'
     '\r\n'
     '          <i class="fas fa-play"></i> Create Draft\r\n'
     '        </button>\r\n'
     '      </div>\r\n'
     '    </form>\r\n'
     '\r\n'
     '  </div>\r\n'
     '</div>',
     '</form>',
     'the footer row and the two panel closes'),
]

# REPEATED MARKUP. Counted, not guessed - a gate below insists on the
# exact number each one replaced.
SWEEP = [
    (r'<div class="form-section">', '<div class="form-card">',
     'form-section -> form-card', 1),
    (r'<div class="form-section-title">([^<]*)</div>',
     r'<h3 class="form-section-title">\1</h3>',
     'the section title becomes an h3, as the house writes it', 1),
    (r'<div class="form-field form-field-full">',
     '<div class="form-group form-group-full">',
     'form-field-full -> form-group-full', 3),
    (r'<div class="form-field">', '<div class="form-group">',
     'form-field -> form-group', 2),
    (r'<span class="req">\*</span>', '<span class="alv-req">*</span>',
     'req -> alv-req', 4),
    (r'class="field-help"', 'class="form-text"',
     'field-help -> form-text', 3),
]

# CSS that stops having a wearer, or that base already owns.
DEAD = [
    ':root',
    '.page-title-h2',
    '.page-action-buttons',
    '.page-action-buttons .action-back',
    '.action-back-label',
    '.crs-panel-container',
    '.crs-panel',
    '.form-section',
    '.form-section-title',
    '.form-field',
    '.form-field label',
    '.form-field .req',
    '.form-field .form-control',
    '.form-field .form-control:disabled',
    '.form-field .field-help',
    '.form-field .field-error',
    '.form-actions',
    '.form-actions .btn',
]

# Kept. base owns none of these.
KEPT = ['.form-section-note', '.form-grid', '.form-group-full',
        '.field-error', '.nil-checkbox-label input[type="checkbox"]']

RETONE = [
    ("""  .form-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px;
  }
  .form-field { display: flex; flex-direction: column; gap: 4px; }
  .form-field-full { grid-column: 1 / -1; }""",
     """  /* Two columns, one on a phone - a house convention twelve form pages
     already share, with finance_expense_add's gap. */
  .form-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 18px 22px;
  }
  .form-group-full { grid-column: 1 / -1; }""",
     'the grid'),

    ("""  .form-section-note {
    font-size: 12px; color: #6c757d;
    margin-bottom: 14px; line-height: 1.6;
  }""",
     """  .form-section-note {
    font-size: 12px; color: var(--alv-ink-soft);
    margin-bottom: 14px; line-height: 1.6;
  }""",
     'the section note'),

    ("""  .form-field .field-error {
    font-size: 12px; color: #dc3545; font-weight: 600;
  }""",
     """  /* base has no field-error component, so this stays - on the token
     that means the thing it means. */
  .field-error {
    font-size: 12px; color: var(--alv-bad); font-weight: 600;
  }""",
     'the field error'),
]

MEDIA = [
    ("""    .crs-panel { padding: 16px; }
    .form-section { padding: 14px; }
    .form-grid { grid-template-columns: 1fr; }
    .form-actions { flex-direction: column-reverse; gap: 8px; }
    .form-actions .btn { width: 100%; }
    .form-field .form-control { font-size: 16px !important; }""",
     """    .form-grid { grid-template-columns: 1fr; gap: 14px; }""",
     "the phone block - only the grid collapse is still this page's job"),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X7 - START SUBMISSION JOINS THE HOUSE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'submission_start.html')
if not os.path.isfile(path):
    raise SystemExit('X7: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'form-card' in text:
    print('  %-30s already on the house form' % 'submission_start')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('submission_start', why))

for pat, rep, why, want in SWEEP:
    text, n = re.subn(pat, rep, text)
    if n != want:
        raise SystemExit('X7: %s replaced %d, expected %d' % (why, n, want))
    print('  %-30s %s  (x%d)' % ('submission_start', why, n))

for was, now, why in RETONE + MEDIA:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('submission_start', why))

# THE FORM BODY WAS INDENTED TO SIT INSIDE A PANEL THAT NO LONGER EXISTS.
# Six spaces where the bar beside it has two. It changes nothing a browser
# sees - and leaving it would hand the next reader a block that looks like
# it is still nested in something. Dedent by four, between the bar and the
# close of the form, and only lines that actually have four to give.
i = text.index('  </div>', text.index('page-action-buttons')) + len('  </div>')
j = text.index('</form>')
mid = text[i:j]
dedented = ''.join(
    (ln[4:] if ln.startswith('      ') else ln) + '\n'
    for ln in mid.replace('\r\n', '\n').split('\n'))[:-1]
if CRLF.get(path):
    dedented = dedented.replace('\n', '\r\n')
text = text[:i] + dedented + text[j:]
print('  %-30s the form body dedented out of the panel it no longer sits in'
      % 'submission_start')

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
print('  %-30s - %d rule(s) base already owns' % ('submission_start', gone))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
# COMMENTS COME OUT BEFORE ANY GATE READS THE MARKUP, and this round is
# the third time in one session that rule has had to be learnt somewhere
# new. Lesson 21 says strip CSS comments before comparing a SELECTOR; X1
# found its hex gate firing on a CSS comment that NAMED a retired token;
# and here the `Cancel` gate fired on the HTML comment this very round
# writes, which explains why Cancel was removed. A gate that reads the
# round's own prose is measuring the documentation, not the page.
#
# So: the general form. Scripts, styles AND comments come out, and every
# check below runs on what the browser would actually render.
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)


def has_class(name):
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


for d in DEAD:
    if d in names:
        raise SystemExit('X7: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X7: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X7: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X7: %d hex(es) left: %s' % (len(hexes), hexes))

for name in ('crs-panel', 'crs-panel-container', 'form-section',
             'form-field', 'form-field-full', 'form-actions',
             'field-help', 'btn-success', 'btn-secondary'):
    if has_class(name):
        raise SystemExit('X7: the class %r survives in the markup' % name)

# The heading standard.
for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X7: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X7: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))
if 'ALIVENTE ONLINE -' in mk:
    raise SystemExit('X7: the title still names the brand')
if mk.count('page-subtitle-h4') != 1:
    raise SystemExit('X7: the entry screen has no subtitle')

# THE BAR, AND THE ONE STRUCTURAL MOVE.
if mk.count('<form method="post" novalidate') != 1:
    raise SystemExit('X7: there is not exactly one form')
if mk.index('<form method="post"') > mk.index('page-action-buttons'):
    raise SystemExit('X7: the bar is OUTSIDE the form, so its submit does '
                     'nothing - the form must open above it')
bar = mk[mk.index('<div class="page-action-buttons">'):]
bar = bar[:bar.index('</div>', bar.index('action-back'))]
if 'action-primary' not in bar or 'action-back' not in bar:
    raise SystemExit('X7: the bar does not hold both controls')
if bar.index('action-primary') > bar.index('action-back'):
    raise SystemExit('X7: Back is before the primary')
if 'type="submit"' not in bar:
    raise SystemExit('X7: the primary in the bar is not a submit')
if 'Cancel' in mk:
    raise SystemExit('X7: Cancel survives - Back already goes there, and '
                     'two controls to one place is the defect '
                     'test_save_and_cancel names')
if mk.count('form-card') != 1:
    raise SystemExit('X7: expected 1 .form-card section, found %d'
                     % mk.count('form-card'))
if mk.count('<h3 class="form-section-title">') != 1:
    raise SystemExit('X7: the section has no h3 title')
# Four on this form. Each round states its own count rather than
# inheriting one, because a count that travels between rounds is a count
# that will be wrong in one of them.
if mk.count('alv-req') != 4:
    raise SystemExit('X7: expected 4 required markers, found %d'
                     % mk.count('alv-req'))
if len(text) >= len(before):
    raise SystemExit('X7: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))

if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
