# -*- coding: utf-8 -*-
"""FL-1 - CATEGORIES AND MEASUREMENT UNITS GET THE HOUSE FILTER

Demetri agreed the filter programme on 2 Oct for four pages. IB-1
delivered the first. These are the second and third; Unit Conversions,
which already has a working bespoke filter, is its own round.

Asked on 3 Oct how deep to go on these two, he chose CLIENT-SIDE ONLY:

    "the panel narrows what is on screen as you type, and that is all it
     does. No view changes, no URL parameters."

and for Measurement Units, SEARCH PLUS A TYPE FILTER.

==========================================================================
THE TWO PAGES USE DIFFERENT MECHANISMS, ON PURPOSE
==========================================================================
Categories has ONE filter, so it takes base's component:

    data-live-search=".categories-table"
    data-live-search-cell="Category Name"

Measurement Units has TWO that have to compose, and it must NOT use that
component. base's live search owns row.style.display outright - it walks
every row on every keystroke and sets display from its own query alone.
A Type dropdown setting the same property is a second owner of one fact,
and the last one to run wins: pick a Type, then type a letter, and the
Type narrowing silently evaporates.

So Measurement Units gets one function that decides a row's visibility
from BOTH inputs at once - the shape unit_conversions_management already
uses for its three. One writer for one property.

That is a real claim and the suite gates it: this page must NOT carry
data-live-search, and the reason is named rather than left to look like
an oversight.

==========================================================================
NO FORM, AND THAT IS NOT AN OVERSIGHT EITHER
==========================================================================
Every other filter panel in the tree wraps its fields in
<form method="get">, because F1 established that a filter is a VIEW and
the URL should carry it. These two have nothing to submit TO - neither
view reads a query parameter - so a form here would put a box in front of
Demetri that clears itself when he presses Enter. base's filter script
already guards for this: `var form = panel.querySelector('form'); if
(form) ...`.

The cost was stated before it was chosen: the URL will not carry these
two filters, so Back and refresh forget them.

==========================================================================
THE CHIP ROW IS NOT AN EXTRA
==========================================================================
base derives the Filter button's count badge from the chips, through a
MutationObserver over .alv-filter-active. A page that builds no chips
gets no badge - so the chips are part of the round, not decoration.

Backups: .bak_reffilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_reffilter'
ROOT = os.getcwd()
CRLF = {}

CAT = os.path.join(ROOT, 'pages', 'templates', 'categories_management.html')
UNI = os.path.join(ROOT, 'pages', 'templates',
                   'measurement_units_management.html')


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
            raise SystemExit('FL1: %s is not a byte copy' % bak)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('FL1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


FILTER_BTN = """        <button type="button" class="btn action-filter" id="filterBtn"
                aria-pressed="false" aria-controls="filterPanel"
                aria-label="Show filters">
          <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
        </button>
"""

CHIPS = """
    <div class="alv-filter-active" id="activeFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="filterTags"></div>
    </div>
"""

print('=' * 74)
print('FL-1 - CATEGORIES AND MEASUREMENT UNITS GET THE HOUSE FILTER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. CATEGORIES - one filter, so it takes base's component.
# ==========================================================================
t, raw = read(CAT)

if 'filterPanel' in t:
    print('  categories_management      already has the panel')
else:
    t = swap(CAT, t,
             """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
""",
             FILTER_BTN +
             """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
""" + CHIPS + """
    {# THE PANEL - FL-1, 3 Oct 2026. Collapsed on load, which is base's   #}
    {# default: .alv-filter is display:none until .is-open.               #}
    {#                                                                    #}
    {# NO <form>. Every other filter panel in the tree submits with GET,  #}
    {# because F1 established that a filter is a VIEW and the URL should  #}
    {# carry it. This page has nothing to submit TO - the view reads no   #}
    {# query parameter and returns every category - so a form here would  #}
    {# put a box in front of you that clears itself when you press Enter. #}
    {# Demetri chose client-side only on 3 Oct, with that cost stated.    #}
    <div class="alv-filter filter-panel" id="filterPanel">
      <div class="filter-header">
        <h5 class="filter-title">
          <i class="fas fa-filter"></i> <span class="filter-title-text">Category Filters</span><span class="filter-title-text-mobile">Filters</span>
        </h5>
        <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
        </button>
      </div>

      <div class="filter-content" id="filterContent">
        <div class="filter-grid">
          <div class="filter-group">
            <label class="filter-label" for="searchInput">
              <i class="fas fa-search"></i> <strong>Search Category</strong>
            </label>
            <div class="search-input-group">
              {# ONE FILTER, SO base's COMPONENT FITS EXACTLY. It owns    #}
              {# row.style.display and nothing else on this page writes   #}
              {# that property, so there is one owner of one fact.        #}
              {# measurement_units_management has TWO filters and         #}
              {# deliberately does NOT use this - see the note there.     #}
              <input type="text"
                     id="searchInput"
                     class="form-control search-input"
                     data-live-search=".categories-table"
                     data-live-search-cell="Category Name"
                     placeholder="Search by name...">
            </div>
          </div>
        </div>
      </div>
    </div>
""",
             'the categories bar')

    # THESE PAGES HAVE NO extra_scripts BLOCK. The first cut anchored on
    # one, the way most templates in this tree are written; categories and
    # measurement_units put their script inline at the end of {% block
    # content %} instead. The anchor is the closing endblock.
    t = swap(CAT, t, """</script>

{% endblock %}""",
             """</script>
<script>
/* FL-1, 3 Oct 2026 - THE CHIP, AND NOTHING ELSE.
   The narrowing is base's: data-live-search on the box above. This only
   keeps the chip row in step, because base derives the Filter button's
   count badge from the chips through a MutationObserver - a page that
   builds no chips gets no badge, which is why the chips are part of the
   round rather than decoration. */
(function () {
    var box = document.getElementById('searchInput');
    var tags = document.getElementById('filterTags');
    var clear = document.getElementById('clearAllBtn');
    if (!box || !tags) { return; }

    function sync() {
        tags.innerHTML = '';
        var v = box.value.trim();
        if (!v) { return; }
        var chip = document.createElement('span');
        chip.className = 'filter-tag';
        chip.textContent = 'Search: ' + v + ' ';
        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'remove-tag';
        x.setAttribute('aria-label', 'Remove the search filter');
        x.innerHTML = '<i class="fas fa-times"></i>';
        x.addEventListener('click', function () {
            box.value = '';
            /* THE EVENT, NOT THE FUNCTION. base's live search listens on
               input; it does not expose anything to call. Clearing the
               value without telling it would leave the rows narrowed to
               a search the box no longer shows. */
            box.dispatchEvent(new Event('input', {bubbles: true}));
            sync();
        });
        chip.appendChild(x);
        tags.appendChild(chip);
    }

    box.addEventListener('input', sync);
    if (clear) {
        clear.addEventListener('click', function () {
            box.value = '';
            box.dispatchEvent(new Event('input', {bubbles: true}));
            sync();
        });
    }
    sync();
}());
</script>

{% endblock %}""",
             'the categories script block')

    if not CHECK:
        back_up(CAT, raw)
        write(CAT, t)
    print('  categories_management      Filter button, panel, chips, '
          'live search')

# ==========================================================================
# 2. MEASUREMENT UNITS - two filters, so the page composes them itself.
# ==========================================================================
t, raw = read(UNI)

if 'filterPanel' in t:
    print('  measurement_units          already has the panel')
else:
    t = swap(UNI, t,
             """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
""",
             FILTER_BTN +
             """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
""" + CHIPS + """
    {# THE PANEL - FL-1, 3 Oct 2026. Search plus Type, Demetri's choice:  #}
    {# Type is the only column here with a small fixed set of values,     #}
    {# which is what a dropdown is for, and Usage is a derived count      #}
    {# rather than something you filter by.                               #}
    {#                                                                    #}
    {# NO data-live-search ON THIS PAGE, AND THAT IS DELIBERATE. base's   #}
    {# live search owns row.style.display outright: it walks every row    #}
    {# on every keystroke and sets display from its own query alone. The  #}
    {# Type dropdown sets the same property, so the two would be two      #}
    {# owners of one fact and the last to run would win - pick a Type,    #}
    {# then type a letter, and the Type narrowing silently evaporates.    #}
    {# One function decides from both inputs instead, which is the shape  #}
    {# unit_conversions_management already uses for its three.            #}
    {#                                                                    #}
    {# No <form> either - the view reads no query parameter. See the      #}
    {# note on categories_management.                                     #}
    <div class="alv-filter filter-panel" id="filterPanel">
      <div class="filter-header">
        <h5 class="filter-title">
          <i class="fas fa-filter"></i> <span class="filter-title-text">Unit Filters</span><span class="filter-title-text-mobile">Filters</span>
        </h5>
        <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
        </button>
      </div>

      <div class="filter-content" id="filterContent">
        <div class="filter-grid">
          <div class="filter-group">
            <label class="filter-label" for="unitSearch">
              <i class="fas fa-search"></i> <strong>Search Unit</strong>
            </label>
            <div class="search-input-group">
              <input type="text"
                     id="unitSearch"
                     class="form-control search-input"
                     placeholder="Name or abbreviation...">
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-label" for="unitTypeFilter">
              <i class="fas fa-layer-group"></i> <strong>Type</strong>
            </label>
            <select id="unitTypeFilter" class="form-control filter-select">
              <option value="">All types</option>
              {% for value, label in unit_types %}
              <option value="{{ value }}">{{ label }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
      </div>
    </div>
""",
             'the units bar')

    # THE TYPE HAS TO BE ON THE ROW. Reading it out of the cell would read
    # the Font Awesome badge AND the edit <select> beside it, which carries
    # every type as an <option> - so every row would match every type.
    t = swap(UNI, t,
             """                <tr id="unit-row-{{ item.unit.measurement_unit_id }}" data-unit-id="{{ item.unit.measurement_unit_id }}">""",
             """                {# data-unit-type - FL-1. The Type CELL cannot be read for this: #}
                {# it holds the badge AND, for an editor, a <select> carrying   #}
                {# every type as an <option>, so a text match on the cell would #}
                {# match every row against every type. The row carries the one  #}
                {# value instead.                                               #}
                <tr id="unit-row-{{ item.unit.measurement_unit_id }}" data-unit-id="{{ item.unit.measurement_unit_id }}" data-unit-type="{{ item.unit.unit_type }}">""",
             'the units row')

    t = swap(UNI, t, """</script>

{% endblock %}""",
             """</script>
<script>
/* FL-1, 3 Oct 2026 - ONE WRITER FOR row.style.display.
   Search and Type both decide whether a row is shown, so one function
   decides it from both. Two independent filters each setting display is
   two owners of one fact, and the last to run wins. */
(function () {
    var box = document.getElementById('unitSearch');
    var type = document.getElementById('unitTypeFilter');
    var tags = document.getElementById('filterTags');
    var clear = document.getElementById('clearAllBtn');
    var body = document.getElementById('unitsTableBody');
    if (!box || !type || !body) { return; }

    function norm(s) { return (s || '').toLowerCase().trim(); }

    function chip(label, value, reset) {
        var c = document.createElement('span');
        c.className = 'filter-tag';
        c.textContent = label + ': ' + value + ' ';
        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'remove-tag';
        x.setAttribute('aria-label', 'Remove the ' + label + ' filter');
        x.innerHTML = '<i class="fas fa-times"></i>';
        x.addEventListener('click', function () { reset(); apply(); });
        c.appendChild(x);
        return c;
    }

    function apply() {
        var q = norm(box.value);
        var want = type.value;
        var rows = body.querySelectorAll('tr[data-unit-id]');
        var shown = 0;
        Array.prototype.forEach.call(rows, function (row) {
            var name = row.querySelector('[data-label="Unit Name"]');
            var abbr = row.querySelector('[data-label="Abbreviation"]');
            /* THE SEARCH MATCHES THE TWO COLUMNS IT SAYS IT MATCHES.
               Not the whole row: Usage holds every recipe name that uses
               the unit, so a whole-row match would find "cup" in a
               recipe called Cupcakes and show a unit that has nothing to
               do with the word. */
            var hay = norm((name ? name.textContent : '') + ' '
                           + (abbr ? abbr.textContent : ''));
            var hit = (!q || hay.indexOf(q) >= 0)
                   && (!want || row.getAttribute('data-unit-type') === want);
            row.style.display = hit ? '' : 'none';
            if (hit) { shown += 1; }
        });

        var empty = document.getElementById('unitsNoMatch');
        if (empty) { empty.style.display = shown ? 'none' : ''; }

        if (tags) {
            tags.innerHTML = '';
            if (box.value.trim()) {
                tags.appendChild(chip('Search', box.value.trim(),
                    function () { box.value = ''; }));
            }
            if (type.value) {
                tags.appendChild(chip('Type',
                    type.options[type.selectedIndex].text,
                    function () { type.value = ''; }));
            }
        }
    }

    box.addEventListener('input', apply);
    type.addEventListener('change', apply);
    if (clear) {
        clear.addEventListener('click', function () {
            box.value = '';
            type.value = '';
            apply();
        });
    }
    apply();
}());
</script>

{% endblock %}""",
             'the units script block')

    t = swap(UNI, t, """            <tbody id="unitsTableBody">""",
             """            <tbody id="unitsTableBody">
                {# A NARROWING THAT FINDS NOTHING HAS TO SAY SO - FL-1.   #}
                {# An empty table with no message reads as a page that    #}
                {# failed to load.                                        #}
                <tr id="unitsNoMatch" style="display: none;">
                    <td colspan="5" class="alv-empty-title">
                        No measurement units match these filters.
                    </td>
                </tr>""",
             'the units empty row')

    if not CHECK:
        back_up(UNI, raw)
        write(UNI, t)
    print('  measurement_units          Filter button, panel, chips, '
          'search and Type')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

C = code_only(read(CAT)[0])
U = code_only(read(UNI)[0])
BASE = code_only(read(alv_tree.path_of('base.html'))[0])

# 1. BOTH WEAR THE HOUSE CONTROL, WIRED THE WAY base EXPECTS.
for name, src in (('categories_management', C),
                  ('measurement_units', U)):
    for need in ('class="btn action-filter"', 'aria-controls="filterPanel"',
                 'aria-pressed="false"', 'id="filterPanel"',
                 'class="alv-filter filter-panel"', 'id="activeFilters"',
                 'id="filterTags"', 'id="clearAllBtn"',
                 'class="filter-grid"'):
        if need not in src:
            raise SystemExit('FL1: %s is missing %s' % (name, need))
    # COLLAPSED ON LOAD IS AN ABSENCE, NOT A SETTING.
    panel = src[src.index('id="filterPanel"'):]
    if 'is-open' in panel[:400]:
        raise SystemExit('FL1: %s opens its panel on load' % name)
    print('  %-26s the house control, panel closed on load' % name)

# 2. BASE REALLY OWNS WHAT THEY ASK FOR.
for cls in ('.action-filter', '.alv-filter', '.filter-grid', '.filter-tag',
            '.alv-filter-active', '.filter-header', '.filter-group'):
    if not re.search(re.escape(cls) + r'[\s,{:]', BASE):
        raise SystemExit('FL1: base does not define %s' % cls)
if 'repeat(auto-fit, minmax(200px, 240px))' not in BASE:
    raise SystemExit('FL1: base has no capped track list - FG-1 must land '
                     'before this round or these panels stack')
print('  base owns every class, including FG-1\'s capped track list')

# 3. THE ONE REAL CLAIM: TWO FILTERS, ONE WRITER.
if 'data-live-search' in C:
    if C.count('data-live-search=') != 1:
        raise SystemExit('FL1: categories has %d live-search boxes'
                         % C.count('data-live-search='))
else:
    raise SystemExit('FL1: categories has one filter and should use base\'s '
                     'component for it')
if 'data-live-search' in U:
    raise SystemExit('FL1: measurement_units carries data-live-search. It '
                     'has TWO filters, and base\'s live search owns '
                     'row.style.display outright - the Type narrowing would '
                     'evaporate on the next keystroke.')
if U.count('row.style.display') != 1:
    raise SystemExit('FL1: measurement_units has %d writers of '
                     'row.style.display, expected exactly one'
                     % U.count('row.style.display'))
print('  categories uses base\'s live search; measurement_units composes '
      'its two itself, with ONE writer of display')

# 4. THE TYPE COMES OFF THE ROW, NOT OUT OF THE CELL.
if 'data-unit-type="{{ item.unit.unit_type }}"' not in read(UNI)[0]:
    raise SystemExit('FL1: the row does not carry its type')
if re.search(r'data-label="Type"[^>]*>[^<]*unitTypeFilter', U):
    raise SystemExit('FL1: the filter reads the Type cell, which holds an '
                     'edit <select> carrying every type as an option')
print('  the Type is read off the row, not out of a cell that holds a '
      '<select> of every type')

# 5. THE SEARCH MATCHES THE COLUMNS IT NAMES AND NOT THE ROW.
if "data-label=\"Usage\"" in U[U.index('function apply()'):
                               U.index('function apply()') + 1200]:
    raise SystemExit('FL1: the search reads Usage, which holds every recipe '
                     'name that uses the unit - "cup" would match a recipe '
                     'called Cupcakes')
for lab in ('Unit Name', 'Abbreviation'):
    if 'data-label="%s"' % lab not in U:
        raise SystemExit('FL1: the search does not name the %s column' % lab)
print('  the search names Unit Name and Abbreviation, and not Usage')

# 6. NO FORM, AND base TOLERATES THAT.
for name, src in (('categories_management', C), ('measurement_units', U)):
    panel = src[src.index('id="filterPanel"'):]
    panel = panel[:panel.index('</div>\n    </div>') + 8] \
        if '</div>\n    </div>' in panel else panel[:4000]
    if '<form' in panel:
        raise SystemExit('FL1: %s submits a filter to a view that reads no '
                         'query parameter' % name)
if "panel.querySelector('form')" not in BASE:
    raise SystemExit('FL1: base no longer guards for a panel with no form')
print('  neither panel carries a form, and base guards for exactly that')

# 7. AN EMPTY RESULT SAYS SO.
if 'unitsNoMatch' not in U:
    raise SystemExit('FL1: a narrowing that finds nothing says nothing')
print('  a narrowing that finds nothing says so')

print('-' * 74)
print('  One filter takes the component; two filters take a function.')
print('  base\'s live search owns row.style.display outright, so a second')
print('  thing setting it is not a second filter - it is a race.')
print('=' * 74)
