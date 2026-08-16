#!/usr/bin/env python3
"""
fix_invoice_verification_email.py
=================================

Repairs an ALREADY-APPLIED install of the invoice verification feature.

Two defects found after the first apply, both in pages/views/expenses.py:

 1. send_expense_mismatch_email used django.core.mail.send_mail and
    settings.MANAGERS. This project has neither configured - it authenticates
    with EMAIL_PASSWORD over smtplib, and picks recipients through
    pages.email_utils.get_email_recipients. The alert would have silently
    failed to send.

 2. The module has no module-level `logger`; the existing email helpers each
    make one locally. The injected code referenced `logger`, so any error path
    would have raised NameError instead of logging.

Idempotent. Backs up to expenses.py.bak_emailfix. Run from the project root:

    python fix_invoice_verification_email.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'views', 'expenses.py')
ANCHOR = 'def send_expense_mismatch_email(expense, verdict):'
SENTINEL = "get_email_recipients('expense_mismatch')"

LOGGER_BLOCK = """
# This module has no module-level logger - the existing email helpers each
# create one locally. Define one here so every function below can log without
# a NameError in the error paths, which is precisely where it would bite.
import logging

logger = logging.getLogger(__name__)

"""

NEW_FUNC = '''def send_expense_mismatch_email(expense, verdict):
    """Tell the approver an invoice disagrees with the approved amount.

    Mirrors send_expense_approved_email / send_expense_paid_email exactly - the
    same recipient registry and the same smtplib path. Django's send_mail is NOT
    used: this project authenticates with EMAIL_PASSWORD via smtplib, so a
    send_mail call would silently fail and the alert would never arrive.

    'expense_mismatch' is not a registered notification type, so the registry
    falls back to its default (the portfolio owner) - the right audience, since
    this alert is for the approver, not the user who uploaded.

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


def main():
    if not os.path.exists(TARGET):
        print('! pages/views/expenses.py not found - run from the project root')
        return 1
    with open(TARGET, encoding='utf-8', newline='') as fh:
        src = fh.read().replace('\r\n', '\n')

    if SENTINEL in src:
        print('= already fixed - nothing to do')
        return 0
    if ANCHOR not in src:
        print('! send_expense_mismatch_email not found.')
        print('  Run apply_invoice_verification.py first.')
        return 1

    # 1. module-level logger, if the injected block does not already have one
    if '\nlogger = logging.getLogger(__name__)\n' not in src:
        marker = '# Invoice verification helpers (two-way match)\n'
        marker += '# ' + '=' * 75 + '\n'
        if marker in src:
            src = src.replace(marker, marker + LOGGER_BLOCK, 1)
            print('+ module-level logger added')
        else:
            src = src.replace('\n' + ANCHOR, LOGGER_BLOCK + '\n' + ANCHOR, 1)
            print('+ module-level logger added (before the email helper)')

    # 2. replace the mismatch email function. It is the last thing in the file,
    #    so everything from the anchor to EOF is exactly that function.
    src = src[:src.index(ANCHOR)] + NEW_FUNC
    print('+ send_expense_mismatch_email rewritten to the working smtplib path')

    if CHECK:
        print('= check only - nothing written')
        return 0

    bak = TARGET + '.bak_emailfix'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding='utf-8', newline='') as fh:
        fh.write(src)
    print('\nDone. Backup: pages/views/expenses.py.bak_emailfix')
    print('Verify:  python -m py_compile pages/views/expenses.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
