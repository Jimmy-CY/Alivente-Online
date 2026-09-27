# -*- coding: utf-8 -*-
"""G1 BEFORE / AFTER - renders the top of all 16 Personal pages the round
touches, at desktop and phone width, from the .bak_pagetitle backup and from
the file on disk, and writes one contact sheet.

Not a test. A LOOK. The suite is test_page_title.py.
"""
import base64
import io
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_celebrations'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h2_before_after.html')
SHOTS = os.path.join('/tmp', 'h2shots')

PAGES = [
    ('celebration_dashboard.html', 'Celebrations Dashboard'),
    ('celebration_management.html', 'Celebrations Management'),
    ('celebration_calendar.html', 'Celebration Calendar'),
]

MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(t):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div>'
            '</body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c
                                   for c in styles_of(t)),
               FREEZE, body_markup(t)))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(html, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(html)
            ctx = br.new_context(viewport={'width': w, 'height': h},
                                 device_scale_factor=1)
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            png = pg.screenshot(clip={'x': 0, 'y': 0,
                                      'width': w, 'height': h})
            ctx.close()
            return base64.b64encode(png).decode('ascii')

        for rel, label in PAGES:
            p = os.path.join(T, rel)
            bak = p + SUFFIX
            if not (os.path.isfile(p) and os.path.isfile(bak)):
                print('SKIP %s' % rel)
                continue
            row = {'rel': rel, 'label': label}
            for key, txt in (('before', read(bak)), ('after', read(p))):
                fx = fixture(txt)
                row[key + '_d'] = shoot(fx, 1280, 560, '%s_%s_d' % (rel, key))
                row[key + '_p'] = shoot(fx, 390, 560, '%s_%s_p' % (rel, key))
            cells.append(row)
            print('shot %s' % rel)
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Celebrations Joins the House</title>
<style>
:root{
  --ink:#1d2327; --ink-soft:#5b6670; --rule:#dfe4e8;
  --ground:#f7f8f9; --card:#ffffff; --teal:#0e7c8b; --teal-ink:#0a5e6a;
  --warn:#b3261e;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
    --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
    --warn:#ff8a80;
  }
}
:root[data-theme="dark"]{
  --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
  --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
  --warn:#ff8a80;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  padding:24px 16px 64px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:1.5rem;margin:0 0 4px;letter-spacing:.01em}
.sub{color:var(--ink-soft);margin:0 0 6px}
.note{color:var(--ink-soft);font-size:.86rem;margin:0 0 28px;
  border-left:3px solid var(--teal);padding-left:10px}
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:0 0 22px}
.page > h2{font-size:1.02rem;margin:0 0 2px}
.page > .file{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink-soft);margin:0 0 12px}
.pair{display:grid;gap:12px;grid-template-columns:1fr 1fr;margin-bottom:14px}
.pair.phone{grid-template-columns:repeat(2,minmax(0,290px));justify-content:start}
figure{margin:0;min-width:0}
figcaption{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--ink-soft);margin:0 0 5px}
figcaption b{color:var(--teal-ink);font-weight:700}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
.wide{overflow-x:auto}
@media (max-width:760px){
  .pair{grid-template-columns:1fr}
  .pair.phone{grid-template-columns:minmax(0,290px)}
}
</style></head><body><div class="wrap">
<h1>Celebrations Joins the House</h1>
<p class="sub">H2 &mdash; cards become buttons, the search moves up, the modals and row actions take house controls.</p>
<p class="note">Rendered from the backup (before) and from the changed file
(after), same stylesheet, same widths: 1280&thinsp;px desktop and
390&thinsp;px phone. Only the top of each page is shown &mdash; that is all
this round changes.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        out.append('<section class="page"><h2>%s</h2>'
                   '<p class="file">%s</p>' % (c['label'], c['rel']))
        out.append('<div class="pair wide">'
                   '<figure><figcaption>Desktop &mdash; <b>before</b></figcaption>'
                   '<img alt="%s desktop before" src="data:image/png;base64,%s"></figure>'
                   '<figure><figcaption>Desktop &mdash; <b>after</b></figcaption>'
                   '<img alt="%s desktop after" src="data:image/png;base64,%s"></figure>'
                   '</div>' % (c['label'], c['before_d'],
                               c['label'], c['after_d']))
        out.append('<div class="pair phone">'
                   '<figure><figcaption>Phone &mdash; <b>before</b></figcaption>'
                   '<img alt="%s phone before" src="data:image/png;base64,%s"></figure>'
                   '<figure><figcaption>Phone &mdash; <b>after</b></figcaption>'
                   '<img alt="%s phone after" src="data:image/png;base64,%s"></figure>'
                   '</div>' % (c['label'], c['before_p'],
                               c['label'], c['after_p']))
        out.append('</section>')
    out.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    mb = os.path.getsize(OUT) / 1048576.0
    print('wrote %s  (%d pages, %.1f MB)' % (OUT, len(cells), mb))


if __name__ == '__main__':
    main()
