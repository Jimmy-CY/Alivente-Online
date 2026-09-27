# -*- coding: utf-8 -*-
"""H2b BEFORE / AFTER - the action bar at phone width.

DIFFERENT FROM EVERY EARLIER SHEET. Most of the pages this round fixes were
not edited: the change is one rule in base, so the BEFORE fixture must use
BASE'S BACKUP stylesheet and the AFTER fixture base's live one, whether or
not the page file itself moved. Two pages moved as well and get both.

It also renders ONE BRANCH of each {% if %}. The plain fixture strips the tags
and leaves both branches standing, which is why two pages measured as "still
wrong" earlier today when Django renders them correctly.

Not a test. A LOOK. The suite is test_bar_mobile.py.
"""
import base64
import io
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_barmobile'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h2b_before_after.html')
SHOTS = os.path.join('/tmp', 'h2bshots')

# (file, label, did the PAGE change too?)
PAGES = [
    ('celebration_dashboard.html', 'Celebrations Dashboard', True),
    ('celebration_management.html', 'Celebrations Management', True),
    ('celebration_calendar.html', 'Celebration Calendar', False),
    ('finance.html', 'Financials', False),
    ('occupancy_trends.html', 'Occupancy Trends', False),
    ('passport_management.html', 'Passports', False),
]

MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')

# THE SHEET MUST SHOW THE THING IT IS ABOUT. .action-back has no border and
# its arrow is a Font Awesome glyph, so in a fixture with no icon font it is
# an invisible control - the first cut of this sheet showed four pages whose
# before and after were the same picture, and the round looked like it did
# nothing. This outline is an ANNOTATION drawn by the sheet, not a style the
# site has; the legend says so.
MARK = ('.action-back{outline:2px dashed #d81b60!important;'
        'outline-offset:2px;border-radius:4px}')


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


TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def one_branch(t):
    """Keep the FIRST branch of every {% if %} and drop the tags with it.

    Not a regex. A non-greedy if/else pattern collapses the wrong pair the
    moment an else-less {% if %} sits in front of one that has an else, and
    this file has both. So: walk the tags, track depth, and replace the
    whole if..endif with its first branch.

    The WHOLE construct goes. An earlier draft cut only from {% else %} to
    {% endif %} and left the opening {% if %} standing - which unbalanced
    the file, so depth never came back to zero and every later pair was
    skipped. One duplicate collapsed out of six and the sheet looked right
    enough to ship.

    Django renders ONE branch. The plain fixture strips the tags and leaves
    every branch standing, which is why two pages measured as "still wrong"
    this morning and are not.
    """
    while True:
        depth = start = first_end = cut_at = None
        depth = 0
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                depth += 1
                if depth == 1:
                    start, first_end, cut_at = m.start(), m.end(), None
            elif k == 'endif':
                depth -= 1
                if depth == 0 and cut_at is not None:
                    t = t[:start] + t[first_end:cut_at] + t[m.end():]
                    break
            elif depth == 1 and k in ('elif', 'else') and cut_at is None:
                cut_at = m.start()
        else:
            return t


def body_one(t):
    return body_markup(one_branch(t))


boot = read(BOOT)
BASE_NOW = '\n'.join(styles_of(read(BASE)))
_bb = BASE + SUFFIX
BASE_WAS = '\n'.join(styles_of(read(_bb))) if os.path.isfile(_bb) else None
if BASE_WAS is None:
    raise SystemExit('H2b: %s is missing - there is no BEFORE to render'
                     % os.path.basename(_bb))
if BASE_WAS == BASE_NOW:
    raise SystemExit('H2b: base\'s stylesheet is identical before and after, '
                     'so this sheet would show nothing')


def fixture(t, bcss):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>%s</style><style>%s</style>%s'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div>'
            '</body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c
                                   for c in styles_of(t)),
               FREEZE, MARK, body_one(t)))


def _px(g):
    if not g:
        return 'no bar here'
    bits = ('Back flush right' if g['gap'] == 0
            else 'Back absent' if g['gap'] is None
            else 'Back %dpx short of the right' % g['gap'])
    if g['cut']:
        bits += ', %d label%s cut off' % (g['cut'],
                                          '' if g['cut'] == 1 else 's')
    return bits


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
            # The number, not the eye - and measured against THE BAR, not
            # the viewport. occupancy_trends sits in a wrapper 8px narrower
            # than the others, so against the viewport it read 23px where
            # finance read 15 and both are flush. What "Back is on the
            # right" means is flush with its own bar.
            # Also counts controls WHOSE LABEL DOES NOT FIT, which is the
            # separate fault on the dashboard. Not boxes outside the bar:
            # flex shrinks the buttons instead of pushing them out, so every
            # box "fits" and the text is what gets cut. Before this round
            # Manage Contacts and Events wanted 176px in a 150px button and
            # rendered as "anage Contacts and Eve"; after, it gets 256.
            gap = pg.evaluate(
                "() => {const bar = document.querySelector("
                "'.page-action-buttons'); if (!bar) return null;"
                " const br = bar.getBoundingClientRect();"
                " const b = bar.querySelector('.action-back');"
                " const kids = [...bar.querySelectorAll(':scope > *')]"
                "   .filter(e => e.getBoundingClientRect().width > 0);"
                " const lim = Math.min(br.right, innerWidth);"
                " const cut = kids.filter(e =>"
                "   e.scrollWidth - e.clientWidth > 2"
                "   || e.getBoundingClientRect().right > lim + 1).length;"
                " const r = b && b.getBoundingClientRect();"
                " return {gap: (r && r.width)"
                "           ? Math.round(br.right - r.right) : null,"
                "         cut: cut};}")
            ctx.close()
            return base64.b64encode(png).decode('ascii'), gap

        for rel, label, page_moved in PAGES:
            p = os.path.join(T, rel)
            bak = p + SUFFIX
            if not os.path.isfile(p):
                print('SKIP %s - not here' % rel)
                continue
            if page_moved and not os.path.isfile(bak):
                print('SKIP %s - the page moved but has no backup' % rel)
                continue
            now = read(p)
            was = read(bak) if page_moved else now
            row = {'rel': rel, 'label': label, 'moved': page_moved}
            for key, txt, bcss in (('before', was, BASE_WAS),
                                   ('after', now, BASE_NOW)):
                fx = fixture(txt, bcss)
                row[key + '_d'], row[key + '_dg'] = shoot(
                    fx, 1280, 560, '%s_%s_d' % (rel, key))
                row[key + '_p'], row[key + '_pg'] = shoot(
                    fx, 390, 560, '%s_%s_p' % (rel, key))
            cells.append(row)
            print('shot %-30s phone: %s  ->  %s'
                  % (rel, _px(row['before_pg']), _px(row['after_pg'])))
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Back On The Right Edge</title>
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
.gap{display:block;text-transform:none;letter-spacing:0;font-size:.78rem;
  color:var(--warn);font-variant-numeric:tabular-nums;margin-top:2px}
.gap.ok{color:var(--teal-ink)}
.legend{display:inline-block;width:26px;height:12px;vertical-align:-1px;
  border:2px dashed #d81b60;border-radius:3px;margin:0 3px}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
.wide{overflow-x:auto}
@media (max-width:760px){
  .pair{grid-template-columns:1fr}
  .pair.phone{grid-template-columns:minmax(0,290px)}
}
</style></head><body><div class="wrap">
<h1>Back On The Right Edge</h1>
<p class="sub">H2b &mdash; one rule in base puts a lone Back back on the right on a phone; two Celebrations pages give up a crowded bar and a loose search field.</p>
<p class="note"><b>The dashed pink outline <span class="legend"></span> is
drawn by this sheet</b>, not by the site: it marks the Back button, which has
no border of its own and whose arrow is an icon-font glyph, so it would
otherwise be invisible here. The number under each phone shot is Back&rsquo;s
measured distance from the right-hand end of its own action bar, and
whether any control&rsquo;s label is wider than the button holding it.</p>
<p class="note"><b>Empty white boxes are the fixture, not the page.</b>
Font&nbsp;Awesome is not loaded here, so every icon-only control &mdash; More,
Filter, Back below 768&thinsp;px, and every row action &mdash; renders as its
own empty outline. They carry glyphs on the site.</p>
<p class="note"><b>The phone pair is the round.</b> Desktop is shown to prove
the rule is phone-only: on the four pages whose template did not change, the
two desktop shots are the same picture. Rendered at 1280&thinsp;px and
390&thinsp;px from base&rsquo;s backup stylesheet (before) and base&rsquo;s
live one (after) &mdash; and one branch of each <code>{% if %}</code>, the way
Django renders it.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        out.append('<section class="page"><h2>%s</h2>'
                   '<p class="file">%s &mdash; %s</p>'
                   % (c['label'], c['rel'],
                      'the page changed too' if c['moved']
                      else 'the page is untouched; base does the work'))
        out.append('<div class="pair wide">'
                   '<figure><figcaption>Desktop &mdash; <b>before</b></figcaption>'
                   '<img alt="%s desktop before" src="data:image/png;base64,%s"></figure>'
                   '<figure><figcaption>Desktop &mdash; <b>after</b></figcaption>'
                   '<img alt="%s desktop after" src="data:image/png;base64,%s"></figure>'
                   '</div>' % (c['label'], c['before_d'],
                               c['label'], c['after_d']))
        out.append('<div class="pair phone">'
                   '<figure><figcaption>Phone &mdash; <b>before</b>'
                   '<span class="gap">%s</span></figcaption>'
                   '<img alt="%s phone before" src="data:image/png;base64,%s"></figure>'
                   '<figure><figcaption>Phone &mdash; <b>after</b>'
                   '<span class="gap ok">%s</span></figcaption>'
                   '<img alt="%s phone after" src="data:image/png;base64,%s"></figure>'
                   '</div>' % (_px(c['before_pg']), c['label'], c['before_p'],
                               _px(c['after_pg']), c['label'], c['after_p']))
        out.append('</section>')
    out.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    mb = os.path.getsize(OUT) / 1048576.0
    print('wrote %s  (%d pages, %.1f MB)' % (OUT, len(cells), mb))


if __name__ == '__main__':
    main()
