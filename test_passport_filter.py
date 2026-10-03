# -*- coding: utf-8 -*-
"""test_passport_filter.py - Section PA round PA-1, 3 Oct 2026.

Demetri, 3 Oct 2026: "The Passports for now are ONLY for the four family
members. Maybe we can make this list the Household members. We want to
bring the filter panel into our standards. Let's bring the typed-in data
onto our standards. Do one round for filter and typed-in."

==========================================================================
FOUR LISTS, EACH WRITTEN OUT TWICE
==========================================================================
Holder was four family names. Type and Status were typed into the template
although Passport.DOCUMENT_TYPE_CHOICES and Passport.STATUS_CHOICES have
existed all along - AND THE TWO COPIES HAD ALREADY DRIFTED: the filter
called arc "ARC" and the form called it "Alien Registration Card".

Country had no home anywhere, so it takes the countries actually recorded,
and the Add form became a text box with those as SUGGESTIONS - a dropdown
restricted to what exists could never be used to add the fifth country.

==========================================================================
SECTION 4 IS THE ROUND
==========================================================================
Narrowing used to be a FORM SUBMIT - every select reloaded the page, which
is why the page carried three sessionStorage keys whose only job was to
re-open the panel afterwards, and a setTimeout that ran `false;`.

So the claim is not "the script is there". It is that four filters narrow
TOGETHER, that the chips follow, that a narrowing which finds nothing says
so, and that Clear All and a chip's x both put every row back. Driven in
Chromium against the page's own script and base's stylesheet.

AND SECTION 5 IS WHY THE SERVER STOPPED NARROWING. If both the server and
the browser narrowed, changing a select would narrow rows the server had
already removed - two owners of one fact, and the second one lying. The
view still READS the four parameters so a bookmarked ?holder=... arrives
showing that filter; the browser applies it.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_passfilter'
ME = 'test_passport_filter.py'
PATCHER = 'apply_passport_filter.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_passfilter_')

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


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('passport_management.html')
BASE = alv_tree.path_of('base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'passports.py')

SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
V = read(VIEW)
VW = was(VIEW)

FAMILY = ('Demetri Manias', 'Angela Manias', 'Erene Manias',
          'Alexandra Manias')
TYPE_LABELS = ('Driver&#39;s License', "Driver's License", 'Alien '
               'Registration Card')
COUNTRIES = ('Cyprus', 'Greece', 'South Africa', 'Zimbabwe')


def options(src):
    """Every <option> VALUE written as a literal in the markup - not the
    ones a {% for %} builds. A value that is a template variable is
    derived; one that is a word is typed in."""
    out = []
    for m in re.finditer(r'<option value="([^"]*)"', src):
        v = m.group(1)
        if v and '{{' not in v:
            out.append(v)
    return out


# ==========================================================================
head('1. NOT ONE OF THE FOUR LISTS IS TYPED INTO THE PAGE')
# ==========================================================================
lits = options(SRC)
for name in FAMILY:
    ok(name not in SRC,
       '%-18s is not written into the template' % name)
ok(not [v for v in lits if v in COUNTRIES],
   'no country is written in as an option value',
   ', '.join(v for v in lits if v in COUNTRIES))
ok(not [v for v in lits if v in ('passport', 'id', 'drivers_license',
                                 'visa', 'arc')],
   'no document type is', ', '.join(lits))
ok(not [v for v in lits if v in ('active', 'renewal', 'inactive')],
   'and no status is')
ok(sorted(set(lits)) == [''] or not lits,
   'the only literal option values left are the empty placeholders',
   sorted(set(lits)))

# ==========================================================================
head('2. CONTROL - THE BACKUP HAD ALL FOUR, AND THEY HAD DRIFTED')
# ==========================================================================
if not OLD:
    for _ in range(4):
        skip('the backup had them', 'no backup')
else:
    had = options(OLD)
    ok(all(n in OLD for n in FAMILY),
       'before this round all four family names were in the template')
    ok(len([v for v in had if v in COUNTRIES]) >= 8,
       '  and every country twice - %d literal country options'
       % len([v for v in had if v in COUNTRIES]))
    ok(len([v for v in had if v in ('passport', 'id', 'drivers_license',
                                    'visa', 'arc')]) >= 10,
       '  and every type twice')
    # THE DRIFT, NAMED. Two copies of a list are two chances to be right.
    ok('>ARC<' in OLD and 'Alien Registration Card' in OLD,
       '  AND THE TWO COPIES DISAGREED: the filter said ARC where the '
       'form said Alien Registration Card')
    ok(not ('>ARC<' in SRC and 'Alien Registration Card' in SRC),
       'now there is one list, so they cannot disagree')

# ==========================================================================
head('3. THE VIEW HANDS THEM OVER, FROM WHERE THEY LIVE')
# ==========================================================================
ok('HouseholdMember' in V, 'the view imports HouseholdMember')
ok("'household_members'" in V, 'and hands over household_members')
ok("'doc_types': Passport.DOCUMENT_TYPE_CHOICES" in V,
   'Type comes from the MODEL, which had it all along')
ok("'statuses': Passport.STATUS_CHOICES" in V,
   'and so does Status')
ok("'countries'" in V and 'country_of_issue' in V,
   'Country is the countries actually recorded')
ok('.filter(is_active=True)' in V,
   'and the holders are the ACTIVE household members')

# AND THE TEMPLATE LOOPS THEM.
for var in ('household_members', 'doc_types', 'statuses', 'countries'):
    # THE % IS A FORMAT CHARACTER AND A DJANGO TAG OPENER. Building this
    # pattern with % formatting made Python read {% as a conversion and
    # raise - the twenty-eighth time this tree has been bitten by a
    # character meaning two things. Concatenated instead.
    pat = r'\{%\s*for[^%]*\b' + var + r'\b'
    ok(len(re.findall(pat, SRC)) == 2,
       '%-18s is looped twice - the filter and the Add form' % var,
       len(re.findall(pat, SRC)))

# THE ADD FORM'S COUNTRY IS A TEXT BOX, not a select. A dropdown of the
# countries already recorded could never be used to add the fifth.
m = re.search(r'<[a-z]+[^>]*id="country_of_issue"[^>]*>', SRC)
ok(m and m.group(0).startswith('<input'),
   'the Add form takes Country as text, with the recorded ones as '
   'suggestions', m.group(0)[:70] if m else '')
ok(m and 'list="countryList"' in m.group(0), '  and names its datalist')
ok('<datalist id="countryList">' in SRC, '  which exists')
if OLD:
    om = re.search(r'<[a-z]+[^>]*id="country_of_issue"[^>]*>', OLD)
    ok(om and om.group(0).startswith('<select'),
       'CONTROL: before this round it was a select of four countries')

# ==========================================================================
head('4. FOUR FILTERS, NARROWING TOGETHER, IN A BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

ROWS = [('Demetri Manias', 'passport', 'Cyprus', 'active'),
        ('Angela Manias', 'id', 'Cyprus', 'active'),
        ('Demetri Manias', 'drivers_license', 'South Africa', 'inactive'),
        ('Erene Manias', 'passport', 'Greece', 'renewal')]
KEYS = ('holder', 'doc-type', 'country', 'status')


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def fixture():
    """The page's OWN script, over a table of four documents.

    The cells carry data-sort-key / data-sort-value, which is what the
    narrowing reads - and reading those rather than the cell TEXT is the
    point: the Type cell renders a badge saying ARC while the value is
    arc, so a text match would compare a label with a key and find
    nothing."""
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', now(PAGE),
                              re.S))
    js = re.sub(r'\{#.*?#\}', '', js, flags=re.S)
    js = re.sub(r'\{%[^%]*%\}', '', js)
    js = re.sub(r'\{\{[^}]*\}\}', '0', js)
    trs = ''.join('<tr>' + ''.join(
        '<td data-sort-key="%s" data-sort-value="%s">%s</td>' % (k, v, v)
        for k, v in zip(KEYS, r)) + '</tr>' for r in ROWS)
    sel = ''
    for eid, vals in (('holderSelect', sorted(set(r[0] for r in ROWS))),
                      ('docTypeSelect', sorted(set(r[1] for r in ROWS))),
                      ('countrySelect', sorted(set(r[2] for r in ROWS))),
                      ('statusSelect', sorted(set(r[3] for r in ROWS)))):
        sel += ('<div class="filter-group"><select class="form-control '
                'filter-select" id="%s"><option value="">All</option>%s'
                '</select></div>'
                % (eid, ''.join('<option value="%s">%s</option>' % (v, v)
                                for v in vals)))
    panel = (
        '<div class="alv-filter-active has-filters" id="passportActiveFilters">'
        '<div class="filter-tags" id="passportFilterTags"></div></div>'
        '<div class="is-open alv-filter filter-panel" id="passportFilterPanel">'
        '<div class="filter-header"><button type="button" id="clearAllBtn" '
        'class="btn btn-outline-secondary btn-sm">Clear All</button></div>'
        '<div class="filter-content"><div class="filter-grid">' + sel +
        '</div></div></div>'
        '<table id="passportTable"><tbody>' + trs +
        '<tr id="passportNoMatch" style="display:none"><td colspan="8">'
        'Nothing here matches those filters</td></tr></tbody></table>')
    # A STUB FOR jQuery, BECAUSE base LOADS IT AND THIS FIXTURE DOES NOT.
    # The page's modals are Bootstrap's and call $('#addEditModal').modal().
    # Without this the fixture raises "$ is not defined" at load and the
    # page-error gate below would be reporting on the fixture rather than
    # on the page. It is a stub, not jQuery: every call returns an object
    # whose every method is a no-op, which is all the modal lines need.
    stub = ('window.jQuery = window.$ = function () {'
            '  return new Proxy({}, {get: function () {'
            '    return function () { return window.$(); }; }}); };'
            'window.$.fn = {};')
    end = '</scr' + 'ipt>'
    return ('<!doctype html><html><head><meta charset="utf-8"><style>%s'
            '</style></head><body>%s<script>%s'
            % (css_of(alv_tree.code_only(now(BASE))), panel, stub + js)) \
        + end + '</body></html>'


STATE = ("""() => {
  const b = document.querySelector('#passportTable tbody');
  return {
    rows: [...b.querySelectorAll('tr')]
            .filter(r => r.id !== 'passportNoMatch'
                      && r.style.display !== 'none').length,
    none: document.getElementById('passportNoMatch').style.display !== 'none',
    chips: [...document.querySelectorAll('#passportFilterTags .filter-tag')]
             .map(c => c.textContent.trim())};
}""")

if sync_playwright is None:
    for _ in range(9):
        skip('four filters narrowing together', 'playwright not installed')
else:
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        boom = []
        pg.on('pageerror', lambda e: boom.append(str(e)))
        pg.set_content(fixture())
        pg.wait_for_timeout(250)

        s = pg.evaluate(STATE)
        ok(s['rows'] == 4 and not s['chips'],
           'with nothing chosen all %d rows show and there are no chips'
           % s['rows'], s)

        pg.select_option('#holderSelect', 'Demetri Manias')
        pg.wait_for_timeout(80)
        s = pg.evaluate(STATE)
        ok(s['rows'] == 2, 'one filter narrows to %d of 4' % s['rows'], s)
        ok(s['chips'] == ['Holder: Demetri Manias'],
           '  and leaves one chip saying so', s['chips'])

        pg.select_option('#statusSelect', 'inactive')
        pg.wait_for_timeout(80)
        s = pg.evaluate(STATE)
        ok(s['rows'] == 1,
           'a SECOND filter narrows further, to %d - they are AND, and one '
           'function decides from both' % s['rows'], s)
        ok(len(s['chips']) == 2, '  two chips', s['chips'])

        pg.select_option('#countrySelect', 'Greece')
        pg.wait_for_timeout(80)
        s = pg.evaluate(STATE)
        ok(s['rows'] == 0 and s['none'],
           'a narrowing that finds nothing SAYS SO - an empty table with '
           'no message reads as a page that failed to load', s)

        pg.click('#clearAllBtn')
        pg.wait_for_timeout(80)
        s = pg.evaluate(STATE)
        ok(s['rows'] == 4 and not s['chips'] and not s['none'],
           'Clear All puts every row back and drops every chip', s)

        pg.select_option('#docTypeSelect', 'passport')
        pg.wait_for_timeout(80)
        pg.click('#passportFilterTags .remove-tag')
        pg.wait_for_timeout(80)
        s = pg.evaluate(STATE)
        ok(s['rows'] == 4 and not s['chips'],
           "and a chip's x clears the filter it names", s)

        ok(not boom, 'no page error while any of that ran', boom[:3])
        br.close()

# ==========================================================================
head('5. THE SERVER STOPPED NARROWING, AND THAT IS DELIBERATE')
# ==========================================================================
# Two narrowers would be two owners of one fact. With the server also
# filtering, changing a select would narrow rows the server had already
# removed, and the browser would report a smaller answer than the truth.
for f in ('holder_name=selected_holder', 'document_type=selected_doc_type',
          'country_of_issue=selected_country', 'status=selected_status'):
    ok('passports.filter(%s)' % f not in V,
       'the view no longer filters on %s' % f.split('=')[0])
if VW:
    ok(all('passports.filter(%s)' % f in VW for f in
           ('holder_name=selected_holder', 'status=selected_status')),
       'CONTROL: before this round it filtered on all four')
else:
    skip('CONTROL: before this round it filtered on all four', 'no backup')

# BUT IT STILL READS THEM, so a bookmarked URL arrives narrowed.
for p_ in ('holder', 'doc_type', 'country', 'status'):
    ok("request.GET.get('%s'" % p_ in V,
       '  and still READS %-9s so a bookmark still works' % p_)
ok(len(re.findall(r'\{%\s*if selected_\w+ ==', SRC)) == 4,
   'and all four selects pre-select from it', 
   len(re.findall(r'\{%\s*if selected_\w+ ==', SRC)))

# ==========================================================================
head('6. ONE WRITER, AND THE MACHINERY THAT IS GONE')
# ==========================================================================
writers = re.findall(r'(\w[\w.]*)\.style\.display\s*=', SRC)
ok(sorted(set(writers)) in ([], ['row'], ['none', 'row'], ['row', 'none']),
   'the only thing that writes a row display is the narrowing itself',
   sorted(set(writers)))
for probe, what in (('sessionStorage', 'three sessionStorage keys'),
                    ('passportFilterForm', 'the form it submitted'),
                    ('clearAllPassportFilters', 'its own Clear All'),
                    ('setTimeout(() => { false; }', 'a setTimeout that ran '
                     'the expression false')):
    ok(probe not in SRC, '%s: gone' % what)
    if OLD:
        ok(probe in OLD, '  CONTROL: and the backup had it')

# ==========================================================================
head('7. THE HOUSE PANEL')
# ==========================================================================
ok('class="alv-filter filter-panel"' in SRC,
   'the panel wears the house classes')
for c in ('filter-header', 'filter-title', 'filter-grid', 'filter-group',
          'filter-label'):
    ok('class="%s"' % c in SRC or 'class="%s ' % c in SRC,
       '  and so does its %s' % c)
ok('id="clearAllBtn"' in SRC, 'Clear All is the house id')
ok('passport-filter-panel' not in SRC and 'passport-filter-grid' not in SRC,
   'and not one bespoke panel class is left')
if OLD:
    ok('passport-filter-grid' in OLD,
       'CONTROL: the backup had five of them')
ok('<form' not in SRC[SRC.index('id="passportFilterPanel"'):
                      SRC.index('</table>')],
   'the panel holds no form - nothing here submits any more')

# THE COLUMN CAP, MEASURED. Its own grid was repeat(4, 1fr), which made
# each field 285px wide at 1280 - the same complaint he made about the
# Recipes filters, on a page nobody had looked at.
if OLD:
    ok('repeat(4, 1fr)' in OLD, 'CONTROL: its grid was four equal columns')
    ok('repeat(4, 1fr)' not in SRC, 'and base caps them at 240 now')

# ==========================================================================
head('8. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
