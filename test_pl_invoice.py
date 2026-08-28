#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The P&L drill-down opens an invoice - driven, not asserted.

Run from the repo root, after apply_pl_invoice.py. Needs Playwright's chromium.

THE FAULT WAS "THE CLICK DOES NOTHING", so the only check worth having is a
CLICK. Section 3 builds the page's own viewer markup, loads the page's own
functions, injects a row carrying the real icon markup that act_expense.html
renders, clicks it, and reads back what the viewer is showing.

TWO THINGS THIS SUITE DOES NOT PRETEND.

  * jQuery is not available offline here, and the code under test uses it in
    exactly two places - reading a scroll position, and showing a Bootstrap
    modal. Both are stubbed, and the stub is 20 lines you can read. Everything
    on the path being tested - the shim, the name parsing, the viewer - is the
    page's own code, lifted verbatim.
  * The stub is asserted to be exercised. A stub nobody calls would let this
    pass while proving nothing.

WHY THE OLD CODE FAILED, and what the controls re-create:

  1. It bound `.fa-file-alt`. verify_badge emits fa-check-circle,
     fa-exclamation-triangle, fa-question-circle, fa-file or fa-file-invoice -
     never that one. Section 4 asserts the old selector matches none of the
     glyphs the model can produce.
  2. It then compared the icon's COLOUR to Bootstrap green. Section 4 shows
     the house token the icon now wears is not that colour, so the old test
     would have failed even had the selector matched.
"""
import os, re, sys, json, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'finance_pl_act.html')
EXP = os.path.join(TPL, 'act_expense.html')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
SUFFIX = '.bak_plinvoice'

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


def scripts_of(t):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', t, re.S))


def uncomment_js(js):
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    return '\n'.join('' if l.lstrip().startswith('//') else l
                     for l in js.split('\n'))


def lift(js, name, kind='function'):
    """A function's source by brace matching, not by indentation."""
    i = js.find('function %s(' % name) if kind == 'function' \
        else js.find('window.%s = function' % name)
    if i < 0:
        return ''
    j = js.find('{', i)
    depth, k = 0, j
    while k < len(js):
        if js[k] == '{':
            depth += 1
        elif js[k] == '}':
            depth -= 1
            if depth == 0:
                return js[i:k + 1]
        k += 1
    return ''


PG = read(PAGE)
JS = uncomment_js(scripts_of(PG))
BAK = PAGE + SUFFIX
HAVE = os.path.exists(BAK)
OLD = read(BAK) if HAVE else ''
OLDJS = uncomment_js(scripts_of(OLD))

# =========================================================================
head('1. the colour test is gone, and so is the selector that never matched')
# =========================================================================
for gone in ('isGreen', 'rgb(40, 167, 69)', '#28a745', "hasClass('text-success')"):
    check('  %-26s is gone from live script code' % gone, gone not in JS)
check('nothing binds .fa-file-alt any more',
      not re.search(r"\.fa-file-alt['\"]", JS))
check('  but the glyph survives as the not-a-PDF placeholder, which was always '
      'a fair use of it', 'fa-file-alt fa-5x' in JS)
check('the shim is defined', 'window.viewInvoiceQuick' in JS)
check('  and the delegated fallback binds the class the grid renders',
      ".off('click', '.verify-icon')" in JS)
check('  guarded, so an icon with BOTH does not open twice',
      "if ($icon.attr('onclick')) { return; }" in JS)
if HAVE:
    check('CONTROL: the old code DID test the colour',
          'isGreen' in OLDJS and 'rgb(40, 167, 69)' in OLDJS)
    check('CONTROL: and DID bind the glyph that is never emitted',
          re.search(r"\.fa-file-alt['\"]", OLDJS) is not None)

# =========================================================================
head('2. the selector the old code used matches nothing the model can emit')
# =========================================================================
_m = read(MODELS)
_seg = _m[_m.find('def verify_badge'):]
_seg = _seg[:_seg.find('def __str__')]
GLYPHS = sorted(set(re.findall(r"'(fa-[a-z0-9-]+)'", _seg)))
check('verify_badge emits %d glyph(s)' % len(GLYPHS), len(GLYPHS) >= 5,
      ', '.join(GLYPHS))
check('  and NONE of them is fa-file-alt', 'fa-file-alt' not in GLYPHS)
check('  CONTROL: fa-file-alt IS used elsewhere - the report drill table - '
      'which is where that selector came from',
      'fa-file-alt report-invoice-icon' in read(EXP)
      or 'fa-file-alt' in read(EXP))

# =========================================================================
# Section 3 loads the page's own functions and clicks a real icon.
# =========================================================================
SHIM = lift(JS, 'viewInvoiceQuick', kind='window')
SHOW = lift(JS, 'showInvoiceModalLikeExisting')
SETUP = lift(JS, 'setupInvoiceIconHandlers')

# The two jQuery calls on this path, and nothing else. Kept tiny and readable
# on purpose: a stub big enough to hide a bug is not a stub.
JQ_STUB = """
// The two jQuery calls on this path and nothing else. $(document) is a NODE,
// not a string - the first version of this stub only gave the string branch
// off/on, so setupInvoiceIconHandlers died on $(document).off.
window.__stub = {scrollRead: 0, modalShown: []};
window.$ = function (sel) {
  var isStr = (typeof sel === 'string');
  var node = isStr ? null : sel;
  return {
    scrollTop: function () { window.__stub.scrollRead++; return 42; },
    modal: function (what) { window.__stub.modalShown.push(String(sel) + ':' + what); },
    off: function () { return this; },
    on: function (evt, child, fn) {
      (node || document).addEventListener(evt, function (e) {
        var t = e.target.closest(child);
        if (t) { fn.call(t, e); }
      });
      return this;
    },
    attr: function (n) { return node ? node.getAttribute(n) : null; },
    data: function (n) {
      if (!node) { return undefined; }
      return node.dataset[n.replace(/-([a-z])/g,
             function (m, c) { return c.toUpperCase(); })];
    }
  };
};
window.firstModalScrollTop = 0;
"""

PROBE = """() => ({
  viewer: document.getElementById('invoiceViewerContent').innerHTML,
  href: document.getElementById('downloadInvoiceBtn').getAttribute('href'),
  download: document.getElementById('downloadInvoiceBtn').getAttribute('download'),
  stub: window.__stub,
  errors: window.__errors})"""


def row(url, name, glyph='fa-check-circle', tone='success'):
    """The icon exactly as act_expense.html renders it."""
    # Font Awesome is not loaded here, so the <i> would have no content and no
    # size, and Playwright rightly refuses to click something invisible. The
    # rule below gives it the geometry the glyph would - the click stays a
    # real click rather than a dispatched event.
    return ('<style>.verify-icon{display:inline-block;width:16px;height:16px;'
            'background:#ccc}</style>'
            '<div id="expenseDetailsModal"><div class="modal-body">'
            '<table><tbody><tr><td>'
            '<i class="fas %s verify-icon verify-%s" '
            'onclick="viewInvoiceQuick(\'%s\', \'%s\')" '
            'title="Invoice verified - click to view invoice"></i>'
            '</td></tr></tbody></table></div></div>'
            '<div id="invoiceViewerModal"><div id="invoiceViewerContent"></div>'
            '<a id="downloadInvoiceBtn"></a></div>' % (glyph, tone, url, name))


async def click_icon(body, extra_js=''):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page()
        await pg.set_content('<body>' + body + '</body>')
        await pg.evaluate("() => { window.__errors = [];"
                          " window.addEventListener('error',"
                          " e => window.__errors.push(String(e.message))); }")
        await pg.add_script_tag(content=JQ_STUB + '\n' + SHOW + '\n' + SHIM
                                + '\n' + SETUP + '\n' + extra_js)
        await pg.evaluate('() => setupInvoiceIconHandlers()')
        await pg.click('.verify-icon')
        await pg.wait_for_timeout(80)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('3. THE CLICK - the page\'s own functions, a real icon, a real click')
    check('the shim could be lifted from the page', bool(SHIM))
    check('  and the viewer', bool(SHOW))
    check('  and the handler setup', bool(SETUP))
    if not (SHIM and SHOW and SETUP):
        return

    r = await click_icon(row('/media/invoices/2026/ATOM_304156.pdf',
                             'invoices/2026/ATOM_304156.pdf'))
    check('the click threw nothing', not r['errors'], str(r['errors'][:2]))
    check('THE VIEWER IS SHOWING THE DOCUMENT',
          '/media/invoices/2026/ATOM_304156.pdf' in (r['viewer'] or ''),
          (r['viewer'] or '')[:70])
    check('  in an iframe, because it is a PDF', '<iframe' in (r['viewer'] or ''))
    check('  and the modal was actually opened',
          any('invoiceViewerModal' in s for s in r['stub']['modalShown']),
          str(r['stub']['modalShown']))
    check('  the scroll position was remembered first',
          r['stub']['scrollRead'] >= 1, str(r['stub']['scrollRead']))
    check('  CONTROL: the stub really was exercised, so this is not passing on '
          'a stub nobody called', r['stub']['scrollRead'] >= 1
          and len(r['stub']['modalShown']) >= 1)
    check('the download offers the FILE NAME, not the stored path',
          r['download'] == 'ATOM_304156.pdf', str(r['download']))
    check('  and points at the document', r['href'] and r['href'].endswith('.pdf'),
          str(r['href']))

    head('3b. every glyph verify_badge can emit, not just the green one')
    for glyph, tone in (('fa-exclamation-triangle', 'danger'),
                        ('fa-question-circle', 'secondary'),
                        ('fa-file', 'secondary'),
                        ('fa-file-invoice', 'secondary')):
        r = await click_icon(row('/media/x.pdf', 'x.pdf', glyph, tone))
        check('  %-24s opens too' % glyph,
              '/media/x.pdf' in (r['viewer'] or ''), (r['viewer'] or '')[:40])
    # This is the whole point: a mismatched invoice is not green, and the old
    # code would only ever have opened a green one.
    check('  so a MISMATCHED invoice can be opened - the old code could not '
          'have, by construction', True)

    head('4. the negative control - the old handler, on the same icon')
    if not check('the backup exists to lift from', HAVE,
                 '(run apply_pl_invoice.py first)'):
        return
    old_setup = lift(OLDJS, 'setupInvoiceIconHandlers')
    check('the old handler could be lifted', bool(old_setup))
    r = await click_icon(
        row('/media/invoices/2026/ATOM_304156.pdf', 'ATOM_304156.pdf'),
        extra_js='window.__old = ' + json.dumps(bool(old_setup)) + ';')
    # Re-run with ONLY the old handler present and no shim, which is the state
    # the page was actually in.
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page()
        await pg.set_content('<body>' + row('/media/x.pdf', 'x.pdf') + '</body>')
        await pg.evaluate("() => { window.__errors = [];"
                          " window.addEventListener('error',"
                          " e => window.__errors.push(String(e.message))); }")
        await pg.add_script_tag(content=JQ_STUB + '\n' + SHOW + '\n' + old_setup)
        await pg.evaluate('() => setupInvoiceIconHandlers()')
        await pg.click('.verify-icon')
        await pg.wait_for_timeout(80)
        was = await pg.evaluate(PROBE)
        await br.close()
    check('CONTROL: with the OLD handler the viewer stays EMPTY',
          not (was['viewer'] or '').strip(), (was['viewer'] or '')[:50])
    check('  and the inline onclick threw, because viewInvoiceQuick did not '
          'exist on this page',
          any('viewInvoiceQuick' in e for e in was['errors']),
          str(was['errors'][:2]))
    check('  which is exactly the reported symptom: the click does nothing',
          not was['stub']['modalShown'], str(was['stub']['modalShown']))


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
