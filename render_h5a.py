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
SUFFIX = '.bak_tablepreview'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h5a_before_after.html')
SHOTS = os.path.join('/tmp', 'h5ashots')

PAGES = [
    ('preview_imported_recipe.html', 'Imported Recipe - preview and edit'),
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
    """Keep the FIRST branch of every {% if %}, tags and all.

    A STACK, NOT A DEPTH COUNTER. The first version tracked depth and only
    ever cut at depth 1, so an if/else NESTED INSIDE AN ELSE-LESS if was
    never examined - and that is exactly how household_member_management
    writes its Activate/Deactivate toggle:

        {% if can_edit %}                      <- no else, never cut
          <button class="... {% if m.is_active %}icon-lock
                            {% else %}icon-unlock{% endif %}">

    so the fixture rendered BOTH halves and the button came out with the
    class `icon-lockicon-unlock` and the title `DeactivateActivate`.
    Django renders one. An endif closes the innermost frame first, so a
    stack collapses inside-out and needs no special case for nesting.
    """
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
                    return t          # unbalanced: leave it alone
                start, first_end, cut = stack.pop()
                if cut is not None:
                    t = t[:start] + t[first_end:cut] + t[m.end():]
                    break
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


ANCHOR = '#ingredientsTable'


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
            # THESE TABLES ARE NOT AT THE TOP OF THE PAGE. Every earlier
            # sheet shot from y=0 because every earlier round changed the
            # bar or the heading; this one changes a grid two screens
            # down, and a shot of the top would show the round doing
            # nothing at all.
            if ANCHOR:
                pg.evaluate(
                    "sel => {const e = document.querySelector(sel);"
                    " if (e) scrollTo(0, Math.max(0,"
                    " e.getBoundingClientRect().top + scrollY - 24));}",
                    ANCHOR)
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
                row[key + '_d'] = shoot(fx, 1280, 620, '%s_%s_d' % (rel, key))
                row[key + '_p'] = shoot(fx, 390, 760, '%s_%s_p' % (rel, key))
            cells.append(row)
            print('shot %s' % rel)
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Two Grids Of Fields</title>
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
<h1>Two Grids Of Fields</h1>
<p class="sub">H5a &mdash; the two imported-recipe grids onto <code>.alv-table</code>, in the markup <em>and</em> in the JavaScript that adds a row.</p>
<p class="note"><b>These are tables of form inputs, and that was a real
question.</b> base lays a phone card out as label left, value right, which
could have squeezed a full-width text field. Measured instead of assumed: at
390&thinsp;px the ingredient row goes from <b>494&thinsp;px tall to
307&thinsp;px</b> and every input keeps 215&thinsp;px of width.</p>
<p class="note"><b>Two row templates, not one.</b> Each grid is built once by
Django and again by JavaScript, for &ldquo;Add Another&rdquo;. Labelling only
the markup would give a phone card its headings on the rows that came from the
server and none on the rows you just added &mdash; which reads as a bug in the
data rather than in the page. Both are done; the suite counts them
separately.</p>
<p class="note"><b>The pinned corners stay.</b> On a phone this page does not
put the drag handle and the remove button in the card &mdash; it pins them to
its top corners. base has no drag handle and no opinion about one, so those
rules are page logic and are kept.</p>
<p class="note">Rendered from the backup (before) and from the changed file
(after), same stylesheet, at 1280&thinsp;px and 390&thinsp;px. Icons are
missing because Font&nbsp;Awesome is not loaded in the fixture.</p>
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
