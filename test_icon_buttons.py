#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Icon buttons: one definition, in base, and a disabled one that looks it.

Run from the repo root. Needs Playwright's chromium.

TWO FAULTS, and the second is the one to read carefully.

Invoice Customers redefined base's icon buttons in its own <style> - same
specificity, later in the document, so the page won. That is visible: bold
2px Bootstrap blue and red instead of base's quiet tinted borders.

Open Invoices marked its no-permission Paid tick `is-disabled`, which base
does not define for icons - the only `.is-disabled` in base belongs to
`.status-btn`. A class that matches nothing has NO appearance of its own, so
the disabled tick rendered exactly like the live one. There is no way to grep
for that: the class is spelled correctly, it is simply not the one that
exists. The only check that finds it renders both and compares them.
"""
import os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
CUST = os.path.join(TPL, 'customer_list.html')
INV  = os.path.join(TPL, 'invoices.html')
BASEF = os.path.join(TPL, 'base.html')

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


def sels_of(t):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(t)):
        s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        if s and not s.startswith('@'):
            out.append(s)
    return out


BASE, CT, IT = read(BASEF), read(CUST), read(INV)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

head('1. Invoice Customers stopped redefining what base owns')
_left = sels_of(CT)
for gone in ('.icon-action-btn', '.icon-action-btn i', '.icon-action-btn:hover',
             '.icon-edit', '.icon-edit:hover', '.icon-delete',
             '.icon-delete:hover', '.icon-disabled', '.table-container',
             '.mobile-action-btn', '.mobile-action-icon', '.icon-color-edit',
             '.icon-color-delete', '.desktop-action-cell', '.btn-info'):
    check('  %-32s is base\'s alone now' % gone, gone not in _left)
check('no raw Bootstrap blue survives', '#007bff' not in CT)
check('  nor red', '#dc3545' not in CT)
check('  and base really does define the icons',
      '.icon-edit' in sels_of(BASE) and '.icon-action-btn' in sels_of(BASE))
check('the page kept its own inline-form wrappers, which base has no name for',
      '.cust-inline-form' in _left and '.cust-inline-form-mobile' in _left)
check('  it is down to %d rules from 41' % len(_left), len(_left) <= 6,
      ', '.join(_left))
check('the mobile bar declares its two columns', 'mobile-action-bar cols-2' in CT)
check('  and base defines cols-2', '.mobile-action-bar.cols-2' in css_of(BASE))
check('the empty state is base\'s', 'alv-empty-title' in CT and 'cust-empty' not in CT)
check('  and it sits outside the tbody, so it needs no colspan',
      'colspan="6"' not in CT and '{% if not rows %}' in CT)
check('the second <body> is gone', '<body>' not in CT)
check('CSS braces balance', css_of(CT).count('{') == css_of(CT).count('}'))
check('div tags balance',
      len(re.findall(r'<div\b', CT)) == len(re.findall(r'</div\s*>', CT)))
check('if/endif balance',
      len(re.findall(r'\{%\s*if\b', CT)) == len(re.findall(r'\{%\s*endif\s*%\}', CT)))

head('1b. one verb, one glyph - across EVERY template')
# base owns an icon button's COLOUR but not its picture: the glyph is an <i>
# in each page's markup, so it drifted unwatched. Four pages drew Edit as
# fa-pencil-alt and two as fa-edit - two different pictures for the same verb
# on screens a user moves between, which is how it was spotted.
#
# This scans every template, not the two that were fixed, because the point is
# that those were the LAST two rather than merely two fewer.
import glob as _glob
# NOT `_f` as the loop variable: that is this file's FAILURE COUNTER, and
# shadowing it made check() raise instead of reporting. A crash is the least
# useful thing a check can do.
_gl = {}
for _path in sorted(_glob.glob(os.path.join(TPL, '*.html'))):
    _src = read(_path)
    for _mm in re.finditer(r'icon-edit[^>]*>\s*(?:\n\s*)?<i class="[^"]*?(fa-[a-z0-9-]+)', _src):
        _gl.setdefault(os.path.basename(_path), set()).add(_mm.group(1))
_all = set()
for _glyphs in _gl.values():
    _all |= _glyphs
check('every icon-only Edit button on %d page(s) uses one glyph' % len(_gl),
      _all == {'fa-pencil-alt'},
      '; '.join('%s: %s' % (k, ', '.join(sorted(v)))
                for k, v in sorted(_gl.items()) if v != {'fa-pencil-alt'})
      or ', '.join(sorted(_all)))
check('  and there are pages to check, so this is not passing on an empty set',
      len(_gl) >= 5, '%d page(s)' % len(_gl))
# CONTROL: the scan must be able to see a disagreement.
check('  CONTROL: a second glyph WOULD be caught',
      (_all | {'fa-edit'}) != {'fa-pencil-alt'})
# A LABELLED button is a different case and is deliberately not in scope: an
# icon alone is the only signal a reader gets, while an icon beside the word
# "Edit" is decoration.
check('a labelled Edit button keeps its own glyph, by design',
      'fa-edit"></i> Edit Asset' in read(os.path.join(TPL, 'asset_detail.html'))
      if os.path.exists(os.path.join(TPL, 'asset_detail.html')) else True)

head('2. Open Invoices: the disabled tick wears a class that exists')
check('it is icon-disabled', 'icon-action-btn icon-approve icon-disabled' in IT)
check('  not is-disabled, which base does not define for icons',
      'is-disabled' not in IT)
check('  base defines .icon-action-btn.icon-disabled',
      '.icon-action-btn.icon-disabled' in css_of(BASE))
check('  and base\'s only .is-disabled belongs to .status-btn',
      re.search(r'\.status-btn\.is-disabled', css_of(BASE)) is not None
      and not re.search(r'\.icon-action-btn\.is-disabled', css_of(BASE)))


FRAG = ("<div class='table-container'><table class='table alv-table'>"
        "<tbody><tr><td class='desktop-action-cell cell-actions'>"
        "<div class='row-actions'>"
        "<a href='#' class='icon-action-btn icon-edit'   id='edit'>x</a>"
        "<a href='#' class='icon-action-btn icon-delete' id='del'>x</a>"
        "<span class='icon-action-btn icon-disabled'     id='off'>x</span>"
        "<a href='#' class='icon-action-btn icon-approve' id='paid'>x</a>"
        "<span class='icon-action-btn icon-approve icon-disabled' id='paidoff'>x</span>"
        "<span class='icon-action-btn icon-approve is-disabled'   id='paidbad'>x</span>"
        "</div></td></tr></tbody></table></div>")

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const g = id => { const e = document.getElementById(id);
    const s = getComputedStyle(e);
    return {color: s.color, border: s.borderTopWidth,
            bc: s.borderTopColor, bg: s.backgroundColor}; };
  const o = {edit: g('edit'), del: g('del'), off: g('off'),
             paid: g('paid'), paidoff: g('paidoff'), paidbad: g('paidbad')};
  for (const v of ['--alv-edit', '--alv-danger', '--alv-good', '--alv-ink-faint'])
    o['T' + v] = tok(v);
  return o; }"""


async def render(page_css):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1200, 'height': 600})
        await pg.set_content("<style>%s</style><style>%s</style><style>%s</style>"
                             "<body style='padding:20px'>%s</body>"
                             % (BOOTSTRAP, css_of(BASE), page_css, FRAG))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('3. what the icons actually render as')
    now = await render(css_of(CT))
    check('Edit is the house blue, not Bootstrap\'s',
          now['edit']['color'] == now['T--alv-edit']
          and now['edit']['color'] != 'rgb(0, 123, 255)', now['edit']['color'])
    check('Delete is the house red',
          now['del']['color'] == now['T--alv-danger']
          and now['del']['color'] != 'rgb(220, 53, 69)', now['del']['color'])
    check('the border is base\'s 1px, not the page\'s 2px',
          now['edit']['border'] == '1px', now['edit']['border'])
    check('a disabled icon is visibly not a live one',
          now['off']['color'] == now['T--alv-ink-faint']
          and now['off']['color'] != now['edit']['color'], now['off']['color'])

    head('4. the disabled Paid tick, which is the one that was invisible')
    check('the live tick is the house green',
          now['paid']['color'] == now['T--alv-good'], now['paid']['color'])
    check('the disabled tick does NOT look like it',
          now['paidoff']['color'] != now['paid']['color'],
          '%s vs %s' % (now['paidoff']['color'], now['paid']['color']))
    check('  it is the faint ink base uses for a permission you lack',
          now['paidoff']['color'] == now['T--alv-ink-faint'],
          now['paidoff']['color'])
    # CONTROL, and the point of the whole round: the class I shipped.
    check('CONTROL: the class I shipped, is-disabled, matches NOTHING - it '
          'renders exactly like the live tick',
          now['paidbad']['color'] == now['paid']['color']
          and now['paidbad']['bc'] == now['paid']['bc'],
          '%s / %s' % (now['paidbad']['color'], now['paid']['color']))

    head('5. the negative controls')
    bak = CUST + '.bak_iconbtn'
    if not check('the backup exists to compare against', os.path.exists(bak),
                 '(run apply_icon_buttons.py first)'):
        return
    was = await render(css_of(read(bak)))
    check('CONTROL: Edit WAS Bootstrap blue',
          was['edit']['color'] == 'rgb(0, 123, 255)', was['edit']['color'])
    check('CONTROL: Delete WAS Bootstrap red',
          was['del']['color'] == 'rgb(220, 53, 69)', was['del']['color'])
    check('CONTROL: the border WAS 2px', was['edit']['border'] == '2px',
          was['edit']['border'])
    check('  so the page really did beat base on document order',
          was['edit']['color'] != now['edit']['color'])
    _old = read(bak)
    _probes = [('no local .icon-edit', lambda t: '.icon-edit' not in sels_of(t)),
               ('base empty state', lambda t: 'alv-empty-title' in t),
               ('cols-2', lambda t: 'mobile-action-bar cols-2' in t),
               ('no stray body', lambda t: '<body>' not in t)]
    _would = sum(1 for _, fn in _probes if not fn(_old))
    check('  and %d of the static checks above fail on the old page' % _would,
          _would >= 4)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
