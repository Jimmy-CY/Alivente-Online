# -*- coding: utf-8 -*-
"""
Apply: switch prepare_physical_invoices' review reminder from Django's
EmailMessage backend to the raw smtplib + EMAIL_* path the project's other
crons use (matching check_lease_renewal_and_invoices: single attempt,
timeout=60, SMTP_SSL/STARTTLS, From = EMAIL_USER).

  pages/management/commands/prepare_physical_invoices.py
    - drop  from django.core.mail import EmailMessage
    + add   os, smtplib, email.header.Header, email.mime.text.MIMEText imports
    ~ rewrite the reminder send block to use raw smtplib via EMAIL_* env vars

No model/template/migration changes. Recipient lookup (NotificationRecipient
for 'physical_invoice_review') is unchanged.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_prepare_smtp_align.py
"""
import ast
import io
import os
import sys

CMD = os.path.join("pages", "management", "commands",
                   "prepare_physical_invoices.py")

EDITS = [
    # 1) stdlib imports for raw smtplib + MIME
    ("from datetime import date, timedelta\nfrom decimal import Decimal",
     "import os\nimport smtplib\nfrom datetime import date, timedelta\n"
     "from decimal import Decimal\nfrom email.header import Header\n"
     "from email.mime.text import MIMEText"),

    # 2) drop the EmailMessage import
    ("from django.conf import settings\n"
     "from django.core.mail import EmailMessage\n"
     "from django.core.management.base import BaseCommand",
     "from django.conf import settings\n"
     "from django.core.management.base import BaseCommand"),

    # 3) rewrite the send block
    ('''        if not to_list:
            self.stdout.write(self.style.WARNING(
                f"No recipients configured for '{REMINDER_TYPE}'; reminder not sent."))
            return
        try:
            EmailMessage(
                subject=subject, body=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=to_list, cc=cc_list,
            ).send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(
                f"Reminder sent to {len(to_list)} recipient(s) ({len(rows)} draft(s))."))
        except Exception as exc:  # don't let a mail failure abort the cron
            self.stderr.write(self.style.ERROR(f"Reminder send failed: {exc}"))''',
     '''        if not to_list:
            self.stdout.write(self.style.WARNING(
                f"No recipients configured for '{REMINDER_TYPE}'; reminder not sent."))
            return

        # Raw smtplib via the EMAIL_* env vars, matching the project's other
        # cron mailers (check_lease_renewal_and_invoices) so this uses the same
        # proven path as everything else rather than Django's mail backend.
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            self.stderr.write(self.style.ERROR(
                "EMAIL_PASSWORD not set; reminder not sent."))
            return

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = email_user
        msg['To'] = ", ".join(to_list)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        msg['Subject'] = Header(subject, 'utf-8')

        smtp_object = None
        try:
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            smtp_object.login(email_user, email_password)
            smtp_object.sendmail(email_user, to_list + cc_list, msg.as_string())
            self.stdout.write(self.style.SUCCESS(
                f"Reminder sent to {len(to_list)} recipient(s) ({len(rows)} draft(s))."))
        except Exception as exc:  # don't let a mail failure abort the cron
            self.stderr.write(self.style.ERROR(f"Reminder send failed: {exc}"))
        finally:
            if smtp_object is not None:
                try:
                    smtp_object.quit()
                except Exception:
                    pass'''),
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