"""test_table_tenant_report - the Tenant Details report is on the standard.

    python test_table_tenant_report.py

Run from the project root, after apply_table_tenant_report.py.

This page is a detail screen, so most of the table suite does not apply. What
does apply, and harder than anywhere else, is PRINT. This template carries its
own `@media print` which used to re-colour the renewal badges by name; rename
those classes and the block styles nothing, silently, and the badges print in
one colour while the screen shows another. Nothing errors. So the browser half
below renders the page TWICE - once on screen and once in print media - and
compares.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_report.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(PAGE):
    sys.exit('! pages/templates/tenant_report.html not found - run from root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


SRC = read(PAGE)
BASE_SRC = read(BASE)
CSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', SRC, re.S | re.I))
PRINT_CSS = CSS[CSS.find('@media print'):] if '@media print' in CSS else ''

# ==================================================================== MARKUP
check('the card is the house card', 'alv-card alv-card-lead' in SRC)
check('  with exactly one head', SRC.count('alv-card-head') == 1)
check('  and exactly one body', SRC.count('alv-card-body') == 1)
check('  and the div tags still balance (%d/%d)'
      % (SRC.count('<div'), SRC.count('</div>')),
      SRC.count('<div') == SRC.count('</div>'))
check('  the tenant name is the card title, not a loose h3',
      'alv-card-title' in SRC and 'property-name' not in SRC)

for gone in ('property-card', 'property-name', 'renewal-status-badge',
             'renewal-pending', 'renewal-declined', 'renewal-signed',
             'badge-success', 'badge-secondary'):
    check('  %s is gone from the file entirely' % gone, gone not in SRC)

# ------------------------------------------------------------- the six colours
check('Active uses the good pill', 'alv-pill-good' in SRC)
check('  and not-Active uses the neutral one', 'alv-pill-neutral' in SRC)
check('  renewal PENDING is amber',
      re.search(r"'pending'.*?alv-pill-attn", SRC, re.S) is not None)
# The decision of this round: Declined comes off red. A tenant declining to
# renew is an answer, not a failure - the same argument that took Inactive off
# red two pages ago. It stays amber rather than going grey because somebody
# still has to find another tenant.
check('  renewal DECLINED is amber, not red',
      re.search(r"'declined'.*?alv-pill-attn", SRC, re.S) is not None)
check('  CONTROL: no pill on this page is on the danger scale',
      'alv-pill-bad' not in SRC)
check('  renewal SIGNED is the only settled outcome, and it is good',
      re.search(r"'new_lease_signed'.*?alv-pill-good", SRC, re.S) is not None)

check('the expired end date survives', '.highlight-red' in CSS)
check('  on the token, not Bootstrap\'s #dc3545',
      re.search(r'\.highlight-red\s*\{[^}]*var\(--alv-bad\)', CSS) is not None)
check('  CONTROL: no raw Bootstrap red anywhere in the style block',
      '#dc3545' not in CSS)
# The FILLS, not the hex anywhere. #6c757d is also Bootstrap's grey TEXT, and
# this page legitimately uses it on the subtitle and the mobile label - a
# blanket "the hex is gone" check failed on two colours that were never the
# problem, and the fix for a check that is wrong is to make it right rather
# than to widen what it tolerates.
for hexv, what in (('#28a745', 'the solid green'),
                   ('#6c757d', 'the solid grey'),
                   ('#ffc107', 'the solid amber'),
                   ('#dc3545', 'the solid red')):
    check('  CONTROL: %s is no longer used as a BADGE FILL' % what,
          not re.search(r'background(?:-color)?:\s*' + re.escape(hexv), CSS))
check('  CONTROL: and the page still uses the grey as ordinary text',
      re.search(r'color:\s*#6c757d', CSS) is not None)

# The stylesheet must still be a stylesheet. A rewritten selector that lost
# its block leaves the style tags balanced, the markup balanced, and the CSS
# broken - which is exactly what the first run of this patcher did, closing
# the mobile @media block early and taking the date-chip sizing with it.
check('CSS braces balance (%d/%d)' % (CSS.count('{'), CSS.count('}')),
      CSS.count('{') == CSS.count('}'))
check('  and no selector survives without a block',
      not re.findall(r'\}\s*([^{}@/\s][^{}]*?)\s*\}', CSS))

# ------------------------------------------- THE PRINT BLOCK, which was the risk
check('the page still has a print block of its own', bool(PRINT_CSS))
check('  and it no longer names a renewal class that does not exist',
      '.renewal-' not in PRINT_CSS)
check('  nor .property-card', '.property-card' not in PRINT_CSS)
check('  but it DOES still lay the detail rows out for paper',
      '.detail-row' in PRINT_CSS and '.detail-label' in PRINT_CSS)
check('base.html governs how a pill prints',
      re.search(r'@media print[\s\S]*?\.alv-pill,\s*\n?\s*\.alv-tag',
                BASE_SRC) is not None)
check('  and hides the Back button on paper',
      re.search(r'@media print[\s\S]{0,900}\.back-button', BASE_SRC)
      is not None)

# ====================================== WHAT MUST NOT HAVE GONE
for sel, why in (('.report-container', 'the page shell'),
                 ('.report-content', 'the sheet'),
                 ('.header-container', 'the title row'),
                 ('.report-title-main', 'the title'),
                 ('.detail-groups', 'the column grid'),
                 ('.detail-group', 'a group'),
                 ('.section-title', 'a group heading'),
                 ('.detail-row', 'a label/value pair'),
                 ('.detail-label', 'the label'),
                 ('.detail-value', 'the value'),
                 ('.date-box', 'the date chip')):
    check('  KEPT %-20s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\s*[,{:.]', CSS) is not None)

_sels = [' '.join(re.sub(r'/\*.*?\*/', '', mm.group(1), flags=re.S).split())
         for mm in re.finditer(r'([^{}]+)\{', CSS)]


def group(prefix):
    return sum(1 for x in _sels if prefix in x)


for prefix, floor, why in (('.detail', 9, 'the label/value machinery'),
                           ('.report', 8, 'the page shell and title'),
                           ('.date-box', 2, 'the date chip')):
    check('  %-12s still has %d rules (>= %d: %s)'
          % (prefix, group(prefix), floor, why), group(prefix) >= floor)
for prefix in ('.property-', '.badge', '.renewal-'):
    check('  %-12s has 0 rules left' % prefix, group(prefix) == 0)

# A selector list that mixed replaced names with surviving ones must have been
# REWRITTEN, not kept whole. Kept whole it still works - and carries two names
# that no longer exist, which is how the next person concludes they do.
_mixed = [s for s in _sels
          if '.date-box' in s and ('badge' in s or 'renewal' in s)]
check('  no surviving selector still names a replaced class', not _mixed)
for s in _mixed[:3]:
    print('        still: %s' % s[:70])

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

    # Render the page's OWN card, not a copy of it.
    _i = SRC.find('<div class="alv-card alv-card-lead">')
    check('the card markup could be located for rendering', _i >= 0)
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
    f = SRC[_i:_j]
    check('  and its close was found by counting, not by indentation',
          f.count('<div') == f.count('</div>'))

    # Resolve conditionals innermost-first, refusing a body that contains
    # another {% if %} or a stray {% else %} - see the lease-agreement suite
    # for what the naive version did to a two-button row.
    _body = r'((?:(?!\{%\s*if)(?!\{%\s*else)(?!\{%\s*elif)[\s\S])*?)'
    _open = r'\{%\s*if[^%]*%\}'
    for _ in range(12):
        _was = f
        f = re.sub(_open + _body + r'\{%\s*else\s*%\}'
                   r'(?:(?!\{%\s*if)(?!\{%\s*else)[\s\S])*?\{%\s*endif\s*%\}',
                   r'\1', f)
        f = re.sub(_open + _body + r'\{%\s*endif\s*%\}', r'\1', f)
        if f == _was:
            break

    # THE SAME TRAP AS EVERY ROUND BEFORE THIS. Flattening resolves each
    # branch to its first, so Active comes out good and the renewal pill comes
    # out Pending - and alv-pill-neutral and alv-pill-good would never reach
    # the DOM for the renewal chain at all. Add the other states explicitly,
    # each in a labelled probe, so every colour this round decided is actually
    # measured rather than skipped.
    f = re.sub(r'\{[{%][^}%]*[%}]\}', 'x', f)
    f += ('<div id="probes">'
          '<span class="alv-pill alv-pill-good" id="p-good">Yes</span>'
          '<span class="alv-pill alv-pill-neutral" id="p-neutral">No</span>'
          '<span class="alv-pill alv-pill-attn" id="p-attn">Pending</span>'
          '<span class="alv-pill alv-pill-attn" id="p-declined">Declined</span>'
          '<span class="alv-pill alv-pill-good" id="p-signed">Signed</span>'
          '<span class="date-box highlight-red" id="p-red">2025-03-14</span>'
          '<a href="#" class="btn back-button" id="p-back">Back</a>'
          '</div>')

    tmp = os.path.join(ROOT, '_report_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>%s</style><style>%s</style><style>%s</style></head>'
        '<body>%s</body></html>' % (BOOT, BASECSS, CSS, f))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            if not os.path.exists(exe):
                for cand in ('/opt/pw-browsers/chromium-1194/chrome-linux/'
                             'chrome',):
                    if os.path.exists(cand):
                        exe = cand
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())

            def cs(pg, sel, props):
                got = pg.evaluate(
                    """([s,ps])=>{const e=document.querySelector(s);
                       if(!e)return null;const c=getComputedStyle(e);
                       const o={};for(const p of ps)o[p]=c.getPropertyValue(p);
                       return o;}""", [sel, props])
                if got is None:
                    check('  !! %s is not in the rendered page' % sel, False)
                    return {q: None for q in props}
                return got

            pg = br.new_page(viewport={'width': 1440, 'height': 900})
            pg.goto('file://' + tmp)

            card = cs(pg, '.alv-card', ['background-color', 'border-top-width'])
            check('screen: the card is the house surface (%s)'
                  % card['background-color'],
                  card['background-color'] == 'rgb(255, 255, 255)')
            head = cs(pg, '.alv-card-head', ['font-size', 'background-color'])
            check('screen: the lead card names the tenant at 18px (%s)'
                  % head['font-size'], head['font-size'] == '18px')

            good = cs(pg, '#p-good', ['background-color', 'color'])
            neut = cs(pg, '#p-neutral', ['background-color'])
            attn = cs(pg, '#p-attn', ['background-color', 'color'])
            decl = cs(pg, '#p-declined', ['background-color'])
            sign = cs(pg, '#p-signed', ['background-color'])
            red = cs(pg, '#p-red', ['color'])

            check('screen: Active is a TINT, not the solid #28a745 (%s)'
                  % good['background-color'],
                  good['background-color'] not in ('rgb(40, 167, 69)',))
            check('  and not-Active is grey', neut['background-color']
                  == 'rgb(238, 241, 242)')
            check('screen: Pending is amber (%s)' % attn['background-color'],
                  attn['background-color'] == 'rgb(253, 243, 221)')
            check('screen: Declined is the SAME amber as Pending',
                  decl['background-color'] == attn['background-color'])
            check('  CONTROL: and specifically not the danger tint',
                  decl['background-color'] != 'rgb(251, 234, 233)')
            check('screen: Signed is green, and differs from both',
                  sign['background-color'] == good['background-color']
                  and sign['background-color'] != attn['background-color'])
            check('screen: an expired end date is the token red (%s)'
                  % red['color'], red['color'] == 'rgb(179, 38, 30)')

            # ---- and now on paper. This is the half that this page needed.
            pg.emulate_media(media='print')
            p_attn = cs(pg, '#p-attn',
                        ['background-color', 'border-top-width', 'color'])
            p_decl = cs(pg, '#p-declined', ['background-color', 'color'])
            p_back = cs(pg, '#p-back', ['display'])
            check('print: base.html outlines a pill rather than tinting it '
                  '(%s border)' % p_attn['border-top-width'],
                  p_attn['border-top-width'] not in ('0px', None))
            check('print: Pending and Declined still match each other',
                  p_decl['color'] == p_attn['color'])
            check('  CONTROL: neither prints the old solid Bootstrap fill',
                  p_attn['background-color'] != 'rgb(255, 193, 7)'
                  and p_decl['background-color'] != 'rgb(220, 53, 69)')
            check('print: the Back button is not on the paper (%s)'
                  % p_back['display'], p_back['display'] == 'none')
            pg.emulate_media(media='screen')
            s_back = cs(pg, '#p-back', ['display'])
            check('  CONTROL: it IS on the screen (%s)' % s_back['display'],
                  s_back['display'] != 'none')
            pg.close()

            pg = br.new_page(viewport={'width': 375, 'height': 900})
            pg.goto('file://' + tmp)
            # A CRASH IS NOT A REPORT. On the un-migrated page .alv-card
            # does not exist, and the bare evaluate() below dereferenced null
            # - the whole suite died with a TypeError instead of printing 40
            # failures. The negative control is the only thing that proves
            # this suite bites, so it is the one run that must not throw.
            _w = pg.evaluate("()=>{const e=document.querySelector('.alv-card');"
                             "return e ? e.scrollWidth : null;}")
            check('mobile: the card still fits the viewport (%s)'
                  % ('%dpx' % _w if _w is not None else 'no card'),
                  _w is not None and _w <= 375)
            _g = cs(pg, '.detail-groups', ['grid-template-columns'])
            check('mobile: the detail grid collapses to one column',
                  _g['grid-template-columns'] is not None
                  and len(_g['grid-template-columns'].split()) == 1)
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
