# -*- coding: utf-8 -*-
"""
Apply: Phase 5b step 1 — extract the shared invoice-email service and repoint the
monthly send cron at it (so the cron and the upcoming customer Send-now view use
ONE copy of the footer / logo / body / SMTP code).

Prereq: copy pages/services/invoice_email.py into place first (delivered earlier;
unchanged). That module is a verbatim lift of the cron's email pieces, so the
cron's behaviour is unchanged.

  pages/management/commands/send_physical_invoices.py
    + import LOGO_PATH, assemble_bodies, load_logo, send_invoice_email
    - delete the duplicated module block (LOGO_PATH, FOOTER_TEXT, _footer_html)
    - delete _load_logo + _send_invoice_email (and the e-mail banner comment)
    ~ _assemble_bodies delegates footer+HTML to the service
    ~ repoint the two call sites

A few now-unused MIME imports remain at the top of the cron; left intentionally
(removing them is cosmetic, out of scope for this behaviour-preserving refactor).

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_invoice_email_extract.py
"""
import ast
import io
import os
import sys

CRON = os.path.join("pages", "management", "commands", "send_physical_invoices.py")

E1_OLD = r'''from pages.views.physical_invoices import (
    build_context_from_invoice,
    render_physical_invoice_pdf,
)'''

E1_NEW = r'''from pages.services.invoice_email import (
    LOGO_PATH, assemble_bodies, load_logo, send_invoice_email,
)
from pages.views.physical_invoices import (
    build_context_from_invoice,
    render_physical_invoice_pdf,
)'''

E2_OLD = r'''CLIENT_NOTIFICATION_TYPE = "physical_invoice_client"

# Inline signature logo (PNG). Set PHYSICAL_INVOICE_EMAIL_LOGO in settings.py to
# the absolute path of your Alivente logo, or adjust the fallback below. If the
# file is not found the e-mail still sends, just without the logo.
LOGO_PATH = getattr(settings, "PHYSICAL_INVOICE_EMAIL_LOGO", "") or os.path.join(
    getattr(settings, "BASE_DIR", ""), "pages", "static", "images", "alivente_logo.png"
)

# Fixed signature / contact footer. One place to change it.
FOOTER_TEXT = (
    "Kind Regards,\n\n"
    "Demetris Manias\n"
    "Executive Director\n\n"
    "Address: Alivente House, Dikaiosynis 13A, Engomi, 2412, Nicosia, Cyprus\n"
    "Tel: +357-22-222202 | Mobile: +357-96-668557\n"
    "Email: demetri.manias@alivente.com | Website: www.alivente.com"
)


def _footer_html(include_logo):
    logo = ('<p><img src="cid:alivente_logo" alt="Alivente Limited" '
            'style="height: 90px;"></p>\n') if include_logo else ""
    return (
        '<p>&nbsp;</p>\n'
        '<p>Kind Regards,</p>\n'
        '<p>&nbsp;</p>\n'
        '<p>Demetris Manias<br>\n<em>Executive Director</em></p>\n'
        + logo +
        '<p><strong>Address:</strong> Alivente House, Dikaiosynis 13A, Engomi, '
        '2412, Nicosia, Cyprus<br>\n'
        '<strong>Tel:</strong> +357-22-222202 | '
        '<strong>Mobile:</strong> +357-96-668557<br>\n'
        '<strong>Email:</strong> '
        '<a href="mailto:demetri.manias@alivente.com">demetri.manias@alivente.com</a> '
        '| <strong>Website:</strong> '
        '<a href="https://www.alivente.com">www.alivente.com</a></p>'
    )


class Command(BaseCommand):'''

E2_NEW = r'''CLIENT_NOTIFICATION_TYPE = "physical_invoice_client"


class Command(BaseCommand):'''

E3_OLD = r'''    def _assemble_bodies(self, saved_body, tenant_name, period_label, include_logo):
        """Return (text_body, html_body). {month} -> period_label in the saved
        body; a blank saved body falls back to a generic default."""
        saved_body = (saved_body or "").strip()
        if saved_body:
            core = saved_body.replace("{month}", period_label)
        else:
            core = (f"Dear {tenant_name},\n\n"
                    f"Please find attached the rental invoice for {period_label}.")

        text_body = core + "\n\n" + FOOTER_TEXT
        html_core = escape(core).replace("\n", "<br>\n")
        html_body = (
            "<!DOCTYPE html>\n<html>\n"
            '<body style="font-family: Calibri, Arial, sans-serif; '
            'font-size: 11pt; color: #000;">\n'
            f"<div>{html_core}</div>\n"
            f"{_footer_html(include_logo)}\n"
            "</body>\n</html>"
        )
        return text_body, html_body'''

E3_NEW = r'''    def _assemble_bodies(self, saved_body, tenant_name, period_label, include_logo):
        """Resolve the per-tenant core (token + generic default), then delegate
        to the shared assembler for footer + HTML wrap."""
        saved_body = (saved_body or "").strip()
        if saved_body:
            core = saved_body.replace("{month}", period_label)
        else:
            core = (f"Dear {tenant_name},\n\n"
                    f"Please find attached the rental invoice for {period_label}.")
        return assemble_bodies(core, include_logo)'''

E4_OLD = r'''    def _load_logo(self):
        """Logo bytes for inline embedding, or None if the file is absent."""
        try:
            if LOGO_PATH and os.path.exists(LOGO_PATH):
                with open(LOGO_PATH, "rb") as fh:
                    return fh.read()
        except OSError:
            pass
        return None

    # ------------------------------------------------------------------ #
    # e-mail (raw smtplib via EMAIL_* env vars)
    #
    # NOTE: confirm this block against email_utils.send_issue_comments_email.
    # If your SMTP wiring differs, THIS is the only method to align.
    # ------------------------------------------------------------------ #
    def _send_invoice_email(self, to_addr, cc_list, subject, text_body, html_body,
                            pdf_bytes, filename, logo_bytes):
        host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
        port = int(os.environ.get("EMAIL_PORT", 465))
        user = os.environ.get("EMAIL_USER", "demetrimanias@gmail.com")
        password = os.environ.get("EMAIL_PASSWORD")
        use_ssl = os.environ.get("EMAIL_USE_SSL", "True").lower() == "true"
        use_tls = os.environ.get("EMAIL_USE_TLS", "False").lower() == "true"

        # related: the HTML/text alternative + the inline logo it references.
        related = MIMEMultipart("related")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(text_body, "plain", "utf-8"))
        alt.attach(MIMEText(html_body, "html", "utf-8"))
        related.attach(alt)
        if logo_bytes:
            img = MIMEImage(logo_bytes)
            img.add_header("Content-ID", "<alivente_logo>")
            img.add_header("Content-Disposition", "inline", filename="alivente_logo.png")
            related.attach(img)

        # mixed: the related body + the PDF attachment.
        msg = MIMEMultipart("mixed")
        msg["From"] = user
        msg["To"] = to_addr
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        msg["Subject"] = Header(subject, "utf-8")
        msg.attach(related)

        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

        recipients = [to_addr] + list(cc_list or [])

        server = None
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                server.ehlo()
                if use_tls:
                    server.starttls()
            server.login(user, password)
            server.sendmail(user, recipients, msg.as_string())
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # handle
    # ------------------------------------------------------------------ #
    def handle'''

E4_NEW = r'''    # ------------------------------------------------------------------ #
    # handle
    # ------------------------------------------------------------------ #
    def handle'''

E5_OLD = r'''        logo_bytes = self._load_logo()'''

E5_NEW = r'''        logo_bytes = load_logo()'''

E6_OLD = r'''                try:
                    self._send_invoice_email(to_addr, cc_list, subject, text_body,
                                             html_body, pdf_bytes, filename, logo_bytes)'''

E6_NEW = r'''                try:
                    send_invoice_email(to_addr, cc_list, subject, text_body,
                                       html_body, pdf_bytes, filename, logo_bytes)'''

EDITS = [(E1_OLD, E1_NEW), (E2_OLD, E2_NEW), (E3_OLD, E3_NEW),
         (E4_OLD, E4_NEW), (E5_OLD, E5_NEW), (E6_OLD, E6_NEW)]


def main():
    if not os.path.exists(CRON):
        sys.exit("ABORTED - missing file: %s" % CRON)
    with io.open(CRON, "r", encoding="utf-8") as fh:
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
        sys.exit("ABORTED - %s does not parse: %s" % (CRON, e))

    with io.open(CRON + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(CRON, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (CRON, CRON))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()