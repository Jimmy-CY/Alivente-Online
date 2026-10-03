# -*- coding: utf-8 -*-
"""UC-2 - THE CONVERSIONS FILTER MOVES INTO THE HOUSE PANEL,
         AND THE SEVENTH HAND-ROLLED SEGMENTED CONTROL GOES

The fourth and last page of the filter programme Demetri agreed on 2 Oct,
and the one that is different: it already HAS a filter, and a working one.
Search, From-Unit and a three-way scope toggle, all client-side, all
composed in one applyFilters().

So this round does not build a filter. It moves one.

==========================================================================
WHAT STAYS, AND WHY THAT IS THE POINT
==========================================================================
applyFilters() is NOT replaced by base's data-live-search. It composes
THREE narrowings and base's component owns row.style.display outright -
the same argument FL-1 made for Measurement Units, and here it is three
filters rather than two. One function decides a row's fate from all three
inputs; nothing else writes that property.

The logic is untouched. What changes is where the controls live and what
they look like.

==========================================================================
THE SEVENTH HAND-ROLLED SEGMENTED CONTROL
==========================================================================
UC-1b left a note on this page two days ago saying exactly this:

    "The CONTROL is not converted - it is the seventh hand-rolled
     segmented control in the tree and base has had ALV-SEG since 2 Sep,
     but that changes how it LOOKS and needs its own round."

This is that round. All / Specific / Generic becomes .alv-seg - the same
control MC-1 put in the Meal Plans bar yesterday - and .scope-toggle,
.scope-btn, its :last-child, .active and :hover go, with #dee2e6, #6c757d
and #f8f9fa.

THE PRESSED SEGMENT IS MARKED aria-pressed, NOT class="active". That is
both the standard's hook for the fill and the thing a screen reader
needs; the old one said class="active" and told assistive technology
nothing. setScopeFilter reads and writes the attribute now, so there is
one record of which scope is on instead of a class and a module global
both claiming to know.

==========================================================================
THE COUNT MOVES INTO THE PANEL
==========================================================================
.filter-results-count said "Showing 12 of 97" beside the Clear button.
With the panel closed that line would be invisible exactly when it
matters, so it goes above the table instead, where the thing it is
counting is.

Backups: .bak_convfilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_convfilter'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'unit_conversions_management.html')


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
            raise SystemExit('UC2: %s is not a byte copy' % bak)


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def swap(text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(TPL):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('UC2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('UC-2 - THE CONVERSIONS FILTER INTO THE HOUSE PANEL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)

if 'filterPanel' in t:
    print('  unit_conversions           already in the house panel')
else:
    # ======================================================================
    # 1. THE FILTER BUTTON, THE CHIPS, AND THE PANEL.
    # ======================================================================
    t = swap(t, """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
""",
             """        <button type="button" class="btn action-filter" id="filterBtn"
                aria-pressed="false" aria-controls="filterPanel"
                aria-label="Show filters">
          <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
        </button>

        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipe Management">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>

    <div class="alv-filter-active" id="activeFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="filterTags"></div>
    </div>

    {# THE PANEL - UC-2, 3 Oct 2026. The fourth and last page of the      #}
    {# filter programme, and the only one that already had a filter. The  #}
    {# three controls are the same three; applyFilters() below is         #}
    {# unchanged except for how it reads the scope. What moved is where   #}
    {# they live and what they look like.                                 #}
    {#                                                                    #}
    {# NO data-live-search, for the reason FL-1 wrote down for            #}
    {# measurement_units and which is stronger here: base's live search   #}
    {# owns row.style.display outright, and this page composes THREE      #}
    {# narrowings. One function decides from all three.                   #}
    {#                                                                    #}
    {# No <form> - the view reads no query parameter and returns every    #}
    {# conversion.                                                        #}
    <div class="alv-filter filter-panel" id="filterPanel">
      <div class="filter-header">
        <h5 class="filter-title">
          <i class="fas fa-filter"></i> <span class="filter-title-text">Conversion Filters</span><span class="filter-title-text-mobile">Filters</span>
        </h5>
        <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
        </button>
      </div>

      <div class="filter-content" id="filterContent">
        <div class="filter-grid">
          <div class="filter-group">
            <label class="filter-label" for="conversionSearch">
              <i class="fas fa-search"></i> <strong>Search</strong>
            </label>
            <div class="search-input-group">
              <input type="text"
                     id="conversionSearch"
                     class="form-control search-input"
                     placeholder="Ingredient or unit..."
                     oninput="applyFilters()">
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-label" for="fromUnitFilter">
              <i class="fas fa-ruler"></i> <strong>From Unit</strong>
            </label>
            <select id="fromUnitFilter" class="form-control filter-select" onchange="applyFilters()">
              <option value="">All From-Units</option>
              {% for name in all_unit_names %}
              <option value="{{ name|lower }}">{{ name }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label" id="scopeLabel">
              <i class="fas fa-filter"></i> <strong>Applies To</strong>
            </label>
            {# THE SEVENTH HAND-ROLLED SEGMENTED CONTROL, CONVERTED.      #}
            {# UC-1b left a note here two days ago saying this control    #}
            {# was the seventh in the tree and that converting it needed  #}
            {# its own round. This is that round, and the control is      #}
            {# base's .alv-seg - the one MC-1 put in the Meal Plans bar.  #}
            {#                                                            #}
            {# aria-pressed, NOT class="active". It is the standard's     #}
            {# hook for the fill AND what a screen reader needs, in one   #}
            {# attribute instead of neither, and it means the pressed     #}
            {# scope is recorded in ONE place.                            #}
            <div class="alv-seg" role="group" aria-labelledby="scopeLabel">
              <button type="button" aria-pressed="true"
                      onclick="setScopeFilter('all', this)">All</button>
              <button type="button" aria-pressed="false"
                      onclick="setScopeFilter('specific', this)"><i class="fas fa-star"></i> Specific</button>
              <button type="button" aria-pressed="false"
                      onclick="setScopeFilter('generic', this)"><i class="fas fa-globe"></i> Generic</button>
            </div>
          </div>
        </div>
      </div>
    </div>
""",
             'the action bar')

    # ======================================================================
    # 2. THE OLD BAR GOES.
    # ======================================================================
    t = swap(t, """        <!-- Filter Bar -->
        <div class="filter-bar">
            <input type="text"
                   id="conversionSearch"
                   class="filter-input"
                   placeholder="\U0001f50d Search by ingredient or unit..."
                   oninput="applyFilters()">

            <select id="fromUnitFilter" class="filter-select" onchange="applyFilters()">
                <option value="">All From-Units</option>
                {% for name in all_unit_names %}
                <option value="{{ name|lower }}">{{ name }}</option>
                {% endfor %}
            </select>

            <div class="scope-toggle">
                <button class="scope-btn active" onclick="setScopeFilter('all', this)">All</button>""",
             """        {# THE BAR IS GONE - UC-2, 3 Oct 2026. Search, From-Unit and the #}
        {# scope toggle are in the house panel at the top of the page,   #}
        {# collapsed on load. What is left here is the count, which      #}
        {# belongs beside the thing it counts: with the panel closed, a  #}
        {# "Showing 12 of 97" inside it would be invisible exactly when  #}
        {# it matters.                                                   #}
        <div class="conversions-count">
            <span class="filter-results-count" id="filterResultsCount"></span>
        </div>
        {% comment %}""",
             'the head of the old bar')

    t = swap(t, """                <button class="scope-btn" onclick="setScopeFilter('specific', this)"><i class="fas fa-star"></i> Specific</button>
                <button class="scope-btn" onclick="setScopeFilter('generic', this)"><i class="fas fa-globe"></i> Generic</button>
            </div>

            <span class="filter-results-count" id="filterResultsCount"></span>

            <button class="btn btn-sm btn-outline-secondary" onclick="clearFilters()">
                <i class="fas fa-times"></i> Clear
            </button>
        </div>
        """,
             """        {% endcomment %}
        """,
             'the tail of the old bar')

    # ======================================================================
    # 3. THE CSS THE OLD BAR CARRIED.
    # ======================================================================
    t = swap(t, """/* Filter Bar */
.filter-bar {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
}""",
             """/* THE BAR'S RULES ARE GONE - UC-2, 3 Oct 2026. .filter-bar,
   .scope-toggle, .scope-btn and its :last-child, .active and :hover, and
   the two 768px fragments that sized them. base owns the panel, the grid
   and the segmented control now, so the only rule left here is where the
   count sits. #dee2e6, #6c757d and #f8f9fa left with them. */
.conversions-count {
    margin-bottom: 14px;
    text-align: right;
}""",
             'the filter-bar rule')

    t = swap(t, """.scope-toggle {
    display: flex;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
}

.scope-btn {
    padding: 9px 16px;
    border: none;
    background: white;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: #6c757d;
    border-right: 1px solid #dee2e6;
    transition: all 0.2s;
    white-space: nowrap;
}

.scope-btn:last-child {
    border-right: none;
}

.scope-btn.active {
    background: var(--alv-accent);
    color: white;
}

.scope-btn:hover:not(.active) {
    background: #f8f9fa;
}

""", '', 'the scope-toggle rules')

    t = swap(t, """    /* Filter bar — stack */
    .filter-bar {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }
        .scope-toggle {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
    }
    .scope-btn {
        padding: 10px 4px;
    }
    .filter-results-count {
        text-align: center;
    }
    .filter-bar > .btn {
        width: 100%;
    }

""",
             """    /* The bar's phone rules went with it - UC-2. base stacks the panel
       to one column under 768px and sizes .alv-seg itself. */
    .conversions-count {
        text-align: center;
    }

""",
             'the 768 fragment')

    # AND THE ONE REFERENCE THAT IS NOT A RULE OF ITS OWN. .filter-input
    # also appears in the iOS zoom guard's shared selector list, which is
    # not the bar's CSS and was not removed with it. .filter-select stays
    # there - it is base's class and the From Unit select still wears it.
    t = swap(t, """    textarea,
    .filter-input,
    .filter-select {""",
             """    textarea,
    .filter-select {""",
             'the zoom guard selector list')

    # ======================================================================
    # 4. THE SCRIPT - ONE RECORD OF THE SCOPE.
    # ======================================================================
    t = swap(t, """function setScopeFilter(scope, btn) {
    currentScope = scope;
    document.querySelectorAll('.scope-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    applyFilters();
}""",
             """function setScopeFilter(scope, btn) {
    // ARIA-PRESSED IS THE RECORD - UC-2, 3 Oct 2026. The old version set
    // a class AND a module global, two things remembering one fact. The
    // attribute is base's hook for the fill and what a screen reader
    // needs, so it is the one that stays; currentScope is still here
    // because applyFilters reads it on every keystroke and an attribute
    // lookup per row would be the only thing this round made slower.
    currentScope = scope;
    document.querySelectorAll('.alv-seg [aria-pressed]').forEach(
        b => b.setAttribute('aria-pressed', 'false'));
    btn.setAttribute('aria-pressed', 'true');
    applyFilters();
}""",
             'setScopeFilter')

    t = swap(t, """function clearFilters() {
    document.getElementById('conversionSearch').value = '';
    document.getElementById('fromUnitFilter').value = '';
    currentScope = 'all';
    document.querySelectorAll('.scope-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.scope-btn').classList.add('active');
    applyFilters();
}""",
             """function clearFilters() {
    document.getElementById('conversionSearch').value = '';
    document.getElementById('fromUnitFilter').value = '';
    currentScope = 'all';
    const segs = document.querySelectorAll('.alv-seg [aria-pressed]');
    segs.forEach(b => b.setAttribute('aria-pressed', 'false'));
    if (segs.length) { segs[0].setAttribute('aria-pressed', 'true'); }
    applyFilters();
}

/* THE CHIPS - UC-2. base derives the Filter button's count badge from
   them through a MutationObserver, so a page that builds none gets no
   badge. Three filters, up to three chips, and each one's x puts its own
   control back to its default and re-runs the narrowing. */
function syncFilterChips() {
    const tags = document.getElementById('filterTags');
    if (!tags) { return; }
    tags.innerHTML = '';
    const add = function (label, value, reset) {
        const c = document.createElement('span');
        c.className = 'filter-tag';
        c.textContent = label + ': ' + value + ' ';
        const x = document.createElement('button');
        x.type = 'button';
        x.className = 'remove-tag';
        x.setAttribute('aria-label', 'Remove the ' + label + ' filter');
        x.innerHTML = '<i class="fas fa-times"></i>';
        x.addEventListener('click', function () { reset(); applyFilters(); });
        c.appendChild(x);
        tags.appendChild(c);
    };
    const box = document.getElementById('conversionSearch');
    const unit = document.getElementById('fromUnitFilter');
    if (box && box.value.trim()) {
        add('Search', box.value.trim(), function () { box.value = ''; });
    }
    if (unit && unit.value) {
        add('From unit', unit.options[unit.selectedIndex].text,
            function () { unit.value = ''; });
    }
    if (currentScope !== 'all') {
        add('Applies to',
            currentScope === 'generic' ? 'Generic' : 'Specific',
            function () {
                currentScope = 'all';
                const segs = document.querySelectorAll(
                    '.alv-seg [aria-pressed]');
                segs.forEach(b => b.setAttribute('aria-pressed', 'false'));
                if (segs.length) {
                    segs[0].setAttribute('aria-pressed', 'true');
                }
            });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    syncFilterChips();
    // CLEAR ALL HAS TO BE WIRED - UC-2. The old bar carried its own
    // Clear button with onclick="clearFilters()"; that button went with
    // the bar, and the panel's #clearAllBtn is markup base styles but
    // does not wire. Without this the control is there and does nothing,
    // which test_conversion_filter.py section 4 caught by pressing it.
    var clear = document.getElementById('clearAllBtn');
    if (clear) { clear.addEventListener('click', clearFilters); }
});""",
             'clearFilters')

    # THE CHIPS HAVE TO BE REBUILT BY THE SAME FUNCTION THAT NARROWS, or
    # the row would be right and the chips stale.
    t = swap(t, """    // Update count
    const total = {{ conversions.count }};""",
             """    syncFilterChips();

    // Update count
    const total = {{ conversions.count }};""",
             'the chip call in applyFilters')

    if not CHECK:
        back_up(TPL, raw)
        write(TPL, t)
    print('  unit_conversions           panel, chips, and the seventh '
          'segmented control converted')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

NOW = read(TPL)[0]
CODE = code_only(NOW)
WAS = code_only(read(TPL + SUFFIX)[0])
BASE = code_only(open(alv_tree.path_of('base.html'), encoding='utf-8',
                      errors='replace').read())

# 1. THE HOUSE CONTROL.
for need in ('class="btn action-filter"', 'aria-controls="filterPanel"',
             'id="filterPanel"', 'id="activeFilters"', 'id="filterTags"',
             'id="clearAllBtn"', 'class="filter-grid"', 'class="alv-seg"'):
    if need not in CODE:
        raise SystemExit('UC2: missing %s' % need)
panel = CODE[CODE.index('id="filterPanel"'):]
if 'is-open' in panel[:400]:
    raise SystemExit('UC2: the panel opens on load')
print('  the house control, panel closed on load, seg inside it')

# 2. THE OLD BAR AND ITS CONTROL ARE GONE.
for dead in ('filter-bar', 'scope-toggle', 'scope-btn', 'filter-input'):
    if re.search(r'\b%s\b' % dead, CODE):
        raise SystemExit('UC2: %s is still in the code' % dead)
print('  no .filter-bar, .scope-toggle, .scope-btn or .filter-input')

# 3. THE LITERALS THOSE RULES CARRIED - counted, because the page uses
#    #6c757d and #dee2e6 elsewhere and a claim that they are gone from
#    the page would be claiming more than this round did.
for lit, k in (('#dee2e6', 2), ('#6c757d', 1), ('#f8f9fa', 1)):
    got = WAS.count(lit) - CODE.count(lit)
    if got != k:
        raise SystemExit('UC2: dropped %d uses of %s, expected %d '
                         '(%d before, %d after)'
                         % (got, lit, k, WAS.count(lit), CODE.count(lit)))
print('  dropped the literals the old control carried')

# 4. ONE RECORD OF THE SCOPE, AND IT IS THE ONE base READS.
seg = CODE[CODE.index('class="alv-seg"'):]
seg = seg[:seg.index('</div>')]
n_press = len(re.findall(r'aria-pressed="(?:true|false)"', seg))
if n_press != 3:
    raise SystemExit('UC2: %d segments carry aria-pressed, expected three'
                     % n_press)
if seg.count('aria-pressed="true"') != 1:
    raise SystemExit('UC2: %d segments are pressed, expected one'
                     % seg.count('aria-pressed="true"'))
if "classList.add('active')" in CODE or "classList.remove('active')" in CODE:
    raise SystemExit('UC2: the scope is still recorded as a class as well')
if '.alv-seg > [aria-pressed="true"]' not in BASE:
    raise SystemExit('UC2: base does not fill a pressed segment')
print('  three segments, one pressed, recorded where base reads it')

# 5. THE NARROWING ITSELF DID NOT CHANGE. The whole premise of this round
#    is that the logic was already right; a round that quietly altered it
#    while moving the controls would be very hard to spot.
body_now = CODE[CODE.index('function applyFilters()'):]
body_now = body_now[:body_now.index('function ', 10)]
body_was = WAS[WAS.index('function applyFilters()'):]
body_was = body_was[:body_was.index('function ', 10)]
for keep in ("row.getAttribute('data-from-unit')",
             "row.getAttribute('data-to-unit')",
             "row.getAttribute('data-ingredient')",
             "row.getAttribute('data-generic') === 'true'",
             'searchMatch && unitMatch && scopeMatch'):
    if keep not in body_now:
        raise SystemExit('UC2: applyFilters lost %r' % keep[:44])
    if body_was.count(keep) != body_now.count(keep):
        raise SystemExit('UC2: applyFilters changed at %r' % keep[:44])
if body_now.count('row.style.display') != body_was.count('row.style.display'):
    raise SystemExit('UC2: the number of writers of display changed')
print('  applyFilters narrows on the same three things, the same way')

# 6. AND NOTHING ELSE WRITES display.
# ONE OWNER, NOT ONE OCCURRENCE. The first cut of this gate demanded a
# single mention of row.style.display and found two - the two branches of
# one if/else inside applyFilters, which is the correct shape and the
# very thing this round is protecting. What matters is that no OTHER
# function writes it.
_hits = [m.start() for m in re.finditer(r'row\.style\.display', CODE)]
_fn = CODE.index('function applyFilters()')
_end = CODE.index('function ', _fn + 10)
outside = [h for h in _hits if not (_fn < h < _end)]
if outside:
    raise SystemExit('UC2: %d writer(s) of row.style.display outside '
                     'applyFilters, at line(s) %s'
                     % (len(outside),
                        ', '.join(str(CODE.count('\n', 0, h) + 1)
                                  for h in outside)))
if 'data-live-search' in CODE:
    raise SystemExit('UC2: this page composes three narrowings and base\'s '
                     'live search owns display outright')
print('  one writer of row.style.display, and no data-live-search')

# 6b. CLEAR ALL IS WIRED. base styles #clearAllBtn and does not wire it;
#     the old bar's Clear went with the bar, so without this the control
#     is present and inert.
if "getElementById('clearAllBtn')" not in CODE:
    raise SystemExit('UC2: #clearAllBtn is not wired - the panel would '
                     'carry a Clear All that does nothing')
if 'clear.addEventListener' not in CODE:
    raise SystemExit('UC2: #clearAllBtn is found and never listened to')
print('  Clear All is wired to clearFilters')

# 7. THE COUNT IS OUTSIDE THE PANEL, where it can be seen with the panel
#    shut.
# ANCHORED ON MARKUP, NOT ON A COMMENT. The first cut bounded the panel
# with '<!-- Conversions Table -->' and searched CODE for it - and
# code_only BLANKS HTML comments, so the marker was never found, the
# bound fell back to the end of the file, and the test said the count was
# inside the panel on a page where it is not. An instrument whose first
# act is to delete the comments cannot then look for one.
i_panel = CODE.index('id="filterPanel"')
i_card = CODE.index('class="conversions-card"')
i_count = CODE.index('id="filterResultsCount"')
if not (i_panel < i_card < i_count):
    raise SystemExit('UC2: the count is not out with the table - panel at '
                     '%d, card at %d, count at %d' % (i_panel, i_card,
                                                      i_count))
print('  the count sits beside the table, not inside a closed panel')

print('-' * 74)
print('  UC-1b wrote two days ago that this control was the seventh and')
print('  needed its own round. That round is this one, and the tree now')
print('  has one segmented control instead of two.')
print('=' * 74)
