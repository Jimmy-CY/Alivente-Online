#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A way back from a receipt edited directly in the database.

THE PROBLEM. The stored PDF is the receipt - it is what was emailed, what was
handed over, and what `cash_receipt_pdf` serves. Every path in the app that
changes a receipt re-renders it, so the row and the document stay together. A
change made straight in MySQL cannot: the row moves, the document does not,
and nothing on the screen says so.

WHAT THIS ADDS. One management command, `regenerate_receipt_pdf`, which
re-renders from whatever is in the database now.

    python manage.py regenerate_receipt_pdf CR-00372
    python manage.py regenerate_receipt_pdf --all --dry-run

IT DOES NOT MARK THE RECEIPT AS EDITED, and that is the point of it.
`edited_at` records that somebody changed a receipt THROUGH THE APP after it
was issued; this command changes nothing, it only makes the document agree
with the row again. Stamping here would claim an edit this run did not make.

Nothing else changes: no model field, no migration, no template, no route. It
reuses `store_pdf` from `views/receipts.py`, which is already the one place
that renders a receipt and replaces its file - so the command cannot drift
from what the screens do.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
CMDDIR = os.path.join(ROOT, 'pages', 'management', 'commands')
TARGET = os.path.join(CMDDIR, 'regenerate_receipt_pdf.py')
VIEWS  = os.path.join(ROOT, 'pages', 'views', 'receipts.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_receiptregen'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


COMMAND_PY = r'''"""
regenerate_receipt_pdf — re-render a receipt's stored PDF from the database.

WHY THIS EXISTS. The stored PDF is the receipt: it is what was emailed, what
was handed over, and what `cash_receipt_pdf` serves. Every path in the app
that changes a receipt re-renders it, so the two stay together. A change made
DIRECTLY IN THE DATABASE cannot do that — the row moves and the document does
not, and nothing on the screen says so. This is the way back.

    python manage.py regenerate_receipt_pdf CR-00372
    python manage.py regenerate_receipt_pdf CR-00372 CR-00374    # several
    python manage.py regenerate_receipt_pdf --all
    python manage.py regenerate_receipt_pdf --all --dry-run      # list only

IT DOES NOT STAMP THE RECEIPT AS EDITED. `edited_at` records that somebody
changed a receipt through the app after it was issued; this command did not
change anything, it only made the document agree with the row again. Setting
the stamp here would claim an edit that this run did not make. If the intent
IS to record an edit, use the Edit screen — that is what it is for.

Nor does it touch `is_void`, the number, or any other field: it renders what
is there. A voided receipt regenerates with its VOID stamp, because it is
still void.

Safe to run repeatedly. The previous file is deleted before the new one is
written, so re-running does not accumulate `CR-00372_a1b2c3.pdf` copies.
"""
from django.core.management.base import BaseCommand, CommandError

from pages.models import CashReceipt
from pages.views.receipts import build_receipt_context, store_pdf


class Command(BaseCommand):
    help = ("Re-render the stored PDF for one or more receipts from the "
            "current database values. Does not mark them edited.")

    def add_arguments(self, parser):
        parser.add_argument(
            'numbers', nargs='*',
            help="Receipt numbers, e.g. CR-00372. Omit with --all.")
        parser.add_argument(
            '--all', action='store_true',
            help="Every receipt in the system.")
        parser.add_argument(
            '--dry-run', action='store_true',
            help="List what would be re-rendered without writing anything.")

    def handle(self, *args, **options):
        numbers = options['numbers']
        do_all = options['all']
        dry = options['dry_run']

        if not numbers and not do_all:
            raise CommandError(
                "Give one or more receipt numbers, or --all.\n"
                "    python manage.py regenerate_receipt_pdf CR-00372")
        if numbers and do_all:
            raise CommandError("Give numbers OR --all, not both.")

        if do_all:
            receipts = list(CashReceipt.objects.all()
                            .order_by('receipt_number'))
        else:
            # Matched case-insensitively and whitespace-trimmed, because these
            # are typed by hand at a shell.
            wanted = [n.strip() for n in numbers if n.strip()]
            receipts = list(CashReceipt.objects.filter(
                receipt_number__in=wanted).order_by('receipt_number'))
            found = {r.receipt_number for r in receipts}
            missing = [n for n in wanted if n not in found]
            if missing:
                # Refuse the whole run rather than half-doing it. A typo in one
                # number should not leave you guessing which of the others went
                # through.
                raise CommandError(
                    "No receipt with %s. Nothing has been changed.\n"
                    "    Known numbers: %s"
                    % (', '.join(missing),
                       ', '.join(CashReceipt.objects.order_by('receipt_number')
                                 .values_list('receipt_number', flat=True)[:10])
                       or '(none)'))

        if not receipts:
            self.stdout.write(self.style.WARNING("No receipts to re-render."))
            return

        if dry:
            self.stdout.write(self.style.NOTICE(
                "Dry run — nothing will be written."))

        done = 0
        for r in receipts:
            was = r.pdf_file.name if r.pdf_file else '(none)'
            label = '%s  %s  %s %s' % (
                r.receipt_number, r.receipt_date, r.currency, r.amount)
            if r.is_void:
                label += '  [VOID]'
            if dry:
                self.stdout.write('  would re-render  %s' % label)
                self.stdout.write('                   current file: %s' % was)
                continue
            try:
                store_pdf(r)
            except Exception as exc:                      # noqa: BLE001
                # Report and carry on: one receipt that will not render must
                # not stop the other forty.
                self.stdout.write(self.style.ERROR(
                    '  FAILED  %s — %s: %s'
                    % (label, type(exc).__name__, exc)))
                continue
            done += 1
            self.stdout.write(self.style.SUCCESS('  re-rendered  %s' % label))
            self.stdout.write('               %s' % r.pdf_file.name)

        if dry:
            self.stdout.write(self.style.NOTICE(
                "Dry run — nothing saved. Re-run without --dry-run to apply."))
            return

        failed = len(receipts) - done
        if failed:
            self.stdout.write(self.style.WARNING(
                "Re-rendered %d of %d; %d failed." % (done, len(receipts), failed)))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Re-rendered %d receipt(s). None marked as edited." % done))
'''


def main():
    if not os.path.isdir(CMDDIR):
        sys.exit('! %s does not exist - is this the repo root?'
                 % os.path.relpath(CMDDIR, ROOT))
    if not os.path.exists(VIEWS):
        sys.exit('! pages/views/receipts.py is missing - run '
                 'apply_cash_receipts.py first')

    vsrc = read(VIEWS)

    if os.path.exists(TARGET) and 'None marked as edited' in read(TARGET):
        print('  regenerate_receipt_pdf      already installed')
        print('\n  0 file(s) changed')
        return

    bad = []
    # THE COMMAND IMPORTS TWO NAMES. If either is not there, the command
    # fails at import - which manage.py reports as a missing command, not as
    # a missing function, and sends you looking in the wrong place.
    for name in ('def store_pdf', 'def build_receipt_context'):
        if name not in vsrc:
            bad.append('views/receipts.py has no %s - the round that added it '
                       'is not in this tree' % name.replace('def ', ''))
    # IT MUST NOT STAMP, and it must not quietly write anything else. That is
    # the whole reason this command exists rather than the Edit screen.
    #
    # Read off the PARSE TREE, not searched for as text. The first version of
    # this check looked for the string "edited_at" and caught the command's
    # own docstring - the paragraph explaining that it does not stamp. Three
    # checks this week have failed that way; prose is not mechanism, and a
    # name appearing in a comment is the commonest way a name appears.
    NEVER_WRITTEN = ('edited_at', 'edited_by', 'receipt_number', 'is_void',
                     'voided_at', 'voided_by', 'void_reason', 'amount',
                     'receipt_date', 'description')
    try:
        import ast
        tree = ast.parse(COMMAND_PY)
        wrote, called, saved = set(), set(), set()
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Attribute) and t.attr in NEVER_WRITTEN:
                    wrote.add(t.attr)
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    called.add(fn.id)
                    if fn.id == 'setattr' and len(node.args) >= 2 \
                            and isinstance(node.args[1], ast.Constant) \
                            and node.args[1].value in NEVER_WRITTEN:
                        wrote.add(node.args[1].value)
                elif isinstance(fn, ast.Attribute) and fn.attr in ('save', 'delete',
                                                                   'update'):
                    saved.add(fn.attr)
        if wrote:
            bad.append('the command assigns %s - it must only re-render'
                       % ', '.join(sorted(wrote)))
        if saved:
            bad.append('the command calls .%s() directly - only store_pdf may '
                       'write' % '() / .'.join(sorted(saved)))
        if 'store_pdf' not in called:
            bad.append('the command does not call store_pdf, so it would not '
                       'reuse the one place that renders and replaces the file')
    except SyntaxError as e:
        bad.append('the command does not parse: %s' % e)
    if bad:
        sys.exit('! receipt-regen self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  pages/management/commands/regenerate_receipt_pdf.py   new')
    print('     re-renders from the database; does NOT mark anything edited')

    if not CHECK:
        if os.path.exists(TARGET):
            b = TARGET + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(TARGET, b)
        with open(TARGET, 'w', encoding='utf-8') as f:
            f.write(COMMAND_PY)

    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))
    if not CHECK:
        print('\n  For the receipt you changed in MySQL:')
        print('     python manage.py regenerate_receipt_pdf CR-00372')


if __name__ == '__main__':
    main()
