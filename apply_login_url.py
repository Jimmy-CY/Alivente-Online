"""LU-1 - THE 404 BEHIND EVERY GUARDED VIEW IN THE APP.

   Demetri, 5 Oct 2026, minutes after rotating SECRET_KEY:
   "Logged Out... Got this error." - alivente.online/accounts/login/
   ?next=/logout/ answering "Not Found".

   WHAT ACTUALLY HAPPENED, in order:

     1. Rotating SECRET_KEY invalidates every session cookie ever issued.
        That is the rotation working. His own session died with the rest.
     2. He pressed Logout.
     3. logout_user carried @login_required. Nobody was logged in, so
        Django redirected to settings.LOGIN_URL.
     4. LOGIN_URL was COMMENTED OUT in mysite/settings.py, so Django used
        its own default of /accounts/login/.
     5. This project has never routed /accounts/anything. 404.

   THIS IS NOT A LOGOUT BUG. There are 282 @login_required decorators
   across 34 view modules, and every one of them answered a dead session
   with that same 404. It has been true for the life of the project. It
   never showed because sessions here effectively never died - no cache
   backend, a long cookie age, and a handful of users who stay logged in.
   The key rotation is simply the first event that ended every session at
   once, and it found the defect immediately.

   TWO EDITS, because one without the other leaves a trap:

     settings.py   LOGIN_URL = '/login/'. All 282 views now reach the
                   login page that exists.

     auth.py       @login_required comes OFF logout_user. With only the
                   first edit, pressing Logout with a dead session sends
                   you to the login page carrying ?next=/logout/ - so you
                   log in, and are immediately logged straight back out
                   again. Django's own LogoutView has never required a
                   login for exactly this reason: logging out when you
                   are already out is not an error, it is a no-op. The
                   view already ends at the public home page.

   WHAT IS DELIBERATELY NOT TOUCHED. LOGIN_REDIRECT_URL on the next line
   stays commented, because this app never reads it: login_user ends on
   `redirect(_safe_next(request) or 'home')` and consults the setting
   nowhere. Uncommenting it would change no behaviour and would read like
   it did. Demetri chose "LOGIN_URL and free the Logout view".

   FILES: mysite/settings.py, pages/views/auth.py.
                                                    [test_login_url.py]
"""
import os
import re
import sys

SUFFIX = '.bak_loginurl'

SETTINGS = os.path.join('mysite', 'settings.py')
AUTH = os.path.join('pages', 'views', 'auth.py')


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def once(text, needle, what):
    """`text` must contain `needle` exactly once, or nothing happens.

    Every anchor in this round is a single short line, and a short line is
    exactly the kind of anchor that turns up twice in a long file."""
    n = text.count(needle)
    if n != 1:
        raise SystemExit('LU-1: %s appears %d times, expected 1' % (what, n))
    return True


# ------------------------------------------------------------- settings

OLD_SETTING = '#LOGIN_URL = "/login/"'

NEW_SETTING = '''# WHERE A GUARDED VIEW SENDS SOMEBODY WITH NO SESSION - LU-1, 5 Oct 2026.
#
# This line was commented out, so Django fell back to its own default of
# /accounts/login/ - a URL this project has never routed. All 282
# @login_required views therefore answered a dead session with a 404
# instead of a login page.
#
# It never showed, because sessions here effectively never died. Rotating
# SECRET_KEY on 5 Oct ended every one of them at once, Demetri pressed
# Logout, and the 404 arrived within the minute.
#
# THE LINE BELOW STAYS COMMENTED ON PURPOSE. login_user ends on
# `redirect(_safe_next(request) or 'home')` and never reads
# LOGIN_REDIRECT_URL, so setting it would change no behaviour while
# reading as though it did.
#                                                  [test_login_url.py]
LOGIN_URL = '/login/\''''


def do_settings(check):
    text = read(SETTINGS)
    if 'LOGIN_URL = \'/login/\'' in text and OLD_SETTING not in text:
        return 0
    once(text, fit(text, OLD_SETTING), 'the commented LOGIN_URL')
    text = text.replace(fit(text, OLD_SETTING), fit(text, NEW_SETTING), 1)
    if not check:
        backup(SETTINGS)
        write(SETTINGS, text)
    return 1


# ----------------------------------------------------------------- auth

DEC = '@login_required\ndef logout_user(request):'
NODEC = '''# NO @login_required HERE - LU-1, 5 Oct 2026.
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
def logout_user(request):'''

OLD_DOC = '- logout_user        : Logs out the current user (@login_required).'
#
# NOT A WORD OF THIS MAY SPELL THE DECORATOR'S NAME. The import is
# removed below only if the name appears nowhere live in the file, and
# this docstring is live - a module docstring is not a comment line. Say
# "no login guard" and the import goes; say the name and it stays, the
# count comes up short, and the gate refuses the whole round.
NEW_DOC = ('- logout_user        : Logs out whoever is logged in, if anyone, and\n'
           '                       returns to the public home page. It carries no\n'
           '                       login guard at all - see LU-1 at the view for\n'
           '                       why that is deliberate.')

OLD_IMPORT = 'from django.contrib.auth.decorators import login_required\n'


def do_auth(check):
    text = read(AUTH)
    done = 0

    old = fit(text, DEC)
    if old in text:
        once(text, old, 'the decorated logout_user')
        text = text.replace(old, fit(text, NODEC), 1)
        done += 1

    old = fit(text, OLD_DOC)
    if old in text:
        once(text, old, 'the logout_user docstring line')
        text = text.replace(old, fit(text, NEW_DOC), 1)
        done += 1

    # The import goes only once the decorator has, and only if nothing
    # else in the file uses the name. A round that deletes an import
    # something still calls is a round that breaks the module on boot.
    #
    # THE COMMENT LINES HAVE TO COME OUT FIRST. The replacement block
    # above EXPLAINS why there is no @login_required here, so it contains
    # the word - and a bare `in text` test reads its own explanation as
    # live code and leaves the import behind. The gate then refuses the
    # round for being partial, which is how this was caught.
    live = '\n'.join(ln for ln in text.replace('\r\n', '\n').split('\n')
                     if not ln.lstrip().startswith('#'))
    live = live.replace(OLD_IMPORT.strip(), '')
    if 'login_required' not in live:
        old = fit(text, OLD_IMPORT)
        if old in text:
            once(text, old, 'the login_required import')
            text = text.replace(old, '', 1)
            done += 1

    if done and not check:
        backup(AUTH)
        write(AUTH, text)
    return done


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    s = do_settings(check)
    a = do_auth(check)

    print('LU-1  settings edits : %d' % s)
    print('LU-1  auth.py edits  : %d' % a)

    if check:
        if s or a:
            print('LU-1  NOT APPLIED')
            return 1
        print('LU-1  applied')
        return 0
    if s not in (0, 1) or a not in (0, 3):
        print('LU-1  REFUSED: partial application (settings %d/1, auth %d/3)'
              % (s, a))
        return 2
    print('LU-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
