# -*- coding: utf-8 -*-
"""SECTION X, ROUND X3 - REPORTING FINANCIAL INSTITUTIONS, THE LIST

Demetri, having listed the Country Configurations defects: "All of the
above need to apply for the Reporting Financial Institutions."

They do, and almost literally: measured against country_list.html as X1
found it, fi_list.html declares the SAME rules with EIGHT additions. So
this round is X1 again, plus the four things that are genuinely this
page's own.

    .in-count / .in-count-empty     the IN count badge in the table
    .view-block                     a <pre> for an address and a contact
    .view-empty                     an inline note in the modal
    .view-ins-table (+ th, td,      a nested table of identification
     tr:last-child td)              numbers inside the view modal

THE COUNT BADGE IS THE ONE REAL DECISION
    .in-count is a solid --crs-dark pill with white text, and
    .in-count-empty repaints it grey at 60% opacity when the count is
    zero. Both go, and the cell takes base's own component:

        .alv-pill .alv-pill-info      when there are INs
        .alv-pill .alv-pill-neutral   when there are none

    Not -good and not -bad, because a count of identification numbers is
    not a health reading. Standard 3.1 lists --alv-info as
    "informational, neutral emphasis", which is exactly what a count in a
    table is, and -neutral already means "nothing here" everywhere else
    in the system. Using -good for a non-zero count would be the error
    3.1 warns about: a colour meaning two things at once.

    It is a visible change - a solid teal badge becomes a soft pill -
    and it is the same change the Status column took in X1, so the two
    pills in one row now read as one family rather than two inventions.

THE NESTED TABLE IN THE MODAL IS NOT .alv-table, DELIBERATELY
    .view-ins-table is three columns inside a modal body. base's
    .alv-table carries a phone card layout, a row-action grammar and a
    sticky head - all of which are for a page's main table, and none of
    which a three-row list inside a dialog wants. It is kept under its
    own name and moved onto tokens. The same reasoning kept .view-row
    and .view-code in X1.

Everything else is X1's round: the panel deleted rather than retoned,
Help off `action-icon`, the house table with data-label and a mobile
action bar, the house empty state, the house modal header.

Backups: .bak_crsfi. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsfi'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('X3: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70 - fi_list.html is CRLF."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    """Lesson 21."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('X3: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'CRS REPORTING FINANCIAL INSTITUTIONS</center></h2>',
     '<h2 class="page-title-h2">CRS REPORTING FINANCIAL INSTITUTIONS</h2>',
     'the title'),

    ('<a href="{% url \'crs:fi_add\' %}" '
     'class="btn btn-info action-primary">',
     '<a href="{% url \'crs:fi_add\' %}" class="btn action-primary" '
     'role="button">',
     'Add Reporting FI'),
    ('  <button type="button" class="btn btn-success btn-sm action-icon"\r\n'
     '        data-toggle="modal" data-target="#crs_reporting_fisHelpModal" '
     'aria-label="Help">\r\n'
     '    <i class="fas fa-question-circle"></i>'
     '<span class="action-back-label"> Help</span>\r\n  </button>',
     '  <button type="button" class="btn action-secondary"\r\n'
     '        data-toggle="modal" data-target="#crs_reporting_fisHelpModal" '
     'aria-label="Help">\r\n'
     '    <i class="fas fa-question-circle"></i> Help\r\n  </button>',
     'Help'),
    ('class="btn btn-success action-back"', 'class="btn action-back"',
     'Back'),

    ('<!-- Single Panel -->\r\n'
     '<div class="crs-panel-container">\r\n'
     '  <div class="crs-panel">\r\n'
     '\r\n'
     '    {% if fis %}\r\n'
     '    <div class="crs-table">\r\n'
     '      <table>',
     '<!-- Reporting FIs (desktop) / card list (mobile) -->\r\n'
     '<div class="table-container">\r\n'
     '  <table class="table alv-table crs-fi-table">',
     'the panel and the table open'),

    ('          <tr>\r\n'
     '            <th>Name</th>\r\n'
     '            <th>Residence</th>\r\n'
     '            <th>INs</th>\r\n'
     '            <th>Status</th>\r\n'
     '            <th>Last Updated</th>\r\n'
     '            <th>Actions</th>\r\n'
     '          </tr>',
     '      <tr>\r\n'
     '        <th style="text-align: left; width: 32%">Name</th>\r\n'
     '        <th style="width: 14%">Residence</th>\r\n'
     '        <th style="width: 10%">INs</th>\r\n'
     '        <th style="width: 14%">Status</th>\r\n'
     '        <th style="width: 18%">Last Updated</th>\r\n'
     '        <th class="desktop-action-cell cell-actions" '
     'style="width: 12%">Actions</th>\r\n'
     '      </tr>',
     'the head'),

    ('        <tbody>\r\n          {% for fi in fis %}',
     '    <tbody>\r\n      {% for fi in fis %}', "the body's open"),
    ('          {% endfor %}\r\n        </tbody>',
     '      {% endfor %}\r\n    </tbody>', "the body's close"),

    ('<div class="modal-header bg-info text-white">',
     '<div class="modal-header alv-modal-head">', "the modal's header"),
    ('<button type="button" class="btn btn-secondary" '
     'data-dismiss="modal">Close</button>',
     '<button type="button" class="btn action-secondary" '
     'data-dismiss="modal">Close</button>', "the modal's Close"),
]

ROW_WAS = """          <tr>
            <td><strong>{{ fi.name }}</strong></td>
            <td>{{ fi.res_country_code }}</td>
            <td>
              <span class="in-count{% if not fi.in_count %} in-count-empty{% endif %}">
                {{ fi.in_count }}
              </span>
            </td>
            <td>
              {% if fi.is_active %}
                <span class="status-active"><i class="fas fa-circle"></i> Active</span>
              {% else %}
                <span class="status-inactive"><i class="fas fa-circle"></i> Inactive</span>
              {% endif %}
            </td>
            <td>{{ fi.updated_at|date:"d M Y H:i" }}</td>
            <td>
              <div class="row-actions">
                <button type="button" class="action-btn btn-view" title="View"
                        onclick="viewFI({{ fi.pk }})">
                  <i class="fas fa-eye"></i>
                </button>
                {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:fi_edit' fi.pk %}"
                   class="action-btn btn-edit" title="Edit">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="action-btn btn-delete" title="Delete"
                        onclick="confirmFIDelete({{ fi.pk }}, '{{ fi.name|escapejs }}')">
                  <i class="fas fa-trash"></i>
                </button>
                {% endif %}
              </div>
            </td>
          </tr>"""

ROW_NOW = """        <tr>
          <td data-label="Name" style="text-align: left"><strong>{{ fi.name }}</strong></td>
          <td data-label="Residence">{{ fi.res_country_code }}</td>
          <td data-label="INs">
            {# A COUNT, not a health reading - so -info and -neutral, never
               -good. Standard 3.1: --alv-info is informational, neutral
               emphasis, and a colour must not mean two things at once. #}
            {% if fi.in_count %}
              <span class="alv-pill alv-pill-info">{{ fi.in_count }}</span>
            {% else %}
              <span class="alv-pill alv-pill-neutral">0</span>
            {% endif %}
          </td>
          <td data-label="Status">
            {% if fi.is_active %}
              <span class="alv-pill alv-pill-good">Active</span>
            {% else %}
              <span class="alv-pill alv-pill-neutral">Inactive</span>
            {% endif %}
          </td>
          <td data-label="Last Updated">{{ fi.updated_at|date:"d M Y H:i" }}</td>

          <!-- Desktop actions: one cell, three buttons -->
          <td class="desktop-action-cell cell-actions">
            <span class="row-actions">
              <button type="button" class="icon-action-btn icon-view" title="View Reporting FI"
                      onclick="viewFI({{ fi.pk }})">
                <i class="fas fa-eye"></i>
              </button>
              {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:fi_edit' fi.pk %}"
                   class="icon-action-btn icon-edit" title="Edit Reporting FI">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="icon-action-btn icon-delete" title="Delete Reporting FI"
                        onclick="confirmFIDelete({{ fi.pk }}, '{{ fi.name|escapejs }}')">
                  <i class="fas fa-trash"></i>
                </button>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No edit permission">
                  <i class="fas fa-pencil-alt"></i>
                </span>
                <span class="icon-action-btn icon-disabled" title="No delete permission">
                  <i class="fas fa-trash"></i>
                </span>
              {% endif %}
            </span>
          </td>

          <!-- Mobile-only action bar (hidden on desktop) -->
          <td class="mobile-action-bar">
            <button type="button" class="mobile-action-btn" onclick="viewFI({{ fi.pk }})">
              <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
              <span class="mobile-action-label">View</span>
            </button>
            {% if perms.auth.can_edit_crs %}
              <a href="{% url 'crs:fi_edit' fi.pk %}" class="mobile-action-btn">
                <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                <span class="mobile-action-label">Edit</span>
              </a>
              <button type="button" class="mobile-action-btn"
                      onclick="confirmFIDelete({{ fi.pk }}, '{{ fi.name|escapejs }}')">
                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                <span class="mobile-action-label">Delete</span>
              </button>
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
          </td>
        </tr>"""

TAIL_WAS = """      </table>
    </div>
    {% else %}
    <div class="crs-empty">
      <i class="fas fa-university"></i>
      <p>No reporting FIs yet.</p>
      <small>Click "Add Reporting FI" to create one.</small>
    </div>
    {% endif %}

  </div>
</div>"""

TAIL_NOW = """  </table>

  {% if not fis %}
    {# An empty tbody looks exactly like a failed load. #}
    <div class="alv-empty">
      <i class="fas fa-university"></i>
      <div class="alv-empty-title">No reporting FIs yet</div>
      <div class="alv-empty-hint">
        Add the institution that will be named as the sender on submissions.
      </div>
    </div>
  {% endif %}
</div>"""

DEAD = [
    ':root',
    '.page-title-h2',
    '.page-action-buttons',
    '.page-action-buttons .action-primary',
    '.page-action-buttons .action-back',
    '.action-back-label',
    '.crs-panel-container',
    '.crs-panel',
    '.crs-table',
    '.crs-table table',
    '.crs-table thead th',
    '.crs-table tbody td',
    '.crs-table tbody tr:last-child td',
    '.crs-table tbody tr:hover',
    '.crs-table table, .crs-table thead, .crs-table tbody, .crs-table tr, '
    '.crs-table td',
    '.crs-table thead',
    '.crs-table tbody tr',
    '.crs-table tbody td::before',
    '.crs-table tbody td:nth-child(1)::before',
    '.crs-table tbody td:nth-child(2)::before',
    '.crs-table tbody td:nth-child(3)::before',
    '.crs-table tbody td:nth-child(4)::before',
    '.crs-table tbody td:nth-child(5)::before',
    '.crs-table tbody td:last-child',
    '.crs-table tbody td:last-child::before',
    '.status-active',
    '.status-active i',
    '.status-inactive',
    '.status-inactive i',
    '.in-count',
    '.in-count-empty',
    '.row-actions',
    '.action-btn',
    '.action-btn:hover',
    '.btn-view',
    '.btn-edit',
    '.btn-delete',
    '.crs-empty',
    '.crs-empty i',
    '.crs-empty p',
    '.crs-empty small',
]

KEPT = ['.view-row', '.view-row label', '.view-section-h',
        '.view-section-h:first-child', '.view-block', '.view-empty',
        '.view-ins-table', '.view-ins-table th', '.view-ins-table td',
        '.view-ins-table tr:last-child td']

RETONE = [
    ('  .view-row label { font-weight: 600; color: #495057; '
     'margin-right: 8px; margin-bottom: 0; }',
     '  .view-row label { font-weight: 600; color: var(--alv-ink-strong); '
     'margin-right: 8px; margin-bottom: 0; }',
     '.view-row label'),

    ("""  .view-section-h {
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid #e9ecef;
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    color: var(--crs-dark); letter-spacing: 0.5px;
  }""",
     """  /* The modal's section headings. base does not own this component, so
     the rule stays - but on the house accent rather than on a --crs-dark
     that no longer exists. */
  .view-section-h {
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid var(--alv-line);
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    color: var(--alv-accent); letter-spacing: 0.5px;
  }""",
     '.view-section-h'),

    ("""    margin: 4px 0 0 0; padding: 10px;
    background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;""",
     """    margin: 4px 0 0 0; padding: 10px;
    background: var(--alv-surface); border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);""",
     '.view-block'),

    ("""    margin-top: 6px; padding: 12px;
    background: #f8f9fa; border-radius: 4px;
    color: #6c757d; font-style: italic; font-size: 13px;""",
     """    margin-top: 6px; padding: 12px;
    background: var(--alv-surface); border-radius: var(--alv-radius-sm);
    color: var(--alv-ink-soft); font-style: italic; font-size: 13px;""",
     '.view-empty'),

    ("""  .view-ins-table th {
    background: #f8f9fa; padding: 6px 8px;
    font-size: 11px; text-transform: uppercase; color: #6c757d;
    border-bottom: 2px solid #dee2e6; text-align: left; letter-spacing: 0.4px;
  }
  .view-ins-table td {
    padding: 6px 8px; font-size: 13px;
    border-bottom: 1px solid #f0f0f0;
  }""",
     """  /* NOT .alv-table, deliberately. base's table component carries a phone
     card layout, a row-action grammar and a sticky head - all of which are
     for a page's MAIN table, and none of which a three-row list inside a
     dialog wants. Kept under its own name, moved onto tokens. */
  .view-ins-table th {
    background: var(--alv-surface); padding: 6px 8px;
    font-size: 11px; text-transform: uppercase; color: var(--alv-ink-soft);
    border-bottom: 2px solid var(--alv-line); text-align: left; letter-spacing: 0.4px;
  }
  .view-ins-table td {
    padding: 6px 8px; font-size: 13px;
    border-bottom: 1px solid var(--alv-line-soft);
  }""",
     '.view-ins-table'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X3 - REPORTING FINANCIAL INSTITUTIONS, THE LIST%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'fi_list.html')
if not os.path.isfile(path):
    raise SystemExit('X3: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'alv-table' in text:
    print('  %-30s already on the house table' % 'fi_list')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('fi_list', why))
text = swap(path, text, ROW_WAS, ROW_NOW, 'the row')
print('  %-30s the row - data-label, house icons, a mobile bar, and the '
      'count' % 'fi_list')
text = swap(path, text, TAIL_WAS, TAIL_NOW, 'the table close and the empty')
print('  %-30s the empty state, inside the container' % 'fi_list')
for was, now, why in RETONE:
    text = swap(path, text, was, now, why)
    print('  %-30s %s onto tokens' % ('fi_list', why))

gone = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body, last, out = text[s:e], 0, []
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in DEAD:
            continue
        st = m.start() + (len(m.group(1)) - len(m.group(1).lstrip()))
        hd = body.rfind('\n', 0, st) + 1
        if body[hd:st].strip():
            hd = st
        en = m.end()
        while en < len(body) and body[en] in ' \t\r':
            en += 1
        if en < len(body) and body[en] == '\n':
            en += 1
        if hd < last:
            continue
        out.append(body[last:hd])
        last, gone = en, gone + 1
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s - %d rule(s) base already owns' % ('fi_list', gone))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
mk = re.sub(r'\{#.*?#\}', '', mk, flags=re.S)


def has_class(name):
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


for d in DEAD:
    if d in names:
        raise SystemExit('X3: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X3: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X3: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X3: %d hex(es) left: %s' % (len(hexes), hexes))

for name in ('crs-panel', 'crs-table', 'crs-empty', 'action-icon',
             'btn-success', 'btn-info', 'status-active', 'status-inactive',
             'in-count', 'in-count-empty', 'action-btn', 'btn-view',
             'btn-edit', 'btn-delete', 'bg-info'):
    if has_class(name):
        raise SystemExit('X3: the class %r survives in the markup' % name)

for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X3: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X3: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))

if mk.count('class="table alv-table crs-fi-table"') != 1:
    raise SystemExit('X3: the table does not wear .alv-table exactly once')
if mk.count('<div class="table-container">') != 1:
    raise SystemExit('X3: there is not exactly one .table-container')
labels = re.findall(r'data-label="([^"]+)"', mk)
if labels != ['Name', 'Residence', 'INs', 'Status', 'Last Updated']:
    raise SystemExit('X3: the data-labels are %r, not the five columns'
                     % labels)
if mk.count('class="desktop-action-cell cell-actions"') != 2:
    raise SystemExit('X3: the actions column needs a header cell and a body '
                     'cell, and has %d'
                     % mk.count('class="desktop-action-cell cell-actions"'))
if mk.count('class="mobile-action-bar"') != 1:
    raise SystemExit('X3: there is no mobile action bar')
for icon in ('icon-view', 'icon-edit', 'icon-delete'):
    if 'icon-action-btn %s' % icon not in mk:
        raise SystemExit('X3: the row has no %s' % icon)

# THE COUNT BADGE. -info and -neutral, never -good.
if 'alv-pill alv-pill-info' not in mk:
    raise SystemExit('X3: the IN count is not on .alv-pill-info')
ins_cell = mk[mk.index('data-label="INs"'):mk.index('data-label="Status"')]
if 'alv-pill-good' in ins_cell or 'alv-pill-bad' in ins_cell:
    raise SystemExit('X3: the IN count uses a HEALTH tone. It is a count, '
                     'not a health reading - standard 3.1, a colour must '
                     'not mean two things at once')
if 'alv-pill-neutral' not in ins_cell:
    raise SystemExit('X3: a zero count has no neutral pill')
if 'alv-pill alv-pill-good' not in mk:
    raise SystemExit('X3: the Status column is not on .alv-pill')
if 'alv-modal-head' not in mk:
    raise SystemExit('X3: the view modal did not get the house header')
if 'btn action-secondary' not in mk:
    raise SystemExit('X3: Help is not on the house secondary')
if mk.count('alv-empty') < 3:
    raise SystemExit('X3: the empty state is not the house component')
if len(text) >= len(before):
    raise SystemExit('X3: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
