# -*- coding: utf-8 -*-
"""
Apply: prettify the physical-invoice review reminder to match the house style
(HTML + plain-text, "Dear User," opener, bold/underlined header, bulleted
drafts, sign-off). Subject and recipient logic unchanged.

  pages/management/commands/prepare_physical_invoices.py
    + import MIMEMultipart
    ~ build text_body + html_body (bulleted, two-decimal amounts, singular/
      plural grammar) in place of the old single-line body
    ~ send as multipart/alternative (text + html) instead of plain MIMEText

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_prepare_reminder_pretty.py
"""
import ast
import io
import os
import sys

CMD = os.path.join("pages", "management", "commands",
                   "prepare_physical_invoices.py")

EDITS = [
    # 1) import MIMEMultipart
    ("from email.header import Header\nfrom email.mime.text import MIMEText",
     "from email.header import Header\n"
     "from email.mime.multipart import MIMEMultipart\n"
     "from email.mime.text import MIMEText"),

    # 2) build the HTML + text bodies (replaces the single-line body)
    ('''        body_lines = [f"{r['number']}  {r['tenant']} ({r['property']})  €{r['total']}" for r in rows]
        body = ("The following physical invoices for {0} are still in DRAFT and need "
                "approving:\\n\\n{1}\\n\\nApprove them in Alivente before the 1st.").format(
                    period_first.strftime("%B %Y"), "\\n".join(body_lines))
        subject = f"Physical invoices to approve — {period_first:%B %Y} ({len(rows)} pending)"''',
     '''        month_label = period_first.strftime("%B %Y")
        count = len(rows)
        invoice_word = "invoice" if count == 1 else "invoices"
        is_are = "is" if count == 1 else "are"
        needs = "needs" if count == 1 else "need"
        them = "it" if count == 1 else "them"
        subject = f"Physical invoices to approve — {month_label} ({count} pending)"

        html_items = "".join(
            f"<li><b>{r['number']}</b> — {r['tenant']} ({r['property']}) "
            f"— €{r['total']:,.2f}</li>"
            for r in rows)
        text_items = "".join(
            f"\\n \\u2022 {r['number']}  {r['tenant']} ({r['property']})  €{r['total']:,.2f}"
            for r in rows)

        html_body = f"""
        <html>
        <head>
        <style>
        p {{ margin: 0; padding: 0; }}
        ul {{ margin: 0; padding: 0; padding-left: 20px; }}
        li {{ margin: 0; padding: 0; margin-bottom: 8px; }}
        .header {{ color: #cc0000; font-weight: bold; }}
        </style>
        </head>
        <body>
            <p>Dear User,</p>
            <br>
            <p><b><u class="header">PHYSICAL INVOICES TO APPROVE \\u2014 {month_label.upper()} ({count}):</u></b></p>
            <p>The following physical {invoice_word} for {month_label} {is_are} still in DRAFT and {needs} approving:</p>
            <br>
            <ul>{html_items}</ul>
            <br>
            <p>Please log into the Alivente Online System to approve {them} before the 1st.</p>
            <br>
            <p>Best regards,<br>
            Alivente Property Management System<br>
            Automated Report</p>
        </body>
        </html>
        """

        text_body = (
            "Dear User,\\n\\n"
            f"PHYSICAL INVOICES TO APPROVE \\u2014 {month_label.upper()} ({count}):\\n"
            f"The following physical {invoice_word} for {month_label} {is_are} "
            f"still in DRAFT and {needs} approving:\\n"
            f"{text_items}\\n\\n"
            f"Please log into the Alivente Online System to approve {them} "
            "before the 1st.\\n\\n"
            "Best regards,\\n"
            "Alivente Property Management System\\n"
            "Automated Report"
        )'''),

    # 3) send as multipart/alternative (text + html)
    ('''        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = email_user
        msg['To'] = ", ".join(to_list)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        msg['Subject'] = Header(subject, 'utf-8')''',
     '''        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = ", ".join(to_list)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))'''),
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