#!/usr/bin/env python3
"""
apply_invoice_upload_email.py
=============================

Turn the mismatch-only alert into a notification on EVERY invoice upload.

Why: nothing previously told the approver that an invoice had arrived and was
ready for payment - you had to go looking. Live data shows ~38 documented
expenses a year (~3 a month), which is a volume worth emailing; the earlier
"300 a year" estimate that argued against this was wrong.

What changes:

 * An email is sent on every upload, whatever the verdict - and even when the
   automatic check could not run at all. The notification is "an invoice
   arrived"; the analysis is a bonus and must not gate the notice.
 * The verdict is in the SUBJECT, so a mismatch is unmistakable in the inbox
   without opening anything.
 * The body carries the full analysis: totals, net/VAT, supplier, invoice
   number and date, confidence, advisory notes, and a deep link to the expense.
 * send_expense_mismatch_email is replaced by send_invoice_verification_email.
   The 'expense_mismatch' notification type is KEPT (so any recipients you have
   already saved survive) but relabelled, since it now covers every upload.

Touches:
  pages/views/expenses.py                     both helper functions
  pages/models.py                             notification-type label
  pages/templates/notification_settings.html  card heading + description
Creates:
  pages/migrations/0091_notification_label_invoice_upload.py

Idempotent; backs up each file. Run from the project root:

    python apply_invoice_upload_email.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
report = []
failed = False

OLD_LABEL = "('expense_mismatch', 'Expense Invoice Mismatch')"
NEW_LABEL = "('expense_mismatch', 'Expense Invoice Uploaded')"


def rw(path, fn, tag, sentinel):
    global failed
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        report.append('! %s not found' % path)
        failed = True
        return
    with open(full, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    src = raw.decode(enc).replace('\r\n', '\n')
    if sentinel in src:
        report.append('= %s already patched' % path)
        return
    out = fn(src)
    if out is None:
        failed = True
        return
    if CHECK:
        report.append('+ %s would be patched' % path)
        return
    bak = full + '.bak_' + tag
    if not os.path.exists(bak):
        shutil.copy2(full, bak)
    with open(full, 'w', encoding=enc, newline='') as fh:
        fh.write(out.replace('\n', nl) if nl == '\r\n' else out)
    report.append('+ %s patched' % path)


# ===========================================================================
# 1. pages/views/expenses.py - replace both helpers (they run to end of file)
# ===========================================================================

ANCHOR = 'def _run_invoice_verification(request, expense, pdf_content):'

NEW_HELPERS = '''def _run_invoice_verification(request, expense, pdf_content):
    """Check an uploaded invoice, then notify the approver.

    Two separable jobs, deliberately not entangled:

      1. Run the check (needs ANTHROPIC_API_KEY, may fail).
      2. Tell the approver an invoice has arrived and is ready for payment.

    (2) happens EVEN IF (1) could not run. The notification is "an invoice
    arrived"; the analysis is a bonus, and a missing key or a network blip must
    not silently cost the approver their notice.

    Nothing here can cost the user their upload: the document is already saved
    by the time we are called.
    """
    verdict = None

    if iv.is_enabled():
        file_bytes = None
        try:
            pdf_content.seek(0)
            file_bytes = pdf_content.read()
            pdf_content.seek(0)
        except Exception:
            logger.exception('Could not re-read the uploaded file for expense %s',
                             expense.act_expense_id)

        if file_bytes:
            try:
                verdict = iv.verify_expense_document(expense, file_bytes, 'application/pdf')
                expense.save()
            except Exception:
                verdict = None
                logger.exception('Invoice verification failed for expense %s '
                                 '(document was saved)', expense.act_expense_id)

    status = (verdict or {}).get('status')
    if status == iv.STATUS_VERIFIED:
        messages.success(request, 'Invoice checked: the total matches the approved amount.')
    elif status == iv.STATUS_MISMATCH:
        messages.warning(
            request,
            'Invoice total does not match the approved amount. %s The approver has been '
            'notified and must un-approve the expense before the amount can be changed.'
            % (verdict.get('notes') or ''))
    elif status == iv.STATUS_SPLIT:
        messages.info(request, 'Invoice checked: %s' % (verdict.get('notes') or ''))
    elif status == iv.STATUS_NOT_INVOICE:
        messages.info(request, 'This file does not look like an invoice, so it was not checked.')
    else:
        messages.info(request, 'The invoice could not be checked automatically; '
                               'please review it by eye.')

    send_invoice_verification_email(expense, verdict)


# --- email ----------------------------------------------------------------

def _verify_extra(expense):
    """net / VAT / confidence / summary out of the stored extraction payload.

    Read from act_expense_verify_raw rather than threaded through the verdict,
    so the service keeps its narrow return contract. Never raises.
    """
    import json
    try:
        return json.loads(expense.act_expense_verify_raw or '{}') or {}
    except Exception:
        return {}


def _subject_for(expense, verdict):
    """Verdict first, so the inbox is scannable without opening anything."""
    prop = expense.prop.prop_name
    amount = expense.act_expense_amount
    status = (verdict or {}).get('status')
    total = (verdict or {}).get('invoice_total')

    if status == iv.STATUS_MISMATCH:
        return ('** INVOICE MISMATCH ** %s - invoice EUR %s vs approved EUR %s'
                % (prop, total if total is not None else '?', amount))
    if status == iv.STATUS_VERIFIED:
        return 'Invoice ready to pay - %s EUR %s [VERIFIED]' % (prop, amount)
    if status == iv.STATUS_SPLIT:
        return 'Invoice ready to pay - %s EUR %s [COVERS SEVERAL EXPENSES]' % (prop, amount)
    if status == iv.STATUS_NOT_INVOICE:
        return 'Document uploaded - %s EUR %s [NOT AN INVOICE]' % (prop, amount)
    return 'Invoice ready to pay - %s EUR %s [CHECK BY EYE]' % (prop, amount)


HEADLINE = {
    'verified': 'VERIFIED - the invoice total matches the approved amount.',
    'mismatch': 'MISMATCH - the invoice total does NOT match the approved amount.',
    'split': 'COVERS SEVERAL EXPENSES - one invoice booked against more than one expense.',
    'unverified': 'NOT CHECKED - the document could not be read with enough confidence.',
    'not_invoice': 'NOT AN INVOICE - this file is a receipt, quote or similar.',
}


def _body_for(expense, verdict):
    extra = _verify_extra(expense)
    status = (verdict or {}).get('status')
    site = os.environ.get('SITE_URL', 'https://alivente.online').rstrip('/')

    def money(v):
        return 'EUR %s' % v if v is not None else '(not read)'

    lines = [
        'An invoice has been uploaded and is ready for your review.',
        '',
        '  Property:         %s' % expense.prop.prop_name,
        '  Expense date:     %s' % expense.act_expense_date,
        '  Description:      %s' % expense.act_expense_description,
        '  Approved amount:  EUR %s' % expense.act_expense_amount,
        '  Status:           Approved=%s, Paid=%s' % (expense.act_expense_approved,
                                                      expense.act_expense_paid),
        '',
        '-' * 66,
    ]

    if verdict is None:
        lines += [
            'AUTOMATIC CHECK: DID NOT RUN',
            '',
            'The invoice could not be checked automatically this time, so please',
            'review it by eye as usual. The document itself uploaded correctly.',
        ]
    else:
        lines += [
            'AUTOMATIC CHECK: %s' % HEADLINE.get(status, status or 'unknown'),
            '',
            '  %s' % (verdict.get('notes') or ''),
            '',
            '  Invoice total:    %s' % money(verdict.get('invoice_total')),
        ]
        net, vat = extra.get('net_amount'), extra.get('vat_amount')
        if net is not None or vat is not None:
            lines.append('  Net + VAT:        %s + %s' % (money(net), money(vat)))
        lines += [
            '  Supplier:         %s' % (verdict.get('supplier') or '(not read)'),
            '  Invoice number:   %s' % (verdict.get('invoice_number') or '(not read)'),
            '  Invoice date:     %s' % (verdict.get('invoice_date') or '(not read)'),
        ]
        if extra.get('description_summary'):
            lines.append('  Invoice is for:   %s' % extra['description_summary'])
        if extra.get('property_hint'):
            lines.append('  Address on it:    %s' % extra['property_hint'])
        if extra.get('confidence') is not None:
            lines.append('  Confidence:       %s   (%s)'
                         % (extra['confidence'], expense.act_expense_verify_model or ''))

        advisories = verdict.get('advisories') or []
        if advisories:
            lines += ['', '  Worth a glance:']
            lines += ['    - %s' % a for a in advisories]

        if status == iv.STATUS_MISMATCH:
            lines += [
                '',
                'To correct this: un-approve the expense, ask the user to amend the',
                'amount, then re-approve. The check runs again on re-approval and',
                'clears if it then matches.',
            ]

    lines += [
        '',
        '-' * 66,
        'Open this expense:',
        '%s/act_expense_all/?manage=%s' % (site, expense.act_expense_id),
        '',
        'This check is advisory. Nothing has been changed in the system.',
        '',
        'Thanks,',
        '',
        'Alivente Property Management System',
    ]
    return '\\n'.join(lines)


def send_invoice_verification_email(expense, verdict):
    """Notify the approver that an invoice has been uploaded.

    Sent on EVERY upload, with the verdict in the subject line. Uses the
    'expense_mismatch' recipient row so recipients already configured in
    Administration -> Notification Settings continue to apply.

    Mirrors send_expense_approved_email exactly - the same recipient registry
    and the same smtplib path. Django's send_mail is NOT used: this project
    authenticates with EMAIL_PASSWORD via smtplib, so send_mail would fail
    silently and the notice would never arrive.

    Fail-safe: a mail problem must never break the upload.
    """
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header

    smtp_object = None
    try:
        recipients = get_email_recipients('expense_mismatch')

        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = _subject_for(expense, verdict)
        msg.attach(MIMEText(_body_for(expense, verdict), 'plain', 'utf-8'))

        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD not set - invoice upload notice not sent')
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
        logger.exception('send_invoice_verification_email failed '
                         '(upload was not affected)')
        return False
    finally:
        if smtp_object is not None:
            try:
                smtp_object.quit()
            except Exception:
                pass
'''


def patch_views(src):
    if ANCHOR not in src:
        report.append('! _run_invoice_verification not found - run the earlier patchers first')
        return None
    return src[:src.index(ANCHOR)] + NEW_HELPERS


# ===========================================================================
# 2. relabel the notification type
# ===========================================================================

def patch_models(src):
    if src.count(OLD_LABEL) != 1:
        report.append('! models label anchor matched %d times' % src.count(OLD_LABEL))
        return None
    return src.replace(OLD_LABEL, NEW_LABEL, 1)


CARD_OLD = ('    <h5><i class="fas fa-exclamation-triangle"></i> Expense Invoice Mismatch</h5>\n'
            '    <p class="text-muted">Alert when an uploaded invoice total does not match the '
            'approved expense amount. Sent only on a confirmed mismatch, never on a routine '
            'upload.</p>')
CARD_NEW = ('    <h5><i class="fas fa-file-invoice-dollar"></i> Expense Invoice Uploaded</h5>\n'
            '    <p class="text-muted">Sent every time an invoice is uploaded against an expense, '
            'so you know it is ready for payment. The subject line carries the automatic check '
            'result and the body contains the full analysis.</p>')


def patch_template(src):
    if src.count(CARD_OLD) != 1:
        report.append('! notification card anchor matched %d times' % src.count(CARD_OLD))
        return None
    return src.replace(CARD_OLD, CARD_NEW, 1)


MIGRATION_NAME = 'pages/migrations/0091_notification_label_invoice_upload.py'
CHOICES = [
    ('celebration_reminder', 'Celebration Reminders'),
    ('document_expiry', 'Document Expiry Alerts'),
    ('daily_report', 'Daily Property Management Report'),
    ('new_lease_upload', 'New Lease Upload Reminders'),
    ('expense_needs_approval', 'Expense Needs Approval'),
    ('expense_approved', 'Expense Approved'),
    ('expense_paid', 'Expense Paid'),
    ('expense_mismatch', 'Expense Invoice Uploaded'),
    ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'),
    ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'),
    ('invoice_paid', 'Invoice Marked as Paid'),
    ('issue_comments_daily', 'Daily Issue Comments Report'),
    ('issue_comment_urgent', 'Urgent Issue Comment Alert'),
    ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
    ('physical_invoice_client', 'Physical Invoice to Client'),
]

MIGRATION = '''from django.db import migrations, models


class Migration(migrations.Migration):
    """Relabel 'expense_mismatch' - it now covers EVERY invoice upload, not
    only mismatches. The key is deliberately unchanged so any recipients
    already configured for it keep working.

    Label-only change: no column altered, no data touched.
    """

    dependencies = [
        ('pages', '0090_notification_type_expense_mismatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(choices=%r, max_length=50),
        ),
    ]
''' % (CHOICES,)


def write_migration():
    path = os.path.join(ROOT, MIGRATION_NAME)
    if os.path.exists(path):
        report.append('= %s already exists' % MIGRATION_NAME)
        return
    if CHECK:
        report.append('+ %s would be created' % MIGRATION_NAME)
        return
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(MIGRATION)
    report.append('+ %s created' % MIGRATION_NAME)


def main():
    print('Invoice upload notification - %s\n' % ('CHECK ONLY' if CHECK else 'APPLYING'))
    rw('pages/views/expenses.py', patch_views, 'uploademail',
       'send_invoice_verification_email')
    rw('pages/models.py', patch_models, 'uploademail', NEW_LABEL)
    rw('pages/templates/notification_settings.html', patch_template, 'uploademail',
       'Expense Invoice Uploaded')
    write_migration()

    for line in report:
        print('  ' + line)
    if failed:
        print('\nNothing was written for the failing file(s).')
        return 1
    if not CHECK:
        print('\nVerify:')
        print('  python -m py_compile pages/views/expenses.py')
        print('  python manage.py makemigrations --check --dry-run')
    return 0


if __name__ == '__main__':
    sys.exit(main())
