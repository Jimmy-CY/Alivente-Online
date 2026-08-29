#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tenant Payment Behaviour joins the standard.

WHAT WAS THERE. 570 lines, 86 rules, 32 distinct colours, and no `alv-`
vocabulary at all - the page predates the standard rather than drifting from
it. Three tables, none in a container, all wearing

    .pd-table thead th { background: #2c3e50; color: white; }

the same navy band the Outstanding Invoices report wore until this morning.
And the same trap beneath it:

    .pd-table-wrap { overflow-x: auto; }

An element that scrolls becomes the scroll container for any sticky
descendant, so a sticky header pins to the wrapper instead of the viewport.
That is the sticky sweep's whole finding, and this is the third page to have
it.

THE BADGES NEEDED NO NEW VOCABULARY, WHICH WAS THE SURPRISE. The `vs Terms`
chips looked like they would force 1.4's deferred question - whether
`.alv-age-1..4` should generalise into a sequential scale. They do not. They
are four VERDICTS, not four degrees, and base has had that family all along:

    .pd-badge-ontime   -> .alv-pill-good
    .pd-badge-slight   -> .alv-pill-attn
    .pd-badge-late     -> .alv-pill-bad
    .pd-badge-unknown  -> .alv-pill-neutral

So the ageing scale stays an ageing scale and 1.4 is still waiting for a
genuine second asker.

THE CLASS NAME MOVES INTO THE VIEW. The template wrote
`pd-badge-{{ r.band }}`, which builds a class name that cannot be found by
searching for it - four class names invisible to any tool that reads the
stylesheet, this patcher included. `BAND_PILL` maps band to pill in the view,
which is the move `physical_invoice_list` made with `status_pill`.

TWO ROW TREATMENTS, AND ONLY ONE GOES. This page said the same thing three
times: a badge, a 4px coloured left border, and a faint wash across every cell
of the row. The WASH goes - it competes with the badge for the same message,
and it existed for only two of the four bands, so the table was already
inconsistent about it. The LEFT BORDER stays, retoned onto house tokens: it is
a scannable edge marker on a wide table, it covers all four bands, and it
never collides with text.

THE TILES BECOME CARDS, but only as far as base can carry them. `.pd-stat` was
`#f8f9fa` on `#e9ecef` with a radius - which is `.alv-card`, hand-rolled. The
4-up grid and the big-number-over-small-label typography stay page-local,
because base has no stat-tile component and ONE page is not enough to invent
one. That is the restraint that deferred the ageing scale until a screen
genuinely needed it.

WHAT THIS ROUND DOES NOT DO. `.pd-detail-table` - the small grid inside an
expanded row - keeps its own rules. A nested detail grid is not a list of
records, and the standard's mobile card view would destroy the column
alignment that makes it readable; the same judgement 1.3b reached about
`physical_invoice_edit`'s lines-table. And `.pd-num` stays: it is `.num` plus
`white-space: nowrap`, on 28 cells, and swapping all of them to carry two
classes is churn for one duplicated declaration.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
VIEW  = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
BASE  = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE  = os.path.join(ROOT, 'pages', 'templates', 'tenant_payment_days.html')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_paydays'

SENTINEL = 'BAND_PILL'

# ---------------------------------------------------------------------------
# 1. the view names the pill
# ---------------------------------------------------------------------------
V_OLD_BAND = """        if vs_terms is None:
            band = 'unknown'"""
V_NEW_BAND = """        # WHICH HOUSE PILL A BAND WEARS, decided here rather than interpolated
        # into a class name in the template. `pd-badge-{{ r.band }}` built four
        # class names that could not be found by searching for them - invisible
        # to anything that reads the stylesheet, including the patcher that
        # replaced them. Same move physical_invoice_list made with status_pill.
        #
        # These are VERDICTS, not degrees, which is why they take the pill
        # family and not the .alv-age-* scale: a tenant is on time or not, and
        # 'slight' is a different answer rather than a milder one.
        BAND_PILL = {
            'ontime': 'alv-pill-good',
            'slight': 'alv-pill-attn',
            'late': 'alv-pill-bad',
            'unknown': 'alv-pill-neutral',
        }

        if vs_terms is None:
            band = 'unknown'"""

V_OLD_ROW = """            'band': band,"""
V_NEW_ROW = """            'band': band,
            'band_pill': BAND_PILL[band],"""

# ---------------------------------------------------------------------------
# 2. the markup
# ---------------------------------------------------------------------------
P_OLD_WRAP1 = """    <div class="pd-table-wrap">
      <table class="pd-table">"""
P_NEW_WRAP1 = """    <div class="table-container">
      <table class="alv-table">"""

P_OLD_WRAP2 = """      <div class="pd-table-wrap">
        <table class="pd-table pd-table-compact">"""
P_NEW_WRAP2 = """      <div class="table-container">
        <table class="alv-table pd-table-compact">"""

P_OLD_BADGE = """<span class="pd-badge pd-badge-{{ r.band }}">"""
P_NEW_BADGE = """<span class="alv-pill {{ r.band_pill }}">"""

# The compact table's rows carried the WASH only. With that gone they keep the
# edge marker instead, which the main table already uses and which covers all
# four bands rather than two.
P_OLD_COMPACT = """            <tr class="{% if o.age > 30 %}pd-band-late{% elif o.age > grace %}pd-band-slight{% endif %}">"""
P_NEW_COMPACT = """            <tr class="pd-row {% if o.age > 30 %}pd-band-late{% elif o.age > grace %}pd-band-slight{% else %}pd-band-ontime{% endif %}">"""

P_OLD_TILES = """      <div class="pd-stat">"""
P_NEW_TILES = """      <div class="alv-card pd-stat">"""
P_OLD_TILE4 = """      <div class="pd-stat {% if summary.flagged %}pd-stat-warn{% endif %}">"""
P_NEW_TILE4 = """      <div class="alv-card pd-stat {% if summary.flagged %}pd-stat-warn{% endif %}">"""

# ---------------------------------------------------------------------------
# 3. the rules base already owns
# ---------------------------------------------------------------------------
P_OLD_TWRAP = """.pd-table-wrap { overflow-x: auto; }"""
P_NEW_TWRAP = """/* .pd-table-wrap set overflow-x: auto, which is the one declaration
   .table-container must not carry - an element that scrolls becomes the
   scroll container for any sticky descendant, and the header then pins to
   the wrapper rather than to the viewport. */"""

P_OLD_TABLE = """.pd-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}"""
P_NEW_TABLE = """/* The table's appearance is base's now: the shell, the header treatment, the
   borders, the hover, the mobile cards and the print behaviour. What was here
   was a navy #2c3e50 band with white text that nothing in base could reach. */"""

P_OLD_TH = """.pd-table thead th {
    background: #2c3e50;
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    white-space: nowrap;
}"""
P_NEW_TH = """"""

P_OLD_TD = """.pd-table tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid #eef0f2;
    vertical-align: middle;
}"""
P_NEW_TD = """"""

P_OLD_HOVER = """.pd-table tbody tr.pd-row:hover { background: #f6fafc; }"""
P_NEW_HOVER = """"""

P_OLD_THNUM = """.pd-table thead th.pd-num { text-align: right; }"""
P_NEW_THNUM = """.alv-table thead th.pd-num { text-align: right; }"""

# ---- the wash goes, the edge marker is retoned ----------------------------
P_OLD_BANDS = """.pd-row.pd-band-ontime { border-left: 4px solid #27ae60; }
.pd-row.pd-band-slight { border-left: 4px solid #f39c12; }
.pd-row.pd-band-late   { border-left: 4px solid #e74c3c; }
.pd-row.pd-band-unknown{ border-left: 4px solid #bdc3c7; }"""
P_NEW_BANDS = """/* THE EDGE MARKER STAYS, the wash does not. This page said one thing three
   times - a badge, this 4px border, and a tint across every cell of the row.
   The tint competed with the badge for the same message and existed for only
   two of the four bands. The border covers all four, never collides with
   text, and is what lets a problem row be spotted from the far side of a wide
   table. */
.pd-row.pd-band-ontime  { border-left: 4px solid var(--alv-good); }
.pd-row.pd-band-slight  { border-left: 4px solid var(--alv-warn); }
.pd-row.pd-band-late    { border-left: 4px solid var(--alv-bad); }
.pd-row.pd-band-unknown { border-left: 4px solid var(--alv-neutral); }"""

P_OLD_WASH = """tr.pd-band-slight td { background: #fffdf7; }
tr.pd-band-late td   { background: #fef8f7; }"""
P_NEW_WASH = """"""

P_OLD_PILL = """.pd-badge {
    display: inline-block;
    min-width: 52px;
    text-align: center;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.82rem;
}"""
P_NEW_PILL = """/* .pd-badge and its four variants are base's .alv-pill family now. They were
   four verdicts all along - good, attn, bad, neutral - not four degrees, so
   they take the pill family rather than the .alv-age-* scale. */"""

P_OLD_PILLV = """.pd-badge-ontime { background: #e8f8f0; color: #1e8449; }
.pd-badge-slight { background: #fdf3e3; color: #b9770e; }
.pd-badge-late   { background: #fdecea; color: #c0392b; }
.pd-badge-unknown{ background: #f2f3f4; color: #7f8c8d; }"""
P_NEW_PILLV = """"""

# ---- the tiles -----------------------------------------------------------
P_OLD_STAT = """.pd-stat {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
}"""
P_NEW_STAT = """/* The surface, border and radius come from .alv-card. What stays here is what
   makes a STAT TILE rather than a card - the centring, and the big figure over
   a small label below. base has no stat-tile component, and one page is not
   enough to invent one; that is the restraint that kept the ageing scale
   waiting until a screen genuinely needed it. */
.pd-stat {
    padding: 14px 16px;
    text-align: center;
    display: block;
}"""

P_OLD_STATV = """.pd-stat-value { font-size: 1.7rem; font-weight: 700; color: #2c3e50; line-height: 1.1; }"""
P_NEW_STATV = """.pd-stat-value { font-size: 1.7rem; font-weight: 700; color: var(--alv-ink-strong); line-height: 1.1; }"""

P_OLD_STATL = """.pd-stat-label {
    font-size: 0.78rem;
    color: #6c757d;"""
P_NEW_STATL = """.pd-stat-label {
    font-size: 0.78rem;
    color: var(--alv-ink-soft);"""

P_OLD_STATW = """.pd-stat-warn { background: #fff8e6; border-color: #ffe0a3; }
.pd-stat-warn .pd-stat-value { color: #b8860b; }"""
P_NEW_STATW = """.pd-stat-warn { background: var(--alv-warn-soft); border-color: var(--alv-warn); }
.pd-stat-warn .pd-stat-value { color: var(--alv-warn); }"""

EDITS_VIEW = [
    ('the view names the pill, so the class can be found by searching for it',
     V_OLD_BAND, V_NEW_BAND),
    ('  and every row carries it', V_OLD_ROW, V_NEW_ROW),
]
EDITS_PAGE = [
    ('the behaviour table goes into a container and onto .alv-table',
     P_OLD_WRAP1, P_NEW_WRAP1),
    ('  and so does the unpaid list', P_OLD_WRAP2, P_NEW_WRAP2),
    ('the vs-Terms chip becomes a house pill', P_OLD_BADGE, P_NEW_BADGE),
    ('the unpaid rows keep the edge marker, having lost the wash',
     P_OLD_COMPACT, P_NEW_COMPACT),
    ('the flagged tile becomes a card', P_OLD_TILE4, P_NEW_TILE4),
    ('the scrolling wrapper goes', P_OLD_TWRAP, P_NEW_TWRAP),
    ('the page stops drawing its own table', P_OLD_TABLE, P_NEW_TABLE),
    ('  the navy band', P_OLD_TH, P_NEW_TH),
    ('  the cell padding and borders', P_OLD_TD, P_NEW_TD),
    ('  and the hover', P_OLD_HOVER, P_NEW_HOVER),
    ('  while the numeric heading rule follows the table', P_OLD_THNUM, P_NEW_THNUM),
    ('the edge marker is retoned and the wash removed', P_OLD_BANDS, P_NEW_BANDS),
    ('  the wash itself', P_OLD_WASH, P_NEW_WASH),
    ('the badge becomes .alv-pill', P_OLD_PILL, P_NEW_PILL),
    ('  and its four variants go', P_OLD_PILLV, P_NEW_PILLV),
    ('the tile keeps only what a card is not', P_OLD_STAT, P_NEW_STAT),
    ('  its figure takes the ink token', P_OLD_STATV, P_NEW_STATV),
    ('  its label too', P_OLD_STATL, P_NEW_STATL),
    ('  and the warn variant', P_OLD_STATW, P_NEW_STATW),
]


# ---------------------------------------------------------------------------
# 4. the mobile card view base already owns
# ---------------------------------------------------------------------------
# The page hand-rolled it: thead hidden, cells to blocks, a card per row, and
# `content: attr(data-label)` before every figure. base has done all of that
# for .alv-table since the standard landed, and does MORE - td:first-child
# becomes a heading strip with no label, which is exactly what .pd-col-name
# was doing by hand.
#
# Ten rules go. What stays is what base cannot know: the two-up summary grid,
# the "Every payment" caption on a cell that has no data-label to borrow, and
# the nine rules that UNDO the card treatment for the nested detail grid.
#
# Those nine are the delicate part. base writes `border`, `padding` and
# `text-align` on .alv-table td with !important, so an undo rule that merely
# out-specifies loses. They are retargeted at .alv-table, given the specificity
# to beat td:first-child, and marked !important where base is - and then the
# result is RENDERED at 390px rather than reasoned about, because "which
# !important wins" is not a question worth answering from memory.
MOBILE_NEW = """@media (max-width: 768px) {
    .report-container { padding: 10px; }
    .report-content { width: 100%; padding: 16px; }
    .report-title-main { font-size: 1.25rem; }
    .report-title-sub { font-size: 0.9rem; }
    .pd-summary { grid-template-columns: repeat(2, 1fr); }

    /* Cards, not a squeezed table: nine numeric columns are unreadable at
       phone width, and horizontal scrolling hides exactly the column that
       matters. base does the whole card treatment for .alv-table - the hidden
       head, the block cells, the per-row card, the data-label before each
       figure, and the first cell as a heading strip. Ten rules that used to
       live here said the same thing about .pd-table. */

    /* The count sits under the tenant name. base makes the first cell a
       block, so the old flex-basis:100% no longer applies to anything. */
    .alv-table tbody td.pd-col-name .pd-count { display: block; }

    /* This cell has no data-label to borrow, so it needs its caption named.
       Must out-specify base's own td::before. */
    .alv-table tbody td.pd-col-toggle::before { content: "Every payment"; }

    /* UNDO THE CARD TREATMENT FOR THE NESTED DETAIL GRID. Everything base
       writes for .alv-table td reaches these cells too - so without this the
       four columns stack into four right-aligned lines with their headers
       orphaned above them. It stays a real table: four short columns fit a
       phone, and one row per payment is the point of it.

       !important throughout, because base uses it on border, padding and
       text-align, and specificity alone does not beat that. */
    .alv-table tbody tr.pd-detail td {
        display: block;
        padding: 0 !important;
        font-size: inherit;
        font-weight: normal;
    }
    .alv-table tbody tr.pd-detail td::before { content: none; }
    .pd-detail .pd-detail-table { display: table; width: 100%; font-size: 0.78rem; }
    .pd-detail .pd-detail-table thead { display: table-header-group; }
    .pd-detail .pd-detail-table tbody { display: table-row-group; }
    .pd-detail .pd-detail-table tr { display: table-row; }
    .pd-detail .pd-detail-table th,
    .pd-detail .pd-detail-table td {
        display: table-cell !important;
        width: auto;
        padding: 4px 5px !important;
        text-align: left !important;
        border-bottom: 1px solid var(--alv-line-soft) !important;
    }
    .pd-detail .pd-detail-table th.pd-num,
    .pd-detail .pd-detail-table td.pd-num { text-align: right !important; }
    .pd-detail .pd-detail-table td::before,
    .pd-detail .pd-detail-table th::before { content: none; }
    .pd-detail-inner { padding: 12px 10px 14px 10px; text-align: left; }
}"""


def replace_media_block(text, new_block):
    """Replace the page's one mobile media query, located by brace balance.

    A 78-line literal anchor would have to match byte for byte, and this block
    is the part of the file most likely to have been touched. Finding it by its
    opening line and counting braces is more robust - and the count is asserted
    to be exactly one, which is the property that mattered about the literal.
    """
    opens = [m for m in re.finditer(r'@media \(max-width: 768px\) \{', text)]
    if len(opens) != 1:
        sys.exit('! expected exactly one mobile media query, found %d'
                 % len(opens))
    i = opens[0].end()
    depth = 1
    while depth and i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    if depth:
        sys.exit('! the mobile media query never closes')
    return text[:opens[0].start()] + new_block + text[i:], text[opens[0].start():i]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:220]))
    return text.replace(old, new, 1)


def many(text, old, new, want, what):
    n = text.count(old)
    if n != want:
        sys.exit('! %s matched %d times, expected %d:\n%s'
                 % (what, n, want, old[:200]))
    return text.replace(old, new)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)      # NOT re.S - nor is Django

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def rules(src):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'@media[^{]*\{', '', css)
    out = {}
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        for sel in m.group(1).split(','):
            sel = ' '.join(sel.split())
            if sel:
                out.setdefault(sel, []).append(' '.join(m.group(2).split()))
    return out


def main():
    for p in (VIEW, BASE, PAGE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    vs, bs, pg = read(VIEW), read(BASE), read(PAGE)
    pg0 = pg

    if SENTINEL in vs:
        print('  payment behaviour migration     already applied')
        print('\n  0 file(s) changed')
        return
    if 'alv-pill-good' not in bs:
        sys.exit('! base has no .alv-pill family - wrong tree?')

    for name, old, new in EDITS_VIEW:
        vs = one(vs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)
    pg = many(pg, P_OLD_TILES, P_NEW_TILES, 3, 'the three plain tiles')
    pg, _mobile_was = replace_media_block(pg, MOBILE_NEW)

    # ---- self-check BEFORE anything is written ----------------------------
    bad = []
    try:
        tree = ast.parse(vs)
    except SyntaxError as exc:
        sys.exit('! the patched tenants.py does not parse: %s' % exc)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    _view = next((n for n in fns if 'payment' in n), None)
    if _view is None:
        bad.append('the payment-days view is gone')
    else:
        _dec = [ast.unparse(d) for d in fns[_view].decorator_list]
        if not any('login_required' in d for d in _dec):
            bad.append('%s lost @login_required' % _view)
        _src = nocomment_py(ast.get_source_segment(vs, fns[_view]))
        if 'BAND_PILL' not in _src:
            bad.append('the band-to-pill map is not in the view')
        if "'band_pill'" not in _src:
            bad.append('the rows do not carry band_pill')
        # EVERY band the view can produce must have a pill, asked of the tree
        # rather than of the text - a band added later with no pill would
        # render an unstyled chip and nothing would say so.
        _bands = {c.value for n in ast.walk(fns[_view])
                  for c in ast.walk(n)
                  if isinstance(c, ast.Constant) and isinstance(c.value, str)
                  and c.value in ('ontime', 'slight', 'late', 'unknown')}
        _mapped = re.findall(r"'(\w+)':\s*'alv-pill-", _src)
        if _bands - set(_mapped):
            bad.append('bands with no pill: %s' % sorted(_bands - set(_mapped)))

    _P, _bc = rules(pg), nocomment_html(bs)
    _pc = nocomment_html(pg)

    for _dead in ('.pd-table', '.pd-table thead th', '.pd-table tbody td',
                  '.pd-table-wrap', '.pd-badge', '.pd-badge-ontime',
                  '.pd-badge-slight', '.pd-badge-late', '.pd-badge-unknown',
                  'tr.pd-band-slight td', 'tr.pd-band-late td'):
        if _dead in _P:
            bad.append('%s is still defined on the page' % _dead)
    if '.pd-detail-table' not in _P:
        bad.append('the nested detail grid lost its rules - it is deliberately '
                   'NOT migrated, so it still needs them')

    if _pc.count('class="alv-table"') + _pc.count('class="alv-table pd-table-compact"') != 2:
        bad.append('both tables should be .alv-table')
    if _pc.count('table-container') != 2:
        bad.append('both tables should be in a container (%d)'
                   % _pc.count('table-container'))
    if 'overflow-x: auto' in _pc:
        bad.append('a scrolling wrapper survives')
    if 'pd-badge' in _pc:
        bad.append('a page badge survives in the markup')
    if _pc.count('alv-card pd-stat') != 4:
        bad.append('the four tiles are not cards (%d)'
                   % _pc.count('alv-card pd-stat'))
    for _cls in ('alv-pill-good', 'alv-pill-attn', 'alv-pill-bad',
                 'alv-pill-neutral'):
        if not re.search(r'\.%s\s*[,{ ]' % _cls, _bc):
            bad.append('%s is not defined in base' % _cls)

    # The edge marker keeps all four bands, and every one on a token.
    for _b in ('ontime', 'slight', 'late', 'unknown'):
        _r = _P.get('.pd-row.pd-band-%s' % _b, [])
        if not _r:
            bad.append('the %s edge marker is gone' % _b)
        elif re.search(r'#[0-9a-fA-F]{3,8}', ' '.join(_r)):
            bad.append('the %s edge marker still carries a literal' % _b)

    for _sel in ('.pd-stat', '.pd-stat-value', '.pd-stat-label',
                 '.pd-stat-warn'):
        _b = ' '.join(_P.get(_sel, []))
        if re.search(r'#[0-9a-fA-F]{3,8}\b', _b):
            bad.append('%s still carries a literal: %s' % (_sel, _b[:60]))
    if 'background' in ' '.join(_P.get('.pd-stat', [])):
        bad.append('.pd-stat still paints its own surface - that is .alv-card')

    _before = len(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocomment_html(pg0)))
    _after = len(re.findall(r'#[0-9a-fA-F]{3,8}\b', _pc))
    if _after >= _before - 17:
        bad.append('the round retired %d literals, expected at least 18'
                   % (_before - _after))

    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pg, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('page CSS braces do not balance')
    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)
    for _l in pg.split('\n'):
        if _l.count('{#') != _l.count('#}'):
            bad.append('a {# #} comment spans lines, which Django renders')
            break
    _want = {'div': 0, 'table': 0, 'tr': 0, 'td': 0, 'span': 0}
    for tag, w in _want.items():
        _o = (len(re.findall(r'<%s\b' % tag, pg))
              - len(re.findall(r'<%s\b' % tag, pg0)))
        _c = (len(re.findall(r'</%s\s*>' % tag, pg))
              - len(re.findall(r'</%s\s*>' % tag, pg0)))
        if _o != _c or _o != w:
            bad.append('the edit changed <%s> counts by %d/%d, expected %d'
                       % (tag, _o, _c, w))
    # THE MOBILE BLOCK. What base owns must be gone; what base cannot know
    # must remain.
    for _gone in ('.pd-table thead { display: none; }',
                  'content: attr(data-label)',
                  '.pd-table tbody td:last-child'):
        if _gone in _mobile_was and _gone in pg:
            bad.append('the mobile block still hand-rolls %r' % _gone[:40])
    for _kept in ('Every payment', 'pd-detail-table', 'repeat(2, 1fr)'):
        if _kept not in pg:
            bad.append('the mobile block lost %r, which base cannot supply'
                       % _kept)
    _det = re.search(r'\.pd-detail \.pd-detail-table th,\s*'
                     r'\.pd-detail \.pd-detail-table td \{([^}]*)\}', pg)
    if not _det:
        bad.append('the detail grid has no undo rule')
    else:
        for _p in ('display', 'padding', 'text-align'):
            if ('%s:' % _p) in _det.group(1) and '!important' not in \
                    _det.group(1).split('%s:' % _p)[1].split(';')[0]:
                bad.append('the detail grid undoes %s without !important, and '
                           'base writes it with one' % _p)

    if 'navy #2c3e50 band' in _pc:
        bad.append('CONTROL: CSS comments are not being stripped')

    if bad:
        sys.exit('! payment-days self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_VIEW + EDITS_PAGE:
        print('  %s' % name)
    print('  and the other three tiles')

    if not CHECK:
        for path, out in ((VIEW, vs), (PAGE, pg)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
