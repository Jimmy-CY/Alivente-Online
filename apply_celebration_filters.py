# -*- coding: utf-8 -*-
"""SECTION P, ROUND P1 - THE CELEBRATIONS FILTER GROWS TWO MORE AXES

Demetri asked for Event Type and Month alongside the search that is
already there.

WHAT THE PAGE SHOWS, AND THEREFORE WHAT EACH FILTER FILTERS.
    The page is a list of CONTACTS, each holding a list of EVENTS. Search
    is about a contact - a name, an email. Event Type and Month are about
    an event: one contact can hold a Birthday in April and an Anniversary
    in June, and asking for April cannot sensibly mean hiding the contact
    or showing the June one.

    So the two new filters narrow the EVENTS, and a contact left showing
    none of them drops out. Asking for Birthday + April gives exactly the
    people with an April birthday, showing that birthday. Search narrows
    the contacts, as it always did. That is the only reading that answers
    the question the filter is asked; if it turns out you want the whole
    contact card kept intact, it is one line in filterEvents().

NOTHING MOVES SERVER-SIDE. Every contact and every event is already in
the page - the view sends them all and always has. So this filters what
is rendered, the way the search already did, and no query, no view and no
URL changes. A page reload is not part of filtering here, which also
means the panel cannot shut under you.

BASE ALREADY OWNS MORE OF THIS THAN THE PAGE DID.
    .alv-filter, .filter-group, .filter-label, .filter-select,
    .filter-input, .filter-tags, .filter-tag, .remove-tag,
    .alv-filter-active.has-filters and the count on the Filter button are
    all base's, and base's own script ALREADY keeps the count in step by
    watching the chip row - one writer, its words. So this page's script
    builds chips and hides cards. It does not touch the count, and the
    old page-local display toggling is not reintroduced.

WHAT IS STILL PAGE-LOCAL, AND WHY IT IS NOT LIFTED HERE.
    .filter-grid, .filter-header and .filter-title are on SEVEN other
    pages, seven times over, and they have drifted - four different
    grid-template-columns, three different borders, #2c3e50 and #dee2e6
    hard-coded in all seven. Lifting them belongs to a round that
    measures all eight and converts them together, the way ALV FILTER
    FIELD v1 did. This page gets the eighth copy TODAY - painted from the
    tokens, not from the hexes - so it looks like its peers and is ready
    to delete when that round lands. It is on the running list.

Backups: .bak_celfilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_celfilter'
PAGE = 'celebration_management.html'
CRLF = {}

EVENT_TYPES = [('birthday', 'Birthday'), ('nameday', 'Nameday'),
               ('anniversary', 'Anniversary'), ('custom', 'Custom Event')]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


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
            raise SystemExit('P1: %s is not a byte copy' % bak)


def swap(text, path, was, now, what):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('P1: %s - %s is there %d time(s), not 1'
                         % (PAGE, what, text.count(a)))
    print('  %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# 1. THE PANEL
# ==========================================================================
PANEL_WAS = """<div class="alv-filter" id="celebrationFilterPanel">
    <div class="filter-group">
        <label class="filter-label" for="contactSearch">
            <i class="fas fa-search"></i> <strong>Search contacts</strong>
        </label>
        <div class="search-input-group">
            <input type="text"
                   id="contactSearch"
                   class="form-control search-input"
                   placeholder="Search contacts..."
                   onkeyup="searchContacts()">
        </div>
    </div>
</div>"""

PANEL_NOW = """<!-- THE CHIPS LIVE OUTSIDE THE PANEL. base's words: a closed
     panel must never mean invisible filtering. base also counts them and
     shows this row - this page writes chips and nothing else. -->
<div class="alv-filter-active" id="activeFilters">
    <span class="alv-filter-active-label">Active filters:</span>
    <div class="filter-tags" id="filterTags"></div>
</div>

<div class="alv-filter" id="celebrationFilterPanel">
    <div class="filter-header">
        <h5 class="filter-title">
            <i class="fas fa-filter"></i> Celebration Filters
        </h5>
        <button type="button" class="btn action-secondary btn-sm"
                id="clearAllBtn" onclick="clearCelebrationFilters()">
            <i class="fas fa-times-circle"></i> Clear All
        </button>
    </div>

    <div class="filter-content">
        <div class="filter-grid">
            <div class="filter-group">
                <label class="filter-label" for="contactSearch">
                    <i class="fas fa-search"></i> <strong>Search contacts</strong>
                </label>
                <input type="text"
                       id="contactSearch"
                       class="filter-input"
                       placeholder="Name or email..."
                       onkeyup="applyCelebrationFilters()">
            </div>

            <div class="filter-group">
                <label class="filter-label" for="eventTypeFilter">
                    <i class="fas fa-tag"></i> <strong>Event Type</strong>
                </label>
                <select id="eventTypeFilter" class="filter-select"
                        onchange="applyCelebrationFilters()">
                    <option value="">All Event Types</option>
{TYPE_OPTIONS}
                </select>
            </div>

            <div class="filter-group">
                <label class="filter-label" for="eventMonthFilter">
                    <i class="fas fa-calendar-alt"></i> <strong>Month</strong>
                </label>
                <select id="eventMonthFilter" class="filter-select"
                        onchange="applyCelebrationFilters()">
                    <option value="">All Months</option>
{MONTH_OPTIONS}
                </select>
            </div>
        </div>
    </div>
</div>

<!-- Shown only when the filters match nothing. It is a SEPARATE block
     from No Contacts Yet, because "you have no contacts" and "none of
     your contacts match this" are different facts and the second one
     needs the way out that the first does not. -->
<div class="alv-empty" id="noMatches" style="display: none;">
    <i class="fas fa-filter"></i>
    <div class="alv-empty-title">Nothing matches these filters</div>
    <div class="alv-empty-hint">
        Try a different month or event type, or
        <a href="#" onclick="clearCelebrationFilters(); return false;">clear
        all filters</a>.
    </div>
</div>"""

PANEL_NOW = PANEL_NOW.replace('{TYPE_OPTIONS}', '\n'.join(
    '                    <option value="%s">%s</option>' % (v, label)
    for v, label in EVENT_TYPES))
PANEL_NOW = PANEL_NOW.replace('{MONTH_OPTIONS}', '\n'.join(
    '                    <option value="%d">%s</option>' % (i + 1, m)
    for i, m in enumerate(MONTHS)))

# ==========================================================================
# 2. THE DATA THE FILTER READS
# ==========================================================================
ITEM_WAS = """<div class="event-item {{ event.event_type }}">"""
ITEM_NOW = ("""<div class="event-item {{ event.event_type }}"\n"""
            """                         data-event-type="{{ event.event_type }}"\n"""
            """                         data-event-month="{{ event.event_date|date:'n' }}">""")

# ==========================================================================
# 3. THE SCRIPT
# ==========================================================================
JS_WAS = """// Search functionality
function searchContacts() {
    const searchTerm = document.getElementById('contactSearch').value.toLowerCase();
    const contactCards = document.querySelectorAll('.contact-card');

    contactCards.forEach(card => {
        const name = card.querySelector('.contact-info h4').textContent.toLowerCase();
        const email = card.querySelector('.contact-details')?.textContent.toLowerCase() || '';

        if (name.includes(searchTerm) || email.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}"""

JS_NOW = """// ===== FILTERING =====
// Search narrows CONTACTS. Type and Month narrow EVENTS, and a contact
// showing none of them drops out - see the round's note for why that is
// the only reading that answers the question the filter is asked.
//
// One function does all three, because three functions each hiding things
// on their own is three ways to disagree about what is visible. Nothing
// here writes the Filter button's count: base watches the chip row and
// keeps that in step itself.
const EVENT_TYPE_LABELS = {
%(TYPE_LABELS)s
};
const MONTH_LABELS = [%(MONTH_LABELS)s];

function celebrationFilterState() {
    const el = id => document.getElementById(id);
    return {
        search: (el('contactSearch') ? el('contactSearch').value : '').trim(),
        type: el('eventTypeFilter') ? el('eventTypeFilter').value : '',
        month: el('eventMonthFilter') ? el('eventMonthFilter').value : ''
    };
}

function applyCelebrationFilters() {
    const f = celebrationFilterState();
    const term = f.search.toLowerCase();
    const filteringEvents = !!(f.type || f.month);
    let shown = 0;

    document.querySelectorAll('.contact-card').forEach(card => {
        const name = card.querySelector('.contact-info h4').textContent.toLowerCase();
        const details = card.querySelector('.contact-details');
        const email = details ? details.textContent.toLowerCase() : '';
        const matchesSearch = !term || name.includes(term) || email.includes(term);

        // Events first, so the count below is the count AFTER hiding.
        let visibleEvents = 0;
        card.querySelectorAll('.event-item').forEach(item => {
            const okType = !f.type || item.dataset.eventType === f.type;
            const okMonth = !f.month || item.dataset.eventMonth === f.month;
            const show = okType && okMonth;
            item.style.display = show ? '' : 'none';
            if (show) visibleEvents++;
        });

        // A contact with no events at all cannot match an event filter,
        // and must not be hidden when there is none.
        const keep = matchesSearch && (!filteringEvents || visibleEvents > 0);
        card.style.display = keep ? '' : 'none';
        if (keep) shown++;
    });

    const noMatches = document.getElementById('noMatches');
    if (noMatches) {
        const anyFilter = !!(term || filteringEvents);
        noMatches.style.display = (anyFilter && shown === 0) ? '' : 'none';
    }
    renderCelebrationChips(f);
}

// The chips ARE the record of what is on - base counts them to number the
// Filter button, so a filter without a chip would be a filter the button
// does not know about.
function renderCelebrationChips(f) {
    const box = document.getElementById('filterTags');
    if (!box) return;
    const chips = [];
    if (f.search) chips.push(['contactSearch', 'Search', f.search]);
    if (f.type) chips.push(['eventTypeFilter', 'Type',
                            EVENT_TYPE_LABELS[f.type] || f.type]);
    if (f.month) chips.push(['eventMonthFilter', 'Month',
                             MONTH_LABELS[parseInt(f.month, 10) - 1] || f.month]);

    box.textContent = '';
    chips.forEach(([id, label, value]) => {
        const tag = document.createElement('span');
        tag.className = 'filter-tag';
        // textContent, not innerHTML: the search chip carries whatever was
        // typed into the box.
        tag.appendChild(document.createTextNode(label + ': ' + value + ' '));
        const x = document.createElement('button');
        x.type = 'button';
        x.className = 'remove-tag';
        x.setAttribute('aria-label', 'Clear ' + label + ' filter');
        x.textContent = '\\u00d7';
        x.onclick = () => clearOneCelebrationFilter(id);
        tag.appendChild(x);
        box.appendChild(tag);
    });
}

function clearOneCelebrationFilter(id) {
    const el = document.getElementById(id);
    if (el) el.value = '';
    applyCelebrationFilters();
}

function clearCelebrationFilters() {
    ['contactSearch', 'eventTypeFilter', 'eventMonthFilter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyCelebrationFilters();
}

// The old name, kept because it is what the search box called and what a
// reader will look for. It is the same function now, not a second one.
function searchContacts() {
    applyCelebrationFilters();
}""" % {
    'TYPE_LABELS': ',\n'.join("    '%s': '%s'" % (v, label)
                              for v, label in EVENT_TYPES),
    'MONTH_LABELS': ', '.join("'%s'" % m for m in MONTHS),
}

# ==========================================================================
# 4. THE CSS - the eighth copy, painted from the tokens
# ==========================================================================
CSS_WAS = """}
</style>"""

CSS_NOW = """}

/* ===== THE FILTER PANEL'S OWN LAYOUT ===== 29 Sep 2026
   base owns .alv-filter, .filter-group, .filter-label, .filter-select,
   .filter-input, the chips and the count. What is NOT in base yet is the
   panel's grid and its header, which seven other pages each carry a copy
   of - four different column counts, three different borders, and
   #2c3e50 / #dee2e6 written out in all seven.

   This is the eighth copy, and the only one painted from the tokens. It
   is here rather than in base because lifting the component means
   measuring all eight and converting them together, which is its own
   round. This block is written to be DELETED by that round. */
.filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--alv-line);
}
.filter-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    color: var(--alv-ink);
    font-size: 18px;
    font-weight: 600;
    user-select: none;
}
.filter-title i { color: var(--alv-ink-soft); }
.filter-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 20px;
    align-items: end;
}

@media screen and (max-width: 768px) {
    /* ONE COLUMN, and the header wraps - three 44px controls side by side
       on a phone is three controls nobody can read the labels of. */
    .filter-grid {
        grid-template-columns: 1fr;
        gap: 12px;
    }
    .filter-header {
        flex-wrap: wrap;
        margin-bottom: 12px;
        padding-bottom: 10px;
    }
    .filter-title { font-size: 15px; }
    #clearAllBtn { flex: 0 0 auto; }
}
</style>"""

# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P1 - EVENT TYPE, MONTH AND THE SEARCH%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

if 'eventTypeFilter' in text and 'eventMonthFilter' in text:
    print('  %s already has all three filters' % PAGE)
else:
    text = swap(text, path, PANEL_WAS, PANEL_NOW,
                'the panel gains Event Type and Month, and the chip row')

    n = text.count(eol(path, ITEM_WAS))
    if n != 1:
        raise SystemExit('P1: the event-item opening tag is there %d '
                         'time(s), not 1' % n)
    text = swap(text, path, ITEM_WAS, ITEM_NOW,
                'each event carries its type and its month as data')

    text = swap(text, path, JS_WAS, JS_NOW,
                'searchContacts becomes applyCelebrationFilters')

    if text.count(eol(path, CSS_WAS)) != 1:
        raise SystemExit('P1: the stylesheet does not end exactly once the '
                         'way this round expects')
    text = swap(text, path, CSS_WAS, CSS_NOW,
                'the panel grid and header, from the tokens')

    # GATES. Each of these was a way to ship this broken.
    if 'style="display: none;"' not in text:
        raise SystemExit('P1: the no-matches block lost its hidden start')
    if text.count('id="contactSearch"') != 1:
        raise SystemExit('P1: contactSearch is not unique - the old search '
                         'box survived beside the new one')
    if 'search-input-group' in text:
        raise SystemExit('P1: the old search-input-group is still here')
    for need in ('data-event-type=', 'data-event-month=', 'id="filterTags"',
                 'clearCelebrationFilters', 'applyCelebrationFilters'):
        if need not in text:
            raise SystemExit('P1: %s did not land' % need)
    # LESSON 21, IN A NEW PLACE. The first version of this gate read
    # CSS_NOW whole and refused - because the COMMENT above the block
    # names the two hexes it exists to avoid. A gate that reads markup or
    # CSS strips the comments first, every time.
    bare = re.sub(r'/\*.*?\*/', '', CSS_NOW, flags=re.S)
    for hexy in ('#2c3e50', '#dee2e6'):
        if hexy in bare:
            raise SystemExit('P1: this round wrote %s in a RULE, which is '
                             'the thing it is avoiding' % hexy)
    if '#2c3e50' not in CSS_NOW:
        raise SystemExit('P1: the note explaining what the seven copies '
                         'hard-code has lost the hexes it names')
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  search narrows contacts; type and month narrow events, and a')
print('  contact left showing none of them drops out.')
print('  base counts the chips and numbers the Filter button - this page')
print('  writes chips and nothing else.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
