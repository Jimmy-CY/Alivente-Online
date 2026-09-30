# -*- coding: utf-8 -*-
"""SECTION F, ROUND F2 - A CLOSED PANEL MUST NOT HIDE WHAT YOU FILTERED BY

F1 gave Recipe Management the house Filter button and made its panel
close on load, which is what Demetri asked for. It also left something,
on purpose, and wrote it down in its own suite:

    THE ACTIVE-FILTER CHIPS ARE INSIDE THE PANEL.

While the panel was always open that was merely a fourth copy of a
component base owns. Now that the panel closes, it is worse than
untidy: search for "chicken", press Filter to put the panel away, and
the page shows you a filtered list with nothing on screen saying it is
filtered. base's own comment on the component says so in as many words:

    a closed panel must never mean invisible filtering.

WHAT IS WRONG, MEASURED.

    .recipe-active-filters   the row       - base has .alv-filter-active
    .recipe-filter-tags      the holder    - base has .filter-tags
    .recipe-filter-tag       one chip      - base has .filter-tag
    .recipe-remove-tag       its x         - base has .filter-tag .remove-tag
    .recipe-remove-tag:hover

Five rules, and the chip is #28a745 - green, where every other chip in
the system is the accent. Nine pages carried this same family on 22 Sep
and the chip round took all nine; it stopped at this page and said why:
"recipe_management.html (Personal) is untouched until its own round."
This is that round.

WHAT CHANGES.

    1. The row moves OUT of the panel and out of the form, to the place
       the other ten pages put it: between the action bar and the panel.
    2. It wears base's classes. The ids stay as they are - the page's own
       script looks the holder up by id, and renaming it would be churn
       with nothing at the end of it.
    3. The five page-local rules go. Nothing replaces them; base has
       said all five things since 22 Sep.
    4. THE PAGE STOPS SETTING display. base's wireCount counts the chips
       with a MutationObserver and toggles .has-filters itself, and its
       comment gives the reason: "The pages used to set
       activeFiltersDiv.style.display themselves; that line is removed,
       or we would be back to two things recording one fact."
       With the reader of `hasFilters` gone the variable has no reader
       left, so its declaration and its six assignments go with it -
       dead arithmetic about visibility is exactly what makes the next
       person think this page still owns it.

AND THE COUNT COMES FREE. base numbers the Filter button from the chips
it can see, so the closed panel now says "Filter 3" instead of saying
nothing.

Backups: .bak_recchips. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_recchips'
CRLF = {}

PAGE = 'recipe_management.html'
F1 = 'test_recipe_filter.py'


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
            raise SystemExit('F2: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label, count=1):
    """Replace `was` with `now`, and REFUSE unless it is there `count`
    times. A round that does half its work is worse than one that does
    none, because only the second kind is obvious."""
    a = eol(path, was)
    if text.count(a) != count:
        raise SystemExit('F2: %s - %s is there %d time(s), not %d'
                         % (label, what, text.count(a), count))
    print('     %s' % what)
    return text.replace(a, eol(path, now))


# ==========================================================================
# 1. THE ROW LEAVES THE PANEL
# ==========================================================================
MK_WAS = """
            <div class="recipe-active-filters" id="recipeActiveFilters" style="display: none;">
                <span>Active filters:</span>
                <div class="recipe-filter-tags" id="recipeFilterTags"></div>
            </div>
        </form>"""

MK_NOW = """
        </form>"""

# base's own shape, and the same words the other ten pages use. NO inline
# style: base's rule is `.alv-filter-active { display: none; }` shown by a
# class, and base's comment says why that way round - "Starting visible
# and hiding it in script means a flash of Active filters: with nothing
# after it on every page load."
ROW_WAS = """<br/>

<!-- Filter Panel -->"""

ROW_NOW = """<br/>

<!-- THE CHIPS LIVE OUTSIDE THE PANEL - 30 Sep. F1 made this panel close
     on load; the chips were inside it, so closing it hid what the list
     was filtered by. base's words on the component: a closed panel must
     never mean invisible filtering. base also counts these and shows the
     row - this page writes chips and nothing else. -->
<div class="alv-filter-active" id="recipeActiveFilters">
    <span class="alv-filter-active-label">Active filters:</span>
    <div class="filter-tags" id="recipeFilterTags"></div>
</div>

<!-- Filter Panel -->"""

# ==========================================================================
# 2. THE FIVE RULES base HAS SAID SINCE 22 SEP
# ==========================================================================
CSS_WAS = """.recipe-active-filters {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #dee2e6;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.recipe-filter-tags { display: flex; gap: 8px; flex-wrap: wrap; }

.recipe-filter-tag {
    background: #28a745;
    color: white;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}

.recipe-remove-tag {
    background: rgba(255, 255, 255, 0.3);
    border: none;
    color: white;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 10px;
    line-height: 1;
}

.recipe-remove-tag:hover { background: rgba(255, 255, 255, 0.5); }"""

CSS_NOW = """/* THE CHIP RULES WERE HERE, AND base HAS OWNED THEM SINCE 22 SEP -
   ALV FILTER CHIP v1. Five rules: the row, the holder, the chip, its x
   and the x's hover. The chip was #28a745; every other chip in the
   system is the accent, and this one was green for no reason this page
   could give. The row's own top border and margin went too - it needed
   a separator when it sat at the bottom of the panel, and it does not
   now that it sits above it.

   NOTHING REPLACES THEM. base's phone treatment comes with them, which
   this page never had: the x is 16px to see and 44px to tap, and the
   chips print while the x does not.
                                              [test_recipe_chips.py] */"""

# ==========================================================================
# 3. THE SCRIPT - base COUNTS, THE PAGE WRITES
# ==========================================================================
# Each of these is a separate question with its own count, so a change in
# the page that moves one of them cannot be absorbed silently by another.
JS = [
    ("""    const activeFiltersDiv = document.getElementById('recipeActiveFilters');\n""",
     '', 1,
     'the row element is no longer looked up - nothing here touches it'),
    ('recipe-filter-tag', 'filter-tag', 6,
     'six chips take base\'s class'),
    ('recipe-remove-tag', 'remove-tag', 6,
     '  and six x buttons take base\'s'),
    ("""    let hasFilters = false;\n""", '', 1,
     'hasFilters is declared no more'),
    ("""        hasFilters = true;\n""", '', 6,
     '  nor set in six branches'),
    ("""\n    activeFiltersDiv.style.display = hasFilters ? 'flex' : 'none';\n""",
     '', 1,
     '  because base owns .has-filters, and two writers of one fact is '
     'one too many'),
]

# ==========================================================================
print('=' * 74)
print('SECTION F, ROUND F2 - THE CHIPS COME OUT OF THE PANEL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(PAGE)
t, raw = read(p)
print('  %s' % PAGE)
if 'alv-filter-active' in t:
    print('     already wears base\'s chip row')
else:
    t = swap(t, p, MK_WAS, MK_NOW,
             'the row leaves the panel, and the form with it', PAGE)
    t = swap(t, p, ROW_WAS, ROW_NOW,
             '  and lands between the action bar and the panel, as on the '
             'other ten', PAGE)
    t = swap(t, p, CSS_WAS, CSS_NOW,
             'five page-local rules go - base has said all five since '
             '22 Sep', PAGE)

    # THE FUNCTION, AND ONLY THE FUNCTION. The renames below are bare
    # words that also appear in the CSS and the markup; by the time we get
    # here neither is left, but slicing to the function says so instead of
    # relying on it.
    i = t.find('function updateRecipeActiveFilters() {')
    if i < 0:
        raise SystemExit('F2: %s - updateRecipeActiveFilters is not there'
                         % PAGE)
    j = t.find(eol(p, '\n}\n'), i)
    if j < 0:
        raise SystemExit('F2: %s - the function does not close' % PAGE)
    j += len(eol(p, '\n}\n'))
    fn = t[i:j]
    for was, now, count, what in JS:
        fn = swap(fn, p, was, now, what, 'the chip writer', count)
    t = t[:i] + fn + t[j:]

    # GATES.
    mk = re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S)
    mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
    for gone in ('recipe-active-filters', 'recipe-filter-tags',
                 'recipe-filter-tag', 'recipe-remove-tag'):
        n = re.sub(r'/\*.*?\*/|<!--.*?-->', '', t, flags=re.S).count(gone)
        if n:
            raise SystemExit('F2: %s still says %s %d time(s)'
                             % (PAGE, gone, n))
    if 'activeFiltersDiv' in t or 'hasFilters' in t:
        raise SystemExit('F2: %s still computes the row\'s visibility'
                         % PAGE)
    # THE QUOTES ARE NOT DECORATION. Counting the bare word counts the
    # label too - .alv-filter-active-label contains it - and the first
    # version of this gate refused on a page that was correct.
    if mk.count('class="alv-filter-active"') != 1:
        raise SystemExit('F2: %s has %d chip rows, not 1'
                         % (PAGE, mk.count('class="alv-filter-active"')))
    # THE POINT OF THE WHOLE ROUND, ASKED AS A POSITION. The row must come
    # BEFORE the panel in the document - which is what puts it outside it,
    # and outside the form the panel contains.
    i_row = mk.index('alv-filter-active')
    i_panel = mk.index('id="recipeFilterPanel"')
    i_form = mk.index('id="recipeFilterForm"')
    if not i_row < i_panel < i_form:
        raise SystemExit('F2: %s - the row is at %d, the panel at %d and '
                         'the form at %d; the row must come first'
                         % (PAGE, i_row, i_panel, i_form))
    if 'style="display' in mk[i_row - 200:i_row + 200]:
        raise SystemExit('F2: %s - the row still carries an inline display'
                         % PAGE)
    # base's interface is the class names, so say them.
    if 'class="filter-tags"' not in mk or 'alv-filter-active-label' not in mk:
        raise SystemExit('F2: %s - the row is not wearing base\'s holder '
                         'and label' % PAGE)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ==========================================================================
# 4. F1'S SUITE PINNED WHAT F2 OWNS - lesson 17, and F2 is the trigger
#
#   F1's section 5 is the record of what F1 left: the chips are still
#   page-local, still inside the panel, still green. Every word of that
#   was true the day F1 landed, and all three lines fail the moment this
#   round runs - with nothing wrong.
#
#   The repair the programme already uses: F1 judges the page AS F1 LEFT
#   IT. Then F1 keeps saying its true thing - that F1 did not move the
#   chips - however many rounds later F2 does.
# ==========================================================================
F1_WAS = """head('5. WHAT THIS ROUND LEFT, AND SAID SO')
# ==========================================================================
ok('.recipe-filter-tag' in bare,"""

F1_NOW = """head('5. WHAT THIS ROUND LEFT, AND SAID SO - AS THIS ROUND LEFT IT')
# ==========================================================================
# F2 took all three of these on 30 Sep, which is the right thing to have
# done: this section is the reason it existed. What F1 is answerable for
# is having left them and said so, and that stays true - so read the page
# as F1 left it, not as it stands.
try:
    from alv_rounds import as_left_by
    _mine = as_left_by(alv_tree.path_of(PAGE), SUFFIX, read)
except Exception:
    _mine = page
bare = re.sub(r'/\\*.*?\\*/', '', css_of(_mine), flags=re.S)
mk = mk_of(_mine)
ok('.recipe-filter-tag' in bare,"""

q = os.path.join(os.getcwd(), F1)
t1, raw1 = read(q)
print('  %s' % F1)
if '_mine' in t1:
    print('     already judges the page as F1 left it')
else:
    t1 = swap(t1, q, F1_WAS, F1_NOW,
              'its "what I left" section reads the page as F1 left it', F1)
    if not CHECK:
        back_up(q, raw1)
        write(q, t1)

print('-' * 74)
print('  the chips sit above the panel now, in the house accent, and base')
print('  numbers the Filter button from them - so a closed panel says')
print('  "Filter 3" instead of saying nothing at all.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
