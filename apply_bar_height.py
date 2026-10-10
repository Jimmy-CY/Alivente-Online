# -*- coding: utf-8 -*-
"""apply_bar_height.py - Section D round D-1, 9 Oct 2026.

D-1 ASKED FOR ONE NUMBER FOR THE DESKTOP ACTION BAR. MEASURED, THE BAR
ALREADY HAS ONE.

The 6 Oct note recorded five heights on controls that sit side by side
- 30, 34, 35, 38, 44 - and asked which one the bar should settle on.
Re-measured on the real corpus with test_tap_target's own renderer,
across 109 business templates at 1280px:

    the action bar     265 control(s)    ONE height, 35px
    a table row        110 control(s)    34px, and one stray
    a modal             91 control(s)    38px, and four strays
    a card              41 control(s)    six heights
    loose on the page   37 control(s)    ten heights

The bar is uniform. So are table rows and modals. The five heights in
the original note came from a synthetic fixture holding one button of
each kind, not from any page - and a height measured without the real
markup around it is a height no user sees.

WHICH IS THE SAME MISTAKE I MADE THREE TIMES RE-MEASURING IT. The
first fixture wrapped the controls in .action-bar when every rule keys
off .page-action-buttons. The second dropped the `btn` class two
selectors require. The third wrapped each control in a span a child
combinator cannot see through. All three produced plausible numbers.
The fourth attempt used the renderer that already existed, and the
answer changed completely.

SO THIS ROUND CHANGES NO APPLICATION CODE. Setting a height would have
moved 265 buttons by one pixel and converged nothing. What was missing
was never a rule - it was anything CHECKING that the uniformity holds.
It is true today by accident. test_bar_height.py makes it true on
purpose.

base's standards block, section 3.6, says controls must not be pinned
to a fixed height, because Bootstrap does that and shaves the
descenders off the value. test_control_height enforces that for
.form-control. Had D-1 gone ahead it would have pinned a height on 265
buttons - outside the letter of that suite, and squarely inside its
reason.

WHAT IS NOT UNIFORM, and is recorded rather than swept: 78 controls in
cards or loose on pages, across 11 heights between 28 and 52px. Those
sit in one-off contexts where a page may have had a reason, so they
want a page-by-page look rather than one number. Section 5 pins the
count so the set cannot grow unnoticed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_barheight'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_bar_height.py'
ME = 'apply_bar_height.py'
CHECK = False


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    if not os.path.isfile(SUITE):
        raise SystemExit('D-1: %s is not on disk - the round IS the suite'
                         % SUITE)

    n_reg = 0
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_radius_token.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('D-1: the $suites anchor is not in %s exactly '
                             'once - D-12 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_radius_token.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    # NO alv_rounds ENTRY and NO alv_tree.CONVERTED ENTRY. ROUNDS is the
    # order as_left_by walks to find what a round left behind, and this
    # round leaves no application file behind. CONVERTED is the register
    # of suites that walk the template tree; this one does not walk at
    # all - it borrows test_tap_target's corpus, which is already on
    # that register under that suite's name. D-2 had to join CONVERTED
    # because it DID walk; the two rounds differ there on purpose.

    if not n_reg:
        print('D-1  already registered')
        return 0

    print('')
    print('D-1  %d registry file(s) resolved' % n_reg)
    print('D-1  no application file changed - the bar already has one')
    print('D-1  height, 35px on all 265 controls. What was missing was')
    print('D-1  anything checking that it stays that way.')
    print('D-1  applied' if CHECK else 'D-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
