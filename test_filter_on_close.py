# -*- coding: utf-8 -*-
"""test_filter_on_close.py - Section F round F3, 30 Sep 2026.

Demetri, with two screenshots: Protein = Chicken chosen, the chip saying
"Protein: Chicken", the button saying "Filter 1" - and 48 of 317 recipes
on screen with no chicken in any of them. Press Apply Filters and the
same page shows 32, all chicken.

The chips and the count were describing the FORM, not the RESULTS. Ten
of the eleven pages with the house filter submit the moment a control
changes; this one had an Apply button, because its four filters are tick
lists and submitting per tick would reload the page per tick.

F3 applies when a tick list CLOSES. A menu records what was ticked when
it opened and compares when it closes; different, submit; the same, do
nothing, because opening a list to read it is not a filter change.

SECTION 3 IS THE ONE THAT MATTERS. Every claim above is about what
happens when somebody clicks, so it is driven in Chromium with the
page's own functions, its own listeners and a form whose submit() is
replaced by a counter. Eight scenarios, including the two that must NOT
submit.
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
try:
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_applyclose'
ME = 'test_filter_on_close.py'
PATCHER = 'apply_filter_on_close.py'
PAGE = 'recipe_management.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

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


def nocom(t):
    t = re.sub(r'<!--.*?-->|\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def mk_of(t):
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


PATH = alv_tree.path_of(PAGE)
page = read(PATH)
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else ''

print('=' * 74)
print('%s - F3, A FILTER THAT IS ON IS A FILTER THAT IS APPLIED' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ELEVEN, AND WHY THIS ONE WAS DIFFERENT')
# ==========================================================================
auto, manual = [], []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    t = read(p)
    m = mk_of(t)
    if not ('action-filter' in m and 'alv-filter' in m):
        continue
    if re.search(r'>\s*(?:<i[^>]*>\s*</i>\s*)?Apply\b', nocom(t)):
        manual.append(rel)
    else:
        auto.append(rel)
# TWELVE SINCE T4, 30 Sep 2026. Manage Lease Agreements joined the house
# filter (test_lease_filter.py). The number stays EXACT rather than
# becoming >= : this census exists so a page joining or leaving the set
# is visible, and >= would let a page leave in silence.
# twelve until 1 Oct 2026; F2 gave Receipts and Invoice
# Customers one each.
ok(len(auto) + len(manual) == 14, 'fourteen pages carry the house filter',
   len(auto) + len(manual))
ok(not manual,
   'and NOT ONE of them now waits for an Apply button - which is what '
   'Demetri saw: a chip saying a filter was on over a list that had not '
   'been filtered', manual)
if was:
    ok(re.search(r'>\s*(?:<i[^>]*>\s*</i>\s*)?Apply\b', nocom(was))
       is not None,
       'CONTROL: before this round, this page did')

# THE OTHER TEN SUBMIT ON CHANGE. That is the standard this round is
# bringing the eleventh to, so read it off them rather than asserting it.
submitters = [r for r in auto
              if re.search(r"addEventListener\(\s*'change'[^)]*\)?[\s\S]{0,200}?"
                           r"\.submit\(\)", read(alv_tree.join(r)))]
ok(len(submitters) >= 5,
   '%d of the other ten submit the form from a change handler - the '
   'pattern this round follows' % len(submitters), submitters[:4])

# ==========================================================================
head('2. ONE PLACE DECIDES WHETHER A CLOSE MEANS APPLY')
# ==========================================================================
js = nocom(page)
for fn in ('recipeMenuSignature', 'applyRecipeFilters', 'closeRecipeMenus'):
    ok(len(re.findall(r'function\s+%s\s*\(' % fn, js)) == 1,
       '%-22s is defined exactly once' % fn)
ok(len(re.findall(r"classList\.remove\('show'\)", js)) == 2,
   'exactly two lines close a menu, and both are inside the two functions '
   'that compare first - a third would be a close nobody measured',
   len(re.findall(r"classList\.remove\('show'\)", js)))
ok('closeRecipeMenus(null)' in js,
   'a click anywhere else on the page closes through the same function')
ok(re.search(r'nut\.addEventListener\(\s*.change.', js) is not None,
   'Sort by Nutrition is wired at last - it was the one control with no '
   'handler of any kind, and the only one that truly needed the button')
ok('Apply Filters' not in js, 'the Apply button is gone')
ok('filter-action-buttons' not in js,
   '  and the row it sat in, which held nothing else but a second '
   'Clear All')
ok(mk_of(page).count('onclick="clearAllRecipeFilters(event)"') == 1,
   '  leaving exactly one Clear All, the one in the panel header',
   mk_of(page).count('onclick="clearAllRecipeFilters(event)"'))
ok('btn-success' not in js,
   'and no green button survives on this page')
ok('class="search-btn"' in js and 'type="submit"' in js,
   'a submit button REMAINS - without one, Enter in the search box would '
   'stop searching, which would be a worse bug than the one being fixed')

# ==========================================================================
head('3. CHROMIUM: EIGHT THINGS A PERSON DOES')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def grab(name, text):
    """A top-level function, from `function name(` to the `}` in column 1."""
    m = re.search(r'^function\s+%s\s*\([^)]*\)\s*\{' % name, text, re.M)
    if not m:
        return ''
    end = text.find('\n}\n', m.start())
    return text[m.start():end + 2] if end > 0 else ''


def listener(text, needle):
    """The document listener whose body contains `needle`."""
    for m in re.finditer(r'^document\.addEventListener\(', text, re.M):
        end = text.find('\n});', m.start())
        blk = text[m.start():end + 4] if end > 0 else ''
        if needle in blk:
            return blk
    return ''


FNS = ('recipeMenuSignature', 'applyRecipeFilters', 'closeRecipeMenus',
       'toggleFilterDropdown', 'toggleFilterCheckbox', 'updateFilterDisplay',
       'updateRecipeActiveFilters', 'updateSearchPlaceholder')
parts = [grab(f, page) for f in FNS]
missing = [f for f, s in zip(FNS, parts) if not s]
outside = listener(page, 'filter-multiselect-dropdown')
wiring = listener(page, 'nutritionSortSelect')

ITEM = ('<div class="filter-multiselect-item" '
        'onclick="toggleFilterCheckbox(event, \'%s\')">'
        '<input type="checkbox" name="%s" value="%s" id="%s" '
        'onchange="updateFilterDisplay(\'%s\')"><span>%s</span></div>')


def group(kind, menu, opts):
    items = ''.join(ITEM % ('%s_%s' % (kind, v), kind, v,
                            '%s_%s' % (kind, v), kind, lab)
                    for v, lab in opts)
    return ('<div class="filter-multiselect-dropdown">'
            '<div class="filter-multiselect-button" id="%sBtn" '
            'onclick="toggleFilterDropdown(\'%s\')">'
            '<span id="%sFilterPlaceholder" '
            'class="filter-multiselect-placeholder">All</span></div>'
            '<div class="filter-multiselect-menu" id="%s">%s</div></div>'
            % (kind, menu, kind, menu, items))


BODY = ('<div id="away" style="height:60px">elsewhere</div>'
        '<div class="alv-filter-active" id="recipeActiveFilters">'
        '<span class="alv-filter-active-label">Active filters:</span>'
        '<div class="filter-tags" id="recipeFilterTags"></div></div>'
        '<form id="recipeFilterForm">'
        + group('protein', 'proteinMenu',
                [('3', 'Chicken'), ('4', 'Beef')])
        + group('course', 'courseMenu',
                [('1', 'Main'), ('2', 'Lunch')])
        + '<input type="text" id="searchInput" name="search" value="">'
          '<input type="radio" name="search_type" id="searchByName" checked>'
          '<input type="radio" name="search_type" id="searchByIngredient">'
          '<select id="nutritionSortSelect" name="nutrition_sort">'
          '<option value="" selected></option>'
          '<option value="calories">Calories</option></select>'
          '<input type="hidden" id="nutritionOrderInput" value="desc">'
          '<button type="submit" class="search-btn">go</button>'
        + '</form>')

if HAVE_PW and not missing and outside and wiring:
    ok(True, 'the page\'s own functions and both of its listeners were '
             'lifted out whole - this section drives the page, not a copy '
             'of it')
    fx = os.path.join(SCRATCH, 'onclose.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>.filter-multiselect-menu{display:none}'
                 '.filter-multiselect-menu.show{display:block}</style>'
                 '</head><body>%s<script>\n'
                 'var NUTRITION_SORT = "";\n'
                 'window.SUBMITS = 0;\n'
                 'HTMLFormElement.prototype.submit = '
                 'function () { window.SUBMITS++; };\n'
                 '%s\n%s\n%s\n</script></body></html>'
                 % (BODY, '\n\n'.join(parts), outside, wiring))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def fresh():
            _goto(pg, fx)
            pg.wait_for_timeout(180)

        def n():
            return pg.evaluate('() => window.SUBMITS')

        # 1 - the case Demetri photographed
        fresh()
        pg.click('#proteinBtn')
        pg.check('#protein_3')
        pg.click('#away')
        pg.wait_for_timeout(120)
        ok(n() == 1,
           'tick Chicken, click away: THE FILTER APPLIES - which is the '
           'whole round', n())

        # 2 - the reload that must not happen
        fresh()
        pg.click('#proteinBtn')
        pg.click('#away')
        pg.wait_for_timeout(120)
        ok(n() == 0,
           'open a list, change nothing, click away: nothing happens - '
           'reading a list is not filtering', n())

        # 3 - closed by its own button
        fresh()
        pg.click('#proteinBtn')
        pg.check('#protein_3')
        pg.click('#proteinBtn')
        pg.wait_for_timeout(120)
        ok(n() == 1, 'tick, then close the list with its own button: '
                     'applies', n())

        # 4 - closed by opening another
        fresh()
        pg.click('#proteinBtn')
        pg.check('#protein_3')
        pg.click('#courseBtn')
        pg.wait_for_timeout(120)
        ok(n() == 1,
           'tick, then reach straight for another list: the first applies',
           n())

        # 5 - THE REASON THIS PAGE HAS TICK LISTS AT ALL
        fresh()
        pg.click('#courseBtn')
        pg.check('#course_1')
        pg.check('#course_2')
        pg.click('#away')
        pg.wait_for_timeout(120)
        ok(n() == 1,
           'tick Main AND Lunch and leave: ONE reload, not two - which is '
           'why this page could not simply submit on every change', n())

        # 6 - back where it started
        fresh()
        pg.click('#proteinBtn')
        pg.check('#protein_3')
        pg.uncheck('#protein_3')
        pg.click('#away')
        pg.wait_for_timeout(120)
        ok(n() == 0,
           'tick and untick the same box: nothing happens, because '
           'nothing changed', n())

        # 7 - the control that had no handler at all
        fresh()
        pg.select_option('#nutritionSortSelect', 'calories')
        pg.wait_for_timeout(120)
        ok(n() == 1, 'Sort by Nutrition applies on change', n())

        # 8 - the radio, both ways round
        fresh()
        pg.click('#searchByIngredient')
        pg.wait_for_timeout(120)
        ok(n() == 0,
           'switch Name to Ingredient over an EMPTY box: nothing - '
           'rerunning an empty search would reload and change nothing',
           n())
        pg.fill('#searchInput', 'chicken')
        pg.click('#searchByName')
        pg.wait_for_timeout(120)
        ok(n() == 1, '  and with a term in the box, it re-searches', n())

        # AND THE THING THE WHOLE ROUND IS FOR: no closed state in which
        # the chips claim a filter that has not been applied.
        fresh()
        seen = pg.evaluate('''() => {
            const chips = () => document.querySelectorAll(
                '#recipeFilterTags .filter-tag').length;
            const menu = document.getElementById('proteinMenu');
            const before = chips();
            document.getElementById('proteinBtn').click();
            document.getElementById('protein_3').checked = true;
            document.getElementById('protein_3').dispatchEvent(
                new Event('change'));
            const mid = chips();
            document.getElementById('away').click();
            return {before: before, mid: mid, after: chips(),
                    open: menu.classList.contains('show'),
                    submits: window.SUBMITS};
        }''')
        ok(seen['mid'] == 1 and seen['submits'] == 1 and not seen['open'],
           'a chip can appear while the list is OPEN - that is a choice '
           'being made - but the list cannot close on it without the '
           'filter being applied', seen)
        br.close()
else:
    if not HAVE_PW:
        skipped += 11
    else:
        failed += 1
        print('  FAIL could not lift the page apart: missing %s%s%s'
              % (missing, '' if outside else ' +outside-listener',
                 '' if wiring else ' +wiring'))

# ==========================================================================
head('4. WHAT THE PAGE ALREADY DID, AND WHY THAT WAS THE TELL')
# ==========================================================================
# Removing a filter applied at once; adding one waited for a button. The
# page was arguing with itself, and these four are the half that was right.
for fn in ('clearSingleFilter', 'clearRecipeFilterGroup',
           'clearNutritionSort', 'toggleNutritionOrder'):
    body = grab(fn, page)
    ok(bool(body) and '.submit()' in body,
       '%-24s submitted the form already, before this round' % fn)
ok(bool(was) and 'Apply Filters' in was,
   '  while ADDING a filter waited for Apply - the same page, two minds')

# ==========================================================================
head('5. SCOPE')
# ==========================================================================
if was:
    import difflib
    a, b = was.split('\n'), page.split('\n')
    regions = {
        'toggleFilterDropdown': 'function toggleFilterDropdown',
        'the outside-click listener': "closest('.filter-multiselect-dropdown')",
        'the Apply row': 'filter-action-buttons',
        'its rule': '.filter-action-buttons {',
        'its phone rule': '.filter-action-buttons { flex-direction',
    }
    lines = set()
    for _name, needle in regions.items():
        for i, ln in enumerate(a):
            if needle in ln:
                lines.update(range(max(0, i - 12), i + 14))
    stray = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        out = [k for k in range(i1, i2) if k not in lines]
        if out:
            stray.append('%s old line %d: %r' % (tag, out[0] + 1,
                                                 a[out[0]][:70]))
    ok(not stray,
       'every edit falls in one of the five places this round declared',
       '\n'.join(stray[:5]))
    ok('recipe-filter-grid' in page and 'letter-filter-item' in page,
       '  and the panel, the A-Z and the view toggle are untouched')
else:
    skip('scope', 'no %s backup' % SUFFIX)
    skip('scope', 'no %s backup' % SUFFIX)

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
    skip('the gate', '%s not on disk' % PS1)
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that the server returns the right recipes. That')
print('  was never in doubt - the second screenshot shows it returning')
print('  exactly the right 32. What was wrong was that the page let you')
print('  stand in front of a list it had not filtered while telling you')
print('  it had.')
print('=' * 74)
sys.exit(1 if failed else 0)
