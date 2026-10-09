# -*- coding: utf-8 -*-
"""apply_issue_dates.py - Section IS round IS-1, 9 Oct 2026.

A RE-OPENED ISSUE KEEPS ITS OLD CLOSURE DATE, AND SOMETHING NOW READS IT.

`fsr_commit_status_change` sets issues_resolution_date when a status
becomes Resolved and has no `else`, so moving an issue back off
Resolved leaves the old date in place. The row is then open by status
and closed by date at the same time.

THIS IS NOT THEORETICAL ANY MORE. The live census on 9 Oct 2026:

    status            real date   none/1900
    'Resolved'              144           0
    'Unresolved'              1           9

One row. It has been open by status and dated as closed since whenever
it was re-opened, and HM-2 shipped a panel two days ago that reads the
date. `resolved_in()` in portfolio_insights counts any row whose resolution
date falls in the window WITHOUT asking its status, so such a row can
be counted as a closure and as open at the same time.

THE ONE LIVE ROW WAS NOT DOING THAT YET. It is issues_id 125, "Parking
Bay", prop 5: logged 2026-02-05, resolved 2026-03-16, re-opened since.
On 9 Oct 2026 the three windows are (2026-07-09, 2026-10-09],
(2026-04-09, 2026-07-09] and (2025-07-09, 2025-10-09], and 2026-03-16
is in none of them - so every figure on the Home page was correct. I
said earlier that closed3 was probably overstated by one; that was a
guess and the arithmetic says otherwise.

The round still stands: the row is wrong, the next re-opened issue
will be a recent one, and a defect that is harmless only because of
where a date happens to fall is not a defect anyone should rely on.

HM-2's own suite prints this as a caveat after every run - "NOT PROVED
HERE: that the resolution date is TRUE" - and its fixture contains no
non-Resolved row carrying a real date, which is exactly why 88 checks
never found it. IS-1 adds that row to the fixture; it is the control.

WHAT THIS ROUND DOES, AND DELIBERATELY DOES NOT
-----------------------------------------------
TAKEN - three parts, each small:

  1. THE CAUSE. `else: issue.issues_resolution_date = ISSUE_NO_DATE`
     in fsr_commit_status_change. Forward-only. No migration, no model
     change, and it is the ONLY path in the tree that writes
     issues_status - fsr_edit_commit says so in its own docstring and
     sets its three fields by hand to avoid touching this one.

  2. THE READ. `_resolved_on()` gains a status check, so a date only
     dates a resolution when the row IS Resolved. His words, and the
     census prints them: "the STATUS is the state - it is what the app
     sets - and the date is only ever the WHEN of one that is already
     Resolved." Part 1 stops it recurring; part 2 makes the panel
     right whatever the data says, which matters because 154 rows of
     history were written before part 1 existed.

  3. THE ONE ROW. issue_date_repair.py, delivered with the round but
     NOT on the gate: it finds rows that are open by status and dated
     by field, prints them, and writes the sentinel only with --fix.
     It is read-only by default and it refuses to touch more rows than
     it was told to expect.

NOT TAKEN, at his instruction - "the module works, I don't want to
break anything":

  * issues.py:627 compares issues_resolution_date to the sentinel with
    NO None guard, so a NULL there raises TypeError. Nothing writes
    NULL today (the add form posts 1900-01-01 in a hidden input) and
    the live census finds none, so it is latent. IT IS ALSO THE
    CONCRETE REASON NOT TO MIGRATE THE SENTINEL AWAY - dropping it for
    NULL breaks that line. Logged, not touched.
  * the hidden 1900-01-01 input in fsr_add.html. Ugly, harmless.
  * the add form can create a Resolved row with the sentinel date,
    violating his rule that every Resolved issue has a date. The
    census finds zero, so nobody does it. Logged.

NOT PROVED HERE: that the one live row's ORIGINAL closure date was
wrong. It may well have been a real resolution that was later
re-opened for good reason. The repair script writes the sentinel
because the row is open NOW and an open row has no resolution date -
it does not claim the history was false, and it prints the date it
clears so the information is not lost silently.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_issuedates'
MARK = 'IS-1, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_issue_dates.py'
ME = 'apply_issue_dates.py'
REPAIR = 'issue_date_check.py'
CHECK = False

VIEWS = os.path.join('pages', 'views', 'issues.py')
SVC = os.path.join('pages', 'services', 'portfolio_insights.py')
PANEL_SUITE = 'test_issue_panel.py'


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


# ---- 1. THE CAUSE ---------------------------------------------------
VIEW_EDITS = (
    ("""        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        issue.save()""",
     """        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        else:
            # IS-1, 9 Oct 2026 - AND CLEAR IT ON THE WAY BACK OUT.
            # Without this an issue moved off Resolved keeps the date it
            # was closed on, so the row is open by status and closed by
            # date at once. One live row was in that state on 9 Oct
            # 2026: issues_id 125, "Parking Bay", logged 2026-02-05,
            # resolved 2026-03-16, re-opened and still carrying it.
            #
            # IT WAS NOT DISTORTING ANY FIGURE ON THE DAY IT WAS FOUND.
            # 2026-03-16 falls outside all three windows the panel
            # reports - last 3 months, the 3 before, the same 3 a year
            # ago - so closed3, closed_prev3 and closed_yoy3 were all
            # correct. Measured, not assumed; an earlier note here
            # claimed the opposite and was wrong. The row would have
            # been double-counted the moment it aged into a window, or
            # if the re-opened issue had been a recent one.
            #
            # The sentinel, not None: issues.py:627 compares this field
            # to date(1900, 1, 1) with no None guard and would raise on
            # a NULL. 1900-01-01 is what "no date" is spelled as here.
            issue.issues_resolution_date = date(1900, 1, 1)
        issue.save()""",
     'the missing else in fsr_commit_status_change'),
)

# ---- 2. THE READ ----------------------------------------------------
SVC_EDITS = (
    ('''def _resolved_on(row):
    """The date an issue was resolved, or None - sentinel included."""
    d = row.issues_resolution_date
    return d if (d and d != ISSUE_NO_DATE) else None''',
     '''def _resolved_on(row):
    """The date an issue was resolved, or None.

    THE STATUS IS THE STATE; THE DATE IS ONLY THE WHEN. A row that is
    not Resolved has no resolution date however its date column reads -
    IS-1, 9 Oct 2026, after the live census found one row open by
    status and carrying a real date. Before this, resolved_in() counted
    that row as a closure while open_rows counted it as open, so one
    issue appeared on both sides of the same three-month window and the
    Executive brief said so in prose.

    HM-2 closed the sentinel half of this (1900-01-01 is no date) and
    left the status half open, because its fixture had no such row.
    IS-1 adds one.
    """
    if _issue_status(row) != ISSUE_RESOLVED:
        return None
    d = row.issues_resolution_date
    return d if (d and d != ISSUE_NO_DATE) else None''',
     'the status gate on _resolved_on'),
)


# ---- test_issue_panel's ONE claim that stops being true -------------
# ITS FIXTURE IS NOT TOUCHED. Adding a row to it would move total,
# open, logged3, net3, the median and the ageing line, and re-pointing
# six counts to prove one rule is how a small round becomes a big one.
# The claim that changes is a single assertion, and the counter-case
# is made with a stand-in object that reads the two attributes
# _resolved_on actually looks at - no row, no fixture, no counts.
PANEL_EDITS = (
    ("""    real = [i for i in Issue.objects.all()
            if i.issues_resolution_date not in (None, D(1900, 1, 1))]
    ok(all(P._resolved_on(i) is not None for i in real),
       '  while a real date comes back as itself')""",
     """    real = [i for i in Issue.objects.all()
            if i.issues_resolution_date not in (None, D(1900, 1, 1))]
    ok(all(P._resolved_on(i) is not None for i in real
           if (i.issues_status or '').strip() == 'Resolved'),
       '  while a real date on a RESOLVED row comes back as itself')

    # IS-1, 9 Oct 2026 - AND THE STATUS HALF, which this suite could
    # not see. Every row in the fixture carrying a real date is
    # Resolved, so the assertion above passed for want of a
    # counter-example rather than because the rule held. The live
    # census then found one: status Unresolved, a real resolution
    # date, counted open AND counted as a closure in the same window.
    # A stand-in object reads the two attributes _resolved_on looks
    # at, so the fixture and its counts stay exactly as HM-2 left them.
    class _ReopenedRow(object):
        issues_status = 'Unresolved'
        issues_resolution_date = D(2026, 9, 10)

    ok(P._resolved_on(_ReopenedRow()) is None,
       '  and a row that is NOT Resolved has no resolution date, '
       'whatever its date column says - the status is the state, the '
       'date is only the WHEN of one already Resolved')""",
     'the resolved-row claim'),

    # AND THE CAVEAT THIS ROUND DISCHARGES. HM-2 printed, after every
    # run, that re-opening an issue does not clear its date and that
    # the panel would count that closure. IS-1 makes both sentences
    # false. A round that fixes a caveat owns the caveat, exactly as a
    # round that changes a number owns every number that counts it -
    # and a suite still warning about something that was fixed two
    # rounds ago teaches people to stop reading its warnings.
    ("""print('  NOT PROVED HERE: that the resolution date is TRUE. Re-opening a')
print('  resolved issue does not clear it - fsr_commit_status_change sets')
print('  the date when the status becomes Resolved and never unsets it -')
print('  so a re-opened issue still reads as closed on its old date, and')
print('  this panel would count that closure. Measured on the live data')
print('  on 9 Oct and left alone deliberately: the module works, and a')
print('  migration to fix it would make issues.py:626 raise on NULL.')
print('  Logged, not taken.')""",
     """print('  TAKEN, 9 Oct 2026, by IS-1. This suite used to warn that')
print('  re-opening an issue did not clear its resolution date and')
print('  that the panel would count that closure. Both are fixed:')
print('  fsr_commit_status_change now writes the sentinel on the way')
print('  out of Resolved, and _resolved_on asks the status first, so')
print('  a row that is not Resolved has no resolution date whatever')
print('  its date column says. The live census found one row in the')
print('  old state - id 125, Parking Bay - and it was corrected by')
print('  hand. issue_date_check.py re-asks the question any day.')
print('')
print('  NOT PROVED HERE: that issues.py:627 is safe. It compares the')
print('  resolution date to the sentinel with no None guard and would')
print('  raise on a NULL. Nothing writes NULL today, so it is latent -')
print('  and it is the concrete reason the sentinel stays.')""",
     'the discharged caveat'),
)


REPAIR_SRC = '''# -*- coding: utf-8 -*-
"""issue_date_check.py - IS-1, 9 Oct 2026. READ-ONLY. It never writes.

Finds issues that are OPEN BY STATUS and DATED BY FIELD - the state a
re-opened issue was left in before IS-1 put an `else` in
fsr_commit_status_change, so the row is open and closed at once.

WHY YOU CANNOT FIND THESE IN THE APP. comments_report.html renders the
resolution date only when `data.status === 'Resolved'`, so the field is
hidden on exactly the rows where it is wrong. The module has always
looked right from the front end for that reason.

IT DOES NOT WRITE, BY DESIGN. The one live row on 9 Oct 2026 was
corrected by hand in the database. This script is what says whether
that worked, and what says so again on any day after.

    railway ssh python issue_date_check.py

Exit code 1 if it finds any, so it can sit in a check later if wanted.
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from datetime import date                                  # noqa: E402

from pages.models import issues                            # noqa: E402

SENTINEL = date(1900, 1, 1)
RESOLVED = 'Resolved'


def main():
    bad, resolved_undated = [], []
    for i in issues.objects.all():
        st = (i.issues_status or '').strip()
        d = i.issues_resolution_date
        dated = d is not None and d != SENTINEL
        if st != RESOLVED and dated:
            bad.append(i)
        if st == RESOLVED and not dated:
            resolved_undated.append(i)

    print('')
    print('=' * 70)
    print('  OPEN BY STATUS, DATED BY FIELD - %d row(s)' % len(bad))
    print('=' * 70)
    if bad:
        print('  %-7s %-13s %-12s %-12s %s'
              % ('id', 'status', 'logged', 'resolution', 'heading'))
        print('  ' + '-' * 66)
        for i in bad:
            print('  %-7s %-13s %-12s %-12s %s'
                  % (i.issues_id, (i.issues_status or '').strip(),
                     i.issues_date_logged, i.issues_resolution_date,
                     (i.issues_heading or '')[:28]))
        print('')
        print('  Each of these is counted OPEN by status and counted as a')
        print('  CLOSURE by date in the same window. Set the resolution')
        print('  date to 1900-01-01 - the sentinel - not to NULL:')
        print('  issues.py:627 compares this field without a None guard.')
    else:
        print('  None. Every row that is not Resolved reads as undated.')

    print('')
    print('  RESOLVED WITH NO DATE - %d row(s)' % len(resolved_undated))
    print('  ' + '-' * 66)
    if resolved_undated:
        for i in resolved_undated:
            print('  %-7s %-12s %s'
                  % (i.issues_id, i.issues_date_logged,
                     (i.issues_heading or '')[:40]))
        print('')
        print('  His rule: every Resolved issue must have a resolution')
        print('  date. These break it. The add form can create one by')
        print('  posting status Resolved with the hidden 1900-01-01.')
    else:
        print('  None - every Resolved row carries a real date.')

    print('')
    return 1 if (bad or resolved_undated) else 0


if __name__ == '__main__':
    sys.exit(main())
'''


def eol_of(text):
    """The line ending this file actually uses.

    pages/views/issues.py is CRLF and the other two files this round
    edits are LF. An anchor written with \n matched the views file
    ZERO times, and the gate said so rather than doing part of the
    round - but an anchor that cannot match the file it was written
    for is still the same mistake in a new costume: THE ANCHOR HOLDS
    WHAT THE FILE HOLDS, line endings included.
    """
    crlf = text.count('\r\n')
    return '\r\n' if crlf and crlf >= (text.count('\n') - crlf) else '\n'


def apply_edits(path, edits, what):
    txt = read(path)
    if MARK in txt:
        return 0
    eol = eol_of(txt)
    out = txt
    for old, new, name in edits:
        old = old.replace('\n', eol)
        new = new.replace('\n', eol)
        if out.count(old) != 1:
            raise SystemExit(
                'IS-1: %s - the anchor for %s is in the file %d time(s), '
                'not once (line ending %r). The anchor holds what the FILE '
                'holds, and this one no longer does'
                % (what, name, out.count(old), eol))
        out = out.replace(old, new, 1)
    if not CHECK:
        backup(path)
        write(path, out)
    return len(edits)


def register():
    root = os.path.dirname(os.path.abspath(__file__))
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_spice',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('IS-1: RC-2 must be applied and must still be '
                             'the last entry in ROUNDS')
        ins = ("    '.bak_spice',\n"
               "    # IS-1, 9 Oct 2026 - a re-opened issue stops carrying\n"
               "    # the date it was closed on.\n"
               "    '%s',\n]\n" % SUFFIX)
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail, ins, 1))
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        # THE LAST ENTRY CARRIES NO TRAILING COMMA. An anchor written
        # with one matched zero times and the gate refused - the same
        # lesson as the CRLF above, one line further down the file.
        anc = "    'test_issue_panel.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit("IS-1: the $suites anchor is not in %s exactly "
                             "once - it has moved" % PS1)
        ins = "    'test_issue_panel.py',\n    '%s'\n)" % SUITE
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(anc, ins, 1))
    return 2


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # THE ROUND THIS ONE FOLLOWS, tested where it landed.
    if "'.bak_spice'" not in read(os.path.join(root, 'alv_rounds.py')):
        raise SystemExit('IS-1: RC-2 is not registered - this round appends '
                         'after it in ROUNDS')
    svc = read(SVC)
    if 'ISSUE_NO_DATE' not in svc or '_issue_status' not in svc:
        raise SystemExit('IS-1: HM-2 is not applied - this round gates the '
                         '_resolved_on() that round introduced')

    done = MARK in read(VIEWS) and MARK in svc
    if done:
        print('IS-1  already applied')
        return 0

    nv = apply_edits(VIEWS, VIEW_EDITS, VIEWS)
    ns = apply_edits(SVC, SVC_EDITS, SVC)
    np_ = apply_edits(PANEL_SUITE, PANEL_EDITS, PANEL_SUITE)

    # the read-only check ships with the round
    rp = os.path.join(root, REPAIR)
    if not os.path.exists(rp) and not CHECK:
        write(rp, REPAIR_SRC)
    nreg = register()

    # ---- PROVE THE CHANGE, DO NOT ASSERT IT --------------------------
    # A patcher verifies, then writes - and this one can verify after,
    # because the rule is a pure function of two attributes.
    # THE VERIFICATION USES THE SAME NORMALISER AS THE WRITE. It did
    # not, at first: it rebuilt the planned text with \n anchors
    # against a CRLF file, the replace did nothing, and the check then
    # failed on text the round had never actually produced. A gate
    # reading a tree the round did not plan is a gate reading nothing.
    def planned(path, edits):
        src = read(path)
        if MARK in src:
            return src
        eol = eol_of(src)
        for old, new, _n in edits:
            src = src.replace(old.replace('\n', eol),
                              new.replace('\n', eol), 1)
        return src

    after = planned(SVC, SVC_EDITS)
    if 'if _issue_status(row) != ISSUE_RESOLVED:' not in after:
        raise SystemExit('IS-1: the status gate is not in _resolved_on '
                         'after the edit')
    vafter = planned(VIEWS, VIEW_EDITS)
    body = vafter[vafter.index('def fsr_commit_status_change'):]
    body = body[:body.index('\n@login_required')]
    if body.count('issues_resolution_date') != 2:
        raise SystemExit('IS-1: fsr_commit_status_change should set the '
                         'resolution date on exactly two branches, found %d'
                         % body.count('issues_resolution_date'))
    if 'else:' not in body:
        raise SystemExit('IS-1: the else branch is not there')

    print('')
    print('IS-1  %d edit to the writer, %d to the reader, %d to HM-2 suite'
          % (nv, ns, np_))
    print('IS-1  fsr_commit_status_change is the ONLY writer of '
          'issues_status in')
    print('IS-1  the tree - fsr_edit_commit sets its three fields by hand '
          'to avoid it')
    print('IS-1  _resolved_on now asks the status first: the state is the '
          'status,')
    print('IS-1  the date is only the WHEN of one already Resolved')
    print('IS-1  %s shipped - READ-ONLY, it never writes' % REPAIR)
    print('IS-1  HM-2 fixture NOT touched - the counter-case is a '
          'stand-in object,')
    print('IS-1  so total/open/logged3/net3/median all stay as HM-2 '
          'measured them')
    print('IS-1  %d registry file(s) resolved' % nreg)
    print('IS-1  applied' if CHECK else 'IS-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
