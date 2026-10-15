# -*- coding: utf-8 -*-
"""apply_project_origin.py - round PJ-1, 15 Oct 2026.

A BACK BUTTON THAT ALWAYS GOES TO THE SAME PLACE IS NOT A BACK BUTTON.

Demetri, after a full check of the Projects module:

  "If I edit a Project from the Projects page, it takes me to the Edit
   screen which is correct, however, when I press the Back button it
   takes me to the Project Details screen."


THREE LINKS REACH THAT SCREEN AND ONE OF THEM SAID SO
============================================================================
    projects.html          two Edit links, desktop and phone   NOTHING
    projects_detail.html   one Edit link                       NOTHING
    project_gantt.html     window.location, in script          from_gantt

So two of the three fell to the same `else` arm and Back went to the
Project Details page whichever page you had left. From the Projects list
that is a stranger's page; from the Gantt chart it was already right.

THIS IS TL-2'S MACHINERY, GROWN FOR THE PROJECT ITSELF. On 4 Oct the same
complaint was answered for the Task List - TASK_ORIGINS, a key chosen
from a map written down in the view rather than a URL taken at face
value. The project's own edit screen never got it.


AND BACK DISAGREED WITH SAVE, ON THE SAME SCREEN
============================================================================
    Back               -> projects_detail
    Update Project     -> projects          (the list)

Two controls an inch apart, two different answers, from every origin but
the Gantt chart. Nobody reported the Save half; it is the same defect
wearing the other button. Demetri was shown both and chose one rule for
both:

  "Follow the same origin as Back"

WHICH CHANGES ONE THING NOBODY REPORTED, and it is said out loud here
rather than buried: Edit opened from Project Details and then SAVED used
to land on the Projects list, and now lands back on the Project. That is
the rule applied honestly; it is not a side effect that went unnoticed.


WHAT TRAVELS IS A KEY, NOT A URL
============================================================================
?next=/anywhere/ taken at face value is an open redirect. A key chooses
from PROJECT_ORIGINS, and an unrecognised one falls back to the Project
exactly as the Back button did before this round.

NOT MERGED WITH TASK_ORIGINS, and that is the one real difference between
the two maps: every task origin takes a project_id, and 'projects' takes
none. The arity travels WITH the key instead of being assumed, because
reverse() is otherwise the only thing that would notice the day a fourth
origin is added.


THE GATE WORTH MORE THAN THE CHANGE
============================================================================
Section 4 censuses EVERY `{% url 'projects_edit' %}` in every template
and refuses the round unless each one names where it came from. The
defect was not that the view could not tell - it was that nothing made a
link say. A fifth link added next month without `?from=` is the same bug
returning, and this refuses it at the gate rather than waiting for
someone to press Back.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_prjorigin'
VIEW = os.path.join('pages', 'views', 'projects.py')
EDIT = 'projects/projects_edit.html'
LIST = 'projects/projects.html'
DETAIL = 'projects/projects_detail.html'
ME = 'test_project_origin.py'
PATCHER = 'apply_project_origin.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
BH = 'test_bar_height.py'
HL = 'test_help_label.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 80, 81
# TWO MARKUP CENSUSES COUNTED THE DUPLICATE, AND NEITHER READER DID.
# projects_edit carried its Back control TWICE, behind an {% if %}, and
# both of these walk markup without resolving a branch - so each counted
# two controls where a reader only ever saw one. The round collapses the
# branch, so each count falls by exactly one. That is the instrument
# working, not a regression: a round that removed a REAL control would
# move these numbers the same way, which is why the fall is one and the
# note says which control it was.
BAR_WAS, BAR_NOW = 268, 267
LBL_WAS, LBL_NOW = 130, 129
ALIAS_WAS, ALIAS_NOW = 71, 73
ALIAS_P_WAS, ALIAS_S_WAS = 35, 36
ALIAS_P_NOW, ALIAS_S_NOW = 36, 37
CO = 'test_code_only.py'

# ===================================================================== view
VIEW_BLOCK_ANCHOR = """    q = '&'.join(p for p in q.split('&') if not p.startswith('from='))
    return (url + ('?' + q if q else ''), TASK_ORIGIN_LABELS[key])"""

VIEW_BLOCK_NEW = VIEW_BLOCK_ANCHOR + '''


# --------------------------------------------------------------------------- #
# PJ-1, 15 Oct 2026 - WHERE A PROJECT EDIT CAME FROM
# --------------------------------------------------------------------------- #
# Demetri: "If I edit a Project from the Projects page, it takes me to the
# Edit screen which is correct, however, when I press the Back button it
# takes me to the Project Details screen."
#
# Three links reach projects_edit and only one of them ever said so - the
# Gantt chart, with from_gantt=true. The other two fell to the same else
# arm, so Back went to the Project whichever page you left. This is the
# block above, grown for the project itself.
#
# AND BACK DISAGREED WITH SAVE. On the same screen Back went to the
# Project Details page and Update Project went to the Projects LIST.
# Both follow one rule now, which is the answer Demetri chose when the
# two were put side by side - including the one case nobody reported:
# an edit opened from Project Details and saved used to land on the list.
#
# NOT MERGED WITH TASK_ORIGINS. Every task origin takes a project_id and
# 'projects' takes none, so the arity travels WITH the key rather than
# being assumed - reverse() is otherwise the only thing that would notice
# the day a fourth origin is added.
PROJECT_ORIGINS = {
    'list': ('projects', False),
    'detail': ('projects_detail', True),
    'gantt': ('project_gantt', True),
}

PROJECT_ORIGIN_LABELS = {
    'list': 'Back to Projects',
    'detail': 'Back to Project',
    'gantt': 'Back to Gantt Chart',
}


def project_origin(request):
    """The key naming the page this project edit was opened from, or ''.

    from_gantt=true is still read: the Gantt chart has linked that way
    since long before this round and its link is not being rewritten.
    """
    key = request.GET.get('from', '')
    if key in PROJECT_ORIGINS:
        return key
    return 'gantt' if request.GET.get('from_gantt') else ''


def project_origin_query(key):
    """The query string that carries an origin through a re-render.

    A save that fails validation re-renders the form, and a form whose
    action has lost the origin sends the next save somewhere else.
    """
    return urlencode([('from', key)]) if key in PROJECT_ORIGINS else ''


def project_origin_back(request, project):
    """(url, title) for Back - and for the redirect after a save.

    An unrecognised key falls back to the Project exactly as the Back
    button did before this round. Every in-app link names its origin, so
    that arm is reached by a bookmark or a hand-typed URL.
    """
    key = project_origin(request)
    if not key:
        return (reverse('projects_detail', args=[project.project_id]),
                'Back to Project')
    name, takes_id = PROJECT_ORIGINS[key]
    url = (reverse(name, args=[project.project_id]) if takes_id
           else reverse(name))
    return (url, PROJECT_ORIGIN_LABELS[key])'''

# A DOCSTRING IS A COMMENT AND THIS ONE NAMED THE DEFECT AS A FEATURE.
# Delimited with single quotes because the payload carries the triple
# double-quotes of the docstring itself.
VIEW_DOC_WAS = '''    """Edit existing project - enhanced to handle Gantt chart returns"""'''

VIEW_DOC_NOW = '''    """Edit existing project, returning you to the page it was opened from.

    PJ-1, 15 Oct 2026 - this said "enhanced to handle Gantt chart
    returns", which was true and was the whole defect: the Gantt chart
    was the ONE origin it handled, and the other two links fell to an
    else arm.
    """'''

VIEW_HEAD_WAS = """    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', 'false') == 'true'"""

VIEW_HEAD_NOW = """    # PJ-1 - and from the Projects list and from the Project itself,
    # neither of which had a way to say so. Back and the save below now
    # read the same answer.
    back_url, back_title = project_origin_back(request, project)
    origin_query = project_origin_query(project_origin(request))"""

VIEW_POST_WAS = """            # Redirect based on where user came from
            if from_gantt:
                return redirect('project_gantt', project_id=project_id)
            else:
                return redirect('projects')"""

VIEW_POST_NOW = """            # PJ-1 - Update Project returns you to the page you opened
            # the edit from, which is the rule the Back button beside it
            # follows. It went to the Projects list from every origin but
            # the Gantt chart, however you had arrived.
            return redirect(back_url)"""

VIEW_CTX_WAS = """        'from_gantt': from_gantt,  # Pass this to template for form action"""

VIEW_CTX_NOW = """        # PJ-1 - Back, and the form's own action, which has to keep the
        # origin across a save that fails validation and re-renders.
        'back_url': back_url,
        'back_title': back_title,
        'form_action': (reverse('projects_edit', args=[project.project_id])
                        + ('?' + origin_query if origin_query else '')),"""

# ================================================================= template
EDIT_NOTE_WAS = """     Back link is context-aware (Gantt vs project detail). -->"""

EDIT_NOTE_NOW = """     Back goes where the edit was opened from - PJ-1, 15 Oct 2026. The
     view decides and hands over back_url, so this template has ONE Back
     control instead of a branch with two copies of it. -->"""

EDIT_BACK_WAS = """  {% if from_gantt %}
    <a href="{% url 'project_gantt' project.project_id %}" class="btn action-back" title="Back to Gantt Chart">
      <i class="fas fa-arrow-left"></i>
      <span class="action-back-label">Back</span>
    </a>
  {% else %}
    <a href="{% url 'projects_detail' project.project_id %}" class="btn action-back" title="Back to Project">
      <i class="fas fa-arrow-left"></i>
      <span class="action-back-label">Back</span>
    </a>
  {% endif %}"""

EDIT_BACK_NOW = """  <a href="{{ back_url }}" class="btn action-back" title="{{ back_title }}">
    <i class="fas fa-arrow-left"></i>
    <span class="action-back-label">Back</span>
  </a>"""

EDIT_FORM_WAS = """      {% if from_gantt %}
        action="{% url 'projects_edit' project.project_id %}?from_gantt=true"
      {% else %}
        action="{% url 'projects_edit' project.project_id %}"
      {% endif %}>"""

EDIT_FORM_NOW = """      action="{{ form_action }}">"""

EDIT_JS_WAS = """const fromGantt = {{ from_gantt|yesno:"true,false" }};
console.log('From Gantt Chart:', fromGantt);

"""

EDIT_JS_NOW = """"""

LIST_DESK_WAS = """<a href="{% url 'projects_edit' project.project_id %}"
                     class="icon-action-btn icon-edit" title="Edit Project">"""

LIST_DESK_NOW = """<a href="{% url 'projects_edit' project.project_id %}?from=list"
                     class="icon-action-btn icon-edit" title="Edit Project">"""

LIST_PHONE_WAS = """<a href="{% url 'projects_edit' project.project_id %}" class="mobile-action-btn">"""

LIST_PHONE_NOW = """<a href="{% url 'projects_edit' project.project_id %}?from=list" class="mobile-action-btn">"""

DETAIL_WAS = """<a href="{% url 'projects_edit' project.project_id %}"
               class="icon-action-btn icon-edit" title="Edit Project">"""

DETAIL_NOW = """<a href="{% url 'projects_edit' project.project_id %}?from=detail"
               class="icon-action-btn icon-edit" title="Edit Project">"""

# ================================================================ registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------- PJ-1, 15 Oct 2026
    # Demetri: Back from the Project Edit screen went to the Project
    # Details page whichever page the edit was opened from. Two of the
    # three links that reach it had no way to say where they were.
    @{ File = 'pages\\views\\projects.py'; Text = 'PROJECT_ORIGINS'; What = 'a project edit knows which of three pages it was opened from' },
    # NO APOSTROPHE IN THE TEXT. PowerShell escapes one inside a
    # single-quoted string by DOUBLING it, and the gate's own table says
    # not to rely on that. The query is enough on its own and appears in
    # no backup of this page.
    @{ File = 'pages\\templates\\projects\\projects.html'; Text = '?from=list'; What = 'and the Projects list says so, on the desktop link and the phone one' },
    @{ File = 'pages\\templates\\projects\\projects_edit.html'; Text = 'from_gantt'; Absent = $true; Code = $true; What = 'the edit screen has one Back control instead of a branch with two' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_calendar_grid.py'
)"""

SUITE_NOW = """    'test_calendar_grid.py',
    'test_project_origin.py'
)"""

TREE_WAS = """    'test_calendar_grid.py',
]"""

TREE_NOW = """    'test_calendar_grid.py',
    # PJ-1, 15 Oct 2026 - a project edit learns which of three pages it
    # was opened from, and Back and Save stop disagreeing about it.
    # Wide from birth.
    'test_project_origin.py',
]"""

ROUNDS_WAS = """    '.bak_calgrid',
]"""

ROUNDS_NOW = """    '.bak_calgrid',
    # PJ-1, 15 Oct 2026 - PROJECT_ORIGINS beside TL-2's TASK_ORIGINS, so
    # Back from the Project Edit screen returns to the page the edit was
    # opened from, and the save beside it follows the same rule.
    '.bak_prjorigin',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('PJ-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def view_body(src, name):
    """One function out of a module - the file has two `from_gantt`
    readers and only one of them is this round's."""
    i = src.find('def %s(' % name)
    if i < 0:
        return ''
    j = src.find('\ndef ', i + 1)
    return src[i:j if j > 0 else len(src)]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the TREE and of the code -
    # this patcher's own docstring names PROJECT_ORIGINS, so a raw read
    # of the view would be answering a question about a comment.
    vp = os.path.join(root, VIEW)
    if 'PROJECT_ORIGINS' in python_code_only(read(vp), payloads=False):
        print('PJ-1  already applied - a project edit knows its origin.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    s = read(vp)
    s = swap(s, VIEW_BLOCK_ANCHOR, VIEW_BLOCK_NEW,
             '%s (the origin map)' % VIEW)
    s = swap(s, VIEW_DOC_WAS, VIEW_DOC_NOW, '%s (the docstring)' % VIEW)
    s = swap(s, VIEW_HEAD_WAS, VIEW_HEAD_NOW, '%s (the view head)' % VIEW)
    s = swap(s, VIEW_POST_WAS, VIEW_POST_NOW,
             '%s (the save redirect)' % VIEW)
    s = swap(s, VIEW_CTX_WAS, VIEW_CTX_NOW, '%s (the context)' % VIEW)
    # THE BRANCH IS GONE FROM THIS VIEW AND FROM NO OTHER. project_tasks_edit
    # reads from_gantt too and is TL-2's, not this round's.
    body = python_code_only(view_body(s.replace('\r\n', '\n'),
                                      'projects_edit'), payloads=False)
    if 'from_gantt' in body:
        refuse('%s: projects_edit still reads from_gantt directly' % VIEW)
    if 'redirect(back_url)' not in body:
        refuse('%s: the save does not follow the origin' % VIEW)
    if "'back_url': back_url" not in body:
        refuse('%s: the template is not given a Back' % VIEW)
    tasks = python_code_only(view_body(s.replace('\r\n', '\n'),
                                       'project_tasks_edit'), payloads=False)
    if 'from_gantt' not in tasks:
        refuse('%s: this round has reached into TL-2\'s view' % VIEW)
    out[vp] = s

    # ---------------------------------------------------------------- 2
    p = alv_tree.join(EDIT.replace('/', os.sep))
    s = read(p)
    s = swap(s, EDIT_NOTE_WAS, EDIT_NOTE_NOW, '%s (the note)' % EDIT)
    s = swap(s, EDIT_BACK_WAS, EDIT_BACK_NOW, '%s (one Back)' % EDIT)
    s = swap(s, EDIT_FORM_WAS, EDIT_FORM_NOW, '%s (the form action)' % EDIT)
    s = swap(s, EDIT_JS_WAS, EDIT_JS_NOW, '%s (the dead const)' % EDIT)
    if 'from_gantt' in code_only(s):
        refuse('%s: from_gantt survives in the page' % EDIT)
    if s.count('class="btn action-back"') != 1:
        refuse('%s: expected exactly one Back control, found %d'
               % (EDIT, s.count('class="btn action-back"')))
    if s.count('action-back-label') != 1:
        refuse('%s: expected exactly one Back label, found %d'
               % (EDIT, s.count('action-back-label')))
    out[p] = s

    # ---------------------------------------------------------------- 3
    p = alv_tree.join(LIST.replace('/', os.sep))
    s = read(p)
    s = swap(s, LIST_DESK_WAS, LIST_DESK_NOW, '%s (the desktop Edit)' % LIST)
    s = swap(s, LIST_PHONE_WAS, LIST_PHONE_NOW, '%s (the phone Edit)' % LIST)
    out[p] = s

    p = alv_tree.join(DETAIL.replace('/', os.sep))
    out[p] = swap(read(p), DETAIL_WAS, DETAIL_NOW, '%s (the Edit)' % DETAIL)

    # ---------------------------------------------------------------- 4
    # THE CENSUS, AND THE REAL GATE. Every link that reaches this screen
    # must name where it came from. The defect was never that the view
    # could not tell - it was that nothing made a link say.
    named, bare = 0, []
    for q in alv_tree.templates():
        t = out.get(q, read(q)) if q in out else read(q)
        for m in re.finditer(r"\{%\s*url\s*'projects_edit'[^}]*%\}", t):
            tail = t[m.end():m.end() + 20]
            if tail.startswith('?from=') or tail.startswith('?from_gantt='):
                named += 1
            else:
                bare.append('%s @ %d: %r'
                            % (alv_tree.rel(q), m.start(), tail))
    if bare:
        refuse('a link reaches the Project Edit screen without saying '
               'where from:\n   ' + '\n   '.join(bare))
    if named != 4:
        refuse('expected 4 links naming an origin, found %d' % named)

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_project_origin.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'PJ-1, 15 Oct 2026 - this round own suite. A project '
                  'edit learns which of three pages opened it, after '
                  'Demetri said Back from the Projects page took him to '
                  'the Project Details screen.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'PJ-1, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # the two markup censuses that counted the duplicate Back
    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_BAR, N_ROW, N_MODAL = %d, 110, 95',
                  BAR_WAS, BAR_NOW,
                  'PJ-1, 15 Oct 2026 - projects_edit carried its Back '
                  'control twice, behind an if on from_gantt. This '
                  'census does not resolve a branch, so it counted both '
                  'arms; one Back control now, and one count.',
                  '%s (the bar census)' % BH)

    p = os.path.join(root, HL)
    out[p] = bump(read(p), 'LABELS_TOTAL = %d', LBL_WAS, LBL_NOW,
                  'PJ-1, 15 Oct 2026 - the same duplicate Back, counted '
                  'by its label span. The check below it compares the '
                  'backup and so falls by one with it.',
                  '%s (the label census)' % HL)

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('PJ-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   %d link(s) name an origin' % named)
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('PJ-1 applied.')
    print('   PROJECT_ORIGINS beside TL-2 TASK_ORIGINS - a key chosen')
    print('         from a map, never a URL taken at face value')
    print('   Back returns to the page the edit was opened from, and')
    print('         Update Project follows the same rule')
    print('   all %d link(s) to that screen now say where they came' % named)
    print('         from, and the gate refuses a fifth that does not')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
