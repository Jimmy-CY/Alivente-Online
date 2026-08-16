"""
invoice_verify_audit - read-only accuracy trial for invoice verification.

Runs the real extraction against real expense documents and prints what the
feature WOULD have concluded. It writes nothing: no model fields are read or
set, no emails are sent, no database row is touched. That means it can be run
on Live BEFORE the migration is applied, which is the whole point - you get to
judge the accuracy before committing to the feature.

Mirrors analysis_audit.py: plain-English, per-row, reconcilable by hand.

    # 20 most recent expenses that have a document
    python manage.py invoice_verify_audit --limit 20

    # only a given property, and show the full extraction for each
    python manage.py invoice_verify_audit --prop "Palikaridi" --verbose

    # estimate the cost without calling the API at all
    python manage.py invoice_verify_audit --limit 20 --dry-run

On Live:
    railway ssh
    python manage.py invoice_verify_audit --limit 20
"""

from django.core.management.base import BaseCommand

from pages.models import act_expense
from pages.services import invoice_verification as iv

BAR = '=' * 78


def sniff_media_type(blob, name=''):
    """Stored documents are not all PDFs - older ones were saved as .jpg/.png
    before the auto-convert-to-PDF path existed. Detect from magic bytes."""
    if blob[:5] == b'%PDF-':
        return 'application/pdf'
    if blob[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if blob[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        return 'image/webp'
    if blob[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    lower = (name or '').lower()
    for ext, mt in (('.pdf', 'application/pdf'), ('.jpg', 'image/jpeg'),
                    ('.jpeg', 'image/jpeg'), ('.png', 'image/png')):
        if lower.endswith(ext):
            return mt
    return None


SYMBOL = {
    iv.STATUS_VERIFIED: 'OK  ',
    iv.STATUS_MISMATCH: 'FLAG',
    iv.STATUS_UNVERIFIED: '??  ',
    iv.STATUS_NOT_INVOICE: '--  ',
}


class Command(BaseCommand):
    help = 'Read-only trial of invoice verification against existing expense documents.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20,
                            help='How many expenses to check (default 20).')
        parser.add_argument('--prop', type=str, default=None,
                            help='Restrict to one property name (icontains).')
        parser.add_argument('--dry-run', action='store_true',
                            help='List what would be checked; make no API calls.')
        parser.add_argument('--verbose', action='store_true',
                            help='Print the full extraction payload per document.')

    def handle(self, *args, **opts):
        limit = opts['limit']
        qs = (act_expense.objects
              .exclude(act_expense_document='')
              .exclude(act_expense_document=None)
              .select_related('prop')
              .order_by('-act_expense_date', '-act_expense_id'))
        if opts['prop']:
            qs = qs.filter(prop__prop_name__icontains=opts['prop'])

        rows = list(qs[:limit])
        if not rows:
            self.stdout.write('No expenses with an attached document were found.')
            return

        self.stdout.write(BAR)
        self.stdout.write('INVOICE VERIFICATION - READ-ONLY TRIAL')
        self.stdout.write('%d expense(s) with a document. Nothing will be written.' % len(rows))
        if not iv.is_enabled():
            self.stdout.write(self.style.WARNING(
                'ANTHROPIC_API_KEY is not set - extraction cannot run here.'))
        self.stdout.write(BAR)

        tally = {}
        for index, exp in enumerate(rows, 1):
            name = (exp.act_expense_document.name or '').split('/')[-1]
            self.stdout.write('')
            self.stdout.write('[%d/%d] expense #%s  %s  %s' % (
                index, len(rows), exp.act_expense_id,
                exp.act_expense_date, exp.prop.prop_name))
            self.stdout.write('        description : %s' % exp.act_expense_description)
            self.stdout.write('        approved    : EUR %s   (approved=%s, paid=%s)' % (
                exp.act_expense_amount, exp.act_expense_approved, exp.act_expense_paid))
            self.stdout.write('        document    : %s' % name)

            if opts['dry_run']:
                tally['dry-run'] = tally.get('dry-run', 0) + 1
                continue

            try:
                exp.act_expense_document.open('rb')
                blob = exp.act_expense_document.read()
                exp.act_expense_document.close()
            except Exception as exc:                            # noqa: BLE001
                self.stdout.write(self.style.ERROR('        FILE UNREADABLE: %s' % exc))
                tally['file error'] = tally.get('file error', 0) + 1
                continue

            media_type = sniff_media_type(blob, name)
            if media_type is None:
                self.stdout.write(self.style.WARNING(
                    '        SKIPPED: not a PDF or image - cannot be read'))
                tally['unsupported'] = tally.get('unsupported', 0) + 1
                continue

            try:
                extracted = iv.extract_invoice(blob, media_type)
            except iv.ExtractionUnavailable as exc:
                self.stdout.write(self.style.WARNING('        extraction unavailable: %s' % exc))
                tally[iv.STATUS_UNVERIFIED] = tally.get(iv.STATUS_UNVERIFIED, 0) + 1
                continue

            verdict = iv.evaluate(
                expense_amount=exp.act_expense_amount,
                expense_date=exp.act_expense_date,
                expense_description=exp.act_expense_description,
                property_name=exp.prop.prop_name,
                extracted=extracted,
            )
            status = verdict['status']
            tally[status] = tally.get(status, 0) + 1

            style = (self.style.SUCCESS if status == iv.STATUS_VERIFIED
                     else self.style.ERROR if status == iv.STATUS_MISMATCH
                     else self.style.WARNING)
            self.stdout.write(style('        VERDICT     : %s %s' % (
                SYMBOL.get(status, '    '), status.upper())))
            self.stdout.write('        invoice tot : %s' % (
                verdict['invoice_total'] if verdict['invoice_total'] is not None else '(not read)'))
            self.stdout.write('        supplier    : %s' % (verdict['supplier'] or '(not read)'))
            self.stdout.write('        %s' % (verdict['notes'] or ''))
            for note in verdict['advisories']:
                self.stdout.write('        note: %s' % note)
            if opts['verbose']:
                self.stdout.write('        raw: %r' % (extracted,))

        self.stdout.write('')
        self.stdout.write(BAR)
        self.stdout.write('SUMMARY')
        for key in (iv.STATUS_VERIFIED, iv.STATUS_MISMATCH,
                    iv.STATUS_UNVERIFIED, iv.STATUS_NOT_INVOICE,
                    'unsupported', 'file error', 'dry-run'):
            if tally.get(key):
                self.stdout.write('  %-14s %d' % (key, tally[key]))
        self.stdout.write('')
        self.stdout.write('How to read this:')
        self.stdout.write('  verified    - total read confidently AND equal to the approved amount')
        self.stdout.write('  mismatch    - total read confidently AND different (would email you)')
        self.stdout.write('  unverified  - could not read a total worth trusting; you review by eye')
        self.stdout.write('  not_invoice - a receipt, quote or other non-invoice')
        self.stdout.write('')
        self.stdout.write('Judge it on two questions:')
        self.stdout.write('  1. Is every "mismatch" a real difference?  (false alarms kill trust)')
        self.stdout.write('  2. Is the "unverified" rate low enough to save you work?')
        self.stdout.write(BAR)
