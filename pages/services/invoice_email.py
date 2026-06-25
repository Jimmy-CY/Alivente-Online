# -*- coding: utf-8 -*-
"""
Shared invoice-email assembly + delivery.

One place for the look and the SMTP wiring of every physical-invoice e-mail,
used by BOTH the monthly tenant send cron (send_physical_invoices) and the
on-demand customer Send-now view. Raw smtplib via the EMAIL_* env vars, matching
email_utils.send_issue_comments_email -- NOT Django's mail backend.

MIME shape:  mixed -> [ related -> [ alternative -> [plain, html], logo ],
                        pdf attachment ].
"""

import os
import smtplib
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.utils.html import escape

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


def footer_html(include_logo):
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


def assemble_bodies(core_text, include_logo):
    """(text_body, html_body) from a ready core message + the shared footer.
    The caller supplies the fully-resolved core (greeting + body, tokens already
    substituted); this only appends the footer and builds the HTML wrapper."""
    core_text = (core_text or "").strip()
    text_body = core_text + "\n\n" + FOOTER_TEXT
    html_core = escape(core_text).replace("\n", "<br>\n")
    html_body = (
        "<!DOCTYPE html>\n<html>\n"
        '<body style="font-family: Calibri, Arial, sans-serif; '
        'font-size: 11pt; color: #000;">\n'
        f"<div>{html_core}</div>\n"
        f"{footer_html(include_logo)}\n"
        "</body>\n</html>"
    )
    return text_body, html_body


def load_logo():
    """Logo bytes for inline embedding, or None if the file is absent."""
    try:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as fh:
                return fh.read()
    except OSError:
        pass
    return None


def send_invoice_email(to_addr, cc_list, subject, text_body, html_body,
                       pdf_bytes, filename, logo_bytes):
    """Deliver one invoice e-mail (raw smtplib via EMAIL_* env vars)."""
    host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_PORT", 465))
    user = os.environ.get("EMAIL_USER", "demetrimanias@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD")
    use_ssl = os.environ.get("EMAIL_USE_SSL", "True").lower() == "true"
    use_tls = os.environ.get("EMAIL_USE_TLS", "False").lower() == "true"

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