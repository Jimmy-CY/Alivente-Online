# -*- coding: utf-8 -*-
"""SECTION N, ROUND N2 - THE SEARCH BOX NARROWS AS YOU TYPE

Demetri: "Can the Search Contact field not search as the user starts
typing, so that they don't need to press the magnifying glass? How would
this work? How do the other searches work?"

HOW THEY WORK TODAY. All of them go to the SERVER. You type, you press
Enter or the glass, the page reloads, and the rows come back filtered.
That round trip is the only reason the glass exists.

    properties           server, on Enter or the glass
    suppliers            server, on Enter or the glass
    fsr                  server
    projects             server - AND IT PAGINATES, 25 to a page
    ingredient_base_units   server
    unit_conversions     server
    tenant_lease_agreement  server (T4, this morning)

WHY IT CAN BE INSTANT HERE. Of the seven, only projects paginates. Every
other one of them renders EVERY row into the page, so the whole table is
already in the browser - narrowing it is a loop over rows that are
already there, with no server and no reload. That is why the answer is
different for projects and why projects is not in this round.

    .alv-live-search - an input that narrows the table as you type.

IT MATCHES THE SAME COLUMN THE SERVER MATCHES. This is the part worth
being careful about. The Suppliers view filters on
supplier_contact_person__icontains, and the table's first cell is
data-label="Contact Person" - so the live filter reads THAT CELL and
nothing else. Matching the whole row would have been easier and would
have meant typing and pressing Enter gave two different answers, which
is worse than not having the feature.

THE GLASS STAYS, AND STILL DOES SOMETHING. Typing narrows what is on
screen, instantly and without a reload. Pressing Enter asks the server,
reloads, and leaves you a filter CHIP that survives the trip - which is
the persistent version of the same question. Neither replaces the other.

SUPPLIERS ONLY, FOR NOW. Demetri asked about the Search Contact field.
The other five eligible pages are named in the suite rather than swept
in on a guess - each one needs its own answer about WHICH column the
server matches, and that answer is the whole correctness of the round.

Backups: .bak_livesearch. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_livesearch'
CRLF = {}

BASE = 'base.html'
PAGE = 'suppliers.html'


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
            raise SystemExit('N2: %s is not a byte copy' % bak)


# ==========================================================================
B_WAS = """})();
</script>

{% block extra_scripts %}{% endblock %}"""
B_NOW = """})();
</script>

  <script>
/* ===== alv-live-search v1 ===== 30 Sep 2026 =========================
   A search box that narrows a table as you type, with no server and no
   reload. Demetri asked for it on the Suppliers contact field.

   OPT IN with two attributes on the input:

     data-live-search="<css selector for the table>"
     data-live-search-cell="<the data-label of the column to match>"

   IT MATCHES ONE COLUMN, ON PURPOSE. Every one of these boxes also
   posts to a server filter that matches ONE model field, and the two
   have to agree - a live filter that matched the whole row would give
   a different answer from the same box pressed with Enter, which is
   worse than having no live filter at all. The cell is named rather
   than guessed, so a page cannot opt in without deciding.

   ONLY FOR A TABLE THAT HOLDS EVERY ROW. A paginated list has rows the
   browser has never seen, so narrowing what is on screen would quietly
   answer a different question. projects paginates at 25 and is not
   opted in.

   THE GLASS STILL WORKS. Typing narrows the screen; Enter asks the
   server and leaves a chip behind. Neither replaces the other.

   WITH THIS SCRIPT BLOCKED nothing is hidden and the box behaves
   exactly as it did before - the server search is untouched.
                                             [test_live_search.py] */
(function () {
    "use strict";
    function norm(s) { return (s || '').toLowerCase().trim(); }

    function wire(box) {
        var table = document.querySelector(
            box.getAttribute('data-live-search'));
        var label = box.getAttribute('data-live-search-cell');
        if (!table || !label) { return; }
        var body = table.tBodies[0];
        if (!body) { return; }
        var note = document.createElement('tr');
        note.className = 'alv-live-search-empty';
        note.style.display = 'none';
        var cell = document.createElement('td');
        cell.colSpan = 99;
        cell.className = 'alv-empty-title';
        note.appendChild(cell);
        body.appendChild(note);

        function run() {
            var q = norm(box.value);
            var rows = body.querySelectorAll(
                'tr:not(.alv-live-search-empty)');
            var shown = 0;
            Array.prototype.forEach.call(rows, function (row) {
                var td = row.querySelector('[data-label="' + label + '"]');
                /* A row with no such cell is not a data row - an empty
                   state, a totals line - and is left alone. */
                if (!td) { return; }
                var hit = !q || norm(td.textContent).indexOf(q) >= 0;
                row.style.display = hit ? '' : 'none';
                if (hit) { shown += 1; }
            });
            if (q && shown === 0) {
                cell.textContent = 'Nothing here matches ' + box.value;
                note.style.display = '';
            } else {
                note.style.display = 'none';
            }
            box.setAttribute('aria-describedby', 'alvLiveCount');
        }

        box.addEventListener('input', run);
        /* Enter still goes to the server, so it must NOT be swallowed
           here - the page's own handler submits the form. */
        run();
    }

    function init() {
        Array.prototype.forEach.call(
            document.querySelectorAll('[data-live-search]'), wire);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>

{% block extra_scripts %}{% endblock %}"""

# THE INPUT IS WRITTEN ONE ATTRIBUTE TO A LINE. The first version of
# this anchor assumed class and placeholder sat together on one line,
# which is how a dump prints them and not how the file holds them.
P_WAS = """                     class="form-control search-input"
                     placeholder="Search by contact person name..."
"""
P_NOW = """                     class="form-control search-input"
                     data-live-search=".suppliers-table"
                     data-live-search-cell="Contact Person"
                     placeholder="Search by contact person name..."
"""

# The other five that COULD have it, and are not in this round.
CANDIDATES = ('properties.html', 'fsr.html',
              'ingredient_base_units_management.html',
              'unit_conversions_management.html',
              'tenant_lease_agreement.html')

# ==========================================================================
print('=' * 74)
print('SECTION N, ROUND N2 - THE SEARCH BOX NARROWS AS YOU TYPE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'alv-live-search v1' in t:
    print('     already carries the controller')
else:
    a = eol(p, B_WAS)
    if t.count(a) != 1:
        raise SystemExit('N2: base - the script anchor is there %d time(s), '
                         'not 1' % t.count(a))
    t = t.replace(a, eol(p, B_NOW), 1)
    print('     alv-live-search v1 - one column, named by the page')

    # THIS ROUND'S BLOCK ONLY, AND NOT COMMENT-STRIPPED ACROSS THE
    # WHOLE FILE. Running /\*.*?\*/ over every script block joined
    # together let a stray comment opener in an earlier block swallow
    # code in this one - the gate then reported that its own JS was
    # missing. Slice this block out by its sentinel first.
    _i = t.find('/* ===== alv-live-search v1 =====')
    _j = t.find('</script>', _i)
    if _i < 0 or _j < 0:
        raise SystemExit('N2: the controller block could not be located')
    js = t[_i:_j]
    for must in ('data-live-search', 'data-live-search-cell',
                 "addEventListener('input'", 'DOMContentLoaded'):
        if must not in js:
            raise SystemExit('N2: the controller does not use %s' % must)
    # IT MUST NOT SWALLOW ENTER. The server search is what gives you a
    # chip that survives a reload, and it has to keep working.
    seg = re.sub(r'/\*.*?\*/', ' ',
                 js[js.find('function wire'):js.find('function init')],
                 flags=re.S)
    if 'preventDefault' in seg or 'keydown' in seg or 'keypress' in seg:
        raise SystemExit('N2: the live filter touches the keyboard handler - '
                         'Enter must still reach the server')
    # AND IT MUST READ ONE NAMED CELL, not the whole row.
    if "querySelector('[data-label=\"' + label + '\"]')" not in seg:
        raise SystemExit('N2: the filter does not read the named cell')
    if 'row.textContent' in seg:
        raise SystemExit('N2: the filter reads the whole row, which would '
                         'disagree with the server')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the page -----------------------------------------------------------
q = alv_tree.path_of(PAGE)
t2, raw2 = read(q)
print('  %s' % PAGE)
if 'data-live-search' in t2:
    print('     the box already narrows as you type')
else:
    a2 = eol(q, P_WAS)
    if t2.count(a2) != 1:
        raise SystemExit('N2: %s - the search input is there %d time(s), '
                         'not 1' % (PAGE, t2.count(a2)))
    t2 = t2.replace(a2, eol(q, P_NOW), 1)
    print('     the Contact Person box narrows the table as you type')

    mk = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', t2, flags=re.S), flags=re.S)
    m = re.search(r'data-live-search="([^"]+)"', mk)
    if not m:
        raise SystemExit('N2: the attribute did not land')
    sel = m.group(1)
    if not re.search(r'<table[^>]*class="[^"]*%s' % re.escape(sel.lstrip('.')),
                     mk):
        raise SystemExit('N2: %s names a table that is not on the page' % sel)
    cell = re.search(r'data-live-search-cell="([^"]+)"', mk).group(1)
    if ('data-label="%s"' % cell) not in mk:
        raise SystemExit('N2: the named cell %r is not in the table' % cell)
    # THE COLUMN AND THE SERVER MUST AGREE. This is the correctness of
    # the whole round: the view filters supplier_contact_person, and
    # the cell the live filter reads has to be that column.
    view = os.path.join('pages', 'views', 'suppliers.py')
    if os.path.isfile(view):
        vt = read(view)[0]
        if 'supplier_contact_person__icontains' not in vt:
            raise SystemExit('N2: the view no longer filters on '
                             'supplier_contact_person - the live column '
                             'would disagree with it')
        row = re.search(r'<td data-label="%s"[^>]*>\{\{\s*([\w.]+)' % cell, mk)
        if not row or 'supplier_contact_person' not in row.group(1):
            raise SystemExit('N2: the %r cell prints %r, not the field the '
                             'server searches'
                             % (cell, row.group(1) if row else '?'))
    if not CHECK:
        back_up(q, raw2)
        write(q, t2)

# ---- who is NOT in this round, and why ----------------------------------
print('  eligible and deliberately not opted in')
for rel in CANDIDATES:
    w = alv_tree.path_of(rel)
    if not os.path.isfile(w):
        raise SystemExit('N2: %s is not where alv_tree says' % rel)
    if 'data-live-search' in read(w)[0]:
        raise SystemExit('N2: %s opted in and was not asked to' % rel)
    print('     %-40s eligible, not opted in' % rel)
pj = alv_tree.join(os.path.join('projects', 'projects.html'))
if 'data-live-search' in read(pj)[0]:
    raise SystemExit('N2: projects opted in, and it PAGINATES - the browser '
                     'does not hold every row')
print('     %-40s PAGINATES - must not opt in'
      % 'projects/projects.html')

print('-' * 74)
print('  the Contact Person box narrows the list on every keystroke, and')
print('  the glass still asks the server and still leaves you a chip.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
