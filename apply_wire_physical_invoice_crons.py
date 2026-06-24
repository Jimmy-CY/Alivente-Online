# -*- coding: utf-8 -*-
"""
Apply: run the physical-invoice crons from the daily 06:00 command.

  pages/management/commands/check_lease_renewal_and_invoices.py
    + import call_command
    + in handle(), right after create_invoices(), call:
        prepare_physical_invoices   (skipped on --dry-run; it has no --dry-run)
        send_physical_invoices      (passed dry_run=self.dry_run)
      Both wrapped in their own try/except so a failure cannot abort the
      property-management report, passport, lease, celebration, or
      issue-comment notifications. Ordering: create_invoices() writes this
      month's collection rows FIRST, then send links/stamps them.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_wire_physical_invoice_crons.py
"""
import ast
import io
import os
import sys

CMD = os.path.join("pages", "management", "commands",
                   "check_lease_renewal_and_invoices.py")

EDITS = [
    # 1) import call_command (placed just above BaseCommand import)
    ("from django.core.management.base import BaseCommand",
     "from django.core.management import call_command\n"
     "from django.core.management.base import BaseCommand"),

    # 2) insert the two call_command blocks after create_invoices()
    ('''            # First, create invoices if needed
            created_invoices_count = self.create_invoices()

            # Then get all the data with property details''',
     '''            # First, create invoices if needed
            created_invoices_count = self.create_invoices()

            # Prepare upcoming-month physical-invoice drafts + approval reminder.
            # (prepare has no --dry-run; skip it entirely on a dry run.)
            if not self.dry_run:
                try:
                    call_command('prepare_physical_invoices')
                except Exception as e:
                    self.stdout.write(f'\\u26a0\\ufe0f  prepare_physical_invoices failed: {e}')
                    logger.error(f'prepare_physical_invoices failed: {e}', exc_info=True)

            # Send approved physical invoices (numbers, emails PDF, links/stamps
            # the collection rows just created above). Runs AFTER create_invoices()
            # on purpose, so the collection rows exist to link.
            try:
                call_command('send_physical_invoices', dry_run=self.dry_run)
            except Exception as e:
                self.stdout.write(f'\\u26a0\\ufe0f  send_physical_invoices failed: {e}')
                logger.error(f'send_physical_invoices failed: {e}', exc_info=True)

            # Then get all the data with property details'''),
]


def main():
    if not os.path.exists(CMD):
        sys.exit("ABORTED - missing file: %s" % CMD)
    with io.open(CMD, "r", encoding="utf-8") as fh:
        src = fh.read()

    problems = []
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            problems.append("  edit %d: anchor found %d time(s) (expected 1)" % (i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (CMD, e))

    with io.open(CMD + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(CMD, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (CMD, CMD))
    print("done. next: check")


if __name__ == "__main__":
    main()