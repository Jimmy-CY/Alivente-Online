# -*- coding: utf-8 -*-
"""SECTION F, ROUND F1 - RECIPE MANAGEMENT JOINS THE HOUSE FILTER

Demetri: every module with a filter section should adopt the small Filter
button at the top; the panel must not show on load and should open only
when the button is pressed. Recipe Management needs to change. The A to Z
and the Grid / List / Book selector need to be teal.

MEASURED FIRST. Eleven pages in the tree have a filter UI. TEN of them
already do exactly what he asked - Properties, Suppliers, Tenants,
Invoices, Passports, Expenses, Physical Invoices, FSR, Projects and
Celebrations all wear .action-filter plus .alv-filter, and .alv-filter is
`display: none` until base's own script opens it.

Recipe Management is the ONE that does not - and it is not a page that
forgot the component. It is a page running a complete parallel copy:

    .recipe-filter-panel      its own panel
    .recipe-filter-header     its own header, with its own onclick
    .recipe-filter-content    its own collapse, .expanded, its own JS
    toggleRecipeFilterPanel() its own open/close, its own sessionStorage
    .recipe-filter-tag        its own chip family, in green

So this round does not recolour it. It deletes the copy.

WHAT CHANGES, AND WHAT OPENS THE PANEL NOW
    The panel gains .alv-filter, so base's rule hides it on load and
    base's script - the same one the other ten pages use - opens it when
    the Filter button is pressed. The button joins the action bar with
    aria-controls pointing at the panel, which is how base finds it.

    The page's own header onclick and chevron go, because two things
    opening one panel is two things that can disagree about whether it is
    open.

    expandRecipeFilterPanel() STAYS, and is rewired. Five places call it -
    after applying a filter, after clearing one - because the form
    submits and the page reloads. Those callers are right and they are
    untouched; only the body changes, to open the house panel instead of
    the page's own.

WHAT THIS ROUND DOES NOT DO, ON PURPOSE
    The chips stay where they are for now. They are a fourth copy of a
    component base owns - .recipe-filter-tag, green, INSIDE the panel,
    which means closing the panel currently hides what you are filtering
    by, and base's own comment on the component says a closed panel must
    never mean invisible filtering. Moving them means rewiring the
    function that writes them, and that deserves its own round and its
    own suite rather than riding along here.

Backups: .bak_recfilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_recfilter'
PAGE = 'recipe_management.html'
CRLF = {}


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
            raise SystemExit('F1: %s is not a byte copy' % bak)


def swap(text, path, was, now, what):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('F1: %s is there %d time(s), not 1'
                         % (what, text.count(a)))
    print('  %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# 1. THE BUTTON, in the action bar, beside the others
# ==========================================================================
BTN_WAS = """        <a href="{% url 'personal_page' %}" class="btn action-back" role="button" aria-label="Back to Personal">"""

BTN_NOW = """        <!-- THE HOUSE FILTER BUTTON. aria-controls is not decoration -
             base's script reads it to find the panel this button owns. -->
        <button type="button" class="btn action-filter" id="filterBtn"
                aria-pressed="false" aria-controls="recipeFilterPanel"
                aria-label="Show filters">
            <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count=""></span>
        </button>

        <a href="{% url 'personal_page' %}" class="btn action-back" role="button" aria-label="Back to Personal">"""

# ==========================================================================
# 2. THE PANEL becomes the house one
# ==========================================================================
PANEL_WAS = """<div class="recipe-filter-panel" id="recipeFilterPanel">
    <div class="recipe-filter-header" onclick="toggleRecipeFilterPanel()">
        <h5 class="recipe-filter-title">
            <i class="fas fa-filter"></i> Recipe Filters
            <i class="fas fa-chevron-down recipe-filter-toggle-icon" id="recipeFilterToggleIcon"></i>
        </h5>"""

PANEL_NOW = """<div class="alv-filter recipe-filter-panel" id="recipeFilterPanel">
    <!-- .alv-filter is what hides this on load and what base's script
         opens. The header no longer opens anything: one panel with two
         things toggling it is two things that can disagree about whether
         it is open. The chevron went with the onclick, because an arrow
         that does nothing is worse than no arrow. -->
    <div class="recipe-filter-header">
        <h5 class="recipe-filter-title">
            <i class="fas fa-filter"></i> Recipe Filters
        </h5>"""

# ==========================================================================
# 3. THE PAGE'S OWN COLLAPSE, removed
# ==========================================================================
CSS_WAS = """.recipe-filter-content {
    display: none;
}

.recipe-filter-content.expanded {
    display: block;
}"""

CSS_NOW = """/* THE CONTENT IS ALWAYS VISIBLE INSIDE THE PANEL - 30 Sep. It used to
   collapse separately, with its own .expanded class and its own script,
   INSIDE a panel that did not collapse at all. The panel is the thing
   that opens and closes now, and .alv-filter does that. */
.recipe-filter-content {
    display: block;
}"""

ICON_WAS = """.recipe-filter-toggle-icon {
    transition: transform 0.3s ease;
    margin-left: 8px;
    font-size: 14px;
}"""
ICON_NOW = """"""

HEADER_CURSOR_WAS = """    border-bottom: 2px solid #dee2e6;
    cursor: pointer;
}"""
HEADER_CURSOR_NOW = """    border-bottom: 2px solid #dee2e6;
}"""

# ==========================================================================
# 4. THE TWO FUNCTIONS
# ==========================================================================
TOGGLE_WAS = """function toggleRecipeFilterPanel() {
    const filterContent = document.getElementById('recipeFilterContent');
    const toggleIcon = document.getElementById('recipeFilterToggleIcon');
    if (filterContent.classList.contains('expanded')) {
        filterContent.classList.remove('expanded');
        toggleIcon.style.transform = 'rotate(0deg)';
        sessionStorage.setItem('recipeUserInteracted', 'false');
    } else {
        filterContent.classList.add('expanded');
        toggleIcon.style.transform = 'rotate(180deg)';
        sessionStorage.setItem('recipeUserInteracted', 'true');
    }
}"""

TOGGLE_NOW = """/* toggleRecipeFilterPanel() WAS HERE, and base's Filter button does its
   job now - the same button, the same script, on all eleven pages that
   have a filter. It is not replaced by anything on this page. */"""

EXPAND_WAS = """function expandRecipeFilterPanel() {
    const filterContent = document.getElementById('recipeFilterContent');
    const toggleIcon = document.getElementById('recipeFilterToggleIcon');
    if (filterContent && toggleIcon) {
        filterContent.classList.add('expanded');
        toggleIcon.style.transform = 'rotate(180deg)';
    }
}"""

EXPAND_NOW = """function expandRecipeFilterPanel() {
    /* KEPT, AND REWIRED. Five places call this - after a filter is
       applied, after one is cleared - because the form submits and the
       page reloads, and the panel should come back open. Those callers
       are right and none of them changed; only what this does changed,
       from opening the page's own collapse to opening the house panel.

       It sets aria-pressed as well as the class, because base's setOpen
       sets both and the button's own styling reads the attribute. */
    const panel = document.getElementById('recipeFilterPanel');
    const btn = document.getElementById('filterBtn');
    if (panel) { panel.classList.add('is-open'); }
    if (btn) { btn.setAttribute('aria-pressed', 'true'); }
}"""

LOAD_WAS = """    const filterContent = document.getElementById('recipeFilterContent');
    const toggleIcon = document.getElementById('recipeFilterToggleIcon');

    if (filterContent && toggleIcon) {
        filterContent.classList.remove('expanded');
        toggleIcon.style.transform = 'rotate(0deg)';
    }

    updateFilterDisplay('course');"""

LOAD_NOW = """    /* THE LOAD-TIME COLLAPSE IS NOT NEEDED ANY MORE. It reached for
       the content and the chevron to force them shut on every load -
       .alv-filter does that now, with a CSS rule, before any script
       runs. The panel is closed on load because it is never open until
       the button opens it. */

    updateFilterDisplay('course');"""

# ==========================================================================
# 5. THE TWO GREENS HE NAMED
# ==========================================================================
AZ_WAS = """.letter-filter-item.available { color: #28a745; border-color: #28a745; }
.letter-filter-item.available:hover {
    background: #28a745;
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}"""

AZ_NOW = """/* TEAL, ASKED FOR BY NAME - 30 Sep. Celebration Management's strip took
   the same tones in P3, which is why the two pages share these class
   names: one later round can lift the component into base once. */
.letter-filter-item.available { color: var(--alv-accent); border-color: var(--alv-accent); }
.letter-filter-item.available:hover {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    transform: translateY(-1px);
}"""

AZ_ACTIVE_WAS = """.letter-filter-item.active {
    background: #28a745;
    color: white;
    border-color: #28a745;
    box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}"""

AZ_ACTIVE_NOW = """.letter-filter-item.active {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    border-color: var(--alv-accent);
}"""

AZ_BAR_WAS = """.letter-filter-wrapper::-webkit-scrollbar-thumb { background: #28a745; border-radius: 3px; }
.letter-filter-wrapper::-webkit-scrollbar-thumb:hover { background: #218838; }"""
AZ_BAR_NOW = """.letter-filter-wrapper::-webkit-scrollbar-thumb { background: var(--alv-accent); border-radius: 3px; }
.letter-filter-wrapper::-webkit-scrollbar-thumb:hover { background: var(--alv-accent-ink); }"""

AZ_SCROLL_WAS = """    scrollbar-color: #28a745 #f1f1f1;"""
AZ_SCROLL_NOW = """    scrollbar-color: var(--alv-accent) var(--alv-surface);"""

VIEW_WAS = """.view-toggle-btn.active { background: #28a745; color: white; }"""
VIEW_NOW = """.view-toggle-btn.active { background: var(--alv-accent); color: var(--alv-on-accent); }"""

# ==========================================================================
print('=' * 74)
print('SECTION F, ROUND F1 - RECIPE MANAGEMENT JOINS THE HOUSE FILTER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# THE CENSUS, so the round says what it found before it moves.
house = []
for q in alv_tree.templates():
    t2 = read(q)[0]
    mk = re.sub(r'<style\b.*?</style>', '', t2, flags=re.S)
    # base DOCUMENTS both names in its standards block, which is prose.
    # Counting it would make the census one too many.
    if alv_tree.rel(q) == 'base.html':
        continue
    if 'action-filter' in mk and 'alv-filter' in mk:
        house.append(alv_tree.rel(q))
print('  %d page(s) already wear the house filter; this is the eleventh.'
      % len(house))

p = alv_tree.path_of(PAGE)
t, raw = read(p)

if 'action-filter' in t:
    print('  %s already joined' % PAGE)
else:
    t = swap(t, p, BTN_WAS, BTN_NOW, 'the Filter button joins the bar')
    t = swap(t, p, PANEL_WAS, PANEL_NOW,
             'the panel becomes .alv-filter - hidden on load, opened by '
             'the button')
    t = swap(t, p, CSS_WAS, CSS_NOW, 'the content stops collapsing on its own')
    t = swap(t, p, ICON_WAS, ICON_NOW, 'the chevron rule goes with the chevron')
    t = swap(t, p, HEADER_CURSOR_WAS, HEADER_CURSOR_NOW,
             '  and the header stops looking clickable')
    t = swap(t, p, LOAD_WAS, LOAD_NOW,
             'the load-time collapse goes - a CSS rule does it now, before '
             'any script runs')
    t = swap(t, p, TOGGLE_WAS, TOGGLE_NOW,
             'toggleRecipeFilterPanel is deleted - base owns the toggle')
    t = swap(t, p, EXPAND_WAS, EXPAND_NOW,
             'expandRecipeFilterPanel is kept and rewired - 5 callers, '
             'none of them changed')
    t = swap(t, p, AZ_WAS, AZ_NOW, 'the A to Z goes teal')
    t = swap(t, p, AZ_ACTIVE_WAS, AZ_ACTIVE_NOW, '  including the chosen letter')
    t = swap(t, p, AZ_BAR_WAS, AZ_BAR_NOW, '  and its scrollbar')
    t = swap(t, p, AZ_SCROLL_WAS, AZ_SCROLL_NOW, '  on Firefox too')
    t = swap(t, p, VIEW_WAS, VIEW_NOW, 'Grid / List / Book goes teal')

    # GATES.
    if 'toggleRecipeFilterPanel()' in re.sub(r'/\*.*?\*/', '', t, flags=re.S):
        raise SystemExit('F1: something still calls toggleRecipeFilterPanel')
    if len(re.findall(r'expandRecipeFilterPanel\(\)', t)) != 6:
        raise SystemExit('F1: expandRecipeFilterPanel has %d mention(s); '
                         'it had 6 - one definition and five callers'
                         % len(re.findall(r'expandRecipeFilterPanel\(\)', t)))
    if 'recipeFilterToggleIcon' in t:
        raise SystemExit('F1: the chevron id survives somewhere')
    mk = re.sub(r'<style\b.*?</style>', '', t, flags=re.S)
    mk = re.sub(r'<script\b.*?</script>', '', mk, flags=re.S)
    if 'aria-controls="recipeFilterPanel"' not in mk:
        raise SystemExit('F1: the button does not name the panel, so base '
                         'cannot find it')
    css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))
    bare = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    for sel in ('.letter-filter-item.available', '.letter-filter-item.active',
                '.view-toggle-btn.active'):
        m = re.search(re.escape(sel) + r'[^{]*\{([^}]*)\}', bare)
        if m and '#28a745' in m.group(1):
            raise SystemExit('F1: %s is still green' % sel)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

print('-' * 74)
print('  eleven of eleven now. The panel is closed on load and opens on')
print('  the button, the same way on every page that has one.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
