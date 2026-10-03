# -*- coding: utf-8 -*-
"""test_fixed_popup.py - Section PU round PU-1, 2 Oct 2026.

Demetri, with screenshots of Categories Management and Measurement Units:
"the list of ingredients cuts off. Please investigate."

TWO CORRECT DECISIONS COLLIDING, not a mistake in either. The list popup
was `position: absolute` growing upward from its trigger, inside
`.table-container`, and base sets that container `overflow: clip` ON
PURPOSE so a sticky heading has something to stick to (base records the
measurement: 615px above the viewport with `hidden`, top:0 with `clip`).
An absolutely-positioned child is POSITIONED by its nearest positioned
ancestor but CLIPPED by any ancestor that clips.

SECTION 3 IS THE ROUND, AND IT NEEDS A BROWSER. Whether a popup is cut off
cannot be read from a stylesheet: it depends on where the trigger lands,
how tall the list is and where the container's edge falls. So section 3
builds the real table from the template's own markup, CLICKS the trigger -
so each version's own code decides where the popup goes - and measures what
the browser actually painted.

    before   popup top -49px, container top 112px   161px of it cut off
    after    popup top 209px                        none

SECTION 2 IS WHY IT WENT IN base. The two pages carried the same component
under two names - .ingredient-popup and .usage-popup - byte for byte
identical. Fixing the bug twice would have left two copies of the fix, so
this suite asserts there is ONE component and that no page in either root
still carries an absolutely-positioned popup of its own.

WHAT THIS SUITE CANNOT DO. It cannot tell you the list is correct - that is
a fact about the database. It asserts the popup escapes the container, that
it flips when there is no room, and that one component serves both pages.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_fixedpop'
ME = 'test_fixed_popup.py'
PATCHER = 'apply_fixed_popup.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
PAGES = ('categories_management.html', 'measurement_units_management.html')
OLD_NAMES = ('ingredient-popup', 'usage-popup',
             'toggleIngredientPopup', 'toggleUsagePopup', 'popupFadeIn')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

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


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def rule(text, selector):
    m = re.search(r'(?m)^[ \t]*' + re.escape(selector) + r'\s*\{', text)
    if not m:
        return None
    return text[m.start():text.index('}', m.end()) + 1]


BASE = alv_tree.path_of('base.html')
B = code_only(now(BASE))

print('=' * 74)
print('%s - PU-1, THE POPUP LEAVES THE CONTAINER' % ME)
print('=' * 74)

# ==========================================================================
head('1. ONE COMPONENT, AND IT IS FIXED')
# ==========================================================================
for sel in ('.alv-pop-trigger', '.alv-pop', '.alv-pop::after',
            '.alv-pop--below::after', '.alv-pop-list'):
    ok(rule(B, sel) is not None, 'base defines %s' % sel)

POP = rule(B, '.alv-pop') or ''
ok('position: fixed' in POP,
   'and .alv-pop is FIXED - positioned against the viewport, so no '
   'ancestor overflow can reach it')
ok('position: absolute' not in POP, '  and not absolute any more')

# THE OTHER HALF OF THE COLLISION IS STILL TRUE. If the container stopped
# clipping, this round would be solving a problem that no longer exists -
# and that is worth being told rather than quietly passing.
TC = rule(B, '.table-container') or ''
ok('overflow: clip' in TC,
   '.table-container still clips - which is WHY the popup had to leave it',
   TC[:120])

# THE SCRIPT. Measured on open, flips, dismissed by scrolling.
JS = '\n'.join(m.group(1) for m in SCRIPT.finditer(now(BASE))
               if 'alv-pop' in m.group(1))
ok(bool(JS), 'base carries the alv-pop script')
for frag, what in (('getBoundingClientRect', 'it measures the trigger on open'),
                   ("classList.add('alv-pop--below')",
                    'and flips below when there is no room above'),
                   ("addEventListener('scroll'",
                    'scrolling dismisses it'),

                   ("e.key === 'Escape'", 'and Escape does too')):
    ok(frag in JS, what)
LIVE_JS = '\n'.join(
    m.group(1) for m in
    re.finditer(r'<script\b[^>]*>(.*?)</script\s*>',
                read(alv_tree.path_of('base.html')), re.S)
    if 'alv-pop' in m.group(1))
ok("closest('.alv-pop')" in LIVE_JS,
   'but a scroll that STARTS INSIDE the popup does NOT close it  [PU-1b]')
ok(', true)' in LIVE_JS,
   '  and capture is kept, or a page scroll inside a container would not '
   'dismiss it at all')

ok('clientWidth' in JS,
   'and it is kept on screen horizontally - a trigger in the last column '
   'would otherwise push half the list past the edge')

# ==========================================================================
head('2. NEITHER PAGE KEEPS A COPY')
# ==========================================================================
for rel in PAGES:
    p = alv_tree.path_of(rel)
    t = code_only(now(p))
    for dead in OLD_NAMES:
        n = len(re.findall(r'\b%s\b' % re.escape(dead), t))
        ok(n == 0, '%-34s %r is gone' % (rel, dead), 'still %d' % n)
    ok(rule(t, '.alv-pop') is None,
       '%-34s does not redefine .alv-pop - base owns it' % rel)
    for need in ('alv-pop-trigger', 'alv-pop-list'):
        ok(need in t, '%-34s uses .%s' % (rel, need))

    w = was(p)
    if w:
        wc = code_only(w)
        ok(any(d in wc for d in OLD_NAMES),
           '%-34s CONTROL: it really carried its own copy' % rel)
        ok('position: absolute' in (rule(wc, '.ingredient-popup')
                                    or rule(wc, '.usage-popup') or ''),
           '%-34s   and that copy really was absolute' % rel)
    else:
        skip('%s control' % rel, 'no %s backup' % SUFFIX)

# THE TWO COPIES WERE THE SAME THING. The argument for one component, kept
# on file - if they had drifted, merging them would have picked one page's
# answer for both.
wa = code_only(was(alv_tree.path_of(PAGES[0])))
wb = code_only(was(alv_tree.path_of(PAGES[1])))
if wa and wb:
    ra, rb = rule(wa, '.ingredient-popup'), rule(wb, '.usage-popup')
    norm = lambda s: re.sub(r'\s+', ' ', s.split('{', 1)[1]).strip() if s \
        else None
    ok(ra and rb and norm(ra) == norm(rb),
       'CONTROL: the two copies were byte-identical - one component under '
       'two names, which is why this went to base rather than being fixed '
       'twice')
else:
    skip('the identical-copies control', 'no %s backups' % SUFFIX)

# AND NO THIRD PAGE CARRIES THE OLD SHAPE.
strays = []
for p in alv_tree.templates():
    if os.path.basename(p) == 'base.html':
        continue
    t = code_only(read(p))
    for m in re.finditer(r'(?m)^[ \t]*\.([\w-]*popup[\w-]*)\s*\{([^}]*)\}', t):
        if 'position: absolute' in m.group(2):
            strays.append('%s  .%s' % (alv_tree.rel(p), m.group(1)))
ok(not strays, 'no page in either root carries an absolute popup of its own',
   '\n'.join(strays[:6]))

# ==========================================================================
head('3. DRIVEN FOR REAL - THE POPUP IS CLICKED, AND MEASURED')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    have_pw = True
except Exception as e:
    have_pw = False
    skip('the rendered popup', 'playwright: %s' % str(e)[:60])

if have_pw:
    PAGE = alv_tree.path_of(PAGES[0])
    ITEMS = ['Butter, unsalted', 'Cream, double', 'Feta', 'Halloumi',
             'Milk, full fat', 'Yoghurt, Greek']

    def styles_of(t):
        return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                         for m in STYLE.finditer(t))

    def cell_of(src):
        m0 = re.search(r'<span[^>]*class="[^"]*'
                       r'(?:popup-trigger|alv-pop-trigger)', src)
        if not m0:
            return ''
        seg = src[m0.start():src.find('</td>', m0.start())]
        seg = re.sub(r'\{#.*?#\}', '', seg, flags=re.S)
        m = re.search(r'\{%\s*if ([\w.]+)\s*%\}(.*?)\{%\s*else\s*%\}(.*?)'
                      r'\{%\s*endif\s*%\}', seg, re.S)
        if m:
            seg = seg[:m.start()] + m.group(2) + seg[m.end():]
        m = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}(.*?)'
                      r'\{%\s*endfor\s*%\}', seg, re.S)
        if m:
            var, body = m.group(1), m.group(3)
            seg = seg[:m.start()] + ''.join(
                re.sub(r'\{\{\s*%s[\w.]*\s*\}\}' % re.escape(var), it, body)
                for it in ITEMS) + seg[m.end():]
        seg = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', '', seg, flags=re.S)
        return seg

    def fixture(src, name):
        cell = cell_of(src)
        if not cell:
            return None
        # DJANGO TAGS OUT OF THE SCRIPT. The old page's popup block carries
        # {% if %} and {{ }} inside <script>, which Django resolves before
        # the browser ever sees it. Left in, the whole block is a
        # JavaScript SyntaxError and toggleIngredientPopup is never
        # defined - so the control clicked a trigger with no handler and
        # reported that the old popup "did not open", which would have read
        # as the bug being absent.
        _clean = lambda x: re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', x,
                                  flags=re.S)
        js = '\n'.join(_clean(m.group(1)) for m in SCRIPT.finditer(src)
                       if 'Popup' in m.group(1))
        if not js:
            js = '\n'.join(
                m.group(1) for m in SCRIPT.finditer(
                    read(alv_tree.path_of('base.html')), )
                if 'alv-pop' in m.group(1))
        rows = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (c, cell)
                       for c in ('Dairy', 'Meat', 'Produce', 'Store'))
        boot = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '<style>.fas,.far{display:inline-block;width:14px;'
                'height:14px}*{animation:none!important;'
                'transition:none!important}</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar"><h2 class="page-title-h2">X</h2>'
                '<div class="table-container"><table class="table '
                'alv-table"><thead><tr><th>Category</th><th>Ingredients'
                '</th></tr></thead><tbody>%s</tbody></table></div>'
                '</div><script>%s</script></body></html>'
                % (read(boot) if os.path.isfile(boot) else '',
                   styles_of(now(BASE)), styles_of(src), rows, js))
        f = os.path.join(SCRATCH, name)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(html)
        return f

    fx_now = fixture(now(PAGE), 'pu1_now.html')
    fx_was = fixture(was(PAGE), 'pu1_was.html') if was(PAGE) else None

    if not ok(bool(fx_now), 'the fixture builds from the template'):
        pass
    else:
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            ctx = br.new_context(viewport={'width': 1180, 'height': 620})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()

            def open_top(f):
                """Click the FIRST row's trigger - the worst case, because
                the popup grows upward and the container's edge is just
                above it."""
                _goto(pg, f)
                tr = pg.query_selector_all(
                    '.alv-pop-trigger, .ingredient-popup-trigger')
                if not tr:
                    return None
                tr[0].click()
                pg.wait_for_timeout(120)
                pop = pg.query_selector('.alv-pop.show, '
                                        '.ingredient-popup.show')
                if not pop:
                    return None
                box = pop.bounding_box()
                cont = pg.query_selector('.table-container')
                cb = cont.bounding_box() if cont else None
                return {
                    'position': pg.evaluate(
                        '(e)=>getComputedStyle(e).position', pop),
                    'open': True,
                    'top': round(box['y']),
                    'cont': round(cb['y']) if cb else 0,
                    'items': len(pg.query_selector_all(
                        '.alv-pop.show li, .ingredient-popup.show li')),
                    'visible': pg.evaluate(
                        '(e)=>{var r=e.getBoundingClientRect();'
                        'return r.top>=0 && r.bottom<=innerHeight}', pop),
                }

            a = open_top(fx_now)
            if ok(bool(a), 'the popup opens when the trigger is clicked'):
                print('     after   %s' % a)
                ok(a['position'] == 'fixed',
                   'it is painted fixed, not absolute', a['position'])
                ok(a['top'] >= a['cont'],
                   'and it starts BELOW the container\'s top edge, so the '
                   'container cannot clip it',
                   'popup %dpx, container %dpx' % (a['top'], a['cont']))
                ok(a['visible'],
                   'the whole of it is inside the viewport')
                ok(a['items'] == len(ITEMS),
                   'and all %d items are in it' % len(ITEMS), a['items'])

            # PU-1b, 3 Oct 2026. Demetri, on Live: "I can't scroll
            # down the list. When I scroll the whole page scrolls down."
            # The listener was registered with CAPTURE, so a scroll inside
            # the popup - which is overflow-y: auto - counted as a page
            # scroll and closed it. The scrollbar was visible and unusable.
            #
            # Both halves are driven, because fixing one by breaking the
            # other would pass a suite that only checked one.
            pop = pg.query_selector('.alv-pop.show')
            if pop:
                pg.eval_on_selector(
                    '.alv-pop.show',
                    '(e)=>{e.scrollTop=20;e.dispatchEvent('
                    'new Event("scroll",{bubbles:true}));}')
                pg.wait_for_timeout(60)
                ok(bool(pg.query_selector('.alv-pop.show')),
                   'scrolling the LIST leaves it open  [PU-1b]')
                pg.evaluate('()=>{window.scrollTo(0,150);'
                            'window.dispatchEvent(new Event("scroll"));}')
                pg.wait_for_timeout(60)
                ok(not pg.query_selector('.alv-pop.show'),
                   '  CONTROL: and scrolling the PAGE still closes it')
            else:
                skip('the scroll behaviour', 'the popup was not open')

            if fx_was:
                b = open_top(fx_was)
                if ok(bool(b), 'CONTROL: the old popup opens too'):
                    print('     before  %s' % b)
                    ok(b['position'] == 'absolute',
                       '  and it really was absolute', b['position'])
                    ok(b['top'] < b['cont'],
                       '  and it really did start %dpx ABOVE the '
                       'container\'s edge - which is the cut-off Demetri '
                       'reported' % (b['cont'] - b['top']),
                       'popup %dpx, container %dpx' % (b['top'], b['cont']))
                    ok(not b['visible'],
                       '  and part of it was off screen entirely')
            else:
                skip('the before measurement', 'no %s backup' % SUFFIX)
            ctx.close()
            br.close()

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
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


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
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
