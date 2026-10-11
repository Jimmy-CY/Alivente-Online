# -*- coding: utf-8 -*-
"""test_held_four.py - round E-1a, 11 Oct 2026.

FOUR SUITES OFF WAITING, TWO DEAD RULES OUT, AND ONE BOX RESIZED.

    python test_held_four.py

Run from the repo root, after apply_held_four.py.

SECTION 3 IS THE ONE THAT WOULD HAVE CAUGHT THE WORST MISTAKE IN THIS
ROUND. The dead rule on view_recipe is written `}ecipe-header {` - the
brace belongs to the rule ABOVE it, because what was lost was `

.r`.
A pattern that matches from the brace and deletes its match closes
nothing and breaks every rule after it. The check measures that
.recipe-detail-container still has a closing brace and that the
stylesheet still balances.

SECTION 5 MEASURES THE BOX, because rows is not pixels. An attribute
says 14; what matters is whether the thing you type into got taller.
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

SUFFIX = '.bak_held4'
PATCHER = 'apply_held_four.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

RELEASED = ('test_req_marker.py', 'test_required_marker.py',
            'test_line_soft.py', 'test_subtree_tones.py')
REQ_PAGE = 'crs/submission_detail.html'
RECIPE = 'view_recipe.html'
FSR = 'fsr_details.html'
N_BOXES = 2
WAITING_AFTER = 8

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


print(__doc__.strip().split('\n')[0])

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
for n in RELEASED:
    check('  %s is still here' % n, os.path.isfile(os.path.join(ROOT, n)))

# ---------------------------------------------------------------------- 2
head('2. THE LAST .req RULE IN THE TREE IS GONE')

left = []
for p in alv_tree.templates():
    for m in re.finditer(r'[^{}]*(?<![-\w])\.req(?![-\w])[^{}]*\{',
                         css_of(read(p))):
        left.append('%s %s' % (alv_tree.rel(p), ' '.join(m.group(0).split())))
check('no .req rule survives anywhere', not left, '; '.join(left[:2]))

rp = alv_tree.path_of(REQ_PAGE)
check('  CONTROL: and the backup proves %s carried one' % REQ_PAGE,
      '.lifecycle-next-action .req' in before(rp))
mk = alv_tree.code_only(read(rp))
bare = [c for c in re.findall(r'class\s*=\s*"([^"]*)"', mk)
        if 'req' in c.split()]
check('  and nothing on that page carries a bare req class', not bare,
      '%d' % len(bare))
check('    CONTROL: alv-req IS there, so this is not an empty page',
      'alv-req' in mk)
print('        alv-req is base own asterisk and a different selector. The')
print('        rule asked for an element inside .lifecycle-next-action')
print('        that has never existed.')

# ---------------------------------------------------------------------- 3
head('3. DW-2 - THE CORPSE WENT AND THE BRACE ABOVE IT STAYED')

rec = alv_tree.path_of(RECIPE)
now = read(rec)
# NOT `'ecipe-header' not in now` - that substring is inside
# .recipe-header-content, which is alive and used, so the check would
# fail on a page where the round had worked perfectly. The corpse is
# identifiable by the brace it was glued to.
check('the ecipe-header corpse is gone', '}ecipe-header' not in now)
check('  CONTROL: and the backup proves it was there',
      '}ecipe-header' in before(rec))

# THE RULE THE BRACE BELONGED TO, not just any rule with that name -
# the page carries several, including
# `.recipe-detail-container > div:first-of-type` and a margin reset,
# either of which would satisfy a looser pattern while the one that
# mattered stayed broken.
owner = [b for s, b in re.findall(
    r'((?<![-\w])\.recipe-detail-container[^{}]*)\{([^{}]*)\}',
    css_of(now)) if 'max-width: 1200px' in b]
# There are TWO bare .recipe-detail-container rules - the desktop one
# and a max-width: 100% inside a phone block - so the body has to be
# named, not just the selector.
check('  the rule that brace closed is intact', len(owner) == 1,
      '%d candidate(s)' % len(owner))
if owner:
    check('    and still holds max-width and its auto margin',
          'max-width' in owner[0] and 'margin' in owner[0],
          ' '.join(owner[0].split())[:50])
c = css_of(now)
check('  the stylesheet still balances', c.count('{') == c.count('}'),
      '%d open, %d close' % (c.count('{'), c.count('}')))
check('  and the gradient the corpse duplicated is drawn by a selector '
      'that IS used',
      len(re.findall(r'\.recipe-header-content\s*\{', c)) >= 1
      and 'recipe-header-content' in alv_tree.code_only(now))
print('        What was lost was a newline pair and a .r, so the corpse was')
print('        glued to the closing brace of the rule above it. A pattern')
print('        that matched from that brace would have closed nothing.')

# ---------------------------------------------------------------------- 4
head('4. E-9 - THE BOX CM-1 NEVER RESIZED')

fp = alv_tree.path_of(FSR)
f_now, f_was = read(fp), before(fp)


def boxes(text, rows):
    return len(re.findall(
        r'<textarea(?=[^>]*maxlength="1000")[^>]*rows="%s"' % rows, text))


check('%d comment box(es) now say rows 14' % N_BOXES,
      boxes(f_now, 14) == N_BOXES, '%d' % boxes(f_now, 14))
check('  CONTROL: and the backup proves they said rows 4',
      boxes(f_was, 4) == N_BOXES, '%d' % boxes(f_was, 4))
check('  the 255-character description box is untouched at rows 3',
      'rows="3"' in f_now and 'rows="3"' in f_was)
print('        CM-1 raised what you can TYPE to 1000 characters and left')
print('        the box at four rows. This raises the box.')

# ---------------------------------------------------------------------- 5
head('5. MEASURED - ROWS IS NOT PIXELS')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    SKIP += 1
    print('  skip playwright is not installed here')
    sync_playwright = None

if sync_playwright is not None:
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    bcss = re.sub(r'\{%.*?%\}', '',
                  css_of(read(alv_tree.path_of('base.html'))), flags=re.S)
    refused = []

    def tall(rows):
        doc = ('<!doctype html><html><head><meta charset="utf-8">'
               '<link rel="stylesheet" href="https://example.invalid/x.css">'
               '<style>%s</style><style>%s</style></head><body>'
               '<textarea class="form-control" rows="%d"></textarea>'
               '</body></html>' % (boot, bcss, rows))
        fx = os.path.join(SCRATCH, 'e9_%d.html' % rows)
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(doc)
        pw = sync_playwright().start()
        try:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={'width': 800, 'height': 700})

            def _abort(route):
                refused.append(route.request.url)
                route.abort()

            ctx.route(re.compile(r'^https?://'), _abort)
            pg = ctx.new_page()
            _goto(pg, fx)
            pg.wait_for_timeout(110)
            h = pg.eval_on_selector(
                'textarea',
                'e => Math.round(e.getBoundingClientRect().height)')
            ctx.close()
            br.close()
            return h
        finally:
            pw.stop()

    four, fourteen = tall(4), tall(14)
    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it, both times', len(refused) == 2,
          '%d refused' % len(refused))
    check('the box really is taller: %dpx against %dpx' % (fourteen, four),
          fourteen > four * 2, '%d vs %d' % (fourteen, four))
    print('        An attribute saying 14 is not a taller box. This is.')

# ---------------------------------------------------------------------- 6
head('6. THE FOUR SUITES, WIDENED AND RELEASED')

for n in RELEASED:
    src = read(os.path.join(ROOT, n))
    check('  %s walks every root' % n,
          'alv_tree.walk3()' in src and 'os.walk(T)' not in src)
    joins = re.findall(r'os\.path\.join\(\s*T\s*,', src)
    check('    and resolves nothing through the one root it used to know',
          not joins, '%d join(s) left' % len(joins))
    check('    off alv_tree.WAITING', n not in alv_tree.WAITING)
    check('    on alv_tree.CONVERTED', n in alv_tree.CONVERTED)
print('        A DORMANT NARROW LOOKUP IS INVISIBLE UNTIL THE TREE WIDENS')
print('        UNDER IT. test_required_marker carried three, in three')
print('        different shapes, and each was found by the one after it.')

# E-1b, 11 Oct 2026 - WAS `len(WAITING) == WAITING_AFTER`, which
# was true for one round. What E-1a claims is that the FOUR IT RELEASED
# are off, and that is checked one by one above. The size of the
# register is not E-1a's to assert.
check('none of the four this round released is still held',
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)

# ---------------------------------------------------------------------- 7
head('7. REGISTERED, ON THE GATE')

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
print('  NOT PROVED HERE: that the four CRS literals test_line_soft')
print('  now counts should stay. They are named in that suite and')
print('  belong to a round that renders those three pages.')
sys.exit(1 if FAIL else 0)
