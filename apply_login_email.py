# -*- coding: utf-8 -*-
"""SECTION A, ROUND A3 - LOG IN WITH THE EMAIL ADDRESS TOO

1 Oct 2026. Demetri reset the password on demetri.manias@alivente.com,
set it, and could not log in. Two things were in the way: that account is
ACTIVE=NO, and - the part this round is about - its USERNAME is
`Demetrios`, not the address.

HE REACHED FOR THE EMAIL BECAUSE THE RESET WAS ABOUT THE EMAIL. The link
arrived at an address, the page asked for a new password, and the login
screen then asked for something else entirely. The email does say "Your
username is Demetrios", and it was still the wrong guess to have to make.
Anybody invited into this system from now on starts the same way.

So the login box takes either. And so does Forgot Password, for the same
reason in reverse: somebody who thinks of themselves as `Demetrios`
should not be told nothing happened because they typed it.

---------------------------------------
THE RESOLUTION ORDER, AND WHY EACH STEP
---------------------------------------
    1. IF IT NAMES AN ACCOUNT, IT IS A USERNAME. Checked first and
       exactly, so a username always beats an email that happens to look
       like one. Nothing can be made ambiguous by somebody else choosing
       an address.
    2. NO @, NO LOOKUP. A string with no @ in it is not an address, and
       asking the database anyway is a query that can only answer no.
    3. EXACTLY ONE MATCH, case-insensitively - the same spelling
       Forgot Password and A1's duplicate check already use.
    4. TWO MATCHES REFUSE. Not "pick the first": two accounts behind one
       address is a state this system no longer allows but may still
       contain, and guessing which one somebody meant is worse than
       failing. It falls through unchanged and authenticate() says no.

A1 LAID THE GROUND FOR THIS WITHOUT MEANING TO. Email became required on
both Add User and Edit User, and duplicates are refused with
email__iexact, so an address now identifies exactly one account by
construction. Show-UserEmails.py measured the five existing accounts the
same morning: every address unique. This round would not have been safe a
day earlier.

-------------------------------------
NO NEW WAY TO ASK "DOES THIS EXIST?"
-------------------------------------
A wrong email and a wrong username get the SAME sentence, character for
character, exactly as before. The only message that is ever conditional
is the disabled-account one, and it still only appears to somebody who
typed the correct password.

THE DISABLED PATH USES THE SAME RESOLUTION, which is not a detail: resolve
only in login_user and an email plus the right password on a disabled
account falls through to "credentials are incorrect" - true, useless, and
precisely the dead end this round exists to remove.

---------------------
type="email" HAD TO GO
---------------------
Forgot Password's field was <input type="email" required>. A browser
refuses to submit `Demetrios` from one of those - the form never reaches
the view, so no amount of work in the view would have been visible. It
becomes type="text".

Backups: .bak_loginemail. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_loginemail'
CRLF = {}
SENTINEL = 'test_login_email.py'
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
            raise SystemExit('A3: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings.

    AND REFUSE AN ANCHOR THAT LANDS MID-LINE. An anchor beginning with
    spaces matches inside a MORE deeply indented line - "    if x:" is a
    substring of "        if x:" - so it replaces real code at the wrong
    indentation and leaves a file that will not parse. That happened on
    this round's first run, to this round's own patcher. An anchor whose
    match does not begin at a line start is a loose anchor, and the gate
    is cheaper than the traceback.
    """
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('A3: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('A3: the anchor for %s starts MID-LINE (after %r) - '
                         'it would edit a more-indented line' % (what,
                                                                text[i - 1]))
    return text.replace(o, n)


print('=' * 74)
print('SECTION A, ROUND A3 - THE EMAIL ADDRESS LOGS IN TOO%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')

# ---- 1. views/auth.py -------------------------------------------------
AP = os.path.join(ROOT, 'pages', 'views', 'auth.py')

HELPER_OLD = """def _disabled_with_right_password(username, password):"""
HELPER_NEW = '''def account_for(identifier):
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


def _disabled_with_right_password(username, password):'''

LOGIN_OLD = """        username = (request.POST.get("username") or '').strip()
        password = request.POST.get("password") or ''
        user = authenticate(request, username=username, password=password)"""
LOGIN_NEW = """        typed = (request.POST.get("username") or '').strip()
        password = request.POST.get("password") or ''
        # EITHER A USERNAME OR AN EMAIL - A3. See account_for().
        username = account_for(typed)
        user = authenticate(request, username=username, password=password)"""

FORGOT_OLD = """        address = (request.POST.get('email') or '').strip()
        if address:
            for user in User.objects.filter(email__iexact=address,
                                            is_active=True):
                _send_link(request, user, pwr.MODE_RESET)
                _notify_reset_requested(request, user)"""
FORGOT_NEW = """        # EITHER, HERE TOO - A3. Somebody who thinks of themselves
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
                _notify_reset_requested(request, user)"""

IMPORT_OLD = """from django.contrib.auth.models import User
from django.shortcuts import redirect, render"""
IMPORT_NEW = """from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render"""

DOC_OLD = """- login_user         : GET renders the login form; POST authenticates,"""
DOC_NEW = """- account_for        : maps whatever was typed in the login box - a
                       username or an email address - to the username to
                       authenticate. Added by round A3, 1 Oct 2026.
- login_user         : GET renders the login form; POST authenticates,"""

at, araw = read(AP)
if 'def account_for(' in at:
    print('  pages/views/auth.py          already done')
else:
    at = swap(at, IMPORT_OLD, IMPORT_NEW, 'the auth.py imports', AP)
    at = swap(at, DOC_OLD, DOC_NEW, 'the auth.py docstring', AP)
    at = swap(at, HELPER_OLD, HELPER_NEW, 'the disabled-account helper', AP)
    at = swap(at, LOGIN_OLD, LOGIN_NEW, 'login_user\'s read', AP)
    at = swap(at, FORGOT_OLD, FORGOT_NEW, 'password_forgot\'s lookup', AP)
    # THE DISABLED PATH RESOLVES TOO. login_user already passes the
    # RESOLVED username into it, so nothing more is needed there - but say
    # so, because the next reader will wonder.
    at = swap(at,
              "\n        if _disabled_with_right_password(username, password):",
              "\n        # `username` is already account_for()'s answer, so an\n"
              "        # email plus the right password on a disabled account\n"
              "        # reaches this branch rather than falling through to\n"
              "        # the generic line.\n"
              "        if _disabled_with_right_password(username, password):",
              'the disabled branch', AP)
    if not CHECK:
        back_up(AP, araw)
        write(AP, at)
    print('  pages/views/auth.py          account_for(), and both callers')

# ---- 2. the two fields say so -----------------------------------------
LP = alv_tree.path_of('login.html')
lt, lraw = read(LP)
if 'Username or Email' in lt:
    print('  login.html                   already done')
else:
    lt = swap(lt,
              '        <label for="usernameInput"><strong>Username</strong></label>\n'
              '        <input type="text" class="form-control" placeholder="Enter Username" name="username" id="usernameInput" value="{{ username|default:\'\' }}" autocomplete="username" autofocus>\n',
              '        {# EITHER, SINCE A3. The box takes a username or the      #}\n'
              '        {# address the invitation arrived at - which is what      #}\n'
              '        {# people reach for, because the reset was about the      #}\n'
              '        {# address.                     [test_login_email.py]     #}\n'
              '        <label for="usernameInput"><strong>Username or Email</strong></label>\n'
              '        <input type="text" class="form-control" placeholder="Enter username or email address" name="username" id="usernameInput" value="{{ username|default:\'\' }}" autocomplete="username" autofocus>\n',
              'the username field', LP)
    if not CHECK:
        back_up(LP, lraw)
        write(LP, lt)
    print('  login.html                   the box says it takes either')

FP = alv_tree.path_of('password_forgot.html')
ft, fraw = read(FP)
if 'or username' in ft:
    print('  password_forgot.html         already done')
else:
    ft = swap(ft,
              '                <label for="forgotEmail"><strong>Email Address</strong> <span class="alv-req">*</span></label>\n'
              '                <input type="email" name="email" id="forgotEmail" class="form-control"\n'
              '                       placeholder="Enter your email address"\n'
              '                       autocomplete="email" required>\n',
              '                {# type="text", NOT type="email" - A3. A browser    #}\n'
              '                {# refuses to submit `Demetrios` from an email      #}\n'
              '                {# field, so the form would never have reached the  #}\n'
              '                {# view and no work there would have shown.         #}\n'
              '                {#                        [test_login_email.py]     #}\n'
              '                <label for="forgotEmail"><strong>Email Address or Username</strong> <span class="alv-req">*</span></label>\n'
              '                <input type="text" name="email" id="forgotEmail" class="form-control"\n'
              '                       placeholder="Enter your email address or username"\n'
              '                       autocomplete="username" required>\n',
              'the forgot-password field', FP)
    ft = swap(ft,
              '            Type the email address on your account. A link to choose a new\n'
              '            password will be sent to it. The link works once and stops\n'
              '            working after three days.\n',
              '            Type the email address on your account, or your username.\n'
              '            A link to choose a new password is sent to the address on\n'
              '            the account. The link works once and stops working after\n'
              '            three days.\n',
              'the forgot-password blurb', FP)
    if not CHECK:
        back_up(FP, fraw)
        write(FP, ft)
    print('  password_forgot.html         takes either, and is not type=email')

# ---- 3. registration --------------------------------------------------
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_pwnotify',\n]\n",
         "    '.bak_pwnotify',\n    '%s',\n]\n" % SUFFIX, 'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_notify_types.py'\n)\n",
         "    'test_notify_types.py'\n"
         "    # The login box takes an email as well as a username. Its\n"
         "    # section 3 drives real sign-ins against a database it builds\n"
         "    # itself, and its control shows Django's own backend refusing\n"
         "    # the address - so the resolution step is provably what makes\n"
         "    # it work. Newest, so most likely to be what breaks.\n"
         "    'test_login_email.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-28s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-28s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

import ast                                                       # noqa: E402

src = read(AP)[0]
ast.parse(src)
print('  views/auth.py parses')

fn = next((n for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.FunctionDef) and n.name == 'account_for'), None)
if fn is None:
    raise SystemExit('A3: account_for is not there')
body = ast.get_source_segment(src, fn)

# THE ORDER IS THE DESIGN, SO THE ORDER IS GATED. A lookup by email that
# ran before the username check would let one person's address change
# which account another person's username reaches.
i_user = body.index("filter(username=identifier)")
i_at = body.index("'@' not in identifier")
i_mail = body.index("email__iexact=identifier")
if not (i_user < i_at < i_mail):
    raise SystemExit('A3: account_for checks the username AFTER the email - '
                     'an address could then shadow a username')
print('  and it checks username first, then the @, then the address')

if '[:2]' not in body or 'len(found) == 1' not in body:
    raise SystemExit('A3: account_for does not refuse an ambiguous address')
print('  and refuses rather than guesses when two accounts share an address')

# NO NEW CONDITIONAL MESSAGE. The round adds a way IN, not a way to ask
# whether an account exists.
login = ast.get_source_segment(src, next(
    n for n in ast.walk(ast.parse(src))
    if isinstance(n, ast.FunctionDef) and n.name == 'login_user'))
if login.count('messages.error') != 2:
    raise SystemExit('A3: login_user now has %d error messages, not the two '
                     'it had' % login.count('messages.error'))
print('  login_user still has exactly two messages, neither of them new')

# THE FIELD A BROWSER WOULD HAVE BLOCKED.
ftxt = read(FP)[0]
if re.search(r'<input type="email"[^>]*name="email"', ftxt):
    raise SystemExit('A3: the forgot field is still type="email", which no '
                     'browser will submit a username from')
print('  the Forgot Password field is type="text", so a username submits')

print('-' * 74)
print('  The login box takes a username or the address the invitation')
print('  arrived at, and so does Forgot Password. A username always wins,')
print('  and a shared address refuses rather than guesses.')
print('=' * 74)
