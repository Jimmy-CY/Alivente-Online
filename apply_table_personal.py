# -*- coding: utf-8 -*-
"""SECTION H, ROUND H4 - THE PERSONAL TABLES JOIN THE HOUSE

Six tables in six files onto `.alv-table`. Re-measured 27 Sep; the note in
claude/RESUME_HERE.md said seven tables and about a hundred rules, and both
numbers were stale.

WHAT WAS COUNTED
    Personal, resolved from urls.py -> view -> render(): 26 templates.
    12 <table> elements in 9 of them. ZERO wear .alv-table, against 32 of 98
    on the property side. 152 page-local rules whose selector names a table.

WHY THESE SIX AND NOT ALL TWELVE
    The twelve are three different jobs, and only one of them is this round.

    SIX are rendered by a Django {% for %} and nothing else. Markup only.
        categories_management, household_member_management,
        ingredient_base_units_management, measurement_units_management,
        passport_management, unit_conversions_management.

    THREE build their rows in JavaScript, so data-label has to be written
    into the row-building code as well as the template - and view_recipe
    additionally keeps a SECOND, separately JS-built mobile card list
    (#breakdownCardsWrap) with the desktop table hidden under 768px, which
    this component would replace wholesale. Different work, own round:
        preview_imported_recipe x2, view_recipe (breakdown-table).

    THREE ARE NOT DATA TABLES AND MUST NOT GET THIS COMPONENT:
        celebration_calendar .calendar-table - a CALENDAR GRID, headed
            Sunday..Saturday. .alv-table's phone rules turn a table into one
            card per ROW, which would deal a calendar out into seven strips.
        view_recipe, the Cooking Schedule panel inside a modal - two
            columns, label and value, NO <th> at all. A layout table.
        view_recipe, #cookingSchedulePrintArea - print-only, set at 14pt.
    Named here because an exception nobody wrote down is a gap, not a scope.

WHAT EACH OF THE SIX WAS DOING INSTEAD
    Every one of them reimplements base's phone card collapse by hand, and
    four do it the pre-data-label way, with the heading hard-coded into a
    positional rule:

        .units-table tbody td:nth-child(2)::before { content: 'Abbreviation'; }

    So the labels are not guesses. THEY ARE READ OUT OF THE CSS THAT IS
    BEING DELETED, column by column, and the round refuses to run if a
    table's column count and label count disagree. The other two -
    passport_management and household_member_management - already reached
    `content: attr(data-label)` on their own, which is base's spelling; for
    those two this round is little more than the class and the container.

WHAT CHANGES, PER TABLE
    1. wrapped in <div class="table-container">          (5 of 6; passport
                                                          already had one)
    2. the table gains `table alv-table`, keeping its own page class
    3. every <td> in the {% for %} row gains data-label="..."
    4. the Actions column gains .desktop-action-cell .cell-actions on BOTH
       the <th> and the <td> - not cosmetic: base's @media print rule hides
       row controls BY THOSE CLASS NAMES, so a table that gains .alv-table
       without them starts printing its buttons.
    5. the duplicated rules go - 97 of them.

WHAT DOES NOT CHANGE, DELIBERATELY
    THE BUTTONS INSIDE THE ROWS. These tables carry btn-sm btn-warning,
    .action-btn, .btn-icon and friends where the house spells
    `icon-action-btn icon-edit` inside a `.row-actions` span.
    Show-ButtonDrift.py already classifies all of them as "a row action
    inside a table" and leaves them alone, which means NOBODY owns them.
    They are a second standard and they are the next round, not this one.
    This round puts the right classes on the CELLS so that round has
    somewhere to land.

    The inline-edit state - .edit-mode, .category-name-edit and the rest -
    is page logic, not table furniture, and is kept untouched on all four
    pages that have it.

Backups: .bak_tablepersonal. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_tablepersonal'
CRLF = {}

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    """An anchor written with \\n, spelled the way THIS file spells a line.

    Lesson 70, paid for twice: four of these six files are CRLF and two are
    LF, and a multi-line anchor matches nothing in the wrong half."""
    return s.replace('\r\n', '\n').replace(
        '\n', '\r\n') if CRLF.get(path) else s.replace('\r\n', '\n')


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies
    - the house order is defeated by accept="image/*" (lesson 61).

    FOR SCANNING MARKUP ONLY. It wipes style bodies, so a caller that wants
    the CSS must not come through here (lesson from test_celebrations)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def styles_of(t):
    """The style BODIES, from the raw text. Never via blanked()."""
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


# ==========================================================================
# THE SIX
#
#   cls      the page's own table class, kept
#   labels   one per <td> in the {% for %} row, IN ORDER.
#            A label of None means "leave this cell unlabelled" - base
#            prints no prefix for a cell with no data-label, which is what
#            an actions cell wants. 'KEEP' means the cell already carries
#            the right one and must not be touched.
#   actions  how many trailing cells are action cells, so the round knows
#            which <th> and <td> take .desktop-action-cell .cell-actions
#   wrap     False only where a .table-container is already there
#   kill     selectors whose whole rule goes, because base declares it.
#            Matched on the NORMALISED selector. A bare string means the
#            selector is worn by EXACTLY ONE rule; ('sel', 2) means two,
#            which is the normal case for a selector declared once for the
#            desktop and again inside the page's own phone block. The round
#            refuses if the file disagrees with the number.
# ==========================================================================

# THREE PAGES CARRY THE SAME SEVENTEEN RULES under three different class
# names - categories, ingredients and units are the same table written out
# three times. Counted, not assumed: each has 1 shell, 2 thead, 1 th, 1 td,
# 2 tbody tr:hover, and the five-rule phone card, plus one ::before per
# column.
CARDS = [
    '%(c)s',
    ('%(c)s thead', 2),
    '%(c)s th',
    '%(c)s td',
    ('%(c)s tbody tr:hover', 2),
    '%(c)s, %(c)s tbody, %(c)s tbody tr',
    '%(c)s tbody tr',
    '%(c)s tbody td',
    '%(c)s tbody td::before',
]


def spell(items, cls):
    out = []
    for i in items:
        if isinstance(i, tuple):
            out.append((i[0] % {'c': '.' + cls}, i[1]))
        else:
            out.append(i % {'c': '.' + cls})
    return out


JOBS = [
    # ------------------------------------------------------------------
    {'rel': 'categories_management.html',
     'cls': 'categories-table',
     'labels': ['Category Name', 'Ingredients', None],
     'actions': 1,
     'wrap': True,
     'kill': spell(CARDS, 'categories-table')
             + ['.categories-table tbody td:nth-child(%d)::before' % n
                for n in (1, 2, 3)],
     'keep': ['.edit-mode td', '.categories-table tbody tr.edit-mode']},
    # ------------------------------------------------------------------
    # ALREADY ON attr(data-label). Five of its six cells carry the right
    # one; only the first does not, because the page made it a card title
    # by hand with .hm-name-cell - which is what base's
    # `.alv-table tbody td:first-child` does for every table in the app.
    {'rel': 'household_member_management.html',
     'cls': 'hm-table',
     'labels': ['Name', 'KEEP', 'KEEP', 'KEEP', 'KEEP', 'KEEP'],
     'actions': 1,
     'wrap': True,
     'drop_cell_class': ['hm-name-cell'],
     'unalign': ('text-right', 2),   # the Actions <th> and <td>; see 4c
     'kill': ['.hm-table',
              '.hm-table th',
              ('.hm-table td', 2),
              '.hm-table thead',
              '.hm-table, .hm-table tbody, .hm-table tr, .hm-table td',
              '.hm-table tr',
              '.hm-table td::before',
              '.hm-table td.hm-name-cell',
              '.hm-table td.hm-name-cell::before'],
     'keep': ['.hm-table .hide-sm', '.hm-table td.hm-actions-cell']},
    # ------------------------------------------------------------------
    {'rel': 'ingredient_base_units_management.html',
     'cls': 'ingredients-table',
     'labels': ['Ingredient Name', 'Category', 'Shopping Unit',
                'Conversion', 'Nutrition', None],
     'actions': 1,
     'wrap': True,
     'kill': spell(CARDS, 'ingredients-table')
             + ['.ingredients-table tbody td:nth-child(%d)::before' % n
                for n in range(1, 7)],
     'keep': ['.edit-mode td', '.ingredients-table tbody tr.edit-mode']},
    # ------------------------------------------------------------------
    {'rel': 'measurement_units_management.html',
     'cls': 'units-table',
     'labels': ['Unit Name', 'Abbreviation', 'Type', 'Usage', None],
     'actions': 1,
     'wrap': True,
     'kill': spell(CARDS, 'units-table')
             + ['.units-table tbody td:nth-child(%d)::before' % n
                for n in range(1, 6)],
     'keep': ['.edit-mode td', '.units-table tbody tr.edit-mode']},
    # ------------------------------------------------------------------
    # THE ONE RAISED IN TESTING: "This table must be standardised."
    # It is the closest of the six already - a .table-container, seven
    # data-labels, a .desktop-action-cell and a .mobile-action-bar. Its
    # nine phone rules are base's own, written out with literals, down to
    # the first-cell prominence rule.
    {'rel': 'passport_management.html',
     'cls': 'passport-table',
     'labels': ['KEEP'] * 7 + [None, None],
     'actions': 2,          # .desktop-action-cell AND .mobile-action-bar
     'wrap': False,
     'uncentre': 16,        # 8 <th> + 7 data <td> + the actions <td>,
                            # which base re-centres through .cell-actions.
                            # The phone-only bar is skipped; counted, 4b.

     'kill': ['.passport-table',
              '.passport-table thead',
              '.passport-table, .passport-table tbody, .passport-table tr, '
              '.passport-table td',
              '.passport-table tbody tr',
              '.passport-table tbody tr:nth-of-type(even)',
              '.passport-table td',
              '.passport-table td::before',
              '.passport-table td[data-label="Holder"]',
              '.passport-table td[data-label="Holder"]::before'],
     'keep': []},
    # ------------------------------------------------------------------
    # THE BIGGEST VISIBLE CHANGE OF THE SIX. This one does not draw rows -
    # it draws floating cards, with border-spacing: 0 10px, a shadow on
    # every row and a 3px lift on hover. On the house table they become
    # rows. That is the round doing what it says, not a regression, and it
    # is the pair to look at hardest in the contact sheet.
    {'rel': 'unit_conversions_management.html',
     'cls': 'conversions-table',
     'labels': ['Conversion', 'Applies To', None],
     'actions': 1,
     'wrap': True,
     'kill': [('.conversions-table', 2),
              ('.conversions-table thead', 2),
              '.conversions-table thead th',
              '.conversions-table tbody tr',
              '.conversions-table tbody tr:nth-child(even)',
              ('.conversions-table tbody tr:hover', 2),
              ('.conversions-table tbody td', 2),
              '.conversions-table tbody tr td:first-child',
              '.conversions-table tbody tr td:last-child',
              '.conversions-table, .conversions-table tbody, '
              '.conversions-table tbody tr',
              '.conversions-table tbody tr, '
              '.conversions-table tbody tr:nth-child(even)',
              '.conversions-table tbody td::before',
              '.conversions-table tbody td:nth-child(1)::before',
              '.conversions-table tbody td:nth-child(2)::before',
              '.conversions-table tbody td:nth-child(3)::before',
              '#noResultsRow td',
              '#noResultsRow td::before'],
     'keep': ['#noResultsRow[style*="table-row"]']},
]


# WHAT AN ACTIONS CELL WEARS, AND WHY IT IS NOT ALWAYS THE SAME PAIR.
#
# base hides .desktop-action-cell outright below 768px:
#
#     @media screen and (max-width: 768px) {
#         .desktop-action-cell { display: none !important; }
#
# because a page that has one is expected to have a .mobile-action-bar
# twin to show instead - which is how passport_management is built, and
# the only one of the six that is. The first cut of this round put the
# pair on all six, and the contact sheet came back with the row buttons
# GONE from the phone card on five pages. Nothing said so; the row simply
# was not there. Reading the markup would not have found it and did not.
#
# So the class is decided from the table, not from a flag: a cell gets
# .desktop-action-cell only where a .mobile-action-bar exists to take
# over. Everything gets .cell-actions, which centres the column and which
# base's @media print rule names in its own right - so the buttons still
# stay off paper either way.
ACT_BOTH = 'desktop-action-cell cell-actions'
ACT_ONLY = 'cell-actions' 


def table_span(text, cls):
    """(start of <table ...>, end past </table>) for the page's table."""
    scan = blanked(text)
    m = re.search(r'<table[^>]*class="[^"]*(?<![\w-])' + re.escape(cls)
                  + r'(?![\w-])[^"]*"[^>]*>', scan)
    if not m:
        return None
    j = scan.find('</table>', m.end())
    if j < 0:
        raise SystemExit('H4: %s has no </table>' % cls)
    return (m.start(), j + len('</table>'))


def row_span(text, span):
    """The first <tr> INSIDE the tbody - the {% for %} prototype row."""
    scan = blanked(text)[span[0]:span[1]]
    tb = scan.find('<tbody')
    if tb < 0:
        raise SystemExit('H4: no <tbody> in the table')
    m = re.search(r'<tr\b', scan[tb:])
    if not m:
        raise SystemExit('H4: no <tr> in the tbody')
    s = tb + m.start()
    e = scan.find('</tr>', s)
    if e < 0:
        raise SystemExit('H4: the first tbody row does not close')
    return (span[0] + s, span[0] + e + len('</tr>'))


def td_tags(text, span):
    """Offsets of every <td ...> OPENING tag in the span, in order."""
    scan = blanked(text)
    return [(span[0] + m.start(), span[0] + m.end())
            for m in re.finditer(r'<td\b[^>]*>', scan[span[0]:span[1]])]


def th_tags(text, span):
    scan = blanked(text)
    return [(span[0] + m.start(), span[0] + m.end())
            for m in re.finditer(r'<th\b[^>]*>', scan[span[0]:span[1]])]


def add_class(tag, extra):
    """Add class tokens to an opening tag, without repeating one."""
    m = re.search(r'class="([^"]*)"', tag)
    if not m:
        return tag[:-1].rstrip() + ' class="%s">' % extra
    have = m.group(1).split()
    for tok in extra.split():
        if tok not in have:
            have.append(tok)
    return tag[:m.start(1)] + ' '.join(have) + tag[m.end(1):]


def drop_rule(css, sel):
    """Remove the ONE rule whose normalised selector is `sel`.

    Comments attached in front of the selector go with it - a comment
    explaining a rule that no longer exists is worse than no comment."""
    want = ' '.join(sel.split())
    found = []
    for m in RULE.finditer(css):
        raw = m.group(1)
        norm = ' '.join(re.sub(r'/\*.*?\*/', ' ', raw, flags=re.S).split())
        if norm == want:
            found.append(m)
    if not found:
        return None, 0
    total = len(found)
    m = found[0]
    # WHERE THE RULE REALLY STARTS. Not m.start(): the RULE pattern begins
    # immediately after the previous rule's closing brace, so m.start()
    # points at the newline AFTER it. Cutting back from there to the
    # previous line's newline ate the rule BEFORE this one - which is how
    # `.categories-table td` vanished while the round was deleting
    # `.categories-table th`, and the round then reported it "not there".
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    sel_start = m.start() + lead      # the comment, if any, goes with it
    head = css.rfind('\n', 0, sel_start) + 1
    if css[head:sel_start].strip():   # something else shares the line
        head = sel_start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], total


# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H4 - THE PERSONAL TABLES JOIN THE HOUSE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed, later, already = 0, 0, 0
for job in JOBS:
    rel, cls = job['rel'], job['cls']
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('H4: %s is not on disk' % rel)
    text = read(path)
    orig = text

    span = table_span(text, cls)
    if span is None:
        raise SystemExit('H4: %s has no .%s' % (rel, cls))

    if re.search(r'\balv-table\b', text[span[0]:text.index('>', span[0])]):
        print('  %-38s already on .alv-table' % rel.replace('.html', ''))
        already += 1
        continue

    # ---------------------------------------------------- 1. the cells
    row = row_span(text, span)
    tds = td_tags(text, row)
    labels = job['labels']
    if len(tds) != len(labels):
        raise SystemExit(
            'H4: %s - the row has %d <td> and this round names %d labels. '
            'A table whose columns moved is not one this round can do '
            'blind.' % (rel, len(tds), len(labels)))

    has_mobile_bar = 'mobile-action-bar' in blanked(text)[span[0]:span[1]]
    if has_mobile_bar != (job['actions'] > 1):
        raise SystemExit(
            'H4: %s - a .mobile-action-bar is %spresent, which does not '
            'match this round\'s count of %d action cell(s).'
            % (rel, '' if has_mobile_bar else 'not ', job['actions']))

    ths = th_tags(text, span)
    want_th = len(labels) - (job['actions'] - 1)
    if len(ths) != want_th:
        raise SystemExit(
            'H4: %s - %d <th> against %d expected. %s'
            % (rel, len(ths), want_th,
               'passport carries a second, phone-only action cell with no '
               'heading of its own' if job['actions'] > 1 else ''))

    # Build the new text from the back, so earlier offsets stay valid.
    edits = []
    for i, (s, e) in enumerate(tds):
        tag = text[s:e]
        lab = labels[i]
        is_action = i >= len(labels) - job['actions']
        new = tag
        if lab == 'KEEP':
            if 'data-label' not in tag:
                raise SystemExit(
                    'H4: %s cell %d is marked KEEP but carries no '
                    'data-label' % (rel, i + 1))
        elif lab is not None:
            if 'data-label' in tag:
                raise SystemExit(
                    'H4: %s cell %d already has a data-label and this '
                    'round would write a second' % (rel, i + 1))
            # AFTER `<td`, which is three characters, not four. The first
            # draft cut at 4 and a bare `<td>` became `<td> data-label=...`
            # - the attribute outside its own tag, on five pages. A tag
            # that already had a class survived it by luck, because there
            # the fourth character is a space.
            new = new[:3] + ' data-label="%s"' % lab + new[3:]
        if is_action and 'mobile-action-bar' not in tag:
            act = ACT_BOTH if has_mobile_bar else ACT_ONLY
            # NOT on the phone-only bar. base's @media print rule names
            # .mobile-action-bar in its own right, beside
            # .desktop-action-cell - they are two controls for two media,
            # and hanging the desktop pair on the phone one says the
            # opposite of what the markup means.
            new = add_class(new, act)
        if new != tag:
            edits.append((s, e, new))

    for i, (s, e) in enumerate(ths):
        if i >= len(ths) - 1:          # the Actions heading
            new = add_class(text[s:e],
                            ACT_BOTH if has_mobile_bar else ACT_ONLY)
            if new != text[s:e]:
                edits.append((s, e, new))

    # ------------------------------------------- 2. the table's classes
    # THE HOUSE ORDER IS `table alv-table <page>-table`, which is how
    # suppliers, properties, tenants and the rest read. Appending would
    # have produced `units-table table alv-table` - the same classes and
    # the wrong sentence.
    open_end = text.index('>', span[0]) + 1
    tag = text[span[0]:open_end]
    cm = re.search(r'class="([^"]*)"', tag)
    have = [c for c in cm.group(1).split() if c not in ('table', 'alv-table')]
    new_tag = (tag[:cm.start(1)] + ' '.join(['table', 'alv-table'] + have)
               + tag[cm.end(1):])
    edits.append((span[0], open_end, new_tag))

    for s, e, new in sorted(edits, reverse=True):
        text = text[:s] + new + text[e:]

    # ------------------------------------------------ 3. the container
    if job['wrap']:
        span = table_span(text, cls)
        if 'table-container' in text[max(0, span[0] - 200):span[0]]:
            raise SystemExit('H4: %s already has a .table-container and '
                             'this round is told to add one' % rel)
        # Indented to sit where the table sits, so the file still reads as
        # a file. A wrapper hard against column 0 inside a block indented
        # eight is a tell that something was done to the page by a script.
        line = text.rfind('\n', 0, span[0]) + 1
        pad = text[line:span[0]]
        pad = pad if not pad.strip() else ''
        text = (text[:span[0]]
                + eol(path, '<div class="table-container">\n' + pad)
                + text[span[0]:span[1]]
                + eol(path, '\n' + pad + '</div>')
                + text[span[1]:])

    # ------------------------------------------------- 4. the CSS goes
    # A selector may legitimately appear twice - `.units-table thead` is
    # declared once for the desktop and once inside the phone block - so
    # each entry says HOW MANY rules wear it, and the round refuses if the
    # file disagrees. A bare string means exactly one.
    gone = 0
    for entry in job['kill']:
        sel, want = entry if isinstance(entry, tuple) else (entry, 1)
        seen = sum(drop_rule(text[a:b], sel)[1] for (a, b) in styles_of(text))
        if seen != want:
            raise SystemExit(
                'H4: %s - "%s" is worn by %d rule(s); this round was '
                'written against %d. Every selector here was read off the '
                'file this morning; if the file has moved, the round is out '
                'of date and must be re-measured, not forced.'
                % (rel, sel, seen, want))
        for _ in range(want):
            for (a, b) in styles_of(text):
                new_css, n = drop_rule(text[a:b], sel)
                if n:
                    text = text[:a] + new_css + text[b:]
                    gone += 1
                    break

    # ------------------------------------ 4b. Bootstrap's text-center
    # WEARING THE CLASS IS NOT THE SAME AS LOOKING LIKE THE HOUSE.
    # base says so itself, above .desktop-action-cell: "Everything else
    # went left when the page dropped Bootstrap's text-center, which is
    # right for names and companies and wrong for a column holding one
    # 34px button." passport_management is the last table still centring
    # all eight columns, and the centring is written in three places - the
    # table's own .text-center, and an inline text-align on every <th> and
    # every <td>. An inline style beats a class, so dropping the class
    # alone would change nothing at all.
    if job.get('uncentre'):
        span = table_span(text, cls)
        head = text.index('>', span[0]) + 1
        tag = text[span[0]:head]
        if 'text-center' not in tag:
            raise SystemExit('H4: %s has no text-center to drop' % rel)
        text = (text[:span[0]]
                + re.sub(r'\s*\btext-center\b', '', tag) + text[head:])
        span = table_span(text, cls)
        cells = sorted(th_tags(text, span) + td_tags(text, span),
                       reverse=True)
        n = 0
        for x, y in cells:
            tag = text[x:y]
            if 'mobile-action-bar' in tag:
                continue
            m2 = re.search(r'style="([^"]*)"', tag)
            if not m2 or 'text-align' not in m2.group(1):
                continue
            body = re.sub(r'\s*text-align\s*:[^;"]*;?', '', m2.group(1))
            body = body.strip().strip(';').strip()
            new_tag = (tag[:m2.start()] + (' style="%s"' % body if body
                                           else '') + tag[m2.end():])
            # Tidy: removing an attribute leaves the space that was in
            # front of it, so `class="x"  style=` and `... >`.
            new_tag = re.sub(r'\s+', ' ', new_tag)
            new_tag = re.sub(r'\s+>$', '>', new_tag)
            text = text[:x] + new_tag + text[y:]
            n += 1
        if n != job['uncentre']:
            raise SystemExit(
                'H4: %s - %d cell(s) carried an inline text-align, and this '
                'round was written against %d.' % (rel, n, job['uncentre']))
        job['_uncentred'] = n

    # -------------------------- 4c. Bootstrap's alignment UTILITIES
    # Same fault, different spelling. household_member_management hangs
    # Bootstrap's .text-right on its Actions heading and cell, and that
    # utility is declared `!important`, so it beats base's .cell-actions
    # outright - the column came out right-aligned while the other five
    # tables centre theirs. Two class tokens, and the six read alike.
    if job.get('unalign'):
        tok, want = job['unalign']
        span = table_span(text, cls)
        cells = sorted(th_tags(text, span) + td_tags(text, span),
                       reverse=True)
        n = 0
        for x, y in cells:
            tag = text[x:y]
            if not re.search(r'\b%s\b' % re.escape(tok), tag):
                continue
            cut = re.sub(r'\s*\b%s\b' % re.escape(tok), '', tag)
            cut = re.sub(r'\s+class="\s*"', '', cut)
            cut = re.sub(r'\s+', ' ', cut)
            text = text[:x] + cut + text[y:]
            n += 1
        if n != want:
            raise SystemExit(
                'H4: %s - .%s is on %d cell(s) of this table, and this '
                'round was written against %d.' % (rel, tok, n, want))

    # ------------------------------- 5. classes nothing styles now
    # A class left in the markup with no rule behind it is drift - the
    # next person reads it as meaning something. .hm-name-cell made the
    # first cell a card title by hand; base's
    # `.alv-table tbody td:first-child` does that for every table in the
    # app, so the rule went above and the class goes here.
    for dead in job.get('drop_cell_class', []):
        left = sum(len(re.findall(r'\.%s\b' % re.escape(dead), text[a:b]))
                   for (a, b) in styles_of(text))
        if left:
            raise SystemExit(
                'H4: %s - .%s still has %d rule(s). This round only removes '
                'a class that nothing styles any more.' % (rel, dead, left))
        span = table_span(text, cls)
        row = row_span(text, span)
        worn = [(x, y) for (x, y) in td_tags(text, row)
                if re.search(r'\b%s\b' % re.escape(dead), text[x:y])]
        if len(worn) != 1:
            raise SystemExit('H4: %s - .%s is worn by %d cell(s), not 1'
                             % (rel, dead, len(worn)))
        x, y = worn[0]
        cut = re.sub(r'\s*\b%s\b' % re.escape(dead), '', text[x:y])
        cut = re.sub(r'\s+class="\s*"', '', cut)
        text = text[:x] + cut + text[y:]

    for sel in job['keep']:
        norm = ' '.join(sel.split())
        here = any(' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                   flags=re.S).split()) == norm
                   for (a, b) in styles_of(text)
                   for m in RULE.finditer(text[a:b]))
        if not here:
            raise SystemExit(
                'H4: %s - "%s" is page logic this round promised to keep, '
                'and it is gone.' % (rel, sel))

    if text == orig:
        print('  %-38s nothing to do' % rel.replace('.html', ''))
        already += 1
        continue

    print('  %-38s %d label(s), %d rule(s) deleted%s%s'
          % (rel.replace('.html', ''),
             sum(1 for x in labels if x not in (None, 'KEEP')), gone,
             ', wrapped' if job['wrap'] else '',
             ', %d centring(s) dropped' % job['_uncentred']
             if job.get('_uncentred') else ''))
    changed += 1

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as fh:
                data = orig.encode('utf-8')
                if CRLF.get(path):
                    data = data.replace(b'\r\n', b'\n').replace(b'\n',
                                                                b'\r\n')
                else:
                    data = data.replace(b'\r\n', b'\n')
                fh.write(data)
        write(path, text)

print('-' * 74)
print('  %d file(s) changed, %d already done, %d LATER edit(s).'
      % (changed, already, later))
print('=' * 74)
