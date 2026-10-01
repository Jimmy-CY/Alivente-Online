# -*- coding: utf-8 -*-
"""test_analysis_order.py - Section E round E1, 1 Oct 2026.

Demetri: "Analysis Report does not load." It had not loaded since 23 Sep.

    TypeError: Cannot read properties of undefined (reading
               'getPropertyValue')

act_expense.html's analysis IIFE mapped the chart's series colours
through anTok() at line 1903. anTok read AN_CS, and AN_CS was not
assigned until line 1975. `var` hoists the NAME, not the VALUE - so
AN_CS was undefined, the call threw, and the IIFE died seventy lines
before the click handler that starts the fetch. Clicking Analysis opened
the modal onto its static "Loading..." markup and left it there. The
.catch that would have said "Failed to load analysis" never ran either,
because no fetch was ever made.

The D5 series-scale round put the SERIES block above the definitions it
depends on. The backup taken just before it has no anTok call at all;
every backup after it has the call above the assignment.

SECTION 3 IS THE CLAIM, and it is a browser rather than a reading,
because "the definition is above the use" is not the same statement as
"the page's JavaScript runs". Measured, on the page's own IIFE:

    before   pageerror: TypeError ...getPropertyValue
             click -> fetch NEVER called, #analysisLoading still block
    after    pageerror: none
             click -> fetch called once, #analysisLoading display:none,
                      the empty branch reached display:block

window.fetch is replaced IN THE PAGE rather than intercepted by the
browser. The first version of this suite used Playwright's route(), which
passed here and failed on Demetri's laptop - whether route() catches a
file:// fetch is a property of the Playwright build, not of the round.
The suite was reporting its own environment and calling it the page.

SECTION 5 IS THE GATE THAT WAS MISSING. Three templates cache
getComputedStyle in a var and read it from a helper. Two were always in
the right order; this one was not, and nothing was watching. The scan is
tree-wide so a fourth cannot arrive unnoticed.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_analysisorder'
ME = 'test_analysis_order.py'
PATCHER = 'apply_analysis_order.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'act_expense.html'
EXE = '/opt/pw-browsers/chromium'

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


PATH = alv_tree.path_of(PAGE)
now = (as_left_by(PATH, SUFFIX, read) if as_left_by else read(PATH))
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else None

print('=' * 74)
print('%s - E1, THE ANALYSIS REPORT LOADS AGAIN' % ME)
print('=' * 74)


def analysis_iife(src):
    """The IIFE that owns ANALYSIS_URL, with Django tags neutered so it
    is runnable. The SUITE DOES NOT REWRITE THE LOGIC - it lifts the
    page's own code and runs it, because a reimplementation would be
    testing the reimplementation."""
    k = src.find('ANALYSIS_URL')
    if k < 0:
        return None
    i = src.rfind('(function', 0, k)
    d, j = 0, i
    while j < len(src):
        if src[j] == '{':
            d += 1
        elif src[j] == '}':
            d -= 1
            if d == 0:
                j = src.find(';', j) + 1
                break
        j += 1
    s = src[i:j]
    s = re.sub(r"\{%\s*url\s+'[^']+'\s*%\}", '/analysis-data/', s)
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    s = re.sub(r'\{\{.*?\}\}', '""', s, flags=re.S)
    return s


# ==========================================================================
head('1. THE DEFINITION IS ABOVE ITS FIRST USE')
# ==========================================================================
blocks = [(m.start(1), m.group(1))
          for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', now, re.S)]
found = False
for base, js in blocks:
    a = js.find('var AN_CS')
    c = js.find("anTok('series-")
    if a < 0 or c < 0:
        continue
    found = True
    la = now[:base + a].count('\n') + 1
    lc = now[:base + c].count('\n') + 1
    ok(a < c, 'AN_CS is declared (line %d) before anTok() is called '
              '(line %d)' % (la, lc),
       'the declaration is still BELOW the call')
ok(found, 'the analysis block is where this suite expects it')

# ==========================================================================
head('2. AND IT READS LAZILY, SO RE-ORDERING CANNOT BREAK IT AGAIN')
# ==========================================================================
# Moving the block fixes today. Reading lazily is what stops the next
# person who inserts code above it from doing this a second time.
m = re.search(r'function anTok\([^)]*\)\s*\{(.*?)\n    \}', now, re.S)
body = m.group(1) if m else ''
ok(bool(m), 'anTok is still a single function')
ok('getComputedStyle' in body,
   '  and it reads getComputedStyle INSIDE itself, not at module scope')
ok('var AN_CS = null;' in now,
   '  so AN_CS starts null and is filled on first use')
ok(now.count('var AN_CS') == 1 and now.count('function anTok') == 1,
   '  and there is exactly one of each')

# ==========================================================================
head('3. THE PAGE\'S OWN IIFE, RUN IN CHROMIUM')
# ==========================================================================
# THE FETCH IS STUBBED IN THE PAGE, NOT INTERCEPTED BY THE BROWSER.
#
# The first version of this suite stubbed the endpoint with Playwright's
# route() and passed here - then FAILED on Demetri's laptop with
# "#analysisLoading is still block". A fetch from a file:// page resolves
# to file:///analysis-data/, and whether route() intercepts that is a
# property of the Playwright build, not of the round. So the suite was
# reporting the test environment and calling it the page.
#
# Replacing window.fetch before the IIFE runs removes the network from
# the question entirely. It is also a STRONGER check: the stub records
# that fetch was called, so the suite can say the handler ran rather
# than inferring it from a div that moved.
STUB = (
    '<script>window.__fetched = [];'
    'window.fetch = function (u, o) {'
    '  window.__fetched.push(String(u));'
    '  return Promise.resolve({ ok: true, status: 200,'
    '    json: function () { return Promise.resolve('
    '      {"properties": [], "available_years": []}); } });'
    '};</script>')
FIXTURE = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<style>:root{--alv-series-1:#eb6834;--alv-bad:#b3261e;'
    '--alv-warn:#8e6207;--alv-good:#1e7d4f}</style></head><body>'
    '<button id="go" data-target="#expenseAnalysisModal">Analysis</button>'
    '<div id="analysisLoading">Loading...</div>'
    '<div id="analysisEmpty" style="display:none"></div>'
    '<div id="analysisContent" style="display:none"></div>'
    + STUB +
    '<script src="%s"></script></body></html>')


def run_iife(js, tag):
    """Load the IIFE, click Analysis, and report what the browser did."""
    from playwright.sync_api import sync_playwright
    d = os.path.join(SCRATCH, tag)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'iife.js'), 'w', encoding='utf-8') as fh:
        fh.write(js)
    page = os.path.join(d, 't.html')
    with open(page, 'w', encoding='utf-8') as fh:
        fh.write(FIXTURE % 'iife.js')
    errs = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        _goto(pg, page)
        pg.wait_for_timeout(200)
        load_errs = list(errs)
        pg.click('#go')
        pg.wait_for_timeout(600)
        disp = dict((s, pg.eval_on_selector(
            s, 'e => getComputedStyle(e).display'))
            for s in ('#analysisLoading', '#analysisEmpty'))
        disp['fetched'] = pg.evaluate('() => window.__fetched || []')
        br.close()
    return load_errs, disp


try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

js_now = analysis_iife(now)
if not have_pw:
    skip('the IIFE in a browser', 'playwright is not installed')
elif not js_now:
    ok(False, 'the analysis IIFE could be lifted out of the page')
else:
    errs, disp = run_iife(js_now, 'after')
    ok(not errs, 'the page\'s JavaScript loads without throwing', errs)
    # THE HANDLER RAN - said by the stub recording the call, not guessed
    # from a div that moved.
    ok(len(disp['fetched']) == 1,
       '  and clicking Analysis calls fetch exactly once',
       'it called it %d time(s): %s'
       % (len(disp['fetched']), disp['fetched']))
    if disp['fetched']:
        print('       it fetched %s' % disp['fetched'][0])
    ok(disp['#analysisLoading'] == 'none',
       '  the Loading state is left',
       'it is still %s' % disp['#analysisLoading'])
    ok(disp['#analysisEmpty'] == 'block',
       '  and the branch that answers is reached',
       'the empty branch is %s' % disp['#analysisEmpty'])

# ==========================================================================
head('4. THE CONTROL - THE OLD ORDER MUST STILL BE BROKEN')
# ==========================================================================
# A check that cannot fail is not a check. This is the page as the
# backup left it: the same IIFE with the definition below the use.
if not have_pw:
    skip('the control', 'playwright is not installed')
elif was is None:
    skip('the control', 'no %s backup to compare against' % SUFFIX)
else:
    js_was = analysis_iife(was)
    if not js_was:
        skip('the control', 'the backup has no analysis IIFE')
    else:
        errs0, disp0 = run_iife(js_was, 'before')
        ok(bool(errs0),
           'the backup really did throw on load - this is not a tautology',
           'it loaded cleanly, so the bug was somewhere else')
        if errs0:
            print('       %s' % errs0[0][:110])
        ok('getPropertyValue' in ' '.join(errs0),
           '  and it threw on getPropertyValue, which is the bug named here',
           errs0)
        ok(disp0['#analysisLoading'] != 'none',
           '  and Loading stayed on screen, which is what Demetri saw',
           'it was %s' % disp0['#analysisLoading'])
        ok(not disp0['fetched'],
           '  because it never even reached fetch - the IIFE died first',
           'it fetched %s' % disp0['fetched'])

# ==========================================================================
head('5. THE GATE THAT WAS MISSING - TREE-WIDE')
# ==========================================================================
# Nothing was watching for a page whose JavaScript throws on load. This
# is the narrow version of that: a getComputedStyle cached in a var, read
# by a helper, and the helper called before the var is assigned.
bad, seen = [], []
for q in alv_tree.templates():
    src = read(q)
    for sm in re.finditer(r'<script\b[^>]*>(.*?)</script>', src, re.S):
        js, base = sm.group(1), sm.start(1)
        for am in re.finditer(r'var\s+(\w+)\s*=\s*getComputedStyle\(', js):
            var = am.group(1)
            hm = re.search(r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\b'
                           + var + r'\b', js)
            if not hm:
                continue
            helper = hm.group(1)
            calls = [m.start() for m in re.finditer(r'\b' + helper + r'\s*\(',
                                                    js)
                     if not (hm.start() <= m.start() <= hm.end())]
            if not calls:
                continue
            rel = alv_tree.rel(q)
            seen.append((rel, var, helper))
            if min(calls) < am.start():
                bad.append('%s: %s() is called before %s is assigned'
                           % (rel, helper, var))
ok(not bad, 'no template calls a token helper before its cache is assigned',
   '\n'.join(bad))
print('       %d eager cache(s) of this shape in the tree:' % len(seen))
for rel, var, helper in seen:
    print('         %-42s %s via %s()' % (rel, var, helper))
print('')
print('       act_expense.html is NOT in that list, and that is the point:')
print('       its cache is lazy now, so there is no order to get wrong.')
print('       Section 2 is what holds it to that. If anyone changes it')
print('       back to an eager read, it rejoins this list and the order')
print('       is checked again.')
ok('var AN_CS = null;' in now,
   '  and the page this round fixed is lazy, so it cannot rejoin the list '
   'by accident')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(os.path.isfile(PATH + SUFFIX),
   'the round left its backup beside the page')

print('')
print('  NOT PROVED HERE: that the chart draws the right picture. This')
print('  suite proves the code RUNS and the fetch happens. What the')
print('  analysis says about a property is the view\'s business, and')
print('  Demetri is the one who can say whether it reads true.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
