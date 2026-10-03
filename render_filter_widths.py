# -*- coding: utf-8 -*-
"""render_filter_widths.py - the filter panel today, and at three candidate
field widths, so the number can be chosen by looking rather than by
arithmetic.

Demetri, 3 Oct 2026: "The filter fields must be made less wide, so that
they fit on one line."
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

OUT = '/tmp/claude-0/filter_widths.html'
FIX = open(os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           encoding='utf-8', errors='replace').read()
BASE = open(alv_tree.path_of('base.html'), encoding='utf-8',
            errors='replace').read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


BCSS = css_of(BASE)

# A panel written out plainly, with the house class names, so the only
# thing varying between shots is the grid recipe. Four fields, which is
# what cash_receipts, physical_invoice_list and the new Measurement Units
# panel all have.
PANEL = """
<div class="alv-filter is-open filter-panel">
  <div class="filter-header">
    <h5 class="filter-title"><i class="fas fa-filter"></i>
      <span class="filter-title-text">Filters</span></h5>
    <button type="button" class="btn btn-outline-secondary btn-sm">
      <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span>
    </button>
  </div>
  <div class="filter-content">
    <form method="get">
      <div class="filter-grid">
        <div class="filter-group">
          <label class="filter-label"><strong>Search</strong></label>
          <div class="search-input-group">
            <input type="text" class="form-control search-input"
                   placeholder="Search by name...">
          </div>
        </div>
        <div class="filter-group">
          <label class="filter-label"><strong>Type</strong></label>
          <select class="form-control filter-select">
            <option>All types</option><option>Volume</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label"><strong>Status</strong></label>
          <select class="form-control filter-select">
            <option>All statuses</option><option>Active</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label"><strong>From</strong></label>
          <input type="date" class="form-control">
        </div>
      </div>
    </form>
  </div>
</div>
"""

TODAY = '.filter-grid { grid-template-columns: 2fr 1fr 1fr 1fr; }'


def candidate(cap):
    return ('.filter-grid { grid-template-columns: '
            'repeat(auto-fit, minmax(190px, %dpx)); '
            'justify-content: start; }' % cap)


SHOTS = []


def run():
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        cases = [('TODAY - fr columns, each field stretches', TODAY)]
        for cap in (220, 260, 300):
            cases.append(('AFTER - capped at %dpx' % cap, candidate(cap)))
        for label, rule in cases:
            for w in (1920, 1440, 1280, 390):
                doc = ('<!doctype html><meta charset=utf-8>'
                       '<style>%s</style><style>%s</style>'
                       '<style>%s</style>'
                       '<style>@media screen and (max-width:768px){'
                       '.filter-grid{grid-template-columns:1fr !important}}'
                       'body{margin:0;padding:16px;background:#fff;'
                       'font-family:system-ui,sans-serif}</style>'
                       '<body>%s' % (FIX, BCSS, rule, PANEL))
                pg.set_viewport_size({'width': w, 'height': 420})
                pg.set_content(doc, wait_until='domcontentloaded')
                pg.wait_for_timeout(80)
                info = pg.evaluate("""() => {
                  const g = document.querySelector('.filter-grid');
                  const k = [...g.children];
                  /* BOTTOM, NOT TOP. base sets align-items: end on
                     .filter-grid, so groups of different heights on the
                     SAME row have different tops and the same bottom.
                     Counting tops reported two rows for a panel the
                     browser had laid out on one. */
                  const tops = new Set(k.map(e =>
                      Math.round(e.getBoundingClientRect().bottom)));
                  return {rows: tops.size, widest: Math.max(...k.map(e => {
                    const c = e.querySelector('input,select');
                    return c ? Math.round(c.getBoundingClientRect().width) : 0;
                  }))};
                }""")
                png = pg.screenshot(full_page=True)
                cap = '%s  -  %dpx screen  -  %d row(s), widest field %dpx' % (
                    label, w, info['rows'], info['widest'])
                SHOTS.append((cap, base64.b64encode(png).decode()))
                print('  %-44s %5d  %d row(s)  widest %4dpx'
                      % (label, w, info['rows'], info['widest']))
        br.close()


run()
rows = ['<figure><figcaption>%s</figcaption>'
        '<img src="data:image/png;base64,%s"></figure>' % (c, p)
        for c, p in SHOTS]
open(OUT, 'w', encoding='utf-8').write(
    '<!doctype html><meta charset=utf-8><title>Filter field widths</title>'
    '<style>body{font:14px system-ui;margin:24px;background:#f6f7f8}'
    'figure{margin:0 0 20px;background:#fff;padding:12px;'
    'border:1px solid #dcdfe2;border-radius:8px}'
    'figcaption{font-weight:600;margin-bottom:8px;color:#21343c}'
    'img{max-width:100%;border:1px solid #eceff1}</style>'
    + '\n'.join(rows))
print('\n  wrote %s  (%d shots)' % (OUT, len(SHOTS)))
