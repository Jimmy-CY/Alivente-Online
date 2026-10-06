"""SE-1 - THE LAST TWO SECRETS LEAVE settings.py.

   Demetri, 4 Oct 2026: "Let's fix this now as well."

   WHAT WAS ACTUALLY HARD-CODED, after I got it wrong once. I told him the
   Anthropic key was a literal at line 345. It never was - that line has
   always read os.getenv('ANTHROPIC_API_KEY'). I had masked my own command
   output with a regex that replaced everything after the `=`, which turned
   os.getenv(...) into <redacted>, and then read my own masking back as
   evidence. Two settings are literals, not three:

       line  28   SECRET_KEY        "django-insecure-..."
       line 355   USDA_API_KEY      '...'

   ANTHROPIC_API_KEY (345), GEOAPIFY_KEY (353) and DEBUG (31) already read
   the environment and this round does not touch them.

   AND THE SAME REGEX MASKED NOTHING TWICE. While establishing the above I
   printed both literals in full into the conversation - the USDA key
   because my pattern matched one line shape and not another, and
   SECRET_KEY because it is written with double quotes and the pattern only
   matched single ones. Both were already in git history; they are now in a
   transcript as well. Both are being rotated.

   THE RULE THAT COMES OUT OF IT, and which this round's suite enforces on
   itself: never print a line that might hold a secret and trust a regex to
   mask it. Test the SHAPE - is the right-hand side a getenv call - and
   print the verdict. Never the value. This patcher matches both lines by
   shape and never puts the matched text anywhere it could be printed.

   WHY THE SETTING NAMES SURVIVE. The temptation is to delete the lines.
   Both are read through Django settings, not only through the environment:

       USDA_API_KEY   -> pages/usda_client.py:70, getattr(settings, ...)
       SECRET_KEY     -> Django itself, signing session cookies and
                         password-reset tokens

   so the names have to stay and only their SOURCE changes. usda_client
   already handles a missing key with its own message, and Django already
   refuses to run on an empty SECRET_KEY, so neither needs a guard invented
   here.

   ORDER, AND WHY THIS ROUND WAS HELD BACK. Demetri set both variables in
   Railway and in his local .env BEFORE this was built, with the values the
   file currently holds, so the change is behaviour-neutral on the way in:
   the same strings reach the same settings by a different route. Rotation
   is a separate act, his, one key at a time with a check after each -
   claude/secrets_to_environment_4_oct.md has the steps.

   WHAT THIS DOES NOT DO. The old values stay in every commit already
   pushed. Moving them out of the file stops the next leak; only rotating
   makes the leaked ones worthless.

   FILES: mysite/settings.py.                   [test_settings_env.py]
"""
import os
import re
import sys

SUFFIX = '.bak_setenv'

SETTINGS = 'mysite/settings.py'

# Matched by SHAPE, so the patcher never has to hold the value anywhere it
# could be printed, logged or put in an error message. The name is on the
# left of the `=`; everything right of it is a quoted literal we replace
# without looking at.
TARGETS = [
    ('SECRET_KEY',
     "SECRET_KEY = os.getenv('SECRET_KEY', '')",
     '# SECURITY WARNING: keep the secret key used in production secret!\n'
     '# SE-1, 4 Oct 2026 - this was a literal, and the literal is in every\n'
     '# commit ever pushed. Set in Railway and in the local .env; rotated\n'
     '# separately, because moving it does not un-expose the old one.\n'
     '# Django refuses to run on an empty SECRET_KEY, which is the right\n'
     '# failure and does not need one invented here.\n'),
    ('USDA_API_KEY',
     "USDA_API_KEY = os.getenv('USDA_API_KEY', '')",
     '# SE-1, 4 Oct 2026 - was a literal. pages/usda_client.py reads it\n'
     '# through getattr(settings, ...) and already says so clearly when it\n'
     '# is missing, so the name stays and only the source changes.\n'),
]

# `NAME = <quoted literal>` at the start of a line, either quote style.
# [ \t]*$ and NOT \s*$. In multiline mode \s matches a newline, so
# \s*$ swallows the blank line that follows the declaration - which it did,
# closing the gap before the next comment block. A round that moves a
# secret should not also reflow the file around it.
# \r is in the trailing class because settings.py is CRLF: in multiline
# mode $ matches before the \n, leaving the \r unconsumed, and the first
# build of this fix matched nothing at all.
LITERAL = r'(?m)^%s[ \t]*=[ \t]*(?:"[^"\n]*"|\'[^\'\n]*\')[ \t\r]*$'


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


def is_env(text, name):
    """Does `name` read the environment? A shape question, answered without
    the value ever leaving this function."""
    m = re.search(r'(?m)^%s\s*=\s*(.*)$' % name, text)
    if not m:
        return None
    rhs = m.group(1)
    return ('getenv' in rhs) or ('environ' in rhs)


# ---- the suites that boot Django need a key of their own ----------------
#
# THE TRAP SE-1 WOULD OTHERWISE HAVE SET. The moment SECRET_KEY reads the
# environment, any suite that boots Django and touches signing - sessions,
# CSRF, a password-reset token - dies with
#
#     ImproperlyConfigured: The SECRET_KEY setting must not be empty
#
# unless a .env happens to be present. test_auth_flow found it within
# minutes of the round being applied, making a reset token. On Demetri's
# laptop .env supplies the key and nothing would have shown; in a fresh
# clone, or in any sandbox, the whole suite collapses on configuration it
# has no business depending on.
#
# A TEST RUN IS NOT A DEPLOYMENT. It should supply its own key, and that
# key is not a credential - it signs nothing that outlives the process.
# setdefault, so a real environment always wins.
BOOT_ANCHOR = ("os.environ.setdefault('DJANGO_SETTINGS_MODULE', "
               "'mysite.settings')")

BOOT_NEW = (
    "# SE-1 - a test run signs with its own throwaway key. SECRET_KEY\n"
    "%(i)s# reads the environment now, and a suite that boots Django must\n"
    "%(i)s# not fall over because a .env is absent. setdefault, so a real\n"
    "%(i)s# key always wins; this one signs nothing that leaves the test.\n"
    "%(i)sos.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')\n"
    "%(i)s" + BOOT_ANCHOR)

# EIGHT, NOT SEVEN, SINCE 5 OCT 2026. LU-1 added test_login_url.py,
# which boots Django to ask what login_required does with an
# anonymous request. It was written carrying its own setdefault, so
# nothing was broken - but this count failed, which is exactly what
# it is for. An exact number is a tripwire; a floor would have let a
# suite with no key of its own in silently, and that suite would
# fail on any machine without a .env.
#
# Raise it deliberately, with the suite named, every time.
# 11 since 6 Oct 2026: Section E added test_url_names.py, which
# boots Django to resolve names and compile templates, and
# test_access_denied.py, which boots it to render one. Both were
# written carrying their own setdefault - this number is the
# tripwire that proves it rather than assuming it.
BOOT_COUNT = 11


def harden_suites(check):
    """Give every suite that boots Django a key of its own."""
    import glob
    done = 0
    for path in sorted(glob.glob('test_*.py')):
        text = read(path)
        if "os.environ.setdefault('SECRET_KEY'" in text:
            continue
        anchor = fit(text, BOOT_ANCHOR)
        n = text.count(anchor)
        if n == 0:
            continue
        if n != 1:
            raise SystemExit('SE-1: %s boots Django %d times - refusing'
                             % (path, n))
        # Keep whatever indentation the call already has.
        m = re.search(r'(?m)^([ \t]*)' + re.escape(anchor), text)
        indent = m.group(1) if m else ''
        new = fit(text, BOOT_NEW % {'i': indent})
        text = text.replace(indent + anchor, indent + new, 1)
        if not check:
            backup(path)
            write(path, text)
        done += 1
    return done


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    text = read(SETTINGS)
    done = 0

    for name, new_line, comment in TARGETS:
        if is_env(text, name):
            continue                      # already applied
        hits = re.findall(LITERAL % name, text)
        if len(hits) != 1:
            raise SystemExit('SE-1: %s matched %d literal lines, expected 1 '
                             '- refusing to guess' % (name, len(hits)))
        replacement = fit(text, comment + new_line)
        text = re.sub(LITERAL % name, lambda _m: replacement, text, count=1)
        done += 1

    # The old SECURITY WARNING comment above SECRET_KEY is now said twice.
    old_warn = ('# SECURITY WARNING: keep the secret key used in production '
                'secret!\n# SECURITY WARNING: keep the secret key used in '
                'production secret!\n')
    o = fit(text, old_warn)
    if o in text:
        text = text.replace(o, fit(text, '# SECURITY WARNING: keep the secret '
                                         'key used in production secret!\n'))

    if done and not check:
        backup(SETTINGS)
        write(SETTINGS, text)

    hardened = harden_suites(check)

    print('SE-1  settings moved to the environment : %d' % done)
    print('SE-1  suites given a test key           : %d' % hardened)

    if check:
        if done or hardened:
            print('SE-1  NOT APPLIED')
            return 1
        print('SE-1  applied')
        return 0
    # EACH PART ALL-OR-NOTHING, not both-or-neither. The first version of
    # this gate demanded that the settings edits and the suite hardening
    # both happen in the same run, and refused a run where the settings
    # were already done and only the suites were outstanding - which is
    # exactly what happened when the hardening was added to a round that
    # had already been applied once. The claim worth gating is that
    # neither part is left half-done, and that is what this says.
    if done not in (0, len(TARGETS)) or hardened not in (0, BOOT_COUNT):
        print('SE-1  REFUSED: partial application (settings %d/%d, '
              'suites %d/%d)' % (done, len(TARGETS), hardened, BOOT_COUNT))
        return 2
    print('SE-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
