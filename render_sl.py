# -*- coding: utf-8 -*-
"""SL-1/2/3 BEFORE / AFTER - the Shopping List.

Not a test. A LOOK. The suite is test_shopping_list.py.

FOUR STATES, because the round changed which controls EXIST at each one:

    step 1   before / after   - Generate and Back move to the bar, and
                                Print is not there at all yet
    step 2   before / after   - Done, Print and Back in the bar, the share
                                box above the list, the badges on the
                                accent

THE MARKUP IS READ OUT OF THE TEMPLATE BEING SHOT, with the `hidden`
attributes resolved the way the page's own setBar() would resolve them -
so if the round's bar changes, these pictures change with it.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
PAGE = os.path.join(T, 'meal_plan_shopping_list.html')
SUF = '.bak_printguard'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'sl_before_after.html')
SHOTS = '/tmp/slshots'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)

ITEMS = [('Dairy', [('500 g', 'Butter, unsalted'), ('1 L', 'Milk, full fat')]),
         ('Produce', [('1 kg', 'Onions, brown'), ('300 g', 'Spinach')]),
         ('Store Cupboard', [('500 g', 'Plain Flour'), ('6', 'Eggs, large')])]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n')


def styles_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in STYLE.finditer(t))


def block(src, start, end):
    i = src.find(start)
    if i < 0:
        return ''
    j = src.find(end, i)
    return src[i:j + len(end)] if j > 0 else ''


def resolve(frag, step):
    frag = re.sub(r'\{#.*?#\}', '', frag, flags=re.S)
    for _ in range(6):
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}',
                   lambda m: m.group(1), frag, flags=re.S)
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*endif\s*%\}',
                   lambda m: m.group(1), n, flags=re.S)
        if n == frag:
            break
        frag = n
    frag = re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', frag, flags=re.S)
    # resolve the bar's hidden attributes the way setBar() would
    if step == 2:
        for bid in ('doneBtn', 'printBtn', 'backStep'):
            frag = re.sub(r'(id="%s"[^>]*?) hidden' % bid, r'\1', frag)
        for bid in ('genBtn', 'backLink'):
            frag = re.sub(r'(<(?:button|a)[^>]*id="%s")' % bid,
                          r'\1 hidden', frag)
    return frag


def badges(step):
    a = 'active' if step == 1 else 'completed'
    b = '' if step == 1 else ' active'
    return ('<div class="step-indicator">'
            '<div class="step-badge %s"><span class="step-number">1</span>'
            ' Review Ingredients</div>'
            '<div class="step-badge%s"><span class="step-number">2</span>'
            ' Your List</div></div>' % (a, b))


def list_html():
    out = ''
    for cat, rows in ITEMS:
        out += '<h3>%s</h3><ul style="list-style:none;padding:0">' % cat
        for qty, name in rows:
            out += ('<li style="padding:6px 0;border-bottom:1px solid '
                    'var(--alv-line,#e3e8ea)">'
                    '<span class="alv-pill alv-pill-info">%s</span> %s</li>'
                    % (qty, name))
        out += '</ul>'
    return out


def page(src, step):
    bar = resolve(block(src, '<div class="page-action-buttons">',
                        '\n    </div>'), step)
    if step == 1:
        inner = ('<div class="ingredients-card"><h2>Review Ingredients</h2>'
                 '<div class="review-list">%s</div>'
                 '<div class="tip-box"><i class="fas fa-lightbulb"></i> '
                 'Untick anything you already have at home.</div>'
                 '%s</div>' % (list_html(), nav_of(src, 1)))
    else:
        share = resolve(block(src, 'class="email-section"',
                              '<div id="emailStatus"'), 2)
        share = share.replace('<div id="emailStatus"', '')
        if not share.startswith('<div'):
            share = '<div ' + share
        share += '</div></div>'
        inner = ('<div class="ingredients-card">%s<h2>Items to Buy</h2>'
                 '<div id="finalShoppingList">%s</div>%s</div>'
                 % (share, list_html(), nav_of(src, 2)))
    return ('<h2 class="page-title-h2">SHOPPING LIST</h2>'
            '<h4 class="page-subtitle-h4">Week of 5 October &mdash; 7 days'
            '</h4>' + bar + badges(step) + inner)


def nav_of(src, step):
    """The bottom bar, if this version still has one."""
    if 'step-navigation' not in src:
        return ''
    blocks = re.findall(r'<div class="step-navigation">.*?</div>', src, re.S)
    if len(blocks) < step:
        return ''
    return resolve(blocks[step - 1] + '</div>', step)


boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = styles_of(read(BASE))


def fixture(src, step):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style>'
            '<style>.fas,.far,.fab{display:inline-block;width:14px;'
            'height:14px}*{animation:none!important;transition:none'
            '!important}</style></head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<div class="shopping-list-container">%s</div></div>'
            '</body></html>'
            % (boot, bcss, styles_of(src), page(src, step)))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    before, after = read(PAGE + SUF), read(PAGE)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, step, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, step))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            try:
                m['Print in the bar'] = (
                    'yes' if pg.query_selector(
                        '.page-action-buttons [aria-label*="Print"]:not([hidden])')
                    else 'no')
                m['buttons at the bottom'] = str(len(
                    pg.query_selector_all('.step-navigation')))
                b = pg.query_selector('.step-badge.active')
                m['active badge'] = (pg.evaluate(
                    '(e)=>getComputedStyle(e).backgroundColor', b)
                    if b else '-')
                c = pg.query_selector('.ingredients-card')
                m['card starts'] = ('%dpx down' % round(c.bounding_box()['y'])
                                    if c else '-')
            except Exception as e:
                m['error'] = str(e)[:50]
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for step in (1, 2):
            for w, h, lab in ((1180, 860, 'desktop 1180'),
                              (386, 900, 'phone 386')):
                b, bm = shoot(before, step, w, h, 'b%d_%d' % (step, w))
                a, am = shoot(after, step, w, h, 'a%d_%d' % (step, w))
                cells.append({'label': 'step %d - %s' % (step, lab),
                              'before': b, 'after': a, 'bm': bm, 'am': am})
                print('step %d %-14s before %s' % (step, lab, bm))
                print('step %d %-14s after  %s' % (step, lab, am))
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Shopping List Finds Its Bar</title>
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
</style></head><body><div class="wrap">
<h1>The shopping list finds its bar</h1>
<p class="sub"><strong>SL-1</strong> &mdash; Print is not in the bar at all
on step 1, because there is nothing to print. <strong>SL-2</strong> &mdash;
Generate, Done and Back move to the top; both bottom bars go; the share box
moves above the list. <strong>SL-3</strong> &mdash; the step badges stop
being green, and 20 distinct colours become one.</p>
<p class="sub"><strong>Font Awesome is not loaded in a <code>file://</code>
fixture</strong>, so every icon is an empty 14px box on both sides.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div><table class="m"><tr><th>measured</th>'
                    '<th>before</th><th>after</th></tr>'
                    % (c['label'], c['before'], c['after']))
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
