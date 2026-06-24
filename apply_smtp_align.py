# -*- coding: utf-8 -*-
"""
Apply: align send_physical_invoices SMTP block to email_utils.send_issue_comments_email.

  pages/management/commands/send_physical_invoices.py
    1. env-var block: int port default, EMAIL_USER default 'demetrimanias@gmail.com',
       and '== "true"' parsing (matching email_utils exactly).
    2. TLS branch: plain starttls(), no context arg, no second ehlo().

Note: this removes the only use of `ssl` in the file. The `import ssl` line is now
unused but harmless; leave it (or strip it during the next normalization pass).

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_smtp_align.py
"""
import ast
import io
import os
import sys

CMD = os.path.join("pages", "management", "commands", "send_physical_invoices.py")

EDITS = [
    ('''        host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
        port = int(os.environ.get("EMAIL_PORT", "465"))
        user = os.environ.get("EMAIL_USER")
        password = os.environ.get("EMAIL_PASSWORD")
        use_ssl = os.environ.get("EMAIL_USE_SSL", "True").lower() in ("1", "true", "yes")
        use_tls = os.environ.get("EMAIL_USE_TLS", "False").lower() in ("1", "true", "yes")''',
     '''        host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
        port = int(os.environ.get("EMAIL_PORT", 465))
        user = os.environ.get("EMAIL_USER", "demetrimanias@gmail.com")
        password = os.environ.get("EMAIL_PASSWORD")
        use_ssl = os.environ.get("EMAIL_USE_SSL", "True").lower() == "true"
        use_tls = os.environ.get("EMAIL_USE_TLS", "False").lower() == "true"'''),

    ('''                server = smtplib.SMTP(host, port, timeout=10)
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()''',
     '''                server = smtplib.SMTP(host, port, timeout=10)
                server.ehlo()
                if use_tls:
                    server.starttls()'''),
]


def main():
    if not os.path.exists(CMD):
        sys.exit("MISSING FILE: %s" % CMD)
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