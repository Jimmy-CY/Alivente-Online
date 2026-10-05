"""
Login and logout views.

Extracted from the legacy pages/views/main.py during the modular views
migration (it lived under the misleadingly named
"### USER ADMIN AND LOGIN AND LOGOUT ###" section). The actual user
management views - create / edit / permissions / roles - are in
pages/views/users.py; this module holds only the public login/logout
entry points. URL patterns are registered in pages/urls.py.

Round A1 (1 Oct 2026) added the public set-password flow here, beside
login, because it is the other way a person without a session reaches
this system. The token mechanics are in pages/password_reset.py; the
administrator-facing trigger is user_reset_password in views/users.py.

Functions
---------
- account_for        : maps whatever was typed in the login box - a
                       username or an email address - to the username to
                       authenticate. Added by round A3, 1 Oct 2026.
- login_user         : GET renders the login form; POST authenticates,
                       honours a safe ?next=, and on failure redirects
                       back with a red message - which login.html can now
                       show, because it has a messages loop.
- logout_user        : Logs out whoever is logged in, if anyone, and
                       returns to the public home page. It carries no
                       login guard at all - see LU-1 at the view for
                       why that is deliberate.
- password_forgot    : Ask for a set-password link by email address.
                       Answers identically whether the address exists.
- password_set       : The link's landing page and its POST. Runs the four
                       configured AUTH_PASSWORD_VALIDATORS, which nothing
                       in this project ran before.
- password_set_done  : The confirmation page.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.db.models import Q
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


def account_for(identifier):
    """The USERNAME to authenticate, given whatever was typed in the box.

    Demetri, 1 Oct 2026, locked out of an account whose username is
    `Demetrios` by typing the address the reset email had just arrived at.
    The box now takes either.

    THE ORDER IS THE WHOLE DESIGN:

      1. If it names an account, it IS a username. Checked first and
         exactly, so a username always beats an address that happens to
         look like one - nobody can make somebody else's login ambiguous
         by choosing an email.
      2. No @, no lookup. That string is not an address and the query
         could only answer no.
      3. Exactly one match, case-insensitively - the spelling Forgot
         Password and the duplicate check on Add/Edit User already use.
      4. TWO MATCHES REFUSE. One address on two accounts is a state this
         system no longer allows but may still contain, and guessing
         which one was meant is worse than failing. The identifier falls
         through unchanged and authenticate() says no, with the same
         sentence any other wrong answer gets.

    Returns a string either way; it never raises and never reveals
    whether anything matched.
    """
    identifier = (identifier or '').strip()
    if not identifier:
        return identifier
    if User.objects.filter(username=identifier).exists():
        return identifier
    if '@' not in identifier:
        return identifier
    found = list(User.objects.filter(email__iexact=identifier)[:2])
    return found[0].username if len(found) == 1 else identifier


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
        typed = (request.POST.get("username") or '').strip()
        password = request.POST.get("password") or ''
        # EITHER A USERNAME OR AN EMAIL - A3. See account_for().
        username = account_for(typed)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # NO SUCCESS MESSAGE. Demetri: "It is either a failure (and then
            # it is a red message at the login screen) or otherwise, you just
            # log in." Landing on the application IS the confirmation.
            return redirect(_safe_next(request) or 'home')
        # `username` is already account_for()'s answer, so an
        # email plus the right password on a disabled account
        # reaches this branch rather than falling through to
        # the generic line.
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


# NO @login_required HERE - LU-1, 5 Oct 2026.
#
# It used to carry one, and that is how a dead session became a 404:
# @login_required redirected to LOGIN_URL, which was unset. LOGIN_URL is
# set now, but the decorator would still be wrong here - it would send
# somebody to the login page carrying ?next=/logout/, so that logging in
# logged them straight back out.
#
# Django's own LogoutView has never required a login either. Logging out
# when you are already out is a no-op, and logout() is happy to be called
# on an anonymous request. The view ends at the public home page, which
# is the right place to be in both cases.
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
        # EITHER, HERE TOO - A3. Somebody who thinks of themselves
        # as `Demetrios` should not be told nothing happened because they
        # typed it. The link still goes to the ADDRESS ON THE ACCOUNT and
        # never to whatever was typed, so this adds no way to send mail
        # anywhere new.
        typed = (request.POST.get('email') or '').strip()
        if typed:
            for user in User.objects.filter(
                    Q(email__iexact=typed) | Q(username=account_for(typed)),
                    is_active=True).distinct():
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
            '(%s).\n\nRequested by: %s\n\nThe link works once and expires '
            'after three days. The existing password has not been changed '
            'and keeps working until the link is used.'
            % (user.username, user.email or 'no address', who))
    return send_html_email(subject, body, text, recipients)