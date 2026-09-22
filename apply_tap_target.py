# -*- coding: utf-8 -*-
"""apply_tap_target.py - Section C, round C2: 44px to tap on a phone.

    python apply_tap_target.py --check     dry run, nothing written
    python apply_tap_target.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 22 Sep (claude/section_c_decision_sheet.md item 2, and the four
answers after claude/tap_target_survey.md):

  - THE BAR. base's own phone rules made every action-bar button 38px
    tall - Primary, Secondary, Back, More, Filter - about 200 buttons on
    about 80 pages. They are 44px now. Desktop is untouched: 35px.
  - THE FLOOR. One new base block, ALV TAP TARGET v1, phone only: every
    house button (.action-primary/-secondary/-danger/-back, .back-button,
    anything in a bar, a More-menu item), every .status-btn and every
    pop-up footer button is at least 44px tall, and .icon-action-btn is a
    44px square. min-height, so a page that pins a height loses to it.
  - THE COPIES GO. 15 pages set 44px on Back and More themselves, and 7
    set it on a pop-up's footer. Only those declarations are removed -
    every other line of those rules stays. The Personal side keeps its
    four copies until its own round.
  - THE PAGE-OWN BUTTONS the survey found are raised in their own pages,
    because base does not know their classes: the invoice status toolbar
    (Approve, Delete, Duplicate, Send, Unapprove) on the two invoice
    screens, and the month quick-set pills on the four Financials type
    screens.
  - EDIT ASSET'S PHOTO BUTTONS stay 28px circles - a 44px circle would
    cover a third of a 140px photo. Their TARGET grows instead: an
    invisible 8px ring, and on a phone the pair is spaced so the two
    rings meet rather than overlap - a tap between them must not land on
    Delete.
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
SUFFIX = '.bak_tap'
SUITE = 'test_tap_target.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')

BLOCK = """/* ===== ALV TAP TARGET v1 ===== 22 Sep 2026
   44px is the smallest thing a thumb should be asked to hit, and 3.4 of
   the standards has promised it on a phone for weeks. Until 22 Sep base
   itself made the action bar 38px there, fifteen pages put 44 back with
   copies of their own, and seven more did it for their pop-up footers.

   PHONE ONLY. On a desk a pointer is precise and the bar stays 35px.
   The bar's heights are set in its own phone rules; this block is the
   FLOOR for every house button wherever it sits. min-height, not height,
   so a page that pins a height loses to the floor instead of fighting it.
   A page's own button classes are the page's to raise - base cannot know
   them.                                          [test_tap_target.py] */
@media screen and (max-width: 768px) {
  .page-action-buttons .btn,
  .action-more-item,
  .btn.action-primary,
  .btn.action-secondary,
  .btn.action-danger,
  .btn.action-back,
  .btn.back-button,
  .status-btn,
  .modal-footer .btn { min-height: 44px; }
  .icon-action-btn { width: 44px; height: 44px; }
}
/* ===== /ALV TAP TARGET v1 ===== */
"""

BASE_EDITS = [
    ('        .page-action-buttons .action-primary {\n'
     '          flex: 1 1 auto;\n'
     '          min-width: 0;\n'
     '          height: 38px;\n'
     '        }\n',
     '        .page-action-buttons .action-primary {\n'
     '          flex: 1 1 auto;\n'
     '          min-width: 0;\n'
     '          height: 44px;\n'
     '        }\n'),
    ('        /* And it has to be SIZED, which it never needed while it was always\n'
     '           hidden here: its neighbours are all 38px and it came out 35. */\n'
     '        .page-action-buttons .action-secondary {\n'
     '          flex: 0 1 auto;\n'
     '          min-width: 0;\n'
     '          height: 38px;\n'
     '        }\n',
     '        /* And it has to be SIZED, which it never needed while it was always\n'
     '           hidden here: its neighbours were all 38px and it came out 35.\n'
     '           44px since 22 Sep, with the rest of the bar - ALV TAP TARGET. */\n'
     '        .page-action-buttons .action-secondary {\n'
     '          flex: 0 1 auto;\n'
     '          min-width: 0;\n'
     '          height: 44px;\n'
     '        }\n'),
    ('          width: 44px;\n'
     '          height: 38px;\n'
     '          padding: 0;\n'
     '        }\n'
     '        .page-action-buttons .action-back .action-back-label',
     '          width: 44px;\n'
     '          height: 44px;\n'
     '          padding: 0;\n'
     '        }\n'
     '        .page-action-buttons .action-back .action-back-label'),
    ('        .page-action-buttons .action-more-btn {\n'
     '          width: 44px;\n'
     '          height: 38px;\n',
     '        .page-action-buttons .action-more-btn {\n'
     '          width: 44px;\n'
     '          height: 44px;\n'),
    ('    flex: 0 0 auto; width: 44px; height: 38px;\n',
     '    flex: 0 0 auto; width: 44px; height: 44px;\n'),
    ('  .page-action-buttons .action-filter { position: relative; }\n}\n',
     '  .page-action-buttons .action-filter { position: relative; }\n}\n\n'
     + BLOCK),
]

# The pages' own 44px copies: file -> the selectors whose 44px
# declarations go. Every other declaration of those rules stays.
LOCAL = {
    'finance.html': ['.action-back'],
    'finance/cashflow_forecast.html': ['.action-back'],
    'finance/financial_indicators.html': [
        '.action-primary', '.modal-dialog.modal-xl .modal-footer .btn'],
    'finance/vacancy_management.html': [
        '#propertyDetailsModal .modal-footer .btn'],
    'finance_expense_add.html': ['#prorataPreviewModal .modal-footer .btn'],
    'finance_expense_edit.html': ['#prorataPreviewModal .modal-footer .btn'],
    'finance_expense_line_types.html': ['#deleteModal .modal-footer .btn'],
    'finance_expense_line_types_edit.html': [
        '#prorataChangePreviewModal .modal-footer .btn'],
    'finance_pl_act.html': ['.action-more-btn', '.action-back'],
    'finance_valuations_add.html': ['.action-back'],
    'finance_valuations_edit.html': ['.action-back'],
    'fsr.html': ['.action-more-btn', '.action-back'],
    'occupancy_trends.html': ['#yearDetailModal .modal-footer .btn'],
    'projects/project_subtasks_add.html': ['.action-back'],
    'projects/project_task_list.html': ['.action-more-btn', '.action-back'],
    'projects/project_tasks_add.html': ['.action-back'],
    'projects/project_tasks_delete.html': ['.action-back'],
    'projects/project_tasks_edit.html': ['.action-back'],
    'projects/projects.html': ['.action-more-btn', '.action-back'],
    'projects/projects_add.html': ['.action-back'],
    'projects/projects_detail.html': ['.action-more-btn', '.action-back'],
    'projects/projects_edit.html': ['.action-back'],
}
DECL44 = re.compile(r'[ \t]*min-(?:height|width)\s*:\s*44px\s*;[ \t]*\n?')

PHONE = '@media screen and (max-width: 768px) {\n'
INVOICE_ADD = ('  /* 44px to tap - page-own buttons, so the page raises them. And\n'
               '     this page keeps its own .icon-action-btn, written after\n'
               '     base, so base\'s floor cannot reach the line\'s Remove. */\n'
               '  .btn-approve, .btn-delete, .btn-duplicate, .btn-send,\n'
               '  .btn-unapprove { min-height: 44px; }\n'
               '  .icon-action-btn { width: 44px; height: 44px; }\n')
QUICKSET_ADD = ('    /* 44px to tap - a page-own pill, so the page raises it. */\n'
                '    .quickset-btn { min-height: 44px; }\n')
PHOTO_ADD = ('    /* 44px to tap. A 44px circle would cover too much of the\n'
             '       photo, so the circle stays 32px and the TARGET grows: an\n'
             '       invisible 8px ring. The pair is spaced 16px so the two\n'
             '       rings meet rather than overlap - a tap between them must\n'
             '       not land on Delete - and moved 8px in, or the tile\'s\n'
             '       overflow:hidden would clip the ring. */\n'
             '    .photo-manage-actions { top: 8px; right: 8px; gap: 16px; }\n'
             '    .btn-photo-star,\n'
             '    .btn-photo-delete { position: relative; }\n'
             '    .btn-photo-star::before,\n'
             '    .btn-photo-delete::before {\n'
             '        content: \'\';\n'
             '        position: absolute;\n'
             '        inset: -8px;\n'
             '        border-radius: 50%;\n'
             '    }\n')
ADDS = {
    'customer_invoice_form.html': ('  .status-action-form, .status-action-form .btn { width: 100%; }\n',
                                   INVOICE_ADD),
    'physical_invoice_edit.html': ('  .status-action-form, .status-action-form .btn { width: 100%; }\n',
                                   INVOICE_ADD),
    'finance_expense_types_add.html': (PHONE, QUICKSET_ADD),
    'finance_expense_types_edit.html': (PHONE, QUICKSET_ADD),
    'finance_revenue_types_add.html': (PHONE, QUICKSET_ADD),
    'finance_revenue_types_edit.html': (PHONE, QUICKSET_ADD),
    'edit_asset.html': (PHONE, PHOTO_ADD),
}

# LATER - test_secondary_visible.py asserted the bar's phone height as the
# literal 38. Its claim is "the secondary is sized like its neighbours",
# so it is now asked of the height base gives the Primary, whatever that
# is. Nothing else in the suite changes.
SV = 'test_secondary_visible.py'
SV_EDITS = [
    ("CODE, WCODE = nocomment(BCSS), nocomment(WCSS)\n",
     "CODE, WCODE = nocomment(BCSS), nocomment(WCSS)\n"
     "# LATER - test_tap_target.py, 22 Sep. The row was 38px when this round\n"
     "# ran; round C2 made the whole bar 44px on a phone. \"Sized like its\n"
     "# neighbours\" is asked of the height base gives the Primary, not of 38.\n"
     "_rh = re.search(r'\\.page-action-buttons \\.action-primary\\s*\\{[^}]*?'\n"
     "                r'(?<![-\\w])height:\\s*(\\d+)px', CODE)\n"
     "ROW_H = _rh.group(1) if _rh else '38'\n"),
    ("check('the secondary is sized like its neighbours',\n"
     "      re.search(r'(?m)^\\s*\\.page-action-buttons \\.action-secondary\\s*\\{'\n"
     "                r'[^}]*height:\\s*38px', CODE) is not None)\n",
     "check('the secondary is sized like its neighbours',\n"
     "      re.search(r'(?m)^\\s*\\.page-action-buttons \\.action-secondary\\s*\\{'\n"
     "                r'[^}]*height:\\s*' + ROW_H + 'px', CODE) is not None)\n"),
    ("      any(re.search(r'\\.action-secondary\\s*\\{[^}]*height:\\s*38px', x)\n",
     "      any(re.search(r'\\.action-secondary\\s*\\{[^}]*height:\\s*' + ROW_H\n"
     "                    + 'px', x)\n"),
    ("              _sec_h and _sec_h[0] == 38, str(_sec_h))\n",
     "              _sec_h and _sec_h[0] == int(ROW_H), str(_sec_h))\n"),
]

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


def rules_of(text, selector):
    """(start, end) of every rule whose selector is exactly `selector`,
       brace to brace, on a CSS text with no nested blocks inside a rule."""
    out = []
    pat = re.compile(r'(^|[{};]|\*/)\s*(' + re.escape(selector) + r')\s*\{',
                     re.M)
    for m in pat.finditer(text):
        open_ = m.end() - 1
        close = text.find('}', open_)
        if close < 0 or '{' in text[open_ + 1:close]:
            continue
        out.append((open_ + 1, close))
    return out


def enclosing(text, pos):
    """The heads of the blocks still open at `pos` - @media and the like -
       walked brace by brace over the <style> the position sits in."""
    start = text.rfind('<style', 0, pos)
    start = text.find('>', start) + 1 if start >= 0 else 0
    css = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)),
                 text[start:pos], flags=re.S)
    stack, last = [], 0
    for m in re.finditer(r'[{}]', css):
        if m.group() == '{':
            stack.append(css[last:m.start()].split(';')[-1].split('}')[-1]
                         .strip())
        elif stack:
            stack.pop()
        last = m.end()
    return [h for h in stack[:-1] if h.startswith('@')]


# --- base ----------------------------------------------------------------
b = read(BASE)
cur, n = b, 0
for old, new in BASE_EDITS:
    if new in cur:
        continue
    if cur.count(old) != 1:
        problems.append('base.html: anchor found %d time(s): %r'
                        % (cur.count(old), old.strip()[:60]))
        continue
    cur = cur.replace(old, new, 1)
    n += 1
if n:
    planned[BASE] = (b, cur)
    report.append('%-52s %d edit(s)' % ('base.html', n))
else:
    report.append('%-52s already done' % 'base.html')

# --- the pages' own 44px copies -----------------------------------------
for rel, sels in LOCAL.items():
    p = os.path.join(T, *rel.split('/'))
    if not os.path.isfile(p):
        problems.append('%s not found' % rel)
        continue
    src = read(p)
    cur, gone = src, 0
    for sel in sels:
        hits = [(a, z) for a, z in rules_of(cur, sel)
                if DECL44.search(cur[a:z])]
        if not hits:
            continue                                   # already done
        if len(hits) != 1:
            problems.append('%s: %d rule(s) for %s carry 44px, expected 1'
                            % (rel, len(hits), sel))
            continue
        a, z = hits[0]
        body = cur[a:z]
        # Inside a phone query? The @media blocks still open at the rule.
        media = ' '.join(enclosing(cur, a))
        if 'max-width' not in media:
            problems.append('%s: the 44px rule for %s is not in a phone '
                            'query' % (rel, sel))
            continue
        new_body = DECL44.sub('', body)
        # A one-line rule keeps its space before the closing brace.
        if body.endswith(' ') and not new_body.endswith((' ', '\n')):
            new_body += ' '
        if not new_body.strip():
            problems.append('%s: %s would be left empty' % (rel, sel))
            continue
        gone += len(DECL44.findall(body))
        cur = cur[:a] + new_body + cur[z:]
    if cur != src:
        planned[p] = (src, cur)
        report.append('%-52s %d declaration(s) removed' % (rel, gone))
    else:
        report.append('%-52s already done' % rel)

# --- the pages' own buttons ---------------------------------------------
for rel, (anchor, add) in ADDS.items():
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        problems.append('%s not found' % rel)
        continue
    src = planned[p][1] if p in planned else read(p)
    orig = planned[p][0] if p in planned else src
    if add in src:
        report.append('%-52s already raised' % rel)
        continue
    if src.count(anchor) != 1:
        problems.append('%s: anchor found %d time(s)' % (rel,
                                                         src.count(anchor)))
        continue
    planned[p] = (orig, src.replace(anchor, anchor + add, 1))
    report.append('%-52s page-own buttons raised' % rel)

# --- LATER: the older suite that named 38px ------------------------------
if not os.path.isfile(SV):
    problems.append('%s not found' % SV)
else:
    src = read(SV)
    cur, n = src, 0
    for old, new in SV_EDITS:
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (SV, cur.count(old), old.strip()[:60]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        try:
            compile(cur, SV, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (SV, e.lineno))
        planned[SV] = (src, cur)
        report.append('%-52s LATER: the bar height read from base (%d)'
                      % (SV, n))
    else:
        report.append('%-52s already reads the height from base' % SV)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-52s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_csmall',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_csmall) - '
                        'apply_c_small.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_csmall',\n]",
            "    '.bak_csmall',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-52s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section C round C2: 44px to tap on a phone - the bar, the floor in
    # base, the pages' own copies gone,
    'test_tap_target.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-52s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-52s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# --- self-checks ---------------------------------------------------------
if BASE in planned:
    t = planned[BASE][1]
    if t.count('/* ===== ALV TAP TARGET v1 =====') != 1:
        problems.append('base.html: the block is not there exactly once')
    blk = t[t.find('/* ===== ALV TAP TARGET v1'):
            t.find('/* ===== /ALV TAP TARGET v1')]
    if blk.count('{') != blk.count('}'):
        problems.append('base.html: the block\'s braces do not balance')
    if re.search(r'#[0-9a-fA-F]{3,8}\b', re.sub(r'/\*.*?\*/', '', blk,
                                                flags=re.S)):
        problems.append('base.html: the block holds a colour')
    css = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    for s, e in ((css.count('{'), css.count('}')),):
        if s != e:
            problems.append('base.html: braces would not balance (%d/%d)'
                            % (s, e))
for p, (src, text) in planned.items():
    if p.endswith('.html'):
        a = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        if a.count('{') - a.count('}') != \
                re.sub(r'/\*.*?\*/', '', src, flags=re.S).count('{') - \
                re.sub(r'/\*.*?\*/', '', src, flags=re.S).count('}'):
            problems.append('%s: the brace balance moved' % p)

print('\n' + '=' * 78)
print('SECTION C, ROUND C2 - 44PX TO TAP - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
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
