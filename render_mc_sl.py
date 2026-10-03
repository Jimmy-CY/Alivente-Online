# -*- coding: utf-8 -*-
"""render_mc_sl.py - before/after renders for MC-1, MC-2, MC-3 and SL-4.

Not a suite. Writes a single HTML sheet to the scratch folder showing each
visible change at desktop and phone width, BEFORE (read from this bundle's
backups) and AFTER, side by side, so the round can be looked at before it
is delivered.
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

OUT = '/tmp/claude-0/mc_renders.html'
FIX = open(os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           encoding='utf-8', errors='replace').read()
TAGS = re.compile(r'\{%\s*(?:if|else|elif|endif|for|empty|endfor)\b.*?%\}',
                  re.S)
IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', re.S)
IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
ANY_TAG = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def resolve(html):
    prev = None
    while prev != html:
        prev = html
        html = IF_ELSE.sub(lambda m: m.group(1), html)
    prev = None
    while prev != html:
        prev = html
        html = IF_ONLY.sub(lambda m: m.group(1), html)
    return ANY_TAG.sub('', html)


def slice_between(t, start, end):
    i = t.index(start)
    j = t.index(end, i)
    return t[i:j]


BASE = read(alv_tree.path_of('base.html'))
BCSS = css_of(BASE)

LISTP = alv_tree.path_of('meal_plans.html')
CALP = alv_tree.path_of('meal_plan_calendar.html')
SLP = alv_tree.path_of('meal_plan_shopping_list.html')

# BEFORE is the earliest backup of this bundle on each file; AFTER is the
# file. The bundle is MC-1 -> MC-2 -> MC-3 -> SL-4, so the earliest
# backup is the state Demetri is looking at on Live today.
BEFORE = {
    LISTP: LISTP + '.bak_viewseg',
    CALP: CALP + '.bak_viewseg',
    SLP: SLP + '.bak_emailrev',
}

SHOTS = []


def shot(pg, name, width, html, page_css, tail=''):
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:12px;background:#fff;'
           'font-family:system-ui,sans-serif}</style>'
           '<body>%s%s' % (FIX, BCSS, page_css, html, tail))
    pg.set_viewport_size({'width': width, 'height': 420})
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    pg.wait_for_timeout(120)
    png = pg.screenshot(full_page=True)
    SHOTS.append((name, width, base64.b64encode(png).decode()))
    print('  %-52s %4dpx' % (name, width))


def run():
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()

        # ---------------- MC-1  the switch -----------------------------
        for label, path in (('BEFORE', BEFORE[LISTP]), ('AFTER', LISTP)):
            t = read(path)
            bar = slice_between(t, '<div class="page-action-buttons">',
                                '{% if messages %}')
            for w in (1280, 390):
                shot(pg, 'MC-1 list page action bar - %s' % label, w,
                     resolve(bar), css_of(t))

        for label, path in (('BEFORE', BEFORE[CALP]), ('AFTER', CALP)):
            t = read(path)
            bar = slice_between(t, '<div class="page-action-buttons">',
                                '<div class="calendar-layout">')
            for w in (1280, 390):
                shot(pg, 'MC-1 calendar action bar - %s' % label, w,
                     resolve(bar), css_of(t))

        # ---------------- MC-2  the two action strips ------------------
        for label, path in (('BEFORE', BEFORE[CALP]), ('AFTER', CALP)):
            t = read(path)
            key = ('week-detail-actions' if label == 'BEFORE'
                   else 'row-actions')
            i = t.index('<div class="%s">' % key)
            j = t.index('{% endif %}', t.index('</div>', t.rindex(
                '</button>', i, t.index('<div class="week-detail-content">'))))
            for w in (1280, 390):
                shot(pg, 'MC-2 calendar week actions - %s' % label, w,
                     '<div class="week-detail-header"><h2>New</h2>'
                     + resolve(t[i:j]) + '</div>', css_of(t))

        for label, path in (('BEFORE', BEFORE[CALP]), ('AFTER', CALP)):
            t = read(path)
            key = ('recipe-actions' if label == 'BEFORE' else 'row-actions')
            i = t.index('<div class="%s">' % key, t.index('recipe-info'))
            j = t.index('</div>', t.index('{% endif %}', i)) + 6
            for w in (1280, 390):
                shot(pg, 'MC-2 recipe card actions - %s' % label, w,
                     '<div class="recipe-item"><div class="recipe-info">'
                     '<h5>Artichokes - Argero Recipe</h5>'
                     + resolve(t[i:j]) + '</div></div>', css_of(t))

        # ---------------- MC-3  the palette ----------------------------
        for label, path in (('BEFORE', BEFORE[CALP]), ('AFTER', CALP)):
            t = read(path)
            i = t.index('<div class="meal-plans-panel">') \
                if '<div class="meal-plans-panel">' in t else -1
            if i < 0:
                i = t.index('meal-plans-panel')
                i = t.rindex('<div', 0, i)
            j = t.index('</div>', t.index('create-plan-btn', i))
            j = t.index('</div>', j + 6) + 6
            for w in (1280, 390):
                shot(pg, 'MC-3 left panel and create - %s' % label, w,
                     resolve(t[i:j]), css_of(t))

        for label, path in (('BEFORE', BEFORE[LISTP]), ('AFTER', LISTP)):
            t = read(path)
            i = t.index('<div class="empty-state">')
            j = t.index('{% endif %}', i)
            for w in (1280, 390):
                shot(pg, 'MC-3 list empty state - %s' % label, w,
                     resolve(t[i:j]), css_of(t))

        # The no-permission Create button, which is the whole of finding 2.
        for label, path in (('BEFORE', BEFORE[LISTP]), ('AFTER', LISTP)):
            t = read(path)
            span = ('<span class="btn btn-create-disabled action-primary">'
                    '<i class="fas fa-plus"></i> Create New Meal Plan</span>'
                    if label == 'BEFORE' else
                    '<span class="btn action-primary disabled-btn">'
                    '<i class="fas fa-plus"></i> Create New Meal Plan</span>')
            shot(pg, 'MC-3 Create with NO permission - %s' % label, 1280,
                 '<div class="page-action-buttons">'
                 '<a class="btn action-primary"><i class="fas fa-plus"></i> '
                 'Create New Meal Plan</a>' + span + '</div>', css_of(t))

        # ---------------- SL-4  the email reveal -----------------------
        for label, path in (('BEFORE', BEFORE[SLP]), ('AFTER', SLP)):
            t = read(path)
            i = t.index('<div class="email-section">')
            j = t.index('<h2>Items to Buy</h2>')
            for w in (1280, 390):
                shot(pg, 'SL-4 share section, closed - %s' % label, w,
                     resolve(t[i:j]), css_of(t))

        # AND THE PANEL OPEN, which only exists after.
        t = read(SLP)
        i = t.index('<div class="email-section">')
        j = t.index('<h2>Items to Buy</h2>')
        opened = resolve(t[i:j]).replace('<div id="emailPanel" '
                                         'class="email-panel" hidden>',
                                         '<div id="emailPanel" '
                                         'class="email-panel">')
        for w in (1280, 390):
            shot(pg, 'SL-4 share section, Email pressed - AFTER', w,
                 opened, css_of(t))

        br.close()


run()

rows = []
for name, w, png in SHOTS:
    rows.append('<figure><figcaption>%s &mdash; %dpx</figcaption>'
                '<img src="data:image/png;base64,%s"></figure>'
                % (name, w, png))

open(OUT, 'w', encoding='utf-8').write(
    '<!doctype html><meta charset=utf-8><title>MC and SL renders</title>'
    '<style>body{font:14px system-ui;margin:24px;background:#f6f7f8}'
    'figure{margin:0 0 22px;background:#fff;padding:12px;'
    'border:1px solid #dcdfe2;border-radius:8px}'
    'figcaption{font-weight:600;margin-bottom:8px;color:#21343c}'
    'img{max-width:100%;border:1px solid #eceff1}</style>'
    + '\n'.join(rows))
print('\n  wrote %s  (%d shots)' % (OUT, len(SHOTS)))
