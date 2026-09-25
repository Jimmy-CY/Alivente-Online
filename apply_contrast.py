# -*- coding: utf-8 -*-
"""apply_contrast.py - Section D, round D10: fifteen rules put white text
on a colour too light to carry it.

    python apply_contrast.py --check     dry run, nothing written
    python apply_contrast.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 25 Sep, from claude/property_side_audit_25_sep.md.

NOT ON ANY PLAN. Every property-side item that was written down is closed
- D6 the modal headers, D7 the Back label, D8 the summary cards, D9 the
avatar - so the question was asked the other way round: not "what is left
on the list", but "what does the list not know about".

Swept every non-Personal template for a rule setting white text on a
colour, and computed the contrast against the WORST stop of its paint:

    edit_asset            .btn-photo-star-active   #f39c12   2.19
    customer_invoice_form .btn-unapprove           #fd7e14   2.57
    physical_invoice_edit .btn-unapprove           #fd7e14   2.57
    project_task_list     .priority-high           #fd7e14   2.57
    projects_detail       .priority-high           #fd7e14   2.57
    customer_invoice_form .btn-unapprove:hover     #e8690b   3.25
    physical_invoice_edit .btn-unapprove:hover     #e8690b   3.25
    comments_report       .btn-print               #28a745   3.13   (dead)
    customer_invoice_form .btn-approve             #28a745   3.13
    physical_invoice_edit .btn-approve             #28a745   3.13
    finance_revenue_types_add  .quickset-btn:hover #28a745   3.13
    finance_revenue_types_edit .quickset-btn:hover #28a745   3.13
    property_detail       .badge-success           #28a745   3.13
    property_detail       .badge-available         #28a745   3.13
    user_permissions      .permission-item.granted #28a745   3.13
    customer_invoice_form .btn-send                #007bff   3.98

Small text needs 4.5:1. Five of these fail 3.0, the bar for LARGE text,
which means they fail for any text at all.

THE FIX IS NOT A NEW COLOUR. Every literal above already MEANS something -
Bootstrap's green is "good", its orange is "needs attention", its blue is
"the primary action" - and base already carries those meanings at a
readable contrast. The round replaces each literal with the token that
already says what it says:

    #28a745 -> var(--alv-good)      5.12
    #fd7e14 -> var(--alv-warn)      4.73
    #007bff -> var(--alv-accent)    4.91
    #f39c12 -> var(--alv-accent)    4.91   [decided: see below]

Two were judgement calls and were decided rather than assumed:

  .btn-photo-star-active marks the COVER photo - the star is filled and
  the button disabled, while every other says "Set as cover photo". That
  is a SELECTION, not a warning, and the house paints selection with the
  accent everywhere else.

  .quickset-btn:hover fills green on hover from a white resting state.
  Green for a hover means nothing; it fills with the accent, like every
  other secondary control in the house.

I NEARLY DELETED A LIVE RULE. `.priority-high` on the two project pages
appears in no class attribute and in no script, so a first pass called it
an orphan and listed it for deletion. It is built by the TEMPLATE:

    <span class="priority-badge priority-{{ item.priority|lower }}">

The scan had looked in <script> blocks and in literal class attributes,
and Django's own interpolation is neither. It is lesson 19 exactly - a
scanner's blind spot becoming a decision - and it would have taken the
paint off every High badge in Projects.

So this round DELETES NOTHING. Two rules do look dead - comments_report's
.btn-print, and #prorataPreviewModal .modal-header on the two expense
pages, which base has overridden with !important since D6 - and they are
reported for the orphan round, where the scanner that understands
interpolation already lives. A contrast round should not also be a
deletion round; that is how the near-miss above happened.

SCOPE, as agreed: each FAILING rule is tokenised completely - background,
border and its :hover partner - so no rule is left half-literal. The 149
Bootstrap literals in these eight files are otherwise untouched; they
belong to a literal sweep across the whole application, which is a round
of its own after the Personal side.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_contrast'
SUITE = 'test_contrast.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'

CRLF = {}
planned = {}
report = []
problems = []
swept = []


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


# A hover is a token mixed toward black, which is what base already does
# for .alv-modal-head--danger. There is no --alv-good-ink or
# --alv-warn-ink, and this round is not the place to invent tokens.
def darker(tok, pct=78):
    return 'color-mix(in srgb, var(%s) %d%%, #000)' % (tok, pct)


# (file, old, new, what it is, before, after)
EDITS = [
 ('edit_asset.html',
  '.btn-photo-star-active {\n    background: #f39c12;\n    color: white;',
  '.btn-photo-star-active {\n    /* The COVER photo - a selection, not a '
  'warning. #f39c12 carried\n       white at 2.19, below the 3.0 that even '
  'large text needs. [D10] */\n    background: var(--alv-accent);\n'
  '    color: var(--alv-on-accent);',
  'the cover-photo star', 2.19, 4.91),

 ('customer_invoice_form.html',
  '.btn-approve { background-color: #28a745; color: white; border: 1px solid'
  ' #28a745;',
  '.btn-approve { background-color: var(--alv-good); color: '
  'var(--alv-on-accent); border: 1px solid var(--alv-good);',
  'Approve', 3.13, 5.12),
 ('customer_invoice_form.html',
  '.btn-approve:hover { background-color: #218838; border-color: #1e7e34;'
  ' color: white;',
  '.btn-approve:hover { background-color: %s; border-color: %s; color: '
  'var(--alv-on-accent);' % (darker('--alv-good'), darker('--alv-good', 70)),
  '  its hover', 3.60, 6.55),
 ('customer_invoice_form.html',
  '.btn-unapprove { background-color: #fd7e14; color: white; border: 1px '
  'solid #fd7e14;',
  '.btn-unapprove { background-color: var(--alv-warn); color: '
  'var(--alv-on-accent); border: 1px solid var(--alv-warn);',
  'Unapprove', 2.57, 4.73),
 ('customer_invoice_form.html',
  '.btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a;'
  ' color: white;',
  '.btn-unapprove:hover { background-color: %s; border-color: %s; color: '
  'var(--alv-on-accent);' % (darker('--alv-warn'), darker('--alv-warn', 70)),
  '  its hover', 3.25, 6.55),
 ('customer_invoice_form.html',
  '.btn-send { background-color: #007bff; color: white; border: 1px solid'
  ' #007bff;',
  '.btn-send { background-color: var(--alv-accent); color: '
  'var(--alv-on-accent); border: 1px solid var(--alv-accent);',
  'Send', 3.98, 4.91),
 ('customer_invoice_form.html',
  '.btn-send:hover { background-color: #0069d9; border-color: #0062cc;'
  ' color: white;',
  '.btn-send:hover { background-color: var(--alv-accent-ink); border-color: '
  'var(--alv-accent-ink); color: var(--alv-on-accent);',
  '  its hover', 4.68, 7.44),

 ('physical_invoice_edit.html',
  '.btn-approve { background-color: #28a745; color: white; border: 1px solid'
  ' #28a745;',
  '.btn-approve { background-color: var(--alv-good); color: '
  'var(--alv-on-accent); border: 1px solid var(--alv-good);',
  'Approve', 3.13, 5.12),
 ('physical_invoice_edit.html',
  '.btn-approve:hover { background-color: #218838; border-color: #1e7e34;'
  ' color: white;',
  '.btn-approve:hover { background-color: %s; border-color: %s; color: '
  'var(--alv-on-accent);' % (darker('--alv-good'), darker('--alv-good', 70)),
  '  its hover', 3.60, 6.55),
 ('physical_invoice_edit.html',
  '.btn-unapprove { background-color: #fd7e14; color: white; border: 1px '
  'solid #fd7e14;',
  '.btn-unapprove { background-color: var(--alv-warn); color: '
  'var(--alv-on-accent); border: 1px solid var(--alv-warn);',
  'Unapprove', 2.57, 4.73),
 ('physical_invoice_edit.html',
  '.btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a;'
  ' color: white;',
  '.btn-unapprove:hover { background-color: %s; border-color: %s; color: '
  'var(--alv-on-accent);' % (darker('--alv-warn'), darker('--alv-warn', 70)),
  '  its hover', 3.25, 6.55),

 ('property_detail.html',
  '.badge-success { background-color: #28a745; color: white; }',
  '.badge-success { background-color: var(--alv-good); color: '
  'var(--alv-on-accent); }',
  'the success badge', 3.13, 5.12),
 ('property_detail.html',
  '.badge-available { background-color: #28a745; color: white; }',
  '.badge-available { background-color: var(--alv-good); color: '
  'var(--alv-on-accent); }',
  'the available badge', 3.13, 5.12),

 ('user_permissions.html',
  '.permission-item.granted .permission-icon {\n    background: #28a745;\n'
  '    color: white;',
  '.permission-item.granted .permission-icon {\n'
  '    background: var(--alv-good);\n    color: var(--alv-on-accent);',
  'a granted permission', 3.13, 5.12),
 ('user_permissions.html',
  '.permission-item.granted {\n    border-color: #28a745;',
  '.permission-item.granted {\n    border-color: var(--alv-good);',
  '  and its border, the same colour on the same component', 0, 0),

 ('finance_revenue_types_add.html',
  '.quickset-btn:hover {\n    background: #28a745;\n    color: white;\n'
  '    border-color: #28a745;',
  '.quickset-btn:hover {\n    /* A hover, not a state. Green meant nothing '
  'here and carried\n       white at 3.13. [D10] */\n'
  '    background: var(--alv-accent);\n    color: var(--alv-on-accent);\n'
  '    border-color: var(--alv-accent);',
  'the quickset hover', 3.13, 4.91),
 ('finance_revenue_types_edit.html',
  '.quickset-btn:hover {\n    background: #28a745;\n    color: white;\n'
  '    border-color: #28a745;',
  '.quickset-btn:hover {\n    /* A hover, not a state. Green meant nothing '
  'here and carried\n       white at 3.13. [D10] */\n'
  '    background: var(--alv-accent);\n    color: var(--alv-on-accent);\n'
  '    border-color: var(--alv-accent);',
  'the quickset hover', 3.13, 4.91),

 # THE TWO THAT WERE NEARLY DELETED. Built by the template, not written in
 # a class attribute: <span class="priority-badge priority-{{ ...|lower }}">
 ('projects/project_task_list.html',
  '.priority-high { background: #fd7e14; color: white; }',
  '.priority-high { background: var(--alv-warn); color: '
  'var(--alv-on-accent); }',
  'High priority (built by the template)', 2.57, 4.73),
 ('projects/projects_detail.html',
  '.priority-high { background: #fd7e14; color: white; }',
  '.priority-high { background: var(--alv-warn); color: '
  'var(--alv-on-accent); }',
  'High priority (built by the template)', 2.57, 4.73),
]

# Reported to the orphan round, NOT deleted here.
SUSPECT_DEAD = [
    ('comments_report.html', '.btn-print',
     'no class attribute, no script, no template interpolation'),
    ('finance_expense_add.html', '#prorataPreviewModal .modal-header',
     'the markup wears .alv-modal-head, whose paint is !important - '
     'overridden since D6'),
    ('finance_expense_edit.html', '#prorataPreviewModal .modal-header',
     'the markup wears .alv-modal-head, whose paint is !important - '
     'overridden since D6'),
]

# ==========================================================================
# WORK
# ==========================================================================
by_file = {}
for rel, old, new, what, before, after in EDITS:
    by_file.setdefault(rel, []).append((old, new, what, before, after))

for rel, items in sorted(by_file.items()):
    path = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.isfile(path):
        problems.append('%s not found' % rel)
        continue
    src = read(path)
    cur, n, done = src, 0, 0
    for old, new, what, before, after in items:
        if new in cur:
            done += 1
            continue
        if old not in cur:
            problems.append('%s: anchor not found for %s' % (rel, what.strip()))
            continue
        if cur.count(old) != 1:
            problems.append('%s: the anchor for %s matched %d time(s)'
                            % (rel, what.strip(), cur.count(old)))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
        if before:
            swept.append((rel, what, before, after))
    if n:
        planned[path] = (src, cur)
        report.append('%-38s %d rule(s) take the token that already means '
                      'what they mean' % (rel, n))
    elif done == len(items):
        report.append('%-38s already done' % rel)

# --- self-checks --------------------------------------------------------
for path, (src, cur) in list(planned.items()):
    name = os.path.basename(path)
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if re.sub(r'<style[^>]*>.*?</style>', '', cur, flags=re.S | re.I) \
            != re.sub(r'<style[^>]*>.*?</style>', '', src, flags=re.S | re.I):
        problems.append('%s: the markup moved - this round changes CSS only'
                        % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    # NOTHING IS DELETED. A rule count that drops means a rule went with an
    # edit, which is how the near-miss on .priority-high would have looked.
    if cur.count('}') != src.count('}'):
        problems.append('%s: the number of rules changed - this round '
                        'replaces declarations and deletes nothing' % name)

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-38s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_avatar',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_avatar) - '
                        'apply_avatar.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_avatar',\n]",
            "    '.bak_avatar',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-38s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D10: fifteen rules put white text on a colour too
    # light to carry it - five of them failed even for large text,
    'test_contrast.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-38s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-38s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION D, ROUND D10 - WHITE TEXT THAT CANNOT BE READ - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if swept:
    print('\n  EVERY RULE THIS ROUND REPAIRS, and what its text measures:')
    for rel, what, b, a in swept:
        print('    %-34s %-38s %4.2f -> %4.2f%s'
              % (rel[:34], what[:38], b, a, '   <- failed even for large'
                 if b < 3 else ''))
print('\n  DELETES NOTHING. Reported to the orphan round instead:')
for rel, sel, why in SUSPECT_DEAD:
    print('    %-30s %-36s %s' % (rel[:30], sel[:36], why[:40]))
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
