# -*- coding: utf-8 -*-
"""lease_email.py - the e-signing emails, branded. ES-7, 25 Oct 2026.

HIS DECISION OF 25 OCTOBER: "add the Alivente branding (small) to the
emails", and NO contact details. So every e-signing email is sent as
plain text AND as a small HTML version carrying the Alivente logo - the
same words in both, so a mail program that shows only text loses nothing
but the logo.

NB-1, 26 Oct 2026 - THE LOGO SIGNS OFF, his decision on Live: under
"Alivente Limited" at the foot of the email, not above "Dear ...", and a
little bigger.

THE LOGO TRAVELS WITH THE MESSAGE (an inline cid: image), not as a link
to the website: a tenant's mail program that blocks remote images still
shows it, and nothing about the tenant is leaked by fetching it.

MIME SHAPE, the one every mail program agrees on:
    mixed -> [ related -> [ alternative -> [plain, html], logo ], pdf... ]
without attachments the outer `mixed` is dropped.

THE SAME LOGO FILE THE INVOICE EMAILS USE (settings.PHYSICAL_INVOICE_
EMAIL_LOGO), so there is one picture of the company and one place to
change it. If it is missing the email still goes - plain, as before.
"""
import os
import re
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.message import SafeMIMEMultipart, SafeMIMEText
from django.utils.html import escape

LOGO_CID = 'alivente_logo'
# SMALL - his word. The invoice footer draws it at 90px; a header that
# introduces a lease link wants to be a line, not a letterhead.
# NB-1, 26 Oct 2026 - "slightly bigger", under the sign-off. (was 56)
LOGO_HEIGHT = 72


def _logo():
    path = getattr(settings, 'PHYSICAL_INVOICE_EMAIL_LOGO', '') or ''
    try:
        if path and os.path.exists(path):
            with open(path, 'rb') as fh:
                return fh.read()
    except OSError:
        pass
    return None


def html_for(text, with_logo):
    """The plain body as a small branded HTML page - the same words."""
    body = escape(text.strip())
    # LINKS STAY LINKS. The signing link is the whole point of the email.
    body = re.sub(r'(https?://[^\s<]+)',
                  r'<a href="\1" style="color:#0e7c8b;">\1</a>', body)
    body = body.replace('\n', '<br>\n')
    logo = ('<img src="cid:%s" alt="Alivente Limited" height="%d" '
            'style="height:%dpx;width:auto;display:block;margin:10px 0 0;">'
            % (LOGO_CID, LOGO_HEIGHT, LOGO_HEIGHT)) if with_logo else ''
    return ('<!DOCTYPE html>\n<html><body style="margin:0;padding:24px;'
            'font-family:Arial,Helvetica,sans-serif;font-size:15px;'
            'line-height:1.5;color:#21343c;">\n'
            '<div style="max-width:600px;"><div>%s</div>\n%s</div>\n'
            '</body></html>' % (body, logo))


class BrandedEmail(EmailMessage):
    """An EmailMessage with an HTML twin and an inline logo.

    `body` stays the plain text, so everything that reads a sent email's
    body (the suites, the locmem outbox) reads exactly what it did.
    """

    def __init__(self, subject='', body='', to=None, **kw):
        super().__init__(subject=subject, body=body, to=to, **kw)
        self.logo = _logo()
        self.html = html_for(body, bool(self.logo))

    def _create_message(self, msg):
        alt = SafeMIMEMultipart(_subtype='alternative',
                                encoding=self.encoding)
        alt.attach(msg)
        alt.attach(SafeMIMEText(self.html, 'html',
                                self.encoding or settings.DEFAULT_CHARSET))
        if self.logo:
            rel = SafeMIMEMultipart(_subtype='related',
                                    encoding=self.encoding)
            rel.attach(alt)
            img = MIMEImage(self.logo, 'png')
            img.add_header('Content-ID', '<%s>' % LOGO_CID)
            img.add_header('Content-Disposition', 'inline',
                           filename='alivente.png')
            rel.attach(img)
            top = rel
        else:
            top = alt
        if not self.attachments:
            return top
        mixed = SafeMIMEMultipart(_subtype='mixed', encoding=self.encoding)
        mixed.attach(top)
        for att in self.attachments:
            if isinstance(att, tuple):
                mixed.attach(self._create_attachment(*att))
            else:
                mixed.attach(att)
        return mixed
