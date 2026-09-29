# -*- coding: utf-8 -*-
"""SECTION P, ROUND P3 - AN A TO Z, AND THREE ACROSS

Demetri, looking at the same screen: three across in Compact View, and an
A to Z selector like the one on Recipe Management.

THE A TO Z IS BUILT LIKE RECIPES' - AND DRIVEN UNLIKE IT, ON PURPOSE.
    Recipe Management's strip is a row of links. Each one reloads the page
    with ?letter=X, and the VIEW decides which letters are available, out
    of 317 recipes that are paged.

    Celebrations is not paged. Every contact is already in the page - that
    is why its search, type and month all filter what is rendered and
    nothing reloads. A letter that reloaded would be the one control on
    the screen that threw the other three away, and it would lose the
    panel with them.

    So it keeps Recipes' class names exactly - .letter-filter-container,
    -wrapper, -list, -item, and .available / .disabled / .active - and
    changes only what drives them. Two pages wearing one set of names is
    what lets a later round lift the strip into base once; two pages
    wearing two sets is how the filter panel ended up copied nine times.

WHICH LETTERS ARE GREY IS MEASURED, NOT ASSUMED. On load the script reads
the first letter of every contact on the page. A letter nobody starts
with is .disabled and cannot be clicked, exactly as on Recipes - the
difference being that here the count is taken from the page rather than
from the queryset, because here the page has all of it.

PAINTED TEAL, NOT GREEN. Recipes' copy hard-codes #28a745 six times, plus
#dee2e6, #495057 and #d0d0d0. This one uses the tokens. That is the
standing instruction - Personal takes the house teal - and it is why the
strip is NOT copied verbatim from the page it is modelled on.

THREE ACROSS, AND A STEP BETWEEN. Compact View was two columns at every
width above 768px. Three at 1200 and above; two between 769 and 1199,
where three would put a long name like Charis Chrysanthou (Alexandra) on
two lines in a 12px-padded card; one below that, as before.

Backups: .bak_celaz. Idempotent. --check writes nothing. Runs AFTER P1 -
it edits the function P1 wrote, and refuses if that function is not there.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_celaz'
PAGE = 'celebration_management.html'
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
            raise SystemExit('P3: %s is not a byte copy' % bak)


def swap(text, path, was, now, what):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('P3: %s - %s is there %d time(s), not 1'
                         % (PAGE, what, text.count(a)))
    print('  %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# 1. THE STRIP - between the panel and the list, where Recipes puts it.
# ==========================================================================
STRIP_WAS = """<!-- Contacts List -->"""

STRIP_NOW = """<!-- A TO Z. Recipes' class names exactly, so a later round can lift the
     strip into base once for both pages. What differs is underneath: this
     one filters what is already rendered instead of reloading with
     ?letter=, because every contact is on this page and a reload would
     throw the other three filters away. The letters are written by the
     script, which also decides which of them are grey. -->
<div class="letter-filter-container">
    <div class="letter-filter-wrapper">
        <div class="letter-filter-list" id="letterFilterList"></div>
    </div>
</div>

<!-- Contacts List -->"""

# ==========================================================================
# 2. THE SCRIPT - a fourth axis in the function P1 wrote
# ==========================================================================
STATE_WAS = """    return {
        search: (el('contactSearch') ? el('contactSearch').value : '').trim(),
        type: el('eventTypeFilter') ? el('eventTypeFilter').value : '',
        month: el('eventMonthFilter') ? el('eventMonthFilter').value : ''
    };"""

STATE_NOW = """    return {
        search: (el('contactSearch') ? el('contactSearch').value : '').trim(),
        type: el('eventTypeFilter') ? el('eventTypeFilter').value : '',
        month: el('eventMonthFilter') ? el('eventMonthFilter').value : '',
        letter: CEL_LETTER
    };"""

MATCH_WAS = """        const matchesSearch = !term || name.includes(term) || email.includes(term);"""

MATCH_NOW = """        const matchesSearch = !term || name.includes(term) || email.includes(term);
        // The letter is about the NAME, and about its first character -
        // so it is a contact filter, like search, and not an event one.
        const matchesLetter = !f.letter || contactLetter(card) === f.letter;"""

KEEP_WAS = """        const keep = matchesSearch && (!filteringEvents || visibleEvents > 0);"""

KEEP_NOW = """        const keep = matchesSearch && matchesLetter
                     && (!filteringEvents || visibleEvents > 0);"""

ANY_WAS = """        const anyFilter = !!(term || filteringEvents);"""

ANY_NOW = """        const anyFilter = !!(term || filteringEvents || f.letter);"""

CHIPS_WAS = """    if (f.month) chips.push(['eventMonthFilter', 'Month',
                             MONTH_LABELS[parseInt(f.month, 10) - 1] || f.month]);"""

CHIPS_NOW = """    if (f.month) chips.push(['eventMonthFilter', 'Month',
                             MONTH_LABELS[parseInt(f.month, 10) - 1] || f.month]);
    // The letter has no field to blank, so its chip carries the id of the
    // strip and clearOneCelebrationFilter knows that one name.
    if (f.letter) chips.push(['letterFilterList', 'Letter', f.letter]);"""

CLEARONE_WAS = """function clearOneCelebrationFilter(id) {
    const el = document.getElementById(id);
    if (el) el.value = '';
    applyCelebrationFilters();
}"""

CLEARONE_NOW = """function clearOneCelebrationFilter(id) {
    if (id === 'letterFilterList') {
        setCelebrationLetter('');
        return;
    }
    const el = document.getElementById(id);
    if (el) el.value = '';
    applyCelebrationFilters();
}"""

CLEARALL_WAS = """function clearCelebrationFilters() {
    ['contactSearch', 'eventTypeFilter', 'eventMonthFilter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyCelebrationFilters();
}"""

CLEARALL_NOW = """function clearCelebrationFilters() {
    ['contactSearch', 'eventTypeFilter', 'eventMonthFilter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    setCelebrationLetter('');
}"""

AZ_JS = """

// ===== A TO Z =====
// The chosen letter is a variable and not a field, because the control is
// a row of buttons. One writer, same as the rest: setCelebrationLetter is
// the only thing that assigns it.
let CEL_LETTER = '';
const CEL_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

function contactLetter(card) {
    const h = card.querySelector('.contact-info h4');
    // textContent, not the markup: the heading carries an icon and a
    // relationship badge, and neither of those is the contact's name.
    const name = h ? h.textContent.trim() : '';
    return name ? name.charAt(0).toUpperCase() : '';
}

function setCelebrationLetter(letter) {
    CEL_LETTER = (CEL_LETTER === letter) ? '' : letter;   // click again to clear
    document.querySelectorAll('.letter-filter-item').forEach(el => {
        el.classList.toggle('active', !!CEL_LETTER
                            && el.dataset.letter === CEL_LETTER);
    });
    applyCelebrationFilters();
}

// WHICH LETTERS ARE GREY IS MEASURED OFF THE PAGE. Recipes asks the view,
// because its list is paged; here every contact is already rendered, so
// the page itself is the count.
function buildCelebrationAlphabet() {
    const list = document.getElementById('letterFilterList');
    if (!list) return;
    const have = new Set();
    document.querySelectorAll('.contact-card').forEach(card => {
        const l = contactLetter(card);
        if (l) have.add(l);
    });
    list.textContent = '';
    CEL_ALPHABET.forEach(letter => {
        const on = have.has(letter);
        const el = document.createElement('button');
        el.type = 'button';
        el.className = 'letter-filter-item ' + (on ? 'available' : 'disabled');
        el.dataset.letter = letter;
        el.textContent = letter;
        if (on) {
            el.onclick = () => setCelebrationLetter(letter);
        } else {
            el.disabled = true;
            el.setAttribute('aria-label', 'No contacts starting with '
                            + letter);
        }
        list.appendChild(el);
    });
}

document.addEventListener('DOMContentLoaded', buildCelebrationAlphabet);"""

# ==========================================================================
# 3. THE CSS - Recipes' shape, the house's colours
# ==========================================================================
COMPACT_WAS = """.contacts-container.compact-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}"""

COMPACT_NOW = """.contacts-container.compact-grid {
    display: grid;
    /* THREE ACROSS, asked for 29 Sep. There is a step between three and
       one: at 1199 and below a third column puts a name like Charis
       Chrysanthou (Alexandra) onto two lines inside a 12px-padded card,
       so that width keeps the two it had. Below 768 it is one, as
       before. */
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

@media screen and (max-width: 1199px) {
    .contacts-container.compact-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}"""

AZ_CSS_WAS = """/* ===== THE FILTER PANEL'S OWN LAYOUT ====="""

AZ_CSS_NOW = """/* ===== A TO Z ===== 29 Sep 2026
   Recipe Management's strip, class for class, so that one later round can
   lift it into base for both pages. Its copy hard-codes #28a745 six
   times, and #dee2e6, #495057 and #d0d0d0 besides; this one is painted
   from the tokens, because Personal takes the house teal.

   28px on the desk and 34 on a phone. The letters are a row of 26, so
   they cannot all be 44 - the compromise is the one Recipes made, plus a
   little: the phone size goes UP rather than down, and the row scrolls
   rather than wrapping, so a thumb has a bigger target than a mouse. */
.letter-filter-container {
    background: var(--alv-paper);
    border: 2px solid var(--alv-line);
    border-radius: var(--alv-radius);
    padding: 10px 12px;
    margin-bottom: 20px;
}
.letter-filter-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
}
.letter-filter-wrapper::-webkit-scrollbar { height: 6px; }
.letter-filter-wrapper::-webkit-scrollbar-track {
    background: var(--alv-surface); border-radius: 3px;
}
.letter-filter-wrapper::-webkit-scrollbar-thumb {
    background: var(--alv-accent); border-radius: 3px;
}
.letter-filter-list {
    display: flex;
    gap: 4px;
    min-width: min-content;
    padding: 2px 0;
    justify-content: center;
}
.letter-filter-item {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    /* THE BOX IS TEAL ON EVERY LETTER - Demetri, 29 Sep. Recipes greys
       the border of a letter nobody is named with; here the box keeps the
       accent and it is the PALE accent that says unavailable, so the row
       reads as one control rather than two. */
    border: 1.5px solid var(--alv-accent);
    border-radius: 4px;
    background: var(--alv-paper);
    color: var(--alv-accent);
    font-family: var(--alv-font-ui);
    font-weight: 600;
    font-size: 12px;
    cursor: pointer;
    transition: background .15s ease, color .15s ease, border-color .15s ease;
}
.letter-filter-item.available {
    color: var(--alv-accent);
    border-color: var(--alv-accent);
}
.letter-filter-item.available:hover {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}
.letter-filter-item.disabled {
    /* Still a teal box, in the soft tone, so unavailable reads as quiet
       rather than as a different component. */
    color: var(--alv-ink-faint);
    border-color: var(--alv-accent-soft);
    background: var(--alv-surface);
    cursor: not-allowed;
}
.letter-filter-item.active {
    background: var(--alv-accent);
    border-color: var(--alv-accent);
    color: var(--alv-on-accent);
}
.letter-filter-item:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: 2px;
}

@media screen and (max-width: 768px) {
    /* BIGGER on a phone, not smaller, and the row scrolls. */
    .letter-filter-container { padding: 8px 10px; }
    .letter-filter-list { justify-content: flex-start; gap: 4px; }
    .letter-filter-item { width: 34px; height: 34px; font-size: 13px; }
}

/* ===== THE FILTER PANEL'S OWN LAYOUT ====="""

# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P3 - AN A TO Z, AND THREE ACROSS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

if 'letterFilterList' in text:
    print('  %s already has the A to Z' % PAGE)
else:
    # P1 FIRST. This round edits the function P1 wrote.
    for need in ('function applyCelebrationFilters', 'renderCelebrationChips',
                 'celebrationFilterState'):
        if need not in text:
            raise SystemExit('P3: %s is not on the page - P1 has not run, '
                             'and this round edits what P1 wrote' % need)

    text = swap(text, path, STRIP_WAS, STRIP_NOW,
                'the A to Z strip, above the list')
    text = swap(text, path, STATE_WAS, STATE_NOW,
                'the chosen letter joins the filter state')
    text = swap(text, path, MATCH_WAS, MATCH_NOW,
                'a contact matches by its first letter')
    text = swap(text, path, KEEP_WAS, KEEP_NOW,
                '  and the letter is an AND with the rest')
    text = swap(text, path, ANY_WAS, ANY_NOW,
                '  and counts as a filter for the empty block')
    text = swap(text, path, CHIPS_WAS, CHIPS_NOW, 'the letter gets a chip')
    text = swap(text, path, CLEARONE_WAS, CLEARONE_NOW,
                '  which its x can clear')
    text = swap(text, path, CLEARALL_WAS, CLEARALL_NOW,
                '  and Clear All clears it too')

    end = text.index('function searchContacts() {')
    end = text.index('\n}', end) + 2
    text = text[:end] + eol(path, AZ_JS) + text[end:]
    print('  the strip is built, measured and wired')

    text = swap(text, path, COMPACT_WAS, COMPACT_NOW,
                'Compact View goes three across, two at 1199 and below')
    text = swap(text, path, AZ_CSS_WAS, AZ_CSS_NOW,
                'the strip, painted from the tokens')

    # GATES.
    az = text[text.index('/* ===== A TO Z ====='):
              text.index("/* ===== THE FILTER PANEL'S OWN LAYOUT")]
    bare = re.sub(r'/\*.*?\*/', '', az, flags=re.S)
    hexes = re.findall(r'#[0-9a-fA-F]{3,6}', bare)
    if hexes:
        raise SystemExit('P3: the strip was written with %s in a rule, and '
                         'the whole point was the tokens' % hexes)
    if '#28a745' not in az:
        raise SystemExit('P3: the note explaining what Recipes hard-codes '
                         'has lost the hex it names')
    # AN = THAT IS NOT AN ASSIGNMENT. The first version counted the
    # string 'CEL_LETTER =' and found three, because `CEL_LETTER ===`
    # starts with it. A comparison is not a writer.
    writes = len(re.findall(r'CEL_LETTER\s*=(?!=)', text))
    if writes != 2:
        raise SystemExit('P3: CEL_LETTER is assigned %d times - it is meant '
                         'to have ONE writer: its declaration, and '
                         'setCelebrationLetter' % writes)
    for need in ('letter-filter-item', 'buildCelebrationAlphabet',
                 'setCelebrationLetter', 'contactLetter',
                 'repeat(3, 1fr)'):
        if need not in text:
            raise SystemExit('P3: %s did not land' % need)
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  the letter narrows contacts, like search; the strip greys what')
print('  nobody is named; clicking the same letter again clears it.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
