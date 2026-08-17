#!/usr/bin/env python3
"""
apply_mismatch_notification_type.py
===================================

Register 'expense_mismatch' as a configurable notification type, so the
invoice-mismatch alert recipients can be set from
Administration -> Notification Settings like every other alert.

Three edits are needed, not one - adding the choice alone is not enough:

  pages/models.py            add the choice to NotificationRecipient
                             .NOTIFICATION_TYPES (without it the DB row is
                             invalid and the admin form cannot offer it)
  pages/views/notifications.py  add it to the `admin_types` allow-list (the
                             settings screen only renders types listed there)
  pages/email_utils.py       add an explicit hardcoded default, so the
                             fallback is documented rather than relying on
                             the catch-all at the bottom of the function

Creates: pages/migrations/0090_notification_type_expense_mismatch.py

Behaviour is unchanged until you set recipients in the UI: the default stays
demetrimanias@gmail.com with no CC. Once a row exists it takes precedence.

Idempotent; backs up each file. Run from the project root:

    python apply_mismatch_notification_type.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
report = []
failed = False

NEW_CHOICE = "        ('expense_mismatch', 'Expense Invoice Mismatch'),\n"


def edit(path, pairs, tag, sentinel):
    """pairs = [(old, new)]; every old must appear exactly once."""
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

    for old, _ in pairs:
        if src.count(old) != 1:
            report.append('! %s: anchor matched %d times, expected 1' % (path, src.count(old)))
            failed = True
            return
    for old, new in pairs:
        src = src.replace(old, new, 1)

    if CHECK:
        report.append('+ %s would be patched' % path)
        return
    bak = full + '.bak_' + tag
    if not os.path.exists(bak):
        shutil.copy2(full, bak)
    with open(full, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)
    report.append('+ %s patched' % path)


# 1. the model choice -------------------------------------------------------
MODELS_OLD = "        ('expense_paid', 'Expense Paid'),\n"
MODELS_NEW = MODELS_OLD + NEW_CHOICE

# 2. the settings-screen allow-list ----------------------------------------
VIEW_OLD = "        'expense_paid',\n"
VIEW_NEW = VIEW_OLD + "        'expense_mismatch',\n"

# 3. the documented default ------------------------------------------------
UTILS_OLD = ("        'expense_paid': {'to': ['stella.simitopoulos@alivente.com'], "
             "'cc': ['demetrimanias@gmail.com']},\n")
UTILS_NEW = UTILS_OLD + (
    "        # Invoice-mismatch alerts go to the APPROVER only. Approved/paid\n"
    "        # notices are for the person doing the work; a mismatch is the\n"
    "        # approver's decision, so Stella is deliberately not copied.\n"
    "        'expense_mismatch': {'to': ['demetrimanias@gmail.com'], 'cc': []},\n")

MIGRATION_NAME = 'pages/migrations/0090_notification_type_expense_mismatch.py'
CHOICES = [
    ('celebration_reminder', 'Celebration Reminders'),
    ('document_expiry', 'Document Expiry Alerts'),
    ('daily_report', 'Daily Property Management Report'),
    ('new_lease_upload', 'New Lease Upload Reminders'),
    ('expense_needs_approval', 'Expense Needs Approval'),
    ('expense_approved', 'Expense Approved'),
    ('expense_paid', 'Expense Paid'),
    ('expense_mismatch', 'Expense Invoice Mismatch'),
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
    """Add 'expense_mismatch' to the notification-type choices.

    Choices-only change: no column alteration, no data migration, no risk to
    existing rows. It exists so the invoice-mismatch alert can be configured
    from Administration -> Notification Settings.
    """

    dependencies = [
        ('pages', '0089_invoice_verification'),
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
    global failed
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
    print('Register expense_mismatch notification type - %s\n'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    edit('pages/models.py', [(MODELS_OLD, MODELS_NEW)], 'mismatchnotif', "'expense_mismatch'")
    edit('pages/views/notifications.py', [(VIEW_OLD, VIEW_NEW)], 'mismatchnotif', "'expense_mismatch'")
    edit('pages/email_utils.py', [(UTILS_OLD, UTILS_NEW)], 'mismatchnotif', "'expense_mismatch'")
    write_migration()

    for line in report:
        print('  ' + line)
    if failed:
        print('\nNothing was written for the failing file(s).')
        return 1
    if not CHECK:
        print('\nNext:')
        print('  python manage.py makemigrations --check --dry-run   # expect: No changes detected')
        print('  git add -A && git commit -m "Configurable recipients for invoice mismatch alerts" && git push')
        print('\nThen: Administration -> Notification Settings -> "Expense Invoice Mismatch"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
