"""Show-GateAudit.py - run EVERY suite to the end and list what fails.

    python Show-GateAudit.py              every test_*.py in the repo root
    python Show-GateAudit.py --full       plus each failure's own output
    python Show-GateAudit.py test_foo.py  just these

Run from the repo root.

WHY THIS EXISTS

Push-PendingChanges.ps1 stops at the FIRST failing suite, which is right for
a push - a failing gate should not stage anything - but it means a queue of
problems is discovered one per push, a day apart. Three in a row have now
been the same species:

    generate_lease_agreement  a rule that would have made a live button grey
    customer_form             a named example that a later round made stale
    generate_lease_agreement  a heading whose words moved down one line

None was caused by the round being pushed. Each was an EARLIER round that
shipped and left some other suite's snapshot out of date, hidden behind the
suite that was failing ahead of it.

This runs all of them, to the end, and prints the whole queue at once.

WHAT THE THREE OUTCOMES MEAN

    PASS      exit 0.
    FAILS     exit non-zero and it printed a summary - a real disagreement
              between a suite and the tree. These are the ones to read.
    CRASHED   it never got to a summary: a missing file, a missing backup,
              or an exception. A CRASH BLOCKS A PUSH EXACTLY AS HARD AS A
              FAILURE and says far less about why, so it is listed
              separately rather than counted as a failure.

It writes nothing, changes nothing, and its own exit code is always 0 - it
is a report, not a gate.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import glob
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
ME = os.path.basename(__file__)
try:
    TTY = sys.stdout.isatty()
except Exception:
    TTY = False


def suites(argv):
    named = [a for a in argv[1:] if a.endswith('.py')]
    if named:
        return sorted(named)
    return sorted(os.path.basename(p) for p in
                  glob.glob(os.path.join(ROOT, 'test_*.py')))


def summary_of(out):
    """The line a suite prints at the end. Two shapes are in use."""
    m = None
    for line in out.split('\n'):
        if re.search(r'\b\d+ passed(,| )', line):
            m = line.strip()
        elif re.match(r'\s*All \d+ checks passed', line):
            m = line.strip()
    return m


def named_failures(out):
    """The `  - name` lines a suite prints after its summary.

    The first draft split on twenty '=' characters, which is a SUBSTRING of
    the 72-character rule every suite prints - so it cut in the middle of
    the footer and found nothing. Anchor on the summary line instead: the
    names always follow it.
    """
    lines = out.replace('\r\n', '\n').split('\n')
    last = -1
    for i, ln in enumerate(lines):
        if re.search(r'\b\d+ passed(,| )', ln):
            last = i
    if last < 0:
        return []
    out2 = []
    for ln in lines[last + 1:]:
        if re.match(r'\s+-\s+\S', ln):
            out2.append(ln.strip()[1:].strip())
    return out2


def first_reason(out):
    """For a crash: the line that says what was missing."""
    for ln in out.split('\n'):
        s = ln.strip()
        if s.startswith('!'):
            return s.lstrip('! ')
    m = re.findall(r'^\w*(?:Error|Exception).*$', out, re.M)
    if m:
        return m[-1].strip()
    last = [ln.strip() for ln in out.split('\n') if ln.strip()]
    return last[-1][:90] if last else '(no output)'


def main():
    full = '--full' in sys.argv
    names = [n for n in suites(sys.argv) if n != ME]
    if not names:
        print('! no test_*.py found - run from the repo root')
        return

    print('')
    print('=' * 74)
    print(' GATE AUDIT - every suite, to the end')
    print('=' * 74)
    print('')
    print('  %d suite(s). The push gate stops at the first failure; this'
          % len(names))
    print('  does not, so the whole queue shows up at once.')
    print('')

    passed, failed, crashed, outputs = [], [], [], {}
    t0 = time.time()
    for i, n in enumerate(names, 1):
        # Only redraw in place on a real console. Piped to a file, the
        # carriage returns smear one long line across the report.
        if TTY:
            sys.stdout.write('\r  running %3d/%-3d %-46s'
                             % (i, len(names), n[:46]))
            sys.stdout.flush()
        try:
            r = subprocess.run([sys.executable, n], cwd=ROOT,
                               capture_output=True, timeout=900)
            out = (r.stdout + r.stderr).decode('utf-8', 'replace')
            code = r.returncode
        except subprocess.TimeoutExpired:
            out, code = '(timed out after 900s)', 124
        except Exception as e:
            out, code = 'could not start: %s' % e, 125
        outputs[n] = out
        if code == 0:
            passed.append(n)
        elif summary_of(out):
            failed.append(n)
        else:
            crashed.append(n)
    if TTY:
        sys.stdout.write('\r' + ' ' * 78 + '\r')

    print('  %d passed, %d FAILED, %d CRASHED   (%.0fs)'
          % (len(passed), len(failed), len(crashed), time.time() - t0))

    if failed:
        print('')
        print('-' * 74)
        print(' FAILED - a suite and the tree disagree. Read these.')
        print('-' * 74)
        for n in failed:
            print('')
            print('  %s' % n)
            print('      %s' % (summary_of(outputs[n]) or ''))
            for f in named_failures(outputs[n]):
                print('      - %s' % f[:88])

    if crashed:
        print('')
        print('-' * 74)
        print(' CRASHED - never reached a summary. Usually a missing file or')
        print(' backup, which on this machine may be real or may be setup.')
        print('-' * 74)
        for n in crashed:
            print('  %-38s %s' % (n, first_reason(outputs[n])[:52]))

    if full:
        for n in failed + crashed:
            print('')
            print('=' * 74)
            print(' %s' % n)
            print('=' * 74)
            print(outputs[n])

    print('')
    print('=' * 74)
    print('  This is a REPORT. It writes nothing and always exits 0.')
    print('  Run it again with --full to see each failure\'s own output.')
    print('=' * 74)


if __name__ == '__main__':
    main()
