# -*- coding: utf-8 -*-
"""TL-2 - EDIT A TASK FROM THE TASK LIST AND YOU LAND ON THE PROJECT

Demetri, 4 Oct 2026: "Within the Task List, if I press to Edit a Task or
Subtask, and I then press the Back Button or the Update Task button, then
I need to be taken back to the Task List, not the Project."

==========================================================================
THE MECHANISM WAS ALREADY THERE, WITH ONE ORIGIN IN IT
==========================================================================
    pages/views/projects.py:521    if from_gantt:
                                       return redirect('project_gantt', ...)
    pages/views/projects.py:524    else:
                                       return redirect('projects_detail', ...)

The Gantt chart sets from_gantt=true on its links and comes back to
itself. Nothing else sets anything, so EVERY other route falls to the
else and lands on the Project - including the four links on the Task
List. Back did not ignore where you came from; it was never told.

==========================================================================
IT CARRIES THE LIST YOU WERE READING, NOT JUST THE PAGE
==========================================================================
Demetri's call. You arrive at the Task List having chosen an assignee and
a language - that is what the Generate Task List modal is for. Returning
you to that project's DEFAULT list (everyone, English) would be a second
version of the same complaint: still not the page you left.

So the origin carries three things, and the Back button rebuilds them:

    ?from=task_list&assigned_to=Demetri&language=greek

==========================================================================
A KEY, NOT A URL
==========================================================================
The obvious shape for this is ?next=/some/path/ and it is an open
redirect: a link can be mailed that opens an edit on a real task and then
lands the user anywhere at all. What travels here is a KEY - 'gantt' or
'task_list' - and the key chooses from a map this module wrote down
itself. An unrecognised key is not an error and not obeyed; it falls back
to the Project, which is where the page went before this round.

The two values that ride along are rebuilt, not echoed: language has to
be one of two words, and assigned_to is re-encoded on the way out.

==========================================================================
DELETE FOLLOWS EDIT
==========================================================================
Demetri's call. Delete Task had no origin awareness at all - a Back, a
Cancel and a confirmed delete, all three hard-wired to the Project. One
rule serves both pages; a Delete that behaved differently from an Edit
would only have been the next bug report.

Delete's form posts to the current URL rather than a named one, so its
confirmed path carries the origin with no change to the markup.

Backups: .bak_taskorigin. Idempotent. --check writes nothing.
"""
import os
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_taskorigin'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

VIEW = os.path.join(ROOT, 'pages', 'views', 'projects.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'projects')
LIST_PAGE = os.path.join(TPL, 'project_task_list.html')
EDIT_PAGE = os.path.join(TPL, 'project_tasks_edit.html')
DEL_PAGE = os.path.join(TPL, 'project_tasks_delete.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('TL2: %s is not a byte copy' % bak)


def swap(nl, old, new, what, times=1):
    c = nl.count(old)
    if c != times:
        raise SystemExit('TL2: %s appears %d times, not %d' % (what, c, times))
    return nl.replace(old, new)


print('=' * 74)
print('TL-2 - BACK RETURNS YOU TO THE LIST YOU LEFT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE VIEW: ONE ORIGIN RULE, SERVING EDIT AND DELETE.
# ==========================================================================
v, vraw = read(VIEW)
vnl = v.replace('\r\n', '\n')

HELPERS = '''

# --------------------------------------------------------------------------- #
# TL-2, 4 Oct 2026 - WHERE AN EDIT CAME FROM
# --------------------------------------------------------------------------- #
# Demetri: "Within the Task List, if I press to Edit a Task or Subtask,
# and I then press the Back Button or the Update Task button, then I need
# to be taken back to the Task List, not the Project."
#
# The machinery existed with exactly one origin in it - the Gantt chart
# sets from_gantt=true and returns to itself, and everything else fell to
# an else branch pointing at the Project. These three functions are that
# else branch grown a second entry, and they serve Edit and Delete alike.
#
# WHAT TRAVELS IS A KEY, NOT A URL. ?next=/anywhere/ taken at face value
# is an open redirect; a key chooses from a map written down here, and an
# unrecognised one falls back to the Project exactly as before.
TASK_ORIGINS = {
    'gantt': 'project_gantt',
    'task_list': 'project_task_list',
}

TASK_ORIGIN_LABELS = {
    'gantt': 'Back to Gantt Chart',
    'task_list': 'Back to Task List',
}


def task_origin(request):
    """The key naming the page this edit or delete was opened from, or ''.

    from_gantt=true is still read: the Gantt chart has linked that way
    since long before this round and its links are not being rewritten.
    """
    key = request.GET.get('from', '')
    if key in TASK_ORIGINS:
        return key
    return 'gantt' if request.GET.get('from_gantt') else ''


def task_origin_query(key, assigned_to='', language=''):
    """The query string that carries an origin, and the Task List's own
    state with it.

    Returning someone to a project's DEFAULT task list - everyone,
    English - would be the same complaint in a second costume: still not
    the page they left. Both values are REBUILT here rather than passed
    along, so language can only ever be one of two words.
    """
    if key not in TASK_ORIGINS:
        return ''
    bits = [('from', key)]
    if assigned_to:
        bits.append(('assigned_to', assigned_to))
    if language == 'greek':
        bits.append(('language', 'greek'))
    return urlencode(bits)


def task_origin_back(request, project):
    """(url, title) for the Back control on an edit or a delete page."""
    key = task_origin(request)
    if not key:
        return (reverse('projects_detail', args=[project.project_id]),
                'Back to Project')
    url = reverse(TASK_ORIGINS[key], args=[project.project_id])
    q = task_origin_query(key,
                          request.GET.get('assigned_to', '').strip(),
                          request.GET.get('language', ''))
    # The origin's own key is not needed on the way BACK - the list does
    # not care where its reader has been - so only the state travels.
    q = '&'.join(p for p in q.split('&') if not p.startswith('from='))
    return (url + ('?' + q if q else ''), TASK_ORIGIN_LABELS[key])

'''

if 'TL-2, 4 Oct 2026' in vnl:
    print('  views/projects.py          already carries the origin')
else:
    # reverse() and urlencode() are what the helpers need and neither is
    # imported today.
    vnl = swap(vnl,
               'from django.shortcuts import get_object_or_404, redirect, render\n',
               'from django.shortcuts import get_object_or_404, redirect, render\n'
               'from django.urls import reverse\n',
               'the shortcuts import')
    vnl = swap(vnl,
               'from django.utils import timezone\n',
               'from django.utils import timezone\n'
               'from django.utils.http import urlencode\n',
               'the timezone import')
    vnl = swap(vnl,
               '\n\n@login_required\n@permission_required(\'auth.can_edit_projects\', raise_exception=True)\ndef project_tasks_edit(request, project_id, task_id):',
               HELPERS + '\n@login_required\n@permission_required(\'auth.can_edit_projects\', raise_exception=True)\ndef project_tasks_edit(request, project_id, task_id):',
               'the edit view header')

    # --- EDIT: the redirect after a save, and the context ------------------
    vnl = swap(vnl,
               """            # Redirect based on where we came from
            if from_gantt:
                return redirect('project_gantt', project_id=project.project_id)
            else:
                return redirect('projects_detail', project_id=project.project_id)
""",
               """            # TL-2 - Update Task returns you to the page you opened
            # the edit from, and to the list you were actually reading.
            return redirect(task_origin_back(request, project)[0])
""",
               'the edit redirect')

    vnl = swap(vnl,
               """        'from_gantt': from_gantt,
    }

    return render(request, 'projects/project_tasks_edit.html', context)""",
               """        'from_gantt': from_gantt,
        # TL-2 - Back, and the form's own action, which has to keep the
        # origin across a save that fails validation and re-renders.
        'back_url': back_url,
        'back_title': back_title,
        'form_action': (reverse('project_tasks_edit',
                                args=[project.project_id, task.task_id])
                        + ('?' + origin_query if origin_query else '')),
    }

    return render(request, 'projects/project_tasks_edit.html', context)""",
               'the edit context')

    vnl = swap(vnl,
               """    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', False)
""",
               """    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', False)

    # TL-2 - and from the Task List, which never had a way to say so.
    back_url, back_title = task_origin_back(request, project)
    origin_query = task_origin_query(task_origin(request),
                                     request.GET.get('assigned_to', '').strip(),
                                     request.GET.get('language', ''))
""",
               'the edit from_gantt read')

    # --- DELETE: the same rule ---------------------------------------------
    vnl = swap(vnl,
               """    if request.method == 'POST':
        task.delete()
        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
""",
               """    # TL-2 - Delete follows Edit. This page had no origin awareness
    # at all: a Back, a Cancel and a confirmed delete, all three
    # hard-wired to the Project. Its form posts to the CURRENT url, so
    # the confirmed path carries the origin without a change to the
    # markup - only the three links needed one.
    back_url, back_title = task_origin_back(request, project)

    if request.method == 'POST':
        task.delete()
        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
""",
               'the delete POST branch')

    vnl = swap(vnl,
               """        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
        return redirect('projects_detail', project_id=project_id)

    context = {
        'project': project,
        'task': task,
    }

    return render(request, 'projects/project_tasks_delete.html', context)""",
               """        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
        return redirect(back_url)

    context = {
        'project': project,
        'task': task,
        'back_url': back_url,
        'back_title': back_title,
    }

    return render(request, 'projects/project_tasks_delete.html', context)""",
               'the delete redirect and context')

    # --- AND THE LIST ITSELF HANDS ITS FOUR LINKS THE ORIGIN ---------------
    vnl = swap(vnl,
               """        'completion_percentage': completion_percentage,
        'current_date': timezone.now(),
    }

    return render(request, 'projects/project_task_list.html', context)""",
               """        'completion_percentage': completion_percentage,
        'current_date': timezone.now(),
        # TL-2 - what the four row links append, so an edit opened from
        # here knows to come back here, to THIS list: same assignee,
        # same language.
        'origin_query': task_origin_query('task_list', assigned_to, language),
    }

    return render(request, 'projects/project_task_list.html', context)""",
               'the task list context')

    out = vnl.replace('\n', '\r\n') if CRLF.get(VIEW) else vnl
    if not CHECK:
        back_up(VIEW, vraw)
        write(VIEW, out)
    print('  views/projects.py          one origin rule, edit and delete')

# ==========================================================================
# 2. THE TASK LIST SAYS WHERE ITS FOUR LINKS CAME FROM.
# ==========================================================================
t, traw = read(LIST_PAGE)
tnl = t.replace('\r\n', '\n')

if 'TL-2, 4 Oct 2026' in tnl:
    print('  project_task_list.html     already names itself on its links')
else:
    NOTE = """            {# TL-2, 4 Oct 2026 - THE LINK SAYS WHERE IT CAME FROM. #}
            {# Demetri: "if I press to Edit a Task or Subtask, and I   #}
            {# then press the Back Button or the Update Task button,   #}
            {# then I need to be taken back to the Task List, not the  #}
            {# Project." origin_query carries this list's assignee and #}
            {# language too, so Back returns the list that was being   #}
            {# read and not the project's default one.                 #}
"""
    tnl = swap(tnl,
               """            <td class="desktop-action-cell cell-actions">
""",
               NOTE + """            <td class="desktop-action-cell cell-actions">
""",
               'the desktop action cell')
    # All four links, desktop and phone, edit and delete. Counted: a
    # change that reached three of four would leave one route landing on
    # the Project and read exactly like the bug not being fixed.
    for name, n in (('project_tasks_edit', 2), ('project_tasks_delete', 2)):
        tnl = swap(
            tnl,
            "{%% url '%s' project.project_id item.task_obj.task_id %%}\"" % name,
            "{%% url '%s' project.project_id item.task_obj.task_id %%}?{{ origin_query }}\"" % name,
            'the %s links' % name, times=n)
    out = tnl.replace('\n', '\r\n') if CRLF.get(LIST_PAGE) else tnl
    if not CHECK:
        back_up(LIST_PAGE, traw)
        write(LIST_PAGE, out)
    print('  project_task_list.html     4 links carry the origin')

# ==========================================================================
# 3. THE EDIT PAGE: ONE BACK CONTROL, AND A FORM THAT KEEPS THE ORIGIN.
# ==========================================================================
e, eraw = read(EDIT_PAGE)
enl = e.replace('\r\n', '\n')

if 'TL-2, 4 Oct 2026' in enl:
    print('  project_tasks_edit.html    already follows the origin')
else:
    enl = swap(enl,
               """<!-- Action Buttons: Back+1 (Gantt-aware) -->
<div class="page-action-buttons">
  <button type="submit" form="taskForm" class="btn action-primary">
    <i class="fas fa-save"></i> Update Task
  </button>
  {% if from_gantt %}
    <a href="{% url 'project_gantt' project.project_id %}" class="btn action-back" title="Back to Gantt Chart">
      <i class="fas fa-arrow-left"></i>
      <span class="action-back-label">Back</span>
    </a>
  {% else %}
    <a href="{% url 'projects_detail' project.project_id %}" class="btn action-back" title="Back to Project">
      <i class="fas fa-arrow-left"></i>
      <span class="action-back-label">Back</span>
    </a>
  {% endif %}
</div>
""",
               """<!-- Action Buttons: Back+1. TL-2, 4 Oct 2026 - the branch that
     used to stand here knew one origin, the Gantt chart, and sent
     everybody else to the Project. The view resolves it now, from a
     map of origins, so a third one is a line there and nothing here. -->
<div class="page-action-buttons">
  <button type="submit" form="taskForm" class="btn action-primary">
    <i class="fas fa-save"></i> Update Task
  </button>
  <a href="{{ back_url }}" class="btn action-back" title="{{ back_title }}">
    <i class="fas fa-arrow-left"></i>
    <span class="action-back-label">Back</span>
  </a>
</div>
""",
               'the edit action bar')

    enl = swap(enl,
               """      {% if from_gantt %}
        action="{% url 'project_tasks_edit' project.project_id task.task_id %}?from_gantt=true"
      {% else %}
        action="{% url 'project_tasks_edit' project.project_id task.task_id %}"
      {% endif %}>""",
               """      {# TL-2 - the origin has to survive a save that fails validation #}
      {# and re-renders this page, or Back changes meaning halfway      #}
      {# through an edit.                                               #}
      action="{{ form_action }}">""",
               'the edit form action')

    out = enl.replace('\n', '\r\n') if CRLF.get(EDIT_PAGE) else enl
    if not CHECK:
        back_up(EDIT_PAGE, eraw)
        write(EDIT_PAGE, out)
    print('  project_tasks_edit.html    Back and the form follow the origin')

# ==========================================================================
# 4. THE DELETE PAGE: BACK AND CANCEL.
# ==========================================================================
d, draw = read(DEL_PAGE)
dnl = d.replace('\r\n', '\n')

if 'TL-2, 4 Oct 2026' in dnl:
    print('  project_tasks_delete.html  already follows the origin')
else:
    dnl = swap(dnl,
               """  <a href="{% url 'projects_detail' project.project_id %}" class="btn action-back" title="Back to Project">
    <i class="fas fa-arrow-left"></i>
    <span class="action-back-label">Back</span>
  </a>""",
               """  {# TL-2, 4 Oct 2026 - this page had no origin awareness at all:  #}
  {# a Back, a Cancel and a confirmed delete, all three hard-wired   #}
  {# to the Project. Delete follows Edit now. The form below posts   #}
  {# to the CURRENT url, so the confirmed path needed no change.     #}
  <a href="{{ back_url }}" class="btn action-back" title="{{ back_title }}">
    <i class="fas fa-arrow-left"></i>
    <span class="action-back-label">Back</span>
  </a>""",
               'the delete action bar')

    dnl = swap(dnl,
               """      <a href="{% url 'projects_detail' project.project_id %}" class="btn action-secondary form-footer-cancel">""",
               """      <a href="{{ back_url }}" class="btn action-secondary form-footer-cancel">""",
               'the delete Cancel')

    out = dnl.replace('\n', '\r\n') if CRLF.get(DEL_PAGE) else dnl
    if not CHECK:
        back_up(DEL_PAGE, draw)
        write(DEL_PAGE, out)
    print('  project_tasks_delete.html  Back and Cancel follow the origin')

# ==========================================================================
# 5. A SUITE THAT WAS READING THE LIVE FILE AGAINST A FROZEN BACKUP.
# ==========================================================================
# test_entry_sections section 4 asks that its round changed only what it
# said it would - same controls, same order, same Django tags. True when
# it was written, and it reads
#
#     before, after = read(bak), read(p)
#
# so `after` is the file AS IT IS NOW, not as that round left it. This
# round removes an {% if from_gantt %} branch from project_tasks_edit,
# which is a tag that round never touched, and a true claim about a
# round four weeks old started failing.
#
# THE SAME DEFECT AS test_passport_filter, YESTERDAY: `SRC = now(PAGE)`
# beside `V = read(VIEW)`. alv_rounds.as_left_by exists for exactly this,
# and the file already imports it forty lines further down - for its
# other section.
REPAIRS = [
    ('test_entry_sections.py',
     """        before, after = read(bak), read(p)
        a, b = fields(before), fields(after)""",
     """        # TL-2, 4 Oct 2026 - AS SECTION 4 LEFT IT, not as it is now.
        # This read the LIVE file, so any later round touching one of
        # these pages broke a true claim about a round that had done
        # its job: TL-2 took an {% if from_gantt %} branch out of
        # project_tasks_edit and the Django-tag census stopped
        # matching. as_left_by is what answers "as that round left it",
        # and this file already imports it for its other section.
        try:
            from alv_rounds import as_left_by as _alb4
        except Exception:
            _alb4 = None
        after = _alb4(p, SUFFIX4, read) if _alb4 else read(p)
        before = read(bak)
        a, b = fields(before), fields(after)"""),
]

for name, old_t, new_t in REPAIRS:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print('  %-42s not on disk - skipped' % name)
        continue
    t2, raw2 = read(path)
    n2 = t2.replace('\r\n', '\n')
    if 'TL-2, 4 Oct 2026' in n2:
        print('  %-42s already repaired' % name)
        continue
    c = n2.count(old_t)
    if c != 1:
        raise SystemExit('TL2: %s - the claim to repair appears %d times, '
                         'not once' % (name, c))
    n2 = n2.replace(old_t, new_t)
    out2 = n2.replace('\n', '\r\n') if CRLF.get(path) else n2
    if not CHECK:
        back_up(path, raw2)
        write(path, out2)
    print('  %-42s reads the file as its round left it' % name)

print('=' * 74)
print('TL-2 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
