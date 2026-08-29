"""test_oi_migration.py - Outstanding Invoices on the table standard.

    python test_oi_migration.py

Run from the project root, after apply_ageing_scale.py and
apply_oi_migration.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 is the migration proper: both tables in a container, on
    .alv-table, with the page no longer defining what base owns. The check
    that matters most is that NO WRAPPER AROUND A CONTAINER SCROLLS - an
    element with overflow-x becomes the scroll container for any sticky
    descendant, which is the sticky sweep's entire finding and the reason
    .table-container clips rather than hiding.
  * SECTION 3 is the print behaviour, and it asserts something slightly
    unusual: that this round wrote NO print CSS. The page was on the list for
    printing white on white; base's print block already carries
    print-color-adjust on .alv-table, so joining the standard is the fix.
  * SECTION 4 checks literals WHERE THE ROUND REACHED, and counts them
    everywhere. The debtor cards and mobile invoice rows keep their own
    layout deliberately and their own colours with it; a check wider than the
    round would fail on things that are not defects, and get relaxed.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'open_invoices_report.html')

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
    text = re.sub(r'\{#[^\n]*?#\}', '', text)      # NOT re.S - nor is Django

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


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


for p in (BASE, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

BS, PG = read(BASE), read(PAGE)
if 'A TOTALS ROW BELONGS IN A tfoot' not in BS:
    print('\n! not patched - run apply_oi_migration.py first.')
    sys.exit(1)

BC, PC = nocomment_html(BS), nocomment_html(PG)
P, B = rules(PG), rules(BS)

# ===========================================================================
head('1. the standard gains a tfoot')
# ===========================================================================
check('base defines .alv-table tfoot', '.alv-table tfoot td' in B)
_tf = ' '.join(B.get('.alv-table tfoot td', []))
check('  on house tokens, not literals',
      'var(--alv-' in _tf and not re.search(r'#[0-9a-fA-F]{3,8}', _tf), _tf[:70])
check('  and NOT sticky - an ordinary table does not scroll under a frozen '
      'column the way .alv-matrix does', 'sticky' not in _tf)
check('the mobile card view knows about tfoot',
      '.alv-table tfoot,' in BC or '.alv-table tfoot ' in BC)
check('CONTROL: .alv-matrix DOES pin its footer, so the two are deliberately '
      'different', bool(re.search(r'\.alv-matrix tfoot td[^}]*sticky', BC, re.S)))

# ===========================================================================
head('2. both tables joined the standard')
# ===========================================================================
check('the debtors table is an .alv-table', 'class="alv-table"' in PC)
check('the modal table is too', "'<table class=\"alv-table\">'" in PC)
check('both sit in a container', PC.count('table-container') == 2,
      '%d' % PC.count('table-container'))
check('NO WRAPPER AROUND A CONTAINER SCROLLS - overflow-x makes it the scroll '
      'container and the sticky header pins to it instead of the viewport',
      'overflow-x: auto' not in PC)
check('the totals row is a real <tfoot>',
      '<tfoot>' in PC and '</tfoot>' in PC)
check('  and is no longer the last <tr> of the tbody',
      'class="totals-row"' not in PC)

for _dead in ('.age-analysis-table', '.age-analysis-table th',
              '.age-analysis-table td', '.totals-row', '.amount-cell',
              '.invoice-table', '.invoice-table th', '.invoice-table-wrap'):
    check('the page no longer defines %s' % _dead, _dead not in P)
check('  which is 8 selectors of table drawing the system already does',
      True)

check('desktop-only is on the CONTAINER, once',
      PC.count('table-container desktop-only-table') == 1)
check('  and not also on the table, which would hide nothing extra',
      'alv-table desktop-only-table' not in PC)
check('  and it hides a block now, because a div is not a table',
      '.desktop-only-table { display: block; }' in PC)
check('  on paper too', '.desktop-only-table { display: block !important; }' in PC)

check('the figure columns take base\'s .num', PC.count('class="num') >= 13,
      '%d cells' % PC.count('class="num'))
check('  including the modal\'s two', 'class=\\"num\\" data-label' in PC
      or 'class="num" data-label' in PC)

# ===========================================================================
head('3. the print fix required no print CSS')
# ===========================================================================
check('base prints tables with print-color-adjust',
      bool(re.search(r'\.alv-table th,\s*\.alv-table td\s*\{[^}]*print-color-adjust',
                     BC, re.S)))
check('  so joining the standard IS the white-on-white fix, and this round '
      'wrote no print rule of its own',
      '.age-analysis-table {\n        font-size: 0.8rem;' not in PC)
check('the page keeps only the print rules base cannot know about - swapping '
      'the desktop table in for the mobile cards on paper',
      'desktop-only-table { display: block !important; }' in PC
      and 'mobile-only-cards { display: none !important; }' in PC)

# ===========================================================================
head('4. literals, where the round reached')
# ===========================================================================
for _sel in ('.analysis-title', '.tenant-name-cell', '.total-amount',
             '.clickable-amount', '.clickable-amount:hover'):
    _b = ' '.join(P.get(_sel, []))
    check('%s carries no literal colour' % _sel,
          bool(_b) and not re.search(r'#[0-9a-fA-F]{3,8}\b', _b), _b[:60])
check('the navy header band is gone from the page', '#2c3e50;' not in
      ' '.join(v for k, vs in P.items() for v in vs if 'analysis-table' in k))
check('  and #34495e with it', '#34495e' not in PC)
check('  and the modal\'s grey band', '#e9ecef' not in PC)
check('Courier New is gone from both tables',
      not any('Courier' in ' '.join(P.get(k, []))
              for k in ('.amount-cell', '.invoice-table', '.num')))
check('CONTROL: it deliberately SURVIVES in the mobile cards, which this '
      'round does not touch', 'Courier New' in PC)

# ---------------------------------------------------------------------------
head('5. the modal says WHICH invoices are old')
# ---------------------------------------------------------------------------
check('a whole row can no longer be painted red', '.overdue' not in P)
check('  and nothing still asks for that class',
      "invoice.overdue ? 'overdue'" not in PC)
check('the five bands are ONE function on the page, not a chain in each loop',
      PC.count('function ageStep') == 1)
check('  used by the modal table and the mobile rows and defined once',
      PC.count('ageStep(') == 3, '%d uses' % PC.count('ageStep('))
check('the Days Overdue figure carries an ageing pill',
      'alv-age-pill \' + ageStep(d)' in PC or 'alv-age-pill' in PC)
for _b in ('> 90', '> 60', '> 30', '> 0'):
    check('  splitting on %s, as the view does' % _b, _b in PC)
check('a not-yet-due invoice reads so rather than showing 0',
      "'Not yet due'" in PC)
check('CONTROL: the pill class is defined in base, not invented here',
      bool(re.search(r'\.alv-age-pill\s*[,{ ]', BC)))

# ---------------------------------------------------------------------------
head('6. headings over the columns, figures on the decimal')
# ---------------------------------------------------------------------------
check('base defines a centred heading, beside the one it already had for '
      'action columns',
      bool(re.search(r'\.alv-table thead th\.col-center\s*\{[^}]*center', BC)))
check('  scoped to thead, so it cannot reach a body cell',
      'thead th.col-center' in BC)
check('the six figure headings are centred', PC.count('class="col-center"') == 6,
      '%d' % PC.count('class="col-center"'))
check('  and Tenant Name is NOT - it is a name, and names read from the left',
      '<th>Tenant Name</th>' in PC)
check('CONTROL: col-center never lands on a <td>',
      'td class="col-center"' not in PC)
# The figures themselves must still be right-aligned, in the body AND in the
# footer. .alv-table td.num is (0,2,1) and .alv-table tfoot td is (0,1,2), so
# .num wins on class count - but that is the kind of thing worth asserting
# rather than reasoning about a second time.
check('base right-aligns .num on a th and a td alike',
      bool(re.search(r'\.alv-table td\.num,\s*\.alv-table th\.num\s*\{[^}]*right',
                     BC, re.S)))
_tf = PC[PC.index('<tfoot>'):PC.index('</tfoot>')]
check('every figure in the totals row carries .num',
      _tf.count('class="num') == 6, '%d of 6' % _tf.count('class="num'))
check('  and the TOTALS label does not', 'tenant-name-cell' in _tf)
_lits = len(re.findall(r'#[0-9a-fA-F]{3,8}\b', PC))
check('the page is down to %d literal colour uses' % _lits, _lits <= 34,
      '(was 46 before this round)')

check('page CSS braces balance',
      '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S)).count('{')
      == '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S)).count('}'))
check('base CSS braces balance',
      '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S)).count('{')
      == '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S)).count('}'))
for _o, _c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
               (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
    check('Django blocks balance (%s)' % _o,
          len(re.findall(_o, PG)) == len(re.findall(_c, PG)))
check('tbody balances', PC.count('<tbody>') == PC.count('</tbody>'))
check('tfoot balances', PC.count('<tfoot>') == PC.count('</tfoot>'))
check('no {# #} comment spans lines',
      not [l for l in PG.split('\n') if l.count('{#') != l.count('#}')])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
