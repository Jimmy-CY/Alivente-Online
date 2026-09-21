# -*- coding: utf-8 -*-
"""apply_print_buttons.py - buttons stay on the screen. On paper they are
furniture, and 283 of them were printing.

    python apply_print_buttons.py --check     dry run, nothing written
    python apply_print_buttons.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, after the phone-queries round)

  Every page that extends base, printed at 718 wide (A4 portrait) in
  Chromium: 283 visible buttons on 55 pages - Help, Back and Add in action
  bars, Edit / Delete / Duplicate / Approve / Pay on rows, greyed-out
  "No permission" placeholders, month quick-set buttons, view and period
  toggles, timeline navigation. base's print block hides a list of named
  containers, so a button anywhere else reaches paper.

  ONE KIND OF BUTTON IS CONTENT. home.html's dashboard cards list their
  data as rows you can click through, and each row is a <button> so the
  click works from the keyboard. Hiding every button would print those
  cards empty.

WHAT THIS DOES - agreed 21 Sep

  1. base.html gains one print rule: button, .btn and the three button
     input types, display none, EXCEPT anything marked .print-keep.
     Simulated on every page before writing: the 283 buttons - 603
     elements with their icons and labels - go, and nothing else on any
     page changes. Toggles showing the current choice go too, agreed:
     base already hides the segmented control on paper, and a printout
     that needs to say what it covers says so in its heading.
  2. home.html's six insight rows get .print-keep.
  3. test_print_buttons.py is wired onto the push gate.
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
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_printbtn'
SUITE = 'test_print_buttons.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(ROOT, 'base.html')
HOME = os.path.join(ROOT, 'home.html')
MARK_OPEN = '/* ALV PRINT BUTTONS v1'
MARK_CLOSE = '/* /ALV PRINT BUTTONS v1 */'
KEEP = 'print-keep'

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


# Comments in the block say nothing a CSS tool would read as CSS: no
# at-sign rule name, no declaration, no comment close.
BLOCK = """

%s - A BUTTON IS FURNITURE ON PAPER.
   base's print block names containers - the action bar, the mobile bar,
   modals - and a button anywhere else printed. Measured at A4 portrait
   width: 283 of them on 55 pages, from Help and Back to row actions,
   disabled placeholders, quick-set chips and view toggles.
   So every button goes, the three button input types with it. The one
   exception is a button that IS content: mark it print-keep and it
   prints. home's dashboard rows are the case this was written for -
   each row of a card is a button so a keyboard can click through it,
   and without the mark the cards would print empty.
   Measured before writing: only buttons and what is inside them leave
   the page; nothing else on any page moves. The screen is untouched.
   See test_print_buttons.py. */
@media print {
    button:not(.print-keep),
    .btn:not(.print-keep),
    input[type="submit"],
    input[type="button"],
    input[type="reset"] { display: none !important; }
}
%s""" % (MARK_OPEN, MARK_CLOSE)

ANCHOR = '/* /ALV SMALL CONTROLS v1 */'

# ---- 1. base --------------------------------------------------------------
src = read(BASE)
if MARK_OPEN in src:
    report.append('%-42s already carries the rule' % 'base.html')
elif src.count(ANCHOR) != 1:
    problems.append('base.html: anchor %r found %d time(s), expected 1 - '
                    'is the small-controls round applied?'
                    % (ANCHOR, src.count(ANCHOR)))
else:
    planned[BASE] = (src, src.replace(ANCHOR, ANCHOR + BLOCK, 1))
    report.append('%-42s + one print rule: every button hidden unless '
                  '.print-keep' % 'base.html')

# ---- 2. home --------------------------------------------------------------
ROW_OLD = 'class="today-row today-row--{{ it.severity }} ins-drill"'
ROW_NEW = 'class="today-row today-row--{{ it.severity }} ins-drill %s"' % KEEP
src = read(HOME)
n_old, n_new = src.count(ROW_OLD), src.count(ROW_NEW)
if n_new and not n_old:
    report.append('%-42s already marks its %d insight rows' % ('home.html',
                                                               n_new))
elif n_old != 6 or n_new:
    problems.append('home.html: expected 6 insight rows to mark, found %d '
                    '(and %d already marked)' % (n_old, n_new))
else:
    planned[HOME] = (src, src.replace(ROW_OLD, ROW_NEW))
    report.append('%-42s 6 insight rows marked print-keep' % 'home.html')

# ---- 2b. two suites that compare a file to THEIR round's backup ---------
# test_small_controls says base is its backup plus ITS block; this round adds
# a second block to base. test_print_queries says each file it touched is its
# backup plus `screen and `; home.html was one of them and gains print-keep
# here. Both would report this round as theirs. Each learns to read the file
# as it stood before THIS round when that backup is there. Caught by the
# all-suites sweep on the laptop - the push gate would have stopped on them.
SUITE_EDITS = [
    ('test_small_controls.py',
     r"""    ok(re.sub(r'\n\n' + MARK.pattern, '', BASE, count=1, flags=re.S)
       == read(bak),""",
     r"""    # LATER - test_print_buttons.py, 21 Sep. That round added its own
    # block to base, after this one. "base" here is base as it stood before
    # that round, when its backup is there, so this goes on judging only
    # its own block.
    _then = (read(BASE_PATH + '.bak_printbtn')
             if os.path.isfile(BASE_PATH + '.bak_printbtn') else BASE)
    ok(re.sub(r'\n\n' + MARK.pattern, '', _then, count=1, flags=re.S)
       == read(bak),"""),
    ('test_print_queries.py',
     r"""    for rel, p in TOUCHED:
        now, was = read(p), read(p + SUFFIX)""",
     r"""    for rel, p in TOUCHED:
        # LATER - test_print_buttons.py, 21 Sep. That round marked home's
        # dashboard rows print-keep, in a file this round had touched. The
        # file is judged as it stood before that round when its backup is
        # there.
        now = (read(p + '.bak_printbtn') if os.path.isfile(p + '.bak_printbtn')
               else read(p))
        was = read(p + SUFFIX)"""),
]
for name, old, new in SUITE_EDITS:
    if not os.path.isfile(name):
        report.append('%-42s not on disk - nothing to adjust' % name)
        continue
    src = read(name)
    if 'LATER - test_print_buttons.py' in src:
        report.append('%-42s already reads the pre-round file' % name)
    elif src.count(old) != 1:
        problems.append('%s: anchor found %d time(s), expected 1'
                        % (name, src.count(old)))
    else:
        planned[name] = (src, src.replace(old, new, 1))
        report.append('%-42s reads the file as it was before this round'
                      % name)

# ---- 3. the gate ----------------------------------------------------------
GATE_NOTE = """    # Buttons stay on the screen. Printed at A4 width, every page that
    # extends base must show no button but a .print-keep one - and ONLY
    # buttons may have left the page. Its control strips print-keep from
    # home's dashboard rows and must see the cards print empty. Newest,
    # so most likely to be what breaks.
    'test_print_buttons.py'"""
if os.path.isfile(PS1):
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
else:
    report.append('%-42s not on disk - the suite is not wired' % PS1)

# ==========================================================================
# SELF-CHECK
# ==========================================================================
COMMENT = re.compile(r'/\*.*?\*/', re.S)
if BASE in planned:
    src, text = planned[BASE]
    if text.replace(BLOCK, '', 1) != src:
        problems.append('base.html: more changed than the one block')
    body = COMMENT.sub('', BLOCK)
    if body.count('{') != 2 or body.count('}') != 2:
        problems.append('base.html: the block is not one rule in one query')
    c = COMMENT.findall(BLOCK)
    if len(c) != 2 or any('@' in x or 'display' in x for x in c):
        problems.append('base.html: a comment says something a tool would '
                        'read as CSS')
import ast
for name, (src, text) in planned.items():
    if name.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (name, e.lineno))
if HOME in planned:
    src, text = planned[HOME]
    if text.replace(' ' + KEEP + '"', '"') != src:
        problems.append('home.html: more changed than the class')

print('\n' + '=' * 74)
print('BUTTONS OFF PAPER - %s' % ('DRY RUN' if CHECK else 'APPLY'))
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
print('         python %s   (the gate)' % PS1)
