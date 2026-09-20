"""apply_project_rollup.py - a parent task is kept in line with its own
   subtasks, the way a project already is with its tasks.

    python apply_project_rollup.py --check     dry run, writes nothing
    python apply_project_rollup.py             apply

Run from the repo root. Idempotent.

THE FAULT, IN ONE LINE

    The rollup exists one level up and was never implemented one level down.

  Project.update_project_from_tasks() writes six calculated values onto the
  stored columns, and a post_save and post_delete signal on ProjectTask
  fires it and saves. A PARENT TASK has all six matching get_calculated_*
  methods and NOTHING THAT CALLS THEM, and ProjectTask.save() is two lines
  that roll nothing up.

  Tick the last subtask Completed and the parent still says In Progress
  everywhere except project_tasks_edit, which renders the accessors into its
  disabled (Auto-calculated) inputs. The one screen that advertises the
  behaviour is the one screen that has it.

WHY NOT JUST READ THE ACCESSOR EVERYWHERE

  Every get_calculated_* falls back to the stored value when a task has no
  subtasks, so the accessor is correct for a parent and a subtask alike and
  reading it is never wrong. But A DATABASE CANNOT CALL A PYTHON METHOD: any
  .filter(task_status=...), .order_by() or Sum() over main tasks reads the
  column, and no read-side change reaches those. The value has to be stored,
  which is what the Project level already decided.

WHAT THIS TOOL CHANGES

  pages/models.py    ProjectTask.update_from_subtasks() - the exact shape of
                     update_project_from_tasks, six assignments and no save.
  pages/signals.py   both receivers walk UP from the task that changed
                     before they roll the project, with a depth check and a
                     re-entrancy guard.
  pages/management/commands/backfill_task_rollup.py
                     DRY BY DEFAULT. The signal cannot reach backwards, so
                     rows stale before today stay stale until somebody saves
                     one of their subtasks.

THREE THINGS MEASURED BEFORE ANY OF IT WAS WRITTEN

  * Show-ProjectRollup.py found 4 of 4 parents stale on the local database -
    every one with an empty start date, an empty expected completion and a
    zero budgeted cost, and one reading Pending while its subtask was under
    way.
  * 0 of them would raise ValidationError if saved as calculated. THAT IS
    WHY THERE IS NO skip_validation ESCAPE HATCH HERE, unlike
    Project.save(). A row that cannot validate should not be written by a
    background rollup; it should be left exactly as it was and reported.
    Run the same tool against production before the backfill - 0 of 4 local
    rows is an encouraging number, not a finished argument.
  * Deepest nesting is 1, which is all the screens offer. The model permits
    more - parent_task is a self-referencing ForeignKey and clean() sets no
    depth limit - so the guard is a DEPTH CHECK rather than an assumption
    that a parent has no parent.

THE ANCHOR HAD TO BE UNIQUE AND NEARLY WAS NOT

  Project.save and ProjectTask.save have byte-identical bodies, so
  `def save(self, *args, **kwargs): self.full_clean(); super().save(...)`
  appears TWICE in models.py. Anchoring on it would have been a coin toss.
  The method above ProjectTask.save is what makes the anchor that class's
  alone, and the count is asserted rather than hoped for.

See claude/projects_auto_calculated_rollup.md.
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

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
SUFFIX = '.bak_rollup'
SUITE = 'test_project_rollup.py'
PS1 = 'Push-PendingChanges.ps1'
CMD_DIR = os.path.join('pages', 'management', 'commands')

problems, report = [], []


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


# ==========================================================================
# 1. pages/models.py - the updater ProjectTask never had
# ==========================================================================
MODELS = os.path.join(ROOT, 'pages', 'models.py')

# THE ANCHOR IS A SPAN, NOT A STRING.
#
# The first version of this matched the three lines of ProjectTask.save
# with the blank line above them, and failed on this file: that blank line
# carries four spaces of trailing whitespace, which does not survive being
# carried through a tool. An anchor that depends on invisible characters is
# not an anchor.
#
# So: find the class, find `def save(` inside THAT class, and insert in
# front of it. Project.save and ProjectTask.save have byte-identical
# bodies - the string appears twice in this file - and asking which class
# a method is in is the question that tells them apart.
def method_start(text, class_name, method):
    """Offset of `    def <method>(` inside `class <class_name>`."""
    i = text.find('class %s' % class_name)
    if i < 0:
        return None
    j = text.find('\nclass ', i + 10)
    j = len(text) if j < 0 else j
    k = text.find('\n    def %s(' % method, i, j)
    return None if k < 0 else k + 1


MODELS_ADD = '''    def update_from_subtasks(self):
        """Write this task's six calculated values onto its stored columns.

        THE EXACT SHAPE OF Project.update_project_from_tasks(), and that is
        the point. A Project is kept up to date from its tasks: that method
        writes calculated to stored, and a post_save and post_delete signal
        on ProjectTask fires it. A PARENT TASK had all six matching
        get_calculated_* methods and NOTHING THAT CALLED THEM. The rollup
        existed one level up and was never implemented one level down.

        What that looked like from outside: tick the last subtask Completed
        and the parent still said In Progress everywhere except
        project_tasks_edit, which renders the accessors into its disabled
        (Auto-calculated) inputs - so the one screen that advertised the
        behaviour was the one screen that had it.

        WHY THE VALUE HAS TO BE STORED AND NOT JUST READ. Every
        get_calculated_* already falls back to the stored value when a task
        has no subtasks, so reading the accessor is never wrong and a
        read-side fix is tempting. But a database cannot call a Python
        method: any .filter(task_status=...), .order_by() or Sum() over main
        tasks reads the column. That is what settles it.

        NO save() HERE - the caller saves, exactly as
        update_project_from_tasks does, so neither can recurse into itself.
        """
        self.task_status = self.get_calculated_status()
        self.task_start_date = self.get_calculated_start_date()
        self.task_expected_completion_date = (
            self.get_calculated_expected_completion())
        self.task_actual_completion_date = (
            self.get_calculated_actual_completion())
        self.task_budgeted_cost = self.get_calculated_budgeted_cost()
        self.task_actual_cost = self.get_calculated_actual_cost()

'''

if not os.path.isfile(MODELS):
    problems.append('pages/models.py not found - run from the repo root')
else:
    src = read(MODELS)
    at = method_start(src, 'ProjectTask', 'save')
    if 'def update_from_subtasks' in src:
        report.append('pages/models.py            already has '
                      'update_from_subtasks()')
        models_new = None
    elif at is None:
        problems.append('pages/models.py: no ProjectTask.save to insert in '
                        'front of')
        models_new = None
    elif method_start(src, 'Project(', 'save') == at:
        problems.append('pages/models.py: the offset found for '
                        'ProjectTask.save is Project.save - the two classes '
                        'are not being told apart')
        models_new = None
    else:
        models_new = src[:at] + MODELS_ADD + src[at:]
        report.append('pages/models.py            + '
                      'ProjectTask.update_from_subtasks()')

# ==========================================================================
# 2. pages/signals.py - the signal walks up as well as out
# ==========================================================================
SIGNALS = os.path.join(ROOT, 'pages', 'signals.py')

SIG_ANCHOR = '@receiver(post_save, sender=ProjectTask)'

SIG_HELPER = '''# ---------------------------------------------------------------------------
# THE PARENT ROLLUP
#
# A Project was kept up to date from its tasks and a PARENT TASK was not.
# Both receivers below now walk UP from the task that changed before they
# roll the project, so completing the last subtask reaches the parent's
# stored columns and not only the accessors one screen happens to call.
#
# DEPTH IS A CHECK, NOT AN ASSUMPTION. parent_task is a self-referencing
# ForeignKey and ProjectTask.clean() sets no depth limit, so the MODEL
# permits a subtask of a subtask even though the screens only ever offer one
# level. Show-ProjectRollup.py measured the live data at depth 1 on
# 20 Sep 2026. A guard written as "the parent has no parent" would be true
# today and silently wrong the day somebody nests deeper, so this walks
# until it runs out of parents - and MAX_TASK_DEPTH stops it if a self-FK
# ever holds a cycle, which one can.
#
# RE-ENTRANCY. Saving a parent fires this same receiver with the parent as
# `instance`. Without a guard it would redo the walk from there, correctly
# but repeatedly. _ROLLING_UP holds the ids this process is mid-way through
# saving, and a receiver that sees its own id returns at once.
MAX_TASK_DEPTH = 10
_ROLLING_UP = set()


def _roll_up_parents(task):
    """Refresh every ancestor of this task, nearest first."""
    seen, current = set(), task
    while current.parent_task_id is not None and len(seen) < MAX_TASK_DEPTH:
        if current.parent_task_id in seen:
            break                      # a cycle: stop rather than spin
        seen.add(current.parent_task_id)
        parent = current.parent_task
        parent.update_from_subtasks()
        _ROLLING_UP.add(parent.pk)
        try:
            # NO skip_validation HERE, DELIBERATELY. ProjectTask.save()
            # calls full_clean(), and a row that cannot validate should not
            # be written by a background rollup - it should fail loudly and
            # stay as it was. Show-ProjectRollup.py reports how many rows
            # would raise before any of this runs; it found none.
            parent.save()
        except Exception as exc:                              # noqa: BLE001
            print('Rollup: task %s did not validate and was left alone: %s'
                  % (parent.pk, exc))
            return
        finally:
            _ROLLING_UP.discard(parent.pk)
        current = parent


'''

SIG_CALL = """    try:
        _roll_up_parents(instance)
        instance.project.update_project_from_tasks()"""

if not os.path.isfile(SIGNALS):
    problems.append('pages/signals.py not found')
    signals_new = None
else:
    src = read(SIGNALS)
    if '_roll_up_parents' in src:
        report.append('pages/signals.py           already walks up')
        signals_new = None
    elif src.count(SIG_ANCHOR) != 1:
        problems.append('pages/signals.py: the post_save receiver appears '
                        '%d time(s), expected 1' % src.count(SIG_ANCHOR))
        signals_new = None
    else:
        text = src.replace(SIG_ANCHOR, SIG_HELPER + SIG_ANCHOR, 1)
        old = """    try:
        instance.project.update_project_from_tasks()"""
        n = text.count(old)
        if n != 2:
            problems.append('pages/signals.py: expected 2 receivers calling '
                            'the project rollup, found %d' % n)
            signals_new = None
        else:
            text = text.replace(old, SIG_CALL)
            # the DELETE receiver must guard too
            text = text.replace(
                'def update_project_on_task_save(sender, instance, **kwargs):'
                '\n    """Update project totals when a task is saved"""',
                'def update_project_on_task_save(sender, instance, **kwargs):'
                '\n    """Update the parent task, then the project."""'
                '\n    if instance.pk in _ROLLING_UP:'
                '\n        return          # this save IS the rollup')
            signals_new = text
            report.append('pages/signals.py           + _roll_up_parents(), '
                          'called by both receivers')

# ==========================================================================
# 3. the backfill, dry by default
# ==========================================================================
COMMAND = '''"""backfill_task_rollup - bring every parent task into line with its
own subtasks.

    python manage.py backfill_task_rollup            DRY RUN, writes nothing
    python manage.py backfill_task_rollup --write    apply

DRY BY DEFAULT, AND THAT IS NOT A COURTESY. This writes to live rows. The
default run prints every row it would change, with the value before and
after, and the --write flag is the only thing that turns it into a write.

WHY IT IS NEEDED AT ALL. From now on the post_save signal keeps a parent in
line with its subtasks. It cannot reach backwards: a parent whose subtasks
were last touched before the signal existed stays stale until somebody
happens to save one of them. On 20 Sep 2026 that was four of four parents on
the local database, every one with an empty start date, an empty expected
completion and a zero budgeted cost.

A ROW THAT WILL NOT VALIDATE IS REPORTED AND LEFT ALONE. ProjectTask.save()
calls full_clean(), and a backfill is no place to decide that a rule does
not apply.
"""
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from pages.models import ProjectTask

FIELDS = ('task_status', 'task_start_date',
          'task_expected_completion_date', 'task_actual_completion_date',
          'task_budgeted_cost', 'task_actual_cost')


def _same(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


class Command(BaseCommand):
    help = 'Bring parent tasks into line with their subtasks (dry by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--write', action='store_true',
            help='actually save. Without this the command only reports.')

    def handle(self, *args, **options):
        write = options['write']
        changed = failed = 0

        qs = (ProjectTask.objects
              .filter(parent_task__isnull=True)
              .select_related('project')
              .prefetch_related('subtasks'))

        for task in qs:
            if not list(task.subtasks.all()):
                continue
            before = {f: getattr(task, f) for f in FIELDS}
            task.update_from_subtasks()
            diffs = [(f, before[f], getattr(task, f))
                     for f in FIELDS if not _same(before[f], getattr(task, f))]
            if not diffs:
                continue
            changed += 1
            self.stdout.write('')
            self.stdout.write('  %s / %s'
                              % (task.project, task.task_name))
            for f, old, new in diffs:
                self.stdout.write('      %-34s %s -> %s'
                                  % (f, old if old not in (None, '')
                                     else '(empty)', new))
            if not write:
                continue
            try:
                task.save()
            except ValidationError as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(
                    '      NOT SAVED - %s' % exc))

        self.stdout.write('')
        if write:
            self.stdout.write(self.style.SUCCESS(
                '%d parent task(s) updated, %d refused by validation'
                % (changed - failed, failed)))
        else:
            self.stdout.write(
                '%d parent task(s) WOULD be updated. Nothing was written.'
                % changed)
            self.stdout.write(
                'Re-run with --write to apply.')
'''

INIT = ('"""Django looks for management commands under this package. It is '
        'empty\non purpose."""\n')

cmd_files = {}
cmd_path = os.path.join(ROOT, CMD_DIR, 'backfill_task_rollup.py')
if os.path.isfile(cmd_path):
    report.append('%-26s already there' % CMD_DIR)
else:
    for d in (os.path.join('pages', 'management'), CMD_DIR):
        ip = os.path.join(ROOT, d, '__init__.py')
        if not os.path.isfile(ip):
            cmd_files[ip] = INIT
    cmd_files[cmd_path] = COMMAND
    report.append('%-26s + backfill_task_rollup.py (dry by default)'
                  % CMD_DIR)

# ==========================================================================
# 4. the gate
# ==========================================================================
GATE_NOTE = """    # A parent task is kept in line with its own subtasks, the way a
    # project already is with its tasks. Its section 2 RUNS against the
    # real database inside a transaction it rolls back, and section 3
    # disconnects the receiver and requires the same sequence to fail -
    # a guard whose control cannot fail is not a guard. Newest, so most
    # likely to be what breaks.
    'test_project_rollup.py'"""

ps1_new = None
if not os.path.isfile(PS1):
    report.append('%-26s not on disk - the suite is not wired' % PS1)
elif SUITE in read(PS1):
    report.append('%-26s already runs %s' % (PS1, SUITE))
else:
    ps1_src = read(PS1)
    i = ps1_src.find('$suites = @(')
    m = re.search(r'\n\)\s*?\n', ps1_src[i:]) if i >= 0 else None
    last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$", ps1_src[i:i + m.start()])
            if m else None)
    if not last:
        problems.append('%s: could not find the end of $suites' % PS1)
    else:
        j = i + m.start()
        ps1_new = ps1_src[:j] + ',\n' + GATE_NOTE + ps1_src[j:]
        report.append('%-26s + %s, after %s' % (PS1, SUITE, last.group(1)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
import ast                                                    # noqa: E402

for label, path, text in (('models', MODELS, models_new),
                          ('signals', SIGNALS, signals_new)):
    if not text:
        continue
    try:
        ast.parse(text)
    except SyntaxError as e:
        problems.append('%s: the result does not parse - %s' % (label, e))

for path, text in cmd_files.items():
    if path.endswith('backfill_task_rollup.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('the command does not parse - %s' % e)

if signals_new:
    if signals_new.count('_roll_up_parents(instance)') != 2:
        problems.append('signals: the walk is called %d time(s), expected 2'
                        % signals_new.count('_roll_up_parents(instance)'))
    if '_ROLLING_UP' not in signals_new:
        problems.append('signals: the re-entrancy guard did not land')
if models_new and models_new.count('def update_from_subtasks') != 1:
    problems.append('models: the updater landed %d time(s), expected 1'
                    % models_new.count('def update_from_subtasks'))

# ==========================================================================
print('\n' + '=' * 74)
print('PROJECT ROLLUP - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not (models_new or signals_new or cmd_files or ps1_new):
    print('\n  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('\n  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, text in ((MODELS, models_new), (SIGNALS, signals_new)):
    if not text:
        continue
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(read(path))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

if ps1_new:
    with open(os.path.join(ROOT, PS1), 'w', encoding='utf-8',
              newline='') as f:
        f.write(ps1_new)

for path, text in cmd_files.items():
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

print('\n  written. Backups at *%s' % SUFFIX)
print('\n  Next:  python manage.py backfill_task_rollup      (DRY RUN)')
print('         python %s' % SUITE)
print('         python manage.py backfill_task_rollup --write')
print('         python %s   (the gate)' % PS1)
