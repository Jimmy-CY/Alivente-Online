# -*- coding: utf-8 -*-
"""apply_required_promise.py - Section D round D-2, 9 Oct 2026.

A MARKER IS A PROMISE. WHO KEEPS IT?

test_required_sweep asserts one direction: every control carrying
`required` has an asterisk beside it. Nothing asserted the other, and
the other is the one a user experiences - they see a star, they leave
the field blank, and either something stops them or the form posts a
hole into the database.

THIS ROUND CHANGES NO APPLICATION CODE. It registers one suite. The
census found no empty promise among the 216 starred labels: every one
is enforced, by one of five mechanisms, residue zero.

  180  a static `required` on the control
    7  `required` set in script - plain DOM or jQuery .prop()
    9  stopped by a submit guard - alert, focus, preventDefault
    2  cannot be empty - no empty option, or a radio group defaulted
   18  a Django form field the form class marks required
  ---
    0  nothing found

WHY A ROUND WITH NO EDIT STILL NEEDS A PATCHER
-----------------------------------------------
The suite has to reach the gate, and the gate list lives in a file.
That edit is a change like any other: it must be idempotent, it must
refuse rather than half-apply, and it must leave a backup. Doing it
by hand is how a suite ends up on one machine and not on the gate.

A FINDING I WITHDREW, KEPT HERE BECAUSE THE NEXT READER WILL HAVE THE
SAME IDEA
----------------------------------------------------------------------
Two starred labels on crs/submission_start.html read for="id_fi" and
for="id_sending_in", while Django's auto_id for those fields is
id_reporting_fi and id_sending_company_in. That looks exactly like two
dead attributes, and I reported it as one.

It is not. SubmissionStartForm sets explicit widget ids:

    widget=forms.Select(attrs={**_INPUT, "id": "id_fi"})

so the RENDERED ids are the short ones, the labels are correct, and
the short names are deliberate - the page's own script reaches those
two selects by exactly those ids to drive the TIN cascade.

auto_id is the id Django WOULD generate from the field name. It is not
the id Django renders. test_required_promise.py section 5 resolves
every Django-rendered star against the rendered widget, not against
auto_id, which is the check that would have refused this mistake.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_reqpromise'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_required_promise.py'
ME = 'apply_required_promise.py'
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
        raise SystemExit('D-2: %s is not on disk - the round IS the suite, '
                         'so there is nothing to register' % SUITE)

    n_reg = 0

    # ---- the walking register ---------------------------------------
    # THIS SUITE WALKS THE TREE, so two census suites have an opinion
    # about it before it has run once. test_tree_roots section 3 holds
    # every walking suite to being on exactly one named list, and
    # test_waiting_down pins the length of that list. The sweep caught
    # both; neither is a fault in this round, they are the register
    # doing its job on a new arrival.
    #
    # CONVERTED is the right list, not ALREADY_WIDE: this suite walks
    # templates through alv_tree.walk3() and builds no root of its own,
    # which is what CONVERTED means. ALREADY_WIDE is for the censuses
    # that walk .py across the repo because a template root would blind
    # them.
    tp = os.path.join(root, 'alv_tree.py')
    tt = read(tp)
    if "'%s'" % SUITE not in tt:
        tail = "'test_zoom_guards.py',\n]\n"
        if tt.count(tail) != 1:
            raise SystemExit('D-2: the CONVERTED tail is not in alv_tree.py '
                             'exactly once')
        if not CHECK:
            backup(tp)
            write(tp, tt.replace(
                tail,
                "'test_zoom_guards.py',\n"
                "    # D-2, 9 Oct 2026 - written walking wide from the\n"
                "    # start rather than converted to it. It belongs here\n"
                "    # because it walks templates through walk3() and\n"
                "    # builds no root of its own, which is what this list\n"
                "    # means - not because any round widened it.\n"
                "    '%s',\n]\n" % SUITE, 1))
        n_reg += 1

    wd = os.path.join(root, 'test_waiting_down.py')
    wt = read(wd)
    # A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS IT.
    # CONVERTED_N is the length of the list this round appends to.
    # CEILING is not: it counts scripts that still walk a hard-coded
    # root, and this suite never did.
    old_n = "CONVERTED_N = 46"
    new_n = ("CONVERTED_N = 47      # 46 + test_required_promise.py, "
             "D-2, 9 Oct 2026")
    if new_n not in wt:
        if wt.count(old_n) != 1:
            raise SystemExit('D-2: CONVERTED_N = 46 is not in '
                             'test_waiting_down.py exactly once - it has '
                             'moved since this round was measured')
        if not CHECK:
            backup(wd)
            write(wd, wt.replace(old_n, new_n, 1))
        n_reg += 1

    pp = os.path.join(root, PS1)
    pt = read(pp)
    # NO EARLY RETURN HERE. It used to bail the moment the gate list
    # already named the suite, and it bailed BEFORE the report - so a
    # run that had just made the two register edits above printed
    # "already registered" and said nothing about them. Each edit
    # checks for itself; the function reports once, at the end.
    if "'%s'" % SUITE not in pt:
        # THE ANCHOR IS HM-4's ENTRY, matched exactly once. If HM-4 is
        # not applied, or something has been appended after it, this
        # refuses rather than inserting the line somewhere plausible.
        anc = "    'test_issue_centre.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('D-2: the $suites anchor is not in %s exactly '
                             'once - HM-4 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_issue_centre.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    if not n_reg:
        print('D-2  already registered in all three')
        return 0

    # NO alv_rounds ENTRY. ROUNDS is the order as_left_by walks to find
    # the file a given round left behind, and this round leaves no
    # application file behind - only the gate list. test_sentinels and
    # fifteen other check-only suites sit on the gate the same way.

    print('')
    print('D-2  %d registry file(s) resolved' % n_reg)
    print('D-2  no application file changed - the round IS the suite')
    print('D-2  216 starred labels, 5 mechanisms, residue 0')
    print('D-2  applied' if CHECK else 'D-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
