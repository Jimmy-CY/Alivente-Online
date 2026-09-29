# -*- coding: utf-8 -*-
"""SECTION X, ROUND X2 - THE ADD / EDIT COUNTRY SCREEN JOINS THE HOUSE

Reported by Demetri: "The Add / Edit Country should comply to our
standards. No Green border, Create button should be teal."

X1 did the list and its view modal. X2 does the third thing he named, on
the same screen family, and after it Country Configurations is finished
end to end.

THE GREEN BORDER, AGAIN, AND THE SAME ANSWER
    .crs-panel wrapped the whole form in a 3px green border and a tinted
    fill, out of the same --crs-dark / --crs-light pair every CRS page
    declares. It is deleted rather than retoned, for the reason X1
    measured: a house entry screen has no outer panel. It has
    .form-card sections on the page background, which is what
    finance_expense_types_add and forty-four other pages already do.

THE CREATE BUTTON IS NOT MOVED TO TEAL. IT IS MOVED, FULL STOP.
    Demetri asked for it to be teal. It becomes teal - but the house
    change is larger than the colour, and doing only the colour would
    have left the screen still failing two suites.

    Measured on the house: an entry screen puts its primary in
    .page-action-buttons AT THE TOP, beside Back, and has no footer row
    at all. This page had Back alone at the top and a footer holding
    `Cancel` and `Create Country` - so it offered TWO ways back to the
    list, one of them labelled Cancel, which is exactly what
    test_save_and_cancel.py names as a defect. The footer goes; Save
    joins Back in the bar; Cancel disappears because Back already is it.

    That means the <form> has to OPEN ABOVE THE BAR, because the primary
    is a submit. It is the one structural move in this round.

WHAT ELSE STOPS BEING HAND-ROLLED
    .form-section      -> .form-card              base owns it
    .form-section-title  the page OVERRODE base's own class with green;
                         the override goes and base's rule applies
    .form-field        -> .form-group             base owns it
    .req               -> .alv-req                base owns it
    .field-help        -> .form-text              base owns it
    div.form-section-title -> h3, as the house writes it

    The title loses <center> and the brand prefix, and gains the
    .page-subtitle-h4 that every house entry screen carries - so the page
    says what it is and then what you are doing to it.

WHAT IS KEPT, AND WHY IT IS NOT A DEVIATION
    .form-grid - two columns, collapsing to one under 768px. base does
    not own it, but ELEVEN house form pages already do exactly this
    (eight as .form-grid, three as .form-row-2), so it is a house
    convention that has not been hoisted yet rather than something CRS
    invented. Kept, with its gap brought onto the spelling
    finance_expense_add uses.

    .field-error and .check-label likewise have no base equivalent. Kept,
    retoned onto tokens.

NOT DONE HERE
    The message block, for the same reason as X1: it is system-wide and
    has a settings.py precondition.

Backups: .bak_crsform. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsform'
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
            raise SystemExit('X2: %s is not a byte copy' % bak)


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
        raise SystemExit('X2: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# ONE-OFF MARKUP
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     '{{ title|upper }}</center></h2>',
     '<h2 class="page-title-h2">CRS COUNTRY CONFIGURATIONS</h2>\r\n'
     '<h4 class="page-subtitle-h4">{{ title|upper }}</h4>',
     'the title, and the subtitle every house entry screen carries'),

    # THE STRUCTURAL MOVE. The form opens above the bar so the primary can
    # be a submit, the panel goes, and Save joins Back.
    ('<!-- Action Buttons -->\r\n'
     '<div class="page-action-buttons">\r\n'
     '  <a href="{% url \'crs:country_list\' %}" '
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
     '    <form method="post" novalidate>\r\n'
     '      {% csrf_token %}',

     '{% if form.non_field_errors %}\r\n'
     '<div class="alert alert-danger">{{ form.non_field_errors }}</div>\r\n'
     '{% endif %}\r\n'
     '\r\n'
     '<form method="post" novalidate>\r\n'
     '  {% csrf_token %}\r\n'
     '\r\n'
     '  <!-- Action Buttons. The primary lives HERE, beside Back, which is\r\n'
     '       why the form has to open above it - it is a submit. The house\r\n'
     '       has no footer row on an entry screen, and this page used to\r\n'
     '       have one holding Cancel as well as Back: two controls going to\r\n'
     '       the same place. -->\r\n'
     '  <div class="page-action-buttons">\r\n'
     '    <button type="submit" class="btn action-primary">\r\n'
     '      <i class="fas fa-save"></i>'
     '{% if mode == "add" %} Create Country{% else %} Save Changes{% endif %}'
     '\r\n'
     '    </button>\r\n'
     '    <a href="{% url \'crs:country_list\' %}" class="btn action-back" '
     'role="button" aria-label="Back to list">\r\n'
     '      <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back</span>\r\n'
     '    </a>\r\n'
     '  </div>',
     'the bar, the form open, and the panel'),

    # THE FOOTER GOES, and with it the two closing panel divs.
    ('      <!-- Submit Row -->\r\n'
     '      <div class="form-actions">\r\n'
     '        <a href="{% url \'crs:country_list\' %}" '
     'class="btn btn-secondary">Cancel</a>\r\n'
     '        <button type="submit" class="btn btn-success">\r\n'
     '          <i class="fas fa-save"></i>\r\n'
     '          {% if mode == "add" %} Create Country'
     '{% else %} Save Changes{% endif %}\r\n'
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
     'form-section -> form-card', 4),
    (r'<div class="form-section-title">([^<]*)</div>',
     r'<h3 class="form-section-title">\1</h3>',
     'the section titles become h3, as the house writes them', 4),
    (r'<div class="form-field form-field-full">',
     '<div class="form-group form-group-full">',
     'form-field-full -> form-group-full', 6),
    (r'<div class="form-field form-field-check">',
     '<div class="form-group form-group-check">',
     'the checkbox field', 1),
    (r'<div class="form-field">', '<div class="form-group">',
     'form-field -> form-group', 4),
    (r'<span class="req">\*</span>', '<span class="alv-req">*</span>',
     'req -> alv-req', 5),
    (r'<small class="field-help">', '<small class="form-text">',
     'field-help -> form-text', 6),
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
    '.form-section:last-of-type',
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
KEPT = ['.form-section-note', '.form-section-note code', '.form-grid',
        '.form-group-full', '.check-label', '.check-label .form-check-input',
        '.field-error']

RETONE = [
    # The grid's own rule loses nothing but its neighbour's name; the gap
    # comes onto the spelling finance_expense_add uses, so two pages that
    # do the same thing say it the same way.
    ("""  .form-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px;
  }
  .form-field { display: flex; flex-direction: column; gap: 4px; }
  .form-field-full { grid-column: 1 / -1; }""",
     """  /* Two columns, one on a phone. base does not own this, but eleven
     house form pages already do exactly it - eight as .form-grid and
     three as .form-row-2 - so it is a convention waiting to be hoisted,
     not something CRS invented. The gap is finance_expense_add's. */
  .form-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 18px 22px;
  }
  .form-group-full { grid-column: 1 / -1; }""",
     'the grid'),

    ("""  .form-section-note {
    font-size: 12px; color: #6c757d;
    margin-bottom: 12px; line-height: 1.6;
  }
  .form-section-note code {
    background: #f1f3f5; color: #c7254e;
    padding: 1px 5px; border-radius: 3px; font-size: 11px;
  }""",
     """  .form-section-note {
    font-size: 12px; color: var(--alv-ink-soft);
    margin-bottom: 12px; line-height: 1.6;
  }
  /* The token chips. #c7254e was Bootstrap 3's inline-code colour, carried
     in by copy and meaning nothing here; --alv-ink for the same reason it
     was chosen in X1 - accent means primary action and selection, and a
     template token is neither. */
  .form-section-note code {
    background: var(--alv-line-soft); color: var(--alv-ink);
    padding: 1px 5px; border-radius: 3px; font-size: 11px;
  }""",
     'the note and its token chips'),

    ("""  .check-label {
    display: flex; align-items: center; gap: 8px;
    font-size: 14px; font-weight: 600; color: #495057;
    cursor: pointer; margin: 0;
  }""",
     """  .check-label {
    display: flex; align-items: center; gap: 8px;
    font-size: 14px; font-weight: 600; color: var(--alv-ink-strong);
    cursor: pointer; margin: 0;
  }""",
     'the checkbox label'),

    ("""  .form-field .field-error {
    font-size: 12px; color: #dc3545; font-weight: 600;
  }""",
     """  /* base has no field-error component, so this stays - on the token
     that means the thing it means. #dc3545 was Bootstrap's danger. */
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
     'the phone block - only the grid collapse is still this page\'s job'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X2 - ADD / EDIT COUNTRY JOINS THE HOUSE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'country_form.html')
if not os.path.isfile(path):
    raise SystemExit('X2: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'form-card' in text:
    print('  %-30s already on the house form' % 'country_form')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('country_form', why))

for pat, rep, why, want in SWEEP:
    text, n = re.subn(pat, rep, text)
    if n != want:
        raise SystemExit('X2: %s replaced %d, expected %d' % (why, n, want))
    print('  %-30s %s  (x%d)' % ('country_form', why, n))

for was, now, why in RETONE + MEDIA:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('country_form', why))

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
      % 'country_form')

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
print('  %-30s - %d rule(s) base already owns' % ('country_form', gone))

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
        raise SystemExit('X2: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X2: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X2: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X2: %d hex(es) left: %s' % (len(hexes), hexes))

for name in ('crs-panel', 'crs-panel-container', 'form-section',
             'form-field', 'form-field-full', 'form-actions', 'req',
             'field-help', 'btn-success', 'btn-secondary'):
    if has_class(name):
        raise SystemExit('X2: the class %r survives in the markup' % name)

# The heading standard.
for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X2: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X2: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))
if 'ALIVENTE ONLINE -' in mk:
    raise SystemExit('X2: the title still names the brand')
if mk.count('page-subtitle-h4') != 1:
    raise SystemExit('X2: the entry screen has no subtitle')

# THE BAR, AND THE ONE STRUCTURAL MOVE.
if mk.count('<form method="post" novalidate>') != 1:
    raise SystemExit('X2: there is not exactly one form')
if mk.index('<form method="post"') > mk.index('page-action-buttons'):
    raise SystemExit('X2: the bar is OUTSIDE the form, so its submit does '
                     'nothing - the form must open above it')
bar = mk[mk.index('<div class="page-action-buttons">'):]
bar = bar[:bar.index('</div>', bar.index('action-back'))]
if 'action-primary' not in bar or 'action-back' not in bar:
    raise SystemExit('X2: the bar does not hold both controls')
if bar.index('action-primary') > bar.index('action-back'):
    raise SystemExit('X2: Back is before the primary')
if 'type="submit"' not in bar:
    raise SystemExit('X2: the primary in the bar is not a submit')
if 'Cancel' in mk:
    raise SystemExit('X2: Cancel survives - Back already goes there, and '
                     'two controls to one place is the defect '
                     'test_save_and_cancel names')
if mk.count('form-card') != 4:
    raise SystemExit('X2: expected 4 .form-card sections, found %d'
                     % mk.count('form-card'))
if mk.count('<h3 class="form-section-title">') != 4:
    raise SystemExit('X2: the four sections do not all have an h3 title')
# FIVE, NOT SIX. The first draft of this round said six, and the counted
# sweep refused rather than doing five and calling it done. Five fields on
# this form are required: country code, country name, OECD version,
# default currency, receiving country strategy.
if mk.count('alv-req') != 5:
    raise SystemExit('X2: expected 5 required markers, found %d'
                     % mk.count('alv-req'))
if len(text) >= len(before):
    raise SystemExit('X2: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
print('  %-30s %s' % ('', 'Country Configurations is now house end to end; '
                      '6 CRS pages remain'))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
