# -*- coding: utf-8 -*-
"""P2 BEFORE / AFTER - the task list, desktop and phone.

Not a test. A LOOK. The suite is test_task_table.py.

THE ROWS ARE PLANTED, because the point of the round is the pills, the
Actions column and the phone card, and one row cannot show four statuses.
But the CLASS STRINGS ARE NOT INVENTED: pill_for() reads the {% if %}
chain out of the template being shot and evaluates it, so if the round's
branches change, these shots change with them. A hand-typed class list
would have gone stale the moment the round did, and would have shown a
card that the page does not actually produce.

Six rows: the project, two tasks and three subtasks, chosen to cover all
four statuses, all four priorities and the no-priority case that the
project row has.
"""
import base64
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
PAGE = os.path.join(T, 'projects', 'project_task_list.html')
SUFFIX = '.bak_tasktable'
EXE = '/opt/pw-browsers/chromium'
OUT = os.path.join(ROOT, 'p2_before_after.html')
SHOTS = '/tmp/p2shots'

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')

# (type, name, priority, status, indent, overdue)
ROWS = [
    ('project',  'Villa Aphrodite - Roof Renewal',   None,       'In Progress', 0, False),
    ('task',     'Strip the existing tiles',         'Critical', 'Completed',   1, False),
    ('subtask',  'Hire the skip',                    'High',     'Completed',   2, False),
    ('subtask',  'Scaffold the north elevation',     'Medium',   'On Hold',     2, True),
    ('task',     'Lay the new membrane',             'Low',      'Pending',     1, False),
    ('subtask',  'Order the membrane from Nicosia',  'Medium',   'Pending',     2, False),
]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in STYLE.finditer(t)]


def pill_for(src, cell, value):
    """The class string the template itself would emit for `value`.

    Reads the <span class="..."> of the named cell out of `src` and walks
    its {% if %}/{% elif %}/{% else %} chain. BEFORE the round there is no
    chain - the class is a single generated name - and this returns that,
    which is why the same function serves both sides of the shot."""
    m = re.search(r'<td class="[^"]*\b' + cell + r'\b[^"]*"[^>]*>(.*?)</td>',
                  src, re.S)
    if not m:
        return ''
    span = re.search(r'<span class="([^"]*)"', m.group(1))
    if not span:
        return ''
    cls = span.group(1)
    if '{%' not in cls:
        # before: priority-{{ item.priority|lower }} / status-{{ ...|slugify }}
        return re.sub(r'\{\{[^}]*\}\}', (value or '').lower().replace(' ', '-'),
                      cls)
    # after: a chain of literal comparisons against one field
    fixed = re.sub(r'\{%.*?%\}', '', cls).strip()
    for cond, tone in re.findall(
            r'\{%\s*(?:el)?if\s+(.*?)\s*%\}([a-z-]+)', cls):
        ok = False
        for lit in re.findall(r"==\s*'([^']*)'", cond):
            if lit == value:
                ok = True
        if ok:
            return (fixed + ' ' + tone).strip()
    els = re.search(r'\{%\s*else\s*%\}([a-z-]+)', cls)
    return (fixed + ' ' + (els.group(1) if els else '')).strip()


def type_pill(src, kind):
    m = re.search(r'<td class="[^"]*\bcell-type\b[^"]*"[^>]*>(.*?)</td>',
                  src, re.S)
    span = re.search(r'<span class="([^"]*)"', m.group(1)) if m else None
    if not span:
        return ''
    return re.sub(r'\{\{[^}]*\}\}', kind, span.group(1))


def table_of(src):
    """The page's table, with ROWS planted into it."""
    after = 'alv-table' in src
    ICON = {'project': 'fas fa-folder-open project-icon',
            'task': 'fas fa-tasks task-icon',
            'subtask': 'fas fa-chevron-right subtask-icon'}
    LABEL = {'project': 'Project', 'task': 'Task', 'subtask': 'Subtask'}
    head = ['Task Name', 'Type', 'Priority', 'Status', 'Start Date',
            'Expected End']
    th = ''.join('<th>%s</th>' % h for h in head)
    if after:
        th += ('<th class="desktop-action-cell cell-actions">Actions</th>')
    out = []
    for kind, name, pri, sta, ind, over in ROWS:
        tds = []
        tds.append(
            '<td class="task-name-cell" data-label="Name">'
            '<div class="task-indent-%d"><i class="%s"></i>'
            '<strong class="task-name">%s</strong>'
            '<div class="task-description">Agreed with the contractor on '
            'the site visit.</div></div></td>'
            % (ind, ICON[kind], name))
        tds.append('<td class="cell-type" data-label="Type">'
                   '<span class="%s">%s</span></td>'
                   % (type_pill(src, kind), LABEL[kind]))
        if pri:
            tds.append('<td class="cell-priority" data-label="Priority">'
                       '<span class="%s">%s</span></td>'
                       % (pill_for(src, 'cell-priority', pri), pri))
        else:
            tds.append('<td class="cell-priority" data-label="Priority">'
                       '<span class="text-muted">-</span></td>')
        tds.append('<td class="cell-status" data-label="Status">'
                   '<span class="%s">%s</span></td>'
                   % (pill_for(src, 'cell-status', sta), sta))
        tds.append('<td class="date-cell cell-start-date" data-label="Start">'
                   '<span class="date-value">14/07/2026</span></td>')
        tds.append(
            '<td class="date-cell cell-end-date" data-label="End">'
            '<span class="date-value%s">30/09/2026%s</span></td>'
            % (' overdue' if over else '',
               '<i class="fas fa-exclamation-triangle overdue-icon"></i>'
               if over else ''))
        if after:
            live = kind != 'project'
            if live:
                acts = ('<a href="#" class="icon-action-btn icon-edit" '
                        'title="Edit"><i class="fas fa-pencil-alt"></i></a>'
                        '<a href="#" class="icon-action-btn icon-delete" '
                        'title="Delete"><i class="fas fa-trash"></i></a>')
                bar = ('<a href="#" class="mobile-action-btn">'
                       '<i class="fas fa-pencil-alt mobile-action-icon '
                       'icon-color-edit"></i>'
                       '<span class="mobile-action-label">Edit</span></a>'
                       '<a href="#" class="mobile-action-btn">'
                       '<i class="fas fa-trash mobile-action-icon '
                       'icon-color-delete"></i>'
                       '<span class="mobile-action-label">Delete</span></a>')
            else:
                acts = ('<span class="icon-action-btn icon-disabled">'
                        '<i class="fas fa-pencil-alt"></i></span>'
                        '<span class="icon-action-btn icon-disabled">'
                        '<i class="fas fa-trash"></i></span>')
                bar = ('<span class="mobile-action-btn is-disabled">'
                       '<i class="fas fa-pencil-alt mobile-action-icon"></i>'
                       '<span class="mobile-action-label">Edit</span></span>'
                       '<span class="mobile-action-btn is-disabled">'
                       '<i class="fas fa-trash mobile-action-icon"></i>'
                       '<span class="mobile-action-label">Delete</span></span>')
            tds.append('<td class="desktop-action-cell cell-actions">'
                       '<span class="row-actions">%s</span></td>' % acts)
            tds.append('<td class="mobile-action-bar cols-2">%s</td>' % bar)
        out.append('<tr class="task-row task-type-%s">%s</tr>'
                   % (kind, ''.join(tds)))
    cls = ('table alv-table task-list-table' if after
           else 'table table-striped task-list-table')
    return ('<div class="task-list-container"><table class="%s">'
            '<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cls, th, ''.join(out)))


def stats_of(src):
    if 'alv-stats' in src:
        return ('<div class="alv-stats task-summary">'
                '<div class="alv-stat"><div class="alv-stat-value">5</div>'
                '<div class="alv-stat-label">Total Tasks</div></div>'
                '<div class="alv-stat alv-stat-good">'
                '<div class="alv-stat-value">2</div>'
                '<div class="alv-stat-label">Completed</div></div>'
                '<div class="alv-stat alv-stat-attn">'
                '<div class="alv-stat-value">3</div>'
                '<div class="alv-stat-label">Pending</div></div></div>')
    return ('<div class="task-summary">'
            '<div class="summary-stat"><div class="stat-number">5</div>'
            '<div class="stat-label">Total Tasks</div></div>'
            '<div class="summary-stat"><div class="stat-number">2</div>'
            '<div class="stat-label">Completed</div></div>'
            '<div class="summary-stat"><div class="stat-number">3</div>'
            '<div class="stat-label">Pending</div></div></div>')


boot = read(BOOT)
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(src):
    page = '\n'.join(styles_of(src))
    head = ('<div class="task-list-header"><div class="row">'
            '<div class="col-md-8"><h3>Villa Aphrodite - Roof Renewal</h3>'
            '<p class="project-description">Full strip and re-lay, north '
            'and south elevations.</p>'
            '<p class="project-property"><i class="fas fa-home"></i> '
            '<strong>Property:</strong> Villa Aphrodite</p></div>'
            '<div class="col-md-4">%s</div></div></div>' % stats_of(src))
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar">'
            '<div class="main-content with-sidebar">%s%s</div></body></html>'
            % (boot, bcss, page, FREEZE, head, table_of(src)))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
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
            png = pg.screenshot(full_page=True)
            m = {}
            for sel, key in (('.task-list-table tbody tr:nth-child(2) '
                              '.cell-status span', 'status'),
                             ('.task-list-table tbody tr:nth-child(2) '
                              '.cell-type span', 'type'),
                             ('.task-list-table tbody tr:nth-child(2) '
                              '.row-actions', 'actions'),
                             ('.task-list-table tbody tr:nth-child(2) '
                              '.mobile-action-bar', 'bar')):
                try:
                    bb = pg.query_selector(sel).bounding_box()
                    m[key] = (round(bb['width']), round(bb['height']))
                except Exception:
                    m[key] = None
            # the card label, which is the drift this round removes
            try:
                st = pg.evaluate(
                    "() => { const td = document.querySelector("
                    "'.task-list-table tbody tr:nth-child(2) .cell-status');"
                    " const s = getComputedStyle(td, '::before');"
                    " return [s.fontSize, s.textTransform, s.color]; }")
                m['label'] = st
            except Exception:
                m['label'] = None
            ctx.close()
            return base64.b64encode(png).decode('ascii'), m

        for w, h, lab in ((1280, 900, 'desktop 1280'), (386, 760, 'phone 386')):
            b, bm = shoot(before, w, h, 'b%d' % w)
            a, am = shoot(after, w, h, 'a%d' % w)
            cells.append({'label': lab, 'before': b, 'after': a,
                          'bm': bm, 'am': am})
            print('%-14s before %s' % (lab, bm))
            print('%-14s after  %s' % (lab, am))
        br.close()
    write_sheet(cells)
    print('wrote', OUT)


def write_sheet(cells):
    html = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Task List Joins The Standard</title>
<style>
:root{--ink:#1d2327;--soft:#5b6670;--rule:#dfe4e8;--ground:#f7f8f9;
--card:#fff;--teal:#0e7c8b}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--soft);margin:0 0 28px;max-width:60ch}
section{background:var(--card);border:1px solid var(--rule);border-radius:10px;
padding:18px;margin-bottom:22px}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.06em;
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
code{background:#eef1f3;padding:1px 5px;border-radius:3px;font-size:12.5px}
</style></head><body><div class="wrap">
<h1>The task list joins the table standard</h1>
<p class="sub">Rows are planted so that four statuses and four priorities
are all on screen at once. The class strings are read out of the template
being shot, not typed here, so these pictures cannot drift from the
round.</p>"""]
    for c in cells:
        html.append('<section><h2>%s</h2><div class="pair">'
                    '<figure><figcaption>before</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '<figure><figcaption>after</figcaption>'
                    '<img src="data:image/png;base64,%s" alt=""></figure>'
                    '</div>' % (c['label'], c['before'], c['after']))
        html.append('<table class="m"><tr><th>measured</th><th>before</th>'
                    '<th>after</th></tr>')
        for k in ('type', 'status', 'actions', 'bar', 'label'):
            html.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td>'
                        '</tr>' % (k, c['bm'].get(k), c['am'].get(k)))
        html.append('</table></section>')
    html.append('</div></body></html>')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(''.join(html))


if __name__ == '__main__':
    main()
