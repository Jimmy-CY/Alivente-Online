# -*- coding: utf-8 -*-
"""SECTION A, ROUND A1 - THE LOGIN SCREEN AND SET-PASSWORD-BY-EMAIL

Demetri, 1 Oct 2026, in three findings and five answers:

  1. "I don't think that we need to have the word Login showing twice on
     the Login Screen. Also, if a user attempts to Login, and their
     credentials are incorrect, the system must show a red message
     stating the Login credentials are incorrect."
  2. "We don't need to have these two messages showing after you log in."
  3. "If I reset a user's Password, I should get a popup... it needs to
     draft a standard Password Reset email... In the email, they should
     have a link that takes them to the application... where they are
     then forced to re-enter a new password (twice)."
     And: Forgot Password, with a notice to the admin. 3 days. Email
     required on Add User. From demetrimanias@gmail.com. The admin user
     is treated exactly the same way.

WHY ALL OF IT IS ONE ROUND. The password field comes OFF user_add and
user_edit in the same change that puts the email flow in. Ship half and
there is a window in which nobody can set anybody's password at all -
either the field is gone with no email to replace it, or the email
arrives at a page that does not exist. The two halves are one change.

--------------------------------------------------------------------
FINDING 2 IS CAUSED BY FINDING 1, WHICH IS WHY THE LOOP IS NOT OPTIONAL
--------------------------------------------------------------------
login.html has no `{% for msg in messages %}` loop. The old view did:

    messages.error(request, 'Error Logging In - Please Try Again !!')
    return redirect('login')

Django's message framework keeps a message until a template ITERATES it.
login.html never did - so the red error sat in the session and surfaced
on the first page that had a loop, which is the page AFTER the next
successful login. That is finding 2: a stale message about a previous
visit. It is not a second bug; it is the same bug seen from the other
end. Adding the loop is what makes finding 1's red message possible AND
what stops finding 2 happening again.

----------------------------------------------
WHAT A RESET DOES AND DELIBERATELY DOES NOT DO
----------------------------------------------
Pressing Reset Password does NOT take the old password away. It emails a
link; the old password keeps working until the person uses it. That is
Django's own design and it is the fail-safe order: if the email never
arrives - wrong address, SMTP down, Gmail throttling - the person is
exactly as able to log in as they were a minute ago. Clear the password
first and a failed send locks somebody out of a system they could reach
before an administrator tried to help them.

The one place a password IS cleared is user_add, because there is no old
password to lose. create_user with password=None leaves an unusable hash
and the invitation email is the only way in - which is the whole point.

AND THE SEND FAILURE IS REPORTED LOUDLY. send_html_email returns a bool.
Every caller here checks it and says so in red. A silent failure here
means a person waits for an email that was never sent.

----------------------------------
WHY THE TOKEN LEAVES THE ADDRESS BAR
----------------------------------
The link carries uidb64 and a token. On the first GET the view checks the
token, parks it in the session, and REDIRECTS to the same URL with the
literal word set-password in the token's place - Django's own
PasswordResetConfirmView does exactly this. The token is then out of the
address bar, out of the browser history and out of any Referer header the
page emits, while the form is being filled in.

It is single-use by construction, not by bookkeeping: the token is
derived from the password hash, so the moment the new password is saved
the token that set it stops checking out. And three days is the expiry -
Django's PASSWORD_RESET_TIMEOUT default, which this round writes down
explicitly rather than inheriting, because a default that changes in a
Django upgrade would change an agreed decision silently.

-----------------------------------------
THE FOUR VALIDATORS, ENFORCED FOR THE FIRST TIME
-----------------------------------------
settings.py has configured AUTH_PASSWORD_VALIDATORS since the project
started - similarity, minimum length, common passwords, all-numeric.
Nothing ran them. user_add and user_edit checked `len(password1) < 8` by
hand and called set_password directly, which does not validate. So
`password` and `12345678` were both accepted by the system that had been
configured to refuse them.

The new page uses django.contrib.auth.forms.SetPasswordForm, which runs
validate_password against the configured list. Those four start being
enforced in this round. test_auth_flow.py section 4 drives real
passwords through a real form and shows which ones are refused.

-------------------------------
NO ACCOUNT ENUMERATION, AND NO LOCKOUT EITHER
-------------------------------
Forgot Password answers the same way whether the address is registered or
not. The login error is the same whether the username exists or not.

That leaves one real problem: an invited person who has never set a
password gets told their credentials are incorrect, which is true and
useless. The fix is NOT a conditional hint - that would answer "does this
username exist". The login page carries a PERMANENT line instead, visible
to everyone, which says that a new account or a forgotten password both
start at the same link. Zero leak and the lockout cannot happen.

The one conditional message kept is the disabled account - and it only
appears when the password submitted was CORRECT, so it tells the person
nothing they did not already know. Demetrios is exactly this case: a
superuser with ACTIVE=NO, who would otherwise get "incorrect" forever
with the right password in hand.

------------------------------------
THE 16TH NOTIFICATION TYPE, AND THE LIST THAT WOULD HAVE SWALLOWED IT
------------------------------------
'password_reset_requested' is added to NotificationRecipient so the admin
notice is configurable from Administration -> Notification Settings
rather than hardcoded. Choices-only AlterField, same shape as migration
0090.

Adding it to the model is NOT ENOUGH. notification_settings() in
pages/views/notifications.py iterates NOTIFICATION_TYPES and then filters
through a HARDCODED admin_types list - a type missing from that list
renders nowhere, with no error. This round adds it to both. The suite
checks both, because the next person to add a type will hit this.

Suppressed when the requester is the recipient: an administrator
resetting their own password does not need an email telling them that
somebody reset their password.

Backups: .bak_authflow. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_authflow'
CRLF = {}
SENTINEL = 'test_auth_flow.py'

ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('A1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's OWN line endings.

    THE TRAP THIS CLOSES, hit in P2 four hours before this was written:
    reading a template with open(encoding='utf-8') hides its line endings
    because text mode translates \\r\\n to \\n. The patcher reads BYTES, so
    every multi-line anchor written with \\n missed in a CRLF file and the
    round reported nothing to do. Every anchor goes through here."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('A1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def new_file(rel, body, what):
    """Create a file this round introduces. No backup: there is nothing to
    back up, and a .bak_ of an empty file would be a lie about what was
    there before. Idempotent by content."""
    path = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.isfile(path):
        with open(path, 'rb') as fh:
            have = fh.read().decode('utf-8')
        if SENTINEL in have:
            print('  %-42s already there' % rel)
            return path
        raise SystemExit('A1: %s exists and is not ours' % rel)
    if not CHECK:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, 'wb') as fh:
            fh.write(body.replace('\r\n', '\n').encode('utf-8'))
    print('  %-42s NEW  %s' % (rel, what))
    return path


# ==========================================================================
# THE NEW MODULE - the one place that decides whether a link is good
# ==========================================================================
PASSWORD_RESET_PY = '''# -*- coding: utf-8 -*-
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
'''


# ==========================================================================
# THE THREE NEW PAGES
# ==========================================================================
PASSWORD_SET_HTML = '''{% extends 'base.html' %}

{% block title %}Set Your Password{% endblock %}

{% block content %}
<style>
/* A PUBLIC PAGE, SO IT CANNOT ASSUME A LOGGED-IN WIDTH. Everything below
   is base's own names and base's own variables; the only page rules are
   the two-column drop and the strength meter, which no other screen has.
                                                  [test_auth_flow.py] */
.pw-set-wrap { max-width: 520px; margin: 0 auto; }
.pw-set-rules { font-size: 12.5px; color: var(--alv-ink-soft); margin: 0 0 18px 0; padding-left: 20px; }
.pw-set-rules li { margin-bottom: 3px; }
.pw-strength { height: 5px; border-radius: 3px; background: var(--alv-neutral-soft); margin-top: 8px; }
.pw-strength-bar { height: 100%; width: 0; border-radius: 3px; transition: width .2s; }
.pw-strength-weak   { width: 33%; background: var(--alv-bad); }
.pw-strength-medium { width: 66%; background: var(--alv-warn); }
.pw-strength-strong { width: 100%; background: var(--alv-good); }
.pw-note { font-size: 12.5px; margin-top: 6px; min-height: 18px; }
.pw-note-bad  { color: var(--alv-bad); }
.pw-note-good { color: var(--alv-good); }
</style>

<div class="pw-set-wrap">

    <h2 class="page-title-h2">SET YOUR PASSWORD</h2>
    <br/>

    {% for msg in messages %}
      <div class="alert alert-{{ msg.tags }} alert-dismissible fade show alv-message" role="alert">
        {{ msg }}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    {% endfor %}

    <div class="form-card">
        <h3 class="form-section-title"><i class="fas fa-lock"></i> Choose a password for {{ target.username }}</h3>

        <p class="text-muted" style="font-size:13px;">
            Type it twice. The second box has to match the first.
        </p>
        <ul class="pw-set-rules">
            <li>At least 8 characters.</li>
            <li>Not a password that appears on lists of common passwords.</li>
            <li>Not all numbers.</li>
            <li>Not too similar to your username, name or email address.</li>
        </ul>

        <form method="POST">
            {% csrf_token %}
            <div class="form-group">
                <label for="new_password1"><strong>New Password</strong> <span class="alv-req">*</span></label>
                <div class="input-group">
                    <input type="password" name="new_password1" id="new_password1"
                           class="form-control" placeholder="Enter new password"
                           autocomplete="new-password" required>
                    <div class="input-group-append">
                        <button class="btn action-secondary" type="button" id="togglePw1"
                                aria-label="Show or hide the password">
                            <i class="fas fa-eye" id="eyePw1"></i>
                        </button>
                    </div>
                </div>
                <div class="pw-strength"><div class="pw-strength-bar" id="pwBar"></div></div>
                <div class="pw-note" id="pwNote"></div>
            </div>
            <div class="form-group">
                <label for="new_password2"><strong>Confirm New Password</strong> <span class="alv-req">*</span></label>
                <input type="password" name="new_password2" id="new_password2"
                       class="form-control" placeholder="Type it again"
                       autocomplete="new-password" required>
                <div class="pw-note" id="matchNote"></div>
            </div>
            <div class="page-action-buttons">
                <button type="submit" class="btn action-primary">
                    <i class="fas fa-check"></i> Save Password
                </button>
            </div>
        </form>
    </div>

</div>

<script>
/* THE METER IS A COURTESY AND NOT THE CHECK. What a password has to pass
   is decided on the SERVER by Django's four configured validators, which
   this round starts enforcing. A green bar here means the four guesses
   below liked it, nothing more - so this script never disables the
   button and never blocks a submit. */
(function () {
  var p1 = document.getElementById('new_password1');
  var p2 = document.getElementById('new_password2');
  if (!p1 || !p2) return;

  var bar = document.getElementById('pwBar');
  var note = document.getElementById('pwNote');
  var match = document.getElementById('matchNote');

  function score(v) {
    var n = 0;
    if (v.length >= 8) n++;
    if (/[A-Z]/.test(v)) n++;
    if (/[0-9]/.test(v)) n++;
    if (/[^A-Za-z0-9]/.test(v)) n++;
    return n;
  }

  function paint() {
    var v = p1.value;
    if (!v.length) {
      bar.className = 'pw-strength-bar';
      note.textContent = '';
      note.className = 'pw-note';
    } else {
      var n = score(v);
      if (n <= 1) {
        bar.className = 'pw-strength-bar pw-strength-weak';
        note.textContent = 'Weak';
        note.className = 'pw-note pw-note-bad';
      } else if (n <= 2) {
        bar.className = 'pw-strength-bar pw-strength-medium';
        note.textContent = 'Medium';
        note.className = 'pw-note';
      } else {
        bar.className = 'pw-strength-bar pw-strength-strong';
        note.textContent = 'Strong';
        note.className = 'pw-note pw-note-good';
      }
    }
    if (!p2.value.length) {
      match.textContent = '';
      match.className = 'pw-note';
    } else if (p1.value === p2.value) {
      match.textContent = 'The two match';
      match.className = 'pw-note pw-note-good';
    } else {
      match.textContent = 'The two do not match yet';
      match.className = 'pw-note pw-note-bad';
    }
  }

  p1.addEventListener('input', paint);
  p2.addEventListener('input', paint);

  var eye = document.getElementById('togglePw1');
  if (eye) eye.addEventListener('click', function () {
    var icon = document.getElementById('eyePw1');
    var showing = p1.type === 'text';
    p1.type = showing ? 'password' : 'text';
    icon.classList.toggle('fa-eye', showing);
    icon.classList.toggle('fa-eye-slash', !showing);
  });
})();
</script>

{% endblock %}
'''

PASSWORD_SET_INVALID_HTML = '''{% extends 'base.html' %}

{% block title %}Link Expired{% endblock %}

{% block content %}
{# ITS OWN TEMPLATE, NOT A BRANCH ON THE FORM PAGE. The two states     #}
{# share a title and nothing else, and one page holding both carries    #}
{# TWO house action bars with a verb in each. test_button_sweep         #}
{# section 9 counts exactly that and is right to: it cannot see that    #}
{# the two are mutually exclusive, and neither can a reader. Two        #}
{# states, two templates.                      [test_auth_flow.py]      #}
<div style="max-width: 520px; margin: 0 auto;">

    <h2 class="page-title-h2">SET YOUR PASSWORD</h2>
    <br/>

    <div class="form-card">
        <h3 class="form-section-title"><i class="fas fa-unlink"></i> This link cannot be used</h3>
        <p>A set-password link works <strong>once</strong> and stops working
           after <strong>three days</strong>. This one has either been used
           already, expired, or was broken by the email program that
           delivered it.</p>
        <p>Ask for a new one and it will arrive in a moment.</p>
        {# NOT .action-back for the second control. The house Back means  #}
        {# "the screen you came from", and its label is the word Back - a  #}
        {# rule test_bar_top enforces across the whole tree. This person   #}
        {# arrived from their email; there is no back.                     #}
        {# AND THE COMMENTS SIT OUTSIDE THE BAR, not inside it. Django     #}
        {# drops them, but the suites that render a block raw in a fixture #}
        {# do not - test_secondary_visible measured this bar at 192px tall #}
        {# with four lines of prose inside it. A check that reads text     #}
        {# catches prose, from the other side.                             #}
        <div class="page-action-buttons">
            <a href="{% url 'password_forgot' %}" class="btn action-primary">
                <i class="fas fa-envelope"></i> Send a New Link
            </a>
            <a href="{% url 'login' %}" class="btn action-secondary">
                <i class="fas fa-sign-in-alt"></i> Login
            </a>
        </div>
    </div>

</div>
{% endblock %}
'''

PASSWORD_SET_DONE_HTML = '''{% extends 'base.html' %}

{% block title %}Password Saved{% endblock %}

{% block content %}
{# THE CONFIRMATION IS A PAGE AND NOT A MESSAGE BAR. A success bar fades #}
{# after two seconds by base's own rule, and this is the one screen where #}
{# the person has to be told what to do next.        [test_auth_flow.py]  #}
<div style="max-width: 520px; margin: 0 auto;">

    <h2 class="page-title-h2">PASSWORD SAVED</h2>
    <br/>

    <div class="form-card">
        <h3 class="form-section-title"><i class="fas fa-check-circle"></i> Your password is set</h3>
        {% if disabled %}
        <p>Your new password has been saved.</p>
        <p><strong>Your account is currently disabled</strong>, so you
           cannot log in with it yet. Ask an administrator to enable your
           account and the password you just chose will work.</p>
        {% else %}
        <p>Your new password has been saved. You can log in with it now.</p>
        {% endif %}
        <div class="page-action-buttons">
            <a href="{% url 'login' %}" class="btn action-primary">
                <i class="fas fa-sign-in-alt"></i> Go to Login
            </a>
        </div>
    </div>

</div>
{% endblock %}
'''

PASSWORD_FORGOT_HTML = '''{% extends 'base.html' %}

{% block title %}Forgot Password{% endblock %}

{% block content %}
<div style="max-width: 520px; margin: 0 auto;">

    <h2 class="page-title-h2">FORGOT PASSWORD</h2>
    <br/>

    {% for msg in messages %}
      <div class="alert alert-{{ msg.tags }} alert-dismissible fade show alv-message" role="alert">
        {{ msg }}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    {% endfor %}

    {# THE SAME ANSWER WHETHER THE ADDRESS EXISTS OR NOT - otherwise this #}
    {# page is an address checker: type ten, note which say "sent", and   #}
    {# you have a list of the system's users. The view builds the message #}
    {# before it looks anything up.              [test_auth_flow.py]      #}
    <div class="form-card">
        <h3 class="form-section-title"><i class="fas fa-envelope"></i> Send me a link</h3>
        <p class="text-muted" style="font-size:13px;">
            Type the email address on your account. A link to choose a new
            password will be sent to it. The link works once and stops
            working after three days.
        </p>
        <p class="text-muted" style="font-size:13px;">
            Use this screen too if your account is new and you have never
            set a password.
        </p>

        <form method="POST">
            {% csrf_token %}
            <div class="form-group">
                <label for="forgotEmail"><strong>Email Address</strong> <span class="alv-req">*</span></label>
                <input type="email" name="email" id="forgotEmail" class="form-control"
                       placeholder="Enter your email address"
                       autocomplete="email" required>
            </div>
            <div class="page-action-buttons">
                <button type="submit" class="btn action-primary">
                    <i class="fas fa-paper-plane"></i> Send Link
                </button>
                <a href="{% url 'login' %}" class="btn action-back" aria-label="Back"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
            </div>
        </form>
    </div>

</div>
{% endblock %}
'''

MIGRATION = '''from django.db import migrations, models


class Migration(migrations.Migration):
    """Add 'password_reset_requested' to the notification-type choices.

    Section A round A1. Choices-only change: no column alteration, no data
    migration, no risk to existing rows. It exists so the notice that goes
    out when somebody asks for a password link can be configured from
    Administration -> Notification Settings instead of being hardcoded.

    THE MODEL IS HALF THE CHANGE. notification_settings() filters the
    choices through a hardcoded admin_types list in
    pages/views/notifications.py; a type missing from that list renders on
    no screen and reports no error. Round A1 adds it to both.
                                                  [test_auth_flow.py]
    """

    dependencies = [
        ('pages', '0095_none_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(choices=[('celebration_reminder', 'Celebration Reminders'), ('document_expiry', 'Document Expiry Alerts'), ('daily_report', 'Daily Property Management Report'), ('new_lease_upload', 'New Lease Upload Reminders'), ('expense_needs_approval', 'Expense Needs Approval'), ('expense_approved', 'Expense Approved'), ('expense_paid', 'Expense Paid'), ('expense_mismatch', 'Expense Invoice Uploaded'), ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'), ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'), ('invoice_paid', 'Invoice Marked as Paid'), ('issue_comments_daily', 'Daily Issue Comments Report'), ('issue_comment_urgent', 'Urgent Issue Comment Alert'), ('physical_invoice_review', 'Physical Invoices Awaiting Approval'), ('physical_invoice_client', 'Physical Invoice to Client'), ('password_reset_requested', 'Password Reset Requested')], max_length=50),
        ),
    ]
'''


# ==========================================================================
print('=' * 74)
print('SECTION A, ROUND A1 - LOGIN AND SET-PASSWORD-BY-EMAIL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')
print('  NEW FILES')
print('  ' + '-' * 70)
new_file('pages/password_reset.py', PASSWORD_RESET_PY,
         'tokens, links, the email')
new_file('pages/templates/password_set.html', PASSWORD_SET_HTML,
         'the two-field page')
new_file('pages/templates/password_set_invalid.html',
         PASSWORD_SET_INVALID_HTML, 'the used-or-expired page')
new_file('pages/templates/password_set_done.html', PASSWORD_SET_DONE_HTML,
         'the completion page')
new_file('pages/templates/password_forgot.html', PASSWORD_FORGOT_HTML,
         'Forgot password')
new_file('pages/migrations/0096_notification_type_password_reset.py',
         MIGRATION, 'the 16th notification type')
print('')
print('  CHANGED FILES')
print('  ' + '-' * 70)


def patch(rel, pairs, done_when):
    """Apply a list of (old, new, what) swaps to one file, back it up once,
    and say so. `done_when` is the string that is already in the file if
    this round has run - checked FIRST, so a second run is a no-op rather
    than a crash on a missing anchor."""
    path = (alv_tree.path_of(rel[len('pages/templates/'):])
            if rel.startswith('pages/templates/')
            else os.path.join(ROOT, rel.replace('/', os.sep)))
    t, raw = read(path)
    if done_when in t:
        print('  %-42s already done' % rel)
        return path, t
    for old, new, what in pairs:
        t = swap(t, old, new, what, path)
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-42s %d change(s)' % (rel, len(pairs)))
    return path, t


# ---- 1. login.html ------------------------------------------------------
LOGIN_OLD = """<h2 class="page-title-h2">LOGIN</h2>
<br/>
<h3 class="text-center">Login</h3>

<div class="col-md-6 offset-md-3">
<form method="POST">
    {% csrf_token %}
    <div class="form-group">
        <label for="exampleInputEmail1"><strong>Username</strong></label>
        <input type="text" class="form-control" placeholder="Enter Username" name="username">
    </div>
    <div class="form-group">
        <label for="passwordInput"><strong>Password</strong></label>
        <div class="input-group">
            <input type="password" class="form-control" placeholder="Enter Password" name="password" id="passwordInput">
            <div class="input-group-append">
                <button class="btn btn-outline-secondary" type="button" id="togglePassword">
                    <i class="fa fa-eye" id="eyeIcon"></i>
                </button>
            </div>
        </div>
    </div>
    <button type="submit" class="btn action-primary">Login</button>
</form>
</div>"""

LOGIN_NEW = """{# ONE HEADING, AND A MESSAGE LOOP THAT IS NOT OPTIONAL - A1, 1 Oct 2026. #}
{# Demetri: the word Login showed twice, and a failed login showed no red  #}
{# bar. Those are ONE bug. This page had no messages loop, so the error    #}
{# the view queued was never iterated here and surfaced on the NEXT page   #}
{# that had a loop - the screen after the next SUCCESSFUL login. That is   #}
{# the stale "You Have Successfully Logged In" he also reported.           #}
{#                                             [test_auth_flow.py]         #}
<h2 class="page-title-h2">LOGIN</h2>
<br/>

{% for msg in messages %}
  <div class="alert alert-{{ msg.tags }} alert-dismissible fade show alv-message" role="alert">
    {{ msg }}
    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  </div>
{% endfor %}

<div class="col-md-6 offset-md-3">
<form method="POST">
    {% csrf_token %}
    {% if next %}<input type="hidden" name="next" value="{{ next }}">{% endif %}
    <div class="form-group">
        <label for="usernameInput"><strong>Username</strong></label>
        <input type="text" class="form-control" placeholder="Enter Username" name="username" id="usernameInput" value="{{ username|default:'' }}" autocomplete="username" autofocus>
    </div>
    <div class="form-group">
        <label for="passwordInput"><strong>Password</strong></label>
        <div class="input-group">
            <input type="password" class="form-control" placeholder="Enter Password" name="password" id="passwordInput" autocomplete="current-password">
            <div class="input-group-append">
                {# action-secondary, not btn-outline-secondary: the house's own #}
                {# neutral button. Bootstrap keeps the geometry, so only the    #}
                {# colour moves - the .action-field-add precedent.              #}
                <button class="btn action-secondary" type="button" id="togglePassword" aria-label="Show or hide the password">
                    <i class="fas fa-eye" id="eyeIcon"></i>
                </button>
            </div>
        </div>
    </div>
    <button type="submit" class="btn action-primary">Login</button>
    {# A PERMANENT LINE, NOT A CONDITIONAL HINT. An invited person who has  #}
    {# never set a password would otherwise be told their credentials are   #}
    {# incorrect, which is true and useless. Saying so only when the        #}
    {# username exists would answer "does this username exist", so it is    #}
    {# said to everybody instead: no leak, and the lockout cannot happen.   #}
    <p class="login-help">
        <a href="{% url 'password_forgot' %}">Forgot your password?</a>
        <span class="login-help-note">New account and never set one? Same link.</span>
    </p>
</form>
</div>"""

LOGIN_STYLE_NEW = """{% block content %}
<style>
/* The one line this page adds. Everything else is base's.
                                              [test_auth_flow.py] */
.login-help { margin-top: 18px; font-size: 13px; line-height: 1.6; }
.login-help-note { display: block; color: var(--alv-ink-soft); font-size: 12.5px; }
</style>
"""

# The eye toggle's script is LEFT ALONE on purpose. It removes 'fa-eye' and
# adds 'fa-eye-slash'; with the icon now `fas fa-eye` that leaves
# `fas fa-eye-slash`, which is right. `fa` alone is Font Awesome 4 and has
# been the odd one out on this page since the system moved to `fas`.
patch('pages/templates/login.html',
      [('{% block content %}\n', LOGIN_STYLE_NEW, 'login.html content block'),
       (LOGIN_OLD, LOGIN_NEW, 'the login form')],
      'login-help')

# ---- 2. views/auth.py ---------------------------------------------------
AUTH_OLD = """from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You Have Successfully Logged In.')
            return redirect('home')
        else:
            messages.error(request, 'Error Logging In - Please Try Again !!')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'You Have Successfully Logged Out.')
    return redirect('home')"""

AUTH_NEW = '''from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from pages import password_reset as pwr

WRONG_CREDENTIALS = ('Those login credentials are incorrect. Please '
                     'double-check them and try again.')
DISABLED_ACCOUNT = ('That password is correct, but the account has been '
                    'disabled. Ask an administrator to enable it.')
# Deliberately the same sentence whether the address is registered or not.
FORGOT_SENT = ('If that email address is on an account, a link to set a new '
               'password is on its way to it. It works once and stops '
               'working after three days.')


def _safe_next(request):
    """The ?next= to honour, or ''.

    url_has_allowed_host_and_scheme IS THE WHOLE POINT. Without it,
    /login/?next=https://example.com/ turns our login page into somebody
    else's redirector - a phishing link that genuinely starts at
    alivente.online. Django ships the check; we use it rather than writing
    a weaker one."""
    nxt = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if not nxt:
        return ''
    if url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return nxt
    return ''


def _disabled_with_right_password(username, password):
    """True when the username exists, the password is RIGHT, and the
    account is switched off.

    WHY THIS IS NOT AN ENUMERATION LEAK. The message it unlocks only
    appears to somebody who already typed the correct password for that
    account - so it tells them nothing they did not already know. Every
    other wrong answer gets the one generic sentence.

    WHY IT IS NEEDED AT ALL. Django's ModelBackend returns None for an
    inactive user, so a correct password and a disabled account are
    indistinguishable from a typo. Demetrios is exactly that account: a
    superuser, ACTIVE=NO, never logged in."""
    if not username or not password:
        return False
    try:
        user = User.objects.get(username=username)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        return False
    return (not user.is_active) and user.check_password(password)


def login_user(request):
    if request.method == "POST":
        username = (request.POST.get("username") or '').strip()
        password = request.POST.get("password") or ''
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # NO SUCCESS MESSAGE. Demetri: "It is either a failure (and then
            # it is a red message at the login screen) or otherwise, you just
            # log in." Landing on the application IS the confirmation.
            return redirect(_safe_next(request) or 'home')
        if _disabled_with_right_password(username, password):
            messages.error(request, DISABLED_ACCOUNT)
        else:
            messages.error(request, WRONG_CREDENTIALS)
        # Redirect rather than re-render, so a refresh does not re-POST the
        # password. login.html now has a messages loop, so the red bar
        # arrives on the login screen itself - which is the finding.
        nxt = _safe_next(request)
        return redirect('%s?next=%s' % (reverse('login'), nxt)
                        if nxt else 'login')
    return render(request, 'login.html', {'next': _safe_next(request)})


@login_required
def logout_user(request):
    logout(request)
    # NO SUCCESS MESSAGE either, same finding. Being back at the public
    # home page with a Login link is the confirmation.
    return redirect('home')


# ===========================================================================
# SET A PASSWORD BY EMAIL
#
# Three public views. None of them logs anybody in: Demetri's words were
# "This password ... is then saved to their profile. Then they can log in."
# Setting a password and starting a session are two different permissions
# and the flow keeps them apart.
#
# The token mechanics live in pages/password_reset.py - one place, four
# callers, and importable without the app registry so the suite can drive
# real tokens against a real database.
# ===========================================================================
def password_forgot(request):
    """Ask for a link. Answers identically whether the address exists.

    THE SAME SENTENCE EVERY TIME is the only thing stopping this page
    being an address checker: type ten addresses, note which ones say
    "sent", and you have a list of the system's users. So the message is
    built before anything is looked up and does not depend on what was
    found.

    ACTIVE ACCOUNTS ONLY. A disabled account cannot log in, so a link for
    one would end at a page saying the account is disabled. Sending
    nothing is the same answer, one email fewer.
    """
    if request.method == 'POST':
        address = (request.POST.get('email') or '').strip()
        if address:
            for user in User.objects.filter(email__iexact=address,
                                            is_active=True):
                _send_link(request, user, pwr.MODE_RESET)
                _notify_reset_requested(request, user)
        messages.info(request, FORGOT_SENT)
        return redirect('login')
    return render(request, 'password_forgot.html', {})


def password_set(request, uidb64, token):
    """The page the link lands on, and the POST that saves the password.

    THE TOKEN LEAVES THE ADDRESS BAR ON THE FIRST HIT. A good token is
    parked in the session and the view redirects to the same URL with the
    literal word set-password in its place, so the token is not in the
    address bar, the browser history, or any Referer the page sends while
    the form is being filled in. Django's own PasswordResetConfirmView
    does this; the shape here is a function view because the project has
    no class-based views.

    SetPasswordForm IS WHAT ENFORCES THE FOUR VALIDATORS - the ones
    settings.py has configured since the project started and nothing ever
    ran. Its own fields are rendered by hand in the template, because this
    project renders no Django forms; only the validation and the save come
    from it.
    """
    user = pwr.user_from_uid(uidb64)
    if user is not None and token != pwr.URL_TOKEN:
        if pwr.token_ok(user, token):
            request.session[pwr.SESSION_TOKEN] = token
            return redirect('password_set', uidb64=uidb64,
                            token=pwr.URL_TOKEN)
        user = None
    if user is not None and not pwr.token_ok(
            user, request.session.get(pwr.SESSION_TOKEN, '')):
        user = None

    if user is None:
        # 400, not 404: the URL exists, the credential in it does not.
        return render(request, 'password_set_invalid.html', {}, status=400)

    if request.method == 'POST':
        form = SetPasswordForm(user, data=request.POST)
        if form.is_valid():
            form.save()
            # The token derived from the OLD hash; saving killed it. Drop
            # the session copy too, so a Back button lands on the invalid
            # page rather than a form that cannot submit.
            request.session.pop(pwr.SESSION_TOKEN, None)
            request.session['_alv_password_set_for'] = user.pk
            return redirect('password_set_done')
        # Django puts the validator messages on new_password2. Every one of
        # them is shown - "too common", "too short", "entirely numeric" -
        # because a single "invalid password" would leave the person
        # guessing which rule they broke.
        for field_errors in form.errors.values():
            for text in field_errors:
                messages.error(request, text)

    return render(request, 'password_set.html', {'target': user})


def password_set_done(request):
    """The confirmation, as a PAGE and not a message bar - base fades a
    success bar after two seconds, and this is the one screen where the
    person has to be told what happens next."""
    pk = request.session.pop('_alv_password_set_for', None)
    disabled = False
    if pk is not None:
        try:
            disabled = not User.objects.get(pk=pk).is_active
        except User.DoesNotExist:
            disabled = False
    return render(request, 'password_set_done.html', {'disabled': disabled})


# ---------------------------------------------------------------------------
# The two helpers the admin side shares. They live here because the public
# flow is the primary caller; pages/views/users.py imports them.
# ---------------------------------------------------------------------------
def _send_link(request, user, mode):
    """Build an absolute link for this user and email it. True if sent.

    THE HOST COMES FROM THE REQUEST, not a setting. An administrator
    working on alivente.online sends a link to alivente.online; one
    working on localhost sends a link to localhost. A SITE_URL setting
    would be wrong in one of those two places permanently."""
    token = pwr.make_token(user)
    url = request.build_absolute_uri(pwr.link_for(user, token))
    return pwr.send_set_password_email(user, url, mode)


def _notify_reset_requested(request, user):
    """Tell the administrators somebody asked for a link.

    SUPPRESSED WHEN THE REQUESTER IS THE RECIPIENT - Demetri: "Agreed.
    Suppress." Two cases count as that: an administrator resetting their
    own password, and a Forgot Password where the only configured
    recipient is the very address the link went to. Either way the notice
    would tell somebody something they just did.

    A FAILURE HERE IS NOT REPORTED TO THE USER. The link is the thing that
    matters; an administrator's courtesy notice failing must not make a
    successful reset look broken. It is logged.
    """
    from pages.email_utils import get_email_recipients, send_html_email
    target = (user.email or '').strip().lower()
    if request.user.is_authenticated and request.user.pk == user.pk:
        return False
    try:
        recipients = get_email_recipients('password_reset_requested')
    except Exception:
        return False
    addresses = [a for a in recipients.get('all') or []
                 if a.strip().lower() != target]
    if not addresses:
        return False
    recipients = {'to': [a for a in recipients.get('to') or []
                         if a.strip().lower() != target],
                  'cc': [a for a in recipients.get('cc') or []
                         if a.strip().lower() != target],
                  'all': addresses}
    if not recipients['to']:
        recipients['to'] = addresses
    who = ('%s (%s)' % (request.user.username, 'administrator')
           if request.user.is_authenticated else 'the person themselves')
    subject = 'Alivente Online - password link sent to %s' % user.username
    body = ("""<html><body style="font-family: Arial, sans-serif; color: #2c3e50;">
        <p>A link to set a new password has been sent for the account
           <b>%s</b> (%s).</p>
        <p>Requested by: %s</p>
        <p>The link works once and expires after three days. The account's
           existing password has not been changed and keeps working until
           the link is used.</p>
        <p>Best regards,<br>Alivente Property Management System</p>
        </body></html>""" % (user.username, user.email or 'no address', who))
    text = ('A link to set a new password has been sent for the account %s '
            '(%s).\\n\\nRequested by: %s\\n\\nThe link works once and expires '
            'after three days. The existing password has not been changed '
            'and keeps working until the link is used.'
            % (user.username, user.email or 'no address', who))
    return send_html_email(subject, body, text, recipients)'''

patch('pages/views/auth.py', [(AUTH_OLD, AUTH_NEW, 'the auth views')],
      'password_set_done')

# and the module docstring's own list of functions, which was true and is not
AUTH_DOC_OLD = """Functions
---------
- login_user  : GET renders the login form; POST authenticates and logs
                the user in, then redirects home.
- logout_user : Logs out the current user (@login_required)."""
AUTH_DOC_NEW = """Round A1 (1 Oct 2026) added the public set-password flow here, beside
login, because it is the other way a person without a session reaches
this system. The token mechanics are in pages/password_reset.py; the
administrator-facing trigger is user_reset_password in views/users.py.

Functions
---------
- login_user         : GET renders the login form; POST authenticates,
                       honours a safe ?next=, and on failure redirects
                       back with a red message - which login.html can now
                       show, because it has a messages loop.
- logout_user        : Logs out the current user (@login_required).
- password_forgot    : Ask for a set-password link by email address.
                       Answers identically whether the address exists.
- password_set       : The link's landing page and its POST. Runs the four
                       configured AUTH_PASSWORD_VALIDATORS, which nothing
                       in this project ran before.
- password_set_done  : The confirmation page."""

AP = os.path.join(ROOT, 'pages', 'views', 'auth.py')
at, araw = read(AP)
if 'password_forgot    : Ask for' in at:
    print('  %-42s docstring already done' % 'pages/views/auth.py')
else:
    at = swap(at, AUTH_DOC_OLD, AUTH_DOC_NEW, 'auth.py docstring', AP)
    if not CHECK:
        write(AP, at)
    print('  %-42s docstring' % 'pages/views/auth.py')

# ---- 3. views/users.py --------------------------------------------------
USERS_IMPORTS_OLD = """from django.contrib.auth.models import Permission, User
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from pages.permissions import MODULE_PERMISSIONS
from django.shortcuts import get_object_or_404, redirect, render

from ..models import UserProfile, Workspace"""

USERS_IMPORTS_NEW = """from django.contrib.auth.models import Permission, User
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from pages.permissions import MODULE_PERMISSIONS
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from pages import password_reset as pwr
# The public flow owns the sending; this module owns the admin trigger.
# No cycle: views/auth.py imports nothing from here.
from .auth import _notify_reset_requested, _send_link

from ..models import UserProfile, Workspace"""

USERS_ADD_READ_OLD = """        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'user')"""
USERS_ADD_READ_NEW = """        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')"""

USERS_ADD_VALID_OLD = """        if not password1:
            errors.append('Password is required.')
        if password1 != password2:
            errors.append('Passwords do not match.')
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        if email and User.objects.filter(email=email).exists():
            errors.append('A user with this email already exists.')"""
USERS_ADD_VALID_NEW = """        # EMAIL IS REQUIRED NOW - Demetri: "Email must be required on Add
        # User." It has to be. The account is created with NO USABLE
        # PASSWORD and an emailed link is the only way one ever gets set,
        # so an account with no address has no route in at all.
        # Show-UserEmails.py was written before this round to check that no
        # existing account was already in that state. None was.
        if not email:
            errors.append('Email address is required - the new user is sent '
                          'a link to choose their own password, so there has '
                          'to be somewhere to send it.')
        # iexact, not exact. Forgot Password matches the address
        # case-insensitively, so two accounts differing only in case would
        # both answer one request and "which account did I just reset"
        # would have no answer.
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append('A user with this email already exists.')"""

USERS_ADD_CREATE_OLD = """        # Create the user
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )"""
USERS_ADD_CREATE_NEW = """        # Create the user WITH NO USABLE PASSWORD. password=None makes
        # create_user call set_unusable_password(), so there is no password
        # for anybody to know - not the new user, not the administrator
        # creating them. The invitation below is the only way in, which is
        # the entire point of the change.
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=None,
            first_name=first_name,
            last_name=last_name,
        )"""

USERS_ADD_TAIL_OLD = """        messages.success(request, f'User "{username}" created successfully!')
        return redirect('user_administration')"""
USERS_ADD_TAIL_NEW = """        # THE INVITATION - AND A LOUD FAILURE IF IT DOES NOT GO OUT.
        #
        # The account is NOT rolled back on a mail failure. Rolling it back
        # would throw away the role, the status and the workspace the
        # administrator just set, and Reset Password on the user list
        # retries the send in one click. What must never happen is a
        # SILENT failure: this account has an unusable password, so with no
        # email nobody can get into it and nothing on screen would say so.
        if _send_link(request, new_user, pwr.MODE_WELCOME):
            messages.success(
                request,
                f'User "{username}" created. A link to choose a password has '
                f'been emailed to {email}.')
        else:
            messages.error(
                request,
                f'User "{username}" was created, BUT THE INVITATION EMAIL DID '
                f'NOT GO OUT to {email}. They cannot log in until it does - '
                f'use Reset Password on the user list to send it again.')
        return redirect('user_administration')"""

USERS_EDIT_READ_OLD = """        new_password = request.POST.get('password1', '').strip()
        confirm_password = request.POST.get('password2', '').strip()
        workspace_id = request.POST.get('workspace_id', '').strip()

        errors = []
        if email and User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')
        if new_password and new_password != confirm_password:
            errors.append('Passwords do not match.')
        if new_password and len(new_password) < 8:
            errors.append('Password must be at least 8 characters.')"""
USERS_EDIT_READ_NEW = """        workspace_id = request.POST.get('workspace_id', '').strip()

        # NO PASSWORD FIELDS HERE ANY MORE - A1. The administrator does not
        # type passwords; Reset Password emails a link. See
        # user_reset_password below.
        errors = []
        # REQUIRED ON EDIT TOO, which is one step past what Demetri asked
        # for ("Email must be required on Add User") and follows from it:
        # if an edit could CLEAR the address, the account it cleared would
        # lose its only route in, and Add User's rule would guard nothing.
        if not email:
            errors.append('Email address is required - it is the only way '
                          'this account can be sent a password link.')
        if email and User.objects.filter(email__iexact=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')"""

USERS_EDIT_SET_OLD = """        if new_password:
            target_user.set_password(new_password)

        target_user.save()"""
USERS_EDIT_SET_NEW = """        target_user.save()"""

USERS_RESET_VIEW = '''@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
@require_POST
def user_reset_password(request, user_id):
    """Email this user a link to set a new password.

    Demetri: "If I reset a user's Password, I should get a popup coming up
    that tells me that an email will be sent to the user... When I press
    OK, it needs to draft a standard Password Reset email."

    The popup is the confirm modal on the user list and on the edit screen;
    it names the address before anything is sent. This view is what OK
    does.

    WHAT IT DOES NOT DO: clear the current password. That is deliberate and
    it is the fail-safe order. If the send fails - wrong address, SMTP
    down, Gmail throttling - the person can still log in exactly as they
    could a minute ago. Clear it first and a failed send locks somebody out
    of a system they could reach before an administrator tried to help
    them. The old password dies when the emailed link is USED, because the
    token is derived from the password hash.

    THE ADMINISTRATOR IS TREATED IDENTICALLY. Demetri asked: "Does this
    mean that the admin user is treated in exactly the same way?" Yes.
    There is no branch on is_superuser anywhere in this flow. The only
    difference is that the courtesy notice is suppressed when the person
    resetting is the person being reset.

    @require_POST is innermost, below the auth decorators - the order
    test_require_post.py section 3 proves: outermost, a logged-out caller
    would get 405 instead of the login page, which both answers wrongly and
    confirms the URL exists.
    """
    target_user = get_object_or_404(User, id=user_id)
    address = (target_user.email or '').strip()

    if not address:
        messages.error(
            request,
            f'"{target_user.username}" has no email address, so there is '
            f'nowhere to send a link. Add one on their Edit screen first.')
        return redirect('user_administration')

    if _send_link(request, target_user, pwr.MODE_RESET):
        _notify_reset_requested(request, target_user)
        messages.success(
            request,
            f'A link to set a new password has been emailed to {address}. '
            f'It works once and expires after three days. "'
            f'{target_user.username}" can still log in with their current '
            f'password until they use it.')
    else:
        # LOUD, because the alternative is somebody waiting for an email
        # that was never sent.
        messages.error(
            request,
            f'THE EMAIL DID NOT GO OUT to {address}. "'
            f'{target_user.username}" has NOT been sent a link - their '
            f'current password still works. Check the mail settings and '
            f'try again.')
    return redirect('user_administration')


# ===========================================================================
# Workspace Management
# ===========================================================================
'''

USERS_DOC_OLD = """- user_add            : Create a user (validates username / email /
                        password; optional superuser role).
- user_edit           : Update a user; optional password reset; cannot
                        strip your own superuser status."""
USERS_DOC_NEW = """- user_add            : Create a user with NO USABLE PASSWORD and email
                        them a link to choose one. Email is required.
- user_edit           : Update a user; cannot strip your own superuser
                        status. No password fields since round A1.
- user_reset_password : POST-only. Emails a set-password link. Does not
                        clear the current password - see the view."""

patch('pages/views/users.py',
      [(USERS_IMPORTS_OLD, USERS_IMPORTS_NEW, 'users.py imports'),
       (USERS_DOC_OLD, USERS_DOC_NEW, 'users.py docstring'),
       (USERS_ADD_READ_OLD, USERS_ADD_READ_NEW, 'user_add POST reads'),
       (USERS_ADD_VALID_OLD, USERS_ADD_VALID_NEW, 'user_add validation'),
       (USERS_ADD_CREATE_OLD, USERS_ADD_CREATE_NEW, 'user_add create_user'),
       (USERS_ADD_TAIL_OLD, USERS_ADD_TAIL_NEW, 'user_add success message'),
       (USERS_EDIT_READ_OLD, USERS_EDIT_READ_NEW, 'user_edit POST reads'),
       (USERS_EDIT_SET_OLD, USERS_EDIT_SET_NEW, 'user_edit set_password'),
       ('# ===========================================================================\n'
        '# Workspace Management\n'
        '# ===========================================================================\n',
        USERS_RESET_VIEW, 'the Workspace Management banner')],
      'def user_reset_password')

# ---- 4. urls.py ---------------------------------------------------------
URLS_OLD = ("    path('user-administration/<int:user_id>/delete/', "
            "views.user_delete, name='user_delete'),\n")
URLS_NEW = URLS_OLD + """    # SET A PASSWORD BY EMAIL - Section A round A1, 1 Oct 2026.
    # One administrator trigger and three public pages.
    #
    # DJANGO'S OWN auth URLconf IS DELIBERATELY NOT INCLUDED. This project
    # authenticates SMTP with EMAIL_PASSWORD through smtplib and does not
    # use Django's send_mail - the note in views/expenses.py says so and
    # says why. The stock PasswordResetView calls send_mail, so including
    # it would produce a flow that looks complete, reports success, and
    # delivers nothing. Only the TOKEN GENERATOR is Django's; the sending
    # is the project's.
    path('user-administration/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('forgot-password/', views.password_forgot, name='password_forgot'),
    # done/ before the two-segment pattern: one segment cannot match two,
    # so the order is for a reader rather than the resolver.
    path('set-password/done/', views.password_set_done, name='password_set_done'),
    path('set-password/<str:uidb64>/<str:token>/', views.password_set, name='password_set'),
"""

patch('pages/urls.py', [(URLS_OLD, URLS_NEW, 'the user-delete route')],
      'password_set_done')


# ---- the two dead blocks the password fields leave behind ---------------
# Written once, removed from BOTH user_add.html and user_edit.html, because
# they are byte-identical in the two files - proved before this was written,
# not assumed. Leaving them would leave six literal hexes and 1,787
# characters of JavaScript driving elements that no longer exist.
PW_CSS = """.password-strength {
    height: 4px;
    border-radius: 2px;
    margin-top: 6px;
    transition: all 0.3s;
    background: var(--alv-surface-deep);
}

.strength-weak { background: #dc3545; width: 33%; }
.strength-medium { background: #ffc107; width: 66%; }
.strength-strong { background: #28a745; width: 100%; }

.strength-text {
    font-size: 11px;
    margin-top: 3px;
}

"""


def cut_js(text, path):
    """Remove the two dead strength-meter functions, leaving </script>.

    An exact-count gate expressed as a slice rather than a literal: the
    1,787-character block would otherwise be pasted into this patcher
    twice, and a single character's drift between the two templates would
    silently skip one of them."""
    mark = '\nfunction checkPasswordStrength() {'
    close = '</script>'
    m = eol(path, mark)
    if text.count(m) != 1:
        raise SystemExit('A1: checkPasswordStrength appears %d times, not once'
                         % text.count(m))
    i = text.index(m)
    j = text.index(close, i)
    if j <= i:
        raise SystemExit('A1: no </script> after the dead functions')
    return text[:i] + eol(path, '\n') + text[j:]


# ---- 5. user_add.html ---------------------------------------------------
ADD_EMAIL_OLD = """                <div class="form-group">
                    <label><strong>Email Address</strong></label>
                    <input type="email" name="email" class="form-control"
                           value="{{ form_data.email|default:'' }}"
                           placeholder="Enter email address">
                </div>"""
ADD_EMAIL_NEW = """                <div class="form-group">
                    {# REQUIRED SINCE A1. The invitation email is the only way #}
                    {# this account ever gets a password, so an account with   #}
                    {# no address would have no route in at all.               #}
                    {#                              [test_auth_flow.py]       #}
                    <label><strong>Email Address</strong> <span class="alv-req">*</span></label>
                    <input type="email" name="email" class="form-control"
                           value="{{ form_data.email|default:'' }}"
                           placeholder="Enter email address" required>
                </div>"""

ADD_PW_OLD = """        <!-- Password -->
        <div class="form-card">
            <h3 class="form-section-title"><i class="fas fa-lock"></i> Password</h3>
            <div class="form-row-2">
                <div class="form-group">
                    <label><strong>Password</strong> <span class="alv-req">*</span></label>
                    <input type="password" name="password1" id="password1" class="form-control"
                           placeholder="Enter password" required onkeyup="checkPasswordStrength()">
                    <div class="password-strength" id="passwordStrength"></div>
                    <div class="strength-text" id="strengthText"></div>
                </div>
                <div class="form-group">
                    <label><strong>Confirm Password</strong> <span class="alv-req">*</span></label>
                    <input type="password" name="password2" id="password2" class="form-control"
                           placeholder="Confirm password" required onkeyup="checkPasswordMatch()">
                    <div class="strength-text" id="matchText"></div>
                </div>
            </div>
        </div>"""
ADD_PW_NEW = """        {# NO PASSWORD FIELDS SINCE A1. Demetri: the administrator stops  #}
        {# typing passwords. The two fields that were here, and the        #}
        {# strength meter that went with them, are gone - and with them    #}
        {# the hand-rolled len < 8 check that was the only password rule   #}
        {# this system ever enforced. The four configured validators run   #}
        {# on the page the emailed link opens.      [test_auth_flow.py]    #}
        <!-- Password: chosen by the user, from a link we email them -->
        <div class="form-card">
            <h3 class="form-section-title"><i class="fas fa-envelope"></i> Password</h3>
            <p class="text-muted" style="font-size:13px;">
                You do not set a password here. When this user is created they
                are emailed a link to choose their own, and until they use it
                the account has no password at all. The link works once and
                expires after three days.
            </p>
            <p class="text-muted" style="font-size:13px; margin-bottom:0;">
                If the email does not arrive, press <strong>Reset Password</strong>
                on the user list to send it again.
            </p>
        </div>"""

AADD = alv_tree.path_of('user_add.html')
at2, araw2 = read(AADD)
if 'chosen by the user, from a link we email them' in at2:
    print('  %-42s already done' % 'pages/templates/user_add.html')
else:
    at2 = swap(at2, PW_CSS, '', 'user_add dead strength CSS', AADD)
    at2 = swap(at2, ADD_EMAIL_OLD, ADD_EMAIL_NEW, 'user_add email field', AADD)
    at2 = swap(at2, ADD_PW_OLD, ADD_PW_NEW, 'user_add password card', AADD)
    at2 = cut_js(at2, AADD)
    if not CHECK:
        back_up(AADD, araw2)
        write(AADD, at2)
    print('  %-42s 4 change(s)' % 'pages/templates/user_add.html')

# ---- 6. user_edit.html --------------------------------------------------
EDIT_EMAIL_OLD = """                <div class="form-group">
                    <label><strong>Email Address</strong></label>
                    <input type="email" name="email" class="form-control"
                           value="{{ target_user.email }}"
                           placeholder="Enter email address">
                </div>"""
EDIT_EMAIL_NEW = """                <div class="form-group">
                    {# REQUIRED SINCE A1, on edit as well as add: an edit that #}
                    {# could CLEAR the address would take away the account's   #}
                    {# only route in, and Add User's rule would guard nothing. #}
                    {#                              [test_auth_flow.py]       #}
                    <label><strong>Email Address</strong> <span class="alv-req">*</span></label>
                    <input type="email" name="email" class="form-control"
                           value="{{ target_user.email }}"
                           placeholder="Enter email address" required>
                </div>"""

EDIT_PW_OLD = """        <!-- Reset Password -->
        <div class="form-card">
            <h3 class="form-section-title"><i class="fas fa-lock"></i> Reset Password</h3>
            <p class="text-muted" style="font-size:13px; margin-bottom:16px;">
                Leave blank to keep the current password.
            </p>
            <div class="form-row-2">
                <div class="form-group">
                    <label><strong>New Password</strong></label>
                    <input type="password" name="password1" id="password1" class="form-control"
                           placeholder="Enter new password" onkeyup="checkPasswordStrength()">
                    <div class="password-strength" id="passwordStrength"></div>
                    <div class="strength-text" id="strengthText"></div>
                </div>
                <div class="form-group">
                    <label><strong>Confirm New Password</strong></label>
                    <input type="password" name="password2" id="password2" class="form-control"
                           placeholder="Confirm new password" onkeyup="checkPasswordMatch()">
                    <div class="strength-text" id="matchText"></div>
                </div>
            </div>
        </div>"""
EDIT_PW_NEW = """        {# NO PASSWORD FIELDS SINCE A1 - the administrator does not type  #}
        {# passwords. The button below only OPENS the confirm dialog; the  #}
        {# form that posts the reset sits OUTSIDE this one, below the      #}
        {# point where the edit form closes, because a form nested in a    #}
        {# form is invalid HTML and the browser drops the inner one. That  #}
        {# is the lesson round require_post learned the hard way - and     #}
        {# that round ALSO learned not to write the tag itself into a      #}
        {# note like this one, because the balance counter in              #}
        {# test_admin_repair reads prose and counts what it finds.         #}
        {#                                          [test_auth_flow.py]    #}
        <!-- Reset Password -->
        <div class="form-card">
            <h3 class="form-section-title"><i class="fas fa-envelope"></i> Reset Password</h3>
            <p class="text-muted" style="font-size:13px; margin-bottom:16px;">
                Nobody here sets this user's password. Pressing the button
                emails them a link to choose their own. The link works once
                and expires after three days - and their <strong>current
                password keeps working</strong> until they use it, so a
                reset cannot lock anybody out.
            </p>
            {% if target_user.email %}
            <button type="button" class="btn action-secondary"
                    onclick="confirmReset()">
                <i class="fas fa-envelope"></i> Reset Password
            </button>
            {% else %}
            <div class="alert alert-warning" style="font-size:13px;">
                <i class="fas fa-exclamation-triangle"></i>
                This account has <strong>no email address</strong>, so no link
                can be sent. Add one above, save, and the button appears.
            </div>
            {% endif %}
        </div>"""

EDIT_FORM_END_OLD = """        <!-- Action Buttons -->

    </form>
</div>

<script>
"""
EDIT_FORM_END_NEW = """        <!-- Action Buttons -->

    </form>
</div>

{# THE RESET DIALOG, AND ITS FORM, OUTSIDE THE EDIT FORM ON PURPOSE. #}
<div class="modal fade" id="resetPwModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title"><i class="fas fa-envelope"></i> Email a Password Link</h5>
                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
            </div>
            <div class="modal-body">
                <p>An email will be sent to
                   <strong>{{ target_user.email }}</strong> with a link for
                   <strong>{{ target_user.username }}</strong> to choose a new
                   password.</p>
                <p class="text-muted">The link works once and expires after
                   three days. Their current password keeps working until they
                   use it.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                <form method="POST" action="{% url 'user_reset_password' target_user.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn action-primary">
                        <i class="fas fa-paper-plane"></i> Send the Email
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
function confirmReset() {
    $('#resetPwModal').modal('show');
}

"""

AEDIT = alv_tree.path_of('user_edit.html')
et, eraw = read(AEDIT)
if 'resetPwModal' in et:
    print('  %-42s already done' % 'pages/templates/user_edit.html')
else:
    et = swap(et, PW_CSS, '', 'user_edit dead strength CSS', AEDIT)
    et = swap(et, EDIT_EMAIL_OLD, EDIT_EMAIL_NEW, 'user_edit email field',
              AEDIT)
    et = swap(et, EDIT_PW_OLD, EDIT_PW_NEW, 'user_edit password card', AEDIT)
    et = swap(et, EDIT_FORM_END_OLD, EDIT_FORM_END_NEW,
              'user_edit end of form', AEDIT)
    et = cut_js(et, AEDIT)
    if not CHECK:
        back_up(AEDIT, eraw)
        write(AEDIT, et)
    print('  %-42s 5 change(s)' % 'pages/templates/user_edit.html')

# ---- 7. base.html gains the row-action colour ---------------------------
BASE_ICON_OLD = """.icon-lock       { color: var(--alv-warn); border-color: #ecd9a8; }
.icon-lock:hover { background-color: var(--alv-warn); border-color: var(--alv-warn); color: #fff; }
.icon-color-lock { color: var(--alv-warn); }
"""
BASE_ICON_NEW = BASE_ICON_OLD + """
/* Reset Password: ANOTHER NAME ON AN EXISTING COLOUR, added by Section A
   round A1 for the user list's row actions. No new hex enters the palette -
   the rule Duplicate, Upload, Manage and Event were all added under.

   WHY --alv-warn. It is the same WEIGHT of action as Disable: it begins
   the process that replaces somebody's password. Not --alv-edit, which
   would sit beside the pencil at a glance and read as "change this row";
   not --alv-delete, because nothing is destroyed - the current password
   keeps working until the emailed link is used.

   WHY ITS OWN NAME AND NOT .icon-lock. A class carries ONE PICTURE.
   .icon-lock is fa-ban (Disable); this is fa-envelope. Hanging a second
   glyph on a class that already has one is precisely the drift
   test_icon_buttons section 1b exists to catch, and .icon-edit had
   already done it once.                            [test_auth_flow.py] */
.icon-reset-pw       { color: var(--alv-warn); border-color: #ecd9a8; }
.icon-reset-pw:hover { background-color: var(--alv-warn); border-color: var(--alv-warn); color: #fff; }
.icon-color-reset-pw { color: var(--alv-warn); }
"""

patch('pages/templates/base.html',
      [(BASE_ICON_OLD, BASE_ICON_NEW, 'base\'s icon-lock rules')],
      '.icon-reset-pw')

# ---- 8. user_administration.html ----------------------------------------
UA_DESK_OLD = """                            <a href="{% url 'user_permissions' user.id %}" class="icon-action-btn icon-permissions" title="Manage Permissions">
                                <i class="fas fa-key"></i>
                            </a>
"""
UA_DESK_NEW = UA_DESK_OLD + """                            {% if user.email %}
                            <button type="button" class="icon-action-btn icon-reset-pw" title="Email a Password Link"
                                    onclick="confirmReset({{ user.id }}, '{{ user.username|escapejs }}', '{{ user.email|escapejs }}')">
                                <i class="fas fa-envelope"></i>
                            </button>
                            {% endif %}
"""

UA_MOB_OLD = """                        <a href="{% url 'user_permissions' user.id %}" class="mobile-action-btn">
                            <i class="fas fa-key mobile-action-icon icon-color-permissions"></i>
                            <span class="mobile-action-label">Permissions</span>
                        </a>
"""
UA_MOB_NEW = UA_MOB_OLD + """                        {% if user.email %}
                        <button type="button" class="mobile-action-btn"
                                onclick="confirmReset({{ user.id }}, '{{ user.username|escapejs }}', '{{ user.email|escapejs }}')">
                            <i class="fas fa-envelope mobile-action-icon icon-color-reset-pw"></i>
                            <span class="mobile-action-label">Password</span>
                        </button>
                        {% endif %}
"""

UA_MODAL_ANCHOR = """{% render_help_modal "user_administration" %}
"""
UA_MODAL_NEW = """<!-- Reset Password Modal -->
{# THE POPUP DEMETRI ASKED FOR: "I should get a popup coming up that tells  #}
{# me that an email will be sent to the user". It names the ADDRESS, because #}
{# the address is the thing that can be wrong and the only thing an         #}
{# administrator can check before pressing send.     [test_auth_flow.py]    #}
<div class="modal fade" id="resetPwModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title"><i class="fas fa-envelope"></i> Email a Password Link</h5>
                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
            </div>
            <div class="modal-body">
                <p>An email will be sent to
                   <strong id="resetPwEmail"></strong> with a link for
                   <strong id="resetPwUser"></strong> to choose a new password.</p>
                <p class="text-muted">The link works once and expires after
                   three days. Their current password keeps working until they
                   use it, so this cannot lock them out.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                <form id="resetPwForm" method="POST">
                    {% csrf_token %}
                    <button type="submit" class="btn action-primary">
                        <i class="fas fa-paper-plane"></i> Send the Email
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

""" + UA_MODAL_ANCHOR

UA_JS_ANCHOR = """function confirmDelete(userId, username) {
    document.getElementById('deleteUsername').textContent = username;
    document.getElementById('deleteForm').action = `/user-administration/${userId}/delete/`;
    $('#deleteModal').modal('show');
}
"""
UA_JS_NEW = UA_JS_ANCHOR + """
function confirmReset(userId, username, email) {
    document.getElementById('resetPwUser').textContent = username;
    document.getElementById('resetPwEmail').textContent = email;
    document.getElementById('resetPwForm').action =
        `/user-administration/${userId}/reset-password/`;
    $('#resetPwModal').modal('show');
}
"""

patch('pages/templates/user_administration.html',
      [(UA_DESK_OLD, UA_DESK_NEW, 'the desktop Permissions action'),
       (UA_MOB_OLD, UA_MOB_NEW, 'the mobile Permissions action'),
       (UA_MODAL_ANCHOR, UA_MODAL_NEW, 'the help-modal tag'),
       (UA_JS_ANCHOR, UA_JS_NEW, 'confirmDelete')],
      'resetPwModal')

# ---- 9. email_utils.py gains the generic sender -------------------------
EU_ANCHOR = """# ============================================================================
# Issue-comments email rendering & sending
"""
EU_NEW = '''def send_html_email(subject, html_body, text_body, recipients):
    """Send one multipart email. True if it went out, False if it did not.

    Added by Section A round A1 for the set-password flow, where a send
    that fails silently leaves a person locked out of an account waiting
    for an email nobody sent. Every caller checks the return value.

    THE SMTP BLOCK BELOW IS A SECOND COPY, AND THAT IS SAID OUT LOUD
    RATHER THAN HIDDEN. send_issue_comments_email() has the same six env
    vars and the same SSL/TLS dance. Rewriting it to call this function is
    the obvious tidy and is DELIBERATELY NOT DONE IN THIS ROUND: that
    function is what the daily cron and the Notify Urgent button use, and
    putting a working production mail path at risk buys this round nothing.
    It is a follow-up.

    What stops the two drifting in the meantime is test_auth_flow.py
    section 7, which reads both blocks and requires the same variable names
    with the same defaults. A copy nobody is watching drifts; a copy a
    suite is watching is just a copy.

    Parameters
    ----------
    subject    -- the subject line. Header-encoded, so Greek survives.
    html_body  -- the HTML alternative.
    text_body  -- the plain-text alternative, for clients that prefer it
                  and for anything that strips HTML.
    recipients -- {'to': [...], 'cc': [...], 'all': [...]} - the shape
                  get_email_recipients() returns.
    """
    smtp_object = None

    if not recipients or not recipients.get('all'):
        logger.warning('send_html_email: no recipients, skipping')
        return False

    try:
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('send_html_email: EMAIL_PASSWORD not set')
            return False

        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients.get('cc'):
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        # RFC 2047, same reason as the issue-comments sender: a Greek first
        # name in a subject line is garbled without it.
        msg['Subject'] = Header(subject, 'utf-8')

        # text FIRST, html SECOND. A multipart/alternative reader shows the
        # LAST part it understands, so this order means an HTML client sees
        # the HTML and a plain-text one still gets a usable message. The
        # other order shows everybody the plain text.
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        smtp_object.login(email_user, email_password)
        smtp_object.sendmail(email_user, recipients['all'], msg.as_string())

        logger.info('send_html_email sent: %s', subject)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error('send_html_email SMTP authentication error: %s', e)
        return False
    except smtplib.SMTPException as e:
        logger.error('send_html_email SMTP error: %s', e)
        return False
    except Exception as e:
        logger.error('send_html_email failed: %s', e, exc_info=True)
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except Exception:
                pass


''' + EU_ANCHOR

patch('pages/email_utils.py',
      [(EU_ANCHOR, EU_NEW, 'the issue-comments banner')],
      'def send_html_email')

# ---- 10. the 16th notification type ------------------------------------
patch('pages/models.py',
      [("        ('physical_invoice_client', 'Physical Invoice to Client'),\n"
        "    )\n",
        "        ('physical_invoice_client', 'Physical Invoice to Client'),\n"
        "        # THE 16TH, added by Section A round A1: who hears about it\n"
        "        # when somebody asks for a password link. Configurable from\n"
        "        # Administration -> Notification Settings rather than\n"
        "        # hardcoded - and see notification_settings() in\n"
        "        # views/notifications.py, which filters these choices\n"
        "        # through a SECOND, hardcoded list. A type missing from that\n"
        "        # list renders on no screen and reports no error.\n"
        "        #                                   [test_auth_flow.py]\n"
        "        ('password_reset_requested', 'Password Reset Requested'),\n"
        "    )\n",
        'the notification-type choices')],
      'password_reset_requested')

# ---- 11. and the hardcoded list that would have swallowed it ------------
patch('pages/views/notifications.py',
      [("        'issue_comment_urgent',\n    ]\n",
        "        'issue_comment_urgent',\n"
        "        # A1: without this line the 16th type is in the model, in the\n"
        "        # migration, and on NO SCREEN. Adding a choice is half a\n"
        "        # change; this list is the other half.  [test_auth_flow.py]\n"
        "        'password_reset_requested',\n    ]\n",
        'the admin_types list')],
      'password_reset_requested')

# ---- 12. the expiry, written down instead of inherited -----------------
patch('mysite/settings.py',
      [('AUTH_PASSWORD_VALIDATORS = [\n',
        '# HOW LONG A SET-PASSWORD LINK LIVES - Section A round A1.\n'
        '# Demetri: "3 days is fine". 259200 seconds is also Django\'s own\n'
        '# default, so this line changes no behaviour today - it WRITES THE\n'
        '# DECISION DOWN, because a Django upgrade that changed the default\n'
        '# would otherwise change an agreed decision with nothing in the\n'
        '# repo recording that it had been agreed.\n'
        '#                                            [test_auth_flow.py]\n'
        'PASSWORD_RESET_TIMEOUT = 259200\n'
        '\n'
        '# These four have been configured since the project started and\n'
        '# NOTHING RAN THEM: user_add and user_edit checked len < 8 by hand\n'
        '# and called set_password directly, which does not validate. Round\n'
        '# A1 replaced both with SetPasswordForm, which does. "password" and\n'
        '# "12345678" were accepted before it and are refused after it.\n'
        'AUTH_PASSWORD_VALIDATORS = [\n',
        'the validators block')],
      'PASSWORD_RESET_TIMEOUT')

# ---- 13. THE MIDDLEWARE THAT WOULD HAVE BROKEN THE WHOLE ROUND ---------
#
# ModuleAccessMiddleware.process_view bounces every path that is not in
# EXEMPT_URL_PATTERNS to the login page when the caller is anonymous. The
# whole point of a set-password link is that the person following it is
# ANONYMOUS - they cannot log in, that is why they were sent the link. So
# without this change the emailed link redirected to /login/?next=... and
# the flow was dead on arrival.
#
# Nothing static could have found this. The URLs resolve, the templates
# compile, the views are correct, the tokens are correct - and the feature
# does not work. It was found by driving the real flow through Django's
# test Client against a real database, which is why test_auth_flow.py
# section 5 does exactly that and why the suite builds itself a sqlite
# database rather than reading the source and believing it.
#
# startswith() matching, so 'set-password/' covers both the token form and
# the parked form. user-administration/<id>/reset-password/ is NOT covered
# by it - that path starts with user-administration/ - so the
# administrator's trigger keeps all four of its decorators.
patch('pages/middleware.py',
      [("            'login/',\n            'logout/',\n",
        "            'login/',\n            'logout/',\n"
        "            # THE SET-PASSWORD FLOW IS PUBLIC BY DEFINITION - A1.\n"
        "            # Somebody following an emailed password link is\n"
        "            # anonymous; that is the entire reason they were sent\n"
        "            # one. Without these two lines this middleware bounced\n"
        "            # them to the login page they cannot use, and the round\n"
        "            # did nothing at all. Found by driving the flow, not by\n"
        "            # reading it.                   [test_auth_flow.py]\n"
        "            'forgot-password/',\n"
        "            'set-password/',\n",
        'the exempt-URL list')],
      'set-password/')

# ---- 14. THE TWO COUNTS A ROUND THAT ADDS PAGES HAS TO MOVE ------------
#
# Two suites keep a NUMBER, and a number is a claim about the tree that
# stops being true the moment the tree grows. This is the ledger pattern
# the P2 and N3 rounds followed: a round that changes what a named list
# counts updates it in the SAME round, so the list never says something
# that was true last week.
#
# (a) test_house_title counts the templates wearing .page-title-h2, and
#     base.html's own standards note states the same number. A1 adds four
#     pages, every one of them wearing it: 117 -> 121.
patch('pages/templates/base.html',
      [('h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. '
        '117 pages\n',
        'h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. '
        '121 pages\n',
        'base\'s count of the pages wearing the class')],
      '121 pages')

patch('test_house_title.py',
      [("ok(len(wearers) == 117,\n"
        "   '117 templates now wear the class, which is the number base\\'s "
        "note '\n   'states', len(wearers))",
        "# 117 until 1 Oct 2026. Section A round A1 added four public pages -\n"
        "# the set-password form, the used-or-expired page, the confirmation\n"
        "# and Forgot password - and all four wear the house title. The\n"
        "# number and base's note move together or one of them is lying.\n"
        "ok(len(wearers) == 121,\n"
        "   '121 templates now wear the class, which is the number base\\'s "
        "note '\n   'states', len(wearers))",
        'the wearer count'),
       # THE NOTE CHECK IS LEFT AT 117 ON PURPOSE. `doc` is read through
       # as_left_by(), so it is base.html AS THE HOUSETITLE ROUND LEFT IT -
       # a frozen copy, where 117 was true and still is. Only section 2's
       # count reads the live tree. Changing this one too would have the
       # suite assert that a file from three weeks ago knows about four
       # pages added today, which is a check that must fail every time the
       # tree grows. The wording is what was wrong, not the number.
       ("ok('117 pages' in doc, '  and the count is the one section 2 just "
        "checked')",
        "ok('117 pages' in doc, '  and the note that round wrote still says "
        "what was true THEN - doc is read through as_left_by, so it is a "
        "frozen copy; the live count is section 2\\'s')",
        'the note check')],
      '121 templates now wear')

# (b) test_modal_heads counts the modal headers on its BUSINESS list, twice
#     - once in the markup census and once in the render. A1 adds the
#     Reset Password dialog to the user list AND to the edit screen, and
#     user_edit.html was not on that list because it had no modal before.
#     It is added rather than excused: an unwatched modal header is how
#     the ten different looks the round found got there.
patch('test_modal_heads.py',
      [("    'user_administration.html', 'workspace_management.html',\n",
        "    'user_administration.html', 'workspace_management.html',\n"
        "    # ADDED 1 Oct 2026 by Section A round A1. user_edit.html had no\n"
        "    # modal until the Reset Password dialog landed on it, so it was\n"
        "    # never on this list. A business template with a modal header\n"
        "    # belongs here; an unwatched header is how the ten different\n"
        "    # looks this round found got there in the first place.\n"
        "    'user_edit.html',\n",
        'the BUSINESS list'),
       ("ok(total == 51 and not bad,",
        "# 51 until A1, which added the Reset Password dialog to the user\n"
        "# list and to the edit screen.\nok(total == 53 and not bad,",
        'the markup census count'),
       ("        ok(sum(now_looks.values()) == 51 and not off,",
        "        ok(sum(now_looks.values()) == 53 and not off,",
        'the rendered count')],
      "'user_edit.html',")

# ---- 15. THE OTHER FOUR LEDGERS A1 MOVES -------------------------------
#
# Four more suites keep a number or a named list about the tree, and A1
# adds four templates and one dialog to it. Same rule as above: the round
# that changes what a list counts updates it, or the list quietly becomes
# a statement about last week.
#
# (c) test_tree_roots and test_subtree_tones both count templates.
#     138 -> 142 under pages/templates, 146 -> 150 across both roots, and
#     the flat listing 120 -> 124 (all four new pages sit at the root of
#     pages/templates, so both numbers move by the same four).
#     THE ANCHORS ARE THE WHOLE LINES, NOT THE DIGITS. '142' already
#     appears in test_subtree_tones as rgb(142, 98, 7), and a bare '138'
#     would match inside any longer number. An anchor that can hit prose
#     or another number is how a patcher edits something nobody meant.
patch('test_tree_roots.py',
      [('# Measured 28 Sep, with the app staged from the laptop.\n'
        'MAIN_N = 138\n',
        '# Measured 28 Sep, with the app staged from the laptop.\n'
        '# 142 since 1 Oct: Section A round A1 added the four public\n'
        '# set-password pages. CRS_N is untouched.\n'
        'MAIN_N = 142\n',
        'MAIN_N'),
       ('SECTION 1 IS THE TREE ITSELF - both roots, 146 templates, and the '
        'zero\n',
        'SECTION 1 IS THE TREE ITSELF - both roots, 150 templates, and the '
        'zero\n',
        'the docstring\'s total')],
      'MAIN_N = 142')

patch('test_subtree_tones.py',
      [("ok(len(tree) == 138, 'a WALK finds 138 templates', len(tree))\n"
        "ok(len(top) == 120, '  a flat listing finds 120 - what H7 counted',\n",
        "# 138 and 120 until 1 Oct 2026, when Section A round A1 added the\n"
        "# four public set-password pages. All four sit at the ROOT of\n"
        "# pages/templates, so both numbers move by four and the eighteen\n"
        "# that live in subdirectories - the whole point of this section -\n"
        "# is still eighteen.\n"
        "ok(len(tree) == 142, 'a WALK finds 142 templates', len(tree))\n"
        "ok(len(top) == 124, '  a flat listing finds 124 - 120 was what H7 "
        "counted',\n",
        'the two counts'),
       ("every one of the 138 and fails if any page declares a rule for one "
        "of\n",
        "every one of the 142 and fails if any page declares a rule for one "
        "of\n",
        'the docstring\'s section-3 claim')],
      "a WALK finds 142 templates")

# (d) test_save_and_cancel names every Cancel that is NOT a way out of a
#     form. user_edit's Reset Password dialog has one, on exactly the same
#     grounds as the five already named: data-dismiss="modal" inside a
#     .modal-footer. Named rather than counted, which is that suite's
#     whole point.
patch('test_save_and_cancel.py',
      [("    'finance_valuations_edit.html': 'it dismisses a dialog',\n}",
        "    'finance_valuations_edit.html': 'it dismisses a dialog',\n"
        "    # ADDED 1 Oct 2026 by Section A round A1. user_edit grew a Reset\n"
        "    # Password dialog, and its Cancel dismisses that dialog - it is\n"
        "    # not a second way out of the edit form, which still has only\n"
        "    # Back. Same grounds as the five above: data-dismiss=\"modal\"\n"
        "    # inside a .modal-footer.\n"
        "    'user_edit.html': 'it dismisses a dialog',\n}",
        'the KEEP_CANCEL list')],
      "'user_edit.html': 'it dismisses a dialog'")

# ---- 16. registration --------------------------------------------------
patch('alv_rounds.py',
      [("    '.bak_stats3up',\n]\n",
        "    '.bak_stats3up',\n    '%s',\n]\n" % SUFFIX,
        'the end of ROUNDS')],
      SUFFIX)

patch('Push-PendingChanges.ps1',
      [("$skipped = @()\nforeach ($t in $suites) {\n    if (-not (Test-Path (Join-Path $root $t))) {\n        Warn ($t + ' not present - skipped')\n        $skipped += $t\n        continue\n    }\n    Say ''\n    Say ('  == ' + $t)\n    & python $t 2>&1 | ForEach-Object { Say ('     ' + $_) }\n    if ($LASTEXITCODE -ne 0) {\n        Bad ($t + ' FAILED')\n",
        '$skipped = @()\n# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of\n# the 203, it shows 1/203 and then name for the first one... This way I can\n# monitor progress and manage my time better."\n#\n# THE TOTAL IS $suites.Count, NOT A NUMBER TYPED HERE. The list grows by a\n# line every round - 197 three weeks ago, 203 today - and a hardcoded total\n# would be wrong the first time somebody appends to it and would go on\n# being wrong silently. The width is computed from the count too, so the\n# numbers stay in a straight column whether there are 99 or 1,099.\n#\n# The three names carry a suite prefix because this script is 1,200 lines\n# and $label already belongs to the manifest loop five hundred lines up.\n$suiteNo = 0\n$suiteWide = (\'\' + $suites.Count).Length\nforeach ($t in $suites) {\n    $suiteNo++\n    $suiteLabel = (\'[\' + (\'\' + $suiteNo).PadLeft($suiteWide) + \'/\' + $suites.Count + \']\')\n    if (-not (Test-Path (Join-Path $root $t))) {\n        Warn ($suiteLabel + \' \' + $t + \' not present - skipped\')\n        $skipped += $t\n        continue\n    }\n    Say \'\'\n    Say (\'  == \' + $suiteLabel + \' \' + $t)\n    & python $t 2>&1 | ForEach-Object { Say (\'     \' + $_) }\n    if ($LASTEXITCODE -ne 0) {\n        # THE NUMBER ON THE FAILURE LINE TOO. In a 203-suite run the failure\n        # scrolls past the banner that said which suite was starting, and\n        # "test_x FAILED" alone does not say how far in it was.\n        Bad ($suiteLabel + \' \' + $t + \' FAILED\')\n',
        'the suite-running loop'),
       ("    'test_stats_3up.py'\n)\n",
        "    'test_stats_3up.py'\n"
        "    # Login and set-password-by-email. Its section 4 runs REAL\n"
        "    # tokens and a REAL SetPasswordForm against a sqlite database it\n"
        "    # builds itself, because the project's settings point at MySQL\n"
        "    # and no suite can reach it - so this is the one flow that is\n"
        "    # proved by running rather than by reading. Newest, so most\n"
        "    # likely to be what breaks.\n"
        "    'test_auth_flow.py'\n)\n",
        'the end of $suites')],
      'test_auth_flow.py')

# ==========================================================================
# GATES
# ==========================================================================
print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    # The gates below read the FINISHED files, and --check wrote none of
    # them. Running them here would report the state before the round and
    # call it a failure, which is a liar rather than a gate.
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

# (a) NOTHING ANYWHERE STILL POSTS A PASSWORD TO AN ADMIN SCREEN.
# The round's whole claim is that the administrator stops typing passwords.
# A template left with name="password1" pointing at user_add or user_edit
# would post a field the view no longer reads - silently doing nothing,
# which is worse than an error.
leaks = {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q).replace(os.sep, '/')
    if rel in ('password_set.html', 'login.html'):
        continue
    src = read(q)[0]
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->|\{#.*?#\}', '', src, flags=re.S),
                  flags=re.S)
    hits = re.findall(r'name="(password1|password2|new_password1|new_password2)"',
                      body)
    if hits:
        leaks[rel] = sorted(set(hits))
if leaks:
    raise SystemExit('A1: a template still posts a password field: %s' % leaks)
print('  no admin template posts a password field any more')

# (b) THE TWO HALVES OF THE NOTIFICATION TYPE ARE BOTH THERE.
# Three halves, really: the model's choices, the hardcoded admin_types list
# that filters them, and the migration. Any one missing is silent.
checks = [('models.py', os.path.join(ROOT, 'pages', 'models.py')),
          ('views/notifications.py',
           os.path.join(ROOT, 'pages', 'views', 'notifications.py'))]
if not CHECK:
    checks.append(('migration 0096',
                   os.path.join(ROOT, 'pages', 'migrations',
                                '0096_notification_type_password_reset.py')))
for where, path in checks:
    if 'password_reset_requested' not in read(path)[0]:
        raise SystemExit('A1: password_reset_requested missing from %s' % where)
print('  password_reset_requested is in the model, the admin_types list%s'
      % ('' if CHECK else ' and the migration'))

# (c) THE ONE PLACE A PASSWORD IS SET IS THE FORM THAT VALIDATES.
# set_password anywhere in the user-administration path would be a way
# round the four validators, which is the thing this round exists to close.
#
# \b IS NOT DECORATION, AND THIS GATE ALREADY LIED ONCE WITHOUT IT. A plain
# `'set_password(' in text` matched `def user_reset_password(` - the very
# view this round adds - and the round refused itself. The substring was
# inside a longer identifier. Same shape as every other narrow check that
# has caught me: the question asked was not the question meant.
u = read(os.path.join(ROOT, 'pages', 'views', 'users.py'))[0]
if re.search(r'\bset_password\s*\(', re.sub(r'#.*', '', u)):
    raise SystemExit('A1: views/users.py still calls set_password - the four '
                     'validators would not run on it')
print('  views/users.py calls set_password nowhere - SetPasswordForm is the '
      'only writer')

# (d) THE SENTINEL IS A ONE-LINE COMMENT EVERYWHERE IT APPEARS.
# P2's lesson, four hours old: tag_re in Django's lexer is
# {%.*?%}|{{.*?}}|{#.*?#} with NO re.DOTALL, so a {# #} that spans lines is
# not a comment - it renders as a paragraph of prose on the page.
bad = {}
for q in alv_tree.templates():
    src = read(q)[0]
    for mm in re.finditer(r'\{#(.*?)#\}', src, flags=re.S):
        if '\n' in mm.group(1):
            bad.setdefault(alv_tree.rel(q).replace(os.sep, '/'), 0)
            bad[alv_tree.rel(q).replace(os.sep, '/')] += 1
for q in ('password_set.html', 'password_set_done.html',
          'password_forgot.html', 'login.html', 'user_add.html',
          'user_edit.html', 'user_administration.html', 'base.html'):
    if q in bad:
        raise SystemExit('A1: %s has a MULTI-LINE {# #}, which Django renders '
                         'as text (%d of them)' % (q, bad[q]))
print('  every Django comment this round wrote is on one line')

# (e) AND NONE OF THEM NESTS. A one-line comment containing an inner
# open-marker is the SAME bug wearing a disguise: the lexer's pattern is
# non-greedy, so it closes at the inner close-marker and the rest of the
# line renders as text. Gate (d) would pass it, because the match it finds
# has no newline in it. That nearly shipped while gate (d) was being
# written - the comment explaining the rule broke the rule by quoting it.
OPEN, CLOSE = '{' + '#', '#' + '}'
nested = {}
for q in alv_tree.templates():
    for mm in re.finditer(r'\{#(.*?)#\}', read(q)[0], flags=re.S):
        if OPEN in mm.group(1) or CLOSE in mm.group(1):
            nested[alv_tree.rel(q).replace(os.sep, '/')] = mm.group(1)[:50]
for q in ('password_set.html', 'password_set_done.html',
          'password_forgot.html', 'login.html', 'user_add.html',
          'user_edit.html', 'user_administration.html'):
    if q in nested:
        raise SystemExit('A1: %s has a comment containing a comment marker, '
                         'which closes early and renders the rest: %r'
                         % (q, nested[q]))
print('  and none of them quotes a comment marker inside itself')

print('-' * 74)
print('  The login screen has one heading, a red message when the')
print('  credentials are wrong, and no stale success bar. The administrator')
print('  stops typing passwords: a new user and a reset both get an emailed')
print('  link to a page that runs the four validators which, until today,')
print('  nothing in this project ran.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
