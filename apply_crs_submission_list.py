# -*- coding: utf-8 -*-
"""SECTION X, ROUND X6 - THE SUBMISSIONS LIST

Demetri: "Finally, all of the same need to apply to the Submissions."
Three screens; this is the first, and it is the list shape for the third
time - so the round is X1 and X3 again, plus the thing that is genuinely
this page's own.

THE FIVE LIFECYCLE BADGES, AND WHY THEY KEEP THEIR NAMES
    A submission has five states, each with a hand-rolled badge:

        draft                 #e9ecef on #495057   Bootstrap secondary
        closed                #cce5ff on #004085   Bootstrap info
        submitted_externally  #fff3cd on #856404   Bootstrap warning
        acknowledged          #d4edda on #155724   Bootstrap success
        rejected              #f8d7da on #721c24   Bootstrap danger

    Those five meanings are the house's own --alv-neutral, --alv-info,
    --alv-warn, --alv-good and --alv-bad, and base already dresses them
    as .alv-pill-neutral / -info / -attn / -good / -bad. So the mapping
    is obvious.

    WHAT IS NOT OBVIOUS IS THAT THE CLASS NAME CANNOT BE THE HOUSE ONE.
    The badge's class is BUILT FROM THE MODEL'S STATUS KEY, in two
    places and two languages:

        template   class="status-badge status-{{ sub.status }}"
        modal JS   badge.className = 'status-badge status-' + s.status_key

    So `.alv-pill-good` can never be written there without a mapping
    somewhere. The choice was between a mapping in the template AND a
    second one in the JS - two mappings in two languages, which will
    drift - or five one-line CSS rules. Five CSS rules.

    The geometry comes from base: `status-badge` becomes `alv-pill` in
    both places, so padding, radius, size and weight stop being this
    page's business. Only the five TONE pairs remain local, and each is
    the house token for the meaning it already had.

    THE BETTER FIX NEEDS PYTHON AND HAS NOT BEEN AGREED. A `pill_class`
    property on the Submission model - the shape CelebrationEvent already
    uses at pages/models.py:2726 - would let the template and the JS emit
    the house class directly and delete all five rules. That is a change
    to crs/models.py, not to a template, so it is written down rather
    than done inside a styling round.

Everything else is the list round as X1 and X3 made it: the panel
deleted, Help off `action-icon`, the house table with data-label and a
mobile action bar, the house empty state and modal header. .view-code,
.view-block, .view-empty and .view-files-table are kept - base owns no
inline code chip, no <pre> block and no in-dialog table - and retoned.

Backups: .bak_crssub. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crssub'
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
            raise SystemExit('X6: %s is not a byte copy' % bak)


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
        raise SystemExit('X6: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'CRS SUBMISSIONS</center></h2>',
     '<h2 class="page-title-h2">CRS SUBMISSIONS</h2>',
     'the title'),

    ('<a href="{% url \'crs:submission_start\' %}" '
     'class="btn btn-info action-primary">',
     '<a href="{% url \'crs:submission_start\' %}" '
     'class="btn action-primary" role="button">',
     'Start Submission'),
    ('  <button type="button" class="btn btn-success btn-sm action-icon"\r\n'
     '        data-toggle="modal" data-target="#crs_submissionsHelpModal" '
     'aria-label="Help">\r\n'
     '    <i class="fas fa-question-circle"></i>'
     '<span class="action-back-label"> Help</span>\r\n  </button>',
     '  <button type="button" class="btn action-secondary"\r\n'
     '        data-toggle="modal" data-target="#crs_submissionsHelpModal" '
     'aria-label="Help">\r\n'
     '    <i class="fas fa-question-circle"></i> Help\r\n  </button>',
     'Help'),
    ('class="btn btn-success action-back"', 'class="btn action-back"',
     'Back'),

    ('<!-- Single Panel -->\r\n'
     '<div class="crs-panel-container">\r\n'
     '  <div class="crs-panel">\r\n'
     '\r\n'
     '    {% if submissions %}\r\n'
     '    <div class="crs-table">\r\n'
     '      <table>',
     '<!-- Submissions (desktop) / card list (mobile) -->\r\n'
     '<div class="table-container">\r\n'
     '  <table class="table alv-table crs-submission-table">',
     'the panel and the table open'),

    ('          <tr>\r\n'
     '            <th>Year</th>\r\n'
     '            <th>Country</th>\r\n'
     '            <th>FI</th>\r\n'
     '            <th>Status</th>\r\n'
     '            <th>MessageRefID</th>\r\n'
     '            <th>Created</th>\r\n'
     '            <th>Actions</th>\r\n'
     '          </tr>',
     '      <tr>\r\n'
     '        <th style="text-align: left; width: 8%">Year</th>\r\n'
     '        <th style="width: 10%">Country</th>\r\n'
     '        <th style="width: 24%">FI</th>\r\n'
     '        <th style="width: 14%">Status</th>\r\n'
     '        <th style="width: 22%">MessageRefID</th>\r\n'
     '        <th style="width: 12%">Created</th>\r\n'
     '        <th class="desktop-action-cell cell-actions" '
     'style="width: 10%">Actions</th>\r\n'
     '      </tr>',
     'the head'),

    # THE BADGE KEEPS ITS STATUS NAME - it is built from the model key -
    # but its GEOMETRY comes from base.
    ('<span class="status-badge status-{{ sub.status }}">'
     '{{ sub.get_status_display }}</span>',
     '<span class="alv-pill status-{{ sub.status }}">'
     '{{ sub.get_status_display }}</span>',
     "the status badge's geometry"),
    ("badge.className = 'status-badge status-' + s.status_key;",
     "badge.className = 'alv-pill status-' + s.status_key;",
     "the modal JS that builds the same badge"),

    ('        <tbody>\r\n          {% for sub in submissions %}',
     '    <tbody>\r\n      {% for sub in submissions %}', "the body's open"),
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
            <td><strong>{{ sub.year }}</strong></td>
            <td>{{ sub.country_config.country_code }}</td>
            <td>{{ sub.reporting_fi.name }}</td>
            <td>
              <span class="alv-pill status-{{ sub.status }}">{{ sub.get_status_display }}</span>
            </td>
            <td class="ref-id" title="{{ sub.message_ref_id }}">
              <code>{{ sub.message_ref_id|truncatechars:30 }}</code>
            </td>
            <td>{{ sub.created_at|date:"d M Y H:i" }}</td>
            <td>
              <div class="row-actions">
                <button type="button" class="action-btn btn-view" title="View"
                        onclick="viewSubmission({{ sub.pk }})">
                  <i class="fas fa-eye"></i>
                </button>
                {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:submission_detail' sub.pk %}"
                   class="action-btn btn-edit" title="Edit">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="action-btn btn-delete" title="Delete Submission"
                        onclick="confirmSubmissionDelete({{ sub.pk }}, '{{ sub.message_ref_id|escapejs }}')">
                  <i class="fas fa-trash"></i>
                </button>
                {% endif %}
              </div>
            </td>
          </tr>"""

ROW_NOW = """        <tr>
          <td data-label="Year" style="text-align: left"><strong>{{ sub.year }}</strong></td>
          <td data-label="Country">{{ sub.country_config.country_code }}</td>
          <td data-label="FI">{{ sub.reporting_fi.name }}</td>
          <td data-label="Status">
            <span class="alv-pill status-{{ sub.status }}">{{ sub.get_status_display }}</span>
          </td>
          <td data-label="MessageRefID" class="ref-id" title="{{ sub.message_ref_id }}">
            <code>{{ sub.message_ref_id|truncatechars:30 }}</code>
          </td>
          <td data-label="Created">{{ sub.created_at|date:"d M Y H:i" }}</td>

          <!-- Desktop actions: one cell, three buttons -->
          <td class="desktop-action-cell cell-actions">
            <span class="row-actions">
              <button type="button" class="icon-action-btn icon-view" title="View Submission"
                      onclick="viewSubmission({{ sub.pk }})">
                <i class="fas fa-eye"></i>
              </button>
              {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:submission_detail' sub.pk %}"
                   class="icon-action-btn icon-edit" title="Open Submission">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="icon-action-btn icon-delete" title="Delete Submission"
                        onclick="confirmSubmissionDelete({{ sub.pk }}, '{{ sub.message_ref_id|escapejs }}')">
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
            <button type="button" class="mobile-action-btn" onclick="viewSubmission({{ sub.pk }})">
              <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
              <span class="mobile-action-label">View</span>
            </button>
            {% if perms.auth.can_edit_crs %}
              <a href="{% url 'crs:submission_detail' sub.pk %}" class="mobile-action-btn">
                <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                <span class="mobile-action-label">Open</span>
              </a>
              <button type="button" class="mobile-action-btn"
                      onclick="confirmSubmissionDelete({{ sub.pk }}, '{{ sub.message_ref_id|escapejs }}')">
                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                <span class="mobile-action-label">Delete</span>
              </button>
            {% else %}
              <span class="mobile-action-btn mobile-action-disabled">
                <i class="fas fa-pencil-alt mobile-action-icon"></i>
                <span class="mobile-action-label">Open</span>
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
      <i class="fas fa-file-export"></i>
      <p>No submissions yet.</p>
      <small>Click "Start Submission" to create your first draft.</small>
    </div>
    {% endif %}

  </div>
</div>"""

TAIL_NOW = """  </table>

  {% if not submissions %}
    {# An empty tbody looks exactly like a failed load. #}
    <div class="alv-empty">
      <i class="fas fa-file-export"></i>
      <div class="alv-empty-title">No submissions yet</div>
      <div class="alv-empty-hint">
        Start one to build a CRS file for a year, a country and an FI.
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
    '.crs-table tbody td:nth-child(6)::before',
    '.crs-table tbody td:last-child',
    '.crs-table tbody td:last-child::before',
    # The badge's GEOMETRY. base's .alv-pill owns it now; only the five
    # tone rules stay, because the class name is built from a model key.
    '.status-badge',
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
        '.view-code', '.view-files-table', '.view-files-table th',
        '.view-files-table td', '.view-files-table tr:last-child td',
        '.ref-id code',
        '.status-draft', '.status-closed', '.status-submitted_externally',
        '.status-acknowledged', '.status-rejected']

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
     """  /* The modal's section headings - base does not own this component. */
  .view-section-h {
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid var(--alv-line);
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    color: var(--alv-accent); letter-spacing: 0.5px;
  }""",
     '.view-section-h'),

    # THE FIVE LIFECYCLE TONES. Each already meant what a house token
    # means; each now says so. The NAMES stay because they are built from
    # the model's status key, in the template and again in the modal's JS.
    ("""  .status-draft                { background: #e9ecef; color: #495057; }
  .status-closed               { background: #cce5ff; color: #004085; }
  .status-submitted_externally { background: #fff3cd; color: #856404; }
  .status-acknowledged         { background: #d4edda; color: #155724; }
  .status-rejected             { background: #f8d7da; color: #721c24; }""",
     """  /* THE FIVE LIFECYCLE TONES.
     The badge's geometry is base's .alv-pill now; these five rules are
     nothing but the mapping from a status to a meaning, and each was
     already the Bootstrap colour for the meaning the house has a token
     for: secondary, info, warning, success, danger.

     The NAMES cannot be .alv-pill-good and friends, because the class is
     built from the model's status key - a template variable appended to
     `status-` in the markup, and 'status-' + s.status_key in the modal's
     JS. Writing a mapping in both places would be two mappings in two
     languages, which drift. Five CSS rules do not.

     (And that sentence used to quote the template tag itself. A CSS
     comment containing braces BREAKS every regex rule reader in this
     repo: the pattern that finds a rule is selector-brace-body-brace,
     so a brace inside a comment splits it in the wrong place and the
     selector comes back as the tail of the prose. Lesson 21 says strip
     comments before comparing a selector - but bare() runs AFTER the
     pattern has already mis-split. The gate below now refuses any CSS
     comment carrying a brace, so this cannot happen quietly again.)

     A `pill_class` property on the Submission model - the shape
     CelebrationEvent already uses at pages/models.py:2726 - would let
     both emit the house class directly and delete all five. That is a
     change to crs/models.py, so it is noted, not done in a styling
     round. */
  .status-draft                { background: var(--alv-neutral-soft); color: var(--alv-neutral); }
  .status-closed               { background: var(--alv-info-soft); color: var(--alv-accent-ink); }
  .status-submitted_externally { background: var(--alv-warn-soft); color: var(--alv-warn); }
  .status-acknowledged         { background: var(--alv-good-soft); color: var(--alv-good); }
  .status-rejected             { background: var(--alv-bad-soft); color: var(--alv-bad); }""",
     'the five lifecycle tones'),

    ("""    background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;
    font-family: inherit; font-size: 13px;""",
     """    background: var(--alv-surface); border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    font-family: inherit; font-size: 13px;""",
     '.view-block'),

    ("""    margin-top: 6px; padding: 12px;
    background: #f8f9fa; border-radius: 4px;
    color: #6c757d; font-style: italic; font-size: 13px;""",
     """    margin-top: 6px; padding: 12px;
    background: var(--alv-surface); border-radius: var(--alv-radius-sm);
    color: var(--alv-ink-soft); font-style: italic; font-size: 13px;""",
     '.view-empty'),

    ("""  .view-files-table th {
    background: #f8f9fa; padding: 6px 8px;
    font-size: 11px; text-transform: uppercase; color: #6c757d;
    border-bottom: 2px solid #dee2e6; text-align: left; letter-spacing: 0.4px;
  }
  .view-files-table td {
    padding: 6px 8px; font-size: 13px;
    border-bottom: 1px solid #f0f0f0; vertical-align: middle;
  }""",
     """  /* NOT .alv-table, deliberately: base's table carries a phone card
     layout, a row-action grammar and a sticky head, none of which a short
     list inside a dialog wants. Kept, moved onto tokens. */
  .view-files-table th {
    background: var(--alv-surface); padding: 6px 8px;
    font-size: 11px; text-transform: uppercase; color: var(--alv-ink-soft);
    border-bottom: 2px solid var(--alv-line); text-align: left; letter-spacing: 0.4px;
  }
  .view-files-table td {
    padding: 6px 8px; font-size: 13px;
    border-bottom: 1px solid var(--alv-line-soft); vertical-align: middle;
  }""",
     '.view-files-table'),

    # The two code chips, on the same tokens X1 chose and for the same
    # reasons: --alv-ink rather than --alv-accent-ink, because accent
    # means primary action and selection and a reference string is
    # neither. The chips are already distinguished by ground and typeface.
    ("""  .ref-id code {
    font-size: 12px;
    background: #f1f3f5;
    color: #495057;
    padding: 2px 6px;
    border-radius: 3px;
  }""",
     """  .ref-id code {
    font-size: 12px;
    background: var(--alv-line-soft);
    color: var(--alv-ink-strong);
    padding: 2px 6px;
    border-radius: 3px;
  }""",
     '.ref-id code'),

    ("""  .view-code {
    display: inline-block; padding: 2px 8px;
    background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;
    font-family: Consolas, monospace; font-size: 12px;
    color: #c7254e; word-break: break-all; max-width: 100%;
  }""",
     """  .view-code {
    display: inline-block; padding: 2px 8px;
    background: var(--alv-surface); border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    font-family: Consolas, monospace; font-size: 12px;
    color: var(--alv-ink); word-break: break-all; max-width: 100%;
  }""",
     '.view-code'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X6 - THE SUBMISSIONS LIST%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'submission_list.html')
if not os.path.isfile(path):
    raise SystemExit('X6: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'alv-table' in text:
    print('  %-30s already on the house table' % 'submission_list')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('submission_list', why))
text = swap(path, text, ROW_WAS, ROW_NOW, 'the row')
print('  %-30s the row - data-label, house icons, a mobile bar, and the '
      'count' % 'submission_list')
text = swap(path, text, TAIL_WAS, TAIL_NOW, 'the table close and the empty')
print('  %-30s the empty state, inside the container' % 'submission_list')
for was, now, why in RETONE:
    text = swap(path, text, was, now, why)
    print('  %-30s %s onto tokens' % ('submission_list', why))

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
print('  %-30s - %d rule(s) base already owns' % ('submission_list', gone))

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
        raise SystemExit('X6: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X6: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X6: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
# A CSS COMMENT WITH A BRACE IN IT BREAKS EVERY RULE READER HERE.
# The pattern is selector-{-body-}, so a brace inside a comment splits a
# rule in the wrong place and the selector comes back as prose. Lesson 21
# does not save us: bare() strips comments AFTER the split has happened.
# This round wrote exactly such a comment and the KEPT gate caught it as
# a missing selector, which is a confusing way to be told. Say it plainly.
for cmt in re.findall(r'/\*.*?\*/', css, re.S):
    if '{' in cmt or '}' in cmt:
        raise SystemExit(
            'X6: a CSS comment contains a brace, which breaks the rule '
            'reader - the selector after it comes back as prose. Rewrite '
            'it without braces: %s' % ' '.join(cmt.split())[:90])

hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X6: %d hex(es) left: %s' % (len(hexes), hexes))

for name in ('crs-panel', 'crs-table', 'crs-empty', 'action-icon',
             'btn-success', 'btn-info', 'status-active', 'status-inactive',
             'in-count', 'in-count-empty', 'action-btn', 'btn-view',
             'btn-edit', 'btn-delete', 'bg-info'):
    if has_class(name):
        raise SystemExit('X6: the class %r survives in the markup' % name)

for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X6: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X6: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))

if mk.count('class="table alv-table crs-submission-table"') != 1:
    raise SystemExit('X6: the table does not wear .alv-table exactly once')
if mk.count('<div class="table-container">') != 1:
    raise SystemExit('X6: there is not exactly one .table-container')
labels = re.findall(r'data-label="([^"]+)"', mk)
if labels != ['Year', 'Country', 'FI', 'Status', 'MessageRefID', 'Created']:
    raise SystemExit('X6: the data-labels are %r, not the six columns'
                     % labels)
if mk.count('class="desktop-action-cell cell-actions"') != 2:
    raise SystemExit('X6: the actions column needs a header cell and a body '
                     'cell, and has %d'
                     % mk.count('class="desktop-action-cell cell-actions"'))
if mk.count('class="mobile-action-bar"') != 1:
    raise SystemExit('X6: there is no mobile action bar')
for icon in ('icon-view', 'icon-edit', 'icon-delete'):
    if 'icon-action-btn %s' % icon not in mk:
        raise SystemExit('X6: the row has no %s' % icon)

# THE FIVE LIFECYCLE TONES, EACH MAPPED TO THE MEANING IT ALREADY HAD.
TONES = {
    '.status-draft': 'var(--alv-neutral-soft)',
    '.status-closed': 'var(--alv-info-soft)',
    '.status-submitted_externally': 'var(--alv-warn-soft)',
    '.status-acknowledged': 'var(--alv-good-soft)',
    '.status-rejected': 'var(--alv-bad-soft)',
}
for sel, want in TONES.items():
    body = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]
    if not body:
        raise SystemExit('X6: %s was removed - the five lifecycle tones '
                         'stay, because the class name is built from the '
                         "model's status key" % sel)
    if want not in body[0]:
        raise SystemExit('X6: %s should take %s and takes %r'
                         % (sel, want, ' '.join(body[0].split())))
if len(set(TONES.values())) != 5:
    raise SystemExit('X6: two statuses share a tone - a colour must not '
                     'mean two things at once')
if mk.count('class="alv-pill status-') != 1:
    raise SystemExit('X6: the badge does not take .alv-pill for geometry')
js = re.search(r"badge\.className\s*=\s*'([^']+)'", text)
if not js or 'alv-pill' not in js.group(1):
    raise SystemExit("X6: the modal's JS still builds the old badge class - "
                     'it is written in two places and both must move')

if 'alv-modal-head' not in mk:
    raise SystemExit('X6: the view modal did not get the house header')
if 'btn action-secondary' not in mk:
    raise SystemExit('X6: Help is not on the house secondary')
if mk.count('alv-empty') < 3:
    raise SystemExit('X6: the empty state is not the house component')
if len(text) >= len(before):
    raise SystemExit('X6: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
