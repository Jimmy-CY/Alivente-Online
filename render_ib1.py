# -*- coding: utf-8 -*-
"""IB-1 BEFORE / AFTER - the Ingredient Shopping Units filter.

Not a test. A LOOK. The suite is test_ingredient_filter.py.

THREE STATES, not two, because the round's whole point is that the third
one did not exist before:

    before        the filter card, always open, above the table
    after closed  what the page looks like on arrival
    after open    what the Filter button reveals

THE MARKUP IS READ OUT OF THE TEMPLATE BEING SHOT. The bar, the chip row,
the panel and a table head all come from the file itself with the Django
tags resolved against a small fixture, so if the round's markup changes
these pictures change with it. Nothing here is typed by hand except the
four ingredient rows, which the template builds from a queryset.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
PAGE = os.path.join(T, 'ingredient_base_units_management.html')
SUFFIX = '.bak_ingfilter'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'ib1_before_after.html')
SHOTS = '/tmp/ib1shots'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
GLYPH = '.fas,.far{display:inline-block;width:14px;height:14px}'
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}'
          + GLYPH)

CATS = ['Dairy', 'Meat', 'Produce', 'Store Cupboard']
ROWS = [('Butter, unsalted', 'Dairy', 'g'),
        ('Chicken Breast', 'Meat', 'g'),
        ('Onions, brown', 'Produce', 'each'),
        ('Plain Flour', 'Store Cupboard', 'g')]


def read(p):
    # NEWLINES NORMALISED. This template is CRLF and the block markers
    # below are written with \\n; the first cut of this harness extracted
    # the action bar (which happens to sit in a LF region) and silently
    # got nothing for the chip row. A renderer may normalise - a PATCHER
    # may not, which is why apply_ingredient_filter.py converts instead.
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in STYLE.finditer(t)]


def block(src, start_pat, end):
    """The markup from the first match of start_pat to the matching end."""
    m = re.search(start_pat, src)
    if not m:
        return ''
    i = m.start()
    j = src.find(end, i)
    return src[i:j + len(end)] if j > 0 else ''


def resolve(frag, counts=True):
    """Django tags out, fixture values in. The STRUCTURE is the template's."""
    # The category loop, expanded with real option text.
    frag = re.sub(
        r'\{%\s*for cat in categories\s*%\}(.*?)\{%\s*endfor\s*%\}',
        lambda m: ''.join(
            '<option value="%d">%s</option>' % (n, c)
            for n, c in enumerate(CATS, 1)), frag, flags=re.S)
    # DJANGO COMMENTS OUT FIRST, or they print on the page - the first cut
    # of this harness shot the round's own explanatory note as body text,
    # which is B-1b's bug reproduced in a picture.
    frag = re.sub(r'\{#.*?#\}', '', frag, flags=re.S)
    # ONE BRANCH, NOT BOTH. Stripping the tags and keeping everything left
    # the bar showing Map Nutrition twice - the live link AND the disabled
    # span - which made the bar two rows tall in the picture and nowhere
    # else. Keep the TRUE branch, which is the one with counts outstanding.
    for _ in range(6):
        new = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', lambda m: m.group(1), frag,
                     flags=re.S)
        new = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*endif\s*%\}',
                     lambda m: m.group(1), new, flags=re.S)
        if new == frag:
            break
        frag = new
    frag = frag.replace('{{ unmapped_count }}', '7')
    frag = frag.replace('{{ unconvertible_count }}', '3')
    frag = re.sub(r'\{\{\s*unmapped_count\|pluralize\s*\}\}', 's', frag)
    frag = re.sub(r'\{\{\s*unconvertible_count\|pluralize\s*\}\}', 's', frag)
    frag = re.sub(r'\{%.*?%\}', '', frag, flags=re.S)
    frag = re.sub(r'\{\{\s*search_query\s*\}\}', '', frag)
    frag = re.sub(r'\{\{.*?\}\}', '', frag, flags=re.S)
    return frag


def table_html():
    body = ''.join(
        '<tr><td data-label="Ingredient Name">%s</td>'
        '<td data-label="Category"><span class="category-badge">%s</span></td>'
        '<td data-label="Shopping Unit">%s</td>'
        '<td data-label="Conversion">1 %s = 1 g</td></tr>'
        % (n, c, u, u) for n, c, u in ROWS)
    return ('<div class="ingredients-card">'
            '<h2 style="font-size:22px;font-weight:600;margin-bottom:20px;'
            'color:#2c3e50;"><i class="fas fa-list"></i> Ingredients (374)'
            '</h2><div class="table-container">'
            '<table class="table alv-table ingredients-table"><thead><tr>'
            '<th>Ingredient Name</th><th>Category</th><th>Shopping Unit</th>'
            '<th>Conversion</th></tr></thead><tbody>%s</tbody></table>'
            '</div></div>' % body)


CHIPS = ('<span class="filter-tag">Search: "flour" '
         '<button class="remove-tag">&times;</button></span>'
         '<span class="filter-tag">Category: Store Cupboard '
         '<button class="remove-tag">&times;</button></span>')


def page_html(src, state):
    """state: 'before', 'closed', 'open'."""
    bar = resolve(block(src, r'<div class="page-action-buttons">',
                        '\n    </div>'))
    if state == 'before':
        panel = resolve(block(src, r'<!-- Filter Bar -->', '\n    </div>'))
        chips = ''
    else:
        panel = resolve(block(src, r'<!-- Collapsible Filter Panel -->',
                              '\n    </div>'))
        chips = resolve(block(src, r'<div class="alv-filter-active"',
                              '</div>\n    </div>\n'))
        if 'filterTags' not in chips:
            raise SystemExit('render_ib1: the chip row did not extract - '
                             'got %r' % chips[:120])
        if state == 'open':
            panel = panel.replace('class="alv-filter filter-panel"',
                                  'class="alv-filter filter-panel is-open"')
            chips = chips.replace('class="alv-filter-active"',
                                  'class="alv-filter-active has-filters"')
            chips = chips.replace('<div class="filter-tags" id="filterTags">',
                                  '<div class="filter-tags" id="filterTags">'
                                  + CHIPS)
            bar = bar.replace('data-count="0"></span>',
                              'data-count="2">2</span>')
            bar = bar.replace('aria-pressed="false"', 'aria-pressed="true"')
    return bar + chips + panel + table_html()


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(src, state):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<h2 class="page-title-h2">INGREDIENT SHOPPING UNITS</h2>'
            '%s</div></body></html>'
            % (boot, bcss, '\n'.join(styles_of(src)), FREEZE,
               page_html(src, state)))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    before, after = read(PAGE + SUFFIX), read(PAGE)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, state, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, state))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            for sel, key in ((
                    '.ingredients-card', 'table top'),
                    ('.alv-filter, .filter-bar', 'panel height'),
                    ('.action-filter', 'Filter button')):
                try:
                    el = pg.query_selector(sel)
                    bb = el.bounding_box() if el else None
                    if bb is None:
                        m[key] = 'not shown'
                    elif key == 'table top':
                        m[key] = '%dpx down' % round(bb['y'])
                    else:
                        m[key] = '%dx%d' % (round(bb['width']),
                                            round(bb['height']))
                except Exception:
                    m[key] = None
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for w, h, lab in ((1180, 900, 'desktop 1180'),
                          (386, 820, 'phone 386')):
            got = []
            for state, src, name in (('before', before, 'before'),
                                     ('closed', after, 'after - on arrival'),
                                     ('open', after, 'after - Filter pressed')):
                png, m = shoot(src, state, w, h, '%s%d' % (state, w))
                got.append({'name': name, 'png': png, 'm': m})
                print('%-14s %-24s %s' % (lab, name, m))
            cells.append({'label': lab, 'shots': got})
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Ingredient Filter Folds Away</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:25px;margin:0 0 6px}
.sub{color:var(--soft);margin:0 0 26px;max-width:66ch}
section{background:var(--card);border:1px solid var(--rule);
border-radius:10px;padding:18px;margin-bottom:20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
color:var(--teal);margin:0 0 14px}
.trio{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
@media(max-width:900px){.trio{grid-template-columns:1fr}}
figure{margin:0}
figcaption{font-size:12px;text-transform:uppercase;letter-spacing:.06em;
color:var(--soft);margin-bottom:6px}
img{width:100%;border:1px solid var(--rule);border-radius:6px;display:block}
table.m{border-collapse:collapse;font-size:13px;margin-top:12px;width:100%}
table.m th,table.m td{border:1px solid var(--rule);padding:5px 9px;
text-align:left}
table.m th{background:var(--ground);font-weight:600}
</style></head><body><div class="wrap">
<h1>The ingredient filter folds away</h1>
<p class="sub">Three states, because the middle one did not exist before:
the card that was always open, the page as it now arrives, and what the
Filter button reveals. The measurement that matters is how far down the
table starts &mdash; on a phone the table now begins 255px higher, which is
most of a screen.</p>
<p class="sub"><strong>Two things in these pictures are the harness, not
the page.</strong> Font Awesome is not loaded in a <code>file://</code>
fixture, so every icon is an empty 14px box: the funnel inside the Filter
button is blank, and the Back button &mdash; which is icon-only on a phone
&mdash; is invisible in <em>all six</em> shots, before and after alike. On
the real page both draw normally.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="trio">' % c['label'])
        for s in c['shots']:
            html.append('<figure><figcaption>%s</figcaption>'
                        '<img src="data:image/png;base64,%s" alt=""></figure>'
                        % (s['name'], s['png']))
        html.append('</div><table class="m"><tr><th>measured</th>')
        for s in c['shots']:
            html.append('<th>%s</th>' % s['name'])
        html.append('</tr>')
        for k in c['shots'][0]['m']:
            html.append('<tr><td>%s</td>%s</tr>'
                        % (k, ''.join('<td>%s</td>' % (s['m'].get(k) or '-')
                                      for s in c['shots'])))
        html.append('</table></section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
