# -*- coding: utf-8 -*-
"""UC-1 BEFORE / AFTER - the Unit Conversions pills.

Not a test. A LOOK. The suite is test_conversion_pills.py.

Demetri: "Can we mellow down the green colour for qty and the yellow colour
for Applies To. Do we have any standards??"

FOUR ROWS, PLANTED, because one row cannot show both scopes at once. The
CLASS STRINGS ARE NOT TYPED HERE: the row markup is read out of the
template being shot and its {% if %} branch evaluated, so if the round's
tones change these pictures change with them.

AND THE MODAL IS IN THE PICTURE TOO, because it asks the question the
Applies To column answers and used to answer it in the same two colours.
Its markup lives inside a JavaScript template string, so the ${...} holes
are filled here rather than resolved by Django.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
PAGE = os.path.join(T, 'unit_conversions_management.html')
SUFFIX = '.bak_convpills'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'uc1_before_after.html')
SHOTS = '/tmp/uc1shots'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
GLYPH = '.fas,.far{display:inline-block;width:14px;height:14px}'
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}'
          + GLYPH)

# from, mult, to, specific-ingredient-or-None
ROWS = [('cup', '240', 'grams', None),
        ('cup', '120', 'grams', 'Plain Flour'),
        ('tablespoon', '15', 'millilitres', None),
        ('each', '58', 'grams', 'Eggs, large')]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in STYLE.finditer(t)]


def between(src, start, end, after=0):
    i = src.find(start, after)
    if i < 0:
        return ''
    j = src.find(end, i)
    return src[i:j + len(end)] if j > 0 else ''


def display_markup(src, mult, frm, to):
    """The conversion-display block, as the template writes it."""
    seg = between(src, '<div class="conversion-display">', '</div>')
    seg = seg.replace('{{ conversion.from_unit.name }}', frm)
    seg = seg.replace('{{ conversion.to_unit.name }}', to)
    seg = seg.replace('{{ conversion.multiplier|normalize_decimal }}', mult)
    return seg


def applies_markup(src, ingredient):
    """The Applies To cell, with its {% if %} branch chosen."""
    seg = between(src, '<td data-label="Applies To">', '</td>')
    seg = re.sub(r'\{#.*?#\}', '', seg, flags=re.S)
    m = re.search(r'\{%\s*if conversion\.specific_ingredient\s*%\}(.*?)'
                  r'\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', seg, re.S)
    if not m:
        raise SystemExit('render_uc1: the Applies To branch did not extract')
    body = m.group(1) if ingredient else m.group(2)
    body = body.replace('{{ conversion.specific_ingredient.name }}',
                        ingredient or '')
    return '<td data-label="Applies To">%s</td>' % body


def scope_cards(src):
    """The two radio cards out of the JS template string."""
    seg = between(src, '<i class="fas fa-tag"></i> Apply this conversion to:',
                  '</div>\n                    </div>')
    seg = seg[seg.find('<div class="row g-2">'):]
    seg = seg.replace('${index}', '0').replace('${item.ingredient}',
                                               'Plain Flour')
    return seg


def table_html(src):
    body = ''
    for frm, mult, to, ing in ROWS:
        body += ('<tr><td data-label="Conversion">%s</td>%s'
                 '<td class="actions-cell" style="text-align:center">'
                 '<span class="icon-action-btn icon-edit">'
                 '<i class="fas fa-pencil-alt"></i></span></td></tr>'
                 % (display_markup(src, mult, frm, to),
                    applies_markup(src, ing)))
    return ('<div class="conversions-card"><h2 style="font-size:22px;'
            'font-weight:600;margin-bottom:20px;color:#2c3e50;">'
            '<i class="fas fa-list"></i> All Conversions (4)</h2>'
            '<div class="table-container">'
            '<table class="table alv-table"><thead><tr>'
            '<th>Conversion</th><th style="width:35%%">Applies To</th>'
            '<th style="text-align:center">Actions</th></tr></thead>'
            '<tbody>%s</tbody></table></div></div>' % body)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(src, what):
    inner = (table_html(src) if what == 'table' else
             '<div class="conversions-card" style="max-width:720px">'
             '<label style="font-size:13px;font-weight:600;margin-bottom:10px;'
             'display:block"><i class="fas fa-tag"></i> Apply this conversion '
             'to:</label>%s</div>' % scope_cards(src))
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div></body></html>'
            % (boot, bcss, '\n'.join(styles_of(src)), FREEZE, inner))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    before, after = read(PAGE + SUFFIX), read(PAGE)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, what, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, what))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            # THE CHIPS ARE PAINTED WITH A GRADIENT BEFORE THE ROUND, and
            # a gradient is a background-IMAGE: backgroundColor reads
            # transparent and says nothing. So both are reported, and the
            # pair is what proves the blue rule never fired - the first and
            # second chip measure IDENTICAL on the left.
            def _paint(e):
                return pg.evaluate(
                    '(x)=>{var s=getComputedStyle(x);'
                    'return s.backgroundImage!=="none"?s.backgroundImage'
                    ':s.backgroundColor}', e)
            try:
                els = pg.query_selector_all('.conversion-number')
                m['1st qty chip'] = _paint(els[0]) if els else None
                m['2nd qty chip'] = (_paint(els[1]) if len(els) > 1
                                     else None)
            except Exception:
                pass
            for sel, key in (('td[data-label="Applies To"] span',
                              'Applies To (generic)'),):
                try:
                    sp = pg.query_selector_all(sel)
                    m['Applies To, wider'] = pg.evaluate(
                        '(e)=>getComputedStyle(e).backgroundColor', sp[0])
                    m['Applies To, narrower'] = pg.evaluate(
                        '(e)=>getComputedStyle(e).backgroundColor', sp[1])
                except Exception:
                    pass
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for what, w, h, lab in (('table', 1180, 560, 'the table, desktop'),
                                ('table', 386, 760, 'the table, phone'),
                                ('modal', 1180, 360,
                                 'the scope chooser, desktop')):
            b, bm = shoot(before, what, w, h, 'b_%s_%d' % (what, w))
            a, am = shoot(after, what, w, h, 'a_%s_%d' % (what, w))
            cells.append({'label': lab, 'before': b, 'after': a,
                          'bm': bm, 'am': am})
            print('%-26s before %s' % (lab, bm))
            print('%-26s after  %s' % (lab, am))
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A Scope Is Not A Verdict</title>
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
<h1>A scope is not a verdict</h1>
<p class="sub">Green reads as <em>good</em> and amber reads as <em>needs
attention</em>. A conversion that applies to one ingredient is not in better
or worse health than one that applies to all of them &mdash; so the tones
that carry a judgement were the wrong ones. Specific takes the accent,
Generic takes neutral, and the star and the globe stay exactly where they
were.</p>
<p class="sub"><strong>The blue rule in the stylesheet never once fired.</strong>
<code>.conversion-number:last-of-type</code> was written to paint the second
number blue. <code>:last-of-type</code> matches the last element of its type
among its siblings, and the siblings are five <code>&lt;span&gt;</code>s
ending in a <code>.conversion-unit</code> &mdash; so it never selected a
number. That is why both numbers render the same green on the left.</p>
<p class="sub"><strong>Font Awesome is not loaded in a <code>file://</code>
fixture</strong>, so the star, globe and arrow glyphs are empty 14px boxes on
both sides.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div>' % (c['label'], c['before'], c['after']))
        keys = [k for k in c['bm'] if c['bm'].get(k) or c['am'].get(k)]
        if keys:
            html.append('<table class="m"><tr><th>measured</th>'
                        '<th>before</th><th>after</th></tr>')
            for k in keys:
                html.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                            % (k, c['bm'].get(k) or '-',
                               c['am'].get(k) or '-'))
            html.append('</table>')
        html.append('</section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
