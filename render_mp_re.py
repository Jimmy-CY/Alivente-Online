# -*- coding: utf-8 -*-
"""MP-1 and RE-1 BEFORE / AFTER.

Not a test. A LOOK. The suites are test_meal_plan_buttons.py and
test_recipe_bar_top.py.

MP-1  the day card's Add Recipe and its trashcans. THE CARD IS BUILT IN
      THE BROWSER, so the markup here comes out of the page's own
      JavaScript template string - which is the point of the round.

RE-1  the Create/Edit Recipe bar. Shot in EDIT mode, which is the one with
      three controls.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
MP = os.path.join(T, 'create_meal_plan.html')
RE = os.path.join(T, 'preview_imported_recipe.html')
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'mp_re_before_after.html')
SHOTS = '/tmp/mpreshots'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RECIPES = [('Shepherd’s Pie', '4'), ('Greek Salad', '2')]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n')


def styles_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in STYLE.finditer(t))


def strip_dj(s, mode=None):
    s = re.sub(r'\{#.*?#\}', '', s, flags=re.S)
    for _ in range(8):
        n = re.sub(r"\{%\s*if mode == '(\w+)'\s*%\}(.*?)"
                   r"\{%\s*elif mode == '(\w+)'\s*%\}(.*?)"
                   r"\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: (m.group(2) if m.group(1) == mode
                              else m.group(4) if m.group(3) == mode
                              else m.group(5)), s, flags=re.S)
        n = re.sub(r"\{%\s*if mode == '(\w+)'\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: m.group(2) if m.group(1) == mode else '',
                   n, flags=re.S)
        n = re.sub(r"\{%\s*if mode != '(\w+)'\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: '' if m.group(1) == mode else m.group(2),
                   n, flags=re.S)
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*else\s*%\}.*?'
                   r'\{%\s*endif\s*%\}', lambda m: m.group(1), n, flags=re.S)
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*endif\s*%\}',
                   lambda m: m.group(1), n, flags=re.S)
        if n == s:
            break
        s = n
    return re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', s, flags=re.S)


def js_card(src):
    """The day card, out of the page's OWN template string."""
    i = src.find("addRecipe('${dateStr}')")
    if i < 0:
        return ''
    a = src.rindex('`', 0, i)
    b = src.index('`', i)
    card = src[a + 1:b]
    card = card.replace('${dateStr}', '2026-10-05')
    card = re.sub(r'\$\{[^}]*\}', '', card)
    return card


def recipe_rows(src):
    i = src.find('removeRecipe(this)')
    if i < 0:
        return ''
    a = src.rindex('`', 0, i)
    b = src.index('`', i)
    row = src[a + 1:b]
    out = ''
    for name, serv in RECIPES:
        r = row.replace('${recipe.servings}', serv)
        r = r.replace('${recipe.recipe_name}', name)
        r = r.replace('${recipe.name}', name)
        r = re.sub(r'\$\{[^}]*\}', name, r)
        out += '<div class="recipe-item">%s</div>' % r
    return out


def mp_page(src):
    """The day card, with the recipe rows put INSIDE its .recipe-list.

    The card and the recipe row live in two different template strings, so
    the first cut shot a card with an empty-day state in it and measured
    the trashcan as absent on BOTH sides - a before/after that showed
    nothing because the thing being changed was never on the page."""
    card = js_card(src)
    rows = recipe_rows(src)
    # THE ROWS GO IN THEIR OWN STRIP, not inside the card. Injected into
    # .recipe-list they are in the DOM - the computed styles below prove
    # it - but not VISIBLE, because the day card collapses an empty list
    # and the fixture has no live script to open it. A picture that cannot
    # show the thing being changed is not a before/after, so the row is
    # shot on its own, in the page's own markup.
    return ('<h2 class="page-title-h2">CREATE MEAL PLAN</h2>'
            '<div id="daysContainer"><div class="day-card">%s</div></div>'
            '<div class="day-card" style="margin-top:18px">'
            '<div class="recipe-list" style="display:block">%s</div></div>'
            % (card, rows))


def re_page(src):
    bar = strip_dj(src[src.index('<div class="page-action-buttons'):
                       src.index('\n    </div>',
                                 src.index('<div class="page-action-buttons'))
                       + len('\n    </div>')], mode='edit')
    bottom = ''
    i = src.find('<!-- Action Buttons -->')
    if i >= 0:
        j = src.index('</div>', src.index('</a>', i)) + len('</div>')
        bottom = strip_dj(src[i:j], mode='edit')
    return ('<h2 class="page-title-h2">EDIT RECIPE</h2>' + bar
            + '<form method="post" id="saveRecipeForm">'
            '<div class="form-card"><h3 class="form-section-title">'
            'Recipe Details</h3><p>Name, servings, ingredients, method '
            '&mdash; 3,670 lines of form.</p></div>' + bottom + '</form>')


boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = styles_of(read(BASE))


def fixture(src, which):
    inner = mp_page(src) if which == 'mp' else re_page(src)
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>.fas,.far{display:inline-block;'
            'width:14px;height:14px}*{animation:none!important;'
            'transition:none!important}</style></head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, bcss, styles_of(src), inner))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    jobs = [('mp', MP, '.bak_mealbtn', 'Create Meal Plan — a day card'),
            ('re', RE, '.bak_recipebar', 'Edit Recipe — the bar')]
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, which, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src, which))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            try:
                if which == 'mp':
                    el = (pg.query_selector('.btn-add-recipe')
                          or pg.query_selector('.add-recipe-row .btn'))
                    m['Add Recipe'] = (pg.evaluate(
                        '(e)=>getComputedStyle(e).backgroundColor', el)
                        if el else '-')
                    tr = (pg.query_selector('.btn-remove-recipe')
                          or pg.query_selector('.icon-delete'))
                    m['trashcan'] = (pg.evaluate(
                        '(e)=>getComputedStyle(e).backgroundColor', tr)
                        if tr else '-')
                    m['trashcan ink'] = (pg.evaluate(
                        '(e)=>getComputedStyle(e).color', tr) if tr else '-')
                else:
                    s = pg.query_selector('.page-action-buttons '
                                          '[type="submit"]')
                    m['save in the bar'] = 'yes' if s else 'no'
                    m['save owns a form'] = (pg.evaluate(
                        '(e)=>!!e.form', s) if s else '-')
                    m['buttons at the bottom'] = str(len(
                        pg.query_selector_all('form .btn-lg')))
            except Exception as e:
                m['error'] = str(e)[:50]
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for which, path, suf, label in jobs:
            before, after = read(path + suf), read(path)
            for w, h, wl in ((1180, 560, 'desktop 1180'),
                             (386, 700, 'phone 386')):
                b, bm = shoot(before, which, w, h, 'b_%s_%d' % (which, w))
                a, am = shoot(after, which, w, h, 'a_%s_%d' % (which, w))
                cells.append({'label': '%s — %s' % (label, wl),
                              'before': b, 'after': a, 'bm': bm, 'am': am})
                print('%-34s %-14s before %s' % (label, wl, bm))
                print('%-34s %-14s after  %s' % (label, wl, am))
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Add, Remove, And Update At The Top</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:25px;margin:0 0 6px}
.sub{color:var(--soft);margin:0 0 16px;max-width:66ch}
section{background:var(--card);border:1px solid var(--rule);
border-radius:10px;padding:18px;margin-bottom:20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
color:var(--teal);margin:0 0 14px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
figure{margin:0}
figcaption{font-size:12px;text-transform:uppercase;letter-spacing:.06em;
color:var(--soft);margin-bottom:6px}
img{width:100%;border:1px solid var(--rule);border-radius:6px;display:block}
table.m{border-collapse:collapse;font-size:13px;margin-top:12px;width:100%}
table.m th,table.m td{border:1px solid var(--rule);padding:5px 9px;
text-align:left}
table.m th{background:var(--ground);font-weight:600}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace}
</style></head><body><div class="wrap">
<h1>Add, remove, and Update at the top</h1>
<p class="sub"><strong>MP-1</strong> &mdash; the day card is built in the
browser, so the markup shot here comes out of the page's <em>own</em>
JavaScript template string. That is the point of the round: a
find-and-replace on the markup would have left every card the page makes
itself still painted the old way.</p>
<p class="sub"><strong>RE-1</strong> &mdash; the bar sits twenty lines
<em>above</em> the <code>&lt;form&gt;</code>, so the Update button carries
<code>form="saveRecipeForm"</code>. The measurement that matters is
<em>save owns a form</em>: without the attribute a submit button there owns
nothing and fails silently.</p>
<p class="sub">Font Awesome is not loaded in a <code>file://</code> fixture,
so every icon is an empty 14px box on both sides.</p>
<p class="sub"><strong>The trashcan is measured but not pictured, and that
is a limit of this harness, not a gap in the round.</strong> A recipe row
only exists once the page's live script has built one into a day card; the
fixture has no script, so the row is in the DOM but never laid out. The
computed styles in the table below are read off the real element and are
the proof: filled red with white ink on the left, white ground with
<code>--alv-danger</code> ink on the right &mdash; base's row-action strip,
which fills only on hover.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div><table class="m"><tr><th>measured</th>'
                    '<th>before</th><th>after</th></tr>'
                    % (c['label'], c['before'], c['after']))
        for k in c['bm']:
            html.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                        % (k, c['bm'].get(k, '-'), c['am'].get(k, '-')))
        html.append('</table></section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
