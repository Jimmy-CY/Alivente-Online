# -*- coding: utf-8 -*-
"""SECTION X, ROUND X4 - THE ADD / EDIT REPORTING FI SCREEN

Demetri: "All of the above need to apply for the Reporting Financial
Institutions." X3 did the list; this does the entry screen, and with it
Reporting FIs are house end to end.

IT IS X2 AGAIN, PLUS AN INLINE FORMSET
    The form shell is country_form's, rule for rule: the same green panel
    deleted rather than retoned, the same footer row holding Cancel AND
    Back replaced by a primary in the top bar, the same .form-section ->
    .form-card, .form-field -> .form-group, .req -> .alv-req,
    .field-help -> .form-text.

    What is new is the identification-numbers editor - twenty rules for a
    four-column grid of formset rows - and it carries three defects worth
    naming separately.

1. A COMPOUND RULE THAT DUPLICATES BASE
       .in-cell .form-control {
         padding: 7px 10px; border: 1px solid #ced4da;
         border-radius: 5px; font-size: 14px; width: 100%;
       }

   base's own .form-control already sets width, padding, border, radius
   and font-size - and sets them differently: a 2px --alv-line border,
   not a 1px #ced4da one. So every input inside the IN editor rendered
   unlike every other input in the system, and did so through a compound
   selector that beat base without saying why. This is one of the rules
   test_compound_rules.py is waiting on. It is DELETED, not retoned: the
   fix for a rule that duplicates base is to stop having it.

2. A DELETE BUTTON THAT IS NOT THE HOUSE DELETE BUTTON
   .btn-remove-in is a 32px #dc3545 square with a scale(1.1) hover. base
   owns .icon-action-btn .icon-delete, which is what every other delete
   control in the system wears. The rule goes; the button joins.

   `Add IN` was btn-outline-success - Bootstrap green, and the fourth
   green control this module hid in a bar. It becomes .action-secondary.

3. THREE HAND-NUMBERED nth-child LABELS, THE SAME DEFECT X1 FOUND
       .in-row .in-cell:nth-child(1)::before { content: 'Type'; }
       .in-row .in-cell:nth-child(2)::before { content: 'Value'; }
       .in-row .in-cell:nth-child(3)::before { content: 'Issued By'; }

   Insert a column and every label after it is wrong, silently. X1
   replaced exactly this pattern in a table by using data-label, which
   base reads. base has no component for a FORMSET row - it is a grid,
   not a table - so the rule stays here, but it becomes ONE rule reading
   attr(data-label) instead of three counting positions. Same lesson,
   applied where base cannot reach.

WHAT IS KEPT
    .in-list, .in-row, .in-row-header, .in-cell, .in-cell-actions,
    .in-add-row - base owns no formset component, so the layout stays
    under its own names, on tokens. Likewise .form-grid, .check-label and
    .field-error, for the reasons X2 recorded.

Backups: .bak_crsfiform. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsfiform'
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
            raise SystemExit('X4: %s is not a byte copy' % bak)


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
        raise SystemExit('X4: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# ONE-OFF MARKUP
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     '{{ title|upper }}</center></h2>',
     '<h2 class="page-title-h2">CRS REPORTING FINANCIAL INSTITUTIONS</h2>'
     '\r\n<h4 class="page-subtitle-h4">{{ title|upper }}</h4>',
     'the title, and the subtitle every house entry screen carries'),

    # THE STRUCTURAL MOVE, as X2 made it: the form opens above the bar so
    # the primary can be a submit, the panel goes, and Save joins Back.
    ('<!-- Action Buttons -->\r\n'
     '<div class="page-action-buttons">\r\n'
     '  <a href="{% url \'crs:fi_list\' %}" '
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
     '    {% if formset.non_form_errors %}\r\n'
     '    <div class="alert alert-danger">{{ formset.non_form_errors }}'
     '</div>\r\n'
     '    {% endif %}\r\n'
     '\r\n'
     '    <form method="post" novalidate>\r\n'
     '      {% csrf_token %}',

     '{% if form.non_field_errors %}\r\n'
     '<div class="alert alert-danger">{{ form.non_field_errors }}</div>\r\n'
     '{% endif %}\r\n'
     '{% if formset.non_form_errors %}\r\n'
     '<div class="alert alert-danger">{{ formset.non_form_errors }}</div>'
     '\r\n'
     '{% endif %}\r\n'
     '\r\n'
     '<form method="post" novalidate>\r\n'
     '  {% csrf_token %}\r\n'
     '\r\n'
     '  <!-- Action Buttons. The primary lives HERE, beside Back, which is\r\n'
     '       why the form has to open above it - it is a submit. The house\r\n'
     '       has no footer row on an entry screen, and this page used to\r\n'
     '       have one holding a second control to the same place. -->\r\n'
     '  <div class="page-action-buttons">\r\n'
     '    <button type="submit" class="btn action-primary">\r\n'
     '      <i class="fas fa-save"></i>'
     '{% if mode == "add" %} Create FI{% else %} Save Changes{% endif %}'
     '\r\n'
     '    </button>\r\n'
     '    <a href="{% url \'crs:fi_list\' %}" class="btn action-back" '
     'role="button" aria-label="Back to list">\r\n'
     '      <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back</span>\r\n'
     '    </a>\r\n'
     '  </div>',
     'the bar, the form open, and the panel'),

    ('      <!-- Submit Row -->\r\n'
     '      <div class="form-actions">\r\n'
     '        <a href="{% url \'crs:fi_list\' %}" '
     'class="btn btn-secondary">Cancel</a>\r\n'
     '        <button type="submit" class="btn btn-success">\r\n'
     '          <i class="fas fa-save"></i>\r\n'
     '          {% if mode == "add" %} Create FI'
     '{% else %} Save Changes{% endif %}\r\n'
     '        </button>\r\n'
     '      </div>\r\n'
     '    </form>\r\n'
     '\r\n'
     '  </div>\r\n'
     '</div>',
     '</form>',
     'the footer row and the two panel closes'),

    ('<button type="button" id="add-in-btn" '
     'class="btn btn-outline-success btn-sm">',
     '<button type="button" id="add-in-btn" class="btn action-secondary">',
     'Add IN'),
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
     'form-field-full -> form-group-full', 4),
    (r'<div class="form-field form-field-check">',
     '<div class="form-group form-group-check">',
     'the checkbox field', 1),
    (r'<div class="form-field">', '<div class="form-group">',
     'form-field -> form-group', 3),
    (r'<span class="req">\*</span>', '<span class="alv-req">*</span>',
     'req -> alv-req', 6),
    (r'<small class="field-help">', '<small class="form-text">',
     'field-help -> form-text', 7),

    # THE nth-child LABELS BECOME ONE ATTRIBUTE, which is X1's lesson
    # applied where base cannot reach: a formset row is a grid, not a
    # table, so base's td[data-label] rule does not cover it - but
    # counting positions is just as fragile here as it was there.
    (r'<div class="in-row in-row-header">\r\n'
     r'            <div class="in-cell">Type</div>\r\n'
     r'            <div class="in-cell">Value</div>\r\n'
     r'            <div class="in-cell">Issued By</div>',
     '<div class="in-row in-row-header">\r\n'
     '            <div class="in-cell">Type</div>\r\n'
     '            <div class="in-cell">Value</div>\r\n'
     '            <div class="in-cell">Issued By</div>',
     'the header row (unchanged, listed so the count is stated)', 1),
    (r'<div class="in-cell">\r\n              \{\{ in_form\.in_type \}\}',
     '<div class="in-cell" data-label="Type">\r\n'
     '              {{ in_form.in_type }}',
     'the Type cell gets its label', 1),
    (r'<div class="in-cell">\r\n              \{\{ in_form\.in_value \}\}',
     '<div class="in-cell" data-label="Value">\r\n'
     '              {{ in_form.in_value }}',
     'the Value cell', 1),
    (r'<div class="in-cell">\r\n              \{\{ in_form\.issued_by \}\}',
     '<div class="in-cell" data-label="Issued By">\r\n'
     '              {{ in_form.issued_by }}',
     'the Issued By cell', 1),
    (r'<div class="in-cell">\{\{ formset\.empty_form\.in_type \}\}</div>',
     '<div class="in-cell" data-label="Type">'
     '{{ formset.empty_form.in_type }}</div>',
     "the empty-form template's Type cell", 1),
    (r'<div class="in-cell">\{\{ formset\.empty_form\.in_value \}\}</div>',
     '<div class="in-cell" data-label="Value">'
     '{{ formset.empty_form.in_value }}</div>',
     "the template's Value cell", 1),
    (r'<div class="in-cell">\{\{ formset\.empty_form\.issued_by \}\}</div>',
     '<div class="in-cell" data-label="Issued By">'
     '{{ formset.empty_form.issued_by }}</div>',
     "the template's Issued By cell", 1),

    # TWICE, NOT ONCE. The remove button is written in the formset loop
    # AND in the <template> the Add IN script clones - and a one-shot
    # anchor refused rather than silently fixing half of them, which is
    # what an exact-count gate is for.
    # TWICE, NOT ONCE, AND WITH A BIN, NOT A CROSS.
    #
    # The first draft kept the page's own fa-times inside base's
    # .icon-delete, and test_row_personal.py failed: the house rule is
    # that .icon-delete draws fa-trash, on all 26 controls that wear it.
    # It is a real defect, not a pedantic one - the whole point of the
    # class is that a delete looks the same everywhere, and a cross
    # inside it would have made this the only one that did not.
    #
    # Removing an unsaved IN row IS a delete of that IN, so the class is
    # right and the icon was wrong. Both are fixed together.
    (r'<button type="button" class="btn-remove-in" '
     r'onclick="removeINRow\(this\)" title="Remove">\r\n'
     r'\s*<i class="fas fa-times"></i>',
     '<button type="button" class="icon-action-btn icon-delete" '
     'onclick="removeINRow(this)" title="Remove this IN">\r\n'
     '                <i class="fas fa-trash"></i>',
     "the IN remove button, in the row AND in the clone template", 2),
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
    '.form-field textarea.form-control',
    '.form-field .field-help',
    '.form-field .field-error',
    '.form-actions',
    '.form-actions .btn',
    # The compound rule that duplicated base, and the hand-rolled delete.
    '.in-cell .form-control',
    '.btn-remove-in',
    '.btn-remove-in:hover',
    # The three position-counted labels. Replaced by one attribute rule.
    '.in-row .in-cell:nth-child(1)::before',
    '.in-row .in-cell:nth-child(2)::before',
    '.in-row .in-cell:nth-child(3)::before',
]

# Kept. base owns no formset component.
KEPT = ['.form-section-note', '.form-grid', '.form-group-full',
        '.check-label', '.check-label .form-check-input', '.field-error',
        '.in-list', '.in-row', '.in-row-header', '.in-cell',
        '.in-cell-actions', '.in-add-row', '.in-cell::before']

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
    margin-bottom: 12px; line-height: 1.6;
  }""",
     """  .form-section-note {
    font-size: 12px; color: var(--alv-ink-soft);
    margin-bottom: 12px; line-height: 1.6;
  }""",
     'the section note'),

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
     that means the thing it means. */
  .field-error {
    font-size: 12px; color: var(--alv-bad); font-weight: 600;
  }""",
     'the field error'),

    ("""  .in-row-header {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.4px;
    color: #6c757d;
    padding-bottom: 4px;
    border-bottom: 1px solid #e9ecef;
    margin-bottom: 2px;
  }""",
     """  .in-row-header {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.4px;
    color: var(--alv-ink-soft);
    padding-bottom: 4px;
    border-bottom: 1px solid var(--alv-line);
    margin-bottom: 2px;
  }""",
     "the IN header row"),
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

    ("""    .in-row {
      grid-template-columns: 1fr;
      background: #f8f9fa; border: 1px solid #e9ecef;
      padding: 12px; border-radius: 6px; gap: 8px;
      position: relative;
    }
    .in-cell::before {
      font-weight: 700; font-size: 11px; text-transform: uppercase;
      color: #6c757d; letter-spacing: 0.4px;
      display: block; margin-bottom: 2px;
    }
    .in-row .in-cell:nth-child(1)::before { content: 'Type'; }
    .in-row .in-cell:nth-child(2)::before { content: 'Value'; }
    .in-row .in-cell:nth-child(3)::before { content: 'Issued By'; }""",
     """    .in-row {
      grid-template-columns: 1fr;
      background: var(--alv-surface); border: 1px solid var(--alv-line);
      padding: 12px; border-radius: var(--alv-radius-sm); gap: 8px;
      position: relative;
    }
    /* ONE RULE READING AN ATTRIBUTE, not three counting positions.
       X1 found the same defect in a table and fixed it with data-label,
       which base's .alv-table reads for free. base has no component for
       a FORMSET row - it is a grid, not a table - so the rule lives
       here; but inserting a column can no longer mislabel every column
       after it. */
    .in-cell::before {
      content: attr(data-label);
      font-weight: 700; font-size: 11px; text-transform: uppercase;
      color: var(--alv-ink-soft); letter-spacing: 0.4px;
      display: block; margin-bottom: 2px;
    }""",
     'the IN card layout, and the three counted labels become one'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X4 - ADD / EDIT REPORTING FI JOINS THE HOUSE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'fi_form.html')
if not os.path.isfile(path):
    raise SystemExit('X4: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'form-card' in text:
    print('  %-30s already on the house form' % 'fi_form')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('fi_form', why))

for pat, rep, why, want in SWEEP:
    text, n = re.subn(pat, rep, text)
    if n != want:
        raise SystemExit('X4: %s replaced %d, expected %d' % (why, n, want))
    print('  %-30s %s  (x%d)' % ('fi_form', why, n))

for was, now, why in RETONE + MEDIA:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('fi_form', why))

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
      % 'fi_form')

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
print('  %-30s - %d rule(s) base already owns' % ('fi_form', gone))

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
        raise SystemExit('X4: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X4: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X4: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X4: %d hex(es) left: %s' % (len(hexes), hexes))

for name in ('crs-panel', 'crs-panel-container', 'form-section',
             'form-field', 'form-field-full', 'form-actions', 'req',
             'field-help', 'btn-success', 'btn-secondary'):
    if has_class(name):
        raise SystemExit('X4: the class %r survives in the markup' % name)

# The heading standard.
for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X4: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X4: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))
if 'ALIVENTE ONLINE -' in mk:
    raise SystemExit('X4: the title still names the brand')
if mk.count('page-subtitle-h4') != 1:
    raise SystemExit('X4: the entry screen has no subtitle')

# THE BAR, AND THE ONE STRUCTURAL MOVE.
if mk.count('<form method="post" novalidate>') != 1:
    raise SystemExit('X4: there is not exactly one form')
if mk.index('<form method="post"') > mk.index('page-action-buttons'):
    raise SystemExit('X4: the bar is OUTSIDE the form, so its submit does '
                     'nothing - the form must open above it')
bar = mk[mk.index('<div class="page-action-buttons">'):]
bar = bar[:bar.index('</div>', bar.index('action-back'))]
if 'action-primary' not in bar or 'action-back' not in bar:
    raise SystemExit('X4: the bar does not hold both controls')
if bar.index('action-primary') > bar.index('action-back'):
    raise SystemExit('X4: Back is before the primary')
if 'type="submit"' not in bar:
    raise SystemExit('X4: the primary in the bar is not a submit')
if 'Cancel' in mk:
    raise SystemExit('X4: Cancel survives - Back already goes there, and '
                     'two controls to one place is the defect '
                     'test_save_and_cancel names')
if mk.count('form-card') != 4:
    raise SystemExit('X4: expected 4 .form-card sections, found %d'
                     % mk.count('form-card'))
if mk.count('<h3 class="form-section-title">') != 4:
    raise SystemExit('X4: the four sections do not all have an h3 title')
# Six on this form, five on country_form - the numbers are stated rather
# than shared, because a count that travels between rounds is a count
# that will be wrong in one of them.
if mk.count('alv-req') != 6:
    raise SystemExit('X4: expected 6 required markers, found %d'
                     % mk.count('alv-req'))
# THE IN EDITOR'S THREE DEFECTS, each gated.
if has_class('btn-remove-in') or '.btn-remove-in' in names:
    raise SystemExit('X4: the hand-rolled delete square survives')
if mk.count('icon-action-btn icon-delete') != 2:
    raise SystemExit('X4: the remove button must be the house delete in '
                     'BOTH the row and the clone template, and is in %d'
                     % mk.count('icon-action-btn icon-delete'))
if has_class('btn-outline-success'):
    raise SystemExit('X4: Add IN is still Bootstrap green')
if '.in-cell .form-control' in names:
    raise SystemExit('X4: the compound rule that duplicates base survives '
                     '- the fix for a rule that duplicates base is to stop '
                     'having it, not to retone it')
if [s for s in names if 'nth-child' in s and '::before' in s]:
    raise SystemExit('X4: a position-counted label survives')
labels = re.findall(r'<div class="in-cell" data-label="([^"]+)"', mk)
if labels != ['Type', 'Value', 'Issued By'] * 2:
    raise SystemExit('X4: the IN cells carry %r, not the three columns in '
                     'the row and again in the clone template' % labels)
before_rule = [m.group(2) for m in RULE.finditer(
    '\n'.join(STYLE.findall(text))) if bare(m.group(1)) == '.in-cell::before']
if not before_rule or 'attr(data-label)' not in before_rule[0]:
    raise SystemExit('X4: .in-cell::before does not read the attribute')

if len(text) >= len(before):
    raise SystemExit('X4: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
