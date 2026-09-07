"""test_ia_drill.py - C3: the drill-down table is base's, and it still works.

    python test_ia_drill.py

Run from the repo root, after apply_ia_drill.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 DRIVES A BROWSER, because every claim this round makes is about
    what RENDERS, not about which class name is in the file. A table can
    carry `alv-table` and still come out unstyled if base never defined the
    rule, and a heading can carry `position: sticky` and still not pin if its
    scrolling ancestor is not what you thought.

    So the drill-down is BUILT the way drillRows() builds it, dropped into a
    real .ia-drill-body, scrolled, and measured.

  * THE CONTROL IS THE OTHER HALF. Every rendered claim is taken again from
    .bak_iadrill, where the OLD table must produce the OLD answer. Without
    that, "the heading pins" would pass just as well on a probe that never
    scrolled, and "the links are accent-coloured" on a page with no links.

  * SECTION 3 IS THE ONE THE FIRST RENDER CAUGHT. `table.ia-tbl a.ia-link`
    was anchored to the class this round renames, so the migration silently
    dropped every issue link back to Bootstrap blue. It is measured as a
    COMPUTED COLOUR against base's own --alv-accent-ink, not as a selector.

  * SECTION 4 asserts what the round did NOT do: the overlay is still
    hand-rolled, the script's hooks all survive, and the sticky shadow is
    absent BY DECISION.

WHY THE SHADOW IS ABSENT. base toggles `.is-stuck` from an IntersectionObserver
that runs once at page load, over `.alv-table thead`, with the VIEWPORT as
root. This table is built long after load and scrolls inside the dialog, so
that observer can never see it. Rendered on and off, the difference is one
faint shadow, and the dialog already has an edge, a title bar and a shadow of
its own. Left out deliberately - and asserted here so it reads as a decision
rather than as base's table misbehaving in a dialog.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
IA = os.path.join(T, 'fsr.html')
BASE = os.path.join(T, 'base.html')
BAK = IA + '.bak_iadrill'
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(src):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))


def js_of(src):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))


def nocomment(t):
    """Comments out of BOTH kinds of block, because a note that quotes the
       selector it replaced is prose and must not be read as code."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, t, flags=re.S)


for _p in (IA, BASE):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)
if not os.path.exists(BAK):
    sys.exit('! no fsr.html.bak_iadrill - run apply_ia_drill.py first.')

F, WAS = read(IA), read(BAK)
FC, WC = nocomment(F), nocomment(WAS)
BASE_CSS = css_of(read(BASE))
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

# ===========================================================================
head('1. the text: 13 rules deleted, 2 back rescoped, 11 net gone')
# ===========================================================================
check('no ia-tbl selector survives anywhere',
      'ia-tbl' not in FC, '')
# RULES, NOT OCCURRENCES. The first draft counted the STRING and demanded
# 13, and got 16: the phone block groups four selectors in one rule, and C1's
# note names the selector in prose. Two different units wearing one number -
# the same mistake as counting characters and calling them bytes. Count rule
# OPENINGS, on comment-stripped text.
_RULE = re.compile(r'(?m)^\s*table\.ia-tbl[^{\n]*\{')
_EMPTY = re.compile(r'(?m)^\s*\.ia-empty-row\s*\{')
# THE ARITHMETIC, stated once and checked rather than repeated. 12 rules
# carry the table.ia-tbl prefix - 7 on the desktop and 5 in the phone block -
# and .ia-empty-row makes 13 deleted. TWO of the twelve come back rescoped
# (the issue link and its hover), so ELEVEN are net gone, every one of them
# something base already does.
check('CONTROL: there were 12 table.ia-tbl RULES before',
      len(_RULE.findall(nocomment(WAS))) == 12,
      '%d rules, %d string occurrences'
      % (len(_RULE.findall(nocomment(WAS))),
         len(re.findall(r'table\.ia-tbl', nocomment(WAS)))))
check('  plus .ia-empty-row, so 13 deleted in total',
      len(_EMPTY.findall(nocomment(WAS))) == 1)
check('  and none of the 13 survives',
      not _RULE.findall(nocomment(F)) and not _EMPTY.findall(nocomment(F)))
check('  with exactly 2 coming back rescoped, so 11 net gone',
      css_of(nocomment(F)).count('.ia-drill-body .alv-table a.ia-link') == 2)
# C1's note still NAMES the old selector, and that is correct - it is the
# record of what the palette round found. What it must not do is point at it
# in the present tense, so the round amended it.
check('C1\'s note was kept pointing somewhere real',
      'AMENDED 5 Sep' in F and 'no longer exist' in F)
check('drillRows builds base\'s table now',
      'class="table alv-table"' in js_of(FC))
check('CONTROL: it built ia-tbl before',
      'class="ia-tbl"' in js_of(WC))

# THE RESCOPE, not a deletion. This is the half that would have shipped
# broken: the link rule was anchored to the class the round renames.
check('the issue-link rule came back, rescoped to the drill body',
      '.ia-drill-body .alv-table a.ia-link{' in css_of(FC))
check('  with its hover', css_of(FC).count('a.ia-link') == 2,
      str(css_of(FC).count('a.ia-link')))
check('CONTROL: it WAS anchored to the old table class',
      'table.ia-tbl a.ia-link{' in css_of(WC))

check('the empty state is base\'s', 'alv-empty-title' in js_of(FC))
check('  and the hand-rolled row went', 'ia-empty-row' not in FC)
check('CONTROL: it was hand-rolled before', 'ia-empty-row' in WC)

# base has to define what the round leans on, or this is a rename onto
# nothing and every check below passes on unstyled rows.
for need in ('.alv-table thead th', '.alv-table tbody td', '.alv-empty',
             '.alv-empty-title', '.alv-empty-hint', '.alv-table .num'):
    check('base defines %s' % need, need in BASE_CSS)
check('base\'s table heading is sticky - the round\'s whole premise',
      re.search(r'\.alv-table thead th\s*\{[^}]*position:\s*sticky',
                BASE_CSS) is not None)

# ===========================================================================
head('2. the browser: does the heading still pin inside the dialog?')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

ROWS = [('Sea Breeze Court', 'Blocked drain', 'kitchen sink', '2026-08-01',
         'Open', 35),
        ('Olive Grove', 'Damp patch', 'north wall', '2026-07-03',
         'In Progress', 64),
        ('Olive Grove', 'Lift service overdue', 'annual inspection',
         '2025-12-22', 'Open', 257),
        ('Harbour View', 'Gate motor noise', 'main entrance', '2026-08-11',
         'Open', 25),
        ('Cedar Heights', 'Intercom dead', 'block B', '2026-05-02',
         'Open', 126)]


def band(d):
    return ('alv-age-0' if d <= 30 else 'alv-age-2' if d <= 90
            else 'alv-age-3' if d <= 180 else 'alv-age-4')


def body_rows():
    return ''.join(
        '<tr><td data-label="Property">%s</td>'
        '<td data-label="Issue"><a class="ia-link" href="#">%s</a>'
        '<br><span class="ia-desc">%s</span></td>'
        '<td class="num" data-label="Logged">%s</td>'
        '<td class="num" data-label="Status">'
        '<span class="alv-pill alv-pill-attn">%s</span></td>'
        '<td class="num" data-label="Age">'
        '<span class="alv-age-pill %s">%dd</span></td></tr>'
        % (p, h, d, lg, st, band(a), a) for p, h, d, lg, st, a in ROWS)


def drill_page(page_css, table_cls):
    """The dialog as fsr.html actually assembles it, with the page's own
       stylesheet over base's - so a page rule that outranks base shows up."""
    return ('<!doctype html><meta charset=utf-8><style>%s</style>'
            '<style>%s</style><style>%s</style>'
            '<div class="ia-drill-overlay show" style="position:static">'
            '<div class="ia-drill" style="max-height:260px">'
            '<div class="ia-drill-head"><span class="ia-tag"></span>'
            '<span class="ia-dt">91-180 days</span>'
            '<span class="ia-dc">5 issues</span>'
            '<button class="ia-dx" type="button">&times;</button></div>'
            '<div class="ia-drill-body" id="db">'
            '<table class="%s"><thead><tr><th>Property</th><th>Issue</th>'
            '<th class="num">Logged</th><th class="num">Status</th>'
            '<th class="num">Age</th></tr></thead><tbody>%s</tbody></table>'
            '</div></div></div>'
            % (FIX, BASE_CSS, page_css, table_cls, body_rows()))


def probe(pg, html, scroll=140):
    f = os.path.join(tempfile.gettempdir(), 'iadrill.html')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(html)
    pg.goto('file://' + f)
    pg.evaluate('n => document.getElementById("db").scrollTop = n', scroll)
    pg.wait_for_timeout(120)
    return pg.evaluate(
        """() => {
             const b  = document.getElementById('db');
             const th = b.querySelector('thead th');
             const td = b.querySelector('tbody td');
             const a  = b.querySelector('a.ia-link');
             const cs = getComputedStyle(th);
             return {
               scrolled:  b.scrollTop,
               scrollable: b.scrollHeight > b.clientHeight,
               position:  cs.position,
               offset:    Math.round(th.getBoundingClientRect().top
                                     - b.getBoundingClientRect().top),
               headBg:    cs.backgroundColor,
               shadow:    cs.boxShadow,
               link:      a ? getComputedStyle(a).color : null,
               rowH:      Math.round(
                            td.closest('tr').getBoundingClientRect().height)
             };
           }""")


if sync_playwright is not None:
    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        pg = _b.new_page(viewport={'width': 900, 'height': 520})

        now = probe(pg, drill_page(css_of(F), 'table alv-table'))
        old = probe(pg, drill_page(css_of(WAS), 'ia-tbl'))

        check('CONTROL: the drill body really does scroll',
              now['scrollable'] and now['scrolled'] > 0,
              '%s / %s' % (now['scrollable'], now['scrolled']))
        check('the heading is sticky', now['position'] == 'sticky',
              now['position'])
        check('  and it PINS to the top of the drill body, not the page',
              now['offset'] == 0, '%dpx off' % now['offset'])
        check('  it paints a band, so rows cannot show through it',
              now['headBg'] not in ('rgba(0, 0, 0, 0)', 'transparent'),
              now['headBg'])
        check('CONTROL: the old table pinned too - the round did not '
              'introduce stickiness, it kept it',
              old['position'] == 'sticky' and old['offset'] == 0,
              '%s / %dpx' % (old['position'], old['offset']))

        # ===================================================================
        head('3. the rescope: are the issue links still house-coloured?')
        # ===================================================================
        _ink = re.search(r'--alv-accent-ink:\s*(#[0-9a-fA-F]{3,8})', BASE_CSS)
        check('base declares --alv-accent-ink', _ink is not None)
        if _ink:
            r, g, bl = (int(_ink.group(1)[i:i + 2], 16) for i in (1, 3, 5))
            want = 'rgb(%d, %d, %d)' % (r, g, bl)
            check('a drill link renders in base\'s accent ink',
                  now['link'] == want, '%s vs %s' % (now['link'], want))
            check('  CONTROL: it did before the rename too',
                  old['link'] == want, '%s vs %s' % (old['link'], want))
            # THE DEFECT THIS ROUND NEARLY SHIPPED, pinned as its own check:
            # rename the table without rescoping and the link goes Bootstrap
            # blue. Reproduced by rendering the NEW table with the OLD sheet.
            broke = probe(pg, drill_page(css_of(WAS), 'table alv-table'))
            check('CONTROL: renaming WITHOUT the rescope would have dropped '
                  'the links to Bootstrap blue', broke['link'] != want,
                  broke['link'])

        # ===================================================================
        head('4. what the round did NOT do')
        # ===================================================================
        # The shadow is absent BY DECISION - base's observer runs once at load
        # with the viewport as root, and this table is built later and scrolls
        # inside the dialog. Asserted so it reads as a decision.
        check('no .table-container wrapper was added - the dialog is the card',
              'table-container' not in js_of(FC))
        check('  so the sticky CUE cannot fire, which is the accepted cost',
              '0px 6px 12px' not in now['shadow'], now['shadow'][:46])
        check('  and the round says so in the file, for the next reader',
              'shadow' in F.lower() and 'ia-drill-body' in css_of(F))
        _b.close()

# ===========================================================================
head('5. the overlay is still hand-rolled, and the script still works')
# ===========================================================================
# base has NO modal component; this is a dialog inside a Bootstrap modal.
# Deleting these with the table's rules would leave it unstyled.
for sel in ('.ia-drill-overlay{', '.ia-drill{', '.ia-drill-head{',
            '.ia-drill-body{', '.ia-desc{'):
    check('the overlay keeps %s' % sel, sel in css_of(FC))
check('base still has no modal component of its own - so this is one asker',
      not re.search(r'\.alv-(modal|dialog|overlay|sheet)\b', BASE_CSS))

# Losing a hook leaves a dialog that renders correctly and does nothing.
for hook in ('iaDrillOverlay', 'iaDrillBody', 'iaDrillClose', 'iaDrillTitle',
             'iaDrillCount', 'iaDrillTag', 'showDrill', 'closeDrill',
             'drillRows', 'lastDrill'):
    check('the script keeps %s' % hook, hook in js_of(FC))
check('Escape still closes it', "e.key==='Escape'" in js_of(FC).replace(' ', ''))
check('  and a backdrop click still does',
      "iaDrillOverlay'" in js_of(FC) and 'closeDrill()' in js_of(FC))

# The rest of the page is C1's and C2's, and this round is not theirs.
check('C1 survives: the charts still read base tokens',
      'iaTok(' in FC and 'AGE_BANDS' in FC)
check('C2 survives: the stat strip still bands its tiles',
      'alv-stat-age' in FC and 'ageBand(' in FC)
check('the segmented tabs are still NOT segments - that was decided 2 Sep',
      '.ia-tab{' in css_of(FC) and 'alv-seg' not in FC)

# Structure.
for blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('braces balance in a style block', blk.count('{') == blk.count('}'))
check('script tags balance',
      len(re.findall(r'<script[^>]*>', F)) == len(re.findall(r'</script>', F)))
# PROSE THAT CONTAINS MARKUP IS MARKUP.
_bad = [m.group(0)[:40] for m in re.finditer(r'/\*.*?\*/', F, re.S)
        if re.search(r'</?(?:script|style)\b', m.group(0))]
check('no CSS comment spells a script or style tag', not _bad, str(_bad))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
