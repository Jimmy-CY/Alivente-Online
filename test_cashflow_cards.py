# -*- coding: utf-8 -*-
"""test_cashflow_cards.py - Section D round D-5, 10 Oct 2026.

THE CASHFLOW CARD IS A DIFFERENT COMPONENT FROM BASE'S STAT TILE, AND
THIS RECORDS WHY RATHER THAN CONVERTING IT.

D-5 asked whether finance/cashflow_forecast should adopt base's stat
tiles, as Tenant Payment Days did. Rendered both ways, it should not.

    the page's card   a PERIOD HEADING over THREE labelled figures -
                      Revenue, Expenses, Net - with Net ruled off as
                      the resolution of the other two
    base's .alv-stat  ONE value under ONE uppercase label, no band

Three cards would become nine tiles, the period would repeat in every
label, and the arithmetic relationship between the three figures would
dissolve into a grid of equals.

SECTION 3 MEASURES THAT DIFFERENCE instead of asserting it. It renders
one of the page's cards and one of base's tiles and counts the value
elements in each: three against one. A sentence claiming the shapes
differ is an opinion; a count is not.

WHAT THIS SUITE IS FOR. The page is right and nothing needs changing -
so what was missing was never a conversion. It was anything recording
why the page differs, so the next person tidying the system does not
harmonise away a band that is carrying a period name. If the card ever
stops holding three figures, section 2 fails and somebody decides
again.

NOT PROVED HERE: that this card is the best design for the data. Only
that it is a different shape from base's tile, that the difference is
load-bearing, and that it was kept on purpose after both were drawn.
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

ME = 'test_cashflow_cards.py'
PATCHER = 'apply_cashflow_cards.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
PAGE = 'finance/cashflow_forecast.html'
STRAY = 'physical_invoice_edit.html'

N_CARDS, N_GRIDS, N_HEADERS = 3, 1, 3
N_LINES = 9                  # three figures on each of three cards
N_RULES = 26                 # the card family this page declares
TITLES = ('Current Month', 'Next 3 Months', 'Next 12 Months')
LABELS = ('Expenses', 'Net', 'Revenue')

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
            for line in str(detail).split('\n')[:10]:
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

import alv_tree as T                                          # noqa: E402

CF = read(T.path_of(PAGE))
CFC = T.code_only(CF)
BASE = read(T.path_of('base.html'))
BC = T.code_only(BASE)


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.isfile(T.path_of(PAGE)), '%s is on disk' % PAGE)


# ==========================================================================
head('2. THREE PERIODS, THREE FIGURES EACH, UNDER A HEADING')
# ==========================================================================
n_cards = len(re.findall(r'class="summary-card[^"]*"', CF))
n_grid = len(re.findall(r'class="summary-grid"', CF))
n_head = len(re.findall(r'class="card-header"', CF))
n_line = len(re.findall(r'class="cf-line[^"]*"', CF))
ok(n_cards == N_CARDS, '%d card(s)' % n_cards, 'pinned at %d' % N_CARDS)
ok(n_grid == N_GRIDS, '  in %d grid' % n_grid, 'pinned at %d' % N_GRIDS)
ok(n_head == N_HEADERS,
   '  each with a heading band - %d of them, which is the part base\'s '
   'tile has nowhere to put' % n_head, 'pinned at %d' % N_HEADERS)
ok(n_line == N_LINES,
   '  and %d figure row(s), three to a card. IF THIS STOPS BEING THREE, '
   'this fails on purpose and the question reopens' % n_line,
   'pinned at %d' % N_LINES)
titles = tuple(m.group(1).strip() for m in
               re.finditer(r'<h6>(?:<i[^>]*></i>)?\s*([^<]+)<span '
                           r'class="cf-range"', CF))
ok(titles == TITLES, '  the headings are the three periods: %s'
   % ', '.join(titles), TITLES)
labels = tuple(sorted(set(re.findall(r'class="cf-lbl">([^<]+)<', CF))))
ok(labels == LABELS,
   '  and every card carries the same three labels: %s - Net being the '
   'other two resolved, which is why they belong in one box'
   % ', '.join(labels), LABELS)


# ==========================================================================
head('3. MEASURED: THE TWO SHAPES ARE NOT THE SAME SHAPE')
# ==========================================================================
# A sentence claiming the shapes differ is an opinion. A count is not.
up = False
try:
    from playwright.sync_api import sync_playwright
    import atexit
    if not os.path.isfile(os.path.join(ROOT, BOOT)):
        raise RuntimeError('%s is missing' % BOOT)
    _pw = sync_playwright().start()
    atexit.register(_pw.stop)
    _br = _pw.chromium.launch()
    up = True
except Exception as _e:
    skip('section 3', 'Chromium or the Bootstrap fixture is unavailable: %s'
         % str(_e).split('\n')[0][:66])

if up:
    boot = read(os.path.join(ROOT, BOOT))

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', mm.group(1), flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                      re.S | re.I)]

    CARD = ('<div class="summary-grid"><div class="summary-card">'
            '<div class="card-header"><h6>Current Month'
            '<span class="cf-range"> 1 - 31 Oct</span></h6></div>'
            '<div class="card-body cf-compact">'
            '<div class="cf-line cf-rev"><span class="cf-lbl">Revenue</span>'
            '<span class="cf-val">1</span></div>'
            '<div class="cf-line cf-exp"><span class="cf-lbl">Expenses</span>'
            '<span class="cf-val">2</span></div>'
            '<div class="cf-line cf-net"><span class="cf-lbl">Net</span>'
            '<span class="cf-val">3</span></div></div></div></div>')
    TILE = ('<div class="alv-stats is-3up"><div class="alv-stat">'
            '<div class="alv-stat-value">1</div>'
            '<div class="alv-stat-label">Current Month Revenue</div>'
            '</div></div>')

    def doc(markup):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(BASE)),
                   ''.join('<style>%s</style>' % c for c in styles_of(CF)),
                   markup))

    REFUSED = []
    ctx = _br.new_context(viewport={'width': 1100, 'height': 900})

    def _offline(route, request):
        REFUSED.append(request.url)
        route.abort()

    ctx.route(re.compile(r'^https?://'), _offline)
    pg = ctx.new_page()
    pg.set_content('<!doctype html><html><body>x</body></html>')
    probe = pg.evaluate(
        '''() => fetch('https://cdn.example.invalid/p.css')
                 .then(() => 'loaded').catch(() => 'blocked')''')
    ok(probe == 'blocked' and len(REFUSED) > 0,
       'CONTROL: the page asked for a remote stylesheet and the browser '
       'REFUSED it, so neither shape depends on what a CDN served today',
       '%r, %s' % (probe, REFUSED[:1]))

    pg.set_content(doc(CARD))
    card = pg.evaluate(
        '''() => {
             const c = document.querySelector('.summary-card');
             const h = c.querySelector('.card-header');
             return {values: c.querySelectorAll('.cf-val').length,
                     heading: (h ? h.textContent : '').trim().slice(0, 13),
                     band: h ? getComputedStyle(h).backgroundColor : ''};
           }''')
    pg.set_content(doc(TILE))
    tile = pg.evaluate(
        '''() => {
             const t = document.querySelector('.alv-stat');
             return {values: t.querySelectorAll('.alv-stat-value').length,
                     headers: t.querySelectorAll('.card-header').length};
           }''')
    ctx.close()
    try:
        _br.close()
    except Exception:
        pass

    ok(card['values'] == 3,
       'the page\'s card renders %d value(s)' % card['values'], card)
    ok(tile['values'] == 1 and tile['headers'] == 0,
       "and base's tile renders %d, with %d heading band(s) - so the same "
       'data needs %d tiles where it needs %d card(s), with the period '
       'repeated in every label'
       % (tile['values'], tile['headers'], N_LINES, N_CARDS), tile)
    ok(card['heading'].startswith('Current Month'),
       '  the band carries the period: %r' % card['heading'])
    ok(card['band'] not in ('', 'rgba(0, 0, 0, 0)'),
       '  and it is a filled band, not a bare line: %s' % card['band'])


# ==========================================================================
head('4. THE PRIVATE RULES ARE COUNTED, NOT LEFT VAGUE')
# ==========================================================================
rules = re.findall(r'[^{}]*\.(?:summary-card|summary-grid|card-body|'
                   r'card-header|card-subtitle|cf-line|cf-lbl|cf-val|'
                   r'cf-range)[^{}]*\{[^}]*\}', CFC)
ok(len(rules) == N_RULES,
   'the page declares %d rule(s) in its card family, across its two '
   'breakpoints' % len(rules), 'pinned at %d' % N_RULES)
ok('alv-stat' not in CF,
   '  and uses none of base\'s stat classes, which is the point rather '
   'than an oversight')


# ==========================================================================
head('5. THE ONE STRAY, NAMED AND LEFT')
# ==========================================================================
st = read(T.path_of(STRAY))
n_stray = len(re.findall(r'class="[^"]*\bsummary-card\b', st))
ok(n_stray == 1,
   '%s carries %d summary-card - a copy of this component on a page with '
   'no three-line structure to justify it' % (STRAY, n_stray),
   'pinned at 1')
others = []
for p in sorted(T.templates()):
    rel = T.rel(p).replace(os.sep, '/')
    if rel in (PAGE, STRAY):
        continue
    if re.search(r'class="[^"]*\bsummary-card\b', read(p)):
        others.append(rel)
ok(not others,
   '  and NOBODY ELSE uses it. That one probably should be base\'s tile, '
   'and it is a visible change on one element - so it waits for a round '
   'that renders it first', others)


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'.bak_cfcards'" not in rounds,
   'and NOT in alv_rounds.ROUNDS - this round leaves no application file '
   'behind')
ok(ME not in T.CONVERTED,
   '  nor in alv_tree.CONVERTED - it reads two named templates and does '
   'not walk the tree, unlike D-2\'s suite and PQ-1\'s, which both had to '
   'join that register')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that this card is the best design for the')
print('  data. Only that it is a different shape from base\'s tile,')
print('  that the difference is load-bearing, and that it was kept')
print('  on purpose after both were drawn at both widths.')
sys.exit(1 if failed else 0)
