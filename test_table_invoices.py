#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Physical Invoices and Customers are on the table standard.

Run from the repo root. Needs Playwright's chromium.

THE HEADLINE. This page redefined seven rules base.html already owns, with
literal Bootstrap colours, and won on document order - so its Send icon was
blue while every other page's was house teal. That is what section 3 measures,
and it is measured in a browser rather than by grepping for a hex, because
what matters is which rule WINS.
"""
import os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
PI   = os.path.join(TPL, 'physical_invoice_list.html')
CL   = os.path.join(TPL, 'customer_list.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'physical_invoices.py')

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def sels(t):
    css = re.sub(r'/\*.*?\*/', '', css_of(t), flags=re.S)
    out = []
    for m in re.finditer(r'([^{}]+)\{[^{}]*\}', css):
        s = ' '.join(m.group(1).split())
        if s and not s.startswith('@'):
            out.append(s)
    return out


BASE, PIT, CLT, VW = read(os.path.join(TPL, 'base.html')), read(PI), read(CL), read(VIEW)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

head('1. base.html closed the gap in its own vocabulary')
_b = sels(BASE)
for s in ('.icon-color-approve', '.icon-color-unapprove', '.icon-color-send',
          '.icon-duplicate', '.icon-color-duplicate'):
    check('base defines %-22s' % s, s in _b)
    check('  and only once', _b.count(s) == 1)
check('  Duplicate is a NAME on --alv-edit, not a seventh colour',
      re.search(r'\.icon-duplicate\s*\{[^}]*var\(--alv-edit\)', css_of(BASE)) is not None)
check('  and no new hex entered base.html for it',
      '#6f42c1' not in BASE)
check('base still has the four it always had',
      all(s in _b for s in ('.icon-color-edit', '.icon-color-view',
                            '.icon-color-delete', '.icon-color-upload')))
_c = css_of(BASE)
check('base braces still balance (%d/%d)' % (_c.count('{'), _c.count('}')),
      _c.count('{') == _c.count('}'))

head('2. the page stopped redefining what base owns')
STALE = ('.icon-action-btn', '.icon-view', '.icon-approve', '.icon-unapprove',
         '.icon-send', '.mobile-action-icon', '.icon-color-view',
         '.icon-trash', '.icon-duplicate', '.icon-color-approve',
         '.icon-color-send', '.icon-color-trash')
_ps = sels(PIT)
for s in STALE:
    check('  %-22s is gone from the page' % s, s not in _ps)
check('  and so are the hexes they carried',
      not any(h in PIT for h in ('#007bff', '#28a745', '#fd7e14', '#6f42c1')),
      '' if not any(h in PIT for h in ('#007bff', '#28a745', '#fd7e14', '#6f42c1'))
      else 'still: ' + ', '.join(h for h in ('#007bff', '#28a745', '#fd7e14', '#6f42c1')
                                 if h in PIT))
check('  the markup uses the house delete name',
      'icon-trash' not in PIT and 'icon-delete' in PIT)
check('  the page still has CSS of its own (%d lines)' % css_of(PIT).count('\n'),
      css_of(PIT).count('\n') > 60)

head('3. both tables joined the standard')
check('physical_invoice_list is on .alv-table',
      re.search(r'<table class="table alv-table pi-table">', PIT) is not None)
for gone in ('table-bordered', 'table-striped', 'text-center pi-table'):
    check('  %-18s is gone from its class list' % gone,
          gone not in re.search(r'<table[^>]*>', PIT).group(0))
check('customer_list is on .alv-table',
      re.search(r'<table class="table alv-table customers-table">', CLT) is not None)
check('  and it has ONE actions column now',
      len(re.findall(r'<th[^>]*>Actions</th>', CLT)) == 1
      and '>Edit</th>' not in CLT and '>Delete</th>' not in CLT)
_w = [float(x) for x in re.findall(r'width:\s*([\d.]+)%',
      re.search(r'<thead.*?</thead>', CLT, re.S).group(0))]
check('  five columns, summing to 100 (%s)' % _w, len(_w) == 5 and abs(sum(_w) - 100) < 0.51)
check('  its two buttons share one wrapper', CLT.count('class="row-actions"') == 1)
check('  and every permission gate survived (%d)' % CLT.count('{% if perms.'),
      CLT.count('{% if perms.') == 4)

head('4. Type is a tag, Status is a pill the view named')
# The class is BUILT BY A CONDITIONAL - `alv-tag-{% if %}sky{% else %}plum
# {% endif %}` - so the literal "alv-tag-sky" never appears in the file and a
# substring test for it fails on markup that is entirely correct. Match the
# shape that is actually written, and check both arms are reachable.
_tag = re.search(r'class="alv-tag alv-tag-\{%\s*if row\.is_customer\s*%\}'
                 r'(\w+)\{%\s*else\s*%\}(\w+)\{%\s*endif\s*%\}"', PIT)
check('Type wears .alv-tag, not a status colour', _tag is not None)
check('  customer -> %s, tenant -> %s'
      % (_tag.group(1) if _tag else '?', _tag.group(2) if _tag else '?'),
      _tag is not None and {_tag.group(1), _tag.group(2)} == {'sky', 'plum'})
check('  and the old .type-badge vocabulary is gone', 'type-badge' not in PIT)
check('  base really defines both tones',
      '.alv-tag-sky' in _b and '.alv-tag-plum' in _b)
check('Status reads its class from the view',
      '{{ row.status_pill }}' in PIT and 'status-{{ row.status }}' not in PIT)
check('  the view defines the map', '_STATUS_PILL' in VW)
for k, v in (('draft', 'attn'), ('approved', 'info'), ('sent', 'good')):
    check('    %-9s -> alv-pill-%s' % (k, v),
          re.search(r'"%s":\s*"alv-pill-%s"' % (k, v), VW) is not None)
check('  an unknown status falls to neutral rather than to nothing',
      'alv-pill-neutral' in VW)
check('  and the row dict carries it', '"status_pill"' in VW)
import py_compile
try:
    py_compile.compile(VIEW, doraise=True)
    check('  physical_invoices.py compiles', True)
except Exception as e:
    check('  physical_invoices.py compiles', False, str(e)[:70])
check('the header counts use the same scale as the column',
      PIT.count('alv-pill-attn') >= 1 and PIT.count('alv-pill-info') >= 1
      and PIT.count('alv-pill-good') >= 1 and 'count-pill' not in PIT)


# ---------------------------------------------------------------------------
head('5. the browser - which rule actually WINS')
# Grepping for a hex proves the literal is gone. It does not prove the icon is
# the right colour, because that is decided by the cascade, not by the file.
# The page's <style> comes AFTER base's, so a page rule of equal specificity
# wins - which is the whole reason this defect existed.
FRAG = ("<div class='table-container'><table class='table alv-table pi-table'>"
        "<tbody><tr><td class='desktop-action-cell pi-actions-cell'>"
        "<div class='row-actions'>"
        + ''.join("<a href='#' class='icon-action-btn icon-%s'>x</a>" % k
                  for k in ('view', 'approve', 'unapprove', 'send',
                            'duplicate', 'delete'))
        + "</div></td></tr></tbody></table></div>"
        + ''.join("<i class='mobile-action-icon icon-color-%s'>x</i>" % k
                  for k in ('approve', 'unapprove', 'send', 'duplicate')))

WANT = {'view': 'rgb(14, 124, 139)', 'approve': 'rgb(30, 125, 79)',
        'unapprove': 'rgb(154, 106, 8)', 'send': 'rgb(14, 124, 139)',
        'duplicate': 'rgb(37, 99, 235)', 'delete': 'rgb(179, 38, 30)'}
BOOTSTRAP_WAS = {'approve': 'rgb(40, 167, 69)', 'unapprove': 'rgb(253, 126, 20)',
                 'send': 'rgb(0, 123, 255)', 'duplicate': 'rgb(111, 66, 193)'}


async def render(base_txt, page_txt):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page()
        await pg.set_content("<style>%s</style><style>%s</style><style>%s</style>"
                             "<body>%s</body>"
                             % (BOOTSTRAP, css_of(base_txt), css_of(page_txt), FRAG))
        await pg.wait_for_timeout(50)
        out = await pg.evaluate("""()=>{const o={};
          for (const k of ['view','approve','unapprove','send','duplicate','delete']) {
            const e=document.querySelector('.icon-'+k);
            o[k]=e?getComputedStyle(e).color:null; }
          for (const k of ['approve','unapprove','send','duplicate']) {
            const e=document.querySelector('.icon-color-'+k);
            o['m-'+k]=e?getComputedStyle(e).color:null; }
          return o;}""")
        await br.close()
        return out


async def align(page_txt, page_name):
    """Does the Actions HEADING sit over the buttons it labels?

    Measured on the heading's TEXT, not on its cell. The cell's centre never
    moves - it is the column - so comparing cell centres reports "off by 1"
    whether the heading is centred or hard left. The first version of this
    check did exactly that and called a 105px miss a pass. A range around the
    text node is what the eye actually sees.
    """
    from playwright.async_api import async_playwright
    m = re.search(r'<table', page_txt)
    frag = page_txt[m.start():page_txt.find('</table>', m.start()) + 8]
    prev = None
    while prev != frag:
        prev = frag
        frag = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*else\s*%\}'
                      r'((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}', r'\1', frag, flags=re.S)
        frag = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}',
                      r'\1', frag, flags=re.S)
    frag = re.sub(r'\{\{[^}]*\}\}', 'x', re.sub(r'\{%[^%]*%\}', '', frag))
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1500, 'height': 600})
        await pg.set_content("<style>%s</style><style>%s</style><style>%s</style>"
                             "<body style='padding:20px'><div class='table-container'>%s</div></body>"
                             % (BOOTSTRAP, css_of(BASE), css_of(page_txt), frag))
        await pg.wait_for_timeout(50)
        g = await pg.evaluate("""()=>{
          const ths=[...document.querySelectorAll('th')];
          const th=ths.find(e=>/Actions/.test(e.textContent));
          const td=document.querySelector('td.cell-actions, td[data-label="Actions"]');
          if(!th||!td) return null;
          const r=document.createRange(); r.selectNodeContents(th);
          const tr=r.getBoundingClientRect();
          const btns=[...td.querySelectorAll('.icon-action-btn')];
          if(!btns.length) return null;
          const bl=Math.min(...btns.map(b=>b.getBoundingClientRect().left));
          const brr=Math.max(...btns.map(b=>b.getBoundingClientRect().right));
          return {off:Math.abs((tr.left+tr.width/2)-((bl+brr)/2)), n:btns.length};}""")
        await br.close()
    return g


async def main():
    now = await render(BASE, PIT)
    for k, want in WANT.items():
        check('%-10s renders %s' % (k, want), now.get(k) == want, str(now.get(k)))
    check('  and Send is specifically NOT Bootstrap blue',
          now.get('send') != BOOTSTRAP_WAS['send'])
    for k in ('approve', 'unapprove', 'send', 'duplicate'):
        check('  the mobile %-10s variant resolves too' % k,
              now.get('m-' + k) == WANT[k], str(now.get('m-' + k)))

    head('5b. the Actions heading sits over its buttons')
    for name, txt in (('physical_invoice_list', PIT), ('customer_list', CLT)):
        g = await align(txt, name)
        if not check('%-22s the heading was measurable' % name, g is not None):
            continue
        check('%-22s   heading text is over its %d buttons (%.0fpx off)'
              % (name, g['n'], g['off']), g['off'] <= 2)
    # CONTROL: the pre-round page had no class on that heading at all, so it
    # sat hard left of the buttons. 105px, not a rounding error.
    _bak = PI + '.bak_actionsalign'
    if os.path.exists(_bak):
        g0 = await align(read(_bak), 'before')
        check('  CONTROL: before the fix it was %.0fpx off' % (g0['off'] if g0 else 0),
              g0 is not None and g0['off'] > 20)

    head('6. the negative control')
    bp = os.path.join(TPL, 'base.html') + '.bak_tableinv'
    pp = PI + '.bak_tableinv'
    if not (os.path.exists(bp) and os.path.exists(pp)):
        check('backups exist to compare against', False,
              '(run apply_table_invoices.py first)')
        return
    was = await render(read(bp), read(pp))
    # The defect must have been REAL before the round, or this suite is
    # measuring a problem nobody had.
    wrong = {k: was.get(k) for k, v in BOOTSTRAP_WAS.items() if was.get(k) == v}
    check('CONTROL: before the round, %d icon(s) were the Bootstrap colour'
          % len(wrong), len(wrong) >= 3,
          ', '.join('%s=%s' % (k, v) for k, v in wrong.items()))
    check('  Send WAS blue', was.get('send') == BOOTSTRAP_WAS['send'], str(was.get('send')))
    check('  and the mobile variants did not resolve at all on desktop',
          was.get('m-send') not in (WANT['send'], BOOTSTRAP_WAS['send']),
          str(was.get('m-send')))
    old = read(pp)
    _stale_then = [s for s in STALE if s in sels(old)]
    check('  the page really did redefine %d of base\'s rules'
          % len(_stale_then), len(_stale_then) >= 8)
    _probes = [('on .alv-table', lambda t: 'alv-table' in t),
               ('Type is a tag', lambda t: 'alv-tag-sky' in t),
               ('Status from the view', lambda t: '{{ row.status_pill }}' in t),
               ('no Bootstrap hex', lambda t: '#007bff' not in t)]
    _would = sum(1 for _, fn in _probes if not fn(old))
    check('  and %d of the static checks above fail on it' % _would, _would >= 3)

asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
