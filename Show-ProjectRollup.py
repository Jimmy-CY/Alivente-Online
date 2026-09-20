"""Show-ProjectRollup.py - which parent tasks are out of date with their
   own subtasks, and by how much.

    python Show-ProjectRollup.py              every project
    python Show-ProjectRollup.py --stale      only the parents that differ
    python Show-ProjectRollup.py --project 7  one project by id

Run from the repo root. READ-ONLY - it opens a database connection, reads,
and writes nothing. No task, project or row is saved by this tool.

WHY IT EXISTS

  A Project is kept up to date from its tasks: update_project_from_tasks()
  writes the six calculated values onto the stored columns, and a post_save
  and post_delete signal on ProjectTask fires it. A PARENT TASK has all six
  matching get_calculated_* methods and nothing that calls them - no
  updater, no signal, and ProjectTask.save() is two lines that roll nothing
  up. So a parent task's stored task_status, dates and costs are whatever
  was written when it was created.

  The screens disagree as a result. project_tasks_delete.html reads the
  STORED status four times and the calculated one never; projects_detail.html
  reads both on the same page; project_tasks_edit.html reads only the
  calculated ones, which is why the screen that advertises the behaviour is
  the one screen that has it.

  THIS TOOL IS THE EVIDENCE, and it is deliberately the first thing built.
  A fix here writes to live rows, so the question "how many parents are
  stale, and what would change" should be answered from YOUR data before
  anything is agreed, not from a reading of the source. See
  claude/projects_auto_calculated_rollup.md.

WHAT IT ALSO CHECKS, AND WHY THAT MATTERS MORE THAN THE COUNT

  ProjectTask.clean() rejects a task whose status is Completed with no
  actual completion date, and one whose expected completion is not after its
  start. ProjectTask.save() calls full_clean() unconditionally - it has no
  skip_validation escape hatch, unlike Project.save(). So a rollup that sets
  those six values would run full_clean() on rows that may predate the
  validations, INSIDE A SIGNAL, which is the worst place to discover it.

  For every parent it would change, this tool runs full_clean() on a COPY
  held in memory and reports whether the save would have raised. That is the
  number that decides whether the fix needs the escape hatch or just a
  backfill.

  It also reports NESTING DEPTH. parent_task is a self-referencing
  ForeignKey with no depth constraint in clean(), so the model permits a
  subtask of a subtask even though the screens only offer one level. A
  rollup signal that assumes one level would silently miss a generation, so
  the guard has to be a depth check and this says what depth the data is.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import sys

ARGS = sys.argv[1:]
ONLY_STALE = '--stale' in ARGS
ONE = None
if '--project' in ARGS:
    i = ARGS.index('--project')
    if i + 1 < len(ARGS):
        ONE = ARGS[i + 1]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django                                                    # noqa: E402
django.setup()                                                   # noqa: E402

from django.core.exceptions import ValidationError               # noqa: E402
from pages.models import Project, ProjectTask                    # noqa: E402

# The six the Project level already rolls up, and the accessor for each.
PAIRS = [
    ('task_status', 'get_calculated_status'),
    ('task_start_date', 'get_calculated_start_date'),
    ('task_expected_completion_date', 'get_calculated_expected_completion'),
    ('task_actual_completion_date', 'get_calculated_actual_completion'),
    ('task_budgeted_cost', 'get_calculated_budgeted_cost'),
    ('task_actual_cost', 'get_calculated_actual_cost'),
]
BAR = '=' * 78


def show(v):
    return '(empty)' if v in (None, '') else str(v)


def same(a, b):
    """Stored and calculated agree. Decimal('0.00') and 0 are the same
    number and a mismatch reported between them would be noise."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def depth_of(task, seen=None):
    """How many parents this task has above it. The model allows a subtask
    of a subtask; the screens do not create one. This says which is true of
    the data - and guards against a cycle rather than recursing for ever,
    because a self-FK can hold one."""
    seen, d, cur = set(), 0, task
    while cur.parent_task_id is not None:
        if cur.task_id in seen:
            return -1
        seen.add(cur.task_id)
        cur = cur.parent_task
        d += 1
    return d


qs = Project.objects.all().prefetch_related('projecttask_set__subtasks')
if ONE:
    qs = qs.filter(project_id=ONE)

parents = stale = would_raise = 0
deepest = 0
cycles = []
rows = []

for project in qs:
    for task in project.projecttask_set.all():
        if task.parent_task_id is not None:
            d = depth_of(task)
            if d < 0:
                cycles.append(task.task_id)
            else:
                deepest = max(deepest, d)
            continue
        subs = list(task.subtasks.all())
        if not subs:
            continue          # no subtasks, so nothing to roll up
        parents += 1
        diffs = []
        for field, accessor in PAIRS:
            stored = getattr(task, field)
            calc = getattr(task, accessor)()
            if not same(stored, calc):
                diffs.append((field, stored, calc))
        if not diffs:
            if not ONLY_STALE:
                rows.append((project, task, len(subs), [], None))
            continue
        stale += 1

        # WOULD THE SAVE HAVE RAISED? Run full_clean on a COPY. Nothing is
        # written: the object is never saved, and the one read from the
        # database is left untouched.
        probe = ProjectTask.objects.get(pk=task.pk)
        for field, _stored, calc in diffs:
            setattr(probe, field, calc)
        err = None
        try:
            probe.full_clean()
        except ValidationError as e:
            err = '; '.join(
                '%s: %s' % (k, ' '.join(v))
                for k, v in (getattr(e, 'message_dict', {}) or
                             {'': e.messages}).items())
            would_raise += 1
        except Exception as e:                       # noqa: BLE001
            err = '%s: %s' % (type(e).__name__, e)
            would_raise += 1
        rows.append((project, task, len(subs), diffs, err))

print('\n' + BAR)
print('PARENT TASKS vs THEIR OWN SUBTASKS - read-only')
print(BAR)

for project, task, nsubs, diffs, err in rows:
    print('\n  %s / %s   (%d subtask(s))'
          % (str(project)[:32], str(task.task_name)[:34], nsubs))
    if not diffs:
        print('      up to date')
        continue
    for field, stored, calc in diffs:
        print('      %-34s stored %-22s -> would become %s'
              % (field, show(stored)[:22], show(calc)))
    if err:
        print('      !! SAVING THIS WOULD RAISE: %s' % err[:120])

print('\n' + BAR)
print('%d parent task(s) have subtasks' % parents)
print('%d of them disagree with their subtasks' % stale)
print('%d of those would RAISE ValidationError if saved as calculated'
      % would_raise)
print('deepest nesting found: %d level(s) below a main task%s'
      % (deepest, '  (the screens only create 1)' if deepest <= 1 else
         '  <-- DEEPER THAN THE SCREENS CREATE'))
if cycles:
    print('!! %d task(s) sit in a parent cycle: %s'
          % (len(cycles), ', '.join(str(c) for c in cycles[:6])))
print(BAR)
print('Nothing was written. This tool only reads.')
if would_raise:
    print('')
    print('ProjectTask.save() calls full_clean() unconditionally and has no')
    print('skip_validation argument, so the %d above would raise inside the'
          % would_raise)
    print('signal that rolled them up. That is the escape hatch the fix')
    print('needs, and this is the number that says so.')
print(BAR)
