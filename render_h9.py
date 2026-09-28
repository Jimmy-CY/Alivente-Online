# -*- coding: utf-8 -*-
"""H9 BEFORE / AFTER - one component, one box, one ink.

THE MENU HAS TO BE OPEN TO BE SEEN, so every shot is taken after one tap
of More. A closed menu shows nothing about the round.

Four pages, chosen because between them they carry every colour the icon
had: amber on view_recipe and unit_conversions, green on view_meal_plan,
red on finance_expense_types. None of those menus holds a destructive
action - they are Nutrition, Shopping List, Print Recipe, Edit,
Duplicate, Missing Conversions, Help.

The fifth strip is the one page this round does NOT touch, shown with its
rules stripped so the reason is visible rather than asserted.

Not a test. A LOOK. The suite is test_more_css.py.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_morecss'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h9_before_after.html')
SHOTS = os.path.join('/tmp', 'h9shots')

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
SEL = re.compile(r'\.action-more-(?:wrapper|btn|menu|item|divider)\b')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')

PAGES = [
    ('view_recipe.html', 'View Recipe',
     'Its menu icons were <code>#ffc107</code>. The box was 240&thinsp;px '
     'with its own border and shadow; base draws 200 on '
     '<code>--alv-line</code>.'),
    ('finance_expense_types.html', 'Expense Types',
     'Its menu icons were <code>#dc3545</code> &mdash; red, on a menu '
     'whose only item is Help.'),
    ('view_meal_plan.html', 'View Meal Plan',
     'Green, <code>#28a745</code>, on Edit and Duplicate.'),
]
STRIPPED = ('property_management_dashboard.html',
            'Property Dashboard &mdash; NOT touched',
            'Shown with its rules stripped, which is what this round would '
            'have done to it. Its More menu is an always-present side '
            'hamburger outside any <code>.page-action-buttons</code>, and '
            'every one of base&rsquo;s More rules is scoped either to that '
            'class or to the phone media query. So base reaches none of it.')


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def strip_more(css):
    out, last = [], 0
    for m in RULE.finditer(css):
        if SEL.search(bare(m.group(1))):
            out.append(css[last:m.start()])
            last = m.end()
    out.append(css[last:])
    return ''.join(out)


def one_branch(t):
    while True:
        stack = []
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
                s, fe, cut = stack.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))
binder = [s for s in SCRIPT.findall(read(BASE)) if 'data-menu-toggle' in s]


def fixture(page_text, strip=False):
    """ONE <script> PER SOURCE. Concatenating them means a page script
    that throws takes base's binder down with it, and the menu never
    opens - which looked like a broken round the first time."""
    cs = styles_of(page_text)
    if strip:
        cs = [strip_more(c) for c in cs]
    parts = ['<script>%s</script>' % s for s in SCRIPT.findall(page_text)]
    if binder:
        parts.append('<script>%s</script>' % binder[0])
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s'
            '<style>%s</style></head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div>%s</body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c for c in cs),
               FREEZE, body_of(page_text), ''.join(parts)))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(text, w, h, tag, strip=False):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, strip))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            note = ''
            try:
                pg.click('#actionMoreBtn', timeout=3500)
            except Exception:
                note = 'the More button could not be tapped'
            png = pg.screenshot(clip={'x': 0, 'y': 0, 'width': w,
                                      'height': h})
            ctx.close()
            return base64.b64encode(png).decode('ascii'), note

        for rel, label, look in PAGES:
            p = os.path.join(T, *rel.split('/'))
            if not (os.path.isfile(p) and os.path.isfile(p + SUFFIX)):
                print('SKIP %s' % rel)
                continue
            row = {'rel': rel, 'label': label, 'look': look, 'kind': 'pair'}
            row['before'], row['bn'] = shoot(read(p + SUFFIX), 390, 560,
                                             rel + '_b')
            row['after'], row['an'] = shoot(read(p), 390, 560, rel + '_a')
            cells.append(row)
            print('shot %s' % rel)

        rel, label, look = STRIPPED
        p = os.path.join(T, rel)
        row = {'rel': rel, 'label': label, 'look': look, 'kind': 'pair'}
        row['before'], row['bn'] = shoot(read(p), 390, 480, 'dash_keep')
        row['after'], row['an'] = shoot(read(p), 390, 480, 'dash_cut', True)
        row['captions'] = ('as it is, and stays',
                           'if this round had touched it')
        cells.append(row)
        print('shot %s (both sides)' % rel)
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>One Menu, Eight Opinions</title>
<style>
:root{
  --ink:#1d2327; --ink-soft:#5b6670; --rule:#dfe4e8;
  --ground:#f7f8f9; --card:#ffffff; --teal:#0e7c8b; --teal-ink:#0a5e6a;
  --bad:#b3261e;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
    --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
    --bad:#ff8a80;
  }
}
:root[data-theme="dark"]{
  --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
  --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
  --bad:#ff8a80;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  padding:24px 16px 64px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:1.5rem;margin:0 0 4px;letter-spacing:.01em}
.sub{color:var(--ink-soft);margin:0 0 6px}
.note{color:var(--ink-soft);font-size:.86rem;margin:0 0 18px;
  border-left:3px solid var(--teal);padding-left:10px}
.note.alarm{border-left-color:var(--bad)}
table.m{border-collapse:collapse;font-size:.85rem;margin:0 0 24px;
  font-variant-numeric:tabular-nums}
table.m th,table.m td{border-bottom:1px solid var(--rule);
  padding:5px 16px 5px 0;text-align:left}
table.m th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink-soft);font-weight:600}
.swatch{display:inline-block;width:11px;height:11px;border-radius:3px;
  vertical-align:-1px;margin-right:6px;border:1px solid rgba(0,0,0,.15)}
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:0 0 22px}
.page > h2{font-size:1.02rem;margin:0 0 2px}
.page > .file{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink-soft);margin:0 0 6px}
.page > .look{color:var(--ink-soft);font-size:.86rem;margin:0 0 12px}
.pair{display:grid;gap:12px;grid-template-columns:repeat(2,minmax(0,290px));
  justify-content:start}
figure{margin:0;min-width:0}
figcaption{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--ink-soft);margin:0 0 5px}
figcaption b{color:var(--teal-ink);font-weight:700}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
@media (max-width:660px){.pair{grid-template-columns:minmax(0,290px)}}
</style></head><body><div class="wrap">
<h1>One Menu, Eight Opinions</h1>
<p class="sub">H9 &mdash; twenty-four pages give up 22,357 characters of
<code>.action-more-*</code> CSS for a component base has styled since the
action-bar round.</p>

<p class="note alarm"><b>Most of it never applied.</b> base scopes its
button rule as <code>.page-action-buttons .action-more-btn</code> &mdash;
specificity (0,2,0). A page&rsquo;s bare <code>.action-more-btn</code> is
(0,1,0) and loses, however late in the document it sits.
<code>asset_detail.html</code> measures <b>zero difference</b> with its local
copy and without it: the whole thing was already dead. This round was
measured by deletion &mdash; each page rendered twice and the computed styles
diffed &mdash; rather than by reading the cascade.</p>

<table class="m">
<tr><th>The icon inside a More item</th><th>Pages</th></tr>
<tr><td><span class="swatch" style="background:#28a745"></span><code>#28a745</code></td><td>finance_revenue_types, view_meal_plan</td></tr>
<tr><td><span class="swatch" style="background:#ffc107"></span><code>#ffc107</code></td><td>unit_conversions_management, view_recipe</td></tr>
<tr><td><span class="swatch" style="background:#dc3545"></span><code>#dc3545</code></td><td>finance_expense_types</td></tr>
<tr><td>nothing at all</td><td>the three <code>projects/</code> pages</td></tr>
<tr><td><span class="swatch" style="background:#0e7c8b"></span><code>var(--alv-accent)</code></td><td>base, and now all of them</td></tr>
</table>

<p class="note"><b>Not one of those eight menus holds a destructive
action.</b> They are Help, Nutrition, Shopping List, Print Recipe, Edit,
Duplicate, Missing Conversions. The colours meant nothing &mdash; which is
the sentence base&rsquo;s own action standard already carries about buttons.</p>

<p class="note"><b>base gains one line, and it is overdue.</b>
<code>.action-more-menu[hidden] { display: none }</code>. base has styled
that menu completely since the action-bar round and never said how it hides
&mdash; every page that worked, worked because the <i>browser</i> hides
<code>[hidden]</code>. Two pages wrote the rule out locally rather than lean
on that.</p>

<p class="note">390&thinsp;px, shot after one tap of More &mdash; a closed
menu shows nothing. Icons are missing because Font&nbsp;Awesome is not
loaded in the fixture, so the icon colour shows as the gap where the glyph
would be; the item ink, the box and the padding are the visible part.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        out.append('<section class="page"><h2>%s</h2>'
                   '<p class="file">%s</p><p class="look">%s</p>'
                   % (c['label'], c['rel'], c['look']))
        cap = c.get('captions', ('before', 'after'))
        out.append('<div class="pair">'
                   '<figure><figcaption>&mdash; <b>%s</b>%s</figcaption>'
                   '<img alt="%s before" src="data:image/png;base64,%s"></figure>'
                   '<figure><figcaption>&mdash; <b>%s</b>%s</figcaption>'
                   '<img alt="%s after" src="data:image/png;base64,%s"></figure>'
                   '</div>'
                   % (cap[0], (' &mdash; ' + c['bn']) if c['bn'] else '',
                      c['label'], c['before'],
                      cap[1], (' &mdash; ' + c['an']) if c['an'] else '',
                      c['label'], c['after']))
        out.append('</section>')
    out.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    mb = os.path.getsize(OUT) / 1048576.0
    print('wrote %s  (%d sections, %.1f MB)' % (OUT, len(cells), mb))


if __name__ == '__main__':
    main()
