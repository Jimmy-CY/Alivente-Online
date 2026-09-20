"""test_project_rollup.py - a parent task is kept in line with its subtasks.

    python test_project_rollup.py

Run from the repo root, after apply_project_rollup.py.

WHAT THIS SUITE IS FOR

  * SECTION 2 IS THE ONE THAT EARNS ITS KEEP, because it RUNS the thing
    against the real database and asserts the parent's STORED COLUMNS
    changed - not its accessors. The accessors passed before this round and
    pass after it; they were never the fault. What was missing is anything
    that wrote their answers down.

    It works on a real parent that already has subtasks, inside a
    transaction it ROLLS BACK, so it exercises the real shapes without
    constructing objects whose required fields this suite would have to
    guess at, and without leaving a row behind. If there is no such parent
    it says so and skips, rather than passing on an empty corpus.

  * SECTION 3 IS THE CONTROL, and without it section 2 measures nothing. It
    disconnects the receiver and requires the same sequence to FAIL to
    update the stored columns. A guard whose control cannot fail is not a
    guard, and this repo has shipped three of those.

  * SECTION 4 counts the saves one subtask save causes. The walk goes up a
    self-referencing ForeignKey, which can hold a cycle, so "it terminates"
    is a claim worth measuring rather than reasoning about.

  * SECTION 5 reports every screen that still reads a STORED status, date or
    cost for a task that can have subtasks. Reported, not failed: making all
    of them read the accessor is a separate round, and the stored columns
    are correct from now on anyway.

WHAT IT CANNOT DO, SAID FIRST

  It cannot tell you the rollup RULES are right - that completed plus
  completed is completed, or that a parent's budget is the sum of its
  children rather than its own. Those came with get_calculated_* and this
  round did not touch them. What it holds is that the answers are written
  down instead of computed for one screen.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django                                                    # noqa: E402
django.setup()                                                   # noqa: E402

from django.db import transaction                                # noqa: E402
from django.db.models.signals import post_save                   # noqa: E402
from pages.models import ProjectTask                             # noqa: E402
from pages import signals as alv_signals                         # noqa: E402

PASS = FAIL = SKIP = 0
FAILED = []
BAR = '=' * 74

ROLLED = ('task_status', 'task_start_date',
          'task_expected_completion_date', 'task_actual_completion_date',
          'task_budgeted_cost', 'task_actual_cost')


def head_(t):
    print('\n' + '-' * 74)
    print(' ' + t)
    print('-' * 74)


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


class Rollback(Exception):
    """Raised to end an atomic block without keeping anything."""


def a_parent_with_subtasks():
    for t in (ProjectTask.objects
              .filter(parent_task__isnull=True)
              .prefetch_related('subtasks')):
        subs = list(t.subtasks.all())
        if subs:
            return t, subs
    return None, None


# ---------------------------------------------------------------------- 1
head_('1. THE CODE SAYS WHAT THE ROUND SAID IT WOULD')

models_src = read(os.path.join('pages', 'models.py'))
signals_src = read(os.path.join('pages', 'signals.py'))

check('ProjectTask has update_from_subtasks()',
      'def update_from_subtasks' in models_src)
i = models_src.find('def update_from_subtasks')
block = models_src[i:i + 2500] if i >= 0 else ''
for field, accessor in (
        ('task_status', 'get_calculated_status'),
        ('task_start_date', 'get_calculated_start_date'),
        ('task_expected_completion_date', 'get_calculated_expected_completion'),
        ('task_actual_completion_date', 'get_calculated_actual_completion'),
        ('task_budgeted_cost', 'get_calculated_budgeted_cost'),
        ('task_actual_cost', 'get_calculated_actual_cost')):
    check('  it writes %-32s from %s' % (field, accessor),
          re.search(r'self\.%s\s*=\s*\(?\s*\n?\s*self\.%s\(\)'
                    % (field, accessor), block) is not None)
check('  and it does NOT save - the caller does, as the project updater does',
      bool(block) and '.save(' not in block)
check('  CONTROL: the method body really was isolated, not a fixed slice',
      block.count('def ') == 1, '%d def(s) in it' % block.count('def '))
check('  CONTROL: the project updater it mirrors is still there',
      'def update_project_from_tasks' in models_src)

check('the signal walks up before it rolls the project',
      signals_src.count('_roll_up_parents(instance)') == 2,
      '%d call(s)' % signals_src.count('_roll_up_parents(instance)'))
check('  a depth cap stops a cycle a self-FK could hold',
      'MAX_TASK_DEPTH' in signals_src)
check('  a re-entrancy guard stops the rollup re-entering itself',
      '_ROLLING_UP' in signals_src)
check('  and there is NO skip_validation on the task save - a row that '
      'cannot validate is left alone',
      'parent.save(skip_validation' not in signals_src)


# ---------------------------------------------------------------------- 2
head_('2. RUN IT - the STORED columns move, and the change is rolled back')

parent, subs = a_parent_with_subtasks()
if parent is None:
    skip('the rollup runs', 'no parent task in this database has subtasks')
else:
    print('        using %s / %s with %d subtask(s)'
          % (parent.project, parent.task_name, len(subs)))
    before = {f: getattr(parent, f) for f in ROLLED}
    moved = []
    try:
        with transaction.atomic():
            sub = subs[0]
            sub.task_status = ('In Progress'
                               if sub.task_status != 'In Progress'
                               else 'Pending')
            if sub.task_status != 'Completed':
                sub.task_actual_completion_date = None
            sub.save()

            fresh = ProjectTask.objects.get(pk=parent.pk)
            after = {f: getattr(fresh, f) for f in ROLLED}
            moved = [f for f in ROLLED
                     if str(before[f]) != str(after[f])]
            raise Rollback
    except Rollback:
        pass

    check('saving a subtask changed the parent\'s stored columns',
          bool(moved), 'none of %s moved' % ', '.join(ROLLED))
    if moved:
        print('        moved: %s' % ', '.join(moved))
    again = ProjectTask.objects.get(pk=parent.pk)
    check('  and the transaction rolled back, so nothing was kept',
          all(str(getattr(again, f)) == str(before[f]) for f in ROLLED))


# ---------------------------------------------------------------------- 3
head_('3. THE CONTROL - with the receiver disconnected, nothing moves')

if parent is None:
    skip('the control', 'no parent task in this database has subtasks')
else:
    post_save.disconnect(alv_signals.update_project_on_task_save,
                         sender=ProjectTask)
    try:
        moved_off = []
        try:
            with transaction.atomic():
                sub = subs[0]
                sub.task_status = ('In Progress'
                                   if sub.task_status != 'In Progress'
                                   else 'Pending')
                if sub.task_status != 'Completed':
                    sub.task_actual_completion_date = None
                sub.save()
                fresh = ProjectTask.objects.get(pk=parent.pk)
                moved_off = [f for f in ROLLED
                             if str(before[f]) != str(getattr(fresh, f))]
                raise Rollback
        except Rollback:
            pass
        check('CONTROL: without the receiver the parent does NOT change',
              not moved_off,
              'moved anyway: %s' % ', '.join(moved_off))
    finally:
        post_save.connect(alv_signals.update_project_on_task_save,
                          sender=ProjectTask)
    def _connected():
        for _key, ref in post_save.receivers:
            fn = ref() if hasattr(ref, '__call__') and not hasattr(
                ref, '__name__') else ref
            if fn is alv_signals.update_project_on_task_save:
                return True
        return False
    check('  and the receiver is connected again', _connected())


# ---------------------------------------------------------------------- 4
head_('4. THE WALK TERMINATES - counted, not reasoned about')

if parent is None:
    skip('the walk terminates', 'no parent task with subtasks')
else:
    saves = {'n': 0}
    real = ProjectTask.save

    def counting_save(self, *a, **kw):
        saves['n'] += 1
        return real(self, *a, **kw)

    ProjectTask.save = counting_save
    try:
        try:
            with transaction.atomic():
                sub = subs[0]
                sub.task_status = ('In Progress'
                                   if sub.task_status != 'In Progress'
                                   else 'Pending')
                if sub.task_status != 'Completed':
                    sub.task_actual_completion_date = None
                sub.save()
                raise Rollback
        except Rollback:
            pass
    finally:
        ProjectTask.save = real
    # one for the subtask, one per ancestor. Anything unbounded shows here.
    check('one subtask save causes a bounded number of task saves',
          1 <= saves['n'] <= 12, '%d save(s)' % saves['n'])
    print('        %d task save(s) for a tree %d level(s) deep'
          % (saves['n'], 1))


# ---------------------------------------------------------------------- 5
head_('5. WHO STILL READS A STORED COLUMN - reported, not failed')

PAIRS = {
    'task_status': 'get_calculated_status',
    'task_budgeted_cost': 'get_calculated_budgeted_cost',
    'task_actual_cost': 'get_calculated_actual_cost',
    'task_start_date': 'get_calculated_start_date',
    'task_expected_completion_date': 'get_calculated_expected_completion',
    'task_actual_completion_date': 'get_calculated_actual_completion',
}
T = os.path.join('pages', 'templates', 'projects')
found = []
if os.path.isdir(T):
    for n in sorted(os.listdir(T)):
        if not n.endswith('.html'):
            continue
        text = read(os.path.join(T, n))
        for f in PAIRS:
            stored = len(re.findall(
                r'(?<![\w.])(?:task|t|subtask|main_task)\.%s(?![\w])' % f,
                text))
            calc = len(re.findall(PAIRS[f], text))
            if stored and not calc:
                found.append('%s reads %s stored (%d) and never calculated'
                             % (n, f, stored))
print('        %d screen/field pair(s) read only the stored column.' % len(found))
for f in found:
    print('          %s' % f)
print('')
print('        Those are correct FROM NOW ON, because the column is')
print('        maintained. Before this round they were stale. Moving them')
print('        onto the accessor is a tidy, not a fix, and it is not this')
print('        round.')
check('this is a report, and it ran', True, '%d pair(s)' % len(found))


# ---------------------------------------------------------------------- 6
head_('6. IT IS ON THE GATE')
PS1 = 'Push-PendingChanges.ps1'
if not os.path.isfile(PS1):
    skip('on the gate', '%s not on disk' % PS1)
else:
    check('%s runs this suite' % PS1,
          "'test_project_rollup.py'" in read(PS1))


print('\n' + BAR)
print('%d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
for f in FAILED:
    print('  -  %s' % f)
print(BAR)
print('NOT PROVED HERE: that the rollup RULES are right - that completed')
print('plus completed is completed, or that a parent\'s budget is the sum')
print('of its children. Those came with get_calculated_* and this round')
print('did not touch them. Only that the answers are written down.')
print(BAR)
sys.exit(1 if FAIL else 0)
