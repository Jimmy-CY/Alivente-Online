"""
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
