# -*- coding: utf-8 -*-
"""SECTION H, ROUND H5a - THE IMPORTED-RECIPE TABLES JOIN THE HOUSE

The first of the two JS-built Personal tables H4 set aside. Both live in
preview_imported_recipe.html: the ingredients grid and the instructions
grid, seven columns and five.

WHY THIS IS NOT H4
    H4 did six tables whose rows come from a Django {% for %} and nothing
    else. These two have a SECOND row template, in JavaScript:

        newRow.innerHTML = `<td class="drag-col">...`

    for "Add Another Ingredient" and "Add Another Step". A round that
    labelled only the markup would give a phone card its headings on the
    rows that came from the server and no headings at all on the rows the
    person just added - which is worse than none, because it looks like a
    bug in the data rather than in the page. Both templates are done here,
    and the suite counts them separately.

THESE ARE TABLES OF FORM INPUTS, AND THAT WAS A QUESTION
    base's phone card lays a cell out as label left, value right. For a
    full-width text input that could have been cramped, so it was
    measured rather than assumed: rendered at 390px with the page's own
    rules removed, the ingredient row goes from 494px tall to 307px and
    every input keeps 215px of width. It reads better, not worse. The
    probe is in this round's contact sheet.

WHAT IS KEPT, AND WHY
    THE PINNED CORNERS. On a phone this page does not lay its controls
    out in the card; it pins the drag handle to the card's top left and
    the remove button to its top right, with position: absolute. base has
    no drag handle and no opinion about one, so those two rules are page
    logic and stay. Without them the grab handle becomes a full-width
    empty row, which the first probe showed.

    BUT NOT THE ACTIONS PIN, WHICH GOES. It is written

        #ingredientsTable td.actions-col, #instructionsTable td:last-child

    and its first half has never matched anything: no <td> in the
    ingredients grid wears .actions-col, only its <th> does. Its second
    half is live and BREAKS on the house card - base lays a cell out as
    label left, value right, so the instructions grid's step-number badge
    moves from x=52 to x=307 and lands underneath the remove button
    pinned at x=320. Measured at 390px, before and after; the first cut
    of this round shipped that overlap and the contact sheet showed it.

    Retired rather than nudged, so both grids read the same - remove
    button at the foot of the card, which is what the ingredients grid
    has done all along because its half of the pin never fired.

    The column widths, the input borders and the valid/invalid colouring
    are the page's own and are untouched.

WHAT GOES
    The seventeen rules that were writing base's table out by hand,
    including eight `td:nth-child(n)::before { content: '...' }` - which
    are, once more, where the labels in this round come from.

    .ingredient-table thead is a TEAL BAND with white text; base's
    thead is --alv-surface with dark ink. That is the biggest visible
    change of the round and it is the round doing what it says.

Backups: .bak_tablepreview. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_tablepreview'
REL = 'preview_imported_recipe.html'
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


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46). H6 wrote five
    of these LF over CRLF originals and a revert then corrupted the source
    itself; it was caught only by cmp against the laptop."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('H5a: %s is not a byte copy' % bak)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Markup only. Comments on the RAW text first (lesson 61)."""
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
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


def scripts_of(t):
    return [(m.start(1), m.end(1)) for m in SCRIPT.finditer(t)]


# ==========================================================================
# THE TWO TABLES.
#
#   labels   one per <td>, in order. None leaves a cell unlabelled, which
#            is what base wants for a control cell - it prints no prefix
#            for a cell with no data-label.
#   js       the marker that finds the JavaScript row template, and how
#            many <td> it must hold.
# ==========================================================================
TABLES = [
    {'id': 'ingredientsTable',
     'labels': [None, 'Quantity', 'Measurement', 'Ingredient',
                'Preparation', 'Group', None],
     'js': "newRow.className = 'ingredient-row';"},
    {'id': 'instructionsTable',
     'labels': [None, 'Step', 'Instruction', 'Group', None],
     'js': "newRow.className = 'instruction-row';"},
]

CLS = 'ingredient-table'

# Every one of these is base's now. Counted from the file, ('sel', 2) where
# the page declares it once for the desktop and again in its phone block.
KILL = [
    ('.ingredient-table', 2),
    ('.ingredient-table thead', 2),
    '.ingredient-table th',
    ('.ingredient-table td', 2),
    '.ingredient-table tbody tr',
    '.ingredient-table tbody tr:last-child',
    '.ingredient-table, .ingredient-table tbody, .ingredient-table tr',
    '.ingredient-table tr.ingredient-row, '
    '.ingredient-table tr.instruction-row',
    '.ingredient-table tr.ingredient-row:hover, '
    '.ingredient-table tr.instruction-row:hover',
    '.ingredient-table td::before',
    # THE ACTIONS PIN, AND WHY IT GOES RATHER THAN STAYS.
    #   #ingredientsTable td.actions-col, #instructionsTable td:last-child
    # Its FIRST half has never matched anything - no <td> in the
    # ingredients grid wears .actions-col, only its <th> does - so that
    # grid's remove button has always been an ordinary row at the foot of
    # the card. Its SECOND half is live, and on the house card it BREAKS:
    # base lays a phone cell out as label left, value right, so the step
    # number badge moves from x=52 to x=307 and lands under the button
    # pinned at x=320. Measured, both ways, before and after.
    #
    # So the pin is retired rather than nudged. The two grids then behave
    # the same - remove button at the foot of the card - which is what the
    # bigger of them has done all along.
    '#ingredientsTable td.actions-col, #instructionsTable td:last-child',
    "#ingredientsTable td:nth-child(2)::before",
    "#ingredientsTable td:nth-child(3)::before",
    "#ingredientsTable td:nth-child(4)::before",
    "#ingredientsTable td:nth-child(5)::before",
    "#ingredientsTable td:nth-child(6)::before",
    "#instructionsTable td:nth-child(2)::before",
    "#instructionsTable td:nth-child(3)::before",
    "#instructionsTable td:nth-child(4)::before",
]

# Page logic. Named so that losing one is a stop, not a silence.
KEEP = [
    '.ingredient-table input',
    '.ingredient-table .drag-col',
    '.ingredient-table .actions-col',
    '#ingredientsTable td.drag-col, #instructionsTable td:first-child',
    '#ingredientsTable td.drag-col::before, '
    '#ingredientsTable td.actions-col::before, '
    '#instructionsTable td:first-child::before, '
    '#instructionsTable td:last-child::before',
]

ACT = 'cell-actions'


def table_span(text, tid):
    scan = blanked(text)
    m = re.search(r'<table[^>]*id="%s"[^>]*>' % re.escape(tid), scan)
    if not m:
        return None
    j = scan.find('</table>', m.end())
    if j < 0:
        raise SystemExit('H5a: %s has no </table>' % tid)
    return (m.start(), j + len('</table>'))


def row_span(text, span):
    scan = blanked(text)[span[0]:span[1]]
    tb = scan.find('<tbody')
    m = re.search(r'<tr\b', scan[tb:]) if tb >= 0 else None
    if not m:
        raise SystemExit('H5a: no prototype row')
    s = tb + m.start()
    e = scan.find('</tr>', s)
    return (span[0] + s, span[0] + e + len('</tr>'))


def td_tags(text, span, scan=None):
    scan = blanked(text) if scan is None else scan
    return [(span[0] + m.start(), span[0] + m.end())
            for m in re.finditer(r'<td\b[^>]*>', scan[span[0]:span[1]])]


def th_tags(text, span):
    scan = blanked(text)
    return [(span[0] + m.start(), span[0] + m.end())
            for m in re.finditer(r'<th\b[^>]*>', scan[span[0]:span[1]])]


def add_class(tag, extra):
    m = re.search(r'class="([^"]*)"', tag)
    if not m:
        return tag[:-1].rstrip() + ' class="%s">' % extra
    have = m.group(1).split()
    for tok in extra.split():
        if tok not in have:
            have.append(tok)
    return tag[:m.start(1)] + ' '.join(have) + tag[m.end(1):]


def label(tag, text_label):
    if text_label is None:
        return tag
    if 'data-label' in tag:
        raise SystemExit('H5a: a cell already carries a data-label')
    return tag[:3] + ' data-label="%s"' % text_label + tag[3:]


def drop_rule(css, sel):
    want = ' '.join(sel.split())
    found = [m for m in RULE.finditer(css)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                flags=re.S).split()) == want]
    if not found:
        return None, 0
    m = found[0]
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    start = m.start() + lead
    head = css.rfind('\n', 0, start) + 1
    if css[head:start].strip():
        head = start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], len(found)


# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H5a - THE IMPORTED-RECIPE TABLES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(ROOT, REL)
if not os.path.isfile(path):
    raise SystemExit('H5a: %s is not on disk' % REL)
with open(path, 'rb') as _fh:
    raw = _fh.read()
text = read(path)
orig = text

if re.search(r'<table[^>]*\balv-table\b', blanked(text)):
    print('  %-38s already on .alv-table' % REL.replace('.html', ''))
    print('-' * 74)
    print('  0 file(s) changed, 1 already done.')
    print('=' * 74)
    raise SystemExit(0)

labelled = jslabelled = 0
for spec in TABLES:
    tid = spec['id']
    span = table_span(text, tid)
    if span is None:
        raise SystemExit('H5a: no table #%s' % tid)

    # ------------------------------------------------- 1. the markup row
    row = row_span(text, span)
    tds = td_tags(text, row)
    if len(tds) != len(spec['labels']):
        raise SystemExit(
            'H5a: #%s has %d <td> and this round names %d labels'
            % (tid, len(tds), len(spec['labels'])))
    ths = th_tags(text, span)
    if len(ths) != len(spec['labels']):
        raise SystemExit('H5a: #%s has %d <th> against %d columns'
                         % (tid, len(ths), len(spec['labels'])))

    edits = []
    for i, (s, e) in enumerate(tds):
        tag = text[s:e]
        new = label(tag, spec['labels'][i])
        if i == len(tds) - 1:
            new = add_class(new, ACT)
        if new != tag:
            edits.append((s, e, new))
            if spec['labels'][i]:
                labelled += 1
    s, e = ths[-1]
    new = add_class(text[s:e], ACT)
    if new != text[s:e]:
        edits.append((s, e, new))

    open_end = text.index('>', span[0]) + 1
    tag = text[span[0]:open_end]
    cm = re.search(r'class="([^"]*)"', tag)
    have = [c for c in cm.group(1).split() if c not in ('table', 'alv-table')]
    edits.append((span[0], open_end,
                  tag[:cm.start(1)] + ' '.join(['table', 'alv-table'] + have)
                  + tag[cm.end(1):]))

    for s, e, new in sorted(edits, reverse=True):
        text = text[:s] + new + text[e:]

    # ------------------------------------------------ 2. the container
    span = table_span(text, tid)
    if 'table-container' in blanked(text)[max(0, span[0] - 200):span[0]]:
        raise SystemExit('H5a: #%s already has a .table-container' % tid)
    line = text.rfind('\n', 0, span[0]) + 1
    pad = text[line:span[0]]
    pad = pad if not pad.strip() else ''
    text = (text[:span[0]] + eol(path, '<div class="table-container">\n' + pad)
            + text[span[0]:span[1]] + eol(path, '\n' + pad + '</div>')
            + text[span[1]:])

    # --------------------------------- 3. THE SECOND ROW TEMPLATE, IN JS
    hit = None
    for (a, b) in scripts_of(text):
        i = text.find(spec['js'], a, b)
        if i >= 0:
            hit = (a, b, i)
            break
    if hit is None:
        raise SystemExit(
            'H5a: the JavaScript row template for #%s is not where this '
            'round expects it (looking for %r). A round that labels only '
            'the markup gives a phone card headings on the rows that came '
            'from the server and none on the rows the person just added.'
            % (tid, spec['js']))
    a, b, i = hit
    m = re.search(r'newRow\.innerHTML\s*=\s*`(.*?)`;', text[i:b], re.S)
    if not m:
        raise SystemExit('H5a: no innerHTML template after %r' % spec['js'])
    tmpl = m.group(1)
    cells = list(re.finditer(r'<td\b[^>]*>', tmpl))
    if len(cells) != len(spec['labels']):
        raise SystemExit(
            'H5a: the JS row for #%s builds %d <td> and the markup row has '
            '%d. The two row templates must agree or a phone card changes '
            'shape depending on where the row came from.'
            % (tid, len(cells), len(spec['labels'])))
    new_tmpl = tmpl
    for k in range(len(cells) - 1, -1, -1):
        c = cells[k]
        tag = c.group(0)
        nt = label(tag, spec['labels'][k])
        if k == len(cells) - 1:
            nt = add_class(nt, ACT)
        if nt != tag:
            new_tmpl = new_tmpl[:c.start()] + nt + new_tmpl[c.end():]
            if spec['labels'][k]:
                jslabelled += 1
    text = text[:i + m.start(1)] + new_tmpl + text[i + m.end(1):]

# ------------------------------------------------------- 4. the CSS goes
gone = 0
for entry in KILL:
    sel, want = entry if isinstance(entry, tuple) else (entry, 1)
    seen = sum(drop_rule(text[a:b], sel)[1] for (a, b) in styles_of(text))
    if seen != want:
        raise SystemExit(
            'H5a: "%s" is worn by %d rule(s); this round was written '
            'against %d.' % (sel, seen, want))
    for _ in range(want):
        for (a, b) in styles_of(text):
            new_css, n = drop_rule(text[a:b], sel)
            if n:
                text = text[:a] + new_css + text[b:]
                gone += 1
                break

for sel in KEEP:
    norm = ' '.join(sel.split())
    here = any(' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                               flags=re.S).split()) == norm
               for (a, b) in styles_of(text)
               for m in RULE.finditer(text[a:b]))
    if not here:
        raise SystemExit(
            'H5a: "%s" is page logic this round promised to keep, and it '
            'is gone.' % sel)

print('  %-38s %d label(s) in the markup, %d in the JS row builders, '
      '%d rule(s) deleted' % (REL.replace('.html', ''), labelled,
                              jslabelled, gone))
print('-' * 74)
print('  1 file changed.')
print('=' * 74)

if not CHECK:
    back_up(path, raw)
    write(path, text)
