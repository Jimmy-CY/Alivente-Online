# -*- coding: utf-8 -*-
"""PU-1 BEFORE / AFTER - the popup that got cut off.

Not a test. A LOOK. The suite is test_fixed_popup.py.

Demetri: "the list of ingredients cuts off. Please investigate."

THE POPUP IS OPENED BY CLICKING IT, both sides, so each page's own code
decides where it lands - the old inline handler on the left, base's
alv-pop script on the right. Nothing here positions anything.

THE TOP ROW IS THE ONE THAT MATTERS. The popup grows upward and is clipped
by .table-container, so the nearer the top of the table, the more of the
list disappears. The first row is the worst case and is what the
screenshots showed.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_fixedpop'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'pu1_before_after.html')
SHOTS = '/tmp/pu1shots'

PAGE = os.path.join(T, 'categories_management.html')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

ITEMS = ['Butter, unsalted', 'Cream, double', 'Feta', 'Halloumi',
         'Milk, full fat', 'Yoghurt, Greek']
ROWS = ['Dairy', 'Meat', 'Produce', 'Store Cupboard']


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n')


def styles_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in STYLE.finditer(t))


def popup_scripts(t):
    """Only the page's own popup code, if it still has any."""
    out = []
    for m in SCRIPT.finditer(t):
        s = m.group(1)
        if 'Popup' in s or 'alv-pop' in s:
            out.append(re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', s, flags=re.S))
    return '\n'.join(out)


def base_popup_script():
    """base's alv-pop block, taken whole."""
    t = read(BASE)
    for m in SCRIPT.finditer(t):
        if 'alv-pop ---' in m.group(1) or 'alv-pop-trigger' in m.group(1):
            return m.group(1)
    return ''


def trigger_markup(src, label, count):
    """The cell the template writes, with its loop expanded."""
    # THE FIRST MATCH IS IN THE STYLESHEET, not the markup. Searching for
    # the bare class name found `.ingredient-popup-trigger {` at line 110
    # and then looked backwards for a <span that is not there. Match the
    # opening tag itself.
    m0 = re.search(r'<span[^>]*class="[^"]*(?:popup-trigger|alv-pop-trigger)',
                   src)
    if not m0:
        return ''
    i = m0.start()
    j = src.find('</td>', i)
    seg = src[i:j]
    seg = re.sub(r'\{#.*?#\}', '', seg, flags=re.S)
    m = re.search(r'\{%\s*if ([\w.]+)\s*%\}(.*?)\{%\s*else\s*%\}(.*?)'
                  r'\{%\s*endif\s*%\}', seg, re.S)
    if m:
        seg = seg[:m.start()] + m.group(2) + seg[m.end():]
    m = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}(.*?)'
                  r'\{%\s*endfor\s*%\}', seg, re.S)
    if m:
        var, body = m.group(1), m.group(3)
        rows = ''.join(re.sub(r'\{\{\s*%s[\w.]*\s*\}\}' % re.escape(var),
                              it, body) for it in ITEMS)
        seg = seg[:m.start()] + rows + seg[m.end():]
    seg = re.sub(r'\{\{\s*item\.ingredient_count\s*\}\}', str(count), seg)
    seg = re.sub(r'\{\{.*?\}\}', '', seg, flags=re.S)
    seg = re.sub(r'\{%.*?%\}', '', seg, flags=re.S)
    return seg


def fixture(src, tag):
    cell = trigger_markup(src, 'Dairy', len(ITEMS))
    body = ''.join(
        '<tr><td data-label="Category Name">%s</td>'
        '<td data-label="Ingredients">%s</td></tr>' % (c, cell)
        for c in ROWS)
    js = popup_scripts(src)
    if 'alv-pop-trigger' in src and 'toggle' not in js:
        js = base_popup_script()
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style>'
            '<style>.fas,.far{display:inline-block;width:14px;height:14px}'
            '*{animation:none!important;transition:none!important}</style>'
            '</head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<h2 class="page-title-h2">CATEGORIES MANAGEMENT</h2>'
            '<div class="categories-card"><div class="table-container">'
            '<table class="table alv-table"><thead><tr>'
            '<th>Category Name</th><th>Ingredients</th></tr></thead>'
            '<tbody>%s</tbody></table></div></div></div>'
            '<script>%s</script></body></html>'
            % (read(BOOT), styles_of(read(BASE)), styles_of(src), body, js))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    before, after = read(PAGE + SUFFIX), read(PAGE)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, tag))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            try:
                trig = pg.query_selector_all(
                    '.alv-pop-trigger, .ingredient-popup-trigger')[0]
                trig.click()
                pg.wait_for_timeout(120)
                pop = pg.query_selector('.alv-pop.show, '
                                        '.ingredient-popup.show')
                if pop:
                    m['position'] = pg.evaluate(
                        '(e)=>getComputedStyle(e).position', pop)
                    box = pop.bounding_box()
                    cont = pg.query_selector('.table-container')
                    cb = cont.bounding_box() if cont else None
                    m['popup top'] = '%dpx' % round(box['y'])
                    m['container top'] = ('%dpx' % round(cb['y'])
                                          if cb else '-')
                    above = (round(cb['y']) - round(box['y'])) if cb else 0
                    m['cut off above the container'] = (
                        '%dpx of it' % above if above > 0 else 'none')
                    m['list items visible'] = str(len(
                        pg.query_selector_all(
                            '.alv-pop.show li, .ingredient-popup.show li')))
                else:
                    m['position'] = 'popup did not open'
            except Exception as e:
                m['position'] = 'error: %s' % str(e)[:60]
            png = pg.screenshot(full_page=False)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for w, h, lab in ((1180, 620, 'desktop 1180'),
                          (386, 700, 'phone 386')):
            b, bm = shoot(before, w, h, 'b%d' % w)
            a, am = shoot(after, w, h, 'a%d' % w)
            cells.append({'label': lab, 'before': b, 'after': a,
                          'bm': bm, 'am': am})
            print('%-14s before %s' % (lab, bm))
            print('%-14s after  %s' % (lab, am))
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Popup Leaves The Container</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:25px;margin:0 0 6px}
.sub{color:var(--soft);margin:0 0 16px;max-width:66ch}
section{background:var(--card);border:1px solid var(--rule);
border-radius:10px;padding:18px;margin-bottom:20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
color:var(--teal);margin:0 0 14px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
figure{margin:0}
figcaption{font-size:12px;text-transform:uppercase;letter-spacing:.06em;
color:var(--soft);margin-bottom:6px}
img{width:100%;border:1px solid var(--rule);border-radius:6px;display:block}
table.m{border-collapse:collapse;font-size:13px;margin-top:12px;width:100%}
table.m th,table.m td{border:1px solid var(--rule);padding:5px 9px;
text-align:left}
table.m th{background:var(--ground);font-weight:600}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace}
</style></head><body><div class="wrap">
<h1>The popup leaves the container</h1>
<p class="sub">The list is opened by <em>clicking it</em> on both sides, so
each version's own code decides where it lands &mdash; the old inline
handler on the left, base's <code>alv-pop</code> script on the right.
Nothing in this harness positions anything.</p>
<p class="sub"><strong>The top row is the worst case.</strong> The popup grew
upward and <code>.table-container</code> is <code>overflow: clip</code> on
purpose &mdash; it is what lets a table heading stick. An absolutely
positioned child is <em>positioned</em> by its nearest positioned ancestor
but <em>clipped</em> by any ancestor that clips. Two correct decisions
colliding. On the right the popup is <code>position: fixed</code>, measured
from the trigger when it opens, and it flips below when there is no room
above.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div><table class="m"><tr><th>measured</th>'
                    '<th>before</th><th>after</th></tr>' % (
                        c['label'], c['before'], c['after']))
        for k in c['bm']:
            html.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                        % (k, c['bm'].get(k, '-'), c['am'].get(k, '-')))
        html.append('</table></section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
