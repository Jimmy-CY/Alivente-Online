#!/usr/bin/env python3
"""
apply_invoice_verification.py
=============================

Idempotent patcher for the Invoice Verification feature (Alivente Online).
Follows the house pattern of upgrade_analysis_ytd.py / upgrade_analysis_modal_v2.py:
asserts before it edits, backs up each file it touches, and is safe to re-run.

Run from the project root:

    python apply_invoice_verification.py            # apply
    python apply_invoice_verification.py --check    # report only, change nothing

Touches:
  pages/models.py            verify_* fields, widened amount, history recorder
  pages/views/expenses.py    verification hook, mismatch email, amount logging
  pages/utils.py             HEIC support
  requirements.txt           pillow-heif

Creates:  pages/migrations/0089_invoice_verification.py
Assumes:  pages/services/invoice_verification.py already copied in.
"""

import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
changed, skipped, problems = [], [], []


def sniff(path):
    """(encoding, newline) - so a file is written back exactly as it was found.

    requirements.txt in this repo is UTF-16 LE with CRLF, and act_expense.html
    is UTF-8 with CRLF. Rewriting either in the wrong encoding or flipping its
    line endings would produce an enormous, unreviewable diff.
    """
    with open(path, 'rb') as fh:
        raw = fh.read()
    if raw.startswith(b'\xff\xfe'):
        enc = 'utf-16'
    elif raw.startswith(b'\xfe\xff'):
        enc = 'utf-16'
    elif raw.startswith(b'\xef\xbb\xbf'):
        enc = 'utf-8-sig'
    else:
        enc = 'utf-8'
    probe = raw.decode(enc, errors='replace')
    return enc, ('\r\n' if '\r\n' in probe else '\n')


def read(path):
    """Return the text with newlines normalised to \\n for anchor matching."""
    enc, _ = sniff(path)
    with open(path, encoding=enc, newline='') as fh:
        return fh.read().replace('\r\n', '\n')


def backup_and_write(path, text, tag):
    if CHECK:
        return
    enc, nl = sniff(path)
    bak = path + '.bak_' + tag
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    if nl == '\r\n':
        text = text.replace('\n', '\r\n')
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text)


def patch(rel, sentinel, edits, tag):
    """edits = [(old, new), ...] - every `old` must appear exactly once."""
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        problems.append('%s: not found' % rel)
        return
    src = read(path)
    if sentinel in src:
        skipped.append('%s (already patched)' % rel)
        return
    for old, _ in edits:
        n = src.count(old)
        if n != 1:
            problems.append('%s: anchor found %d times, expected 1:\n    %s'
                            % (rel, n, old.strip().splitlines()[0][:90]))
            return
    for old, new in edits:
        src = src.replace(old, new, 1)
    backup_and_write(path, src, tag)
    changed.append(rel)


# ===========================================================================
# 1. pages/models.py
# ===========================================================================

MODELS_SENTINEL = 'act_expense_verify_status'

OLD_ACT_EXPENSE = """class act_expense(models.Model):
    act_expense_id = models.AutoField(primary_key=True)
    act_expense_date = models.DateField(blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    act_expense_description = models.CharField(max_length=55, blank=True, null=True)
    act_expense_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    act_expense_approved = models.CharField(max_length=3, blank=True, null=True)
    act_expense_paid = models.CharField(max_length=3, blank=True, null=True)
    act_expense_document = models.FileField(upload_to=expense_document_upload_path, blank=True, null=True)
"""

NEW_ACT_EXPENSE = '''class act_expense(models.Model):
    act_expense_id = models.AutoField(primary_key=True)
    act_expense_date = models.DateField(blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    act_expense_description = models.CharField(max_length=55, blank=True, null=True)
    # max_digits widened 6 -> 10 (Aug 2026). At 6 the ceiling was EUR 9,999.99,
    # which silently blocked any larger invoice (a renovation, a boiler).
    act_expense_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    act_expense_approved = models.CharField(max_length=3, blank=True, null=True)
    act_expense_paid = models.CharField(max_length=3, blank=True, null=True)
    act_expense_document = models.FileField(upload_to=expense_document_upload_path, blank=True, null=True)

    # ---- Invoice verification (two-way match) -----------------------------
    # Written by pages.services.invoice_verification when a document is
    # uploaded. Advisory only: nothing here ever alters a financial figure.
    act_expense_verify_status = models.CharField(
        max_length=20, blank=True, null=True,
        help_text='verified | mismatch | unverified | not_invoice | pending')
    act_expense_verify_checked_at = models.DateTimeField(blank=True, null=True)
    act_expense_verify_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text='Payable total as read from the invoice.')
    act_expense_verify_date = models.DateField(blank=True, null=True)
    act_expense_verify_number = models.CharField(max_length=60, blank=True, null=True)
    act_expense_verify_supplier = models.CharField(max_length=120, blank=True, null=True)
    act_expense_verify_notes = models.TextField(blank=True, null=True)
    act_expense_verify_raw = models.TextField(
        blank=True, null=True, help_text='Full extraction payload - the audit record.')
    act_expense_verify_model = models.CharField(
        max_length=60, blank=True, null=True,
        help_text='Model + prompt version, so old verdicts stay interpretable.')

    def verify_badge(self):
        """(css_class, icon, label) for the list icon and the modal banner."""
        return {
            'verified':    ('success', 'fa-check-circle',        'Invoice verified'),
            'mismatch':    ('danger',  'fa-exclamation-triangle', 'Invoice does not match'),
            'unverified':  ('secondary', 'fa-question-circle',   'Not checked - review by eye'),
            'not_invoice': ('secondary', 'fa-file',              'Not an invoice'),
            'split':       ('info',    'fa-object-group',        'One invoice covering several expenses'),
        }.get(self.act_expense_verify_status, ('secondary', 'fa-file-invoice', 'Document attached'))
'''

MODELS_HISTORY_ANCHOR = "def record_valuation_history(pv, effective_date, *, source='valuation', user=None):"

MODELS_HISTORY_NEW = '''KIND_ACTUAL_EXPENSE = 'expense_actual'   # ad-hoc act_expense amount amendments


def record_actual_expense_history(exp, effective_date=None, *, source='actual', user=None):
    """Append-only log of an `act_expense` amount.

    Why this exists: the amount captured at creation is an ESTIMATE (the work
    has not been done). When the invoice arrives higher, the superuser
    un-approves, the amount is edited and it is re-approved - and the original
    approved figure is overwritten and lost. Logging each value makes
    "which suppliers routinely exceed their estimate" answerable.

    Stored as a raw kind string (like KIND_VALUATION) so no migration to
    KIND_CHOICES is needed. Fail-safe: never raises, so a history problem
    cannot break the user's save.
    """
    try:
        if exp is None or exp.act_expense_amount is None:
            return None
        return FinancialFigureHistory.objects.create(
            prop=exp.prop, kind=KIND_ACTUAL_EXPENSE,
            source_pk=exp.act_expense_id, line_type='Actual expense',
            effective_date=effective_date or exp.act_expense_date or _fh_today(),
            amount=exp.act_expense_amount,
            source=source, changed_by=user,
        )
    except Exception:
        _fh_log.exception('record_actual_expense_history failed (save itself was not affected)')
        return None


'''

# ===========================================================================
# 2. pages/views/expenses.py
# ===========================================================================

VIEWS_SENTINEL = 'invoice_verification'

VIEWS_IMPORT_OLD = "from ..utils import convert_to_pdf, is_pdf, merge_pdfs"
VIEWS_IMPORT_NEW = """from ..utils import convert_to_pdf, is_pdf, merge_pdfs
from ..models import record_actual_expense_history
from ..services import invoice_verification as iv"""

# -- verification after a straight upload / replace -------------------------
VIEWS_UPLOAD_OLD = """                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            expense.act_expense_document.save(pdf_filename, pdf_content, save=True)
"""
VIEWS_UPLOAD_NEW = """                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            expense.act_expense_document.save(pdf_filename, pdf_content, save=True)

                            # Two-way match against the approved amount. Never
                            # blocks: any problem becomes an 'unverified' verdict.
                            _run_invoice_verification(request, expense, pdf_content)
"""

# -- verification of the NEW file on a merge (before it is merged away) -----
VIEWS_MERGE_OLD = """                            messages.success(request, f'Documents merged successfully for expense on {expense.act_expense_date}!')
"""
VIEWS_MERGE_NEW = """                            messages.success(request, f'Documents merged successfully for expense on {expense.act_expense_date}!')

                            # Verify the file just added, not the merged result:
                            # "verify each document" means each upload event.
                            _run_invoice_verification(request, expense, pdf_content)
"""

# -- clear the verdict when the document is removed -------------------------
VIEWS_DELETE_OLD = """                    expense.act_expense_document = None
"""
VIEWS_DELETE_NEW = """                    expense.act_expense_document = None
                    iv.clear_verification(expense)
"""

# -- log amount amendments --------------------------------------------------
VIEWS_EDIT_OLD = """            expense.save()

            messages.success(request, 'Expense updated successfully!')
"""
VIEWS_EDIT_NEW = """            expense.save()

            # Append-only log of the amount, so an estimate that is later
            # amended upward leaves a trail instead of overwriting history.
            if _amount_changed(previous_amount, expense.act_expense_amount):
                record_actual_expense_history(expense, user=request.user)

            messages.success(request, 'Expense updated successfully!')
"""

VIEWS_EDIT_CAPTURE_OLD = """            # Update expense fields
            expense.act_expense_date = request.POST.get('act_expense_date')
"""
VIEWS_EDIT_CAPTURE_NEW = """            previous_amount = expense.act_expense_amount

            # Update expense fields
            expense.act_expense_date = request.POST.get('act_expense_date')
"""

VIEWS_HELPERS = '''

# ===========================================================================
# Invoice verification helpers (two-way match)
# ===========================================================================
# This module has no module-level logger - the existing email helpers each
# create one locally. Define one here so every function below can log without
# a NameError in the error paths, which is precisely where it would bite.
import logging

logger = logging.getLogger(__name__)


def _amount_changed(before, after):
    """True when the amount really moved. Tolerant of str/Decimal/None."""
    from decimal import Decimal, InvalidOperation

    def norm(value):
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    return norm(before) != norm(after)


def _run_invoice_verification(request, expense, pdf_content):
    """Check an uploaded invoice against the approved amount.

    Wrapped so that NOTHING here can cost the user their upload: the document
    is already saved by the time we are called, and every failure path ends in
    an 'unverified' verdict plus an informational message.
    """
    if not iv.is_enabled():
        return
    try:
        pdf_content.seek(0)
        file_bytes = pdf_content.read()
        pdf_content.seek(0)
    except Exception:
        return

    try:
        verdict = iv.verify_expense_document(expense, file_bytes, 'application/pdf')
        expense.save()
    except Exception:
        logger.exception('Invoice verification failed for expense %s (document was saved)',
                         expense.act_expense_id)
        return

    status = verdict.get('status')
    if status == iv.STATUS_VERIFIED:
        messages.success(request, 'Invoice checked: the total matches the approved amount.')
    elif status == iv.STATUS_MISMATCH:
        messages.warning(
            request,
            'Invoice total does not match the approved amount. %s The approver has been '
            'notified and must un-approve the expense before the amount can be changed.'
            % (verdict.get('notes') or ''))
        send_expense_mismatch_email(expense, verdict)
    elif status == iv.STATUS_NOT_INVOICE:
        messages.info(request, 'This file does not look like an invoice, so it was not checked.')
    else:
        messages.info(request, 'The invoice could not be checked automatically; '
                               'please review it by eye.')


def send_expense_mismatch_email(expense, verdict):
    """Tell the approver an invoice disagrees with the approved amount.

    Mirrors send_expense_approved_email / send_expense_paid_email exactly - the
    same recipient registry and the same smtplib path. Django's send_mail is NOT
    used here: this project authenticates with EMAIL_PASSWORD via smtplib, so a
    send_mail call would silently fail to authenticate and the alert would never
    arrive.

    'expense_mismatch' is not a registered notification type, so the registry
    falls back to its default (the portfolio owner) - which is the right
    audience: this alert is for the approver, not for the user who uploaded.

    Fail-safe: a mail problem must never break the upload.
    """
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header

    smtp_object = None
    try:
        recipients = get_email_recipients('expense_mismatch')

        total = verdict.get('invoice_total')
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = ("Invoice does not match approved amount - %s (EUR %s)"
                          % (expense.prop.prop_name, expense.act_expense_amount))

        body = """An uploaded invoice does not match the amount that was approved.

Property:         %s
Expense date:     %s
Description:      %s
Approved amount:  EUR %s
Invoice total:    EUR %s
Supplier:         %s
Invoice number:   %s
Invoice date:     %s

%s

To correct this: un-approve the expense, ask the user to amend the amount, then
re-approve. The check runs again on re-approval and clears if it then matches.

This check is advisory. Nothing has been changed in the system.

Thanks,

Alivente Property Management System""" % (
            expense.prop.prop_name,
            expense.act_expense_date,
            expense.act_expense_description,
            expense.act_expense_amount,
            total if total is not None else '(not read)',
            verdict.get('supplier') or '(not read)',
            verdict.get('invoice_number') or '(not read)',
            verdict.get('invoice_date') or '(not read)',
            '\\n'.join([verdict.get('notes') or ''] + (verdict.get('advisories') or [])).strip(),
        )
        msg.attach(MIMEText(body, 'plain'))

        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD not set - mismatch alert not sent')
            return False

        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        smtp_object.sendmail(email, recipients['all'], msg.as_string())
        return True

    except Exception:
        logger.exception('send_expense_mismatch_email failed (upload was not affected)')
        return False
    finally:
        if smtp_object is not None:
            try:
                smtp_object.quit()
            except Exception:
                pass
'''

# ===========================================================================
# 3. pages/utils.py - HEIC
# ===========================================================================

UTILS_SENTINEL = 'pillow_heif'

UTILS_IMPORT_OLD = "from PIL import Image\n"
UTILS_IMPORT_NEW = '''from PIL import Image, ImageOps

# iPhones capture HEIC. Registering the opener lets Pillow read it exactly like
# a JPEG, so the existing image -> PDF path needs no other change. Optional: if
# the package is missing the app still runs, HEIC uploads simply fail as before.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except Exception:  # pragma: no cover - depends on deployment
    HEIC_SUPPORTED = False
'''


def patch_requirements():
    path = os.path.join(ROOT, 'requirements.txt')
    if not os.path.exists(path):
        problems.append('requirements.txt: not found')
        return
    src = read(path)
    if 'pillow-heif' in src.lower():
        skipped.append('requirements.txt (already has pillow-heif)')
        return
    text = src.rstrip('\n') + '\npillow-heif==0.18.0\n'
    backup_and_write(path, text, 'invverify')
    changed.append('requirements.txt')


MIGRATION_NAME = 'pages/migrations/0089_invoice_verification.py'
MIGRATION = '''from django.db import migrations, models


class Migration(migrations.Migration):
    """Invoice verification fields + widened actual-expense amount.

    Purely additive. The amount change widens max_digits 6 -> 10, which no
    existing value can fail, so it is safe on live data.
    """

    dependencies = [
        ('pages', '0088_invoices_invoice_paid_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_status',
            field=models.CharField(blank=True, max_length=20, null=True,
                help_text='verified | mismatch | unverified | not_invoice | pending'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True,
                help_text='Payable total as read from the invoice.'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_number',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_supplier',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_raw',
            field=models.TextField(blank=True, null=True,
                help_text='Full extraction payload - the audit record.'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_model',
            field=models.CharField(blank=True, max_length=60, null=True,
                help_text='Model + prompt version, so old verdicts stay interpretable.'),
        ),
    ]
'''


def write_migration():
    path = os.path.join(ROOT, MIGRATION_NAME)
    if os.path.exists(path):
        skipped.append(MIGRATION_NAME + ' (already exists)')
        return
    if CHECK:
        changed.append(MIGRATION_NAME + ' (would create)')
        return
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(MIGRATION)
    changed.append(MIGRATION_NAME)


def main():
    print('Invoice Verification patcher - %s\n' % ('CHECK ONLY' if CHECK else 'APPLYING'))

    # models.py needs a _fh_today helper if it is not already there.
    models_path = os.path.join(ROOT, 'pages/models.py')
    extra = []
    if os.path.exists(models_path) and '_fh_today' not in read(models_path):
        extra.append((MODELS_HISTORY_ANCHOR,
                      'def _fh_today():\n'
                      '    from datetime import date as _d\n'
                      '    return _d.today()\n\n\n'
                      + MODELS_HISTORY_NEW + MODELS_HISTORY_ANCHOR))
    else:
        extra.append((MODELS_HISTORY_ANCHOR, MODELS_HISTORY_NEW + MODELS_HISTORY_ANCHOR))

    patch('pages/models.py', MODELS_SENTINEL,
          [(OLD_ACT_EXPENSE, NEW_ACT_EXPENSE)] + extra, 'invverify')

    patch('pages/views/expenses.py', VIEWS_SENTINEL, [
        (VIEWS_IMPORT_OLD, VIEWS_IMPORT_NEW),
        (VIEWS_DELETE_OLD, VIEWS_DELETE_NEW),
        (VIEWS_MERGE_OLD, VIEWS_MERGE_NEW),
        (VIEWS_UPLOAD_OLD, VIEWS_UPLOAD_NEW),
        (VIEWS_EDIT_CAPTURE_OLD, VIEWS_EDIT_CAPTURE_NEW),
        (VIEWS_EDIT_OLD, VIEWS_EDIT_NEW),
    ], 'invverify')

    # helper block appended to the end of the views module
    vp = os.path.join(ROOT, 'pages/views/expenses.py')
    if os.path.exists(vp):
        vsrc = read(vp)
        if '_run_invoice_verification' in vsrc and 'def _run_invoice_verification' not in vsrc:
            backup_and_write(vp, vsrc.rstrip('\n') + '\n' + VIEWS_HELPERS, 'invverify2')
            changed.append('pages/views/expenses.py (helpers)')

    patch('pages/utils.py', UTILS_SENTINEL,
          [(UTILS_IMPORT_OLD, UTILS_IMPORT_NEW)], 'invverify')

    patch_requirements()
    write_migration()

    print('Changed:')
    for c in changed:
        print('  +', c)
    print('Skipped:')
    for s in skipped:
        print('  =', s)
    if problems:
        print('\nPROBLEMS - nothing was written for these:')
        for p in problems:
            print('  !', p)
        return 1
    if not CHECK:
        print('\nNext:  python manage.py makemigrations --check --dry-run')
        print('       python manage.py migrate')
    return 0


if __name__ == '__main__':
    sys.exit(main())
