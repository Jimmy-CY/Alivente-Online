# -*- coding: utf-8 -*-
"""apply_small_controls.py - every text control 16px on a phone, so iOS
stops zooming the page when one is tapped.

    python apply_small_controls.py --check     dry run, nothing written
    python apply_small_controls.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (Show-SmallControls.py, 21 Sep)

  Every template that extends base (128) rendered at 375 wide with the real
  base CSS, Bootstrap 4.1.3 and the page's own styles. 64 text controls on
  16 pages came out under 16px, and Chromium's own cascade - DevTools'
  getMatchedStylesForNode - said the same thing about every one of them:
  the page made it small. A local rule at 13-14px, or an inline style.
  None inherited it, none got it from base or Bootstrap. Only 10 of the 64
  even carry .form-control, the one class base's guard reaches, and on
  those a page rule of equal weight comes later and wins.

  No text control on any page measures ABOVE 16px at 375.

WHAT THIS DOES - agreed 21 Sep, option A

  1. base.html gains ONE rule, directly after the existing .form-control
     guard: every text input, select and textarea at 16px !important,
     below 768px, on screen only. !important is the only way a stylesheet
     rule outranks an inline style, and seven of the 64 are inline.
     Simulated on all 128 pages before writing: it changes exactly the
     small controls and nothing else, and it cannot shrink anything,
     because nothing is larger. The existing .form-control rule stays -
     test_zoom_guards.py and test_entry_sections.py both assert it, and it
     is not wrong, only narrower.
  2. dashboard_pl.html's year <select> carries `font-size: 14px
     !important` INLINE. Inline !important beats every stylesheet, so no
     base rule can reach it. The word !important comes off that one
     declaration; 14px stays, so the desktop reads exactly as before, and
     every other inline !important on the element is left alone.
  3. test_panel_title.py's CONTROL strips base's 16px font-sizes to show
     what section titles would be without them, and its pattern did not
     allow for !important - so base's new rule would survive the strip
     and the control would report it could not run. The pattern learns
     the optional !important. Written into the suite with the reason.
  4. test_zoom_guards.py renders base as it is NOW against base as it was
     before ITS round, and requires no control to move. With the new rule
     in base, the small ones move - correctly, and because of THIS round.
     Its "now" learns to leave this round's block out, marked by the
     block's own begin and end comments, so it goes on measuring what
     its own round changed and nothing else. Its fsr.html control would
     otherwise stop being able to fail. Written into the suite.
  5. test_small_controls.py is wired onto the push gate.

  The 21 pages' zoom guards the last round kept are now redundant too.
  Agreed: LEFT for a later tidy, not this round.
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
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_smallctl'
SUITE = 'test_small_controls.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(ROOT, 'base.html')
DASH = os.path.join(ROOT, 'dashboard_pl.html')
PANEL = 'test_panel_title.py'
ZOOM = 'test_zoom_guards.py'

MARK_OPEN = '/* ALV SMALL CONTROLS v1'
MARK_CLOSE = '/* /ALV SMALL CONTROLS v1 */'

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    """Text as LF, and remember what the file used so it goes back the
    same way - a patcher must not reformat what it does not change."""
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def once(text, anchor, where):
    n = text.count(anchor)
    if n != 1:
        problems.append('%s: anchor found %d time(s), expected 1: %r'
                        % (where, n, anchor[:70]))
        return False
    return True


# THE TYPES iOS DOES NOT ZOOM ON, and so the rule leaves alone. One line,
# on purpose: `input:not(a)` NEWLINE `:not(b)` would put whitespace between
# them, and whitespace is the descendant combinator - the rule would then
# match nothing at all.
SKIP = ('checkbox', 'radio', 'hidden', 'submit', 'button', 'reset', 'file',
        'image', 'range', 'color')
INPUT_SEL = 'input' + ''.join(':not([type="%s"])' % t for t in SKIP)

# A comment here must not say what it describes in the words a tool looks
# for. Lesson four of 20 Sep, six times over: no at-sign rule name, no
# declaration spelled out, no comment close inside it.
BLOCK = """

%s - EVERY TEXT CONTROL, not only the one class.
   The rule above reaches .form-control and nothing else. Rendering all
   128 pages that extend base at 375 wide found 64 text controls on 16
   pages still under 16px, so iOS zoomed on every one: 30 quantity boxes
   on the lease generator, filter dropdowns on Properties, Tenants and
   Physical Invoices, the Analysis year pickers, the Edit Issue fields,
   seven "Applies from" dates. Chromium's own cascade said the same of
   all 64 - the PAGE made it small, with a local rule or an inline style
   at 13-14px, which beats a plain base rule by coming later or by being
   written on the element.
   So this one is important, the only way a stylesheet outranks inline.
   It cannot make anything smaller: measured, no text control on any page
   is above 16px at 375. The desktop is untouched - screen, 768 and below.
   Checkboxes, radios, buttons, colour and file pickers are left out;
   iOS does not zoom on them. Keep the input selector on ONE line - a
   line break inside that chain is a descendant combinator.
   See Show-SmallControls.py and test_small_controls.py. */
@media screen and (max-width: 768px) {
    %s,
    select,
    textarea { font-size: 16px !important; }
}
%s""" % (MARK_OPEN, INPUT_SEL, MARK_CLOSE)

BASE_ANCHOR = """   paper, where A4 portrait is about 718 CSS px. 35 pages carry exactly
   that. */
@media screen and (max-width: 768px) {
    .form-control { font-size: 16px; }
}"""

# ---- 1. base --------------------------------------------------------------
src = read(BASE)
if MARK_OPEN in src:
    report.append('%-42s already carries the rule' % 'base.html')
elif once(src, BASE_ANCHOR, 'base.html'):
    text = src.replace(BASE_ANCHOR, BASE_ANCHOR + BLOCK, 1)
    planned[BASE] = (src, text)
    report.append('%-42s + one rule: every text control, 16px !important, '
                  'screen <= 768px' % 'base.html')

# ---- 2. dashboard_pl ------------------------------------------------------
DASH_OLD = """                                               font-weight: 500 !important;
                                               font-size: 14px !important;
                                               min-width: 120px !important;"""
DASH_NEW = """                                               font-weight: 500 !important;
                                               font-size: 14px;
                                               min-width: 120px !important;"""
src = read(DASH)
if DASH_NEW in src and DASH_OLD not in src:
    report.append('%-42s already done' % 'dashboard_pl.html')
elif once(src, DASH_OLD, 'dashboard_pl.html'):
    planned[DASH] = (src, src.replace(DASH_OLD, DASH_NEW, 1))
    report.append('%-42s year select: font-size 14px, no longer !important'
                  % 'dashboard_pl.html')

# ---- 3. test_panel_title.py -----------------------------------------------
PANEL_OLD = """    stripped = re.sub(r'(?<![-\\w])font-size\\s*:\\s*16px\\s*;', '',
                      base_css(BASE_SRC))"""
PANEL_NEW = """    # LATER - test_small_controls.py, 21 Sep. base gained a phone rule
    # setting every text control to 16px !important, and a pattern with no
    # room for !important left it standing in the stripped copy, so this
    # control reported it could not run. The strip allows !important now;
    # the rule it also removes is about inputs, which this fixture has none
    # of, so nothing measured here moves.
    stripped = re.sub(r'(?<![-\\w])font-size\\s*:\\s*16px\\s*'
                      r'(?:!important\\s*)?;', '',
                      base_css(BASE_SRC))"""
if os.path.isfile(PANEL):
    src = read(PANEL)
    if 'LATER - test_small_controls.py' in src:
        report.append('%-42s already allows !important' % PANEL)
    elif once(src, PANEL_OLD, PANEL):
        planned[PANEL] = (src, src.replace(PANEL_OLD, PANEL_NEW, 1))
        report.append('%-42s CONTROL strip allows !important' % PANEL)
else:
    report.append('%-42s not on disk - nothing to adjust' % PANEL)

# ---- 4. test_zoom_guards.py -----------------------------------------------
ZOOM_OLD = """    base_now = COMMENT.sub('', '\\n'.join(styles_of(BASE)))"""
ZOOM_NEW = """    # LATER - test_small_controls.py, 21 Sep. base gained a rule setting
    # EVERY text control to 16px on a phone, so the controls this round
    # left small now move - correctly, and because of that round, not this
    # one. Left in, it would also stop fsr.html's control from failing: a
    # guard removed by hand could no longer change anything. So "now" here
    # is base without that one block, cut out by its own begin and end
    # comments, and this section goes on measuring only what ITS round did.
    base_now = COMMENT.sub('', re.sub(
        r'/\\* ALV SMALL CONTROLS v1\\b.*?/\\* /ALV SMALL CONTROLS v1 \\*/', '',
        '\\n'.join(styles_of(BASE)), flags=re.S))"""
if os.path.isfile(ZOOM):
    src = read(ZOOM)
    if 'LATER - test_small_controls.py' in src:
        report.append('%-42s already leaves the new block out' % ZOOM)
    elif once(src, ZOOM_OLD, ZOOM):
        planned[ZOOM] = (src, src.replace(ZOOM_OLD, ZOOM_NEW, 1))
        report.append('%-42s renders base without the new block' % ZOOM)
else:
    report.append('%-42s not on disk - nothing to adjust' % ZOOM)

# ---- 5. the gate ----------------------------------------------------------
GATE_NOTE = """    # Every text control 16px on a phone. Its rendered section is the
    # invariant itself - every page that extends base, at 375, and NO
    # text control under 16px - plus the other half: at 1280, every
    # control's size identical to before the round. Its control takes the
    # new rule back out of base and must find the small ones again.
    # Newest, so most likely to be what breaks.
    'test_small_controls.py'"""
if not os.path.isfile(PS1):
    report.append('%-42s not on disk - the suite is not wired' % PS1)
else:
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
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
            report.append('%-42s + %s, after %s'
                          % (PS1, SUITE, last.group(1)))

# ==========================================================================
# SELF-CHECK - on what is about to be written, before a byte of it is.
# ==========================================================================
COMMENT = re.compile(r'/\*.*?\*/', re.S)
for path, (src, text) in sorted(planned.items()):
    name = os.path.basename(path)
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (name, e.lineno))
        continue
    if path == BASE:
        # Only ADDED, nothing else touched: the old text is the new text
        # with the block taken out.
        if text.replace(BLOCK, '', 1) != src:
            problems.append('base.html: more changed than the one block')
        body = COMMENT.sub('', BLOCK)
        if body.count('{') != body.count('}') or body.count('{') != 2:
            problems.append('base.html: the block is not one rule in one '
                            'query')
        if re.search(r'input(:not\(\[type="\w+"\]\))+\s+:not', body):
            problems.append('base.html: whitespace inside the input chain')
        c = COMMENT.findall(BLOCK)
        if len(c) != 2 or any('@' in x or 'font-size' in x or
                              x.count('*/') != 1 for x in c):
            problems.append('base.html: a comment in the block says '
                            'something a tool would read as CSS')
        if '@media screen and (max-width: 768px)' not in body:
            problems.append('base.html: the rule is not screen-only')
    if path == DASH:
        if text.replace(DASH_NEW, DASH_OLD, 1) != src:
            problems.append('dashboard_pl.html: more changed than one word')

# ==========================================================================
print('\n' + '=' * 74)
print('SMALL CONTROLS - %s' % ('DRY RUN' if CHECK else 'APPLY'))
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
        # The backup keeps the ORIGINAL's line endings - recorded against
        # the file's own path, so it is copied across to the backup's.
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)

print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
print('         python Show-SmallControls.py      (should now say 0)')
print('         python %s   (the gate)' % PS1)
