# -*- coding: utf-8 -*-
"""SECTION P, ROUND P3 - PROJECT DETAIL JOINS THE STANDARD

Demetri's six Projects findings, 1 Oct. Four of them are this one file:

  1. "Why is the Pending on the right that colour?"   -> #f8d7da
  2. "the Edit and Delete action icons onto our standards"
  3. "standardise the High, Medium, Low colours"
  4. "standardise Pending, In Progress and Completed"

AGREED 1 Oct, four questions:

  1. ACTIONS AND PILLS IN ONE ROUND. Both live in this 1,643-line file and
     two passes over it is how a half-converted page happens.
  2. THE LONE PROJECT EDIT IS CONVERTED IN PLACE, beside the status it
     edits, rather than moved into the action bar.
  3. THE SUBTASK STATUS PILL STAYS CLICKABLE and keeps a visible hover -
     clicking it changes the status, and removing the signal would hide
     a feature.
  4. Add Task and Add Subtask KEEP .action-secondary and LOSE .btn-sm.

THE BUTTONS. Three clusters, ten buttons:

    project   btn-sm btn-info Edit              + btn-light twin
    task      btn-sm btn-info / btn-sm btn-danger + two twins
    subtask   btn-xs btn-info / btn-xs btn-danger + two twins

btn-xs - AND A CORRECTION I OWE THE RECORD. I reported three times that
btn-xs is undefined, so the subtask buttons fell back to plain .btn and
rendered LARGER than their parents. That is wrong. Bootstrap 4.1.3 did
drop btn-xs, but THIS PAGE DEFINES IT ITSELF:

    .btn-xs { padding: 2px 6px; font-size: 11px; border-radius: 3px; }

Measured in Chromium with identical content in each button:

    task button    btn-sm           32x31
    subtask button btn-xs, as this page defines it     28x24
    btn-xs with NO definition anywhere (what I claimed) 40x38

So the subtask buttons are deliberately SMALLER, not accidentally bigger.
My error was asking a narrow question - I grepped base.html and the
static folder for btn-xs, found nothing, and concluded "we do not define
it" without reading the page's own stylesheet. Lesson 21 again: ask the
question the claim actually rests on.

What survives is smaller but real: btn-xs is a Bootstrap 3 class name
kept alive by a page-local redefinition, and the three action clusters
are three different sizes. All of it goes anyway - .icon-action-btn
makes every one of them 34x34, and 44x44 on a phone.

fa-edit SIX TIMES. The house glyph is fa-pencil-alt on all 23 converted
pages; P1 shipped fa-edit here once and test_row_personal caught it.

FIVE INLINE style="opacity: 0.5" WITH A LITERAL #6c757d on the disabled
twins, where base has .icon-disabled.

AND BASE ALREADY MAKES .icon-action-btn 44x44 BELOW 768px, so converting
buys a proper phone touch target with no phone-specific work.

THE PILLS. Six spans, and the tone map is the one agreed in P2 rather
than a new decision:

    Critical -bad | High, Medium -attn | Low -neutral
    Completed -good | In Progress -info | On Hold -attn
    Pending, Not Started, anything unforeseen -neutral

Seventeen page rules go with them, including .status-pending's #f8d7da -
which is Demetri's first finding - and .clickable-status:hover's #007bff,
rewritten onto the house accent rather than deleted.

NOT IN THIS ROUND. projects.html and project_gantt.html carry the same
three .status-* colours and nothing else of this; they are a small round
of their own rather than three files half-done here.

Backups: .bak_detailpills. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_detailpills'
CRLF = {}
PAGE = os.path.join('projects', 'projects_detail.html')
SENTINEL = 'test_detail_pills.py'

# The two chains, written once. EXPR is the template expression holding
# the value; the mapping is P2's, agreed 1 Oct and not re-decided here.
STATUS = ("{%% if %(e)s == 'Completed' %%}alv-pill-good"
          "{%% elif %(e)s == 'In Progress' %%}alv-pill-info"
          "{%% elif %(e)s == 'On Hold' %%}alv-pill-attn"
          "{%% else %%}alv-pill-neutral{%% endif %%}")
PRIORITY = ("{%% if %(e)s == 'Critical' %%}alv-pill-bad"
            "{%% elif %(e)s == 'High' or %(e)s == 'Medium' %%}alv-pill-attn"
            "{%% else %%}alv-pill-neutral{%% endif %%}")


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
            raise SystemExit('P3: %s is not a byte copy' % bak)


CUTS = []


def swap(text, old, new, what):
    """Replace exactly once, in THIS FILE'S line endings. This file is
    CRLF; an anchor written with \\n misses every time, which is the trap
    P2 lost half an hour to."""
    o, n = eol(PATH, old), eol(PATH, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('P3: %s appears %d times, not once\n%r'
                         % (what, c, old[:90]))
    CUTS.append(what)
    return text.replace(o, n)


# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P3 - PROJECT DETAIL JOINS THE STANDARD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

PATH = alv_tree.join(PAGE)
t, raw = read(PATH)
if SENTINEL in t:
    print('  already done')
    raise SystemExit(0)

# ---- base must own what this round hands over --------------------------
b = read(alv_tree.path_of('base.html'))[0]
bcss = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
    re.findall(r'<style\b[^>]*>(.*?)</style>', b, re.S)), flags=re.S)
NEEDED = ('.alv-pill', '.alv-pill-good', '.alv-pill-attn', '.alv-pill-bad',
          '.alv-pill-info', '.alv-pill-neutral', '.row-actions',
          '.icon-action-btn')
missing = [n for n in NEEDED
           if not re.search(r'(?<![-\w])' + re.escape(n) + r'\s*\{', bcss)]
if missing or not re.search(r'(?<![-\w])\.icon-disabled\b', bcss):
    raise SystemExit('P3: base does not own %s' % (missing or ['.icon-disabled']))
# and the 44px phone target, which is half the argument for converting
if not re.search(r'\.icon-action-btn\s*\{[^}]*width:\s*44px', bcss):
    raise SystemExit('P3: base no longer gives .icon-action-btn a 44px '
                     'phone target, so this round loses that claim')
print('  base owns the pills, the row actions and the 44px phone target')

# ==========================================================================
# MARKUP
# ==========================================================================

# ---- 1. the project status pill ----------------------------------------
t = swap(t, """        <span class="status-badge
          {% if project.get_calculated_status == 'Completed' %}status-completed
          {% elif project.get_calculated_status == 'In Progress' %}status-in-progress
          {% else %}status-pending{% endif %}">""",
         '        <span class="alv-pill '
         + STATUS % {'e': 'project.get_calculated_status'} + '">',
         'the project status pill')

# ---- 2. the lone project Edit, converted in place ----------------------
t = swap(t, """        {% if perms.auth.can_edit_projects %}
          <a href="{% url 'projects_edit' project.project_id %}" class="btn btn-sm btn-info ml-2">
            <i class="fas fa-edit"></i>
          </a>
        {% else %}
          <button type="button" class="btn btn-sm btn-light ml-2" disabled style="opacity: 0.5;">
            <i class="fas fa-edit" style="color: #6c757d;"></i>
          </button>
        {% endif %}""",
         """        <span class="row-actions">
          {% if perms.auth.can_edit_projects %}
            <a href="{% url 'projects_edit' project.project_id %}"
               class="icon-action-btn icon-edit" title="Edit Project">
              <i class="fas fa-pencil-alt"></i>
            </a>
          {% else %}
            <span class="icon-action-btn icon-disabled"
                  title="No edit permission">
              <i class="fas fa-pencil-alt"></i>
            </span>
          {% endif %}
        </span>""",
         'the project Edit button')

# ---- 3 + 4. the two Add buttons lose btn-sm ----------------------------
t = swap(t, 'class="btn action-secondary btn-sm add-task-btn"',
         'class="btn action-secondary add-task-btn"', 'Add Task')
t = swap(t, 'class="btn action-secondary btn-sm ml-2 add-subtask-btn"',
         'class="btn action-secondary ml-2 add-subtask-btn"', 'Add Subtask')

# ---- 5. the task priority pill -----------------------------------------
t = swap(t,
         '<span class="task-priority-indicator '
         'priority-{{ task.task_priority|lower }}">',
         '<span class="alv-pill '
         + PRIORITY % {'e': 'task.task_priority'} + '">',
         'the task priority pill')

# ---- 6. the task status pill -------------------------------------------
t = swap(t,
         '<span class="task-status-badge '
         'status-{{ task.get_calculated_status|slugify }}">',
         '<span class="alv-pill '
         + STATUS % {'e': 'task.get_calculated_status'} + '">',
         'the task status pill')

# ---- 7. the task action cluster ----------------------------------------
t = swap(t, """              {% if perms.auth.can_edit_projects %}
                <div class="btn-group ml-2">
                  <a href="{% url 'project_tasks_edit' project.project_id task.task_id %}" class="btn btn-sm btn-info">
                    <i class="fas fa-edit"></i>
                  </a>
                  <button type="button" class="btn btn-sm btn-danger" onclick="confirmDeleteTask('{{ task.task_id }}', '{{ task.task_name|escapejs }}', {{ task.subtasks.all|length }})">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              {% else %}
                <div class="btn-group ml-2">
                  <button type="button" class="btn btn-sm btn-light" disabled style="opacity: 0.5;">
                    <i class="fas fa-edit" style="color: #6c757d;"></i>
                  </button>
                  <button type="button" class="btn btn-sm btn-light" disabled style="opacity: 0.5;">
                    <i class="fas fa-trash" style="color: #6c757d;"></i>
                  </button>
                </div>
              {% endif %}""",
         """              <span class="row-actions ml-2">
                {% if perms.auth.can_edit_projects %}
                  <a href="{% url 'project_tasks_edit' project.project_id task.task_id %}"
                     class="icon-action-btn icon-edit" title="Edit Task">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                  <button type="button" class="icon-action-btn icon-delete"
                          title="Delete Task"
                          onclick="confirmDeleteTask('{{ task.task_id }}', '{{ task.task_name|escapejs }}', {{ task.subtasks.all|length }})">
                    <i class="fas fa-trash"></i>
                  </button>
                {% else %}
                  <span class="icon-action-btn icon-disabled"
                        title="No edit permission">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                  <span class="icon-action-btn icon-disabled"
                        title="No edit permission">
                    <i class="fas fa-trash"></i>
                  </span>
                {% endif %}
              </span>""",
         'the task action cluster')

# ---- 8. the subtask priority pill --------------------------------------
t = swap(t,
         '<span class="subtask-priority-indicator '
         'priority-{{ subtask.task_priority|lower }}">',
         '<span class="alv-pill '
         + PRIORITY % {'e': 'subtask.task_priority'} + '">',
         'the subtask priority pill')

# ---- 9. the subtask cluster, both branches -----------------------------
# The clickable pill keeps its onclick AND its .clickable-status hook -
# question 3. Without the hook the cursor and the hover go with it, and
# a control that changes data would look like a label.
t = swap(t, """                        {% if perms.auth.can_edit_projects %}
                          <span class="subtask-status-badge status-{{ subtask.task_status|slugify }} clickable-status"
                                onclick="editTaskStatus('{{ subtask.task_id }}', '{{ subtask.task_status }}')">
                            {{ subtask.task_status }}
                          </span>
                          <a href="{% url 'project_tasks_edit' project.project_id subtask.task_id %}" class="btn btn-xs btn-info ml-1">
                            <i class="fas fa-edit"></i>
                          </a>
                          <button type="button" class="btn btn-xs btn-danger ml-1" onclick="confirmDeleteSubtask('{{ subtask.task_id }}', '{{ subtask.task_name|escapejs }}')">
                            <i class="fas fa-trash"></i>
                          </button>""",
         """                        {% if perms.auth.can_edit_projects %}
                          <span class="alv-pill """
         + STATUS % {'e': 'subtask.task_status'} + """ clickable-status"
                                title="Click to change the status"
                                onclick="editTaskStatus('{{ subtask.task_id }}', '{{ subtask.task_status }}')">
                            {{ subtask.task_status }}
                          </span>
                          <span class="row-actions ml-1">
                            <a href="{% url 'project_tasks_edit' project.project_id subtask.task_id %}"
                               class="icon-action-btn icon-edit" title="Edit Subtask">
                              <i class="fas fa-pencil-alt"></i>
                            </a>
                            <button type="button" class="icon-action-btn icon-delete"
                                    title="Delete Subtask"
                                    onclick="confirmDeleteSubtask('{{ subtask.task_id }}', '{{ subtask.task_name|escapejs }}')">
                              <i class="fas fa-trash"></i>
                            </button>
                          </span>""",
         'the subtask cluster, live branch')

t = swap(t,
         '<span class="subtask-status-badge '
         'status-{{ subtask.task_status|slugify }}">',
         '<span class="alv-pill '
         + STATUS % {'e': 'subtask.task_status'} + '">',
         'the subtask status pill, read-only branch')

# the read-only subtask twins
t = swap(t, """                          <button type="button" class="btn btn-xs btn-light ml-1" disabled style="opacity: 0.5;">
                            <i class="fas fa-edit" style="color: #6c757d;"></i>
                          </button>
                          <button type="button" class="btn btn-xs btn-light ml-1" disabled style="opacity: 0.5;">
                            <i class="fas fa-trash" style="color: #6c757d;"></i>
                          </button>""",
         """                          <span class="row-actions ml-1">
                            <span class="icon-action-btn icon-disabled"
                                  title="No edit permission">
                              <i class="fas fa-pencil-alt"></i>
                            </span>
                            <span class="icon-action-btn icon-disabled"
                                  title="No edit permission">
                              <i class="fas fa-trash"></i>
                            </span>
                          </span>""",
         'the subtask disabled twins')

print('  markup: %d region(s) converted' % len(CUTS))

# ==========================================================================
# CSS - the private pill stylesheet goes back to base
# ==========================================================================
DEAD = [
    """.status-badge {
    padding: 6px 15px;
    border-radius: 15px;
    font-size: 13px;
    font-weight: 500;
}

""",
    """.status-completed { background: #d4edda; color: #155724; }
.status-in-progress { background: #fff3cd; color: #856404; }
.status-pending { background: #f8d7da; color: #721c24; }
""",
    """/* Priority Indicators */
.task-priority-indicator, .subtask-priority-indicator {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    margin-right: 0;
}

.priority-critical { background: #dc3545; color: white; }
.priority-high { background: var(--alv-warn); color: var(--alv-on-accent); }
.priority-medium { background: #ffc107; color: #212529; }
.priority-low { background: #6c757d; color: white; }

.task-status-badge, .subtask-status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
}

""",
    """.status-not-started { background: #f8d7da; color: #721c24; }
.status-on-hold { background: #e2e3e5; color: #383d41; }
""",
    # Nothing wears btn-xs once the clusters are converted, and a class
    # name that nothing uses is the defect this project already tracks
    # three of. It kept a Bootstrap 3 name alive, which is the whole
    # reason it was confusing enough to get wrong.
    """.btn-xs { padding: 2px 6px; font-size: 11px; border-radius: 3px; }
""",
]
for i, d in enumerate(DEAD, 1):
    t = swap(t, d, '', 'CSS cut %d' % i)

# the hover keeps its job and loses its literal blue
t = swap(t, """@media (hover: hover) and (pointer: fine) {
    .clickable-status:hover {
        transform: scale(1.05);
        border: 1px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,123,255,0.2);
    }
}""",
         """/* The subtask status pill is a CONTROL - clicking it changes the
   status - so it keeps a cursor and a hover. Only the colour changed:
   #007bff was Bootstrap's blue, and the accent is the house signal for
   something you can act on.    [test_detail_pills.py] */
@media (hover: hover) and (pointer: fine) {
    .clickable-status:hover {
        transform: scale(1.05);
        border-color: var(--alv-accent);
        box-shadow: 0 2px 4px var(--alv-accent-soft);
    }
}""",
         'the clickable hover')

# ==========================================================================
# GATES
# ==========================================================================
body = re.sub(r'<(script|style)\b.*?</\1>', '',
              re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
cssn = re.sub(r'/\*.*?\*/', ' ', t[t.find('<style'):t.find('</style>')],
              flags=re.S)

for dead in ('btn-xs', 'btn-info', 'btn-danger', 'btn-light', 'fa-edit'):
    if re.search(r'(?<![-\w])' + dead + r'(?![\w-])', body):
        raise SystemExit('P3: %s is still in the markup' % dead)
if 'opacity: 0.5' in body or '#6c757d' in body:
    raise SystemExit('P3: an inline disabled style survived')
# six pills, and the tone each one can take
if body.count('alv-pill ') != 6:
    raise SystemExit('P3: %d alv-pill spans, not 6' % body.count('alv-pill '))
for tone, n in (('alv-pill-good', 4), ('alv-pill-info', 4),
                ('alv-pill-bad', 2), ('alv-pill-attn', 6),
                ('alv-pill-neutral', 6)):
    got = body.count(tone)
    if got != n:
        raise SystemExit('P3: %s appears %d times, not %d' % (tone, got, n))
# the glyph, and the clusters
if body.count('fa-pencil-alt') != 6:
    raise SystemExit('P3: %d fa-pencil-alt, not 6' % body.count('fa-pencil-alt'))
# FOUR clusters, not five: the project cluster wraps its {% if %} in one
# .row-actions, while the subtask's two branches each carry their own.
if body.count('row-actions') != 4:
    raise SystemExit('P3: %d row-actions, not 4' % body.count('row-actions'))
if body.count('icon-disabled') != 5:
    raise SystemExit('P3: %d icon-disabled twins, not 5'
                     % body.count('icon-disabled'))
# the clickable pill kept its job
if 'editTaskStatus(' not in body or 'clickable-status' not in body:
    raise SystemExit('P3: the subtask status pill stopped being clickable')
if '#007bff' in cssn:
    raise SystemExit('P3: the hover still carries Bootstrap blue')
# the private stylesheet is gone, and the layout it sat in is not
for gone in ('.status-badge', '.status-completed', '.status-pending',
             '.priority-critical', '.task-status-badge',
             '.task-priority-indicator', '.status-on-hold'):
    if re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', cssn):
        raise SystemExit('P3: %s is still styled' % gone)
for keep in ('.project-status-container', '.overview-status-col',
             '.clickable-status'):
    if not re.search(re.escape(keep) + r'(?![\w-])[^{}]*\{', cssn):
        raise SystemExit('P3: %s was removed, and it is layout this round '
                         'has no business taking' % keep)

NOTE = """{% endblock %}

{# P3, 1 Oct 2026 - Project Detail joins the standard. Ten buttons in #}
{# three clusters were btn-info / btn-danger / btn-light at three #}
{# different sizes - 32x31, 28x24 and the project one - and are one #}
{# 34x34 control now, 44x44 on a phone. Six pills #}
{# and seventeen page rules, including Pending as #f8d7da, are base's #}
{# .alv-pill now. The subtask status pill is still a control: it keeps #}
{# its click and its hover, on the accent.    [test_detail_pills.py] #}"""
cut = t.rfind('{% endblock %}')
if cut < 0:
    raise SystemExit('P3: no {% endblock %} to sign')
t = t[:cut] + eol(PATH, NOTE) + t[cut + len('{% endblock %}'):]
for m in re.finditer(r'\{#(.*?)#\}', t, re.S):
    if '\n' in m.group(1):
        raise SystemExit('P3: a {# #} outlives its line, so Django renders '
                         'it on the page')
if SENTINEL not in t:
    raise SystemExit('P3: the sentinel did not land')

if not CHECK:
    back_up(PATH, raw)
    write(PATH, t)

print('  CSS: the private pill stylesheet handed back, hover retoned')
print('-' * 74)
print('  gates: no Bootstrap button class or inline disabled style left,')
print('         6 pills, 6 pencil glyphs, 4 clusters, 5 twins, and the')
print('         subtask pill still changes the status when clicked')
print('-' * 74)
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
