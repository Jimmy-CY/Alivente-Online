# -*- coding: utf-8 -*-
"""H7 BEFORE / AFTER - the green and the amber, desktop and phone.

DIFFERENT FROM EVERY EARLIER SHEET. Those rounds changed a page, so the
before/after came from the page's own backup. This round changes base and
leaves 33 of its 35 pages untouched - so the pair swaps THE STYLESHEET
and holds the markup still, which is the honest picture of what a base
round does.

Two pages change as well (they gave up a copy of a rule base now owns), so
those use their own backups on the before side too.

The real defect is on wcim_results: `bg-warning text-white`, which is
white on #ffc107 and measures 1.63. It is at the top of the sheet.

Not a test. A LOOK. The suite is test_good_warn.py.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_goodwarn'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h7_before_after.html')
SHOTS = os.path.join('/tmp', 'h7shots')

# (file, label, what to look at, css selector to scroll to, desktop h, phone h)
PAGES = [
    ('wcim_results.html', 'What Can I Make - Results',
     'Two tier heads (bg-success, bg-warning) each with text-white, score '
     'pills (badge-success, badge-warning) and a text-success line.',
     '.card', 700, 900),
    ('passport_management.html', 'Passports and Documents',
     'badge-success and badge-warning as status and as document type, in '
     'a table.', '.alv-table', 560, 760),
    ('personal_notification_settings.html', 'Notification Settings',
     'alert-success, the banner every save on this page puts up.',
     '.alert', 380, 500),
    # ANCHOR ON THE CLASS, NOT THE COMPONENT. '.alert' finds this page's
    # alert-success banner first and leaves the warning box below the
    # clip - the pair came out byte-identical and looked like a broken
    # render rather than a missed target.
    ('user_edit.html', 'Edit User',
     'alert-warning - the box that tells you you are editing yourself.',
     '.alert-warning', 460, 600),
    ('pantry_staples.html', 'Pantry Staples',
     'A card head painted bg-success with white text on it.',
     '.card-header', 520, 700),
]

FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def one_branch(t):
    """Keep the FIRST branch of every {% if %}. A STACK, not a depth
    counter - lesson from render_h4: an if/else nested inside an else-less
    if is never examined by a counter, and renders both halves."""
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
                start, first_end, cut = stack.pop()
                if cut is not None:
                    t = t[:start] + t[first_end:cut] + t[m.end():]
                    break
        else:
            return t


def body_one(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


boot = read(BOOT)


def fixture(base_text, page_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div>'
            '</body></html>'
            % (boot, '\n'.join(styles_of(base_text)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               FREEZE, body_one(page_text)))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    base_now, base_was = read(BASE), read(BASE + SUFFIX)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(html, w, h, anchor, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(html)
            ctx = br.new_context(viewport={'width': w, 'height': h},
                                 device_scale_factor=1)
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            if anchor:
                pg.evaluate(
                    "sel => {const e = document.querySelector(sel);"
                    " if (e) scrollTo(0, Math.max(0,"
                    " e.getBoundingClientRect().top + scrollY - 16));}",
                    anchor)
            png = pg.screenshot(clip={'x': 0, 'y': 0,
                                      'width': w, 'height': h})
            ctx.close()
            return base64.b64encode(png).decode('ascii')

        for rel, label, look, anchor, dh, ph in PAGES:
            p = os.path.join(T, rel)
            if not os.path.isfile(p):
                print('SKIP %s' % rel)
                continue
            now = read(p)
            # a page with its own backup gave up a rule; the rest did not
            was = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now
            row = {'rel': rel, 'label': label, 'look': look,
                   'own': os.path.isfile(p + SUFFIX)}
            for key, bt, pt in (('before', base_was, was),
                                ('after', base_now, now)):
                fx = fixture(bt, pt)
                row[key + '_d'] = shoot(fx, 1280, dh, anchor,
                                        '%s_%s_d' % (rel, key))
                row[key + '_p'] = shoot(fx, 390, ph, anchor,
                                        '%s_%s_p' % (rel, key))
            cells.append(row)
            print('shot %s' % rel)
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Green and the Amber</title>
<style>
:root{
  --ink:#1d2327; --ink-soft:#5b6670; --rule:#dfe4e8;
  --ground:#f7f8f9; --card:#ffffff; --teal:#0e7c8b; --teal-ink:#0a5e6a;
  --bad:#b3261e; --good:#1e7d4f;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
    --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
    --bad:#ff8a80; --good:#7fd6a4;
  }
}
:root[data-theme="dark"]{
  --ink:#e8ecef; --ink-soft:#9aa6b0; --rule:#2d363d;
  --ground:#14181b; --card:#1b2024; --teal:#2fa7b8; --teal-ink:#7fd3de;
  --bad:#ff8a80; --good:#7fd6a4;
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
table.m{border-collapse:collapse;font-size:.85rem;margin:0 0 26px;
  font-variant-numeric:tabular-nums}
table.m th,table.m td{border-bottom:1px solid var(--rule);
  padding:5px 12px 5px 0;text-align:left}
table.m th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink-soft);font-weight:600}
table.m td.n{text-align:right;padding-right:22px}
table.m td.up{color:var(--good);font-weight:600}
table.m td.low{color:var(--bad);font-weight:600}
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:0 0 22px}
.page > h2{font-size:1.02rem;margin:0 0 2px}
.page > .file{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink-soft);margin:0 0 6px}
.page > .look{color:var(--ink-soft);font-size:.86rem;margin:0 0 12px}
.tagown{display:inline-block;font-size:.68rem;letter-spacing:.06em;
  text-transform:uppercase;color:var(--teal-ink);border:1px solid var(--rule);
  border-radius:20px;padding:1px 8px;margin-left:6px;vertical-align:2px}
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
<h1>The Green and the Amber</h1>
<p class="sub">H7 &mdash; base answered Bootstrap&rsquo;s <code>info</code>
family in the accent round and never answered <code>success</code> or
<code>warning</code>, so those two still come straight off the CDN.</p>

<p class="note alarm"><b>The worst of it is not text.</b>
<code>wcim_results.html</code> heads its &ldquo;Almost there&rdquo; tier with
<code>bg-warning text-white</code> &mdash; white on <code>#ffc107</code>,
which measures <b>1.63</b>. Five more card heads do the same thing in green
at 3.13. Those six are the reason this round sets a colour on every fill it
repaints rather than only the background.</p>

<table class="m">
<tr><th>What</th><th class="n">Before</th><th class="n">After</th></tr>
<tr><td>bg-warning + text-white</td><td class="n low">1.63</td><td class="n up">5.38</td></tr>
<tr><td>text-warning on white</td><td class="n low">1.63</td><td class="n up">5.38</td></tr>
<tr><td>text-warning on the #e9ecef wash</td><td class="n low">1.37</td><td class="n up">4.54</td></tr>
<tr><td>badge-warning, as white ink</td><td class="n low">1.94</td><td class="n up">5.38</td></tr>
<tr><td>bg-success + text-white</td><td class="n low">3.13</td><td class="n up">5.12</td></tr>
<tr><td>text-success on white</td><td class="n low">3.13</td><td class="n up">5.12</td></tr>
<tr><td>text-success on the #e9ecef wash</td><td class="n low">2.64</td><td class="n up">4.32</td></tr>
<tr><td>badge-success</td><td class="n low">3.13</td><td class="n up">5.12</td></tr>
<tr><td>alert-warning</td><td class="n">4.96</td><td class="n up">7.34</td></tr>
<tr><td>alert-success</td><td class="n">6.99</td><td class="n up">7.56</td></tr>
</table>

<p class="note"><b>One number short of AA, said plainly.</b>
<code>text-success</code> on the deepest wash the system paints
(<code>#e9ecef</code>) comes out at <b>4.32</b>, where AA normal text is 4.50.
It was 2.64. <code>--alv-good</code> is a house token much older than this
round and used far beyond these fourteen rules, so deepening it is its own
decision with its own blast radius, not something to do inside a Bootstrap
round. No <code>text-success</code> in the tree sits on <code>#e9ecef</code>
today &mdash; the surfaces they are on are white (5.12), <code>bg-light</code>
(4.86) and wcim_results&rsquo; own <code>#fafafa</code> (4.91).</p>

<p class="note"><b>The button families get nothing, deliberately.</b>
<code>btn-success</code> 40, <code>btn-warning</code> 8,
<code>btn-outline-success</code> 4 &mdash; and read out, not one is a status:
Save, Add, Create, Generate, Email, WhatsApp, Continue, Try again, Edit.
They are actions wearing a status colour. base&rsquo;s action standard already
settles it &mdash; colour on an action is by <b>weight</b>, not by verb &mdash;
so a house tint here would make 52 buttons look deliberate while still being
drift, and would hide them from <code>Show-ButtonDrift</code> and from a
walkthrough that is about to go looking for exactly this. They want the
markup, in their own round. The suite fails if a <code>btn-*</code> family
ever appears in base.</p>

<p class="note"><b>These pairs swap the stylesheet, not the page.</b> Every
earlier sheet rendered a page&rsquo;s backup against the page; this round
changes base, so the markup is held still and base&rsquo;s own before/after
is what moves. A page marked <span class="tagown">gave up a rule</span> also
stopped declaring something base now owns, and uses its own backup on the
before side.</p>

<p class="note"><b>Two pages are not on this sheet, on purpose.</b>
<code>property_detail</code> gave up <code>.badge-success</code> and
<code>.badge-info</code>, and <code>tenant_add</code> gave up
<code>.alert-success</code>. Their before/after pairs are <i>identical</i> —
which is the whole argument for deleting them. property_detail had
independently reached <code>var(--alv-good)</code> and
<code>var(--alv-on-accent)</code>, the exact rule base now carries, and its
<code>.badge-info</code> was <code>#0e7c8b</code> plus the keyword
<code>white</code>, which is what <code>--alv-accent</code> and
<code>--alv-on-accent</code> already resolve to. A pair of identical
screenshots reads as a broken render, so the evidence is stated here
instead.</p>

<p class="note">1280&thinsp;px and 390&thinsp;px, same fixture both sides.
Icons are missing because Font&nbsp;Awesome is not loaded.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        tag = ('<span class="tagown">gave up a rule</span>' if c['own']
               else '')
        out.append('<section class="page"><h2>%s%s</h2>'
                   '<p class="file">%s</p><p class="look">%s</p>'
                   % (c['label'], tag, c['rel'], c['look']))
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
