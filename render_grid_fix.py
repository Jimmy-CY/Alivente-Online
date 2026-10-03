# -*- coding: utf-8 -*-
"""render_grid_fix.py - four real filter panels, today and under one
base-level grid recipe.

Demetri, 3 Oct 2026: "The filter fields must be made less wide, so that
they fit on one line."

TWO FAULTS, ONE CAUSE. base's .filter-grid sets display:grid, a gap and
align-items and NO grid-template-columns, so every page has had to supply
its own. Thirteen do, in fr units, which makes each field stretch to a
share of the whole panel - Suppliers' search box renders 1178px wide at
1920. And ingredient_base_units_management, delivered yesterday as IB-1,
supplies NONE, so it falls back to a single column and its two fields
stack - which is the page that prompted this.
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(errors='replace')
    except Exception:
        pass

import os
import re
import base64

ROOT = os.getcwd()
_sys.path.insert(0, ROOT)
import alv_tree
from playwright.sync_api import sync_playwright

OUT = '/tmp/claude-0/grid_fix.html'
FIX = open(os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           encoding='utf-8', errors='replace').read()
BASE = open(alv_tree.path_of('base.html'), encoding='utf-8',
            errors='replace').read()

IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', re.S)
IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
FOR = re.compile(r'\{%\s*for\b.*?%\}(.*?)\{%\s*endfor\s*%\}', re.S)
ANY = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)

# THE RECIPES MODULE ONLY - Demetri, 3 Oct 2026: "No, I mean for the new
# filters we are just creating in the Recipes module". The measurement
# that found Suppliers at 1178px and Celebrations at 924px stands, and is
# written up for later; it is not this round's business.
#
# ingredient_base_units_management is here because it IS in this module
# and it IS broken: IB-1 shipped it yesterday with no grid-template-
# columns at all, so base's column-less .filter-grid falls back to one
# column and its two fields stack, each the full width of the panel.
PAGES = ['ingredient_base_units_management.html']

# THE PROPOSED BASE RECIPE. auto-fit so the browser decides how many fit;
# a floor so a field is never unusably narrow; a CAP so it never stretches
# into a banner; justify-content so the row packs from the left instead of
# spreading the slack between the fields.
def recipe(cap):
    return (""".filter-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, %dpx)) !important;
    justify-content: start !important;
}
@media screen and (max-width: 768px) {
  .filter-grid { grid-template-columns: 1fr !important; }
}""" % cap)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def resolve(h):
    prev = None
    while prev != h:
        prev = h
        h = IF_ELSE.sub(lambda m: m.group(1), h)
    prev = None
    while prev != h:
        prev = h
        h = IF_ONLY.sub(lambda m: m.group(1), h)
    prev = None
    while prev != h:
        prev = h
        h = FOR.sub(lambda m: m.group(1), h)
    return ANY.sub('', h)


def panel_of(t):
    i = -1
    for m in re.finditer(r'class="([^"]*)"', t):
        if 'alv-filter' in m.group(1).split():
            i = m.start()
            break
    if i < 0:
        return None
    i = t.rindex('<div', 0, i)
    depth, j = 0, i
    tag = re.compile(r'</?div\b')
    while True:
        m = tag.search(t, j)
        if not m:
            return None
        depth += 1 if t[m.start():m.start() + 2] == '<d' else -1
        j = m.end()
        if depth == 0:
            break
    j = t.index('>', j - 1) + 1
    return resolve(t[i:j]).replace('class="alv-filter',
                                   'class="is-open alv-filter')


PROBE = """() => {
  const g = document.querySelector('.filter-grid');
  if (!g) return null;
  const k = [...g.children];
  const b = new Set(k.map(e => Math.round(e.getBoundingClientRect().bottom)));
  return {rows: b.size, n: k.length, widest: Math.max(...k.map(e => {
    const c = e.querySelector('input,select,textarea');
    return c ? Math.round(c.getBoundingClientRect().width) : 0;
  }))};
}"""

SHOTS = []

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    for rel in PAGES:
        t = read(alv_tree.path_of(rel))
        html = panel_of(t)
        if not html:
            print('  %-42s could not slice' % rel)
            continue
        print('\n%s' % rel)
        for label, extra in (('TODAY', ''),
                             ('AFTER - capped 240px', recipe(240)),
                             ('AFTER - capped 280px', recipe(280))):
            for w in (1920, 1280):
                doc = ('<!doctype html><meta charset=utf-8>'
                       '<style>%s</style><style>%s</style>'
                       '<style>%s</style><style>%s</style>'
                       '<style>body{margin:0;padding:16px;background:#fff;'
                       'font-family:system-ui,sans-serif}</style>'
                       '<body>%s'
                       % (FIX, css_of(BASE), css_of(t), extra, html))
                pg.set_viewport_size({'width': w, 'height': 460})
                pg.set_content(doc, wait_until='domcontentloaded')
                pg.wait_for_timeout(80)
                r = pg.evaluate(PROBE)
                if not r:
                    continue
                cap = ('%s  -  %s  -  %dpx screen  -  %d field(s) on %d '
                       'row(s), widest %dpx'
                       % (rel.replace('.html', ''), label, w, r['n'],
                          r['rows'], r['widest']))
                SHOTS.append((cap, base64.b64encode(
                    pg.screenshot(full_page=True)).decode()))
                print('   %-22s %5d  %d field(s) on %d row(s)  widest %4dpx'
                      % (label, w, r['n'], r['rows'], r['widest']))
    br.close()

rows = ['<figure><figcaption>%s</figcaption>'
        '<img src="data:image/png;base64,%s"></figure>' % (c, p)
        for c, p in SHOTS]
open(OUT, 'w', encoding='utf-8').write(
    '<!doctype html><meta charset=utf-8><title>Filter grid</title>'
    '<style>body{font:14px system-ui;margin:24px;background:#f6f7f8}'
    'figure{margin:0 0 20px;background:#fff;padding:12px;'
    'border:1px solid #dcdfe2;border-radius:8px}'
    'figcaption{font-weight:600;margin-bottom:8px;color:#21343c}'
    'img{max-width:100%;border:1px solid #eceff1}</style>'
    + '\n'.join(rows))
print('\n  wrote %s  (%d shots)' % (OUT, len(SHOTS)))
