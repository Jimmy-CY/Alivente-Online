# -*- coding: utf-8 -*-
"""P3 BEFORE / AFTER - Project Detail's pills and row actions.

Not a test. A LOOK. The suite is test_detail_pills.py.

The cards are planted, because one task cannot show four priorities and
four statuses at once. THE CLASS STRINGS ARE NOT TYPED HERE: pill_for()
reads the {% if %} chain out of the template being shot and evaluates it,
so if the round's branches change these pictures change with them.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
PAGE = os.path.join(T, 'projects', 'projects_detail.html')
SUFFIX = '.bak_detailpills'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'p3_before_after.html')
SHOTS = '/tmp/p3shots'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
# Font Awesome is not loaded in a file:// fixture, so an <i> has NO SIZE
# and every button collapses to its padding. The first cut of this harness
# reported the subtask button as smaller than the task button, which is the
# opposite of the truth. A 14px box stands in for the glyph so both sides
# are measured with identical content. Checked on its own, with the real
# Bootstrap 4.1.3 fixture and the same content in each:
#
#     btn-sm              32x31
#     btn-xs (undefined)  40x38
#     plain .btn          40x38
#
# btn-xs is not in Bootstrap 4 and we do not define it, so it falls all the
# way back to .btn - which is why the subtask buttons render LARGER than
# the task buttons above them.
GLYPH = '.fas,.far{display:inline-block;width:14px;height:14px}'
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}'
          + GLYPH)

TASKS = [('Update Kitchen', 'Critical', 'In Progress',
          [('Backsplash', 'High', 'Completed'),
           ('Granite Top Replacement', 'Medium', 'On Hold')]),
         ('Bedrooms Update', 'Low', 'Pending',
          [('Paint Bedrooms', 'Critical', 'Pending')])]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in STYLE.finditer(t)]


def chain_for(cls, value):
    """Evaluate a template class string's {% if %} chain for `value`.
    BEFORE the round there is no chain - the class is generated - and
    this returns that, so one function serves both sides."""
    if '{%' not in cls:
        return re.sub(r'\{\{[^}]*\}\}',
                      (value or '').lower().replace(' ', '-'), cls)
    fixed = re.sub(r'\{%.*?%\}', '', cls).strip()
    for cond, tone in re.findall(r'\{%\s*(?:el)?if\s+(.*?)\s*%\}([a-z-]+)',
                                 cls):
        if any(lit == value for lit in re.findall(r"==\s*'([^']*)'", cond)):
            return (fixed + ' ' + tone).strip()
    els = re.search(r'\{%\s*else\s*%\}([a-z-]+)', cls)
    return (fixed + ' ' + (els.group(1) if els else '')).strip()


def grab(src, needle):
    """The class string of the first <span> whose markup follows `needle`."""
    i = src.find(needle)
    if i < 0:
        return ''
    m = re.search(r'<span class="((?:[^"]|\{%[^%]*%\})*)"', src[i:i + 900])
    return ' '.join(m.group(1).split()) if m else ''


def actions(src, live, kind):
    """The round's own action markup, or the old one, for one row."""
    if 'icon-action-btn' in src:
        if live:
            return ('<span class="row-actions ml-2">'
                    '<a href="#" class="icon-action-btn icon-edit">'
                    '<i class="fas fa-pencil-alt"></i></a>'
                    '<button class="icon-action-btn icon-delete">'
                    '<i class="fas fa-trash"></i></button></span>')
        return ('<span class="row-actions ml-2">'
                '<span class="icon-action-btn icon-disabled">'
                '<i class="fas fa-pencil-alt"></i></span>'
                '<span class="icon-action-btn icon-disabled">'
                '<i class="fas fa-trash"></i></span></span>')
    sz = 'btn-xs' if kind == 'subtask' else 'btn-sm'
    return ('<div class="btn-group ml-2">'
            '<a href="#" class="btn %s btn-info"><i class="fas fa-edit">'
            '</i></a><button class="btn %s btn-danger">'
            '<i class="fas fa-trash"></i></button></div>' % (sz, sz))


def card_html(src):
    pri_src = grab(src, 'task-priority-indicator') or grab(src, 'alv-pill')
    out = []
    for name, pri, sta, subs in TASKS:
        tp = grab(src, 'task-priority-indicator') or pri_src
        ts = grab(src, 'task-status-badge') or grab(src, 'alv-pill')
        # after the round both pills are alv-pill chains; pick by field
        if 'alv-pill' in src and '{%' in src:
            spans = re.findall(r'<span class="(alv-pill (?:[^"]|\{%[^%]*%\})*)"',
                               src)
            tp = next((s for s in spans if 'task.task_priority' in s), tp)
            ts = next((s for s in spans
                       if 'task.get_calculated_status' in s), ts)
        out.append(
            '<div class="task-card"><div class="task-header">'
            '<div class="task-title-section"><h5 class="task-title">'
            '<span class="%s">%s</span>'
            '<span class="task-name-text">%s</span>'
            '<a href="#" class="btn action-secondary add-subtask-btn ml-2">'
            '<i class="fas fa-plus"></i> Add Subtask</a></h5></div>'
            '<div class="task-actions"><span class="%s">%s</span>%s</div>'
            '</div>' % (chain_for(tp, pri), pri, name,
                        chain_for(ts, sta), sta, actions(src, True, 'task')))
        rows = []
        for sn, sp, ss in subs:
            sps = tp
            sss = ts
            if 'alv-pill' in src and '{%' in src:
                spans = re.findall(
                    r'<span class="(alv-pill (?:[^"]|\{%[^%]*%\})*)"', src)
                sps = next((s for s in spans
                            if 'subtask.task_priority' in s), tp)
                sss = next((s for s in spans
                            if 'subtask.task_status' in s), ts)
            else:
                sps = grab(src, 'subtask-priority-indicator') or tp
                sss = grab(src, 'subtask-status-badge') or ts
            rows.append(
                '<div class="subtask-item"><div class="subtask-header">'
                '<div class="subtask-title"><span class="%s">%s</span>'
                '<span class="subtask-name-text">%s</span></div>'
                '<div class="subtask-actions"><span class="%s">%s</span>%s'
                '</div></div></div>'
                % (chain_for(sps, sp), sp, sn,
                   chain_for(sss, ss).replace('clickable-status',
                                              'clickable-status'),
                   ss, actions(src, True, 'subtask')))
        out.append('<div class="subtasks-section">'
                   '<div class="subtasks-container">%s</div></div></div>'
                   % ''.join(rows))
    return ''.join(out)


def head_html(src):
    sb = grab(src, 'project-status-container')
    edit = ('<span class="row-actions">'
            '<a href="#" class="icon-action-btn icon-edit">'
            '<i class="fas fa-pencil-alt"></i></a></span>'
            if 'icon-action-btn' in src else
            '<a href="#" class="btn btn-sm btn-info ml-2">'
            '<i class="fas fa-edit"></i></a>')
    return ('<div class="project-overview-card"><div class="row">'
            '<div class="col-md-8"><h3>New Project</h3>'
            '<p class="project-property"><i class="fas fa-home"></i> '
            '<strong>Property:</strong> Palikaridi</p></div>'
            '<div class="col-md-4 text-right overview-status-col">'
            '<div class="project-status-container">'
            '<span class="%s">Pending</span>%s</div></div></div></div>'
            % (chain_for(sb, 'Pending'), edit))


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(src):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<div class="tasks-section-header"><h4>'
            '<i class="fas fa-tasks"></i> Project Tasks</h4>'
            '<a href="#" class="btn action-secondary add-task-btn">'
            '<i class="fas fa-plus"></i> Add Task</a></div>'
            '%s<div class="tasks-container">%s</div></div></body></html>'
            % (boot, bcss, '\n'.join(styles_of(src)), FREEZE,
               head_html(src), card_html(src)))


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SHOTS, exist_ok=True)
    before, after = read(PAGE + SUFFIX), read(PAGE)
    cells = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shoot(src, w, h, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(src))
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.goto('file://' + fx)
            m = {}
            for sel, key in (('.task-actions a', 'task edit btn'),
                             ('.subtask-actions a', 'subtask edit btn'),
                             ('.task-actions span', 'task status pill')):
                try:
                    bb = pg.query_selector(sel).bounding_box()
                    m[key] = '%dx%d' % (round(bb['width']),
                                        round(bb['height']))
                except Exception:
                    m[key] = None
            png = pg.screenshot(full_page=True)
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for w, h, lab in ((1180, 760, 'desktop 1180'),
                          (386, 820, 'phone 386')):
            b, bm = shoot(before, w, h, 'b%d' % w)
            a, am = shoot(after, w, h, 'a%d' % w)
            cells.append({'label': lab, 'before': b, 'after': a,
                          'bm': bm, 'am': am})
            print('%-14s before %s' % (lab, bm))
            print('%-14s after  %s' % (lab, am))
        br.close()

    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Detail Joins The Standard</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:25px;margin:0 0 6px}
.sub{color:var(--soft);margin:0 0 26px;max-width:62ch}
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
</style></head><body><div class="wrap">
<h1>Project Detail joins the standard</h1>
<p class="sub">Four priorities and four statuses on screen at once. The
class strings are read out of the template being shot, not typed into this
harness. Watch the subtask buttons on the left: <code>btn-xs</code> does
not exist in Bootstrap 4.1.3, so they render larger than the task buttons
above them.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div><table class="m"><tr><th>measured</th>'
                    '<th>before</th><th>after</th></tr>' % (
                        c['label'], c['before'], c['after']))
        for k in c['bm']:
            html.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                        % (k, c['bm'][k], c['am'].get(k)))
        html.append('</table></section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(''.join(html))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
