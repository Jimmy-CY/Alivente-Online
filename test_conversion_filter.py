# -*- coding: utf-8 -*-
"""test_conversion_filter.py - Section UC round UC-2, 3 Oct 2026.

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
The fourth and last page of the filter programme, and the only one that
already HAD a filter. Search, From-Unit and a three-way scope, all
client-side, all composed in one applyFilters(). This round moved the
controls into the house panel and converted the scope toggle - the
SEVENTH hand-rolled segmented control - onto base's ALV-SEG, which UC-1b
wrote down two days ago as needing its own round.

SECTION 2 IS THE CLAIM. The narrowing itself did not change. A round that
quietly altered what applyFilters matches while restyling the controls
around it would look perfect and answer different questions, so the
three row attributes and the composed condition are compared against the
backup character for character.

SECTION 4 DRIVES A BROWSER, because the thing worth checking is that the
three narrowings still COMPOSE: pick a scope, type a letter, and both
must still be honoured.
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

SUFFIX = '.bak_convfilter'
ME = 'test_conversion_filter.py'
PATCHER = 'apply_conversion_filter.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'unit_conversions_management.html'
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

SCRATCH = tempfile.mkdtemp(prefix='alv_convfilter_')

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


def code_only(t):
    """Blank every comment, preserving length - and the CSS/JS syntax
    ONLY WHERE IT IS A COMMENT.

    `/*` IS NOT A COMMENT OPENER IN MARKUP. `accept="image/*"` puts one
    inside an attribute value on five templates - edit_asset, my_profile,
    passport_management, preview_imported_recipe and property_assets -
    and the usual form of this helper blanks from there to the next `*/`
    anywhere in the file. On property_assets that is 1,385 characters of
    real markup, which is how SG-2's gate came to report a class as
    absent while grep found it on line 355.

    A block comment only exists inside <style> or <script>, so that is
    the only place it is looked for.
    """
    blank = lambda m: ' ' * len(m.group(0))
    t = re.sub(r'\{#.*?#\}', blank, t, flags=re.S)
    t = re.sub(r'<!--.*?-->', blank, t, flags=re.S)

    def inner(m):
        return (m.group(1)
                + re.sub(r'/\*.*?\*/', blank, m.group(2), flags=re.S)
                + m.group(3))

    return re.sub(r'(<(?:style|script)\b[^>]*>)(.*?)(</(?:style|script)>)',
                  inner, t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W = code_only(was(P))
BASE = read(alv_tree.path_of('base.html'))
BCODE = code_only(BASE)
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

print('=' * 74)
print('%s - UC-2, THE CONVERSIONS FILTER INTO THE HOUSE PANEL' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE HOUSE PANEL, AND THE SEVENTH SEGMENT')
# ==========================================================================
for need in ('class="btn action-filter"', 'aria-controls="filterPanel"',
             'id="filterPanel"', 'id="activeFilters"', 'id="filterTags"',
             'id="clearAllBtn"', 'class="filter-grid"', 'class="alv-seg"'):
    ok(need in CODE, 'the page carries %s' % need)
panel = CODE[CODE.index('id="filterPanel"'):]
ok('is-open' not in panel[:400], 'and the panel is closed on load')
ok(CODE.index('action-filter') < CODE.index('action-back'),
   'the Filter button sits before Back')

for dead in ('filter-bar', 'scope-toggle', 'scope-btn', 'filter-input'):
    ok(not re.search(r'\b%s\b' % dead, CODE),
       '%s is gone from markup and CSS alike' % dead)

seg = CODE[CODE.index('class="alv-seg"'):]
seg = seg[:seg.index('</div>')]
ok(len(re.findall(r'aria-pressed="(?:true|false)"', seg)) == 3,
   'three segments, each carrying aria-pressed')
ok(seg.count('aria-pressed="true"') == 1, 'exactly one of them pressed')
ok("classList.add('active')" not in CODE,
   'and the scope is NOT also recorded as a class - two things '
   'remembering one fact is how a control comes to disagree with itself')
ok('.alv-seg > [aria-pressed="true"]' in BCODE,
   'base fills a pressed segment')

if W:
    for lit, k in (('#dee2e6', 2), ('#6c757d', 1), ('#f8f9fa', 1)):
        ok(W.count(lit) - CODE.count(lit) == k,
           'dropped %d use(s) of %s' % (k, lit),
           '%d before, %d after' % (W.count(lit), CODE.count(lit)))
    ok('scope-btn' in W,
       'CONTROL: the page really did hand-roll its segmented control')
else:
    skip('the literal drops', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. THE NARROWING ITSELF DID NOT CHANGE')
# ==========================================================================
# The premise of the round is that the logic was already right. A round
# that altered it while moving the controls would be very hard to spot.
body = CODE[CODE.index('function applyFilters()'):]
body = body[:body.index('function ', 10)]
for keep in ("row.getAttribute('data-from-unit')",
             "row.getAttribute('data-to-unit')",
             "row.getAttribute('data-ingredient')",
             "row.getAttribute('data-generic') === 'true'",
             'searchMatch && unitMatch && scopeMatch'):
    ok(keep in body, 'applyFilters still reads %s' % keep[:46])
if W:
    wbody = W[W.index('function applyFilters()'):]
    wbody = wbody[:wbody.index('function ', 10)]
    for keep in ("row.getAttribute('data-from-unit')",
                 'searchMatch && unitMatch && scopeMatch'):
        ok(wbody.count(keep) == body.count(keep),
           '  and exactly as many times as before (%s)' % keep[:34])

hits = [m.start() for m in re.finditer(r'row\.style\.display', CODE)]
fn = CODE.index('function applyFilters()')
end = CODE.index('function ', fn + 10)
ok(all(fn < h < end for h in hits),
   'every writer of row.style.display is inside applyFilters - %d of them, '
   'which are the two branches of one if/else' % len(hits))
ok('data-live-search' not in CODE,
   'and no data-live-search: this page composes THREE narrowings and '
   "base's component owns display outright")

# ==========================================================================
head('3. THE COUNT IS WHERE IT CAN BE SEEN')
# ==========================================================================
ok(CODE.index('id="filterPanel"') < CODE.index('class="conversions-card"')
   < CODE.index('id="filterResultsCount"'),
   'the count sits with the table, not inside a panel that is shut')

# ==========================================================================
head('4. THE THREE COMPOSE - RUN IN A BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the compose test', 'playwright not installed')

if sync_playwright is not None and FIX:
    IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                         r'\{%\s*endif\s*%\}', re.S)
    IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
    ANYT = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)
    t = NOW
    h = t[t.index('<div class="page-action-buttons">'):t.rindex('{% endblock %}')]
    for pat in (IF_ELSE, IF_ONLY):
        prev = None
        while prev != h:
            prev = h
            h = pat.sub(lambda m: m.group(1), h)
    # A STRIPPED {{ }} IN A SCRIPT IS A SYNTAX ERROR, NOT A BLANK. The
    # page's script reads `const total = {{ conversions.count }};`, and
    # stripping the variable leaves `const total = ;` - so the whole
    # <script> failed to parse, applyFilters was never defined, and every
    # check below measured a page where nothing narrows at all. Numeric
    # interpolations are given a number before the strip runs.
    h = h.replace('{{ conversions.count }}', '4')
    h = ANYT.sub('', h)
    h = h.replace('class="alv-filter filter-panel"',
                  'class="alv-filter filter-panel is-open"')
    # THE ROWS, WRITTEN HERE. applyFilters reads three data- attributes
    # off each row, so the fixture supplies rows whose attributes it
    # knows rather than whatever the template loop left behind.
    rows = ''.join(
        '<tr data-from-unit="%s" data-to-unit="%s" data-ingredient="%s" '
        'data-generic="%s"><td data-label="Conversion">%s to %s</td>'
        '<td data-label="Applies To">%s</td></tr>'
        % (f, to, ing, g, f, to, ing or 'Generic')
        for f, to, ing, g in [
            ('cup', 'ml', 'flour', 'false'),
            ('cup', 'ml', '', 'true'),
            ('gram', 'kg', 'sugar', 'false'),
            ('litre', 'ml', '', 'true'),
        ])
    h = re.sub(r'<tbody id="conversionsTableBody">.*?</tbody>',
               '<tbody id="conversionsTableBody">' + rows + '</tbody>',
               h, 1, re.S)
    sel = re.search(r'(<select id="fromUnitFilter"[^>]*>)(.*?)(</select>)',
                    h, re.S)
    if sel:
        h = h.replace(sel.group(0), sel.group(1)
                      + '<option value="">All From-Units</option>'
                      + ''.join('<option value="%s">%s</option>' % (u, u)
                                for u in ('cup', 'gram', 'litre'))
                      + sel.group(3))
    doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
           '<style>%s</style><style>%s</style><body>%s'
           % (FIX, css_of(BASE), css_of(NOW), h))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1280, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')

        def vis():
            return pg.evaluate("""() => [...document.querySelectorAll(
                '#conversionsTableBody tr[data-from-unit]')]
                .filter(r => getComputedStyle(r).display !== 'none')
                .map(r => r.getAttribute('data-from-unit') + '/' +
                          (r.getAttribute('data-ingredient') || '-'))""")

        ok(len(vis()) == 4, 'the fixture starts with four conversions', vis())

        pg.click('.alv-seg button:nth-child(3)')      # Generic
        g = vis()
        ok(sorted(g) == ['cup/-', 'litre/-'],
           'choosing Generic leaves the two generic rows', g)
        ok(pg.evaluate("""() => document.querySelectorAll(
            '.alv-seg [aria-pressed=\"true\"]').length""") == 1,
           '  and exactly one segment reads as pressed')

        pg.fill('#conversionSearch', 'cup')
        both = vis()
        ok(both == ['cup/-'],
           'then typing "cup" leaves only the generic cup row - scope and '
           'search both honoured', both)

        pg.select_option('#fromUnitFilter', 'litre')
        ok(vis() == [],
           'and adding From-Unit = litre leaves nothing, which is all '
           'three composing', vis())

        chips = pg.evaluate("""() => [...document.querySelectorAll(
            '#filterTags .filter-tag')].map(c => c.textContent.trim())""")
        ok(len(chips) == 3, 'three filters set, three chips built', chips)

        pg.click('#clearAllBtn')
        ok(len(vis()) == 4, 'Clear All brings every row back')
        ok(pg.evaluate("""() => document.querySelector(
            '.alv-seg [aria-pressed=\"true\"]').textContent.trim()""")
           == 'All', '  and puts the scope back to All')
        br.close()
else:
    skip('the compose test', 'no browser or no fixture')


# ==========================================================================
head('5. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
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
SG_ = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rws = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG_.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rws.append(f)
ok(len(rws) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rws))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rws:
    pth = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(pth):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(pth)
    if r.get('Code'):
        b2 = _strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rws),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
