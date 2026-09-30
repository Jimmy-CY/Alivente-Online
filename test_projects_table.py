# -*- coding: utf-8 -*-
"""test_projects_table.py - Section P round P1, 30 Sep 2026.

Demetri, on Projects: "This table does not comply."

It did not. Edit and Delete sat in two columns with two headers, Delete
was a filled red button the height of the row and Edit a small pale one
beside it, and fifteen rules on the page held it together - including a
literal #dc3545, a hand-built 33.33% three-up grid for the phone, and
.btn-label-text { display: none }, which is a label the markup wrote and
the stylesheet then hid on every screen there is.

The header row also declared widths summing to 110%. The browser
normalises that, so nobody ever saw it - which is the point: the widths
were never a decision, only an accumulation.

SECTION 4 IS THE CLAIM. Chromium draws the row at both widths. On a
desktop: one actions cell, three buttons the SAME SIZE, the header
centred over them. On a phone: that cell steps aside and base's
.mobile-action-bar takes over as a three-up grid. Delete being the size
of Edit is the whole of what Demetri asked for, and it is measured
rather than described.
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

SUFFIX = '.bak_projtable'
ME = 'test_projects_table.py'
PATCHER = 'apply_projects_table.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join('projects', 'projects.html')
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
# base's own tokens, so the numbers below are the system's, not mine.
VIEW = 'rgb(14, 124, 139)'    # --alv-accent
DELETE = 'rgb(179, 38, 30)'   # --alv-bad
BOOTSTRAP_RED = 'rgb(220, 53, 69)'

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


def no_comments(s):
    """Lesson 21. This round ships two long comments naming every class
    the gates look for - one in the markup and one in the stylesheet."""
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', no_comments(t), flags=re.S)


def left(rel):
    p = alv_tree.join(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


page = left(PAGE)
base = read(alv_tree.path_of('base.html'))
bak = alv_tree.join(PAGE) + SUFFIX

print('=' * 74)
print('%s - P1, THE PROJECTS TABLE JOINS THE STANDARD' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE TABLE WEARS THE STANDARD')
# ==========================================================================
mk = markup_of(page)
tag = re.search(r'<table[^>]*projects-table[^>]*>', mk)
ok(bool(tag), 'the projects table is still there')
if tag:
    cls = re.search(r'class="([^"]*)"', tag.group(0)).group(1).split()
    ok('alv-table' in cls, '  it joins .alv-table', cls)
    ok('projects-table' in cls, '  and keeps its own name for the rest', cls)
    for gone in ('table-bordered', 'table-striped', 'text-center'):
        ok(gone not in cls, '  %s is gone from the class list' % gone, cls)
    ok('table' in cls, '  Bootstrap .table survives - it sets the metrics')

# ==========================================================================
head('2. ONE ACTIONS COLUMN, NOT TWO')
# ==========================================================================
for name, n in (('>Actions<', 1), ('>Edit</th>', 0), ('>Delete</th>', 0),
                ('cell-actions', 2), ('desktop-action-cell', 2),
                ('row-actions', 1), ('mobile-action-bar cols-3', 1),
                ('cell-action--view-mobile', 0), ('btn-label-text', 0),
                ('delete-btn', 0), ('action-btn--view', 0)):
    ok(mk.count(name) == n, '%-26s appears %d time(s)' % (name, n),
       '%d time(s)' % mk.count(name))
# THE WIDTHS SUMMED TO 110 BEFORE. Nobody saw it, because the browser
# normalises - which is exactly why it was never a decision.
w = [int(x) for x in re.findall(r'<th[^>]*width:\s*(\d+)%', mk)]
ok(len(w) == 7 and sum(w) == 100,
   'seven columns, and the widths sum to 100', '%d columns, %d%%'
   % (len(w), sum(w)))
if os.path.isfile(bak):
    wasmk = markup_of(read(bak))
    w0 = [int(x) for x in re.findall(r'<th[^>]*width:\s*(\d+)%', wasmk)]
    ok(len(w0) == 8 and sum(w0) == 110,
       'CONTROL: before, eight columns summing to 110%',
       '%d columns, %d%%' % (len(w0), sum(w0)))
    ok(wasmk.count('>Edit</th>') == 1 and wasmk.count('>Delete</th>') == 1,
       '  CONTROL: and Edit and Delete each had a header of their own')
else:
    skip('the before and after', 'no %s backup' % SUFFIX)
# THE DISABLED TWINS ARE DRAWN, NOT DROPPED, so the cluster is the same
# width on a row the permissions have narrowed.
ok(mk.count('icon-disabled') == 2,
   'both restricted slots keep a disabled twin on the desktop',
   mk.count('icon-disabled'))
ok(mk.count('mobile-action-disabled') == 2, '  and both on the phone',
   mk.count('mobile-action-disabled'))
ok(mk.count('perms.auth.can_edit_projects') >= 2,
   'every can_edit_projects gate survived the collapse',
   mk.count('perms.auth.can_edit_projects'))
# FOUR DISTINCT GLYPHS, so no two buttons look alike.
gl = set(re.findall(r'fa-(eye|pencil-alt|trash)', mk))
ok(gl == {'eye', 'pencil-alt', 'trash'},
   'three distinct glyphs, and Edit uses the house pencil', sorted(gl))
ok('fa-edit' not in mk,
   '  not fa-edit - .icon-edit draws fa-pencil-alt on all 22 pages that '
   'have one, which test_row_personal.py holds')

# ==========================================================================
head('3. FIFTEEN RULES LEFT, AND base OWNED EVERY ONE')
# ==========================================================================
css = css_of(page)
for name in ('action-btn', 'cell-action', 'btn-label-text', 'delete-btn'):
    n = len(re.findall(r'(?m)^[ \t]*[^{}\n]*\.' + name
                       + r'[a-zA-Z-]*[^{}\n]*\{', css))
    ok(n == 0, '.%-18s has no rules left - base owns it now' % name, n)
if os.path.isfile(bak):
    wascss = css_of(read(bak))
    n0 = len(re.findall(r'(?m)^[ \t]*[^{}\n]*\.(?:action-btn|cell-action|'
                        r'btn-label-text|delete-btn)[a-zA-Z-]*[^{}\n]*\{',
                        wascss))
    ok(n0 == 15, 'CONTROL: there were fifteen of them', n0)
    ok('#dc3545' in wascss, '  CONTROL: including a literal Bootstrap red')
ok('#dc3545' not in css, 'and no literal Bootstrap red survives')
# THE PAGE KEEPS WHAT IS GENUINELY ITS OWN.
for name, least in (('project-name-link', 3), ('progress-container', 1),
                    ('progress-bar', 1)):
    n = len(re.findall(r'\.' + name + r'\b[^{}]*\{', css))
    ok(n >= least, 'KEPT .%-20s %d rule(s)' % (name, n))
# AND WRITES NOTHING base ALREADY HAS.
own = re.findall(r'(?m)^[ \t]*[^{}\n]*\.(?:icon-action-btn|icon-view|'
                 r'icon-edit|icon-delete|icon-disabled|row-actions|'
                 r'cell-actions|mobile-action-|desktop-action-cell|'
                 r'table-container)[a-zA-Z-]*[^{}\n]*\{', css)
ok(not own, 'and the page writes no rule base already owns',
   [x.strip() for x in own[:4]])

# ==========================================================================
head('4. CHROMIUM: DELETE IS THE SIZE OF EDIT')
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


def resolve(s):
    """Django out, keeping the {% if %} branch - the permitted user,
    which is the row Demetri was looking at."""
    while True:
        m = re.search(r'\{%\s*if\b[^%]*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                      r'\{%\s*else\s*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                      r'\{%\s*endif\s*%\}', s, re.S)
        if not m:
            break
        s = s[:m.start()] + m.group(1) + s[m.end():]
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Sample', s, flags=re.S)


def table_of(t):
    i = t.find('projects-table')
    j = t.rfind('<table', 0, i)
    if i < 0 or j < 0:
        return None
    d = 0
    for m in re.finditer(r'<table\b|</table>', t[j:]):
        d += 1 if m.group(0) != '</table>' else -1
        if d == 0:
            return resolve(t[j:j + m.end()])
    return None


LOOK = '''() => {
  const cell = document.querySelector("td.cell-actions");
  const th = document.querySelector("th.cell-actions");
  const bar = document.querySelector(".mobile-action-bar");
  const btns = [...document.querySelectorAll("td.cell-actions .icon-action-btn")]
    .map(e => { const r = e.getBoundingClientRect();
                return {w: Math.round(r.width), h: Math.round(r.height),
                        col: getComputedStyle(e).color}; });
  const tiles = bar ? [...bar.querySelectorAll(".mobile-action-btn")]
    .map(e => Math.round(e.getBoundingClientRect().width)) : [];
  return {cells: document.querySelectorAll("td.cell-actions").length,
          btns: btns, tiles: tiles,
          thAlign: th ? getComputedStyle(th).textAlign : "-",
          cellShown: cell ? getComputedStyle(cell).display !== "none" : false,
          bar: bar ? getComputedStyle(bar).display : "-",
          cols: bar ? getComputedStyle(bar).gridTemplateColumns
                        .split(" ").length : 0,
          scrollW: document.documentElement.scrollWidth,
          clientW: document.documentElement.clientWidth};
}'''

if HAVE_PW and BOOT and table_of(page):
    with sync_playwright() as pw:
        br = sync_playwright  # placeholder, replaced below
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(basecss, pagecss, mkup, name, w, h):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, basecss, pagecss, mkup))
            pg.set_viewport_size({'width': w, 'height': h})
            _goto(pg, f)
            pg.wait_for_timeout(120)
            return pg.evaluate(LOOK)

        mkup = table_of(page)
        d = draw(css_of(base), css_of(page), mkup, 'desk.html', 1280, 900)
        print('     desktop  %d button(s): %s'
              % (len(d['btns']), [(b['w'], b['h']) for b in d['btns']]))
        ok(d['cells'] == 1, 'one actions cell per row, not three', d['cells'])
        ok(len(d['btns']) == 3, '  three buttons in it', len(d['btns']))
        sizes = set((b['w'], b['h']) for b in d['btns'])
        ok(len(sizes) == 1,
           '  and DELETE IS THE SIZE OF EDIT - all three identical',
           sorted(sizes))
        ok(d['thAlign'] == 'center',
           '  the header is centred over them', d['thAlign'])
        cols = [b['col'] for b in d['btns']]
        ok(cols[0] == VIEW, '  View is the accent teal', cols[0])
        ok(cols[-1] == DELETE, '  Delete is the token red', cols[-1])
        ok(BOOTSTRAP_RED not in cols,
           '  and not one of them is Bootstrap red', cols)
        ok(len(set(cols)) == 3, '  three different colours, one per verb',
           cols)
        ok(d['bar'] == 'none', '  the phone bar is not drawn on a desktop',
           d['bar'])

        m = draw(css_of(base), css_of(page), mkup, 'phone.html', 390, 900)
        print('     phone    bar %s, %d tile(s): %s'
              % (m['bar'], len(m['tiles']), m['tiles']))
        ok(not m['cellShown'],
           'on a phone the desktop cell steps aside')
        ok(m['bar'] == 'grid', '  and base\'s action bar takes over',
           m['bar'])
        ok(m['cols'] == 3, '  as a three-up grid', m['cols'])
        ok(len(set(m['tiles'])) == 1 and m['tiles'],
           '  with every tile the same width', m['tiles'])
        ok(m['scrollW'] <= m['clientW'] + 1,
           '  and the row fits the phone', '%d in %d'
           % (m['scrollW'], m['clientW']))

        # CONTROL - the probe sees the old shape as the old shape.
        if os.path.isfile(bak):
            wasmk = table_of(read(bak))
            if wasmk:
                c = draw(css_of(base), css_of(read(bak)), wasmk, 'was.html',
                         1280, 900)
                ok(c['cells'] == 0 and not c['btns'],
                   'CONTROL: before this round there was no actions cell at '
                   'all - three separate ones instead',
                   '%d cell(s), %d button(s)' % (c['cells'], len(c['btns'])))
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable, or no table found')

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
print('  REPORTED, NOT CHANGED. projects.html is the only list in the')
print('  system that paginates - 25 to a page - so its row count is')
print('  bounded where every other list draws everything. That is why it')
print('  is the one page where searching in the browser rather than at')
print('  the server would be wrong. Nothing here changes it.')
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
