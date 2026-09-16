"""apply_gate_wire_two.py - the rest of the repo's suites join the gate, and
   only the ones that can prove it today.

    python apply_gate_wire_two.py --check     run them all, write nothing
    python apply_gate_wire_two.py             run them all, wire the green

Run from the repo root.

WHY THIS ONE RUNS THE SUITES ITSELF

  The 9 Sep round wired thirteen suites on and found two had been failing
  for a day and a half with nothing saying so. The lesson recorded then was
  "a suite that is not on the gate enforces nothing". The lesson this round
  adds is the other half:

      A SUITE THAT CANNOT PASS TODAY CANNOT HONESTLY BE WIRED ON TODAY.

  Listing one that fails does not enforce a standard - it stops every push
  until somebody deletes the line, which is how a gate gets a reputation
  and then gets bypassed with -Force. So this patcher RUNS each candidate
  first, wires the ones that exit clean, and names the ones that do not
  without touching the list for them. Their repair is the next round, with
  the failure text in hand.

  That also means no separate survey step. A loop that reports, followed by
  a patcher that acts on what the loop said, is two chances for the two to
  disagree - and this project has already shipped a round where the survey
  and the tree disagreed because the survey ran somewhere else.

WHAT IT DOES NOT WIRE, AND WHY

  test_parser.py is not a suite. It is a smoke-test for a CRS Excel parser
  with a hardcoded path into somebody's Downloads folder, and it ASSERTS
  NOTHING - it prints what it found and exits 0 whatever that was. On the
  gate it would be a check that cannot fail, which this project has now
  shipped four of. It is renamed out of the test_ namespace instead.

  test_map_tiles.py is superseded by the map-provider round. It asserts the
  OpenStreetMap tile URL is a literal in map_view, that the tile layer's
  only options are attribution and maxZoom, and that the attribution
  credits OpenStreetMap - all true of the page that round replaced. Its
  map_view regression half (the markers, the centre, where Leaflet is
  loaded from) is still worth having, so this round neither wires it nor
  deletes it: rewriting it down to the claims that survive is a decision,
  and decisions do not belong inside a sweep.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_gatetwo'
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
TIMEOUT = 600

# The seventeen. Each entry is (suite, the one line that says why it is worth
# running on every push). The note is not decoration - the list is read by
# whoever is deciding whether a red suite is worth stopping for.
CANDIDATES = [
    ('test_ageing_scale.py',
     'The ageing bands, on the cells and on the legend that explains them.'),
    ('test_alv_stat.py',
     "base's stat tile, and the rule that a verdict colours the FIGURE and\n"
     '    # not the box behind it.'),
    ('test_banner_pages.py',
     'The page banner. Reads a .bak_banner snapshot and exits 1 loudly if it\n'
     '    # is missing, which is the right behaviour and not all of them do it.'),
    ('test_comments_report.py',
     'The comments report, down to the 34px icon button base owns.'),
    ('test_fi_seg.py',
     'The Financial Indicators segmented control. Section 2 RENDERS the four\n'
     '    # controls, because "they look the same" is not a static claim.'),
    ('test_finance_headings.py',
     'Every Financials page heads itself the way base says.'),
    ('test_fsr_palette.py',
     'The Friday status report colours. Its control renders the OLD file and\n'
     '    # requires the old answer, so a green result cannot be vacuous.'),
    ('test_grade_tables.py',
     'The grade scale, and the detail tables that read it.'),
    ('test_ia_drill.py',
     'The Issues Analysis drill-down: a modal inside a modal, measured.'),
    ('test_ind_modal.py',
     'The indicator modal.'),
    ('test_invoice_verification.py',
     'Invoice verification. Pure value tests - what 95.2 against 95.20 does.'),
    ('test_issues_table.py',
     'The Issues table, narrow and wide, against the markup it replaced.'),
    ('test_matrix_range.py',
     'The year-on-year matrix range. Every year in it is INJECTED as\n'
     '    # today_year, so the suite owns the clock and cannot age.'),
    ('test_oi_migration.py',
     'The outstanding-invoices migration.'),
    ('test_pl_drill.py',
     'The P&L drill-down.'),
    ('test_print_media.py',
     'What the print stylesheet does, as opposed to what it says.'),
    ('test_resolved_report.py',
     'The resolved-issues report.'),
]

# Not wired. See the docstring; both are reported every run so neither is
# quietly forgotten.
RENAME = ('test_parser.py', 'probe_crs_parser.py')
SUPERSEDED = ('test_map_tiles.py', 'superseded by test_map_provider.py - '
              'retire or rewrite, do not wire')

ANCHOR = "    'test_map_provider.py'\n)\n"


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def run(suite):
    """Run one suite and report (ok, summary line).

    A TIMEOUT IS A FAILURE, and a crash is a failure. Both block a push
    exactly as hard as a failing check - that lesson cost a push on 16 Sep
    and is not going to be re-learned by a patcher that treats a hang as
    'no news'.
    """
    try:
        r = subprocess.run([sys.executable, suite], cwd=ROOT, timeout=TIMEOUT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.TimeoutExpired:
        return False, 'TIMED OUT after %ds' % TIMEOUT
    out = r.stdout.decode('utf-8', 'replace')
    line = ''
    for ln in out.split('\n'):
        if 'passed' in ln and 'failed' in ln:
            line = ln.strip()
    if not line:
        tail = [x for x in out.strip().split('\n') if x.strip()]
        line = tail[-1].strip()[:70] if tail else '(no output)'
    return r.returncode == 0, line


def main():
    check_only = '--check' in sys.argv
    if not os.path.exists(PS1):
        print('! Push-PendingChanges.ps1 not found - run from the repo root')
        sys.exit(1)

    text, nl, raw = read(PS1)

    print('  Running %d candidate suite(s). This takes a few minutes - most '
          'of them\n  drive a browser.\n' % len(CANDIDATES))

    green, red, already = [], [], []
    for suite, note in CANDIDATES:
        if not os.path.exists(os.path.join(ROOT, suite)):
            red.append((suite, 'not on disk'))
            print('  MISS  %-30s not on disk' % suite)
            continue
        if "'" + suite + "'" in text:
            already.append(suite)
            print('  ---   %-30s already on the gate' % suite)
            continue
        ok, line = run(suite)
        print('  %s  %-30s %s' % ('OK  ' if ok else 'FAIL', suite, line))
        (green if ok else red).append((suite, line, note) if ok
                                      else (suite, line))

    print('')
    if not green:
        print('  Nothing to wire: %d already on the gate, %d not passing.'
              % (len(already), len(red)))
    else:
        if text.count(ANCHOR) != 1:
            print('  FAIL  the suite-list anchor matches %d times, not once. '
                  'NOTHING written.' % text.count(ANCHOR))
            sys.exit(1)
        block = ["    'test_map_provider.py',",
                 '',
                 '    # ------------------------------------------------------------------',
                 '    # WIRED ON 16 Sep 2026, by a patcher that RAN each of them first.',
                 '    # A suite that cannot pass today cannot honestly be wired on today:',
                 '    # listing a red one does not enforce a standard, it stops every push',
                 '    # until somebody deletes the line.',
                 '    # ------------------------------------------------------------------']
        for suite, line, note in green:
            block.append('    # ' + note)
            block.append("    '%s'," % suite)
        block[-1] = block[-1].rstrip(',')
        block.append(')')
        new = text.replace(ANCHOR, '\n'.join(block) + '\n')

        # Self-check, all of it about this file.
        bad = []
        for suite, _line, _note in green:
            if new.count("'" + suite + "'") != 1:
                bad.append('%s would be listed %d times'
                           % (suite, new.count("'" + suite + "'")))
        after = new[new.rindex("'" + green[-1][0] + "'"):]
        if after.split('\n')[1].strip() != ')':
            bad.append('the last entry would not close the array')
        if new.count('$suites = @(') != 1:
            bad.append('the array opener moved')
        if len(new) <= len(text):
            bad.append('the file did not grow')
        if bad:
            print('')
            for b in bad:
                print('  FAIL  %s' % b)
            print('\nFAIL  self-check failed. NOTHING has been written.')
            sys.exit(1)

        if not check_only:
            bak = PS1 + SUFFIX
            if not os.path.exists(bak):
                with open(bak, 'wb') as f:
                    f.write(raw)
            write(PS1, new, nl)
        print('  %s %d suite(s) %s the gate'
              % ('WOULD wire' if check_only else 'OK    wired',
                 len(green), 'onto' if check_only else 'onto'))

    # ---- the two that are not candidates, reported every run.
    src = os.path.join(ROOT, RENAME[0])
    dst = os.path.join(ROOT, RENAME[1])
    if os.path.exists(src) and not os.path.exists(dst):
        if check_only:
            print('  WOULD rename %s -> %s (it asserts nothing)' % RENAME)
        else:
            os.rename(src, dst)
            print('  OK    renamed %s -> %s (it asserts nothing, so on the '
                  'gate it\n        would be a check that cannot fail)'
                  % RENAME)
    elif os.path.exists(dst):
        print('  ---   %s already renamed to %s' % RENAME)

    print('  NOTE  %s: %s' % SUPERSEDED)

    if red:
        print('')
        print('  %d suite(s) were NOT wired, because they do not pass today:'
              % len(red))
        for suite, line in red:
            print('     %-30s %s' % (suite, line))
        print('')
        print('  That is the next round, and the failure text above is the')
        print('  starting point. None of them is on the gate, so none of them')
        print('  blocks a push.')

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')


if __name__ == '__main__':
    main()
