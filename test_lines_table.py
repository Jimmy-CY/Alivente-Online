# -*- coding: utf-8 -*-
"""test_lines_table.py - round IN-2, 11 Oct 2026.

THE INVOICE LINE GRID, SAID ONCE, AND SAID FOR A PHONE TOO.

    python test_lines_table.py

Run from the repo root, after apply_lines_table.py.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP. Both pages add a line by
cloning `<template id="lineTemplate">`, so a row the user adds after the
page has loaded comes from there and not from the server. If only the
server-rendered rows carried data-label, every line added on a phone
would be a column of unnamed boxes - and it would look perfect in any
screenshot taken before somebody pressed Add. The suite reads the
template, not just the tbody.

SECTION 5 MEASURES BOTH WIDTHS AGAINST THE BACKUP. It is not enough to
show the phone stacking; the control is that the SAME markup under the
page's old CSS still hides a third of itself, so the measurement is of
this round and not of a browser default.

WHAT THIS SUITE DOES NOT CLAIM. It does not claim stacking is the right
answer. That was chosen from two renders - a stacked block against a
pinned column with a swipe cue - knowing stacking costs height. It holds
the system to the choice.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_cssrules                                             # noqa: E402
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_lines'
PATCHER = 'apply_lines_table.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

PAGES = ('customer_invoice_form.html', 'physical_invoice_edit.html')

N_LABELLED = 24        # 6 named columns x 2 rows x 2 pages
N_ROWS = 4             # a tbody row and a template row, on each page
N_COLS = 7             # six named, one for the remove button
HIDDEN_WAS = 362       # px of the grid outside its box at 390, before
PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def before(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def css_of(text):
    return '\n'.join(re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
                     for a, b in alv_cssrules.style_spans(text))


def headers_of(text):
    m = re.search(r'<thead>(.*?)</thead>', text, re.S)
    if not m:
        return []
    return [' '.join(re.sub(r'<[^>]+>|\{%.*?%\}', '', th).split())
            for th in re.findall(r'<th\b[^>]*>(.*?)</th>', m.group(1), re.S)]


print(__doc__.strip().split('\n')[0])

BASE = alv_tree.path_of('base.html')
b = read(BASE)
bcss = css_of(b)

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
for rel in PAGES:
    check('  %s is where alv_tree says' % rel,
          os.path.isfile(alv_tree.path_of(rel)))

# ---------------------------------------------------------------------- 2
head('2. BASE OWNS THE COMPONENT NOW, AND THE PAGES DO NOT')

for sel in ('.lines-scroll', '.lines-table', '.lines-table thead th'):
    check('base declares %s' % sel,
          re.search(r'(?<![-\w])%s\s*\{' % re.escape(sel), bcss) is not None)
check('  and the radius is the token D-12 put in reach, not 8px again',
      re.search(r'\.lines-scroll\s*\{[^}]*border-radius:\s*'
                r'var\(--alv-radius\)', bcss) is not None)
_shadow = re.search(r'\.lines-scroll\s*\{[^}]*box-shadow:\s*([^;]+)', bcss)
check('  and the shadow is a literal, like every other shadow base writes',
      _shadow is not None and 'rgba(' in _shadow.group(1)
      and 'var(' not in _shadow.group(1),
      '' if _shadow is None else ' '.join(_shadow.group(1).split())[:40])
_tok = re.findall(r'--alv-shadow[\w-]*\s*:', bcss)
check('    CONTROL: because base defines no shadow token to use instead',
      not _tok, '%d found: %s' % (len(_tok), ', '.join(_tok[:2])))

for rel in PAGES:
    t = read(alv_tree.path_of(rel))
    left = re.findall(r'(?<![-\w])\.lines-[\w-]*[^{}]*\{', css_of(t))
    check('  %s declares none of it any more' % rel, not left,
          '%d left: %s' % (len(left), ' '.join(x.strip() for x in left[:2])))

# A GATE READS THE FILE AS THE ROUND LEFT IT - and the backups are what
# make the claim "they were identical" checkable rather than a story.
was = []
for rel in PAGES:
    t = before(alv_tree.path_of(rel))
    was.append(sorted(re.findall(r'[ \t]*\.lines[^{}]*\{[^}]*\}', css_of(t))))
check('CONTROL: the backups prove both pages carried the rules',
      all(len(w) == 3 for w in was), '%s' % [len(w) for w in was])
check('  and that they were IDENTICAL, which is what made it a component',
      was[0] == was[1])
check('  CONTROL: and base did not already say it',
      '.lines-table' not in css_of(before(BASE)))

# ---------------------------------------------------------------------- 3
head('3. EVERY CELL CARRIES ITS OWN COLUMN NAME')

labelled = 0
rows = 0
mismatch = []
for rel in PAGES:
    t = read(alv_tree.path_of(rel))
    heads = headers_of(t)
    check('  %s still has %d columns, the last unnamed' % (rel, N_COLS),
          len(heads) == N_COLS and heads[-1] == '', '%r' % (heads,))
    for what, pat in (('tbody', r'<tbody id="linesBody">(.*?)</tbody>'),
                      ('template',
                       r'<template id="lineTemplate">(.*?)</template>')):
        m = re.search(pat, t, re.S)
        if not m:
            mismatch.append('%s: no %s' % (rel, what))
            continue
        rows += 1
        got = re.findall(r'<td\b[^>]*?data-label="([^"]*)"', m.group(1))
        labelled += len(got)
        # THE LABEL IS THE COLUMN'S OWN NAME, read from the page's thead.
        # Typing them in here would be a second copy of the header, and
        # the label-fit round already found one field wearing four names
        # because four places each kept their own.
        if got != [h for h in heads if h]:
            mismatch.append('%s %s: %r' % (rel, what, got))

check('%d cell(s) carry a data-label' % labelled, labelled == N_LABELLED,
      '%d' % labelled)
check('  across %d row(s) - a tbody row and a template row on each page'
      % N_ROWS, rows == N_ROWS, '%d' % rows)
check('  and every label is that column\'s own heading, in order',
      not mismatch, '; '.join(mismatch[:2]))

# ---------------------------------------------------------------------- 4
head('4. THE TEMPLATE IS LABELLED TOO - WHERE AN ADDED LINE COMES FROM')

for rel in PAGES:
    t = read(alv_tree.path_of(rel))
    m = re.search(r'<template id="lineTemplate">(.*?)</template>', t, re.S)
    n = len(re.findall(r'data-label=', m.group(1))) if m else 0
    check('  %s: its <template> row is labelled' % rel, n == N_COLS - 1,
          '%d of %d' % (n, N_COLS - 1))
    # The template only matters because something clones it.
    check('    CONTROL: and the page really does clone it to add a line',
          'lineTemplate' in t and 'cloneNode' in t)
print('        Label only the server-rendered rows and every line added')
print('        on a phone is a column of unnamed boxes - a defect that')
print('        appears after an interaction, which no screenshot catches.')

# ---------------------------------------------------------------------- 5
head('5. MEASURED - THE GRID ON A DESKTOP, BLOCKS ON A PHONE')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    SKIP += 1
    print('  skip playwright is not installed here')
    sync_playwright = None

if sync_playwright is not None:
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    page_p = alv_tree.path_of(PAGES[0])
    now = read(page_p)
    old = before(page_p)

    def grid(text):
        m = re.search(r'<div class="lines-scroll">(.*?)</div>', text, re.S)
        if m:
            return m.group(1)
        i = text.find('lines-table')
        j = text.rfind('<table', 0, i)
        return text[j:text.find('</table>', j) + 8]

    def fill(markup):
        """Resolve the template's Django tags to the editable branch and
        give the inputs something to show. A fixture of empty boxes
        measures the boxes, not the page."""
        markup = re.sub(r'\{%\s*if editable\s*%\}(.*?)\{%\s*endif\s*%\}',
                        r'\1', markup, flags=re.S)
        markup = re.sub(r'\{%\s*if not editable\s*%\}.*?\{%\s*endif\s*%\}',
                        '', markup, flags=re.S)
        markup = re.sub(r'\{%\s*for .*?%\}|\{%\s*endfor\s*%\}', '', markup)
        markup = re.sub(r'value="\{\{[^}]*\}\}"', 'value="Cleaning"', markup)
        markup = re.sub(r'\{\{.*?\}\}', '', markup, flags=re.S)
        return markup

    body = fill(grid(now))
    DOC = ('<!doctype html><html><head><meta charset="utf-8">'
           '<link rel="stylesheet" href="https://example.invalid/x.css">'
           '<style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:12px}</style></head>'
           '<body><div class="lines-scroll">%s</div></body></html>')

    fx_now = os.path.join(SCRATCH, 'in2_now.html')
    with open(fx_now, 'w', encoding='utf-8') as f:
        f.write(DOC % (boot, re.sub(r'\{%.*?%\}', '', bcss, flags=re.S),
                       body))
    # The control: the SAME markup under the page's OLD css.
    fx_was = os.path.join(SCRATCH, 'in2_was.html')
    with open(fx_was, 'w', encoding='utf-8') as f:
        f.write(DOC % (boot, css_of(old), body))

    refused = []

    def measure(path, width):
        pw = sync_playwright().start()
        try:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={'width': width, 'height': 800})

            def _abort(route):
                refused.append(route.request.url)
                route.abort()

            ctx.route(re.compile(r'^https?://'), _abort)
            pg = ctx.new_page()
            _goto(pg, path)
            pg.wait_for_timeout(140)
            out = pg.evaluate(
                '() => { var b = document.querySelector(".lines-scroll");'
                ' var t = document.querySelector(".lines-table");'
                ' var tr = document.querySelector(".lines-table tbody tr");'
                ' var td = document.querySelector('
                '   ".lines-table tbody td[data-label]");'
                ' return {hidden: b ? Math.max(0,'
                '   b.scrollWidth - b.clientWidth) : -1,'
                '  tall: tr ? Math.round(tr.getBoundingClientRect().height)'
                '   : -1,'
                '  disp: td ? getComputedStyle(td).display : "",'
                '  label: td ? getComputedStyle(td, "::before").content'
                '   : ""}; }')
            ctx.close()
            br.close()
            return out
        finally:
            pw.stop()

    wide = measure(fx_now, 1100)
    phone = measure(fx_now, 390)
    ctl = measure(fx_was, 390)

    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it, every time', len(refused) == 3,
          '%d refused' % len(refused))
    check('on a desktop it is still a grid - nothing hidden',
          wide['hidden'] == 0, '%s px hidden' % wide['hidden'])
    check('  and its cells are still table cells',
          wide['disp'] in ('table-cell', 'block') and wide['disp'] != 'block'
          or wide['disp'] == 'table-cell', wide['disp'])
    check('on a phone NOTHING sits outside the box', phone['hidden'] == 0,
          '%s px hidden' % phone['hidden'])
    check('  because each cell became a block', phone['disp'] == 'block',
          phone['disp'])
    check('  and each one draws its own column name',
          'Service' in (phone['label'] or ''), phone['label'])
    check('  which costs height, and that was the trade he chose',
          phone['tall'] > wide['tall'] * 2,
          '%s px against %s' % (phone['tall'], wide['tall']))
    check('CONTROL: the SAME markup under the old page CSS still hides a '
          'third of itself at 390px', ctl['hidden'] > 300,
          '%s px hidden' % ctl['hidden'])
    print('        Without that control this section would pass on a')
    print('        browser default and say nothing about the round.')

# ---------------------------------------------------------------------- 6
head('6. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
print('')
print('  NOT PROVED HERE: that stacking is the right answer for a')
print('  line grid on a phone. It was chosen from two renders,')
print('  knowing it costs height. This holds the system to it.')
sys.exit(1 if FAIL else 0)
