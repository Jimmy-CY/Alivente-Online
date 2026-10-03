# -*- coding: utf-8 -*-
"""test_ref_filters.py - Section FL round FL-1, 3 Oct 2026.

Categories and Measurement Units join the house filter panel. Demetri
agreed the programme on 2 Oct for four pages; IB-1 did the first, these
are the second and third, and Unit Conversions is its own round because
it already has a working filter to move rather than one to build.

On 3 Oct he chose CLIENT-SIDE ONLY for these two, with the cost stated:
the URL will not carry the filter, so Back and refresh forget it.

THE CLAIM THIS SUITE EXISTS FOR is section 3. The two pages use DIFFERENT
mechanisms and that is deliberate:

  Categories has ONE filter and takes base's data-live-search.

  Measurement Units has TWO that must compose, and must NOT take it.
  base's live search owns row.style.display outright - it walks every row
  on every keystroke and sets display from its own query alone. A Type
  dropdown setting the same property is a second owner of one fact, and
  the last to run wins: pick a Type, then type a letter, and the Type
  narrowing silently evaporates.

Section 6 is the proof rather than the argument: it drives a real browser,
sets a Type, types a letter, and checks the Type is still being honoured.
A race condition is not something a reader can see in the markup.
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

SUFFIX = '.bak_reffilter'
ME = 'test_ref_filters.py'
PATCHER = 'apply_ref_filters.py'
PS1 = 'Push-PendingChanges.ps1'
CAT = 'categories_management.html'
UNI = 'measurement_units_management.html'
PAGES = (CAT, UNI)
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
CAP = 240

SCRATCH = tempfile.mkdtemp(prefix='alv_reffilter_')

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


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


RAW = {p: now(alv_tree.path_of(p)) for p in PAGES}
SRC = {p: code_only(RAW[p]) for p in PAGES}
WAS = {p: code_only(was(alv_tree.path_of(p))) for p in PAGES}
BASE = read(alv_tree.path_of('base.html'))
BCODE = code_only(BASE)
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

print('=' * 74)
print('%s - FL-1, THE HOUSE FILTER ON TWO REFERENCE PAGES' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE HOUSE CONTROL, WIRED THE WAY base EXPECTS')
# ==========================================================================
for p in PAGES:
    for need in ('class="btn action-filter"', 'aria-controls="filterPanel"',
                 'aria-pressed="false"', 'id="filterPanel"',
                 'id="activeFilters"', 'id="filterTags"',
                 'id="clearAllBtn"', 'class="filter-grid"'):
        ok(need in SRC[p], '%s carries %s' % (p.split('_')[0], need))
    # COLLAPSED ON LOAD IS AN ABSENCE, NOT A SETTING - .alv-filter is
    # display:none until base adds .is-open.
    panel = SRC[p][SRC[p].index('id="filterPanel"'):]
    ok('is-open' not in panel[:400],
       '  and its panel is closed on load')
    # THE FILTER BUTTON SITS BEFORE BACK. Back carries margin-left:auto,
    # so anything after it would land on the far right beside it.
    ok(SRC[p].index('action-filter') < SRC[p].index('action-back'),
       '  with the Filter button before Back in the bar')

for cls in ('.action-filter', '.alv-filter', '.filter-grid', '.filter-tag',
            '.alv-filter-active', '.filter-header', '.filter-group'):
    ok(bool(re.search(re.escape(cls) + r'[\s,{:]', BCODE)),
       'base defines %s' % cls)

# ==========================================================================
head('2. THE FIELDS ARE NARROW, WHICH IS WHAT WAS ASKED')
# ==========================================================================
# Demetri, 3 Oct: "The filter fields must be made less wide, so that they
# fit on one line." FG-1 put the capped track list in base; this holds
# these two pages to it and refuses a local override that would undo it.
ok('repeat(auto-fit, minmax(200px, %dpx))' % CAP in BCODE,
   'base caps a filter field at %dpx' % CAP)
for p in PAGES:
    local = 0
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(SRC[p])):
        if (re.search(r'\.filter-grid(?![-\w])', m.group(1))
                and 'grid-template-columns' in m.group(2)):
            local += 1
    ok(local == 0,
       '%s sets no columns of its own, so it inherits the cap'
       % p.split('_')[0],
       '%d local rule(s)' % local)

# ==========================================================================
head('3. ONE FILTER TAKES THE COMPONENT; TWO TAKE A FUNCTION')
# ==========================================================================
ok(SRC[CAT].count('data-live-search=') == 1,
   'categories has exactly one live-search box - base\'s component, '
   'which fits a page with one filter exactly',
   SRC[CAT].count('data-live-search='))
ok('data-live-search-cell="Category Name"' in SRC[CAT],
   '  and it names the column it matches')

ok('data-live-search' not in SRC[UNI],
   'measurement_units does NOT use it - two filters and base\'s live '
   'search owns row.style.display outright, so the Type narrowing would '
   'evaporate on the next keystroke')
ok(SRC[UNI].count('row.style.display') == 1,
   '  exactly one writer of row.style.display on the page',
   SRC[UNI].count('row.style.display'))
ok('function apply()' in SRC[UNI],
   '  and one function deciding from both inputs at once')

# THE PREMISE. If base's live search did not own display outright, the
# whole argument above is wrong and these two pages should match.
ok("row.style.display = hit ? '' : 'none'" in BASE,
   'CONTROL: base\'s live search really does set row.style.display from '
   'its own query alone')

# ==========================================================================
head('4. THE TYPE COMES OFF THE ROW, NOT OUT OF THE CELL')
# ==========================================================================
ok('data-unit-type="{{ item.unit.unit_type }}"' in RAW[UNI],
   'the row carries its own type')
# The Type CELL holds the badge AND, for an editor, a <select> with every
# type as an <option>. A text match on that cell matches every row against
# every type.
cell = RAW[UNI][RAW[UNI].index('data-label="Type"'):]
cell = cell[:cell.index('</td>')]
ok('<select' in cell,
   'CONTROL: the Type cell really does hold a <select> of every type - '
   'which is why reading the cell would match every row against every type')
body = SRC[UNI][SRC[UNI].index('function apply()'):]
body = body[:body.index('box.addEventListener')]
ok("getAttribute('data-unit-type')" in body,
   'and the filter reads the attribute instead')
ok('data-label="Type"' not in body,
   '  never the cell')

# ==========================================================================
head('5. THE SEARCH MATCHES THE COLUMNS IT NAMES')
# ==========================================================================
for lab in ('Unit Name', 'Abbreviation'):
    ok('data-label="%s"' % lab in body,
       'the unit search names the %s column' % lab)
ok('data-label="Usage"' not in body,
   'and NOT Usage, which holds every recipe name that uses the unit - a '
   'whole-row match would find "cup" in a recipe called Cupcakes')
ok('unitsNoMatch' in SRC[UNI],
   'a narrowing that finds nothing says so - an empty table with no '
   'message reads as a page that failed to load')

# ==========================================================================
head('6. THE RACE, RUN IN A BROWSER')
# ==========================================================================
# The reason section 3 is a claim and not a preference. Set a Type, then
# type a letter, and ask the browser whether the Type is still honoured.
# Nothing in the markup can show this.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the compose test', 'playwright not installed')

if sync_playwright is not None and FIX:
    t = RAW[UNI]
    i = t.index('<div class="page-action-buttons">')
    # THE LAST endblock, NOT THE FIRST. {% endblock %} appears on line 3
    # of this template, closing {% block title %}, which is BEFORE the
    # action bar - so t.index gave a j smaller than i and the slice came
    # out as the empty string. Every check in this section then measured
    # a blank page.
    j = t.rindex('{% endblock %}')
    IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                         r'\{%\s*endif\s*%\}', re.S)
    IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
    ANYT = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)
    html = t[i:j]
    for pat in (IF_ELSE, IF_ONLY):
        prev = None
        while prev != html:
            prev = html
            html = pat.sub(lambda m: m.group(1), html)
    # THE ROWS ARE WRITTEN HERE, not resolved from the template's {% for %}.
    # The fixture needs rows whose type it KNOWS, so that "the Type is
    # still honoured" is a fact rather than whatever the loop produced.
    html = ANYT.sub('', html)

    # TWO REPAIRS THE STRIPPER MAKES NECESSARY, BOTH NAMED.
    #
    # 1. {{ value }} is stripped, so every <option> in the Type select
    #    arrives with value="" and select_option('volume') times out
    #    against a control that has no such option. The four real choices
    #    come from MeasurementUnit.UNIT_TYPE_CHOICES and are written in.
    # 2. The template's own {% for %} row survives the strip as one
    #    literal <tr data-unit-id="">, which counted as a fifth unit
    #    called "Plural:". The tbody is replaced wholesale with rows whose
    #    type this fixture KNOWS, so "the Type is still honoured" is a
    #    fact rather than whatever the loop happened to leave behind.
    # AND THE PANEL HAS TO BE OPEN. .alv-filter is display:none until
    # base adds .is-open, and Playwright will not act on a control it
    # cannot see - select_option sat waiting for 30 seconds against a
    # select that was there and hidden. Opening it here is the fixture
    # standing in for the Filter button, which section 1 already checks.
    html = html.replace('class="alv-filter filter-panel"',
                        'class="alv-filter filter-panel is-open"')

    sel = re.search(r'(<select id="unitTypeFilter"[^>]*>)(.*?)(</select>)',
                    html, re.S)
    if sel:
        html = html.replace(
            sel.group(0),
            sel.group(1)
            + '<option value="">All types</option>'
            + ''.join('<option value="%s">%s</option>' % (v, v.title())
                      for v in ('volume', 'weight', 'count', 'other'))
            + sel.group(3))

    rows = ''.join(
        '<tr data-unit-id="%d" data-unit-type="%s">'
        '<td data-label="Unit Name"><strong>%s</strong></td>'
        '<td data-label="Abbreviation">%s</td>'
        '<td data-label="Type">%s</td>'
        '<td data-label="Usage">%s</td><td></td></tr>'
        % (n, ty, nm, ab, ty, use)
        for n, (nm, ab, ty, use) in enumerate([
            ('cup', 'c', 'volume', 'Cupcakes, Soup'),
            ('gram', 'g', 'weight', 'Bread'),
            ('piece', 'pc', 'count', 'Cupcakes'),
            ('teaspoon', 'tsp', 'volume', 'Cake'),
        ]))
    keep = ('<tr id="unitsNoMatch" style="display: none;">'
            '<td colspan="5" class="alv-empty-title">'
            'No measurement units match these filters.</td></tr>')
    html = re.sub(r'<tbody id="unitsTableBody">.*?</tbody>',
                  '<tbody id="unitsTableBody">' + keep + rows + '</tbody>',
                  html, 1, re.S)

    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<body>%s' % (FIX, css_of(BASE), css_of(RAW[UNI]), html))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1280, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')

        def visible():
            return pg.evaluate("""() => [...document.querySelectorAll(
                '#unitsTableBody tr[data-unit-id]')]
                .filter(r => getComputedStyle(r).display !== 'none')
                .map(r => r.querySelector('[data-label="Unit Name"]').innerText.trim())""")

        start = visible()
        ok(len(start) == 4, 'the fixture starts with four units', start)

        pg.select_option('#unitTypeFilter', 'volume')
        after_type = visible()
        ok(sorted(after_type) == ['cup', 'teaspoon'],
           'choosing Type = volume leaves the two volume units',
           after_type)

        # THE RACE. If anything else owned display, this keystroke would
        # re-show gram and piece.
        pg.fill('#unitSearch', 'c')
        both = visible()
        ok(sorted(both) == ['cup'],
           'then typing "c" leaves ONLY cup - the Type is still honoured, '
           'which is the whole claim of section 3', both)
        ok('gram' not in both and 'piece' not in both,
           '  the weight and count units did not come back')

        # AND THE SEARCH REALLY IS SCOPED TO TWO COLUMNS.
        pg.select_option('#unitTypeFilter', '')
        pg.fill('#unitSearch', 'cupcakes')
        none_ = visible()
        ok(none_ == [],
           'searching "cupcakes" finds nothing, though two rows carry it '
           'in Usage - the search matches Unit Name and Abbreviation only',
           none_)
        empty = pg.evaluate("""() => {const e =
            document.getElementById('unitsNoMatch');
            return e && getComputedStyle(e).display !== 'none';}""")
        ok(bool(empty), '  and the empty state says so')

        # THE CHIPS, WHICH ARE WHAT base COUNTS FOR THE BADGE.
        pg.fill('#unitSearch', 'cup')
        pg.select_option('#unitTypeFilter', 'volume')
        chips = pg.evaluate("""() => [...document.querySelectorAll(
            '#filterTags .filter-tag')].map(c => c.textContent.trim())""")
        ok(len(chips) == 2, 'two filters set, two chips built', chips)

        pg.click('#clearAllBtn')
        ok(len(visible()) == 4, 'Clear All brings every unit back')
        ok(pg.evaluate("""() => document.querySelectorAll(
            '#filterTags .filter-tag').length""") == 0,
           '  and takes the chips with it')
        br.close()
else:
    skip('the compose test', 'no browser or no fixture')

# ==========================================================================
head('7. NO FORM, AND base TOLERATES THAT')
# ==========================================================================
for p in PAGES:
    panel = SRC[p][SRC[p].index('id="filterPanel"'):]
    end = panel.find('</div>\n    </div>')
    panel = panel[:end if end > 0 else 4000]
    ok('<form' not in panel,
       '%s submits nothing - its view reads no query parameter, so a form '
       'would clear the box on Enter' % p.split('_')[0])
ok("panel.querySelector('form')" in BASE,
   'and base guards for a panel with no form')

# ==========================================================================
head('8. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
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
rows_ = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows_.append(f)
ok(len(rows_) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows_))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows_:
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
ok(not stale, 'and all %d of them still resolve' % len(rows_),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
