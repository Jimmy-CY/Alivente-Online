"""test_table_suppliers - Suppliers is on the standard, and nothing else moved.

    python test_table_suppliers.py

Two halves, and the second is the one that matters.

STATIC: the right rules left, and - just as important - the WRONG ones did
not. A deletion pass is only safe if it stopped where it should have, so this
asserts that the filter panel, the delete modal, the search box and the
page-header buttons all still have their own CSS. A patcher that removed those
would also make every "is it gone?" check pass.

BROWSER: renders the page's real table markup against real Bootstrap plus the
CSS lifted from base.html, and reads the result back. The interesting checks
are the ones the pilot itself discovered - that dropping text-center must not
drag the action buttons left with the names, and that the mobile cards stop
inheriting Bootstrap's stripe.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(PAGE):
    sys.exit('! pages/templates/suppliers.html not found - run from the root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


SRC = read(PAGE)
BASE_SRC = read(BASE)
CSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', SRC, re.S | re.I))

# ==================================================================== MARKUP
m = re.search(r'<table[^>]*class="([^"]*)"', SRC)
cls = m.group(1).split() if m else []
check('the table joins the standard', 'alv-table' in cls)
check('  and keeps its own name for anything page-specific',
      'suppliers-table' in cls)
for gone in ('table-bordered', 'table-striped', 'text-center'):
    check('  %s is gone from the class list' % gone, gone not in cls)
check('  Bootstrap .table survives (padding, base metrics)', 'table' in cls)

# Django's tag_re has no DOTALL: a {# #} spanning a newline renders as visible
# text. This shipped once, hidden behind a self-granted exemption in the
# patcher, and test_delete_choice.py caught it. Asserted here too so the page
# that carries the comment is the page that checks it.
_bad = [i for i, l in enumerate(SRC.split('\n'), 1)
        if '{#' in l and '#}' not in l]
check('no {# comment spans a newline%s'
      % (' (line %s)' % _bad[0] if _bad else ''), not _bad)

check('the empty state exists at all', 'alv-empty' in SRC)
check('  and is conditional, not always drawn',
      re.search(r'\{%\s*if\s+not\s+supplier\s*%\}', SRC) is not None)
check('  it closes its if', SRC.count('{% endif %}') >= SRC.count('{% if '))
check('  and sits outside the table, not inside tbody',
      SRC.find('alv-empty') > SRC.find('</table>'))

# ---------------------------------------------- three columns become one
check('there is ONE actions column, not three',
      SRC.count('desktop-action-cell cell-actions') == 2)   # one th, one td
check('  no bare per-verb action cell survives',
      SRC.count('class="desktop-action-cell"') == 0)
check('  the buttons share a single inline wrapper',
      SRC.count('class="row-actions"') == 1)
check('  the header reads Actions, not Edit/Report/Delete',
      '>Actions</th>' in SRC
      and not re.search(r'<th[^>]*>\s*Edit\s*</th>', SRC))
check('  column widths were redistributed to sum to 100',
      sum(int(x) for x in re.findall(r'width:\s*(\d+)%',
          SRC[SRC.find('<thead'):SRC.find('</thead>')])) == 100)

# The risk in a cell merge is losing a permission branch with the cell.
check('  every action keeps its disabled twin (%d)'
      % SRC.count('icon-disabled'), SRC.count('icon-disabled') == 2)
check('  and the delete button keeps its five data- attributes',
      SRC.count('data-supplier-id') >= 2
      and 'data-contact-person' in SRC and 'data-company-name' in SRC)

check('base.html centres action cells',
      '.alv-table .desktop-action-cell' in BASE_SRC)
check('base.html centres the actions column, heading and cells as one',
      re.search(r'\.alv-table \.cell-actions,\s*\.alv-table th\.cell-actions'
                r'\s*\{[^}]*text-align:\s*center', BASE_SRC, re.S) is not None)
check('  and lays its buttons out inline',
      re.search(r'\.row-actions\s*\{[^}]*inline-flex', BASE_SRC) is not None)

# ================================================= WHAT SHOULD HAVE GONE
for sel in ('.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
            '.icon-disabled', '.mobile-action-bar', '.mobile-action-btn',
            '.mobile-action-icon', '.mobile-action-label',
            '.mobile-action-disabled', '.desktop-action-cell',
            '.icon-color-edit', '.table-container'):
    check('  local %s is gone (base.html owns it)' % sel,
          not re.search(re.escape(sel) + r'\s*[,{:]', CSS))
check('  and so are the .suppliers-table layout rules',
      not re.search(r'\.suppliers-table\s*[,{]', CSS))
check('  including the per-page card-title rule :first-child replaced',
      'data-label="Contact Person"' not in CSS)

# ============================== WHAT MUST NOT HAVE GONE  (the real safety net)
# A patcher that deleted too much would pass every check above.
for sel, why in (('.filter-panel', 'the filter panel'),
                 ('.filter-grid', 'its layout'),
                 ('.search-btn', 'the search button'),
                 ('.filter-tag', 'the active-filter chips'),
                 ('.modal-header', 'the delete modal'),
                 ('.delete-modal-grid', 'its grid'),
                 ('.action-add-new', 'Add New'),
                 ('.action-more-btn', 'the mobile More menu'),
                 ('.action-back', 'Back'),
                 ('.btn-info', 'the page-header buttons')):
    check('  KEPT %-22s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\s*[,{:.]', CSS) is not None)

# Presence is not integrity. A negative control that deleted ONE .filter-panel
# rule passed every check above, because .filter-panel.expanded still matched.
# So count them: the page's own components must still have all their rules,
# not merely one apiece.
_sels = [' '.join(re.sub(r'/\*.*?\*/', '', mm.group(1), flags=re.S).split())
         for mm in re.finditer(r'([^{}]+)\{', CSS)]


def group(prefix):
    return sum(1 for x in _sels if prefix in x)


# Floors are the EXACT post-migration counts, not a comfortable margin. A
# margin lets a rule go missing quietly, which is the failure this exists to
# catch. If a later round legitimately removes one, the number moves with it -
# deliberately, in the same commit.
for prefix, floor, why in (('.filter', 27, 'filter panel + chips'),
                           # 11 UNTIL THE MODULE-WIDE BUTTON SWEEP. That round
                           # deleted three page-local rules base.html had come
                           # to own - `.page-action-buttons .action-secondary`,
                           # `.action-more-item` and `.action-more-item i` - so
                           # 8 is the correct count now, and this page carries
                           # exactly the same eight as Properties and Tenants.
                           #
                           # The number MOVED with the decision. It was not
                           # deleted, and it was not passed with -Force: a
                           # floor that is quietly lowered every time it fails
                           # stops being a floor. The check below names what
                           # went, so the next person does not have to work out
                           # why the number changed.
                           ('.action-', 8, 'page-header buttons'),
                           ('.modal', 10, 'delete modal'),
                           ('.search', 8, 'search box')):
    check('  %-10s still has %d rules (>= %d expected: %s)'
          % (prefix, group(prefix), floor, why), group(prefix) >= floor)

# WHY EIGHT AND NOT ELEVEN. A floor alone records a number, not a reason - and
# this one has now moved once, which is exactly when a check earns an
# explanation. The three rules the button sweep removed are named here, and
# each is asserted to be defined in base.html: a rule is only safe to delete
# locally BECAUSE something replaced it.
_SWEPT = ('.page-action-buttons .action-secondary',
          '.action-more-item',
          '.action-more-item i')
# EXACT selectors, not substrings. `.action-more-item` is gone as a rule of
# its own, but `.action-more-item:hover, .action-more-item:active, ...`
# survives - and a substring test cannot tell those apart, so the first
# version of this check reported the deletion as having failed. Compare
# against the parsed selector list instead.
_flat = [x.strip() for sel in _sels for x in sel.split(',') if x.strip()]

# (selector, declarations) pairs, needed to assert a rule still CARRIES a
# declaration rather than merely existing.
_rule_pairs = [(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).strip(),
                m.group(2))
               for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', CSS)]

for _s in _SWEPT:
    check('  the sweep removed %-40s because base.html owns it' % _s,
          _s not in _flat
          and re.search(re.escape(_s.split()[-1]) + r'\s*[,{:]', BASE_SRC)
          is not None)
check('  CONTROL: the eight that remain are page-specific, not base\'s',
      group('.action-') == 8)

for prefix in ('.icon-', '.mobile-action', '.table-container',
               '.suppliers-table'):
    check('  %-16s has 0 rules left - base.html owns it now' % prefix,
          group(prefix) == 0)

check('  the mobile @media block still exists for the page-specific half',
      re.search(r'@media[^{]*max-width:\s*768px', CSS) is not None)
check('  and the page still has substantial CSS of its own (%d lines)'
      % CSS.count('\n'), CSS.count('\n') > 150)

# ---------------------------------------------------------------------------
# WHY THE .filter FLOOR MOVED  (27 Aug, the filter round)
# ---------------------------------------------------------------------------
# Same shape as the .action- move above, and the same rule applied: the number
# moved WITH the decision, in the same commit, and what went is named here so
# nobody has to reverse-engineer the arithmetic later.
#
# The filter panel now has one owner. base.html decides whether it is open -
# `.alv-filter` hidden by default, `.is-open` to show it - and the page keeps
# only its appearance. Before that, four pages recorded "is the panel open" in
# TEN separate places. These eleven selectors were the CSS half of that.
_FILTER_GONE = (
    '.filter-panel:not(.expanded) .filter-content',
    '.filter-panel.expanded .filter-content',
    '.filter-panel.force-expanded',
    '.filter-panel.force-expanded .filter-content',
    '.filter-panel.expanded',
    '.filter-header.expanded',
    '.filter-header.expanded:hover',
    '.filter-header:hover',
    '.filter-toggle-icon',
    '.filter-toggle-icon.rotated',
    '.filter-content.show',
)
for _s in _FILTER_GONE:
    check('  the filter round removed %-44s' % _s, _s not in _flat)

# TWO WERE REWRITTEN, NOT DROPPED - and this is the half that matters.
# `.filter-panel.expanded` is where the panel's PADDING lived. Delete it as
# "expanded machinery" and the panel opens with its fields flush against the
# border: no count changes, no tag unbalances, nothing throws. So the rule was
# renamed in place, exactly as `.lease-end-red` was in the Tenants round -
# base.html does not own these selectors, and a rule nothing replaces must
# never simply be dropped.
check('  .filter-panel survived the round', '.filter-panel' in _flat)
check('    and still declares its padding',
      any(' '.join(s.split()) == '.filter-panel' and 'padding' in b
          for s, b in _rule_pairs))
check('  .filter-header survived too', '.filter-header' in _flat)
check('  base.html is what hides the panel now',
      '.alv-filter' in BASE_SRC and 'alv-filter script v1' in BASE_SRC)
check('    and the page defers to it', 'alv-filter' in SRC)
check('  CONTROL: the page did NOT keep a second way to hide it',
      'force-expanded' not in SRC and 'filter-toggle-icon' not in SRC)

# The permission-aware markup must be untouched: this round is CSS.
check('permission conditionals survive (%d)' % SRC.count('{% if perms.'),
      SRC.count('{% if perms.') >= 2)
check('  every url tag survives (%d)' % SRC.count('{% url '),
      SRC.count('{% url ') >= 3)
check('  and the disabled twins are still rendered, not dropped',
      'icon-disabled' in SRC and 'mobile-action-disabled' in SRC)

# ================================================================ IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break

if BOOT is None:
    print('')
    print('  !! test_fixture_bootstrap413.css missing - browser checks need it')
else:
    _c = re.sub(r'<!--.*?-->', '', BASE_SRC, flags=re.S)
    _b = re.findall(r'<style[^>]*>(.*?)</style>', _c, re.S | re.I)
    _d = lambda x: re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    BASECSS = '\n'.join(x for x in _b
                        if '--alv-accent:' in _d(x) or '--alv-paper:' in _d(x))

    # Render the page's OWN table markup - not a hand-made copy of it - so a
    # markup change that breaks the layout is caught here rather than on Live.
    frag = re.search(r'<div class="table-container">.*?\n  </div>',
                     SRC, re.S)
    check('the table markup could be located for rendering', frag is not None)
    f = frag.group(0) if frag else ''
    f = re.sub(r'\{%\s*if\s+not\s+supplier\s*%\}.*?\{%\s*endif\s*%\}', '',
               f, flags=re.S)
    f = re.sub(r'\{%\s*if[^%]*%\}(.*?)\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}',
               r'\1', f, flags=re.S)
    f = re.sub(r'\{%\s*if[^%]*%\}(.*?)\{%\s*endif\s*%\}', r'\1', f, flags=re.S)
    fm = re.search(r'\{%\s*for[^%]*%\}(.*?)\{%\s*endfor\s*%\}', f, re.S)
    rows = ''
    for name in ('Andreas Papadopoulos', 'Maria Georgiou', 'Nikos C'):
        r = fm.group(1).replace('{{sresults.supplier_contact_person}}', name)
        rows += re.sub(r'\{[{%][^}%]*[%}]\}', 'x', r)
    f = f[:fm.start()] + rows + f[fm.end():]
    f = re.sub(r'\{#.*?#\}', '', f, flags=re.S)
    f = re.sub(r'\{[{%][^}%]*[%}]\}', '', f)

    tmp = os.path.join(ROOT, '_sup_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>%s</style><style>%s</style><style>%s</style></head>'
        '<body>%s</body></html>' % (BOOT, BASECSS, CSS, f))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())

            def cs(pg, sel, props):
                """Computed styles, or a dict of Nones if the element is absent.

                Never None. A negative control that removed .row-actions made
                this return None, the next line did ra['display'], and the
                suite died with a TypeError - a real failure reported as a
                traceback instead of a named check. Missing elements are a
                normal thing for a test to discover, so they get a clean FAIL.
                """
                got = pg.evaluate(
                    """([s,ps])=>{const e=document.querySelector(s);
                       if(!e)return null;const c=getComputedStyle(e);
                       const o={};for(const p of ps)o[p]=c.getPropertyValue(p);
                       return o;}""", [sel, props])
                if got is None:
                    check('  !! %s is not in the rendered page' % sel, False)
                    return {p: None for p in props}
                return got

            pg = br.new_page(viewport={'width': 1440, 'height': 900})
            pg.goto('file://' + tmp)

            td = cs(pg, 'tbody td:nth-child(2)',
                    ['border-left-width', 'border-top-width', 'text-align'])
            check('desktop: no vertical grid lines',
                  td['border-left-width'] == '0px')
            check('desktop: the horizontal rule survives',
                  td['border-top-width'] == '1px')
            check('desktop: text columns read left, not centred',
                  td['text-align'] == 'left')

            act = cs(pg, 'tbody td.cell-actions', ['text-align'])
            check('desktop: the actions column is centred',
                  act['text-align'] == 'center')
            # Heading AND cells centred. This expectation has now moved
            # TWICE. It said "right" for the cells until the card round
            # measured what "centred" was actually doing: centring the
            # heading alone centres it on the COLUMN, while the buttons are
            # a cluster sitting inside that column. The two coincide only by
            # luck of the column width - 51px apart here at one point.
            #
            # Both failures were the suite doing its job: pinning behaviour
            # that had been deliberately changed. The fix is to move the
            # expectation in the same commit as the change, never to loosen
            # it - so the assertion below is now STRONGER than the one it
            # replaces. "center" is a property; the measurement is the
            # decision.
            hdr = cs(pg, 'thead th.cell-actions', ['text-align'])
            check('  and so is its header',
                  hdr['text-align'] == 'center')
            _off = pg.evaluate(
                """()=>{const th=document.querySelector('thead th.cell-actions');
                   const sp=document.querySelector('tbody .row-actions');
                   if(!th||!sp) return null;
                   const r=document.createRange(); r.selectNodeContents(th);
                   const lr=r.getBoundingClientRect(), sr=sp.getBoundingClientRect();
                   return (lr.left+lr.width/2)-(sr.left+sr.width/2);}""")
            check('  so the heading really does sit over the buttons (%s)'
                  % ('%+.1fpx' % _off if _off is not None else 'not measured'),
                  _off is not None and abs(_off) <= 1.5)
            ra = cs(pg, '.row-actions', ['display', 'gap'])
            check('  the three buttons sit inline with a gap',
                  ra['display'] == 'inline-flex' and ra['gap'] == '6px')
            check('  and there are exactly three of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 3)
            check('  one actions cell per row, not three',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child td').length")
                  == 6 + 1)   # 5 data columns + actions + the mobile bar cell

            r1 = cs(pg, 'tbody tr:nth-child(1)', ['background-color'])
            r2 = cs(pg, 'tbody tr:nth-child(2)', ['background-color'])
            check('desktop: no zebra - both rows the same',
                  r1['background-color'] == r2['background-color'])

            th = cs(pg, 'thead th', ['text-transform', 'background-color'])
            check('desktop: the header reads as a header',
                  th['text-transform'] == 'uppercase')
            e = cs(pg, '.icon-edit', ['color', 'width'])
            check('desktop: the edit icon still gets its colour from base.html',
                  e is not None and e['color'] == 'rgb(37, 99, 235)'
                  and e['width'] == '34px')
            pg.close()

            pg = br.new_page(viewport={'width': 375, 'height': 900})
            pg.goto('file://' + tmp)
            check('mobile: the header row is dropped',
                  cs(pg, 'thead', ['display'])['display'] == 'none')
            c1 = cs(pg, 'tbody tr:nth-child(1)',
                    ['background-color', 'display', 'border-radius'])
            c2 = cs(pg, 'tbody tr:nth-child(2)', ['background-color'])
            check('mobile: rows are cards', c1['display'] == 'block'
                  and c1['border-radius'] == '8px')
            check('mobile: EVERY card is the same colour',
                  c1['background-color'] == c2['background-color']
                  == 'rgb(255, 255, 255)')
            check('mobile: the action bar is a 3-up grid',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 3)
            check('mobile: the per-action cells step aside',
                  cs(pg, '.desktop-action-cell', ['display'])['display']
                  == 'none')
            check('mobile: the card fits the viewport',
                  pg.evaluate("()=>document.querySelector("
                              "'.table-container').scrollWidth") <= 375)
            pg.close()
            br.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
