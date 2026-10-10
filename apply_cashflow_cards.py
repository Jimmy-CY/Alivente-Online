# -*- coding: utf-8 -*-
"""apply_cashflow_cards.py - Section D round D-5, 10 Oct 2026.

THE CASHFLOW CARD IS NOT A DIALECT OF BASE'S STAT TILE. IT IS A
DIFFERENT COMPONENT, AND IT KEEPS ITS OWN RULES.

D-5 was recorded as: cashflow_forecast built nine private card
selectors beside base's, using neither .alv-stats nor .alv-card -
adopt base's stat tiles as Tenant Payment Days did, or record why not.

Measured and rendered both ways, the premise does not hold.

    the page's card   a PERIOD HEADING over THREE labelled figures,
                      Revenue, Expenses and Net, with Net ruled off
                      as the resolution of the other two
    base's .alv-stat  ONE value under ONE uppercase label, no band

So "adopt base's stat tiles" is not a lift. Three cards become NINE
tiles, the period name has to be repeated in every label, and the
relationship between the three figures - that Net is the other two
resolved - dissolves into a grid of equals. He saw both renders at
both widths and kept the card.

TENANT PAYMENT DAYS IS NOT THE PRECEDENT IT LOOKED LIKE. Its twelve
.alv-stat tiles are twelve INDEPENDENT numbers, which is exactly what
base's tile is for. That page never had a heading to lose.

SO THIS ROUND CHANGES NO APPLICATION CODE. What was missing was never
a conversion - it was anything recording WHY the page differs, so that
the next person to tidy the system does not harmonise away a header
band that is carrying a period name.

WHAT IS RECORDED AND NOT FIXED
------------------------------
physical_invoice_edit.html carries ONE summary-card and one rule of
its own - a copy of this page's component on a page with no three-line
structure to justify it. That one probably SHOULD be base's tile. It
is named in the suite and left for a round that renders it first,
because it is one element and a visible change, and this round was
agreed as a check.

D-3 closed the same way and for a related reason: base's own note
defers the compact table "until a second page asked", and exactly one
has. A component with one caller is not a component yet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_cfcards'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_cashflow_cards.py'
ME = 'apply_cashflow_cards.py'
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
        raise SystemExit('D-5: %s is not on disk - the round IS the suite'
                         % SUITE)

    n_reg = 0
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_crs_print.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('D-5: the $suites anchor is not in %s exactly '
                             'once - PQ-1 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_crs_print.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    # NO alv_rounds ENTRY - this round leaves no application file behind,
    # so there is nothing for as_left_by to walk to. NO alv_tree.CONVERTED
    # entry either: the suite reads two named templates and does not walk
    # the tree, unlike D-2's and PQ-1's, which both had to join.

    if not n_reg:
        print('D-5  already registered')
        return 0

    # SAY WHAT WAS DONE, NOT WHAT WAS CONSIDERED. --check writes nothing,
    # so it may not report the round as applied. D-1, B-7 and PQ-1 all
    # print 'applied' under --check; that is wrong and it is theirs to fix.
    print('')
    print('D-5  %d registry file(s) %s'
          % (n_reg, 'would be resolved' if CHECK else 'resolved'))
    print('D-5  no application file changed - the cashflow card is a')
    print('D-5  different component from base stat tile, not a dialect of')
    print('D-5  it. Three cards would become nine tiles and Net would stop')
    print('D-5  reading as the resolution of the other two.')
    print('D-5  check only - nothing written' if CHECK else 'D-5  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
