# -*- coding: utf-8 -*-
"""H4 BEFORE / AFTER - the six Personal tables, desktop and phone.

The phone pair is where the component earns its place: every one of these
six pages had written out base's card collapse by hand, four of them the
pre-data-label way with the heading hard-coded into a positional rule.

Renders ONE BRANCH of each {% if %}, the way Django does - the plain fixture
leaves both standing and shows every permission-gated control twice.

Not a test. A LOOK. The suite is test_table_personal.py.
"""
import base64
import io
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_tablepersonal'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h4_before_after.html')
SHOTS = os.path.join('/tmp', 'h4shots')

PAGES = [
    ('passport_management.html', 'Passports'),
    ('household_member_management.html', 'Household Members'),
    ('categories_management.html', 'Ingredient Categories'),
    ('measurement_units_management.html', 'Measurement Units'),
    ('ingredient_base_units_management.html', 'Ingredient Base Units'),
    ('unit_conversions_management.html', 'Unit Conversions'),
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


def body_one(t):
    return body_markup(one_branch(t))


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
               FREEZE, body_one(t)))


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
<title>Six Tables Come Home</title>
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
<h1>Six Tables Come Home</h1>
<p class="sub">H4 &mdash; six Personal tables onto <code>.alv-table</code>, and 87 rules that were writing it out by hand are deleted.</p>
<p class="note"><b>Look hardest at Unit Conversions.</b> Five of these six
were already drawing something close to a house table; that one draws
floating cards, with a 3&thinsp;px lift on hover and 10&thinsp;px of air
between the rows. On the house table they become rows. That is the round
doing what it says, and it is the one pair where the change is a judgement
rather than a tidy-up.</p>
<p class="note"><b>Empty white boxes are the fixture, not the page.</b>
Font&nbsp;Awesome is not loaded here, so every icon-only control renders as
its own outline. The <b>row buttons keep their current colours on purpose</b>
&mdash; those are a second standard and the next round; this one puts the
right classes on the cells around them.</p>
<p class="note">Rendered from the backup (before) and from the changed file
(after), same stylesheet, at 1280&thinsp;px and 390&thinsp;px.</p>
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
