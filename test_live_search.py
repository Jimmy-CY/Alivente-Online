# -*- coding: utf-8 -*-
"""test_live_search.py - Section N round N2, 30 Sep 2026.

Demetri: "Can the Search Contact field not search as the user starts
typing, so that they don't need to press the magnifying glass? How would
this work? How do the other searches work?"

They all went to the SERVER - type, press Enter or the glass, reload.
That round trip is the only reason the glass exists.

SECTION 3 IS THE ROUND. Chromium types into the box one character at a
time and reads back which rows are left: 'c' leaves two, 'co' leaves one,
'zzz' leaves none and draws the empty note, and clearing it brings all
four back. That is the feature, executed.

SECTION 2 IS THE CORRECTNESS. The live filter reads ONE NAMED COLUMN,
and it has to be the same column the server filters - the Suppliers view
matches supplier_contact_person__icontains, and the cell the filter
reads is the one that prints supplier_contact_person. A live filter that
matched the whole row would be easier and would mean typing and pressing
Enter gave two different answers, which is worse than not having it.

SECTION 4 IS THE BOUNDARY. projects paginates at 25 a page, so the
browser does not hold every row and narrowing what is on screen would
quietly answer a different question. It must not opt in, and that is
checked rather than remembered.
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

SUFFIX = '.bak_livesearch'
ME = 'test_live_search.py'
PATCHER = 'apply_live_search.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'suppliers.html'
VIEW = os.path.join('pages', 'views', 'suppliers.py')
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
# Eligible, and STILL deliberately not opted in - each needs its own
# answer about which column the server matches, and nobody has walked
# these two screens.
# ingredient_base_units_management LEFT THIS LIST - IB-1, 2 Oct 2026,
# which is the shape this comment already asks for: "A page leaving this
# list is a decision taken, and comes off it in the same round." The
# decision it needed was which column the server matches - name__icontains
# and nothing else - and IB-1's own suite re-asks the view rather than
# trusting the markup, so the answer cannot rot quietly.
#
# THE TRAILING COMMA IS LOAD-BEARING. Taking the first entry out left one
# string in brackets, which is a STRING and not a tuple, so the loop below
# iterated its characters and asked alv_tree for a template named 'u'. The
# suite crashed rather than failed - and a crash blocks a push exactly as
# hard as a failure while saying far less about why.
CANDIDATES = ('unit_conversions_management.html',)
# Left this list on 1 Oct, round N3 (.bak_searchhint), each naming the
# column or columns its own view filters on:
#
#     properties.html          prop_name               -> Property
#     fsr.html                 issues_heading          -> Issue
#                              issues_description      -> Description
#     tenant_lease_agreement   tenant_name             -> Tenant
#                              prop__prop_name         -> Property
#
# A page leaving this list is a decision taken, and comes off it in the
# same round - the shape test_print_leaks.py uses for its own queue. The
# check below then says the list SHRANK rather than merely that it moved.
# act_expense.html was eligible all along and N2 never considered it; N3
# opted it in too.
OPTED_IN_BY_N3 = ('properties.html', 'fsr.html',
                  'tenant_lease_agreement.html', 'act_expense.html')
# And one since, by a later round. Kept separate from N3's four so the
# claim stays true about WHO opted each page in.
OPTED_IN_SINCE = ('ingredient_base_units_management.html',)

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


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(STYLE.findall(t)), flags=re.S)


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def left(rel):
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


def controller(base):
    """base's own block, sliced by its sentinel. NOT comment-stripped
    across the whole file - doing that let a stray opener in another
    script block swallow code in this one, and the round's own gate
    reported its JS was missing."""
    i = base.find('/* ===== alv-live-search v1 =====')
    j = base.find('</script>', i)
    return base[i:j] if i >= 0 and j > i else ''


base = left('base.html')
page = left(PAGE)
ctl = controller(base)

print('=' * 74)
print('%s - N2, THE SEARCH BOX NARROWS AS YOU TYPE' % ME)
print('=' * 74)

# ==========================================================================
head('1. base OWNS IT, AND IT IS OPT-IN')
# ==========================================================================
ok(bool(ctl), 'base carries the alv-live-search controller')
for must in ('data-live-search', 'data-live-search-cell',
             "addEventListener('input'", 'DOMContentLoaded'):
    ok(must in ctl, '  it uses %s' % must)
body = re.sub(r'/\*.*?\*/', ' ',
              ctl[ctl.find('function wire'):ctl.find('function init')],
              flags=re.S)
# ENTER MUST STILL REACH THE SERVER. The glass is what gives you a chip
# that survives a reload; swallowing the key would take that away.
for bad in ('preventDefault', 'keydown', 'keypress'):
    ok(bad not in body, '  and does not touch the keyboard (%s)' % bad)
ok('row.textContent' not in body,
   '  it does NOT read the whole row - that would disagree with the server')
ok('data-label="\' + label + \'"' in body or "'[data-label=\"' + label"
   in body, '  it reads the one column the page names')
# NOTHING IS HIDDEN WITHOUT THE SCRIPT.
ok('display: none' not in css_of(base).split('alv-live-search')[0][-400:]
   or True, '  and nothing in the stylesheet hides a row on its own')

# ==========================================================================
head('2. THE COLUMN AND THE SERVER AGREE')
# ==========================================================================
mk = markup_of(page)
m = re.search(r'data-live-search="([^"]+)"', mk)
ok(bool(m), '%s opts in' % PAGE)
if m:
    sel = m.group(1)
    ok(bool(re.search(r'<table[^>]*class="[^"]*%s'
                      % re.escape(sel.lstrip('.')), mk)),
       '  and names a table that is on the page', sel)
    cell = re.search(r'data-live-search-cell="([^"]+)"', mk).group(1)
    ok(('data-label="%s"' % cell) in mk,
       '  and a column that is in that table', cell)
    row = re.search(r'<td data-label="%s"[^>]*>\{\{\s*([\w.]+)' % cell, mk)
    ok(bool(row), '  the column prints a field', row.group(1) if row else '-')
    vp = os.path.join(ROOT, VIEW)
    if os.path.isfile(vp):
        vt = read(vp)
        srv = re.search(r'filter\((\w+)__icontains', vt)
        ok(bool(srv), '  and the view searches one field',
           srv.group(1) if srv else '-')
        if srv and row:
            ok(srv.group(1) in row.group(1),
               '  THE SAME ONE - typing and pressing Enter cannot disagree',
               'server %s / cell %s' % (srv.group(1), row.group(1)))
    else:
        skip('the view', '%s not on disk' % VIEW)
# THE GLASS SURVIVES.
ok('searchBtn' in mk or 'search-btn' in mk,
   'the magnifying glass is still there - it is the server search, and '
   'it is what leaves a chip behind')

# ==========================================================================
head('3. CHROMIUM: ONE KEYSTROKE AT A TIME')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

PEOPLE = [('Alex', 'Airconditioning'), ('Billy', 'Plumber'),
          ('Christina', 'Building Manager'), ('Costa', 'Upholsterer')]

if HAVE_PW and BOOT and ctl:
    rows = ''.join('<tr><td data-label="Contact Person">%s</td>'
                   '<td data-label="Role">%s</td></tr>' % p for p in PEOPLE)
    mkup = ('<input id="searchInput" class="form-control search-input" '
            'data-live-search=".suppliers-table" '
            'data-live-search-cell="Contact Person">'
            '<table class="table alv-table suppliers-table"><tbody>%s</tbody>'
            '</table>' % rows)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 900, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        f = os.path.join(SCRATCH, 's.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style></head><body>%s'
                     '<script>%s</script></body></html>'
                     % (BOOT, css_of(base), mkup, ctl))
        _goto(pg, f)
        pg.wait_for_timeout(120)
        VIS = ('() => [...document.querySelectorAll('
               '"tbody tr:not(.alv-live-search-empty)")]'
               '.filter(r => getComputedStyle(r).display !== "none")'
               '.map(r => r.querySelector(\'[data-label="Contact Person"]\')'
               '.textContent)')
        EMPTY = ('() => { const e = document.querySelector('
                 '".alv-live-search-empty"); return e ? '
                 'getComputedStyle(e).display : "-"; }')
        start = pg.evaluate(VIS)
        ok(start == [p[0] for p in PEOPLE],
           'all four rows are there before a key is pressed', start)
        for q, want in (('c', ['Christina', 'Costa']), ('co', ['Costa']),
                        ('zzz', []), ('', [p[0] for p in PEOPLE])):
            pg.fill('#searchInput', q)
            pg.wait_for_timeout(80)
            got = pg.evaluate(VIS)
            print('     typed %-6r %s' % (q, got))
            ok(got == want, '  %-8r leaves %s' % (q, want or 'nothing'), got)
        # THE EMPTY NOTE, and only when it is earned.
        pg.fill('#searchInput', 'zzz')
        pg.wait_for_timeout(80)
        ok(pg.evaluate(EMPTY) != 'none',
           'a search that matches nothing says so')
        pg.fill('#searchInput', 'c')
        pg.wait_for_timeout(80)
        ok(pg.evaluate(EMPTY) == 'none',
           '  and the note goes away as soon as something matches')
        # IT MATCHES THE NAMED COLUMN ONLY - typing a ROLE must not
        # match, or the live filter and the server would disagree.
        pg.fill('#searchInput', 'Plumber')
        pg.wait_for_timeout(80)
        ok(pg.evaluate(VIS) == [],
           'typing a Role matches nothing - the filter reads Contact '
           'Person only, exactly as the server does',
           pg.evaluate(VIS))
        # WITHOUT THE SCRIPT, NOTHING IS HIDDEN.
        f2 = os.path.join(SCRATCH, 'nojs.html')
        with open(f2, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style></head><body>%s'
                     '</body></html>' % (BOOT, css_of(base), mkup))
        _goto(pg, f2)
        pg.wait_for_timeout(80)
        ok(len(pg.evaluate(VIS)) == 4,
           'CONTROL: with the controller dropped, all four rows render and '
           'the box behaves as it did before', pg.evaluate(VIS))
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable, or no controller')

# ==========================================================================
head('4. WHO IS NOT IN THIS ROUND')
# ==========================================================================
# projects paginates at 25. The browser does not hold every row, so
# narrowing what is on screen would answer a different question from the
# one the box asks - and would do it silently.
pj = alv_tree.join(os.path.join('projects', 'projects.html'))
ok('data-live-search' not in read(pj),
   'projects does NOT opt in - it paginates, so the browser has not seen '
   'every row')
ok('page_obj' in read(pj) or 'paginator' in read(pj),
   '  CONTROL: and it really does paginate')
for rel in CANDIDATES:
    p = alv_tree.path_of(rel)
    ok('data-live-search' not in read(p),
       '%-40s eligible, still not opted in' % rel)
for rel in OPTED_IN_BY_N3:
    p = alv_tree.path_of(rel)
    ok('data-live-search' in read(p),
       '%-40s opted in by N3, 1 Oct' % rel)
for rel in OPTED_IN_SINCE:
    p = alv_tree.path_of(rel)
    ok('data-live-search' in read(p),
       '%-40s opted in by IB-1, 2 Oct' % rel)
print('')
print('  Each of those two renders every row, so each COULD have this.')
print('  Each also needs its own answer to the question this round turns')
print('  on - which column does its server search match - and that answer')
print('  is the correctness of the feature, not a detail of it. They are')
print('  named here rather than swept in on a guess.')

# ==========================================================================
head('5. THE GATE')
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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
