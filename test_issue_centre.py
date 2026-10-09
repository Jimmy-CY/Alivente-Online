# -*- coding: utf-8 -*-
"""test_issue_centre.py - Section HM round HM-4, 9 Oct 2026.

His centring, asked for from a render: the three header values centre
over their labels, and the six table figures centre in their cells.

A CLASS NAME IN THE MARKUP PROVES NOTHING ABOUT WHAT A READER SEES.
test_required_sweep's section 4 makes that point about an asterisk and
it is truer of alignment than of anything: text-align is the most
overridden property in CSS, a later rule on .iss-n or on the table
would win silently, and a suite that greps for "text-align: center"
would pass on a card that renders right-aligned. Section 3 measures
getComputedStyle in a real browser.

WHAT THIS ROUND GIVES UP, AND SAYS SO. Right alignment with
tabular-nums is what makes a column of figures scannable - the digits
sit under each other and the eye reads the column. Centring takes
that away. It is the right call on TWO data rows, where there is no
column to scan, and it would be the wrong one on ten. Section 4 pins
the row count so that if the table ever grows, this suite fails and
somebody has to decide again rather than inherit a choice made for a
smaller table.

NOT PROVED HERE: that centred reads better than right-aligned. It is
an appearance decision and he made it from a render, which is the
right way round.
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

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_isscentre'
ME = 'test_issue_centre.py'
PATCHER = 'apply_issue_centre.py'
PS1 = 'Push-PendingChanges.ps1'

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


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
import alv_rounds as RD                                      # noqa: E402
import alv_tree as T                                         # noqa: E402
PAGE = T.path_of('home.html')
src = RD.as_left_by(PAGE, SUFFIX, read)

applied = 'HM-4, 9 Oct 2026' in src
ok(applied, 'home.html carries the round note')
if not applied:
    skip('every later section', 'HM-4 is not applied to this tree.')
    print('')
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. THE RULES SAY SO')
# ==========================================================================
def rule(name):
    # re.escape ALREADY escapes the dot. A leading backslash here makes
    # the pattern hunt for a literal backslash and every rule reads
    # empty - which looks exactly like a broken stylesheet. Cost me
    # five false failures in section 2 before I read the pattern.
    m = re.search(re.escape(name) + r'\s*\{([^}]*)\}', src)
    return ' '.join(m.group(1).split()) if m else ''


card = src[src.index('ins-ic--iss'):]
card = card[:card.index('</section>')]
ok('iss-chg' not in card,
   'not one change chip is left on the card - he asked for the numbers '
   'alone after seeing +266.7% off a base of nine')
ok('fa-arrow' not in card, '  and not one arrow')
ok(card.count('{{ insights.issues.') >= 9,
   '  while every figure is still there: %d bindings'
   % card.count('{{ insights.issues.'))
svc = read(os.path.join(ROOT, 'pages', 'services',
                        'portfolio_insights.py'))
ok('def direction(' not in svc and 'def arrow(' not in svc,
   'and the service stopped computing the directions - they went with '
   'their last caller, which is the fault HM-3 was built to remove')
ok('_dir":' not in svc and '_arrow":' not in svc,
   '  no key for them either')

ok('align-items: center' in rule('.ins-kpi'),
   '.ins-kpi centres its two lines against each other', rule('.ins-kpi'))
ok('text-align: center' in rule('.iss-tbl td.iss-n'),
   '.iss-tbl td.iss-n is centred', rule('.iss-tbl td.iss-n'))
ok('tabular-nums' in rule('.iss-tbl td.iss-n'),
   '  and KEEPS tabular-nums - the digits stay even width even though '
   'the shared right edge has gone')
ok('text-align: center' in rule('.iss-tbl th'),
   '.iss-tbl th follows the figures', rule('.iss-tbl th'))
ok('text-align: left' in rule('.iss-tbl th:first-child'),
   'and the row-name header STAYS LEFT - it sits over names, not '
   'figures', rule('.iss-tbl th:first-child'))


# ==========================================================================
head('3. MEASURED IN A BROWSER, NOT GREPPED')
# ==========================================================================
up = False
try:
    from playwright.sync_api import sync_playwright
    import atexit
    _pw = sync_playwright().start()
    atexit.register(_pw.stop)
    _br = _pw.chromium.launch()
    up = True
except Exception as _e:
    skip('section 3', 'Chromium would not start: %s'
         % str(_e).split('\n')[0][:80])

if up:
    base = read(T.path_of('base.html'))
    toks = '\n'.join(l for l in base.split('\n')
                     if re.match(r'\s*--alv-[a-z0-9-]+:', l))
    rules = ['%s{%s}' % (m.group(1).strip(), m.group(2))
             for m in re.finditer(
                 r'(\.(?:iss|ins)[-\w.:()\s,>]*)\{([^{}]*)\}', src)]
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>'
           ':root{%s}\n%s\n.ins-card{grid-column:auto}</style></head>'
           '<body><section class="ins-card ins-card--half">'
           '<div class="ins-kpis"><div class="ins-kpi" id="k">'
           '<span class="ins-kpi__n" id="n">10</span>'
           '<span class="ins-kpi__k" id="l">OPEN NOW</span></div></div>'
           '<table class="iss-tbl"><tr><th id="h0"></th>'
           '<th id="h1">Latest 3 months</th></tr>'
           '<tr><td id="r">Logged</td><td class="iss-n" id="c">28</td></tr>'
           '</table></section></body></html>' % (toks, '\n'.join(rules)))
    f = os.path.join(SCRATCH, 'hm4_probe.html')
    open(f, 'w', encoding='utf-8').write(doc)
    pg = _br.new_page(viewport={'width': 660, 'height': 400})
    try:
        _goto(pg, f)
        got = pg.evaluate(
            """() => {
                 const g = id => getComputedStyle(
                   document.getElementById(id));
                 const k = document.getElementById('k').getBoundingClientRect();
                 const n = document.getElementById('n').getBoundingClientRect();
                 const l = document.getElementById('l').getBoundingClientRect();
                 return {cell: g('c').textAlign, head1: g('h1').textAlign,
                         head0: g('h0').textAlign,
                         nums: g('c').fontVariantNumeric,
                         nMid: n.left + n.width / 2,
                         lMid: l.left + l.width / 2,
                         kMid: k.left + k.width / 2};
               }""")
    finally:
        pg.close()

    ok(got['cell'] == 'center',
       'the figure cell computes text-align %r' % got['cell'])
    ok(got['head1'] == 'center',
       'its header computes %r' % got['head1'])
    ok(got['head0'] == 'left',
       'and the row-name header computes %r' % got['head0'])
    ok('tabular-nums' in (got['nums'] or ''),
       'the figures are still tabular-nums: %r' % got['nums'])

    # THE HEADER TRIO: the number's centre line sits on the label's.
    # A text-align check would pass on a column whose two boxes are
    # different widths and both left-aligned inside themselves.
    off = abs(got['nMid'] - got['lMid'])
    ok(off < 1.0,
       'the value sits centred over its label - the two midpoints are '
       '%.2fpx apart' % off, got)


# ==========================================================================
head('4. TWO DATA ROWS, WHICH IS WHY THIS IS THE RIGHT CALL')
# ==========================================================================
tbl = src[src.index('<table class="iss-tbl">'):]
tbl = tbl[:tbl.index('</table>')]
rows = tbl.count('<tr>')
ok(rows == 3,
   'the table has %d rows: one header and TWO of data. Centring gives '
   'up the shared right edge, which is what makes a column scannable - '
   'and there is no column to scan. IF THIS NUMBER GROWS, this check '
   'fails on purpose, so somebody decides again rather than inheriting '
   'a choice made for a smaller table' % rows)
ok('<td>Logged</td>' in tbl and '<td>Closed</td>' in tbl,
   '  and they are Logged and Closed')


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_isscard'"),
   '  and after HM-3, whose card it centres')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that centred reads better than right-aligned.')
print('  It is an appearance decision, made from a render, which is the')
print('  right way round. What IS proved is that it renders centred and')
print('  that the table is still small enough for that to be sensible.')
sys.exit(1 if failed else 0)
