# -*- coding: utf-8 -*-
"""apply_applies_from.py - the "Applies from" date panel and the delete
choice cards, owned by base; one name for the date.

    python apply_applies_from.py --check     dry run, nothing written
    python apply_applies_from.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, claude/applies_from_survey.md)

  Five Financials entry screens carry the same "Applies from" panel, every
  inch of it inline: five literal colours per panel, a date input with its
  own border and no .form-control. Two delete pop-ups carry the same two
  radio cards - "Stop it from a date" in teal and "Remove it completely" in
  red - inline as well. Valuations calls the same effective_date field
  "Effective From".

WHAT THIS DOES - agreed 21 Sep

  1. base gains ALV APPLIES v1: .alv-applies (the panel, its label and
     icon), .alv-applies-help (the paragraph), and .alv-choice /
     .alv-choice--danger / .alv-choice-note / .alv-choice-when (the cards),
     all painted from base's tokens.
  2. On the five screens and the two pop-ups ONLY style attributes change:
     each becomes a class, or goes. Every word, id, name, value, radio and
     script hook stays. line_types_edit keeps its panel's display:none,
     which its script lifts.
  3. The date input becomes .form-control - base's field - kept narrow -
     and its label names it in <strong>, as every field label does.
  4. The panel moves from ABOVE the Save bar to straight UNDER it. The
     sweep found it: the 16 Sep decision is that the bar is the first
     thing in every form, and the panel only escaped that check because
     its date was not a .form-control. Agreed 21 Sep.
  5. Valuations add/edit: the label "Effective From" reads "Applies from".
  6. test_small_controls.py compared every control with the file NOW; it
     reads the page and base as its round left them (LATER).
  7. alv_rounds.py learns this round; test_applies_from.py goes on the gate.
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

import ast
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_appliesfrom'
SUITE = 'test_applies_from.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
ANCHOR = '/* /ALV REPORT HEAD v1 */'
MARK_OPEN = '/* ALV APPLIES v1'

PANEL_PAGES = ['finance_expense_add.html', 'finance_expense_edit.html',
               'finance_revenue_add.html', 'finance_revenue_edit.html',
               'finance_expense_line_types_edit.html']
CHOICE_PAGES = ['finance_expense.html', 'finance_expense_line_types.html']
LABEL_PAGES = ['finance_valuations_add.html', 'finance_valuations_edit.html']

# style value (whitespace collapsed) -> (class to add or None, style to keep)
PANEL_MAP = {
    'background:#f8f9fa; border:1px solid #e9ecef; border-left:4px solid '
    '#0e7c8b; border-radius:8px; padding:14px 18px; margin-bottom:18px;':
        ('alv-applies', None),
    'display:none; background:#f8f9fa; border:1px solid #e9ecef; '
    'border-left:4px solid #0e7c8b; border-radius:8px; padding:14px 18px; '
    'margin-bottom:18px;':
        ('alv-applies', 'display:none;'),
    'display:block; font-weight:600; color:#2c3e50; margin-bottom:6px;':
        (None, None),
    'color:#0e7c8b;': (None, None),
    'border:2px solid #e9ecef; border-radius:8px; padding:8px 12px; '
    'font-size:14px; background:#fff;': ('form-control', None),
    'margin:8px 0 0 0; font-size:13px; color:#6c757d; line-height:1.5;':
        ('alv-applies-help', None),
}
PANEL_WANT = 5          # attributes rewritten per panel
CHOICE_MAP = {
    'display:block; border:1px solid #e9ecef; border-left:4px solid #0e7c8b; '
    'border-radius:8px; padding:12px 14px; margin-bottom:10px; '
    'cursor:pointer;': ('alv-choice', None),
    'display:block; border:1px solid #f5c6cb; border-left:4px solid #dc3545; '
    'border-radius:8px; padding:12px 14px; cursor:pointer;':
        ('alv-choice alv-choice--danger', None),
    'color:#a71d2a;': (None, None),
    'display:block; margin:6px 0 0 22px; font-size:13px; color:#6c757d;':
        ('alv-choice-note', None),
    'display:block; margin:10px 0 0 22px;': ('alv-choice-when', None),
    'font-size:13px; color:#495057;': (None, None),
    'border:2px solid #e9ecef; border-radius:8px; padding:6px 10px; '
    'font-size:14px; margin-left:6px;': ('form-control', None),
}
CHOICE_WANT = 8

BLOCK = """/* ALV APPLIES v1 - the date a Financials figure takes effect from, and
   the two ways to stop one. The panel sits under an entry form: a soft
   surface, the accent rule down its left edge, the label in ink with the
   calendar mark in the accent, the date as base's own field kept narrow,
   and the guidance under it in the soft ink. The choice cards are the two
   radios a delete pop-up offers - stop it from a date, the calm one, in
   the accent; remove it completely, which cannot be undone, in the bad
   colour. Their note and their date line indent to clear the radio. See
   test_applies_from.py. */
.alv-applies {
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    border-left: 4px solid var(--alv-accent);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 18px;
}
.alv-applies > label {
    display: block;
    font-weight: 600;
    color: var(--alv-ink);
    margin-bottom: 6px;
}
.alv-applies > label > i { color: var(--alv-accent); }
.alv-applies > .form-control { max-width: 220px; }
.alv-applies-help {
    margin: 8px 0 0 0;
    font-size: 13px;
    color: var(--alv-ink-soft);
    line-height: 1.5;
}
.alv-choice {
    display: block;
    border: 1px solid var(--alv-line);
    border-left: 4px solid var(--alv-accent);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    cursor: pointer;
    font-weight: 400;
}
.alv-choice:last-child { margin-bottom: 0; }
.alv-choice--danger {
    border-color: color-mix(in srgb, var(--alv-bad) 30%, #fff);
    border-left-color: var(--alv-bad);
}
.alv-choice--danger > strong { color: var(--alv-bad); }
.alv-choice-note {
    display: block;
    margin: 6px 0 0 22px;
    font-size: 13px;
    color: var(--alv-ink-soft);
}
.alv-choice-when {
    display: block;
    margin: 10px 0 0 22px;
    font-size: 13px;
    color: var(--alv-ink-soft);
}
.alv-choice-when > .form-control {
    display: inline-block;
    width: auto;
    margin-left: 6px;
    padding: 6px 10px;
}
/* /ALV APPLIES v1 */"""

report, problems = [], []
planned = {}
CRLF = {}


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


def element_end(t, start, tag):
    """End of the element whose opening tag begins at `start`."""
    depth = 0
    for m in re.finditer(r'<(/?)%s\b[^>]*>' % tag, t[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    return -1


def rewrite(region, mapping):
    """Swap each mapped style attribute for a class, inside `region`.
    Returns (new_region, count, problems)."""
    probs = []
    n = [0]

    def one_tag(m):
        tag = m.group(0)
        st = re.search(r'\s+style="([^"]*)"', tag)
        if not st:
            return tag
        key = ' '.join(st.group(1).split())
        if key not in mapping:
            return tag
        cls, keep = mapping[key]
        if cls and re.search(r'\sclass="', tag):
            probs.append('a styled tag already carries a class: %s'
                         % tag[:60])
            return tag
        rep = ''
        if cls:
            rep += ' class="%s"' % cls
        if keep:
            rep += ' style="%s"' % keep
        n[0] += 1
        return tag[:st.start()] + rep + tag[st.end():]

    out = re.sub(r'<[a-zA-Z][^<>]*>', one_tag, region)
    return out, n[0], probs


# ---- 1. base --------------------------------------------------------------
b = read(BASE)
if MARK_OPEN in b:
    report.append('%-44s already carries the component' % 'base.html')
elif b.count(ANCHOR) != 1:
    problems.append('base.html: anchor %r found %d time(s)'
                    % (ANCHOR, b.count(ANCHOR)))
else:
    planned[BASE] = (b, b.replace(ANCHOR, ANCHOR + '\n\n' + BLOCK, 1))
    report.append('%-44s + ALV APPLIES v1' % 'base.html')

# ---- 2. the five panels ---------------------------------------------------
for name in PANEL_PAGES:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        problems.append('%s not found' % name)
        continue
    t = read(p)
    if 'class="alv-applies"' in t:
        report.append('%-44s already done' % name)
        continue
    m = re.search(r'<div\b[^>]*style="[^"]*border-left:4px solid #0e7c8b;'
                  r'[^"]*padding:14px 18px;[^"]*"[^>]*>', t)
    if not m or 'effective_date' not in t[m.end():m.end() + 400]:
        problems.append('%s: no Applies-from panel' % name)
        continue
    e = element_end(t, m.start(), 'div')
    new, k, pr = rewrite(t[m.start():e], PANEL_MAP)
    problems += ['%s: %s' % (name, x) for x in pr]
    if k != PANEL_WANT:
        problems.append('%s: %d panel attribute(s) rewritten, expected %d'
                        % (name, k, PANEL_WANT))
        continue
    # The label is base's field label: its name in <strong>.
    if new.count('</i> Applies from\n') != 1:
        problems.append('%s: the label text not found once' % name)
        continue
    new = new.replace('</i> Applies from\n', '</i> <strong>Applies from'
                      '</strong>\n', 1)
    # UNDER the Save bar, agreed 21 Sep: the bar is the first thing in the
    # form (16 Sep). The panel is cut from above the bar, with its
    # indentation and the blank line after it, and put straight below.
    ls = t.rfind('\n', 0, m.start()) + 1
    ind = t[ls:m.start()]
    gap = re.match(r'\n\n([ \t]*)<div class="page-action-buttons">', t[e:])
    if ind.strip() or not gap:
        problems.append('%s: the Save bar does not follow the panel' % name)
        continue
    bar = e + 2 + len(gap.group(1))
    be = element_end(t, bar, 'div')
    text = (t[:ls] + t[bar - len(gap.group(1)):be] + '\n\n' + ind + new
            + t[be:])
    planned[p] = (t, text)
    report.append('%-44s the panel -> .alv-applies (%d attributes), '
                  'moved under Save' % (name, k))

# ---- 3. the choice cards --------------------------------------------------
for name in CHOICE_PAGES:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        problems.append('%s not found' % name)
        continue
    t = read(p)
    if 'class="alv-choice"' in t:
        report.append('%-44s already done' % name)
        continue
    a = re.search(r'<label\b[^>]*style="display:block; border:1px solid '
                  r'#e9ecef; border-left:4px solid #0e7c8b;', t)
    d = re.search(r'<label\b[^>]*style="display:block; border:1px solid '
                  r'#f5c6cb;', t)
    if not a or not d or d.start() < a.start():
        problems.append('%s: the two choice cards not found in order' % name)
        continue
    e = element_end(t, d.start(), 'label')
    new, k, pr = rewrite(t[a.start():e], CHOICE_MAP)
    problems += ['%s: %s' % (name, x) for x in pr]
    if k != CHOICE_WANT:
        problems.append('%s: %d card attribute(s) rewritten, expected %d'
                        % (name, k, CHOICE_WANT))
        continue
    planned[p] = (t, t[:a.start()] + new + t[e:])
    report.append('%-44s the two cards -> .alv-choice (%d attributes)'
                  % (name, k))

# ---- 4. one name for the date ---------------------------------------------
OLD_LABEL = '<label for="effective_date"><strong>Effective From</strong></label>'
NEW_LABEL = '<label for="effective_date"><strong>Applies from</strong></label>'
for name in LABEL_PAGES:
    p = os.path.join(T, name)
    t = read(p)
    if NEW_LABEL in t and OLD_LABEL not in t:
        report.append('%-44s already says Applies from' % name)
    elif t.count(OLD_LABEL) != 1:
        problems.append('%s: the Effective From label found %d time(s)'
                        % (name, t.count(OLD_LABEL)))
    else:
        planned[p] = (t, t.replace(OLD_LABEL, NEW_LABEL, 1))
        report.append('%-44s Effective From -> Applies from' % name)

# ---- 4b. test_small_controls.py: LATER -----------------------------------
# Its render compared every control's size before its round with the file
# as it is NOW, so a later round restyling a control on purpose - this one
# makes the Applies-from date a .form-control - reads as its failure. The
# sweep caught it. It now compares with the page and base as ITS round
# left them.
SC = 'test_small_controls.py'
SC_OLD = """            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else t
            old_mk = body_markup(old_t)"""
SC_NEW = """            # LATER - test_applies_from.py, 21 Sep: compare with the page
            # and base as THIS round left them; a later round may restyle
            # a control on purpose.
            from alv_rounds import as_left_by
            _lt = as_left_by(p, SUFFIX, read)
            _bl = '\\n'.join(styles_of(as_left_by(BASE_PATH, SUFFIX, read)))
            if _lt != t:
                t, mk = _lt, body_markup(_lt)
                now = render(br, fixture(boot, _bl, styles_of(t), mk), 375)
            _base_now = _bl if _lt != read(p) else base_now
            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else t
            old_mk = body_markup(old_t)"""
SC_OLD2 = """            d_now = render(br, fixture(boot, base_now, styles_of(t), mk),
                           1280)"""
SC_NEW2 = """            d_now = render(br, fixture(boot, _base_now, styles_of(t), mk),
                           1280)"""
if os.path.isfile(SC):
    cur = read(SC)
    if SC_NEW in cur:
        report.append('%-44s already reads its round\'s pages' % SC)
    elif cur.count(SC_OLD) == 1 and cur.count(SC_OLD2) == 1:
        planned[SC] = (cur, cur.replace(SC_OLD, SC_NEW, 1).replace(
            SC_OLD2, SC_NEW2, 1))
        report.append('%-44s LATER: compares with the pages its round left'
                      % SC)
    else:
        problems.append('%s: anchors not found once' % SC)

# ---- 5. rounds, gate ------------------------------------------------------
ROUNDS_FILE = 'alv_rounds.py'
if os.path.isfile(ROUNDS_FILE):
    cur = read(ROUNDS_FILE)
    if "'.bak_appliesfrom'" in cur:
        report.append('%-44s already lists this round' % ROUNDS_FILE)
    elif cur.count("    '.bak_reporthead',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (cur, cur.replace(
            "    '.bak_reporthead',\n]",
            "    '.bak_reporthead',\n    '.bak_appliesfrom',\n]", 1))
        report.append('%-44s learns .bak_appliesfrom' % ROUNDS_FILE)
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # The Applies-from panel on five Financials entry screens and the two
    # delete pop-ups' choice cards are base's. Only style attributes moved;
    # rendered, all five panels and both card pairs read the same, from
    # base's tokens. Valuations names the date Applies from too.
    # Newest, so most likely to be what breaks.
    'test_applies_from.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK - on the templates only attributes (and one label) changed
# ==========================================================================
def skeleton(t):
    t = re.sub(r'\s(?:style|class)="[^"]*"', '', t)
    t = t.replace('Effective From', 'Applies from')
    t = t.replace('<strong>Applies from</strong>', 'Applies from')
    return re.sub(r'\s+>', '>', ' '.join(t.split()))


def split_panel(t, old):
    """(the page without its panel, the panel) - so a panel that MOVED
    compares equal, and anything else that changed does not."""
    m = (re.search(r'<div\b[^>]*style="[^"]*border-left:4px solid #0e7c8b;'
                   r'[^"]*padding:14px 18px;', t) if old else
         re.search(r'<div\b[^>]*class="alv-applies"', t))
    if not m:
        return t, ''
    e = element_end(t, m.start(), 'div')
    return t[:m.start()] + t[e:], t[m.start():e]


for path, (src, text) in planned.items():
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (path, e.lineno))
    if path.endswith('.html') and path != BASE:
        a_rest, a_pan = split_panel(src, True)
        b_rest, b_pan = split_panel(text, False)
        if skeleton(a_rest) != skeleton(b_rest) or \
                skeleton(a_pan) != skeleton(b_pan):
            problems.append('%s: something other than style/class changed'
                            % path)
        if b_pan:
            bar = text.find('class="page-action-buttons"')
            if not (0 <= bar < text.find(b_pan) < text.find('class="form-card')):
                problems.append('%s: the panel is not between Save and the '
                                'first section' % path)
if BASE in planned:
    src, text = planned[BASE]
    if text.replace('\n\n' + BLOCK, '', 1) != src:
        problems.append('base.html: more changed than the one block')
    if any('{' in x or '@' in x for x in re.findall(r'/\*.*?\*/', BLOCK,
                                                     re.S)):
        problems.append('base.html: a comment reads like CSS')

print('\n' + '=' * 74)
print('APPLIES FROM - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
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
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
