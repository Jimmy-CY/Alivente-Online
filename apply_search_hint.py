# -*- coding: utf-8 -*-
"""SECTION N, ROUND N3 - THE REST OF THE SEARCH BOXES

Demetri listed six searches that do not narrow as you type: Issues,
Properties, Projects, Actual Expenses, Tenant Lease Agreements and
Recipes. Suppliers does (N2) and Celebrations does (its own onkeyup
filter, no server search at all).

FOUR OF THE SIX CAN HAVE IT. Two cannot, and the reason is not
pagination - it is that THE SERVER SEARCHES A FIELD THAT IS NOT ON THE
PAGE:

    projects     project_name OR project_description
                 -> there is no Description column, and it pages at 25
    recipes      recipe_name, or, in ingredient mode,
                 recipe_ingredients__ingredient__name
                 -> no table at all, ingredients are never rendered,
                    and it pages at 48

A live filter there would narrow what is on screen while the glass
narrows something else, so the same box would give two different
answers. Demetri, 1 Oct: "for Projects and Recipes, we need to have a
small text near the search field notifying a user that they need to type
the search and then press the search button." That is this round's answer
for those two, and it is a better one than the debounced round-trip that
was queued.

WHAT THIS ROUND DOES, in three parts.

 1. base gets .alv-search-hint - one quiet line under a search box that
    does not narrow as you type. It sits beside .search-input-group,
    .search-input, .search-btn and .filter-group, all of which base
    already owns.

 2. THE CONTROLLER GOES TO v2: data-live-search-cell becomes a
    COMMA-SEPARATED LIST, and a row matches if ANY named column matches.
    This is not a convenience. Two of the four eligible pages search two
    model fields with Q(a) | Q(b), and a one-column live filter would
    disagree with the glass on exactly the rows that matched the other
    field. v1's single name still works unchanged - suppliers is not
    touched.

 3. FOUR PAGES OPT IN, each naming the column or columns its own view
    filters on. Verified against the views, not guessed:

      properties.html            prop_name                -> Property
      act_expense.html           act_expense_description  -> Description
      fsr.html                   issues_heading           -> Issue
                                 issues_description       -> Description
      tenant_lease_agreement     tenant_name              -> Tenant
                                 prop__prop_name          -> Property

    None of those four paginates - checked, all four views - so the
    browser holds every row and narrowing the screen answers the same
    question the server would.

    act_expense carries FOUR tables (the list, a report, a drill-down
    and an an-table), so its selector names .expense-table rather than
    .alv-table. fsr's list has an id, #issuesTable, and that is used.

Backups: .bak_searchhint. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_searchhint'
CRLF = {}
SENTINEL = 'test_search_hint.py'

# rel -> (table selector, comma-separated data-labels)
OPT_IN = {
    'properties.html': ('.properties-table', 'Property'),
    'act_expense.html': ('.expense-table', 'Description'),
    'fsr.html': ('#issuesTable', 'Issue,Description'),
    'tenant_lease_agreement.html': ('.lease-agreements-table',
                                    'Tenant,Property'),
}
HINTED = ('projects/projects.html', 'recipe_management.html')

HINT = ('<small class="alv-search-hint">Type your search, then press the '
        'magnifying glass.</small>')


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
            raise SystemExit('N3: %s is not a byte copy' % bak)


def close_of(text, start):
    """The index just past the </div> that closes the <div> at `start`.

    The seven search boxes are indented seven different ways, so an
    anchor written as a literal '</button>\\n            </div>' matches
    one page and misses six. Counting the tags does not care."""
    i = text.find('>', start) + 1
    depth = 1
    for m in re.finditer(r'<div\b|</div\s*>', text[i:]):
        depth += 1 if m.group(0).startswith('<div') else -1
        if depth == 0:
            return i + m.end()
    raise SystemExit('N3: the search-input-group at %d is never closed'
                     % start)


# ==========================================================================
print('=' * 74)
print('SECTION N, ROUND N3 - THE REST OF THE SEARCH BOXES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

EDITED = {}

# ==========================================================================
# 1 + 2. base: the hint's style, and the controller at v2
# ==========================================================================
bp = alv_tree.path_of('base.html')
bt, braw = read(bp)
if SENTINEL in bt:
    print('  base already done')
else:
    # ---- the style, placed beside the search box rules it belongs with
    # base declares .search-input-group TWICE - once at top level and
    # once inside the phone block, where it only sets a width. The style
    # belongs beside the top-level one, so the anchor is depth 0 rather
    # than "the only one", which it is not.
    hits = [m.start() for m in re.finditer(
        r'(?m)^[ \t]*\.search-input-group\s*\{', bt)
        if bt.count('{', 0, m.start()) == bt.count('}', 0, m.start())]
    if len(hits) != 1:
        raise SystemExit('N3: base declares .search-input-group at top '
                         'level %d times, not once' % len(hits))
    CSS = """/* A search box that does NOT narrow as you type says so, once,
   quietly, under the box. Two lists cannot have the live filter -
   projects and recipes both search a field that is not rendered on the
   page (a project's description, a recipe's ingredients), so narrowing
   the screen would answer a different question from the glass. Demetri
   asked for the line on 1 Oct 2026.       [test_search_hint.py] */
.alv-search-hint {
    display: block;
    margin-top: 6px;
    font-size: 12.5px;
    line-height: 1.35;
    color: var(--alv-ink-soft);
}

"""
    bt = bt[:hits[0]] + eol(bp, CSS) + bt[hits[0]:]

    # ---- the controller: one name becomes a list of names
    OLD_HEAD = """/* ===== alv-live-search v1 ===== 30 Sep 2026 ========================="""
    if bt.count(OLD_HEAD) != 1:
        raise SystemExit('N3: the v1 controller header is not where it was')
    bt = bt.replace(OLD_HEAD, """/* ===== alv-live-search v2 ===== 1 Oct 2026 ==========================""")

    OLD_DOC = """     data-live-search-cell="<the data-label of the column to match>"

   IT MATCHES ONE COLUMN, ON PURPOSE. Every one of these boxes also
   posts to a server filter that matches ONE model field, and the two
   have to agree - a live filter that matched the whole row would give
   a different answer from the same box pressed with Enter, which is
   worse than having no live filter at all. The cell is named rather
   than guessed, so a page cannot opt in without deciding."""
    NEW_DOC = """     data-live-search-cell="<data-label>[,<data-label>...]"

   IT MATCHES THE COLUMNS THE SERVER MATCHES, AND NO OTHERS. v1 took one
   name because suppliers filters on one model field. Two of the four
   pages added on 1 Oct filter on two - fsr does Q(issues_heading) |
   Q(issues_description), tenant_lease_agreement does Q(tenant_name) |
   Q(prop__prop_name) - so the attribute is a LIST now and a row matches
   if ANY named column matches, which is the same OR the server does.

   What it must never become is "match the whole row". The box also
   posts to the server, and the two have to agree: a live filter that
   matched a column the server ignores would give a different answer
   from the same box pressed with Enter, which is worse than having no
   live filter at all. The columns are named rather than guessed, so a
   page cannot opt in without deciding."""
    if bt.count(OLD_DOC) != 1:
        raise SystemExit('N3: the v1 doc block is not where it was')
    bt = bt.replace(OLD_DOC, NEW_DOC)

    OLD_JS = """        var label = box.getAttribute('data-live-search-cell');
        if (!table || !label) { return; }"""
    NEW_JS = """        var labels = (box.getAttribute('data-live-search-cell') || '')
            .split(',');
        var i;
        for (i = labels.length - 1; i >= 0; i -= 1) {
            labels[i] = labels[i].trim();
            if (!labels[i]) { labels.splice(i, 1); }
        }
        if (!table || !labels.length) { return; }"""
    if bt.count(OLD_JS) != 1:
        raise SystemExit('N3: the v1 label read is not where it was')
    bt = bt.replace(OLD_JS, eol(bp, NEW_JS))

    OLD_ROW = """                var td = row.querySelector('[data-label="' + label + '"]');
                /* A row with no such cell is not a data row - an empty
                   state, a totals line - and is left alone. */
                if (!td) { return; }
                var hit = !q || norm(td.textContent).indexOf(q) >= 0;"""
    NEW_ROW = """                var cells = [], k, td;
                for (k = 0; k < labels.length; k += 1) {
                    td = row.querySelector(
                        '[data-label="' + labels[k] + '"]');
                    if (td) { cells.push(td); }
                }
                /* A row with none of those cells is not a data row - an
                   empty state, a totals line - and is left alone. */
                if (!cells.length) { return; }
                var hit = !q;
                for (k = 0; !hit && k < cells.length; k += 1) {
                    hit = norm(cells[k].textContent).indexOf(q) >= 0;
                }"""
    if bt.count(OLD_ROW) != 1:
        raise SystemExit('N3: the v1 row test is not where it was')
    bt = bt.replace(OLD_ROW, eol(bp, NEW_ROW))

    bt = bt.replace('[test_live_search.py] */',
                    '[test_live_search.py, test_search_hint.py] */', 1)
    if SENTINEL not in bt:
        raise SystemExit('N3: base did not pick up the sentinel')
    EDITED[alv_tree.rel(bp)] = bt
    if not CHECK:
        back_up(bp, braw)
        write(bp, bt)
    print('  base.html                      .alv-search-hint, controller v2')

# ==========================================================================
# 3. the two pages that get the hint
# ==========================================================================
for rel in HINTED:
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p):
        raise SystemExit('N3: %s is not where alv_tree says' % rel)
    t, raw = read(p)
    if SENTINEL in t or 'alv-search-hint' in t:
        print('  %-30s already done' % rel)
        continue
    hits = [m.start() for m in re.finditer(
        r'<div class="search-input-group">', t)]
    if len(hits) != 1:
        raise SystemExit('N3: %s has %d search-input-group(s), not 1'
                         % (rel, len(hits)))
    end = close_of(t, hits[0])
    # keep the indentation of the line the group's close sits on
    line = t.rfind('\n', 0, end) + 1
    pad = re.match(r'[ \t]*', t[line:]).group(0)
    note = ('\n%s{# This list is searched on the SERVER. It cannot narrow '
            'as you type: #}\n'
            '%s{# the view filters on a field that is not on the page, so '
            'a live #}\n'
            '%s{# filter would answer a different question from the '
            'glass. #}\n'
            '%s{#                                   '
            '[test_search_hint.py] #}\n'
            '%s%s' % (pad, pad, pad, pad, pad, HINT))
    t = t[:end] + eol(p, note) + t[end:]
    EDITED[alv_tree.rel(p)] = t
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    print('  %-30s hint added' % rel)

# ==========================================================================
# 4. the four pages that opt in
# ==========================================================================
for rel, (sel, cells) in OPT_IN.items():
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p):
        raise SystemExit('N3: %s is not where alv_tree says' % rel)
    t, raw = read(p)
    if 'data-live-search' in t:
        print('  %-30s already done' % rel)
        continue
    hits = [m for m in re.finditer(
        r'<input[^>]*id="searchInput"[^>]*>', t, re.S)]
    if len(hits) != 1:
        raise SystemExit('N3: %s has %d #searchInput, not 1'
                         % (rel, len(hits)))
    tag = hits[0].group(0)
    at = tag.find('placeholder=')
    if at < 0:
        raise SystemExit('N3: %s - #searchInput has no placeholder to '
                         'insert before' % rel)
    # the indentation of the attribute we insert before
    nl = tag.rfind('\n', 0, at)
    pad = re.match(r'[ \t]*', tag[nl + 1:]).group(0) if nl >= 0 else ' '
    join = ('\n' + pad) if nl >= 0 else ' '
    ins = ('data-live-search="%s"%s'
           'data-live-search-cell="%s"%s' % (sel, join, cells, join))
    new = tag[:at] + eol(p, ins) + tag[at:]
    t = t[:hits[0].start()] + new + t[hits[0].end():]

    # THE SELECTOR MUST FIND EXACTLY ONE TABLE on this page, or the
    # filter narrows a table nobody is looking at.
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
    if sel.startswith('#'):
        n = len(re.findall(r'<table[^>]*id="%s"' % sel[1:], body))
    else:
        n = len([m for m in re.finditer(r'<table[^>]*class="([^"]*)"', body)
                 if sel[1:] in m.group(1).split()])
    if n != 1:
        raise SystemExit('N3: %s - the selector %s finds %d tables, not 1'
                         % (rel, sel, n))
    # AND EVERY NAMED COLUMN MUST EXIST, or the filter silently matches
    # nothing and hides every row.
    for want in cells.split(','):
        if 'data-label="%s"' % want not in body:
            raise SystemExit('N3: %s has no column labelled %r'
                             % (rel, want))
    EDITED[alv_tree.rel(p)] = t
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    print('  %-30s %-22s %s' % (rel, sel, cells))

# ==========================================================================
# GATES
# ==========================================================================
print('-' * 74)
# Not one opted-in page may paginate. A paginated list has rows the
# browser has never seen, so narrowing the screen answers a smaller
# question than the glass does.
VIEWS = {'properties.html': 'properties.py', 'act_expense.html': 'expenses.py',
         'fsr.html': 'issues.py', 'tenant_lease_agreement.html': 'tenants.py'}
for rel, v in VIEWS.items():
    vp = os.path.join(os.getcwd(), 'pages', 'views', v)
    if not os.path.isfile(vp):
        raise SystemExit('N3: %s is not on disk, so pagination is unproved'
                         % v)
    if 'Paginator(' in read(vp)[0]:
        raise SystemExit('N3: %s paginates - %s must not opt in' % (v, rel))
print('  none of the four opted-in views paginates')

# The two hinted pages must NOT have opted in by accident.
for rel in HINTED:
    p = alv_tree.join(rel.replace('/', os.sep))
    src = EDITED.get(alv_tree.rel(p)) or read(p)[0]
    if 'data-live-search' in src:
        raise SystemExit('N3: %s has both the hint and a live filter' % rel)
print('  and neither hinted page carries a live filter')

# suppliers, which came in at v1 with ONE name, must still work.
sp = alv_tree.path_of('suppliers.html')
ss = EDITED.get(alv_tree.rel(sp)) or read(sp)[0]
m = re.search(r'data-live-search-cell="([^"]*)"', ss)
if not m or ',' in m.group(1):
    raise SystemExit('N3: suppliers should still carry one name, not %r'
                     % (m.group(1) if m else None))
print('  and suppliers still carries v1\'s single name, untouched')

print('-' * 74)
print('  Four more lists narrow as you type. The two that cannot say so,')
print('  once, under the box.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
