# -*- coding: utf-8 -*-
"""SECTION F, ROUND F3 - A FILTER THAT IS ON IS A FILTER THAT IS APPLIED

Demetri, 30 Sep, with two screenshots: choose Protein = Chicken on Recipe
Management and the chip says "Protein: Chicken", the button says
"Filter 1" - and the list is 48 of 317 recipes with no chicken in it.
Press Apply Filters and the same page shows 32, all chicken.

    THE CHIPS AND THE COUNT WERE DESCRIBING THE FORM, NOT THE RESULTS.

That was always true. It was invisible while the panel was always open
and the chips sat inside it; F1 closed the panel and F2 lifted the chips
onto the page, which is what a status row is for - it made the page say
out loud something that had been wrong quietly.

MEASURED ACROSS THE ELEVEN PAGES WITH THE HOUSE FILTER. Ten of them
submit the moment a control changes:

    properties, suppliers, tenant       element.addEventListener('change',
    invoices, passports, celebrations     () => form.submit())
    physical_invoice_list, projects,
    fsr, act_expense

Recipe Management is the only one with an Apply button - and it has one
for a real reason. Its Courses, Categories, Proteins and Author filters
are TICK LISTS, not single dropdowns: choosing three courses on the house
pattern would reload the page three times.

AND THE PAGE WAS ALREADY HALF HERE. clearSingleFilter, clearRecipeFilterGroup,
clearNutritionSort and toggleNutritionOrder all submit the form
themselves. REMOVING a filter applied at once; ADDING one waited for a
button. That is the inconsistency, stated exactly.

WHAT DEMETRI CHOSE, 30 Sep: apply when a tick list CLOSES.

    A menu remembers what was ticked when it opened. When it closes -
    by a second click on its own button, by opening another one, or by a
    click anywhere else on the page - it compares. Different, submit.
    The same, do nothing, because opening a list to look at it is not a
    filter change.

    Ticking Main, Lunch and Dinner is therefore ONE reload, and the
    chips can never again describe something the list does not.

THE OTHER FOUR CONTROLS, for completeness:
    Search          Enter, or the magnifier - both already submit
    Name/Ingredient applies when there is a term to re-search; with an
                    empty box it only changes the placeholder, because
                    re-running an empty search is not a filter change
    Sort by Nutrition  applies on change - it had NO handler at all and
                    was the one control that needed the button
    Order toggle    already submitted

AND THE BUTTON GOES, with the row it sat in - which held nothing else but
a SECOND Clear All, the panel header already having one. Its CSS goes
with it, here and in the phone block.

Backups: .bak_applyclose. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_applyclose'
CRLF = {}

PAGE = 'recipe_management.html'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('F3: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, count=1):
    a = eol(path, was)
    if text.count(a) != count:
        raise SystemExit('F3: %s - %s is there %d time(s), not %d'
                         % (os.path.basename(path), what,
                            text.count(a), count))
    print('     %s' % what)
    return text.replace(a, eol(path, now))


# ==========================================================================
# 1. THE CONTROLLER - one place that knows when a menu closed and whether
#    anything changed while it was open.
# ==========================================================================
TOGGLE_WAS = """function toggleFilterDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    const button = dropdown.previousElementSibling;
    document.querySelectorAll('.filter-multiselect-menu').forEach(menu => {
        if (menu.id !== dropdownId) {
            menu.classList.remove('show');
            menu.previousElementSibling.classList.remove('active');
        }
    });
    dropdown.classList.toggle('show');
    button.classList.toggle('active');
}"""

TOGGLE_NOW = """/* ===== APPLY WHEN THE LIST CLOSES ===== 30 Sep 2026
   Ten of the eleven pages with the house filter submit the moment a
   control changes. This page could not: its four filters are tick
   lists, so submitting on every tick would reload the page once per
   box. It had an Apply button instead - and a page with an Apply
   button has a state where the chips say one thing and the list
   shows another, which is what Demetri photographed.

   So the moment that counts is not the tick, it is the CLOSE. A menu
   records what was ticked when it opened; when it closes it compares,
   and submits only if the answer changed. Opening a list to read it
   is not a filter change and must not cost a reload.

   Three things close a menu and all three come through closeMenus():
   a second click on its own button, opening another menu, and a click
   anywhere else on the page.
                                          [test_filter_on_close.py] */
var RECIPE_MENU_OPEN = null;     /* {id, sig} for the menu now open */


function recipeMenuSignature(menu) {
    return Array.prototype.map.call(
        menu.querySelectorAll('input[type="checkbox"]'),
        function (cb) { return cb.checked ? '1' : '0'; }).join('');
}


function applyRecipeFilters() {
    /* The two flags the page already uses to decide what to reopen
       after the reload. Set here so every path through this round
       looks to the rest of the page exactly like the old Apply. */
    try {
        sessionStorage.setItem('recipeUserInteracted', 'true');
        sessionStorage.setItem('recipeJustAppliedFilters', 'true');
    } catch (e) { /* private mode: the panel starts closed, no worse */ }
    document.getElementById('recipeFilterForm').submit();
}


function closeRecipeMenus(except) {
    /* Close every open menu but `except`, and say whether the one that
       was open closed with a different set of ticks than it opened
       with. Returns true if the page should now apply. */
    var changed = false;
    document.querySelectorAll('.filter-multiselect-menu').forEach(
        function (menu) {
            if (menu.id === except || !menu.classList.contains('show')) {
                return;
            }
            menu.classList.remove('show');
            menu.previousElementSibling.classList.remove('active');
            if (RECIPE_MENU_OPEN && RECIPE_MENU_OPEN.id === menu.id) {
                if (RECIPE_MENU_OPEN.sig !== recipeMenuSignature(menu)) {
                    changed = true;
                }
                RECIPE_MENU_OPEN = null;
            }
        });
    return changed;
}


function toggleFilterDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    const button = dropdown.previousElementSibling;
    const wasOpen = dropdown.classList.contains('show');
    /* Another menu closing is a close like any other - if the user
       ticked something in it and then reached straight for this one,
       that tick is applied. */
    var changed = closeRecipeMenus(dropdownId);
    if (wasOpen) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
        if (RECIPE_MENU_OPEN && RECIPE_MENU_OPEN.id === dropdownId &&
            RECIPE_MENU_OPEN.sig !== recipeMenuSignature(dropdown)) {
            changed = true;
        }
        RECIPE_MENU_OPEN = null;
    } else {
        dropdown.classList.add('show');
        button.classList.add('active');
        RECIPE_MENU_OPEN = {id: dropdownId,
                            sig: recipeMenuSignature(dropdown)};
    }
    if (changed) { applyRecipeFilters(); }
}"""

# ==========================================================================
# 2. A CLICK ANYWHERE ELSE closes the menu too, and is the commonest way
#    a person leaves one.
# ==========================================================================
OUTSIDE_WAS = """document.addEventListener('click', function(event) {
    if (!event.target.closest('.filter-multiselect-dropdown')) {
        document.querySelectorAll('.filter-multiselect-menu').forEach(menu => {
            menu.classList.remove('show');
            menu.previousElementSibling.classList.remove('active');
        });
    }
});"""

OUTSIDE_NOW = """document.addEventListener('click', function(event) {
    /* THE COMMONEST WAY TO LEAVE A TICK LIST is to click away from it,
       so this is the path that matters most. It closes through the
       same function as the other two, which is the point: one place
       decides whether a close means apply. */
    if (!event.target.closest('.filter-multiselect-dropdown')) {
        if (closeRecipeMenus(null)) { applyRecipeFilters(); }
    }
});"""

# ==========================================================================
# 3. THE TWO CONTROLS THAT STILL WAITED FOR THE BUTTON
# ==========================================================================
WIRE_AT = """document.addEventListener('click', function(event) {
    /* THE COMMONEST WAY TO LEAVE A TICK LIST"""

WIRE_NOW = """document.addEventListener('DOMContentLoaded', function () {
    /* SORT BY NUTRITION HAD NO HANDLER AT ALL - it was the one control
       that genuinely needed the Apply button, because nothing else
       would ever submit for it. It is a single select: changed IS
       finished, the way it is on the other ten pages. */
    var nut = document.getElementById('nutritionSortSelect');
    if (nut) {
        nut.addEventListener('change', function () { applyRecipeFilters(); });
    }
    /* NAME / INGREDIENT changes WHAT a term means, so it re-searches -
       but only when there is a term. Switching the radio over an empty
       box changes the placeholder and nothing else, and reloading the
       page to run an empty search again would be a reload that changes
       nothing on screen. */
    ['searchByName', 'searchByIngredient'].forEach(function (id) {
        var r = document.getElementById(id);
        if (!r) { return; }
        r.addEventListener('change', function () {
            var box = document.getElementById('searchInput');
            if (box && box.value.trim()) { applyRecipeFilters(); }
        });
    });
});


document.addEventListener('click', function(event) {
    /* THE COMMONEST WAY TO LEAVE A TICK LIST"""

# ==========================================================================
# 4. THE BUTTON, AND THE ROW THAT HELD NOTHING ELSE
# ==========================================================================
ROW_WAS = """
                <!-- Action Buttons -->
                <div class="filter-action-buttons">
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-filter"></i> Apply Filters
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="clearAllRecipeFilters(event)">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </div>"""

ROW_NOW = """
                <!-- THE APPLY BUTTON WAS HERE - taken 30 Sep. Nothing
                     replaces it: a tick list applies when it closes, the
                     search on Enter, the nutrition sort on change. The
                     row held one other thing, a SECOND Clear All, and
                     the panel header two inches above has one already. -->"""

CSS_WAS = """.filter-action-buttons {
    display: flex;
    gap: 10px;
    grid-column: 1 / -1;
    justify-content: center;
}"""

CSS_NOW = """/* .filter-action-buttons was the Apply row's rule, and the row went on
   30 Sep with the button in it.                [test_filter_on_close.py] */"""

PHONE_WAS = """    .filter-action-buttons { flex-direction: column; gap: 8px; }
    .filter-action-buttons .btn { width: 100%; }
"""
PHONE_NOW = ""

# ==========================================================================
print('=' * 74)
print('SECTION F, ROUND F3 - A FILTER THAT IS ON IS A FILTER THAT IS '
      'APPLIED%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(PAGE)
t, raw = read(p)
print('  %s' % PAGE)
if 'closeRecipeMenus' in t:
    print('     already applies when a list closes')
else:
    t = swap(t, p, TOGGLE_WAS, TOGGLE_NOW,
             'a menu remembers what was ticked when it opened, and '
             'applies if that changed by the time it closes')
    t = swap(t, p, OUTSIDE_WAS, OUTSIDE_NOW,
             '  a click anywhere else closes through the same function')
    t = swap(t, p, WIRE_AT, WIRE_NOW,
             '  Sort by Nutrition applies on change - it had no handler '
             'at all')
    t = swap(t, p, ROW_WAS, ROW_NOW,
             '  the Apply button goes, and the duplicate Clear All with it')
    t = swap(t, p, CSS_WAS, CSS_NOW, '  and its rule')
    t = swap(t, p, PHONE_WAS, PHONE_NOW, '  and its phone rule')

    # GATES ----------------------------------------------------------------
    def nocom(s):
        s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
        s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
        return s

    bare = nocom(t)
    if 'Apply Filters' in bare:
        raise SystemExit('F3: the Apply button is still there')
    if 'filter-action-buttons' in bare:
        raise SystemExit('F3: .filter-action-buttons survives somewhere')
    # THE BUTTONS, NOT THE FUNCTION. The first version of this gate
    # counted clearAllRecipeFilters(event) and found two after the row
    # went - one button and the function's own definition. Count the
    # thing being asked about.
    n_clear = bare.count('onclick="clearAllRecipeFilters(event)"')
    if n_clear != 1:
        raise SystemExit('F3: Clear All is on %d button(s), not 1' % n_clear)
    # ONE PLACE CLOSES A MENU. The whole round rests on it: if any other
    # line still removes the show class, a close can happen that nobody
    # compared, and the page is back to chips that disagree with the list.
    closers = len(re.findall(r"classList\.remove\('show'\)", bare))
    if closers != 2:
        raise SystemExit('F3: %d places remove the show class, not the 2 '
                         'inside closeRecipeMenus and toggleFilterDropdown'
                         % closers)
    for fn in ('recipeMenuSignature', 'applyRecipeFilters',
               'closeRecipeMenus'):
        if len(re.findall(r'function\s+%s\s*\(' % fn, bare)) != 1:
            raise SystemExit('F3: %s is not defined exactly once' % fn)
    # A SUBMIT BUTTON MUST SURVIVE, or Enter in the search box stops
    # submitting the form - which would take away the one way to search.
    if 'class="search-btn"' not in bare or 'type="submit"' not in bare:
        raise SystemExit('F3: the search submit button is gone, so Enter '
                         'no longer searches')
    if 'btn-success' in bare:
        raise SystemExit('F3: a green button survives on this page')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ==========================================================================
# 5. F2'S SUITE PINNED THIS FILE - lesson 17, and F3 is the trigger
#
#   test_recipe_chips.py proves its own scope by diffing its backup
#   against the page AS IT IS NOW. That is true only until the next round
#   edits the same page, and this is that round: F2's scope check now
#   reports F3's edits as strays, with nothing wrong.
#
#   The repair the programme has made six times. One line - the page F2
#   judges becomes the page AS F2 LEFT IT - and it protects every section
#   of that suite at once, not just the one that broke today.
# ==========================================================================
F2 = 'test_recipe_chips.py'
F2_WAS = """page = read(PATH)"""
F2_NOW = """# AS F2 LEFT IT - lesson 17. Every section below judges what F2 did,
# and a later round editing this same page must not make F2's own
# scope check report strays. F3 was that round, on 30 Sep.
try:
    from alv_rounds import as_left_by
    page = as_left_by(PATH, SUFFIX, read)
except Exception:
    page = read(PATH)"""

q = os.path.join(os.getcwd(), F2)
if os.path.isfile(q):
    t2, raw2 = read(q)
    print('  %s' % F2)
    # THE NARROW QUESTION, AGAIN. "as_left_by in t2" is true before this
    # edit ever runs: F2's own gate checks that F1's suite contains the
    # string 'as_left_by'. That is the second time today a guard has read
    # a round's prose and concluded the work was done - lesson 21 does
    # its most damage here, because a false "already" ships nothing and
    # says everything is fine.
    if 'page = as_left_by(PATH, SUFFIX, read)' in t2:
        print('     already judges the page as F2 left it')
    else:
        t2 = swap(t2, q, F2_WAS, F2_NOW,
                  'its whole judgement reads the page as F2 left it')
        if not CHECK:
            back_up(q, raw2)
            write(q, t2)

print('-' * 74)
print('  the tick list applies itself when you leave it, so the chips and')
print('  the count can no longer describe a filter that is not on.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
