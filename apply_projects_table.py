# -*- coding: utf-8 -*-
"""SECTION P, ROUND P1 - THE PROJECTS TABLE JOINS THE STANDARD

Demetri, on Projects: "This table does not comply."

It does not, and the screenshot says exactly how: Edit and Delete sit in
two columns with two headers, Delete is a filled red button the height of
the row and Edit is a small pale one beside it. Every other list in the
system has ONE Actions column holding icon buttons of equal size.

WHAT IS THERE NOW

    <table class="table table-bordered table-striped text-center ...">
    <th>Edit</th><th>Delete</th>                     two headers
    <td class="cell-action" data-label="View">       three cells
    <td class="cell-action" data-label="Edit">
    <td class="cell-action" data-label="Delete">

and FIFTEEN rules on the page to hold it together, including a literal
#dc3545 for the red, a hand-built 33.33% three-up grid for the phone, and
.btn-label-text { display: none } - a label written into the markup and
then hidden by CSS on every screen there is.

The header row also declares widths of 30+20+13+12+10+10+8+7, which is
110%. Nobody notices because the browser normalises it, but it means the
widths were never a decision, only an accumulation.

WHAT IT BECOMES - the same shape as Tenants and Lease Agreements:

    <table class="table alv-table projects-table">
    <th class="desktop-action-cell cell-actions">Actions</th>
    <td class="desktop-action-cell cell-actions">
      <span class="row-actions"> ... three .icon-action-btn ...
    <td class="mobile-action-bar cols-3">

base already owns every one of those names - the table standard, the row
actions, the icon colours, the phone bar and its grid. So the fifteen
rules go, the widths are redistributed to sum to 100, and the page keeps
only what is genuinely its own: the project-name link and the progress
bar.

DISABLED TWINS, NOT MISSING BUTTONS. Without can_edit_projects the Edit
and Delete slots are drawn as .icon-disabled rather than left out, so the
cluster is the same width on every row - which is the rule the other two
converted tables already follow.

Backups: .bak_projtable. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_projtable'
CRLF = {}

PAGE = os.path.join('projects', 'projects.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('P1: %s is not a byte copy' % bak)


def once(text, needle, what):
    n = text.count(needle)
    if n != 1:
        raise SystemExit('P1: %s is there %d time(s), not 1' % (what, n))
    return n


# ==========================================================================
TABLE_WAS = '<table class="table table-bordered table-striped text-center projects-table">'
TABLE_NOW = '<table class="table alv-table projects-table">'

# THE WIDTHS SUMMED TO 110. Seven columns now, and they sum to 100 -
# checked below rather than asserted here.
HEAD_WAS = """          <th style="text-align: left; width: 30%">Project Name</th>
          <th style="width: 20%">Property</th>
          <th style="width: 13%">Status</th>
          <th style="width: 12%">Progress</th>
          <th style="width: 10%">Start Date</th>
          <th style="width: 10%">End Date</th>
          <th style="width: 8%">Edit</th>
          <th style="width: 7%">Delete</th>"""
HEAD_NOW = """          <th style="text-align: left; width: 30%">Project Name</th>
          <th style="width: 18%">Property</th>
          <th style="width: 12%">Status</th>
          <th style="width: 12%">Progress</th>
          <th style="width: 10%">Start Date</th>
          <th style="width: 10%">End Date</th>
          <th class="desktop-action-cell cell-actions" style="width: 8%">Actions</th>"""

CELL_START = '<td data-label="View" class="cell-action cell-action--view-mobile">'
CELL_END = '{% endif %}\n            </td>'

CELLS_NOW = """<!-- ONE ACTIONS COLUMN - 30 Sep 2026. Three cells and two
                 headers became one of each. View, Edit and Delete are
                 base's .icon-action-btn now, the same size on every row,
                 and the slots a permission removes are drawn as
                 .icon-disabled twins so the cluster never shifts. The
                 phone gets base's .mobile-action-bar instead of the
                 33.33% grid this page built for itself.
                                              [test_projects_table.py] -->
            <td class="desktop-action-cell cell-actions">
              <span class="row-actions">
                <a href="{% url 'projects_detail' project.project_id %}"
                   class="icon-action-btn icon-view" title="View Project">
                  <i class="fas fa-eye"></i>
                </a>
                {% if perms.auth.can_edit_projects %}
                  <a href="{% url 'projects_edit' project.project_id %}"
                     class="icon-action-btn icon-edit" title="Edit Project">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                  <a href="{% url 'projects_delete' project.project_id %}"
                     class="icon-action-btn icon-delete" title="Delete Project">
                    <i class="fas fa-trash"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No edit permission">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                  <span class="icon-action-btn icon-disabled" title="No edit permission">
                    <i class="fas fa-trash"></i>
                  </span>
                {% endif %}
              </span>
            </td>

            <td class="mobile-action-bar cols-3">
              <a href="{% url 'projects_detail' project.project_id %}" class="mobile-action-btn">
                <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View</span>
              </a>
              {% if perms.auth.can_edit_projects %}
                <a href="{% url 'projects_edit' project.project_id %}" class="mobile-action-btn">
                  <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                  <span class="mobile-action-label">Edit</span>
                </a>
                <a href="{% url 'projects_delete' project.project_id %}" class="mobile-action-btn">
                  <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                  <span class="mobile-action-label">Delete</span>
                </a>
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-pencil-alt mobile-action-icon"></i>
                  <span class="mobile-action-label">Edit</span>
                </span>
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-trash mobile-action-icon"></i>
                  <span class="mobile-action-label">Delete</span>
                </span>
              {% endif %}
            </td>"""

# The fifteen the page no longer needs, matched as whole rules.
DEAD = re.compile(r'(?m)^[ \t]*[^{}\n]*\.(?:action-btn|cell-action|'
                  r'btn-label-text|delete-btn)[a-zA-Z-]*[^{}\n]*\{[^}]*\}\n?')
NOTE = """      /* THE ROW ACTIONS ARE base's - 30 Sep 2026. Fifteen rules
         lived here: .action-btn and its hover, .delete-btn in a literal
         #dc3545, .btn-label-text { display: none } for a label the
         markup wrote and the CSS then hid on every screen, and a
         33.33% three-up grid this page built for the phone. base owns
         all of it - .icon-action-btn, .row-actions, the icon colours,
         .mobile-action-bar and its columns - so the fifteen are gone
         and nothing about the page renders differently for it, except
         that Delete is now the size of Edit.
                                          [test_projects_table.py] */
"""

# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P1 - THE PROJECTS TABLE JOINS THE STANDARD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.join(PAGE)
if not os.path.isfile(p):
    raise SystemExit('P1: %s is not on disk' % PAGE)
t, raw = read(p)
print('  %s' % PAGE)

if 'cell-actions' in t:
    print('     already wears the standard')
else:
    # ---- the table ---------------------------------------------------
    once(t, eol(p, TABLE_WAS), 'the table tag')
    t = t.replace(eol(p, TABLE_WAS), eol(p, TABLE_NOW), 1)
    print('     the table joins .alv-table; bordered, striped and centred go')

    # ---- the header --------------------------------------------------
    once(t, eol(p, HEAD_WAS), 'the header row')
    t = t.replace(eol(p, HEAD_WAS), eol(p, HEAD_NOW), 1)
    print('     two headers become one, and the widths sum to 100 again')

    # ---- the three action cells --------------------------------------
    a = t.find(eol(p, CELL_START))
    if a < 0 or t.count(eol(p, CELL_START)) != 1:
        raise SystemExit('P1: the View cell is there %d time(s), not 1'
                         % t.count(eol(p, CELL_START)))
    # THE END IS THE LAST </td> BEFORE THE ROW CLOSES. Looking for the
    # first `{% endif %}</td>` after the View cell finds the EDIT cell's
    # - all three end the same way - and the span then held two cells
    # while claiming to hold three.
    dele = t.find(eol(p, 'data-label="Delete"'), a)
    if dele < 0:
        raise SystemExit('P1: no Delete cell after the View cell')
    close = t.find(eol(p, '</tr>'), dele)
    if close < 0:
        raise SystemExit('P1: the row does not close after the Delete cell')
    end = t.rfind(eol(p, '</td>'), dele, close)
    if end < 0:
        raise SystemExit('P1: the Delete cell does not close')
    end += len(eol(p, '</td>'))
    span = t[a:end]
    # THE SPAN IS THE THREE CELLS AND NOTHING ELSE.
    if span.count('<td ') != 3 or span.count('</td>') != 3:
        raise SystemExit('P1: the span holds %d <td> and %d </td>, not 3 and '
                         '3' % (span.count('<td '), span.count('</td>')))
    for must in ('data-label="View"', 'data-label="Edit"',
                 'data-label="Delete"'):
        if must not in span:
            raise SystemExit('P1: the span does not hold %s' % must)
    if '<tr' in span or '</tr>' in span:
        raise SystemExit('P1: the span reaches past the row')
    t = t[:a] + eol(p, CELLS_NOW) + t[end:]
    print('     three cells become one, plus base\'s phone bar')

    # ---- the fifteen rules -------------------------------------------
    css_a = t.find('<style')
    css_b = t.find('</style>', css_a)
    if css_a < 0 or css_b < 0:
        raise SystemExit('P1: no style block')
    css = t[css_a:css_b]
    hits = DEAD.findall(css)
    if len(hits) != 15:
        raise SystemExit('P1: %d rule(s) to remove, not 15' % len(hits))
    css2 = DEAD.sub('', css)
    # The replacement note goes where the first of them was.
    first = DEAD.search(css).start()
    css2 = DEAD.sub('', css[:first]) + eol(p, NOTE) + DEAD.sub('', css[first:])
    t = t[:css_a] + css2 + t[css_b:]
    print('     fifteen local rules go; base already owned every one')

    # ---- GATES --------------------------------------------------------
    mk = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
    css3 = re.sub(r'/\*.*?\*/', ' ', t[css_a:t.find('</style>', css_a)],
                  flags=re.S)
    # ONE ACTIONS COLUMN, ONE PHONE BAR.
    for name, n in (('cell-actions', 2), ('desktop-action-cell', 2),
                    ('mobile-action-bar cols-3', 1), ('row-actions', 1),
                    ('>Actions<', 1), ('>Edit</th>', 0), ('>Delete</th>', 0),
                    ('cell-action--view-mobile', 0), ('btn-label-text', 0),
                    ('action-btn--view', 0), ('delete-btn', 0)):
        got = mk.count(name)
        if got != n:
            raise SystemExit('P1: %s appears %d time(s) in the markup, not %d'
                             % (name, got, n))
    # THE WIDTHS SUM TO 100 NOW - they summed to 110 before.
    w = [int(x) for x in re.findall(r'<th[^>]*width:\s*(\d+)%', mk)]
    if sum(w) != 100 or len(w) != 7:
        raise SystemExit('P1: %d column(s) summing to %d%%, not 7 to 100%%'
                         % (len(w), sum(w)))
    # THE ICONS ARE FOUR DIFFERENT GLYPHS ACROSS THE TWO HALVES, and the
    # three disabled twins are drawn rather than dropped.
    # THE HOUSE GLYPH FOR EDIT IS fa-pencil-alt, on all 22 pages that
    # draw one - test_row_personal.py holds that line, and it caught
    # this round shipping fa-edit.
    if 'fa-edit' in mk:
        raise SystemExit('P1: fa-edit is not the house glyph - .icon-edit '
                         'draws fa-pencil-alt everywhere else')
    if mk.count('icon-disabled') != 2 or mk.count('mobile-action-disabled') != 2:
        raise SystemExit('P1: the disabled twins were dropped')
    # EVERY PERMISSION GATE SURVIVED.
    if mk.count('perms.auth.can_edit_projects') < 2:
        raise SystemExit('P1: a can_edit_projects gate was lost')
    # AND THE PAGE WRITES NO RULE base OWNS.
    own = re.findall(r'(?m)^[ \t]*[^{}\n]*\.(?:icon-action-btn|icon-view|'
                     r'icon-edit|icon-delete|icon-disabled|row-actions|'
                     r'cell-actions|mobile-action-|desktop-action-cell|'
                     r'table-container)[a-zA-Z-]*[^{}\n]*\{', css3)
    if own:
        raise SystemExit('P1: the page writes %d rule(s) base owns: %s'
                         % (len(own), [x.strip() for x in own[:3]]))
    # NO LITERAL BOOTSTRAP RED SURVIVES.
    if '#dc3545' in css3:
        raise SystemExit('P1: the Bootstrap red is still in the stylesheet')
    # DJANGO STILL BALANCES.
    for tag, close in (('if', 'endif'), ('for', 'endfor'),
                       ('block', 'endblock')):
        x = len(re.findall(r'\{%\s*' + tag + r'\b', t))
        y = len(re.findall(r'\{%\s*' + close + r'\b', t))
        if x != y:
            raise SystemExit('P1: %d {%% %s %%} against %d {%% %s %%}'
                             % (x, tag, y, close))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- what the page keeps ------------------------------------------------
t2 = read(p)[0]
css4 = re.sub(r'/\*.*?\*/', ' ', t2[t2.find('<style'):t2.find('</style>')],
              flags=re.S)
print('  what the page keeps, because it is genuinely its own')
for name in ('project-name-link', 'progress-container', 'progress-bar'):
    n = len(re.findall(r'\.' + name + r'\b[^{}]*\{', css4))
    print('     .%-22s %d rule(s)' % (name, n))
    if not n:
        raise SystemExit('P1: .%s was removed and should not have been'
                         % name)

print('-' * 74)
print('  one Actions column, three icon buttons the same size, and the')
print('  phone gets the bar every other list already has.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
