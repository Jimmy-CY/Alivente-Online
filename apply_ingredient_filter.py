# -*- coding: utf-8 -*-
"""SECTION IB, ROUND IB-1 - THE INGREDIENT FILTER, ONTO THE HOUSE PANEL

Demetri, with a screenshot of Ingredient Shopping Units: "Can we create a
Filter Button. Then the filter section is compressed on load. Then can the
ingredient search box be search as you type?"

Agreed shape: FOLLOW suppliers.html EXACTLY. Clear moves into the panel
header as "Clear All", an .alv-filter-active chip row sits above the panel,
and the bespoke .filter-row becomes the house .filter-grid.

==========================================================================
NOTHING HERE IS INVENTED - base OWNS ALL FOUR PIECES
==========================================================================
    .action-filter + aria-pressed + aria-controls="filterPanel"   11 pages
    .alv-filter { display: none } / .is-open     collapsed IS the default
    .alv-filter-active + .action-filter-count    the badge, counted by base
    data-live-search / -cell                     alv-live-search v2, 1 Oct

THE BADGE IS NOT THIS PAGE'S JOB. base wires a MutationObserver over the
chip row: it counts .filter-tag, writes the number into
.action-filter-count, and toggles .has-filters. So the page builds chips
and base does the rest - and a page that builds no chips gets no badge,
which is why the chip row is part of this round and not an extra.

==========================================================================
WHY THIS PAGE MAY HAVE LIVE SEARCH, ASKED OF THE VIEW
==========================================================================
base states the contract in two parts, and both are checked below against
ingredient_base_units_management itself rather than assumed:

  1. IT MATCHES THE COLUMNS THE SERVER MATCHES, AND NO OTHERS. The view
     does name__icontains and nothing else, and the column carrying that
     name is data-label="Ingredient Name". So the live filter and the
     same box pressed with Enter give the same answer. A live filter
     matching a column the server ignores would not.

  2. ONLY FOR A TABLE THAT HOLDS EVERY ROW. There is no Paginator in this
     view - all 374 ingredients render - so the browser can see every row
     it is being asked about. `projects` paginates at 25 and is
     deliberately NOT opted in.

==========================================================================
WHAT MOVES ON THE SCREEN
==========================================================================
    before   a white card with Search / Category / Clear, always open,
             pushing the table down on every visit
    after    a Filter button in the bar, the panel closed, a chip row
             naming what is set, and the search narrowing as you type

The bar reads Map Nutrition / Conversions / Filter / Back - two primaries,
the filter, Back. A-BAR order, unchanged by this round except for where
the new button sits.

Backups: .bak_ingfilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_ingfilter'
ROOT = os.getcwd()
CRLF = {}

TPL = os.path.join(ROOT, 'pages', 'templates',
                   'ingredient_base_units_management.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'conversions.py')
FN = 'ingredient_base_units_management'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('IB1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('IB1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION IB, ROUND IB-1 - THE INGREDIENT FILTER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 0. THE PREMISE, BEFORE ANYTHING IS WRITTEN.
#
# base's live-search contract is a claim about THIS view, so it is measured
# here rather than taken on trust - and the round refuses if it does not
# hold, because a live filter that disagrees with the server is worse than
# no live filter at all.
# ==========================================================================
import ast

vt = read(VIEW)[0]
_fn = [n for n in ast.walk(ast.parse(vt)) if isinstance(n, ast.FunctionDef)
       and n.name == FN]
if not _fn:
    raise SystemExit('IB1: %s is not in conversions.py' % FN)
vsrc = ast.get_source_segment(vt, _fn[0]) or ''
vcode = re.sub(r'(?m)#.*$', '', re.sub(r'"""[\s\S]*?"""', '', vsrc))

cols = sorted(set(re.findall(r'(\w+)__icontains', vcode)))
if cols != ['name']:
    raise SystemExit('IB1: the view searches %s, not name alone - the live '
                     'filter would disagree with it' % cols)
if 'Paginator' in vcode or 'paginate' in vcode.lower():
    raise SystemExit('IB1: the view paginates - the browser cannot see every '
                     'row and must not be asked to filter them')
print('  the view searches name__icontains only, and does not paginate')

# ==========================================================================
# 1. THE TEMPLATE.
# ==========================================================================
t, raw = read(TPL)

BACK = """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
"""

FILTER_BTN = """        {# IB-1, 2 Oct 2026. The house filter button: base hides            #}
        {# .alv-filter and shows it on .is-open, so COLLAPSED ON LOAD is    #}
        {# the default rather than something this page arranges. The count  #}
        {# span is filled by base, which counts the chips below.            #}
        <button type="button" class="btn action-filter" id="filterBtn"
                aria-pressed="false" aria-controls="filterPanel"
                aria-label="Show filters">
          <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
        </button>

"""

# THE BLANK LINES IN THIS ANCHOR ARE NOT BLANK - they carry sixteen
# spaces, and an editor that trims trailing whitespace silently turns an
# anchor that matches once into one that matches none. That has cost this
# repo two rounds already (A-BAR's view_meal_plan, ML-1's button line), so
# the padding is spliced in rather than typed.
PAD16 = ' ' * 16

OLD_PANEL = ("""    <!-- Filter Bar -->
    <div class="filter-bar">
        <form method="GET" id="filterForm">
            <div class="filter-row">
                <div class="form-group" style="margin: 0;">
                    <label style="font-weight: 600; margin-bottom: 8px;">Search Ingredient</label>
                    <div class="search-with-icon">
                        <input type="text" name="search" class="form-control" placeholder="Search by name..." value="{{ search_query }}">
                        <i class="fas fa-search search-icon" onclick="document.getElementById('filterForm').submit()"></i>
                    </div>
                </div>
""" + PAD16 + """
                <div class="form-group" style="margin: 0;">
                    <label style="font-weight: 600; margin-bottom: 8px;">Filter by Category</label>
                    <select name="category" class="form-control" id="categoryFilter" onchange="this.form.submit()">
                        <option value="">All Categories</option>
                        {% for cat in categories %}
                        <option value="{{ cat.ingredient_category_id }}" {% if category_filter == cat.ingredient_category_id|stringformat:"s" %}selected{% endif %}>
                            {{ cat.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
""" + PAD16 + """
                <div style="display: flex; gap: 10px; align-items: end;">
                    <a href="{% url 'ingredient_base_units_management' %}" class="btn btn-secondary" style="height: 42px;">
                        <i class="fas fa-times"></i> Clear
                    </a>
                </div>
            </div>
        </form>
    </div>
""")

NEW_PANEL = """    {# IB-1, 2 Oct 2026 - THE CHIP ROW. base counts .filter-tag inside   #}
    {# this element with a MutationObserver, writes the number into the  #}
    {# Filter button's badge, and toggles .has-filters to show or hide   #}
    {# the row. One writer for the row's visibility, and it is not here. #}
    <div class="alv-filter-active" id="activeFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="filterTags"></div>
    </div>

    <!-- Collapsible Filter Panel -->
    <div class="alv-filter filter-panel" id="filterPanel">
      <div class="filter-header">
        <h5 class="filter-title">
          <i class="fas fa-filter"></i> <span class="filter-title-text">Ingredient Filters</span><span class="filter-title-text-mobile">Filters</span>
        </h5>
        {# CLEAR LIVES IN THE HEADER NOW, as on suppliers. It used to be a #}
        {# third column of the filter row, which made the row three things #}
        {# wide on a phone for the sake of one link.                       #}
        <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
        </button>
      </div>

      <div class="filter-content" id="filterContent">
        {# GET, NOT POST - Section F round F1, 1 Oct 2026. A filter is a    #}
        {# VIEW, not a change: the URL carries it, Back works, and a        #}
        {# refresh does not re-submit. No csrf token on a GET form - it     #}
        {# would serialise into the address bar, the history and the        #}
        {# Referer.                                  [test_filter_get.py]   #}
        <form action="{% url 'ingredient_base_units_management' %}" method="get" id="filterForm">
          <div class="filter-grid">
            <div class="filter-group">
              <label class="filter-label">
                <i class="fas fa-search"></i> <strong>Search Ingredient</strong>
              </label>
              <div class="search-input-group">
                {# SEARCH AS YOU TYPE - alv-live-search v2. The cell named  #}
                {# here is the one column the view searches                 #}
                {# (name__icontains), so the live filter and the same box   #}
                {# pressed with Enter give the same answer. The view does   #}
                {# not paginate, so the browser holds every row it is being #}
                {# asked about. Both halves are gated in this round.        #}
                <input type="text"
                       name="search"
                       id="searchInput"
                       class="form-control search-input"
                       data-live-search=".ingredients-table"
                       data-live-search-cell="Ingredient Name"
                       placeholder="Search by name..."
                       value="{{ search_query }}">
                <button type="button" class="search-btn" id="searchBtn">
                  <i class="fas fa-search"></i>
                </button>
              </div>
            </div>

            <div class="filter-group">
              <label class="filter-label">
                <i class="fas fa-tags"></i> <strong>Category</strong>
              </label>
              <select name="category" class="form-control filter-select" id="categoryFilter">
                <option value="">All Categories</option>
                {% for cat in categories %}
                <option value="{{ cat.ingredient_category_id }}" {% if category_filter == cat.ingredient_category_id|stringformat:"s" %}selected{% endif %}>{{ cat.name }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
        </form>
      </div>
    </div>
"""

OLD_CSS = """.filter-bar {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    margin-bottom: 25px;
}

.filter-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 15px;
    align-items: end;
}

"""

NEW_CSS = """/* .filter-bar and .filter-row are GONE - IB-1, 2 Oct 2026. The house
   .alv-filter panel carries its own card, its own grid and its own phone
   behaviour, so a local copy of all three could only drift from it. The
   two phone overrides below went with them. */

"""

OLD_ICON_CSS = """.search-with-icon {
    position: relative;
}

.search-with-icon input {
    padding-right: 38px;
}

.search-icon {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #6c757d;
    font-size: 16px;
    cursor: pointer;
    transition: color 0.2s ease;
}

.search-icon:hover {
    color: #343a40;
}

"""

OLD_CSS_M = """    .filter-bar {
        padding: 14px;
        margin-bottom: 16px;
        border-radius: 10px;
    }
    .filter-row {
        grid-template-columns: 1fr;
        gap: 12px;
    }
    .filter-row > div[style*="display: flex"][style*="align-items: end"] {
        justify-content: stretch;
    }
    .filter-row .btn {
        width: 100%;
        justify-content: center;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

"""

JS = """
<script>
/* IB-1, 2 Oct 2026 - THE CHIPS, AND NOTHING ELSE.
   base opens and closes the panel, counts the chips, writes the badge and
   toggles the row's visibility. What is left for the page is what only the
   page knows: which filters it has, and what to call them. */
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('filterForm');
  var searchInput = document.getElementById('searchInput');
  var categorySelect = document.getElementById('categoryFilter');
  if (!form || !searchInput || !categorySelect) return;

  updateActiveFilters();

  categorySelect.addEventListener('change', function () { form.submit(); });

  var searchBtn = document.getElementById('searchBtn');
  if (searchBtn) {
    searchBtn.addEventListener('click', function () { form.submit(); });
  }

  /* ENTER SUBMITS, which is the whole point of keeping the server read.
     The live filter narrows what is on screen; Enter asks the server, and
     because the two match the same column the answer is the same. */
  searchInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); form.submit(); }
  });

  var clearAllBtn = document.getElementById('clearAllBtn');
  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', function () {
      searchInput.value = '';
      categorySelect.value = '';
      form.submit();
    });
  }
});

function updateActiveFilters() {
  var searchInput = document.getElementById('searchInput');
  var categorySelect = document.getElementById('categoryFilter');
  var tags = document.getElementById('filterTags');
  if (!searchInput || !categorySelect || !tags) return;
  tags.innerHTML = '';
  var search = (searchInput.value || '').trim();
  if (search !== '') {
    tags.innerHTML += '<span class="filter-tag">Search: "' + search
      + '" <button class="remove-tag" onclick="clearFilter(\\'search\\')">&times;</button></span>';
  }
  var opt = categorySelect.options[categorySelect.selectedIndex];
  if (categorySelect.value !== '' && opt) {
    tags.innerHTML += '<span class="filter-tag">Category: '
      + opt.textContent.trim()
      + ' <button class="remove-tag" onclick="clearFilter(\\'category\\')">&times;</button></span>';
  }
}

function clearFilter(which) {
  var form = document.getElementById('filterForm');
  if (which === 'search') {
    var s = document.getElementById('searchInput');
    if (s) s.value = '';
  } else if (which === 'category') {
    var c = document.getElementById('categoryFilter');
    if (c) c.value = '';
  }
  if (form) form.submit();
}
</script>
"""

if 'IB-1, 2 Oct 2026' in t:
    print('  ingredient_base_units_management.html   already on the house '
          'panel')
else:
    t = swap(t, BACK, FILTER_BTN + BACK, 'the Back link in the bar', TPL)
    t = swap(t, OLD_PANEL, NEW_PANEL, 'the old filter bar', TPL)
    t = swap(t, OLD_CSS, NEW_CSS, 'the .filter-bar CSS', TPL)
    t = swap(t, OLD_CSS_M, '', 'the phone overrides', TPL)
    # THE SEARCH ICON GOES WITH ITS MARKUP. Four rules styling a magnifying
    # glass welded into a text box - the house .search-input-group does
    # that, with a real <button> rather than an <i> carrying an onclick, so
    # it is reachable from a keyboard. Leaving the rules behind would have
    # left the dead-rule shape C-1 and UC-1 both found.
    t = swap(t, OLD_ICON_CSS, '', 'the search-icon rules', TPL)
    t = t.rstrip('\n') + '\n' + JS
    if not CHECK:
        back_up(TPL, raw)
        write(TPL, t)
    print('  ingredient_base_units_management.html   Filter button, chip '
          'row, house panel, live search')

# ==========================================================================
# 2. base GAINS THE TWO LABEL SWAPS.
#
# Caught by the render, which is what renders are for. The panel header has
# a long label and a short one for each of its two pieces - "Ingredient
# Filters" / "Filters", "Clear All" / "Clear" - and base hides neither, so
# BOTH printed: "Ingredient Filters Filters" and "Clear AllClear".
#
# suppliers.html carries the three rules LOCALLY. Copying them onto a
# second page would start the twelfth local copy of a filter rule in this
# tree, which is the drift this whole programme exists to stop - and base
# already owns every other class in that header (.filter-header,
# .filter-title, .filter-group, .filter-label, .search-input-group,
# .filter-tag). These belong beside them.
#
# suppliers' own copy is left exactly where it is. It is identical, so it
# is duplication and not disagreement, and removing a rule from a page that
# is on Live is not this round's business. The gate counts the copies and
# pins the number, so a thirteenth is reported the day it is written.
# ==========================================================================
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
bt, braw = read(BASE)

B_ANCHOR = """.filter-group {
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: visible;
}
"""

B_NEW = """/* THE HEADER'S TWO LABELS - IB-1, 2 Oct 2026.
   A filter panel header carries a long label and a short one for each of
   its two pieces, and shows one of each. Without these, BOTH print:
   "Ingredient Filters Filters" and "Clear AllClear" - which is exactly
   what the IB-1 render caught before the round went anywhere.

   suppliers.html has carried these three rules locally since 23 Sep. They
   are here now because base owns every other class in that header, and a
   second page copying them would have been the twelfth local copy of a
   filter rule in this tree. The suppliers copy is identical and is left
   alone; test_ingredient_filter.py pins the count.      [ALV FILTER v1] */
.filter-title-text-mobile,
.clear-all-text-mobile { display: none; }
@media screen and (max-width: 768px) {
  .filter-title-text { display: none; }
  .filter-title-text-mobile { display: inline; }
  .clear-all-text { display: none; }
  .clear-all-text-mobile { display: inline; }
}

.filter-group {
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: visible;
}
"""

if 'IB-1, 2 Oct 2026' in bt:
    print('  base.html                               already swaps the '
          'header labels')
else:
    bt = swap(bt, B_ANCHOR, B_NEW, 'the .filter-group rule in base', BASE)
    if not CHECK:
        back_up(BASE, braw)
        write(BASE, bt)
    print('  base.html                               the header shows one '
          'label of each pair')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(TPL)[0]
code = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
code = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), code, flags=re.S)
# AND THE THIRD KIND OF COMMENT - IB-1, 2 Oct 2026.
#
# The dead-class gate below fired on its own explanation. This file's note
# in the stylesheet says ".filter-bar and .filter-row are GONE", and a gate
# looking for .filter-bar found it there and reported the class as
# surviving - a round refusing to finish because of a sentence saying the
# thing it was looking for had been removed.
#
# That is the same defect as the Favourites tag this morning and the
# os.walk grep before it, in a THIRD syntax: a template carries Django
# comments, HTML comments AND CSS/JS block comments, and an instrument that
# strips two of the three can still read prose as code. Blanking preserves
# length so every line number reported below is still the file's own.
code = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), code, flags=re.S)

# 1. THE FOUR HOUSE PIECES ARE PRESENT, EACH EXACTLY ONCE.
for frag, what in (
        ('class="btn action-filter" id="filterBtn"', 'the Filter button'),
        ('aria-controls="filterPanel"', 'the control it names'),
        ('class="alv-filter filter-panel" id="filterPanel"', 'the panel'),
        ('class="alv-filter-active" id="activeFilters"', 'the chip row'),
        ('class="action-filter-count"', 'the count badge'),
        ('class="filter-grid"', 'the house grid'),
        ('id="clearAllBtn"', 'Clear All, in the header'),
        ('data-live-search=".ingredients-table"', 'the live search'),
        ('data-live-search-cell="Ingredient Name"', 'and the column it reads')):
    n = code.count(frag)
    if n != 1:
        raise SystemExit('IB1: %s appears %d times, not once' % (what, n))
print('  nine house pieces, each exactly once')

# 2. THE LIVE-SEARCH CELL IS A COLUMN THAT EXISTS ON THIS TABLE.
m = re.search(r'data-live-search-cell="([^"]+)"', code)
cell = m.group(1)
labels = set(re.findall(r'data-label="([^"]+)"', code))
if cell not in labels:
    raise SystemExit('IB1: the live filter reads %r, and the table has no '
                     'such column: %s' % (cell, sorted(labels)))
sel = re.search(r'data-live-search="([^"]+)"', code).group(1)
if not re.search(r'<table[^>]*class="[^"]*\b%s\b' % sel.lstrip('.'), code):
    raise SystemExit('IB1: the live filter points at %r and no table carries '
                     'that class' % sel)
print('  and it names a column (%s) on a table that is really there (%s)'
      % (cell, sel))

# 3. THE SERVER AND THE BROWSER STILL AGREE - re-asked AFTER the write, so
#    a view edited later cannot leave a live filter behind that lies.
vt = read(VIEW)[0]
vsrc = ast.get_source_segment(vt, [n for n in ast.walk(ast.parse(vt))
                                   if isinstance(n, ast.FunctionDef)
                                   and n.name == FN][0]) or ''
vcode = re.sub(r'(?m)#.*$', '', re.sub(r'"""[\s\S]*?"""', '', vsrc))
if sorted(set(re.findall(r'(\w+)__icontains', vcode))) != ['name']:
    raise SystemExit('IB1: the view no longer searches name alone')
if 'Paginator' in vcode:
    raise SystemExit('IB1: the view paginates now - the live filter must go')
print('  the view still searches one column and still holds every row')

# 4. THE PANEL IS CLOSED ON LOAD - which means the page does NOT add
#    .is-open itself. base's default IS closed; a page that opens it would
#    be answering a question it was not asked.
if re.search(r'class="[^"]*\balv-filter\b[^"]*\bis-open\b', code):
    raise SystemExit('IB1: the panel ships with .is-open - it must load '
                     'collapsed')
print('  the panel carries no .is-open, so it loads collapsed')

# 5. A-BAR ORDER STILL HOLDS: primaries, filter, Back.
bar = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', code,
                re.S)
if not bar:
    raise SystemExit('IB1: the action bar is gone')
b = bar.group(1)
i_p = b.index('action-primary')
i_f = b.index('action-filter')
i_b = b.index('action-back')
if not i_p < i_f < i_b:
    raise SystemExit('IB1: the bar is out of A-BAR order - primary %d, '
                     'filter %d, back %d' % (i_p, i_f, i_b))
print('  the bar reads primaries, filter, Back - A-BAR order holds')

# 6. THE OLD PANEL IS GONE, MARKUP AND CSS, with nothing left referring to
#    it. A rule with no markup is the dead-rule shape C-1 and UC-1 both hit.
for dead in ('filter-bar', 'filter-row', 'search-with-icon', 'search-icon'):
    n = len(re.findall(r'\b%s\b' % dead, code))
    if n:
        raise SystemExit('IB1: %r survives %d time(s)' % (dead, n))
print('  .filter-bar, .filter-row and the search-icon pair are gone, '
      'markup and CSS')

# 7. THE CHIPS ARE BUILT, AND THE PAGE DOES NOT TOUCH VISIBILITY.
if 'id="filterTags"' not in code:
    raise SystemExit('IB1: there is no chip container for base to count')
if re.search(r'activeFilters[^\n]*style\.display', code):
    raise SystemExit('IB1: the page sets the chip row display itself - base '
                     'is the one writer for that')
if 'filter-tag' not in code:
    raise SystemExit('IB1: nothing builds a .filter-tag, so the badge would '
                     'always read zero')
print('  the page builds chips and leaves the row visibility to base')

# 8. THE MARKUP STILL CLOSES, AND NO COMMENT IS IN THE WRONG PLACE OR SHAPE
#    - B-1b and B-1c, both in one day, both reached Live.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', code))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', code))
    if a != z:
        raise SystemExit('IB1: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', code, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('IB1: %+d unbalanced <div>' % d)
if [i for i, ln in enumerate(t.split('\n'), 1)
        if '{#' in ln and '#}' not in ln]:
    raise SystemExit('IB1: a Django comment spans lines - the lexer has no '
                     'DOTALL')
OPENER, CLOSER = '<' + '!--', '--' + '>'
depth = 0
for mm in re.finditer(r'<[a-zA-Z/!]|>', t):
    if mm.group(0) == '>':
        depth = max(0, depth - 1)
    elif t.startswith(OPENER, mm.start()):
        if depth:
            raise SystemExit('IB1: a comment opens inside a tag at line %d'
                             % (t.count('\n', 0, mm.start()) + 1))
    else:
        depth = 1
print('  every if, for and <div> closes, and no comment opens inside a tag')

# 9. THE CONTROL: the live-search gate really can fail.
_bad = '<input data-live-search=".ingredients-table" ' \
       'data-live-search-cell="Nothing Like This">'
_cell = re.search(r'data-live-search-cell="([^"]+)"', _bad).group(1)
if _cell in labels:
    raise SystemExit('IB1: the fixture column exists - pick another')
print('  CONTROL: a cell naming a column the table does not have is caught')

# 10. THE LABEL SWAPS ARE IN base, AND ONLY ONE PAGE STILL HAS ITS OWN.
bt = read(BASE)[0]
bcode = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), bt, flags=re.S)
for rule in ('.filter-title-text-mobile', '.clear-all-text-mobile',
             '.filter-title-text', '.clear-all-text'):
    if not re.search(re.escape(rule) + r'[\s,{]', bcode):
        raise SystemExit('IB1: base does not carry %s' % rule)
if 'display: inline' not in bcode.split('.filter-title-text-mobile')[-1][:400]:
    raise SystemExit('IB1: base hides the mobile label and never shows it')
print('  base carries both label swaps, desktop and phone')

# FOUR, NOT ONE. The round was written believing suppliers.html was the
# only page carrying these rules; the gate said four, which is the whole
# point of asking the tree rather than the page you happened to read. They
# are identical copies, so this is duplication and not disagreement, and
# none of the four is touched here - base simply means a FIFTH was not
# written. Pinned by name so a fifth is reported the day it appears.
LOCALS = ('passport_management.html', 'properties.html', 'suppliers.html',
          'tenant.html')
import alv_tree
local = []
for p in alv_tree.templates():
    if os.path.basename(p) == 'base.html':
        continue
    pt = read(p)[0]
    pc = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), pt, flags=re.S)
    if re.search(r'(?m)^\s*\.(filter-title-text-mobile|clear-all-text)[\s,{]',
                 pc):
        local.append(os.path.basename(p))
if sorted(local) != sorted(LOCALS):
    raise SystemExit('IB1: %d page(s) define the label swaps locally, '
                     'expected %s: %s' % (len(local), list(LOCALS),
                                          sorted(local)))
print('  and the %d page(s) that define them locally are pinned by name'
      % len(LOCALS))
for _p in LOCALS:
    print('      %s' % _p)

# AND NOTHING ELSE IN base MOVED. The round added one block; a round that
# touches base has to say precisely how much.
was = read(BASE + SUFFIX)[0]
grew = len(bt.split('\n')) - len(was.split('\n'))
if grew != 20:
    raise SystemExit('IB1: base grew by %d lines, not the 20 this round '
                     'writes' % grew)
import difflib
removed = [ln for ln in difflib.unified_diff(was.split('\n'),
                                             bt.split('\n'), lineterm='', n=0)
           if ln.startswith('-') and not ln.startswith('---')]
if removed:
    raise SystemExit('IB1: base LOST %d line(s): %s'
                     % (len(removed), removed[:3]))
print('  base gained %d lines and lost none' % grew)

print('-' * 74)
print('  The panel is closed until asked for, the chips say what is set,')
print('  and the search narrows the rows the server would have narrowed.')
print('=' * 74)
