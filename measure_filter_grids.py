# -*- coding: utf-8 -*-
"""measure_filter_grids.py - how wide is every filter field, on every page
that has a panel, at three widths.

Not a suite. Demetri, 3 Oct 2026: "The filter fields must be made less
wide, so that they fit on one line." Eleven pages carry a panel and each
sets its own grid-template-columns in fr units, so each field stretches
to fill whatever the panel is given. This prints what that actually comes
to, and how many rows the fields land on, so the fix is aimed at a
measurement rather than at a guess.
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(errors='replace')
    except Exception:
        pass

import os
import re

ROOT = os.getcwd()
_sys.path.insert(0, ROOT)
import alv_tree
from playwright.sync_api import sync_playwright

FIX = open(os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           encoding='utf-8', errors='replace').read()
IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', re.S)
IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
FOR = re.compile(r'\{%\s*for\b.*?%\}(.*?)\{%\s*endfor\s*%\}', re.S)
ANY = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)


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
    # ONE iteration of every loop. A filter panel's loops fill <option>
    # lists; the field's WIDTH does not depend on how many options it has.
    prev = None
    while prev != h:
        prev = h
        h = FOR.sub(lambda m: m.group(1), h)
    return ANY.sub('', h)


BASE = read(alv_tree.path_of('base.html'))
BCSS = css_of(BASE)

JS = """() => {
  const g = document.querySelector('.filter-grid');
  if (!g) return null;
  const kids = [...g.children];
  /* BOTTOM, NOT TOP - base sets align-items: end on .filter-grid, so two
     groups of different heights on the SAME row have different tops and
     the same bottom. Counting tops reported two rows for panels the
     browser had laid out on one. */
  const tops = new Set(kids.map(e => Math.round(e.getBoundingClientRect().bottom)));
  return {
    panelW: Math.round(g.getBoundingClientRect().width),
    cols: getComputedStyle(g).gridTemplateColumns,
    rows: tops.size,
    fields: kids.map(e => {
      const c = e.querySelector('input, select, textarea');
      return {
        label: (e.querySelector('.filter-label, label') || {}).innerText || '?',
        groupW: Math.round(e.getBoundingClientRect().width),
        ctrlW: c ? Math.round(c.getBoundingClientRect().width) : null,
        tag: c ? c.tagName.toLowerCase() : null
      };
    })
  };
}"""


def panel_of(t):
    """The .alv-filter panel, whole, forced open.

    NOT BY GUESSING WHERE IT ENDS. The first cut looked for the next
    table or comment after the panel opened and took everything up to
    it; on six of fifteen pages that overshot or undershot and the slice
    arrived with no .filter-grid in it at all - so the pages with the
    MOST fields, the ones this measurement is actually about, were the
    ones it could not read. Count the divs instead."""
    # A CLASS IS A TOKEN, NOT A SUBSTRING. t.find('class="alv-filter')
    # matched class="alv-filter-active" - the CHIP ROW, which sits above
    # the panel and contains no fields at all - on all fifteen pages. The
    # slice was then four tags long and the measurement reported that no
    # page in the tree had a filter grid. Twentieth time this week.
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
    h = resolve(t[i:j])
    return h.replace('class="alv-filter', 'class="is-open alv-filter')


PAGES = []
for rel in sorted(alv_tree.templates()):
    t = read(alv_tree.path_of(rel))
    if 'class="alv-filter' in t and 'filter-grid' in t:
        PAGES.append(rel)

print('=' * 78)
print('FILTER PANELS - %d pages carry one' % len(PAGES))
print('=' * 78)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    for rel in PAGES:
        t = read(alv_tree.path_of(rel))
        html = panel_of(t)
        if not html:
            continue
        print('\n%s' % rel)
        for w in (1920, 1440, 1280, 390):
            doc = ('<!doctype html><meta charset=utf-8>'
                   '<style>%s</style><style>%s</style><style>%s</style>'
                   '<style>body{margin:0;padding:16px}</style><body>%s'
                   % (FIX, BCSS, css_of(t), html))
            pg.set_viewport_size({'width': w, 'height': 700})
            pg.set_content(doc, wait_until='domcontentloaded')
            try:
                r = pg.evaluate(JS)
            except Exception as e:
                print('   %4d  could not measure: %s' % (w, str(e)[:50]))
                continue
            if not r:
                print('   %4d  no .filter-grid in the slice' % w)
                continue
            widest = max((f['ctrlW'] or 0) for f in r['fields']) \
                if r['fields'] else 0
            print('   %4d  panel %4d  %d field(s) on %d row(s)  widest '
                  'control %4dpx   %s'
                  % (w, r['panelW'], len(r['fields']), r['rows'], widest,
                     r['cols'][:46]))
            if w == 1920:
                for f in r['fields']:
                    print('           %-26s %s %4spx'
                          % (f['label'].replace('\n', ' ')[:26],
                             (f['tag'] or '-')[:6], f['ctrlW']))
    br.close()

print('\n' + '=' * 78)
