# -*- coding: utf-8 -*-
"""test_ae_line.py - Section AE rounds AE-1 and AE-3, 1 Oct 2026.

    AE-1  Demetri: "Fit Search, Property, Status, From and To on one
          line."
    AE-3  The drill-down Back: label to "Back", move it right, and hide
          the year selector while drilled down.

SECTION 3 NEEDS A BROWSER, AND THAT IS THE POINT OF THE ROUND.

The reported defect is a layout one and could almost be checked by
reading the CSS. The defect FOUND while fixing it cannot: .date-filter-
grid gave From and To 150px each, and a date input needs 165 - so both
have been clipping their own value at every desktop width, and at 162px
on a phone, for as long as that rule existed. A truncated date still
reads as a date. Nobody reported it and nobody could have.

So 165 is not typed in here as a constant either. Section 3 MEASURES it,
in whatever browser is running, by putting a date input carrying a real
value at width:auto and reading its intrinsic width back - and then
checks every control against that number at six widths. On a machine
whose fonts resolve differently the requirement moves and the check moves
with it. test_filter_gap learned this the hard way three days ago, when a
figure recorded in this sandbox was two pixels different on Demetri's
laptop and failed a push that was not wrong.

SECTION 4 IS THE TRAP, AND IT IS NOT COSMETIC. Every checkbox in the
years bar calls loadData(), and loadData() calls showOverview() - so
touching a year while reading one property's expenses threw you out to
the overview. That is read out of the page's own script rather than
asserted, because if the wiring ever changes the reason to hide the bar
changes with it.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_aeline'
ME = 'test_ae_line.py'
PATCHER = 'apply_ae_line.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

PAGE = alv_tree.path_of('act_expense.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# The column template AE-1 settled on, and the band below it. Read off
# the patcher so the two cannot drift - the suite and the round have to
# be measuring the same thing or they are only agreeing with each other.
_pat = open(os.path.join(ROOT, PATCHER), encoding='utf-8',
            errors='replace').read()
COLS = re.search(r"^COLS = '([^']+)'", _pat, re.M).group(1)
MID = re.search(r"^MID = '([^']+)'", _pat, re.M).group(1)

# The five controls, in the order they must appear on the line.
CONTROLS = [('searchInput', 'Search'), ('propertySelect', 'Property'),
            ('statusSelect', 'Status'), ('fromDateInput', 'From'),
            ('toDateInput', 'To')]

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
    """The file BEFORE this round. as_left_by() returns it as the round
    LEFT it, which is the opposite of a control - A1's lesson, and it
    cost a push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(text):
    """Every kind of comment blanked, length preserved.

    A CHECK THAT A NAME IS ABSENT MUST NOT READ PROSE. The notes this
    round left behind name .date-filter-grid, 150px and "Back to
    overview", because recording what was removed is what a note is for.
    Four gates in this round's first draft read those notes as the
    defect. The instrument was wrong, not the record."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


P_NOW, P_WAS = now(PAGE), was(PAGE)
C_NOW = code_only(P_NOW)
C_WAS = code_only(P_WAS) if P_WAS else ''
CSS_NOW = '\n'.join(STYLE.findall(C_NOW))
JS_NOW = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', P_NOW, re.S))

print('=' * 74)
print('%s - AE-1 AND AE-3, ACTUAL EXPENSES' % ME)
print('=' * 74)

# ==========================================================================
head('1. AE-1 - ONE GRID, FIVE CHILDREN')
# ==========================================================================
ok('date-filter-grid' not in C_NOW,
   '.date-filter-grid is gone - rule and markup both')
if C_WAS:
    ok(C_WAS.count('date-filter-grid') >= 3,
       'CONTROL: it was a desktop rule, a mobile rule and a wrapper div',
       C_WAS.count('date-filter-grid'))
    ok('grid-template-columns: 150px 150px' in C_WAS,
       '  and it pinned both dates at 150px')
else:
    skip('the two-grid control', 'no %s backup' % SUFFIX)

m = re.search(r'<div class="filter-grid">(.*?)\n            </div>', C_NOW,
              re.S)
ok(m is not None, 'the page has one .filter-grid')
kids = re.findall(r'<div class="filter-group">', m.group(1)) if m else []
ok(len(kids) == 5, '  with five .filter-group children', len(kids))
for cid, name in CONTROLS:
    ok(m is not None and ('id="%s"' % cid) in m.group(1),
       '  %-8s (#%s) is one of them' % (name, cid))

# The three bands, in the file, in the order that makes the phone win.
ok(('grid-template-columns: %s;' % COLS) in CSS_NOW,
   'the desktop band is %s' % COLS)
ok(re.search(r'@media screen and \(max-width: 1199px\)\s*\{\s*'
             r'\.filter-grid\s*\{\s*grid-template-columns: %s;'
             % re.escape(MID), CSS_NOW) is not None,
   'the 769-1199 band is %s - today\'s shape, from one grid' % MID)
i_mid = C_NOW.find('max-width: 1199px')
i_small = C_NOW.find('max-width: 768px')
ok(0 < i_mid < i_small,
   'and the 1199 block sits ABOVE the 768 block - both match a phone and '
   'the later one wins, so this ordering is what makes the phone rule hold',
   'mid at %d, small at %d' % (i_mid, i_small))
ok(re.search(r'@media screen and \(max-width: 768px\).*?'
             r'\.filter-grid \{\s*grid-template-columns: 1fr;', CSS_NOW,
             re.S) is not None,
   'and the phone stacks to one column, like every other panel in the house')

# ==========================================================================
head('2. AE-3 - THE DRILL-DOWN, STATICALLY')
# ==========================================================================
drill = re.search(r'<div class="report-drill-head">(.*?)</div>', C_NOW, re.S)
ok(drill is not None, 'the drill title and its Back share one row')
if drill:
    seg = drill.group(1)
    i_title = seg.find('reportDrillTitle')
    i_back = seg.find('reportDrillBack')
    ok(0 <= i_title < i_back,
       '  the title comes first and the Back after it - left and right '
       'under space-between', '%d / %d' % (i_title, i_back))
ok(re.search(r'id="reportDrillBack">\s*\n\s*<i class="fas fa-arrow-left">'
             r'</i> Back\s*\n\s*</button>', C_NOW) is not None,
   'the label is exactly "Back"')
ok('Back to overview' not in C_NOW,
   '  and the old three-word label is gone from the markup')
if C_WAS:
    ok('Back to overview' in C_WAS,
       'CONTROL: it said "Back to overview" before this round')
    ok('report-drill-head' not in C_WAS,
       '  and the button sat alone above the title')
else:
    skip('the label control', 'no %s backup' % SUFFIX)

for want, why in (
        ('.report-drill-head {', 'the row exists'),
        ('justify-content: space-between;', 'title left, Back right'),
        ('.report-drill-head .btn { flex-shrink: 0; }',
         'a long property name takes the squeeze, not the word Back')):
    ok(want in CSS_NOW, '  %s - %s' % (want, why))

# THE TRAP, READ OUT OF THE PAGE'S OWN SCRIPT rather than asserted. If
# the wiring ever changes, the reason to hide the bar changes with it.
# To the handler's OWN closing brace, at its own indentation - a
# non-greedy .*?}); stops at the first nested forEach(function(cb){...});
# and reads a slice with no loadData() in it. The measuring instrument is
# the most common liar; this one lied twice before it was pinned to the
# indentation.
yearcb = re.search(r"allCb\.addEventListener\('change'.*?\n        \}\);",
                   JS_NOW, re.S)
ok(yearcb is not None and 'loadData()' in yearcb.group(0),
   'MEASURED FROM THE SOURCE: a year checkbox calls loadData()')
ld = re.search(r'function loadData\(\) \{(.*?)\n    \}', JS_NOW, re.S)
ok(ld is not None and 'showOverview();' in ld.group(1),
   '  and loadData() calls showOverview() - so touching a year while '
   'drilled down threw you out of the drill. That is why it is hidden, '
   'and it is a trap rather than mere clutter')

ok('function yearBar(show)' in JS_NOW, 'yearBar() exists')
ok("bar.style.display = show ? '' : 'none';" in JS_NOW,
   "  and restores '' rather than a hardcoded flex, so the stylesheet "
   'stays the one place that says how the bar lays out')
od = re.search(r'function openDrill\(propId, propName\) \{(.*?)\n        fetch',
               JS_NOW, re.S)
ok(od is not None and 'yearBar(false);' in od.group(1),
   'openDrill() hides it')
so = re.search(r'function showOverview\(\) \{(.*?)\n    \}', JS_NOW, re.S)
ok(so is not None and 'yearBar(true);' in so.group(1),
   'showOverview() brings it back')
ok('function yearScope()' in JS_NOW,
   'and the heading carries the year scope the hidden bar was showing')
# THE TITLE LINE, not the whole function - openDrill also writes a
# spinner row into the drill table with innerHTML, which is markup this
# file wrote about itself and not a name somebody typed.
title_line = re.search(r"getElementById\('reportDrillTitle'\)\.(\w+)\s*=",
                       JS_NOW)
ok(title_line is not None and title_line.group(1) == 'textContent',
   '  the heading is built with textContent - a property called Smith & '
   'Co is a name, not markup',
   title_line.group(1) if title_line else 'no assignment found')

# ==========================================================================
head('3. CHROMIUM - WHERE THE FIVE CONTROLS ACTUALLY LAND')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

# The panel, rendered from the page's OWN markup with the template tags
# taken out - not a hand-written stand-in that could differ from the page
# in exactly the way that matters.
def fixture_panel(text):
    g = re.search(r'<div class="filter-grid">.*?\n            </div>',
                  code_only(text), re.S)
    if not g:
        # before AE-1 there were two grids; take both
        a = re.search(r'<div class="filter-grid">.*?\n            </div>',
                      code_only(text), re.S)
        b = re.search(r'<div class="date-filter-grid">.*?\n            </div>',
                      code_only(text), re.S)
        inner = (a.group(0) if a else '') + (b.group(0) if b else '')
    else:
        b = re.search(r'<div class="date-filter-grid">.*?\n            </div>',
                      code_only(text), re.S)
        inner = g.group(0) + (b.group(0) if b else '')
    # strip Django: tags, then the {{ }} that remain
    inner = re.sub(r'\{%.*?%\}', '', inner, flags=re.S)
    inner = re.sub(r'\{\{.*?\}\}', '', inner, flags=re.S)
    # give the two dates and the two selects something real to hold
    inner = inner.replace('value=""', '')
    inner = inner.replace('id="fromDateInput"',
                          'id="fromDateInput" value="2026-01-31"')
    inner = inner.replace('id="toDateInput"',
                          'id="toDateInput" value="2026-12-31"')
    inner = inner.replace('<option value=""></option>', '')
    inner = inner.replace('>All Properties<', '>All Properties<')
    return ('<div class="alv-filter filter-panel is-open" id="p">'
            '<div class="filter-header">'
            '<h5 class="filter-title"><i></i> Expense Filters</h5>'
            '<button class="btn btn-outline-secondary btn-sm">Clear All'
            '</button></div>'
            '<div class="filter-content"><form>' + inner
            + '</form></div></div>')


LOOK = '''() => {
  const out = {rows: {}};
  const p = document.getElementById('p');
  out.panel = Math.round(p.getBoundingClientRect().width);
  const ids = %s;
  ids.forEach(id => {
    const e = document.getElementById(id);
    if (!e) { out.rows[id] = null; return; }
    const r = e.getBoundingClientRect();
    out.rows[id] = {w: Math.round(r.width), top: Math.round(r.top)};
  });
  // How many ROWS the five groups occupy: distinct bottom edges, because
  // align-items: end lines the bottoms up and the groups differ in height.
  const groups = [...p.querySelectorAll('.filter-grid > .filter-group, '
                 + '.date-filter-grid > .filter-group')];
  out.lines = new Set(groups.map(e =>
      Math.round(e.getBoundingClientRect().bottom))).size;
  // WHAT A DATE INPUT ACTUALLY NEEDS, measured in THIS browser rather
  // than typed in from another one. test_filter_gap's lesson.
  const probe = document.createElement('input');
  probe.type = 'date'; probe.value = '2026-12-31';
  probe.style.cssText = 'position:absolute;left:-9999px;width:auto;'
    + 'font:inherit;padding:10px 14px;border:2px solid;box-sizing:border-box';
  p.appendChild(probe);
  out.need = Math.ceil(probe.getBoundingClientRect().width);
  probe.remove();
  return out;
}''' % str([c[0] for c in CONTROLS]).replace("'", '"')

WIDTHS = (1920, 1440, 1280, 1100, 900, 390)

if HAVE_PW and os.path.isfile(BOOT):
    boot = read(BOOT)
    base_css = '\n'.join(STYLE.findall(read(alv_tree.path_of('base.html'))))

    def draw(pg, text, name):
        f = os.path.join(SCRATCH, name)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style><style>%s</style>'
                     '</head><body><div class="main-content with-topnav">'
                     '<br/><div class="container">%s</div></div></body>'
                     '</html>'
                     % (boot, base_css, '\n'.join(STYLE.findall(text)),
                        fixture_panel(text)))
        _goto(pg, f)
        return f

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        f_now = draw(pg, P_NOW, 'now.html')
        f_was = draw(pg, P_WAS, 'was.html') if P_WAS else None

        need = None
        for w in WIDTHS:
            pg.set_viewport_size({'width': w, 'height': 900})
            _goto(pg, f_now)
            pg.wait_for_timeout(40)
            r = pg.evaluate(LOOK)
            need = r['need']
            got = dict((k, (v or {}).get('w')) for k, v in r['rows'].items())
            label = ('one line' if w >= 1200 else
                     'stacked' if w <= 768 else 'three up, two under')
            want_lines = 1 if w >= 1200 else (5 if w <= 768 else 2)
            ok(r['lines'] == want_lines,
               '%4dpx (panel %4d) - %-18s %d row(s)'
               % (w, r['panel'], label, r['lines']),
               '%d, wanted %d: %s' % (r['lines'], want_lines, r['rows']))
            # AE-1's claim at the widths it is about.
            if w >= 1200:
                tops = set(v['top'] for v in r['rows'].values() if v)
                ok(len(tops) <= 2,
                   '  ALL FIVE ARE ON ONE LINE - %s'
                   % ', '.join('%s %d' % (n, got[c])
                               for c, n in CONTROLS), sorted(tops))
            # AND EVERY DATE IS WIDE ENOUGH TO SHOW A DATE, at every
            # width, which is the defect nobody could report.
            for cid in ('fromDateInput', 'toDateInput'):
                ok(got[cid] is not None and got[cid] >= need,
                   '    %-13s %3dpx, and a date input needs %d here'
                   % (cid, got[cid] or -1, need),
                   '%s < %s' % (got[cid], need))

        print('')
        if f_was:
            for w in (1280, 390):
                pg.set_viewport_size({'width': w, 'height': 900})
                _goto(pg, f_was)
                pg.wait_for_timeout(40)
                r = pg.evaluate(LOOK)
                got = dict((k, (v or {}).get('w'))
                           for k, v in r['rows'].items())
                ok(r['lines'] >= 2,
                   'CONTROL: at %4dpx the five used to take %d rows'
                   % (w, r['lines']), r['lines'])
                clipped = [c for c in ('fromDateInput', 'toDateInput')
                           if got[c] is not None and got[c] < r['need']]
                ok(len(clipped) == 2,
                   '  and BOTH dates were narrower than a date needs: '
                   '%d and %d against %d'
                   % (got['fromDateInput'] or -1, got['toDateInput'] or -1,
                      r['need']), clipped)
        else:
            skip('the before-and-after render', 'no %s backup' % SUFFIX)
        br.close()
elif not HAVE_PW:
    skipped += 26
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 25

# ==========================================================================
head('4. NOTHING ELSE ON THE PAGE MOVED')
# ==========================================================================
if P_WAS:
    for what, pat in (
            ('<div', r'<div\b'), ('</div', r'</div\s*>'),
            ('<table', r'<table\b'), ('{% if', r'\{%\s*if\b'),
            ('{% endif', r'\{%\s*endif\s*%\}')):
        a, b = (len(re.findall(pat, P_NOW)), len(re.findall(pat, P_WAS)))
        # THE DIV COUNT DOES NOT MOVE, AND IT IS WORTH SAYING WHY.
        # AE-1 removes one wrapper (.date-filter-grid, one <div> and one
        # </div>); AE-3 adds one (.report-drill-head, one of each). They
        # cancel. The first draft of this check expected -1, having
        # counted only the round it was looking at - which is how a
        # suite ends up asserting half of what its own round did.
        ok(a == b, '%-10s %d -> %d' % (what, b, a), '%d, wanted %d'
           % (a, b))
    f_a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', P_NOW))
    f_b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', P_WAS))
    ok(f_a <= f_b, 'and no literal colour entered the page: %d -> %d'
       % (f_b, f_a))
else:
    skip('the shape checks', 'no %s backup' % SUFFIX)

ok(not [i for i, line in enumerate(P_NOW.split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')
for blk in re.findall(r'<script[^>]*>(.*?)</script>', C_NOW, re.S):
    pass
ok(all(b.count('{') == b.count('}')
       for b in re.findall(r'<script[^>]*>(.*?)</script>', C_NOW, re.S)),
   'every <script> block still balances on braces')
ok(CSS_NOW.count('{') == CSS_NOW.count('}'), 'and so does the CSS')

# ==========================================================================
head('5. THE TWO LEDGERS THAT KNEW THE OLD SHAPE')
# ==========================================================================
ff = read(os.path.join(ROOT, 'test_filter_frame.py'))
ok('AMENDED = {' in ff,
   'test_filter_frame.py declares the amendment rather than having its '
   'patcher rewritten - a patcher is the record of what it did')
ok(COLS in ff, '  and names the new column template exactly', COLS[:40])
ok("if (k == 'grid.cols' and rel == 'act_expense.html'" in ff,
   '  its render check exempts this one grid BY NAME')
ok("len(v[1].split()) == 5" in ff,
   '  and the exemption is still a claim - five tracks, not "something "'
   '"changed"')

bb = read(os.path.join(ROOT, 'test_body_backs.py'))
bt_ = read(os.path.join(ROOT, 'test_bar_top.py'))
ok('AE-3' in bt_ and 'two Back controls still say something else' in bt_,
   'test_bar_top.py counts TWO long Back labels now, not three, and '
   'names both rather than counting them - a bare number is what let '
   'that ledger go on listing three after one was fixed')
ok('AE-3' in bb and 'Back to overview' in bb,
   'test_body_backs.py\'s ledger records BOTH labels and which round '
   'changed it - a printed ledger that is quietly wrong is worse than '
   'none, because it is read as fact')

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
