# -*- coding: utf-8 -*-
"""H7b BEFORE / AFTER - four hexes leave three projects/ pages.

A SMALL SHEET FOR A SMALL ROUND, and honest about how little moves. Two
of the five rules were dead before it started, and the one live text
colour shifts by a hair - #856404 to #8e6207, 5.49 to 5.38 on white.

The one thing anyone will actually see is the ALERT EDGE. Bootstrap's
rim measures 2.76 against the tint inside it; the house line is 1.25,
which is where H7 put it to match the accent family. Those alerts are
built inside a script, so they are shown here as components rather than
as a page - a fixture cannot run the code that injects them.

The delete page is shown whole, at both widths, so that "nothing else
moved" is something you can look at rather than take on trust.

Not a test. A LOOK. The suite is test_subtree_tones.py.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_subtree'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h7b_before_after.html')
SHOTS = os.path.join('/tmp', 'h7bshots')

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')

# The alerts this round repaints are injected by script, so they are
# built here by hand from the same classes the script uses.
COMPONENT = """
<div style="padding:18px;max-width:560px">
  <div class="alert alert-success">
    <strong>Saved.</strong> The task has been updated.
  </div>
  <div class="alert alert-warning">
    <strong>Careful.</strong> This task has subtasks that will move with it.
  </div>
  <div class="subtasks-warning">
    <h6 class="text-warning">Warning: this task has 3 subtasks</h6>
  </div>
</div>
"""

PAGES = [('projects/project_tasks_delete.html', 'Delete Task',
          'The only one of the five with a wearer you can see in the '
          'markup. Its heading moves from the page hex <code>#856404</code> '
          'to <code>--alv-warn</code> &mdash; a shift you will have to look '
          'for.')]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
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


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '3', b, flags=re.S)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(page_css, body):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, bcss, page_css, FREEZE, body))


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
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            png = pg.screenshot(clip={'x': 0, 'y': 0,
                                      'width': w, 'height': h})
            ctx.close()
            return base64.b64encode(png).decode('ascii')

        # 1. the injected alerts, as components
        ep = os.path.join(T, 'projects', 'project_tasks_edit.html')
        dp = os.path.join(T, 'projects', 'project_tasks_delete.html')
        row = {'kind': 'component', 'label': 'The alerts, and the heading',
               'rel': 'projects/project_tasks_edit.html + '
                      'project_tasks_delete.html',
               'look': 'Built here by hand, because the page injects them '
                       'from a script and a fixture cannot run that. The '
                       'edge is the visible change: a loud Bootstrap rim '
                       'becomes the house line.'}
        for key, src in (('before', SUFFIX), ('after', '')):
            css = '\n'.join(
                styles_of(read(ep + src)) + styles_of(read(dp + src)))
            row[key] = shoot(fixture(css, COMPONENT), 620, 260,
                             'comp_' + key)
        cells.append(row)

        # 2. the delete page, whole, at both widths
        for rel, label, look in PAGES:
            p = os.path.join(T, *rel.split('/'))
            row = {'kind': 'page', 'rel': rel, 'label': label, 'look': look}
            for key, src in (('before', SUFFIX), ('after', '')):
                t = read(p + src)
                fx = fixture('\n'.join(styles_of(t)), body_of(t))
                row[key + '_d'] = shoot(fx, 1280, 560, '%s_%s_d'
                                        % (label, key))
                row[key + '_p'] = shoot(fx, 390, 700, '%s_%s_p'
                                        % (label, key))
            cells.append(row)
            print('shot %s' % rel)
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Four Hexes in a Blind Spot</title>
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
  padding:5px 14px 5px 0;text-align:left}
table.m th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink-soft);font-weight:600}
table.m td.n{text-align:right;padding-right:22px}
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:0 0 22px}
.page > h2{font-size:1.02rem;margin:0 0 2px}
.page > .file{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink-soft);margin:0 0 6px}
.page > .look{color:var(--ink-soft);font-size:.86rem;margin:0 0 12px}
.pair{display:grid;gap:12px;grid-template-columns:1fr 1fr;margin-bottom:14px}
.pair.phone{grid-template-columns:repeat(2,minmax(0,290px));justify-content:start}
figure{margin:0;min-width:0}
figcaption{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--ink-soft);margin:0 0 5px}
figcaption b{color:var(--teal-ink);font-weight:700}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
@media (max-width:760px){
  .pair{grid-template-columns:1fr}
  .pair.phone{grid-template-columns:minmax(0,290px)}
}
</style></head><body><div class="wrap">
<h1>Four Hexes in a Blind Spot</h1>
<p class="sub">H7b &mdash; H7 pointed Bootstrap&rsquo;s success and warning
families at the house tokens. Its census ran over
<code>glob(&#39;pages/templates/*.html&#39;)</code>, which does not descend.</p>

<p class="note alarm"><b>There are 138 templates. H7 counted 120.</b>
Eighteen live in six subdirectories, eleven of them in
<code>projects/</code>. H7&rsquo;s <i>outcome</i> was fine &mdash; the fix is
in <code>base</code>, which every one of those templates extends, so they
were corrected the day it deployed. What H7 could not do is delete the
page-level rules that override base in a folder it never opened.
<code>test_hub_bar.py</code>, whose own census walks the tree, is what said
so during H8&rsquo;s sweep.</p>

<p class="note"><b>This is not a contrast round, and pretending otherwise
would be the easy thing to write.</b> The page hex <code>#856404</code>
measures 5.49 on white; the house token <code>#8e6207</code> measures 5.38.
The house token is a hair <i>worse</i>, and both pass AA comfortably. What
the round buys is that the system has one amber instead of two, and that
four hexes and one colour keyword leave a page&rsquo;s own stylesheet
&mdash; which standard 3.1 forbids precisely because a hex is invisible to
a token audit.</p>

<table class="m">
<tr><th>Rule</th><th>Page</th><th>State before</th></tr>
<tr><td><code>.btn-warning</code> + <code>:hover</code></td><td>projects_detail</td><td>dead &mdash; no wearer in markup or script</td></tr>
<tr><td><code>.text-warning</code></td><td>project_tasks_edit</td><td>dead &mdash; no wearer</td></tr>
<tr><td><code>.alert-success</code> border</td><td>project_tasks_edit</td><td>live, injected by script</td></tr>
<tr><td><code>.alert-warning</code> border</td><td>project_tasks_edit</td><td>live, injected by script</td></tr>
<tr><td><code>.subtasks-warning .text-warning</code></td><td>project_tasks_delete</td><td>live &mdash; colour removed, layout kept</td></tr>
</table>

<p class="note">1280&thinsp;px and 390&thinsp;px. Icons are missing because
Font&nbsp;Awesome is not loaded in the fixture.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        out.append('<section class="page"><h2>%s</h2>'
                   '<p class="file">%s</p><p class="look">%s</p>'
                   % (c['label'], c['rel'], c['look']))
        if c['kind'] == 'component':
            out.append('<div class="pair">'
                       '<figure><figcaption>&mdash; <b>before</b></figcaption>'
                       '<img alt="alerts before" src="data:image/png;base64,%s"></figure>'
                       '<figure><figcaption>&mdash; <b>after</b></figcaption>'
                       '<img alt="alerts after" src="data:image/png;base64,%s"></figure>'
                       '</div>' % (c['before'], c['after']))
        else:
            out.append('<div class="pair">'
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
    print('wrote %s  (%d sections, %.1f MB)' % (OUT, len(cells), mb))


if __name__ == '__main__':
    main()
