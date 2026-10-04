# -*- coding: utf-8 -*-
"""test_filter_grid.py - Section FG round FG-1, 3 Oct 2026.

Demetri, of the filters going into the Recipes module: "The filter fields
must be made less wide, so that they fit on one line."

Measuring every filter panel in the tree to find which one he meant found
that ingredient_base_units_management - shipped yesterday as IB-1 -
rendered its two fields STACKED, each 1888px wide at a 1920 screen.

base's .filter-grid declared `display: grid` and no grid-template-columns.
A grid with no columns is a grid with ONE column. It worked anyway for a
year because all twelve pages using it set their own; the first page that
did not got a stacked panel.

SECTION 3 IS THE ONE THAT MATTERS. A default in base is a change to every
page that does NOT override it, and "only one page overrides nothing" is a
claim about a cascade. So the suite counts the pages, renders all of them
under the old base CSS and the new, and fails if any page that sets its
own columns moves by a single pixel. An argument about specificity is not
evidence; the cascade, run, is.

AND SECTION 2 IS THE TOKEN TEST, which cost this round two goes. A class
is a token, not a substring, and `\\b` IS NOT A TOKEN BOUNDARY WHEN THE
NEIGHBOUR IS A HYPHEN: r'\\bfilter-grid\\b' matches
class="passport-filter-grid". The first gate reported this round moving
three pages instead of one.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_filtergrid'
ME = 'test_filter_grid.py'
PATCHER = 'apply_filter_grid.py'
PS1 = 'Push-PendingChanges.ps1'
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
CAP, FLOOR = 240, 200
# The one page in the tree that relies on base for its columns.
THE_ONE = 'ingredient_base_units_management.html'

SCRATCH = tempfile.mkdtemp(prefix='alv_fgrid_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def nocomment(t):
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def classes_of(src):
    """Every class TOKEN in the markup. Not a substring search: \\b sits
    happily between '-' and 'f', so r'\\bfilter-grid\\b' matches
    class="passport-filter-grid" and this round was reported as moving
    three pages instead of one."""
    out = set()
    for m in re.finditer(r'class="([^"]*)"', src):
        out.update(m.group(1).split())
    return out


def sets_columns(css):
    """Rules whose SELECTOR carries the token .filter-grid and which set
    grid-template-columns. Same token rule on the CSS side:
    .recipe-filter-grid is not .filter-grid."""
    n = 0
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', nocomment(css)):
        if (re.search(r'\.filter-grid(?![-\w])', m.group(1))
                and 'grid-template-columns' in m.group(2)):
            n += 1
    return n


BASEP = alv_tree.path_of('base.html')
NOW = now(BASEP)
WAS = was(BASEP)

print('=' * 74)
print('%s - FG-1, .filter-grid DECLARES ITS COLUMNS' % ME)
print('=' * 74)

# ==========================================================================
head('1. base DECLARES THE TRACK LIST')
# ==========================================================================
bcss = nocomment(css_of(NOW))
ok('repeat(auto-fit, minmax(%dpx, %dpx))' % (FLOOR, CAP) in bcss,
   'base sets repeat(auto-fit, minmax(%dpx, %dpx))' % (FLOOR, CAP))
ok('justify-content: start' in bcss,
   'and packs the row from the left - without it the slack is shared '
   'BETWEEN the tracks and two fields sit at opposite ends of the panel')
ok(sets_columns(css_of(NOW)) >= 2,
   'two rules set columns: the default and the phone override',
   sets_columns(css_of(NOW)))
m = re.search(r'@media[^{]*max-width:\s*768px[^{]*\{(.*?\.filter-grid'
              r'\s*\{[^}]*\})', nocomment(css_of(NOW)), re.S)
ok(bool(m) and '1fr' in (m.group(1) if m else ''),
   'and a phone gets one full-width column - a 240px cap on a 358px '
   'screen would leave a third of it empty')

if WAS:
    ok(sets_columns(css_of(WAS)) == 0,
       'CONTROL: base really did declare a grid with no columns at all')
    ok('display: grid' in nocomment(css_of(WAS)),
       '  it was a grid, so every child stacked and filled the one track')
else:
    skip('the no-columns control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. WHO USES IT - BY TOKEN, NOT BY SUBSTRING')
# ==========================================================================
users, own = [], []
for rel in sorted(alv_tree.templates()):
    src = read(alv_tree.path_of(rel))
    if 'filter-grid' not in classes_of(src):
        continue
    users.append(rel)
    if sets_columns(css_of(src)):
        own.append(rel)

ok(len(users) >= 10, '%d templates wear class="filter-grid"' % len(users))
# WHO RELIES ON base. When FG-1 was written this was ONE page - the
# broken one - and the gate said so. FL-1 and UC-2 then built three more
# panels in the same module that deliberately set no columns of their
# own, which is the whole point of putting the default in base. So the
# claim is no longer "exactly one"; it is "every page relying on base is
# one this programme owns, and no other page moved" - and the second half
# is what section 3 renders.
moved = sorted(os.path.basename(p) for p in users if p not in own)
OURS = sorted(['ingredient_base_units_management.html',
               'categories_management.html',
               'measurement_units_management.html',
               'unit_conversions_management.html',
               # PA-1, 3 Oct 2026. Passports joined. It was on the list
               # below as a page that LOOKS like a user and is not - its
               # class was .passport-filter-grid, and matching that as
               # .filter-grid is the error this round was written around.
               # It is a real user now, and its four fields went from
               # 285px to the 240px cap.
               'passport_management.html'])
ok(moved == OURS,
   'the %d pages relying on base for their columns are the four Recipes '
   'panels, and nothing else' % len(moved),
   'got %s\nwant %s' % (moved, OURS))
ok(THE_ONE in moved,
   '  including %s, the page measured as stacked before this round'
   % THE_ONE)

# The two that LOOK like users and are not. Named, so that a page which
# genuinely starts using .filter-grid is noticed rather than absorbed.
# passport_management.html WAS HERE until PA-1, 3 Oct 2026. The token
# lesson it was here for still stands and is tested on recipe_management,
# which keeps .filter-multiselect-menu and friends.
for other in ('recipe_management.html',):
    src = read(alv_tree.path_of(other))
    ok('filter-grid' not in classes_of(src),
       '%s has its own grid class and is NOT a user of this one' % other)
    ok('filter-grid' in src,
       '  (its name contains the string, which is why the token test '
       'matters here)')

# ==========================================================================
head('3. WHAT IT MOVES - RENDERED, NOT ARGUED')
# ==========================================================================
# A default in base changes every page that does not override it, and
# "only one page overrides nothing" is a claim about a cascade. So every
# user is rendered under the OLD base CSS and the NEW, and any page that
# sets its own columns must come out identical to the pixel.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the before/after render of every user', 'playwright not installed')

FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''
IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', re.S)
IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
FOR = re.compile(r'\{%\s*for\b.*?%\}(.*?)\{%\s*endfor\s*%\}', re.S)
ANYT = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)


def resolve(h):
    for pat in (IF_ELSE, IF_ONLY, FOR):
        prev = None
        while prev != h:
            prev = h
            h = pat.sub(lambda mm: mm.group(1), h)
    return ANYT.sub('', h)


def panel_of(src):
    i = -1
    for m2 in re.finditer(r'class="([^"]*)"', src):
        if 'alv-filter' in m2.group(1).split():
            i = m2.start()
            break
    if i < 0:
        return None
    i = src.rindex('<div', 0, i)
    depth, j = 0, i
    tag = re.compile(r'</?div\b')
    while True:
        m2 = tag.search(src, j)
        if not m2:
            return None
        depth += 1 if src[m2.start():m2.start() + 2] == '<d' else -1
        j = m2.end()
        if depth == 0:
            break
    j = src.index('>', j - 1) + 1
    return resolve(src[i:j]).replace('class="alv-filter',
                                     'class="is-open alv-filter')


PROBE = """() => {
  const g = document.querySelector('.filter-grid');
  if (!g) return null;
  const k = [...g.children];
  /* BOTTOM, NOT TOP - .filter-grid sets align-items: end, so two groups
     of different heights on the SAME row have different tops and the
     same bottom. Counting tops reported two rows for panels the browser
     had laid out on one, which sent this round looking for a wrap that
     was not there. */
  const b = new Set(k.map(e => Math.round(e.getBoundingClientRect().bottom)));
  return {rows: b.size, n: k.length, widest: Math.max(...k.map(e => {
    const c = e.querySelector('input,select,textarea');
    return c ? Math.round(c.getBoundingClientRect().width) : 0;
  }))};
}"""

if sync_playwright is not None and FIX and WAS:
    bnow, bwas = css_of(NOW), css_of(WAS)
    drifted, unslicable, shown = [], [], None
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def measure(page_css, html, basecss, w):
            doc = ('<!doctype html><meta charset=utf-8>'
                   '<style>%s</style><style>%s</style><style>%s</style>'
                   '<style>body{margin:0;padding:16px}</style><body>%s'
                   % (FIX, basecss, page_css, html))
            pg.set_viewport_size({'width': w, 'height': 600})
            pg.set_content(doc, wait_until='domcontentloaded')
            return pg.evaluate(PROBE)

        for rel in users:
            src = read(alv_tree.path_of(rel))
            html = panel_of(src)
            if not html:
                # AN UNMEASURED PAGE IS NOT AN UNMOVED ONE.
                unslicable.append(rel)
                continue
            pcss = css_of(src)
            for w in (1920, 1280, 390):
                a = measure(pcss, html, bwas, w)
                b = measure(pcss, html, bnow, w)
                if rel in own:
                    # FA-1, 4 Oct 2026 - Projects is the exception now.
                    # Demetri, asked whether Search should stay wider
                    # than the two selects: "No - all three the same."
                    # It dropped its 2fr 1fr 1fr and takes base's capped
                    # track list, so it moves at 1920 and 1280 and this
                    # check would be asserting the opposite of what was
                    # asked for. NAMED, not loosened: every other page
                    # on that list is still held to the byte.
                    if 'projects' in os.path.basename(rel):
                        continue
                    if a != b:
                        drifted.append('%s @%d  %s -> %s'
                                       % (os.path.basename(rel), w, a, b))
                elif w == 1920 and THE_ONE in rel:
                    # ONLY THE PAGE THAT EXISTED BEFORE THIS ROUND has a
                    # meaningful before-state; the three panels FL-1 and
                    # UC-2 built did not exist when the old base CSS did.
                    shown = (a, b)
        br.close()

    ok(not unslicable,
       'every one of the %d panels could be measured' % len(users),
       '\n'.join(os.path.basename(p) for p in unslicable))
    ok(not drifted,
       'all %d pages that set their own columns are IDENTICAL before and '
       'after, at 1920, 1280 and 390' % len(own),
       '\n'.join(drifted[:6]))
    if shown:
        a, b = shown
        ok(a['rows'] > b['rows'] or a['widest'] > b['widest'],
           '%s changed: %d row(s) at %dpx wide -> %d row(s) at %dpx'
           % (THE_ONE, a['rows'], a['widest'], b['rows'], b['widest']))
        ok(b['rows'] == 1,
           '  its fields are on ONE line now, which is what was asked',
           b)
        ok(b['widest'] <= CAP,
           '  and none of them is wider than %dpx' % CAP, b['widest'])
        ok(a['widest'] > 1000,
           '  CONTROL: before this round the widest was %dpx' % a['widest'])
else:
    skip('the before/after render of every user',
         'no browser, fixture or backup')

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
ok(len(rows) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(p)
    if r.get('Code'):
        b2 = _strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
