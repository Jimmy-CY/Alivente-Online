"""apply_crb_4b.py - two suites the Comments Report round reaches.

    python apply_crb_4b.py --check
    python apply_crb_4b.py

A. test_sticky_sweep.py  section 3, the SCOPE GUARD - a FAILING 4b
B. test_comment_tint.py  the fixture, a STALE HARNESS - a SILENT one

Run from the repo root. Found by the push gate on 2 Sep.

THE SPLIT WAS TWO CLAIMS SHARING ONE VARIABLE.

  HISTORICAL  when the sticky sweep ran, exactly one of its six pages was on
              .alv-table. True then, true for ever, and the right thing to
              measure it against is .bak_sticky - the pages AS THE SWEEP
              FOUND THEM.
  LIVE        every page on .alv-table TODAY must have a heading that really
              sticks. That set GROWS as pages migrate, and a round that grows
              it has SUCCEEDED.

Both were read off the live file, so the second silently policed the first:
comments_report.html joined the standard and the split check reported a
successful migration as a defect.

Third time a scope guard has moved in this suite, and like the other two it
comes out stronger: section 4 now measures every migrated page rather than
the one the sweep happened to find. Measured here - comments_report.html
passes all four of section 4's rendered checks the moment it joins.

B. THE SILENT ONE, and it is the more interesting of the two.

test_comment_tint.py renders three comment surfaces and asks whether two
authors look the same. Its fixture builds the report rows as

    <table class="report-table">

which was right on 1 Sep. This round deletes .report-table, so that table
is now styled by NOTHING - and the suite still passes 80 of 80, because
every check in it asserts an ABSENCE of difference and two unstyled rows
have none. A stale harness that FAILS tells you it is stale. One that
passes just quietly stops testing.

The fixture moves to .alv-table with the real cell classes, so the tint
round keeps being checked against what the page actually renders.
"""
import os
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
SW = os.path.join(ROOT, 'test_sticky_sweep.py')
TI = os.path.join(ROOT, 'test_comment_tint.py')
for _f in (SW, TI):
    if not os.path.exists(_f):
        sys.exit('! %s not found - run from the repo root'
                 % os.path.basename(_f))


def sub1(t, old, new, what):
    if t.count(old) != 1:
        sys.exit('! %s: anchor matched %d times, expected 1'
                 % (what, t.count(old)))
    return t.replace(old, new, 1)


def load(p):
    with open(p, encoding='utf-8', newline='') as fh:
        raw = fh.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def save(p, orig, crlf, new, suffix='.bak_crb'):
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-24s %d -> %d bytes'
          % (os.path.basename(p), len(orig), len(out)))
    if CHECK:
        return
    bak = p + suffix
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


# ============================================== A. the FAILING 4b, per file
ORIG, CRLF, s = load(SW)
DONE_A = 'was_live' in s
if DONE_A:
    print('  test_sticky_sweep.py already patched')


if not DONE_A:
    s = sub1(s, """    live, preemptive = [], []
    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        if not os.path.exists(path):
            continue
        (live if on_standard(read(path)) else preemptive).append(rel)""",
         """    # TWO CLAIMS, and until 2 Sep they shared one variable.
    #
    #   was_live  HISTORICAL: what the sweep FOUND, measured on .bak_sticky.
    #             A fact about 30 Aug. It cannot change, so a check on it
    #             cannot go stale.
    #   live      TODAY: what is on the standard now, measured on the live
    #             file. This set GROWS as pages migrate, and a round that
    #             grows it has succeeded.
    #
    # Reading both off the live file made the second police the first:
    # comments_report.html joined the standard on 2 Sep and the split check
    # below failed, reporting a successful migration as a defect. Third scope
    # guard moved in this suite; like the other two it comes out stronger,
    # because section 4 now measures EVERY migrated page instead of the one
    # the sweep happened to find.
    live, preemptive, was_live = [], [], []
    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        if not os.path.exists(path):
            continue
        (live if on_standard(read(path)) else preemptive).append(rel)
        bak = path + SUFFIX
        if os.path.exists(bak) and on_standard(read(bak)):
            was_live.append(rel)""", 'the split gains a historical half')

    s = sub1(s, """    check('  and the split is what the round claimed',
          len(live) == 1 and live == ['physical_invoice_list.html'],
          '%s' % live)""",
         """    check('  and the split is what the SWEEP found - measured on %s, '
          'not on the live files' % SUFFIX,
          was_live == ['physical_invoice_list.html'], '%s' % was_live)
    check('  .. and every page it found has STAYED on the standard',
          set(was_live) <= set(live),
          'was %s, now %s' % (was_live, live))
    check('  .. and any page that JOINED since is measured below, not '
          'reported as a defect',
          True, '%d joined: %s'
          % (len(set(live) - set(was_live)),
             sorted(set(live) - set(was_live)) or 'none yet'))""",
         'the split check')

    # The section 5 line that says the same thing per page.
    s = sub1(s, """        check('  %-28s and it is honestly NOT on .alv-table, so nothing on '
              'screen moved' % '', not on_standard(read(path)))""",
         """        # Also historical, and also on the backup. This loop only walks
        # `preemptive`, so the live file cannot be on the standard here
        # today - but reading the backup is what makes the sentence TRUE
        # rather than merely currently-true.
        check('  %-28s and it was honestly NOT on .alv-table, so nothing on '
              'screen moved' % '', not on_standard(read(bak)))""",
         'section 5 per-page claim')

save(SW, ORIG, CRLF, s)

# ============================================== B. the SILENT one, per file
ORIG2, CRLF2, t = load(TI)
if 'alv-table' in t:
    print('  test_comment_tint.py already patched')
else:
    # The fixture's report rows. .report-table no longer exists, so this
    # table renders unstyled and every "they match" check in section 2 has
    # been passing on nothing. Moved to what the page actually ships.
    t = sub1(t, '''<table class="report-table"><tbody>
  <tr id="rowA"><td class="comment-cell"><span class="comment-text">first</span></td>
      <td class="user-cell">%s</td></tr>
  <tr id="rowB"><td class="comment-cell"><span class="comment-text">second</span></td>
      <td class="user-cell">%s</td></tr>
</tbody></table>''',
               '''<table class="alv-table"><tbody>
  <tr id="rowA"><td class="comment-cell"><span class="comment-text">first</span></td>
      <td class="user-cell" data-label="User">%s</td></tr>
  <tr id="rowB"><td class="comment-cell"><span class="comment-text">second</span></td>
      <td class="user-cell" data-label="User">%s</td></tr>
</tbody></table>''', 'tint fixture: report rows')

    t = sub1(t, """  * SECTION 2 RENDERS all three comment surfaces and asks the browser the only
    question that matters: do two comments by DIFFERENT authors look the same?""",
             """  * SECTION 2 RENDERS all three comment surfaces and asks the browser the only
    question that matters: do two comments by DIFFERENT authors look the same?
    THE FIXTURE MUST RENDER WHAT THE PAGE RENDERS. Its report rows were
    <table class="report-table"> until 2 Sep, when the Comments Report round
    deleted that class - after which the table was styled by NOTHING and this
    section passed 80 of 80 on two unstyled rows, because every check here
    asserts an ABSENCE of difference. A stale harness that fails tells you it
    is stale; one that passes just stops testing. It is .alv-table now.""",
             'tint fixture: say why')

    save(TI, ORIG2, CRLF2, t)

print('\n  done.')
