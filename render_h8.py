# -*- coding: utf-8 -*-
"""H8 BEFORE / AFTER - the three More buttons that did not work.

DIFFERENT FROM EVERY EARLIER SHEET IN ONE WAY: it CLICKS. A menu that is
closed looks exactly like a menu that is broken, so a still picture of
the bar proves nothing. Each page is shot twice - on arrival, and after
one tap of the More button - and the pair either changes or it does not.

The before side loads the page's OWN scripts, because the claim there is
about the page's own code. The after side loads base's binder and no page
script at all, because the claim there is that base is what makes it work.

Twenty-one other pages are in this round and are not on this sheet: they
worked before and they work now, and their menus are identical to look
at. What changed for them is that 26,317 characters of JavaScript went
away. test_more_menu.py opens and closes all twenty-four.

Not a test. A LOOK. The suite is test_more_menu.py.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SUFFIX = '.bak_moremenu'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'h8_before_after.html')
SHOTS = os.path.join('/tmp', 'h8shots')

PAGES = [
    ('finance_valuations.html', 'Property Valuations',
     'Its opener toggled a <code>.show</code> class that no rule in the '
     'tree defines, and its markup omitted <code>hidden</code> - so the '
     'panel hung open over the first card and the button did nothing.'),
    ('celebration_dashboard.html', 'Celebrations',
     'The markup was there and no opener ever was. The button did '
     'nothing at all.'),
    ('user_administration.html', 'User Administration',
     'It re-typed half of base&rsquo;s wrapper pair - the unscoped '
     '<code>display: none</code> without the media rule that puts it '
     'back - so the More button was hidden at every width, and the '
     'secondary actions it holds were unreachable on a phone.'),
]

FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


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
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))
binder = [s for s in SCRIPT.findall(read(BASE)) if 'data-menu-toggle' in s]


def fixture(page_text, with_page_js):
    js = binder[0] if binder else ''
    if with_page_js:
        js = '\n'.join(SCRIPT.findall(page_text)) + '\n' + js
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s'
            '<style>%s</style></head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s</div>'
            '<script>%s</script></body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               FREEZE, body_of(page_text), js))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 390, 'height': 560})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())

        def shoot(text, with_js, tag):
            """Two shots: on arrival, and after one tap of More."""
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, with_js))
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            a = pg.screenshot(clip={'x': 0, 'y': 0,
                                    'width': 390, 'height': 560})
            note = 'tapped'
            try:
                pg.click('#actionMoreBtn', timeout=3500)
            except Exception:
                note = 'the button could not be tapped - it is not visible'
            b = pg.screenshot(clip={'x': 0, 'y': 0,
                                    'width': 390, 'height': 560})
            pg.close()
            return (base64.b64encode(a).decode('ascii'),
                    base64.b64encode(b).decode('ascii'), note)

        for rel, label, look in PAGES:
            p = os.path.join(T, rel)
            if not (os.path.isfile(p) and os.path.isfile(p + SUFFIX)):
                print('SKIP %s' % rel)
                continue
            row = {'rel': rel, 'label': label, 'look': look}
            (row['b_a'], row['b_b'], row['b_note']) = shoot(
                read(p + SUFFIX), True, rel + '_before')
            (row['a_a'], row['a_b'], row['a_note']) = shoot(
                read(p), False, rel + '_after')
            cells.append(row)
            print('shot %s  (before: %s)' % (rel, row['b_note']))
        br.close()
    write_sheet(cells)


SHEET_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Three Dead More Buttons</title>
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
.page{background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:14px 14px 18px;margin:0 0 22px}
.page > h2{font-size:1.02rem;margin:0 0 2px}
.page > .file{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink-soft);margin:0 0 6px}
.page > .look{color:var(--ink-soft);font-size:.86rem;margin:0 0 12px}
.strip{display:grid;gap:12px;grid-template-columns:repeat(4,minmax(0,250px));
  justify-content:start}
figure{margin:0;min-width:0}
figcaption{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink-soft);margin:0 0 5px;min-height:2.2em}
figcaption b{color:var(--teal-ink);font-weight:700}
figcaption em{color:var(--bad);font-style:normal;font-weight:700}
img{display:block;width:100%;height:auto;border:1px solid var(--rule);
  border-radius:6px;background:#fff}
@media (max-width:920px){.strip{grid-template-columns:repeat(2,minmax(0,250px))}}
@media (max-width:560px){.strip{grid-template-columns:minmax(0,250px)}}
</style></head><body><div class="wrap">
<h1>Three Dead More Buttons</h1>
<p class="sub">H8 &mdash; twenty-three pages each wrote out their own
More-menu opener, 26,317 characters between them, nineteen of them identical
to the byte. base already had a binder waiting for them.</p>

<p class="note"><b>base gains no code in this round.</b> Its shared action
dropdown &mdash; driven by <code>data-menu</code>,
<code>data-menu-toggle</code> and <code>data-menu-panel</code> &mdash; has
been there since the menus round, and its own comment said why it could not
be bound to the More menu: a page carrying its own copy would be double-bound
and the menu would open and immediately close. Deleting the copies is what
lets the pages opt in. <code>fsr</code> and <code>tenant</code> had already
done exactly this, which is how the shape was confirmed rather than guessed.</p>

<p class="note alarm"><b>Three of the twenty-four did not work at all.</b>
That is what this sheet shows. The other twenty-one worked before and work
now and look identical either way &mdash; what changed for them is that their
copy of the opener is gone, and they picked up arrow-key navigation and
one-panel-at-a-time for free.</p>

<p class="note"><b>These strips CLICK.</b> A closed menu and a broken menu
look the same standing still, so each page is shot on arrival and again after
one tap of More. The <b>before</b> pair loads the page&rsquo;s own scripts,
because the claim there is about the page&rsquo;s own code. The <b>after</b>
pair loads base&rsquo;s binder and <em>no page script at all</em>, so a menu
that opens is base&rsquo;s doing.</p>

<p class="note">390&thinsp;px. Icons are missing because Font&nbsp;Awesome is
not loaded in the fixture.</p>
"""


def write_sheet(cells):
    out = [SHEET_HEAD]
    for c in cells:
        out.append('<section class="page"><h2>%s</h2>'
                   '<p class="file">%s</p><p class="look">%s</p>'
                   % (c['label'], c['rel'], c['look']))
        bnote = ('after a tap' if c['b_note'] == 'tapped'
                 else '<em>%s</em>' % c['b_note'])
        anote = ('after a tap' if c['a_note'] == 'tapped'
                 else '<em>%s</em>' % c['a_note'])
        out.append(
            '<div class="strip">'
            '<figure><figcaption><b>Before</b> &mdash; on arrival</figcaption>'
            '<img alt="%s before arrival" src="data:image/png;base64,%s"></figure>'
            '<figure><figcaption><b>Before</b> &mdash; %s</figcaption>'
            '<img alt="%s before tapped" src="data:image/png;base64,%s"></figure>'
            '<figure><figcaption><b>After</b> &mdash; on arrival</figcaption>'
            '<img alt="%s after arrival" src="data:image/png;base64,%s"></figure>'
            '<figure><figcaption><b>After</b> &mdash; %s</figcaption>'
            '<img alt="%s after tapped" src="data:image/png;base64,%s"></figure>'
            '</div>'
            % (c['label'], c['b_a'], bnote, c['label'], c['b_b'],
               c['label'], c['a_a'], anote, c['label'], c['a_b']))
        out.append('</section>')
    out.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    mb = os.path.getsize(OUT) / 1048576.0
    print('wrote %s  (%d pages, %.1f MB)' % (OUT, len(cells), mb))


if __name__ == '__main__':
    main()
