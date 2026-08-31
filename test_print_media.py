"""test_print_media.py - the phone card view stops printing.

    python test_print_media.py

Run from the repo root, after apply_print_media.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS THE TABLE AT PAPER WIDTH WITH PRINT MEDIA EMULATED.
    That is the whole bug: on paper the viewport is the page box, and A4
    portrait is ~718 CSS px of content - under base's 768px phone breakpoint -
    so a query written without `screen` fired on every printed page and turned
    every table into a stack of cards. 718px + print media is a MODEL of the
    page box, not the real print pipeline; it reproduces the media-query
    evaluation exactly, which is where the fault lives.
  * IT CARRIES TWO CONTROLS. At 390px on SCREEN the card view must still work
    - a fix that killed it everywhere would pass every "it is a table now"
    check. And the SAME 718px width must give CARDS on screen and a TABLE on
    paper: a 718px window is a narrow window and cards are right there. If
    both came out as tables the breakpoint would merely have moved, and every
    other check here would still pass.
  * SECTION 1 reads base: five blocks qualified, none left bare, the 991px
    sidebar block deliberately untouched, and the Actions column hidden on
    paper - because until this round it was hidden by accident.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

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


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


if not os.path.exists(BASE):
    sys.exit('! %s not found - run from the repo root' % BASE)
BS = read(BASE)
if '@media screen and (max-width: 768px)' not in BS:
    print('\n! not patched - run apply_print_media.py first.')
    sys.exit(1)
BC = nocomment_html(BS)

# ===========================================================================
head('1. five blocks qualified, one left alone, and the actions off paper')
# ===========================================================================
# The round's own prose names the bare query it removes, so this comes first.
check('CONTROL: base still explains the bare query it removed',
      '@media (max-width: 768px)' in BS)
check('CONTROL: .. and it is gone once stripped',
      '@media (max-width: 768px)' not in BC)

_guarded = len(re.findall(r'@media screen and \(max-width: 768px\)', BC))
check('five phone blocks are screen-only', _guarded == 5, '%d' % _guarded)
check('  and no bare 768px block survives',
      not re.search(r'@media \(max-width: 768px\)', BC))
# DELIBERATELY LEFT: hiding the sidebar on paper is correct.
check('the 991px sidebar block is untouched, on purpose',
      '@media (max-width: 991px)' in BC)

_print = BC[BC.find('@media print'):]
for _cls in ('.desktop-action-cell', '.alv-table .cell-actions', '.row-actions',
             '.mobile-action-bar'):
    check('%s is hidden on paper' % _cls, _cls in _print)

# ===========================================================================
head('2. rendered at paper width, with print media')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

BOOT = None
for _c in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           '/tmp/bootstrap.min.css'):
    if os.path.exists(_c):
        BOOT = open(_c, encoding='utf-8').read()
        break
if BOOT is None:
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
    sync_playwright = None

if sync_playwright is not None:
    _b = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))
    _rows = '\n'.join(
        '<tr><td data-label="Property">Property %d</td>'
        '<td class="num" data-label="Amount">%d.00</td>'
        '<td class="cell-actions desktop-action-cell">'
        '<button class="icon-action-btn">e</button></td></tr>' % (i, 900 + i)
        for i in range(1, 9))

    FIX = """<!doctype html><meta charset=utf-8>
<style>%s</style><style>%s</style><style>body{margin:0}</style>
<div class="table-container"><table class="table alv-table" id="t">
  <thead><tr><th>Property</th><th class="num">Amount</th>
    <th class="cell-actions">Actions</th></tr></thead>
  <tbody>%s</tbody>
  <tfoot><tr><td>Total</td><td class="num">7,236.00</td><td></td></tr></tfoot>
</table></div>
<div class="mobile-action-bar"><button>x</button></div>
""" % (BOOT, _b, _rows)

    _f = os.path.join(tempfile.gettempdir(), 'print_media_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const cs = s => getComputedStyle(document.querySelector(s));
      return {
        thead: cs('#t thead').display,
        tbody: cs('#t tbody').display,
        tfoot: cs('#t tfoot').display,
        tr:    cs('#t tbody tr').display,
        td:    cs('#t tbody td').display,
        before: getComputedStyle(document.querySelector('#t tbody td.num'),
                                 '::before').content,
        deskActions: cs('#t tbody td.desktop-action-cell').display,
        mobBar: cs('.mobile-action-bar').display,
      };
    }"""

    def probe(pw, width, media):
        pg = pw.new_page(viewport={'width': width, 'height': 900})
        pg.goto('file://' + _f)
        pg.emulate_media(media=media)
        out = pg.evaluate(PROBE)
        pg.close()
        return out

    with sync_playwright() as p:
        br = p.chromium.launch()
        D = probe(br, 1200, 'screen')      # desktop
        M = probe(br, 390, 'screen')       # phone
        S718 = probe(br, 718, 'screen')    # a narrow window - cards are right here
        P718 = probe(br, 718, 'print')     # A4 portrait content width
        P = probe(br, 1200, 'print')       # a wide page box, e.g. landscape
        br.close()

    # THE FIX.
    check('PRINT at A4 width: the table is still a TABLE',
          P718['tr'] == 'table-row' and P718['td'] == 'table-cell',
          '%s / %s' % (P718['tr'], P718['td']))
    check('  the heading is a header GROUP, so it repeats on every page',
          P718['thead'] == 'table-header-group', P718['thead'])
    check('  and the totals band is a footer group, so it does too',
          P718['tfoot'] == 'table-footer-group', P718['tfoot'])
    check('  no data-label prefix is printed beside the figures',
          P718['before'] in ('none', 'normal'), P718['before'])
    check('  the Actions column does not print',
          P718['deskActions'] == 'none', P718['deskActions'])
    check('  and neither does the mobile bar', P718['mobBar'] == 'none',
          P718['mobBar'])
    check('PRINT on a wide page box behaves the same',
          P['tr'] == 'table-row' and P['thead'] == 'table-header-group')

    # CONTROL 1. A fix that killed the card view would pass everything above.
    check('CONTROL: on a PHONE the card view still works',
          M['thead'] == 'none' and M['tr'] == 'block'
          and 'Amount' in M['before'],
          '%s / %s / %s' % (M['thead'], M['tr'], M['before']))
    # CONTROL 2, AND THE STRONGEST STATEMENT OF THE FIX. The same 718px
    # width must give CARDS on a screen and a TABLE on paper. A screen 718px
    # wide is a narrow window and the card view is exactly right there; what
    # was wrong was that paper counted as one. If both came out as tables the
    # breakpoint would simply have moved, and every check above would still
    # pass.
    check('CONTROL: 718px on SCREEN is still cards, as a narrow window should be',
          S718['tr'] == 'block' and S718['thead'] == 'none',
          '%s / %s' % (S718['tr'], S718['thead']))
    check('  and the SAME width on PAPER is a table - which is the whole fix',
          P718['tr'] == 'table-row' and S718['tr'] != P718['tr'],
          'screen %s vs print %s' % (S718['tr'], P718['tr']))

    check('DESKTOP is unchanged', D['thead'] == 'table-header-group'
          and D['tr'] == 'table-row' and D['deskActions'] == 'table-cell',
          '%s / %s' % (D['thead'], D['deskActions']))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
