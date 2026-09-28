# -*- coding: utf-8 -*-
"""SECTION H, ROUND H5b - THE NUTRITION BREAKDOWN JOINS THE HOUSE

The last of the twelve Personal tables, and the only one that was keeping
TWO complete renderings of the same numbers.

WHAT IS THERE NOW
    view_recipe.html draws its per-ingredient nutrition breakdown twice.
    Above 768px a <table class="breakdown-table"> - five columns, a tfoot
    with the per-100g totals. Below 768px that table is display:none and a
    SECOND renderer builds a list of .breakdown-card divs into
    #breakdownCardsWrap: a header, a name, an amount line, a status badge,
    four label/value rows, and a totals card of its own.

    Both are built by the same JavaScript function, from the same data,
    3553 characters apart. Seventeen CSS rules exist only to style the
    second one.

    .alv-table IS THAT SECOND RENDERER, in base, for every table in the
    application. So this round does not add a phone layout - it deletes
    one, and lets the table do what the cards were doing.

NOTHING IS LOST, AND THAT WAS CHECKED BEFORE IT WAS DELETED
    The card was not showing anything the row does not. Compared field by
    field:

      card                          row
      breakdown-card-name           td.bt-name, same escaped name
      breakdown-card-amount         .bt-amount, INSIDE td.bt-name already
      breakdown-card-status         .bt-status, INSIDE td.bt-name already
      four label/value rows         the four td.bt-num, with data-label
      totals card                   the tfoot, which base now styles

    The amount line and the status badge were already in the table cell -
    the same two template fragments are interpolated into both. So the
    only thing the cards held on their own was the LABELS, and data-label
    is where those go.

WHAT ELSE CHANGES
    .breakdown-table-wrap BECOMES .table-container rather than gaining
    one. It exists only for `overflow-x: auto`, and .table-container sets
    `overflow: clip` on purpose - nesting the two would put a scroll
    container around a sticky heading and swallow it. Two wrappers doing
    one job is how that gets missed later.

    .bt-num GAINS .num. base's .num is the house numeric cell - right
    aligned, tabular figures, and a phone rule of its own - so the three
    page rules that were spelling that out go.

    THE TOTALS BAR STOPS BEING BOOTSTRAP GREEN. `.breakdown-table tfoot
    td` is #28a745 with white text; base's tfoot is --alv-surface with
    --alv-ink-strong and a 2px rule above it. That is the round's most
    visible change and it is the point of it.

WHAT IS KEPT
    .bt-amount, .bt-na, and the .unmapped / .unconvertible state with its
    .bt-status badge. Those are what this page knows about its own data,
    and base has no opinion about an ingredient that could not be mapped.

Backups: .bak_tablebreakdown. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_tablebreakdown'
REL = 'view_recipe.html'
CRLF = {}

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
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('H5b: %s is not a byte copy' % bak)


def eol(path, s):
    """An anchor written with \\n, spelled the way THIS file spells a line.

    view_recipe.html is CRLF. Lesson 70, paid for a third time: the
    multi-line cards anchor matched nothing and the round reported the
    div "not where this round expects it" while looking straight at it.
    """
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def styles_of(t):
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


def scripts_of(t):
    return [(m.start(1), m.end(1)) for m in SCRIPT.finditer(t)]


# ==========================================================================
# THE FIVE COLUMNS, and the label each cell carries on a phone. Read off
# the table's own <th> text, which is the only place they have ever been
# written down - this page never had nth-child ::before rules because it
# never collapsed its table; it built a second one instead.
COLS = [('bt-name', 'Ingredient'),
        ('bt-num', 'Calories'),
        ('bt-num', 'Carbs (g)'),
        ('bt-num', 'Fat (g)'),
        ('bt-num', 'Protein (g)')]

WRAP_WAS = '<div class="breakdown-table-wrap">'
WRAP_NOW = '<div class="table-container">'

CARDS_DIV = ('                        <!-- Mobile cards -->\n'
             '                        <div class="breakdown-cards-wrap" '
             'id="breakdownCardsWrap"></div>\n')

CARDS_FROM = '    // === Mobile cards ==='
CARDS_TO = '    cardsWrap.innerHTML = cardsHtml;'

# Every one of these is base's now, or belonged only to the cards.
KILL = [
    '.breakdown-table-wrap',                 # overflow-x, desktop
    '.breakdown-table',
    '.breakdown-table thead th',
    '.breakdown-table thead th.bt-num',
    '.breakdown-table tbody td',
    '.breakdown-table tbody td.bt-num',
    '.breakdown-table tfoot td',
    '.breakdown-table tfoot td.bt-num',
    ('.breakdown-cards-wrap', 2),            # desktop hide, phone show
    '.breakdown-card',
    '.breakdown-card.unmapped, .breakdown-card.unconvertible',
    '.breakdown-card.totals',
    '.breakdown-card-header',
    '.breakdown-card-name',
    '.breakdown-card.totals .breakdown-card-name',
    '.breakdown-card-amount',
    '.breakdown-card-status',
    '.breakdown-card-row',
    '.breakdown-card-label',
    '.breakdown-card.totals .breakdown-card-label',
    '.breakdown-card-value',
    '.breakdown-card.totals .breakdown-card-value',
    '.breakdown-card-value.bt-na',
    '.breakdown-card.totals .breakdown-card-value.bt-na',
]
# .breakdown-table-wrap is declared twice - once for overflow, once to
# hide it on a phone. Both go with the wrapper's name.
KILL[0] = ('.breakdown-table-wrap', 2)

# Page logic: what this page knows about its own data.
KEEP = [
    '.breakdown-table tbody td.bt-name',
    '.breakdown-table tbody td.bt-name .bt-amount',
    '.breakdown-table .bt-na',
]


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
print('SECTION H, ROUND H5b - THE NUTRITION BREAKDOWN%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(ROOT, REL)
if not os.path.isfile(path):
    raise SystemExit('H5b: %s is not on disk' % REL)
with open(path, 'rb') as _fh:
    raw = _fh.read()
text = read(path)
orig = text

if 'alv-table breakdown-table' in text:
    print('  %-38s already done' % REL.replace('.html', ''))
    print('-' * 74)
    print('  0 file(s) changed, 1 already done.')
    print('=' * 74)
    raise SystemExit(0)

# ------------------------------------------------------- 1. the wrapper
if text.count(WRAP_WAS) != 1:
    raise SystemExit('H5b: %s appears %d time(s), not 1'
                     % (WRAP_WAS, text.count(WRAP_WAS)))
text = text.replace(WRAP_WAS, WRAP_NOW, 1)

# --------------------------------------------------------- 2. the table
TAB = '<table class="breakdown-table">'
if text.count(TAB) != 1:
    raise SystemExit('H5b: the table tag appears %d time(s), not 1'
                     % text.count(TAB))
text = text.replace(TAB, '<table class="table alv-table breakdown-table">', 1)

# --------------------------------------- 3. the headings, so .num lands
#    The <th> already carry .bt-num; they gain .num beside it so the
#    heading and the figures under it are aligned by the SAME rule.
n_th = 0
for cls, lab in COLS:
    if cls != 'bt-num':
        continue
th_pat = re.compile(r'<th class="bt-num">')
n_th = len(th_pat.findall(text))
if n_th != 4:
    raise SystemExit('H5b: %d <th class="bt-num">, not 4' % n_th)
text = th_pat.sub('<th class="bt-num num">', text)

# ------------------------------------ 4. the JS row and the tfoot row
for (marker, labels) in (
        ('<td class="bt-name">', [c[1] for c in COLS]),
        (None, None)):
    break

js_hit = None
for (a, b) in scripts_of(text):
    i = text.find('<td class="bt-name">', a, b)
    if i >= 0:
        js_hit = (a, b)
        break
if js_hit is None:
    raise SystemExit('H5b: the JS row template is not where this round '
                     'expects it')
a, b = js_hit
body = text[a:b]

rows = list(re.finditer(r'<tr[^>]*>\s*(?:<td[^>]*>.*?</td>\s*){5}</tr>',
                        body, re.S))
if len(rows) != 2:
    raise SystemExit(
        'H5b: found %d five-cell row template(s) in the script, not 2 - '
        'one for a row and one for the totals. A page that builds its '
        'rows somewhere else is not one this round can do blind.'
        % len(rows))

# THE TWO ROWS ARE NOT LABELLED THE SAME. The tbody row is an
# ingredient, so its first cell is that ingredient's name and gets
# "Ingredient". The tfoot row is the totals, and its first cell already
# READS "Per 100g total" - labelling it would make the phone card say
# "Ingredient: Per 100g total", which is not what that line is. base
# prints no prefix for a cell with no data-label, which is exactly right
# here, so the totals row's first cell is left alone.
FIRST = {0: 'Ingredient', 1: None}       # index in `rows`: tbody, tfoot
labelled = 0
for idx in range(len(rows) - 1, -1, -1):
    m = rows[idx]
    seg = m.group(0)
    cells = list(re.finditer(r'<td\b[^>]*>', seg))
    if len(cells) != 5:
        raise SystemExit('H5b: a row template has %d cells' % len(cells))
    new = seg
    for k in range(4, -1, -1):
        c = cells[k]
        tag = c.group(0)
        if 'data-label' in tag:
            raise SystemExit('H5b: a cell already carries a data-label')
        lab = COLS[k][1] if k else FIRST[idx]
        nt = tag
        if lab is not None:
            nt = tag[:3] + ' data-label="%s"' % lab + tag[3:]
            labelled += 1
        if COLS[k][0] == 'bt-num':
            cm = re.search(r'class="([^"]*)"', nt)
            if cm and 'num' not in cm.group(1).split():
                nt = (nt[:cm.start(1)] + cm.group(1) + ' num'
                      + nt[cm.end(1):])
        # NO CLASS IS ADDED TO A CELL THAT HAS NONE. A first cut gave the
        # totals row's first cell .bt-name, and the only rule wearing that
        # name is scoped to tbody - a class nothing styles, which is the
        # drift this section of work exists to remove.
        new = new[:c.start()] + nt + new[c.end():]
    body = body[:m.start()] + new + body[m.end():]
text = text[:a] + body + text[b:]

# --------------------------------------------- 5. the second renderer
i = text.find(CARDS_FROM)
j = text.find(CARDS_TO)
if i < 0 or j < 0 or j < i:
    raise SystemExit('H5b: the mobile card block is not where this round '
                     'expects it (%d, %d)' % (i, j))
j = text.find('\n', j) + 1
cut = j - i
text = text[:i] + text[j:]

if text.count('breakdownCardsWrap') != 1:
    raise SystemExit('H5b: #breakdownCardsWrap is named %d time(s) after '
                     'the renderer went; expected the div alone'
                     % text.count('breakdownCardsWrap'))
CARDS_DIV = eol(path, CARDS_DIV)
if text.count(CARDS_DIV) != 1:
    # fall back to a looser match so a reflow is a STOP, not a wrong edit
    m = re.search(r'[ \t]*<!-- Mobile cards -->[ \t]*\r?\n[ \t]*'
                  r'<div class="breakdown-cards-wrap" '
                  r'id="breakdownCardsWrap"></div>[ \t]*\r?\n', text)
    if not m:
        raise SystemExit('H5b: the cards div is not where this round '
                         'expects it')
    text = text[:m.start()] + text[m.end():]
else:
    text = text.replace(CARDS_DIV, '', 1)

if 'breakdownCardsWrap' in text or 'breakdown-card' in re.sub(
        r'\.breakdown-card', '', text):
    left = text.count('breakdownCardsWrap')
    if left:
        raise SystemExit('H5b: %d reference(s) to the cards remain' % left)

# ------------------------------------------------------- 6. the CSS goes
gone = 0
for entry in KILL:
    sel, want = entry if isinstance(entry, tuple) else (entry, 1)
    seen = sum(drop_rule(text[a2:b2], sel)[1]
               for (a2, b2) in styles_of(text))
    if seen != want:
        raise SystemExit('H5b: "%s" is worn by %d rule(s); this round was '
                         'written against %d.' % (sel, seen, want))
    for _ in range(want):
        for (a2, b2) in styles_of(text):
            new_css, n = drop_rule(text[a2:b2], sel)
            if n:
                text = text[:a2] + new_css + text[b2:]
                gone += 1
                break

for sel in KEEP:
    norm = ' '.join(sel.split())
    here = any(' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                               flags=re.S).split()) == norm
               for (a2, b2) in styles_of(text)
               for m in RULE.finditer(text[a2:b2]))
    if not here:
        raise SystemExit('H5b: "%s" is page logic this round promised to '
                         'keep, and it is gone.' % sel)

print('  %-38s %d cell(s) labelled, %d rule(s) deleted, %d characters of '
      'a second renderer removed' % (REL.replace('.html', ''), labelled,
                                     gone, cut))
print('-' * 74)
print('  1 file changed.')
print('=' * 74)

if not CHECK:
    back_up(path, raw)
    write(path, text)
