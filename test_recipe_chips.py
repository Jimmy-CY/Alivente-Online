# -*- coding: utf-8 -*-
"""test_recipe_chips.py - Section F round F2, 30 Sep 2026.

F1 gave Recipe Management the house Filter button and a panel that is
closed on load. Its own section 5 recorded what it had left: the
active-filter chips were still a page-local copy of a component base
owns, and they were INSIDE the panel - so closing the panel hid what the
list was filtered by. base's comment on the component says exactly that:
"a closed panel must never mean invisible filtering."

This round moves the row out, onto base's classes, and stops the page
recording the row's visibility - base's wireCount counts the chips and
toggles .has-filters itself, and numbers the Filter button from them.

SECTION 3 IS WHERE THIS ROUND IS EITHER TRUE OR NOT. "The chips are
visible while the panel is closed" is behaviour: it depends on base's
CSS, base's script and the page's own chip writer all at once, and no
amount of reading the markup answers it. So the fixture runs the page's
REAL function, in Chromium, inside base's REAL script - and then runs the
page as it was before this round in the same fixture, which is the
control that must fail.
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
import difflib
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_recchips'
ME = 'test_recipe_chips.py'
PATCHER = 'apply_recipe_chips.py'
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
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def nocomment(t):
    """CSS, HTML and JS comments out. Lesson 21: a gate that reads the
    round's own explanation of what it removed finds every word it came
    to look for."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', t)


def mk_of(t):
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


PATH = alv_tree.path_of(PAGE)
BAK = PATH + SUFFIX
base = read(alv_tree.path_of('base.html'))
# AS F2 LEFT IT - lesson 17. Every section below judges what F2 did,
# and a later round editing this same page must not make F2's own
# scope check report strays. F3 was that round, on 30 Sep.
try:
    from alv_rounds import as_left_by
    page = as_left_by(PATH, SUFFIX, read)
except Exception:
    page = read(PATH)
was = read(BAK) if os.path.isfile(BAK) else ''

print('=' * 74)
print('%s - F2, THE CHIPS COME OUT OF THE PANEL' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ROUND THE CHIP ROUND DEFERRED')
# ==========================================================================
# ALV FILTER CHIP v1 took nine pages on 22 Sep and stopped at this one,
# saying so in a check of its own. That line is the reason this round
# exists, so read it rather than paraphrase it.
chip_suite = os.path.join(ROOT, 'test_filter_chip.py')
if os.path.isfile(chip_suite):
    cs = read(chip_suite)
    ok('untouched until its own round' in cs and PAGE in cs,
       'the chip round deferred this page explicitly, and this is that '
       'round')
    ok(not os.path.isfile(PATH + '.bak_chip'),
       '  and it kept its word - the chip round left no backup here')
else:
    skip('the chip round\'s deferral', 'test_filter_chip.py not on disk')
    skip('its backup', 'test_filter_chip.py not on disk')

b_css = nocomment(css_of(base))
for sel in ('.filter-tags', '.filter-tag', '.filter-tag .remove-tag'):
    ok(re.search(r'(?:^|[,{}\s])' + re.escape(sel) + r'\s*[,{]', b_css,
                 re.M) is not None,
       'base owns %-24s so the page does not have to' % sel)
ok('.alv-filter-active.has-filters' in b_css,
   'base owns the row, shown by a class')

p_css = nocomment(css_of(page))
for gone in ('.recipe-active-filters', '.recipe-filter-tags',
             '.recipe-filter-tag', '.recipe-remove-tag'):
    ok(gone not in p_css, '%-26s is no longer page-local' % gone)
# AND IT DOES NOT REDEFINE base'S EITHER. Deleting the copy and then
# writing .filter-tag { background: #28a745 } on the page would pass every
# check above and change nothing on screen.
mine = re.findall(r'(?:^|[,{}\s])\.(?:filter-tags?|remove-tag'
                  r'|alv-filter-active(?:-label)?)\b[^{]*\{([^}]*)\}',
                  p_css, re.M)
ok(not mine, 'and the page does not redefine base\'s chip either', mine[:2])

# ==========================================================================
head('2. OUT OF THE PANEL, AND OUT OF THE FORM')
# ==========================================================================
mk = mk_of(page)
ok(mk.count('class="alv-filter-active"') == 1,
   'the page has exactly one chip row',
   mk.count('class="alv-filter-active"'))
ok('class="filter-tags"' in mk and 'alv-filter-active-label' in mk,
   '  wearing base\'s holder and base\'s label - the class names ARE the '
   'interface, because scripts build the chips at run time')
# find, NOT index. A revert control has to FAIL and not CRASH: with the
# round undone there is no row to index, and a traceback here would take
# the rest of the suite with it and say far less about why.
i_row = mk.find('class="alv-filter-active"')
i_panel = mk.find('id="recipeFilterPanel"')
i_form = mk.find('id="recipeFilterForm"')
ok(0 <= i_row < i_panel,
   'THE POINT OF THIS ROUND: the row comes BEFORE the panel, so closing '
   'the panel cannot hide it', '%d vs %d' % (i_row, i_panel))
ok(0 <= i_row < i_form, '  and before the form the panel contains')
ok(i_row >= 0 and 'style="display' not in mk[max(0, i_row - 200):i_row + 200],
   '  and carries no inline display - base starts it hidden and shows it '
   'by class, so there is no flash of "Active filters:" with nothing '
   'after it')
ok('<span>Active filters:</span>' not in mk,
   'the bare label span is gone, as on the other ten pages')

if was:
    was_mk = mk_of(was)
    ok(0 <= was_mk.find('id="recipeFilterPanel"')
       < was_mk.find('recipe-active-filters'),
       'CONTROL: before this round the row was INSIDE the panel')
    ok('style="display: none;"' in was_mk,
       '  and started hidden by an inline style')
else:
    skip('the control', 'no %s backup' % SUFFIX)
    skip('the control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. CHROMIUM: A CLOSED PANEL STILL SAYS WHAT IS FILTERED')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

# base's own filter script, taken as the whole inline block that defines
# setOpen. F1 learned this the hard way: a regex that ran to </body>
# dragged the closing tags in, the script never parsed, and the panel
# then "failed to open" for a reason that had nothing to do with the
# round under test.
blocks = [b for b in re.findall(r'<script>(.*?)</script>', base, re.S)
          if 'function setOpen' in b]
base_js = blocks[-1] if blocks else ''

# THE PAGE'S OWN CHIP WRITER, whichever version of the page we are
# driving. Not a copy of it - the function itself, so the fixture cannot
# quietly test something the page does not do.
def writer(text):
    m = re.search(r'function updateRecipeActiveFilters\(\)\s*\{.*?\n\}\n',
                  text, re.S)
    return m.group(0) if m else ''


# The form the function reads: a search term and two checked courses, so
# three chips - and the count should read 3.
FORM = ('<form id="recipeFilterForm">'
        '<input id="searchInput" value="chicken">'
        '<input type="checkbox" id="searchByIngredient">'
        '<input type="checkbox" name="course" value="main" checked>'
        '<span>Main</span>'
        '<input type="checkbox" name="course" value="side" checked>'
        '<span>Side</span>'
        '</form>')

BUTTON = ('<div class="page-action-buttons">'
          '<button type="button" class="btn action-filter" id="filterBtn" '
          'aria-pressed="false" aria-controls="recipeFilterPanel">'
          '<i></i><span class="action-filter-label"> Filter</span>'
          '<span class="action-filter-count" data-count=""></span>'
          '</button></div>')

def row_of(text):
    """The chip row EXACTLY AS THE PAGE WRITES IT, and whether the page
    puts it inside the filter panel.

    The fixture must not invent either one. A fixture that hard-codes the
    right markup tests markup the suite wrote, not markup the round wrote
    - and it would go on passing with the round reverted, which is the one
    thing a control exists to prevent."""
    mk = mk_of(text)
    i = -1
    for cls in ('class="alv-filter-active"', 'class="recipe-active-filters"'):
        i = mk.find('<div ' + cls)
        if i >= 0:
            break
    if i < 0:
        return '', None
    j = mk.find('id="recipeFilterTags"', i)
    if j < 0:
        return '', None
    j = mk.find('</div>', mk.find('</div>', j) + 1) + len('</div>')
    inside = 0 <= mk.find('id="recipeFilterPanel"') < i
    return mk[i:j], inside


def fixture(name, text):
    """One page, built from what THAT page actually says: its stylesheet,
    its chip writer, its row, and its row's place."""
    row, inside = row_of(text)
    panel = ('<div class="alv-filter recipe-filter-panel" '
             'id="recipeFilterPanel"><div class="recipe-filter-content">'
             + FORM + (row if inside else '') + '</div></div>')
    body = BUTTON + ('' if inside else row) + panel
    p = os.path.join(SCRATCH, name)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>%s'
                 '<script>var NUTRITION_SORT = "";\n%s\n%s\n'
                 'document.addEventListener("DOMContentLoaded", function(){'
                 '  updateRecipeActiveFilters(); });</script>'
                 '</body></html>'
                 % (css_of(base), css_of(text), body, base_js,
                    writer(text)))
    return p


LOOK = '''() => {
  const seen = e => !!(e && (e.offsetParent !== null ||
                    getComputedStyle(e).display !== "none")) &&
                    e.getBoundingClientRect().height > 0;
  const row = document.getElementById("recipeActiveFilters");
  const chips = [...document.querySelectorAll("#recipeFilterTags > *")];
  const box = document.querySelector(".action-filter-count");
  const one = chips[0] ? getComputedStyle(chips[0]) : null;
  const x = chips[0] ? chips[0].querySelector("button") : null;
  return {
    panel: seen(document.getElementById("recipeFilterPanel")),
    row: seen(row),
    hasClass: row ? row.classList.contains("has-filters") : null,
    chips: chips.length,
    chipClass: chips[0] ? chips[0].className : "",
    bg: one ? one.backgroundColor : "",
    fg: one ? one.color : "",
    count: box ? box.textContent : null,
    xw: x ? Math.round(x.getBoundingClientRect().width) : 0,
    xbg: x ? getComputedStyle(x).backgroundColor : ""
  };
}'''

if HAVE_PW and base_js and writer(page):
    ok(True, 'base\'s real filter script and the page\'s real chip writer '
             'were both found - this section drives the things themselves')
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        _goto(pg, fixture('chips_now.html', page))
        pg.wait_for_timeout(300)
        now = pg.evaluate(LOOK)
        ok(not now['panel'], 'the panel is closed on load, as F1 left it')
        ok(now['chips'] == 3, '  and the page wrote three chips',
           now['chips'])
        ok(now['row'],
           'THE CHIPS ARE VISIBLE WITH THE PANEL CLOSED - which is the '
           'whole round', now)
        ok(now['hasClass'] is True,
           '  because base put .has-filters on the row itself', now)
        ok(now['chipClass'].strip() == 'filter-tag',
           '  and each chip is base\'s .filter-tag', now['chipClass'])
        ok(now['bg'] == ACCENT, 'a chip is the house accent', now['bg'])
        ok(now['bg'] != GREEN, '  and not the green it used to be')
        ok(now['count'] == '3',
           'the Filter button carries the number of chips, so a closed '
           'panel says "Filter 3" instead of nothing', now['count'])
        ok(now['xw'] == 16, '  and the x is base\'s 16px', now['xw'])

        pg.click('#filterBtn')
        pg.wait_for_timeout(150)
        opened = pg.evaluate(LOOK)
        ok(opened['panel'] and opened['row'],
           'opening the panel does not move or hide the chips - they are '
           'not inside it any more', opened)

        # PHONE. Every screen has to work on one, and the chips are the
        # only thing telling a phone what it is looking at.
        pg.set_viewport_size({'width': 390, 'height': 844})
        pg.wait_for_timeout(200)
        ph = pg.evaluate(LOOK)
        ok(ph['row'] and ph['chips'] == 3,
           'on a 390px phone the row is still there, all three chips',
           ph)
        ok(ph['count'] == '3', '  and the count still shows - base keeps '
                               'it when it drops the word "Filter"')
        tap = pg.evaluate('''() => {
            const x = document.querySelector('.filter-tag .remove-tag');
            if (!x) return 0;
            const r = getComputedStyle(x, '::before');
            return r.content === 'none' ? 0 : 1;
        }''')
        ok(tap == 1,
           '  and base\'s 44px tap ring applies to the x, which the '
           'page\'s own chips never had', tap)

        # THE CONTROL THAT MUST FAIL. The same fixture, the same base, the
        # page as it was before this round: chips inside the panel, the
        # panel closed.
        if was:
            _goto(pg, fixture('chips_was.html', was))
            pg.set_viewport_size({'width': 1280, 'height': 900})
            pg.wait_for_timeout(300)
            old = pg.evaluate(LOOK)
            ok(old['chips'] == 3,
               'CONTROL: the old page writes three chips too - the chips '
               'were never the problem', old['chips'])
            ok(not old['row'],
               '  AND NOT ONE OF THEM IS VISIBLE, because the row is '
               'inside a panel that is now closed. That is the fault this '
               'round removes', old)
            ok(old['count'] in ('', None),
               '  and the button says nothing either: base counts a row '
               'it cannot find', old['count'])
            ok(old['bg'] == GREEN,
               '  and the chip was green, where every other chip in the '
               'system is the accent', old['bg'])
        else:
            for _ in range(4):
                skip('the revert control', 'no %s backup' % SUFFIX)
        br.close()
else:
    if not HAVE_PW:
        skipped += 17
    else:
        failed += 1
        print('  FAIL base\'s script (%d chars) or the page\'s chip writer '
              '(%d chars) could not be found'
              % (len(base_js), len(writer(page))))

# ==========================================================================
head('4. ONE WRITER FOR ONE FACT')
# ==========================================================================
# base's wireCount comment: "The pages used to set
# activeFiltersDiv.style.display themselves; that line is removed, or we
# would be back to two things recording one fact."
js = nocomment(page)
ok('activeFiltersDiv' not in js,
   'the page does not look the row up at all any more')
ok('hasFilters' not in js,
   '  and does not count its own chips - the declaration and all six '
   'assignments went with the line that read them, because dead '
   'arithmetic about visibility is what makes the next reader think this '
   'page still owns it')
ok(not re.search(r'recipeActiveFilters[^\n]*style', js),
   '  and writes no display on the row')
ok('wireCount' in base and 'has-filters' in base,
   'base is the one that owns it - wireCount toggles .has-filters from '
   'the chips a MutationObserver can see')
n_writers = len([p for p in alv_tree.templates()
                 if re.search(r'ActiveFilters?\w*\.style\.display',
                              nocomment(read(p)))])
ok(n_writers == 0,
   'and NO page in the tree sets a chip row\'s display in script',
   n_writers)

if was:
    ok('activeFiltersDiv.style.display' in was,
       'CONTROL: this page did, before this round')

# ==========================================================================
head('5. SCOPE - AND NOTHING ELSE')
# ==========================================================================
if was:
    # WHERE, NOT WHICH WORDS. The first version of this check asked
    # whether every changed line contained one of a list of words, and
    # refused on the round's own replacement comment - lesson 21 again,
    # a gate reading the prose that explains what it removed. The honest
    # question is positional: this round declared three regions of the
    # old file, and every edit must fall inside one of them.
    a, b = was.split('\n'), page.split('\n')

    def span(first, last=None):
        """The line range of a region of the OLD file, named by the text
        that opens it and the text that closes it. None when the old file
        does not have it - which is what a reverted page looks like, and
        it must produce a failure and not a traceback."""
        i = next((k for k, ln in enumerate(a) if first in ln), None)
        if i is None:
            return None
        if last is None:
            return i, i + 1
        j = next((k for k, ln in enumerate(a) if last in ln and k >= i),
                 None)
        return None if j is None else (i, j + 1)

    REGIONS = {
        'the five chip rules': span('.recipe-active-filters {',
                                    '.recipe-remove-tag:hover'),
        'the row inside the panel': span('id="recipeActiveFilters"',
                                         '</form>'),
        'the chip writer': span('function updateRecipeActiveFilters() {',
                                'activeFiltersDiv.style.display'),
    }
    # A REGION THAT IS NOT THERE IS A FAILURE, NOT A CRASH. Reverted, the
    # old file and the new one are the same file and the diff is empty -
    # so the scope check would pass while every check above it failed.
    # Say it instead.
    missing = sorted(n for n, r in REGIONS.items() if r is None)
    ok(not missing,
       'the backup has all three regions this round declared, so there is '
       'something to have scoped', missing)
    # The one place something ARRIVES: the row's new home, above the panel.
    _where = span('<!-- Filter Panel -->')
    WHERE_IN = _where[0] if _where else -99
    allowed = set()
    for r in REGIONS.values():
        if r:
            allowed.update(range(r[0], r[1]))

    moved = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        if i1 == i2:                      # pure insertion
            if i1 in (WHERE_IN, WHERE_IN + 1) or i1 in allowed:
                continue
            moved.append('insert at old line %d: %r' % (i1, b[j1][:80]))
            continue
        outside = [k for k in range(i1, i2) if k not in allowed]
        if outside:
            moved.append('%s old line %d: %r'
                         % (tag, outside[0] + 1, a[outside[0]][:80]))
    ok(not moved,
       'every edit falls inside one of the three regions this round '
       'declared - the five rules, the row, the chip writer - and the one '
       'insertion is the row\'s new home above the panel',
       '\n'.join(moved[:6]))
    for name, r in sorted(REGIONS.items()):
        print('         %-26s %s' % (name, 'old lines %d-%d' % (r[0] + 1,
                                                                r[1])
                                     if r else 'NOT IN THE BACKUP'))
    ok(len(page) < len(was),
       'and the page got smaller - five rules and a dead variable left, '
       'one row and one comment arrived',
       '%d -> %d' % (len(was), len(page)))
else:
    skip('scope', 'no %s backup' % SUFFIX)
    skip('size', 'no %s backup' % SUFFIX)

# ==========================================================================
head('6. THE ELEVEN, ALL THE SAME NOW')
# ==========================================================================
rows, house = [], []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    m = mk_of(read(p))
    if 'action-filter' in m and 'alv-filter' in m:
        house.append(rel)
    if 'class="alv-filter-active"' in m:
        rows.append(rel)
# TWELVE SINCE T4, 30 Sep 2026. Manage Lease Agreements joined the
# house filter, chips row and all (test_lease_filter.py). EXACT and
# not >= : this census exists so the set cannot change in silence.
ok(len(house) == 12, 'twelve pages wear the house filter', len(house))
ok(PAGE in rows, '%s is one of the rows' % PAGE)
ok(len(rows) == 12,
   'and TWELVE of twelve now put their chips on base\'s row - the fourth '
   'copy was the last one', sorted(set(house) - set(rows)))

# ==========================================================================
head('7. THE GATE')
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

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_recfilter'),
       '  after F1, which is the order they ran in - as_left_by depends '
       'on it')
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

f1 = os.path.join(ROOT, 'test_recipe_filter.py')
if os.path.isfile(f1):
    ok('as_left_by' in read(f1),
       'F1\'s suite now judges the page AS F1 LEFT IT - its section 5 is '
       'the record of what F1 left, and this round took all of it '
       '(lesson 17)')
else:
    skip('F1\'s repair', 'test_recipe_filter.py not on disk')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that clearing a chip re-runs the search. That is')
print('  base\'s own listener on .remove-tag and test_filter_chip.py owns')
print('  it; this page\'s x buttons call the page\'s clear functions, which')
print('  submit the form - unchanged by this round and unchanged in the')
print('  diff above.')
print('=' * 74)
sys.exit(1 if failed else 0)
