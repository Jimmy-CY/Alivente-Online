# -*- coding: utf-8 -*-
"""N3 - the hint under the two boxes that cannot narrow as you type.

Not a test. A LOOK. The suite is test_search_hint.py.

One shot per page per width, before and after, of the filter panel only -
the hint is one line and a full page would bury it.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_searchhint'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'n3_hint.html')
SHOTS = '/tmp/n3hint'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')

PAGES = [('projects/projects.html', 'Projects',
          'Searches the project <em>description</em> as well as the name, '
          'and pages at 25.'),
         ('recipe_management.html', 'Recipes',
          'Searches <em>ingredient names</em> in ingredient mode, which are '
          'never rendered, and pages at 48.')]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in STYLE.finditer(t)]


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


def panel_of(t):
    """The filter group that holds the search box, and nothing else."""
    t = one_branch(t)
    i = t.find('<div class="search-input-group">')
    if i < 0:
        return '<p>no search box</p>'
    # back out to the enclosing .filter-group
    a = t.rfind('<div class="filter-group"', 0, i)
    if a < 0:
        a = t.rfind('<div', 0, i)
    # forward to the end of that div
    j = t.find('>', a) + 1
    depth = 1
    for m in re.finditer(r'<div\b|</div\s*>', t[j:]):
        depth += 1 if m.group(0).startswith('<div') else -1
        if depth == 0:
            j = j + m.end()
            break
    b = t[a:j]
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '', b, flags=re.S)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))
bwas = None
if os.path.isfile(BASE + SUFFIX):
    bwas = '\n'.join(styles_of(read(BASE + SUFFIX)))


def fixture(page_text, base_css):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '%s<style>%s</style></head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<div class="alv-filter is-open"><div class="filter-content">'
            '<div class="filter-grid">%s</div></div></div>'
            '</div></body></html>'
            % (boot, base_css,
               ''.join('<style>%s</style>' % c
                       for c in styles_of(page_text)),
               FREEZE, panel_of(page_text)))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(text, base_css, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, base_css))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = None
            try:
                bb = pg.query_selector('.alv-search-hint').bounding_box()
                st = pg.evaluate(
                    "() => { const e = document.querySelector("
                    "'.alv-search-hint'); const s = getComputedStyle(e);"
                    " return [s.fontSize, s.color]; }")
                m = (round(bb['width']), round(bb['height']), st[0], st[1])
            except Exception:
                m = None
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for rel, label, why in PAGES:
            p = os.path.join(T, *rel.split('/'))
            if not (os.path.isfile(p) and os.path.isfile(p + SUFFIX)):
                print('SKIP %s' % rel)
                continue
            for w, h, wl in ((1100, 320, 'desktop 1100'), (386, 360, 'phone 386')):
                b, bm = shoot(read(p + SUFFIX), bwas or bcss, w, h,
                              '%s_b%d' % (label, w))
                a, am = shoot(read(p), bcss, w, h, '%s_a%d' % (label, w))
                cells.append({'label': '%s - %s' % (label, wl), 'why': why,
                              'before': b, 'after': a, 'bm': bm, 'am': am})
                print('%-22s %-14s before %s  after %s'
                      % (label, wl, bm, am))
        br.close()
    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Two Boxes That Ask For The Glass</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:25px;margin:0 0 6px}
.sub{color:var(--soft);margin:0 0 26px;max-width:62ch}
section{background:var(--card);border:1px solid var(--rule);
border-radius:10px;padding:18px;margin-bottom:20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
color:var(--teal);margin:0 0 4px}
.why{color:var(--soft);font-size:13.5px;margin:0 0 14px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:780px){.pair{grid-template-columns:1fr}}
figure{margin:0}
figcaption{font-size:12px;text-transform:uppercase;letter-spacing:.06em;
color:var(--soft);margin-bottom:6px}
img{width:100%;border:1px solid var(--rule);border-radius:6px;display:block}
.m{font-size:12.5px;color:var(--soft);margin-top:10px}
code{background:#eef1f3;padding:1px 5px;border-radius:3px}
</style></head><body><div class="wrap">
<h1>Two boxes that ask for the glass</h1>
<p class="sub">Four lists now narrow as you type. These two cannot, because
the server searches a field that is never drawn on the page &mdash; so the
line under the box is the honest answer rather than a filter that would
quietly disagree with the magnifying glass.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><p class="why">%s</p>'
                    '<div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div><p class="m">hint measured: <code>%s</code></p>'
                    '</section>'
                    % (c['label'], c['why'], c['before'], c['after'],
                       c['am']))
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(''.join(html))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
