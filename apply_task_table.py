# -*- coding: utf-8 -*-
"""SECTION P, ROUND P2 - THE TASK LIST JOINS THE TABLE STANDARD

Demetri: "This table in Projects does not comply." That was projects.html,
and P1 fixed it. Surveying the module for what was left turned up its
sibling, projects/project_task_list.html, which does not comply either -
and in a more interesting way.

IT HAS REBUILT THE STANDARD UNDER ITS OWN NAME. 23 rules, 77 declarations
keyed on .task-list-table, six of them a straight rename of a rule base
already owns, and one of them DRIFTED while nobody was looking:

    base   td::before   12.5px, sentence case, var(--alv-ink-soft)
    page   td::before   11px, UPPERCASE, letter-spacing .4px, #6c757d

So on a phone this page's card labels have been a different size, a
different case and a different grey from every other list in the system.
That is the visible non-compliance, and it is why a private copy of a
standard is worse than no standard.

AGREED WITH DEMETRI, 1 Oct 2026, seven questions:

 1. ADD THE ACTIONS COLUMN. The screen had none - six columns and no way
    to act on a row. project_tasks_edit and project_tasks_delete both
    exist and Project Detail already links them.
 2. DISABLED TWINS ON A PROJECT ROW. The table mixes three row types; a
    project is not edited from here. The twin keeps the cluster the same
    width on every row, which is the rule the other three converted
    tables follow. The discriminator is `item.task_obj` - the view puts
    task_obj on task and subtask rows and project_obj on the project row,
    so asking for task_obj asks whether there is a task to edit.
 3. PRIORITY, four values into three tones. Critical alone on -bad, High
    and Medium share -attn, Low -neutral.
 4. STATUS. Completed -good, On Hold -attn, Pending -neutral. In Progress
    takes -info: my own wording to Demetri said both "On Hold -> neutral
    is obvious" and "my lean: On Hold = attn", which cannot both hold, and
    he agreed to the lean. -info is the fourth tone base already has, so
    each of his four statuses still reads as its own colour instead of two
    of them sharing -attn.
 5. THE TYPE BADGE LOSES ITS COLOUR. Project/Task/Subtask is a CATEGORY,
    and base's pills are semantic - good, bad, attn - so there is no
    honest mapping. The row already carries an icon for its type and the
    name is indented by level, so the colour was the third telling of the
    same fact. The pill goes -neutral.
 6. THE STATS BLOCK IS A RENAME. .task-summary/.summary-stat/.stat-number
    /.stat-label is a private copy of base's .alv-stats/.alv-stat/
    .alv-stat-value/.alv-stat-label. Three stats, so --alv-stats-cols: 3,
    the same way fsr sets 5 and the two finance pages set 3.
 7. THE PHONE CARD BECOMES BASE'S, WHOLE. Demetri: "Bring everything in
    line with our standards on the phone cards too."

WHAT THAT LAST ONE COSTS, STATED PLAINLY. The page grouped Type/Priority/
Status into a 3-across row and Start/End into a 2-across row inside the
card. base's card is ONE FIELD PER ROW, label left and value right. fsr
has six columns and does not group, and Demetri said the Issues module
looks good - so the grouping goes. The card gets taller and every other
list in the system reads the same way.

AND THE DEFECT THIS ROUND WOULD OTHERWISE HAVE CREATED. The page exports
the table to Excel by reading every th and td:

    const cells = row.querySelectorAll('th, td');

Adding an Actions column adds TWO cells to every row - the desktop one
and the phone bar - so the spreadsheet would have gained a blank column
and a column reading "Edit Delete" on every line, and the !cols widths
would have described six columns of an eight-column sheet. The export now
skips both action cells. Nothing else about the export changes.

NOT IN THIS ROUND, and said out loud rather than quietly swept in:

  * .task-type-project/-task/-subtask put a 4px left border and a 3%
    background tint on the row in #3498db / #2ecc71 / #f39c12. That is
    the same category colour as the type badge, a fourth time. Removing
    it was not among the seven questions, so it stays. On a phone base's
    card rule outranks it (0,1,2 against 0,1,0), so it does not fight
    the card.
  * The icon colours, and 46 literal hexes on the page, belong to the
    retone work.
  * THE LEGEND NEEDS NOTHING. Question 7 asked about dropping the colour
    half of it. There is no colour half - the legend is four icons and
    their names. Nothing to do, so nothing is done to it.

Backups: .bak_tasktable. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tasktable'
CRLF = {}

PAGE = os.path.join('projects', 'project_task_list.html')
SENTINEL = 'test_task_table.py'


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
            raise SystemExit('P2: %s is not a byte copy' % bak)


def once(text, needle, what):
    """`needle` must appear exactly once. Anything else is a mis-aimed
    anchor, and the round refuses rather than patching the wrong place."""
    n = text.count(needle)
    if n != 1:
        raise SystemExit('P2: %s appears %d times, not once' % (what, n))
    return text


def swap(text, old, new, what):
    """Replace a multi-line anchor, in THIS FILE'S line endings.

    This page is CRLF. Checking it with open(encoding='utf-8') says it is
    not, because text mode translates \\r\\n to \\n on the way in - and the
    patcher reads bytes, so every anchor written here as \\n missed. The
    conversion belongs in one place, which is here."""
    o, n = eol(PATH, old), eol(PATH, new)
    once(text, o, what)
    return text.replace(o, n)


# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P2 - THE TASK LIST JOINS THE TABLE STANDARD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = PATH = alv_tree.join(PAGE)
if not os.path.isfile(p):
    raise SystemExit('P2: %s is not where alv_tree says' % PAGE)
t, raw = read(p)
if SENTINEL in t:
    print('  already done')
    raise SystemExit(0)

# ---- base must own everything this round hands over to it ---------------
b = read(alv_tree.path_of('base.html'))[0]
bcss = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
    re.findall(r'<style\b[^>]*>(.*?)</style>', b, re.S)), flags=re.S)
NEEDED = {
    '.alv-table': r'(?<![-\w])\.alv-table\s*\{',
    '.alv-table thead th': r'(?<![-\w])\.alv-table thead th\s*\{',
    '.alv-table td::before': r'(?<![-\w])\.alv-table td::before\s*\{',
    '.alv-table tbody td:first-child':
        r'(?<![-\w])\.alv-table tbody td:first-child\s*\{',
    '.alv-stats': r'(?<![-\w])\.alv-stats\s*\{',
    '.alv-stat': r'(?<![-\w])\.alv-stat\s*\{',
    '.alv-stat-value': r'(?<![-\w])\.alv-stat-value\s*\{',
    '.alv-stat-label': r'(?<![-\w])\.alv-stat-label\s*\{',
    '.alv-pill': r'(?<![-\w])\.alv-pill\s*\{',
    '.alv-pill-good': r'(?<![-\w])\.alv-pill-good\s*\{',
    '.alv-pill-attn': r'(?<![-\w])\.alv-pill-attn\s*\{',
    '.alv-pill-info': r'(?<![-\w])\.alv-pill-info\s*\{',
    '.alv-pill-bad': r'(?<![-\w])\.alv-pill-bad\s*\{',
    '.alv-pill-neutral': r'(?<![-\w])\.alv-pill-neutral\s*\{',
    '.row-actions': r'(?<![-\w])\.row-actions\s*\{',
    '.icon-action-btn': r'(?<![-\w])\.icon-action-btn\s*\{',
    '.icon-disabled': r'(?<![-\w])\.icon-disabled\b',
    '.mobile-action-bar.cols-2': r'(?<![-\w])\.mobile-action-bar\.cols-2\s*\{',
    '--alv-stats-cols': r'--alv-stats-cols',
}
missing = [k for k, v in NEEDED.items() if not re.search(v, bcss)]
if missing:
    raise SystemExit('P2: base does not own %s, so this page cannot hand '
                     'them over' % missing)
print('  base owns all %d names this round hands over to it' % len(NEEDED))

# ==========================================================================
# MARKUP
# ==========================================================================
GREEK = "{% if language == 'greek' %}"

# ---- 1. the table joins the standard, and stops striping ----------------
# Of 43 house tables in the tree exactly one stripes. The standard is not
# striped, and base retones .alv-table.table-striped rather than blessing
# it, so the class simply goes.
once(t, '<table class="table table-striped task-list-table">', 'the table tag')
t = t.replace('<table class="table table-striped task-list-table">',
              '<table class="table alv-table task-list-table">')

# ---- 2. the Actions header ---------------------------------------------
HEAD_ANCHOR = ("          <th>%sΑναμ. Λήξη{%% else %%}Expected End{%% endif %%}"
               "</th>\n        </tr>" % GREEK)
HEAD_NEW = (HEAD_ANCHOR.replace('</tr>', '')
            + '          <th class="desktop-action-cell cell-actions">'
              '%sΕνέργειες{%% else %%}Actions{%% endif %%}</th>\n'
              '        </tr>' % GREEK)
t = swap(t, HEAD_ANCHOR, HEAD_NEW, 'the last header cell')

# ---- 3. the type badge loses its colour --------------------------------
once(t, '<span class="type-badge type-{{ item.type|lower }}">',
     'the type badge')
t = t.replace('<span class="type-badge type-{{ item.type|lower }}">',
              '<span class="alv-pill alv-pill-neutral">')

# ---- 4. priority: four values, three tones -----------------------------
once(t, '<span class="priority-badge priority-{{ item.priority|lower }}">',
     'the priority badge')
PRI = ('<span class="alv-pill '
       "{% if item.priority == 'Critical' %}alv-pill-bad"
       "{% elif item.priority == 'High' or item.priority == 'Medium' %}"
       'alv-pill-attn'
       '{% else %}alv-pill-neutral{% endif %}">')
t = t.replace('<span class="priority-badge priority-{{ item.priority|lower }}">',
              PRI)

# ---- 5. status: four values, four tones --------------------------------
# The template's own Greek block compares item.status against the ENGLISH
# words, so item.status is English here and the four Greek class names in
# the stylesheet were never reachable. The {% else %} keeps a value this
# round has not been told about on -neutral rather than unstyled.
once(t, '<span class="status-badge status-{{ item.status|slugify }}">',
     'the status badge')
STA = ('<span class="alv-pill '
       "{% if item.status == 'Completed' %}alv-pill-good"
       "{% elif item.status == 'In Progress' %}alv-pill-info"
       "{% elif item.status == 'On Hold' %}alv-pill-attn"
       '{% else %}alv-pill-neutral{% endif %}">')
t = t.replace('<span class="status-badge status-{{ item.status|slugify }}">',
              STA)

# ---- 6. the row gets its actions ---------------------------------------
ROW_ANCHOR = ('              {% endif %}\n'
              '            </td>\n'
              '          </tr>\n'
              '        {% empty %}')

ACTIONS = """              {% endif %}
            </td>
            <td class="desktop-action-cell cell-actions">
              <span class="row-actions">
                {% if item.task_obj and perms.auth.can_edit_projects %}
                  <a href="{% url 'project_tasks_edit' project.project_id item.task_obj.task_id %}"
                     class="icon-action-btn icon-edit"
                     title="{GREEK}Επεξεργασία{% else %}Edit{% endif %}">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                  <a href="{% url 'project_tasks_delete' project.project_id item.task_obj.task_id %}"
                     class="icon-action-btn icon-delete"
                     title="{GREEK}Διαγραφή{% else %}Delete{% endif %}">
                    <i class="fas fa-trash"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled"
                        title="{GREEK}Δεν είναι διαθέσιμο εδώ{% else %}Not available here{% endif %}">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                  <span class="icon-action-btn icon-disabled"
                        title="{GREEK}Δεν είναι διαθέσιμο εδώ{% else %}Not available here{% endif %}">
                    <i class="fas fa-trash"></i>
                  </span>
                {% endif %}
              </span>
            </td>

            <td class="mobile-action-bar cols-2">
              {% if item.task_obj and perms.auth.can_edit_projects %}
                <a href="{% url 'project_tasks_edit' project.project_id item.task_obj.task_id %}" class="mobile-action-btn">
                  <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                  <span class="mobile-action-label">{GREEK}Επεξεργασία{% else %}Edit{% endif %}</span>
                </a>
                <a href="{% url 'project_tasks_delete' project.project_id item.task_obj.task_id %}" class="mobile-action-btn">
                  <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                  <span class="mobile-action-label">{GREEK}Διαγραφή{% else %}Delete{% endif %}</span>
                </a>
              {% else %}
                <span class="mobile-action-btn is-disabled">
                  <i class="fas fa-pencil-alt mobile-action-icon"></i>
                  <span class="mobile-action-label">{GREEK}Επεξεργασία{% else %}Edit{% endif %}</span>
                </span>
                <span class="mobile-action-btn is-disabled">
                  <i class="fas fa-trash mobile-action-icon"></i>
                  <span class="mobile-action-label">{GREEK}Διαγραφή{% else %}Delete{% endif %}</span>
                </span>
              {% endif %}
            </td>
          </tr>
        {% empty %}""".replace('{GREEK}', GREEK)
t = swap(t, ROW_ANCHOR, ACTIONS, 'the end of the last row cell')

# ---- 7. the empty state spans the new column ---------------------------
once(t, '<td colspan="6" class="text-center text-muted py-4">',
     'the empty-state cell')
t = t.replace('<td colspan="6" class="text-center text-muted py-4">',
              '<td colspan="8" class="text-center text-muted py-4">')

# ---- 8. the stats block is a rename ------------------------------------
STATS_OLD = """        <div class="task-summary">
          <div class="summary-stat">
            <div class="stat-number">{{ total_tasks }}</div>
            <div class="stat-label">%sΣυνολικές Εργασίες{%% else %%}Total Tasks{%% endif %%}</div>
          </div>
          <div class="summary-stat">
            <div class="stat-number">{{ completed_tasks }}</div>
            <div class="stat-label">%sΟλοκληρωμένες{%% else %%}Completed{%% endif %%}</div>
          </div>
          <div class="summary-stat">
            <div class="stat-number">{{ pending_tasks }}</div>
            <div class="stat-label">%sΕκκρεμείς{%% else %%}Pending{%% endif %%}</div>
          </div>
        </div>""" % (GREEK, GREEK, GREEK)

STATS_NEW = """        <div class="alv-stats task-summary">
          <div class="alv-stat">
            <div class="alv-stat-value">{{ total_tasks }}</div>
            <div class="alv-stat-label">%sΣυνολικές Εργασίες{%% else %%}Total Tasks{%% endif %%}</div>
          </div>
          <div class="alv-stat alv-stat-good">
            <div class="alv-stat-value">{{ completed_tasks }}</div>
            <div class="alv-stat-label">%sΟλοκληρωμένες{%% else %%}Completed{%% endif %%}</div>
          </div>
          <div class="alv-stat alv-stat-attn">
            <div class="alv-stat-value">{{ pending_tasks }}</div>
            <div class="alv-stat-label">%sΕκκρεμείς{%% else %%}Pending{%% endif %%}</div>
          </div>
        </div>""" % (GREEK, GREEK, GREEK)
t = swap(t, STATS_OLD, STATS_NEW, 'the stats block')

# ---- 9. the Excel export skips the action cells ------------------------
EXP_OLD = "            const cells = row.querySelectorAll('th, td');"

EXP_NEW = """            /* The two action cells are controls, not data. Without
               this the sheet gained a blank column and a column reading
               "Edit Delete" on every line, and !cols below described six
               columns of an eight-column sheet.   [test_task_table.py] */
            const cells = row.querySelectorAll(
                'th:not(.cell-actions):not(.mobile-action-bar), '
                + 'td:not(.cell-actions):not(.mobile-action-bar)');"""
t = swap(t, EXP_OLD, EXP_NEW, 'the export cell query')

print('  markup: table class, Actions header, 2 row cells, 3 badges,')
print('          stats rename, empty-state colspan, export query')

# ==========================================================================
# CSS - hand the standard back to base
# ==========================================================================
a = t.find('<style')
z = t.find('</style>', a)
if a < 0 or z < 0:
    raise SystemExit('P2: no style block')
css = t[a:z]

# Each entry is matched exactly once and removed. Every one of them is
# either a rule base already owns, or a rule that would FIGHT base now
# that the table is .alv-table - the page's block renders after base's, so
# at equal specificity the page wins, which is the whole problem.
CUTS = [
    # desktop head: #f8f9fa / #2c3e50 / 13px / no uppercase, against
    # base's var(--alv-surface) / var(--alv-ink-strong) / 13.5px / upper
    """.task-list-table thead th {
    background: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
    font-weight: 600;
    color: #2c3e50;
    padding: 14px 10px;
    vertical-align: middle;
    font-size: 13px;
}

""",
    # phone: base's .alv-table thead is display:none already
    """    .task-list-table thead {
        position: absolute;
        top: -9999px;
        left: -9999px;
    }
""",
    # phone: display:block on td fights base's display:flex label/value
    """    .task-list-table,
    .task-list-table thead,
    .task-list-table tbody,
    .task-list-table tr,
    .task-list-table td {
        display: block;
        width: 100%;
    }
""",
    # phone: the card, in literal white/#dee2e6 against base's tokens
    """    .task-list-table tr {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        margin-bottom: 14px;
        padding: 14px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
""",
    """    .task-list-table td {
        text-align: left !important;
        border: none;
        padding: 6px 0;
        font-size: 14px;
        position: relative;
        min-width: 0 !important;
        width: 100% !important;
    }
""",
    # phone: THE DRIFTED LABEL - 11px uppercase #6c757d
    """    .task-list-table td[data-label]::before {
        content: attr(data-label);
        display: inline-block;
        font-weight: 600;
        color: #6c757d;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 2px;
        width: 100%;
    }
""",
    # phone: base's td:first-child IS the card title treatment
    """    /* Task name cell becomes the card title — no label prefix */
    .task-list-table td.task-name-cell {
        padding-bottom: 10px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--alv-line-soft);
    }
    .task-list-table td.task-name-cell::before {
        display: none;
    }
""",
    # phone: the groupings. base's card is one field per row.
    """    /* Group Type / Priority / Status on a single row (3 columns) */
    .task-list-table td.cell-type,
    .task-list-table td.cell-priority,
    .task-list-table td.cell-status {
        display: inline-block !important;
        width: calc(33.33% - 4px) !important;
        vertical-align: top;
        padding: 6px 0 6px 0;
    }
    .task-list-table td.cell-priority { padding-left: 4px; padding-right: 4px; }
    .task-list-table td.cell-status { padding-left: 4px; }

    /* Group Start / End on a single row (2 columns) */
    .task-list-table td.cell-start-date,
    .task-list-table td.cell-end-date {
        display: inline-block !important;
        width: calc(50% - 4px) !important;
        vertical-align: top;
        padding: 6px 0 6px 0;
    }
    .task-list-table td.cell-end-date { padding-left: 4px; }
""",
    # phone: base covers a cell with no data-label
    """    .task-list-table tr td[colspan]::before { display: none; }
""",
    # THE PRIVATE BADGE STYLESHEET. The markup is .alv-pill now, so
    # every one of these is either dead or fighting base - and the
    # shared rule WAS fighting it, since the page's block renders after
    # base's and .type-badge/.priority-badge/.status-badge sat in the
    # same class lists at the same specificity. 14 literal hexes leave
    # with it. The four Greek status names were never reachable: the
    # template's own Greek block compares item.status against the
    # ENGLISH words, so item.status is English wherever it is read.
    """/* Badges */
.type-badge, .priority-badge, .status-badge {
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    display: inline-block;
}

.type-badge { text-transform: uppercase; }
.type-project { background: rgba(52, 152, 219, 0.15); color: #2980b9; }
.type-task { background: rgba(46, 204, 113, 0.15); color: #27ae60; }
.type-subtask { background: rgba(243, 156, 18, 0.15); color: #e67e22; }

.priority-critical { background: #dc3545; color: white; }
.priority-high { background: var(--alv-warn); color: var(--alv-on-accent); }
.priority-medium { background: #ffc107; color: #212529; }
.priority-low { background: #6c757d; color: white; }

.status-completed, .status-\u03bf\u03bb\u03bf\u03ba\u03bb\u03b7\u03c1\u03c9\u03bc\u03ad\u03bd\u03b7 { background: #d4edda; color: #155724; }
.status-in-progress, .status-\u03c3\u03b5-\u03b5\u03be\u03ad\u03bb\u03b9\u03be\u03b7 { background: #fff3cd; color: #856404; }
.status-on-hold, .status-\u03c3\u03b5-\u03b1\u03bd\u03b1\u03bc\u03bf\u03bd\u03ae { background: #e2e3e5; color: #383d41; }
.status-pending, .status-\u03b5\u03ba\u03ba\u03c1\u03b5\u03bc\u03ae\u03c2 { background: #f8d7da; color: #721c24; }

""",
    # the stats block, desktop - markup now uses base's names
    """.task-summary {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    flex-wrap: wrap;
}

.summary-stat {
    text-align: center;
    background: #f8f9fa;
    padding: 14px 8px;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    min-width: 100px;
    flex: 1;
}

.stat-number {
    font-size: 22px;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 11px;
    color: #6c757d;
    font-weight: 500;
    word-wrap: break-word;
    line-height: 1.2;
}

""",
    # the stats block, phone
    """    .task-summary {
        flex-direction: row;
        gap: 8px;
        justify-content: stretch;
        margin-top: 16px;
    }
    .summary-stat {
        min-width: 0;
        padding: 10px 6px;
    }
    .stat-number { font-size: 18px; }
    .stat-label { font-size: 10px; }
""",
]

for i, cut in enumerate(CUTS, 1):
    cut = eol(p, cut)
    n = css.count(cut)
    if n != 1:
        raise SystemExit('P2: CSS cut %d matches %d times, not once:\n%s'
                         % (i, n, cut[:120]))
    css = css.replace(cut, '')
print('  CSS: %d block(s) handed back to base' % len(CUTS))

# ---- the two rules that are REWRITTEN, not removed ---------------------
# th/td keeps its wrapping - base does not set word-wrap, and a fixed
# layout with long task names needs it - and loses the padding and the
# vertical-align, which base's .alv-table tbody td owns.
TD_OLD = """.task-list-table th,
.task-list-table td {
    white-space: normal;
    word-wrap: break-word;
    overflow-wrap: break-word;
    vertical-align: top;
    padding: 12px 8px;
}"""
TD_NEW = """.task-list-table th,
.task-list-table td {
    /* The wrapping is this page's own - base does not set it, and a
       fixed-layout table with long task names and descriptions needs
       it. The padding and the vertical-align were here too; both are
       base's .alv-table tbody td now.          [test_task_table.py] */
    white-space: normal;
    word-wrap: break-word;
    overflow-wrap: break-word;
}"""
css = swap(css, TD_OLD, TD_NEW, 'the th/td rule')

# widths: seven columns now, and they still sum to 100.
W_OLD = """.task-list-table th:nth-child(1),
.task-list-table td:nth-child(1) { width: 40%; min-width: 250px; }
.task-list-table th:nth-child(2),
.task-list-table td:nth-child(2) { width: 12%; min-width: 80px; }
.task-list-table th:nth-child(3),
.task-list-table td:nth-child(3) { width: 12%; min-width: 80px; }
.task-list-table th:nth-child(4),
.task-list-table td:nth-child(4) { width: 12%; min-width: 90px; }
.task-list-table th:nth-child(5),
.task-list-table td:nth-child(5) { width: 12%; min-width: 90px; }
.task-list-table th:nth-child(6),
.task-list-table td:nth-child(6) { width: 12%; min-width: 90px; }"""
# The two date columns carry 'dd/mm/yyyy' in Courier New 13px - about
# 78px of glyph - plus base's 12px cell padding each side, and the End
# column also holds the overdue triangle. The first cut of this round
# gave them 10% and 90px and the render came back reading '14/07/202'
# over '6'. They get 12 and 13 now, and 110px of floor.
WIDTHS = ((1, 32, 250), (2, 10, 78), (3, 10, 78), (4, 11, 88),
          (5, 12, 110), (6, 13, 118), (7, 12, 110))
if sum(x[1] for x in WIDTHS) != 100:
    raise SystemExit('P2: the widths sum to %d, not 100'
                     % sum(x[1] for x in WIDTHS))
W_NEW = ('/* Seven columns, summing to 100. projects.html had eight that\n'
         '   summed to 110 until P1; nobody noticed because the browser\n'
         '   normalises it, which is exactly why it is asserted here.\n'
         '                                       [test_task_table.py] */\n'
         + '\n'.join(
    '.task-list-table th:nth-child(%d),\n'
    '.task-list-table td:nth-child(%d) { width: %d%%; min-width: %dpx; }'
    % (i, i, w, m) for i, w, m in WIDTHS))
css = swap(css, W_OLD, W_NEW, 'the width block')

# the stats block needs its column count, the way fsr sets 5.
STATS_CSS = """/* Three stats, so three columns - fsr sets 5 and the two finance pages
   set 3 the same way. base takes it to 2 on a phone by itself.
                                            [test_task_table.py] */
.task-summary { --alv-stats-cols: 3; }

"""
MARK = eol(p, """/* ============================================================
   TABLE — DESKTOP""")
if css.count(MARK) != 1:
    raise SystemExit('P2: the TABLE - DESKTOP marker does not match once')
css = css.replace(MARK, eol(p, STATS_CSS) + MARK)

print('  CSS: th/td rewritten, 7 widths summing to 100, stats-cols set')

t = t[:a] + css + t[z:]

# ==========================================================================
# GATES
# ==========================================================================
cssn = re.sub(r'/\*.*?\*/', ' ', t[t.find('<style'):t.find('</style>')],
              flags=re.S)
body = re.sub(r'<(script|style)\b.*?</\1>', '',
              re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)

# nothing base owns is left behind under the page's own name
for gone in ('thead th', 'td[data-label]::before', 'td.task-name-cell',
             'td.cell-type', 'td.cell-start-date'):
    if '.task-list-table ' + gone in cssn:
        raise SystemExit('P2: .task-list-table %s is still here' % gone)
# The three renamed stat classes must have no rule left anywhere on the
# page. .task-summary itself SURVIVES - it is the hook that carries
# --alv-stats-cols - so it is checked separately, for exactly one rule.
for gone in ('.summary-stat', '.stat-number', '.stat-label'):
    if re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', cssn):
        raise SystemExit('P2: %s is still styled' % gone)
summary = re.findall(r'\.task-summary(?![\w-])[^{}]*\{([^}]*)\}', cssn)
if len(summary) != 1 or '--alv-stats-cols' not in summary[0]:
    raise SystemExit('P2: .task-summary has %d rule(s); it should have one, '
                     'carrying --alv-stats-cols' % len(summary))
for dead in ('.type-badge', '.priority-badge', '.status-badge',
             '.type-project', '.priority-critical', '.status-completed'):
    if re.search(re.escape(dead) + r'(?![\w-])[^{}]*\{', cssn):
        raise SystemExit('P2: %s is still styled' % dead)
for dead in ('type-badge', 'priority-badge', 'status-badge'):
    if dead in body:
        raise SystemExit('P2: %s is still in the markup with nothing to '
                         'style it' % dead)
if 'table-striped' in body:
    raise SystemExit('P2: the table still stripes')
if 'alv-table' not in body:
    raise SystemExit('P2: the table did not join the standard')

# The pill tones, counted. -attn is used TWICE on purpose: priority High
# and Medium share it (four priorities, three tones, question 3), and
# status On Hold has it (question 4). Everything else appears once.
for tone, n in (('alv-pill-bad', 1), ('alv-pill-attn', 2),
                ('alv-pill-good', 1), ('alv-pill-info', 1)):
    if body.count(tone) != n:
        raise SystemExit('P2: %s appears %d times, not %d'
                         % (tone, body.count(tone), n))
if body.count('alv-pill-neutral') != 3:
    raise SystemExit('P2: alv-pill-neutral appears %d times, not 3 '
                     '(type, priority fallback, status fallback)'
                     % body.count('alv-pill-neutral'))

# the action cells, and the glyph
if body.count('desktop-action-cell') != 2:
    raise SystemExit('P2: desktop-action-cell appears %d times, not 2 '
                     '(the header and the row)' % body.count('desktop-action-cell'))
if body.count('mobile-action-bar') != 1:
    raise SystemExit('P2: mobile-action-bar appears %d times, not 1'
                     % body.count('mobile-action-bar'))
if 'fa-edit' in body:
    raise SystemExit('P2: fa-edit - the house glyph is fa-pencil-alt')
if body.count('fa-pencil-alt') != 4:
    raise SystemExit('P2: fa-pencil-alt appears %d times, not 4 (desktop '
                     'live + disabled, phone live + disabled)'
                     % body.count('fa-pencil-alt'))

# the export no longer reads them
js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))
if "querySelectorAll('th, td')" in js:
    raise SystemExit('P2: the export still reads every cell')
if 'not(.cell-actions)' not in js or 'not(.mobile-action-bar)' not in js:
    raise SystemExit('P2: the export does not skip the action cells')

# every column still has a width, and they still sum to 100
got = [(int(m.group(1)), float(m.group(2))) for m in re.finditer(
    r'\.task-list-table th:nth-child\((\d)\)[^{}]*\{[^}]*width:\s*([\d.]+)%',
    cssn)]
if sorted(x[0] for x in got) != [1, 2, 3, 4, 5, 6, 7]:
    raise SystemExit('P2: the widths cover columns %s, not 1-7'
                     % sorted(x[0] for x in got))
if abs(sum(x[1] for x in got) - 100) > 0.001:
    raise SystemExit('P2: the widths sum to %s, not 100'
                     % sum(x[1] for x in got))

# THE SENTINEL IS SEVEN ONE-LINE COMMENTS, NOT ONE SEVEN-LINE COMMENT.
# Django's tag_re is {%.*?%}|{{.*?}}|{#.*?#} WITHOUT re.DOTALL, so a {# #}
# that outlives its line is not a comment at all - the lexer never matches
# it and every character renders on the page. The first cut of this round
# had a seven-line one, and test_crs_comment_fix.py caught it, which is
# the suite that exists for exactly this.
NOTE = """{% endblock %}

{# P2, 1 Oct 2026 - this page used to rebuild base's table standard #}
{# under .task-list-table: 23 rules, 77 declarations, and a phone #}
{# card label that had drifted to 11px UPPERCASE #6c757d while the #}
{# house was 12.5px sentence case in var(--alv-ink-soft). The table #}
{# is .alv-table now and base owns the card. The Actions column is #}
{# new - the screen had no way to act on a row at all - and the #}
{# Excel export skips it.              [test_task_table.py] #}"""
# THE LAST endblock, not the first. The first one closes {% block title %}
# on line 6, and the first cut of this round signed itself there - above
# the page rather than below it.
cut = t.rfind('{% endblock %}')
if cut < 0:
    raise SystemExit('P2: no {% endblock %} to sign')
t = t[:cut] + eol(p, NOTE) + t[cut + len('{% endblock %}'):]
if SENTINEL not in t:
    raise SystemExit('P2: the sentinel did not land')
for m in re.finditer(r'\{#(.*?)#\}', t, re.S):
    if '\n' in m.group(1):
        raise SystemExit('P2: a {# #} outlives its line, so Django will '
                         'render it on the page: %r' % m.group(1)[:60])

print('-' * 74)
print('  gates: no base-owned rule left under the page name, 4 tones + 3')
print('         neutral, 4 pencil glyphs, export skips both action cells,')
print('         7 column widths summing to 100')

if not CHECK:
    back_up(p, raw)
    write(p, t)

print('-' * 74)
print('  The task list is a house table. Edit and Delete per row, with a')
print('  disabled twin on the project row, and base owns the phone card.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
