# -*- coding: utf-8 -*-
"""apply_colour_census.py - 30 Oct 2026.

RELEASE 41 - THE COLOUR-LITERAL CENSUS GETS AN OWNER. Registers
test_colour_census.py on the push gate and in alv_tree.CONVERTED (it walks
every template root), and moves CONVERTED_N with it. No application file
changes, so nothing is added to alv_rounds.ROUNDS (the test_bar_height
precedent); the three registers are backed up to .bak_colourcensus.

Idempotent.
"""
import os
import re
import sys

SUFFIX = '.bak_colourcensus'
ME = 'test_colour_census.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
WD = 'test_waiting_down.py'


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def fit(text, lit):
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def swap(text, old, new, where):
    o, n = fit(text, old), fit(text, new)
    if text.count(o) != 1:
        raise SystemExit('REFUSED: %s: the anchor appears %d time(s), '
                         'expected exactly 1' % (where, text.count(o)))
    return text.replace(o, n)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    pq, pt, pw = (os.path.join(root, x) for x in (PS1, TREE, WD))
    if "'%s'" % ME in read(pq):
        print('colour census already registered.')
        return 0
    if not os.path.isfile(os.path.join(root, ME)):
        raise SystemExit('REFUSED: %s is missing - copy it in first.' % ME)
    out = {}
    out[pq] = swap(read(pq), """    'test_celebration_help.py'
)""", """    'test_celebration_help.py',
    # 30 Oct 2026 - the colour-literal census: no template gains a hex colour.
    'test_colour_census.py'
)""", PS1)
    out[pt] = swap(read(pt), """    'test_celebration_help.py',
]""", """    'test_celebration_help.py',
    # 30 Oct 2026 - the colour-literal census walks every root.
    'test_colour_census.py',
]""", TREE)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        raise SystemExit('REFUSED: %s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # 30 Oct 2026 - the colour-literal '
                   'census   # (was %s)' % (int(n.group(1)) + 1, n.group(1)),
                   WD)
    for p, t in sorted(out.items()):
        if not os.path.exists(p + SUFFIX):
            write(p + SUFFIX, read(p))
        write(p, t)
    print('colour census registered - %d file(s) written, backed up to %s'
          % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main())
