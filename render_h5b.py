# -*- coding: utf-8 -*-
"""H5b BEFORE / AFTER - the nutrition breakdown, desktop and phone.

NOT LIKE THE OTHER SHEETS, because this table has nothing in it. Every row
is built by JavaScript from data the server sends to a modal, so the plain
fixture renders an empty <tbody> inside a closed dialog and both halves of
the pair come out blank.

So this sheet does three things the others do not:

  1. It FILLS the table, from a small sample written below, using the same
     five columns the page's own row template builds - once without the
     labels (the before) and once with them (the after).
  2. It OPENS the dialog. #nutritionModal is a Bootstrap modal: display
     none, and .modal.fade is opacity 0 as well, which is why forcing only
     the display gave four white pictures.
  3. It clips to the TABLE'S OWN BOX rather than to the top of the page.

Not a test. A LOOK. The suite is test_table_breakdown.py.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_tablebreakdown'
EXE = '/opt/pw-browsers/chromium'
REL = 'view_recipe.html'
OUT = os.path.join(ROOT, 'h5b_before_after.html')

# Three ingredients and a total: one ordinary, one with a big number, and
# one the page could not map - which is the state with its own styling and
# the one most likely to be lost when a renderer is deleted.
SAMPLE = [
    ('Chicken breast', 165, 0.0, 3.6, 31.0, '200 g', ''),
    ('Olive oil', 884, 0.0, 100.0, 0.0, '15 g', ''),
    ('Sea salt', None, None, None, None, '', 'Not mapped'),
]
COLS = [('Calories', 0), ('Carbs (g)', 1), ('Fat (g)', 1), ('Protein (g)', 1)]
TOTALS = ('524', '0.0', '51.8', '15.5')

# Everything this page needs forced open. .modal.fade is opacity 0, which
# display:block does not undo.
OPEN = ("<style>#nutritionModal{display:block !important;"
        "position:static !important}"
        "#nutritionResults{display:block !important}"
        "#nutritionBreakdownContent{display:block !important}"
        ".modal.fade{opacity:1 !important}"
        ".modal-dialog{margin:0 !important;max-width:none !important}"
        ".modal{background:transparent !important}"
        ".modal-content{background:#fff !important}</style>")

FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def one_branch(t):
    """Keep the FIRST branch of every {% if %}; a stack, so a pair nested
    inside an else-less if collapses too."""
    while True:
        stack, cut = [], None
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                start, first_end, cut = stack.pop()
                if cut is not None:
                    t = t[:start] + t[first_end:cut] + t[m.end():]
                    break
        else:
            return t


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def rows(labelled):
    out = []
    for name, cal, carb, fat, prot, amount, status in SAMPLE:
        def dl(k):
            return ' data-label="%s"' % k if labelled else ''
        cls = 'bt-num num' if labelled else 'bt-num'

        def cell(v, d):
            return ('<span class="bt-na">N/A</span>' if v is None
                    else '%.*f' % (d, v))
        head = (name
                + ('<span class="bt-status">%s</span>' % status
                   if status else '')
                + ('<span class="bt-amount">%s</span>' % amount
                   if amount else ''))
        body = ''.join('<td%s class="%s">%s</td>'
                       % (dl(k), cls, cell(v, d))
                       for (k, d), v in zip(COLS, (cal, carb, fat, prot)))
        out.append('<tr class="%s"><td%s class="bt-name">%s</td>%s</tr>'
                   % ('unmapped' if status else '', dl('Ingredient'),
                      head, body))
    return ''.join(out)


def foot(labelled):
    cls = 'bt-num num' if labelled else 'bt-num'
    cells = ''.join('<td%s class="%s">%s</td>'
                    % ((' data-label="%s"' % k) if labelled else '', cls, v)
                    for (k, _d), v in zip(COLS, TOTALS))
    return '<tr><td>Per 100g total</td>%s</tr>' % cells


def fixture(t, labelled):
    boot = read(BOOT)
    bcss = '\n'.join(styles_of(read(BASE)))
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1">'
            '<style>%s</style><style>%s</style>%s<style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(t)),
               FREEZE, OPEN, body_of(t)))
    html = html.replace('<tbody id="breakdownTableBody"></tbody>',
                        '<tbody id="breakdownTableBody">%s</tbody>'
                        % rows(labelled))
    html = html.replace('<tfoot id="breakdownTableFoot"></tfoot>',
                        '<tfoot id="breakdownTableFoot">%s</tfoot>'
                        % foot(labelled))
    return html


def main():
    from playwright.sync_api import sync_playwright
    scratch = '/tmp/h5bshots'
    if not os.path.isdir(scratch):
        os.makedirs(scratch)
    page = os.path.join(T, REL)
    bak = page + SUFFIX
    if not os.path.isfile(bak):
        raise SystemExit('H5b: no %s - nothing to compare against' % bak)

    shots = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for key, src, labelled in (('before', read(bak), False),
                                   ('after', read(page), True)):
            fx = os.path.join(scratch, 'fx_%s.html' % key)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, labelled))
            for w in (1280, 390):
                ctx = br.new_context(viewport={'width': w, 'height': 2200},
                                     device_scale_factor=1)
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                pg.goto('file://' + fx)
                # THE TABLE'S OWN BOX. Below 768px the BEFORE hides the
                # table and shows a card list built by a script this
                # fixture does not run - so there is nothing to shoot, and
                # saying so is the honest picture.
                box = pg.evaluate(
                    "() => {const e = document.querySelector("
                    "'.breakdown-table'); const b = e.getBoundingClientRect();"
                    " return {x: Math.round(b.left), y: Math.round(b.top),"
                    " w: Math.round(b.width), h: Math.round(b.height)};}")
                if box['w'] > 0:
                    shots[(key, w)] = base64.b64encode(pg.screenshot(
                        clip={'x': max(0, box['x'] - 10),
                              'y': max(0, box['y'] - 10),
                              'width': min(w, box['w'] + 20),
                              'height': min(1400, box['h'] + 20)})
                    ).decode('ascii')
                else:
                    shots[(key, w)] = None
                print('%-7s %5dpx  %s' % (key, w, box))
                ctx.close()
        br.close()
    write_sheet(shots)


SHEET = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>One Table, Not Two</title>
<style>
:root{--ink:#1d2327;--ink-soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
  --card:#fff;--teal:#0e7c8b;--teal-ink:#0a5e6a;--warn:#b3261e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --ink:#e8ecef;--ink-soft:#9aa6b0;--rule:#2d363d;--ground:#14181b;
  --card:#1b2024;--teal:#2fa7b8;--teal-ink:#7fd3de;--warn:#ff8a80}}
:root[data-theme="dark"]{--ink:#e8ecef;--ink-soft:#9aa6b0;--rule:#2d363d;
  --ground:#14181b;--card:#1b2024;--teal:#2fa7b8;--teal-ink:#7fd3de;
  --warn:#ff8a80}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,
  sans-serif;padding:24px 16px 64px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:1.5rem;margin:0 0 4px}
.sub{color:var(--ink-soft);margin:0 0 6px}
.note{color:var(--ink-soft);font-size:.86rem;margin:0 0 14px;
  border-left:3px solid var(--teal);padding-left:10px}
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:22px 0 0}
.page>h2{font-size:1.02rem;margin:0 0 12px}
.pair{display:grid;gap:12px;grid-template-columns:1fr 1fr;margin-bottom:14px}
.pair.phone{grid-template-columns:repeat(2,minmax(0,300px));
  justify-content:start}
figure{margin:0;min-width:0}
figcaption{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--ink-soft);margin:0 0 5px}
figcaption b{color:var(--teal-ink);font-weight:700}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
.none{border:1px dashed var(--rule);border-radius:6px;padding:26px 14px;
  color:var(--ink-soft);font-size:.86rem;text-align:center;background:none}
@media (max-width:760px){.pair,.pair.phone{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>One Table, Not Two</h1>
<p class="sub">H5b &mdash; the nutrition breakdown was drawing the same
numbers twice: a table above 768&thinsp;px, and a separate list of cards
built by 3.6&thinsp;KB of JavaScript below it. <code>.alv-table</code> is
that second renderer, in base, for every table in the application.</p>
<p class="note"><b>These rows are a sample, not the page's data.</b> Every
row here is built by a script from data the server sends to a dialog, so an
ordinary fixture renders an empty table inside a closed modal. This sheet
fills it with three ingredients &mdash; including one the page could not map,
which is the state with its own styling &mdash; and opens the dialog.</p>
<p class="note"><b>The phone &ldquo;before&rdquo; is empty on purpose.</b>
Below 768&thinsp;px the old page hid the table outright and showed the card
list instead, and that list is built by the script this fixture does not run.
An empty frame is the honest picture of what the table did at that width:
nothing.</p>
<p class="note"><b>Look at the totals bar.</b> It was Bootstrap green
(<code>#28a745</code>) with white text. base&rsquo;s <code>tfoot</code> is the
house surface with strong ink and a 2&thinsp;px rule above it.</p>
"""


def write_sheet(shots):
    out = [SHEET]
    for w, title, cls in ((1280, 'Desktop &mdash; 1280&thinsp;px', 'pair'),
                          (390, 'Phone &mdash; 390&thinsp;px',
                           'pair phone')):
        out.append('<section class="page"><h2>%s</h2><div class="%s">'
                   % (title, cls))
        for key in ('before', 'after'):
            b64 = shots.get((key, w))
            out.append('<figure><figcaption>Nutrition breakdown &mdash; '
                       '<b>%s</b></figcaption>%s</figure>'
                       % (key,
                          ('<img alt="breakdown %s %d" '
                           'src="data:image/png;base64,%s">'
                           % (key, w, b64)) if b64 else
                          '<div class="none">The table was '
                          '<code>display:&nbsp;none</code> at this width. '
                          'A separate list of cards stood here, built by '
                          'the script.</div>'))
        out.append('</div></section>')
    out.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    print('wrote %s  (%.1f MB)' % (OUT, os.path.getsize(OUT) / 1048576.0))


if __name__ == '__main__':
    main()
