# -*- coding: utf-8 -*-
"""SE-1b - THE SUITE COUNT GOES, THE CHECK IT GUARDED STAYS.

Demetri, 7 Oct 2026, after CM-1: "What suites did CM-1 break and why? I
don't understand. I made so many changes to the system before and not
once did the sweep."

NONE OF THE THREE WAS ABOUT HIS APPLICATION. test_passport_holder
claimed to be the latest migration, test_ei_modal read a page live
instead of at its own round's scope - both defects in the suites, both
fixed in CM-1 - and this one:

    BOOT_COUNT = 12    'exactly 12 suites boot Django'

SE-1 wrote that as a tripwire. The stated reason was that a floor would
let a suite with no throwaway SECRET_KEY of its own in silently, and
that suite would then die on any machine with no .env. The reason is
sound. The instrument is redundant, because six lines below it in the
same function test_settings_env ALREADY asks the question directly, by
glob, of however many suites there are:

    missing = [p for p in boots
               if "os.environ.setdefault('SECRET_KEY'" not in read(p)]
    ok(not missing, 'and every one of them supplies its own test key
       first', ...)
    ... and 'supplies it before the settings module is named'

Those two catch exactly the defect, on any suite, at any number. The
count catches nothing they miss - it only fires every time a round adds
a suite that boots Django, which is a line of maintenance per round for
no information. It had already been raised three times in two days:
9 -> 11 in E-2b, 11 -> 12 in E-2c, 12 -> 13 in CM-1.

A TRIPWIRE ON A DOOR THAT IS ALREADY LOCKED. It goes.

WHAT STAYS, AND THE SUITE NOW PROVES IT. test_settings_env keeps both
direct checks and gains one more: that the count is gone and has not
been quietly replaced by a different number somewhere else.

FILES: apply_settings_env.py, test_settings_env.py. No new suite - the
suite that carried the redundant check is the one that should assert its
absence.
"""
import os
import re
import sys

SUFFIX = '.bak_bootfree'
MARK = 'SE-1b, 7 Oct 2026'

ROOT = os.path.dirname(os.path.abspath(__file__))
APPLY = os.path.join(ROOT, 'apply_settings_env.py')
SUITE = os.path.join(ROOT, 'test_settings_env.py')
CHECK = False


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    a, s = read(APPLY), read(SUITE)
    if MARK in s:
        print('SE-1b  already applied')
        return 1 if CHECK else 0

    # --- the premise ---------------------------------------------------
    m = re.search(r'^BOOT_COUNT = (\d+)$', a, re.M)
    if not m:
        raise SystemExit('SE-1b: BOOT_COUNT is not assigned in '
                         'apply_settings_env.py - nothing to remove')
    now = int(m.group(1))
    for needed in ("os.environ.setdefault('SECRET_KEY'",
                   'supplies it before the settings module is named'):
        if needed not in s:
            raise SystemExit('SE-1b: the DIRECT check is not in '
                             'test_settings_env.py (%r) - the count is not '
                             'redundant and must stay' % needed[:40])

    # --- the patcher: drop the constant and its gate --------------------
    a2 = re.sub(r'(?:^#[^\n]*\n)*^BOOT_COUNT = \d+\n', '', a, count=1,
                flags=re.M)
    if 'BOOT_COUNT' in a2.replace('hardened not in (0, BOOT_COUNT)', ''):
        pass
    # THE GATE THAT USED THE COUNT, AND THE MESSAGE THAT PRINTED IT.
    # SE-1's own refusal was "neither part is left half-done", and it
    # measured the suite half against the exact number. Without the
    # number the suite half has nothing to be half OF - harden_suites
    # hardens whatever it finds - so only the settings half stays
    # all-or-nothing, and the message stops quoting a total it no
    # longer has.
    OLD_GATE = ("    if done not in (0, len(TARGETS)) or hardened not in "
                "(0, BOOT_COUNT):\n"
                "        print('SE-1  REFUSED: partial application "
                "(settings %d/%d, '\n"
                "              'suites %d/%d)' % (done, len(TARGETS), "
                "hardened, BOOT_COUNT))\n")
    NEW_GATE = ("    # SE-1b, 7 Oct 2026: the suite half no longer has a\n"
                "    # target number to be half of, because the count is\n"
                "    # gone. Only the settings half is all-or-nothing.\n"
                "    if done not in (0, len(TARGETS)):\n"
                "        print('SE-1  REFUSED: partial application "
                "(settings %d/%d, '\n"
                "              'suites hardened %d)' % (done, "
                "len(TARGETS), hardened))\n")
    if a2.count(fit(a2, OLD_GATE)) != 1:
        raise SystemExit('SE-1b: the refusal gate matched %d time(s), not '
                         'once' % a2.count(fit(a2, OLD_GATE)))
    a2 = a2.replace(fit(a2, OLD_GATE), fit(a2, NEW_GATE), 1)
    if 'BOOT_COUNT' in a2:
        raise SystemExit('SE-1b: BOOT_COUNT survives in '
                         'apply_settings_env.py: %r'
                         % a2[a2.index('BOOT_COUNT') - 60:
                              a2.index('BOOT_COUNT') + 60])

    # --- the suite: drop the count, keep the two direct checks ----------
    OLD = """    from apply_settings_env import BOOT_ANCHOR, BOOT_COUNT

    boots = [p for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py')))
             if BOOT_ANCHOR in read(p)]
    ok(len(boots) == BOOT_COUNT,
       '%d suites boot Django' % BOOT_COUNT,
       'found %d: %s' % (len(boots),
                         [os.path.basename(p) for p in boots]))
"""
    NEW = """    from apply_settings_env import BOOT_ANCHOR

    boots = [p for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py')))
             if BOOT_ANCHOR in read(p)]
    # NO EXACT COUNT ANY MORE.                    [SE-1b, 7 Oct 2026]
    # This asserted len(boots) == BOOT_COUNT, and the reason given was
    # that a floor would let a suite with no key of its own in silently.
    # It would not: the two checks immediately below ask that question
    # DIRECTLY, by glob, of however many suites exist. The count caught
    # nothing they miss and fired every time a round added a suite -
    # three times in two days, 9 to 11 to 12 to 13 - which is a line of
    # maintenance per round for no information. A tripwire on a door
    # that is already locked.
    ok(len(boots) > 0, '%d suite(s) boot Django' % len(boots), len(boots))
"""
    if s.count(fit(s, OLD)) != 1:
        raise SystemExit('SE-1b: the count block in test_settings_env.py '
                         'matched %d time(s), not once'
                         % s.count(fit(s, OLD)))
    s2 = s.replace(fit(s, OLD), fit(s, NEW), 1)

    # and the suite now asserts its own absence
    TAIL = "    ok('setdefault' in read(os.path.join(ROOT, 'apply_settings_env.py')),"
    GUARD = """    # AND THE COUNT IS GONE, AND HAS NOT COME BACK UNDER ANOTHER
    # NAME.                                       [SE-1b, 7 Oct 2026]
    ap = read(os.path.join(ROOT, 'apply_settings_env.py'))
    ok('BOOT_COUNT' not in ap,
       'apply_settings_env.py no longer keeps an exact count of them')
    ok('BOOT_ANCHOR' in ap,
       '  but it still names what makes a suite one - the anchor the '
       'glob above looks for')
"""
    if s2.count(fit(s2, TAIL)) != 1:
        raise SystemExit('SE-1b: the tail of section 4b matched %d time(s)'
                         % s2.count(fit(s2, TAIL)))
    s2 = s2.replace(fit(s2, TAIL), fit(s2, GUARD) + fit(s2, TAIL), 1)

    import ast
    for name, src in (('apply_settings_env.py', a2),
                      ('test_settings_env.py', s2)):
        try:
            ast.parse(src)
        except SyntaxError as e:
            raise SystemExit('SE-1b: %s would not parse - %s' % (name, e))

    if not CHECK:
        backup(APPLY); write(APPLY, a2)
        backup(SUITE); write(SUITE, s2)

    print('SE-1b  BOOT_COUNT removed (it stood at %d)' % now)
    print('SE-1b  the two direct checks stay, and the suite now asserts '
          'the count is gone')
    if CHECK:
        print('SE-1b  NOT APPLIED')
        return 1
    print('SE-1b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
