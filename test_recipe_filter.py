# -*- coding: utf-8 -*-
"""test_recipe_filter.py - Section F round F1, 30 Sep 2026.

Demetri: every module with a filter section should adopt the small Filter
button; the panel must not show on load and should open only when the
button is pressed. Recipe Management needs to change, and the A to Z and
the Grid / List / Book selector need to be teal.

MEASURED: ten of the eleven pages with a filter already did exactly that.
Recipe Management was not a page that had forgotten the component - it
was running a complete parallel copy of it: its own panel, its own
header, its own collapse, its own open/close function with its own
sessionStorage, and its own chip family in green.

SECTION 3 drives it in Chromium with base's real script, because "closed
on load, opens on the button" is behaviour and markup cannot answer it.

SECTION 5 records what was deliberately left: the chips are still a
fourth copy of a component base owns, and they sit INSIDE the panel - so
closing it now hides what you are filtering by. That is the next round.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_recfilter'
ME = 'test_recipe_filter.py'
PATCHER = 'apply_recipe_filter.py'
PAGE = 'recipe_management.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
ACCENT = 'rgb(14, 124, 139)'
GREEN = 'rgb(40, 167, 69)'

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def mk_of(t):
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


base = read(alv_tree.path_of('base.html'))
page = read(alv_tree.path_of(PAGE))

print('=' * 74)
print('%s - F1, RECIPE MANAGEMENT JOINS THE HOUSE FILTER' % ME)
print('=' * 74)

# ==========================================================================
head('1. ELEVEN OF ELEVEN')
# ==========================================================================
house, other = [], []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    m = mk_of(read(p))
    if 'action-filter' in m and 'alv-filter' in m:
        house.append(rel)
    elif re.search(r'filter-panel|filter-header|alv-filter', m):
        other.append(rel)
ok(PAGE in house, '%s wears the house filter' % PAGE)
ok(not other,
   'and NO page in the tree has a filter UI that is not the house one',
   other)
ok(len(house) == 11, 'eleven pages have one, all the same', len(house))

b = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(b):
    was = mk_of(read(b))
    ok('action-filter' not in was,
       'CONTROL: before this round this page had no Filter button')
    ok('toggleRecipeFilterPanel' in read(b),
       '  and opened its panel with a function of its own')
else:
    skipped += 2

# ==========================================================================
head('2. ONE THING OPENS THE PANEL')
# ==========================================================================
mk = mk_of(page)
ok('aria-controls="recipeFilterPanel"' in mk,
   'the button names the panel, which is how base finds it')
ok('class="alv-filter recipe-filter-panel"' in mk,
   '  and the panel wears .alv-filter')
ok('onclick="toggleRecipeFilterPanel()"' not in mk,
   'the header no longer opens it - two things toggling one panel is two '
   'things that can disagree')
ok('recipeFilterToggleIcon' not in page,
   '  and the chevron is gone entirely, markup and script')
ok(not re.search(r'function toggleRecipeFilterPanel', page),
   '  and so is the function')

ok(re.search(r'function expandRecipeFilterPanel', page) is not None,
   'expandRecipeFilterPanel is KEPT - the page reloads when a filter is '
   'applied, and the panel should come back open')
ok(len(re.findall(r'expandRecipeFilterPanel\(\)', page)) == 6,
   '  with its five callers untouched', 
   len(re.findall(r'expandRecipeFilterPanel\(\)', page)))
fn = re.search(r'function expandRecipeFilterPanel\(\)\s*\{(.*?)\n\}',
               page, re.S)
ok(fn and "classList.add('is-open')" in fn.group(1),
   '  and rewired to open the house panel', fn.group(1)[:120] if fn else '')
ok(fn and "aria-pressed" in fn.group(1),
   '  setting aria-pressed too, the way base\'s own setOpen does')

# ==========================================================================
head('3. CHROMIUM: CLOSED ON LOAD, OPEN ON THE BUTTON')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

if HAVE_PW:
    # BASE'S REAL SCRIPT, TAKEN AS A WHOLE BLOCK. The first version cut
    # it with a regex that ran to </body> and dragged the closing tags in
    # with it, so the fixture loaded a script that never parsed - and the
    # panel then "failed to open" for a reason that had nothing to do
    # with this round. Take the inline block that defines setOpen.
    blocks = [b for b in re.findall(r'<script>(.*?)</script>', base, re.S)
              if 'function setOpen' in b]
    base_js = blocks[-1] if blocks else ''
    ok(bool(base_js),
       'base\'s own filter script was found, so this section drives the '
       'real thing rather than a copy of it', len(base_js))
    fx = os.path.join(SCRATCH, 'recfilter.html')
    body = ('<div class="page-action-buttons">'
            '<button type="button" class="btn action-filter" id="filterBtn" '
            'aria-pressed="false" aria-controls="recipeFilterPanel">'
            '<i></i><span class="action-filter-label"> Filter</span>'
            '<span class="action-filter-count" data-count=""></span>'
            '</button></div>'
            '<div class="alv-filter recipe-filter-panel" '
            'id="recipeFilterPanel"><div class="recipe-filter-content">'
            '<form id="recipeFilterForm"></form></div></div>'
            '<div class="letter-filter-list">'
            '<a class="letter-filter-item available" id="az">A</a>'
            '<a class="letter-filter-item active" id="azon">B</a></div>'
            '<div class="view-toggle-buttons">'
            '<button class="view-toggle-btn active" id="vt">List</button>'
            '</div>')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>%s'
                 '<script>%s</script></body></html>'
                 % (css_of(base), css_of(page), body, base_js))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        pg.wait_for_timeout(250)
        shown = lambda s: pg.eval_on_selector(
            s, 'e => e.offsetParent !== null || '
               'getComputedStyle(e).display !== "none"')
        ok(not shown('#recipeFilterPanel'),
           'ON LOAD the panel is NOT shown - which is what was asked for')
        ok(pg.eval_on_selector('#filterBtn',
                               'e => e.getAttribute("aria-pressed")')
           == 'false', '  and the button says so')
        pg.click('#filterBtn')
        pg.wait_for_timeout(150)
        ok(shown('#recipeFilterPanel'),
           'pressing Filter opens it')
        ok(pg.eval_on_selector('#filterBtn',
                               'e => e.getAttribute("aria-pressed")')
           == 'true', '  and the button says so')
        pg.click('#filterBtn')
        pg.wait_for_timeout(150)
        ok(not shown('#recipeFilterPanel'), 'pressing it again closes it')

        tones = pg.evaluate('''() => {
            const g = id => {
              const c = getComputedStyle(document.getElementById(id));
              return [c.color, c.backgroundColor, c.borderTopColor];
            };
            return {az: g('az'), azon: g('azon'), vt: g('vt')};
        }''')
        ok(tones['az'][0] == ACCENT,
           'an available letter is the accent', tones['az'])
        ok(tones['azon'][1] == ACCENT,
           '  and the chosen one fills with it', tones['azon'])
        ok(tones['vt'][1] == ACCENT,
           'the chosen Grid / List / Book button fills with the accent',
           tones['vt'])
        for k, v in tones.items():
            ok(GREEN not in v, '  %s carries no green at all' % k, v)
        br.close()
else:
    skipped += 11

# ==========================================================================
head('4. THE COLLAPSE IT NO LONGER NEEDS')
# ==========================================================================
bare = re.sub(r'/\*.*?\*/', '', css_of(page), flags=re.S)
ok('.recipe-filter-content.expanded' not in bare,
   'the content has no .expanded rule - the PANEL opens now, not the '
   'content inside it')
m = re.search(r'\.recipe-filter-content\s*\{([^}]*)\}', bare)
ok(m and 'display: block' in m.group(1),
   '  and the content is simply visible', m.group(1) if m else '')
ok('.recipe-filter-toggle-icon' not in bare,
   '  and the chevron rule went with the chevron')
ok('cursor: pointer' not in (re.search(
    r'\.recipe-filter-header\s*\{([^}]*)\}', bare).group(1)
    if re.search(r'\.recipe-filter-header\s*\{([^}]*)\}', bare) else ''),
   '  and the header no longer looks clickable')

# ==========================================================================
head('5. WHAT THIS ROUND LEFT, AND SAID SO')
# ==========================================================================
ok('.recipe-filter-tag' in bare,
   'the chip family is still page-local - a fourth copy of something base '
   'owns, and its own round')
i_chips = mk.index('recipe-active-filters')
i_panel = mk.index('id="recipeFilterPanel"')
i_end = mk.index('</div>', mk.index('recipeFilterTags'))
ok(i_panel < i_chips,
   '  and still INSIDE the panel, which means closing the panel hides '
   'what you are filtering by - recorded here so the next round has it')
ok('#28a745' in bare,
   '  the green survives in those chip rules, and nowhere this round '
   'touched')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that the chips are in the right place. They')
print('  are not - they sit inside a panel that now closes. That is the')
print('  next round, and section 5 is the record of it.')
print('=' * 74)
sys.exit(1 if failed else 0)
