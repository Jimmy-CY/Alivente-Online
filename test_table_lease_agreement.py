"""test_table_lease_agreement - the Lease Agreements screen is on the standard.

    python test_table_lease_agreement.py

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
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_lease_agreement.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(PAGE):
    sys.exit('! pages/templates/tenant_lease_agreement.html not found - run from the root')

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
      'lease-agreements-table' in cls)
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
      re.search(r'\{%\s*if\s+not\s+tenants\s*%\}', SRC) is not None)
check('  it closes its if', SRC.count('{% endif %}') >= SRC.count('{% if '))
check('  and sits outside the table, not inside tbody',
      SRC.find('alv-empty') > SRC.find('</table>'))

# ---------------------------------------------- three columns become one
check('there is ONE actions column, not two',
      SRC.count('desktop-action-cell cell-actions') == 2)   # one th, one td
check('  no bare per-verb action cell survives',
      SRC.count('class="desktop-action-cell"') == 0)
check('  the buttons share a single inline wrapper',
      SRC.count('class="row-actions"') == 1)
check('  the header reads Actions, not Lease Agreement / Actions',
      '>Actions</th>' in SRC
      and not re.search(r'<th[^>]*>\s*Lease Agreement\s*</th>', SRC))
check('  column widths were redistributed to sum to 100',
      sum(int(x) for x in re.findall(r'width:\s*(\d+)%',
          SRC[SRC.find('<thead'):SRC.find('</thead>')])) == 100)

# The risk in a cell merge is losing a permission branch with the cell.
check('  both slots keep a disabled twin, so the cluster never shifts (%d)'
      % SRC.count('icon-disabled'), SRC.count('icon-disabled') == 2)
check('  and the document viewer keeps its three arguments',
      SRC.count('viewDocument(') >= 2
      and 'tenant_lease_agreement.url' in SRC
      and 'tenant_lease_agreement.name' in SRC)

check('the mobile bar declares two columns', 'cols-2' in SRC)


# ------------------------------------------- the expired date, on the token
# Same Bootstrap red as tenant.html carried, and the same fix. Rewritten, not
# deleted: base.html does not own .end-date-expired, and a rule nothing
# replaces must never be dropped.
check('the expired-date rule survives', '.end-date-expired' in CSS)
check('  and is on the token, not Bootstrap\'s #dc3545',
      re.search(r'\.end-date-expired\s*\{[^}]*var\(--alv-bad\)', CSS)
      is not None)
check('  CONTROL: no raw Bootstrap red survives anywhere in the style block',
      '#dc3545' not in CSS)
check('  and the template still applies it', 'end-date-expired' in SRC)

# ------------------------------- the change that makes this round different
# The three rounds before this deleted CSS base.html had come to own. This one
# CONVERTS labelled Bootstrap buttons into house icon buttons, so the checks
# have to assert the conversion happened rather than infer it from a
# substitution having run without error.
for gone in ('btn-sm btn-success', 'btn-sm btn-danger',
             'btn-sm btn-outline-primary'):
    check('  no labelled Bootstrap row button survives (%s)' % gone,
          gone not in SRC)
# FIVE, not four: View, View-disabled, Delete, Upload, Upload-disabled. Only
# two are ever drawn at once - Delete and Upload are mutually exclusive, and
# each slot has a twin for the branch where it is unavailable.
check('  the row buttons are house icon buttons now (%d)'
      % SRC.count('icon-action-btn'), SRC.count('icon-action-btn') == 5)
check('  Upload carries the new tone', 'icon-upload' in SRC)
check('  and base.html defines it', '.icon-upload' in BASE_SRC)
check('  .icon-upload is an ALIAS, not a seventh colour',
      re.search(r'\.icon-upload\s*\{[^}]*var\(--alv-edit\)', BASE_SRC)
      is not None)
check('  and the mobile half is aliased too',
      re.search(r'\.icon-color-upload\s*\{[^}]*var\(--alv-edit\)', BASE_SRC)
      is not None)
check('  CONTROL: the local Bootstrap upload blue is gone', '#007bff' not in CSS)

# Two slots, both always drawn. Without the disabled twins the first slot
# would be empty on rows with no agreement and filled on rows with one, and
# the cluster would step sideways down the page.
_icons = re.findall(r'row-actions(.*?)</span>\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
check('  the row draws three possible glyphs across two slots (%s)'
      % ', '.join(sorted(set(_glyphs))),
      set(_glyphs) == {'fa-file-contract', 'fa-trash', 'fa-upload'})

# ------------------------------------------------- the permission gates again
# Counted against the backup rather than pinned to a literal - I have picked
# the wrong literal for this check twice. The invariant is that the collapse
# does not CHANGE the count.
_bak = PAGE + '.bak_tablelease'
if os.path.exists(_bak):
    _g = '{% if perms.auth.can_edit_tenants %}'
    check('every can_edit_tenants gate survived the collapse (%d)'
          % SRC.count(_g), SRC.count(_g) == read(_bak).count(_g))
    check('  CONTROL: there were gates to preserve in the first place',
          read(_bak).count(_g) > 0)

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
            '.icon-color-upload', '.table-container'):
    check('  local %s is gone (base.html owns it)' % sel,
          not re.search(re.escape(sel) + r'\s*[,{:]', CSS))
check('  and so are the .lease-agreements-table layout rules',
      not re.search(r'\.lease-agreements-table\s*[,{]', CSS))
check('  including the per-page card-title rule :first-child replaced',
      'data-label="Tenant"' not in CSS)

# ============================== WHAT MUST NOT HAVE GONE  (the real safety net)
# A patcher that deleted too much would pass every check above.
for sel, why in (('.upload-target-info', 'the upload banner'),
                 ('.file-upload-input', 'the file field'),
                 ('.modal-fullscreen-mobile', 'the modal on a phone'),
                 ('.end-date-expired', 'the expired-date red'),
                 ('.page-action-buttons-single', 'the lone Back bar'),
                 ('.action-btn-back', 'Back on a phone')):
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
for prefix, floor, why in (('.modal', 6, 'the upload modal'),
                           ('.page-title', 2, 'the page heading'),
                           ('.file-upload', 1, 'the file field')):
    check('  %-10s still has %d rules (>= %d expected: %s)'
          % (prefix, group(prefix), floor, why), group(prefix) >= floor)

for prefix in ('.icon-', '.mobile-action', '.table-container',
               '.lease-agreements-table', '.status'):
    check('  %-16s has 0 rules left - base.html owns it now' % prefix,
          group(prefix) == 0)

check('  the mobile @media block still exists for the page-specific half',
      re.search(r'@media[^{]*max-width:\s*768px', CSS) is not None)
check('  and the page still has substantial CSS of its own (%d lines)'
      % CSS.count('\n'), CSS.count('\n') > 60)

# The permission-aware markup must be untouched: this round is CSS.
check('permission conditionals survive (%d)' % SRC.count('{% if perms.'),
      SRC.count('{% if perms.') >= 2)
check('  every url tag survives (%d)' % SRC.count('{% url '),
      SRC.count('{% url ') >= 1)
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
    # FIND THE MATCHING CLOSE, do not guess at it from indentation.
    #
    # The Suppliers/Properties/Tenants version of this looked for
    # `<div class="table-container"> ... \n  </div>` - the close tag at two
    # spaces. This page closes it at column zero, so that regex ran straight
    # past it and stopped at the first two-space `</div>` it could find, which
    # is inside the upload modal. The fragment then contained the modal, the
    # empty state and their conditionals, and every measurement below was
    # being taken on markup the row never renders. It did not error; it just
    # measured the wrong thing.
    _i = SRC.find('<div class="table-container">')
    check('the table markup could be located for rendering', _i >= 0)
    _depth, _j = 0, _i
    while _j < len(SRC):
        if SRC.startswith('<div', _j):
            _depth += 1
        elif SRC.startswith('</div>', _j):
            _depth -= 1
            if _depth == 0:
                _j += 6
                break
        _j += 1
    f = SRC[_i:_j] if _i >= 0 else ''
    check('  and its closing tag was found by counting, not by indentation',
          f.endswith('</div>') and f.count('<div') == f.count('</div>'))
    check('  CONTROL: the fragment stops before the upload modal',
          'uploadModal' not in f)
    f = re.sub(r'\{%\s*if\s+not\s+tenants\s*%\}.*?\{%\s*endif\s*%\}',
               '', f, flags=re.S)
    # NESTED conditionals, resolved innermost-first.
    #
    # The flat version of this - one non-greedy pass - is fine on Suppliers,
    # Properties and Tenants, whose action cells are a flat if/else each. This
    # page nests them: `{% if perms %}{% if agreement %}Delete{% else %}Upload
    # {% endif %}{% else %}(disabled){% endif %}`. A non-greedy `.*?` matched
    # the WRONG endif, and the fragment came out with three buttons in a
    # two-button row - Delete, Upload's twin, and a disabled span that can
    # never appear beside them. Every measurement taken on that fragment was
    # being taken on markup the template cannot produce.
    #
    # The guard is `(?!\{%\s*if)`: only a block containing no further `{% if`
    # is resolved, so the innermost pair goes first and the outer one is a
    # flat if/else by the time it is reached. Bounded, so a malformed template
    # cannot spin here.
    # The no-else form must also refuse a body containing `{% else %}`, or it
    # swallows an if/else pair whole and keeps BOTH branches. That is what put
    # a third button in a two-button row even after the nesting was handled:
    # `{% if perms %}Delete{% else %}(disabled){% endif %}` matched the
    # bodiless pattern, the `{% else %}` tag was deleted as ordinary text, and
    # Delete and the disabled twin were rendered side by side.
    _body = r'((?:(?!\{%\s*if)(?!\{%\s*else)[\s\S])*?)'
    _open = r'\{%\s*if[^%]*%\}'
    for _ in range(12):
        _was = f
        f = re.sub(_open + _body + r'\{%\s*else\s*%\}'
                   r'(?:(?!\{%\s*if)(?!\{%\s*else)[\s\S])*?'
                   r'\{%\s*endif\s*%\}', r'\1', f)
        f = re.sub(_open + _body + r'\{%\s*endif\s*%\}', r'\1', f)
        if f == _was:
            break
    check('  every conditional in the fragment was resolved',
          '{% if' not in f and '{% else' not in f)
    fm = re.search(r'\{%\s*for[^%]*%\}(.*?)\{%\s*endfor\s*%\}', f, re.S)
    # The harness resolves every {% if %} to its FIRST branch, so every
    # rendered row comes out "agreement attached" - View plus Delete - and
    # the two things this round actually introduced, the disabled twin and
    # the upload tone, would never appear in the DOM at all. The checks below
    # would then have measured nothing and reported PASS by being skipped,
    # which is exactly how the Properties grey-pill check went vacuous.
    #
    # So one row is deliberately switched to the else-branch classes.
    rows = ''
    for i, name in enumerate(('Andreas Georgiou', 'Maria Christou',
                              'Petros Loizou')):
        r = fm.group(1).replace('{{ tenant.tenant_name }}', name)
        if i == 2:
            r = (r.replace('icon-action-btn icon-view',
                           'icon-action-btn icon-disabled', 1)
                  .replace('icon-action-btn icon-delete',
                           'icon-action-btn icon-upload', 1))
        if i == 0:
            r = r.replace('>{{ tenant.tenant_lease_end_date|date:"Y-m-d" }}<',
                          '><span class="end-date-expired">2025-03-14</span><')
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
            check('  and there are exactly TWO of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 2)
            check('  one actions cell per row, not four',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child td').length")
                  == 4 + 1 + 1)   # 4 data columns + actions + the mobile bar cell


            exp = cs(pg, '.end-date-expired', ['color'])
            check('desktop: an expired lease date reads red (%s)'
                  % exp['color'], exp['color'] == 'rgb(179, 38, 30)')
            check('  and it is the token red, not Bootstrap\'s #dc3545',
                  exp['color'] != 'rgb(220, 53, 69)')

            up = cs(pg, '.icon-upload', ['color', 'width'])
            ed = cs(pg, 'thead th', ['color'])
            check('desktop: Upload gets its colour from base.html (%s)'
                  % up['color'], up['color'] == 'rgb(37, 99, 235)')
            check('  and it is 34px like every other row button',
                  up['width'] == '34px')
            check('  CONTROL: it is not simply inheriting the page ink',
                  up['color'] != ed['color'])
            vw = cs(pg, '.icon-view', ['color'])
            check('desktop: View is the accent teal (%s)' % vw['color'],
                  vw['color'] == 'rgb(14, 124, 139)')
            dis = cs(pg, '.icon-disabled', ['color', 'width'])
            check('desktop: the disabled twin holds the slot (%s wide)'
                  % dis['width'], dis['width'] == '34px')
            check('  and reads as unavailable, not as an action',
                  dis['color'] not in (up['color'], vw['color']))

            r1 = cs(pg, 'tbody tr:nth-child(1)', ['background-color'])
            r2 = cs(pg, 'tbody tr:nth-child(2)', ['background-color'])
            check('desktop: no zebra - both rows the same',
                  r1['background-color'] == r2['background-color'])

            th = cs(pg, 'thead th', ['text-transform', 'background-color'])
            check('desktop: the header reads as a header',
                  th['text-transform'] == 'uppercase')
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
            # FOUR, not three. Properties carries an extra action, and the
            # markup declares cols-4 so base.html's default three-column grid
            # does not wrap the last button onto a second row - a break that
            # would only ever appear on a phone.
            check('mobile: the action bar is a 2-up grid (cols-2)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 2)
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
