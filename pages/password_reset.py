# -*- coding: utf-8 -*-
"""The one place that decides whether a set-password link is good.

Section A round A1, 1 Oct 2026. Agreed with Demetri: the administrator
stops typing passwords. A new user is created with no usable password and
an email invites them to choose one; Reset Password sends the same kind
of email; Forgot Password lets somebody ask for one themselves.

WHY THIS IS ITS OWN MODULE AND NOT PART OF views/auth.py.

  1. ONE DECISION, ONE PLACE. Four callers need to know whether a link is
     good - the set-password page, its POST, the admin reset, and the
     invitation. A helper each is how two of them end up disagreeing.

  2. IT IS TESTABLE. This module imports django.contrib.auth and nothing
     from pages.models, so test_auth_flow.py can import it under its own
     minimal settings with a sqlite database and drive REAL tokens
     against REAL users. The project's settings point at MySQL, which no
     suite can reach, so a module that pulled in pages.models could only
     ever be tested by reading its source. The email send is deferred
     inside the function for exactly this reason - keep the import light.

WHAT MAKES A TOKEN SINGLE-USE. Nothing in here. Django's
PasswordResetTokenGenerator hashes the user's current password hash into
the token, so saving a new password invalidates the token that set it -
by construction, with no used-tokens table to keep. Expiry is
settings.PASSWORD_RESET_TIMEOUT, which mysite/settings.py pins at three
days (Demetri: "3 days is fine").

WHY THE TOKEN LEAVES THE ADDRESS BAR. See URL_TOKEN below.

                                                  [test_auth_flow.py]
"""
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# The session key the token is parked under once it has been checked, and
# the word that stands in its place in the URL afterwards.
#
# WHY. The emailed link carries the real token. On the first GET the view
# checks it, puts it here, and redirects to the same URL with URL_TOKEN
# where the token was - so while the person is typing their new password
# the token is not in the address bar, not in the browser history, and not
# in any Referer header the page sends. Django's own
# PasswordResetConfirmView does precisely this; the names are ours because
# this is a function view, not that class.
SESSION_TOKEN = '_alv_set_password_token'
URL_TOKEN = 'set-password'

# Two words for the two reasons a link gets sent. They change the subject
# line and the first sentence; the mechanism is identical.
MODE_WELCOME = 'welcome'
MODE_RESET = 'reset'


def uid_of(user):
    """The user's pk, URL-safe, as it appears in a link."""
    return urlsafe_base64_encode(force_bytes(user.pk))


def user_from_uid(uidb64):
    """The user a link's uidb64 names, or None.

    EVERY WAY A HAND-EDITED URL CAN GO WRONG ARRIVES HERE, and all of them
    have to be None rather than a 500: not base64, base64 of something
    that is not a number, a number no row has, a number too large for the
    column. The tuple is the one Django's own view catches."""
    try:
        pk = urlsafe_base64_decode(uidb64).decode()
        return User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, ValidationError,
            UnicodeDecodeError, User.DoesNotExist):
        return None


def make_token(user):
    return default_token_generator.make_token(user)


def token_ok(user, token):
    """Whether `token` is this user's, unexpired, and unused.

    Guarded against None on both arguments: the caller gets user=None from
    user_from_uid for a mangled link, and an empty session value for
    somebody who typed the set-password URL by hand. Either way the answer
    is False, not an exception."""
    if user is None or not token:
        return False
    return default_token_generator.check_token(user, token)


def link_for(user, token):
    """The path half of a set-password link. The caller turns it into an
    absolute URL with request.build_absolute_uri, so the link points at
    whatever host the administrator is actually using - alivente.online in
    production, localhost in development - rather than at a hostname
    written down in a setting and wrong half the time."""
    return '/set-password/%s/%s/' % (uid_of(user), token)


# ==========================================================================
# The email itself
# ==========================================================================
def render_set_password_email(user, url, mode):
    """(subject, html, text) for an invitation or a reset.

    THE SAME BODY FOR BOTH, with one sentence different. A new user and a
    reset user do the identical thing next - follow the link, type a
    password twice - and two templates would drift."""
    name = (user.first_name or user.username).strip()
    if mode == MODE_WELCOME:
        subject = 'Welcome to Alivente Online - set your password'
        opening = ('An account has been created for you on the Alivente '
                   'Online Property Management System.')
        lead = 'To get started, choose a password:'
    else:
        subject = 'Alivente Online - set a new password'
        opening = ('A new password has been requested for your Alivente '
                   'Online account.')
        lead = 'To set a new password, follow this link:'

    html = """
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #2c3e50; line-height: 1.5; }}
        p {{ margin: 0 0 12px 0; padding: 0; }}
        .header-line {{ color: #17a2b8; font-weight: bold; }}
        .btn-wrap {{ margin: 24px 0; }}
        .btn-link {{
            display: inline-block;
            padding: 12px 22px;
            background-color: #0e7c8b;
            color: #ffffff;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 15px;
        }}
        .small {{ font-size: 12px; color: #6c757d; }}
        .raw {{ font-size: 12px; color: #6c757d; word-break: break-all; }}
    </style>
    </head>
    <body>
        <p>Dear {name},</p>
        <p><b><u class="header-line">{subject}</u></b></p>
        <p>{opening}</p>
        <p>{lead}</p>
        <div class="btn-wrap">
            <a class="btn-link" href="{url}">Set my password</a>
        </div>
        <p class="small">Your username is <b>{username}</b>. You will be
           asked to type your new password twice.</p>
        <p class="small">This link can be used once and stops working
           after three days. If it has expired, go to
           <a href="https://alivente.online/login/">alivente.online</a>
           and use Forgot password.</p>
        <p class="small">If you did not expect this email you can ignore
           it - your current password has not been changed.</p>
        <p class="raw">If the button does not work, copy this address into
           your browser:<br>{url}</p>
        <p>Best regards,<br>
        Alivente Property Management System</p>
    </body>
    </html>
    """.format(name=name, subject=subject, opening=opening, lead=lead,
               url=url, username=user.username)

    text = """Dear {name},

{subject}

{opening}

{lead}

{url}

Your username is {username}. You will be asked to type your new password
twice.

This link can be used once and stops working after three days. If it has
expired, go to https://alivente.online/login/ and use Forgot password.

If you did not expect this email you can ignore it - your current
password has not been changed.

Best regards,
Alivente Property Management System""".format(
        name=name, subject=subject, opening=opening, lead=lead,
        url=url, username=user.username)

    return subject, html, text


def send_set_password_email(user, url, mode):
    """Send the link. True if it went out, False if it did not.

    THE RETURN VALUE IS NOT DECORATION. Every caller reports False in red.
    A person waiting for an email that was never sent is the worst
    outcome this flow has, and it is also the silent one.

    The import is deferred so this module stays importable without the app
    registry - see the module docstring."""
    from pages.email_utils import send_html_email
    address = (user.email or '').strip()
    if not address:
        return False
    subject, html, text = render_set_password_email(user, url, mode)
    return send_html_email(subject, html, text,
                           {'to': [address], 'cc': [], 'all': [address]})
