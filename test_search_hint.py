# -*- coding: utf-8 -*-
"""test_search_hint.py - Section N round N3, 1 Oct 2026.

Demetri named six searches that do not narrow as you type. Four now do.
Two cannot, and say so under the box.

THE ONE THING THIS ROUND CAN GET WRONG is that the box and the glass
disagree. Every one of these inputs ALSO posts to a server filter. If
the live filter reads a different set of columns from the ones the view
ORs together, then a query the server would answer with three rows
narrows the screen to one, and the user never learns the other two
exist. That is worse than having no live filter.

So section 3 does not read the template. It reads THE VIEW, pulls out
the model fields that view actually filters on, and checks there are as
many of them as the template names columns. A fifth Q() added to fsr
next year breaks this suite, which is the point.

And section 5 drives base's OWN controller in Chromium over a
two-column table, typing queries that hit the heading only, the
description only, both and neither, and compares each answer with what
the server's OR would return. Measured:

    'boiler'    server 1 | live 1      heading only
    'pilot'     server 1 | live 1      DESCRIPTION only
    'engineer'  server 1 | live 1      description only
    'zzz'       server 0 | live 0      and the empty note shows
    ''          server 4 | live 4

The control forces the controller back to ONE column and runs the same
seven queries: two of them then disagree with the server. That is the
whole argument for making the attribute a list, and it is measured
rather than asserted.
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

SUFFIX = '.bak_searchhint'
ME = 'test_search_hint.py'
PATCHER = 'apply_search_hint.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

# rel -> (view file, the model fields that view ORs, the data-labels the
# template names, the table selector). The fields are what makes this
# suite worth running: they are read back out of the view.
OPT_IN = {
    'properties.html': ('properties.py', ['prop_name__icontains'],
                        ['Property'], '.properties-table'),
    'act_expense.html': ('expenses.py', ['act_expense_description__icontains'],
                         ['Description'], '.expense-table'),
    'fsr.html': ('issues.py', ['issues_heading__icontains',
                               'issues_description__icontains'],
                 ['Issue', 'Description'], '#issuesTable'),
    'tenant_lease_agreement.html': ('tenants.py',
                                    ['tenant_name__icontains',
                                     'prop__prop_name__icontains'],
                                    ['Tenant', 'Property'],
                                    '.lease-agreements-table'),
}
# rel -> why it cannot have the live filter, in one phrase
HINTED = {
    'projects/projects.html':
        'searches project_description, which has no column, and pages at 25',
    'recipe_management.html':
        'searches ingredient names, which are never rendered, and pages at 48',
}

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
    p = alv_tree.join(rel.replace('/', os.sep))
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


def view(name):
    p = os.path.join(ROOT, 'pages', 'views', name)
    return read(p) if os.path.isfile(p) else None


base = left('base.html')

print('=' * 74)
print('%s - N3, THE REST OF THE SEARCH BOXES' % ME)
print('=' * 74)

# ==========================================================================
head('1. base CARRIES THE HINT STYLE AND THE v2 CONTROLLER')
# ==========================================================================
bcss = css_of(base)
ok(bool(re.search(r'(?<![-\w])\.alv-search-hint\s*\{', bcss)),
   'base draws .alv-search-hint')
ok('var(--alv-ink-soft)' in
   (re.search(r'\.alv-search-hint\s*\{([^}]*)\}', bcss).group(1)
    if re.search(r'\.alv-search-hint\s*\{([^}]*)\}', bcss) else ''),
   '  and draws it in a token, not a literal grey')
ok('alv-live-search v2' in base,
   'the controller is at v2')
ok('alv-live-search v1' not in base,
   '  and v1 is not still beside it')
# The list, in the controller itself - not a comment claiming a list.
js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', base, re.S))
ok(".split(',')" in js and 'labels.length' in js,
   'it splits data-live-search-cell on commas and loops the names')
ok('the whole row' in base and 'pressed with Enter' in base,
   '  and still says in writing why it must not match the whole row')

# ==========================================================================
head('2. THE FOUR THAT OPTED IN')
# ==========================================================================
for rel, (vf, fields, labels, sel) in sorted(OPT_IN.items()):
    t = left(rel)
    m = markup_of(t)
    tag = re.search(r'<input[^>]*id="searchInput"[^>]*>', m, re.S)
    if not ok(tag is not None, '%s has its search input' % rel):
        continue
    tag = tag.group(0)
    got_sel = re.search(r'data-live-search="([^"]*)"', tag)
    got_cell = re.search(r'data-live-search-cell="([^"]*)"', tag)
    ok(got_sel is not None and got_sel.group(1) == sel,
       '%-28s narrows %s' % (rel, sel),
       'it names %s' % (got_sel.group(1) if got_sel else None))
    ok(got_cell is not None
       and [x.strip() for x in got_cell.group(1).split(',')] == labels,
       '%-28s on %s' % ('', ','.join(labels)),
       'it names %s' % (got_cell.group(1) if got_cell else None))
    # THE SELECTOR MUST FIND EXACTLY ONE TABLE. act_expense carries four.
    if sel.startswith('#'):
        n = len(re.findall(r'<table[^>]*id="%s"' % sel[1:], m))
    else:
        n = len([x for x in re.finditer(r'<table[^>]*class="([^"]*)"', m)
                 if sel[1:] in x.group(1).split()])
    ok(n == 1, '%-28s and that selector finds exactly one table' % '',
       'it finds %d' % n)
    # AND EVERY NAMED COLUMN EXISTS, or the filter hides every row.
    missing = [x for x in labels if 'data-label="%s"' % x not in m]
    ok(not missing, '%-28s and every named column is on the page' % '',
       'missing %s' % missing)

# ==========================================================================
head('3. THE LIVE FILTER READS THE COLUMNS THE VIEW FILTERS ON')
# ==========================================================================
# This is the check that matters. Everything else is spelling.
for rel, (vf, fields, labels, sel) in sorted(OPT_IN.items()):
    src = view(vf)
    if src is None:
        skip('%s against %s' % (rel, vf), 'the view is not on disk')
        continue
    found = [f for f in fields if f in src]
    ok(len(found) == len(fields),
       '%-28s the view really filters on %s' % (rel, ', '.join(fields)),
       'not found: %s' % [f for f in fields if f not in src])
    # AND NO MORE THAN THOSE. A fifth Q() added later must break this.
    every = set(re.findall(r'(\w+(?:__\w+)*__icontains)\s*=', src))
    extra = sorted(every - set(fields))
    ok(len(fields) == len(labels),
       '%-28s and names one column per field (%d and %d)'
       % ('', len(fields), len(labels)))
    if extra:
        print('       note: %s also contains %s - check they belong to a '
              'different view' % (vf, extra[:3]))

# ==========================================================================
head('4. THE TWO THAT CANNOT, AND SAY SO')
# ==========================================================================
for rel, why in sorted(HINTED.items()):
    t = left(rel)
    m = markup_of(t)
    ok('alv-search-hint' in m, '%-28s carries the hint' % rel)
    ok('data-live-search' not in t,
       '%-28s and does NOT carry a live filter' % '')
    print('       because it %s' % why)
# and the reason is a real one: both views paginate
for vf, page_of in (('projects.py', 'projects'),
                    (os.path.join('recipes', 'recipe_crud.py'), 'recipes')):
    src = view(vf)
    if src is None:
        skip('%s paginates' % vf, 'not on disk')
        continue
    ok('Paginator(' in src, '%-28s %s really does paginate' % ('', page_of))

# ==========================================================================
head('5. THE CONTROLLER, IN A BROWSER, AGAINST THE SERVER\'S OWN ANSWER')
# ==========================================================================
ISSUES = [('Boiler will not fire', 'The pilot light keeps going out'),
          ('Garden gate hinge', 'Rusted through, will not latch'),
          ('Kitchen tap drips', 'Constant drip, worse at night'),
          ('Lift out of service', 'Engineer booked for Tuesday')]
CASES = ['boiler', 'pilot', 'drip', 'gate', 'engineer', 'zzz', '']


def server_says(q):
    """heading OR description - exactly what issues.py does."""
    q = q.lower().strip()
    if not q:
        return len(ISSUES)
    return sum(1 for h, d in ISSUES if q in h.lower() or q in d.lower())


def controller_of(src):
    for s in re.findall(r'<script\b[^>]*>(.*?)</script>', src, re.S):
        if 'data-live-search' in s and 'function wire' in s:
            return s
    return None


def drive(cells, script, tag):
    """Type each case into a real box and count what stays visible."""
    from playwright.sync_api import sync_playwright
    rows = ''.join('<tr><td data-label="Issue">%s</td>'
                   '<td data-label="Description">%s</td></tr>' % (h, d)
                   for h, d in ISSUES)
    fx = os.path.join(SCRATCH, 'fx_%s.html' % tag)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8"></head>'
                 '<body><input id="searchInput" '
                 'data-live-search="#issuesTable" '
                 'data-live-search-cell="%s">'
                 '<table id="issuesTable"><tbody>%s</tbody></table>'
                 '<script>%s</script></body></html>' % (cells, rows, script))
    out, errs = [], []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1100, 'height': 600})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        _goto(pg, fx)
        for q in CASES:
            pg.fill('#searchInput', q)
            pg.dispatch_event('#searchInput', 'input')
            out.append(pg.evaluate(
                "() => Array.from(document.querySelectorAll("
                "'#issuesTable tbody tr')).filter("
                "r => !r.classList.contains('alv-live-search-empty')"
                " && r.offsetParent !== null).length"))
        br.close()
    return out, errs


try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

script = controller_of(base)
if not have_pw:
    skip('the controller in a browser', 'playwright is not installed')
elif not script:
    ok(False, 'the controller could be lifted out of base.html')
else:
    got, errs = drive('Issue,Description', script, 'two')
    want = [server_says(q) for q in CASES]
    for q, g, w in zip(CASES, got, want):
        ok(g == w, '%-10r server %d, live %d' % (q, w, g))
    ok(not errs, '  and the console is silent', errs)

# ==========================================================================
head('6. THE CONTROL - ONE COLUMN MUST DISAGREE WITH THE SERVER')
# ==========================================================================
# A check that cannot fail is not a check. Section 5 passing proves the
# two-column read works; it does not prove the second column was needed.
# This runs the same seven queries with only the heading named - which is
# exactly what v1 would have done - and the answers MUST diverge.
if not have_pw or not script:
    skip('the control', 'playwright or the controller is unavailable')
else:
    one, errs1 = drive('Issue', script, 'one')
    want = [server_says(q) for q in CASES]
    diff = [(q, w, g) for q, w, g in zip(CASES, want, one) if w != g]
    ok(len(diff) >= 2,
       'with one column named, at least two queries disagree',
       'they all agreed: %s' % list(zip(CASES, one)))
    for q, w, g in diff:
        print('       %-10r server would say %d, one column says %d'
              % (q, w, g))
    ok(not errs1, '  and it failed by giving a wrong answer, not by '
                  'crashing', errs1)

# ==========================================================================
head('7. SUPPLIERS, WHICH CAME IN AT v1, IS UNTOUCHED')
# ==========================================================================
sup = left('suppliers.html')
m = re.search(r'data-live-search-cell="([^"]*)"', sup)
ok(m is not None and ',' not in m.group(1),
   'suppliers still names one column, %r' % (m.group(1) if m else None))
ok(not os.path.isfile(alv_tree.path_of('suppliers.html') + SUFFIX),
   '  and this round did not back it up, because it did not touch it')
if have_pw and script:
    got, _ = drive('Issue', script, 'compat')
    ok(got[0] == 1 and got[-1] == len(ISSUES),
       '  and a single name still filters, so v1\'s pages keep working')

# ==========================================================================
head('8. THE GATE')
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
print('  STILL ON THE SERVER, and not candidates: ingredient_base_units')
print('  and unit_conversions_management both render every row and could')
print('  opt in, but Demetri did not name them and nobody has walked')
print('  those screens. They are a decision, not an oversight.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
