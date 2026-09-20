"""backfill_task_rollup - bring every parent task into line with its
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

from pages.db_banner import banner_lines, describe_database
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

        # WHICH DATABASE, BEFORE ANYTHING ELSE. This command writes to live
        # rows, and the environment that decides which rows is five
        # variables that can come from a .env or from `railway run` with no
        # difference in the output. See pages/db_banner.py.
        for line in banner_lines():
            self.stdout.write(line)
        if write:
            self.stdout.write(self.style.WARNING(
                'THIS RUN WILL SAVE. Re-run without --write to only '
                'report.'))

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
            # AND AGAIN AT THE END, because the banner at the top has
            # scrolled off by now and this is the line that gets pasted
            # into a conversation as the record of what happened.
            _db = describe_database()
            self.stdout.write(self.style.SUCCESS(
                '%d parent task(s) updated, %d refused by validation'
                % (changed - failed, failed)))
            self.stdout.write(self.style.SUCCESS(
                'written to %s at %s' % (_db['name'], _db['host'])))
        else:
            self.stdout.write(
                '%d parent task(s) WOULD be updated. Nothing was written.'
                % changed)
            self.stdout.write(
                'Re-run with --write to apply.')
