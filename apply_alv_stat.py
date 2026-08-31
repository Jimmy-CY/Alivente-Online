#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One stat tile, and a verdict that stops saying the same thing twice.

FOUR SCREENS BUILT THE SAME TILE FOUR TIMES.

    tenant_payment_days.html    .pd-stat        4 tiles  borrows .alv-card
    fsr.html  (Issues Analysis) .ia-kpi         5 tiles  own box, page tokens
    financial_indicators.html   .summary-stat   3 tiles  own box, Bootstrap
    vacancy_management.html     .summary-stat   3 tiles  a copy of the above

Fifteen tiles, four implementations, and the last two are near enough the same
bytes in two files. When Tenant Payment Behaviour shipped on 29 Aug its own CSS
said why it stopped short:

    base has no stat-tile component, and one page is not enough to invent one

Four is. This round invents it.

A VERDICT COLOURS THE FIGURE, NOT THE TILE.

The four disagreed about the one thing that matters. Financial Indicators and
Vacancy Management wash the whole tile green, amber or red. Payment Behaviour
washes it amber when a count is non-zero. Issues Analysis colours the NUMBER
and leaves the tile alone.

The wash loses. A tile that reads

    3
    NEEDS IMPROVEMENT

already says which verdict it is, in words, directly under the figure. Painting
the box behind it red says it a second time and spends the loudest signal on
the page saying nothing new - which is the objection the tables spent nine
rounds settling, and the same objection about to be put to the P&L rows and to
the comment tints. The figure is the part a reader actually looks at, so the
figure is where the colour goes. `.alv-stat-good / -attn / -bad` take base's
own verdict tokens, so a tile and the pill in the table below it cannot drift.

THE TILE BRINGS ITS OWN SURFACE. Payment Behaviour stacked `.alv-card` under
`.pd-stat` to get a border, and needed a paragraph of comment explaining what
it was subtracting back out. Three of the four already brought their own.

WHAT THIS ROUND DOES NOT DO. It migrates ONE screen - Payment Behaviour, the
smallest, and the one already known good. The Issues Analysis strip and the two
Financials modals are the 2.B and 2.C rounds, which open those files for their
tables anyway; migrating their tiles now would mean opening them twice. Nor
does it ship a modal density (`.alv-stats-sm`): nothing this round renders is
in a dialog, and CSS nothing uses is CSS nobody has looked at.

SECTION 3 IS A CHANGE TO AN EXISTING SUITE - section 4b of the plan.
test_payment_days.py hardcodes `.pd-summary`, `.pd-stat` and `.pd-stat-warn` in
its fixture and asserts the tile IS a card. That expectation is not wrong, it
is superseded - so it MOVES, with its polarity reversed, and reads base's rules
instead of the page's. Two of its checks would otherwise have gone on passing
while reading a selector that no longer exists anywhere, which is precisely a
control that cannot fail.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_payment_days.html')
SUITE = os.path.join(ROOT, 'test_payment_days.py')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_alvstat'

SENTINEL = '.alv-stats {'

# A tile, and NOT the .alv-stats wrapper that holds them. `class="alv-stat`
# alone counts the wrapper too, which is how a four-tile page reports five.
TILE_RE = re.compile(r'class="alv-stat[" ]')

# ---------------------------------------------------------------------------
# 1. base gains the component
# ---------------------------------------------------------------------------
B_STAT_CSS = """      /* ================================================================
         .alv-stat - a figure and the words for it        --alv-stat-std

         Four screens built this four times before base got it: .pd-stat
         on Tenant Payment Behaviour, .ia-kpi in the Issues Analysis
         modal, and .summary-stat twice over in Financial Indicators and
         Vacancy Management, near enough the same bytes in two files.

         A VERDICT COLOURS THE FIGURE, NOT THE TILE. Two of those four
         washed the whole box green, amber or red - which repeats, in
         the loudest way available, what the label under the figure has
         already said in words. The figure is the part a reader looks
         at, so the figure is where the colour goes, and it comes from
         the same tokens as .alv-pill so that a tile and the pill in the
         table below it cannot part company.

         The tile brings its OWN surface. Stacking .alv-card underneath
         one to borrow a border is what made .pd-stat need a paragraph
         explaining what it was subtracting back out.
         ================================================================ */
      .alv-stats {
        display: grid;
        /* Three tiles, four, or the five in the Issues Analysis strip -
           one grid, set per page, rather than a second class each time.
           Deliberately a DEFAULTED custom property: no page has to
           define it, and nothing in base defines it either. */
        grid-template-columns: repeat(var(--alv-stats-cols, 4), 1fr);
        gap: 12px;
        margin-bottom: 20px;
      }
      .alv-stat {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        border-radius: 6px;
        padding: 14px 16px;
        text-align: center;
        /* A long label must not widen its own column and starve the rest. */
        min-width: 0;
      }
      .alv-stat-value {
        font-family: var(--alv-font-ui);
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.1;
        color: var(--alv-ink-strong);
        /* Figures side by side line up only if the digits are one width. */
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
      }
      .alv-stat-label {
        font-size: 0.78rem;
        color: var(--alv-ink-soft);
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-top: 4px;
      }
      .alv-stat-good .alv-stat-value { color: var(--alv-good); }
      .alv-stat-attn .alv-stat-value { color: var(--alv-warn); }
      .alv-stat-bad  .alv-stat-value { color: var(--alv-bad); }

      @media (max-width: 768px) {
        /* Four figures across a phone is four figures nobody can read. */
        .alv-stats { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .alv-stat { padding: 12px 10px; }
        .alv-stat-value { font-size: 1.4rem; }
      }
"""

B_TAG_HEAD = """      /* ================================================================
         .alv-tag - a CATEGORY, not a status"""

B_OLD_CARD = ("""      .alv-card > .table-container { border: 0; border-radius: 0; }

""" + B_TAG_HEAD)

B_NEW_CARD = ("""      .alv-card > .table-container { border: 0; border-radius: 0; }

""" + B_STAT_CSS + """
""" + B_TAG_HEAD)

B_OLD_PRINT = (
    """        .alv-card { border-color: #9aa5ab !important; break-inside: avoid; }""")

B_NEW_PRINT = """        /* The tile stopped borrowing .alv-card for a surface, so it
           stopped borrowing its paper treatment with it. */
        .alv-card,
        .alv-stat { border-color: #9aa5ab !important; break-inside: avoid; }"""

# ---------------------------------------------------------------------------
# 2. the page hands its tiles over
# ---------------------------------------------------------------------------
P_OLD_MARKUP = """    <div class="pd-summary">
      <div class="alv-card pd-stat">
        <div class="pd-stat-value">{{ summary.payments_measured }}</div>
        <div class="pd-stat-label">payments measured</div>
      </div>
      <div class="alv-card pd-stat">
        <div class="pd-stat-value">{{ summary.tenants_measured }}</div>
        <div class="pd-stat-label">tenants with data</div>
      </div>
      <div class="alv-card pd-stat">
        <div class="pd-stat-value">{{ summary.portfolio_avg|floatformat:1 }}</div>
        <div class="pd-stat-label">average days to pay</div>
      </div>
      <div class="alv-card pd-stat {% if summary.flagged %}pd-stat-warn{% endif %}">
        <div class="pd-stat-value">{{ summary.flagged }}</div>
        <div class="pd-stat-label">flagged slow</div>
      </div>
    </div>"""

P_NEW_MARKUP = """    <div class="alv-stats">
      <div class="alv-stat">
        <div class="alv-stat-value">{{ summary.payments_measured }}</div>
        <div class="alv-stat-label">payments measured</div>
      </div>
      <div class="alv-stat">
        <div class="alv-stat-value">{{ summary.tenants_measured }}</div>
        <div class="alv-stat-label">tenants with data</div>
      </div>
      <div class="alv-stat">
        <div class="alv-stat-value">{{ summary.portfolio_avg|floatformat:1 }}</div>
        <div class="alv-stat-label">average days to pay</div>
      </div>
      <div class="alv-stat {% if summary.flagged %}alv-stat-attn{% endif %}">
        <div class="alv-stat-value">{{ summary.flagged }}</div>
        <div class="alv-stat-label">flagged slow</div>
      </div>
    </div>"""

P_OLD_CSS = """/* ---- summary strip ---- */
.pd-summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}
/* The surface, border and radius come from .alv-card. What stays here is what
   makes a STAT TILE rather than a card - the centring, and the big figure over
   a small label below. base has no stat-tile component, and one page is not
   enough to invent one; that is the restraint that kept the ageing scale
   waiting until a screen genuinely needed it. */
.pd-stat {
    padding: 14px 16px;
    text-align: center;
    display: block;
}
.pd-stat-value { font-size: 1.7rem; font-weight: 700; color: var(--alv-ink-strong); line-height: 1.1; }
.pd-stat-label {
    font-size: 0.78rem;
    color: var(--alv-ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-top: 4px;
}
.pd-stat-warn { background: var(--alv-warn-soft); border-color: var(--alv-warn); }
.pd-stat-warn .pd-stat-value { color: var(--alv-warn); }

/* ---- toolbar ---- */"""

P_NEW_CSS = """/* The summary strip is base's .alv-stats and .alv-stat now, phone grid and
   all. What used to live here was the fourth copy of a tile four screens had
   each built for themselves. The amber WASH on the flagged tile went with it:
   the figure goes amber, the box does not, because the label directly under
   the figure already says which tile is the alarm. */

/* ---- toolbar ---- */"""

P_OLD_MOBILE = """    .report-title-sub { font-size: 0.9rem; }
    .pd-summary { grid-template-columns: repeat(2, 1fr); }
"""

P_NEW_MOBILE = """    .report-title-sub { font-size: 0.9rem; }
"""

# ---------------------------------------------------------------------------
# 3. section 4b - the existing suite's expectation MOVES
# ---------------------------------------------------------------------------
S_OLD_RULES = """P = rules(PG)"""

S_NEW_RULES = """P = rules(PG)
# base's rules too, since 30 Aug: the tile is base's component now, so the
# checks that used to read the page's copy have to read the real one.
B = rules(BS)"""

S_OLD_TILES = """check('the four tiles are cards', PC.count('alv-card pd-stat') == 4)
check('  and .pd-stat no longer paints its own surface',
      'background' not in ' '.join(P.get('.pd-stat', [])))
for _sel in ('.pd-stat', '.pd-stat-value', '.pd-stat-label', '.pd-stat-warn'):
    check('%s carries no literal colour' % _sel,
          not re.search(r'#[0-9a-fA-F]{3,8}\\b', ' '.join(P.get(_sel, []))))"""

S_NEW_TILES = """# SUPERSEDED 30 Aug by the .alv-stat round, and the polarity is REVERSED.
# These four checks asserted the tile borrowed .alv-card for a surface and
# painted none of its own. base owns the whole tile now, so the expectation
# MOVES to base rather than being deleted. Note that reading P.get() for a
# selector the page no longer defines returns [] and passes for free, which is
# a control that cannot fail - hence bool(B.get(...)) below.
#
# The regex counts TILES. `class="alv-stat` alone also matches the .alv-stats
# wrapper, which is how a four-tile page reports five.
_tiles = len(re.findall(r'class="alv-stat[" ]', PC))
check('the four tiles are .alv-stat', _tiles == 4, '%d' % _tiles)
check('  and none of them borrows .alv-card for a surface',
      'alv-card' not in PC)
check('  the page defines no tile CSS of its own',
      not [s for s in P if 'pd-stat' in s or 'pd-summary' in s])
check('  base paints the tile instead',
      'background' in ' '.join(B.get('.alv-stat', [])))
# The ONE literal that is house style: #9aa5ab is the grey every .alv-card
# prints with, and the tile joins it now that it no longer borrows the card.
# rules() flattens media queries, so the print rule arrives in this dict -
# name the exception rather than widen the pattern and catch nothing.
_PRINT_GREY = '#9aa5ab'
check('the tile prints in the same grey as a card',
      _PRINT_GREY in ' '.join(B.get('.alv-stat', [])))
for _sel in ('.alv-stats', '.alv-stat', '.alv-stat-value', '.alv-stat-label'):
    _decl = ' '.join(B.get(_sel, [])).replace(_PRINT_GREY, '')
    check('base defines %s, on tokens only' % _sel,
          bool(B.get(_sel))
          and not re.search(r'#[0-9a-fA-F]{3,8}\\b', _decl), _decl[:60])"""

S_OLD_FIX = """<div class="pd-summary">
  <div class="alv-card pd-stat"><div class="pd-stat-value">9</div>
    <div class="pd-stat-label">payments measured</div></div>
  <div class="alv-card pd-stat pd-stat-warn"><div class="pd-stat-value">2</div>
    <div class="pd-stat-label">flagged slow</div></div>
</div>"""

S_NEW_FIX = """<div class="alv-stats">
  <div class="alv-stat"><div class="alv-stat-value">9</div>
    <div class="alv-stat-label">payments measured</div></div>
  <div class="alv-stat alv-stat-attn"><div class="alv-stat-value">2</div>
    <div class="alv-stat-label">flagged slow</div></div>
</div>"""

S_OLD_PROBE = """        statBorder: getComputedStyle(q('.pd-stat')).borderTopWidth,
        summaryCols: getComputedStyle(q('.pd-summary')).gridTemplateColumns.split(' ').length,"""

S_NEW_PROBE = """        statBorder: getComputedStyle(q('.alv-stat')).borderTopWidth,
        summaryCols: getComputedStyle(q('.alv-stats')).gridTemplateColumns.split(' ').length,
        plainBg:    getComputedStyle(q('.alv-stat')).backgroundColor,
        attnBg:     getComputedStyle(q('.alv-stat-attn')).backgroundColor,
        plainValue: getComputedStyle(q('.alv-stat .alv-stat-value')).color,
        attnValue:  getComputedStyle(q('.alv-stat-attn .alv-stat-value')).color,"""

S_OLD_TAIL = """    check('the tile has a card border', D['statBorder'] == '1px',
          D['statBorder'])"""

S_NEW_TAIL = """    check('the tile brings its own border', D['statBorder'] == '1px',
          D['statBorder'])
    # THE DECISION OF 30 AUG, PUT TO THE BROWSER RATHER THAN TO MEMORY. Two of
    # the four implementations .alv-stat replaces washed the whole tile by
    # verdict. If that wash ever comes back, these two part company.
    check('a verdict does NOT wash the tile',
          D['attnBg'] == D['plainBg'],
          '%s vs %s' % (D['attnBg'], D['plainBg']))
    check('  it colours the figure instead',
          D['attnValue'] != D['plainValue'],
          '%s vs %s' % (D['attnValue'], D['plainValue']))"""

EDITS_BASE = [
    ('base gains .alv-stats / .alv-stat', B_OLD_CARD, B_NEW_CARD),
    ('  and the tile keeps its print treatment', B_OLD_PRINT, B_NEW_PRINT),
]
EDITS_PAGE = [
    ('the four tiles move onto the component', P_OLD_MARKUP, P_NEW_MARKUP),
    ('  the page drops its own tile CSS', P_OLD_CSS, P_NEW_CSS),
    ('  and its own two-up phone grid', P_OLD_MOBILE, P_NEW_MOBILE),
]
EDITS_SUITE = [
    ('4b: the suite reads base as well as the page', S_OLD_RULES, S_NEW_RULES),
    ('  the tile expectation moves, reversed', S_OLD_TILES, S_NEW_TILES),
    ('  the fixture uses the component', S_OLD_FIX, S_NEW_FIX),
    ('  the probe asks about the wash', S_OLD_PROBE, S_NEW_PROBE),
    ('  and a verdict is asserted not to wash', S_OLD_TAIL, S_NEW_TAIL),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:220]))
    return text.replace(old, new, 1)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S. Django's {# #} does not span lines, and a stripper more
    # permissive than the lexer it models certifies the faults it exists to
    # catch.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def css_of(text):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))


def main():
    for p in (BASE, PAGE, SUITE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    bs, pg, su = read(BASE), read(PAGE), read(SUITE)
    bs0, pg0, su0 = bs, pg, su

    if SENTINEL in bs:
        print('  .alv-stat                      already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_BASE:
        bs = one(bs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)
    for name, old, new in EDITS_SUITE:
        su = one(su, old, new, name)

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    bc, pc = nocomment_html(bs), nocomment_html(pg)
    blk = re.sub(r'/\*.*?\*/', '', B_STAT_CSS, flags=re.S)

    # -- base defines the component, once each, on tokens ------------------
    # ONCE, and as written. Counting a bare selector would count the phone
    # grid and the print rule as duplicates; the block is the unit.
    if bc.count(blk.strip()) != 1:
        bad.append('the component block appears %d times in base, expected 1'
                   % bc.count(blk.strip()))
    for _sel in ('.alv-stats', '.alv-stat', '.alv-stat-value',
                 '.alv-stat-label'):
        if not re.search(r'%s\s*\{' % re.escape(_sel), bc):
            bad.append('base never defines %s' % _sel)
    for _v in ('good', 'attn', 'bad'):
        if not re.search(r'\.alv-stat-%s\s+\.alv-stat-value' % _v, bc):
            bad.append('base has no .alv-stat-%s rule' % _v)
    if re.search(r'#[0-9a-fA-F]{3,8}\b', blk):
        bad.append('the .alv-stat block carries a literal colour: %s'
                   % re.findall(r'#[0-9a-fA-F]{3,8}\b', blk))
    for _tok in ('--alv-paper', '--alv-line', '--alv-ink-strong',
                 '--alv-ink-soft', '--alv-good', '--alv-warn', '--alv-bad'):
        if _tok not in blk:
            bad.append('the block does not use %s' % _tok)
    # A TOKEN MUST BE DEFINED, NOT MERELY REFERENCED - `visually-hidden` was
    # referenced, defined nowhere, and would have rendered as visible text.
    # Only vars used WITHOUT a fallback are checked: --alv-stats-cols is the
    # component's parameter and is deliberately defined by nobody.
    for _tok in sorted(set(re.findall(r'var\((--alv-[a-z0-9-]+)\s*\)', blk))):
        if '%s:' % _tok not in bc:
            bad.append('%s is referenced and never defined' % _tok)
    if 'repeat(2, 1fr)' not in blk:
        bad.append('base did not gain the two-up phone grid')
    if '.alv-stat { border-color: #9aa5ab !important' not in bc:
        bad.append('the tile lost its print treatment')

    # -- the page hands everything over ------------------------------------
    for _dead in ('pd-summary', 'pd-stat'):
        if _dead in pg:
            bad.append('%s survives on the page' % _dead)
    _tiles = len(TILE_RE.findall(pc))
    if _tiles != 4:
        bad.append('the page carries %d tiles, expected 4' % _tiles)
    if pc.count('alv-stat-value') != 4 or pc.count('alv-stat-label') != 4:
        bad.append('a tile is missing its figure or its label (%d / %d)'
                   % (pc.count('alv-stat-value'), pc.count('alv-stat-label')))
    if pc.count('class="alv-stats"') != 1:
        bad.append('the tiles are not in exactly one .alv-stats grid')
    if 'alv-stat-attn' not in pc:
        bad.append('the flagged tile lost its verdict')
    if 'alv-card' in pc:
        bad.append('a tile still borrows .alv-card')
    # The wash is the point of the round. It must be gone from the page, and
    # must not have reappeared as a background on a verdict rule in base.
    if 'alv-warn-soft' in pc:
        bad.append('the amber wash survives on the page')
    if re.search(r'\.alv-stat-(good|attn|bad)[^{]*\{[^}]*background', bc):
        bad.append('a verdict washes the tile in base')

    # -- structure ---------------------------------------------------------
    for _name, _txt in (('base', css_of(bs)), ('page', css_of(pg))):
        if _txt.count('{') != _txt.count('}'):
            bad.append('%s CSS braces do not balance' % _name)
    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)
    for _l in pg.split('\n'):
        if _l.count('{#') != _l.count('#}'):
            bad.append('a {# #} comment spans lines, which Django renders')
            break
    # BALANCE AS A DELTA. This template need not balance as raw text - it has
    # {% if %} branches - so what must hold is that THIS EDIT opens and closes
    # the same number of everything, and in fact adds none of either.
    for tag in ('div', 'span', 'td', 'th'):
        _o = (len(re.findall(r'<%s\b' % tag, pg))
              - len(re.findall(r'<%s\b' % tag, pg0)))
        _c = (len(re.findall(r'</%s\s*>' % tag, pg))
              - len(re.findall(r'</%s\s*>' % tag, pg0)))
        if _o != _c or _o != 0:
            bad.append('the edit changes <%s> counts by %d open / %d close'
                       % (tag, _o, _c))
    if len(re.findall(r'<style', bs)) != len(re.findall(r'<style', bs0)):
        bad.append('base gained or lost a <style> element')

    # -- the suite still parses, and still says at least as much -----------
    try:
        compile(su, 'test_payment_days.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched suite does not parse: %s' % exc)
    _was, _now = su0.count('check('), su.count('check(')
    if _now < _was:
        bad.append('the suite lost %d check() calls - an expectation was '
                   'DELETED rather than moved' % (_was - _now))
    # The suite may still NAME pd-stat - the moved check looks for exactly
    # that selector on the page, and the comment explains why. What must be
    # gone is the suite ASKING the browser or the page about it.
    for _stale in ("q('.pd-stat')", "q('.pd-summary')", 'alv-card pd-stat',
                   'class="pd-stat', 'class="alv-card pd-stat'):
        if _stale in su:
            bad.append('the suite still reads %s' % _stale)

    # -- CONTROL on the stripper -------------------------------------------
    # This round's own prose in base names .pd-stat, the class it deletes. If
    # comments were not being stripped, a "survives" check would be reading
    # prose, and this control fires first.
    if '.pd-stat' not in bs:
        bad.append('CONTROL: the round lost the prose it strips against')
    if '.pd-stat' in bc:
        bad.append('CONTROL: comments are not being stripped from base')

    if bad:
        sys.exit('! .alv-stat self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_BASE + EDITS_PAGE + EDITS_SUITE:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((BASE, bs), (PAGE, pg), (SUITE, su)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
