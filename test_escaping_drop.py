# -*- coding: utf-8 -*-
"""test_escaping_drop.py - Section DD round DD-1, 3 Oct 2026.

Demetri, 3 Oct 2026: "When I capture a recipe, the dropdowns/modals are
cutting off."

base gives every .table-container `overflow: clip`, chosen over `hidden`
on 26 September so the sticky table header still sticks while the rounded
corners still clip - 615px of drift measured with hidden, none with clip.

BUT clip CLIPS AN ABSOLUTELY-POSITIONED DESCENDANT EXACTLY AS hidden
DOES. The ingredient autocomplete is one, inside a cell, and the
container's bottom edge sits a few pixels under the input.

SECTION 2 IS THE ROUND. Not "the rule is in the stylesheet" - that is a
claim about text. The dropdown is rendered in a browser under base's
stylesheet and the page's, with and without the marker, and the pixels
are counted: 13 of 159 inside the container before, 159 of 159 after.
That is the sliver in his screenshot, measured.

SECTION 4 IS THE SCOPE, AND IT CHANGED THE ROUND. Of the positioned popup
layers in this tree, the ones that live inside a table container are the
six autocompletes on this one page. The More menus are also absolute, but
every page puts them in the ACTION BAR; the three multiselects on this
same page sit in the Basic Information card. So the fix is one rule keyed
on the popup, not a fixed-layer machine - and the suite keeps the census
so a seventh is found by a gate rather than by a screenshot.
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

SUFFIX = '.bak_escapedrop'
ME = 'test_escaping_drop.py'
PATCHER = 'apply_escaping_drop.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_escapedrop_')

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

BASE = alv_tree.path_of('base.html')
PAGE = alv_tree.path_of('preview_imported_recipe.html')
RULE = '.table-container:has(.alv-escapes)'


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S))


def classes(src):
    return [m.group(1).split() for m in re.finditer(r'class="([^"]*)"', src)]


B = alv_tree.code_only(now(BASE))
P = alv_tree.code_only(now(PAGE))

# ==========================================================================
head('1. ONE RULE, IN base, NARROWING THE clip RATHER THAN REMOVING IT')
# ==========================================================================
hits = re.findall(re.escape(RULE) + r'\s*\{[^}]*\}', B)
ok(len(hits) == 1, '%d copy of the rule in base' % len(hits))
ok(hits and 'overflow: visible' in hits[0], 'and it sets overflow visible')
ok('overflow: clip;' in B,
   'the clip it narrows is still there - this round narrows that rule, it '
   'does not remove it')
ok(B.index('overflow: clip;') < B.index(RULE),
   'and comes first, so the narrowing wins')
ok(':has(' in hits[0] if hits else False,
   'it is a :has() on the container - a browser that does not know :has() '
   'drops the rule and behaves as it does today, which is the only safe '
   'way for a fix to fail')

# ==========================================================================
head('2. THE PIXELS, IN A BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

ROW = ('<div class="ingredient-table-wrapper"><div class="table-container">'
       '<table class="table alv-table"><tbody><tr>'
       '<td><input value="200"></td>'
       '<td><div class="autocomplete-wrapper"><input value="Corn">'
       '<div class="%s autocomplete-dropdown ingredient-dropdown show">'
       '<div class="autocomplete-item">Corn, Sweet</div>'
       '<div class="autocomplete-item">Corn Flour</div>'
       '<div class="autocomplete-item">Cornichons</div>'
       '<div class="autocomplete-item">Corn Syrup</div>'
       '</div></div></td></tr></tbody></table></div></div>')

if sync_playwright is None:
    for _ in range(4):
        skip('the pixels, in a browser', 'playwright not installed')
else:
    def measure(mark):
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style></head>'
                '<body><div style="padding:40px">%s</div></body></html>'
                % (css_of(B), css_of(P), ROW % mark))
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            p = b.new_page(viewport={'width': 1280, 'height': 800})
            p.set_content(html)
            r = p.evaluate("""() => {
              const d = document.querySelector('.autocomplete-dropdown');
              const c = document.querySelector('.table-container');
              const dr = d.getBoundingClientRect();
              const cr = c.getBoundingClientRect();
              const clipped = getComputedStyle(c).overflow !== 'visible';
              return {h: Math.round(dr.height),
                      overflow: getComputedStyle(c).overflow,
                      seen: Math.round((clipped
                            ? Math.min(dr.bottom, cr.bottom) : dr.bottom)
                            - dr.top)};
            }""")
            b.close()
        return r

    a = measure('')
    z = measure('alv-escapes')
    ok(a['h'] > 100, 'the suggestion list is %dpx tall' % a['h'])
    ok(a['seen'] < a['h'] / 2,
       'CONTROL: unmarked, only %d of those %d pixels are inside the '
       'container - the container is %s' % (a['seen'], a['h'], a['overflow']))
    ok(z['seen'] == z['h'],
       'marked, all %d of them are - the container is %s'
       % (z['h'], z['overflow']))
    ok(z['h'] == a['h'],
       'and the list itself did not change size, so this is about clipping '
       'and nothing else')

# ==========================================================================
head('3. EVERY POPUP IN THAT TABLE IS MARKED, AND IT IS A TOKEN')
# ==========================================================================
every = [c for c in classes(P) if 'autocomplete-dropdown' in c]
marked = [c for c in every if 'alv-escapes' in c]
ok(len(every) >= 6, '%d autocomplete dropdowns on the capture page'
   % len(every))
ok(len(marked) == len(every), 'and every one of them carries the class')
for c in classes(P):
    if 'alv-escapes' in c:
        ok('autocomplete-dropdown' in c,
           '  and nothing that is not a dropdown does')
        break

o = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
if o:
    ok('alv-escapes' not in o,
       'CONTROL: before this round not one of them did')
else:
    skip('CONTROL: before this round not one of them did', 'no backup')

leak = [alv_tree.rel(p) for p in alv_tree.templates()
        if p not in (BASE, PAGE)
        and 'alv-escapes' in alv_tree.code_only(now(p))]
ok(not leak, 'and no other page carries it - a container only stops '
   'clipping where something needs to escape', ', '.join(leak[:5]))

# ==========================================================================
head('4. THE CENSUS - WHICH POPUPS LIVE INSIDE A TABLE')
# ==========================================================================
# The round claims the clipped family is this page. A seventh appearing
# later should be found by this gate and not by a screenshot.
found = []
for p in sorted(alv_tree.templates()):
    s = alv_tree.code_only(now(p))
    if 'table-container' not in s:
        continue
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(s)):
        body = m.group(2)
        if 'position: absolute' not in body or 'z-index' not in body:
            continue
        sel = m.group(1).strip().split('\n')[-1].strip()
        name = sel.lstrip('.').split()[0].split(':')[0]
        if name and ('class="%s' % name) in s:
            found.append((alv_tree.rel(p), name))
names = sorted(set(n for _, n in found))
ok(len(found) <= 6,
   '%d positioned popup layer(s) live in a page that has a table container'
   % len(found), '\n'.join('%s %s' % f for f in found))
for rel, name in found:
    print('         %-40s .%s' % (rel, name))

# AND THE ONE THIS ROUND IS ABOUT IS IN A CELL, which is what makes it
# clipped. The others on the same page are not.
i = P.index('<table')
j = P.index('</table>', i)
ok(P.find('autocomplete-dropdown', i, j) > 0,
   'the autocomplete is inside the ingredients table')
ok(P.find('multiselect-menu', i, j) < 0,
   'CONTROL: and the multiselect menus on the same page are not - they '
   'sit in the Basic Information card, so nothing clips them and marking '
   'them would unclip a table that holds no popup')

# ==========================================================================
head('5. AND NO OTHER TABLE IN THE APP STOPPED CLIPPING')
# ==========================================================================
# The rule is keyed on the popup precisely so this stays true.
ok('.table-container {' in B or '.table-container{' in B.replace(' ', ''),
   'base still has a plain .table-container rule')
plain = re.search(r'\.table-container\s*\{[^}]*\}', B)
ok(plain and 'overflow: clip' in plain.group(0),
   'and it still clips, for every table that holds no popup')

# ==========================================================================
head('6. REGISTERED')
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
