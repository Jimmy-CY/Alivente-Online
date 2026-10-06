# -*- coding: utf-8 -*-
"""alv_sweep.py - run the gate's suites here, the way the push runs them.

SERIALLY AND ONE AT A TIME, which is not a performance choice. The E4
flake has a named writer: test_css_order.py section 7 plants a selector
collision into a real template on disk, runs its check, then restores it.
Any other suite reading that template inside that window sees the plant.
The push runs serially so the gate cannot hit it, and so does this.

It reads $suites out of Push-PendingChanges.ps1 rather than keeping its
own list, because a second list is a second thing to forget.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')


def suites():
    src = open(PS1, encoding='utf-8', errors='replace').read()
    m = re.search(r'\$suites = @\((.*?)\n\)', src, re.S)
    if not m:
        raise SystemExit('alv_sweep: could not find $suites in %s' % PS1)
    return re.findall(r"'([^']+\.py)'", m.group(1))


def main(argv):
    only = [a for a in argv if not a.startswith('-')]
    names = suites()
    if only:
        names = [n for n in names if any(o in n for o in only)]
    bad = []
    for i, n in enumerate(names, 1):
        p = os.path.join(ROOT, n)
        if not os.path.exists(p):
            bad.append((n, 'MISSING'))
            print('[%d/%d] %-44s MISSING' % (i, len(names), n))
            continue
        r = subprocess.run([sys.executable, p], cwd=ROOT,
                           capture_output=True, text=True, timeout=900)
        tail = (r.stdout or '').strip().splitlines()
        verdict = ''
        for line in reversed(tail[-6:]):
            if 'passed' in line and 'failed' in line:
                verdict = line.strip()
                break
        if r.returncode != 0:
            bad.append((n, verdict or 'rc=%d' % r.returncode))
            print('[%d/%d] %-44s FAIL  %s' % (i, len(names), n,
                                              verdict or 'rc=%d' % r.returncode))
        else:
            print('[%d/%d] %-44s ok    %s' % (i, len(names), n, verdict))
        sys.stdout.flush()
    print('\n%d suite(s), %d failing' % (len(names), len(bad)))
    for n, why in bad:
        print('   %-44s %s' % (n, why))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
