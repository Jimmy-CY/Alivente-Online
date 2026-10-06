# -*- coding: utf-8 -*-
"""E-2c - SEVEN SUITES GET THE REAL URLconf BACK.

E-2 could not be measured at all until the sandbox mirror was repaired.
`crs/views/config.py` does `from crs.forms import CountryConfigurationForm`
and `crs/forms.py` was not in the mirror, so importing `mysite.urls` -
the project's real ROOT_URLCONF - died there. The laptop has always had
the file. It was a gap in the mirror, not a fact about the product, and
the first E-2 measurement reported 260 of 260 URL names as broken on the
strength of it.

SEVEN SUITES HAD ALREADY WORKED AROUND IT, each with one line:

    test_auth_flow.py        dj_settings.ROOT_URLCONF = 'pages.urls'
    test_filter_distinct.py  dj.ROOT_URLCONF = 'pages.urls'
    test_filter_get.py       dj.ROOT_URLCONF = 'pages.urls'
    test_filters_in_rc.py    dj.ROOT_URLCONF = 'pages.urls'
    test_login_email.py      dj.ROOT_URLCONF = 'pages.urls'
    test_login_url.py        dj_settings.ROOT_URLCONF = 'pages.urls'
    test_notify_types.py     dj.ROOT_URLCONF = 'pages.urls'

Six carry it with no comment at all, inside the same block that swaps
DATABASES to in-memory sqlite. Only test_login_url.py says why - and
says it as a fact about the product that it was not - and that one is
also honest about the price: "What that substitution cannot see is
whether some OTHER include answers /accounts/login/."

IT IS NOT A HYPOTHETICAL PRICE. Measured 6 Oct, through both URLconfs:

    mysite.urls   /crs/  ->  crs:index          reverse('crs:index') ok
    pages.urls    /crs/  ->  404                reverse('crs:index') NOT FOUND

A suite resolving against pages.urls is blind to every URL the project
mounts outside that include, and says 404 where the app says 200.

MEASURED BEFORE THIS ROUND WAS WRITTEN. Each of the seven was edited to
mysite.urls, run, and reverted, one at a time. All seven passed - 152,
71, 120, 88, 49, rc=0, 26. Nothing any of them asserts depends on the
substitution.

WHAT ELSE THIS ROUND CHANGES. test_login_url.py section 3 reads
mysite/urls.py AS TEXT and checks the include prefixes, because it could
not import the thing it wanted to ask. It can now resolve, and the
reading stays as a second, independent check rather than as a stand-in.
Its comments are rewritten: a file that records a sandbox gap as its
reason would be lying about its own shape.

FILES: seven suites.                        [test_root_urlconf.py]
"""
import os
import re
import sys

SUFFIX = '.bak_rooturl'
MARK = 'E-2c, 6 Oct 2026'

ROOT = os.path.dirname(os.path.abspath(__file__))
CHECK = False

OLD_CONF = "ROOT_URLCONF = 'pages.urls'"
NEW_CONF = "ROOT_URLCONF = 'mysite.urls'"

# The six that carry the line bare. Each is (file, the exact variable the
# file uses). The anchor is the WHOLE LINE including its indent, matched
# exactly once - 'pages.urls' on its own appears in prose in at least one
# of these files, and an anchor that can hit prose is how a patcher edits
# something nobody meant.
BARE = [
    ('test_auth_flow.py', 'dj_settings'),
    ('test_filter_distinct.py', 'dj'),
    ('test_filter_get.py', 'dj'),
    ('test_filters_in_rc.py', 'dj'),
    ('test_login_email.py', 'dj'),
    ('test_notify_types.py', 'dj'),
]

NOTE = (
    "    # THE REAL ROOT URLconf, since %s. This read 'pages.urls'\n"
    "    # because the sandbox mirror did not carry crs/forms.py, so\n"
    "    # importing mysite.urls died on it - a gap in the mirror, not a\n"
    "    # fact about the product; the laptop has always had the file.\n"
    "    # Measured both ways before the line moved: under pages.urls\n"
    "    # /crs/ answers 404 and crs:index does not reverse at all, so a\n"
    "    # suite resolving against it is blind to every URL the project\n"
    "    # mounts outside that one include.               [E-2c]\n"
) % MARK


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
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def swap(name, edits):
    """Whole-line edits, every anchor exactly once or nothing is written."""
    path = os.path.join(ROOT, name)
    text = read(path)
    if MARK in text:
        print('  %-26s already carries %s' % (name, MARK))
        return 0
    for old, _new, what in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit('E-2c: %s - the anchor for %s matched %d '
                             'time(s), not once' % (name, what, n))
    for old, new, _what in edits:
        text = text.replace(old, fit(text, new), 1)
    if OLD_CONF in text:
        raise SystemExit('E-2c: %s still names pages.urls as its root '
                         'after the rewrite' % name)
    if text.count(NEW_CONF) != 1:
        raise SystemExit('E-2c: %s does not name mysite.urls exactly once '
                         'after the rewrite' % name)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-26s %d edit(s)' % (name, len(edits)))
    return 1


# ==========================================================================
# test_login_url.py - the one with more than a line in it
# ==========================================================================
LU_OLD_COMMENT = (
    "    # RESOLVING AGAINST pages.urls, AND SAYING SO. mysite/urls.py also\n"
    "    # includes crs.urls, and the sandbox mirror does not carry the crs\n"
    "    # view package - importing the project root URLconf here dies on\n"
    "    # `from crs.views import main`, which is a gap in the mirror and not\n"
    "    # a fact about the product. pages.urls is what mysite/urls.py mounts\n"
    "    # at '', and every account URL in the app lives in it.\n"
    "    #\n"
    "    # What that substitution cannot see is whether some OTHER include\n"
    "    # answers /accounts/login/. Section 3 reads mysite/urls.py and checks\n"
    "    # the prefixes directly, which settles it without importing anything.\n"
    "    dj_settings.ROOT_URLCONF = 'pages.urls'\n")

LU_NEW_COMMENT = (
    "    # RESOLVING AGAINST THE PROJECT'S OWN ROOT, since %s.\n"
    "    # This read 'pages.urls' until then, and the comment that stood\n"
    "    # here gave the reason as `from crs.views import main` failing -\n"
    "    # which was true only of the sandbox mirror, which was missing\n"
    "    # crs/forms.py. The laptop has always had it. A suite that\n"
    "    # records a gap in a copy of the tree as a fact about the tree\n"
    "    # is the kind of wrong that outlives whoever wrote it.\n"
    "    #\n"
    "    # IT ALSO COST SOMETHING. The old comment said so itself: the\n"
    "    # substitution could not see whether some OTHER include answers\n"
    "    # /accounts/login/. Section 3 now asks the whole project instead\n"
    "    # of reading mysite/urls.py as text for that half.    [E-2c]\n"
    "    dj_settings.ROOT_URLCONF = 'mysite.urls'\n") % MARK

LU_OLD_S3 = (
    "    ok(routed(DJANGO_DEFAULT) is None,\n"
    "       '%s resolves to nothing in pages.urls' % DJANGO_DEFAULT,\n"
    "       'something answers it - then the 404 had another cause')\n")

LU_NEW_S3 = (
    "    # THE WHOLE PROJECT, NOT ONE INCLUDE. Before E-2c this resolved\n"
    "    # against pages.urls and could only speak for that mount.\n"
    "    ok(routed(DJANGO_DEFAULT) is None,\n"
    "       '%s resolves to nothing ANYWHERE in the project'\n"
    "       % DJANGO_DEFAULT,\n"
    "       'something answers it - then the 404 had another cause')\n")

LU_OLD_READ = (
    "# AND NOTHING ELSE MOUNTED AT THE ROOT COULD ANSWER IT EITHER. This is\n"
    "# the half pages.urls cannot speak for, so it is read off mysite/urls.py\n"
    "# rather than resolved: every include has a prefix, and a prefix that is\n"
    "# not '' and is not a prefix of 'accounts/' can never produce the URL.\n")

LU_NEW_READ = (
    "# AND THE SAME THING ASKED A SECOND WAY, off the text of mysite/urls.py.\n"
    "# Until E-2c this reading was a STAND-IN for a resolve that could not be\n"
    "# run; the resolve above now runs against the real root, so this is a\n"
    "# cross-check instead - a different instrument reaching the same answer.\n"
    "# Every include has a prefix, and a prefix that is not '' and is not a\n"
    "# prefix of 'accounts/' can never produce the URL.\n")


# ==========================================================================
# SE-1'S TRIPWIRE, WHICH THIS ROUND MOVES BY ONE
# ==========================================================================
# apply_settings_env.py keeps an EXACT count of the suites that boot
# Django, deliberately: a floor would let a suite with no throwaway key
# of its own in silently, and that suite would then fail on any machine
# without a .env. test_root_urlconf.py boots Django to ask two URLconfs
# the same questions, so the number goes up by one and is raised HERE,
# by the round that added the suite, rather than by whoever next runs
# the sweep and finds it red.
SE = 'apply_settings_env.py'
SE_OLD = 'BOOT_COUNT = 11\n'
SE_NEW = ('# 12 since 6 Oct 2026: Section E round E-2c added\n'
          '# test_root_urlconf.py, which boots Django to resolve the same\n'
          '# paths through mysite.urls and pages.urls side by side. It\n'
          '# carries its own setdefault; this number is what proves that\n'
          '# rather than assuming it.\n'
          'BOOT_COUNT = 12\n')


def patch_se():
    path = os.path.join(ROOT, SE)
    text = read(path)
    if 'BOOT_COUNT = 12' in text:
        print('  %-26s already at 12' % SE)
        return
    n = text.count(SE_OLD)
    if n != 1:
        raise SystemExit('E-2c: %s - BOOT_COUNT = 11 matched %d time(s), '
                         'not once' % (SE, n))
    text = text.replace(SE_OLD, fit(text, SE_NEW), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-26s boot count 11 -> 12' % SE)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    print('')
    print('  THE SIX THAT CARRIED IT BARE')
    print('  ' + '-' * 70)
    n = 0
    for name, var in BARE:
        line = "    %s.%s\n" % (var, OLD_CONF)
        n += swap(name, [(line, NOTE + "    %s.%s\n" % (var, NEW_CONF),
                          'the URLconf line')])

    print('')
    print('  AND THE ONE THAT EXPLAINED ITSELF')
    print('  ' + '-' * 70)
    n += swap('test_login_url.py', [
        (LU_OLD_COMMENT, LU_NEW_COMMENT, 'the comment and the line'),
        (LU_OLD_S3, LU_NEW_S3, "section 3's resolve"),
        (LU_OLD_READ, LU_NEW_READ, "section 3's text reading"),
    ])

    # NOT ONE SUITE MAY BE LEFT BEHIND. A round that moved six of seven
    # would leave a tree nobody measured, and the one left would be the
    # only evidence that the others ever needed moving.
    print('')
    print('  SE-1 COUNT')
    print('  ' + '-' * 70)
    patch_se()

    print('')
    left = []
    for name in sorted(f for f in os.listdir(ROOT)
                       if f.startswith('test_') and f.endswith('.py')):
        if OLD_CONF in read(os.path.join(ROOT, name)):
            left.append(name)
    if left and not CHECK:
        raise SystemExit('E-2c: %d suite(s) still name pages.urls as their '
                         'root: %s' % (len(left), ', '.join(left)))

    print('E-2c  suites moved : %d' % n)
    print('E-2c  still on pages.urls : %d' % len(left))
    if CHECK:
        print('E-2c  NOT APPLIED')
        return 1
    print('E-2c  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
