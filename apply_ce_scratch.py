# -*- coding: utf-8 -*-
"""apply_ce_scratch.py - round CE-1, 20 Oct 2026.

A SUITE THAT WRITES INTO THE TREE IT IS BEING RUN AGAINST.

This stopped Demetri's push on the morning of the 20th, at 290 of 395,
with nothing staged:

    FileNotFoundError: ...\\Alivente-Online\\tmpzv3mfgnd.py
    test_code_only.py PASSED alone in 9.5s - the pool was the cause

TWO SUITES, ONE DIRECTORY.

    test_console_encoding   tempfile.mkstemp(suffix='.py', dir=ROOT)
    test_code_only          os.listdir(ROOT), everything ending .py

The first writes a throwaway script into the working tree, runs it as
a subprocess and deletes it. The second lists the tree and reads what
it found. Between the listing and the read, the file is gone.

THE WINDOW IS A FEW MILLISECONDS WIDE, which is why this has never
appeared before and why it will appear again. A pool failure cancels
the queue, so one unlucky interleaving costs a whole sweep.

THE HOUSE ALREADY FIXED THIS CLASS. apply_probe_location moved every
probe onto a private directory and wrote down why:

    "mkdtemp hands THIS PROCESS a directory whose name no other
     process knows, so two suites cannot collide however they are
     ordered, and nothing is written into the working tree at all."

test_console_encoding is the one probe that round did not reach,
because it is not a probe - it runs a script rather than rendering a
page, and nobody went looking for the pattern outside the set that
round was about.

dir=ROOT WAS NEVER NEEDED. The throwaway script is run as a separate
process and imports nothing from the repository - it is the console
encoding preamble and two prints. It could have lived anywhere; it
lived in the tree because that is where the author happened to be.

Idempotent. Every file backed up to .bak_cescratch.
"""
import os
import re
import sys

SUFFIX = '.bak_cescratch'
CE = 'test_console_encoding.py'
ME = 'test_ce_scratch.py'
PATCHER = 'apply_ce_scratch.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'CE-1, 20 Oct 2026'
CHECK = False
CREATES = ()

IMP_WAS = """import alv_tree
import tempfile"""
IMP_NOW = """import alv_tree
import atexit as _atexit
import shutil as _shutil
import tempfile

# A DIRECTORY NO OTHER PROCESS KNOWS - CE-1, 20 Oct 2026.
#
# The throwaway script below used to be written into the repository
# itself, with dir=ROOT. test_code_only lists the repository for
# *.py and reads every name it finds, so when the two ran together in
# the pool it listed a temporary file and then read a file that had
# already been deleted:
#
#     FileNotFoundError: ...\\Alivente-Online\\tmpzv3mfgnd.py
#
# That stopped a push at 290 of 395 with nothing staged. The window is
# a few milliseconds wide, which is why it took until the twentieth to
# appear and why it would have come back.
#
# THIS IS apply_probe_location's PATTERN, and its words: mkdtemp hands
# THIS PROCESS a directory whose name no other process knows, so two
# suites cannot collide however they are ordered, and nothing is
# written into the working tree at all. That round moved the probes;
# this one is the script-runner it did not reach.
SCRATCH = tempfile.mkdtemp(prefix='alv_conenc_')
_atexit.register(_shutil.rmtree, SCRATCH, True)"""

RUN_WAS = """    fd, path = tempfile.mkstemp(suffix='.py', dir=ROOT)"""
RUN_NOW = """    # NOT dir=ROOT - CE-1, 20 Oct 2026. The script is run as its own
    # process and imports nothing from this repository, so it never
    # needed to live in it.
    fd, path = tempfile.mkstemp(suffix='.py', dir=SCRATCH)"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('CE-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pce = os.path.join(root, CE)
    t = read(pce)

    if 'alv_conenc_' in t:
        print('CE-1  already applied - the probe writes outside the tree.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FAULT MUST BE THERE, and it must be the only one. A
    # second suite writing into the tree would not be fixed by this
    # round and should not be hidden by it.
    # THIS ROUND'S OWN FILES ARE NOT THE TREE. The walk below looks
    # for the pattern it is removing, and the patcher CONTAINS that
    # pattern - as the literal it is replacing. Counting itself made
    # it refuse with two writers where there is one.
    writers = []
    mine = (PATCHER, ME)
    for name in sorted(n for n in os.listdir(root)
                       if n.endswith('.py') and n not in mine):
        src = T.python_code_only(read(os.path.join(root, name)),
                                 payloads=True)
        if re.search(r'mkstemp\([^)]*dir\s*=\s*ROOT', src) or \
                re.search(r'mkdtemp\([^)]*dir\s*=\s*ROOT', src):
            writers.append(name)
    if CE not in writers:
        refuse('%s: it does not write into the tree, so this round has '
               'nothing to fix' % CE)
    if len(writers) > 1:
        refuse('more than one file writes a temporary into the tree, '
               'and this round repairs one: %s' % ', '.join(writers))

    t = swap(t, IMP_WAS, IMP_NOW, '%s (the scratch directory)' % CE)
    t = swap(t, RUN_WAS, RUN_NOW, '%s (where the script goes)' % CE)
    out[pce] = t

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_list_range.py'
)""", """    'test_list_range.py',
    # CE-1, 20 Oct 2026 - the console-encoding probe stops writing a
    # .py into the repository that test_code_only is reading.
    'test_ce_scratch.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "'sl_from': sl_from";""",
             """    @{ File = 'test_console_encoding.py'; Text = 'alv_conenc_'; What = 'CE-1: the console-encoding probe writes its throwaway script into a directory of its own - it used to write a .py into the repository, which test_code_only lists and reads, and one unlucky interleaving stopped a push at 290 of 395' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "'sl_from': sl_from";""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # SL-7, 20 Oct 2026 - the shopping list range follows the view,
    # decided in one place rather than spelled in the markup.
    'test_list_range.py',
]""", """    # SL-7, 20 Oct 2026 - the shopping list range follows the view,
    # decided in one place rather than spelled in the markup.
    'test_list_range.py',
    # CE-1, 20 Oct 2026 - a suite stops writing into the tree it is
    # being run against, which cost a whole sweep.
    'test_ce_scratch.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # SL-7, 20 Oct 2026 - the list covers what you are looking at.
    '.bak_listrange',
]""", """    # SL-7, 20 Oct 2026 - the list covers what you are looking at.
    '.bak_listrange',
    # CE-1, 20 Oct 2026 - the probe writes outside the tree.
    '.bak_cescratch',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # CE-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nce = T.python_code_only(out[pce], payloads=True)
    if re.search(r'mkstemp\([^)]*dir\s*=\s*ROOT', nce):
        refuse('%s: it still writes into the tree' % CE)
    if 'tempfile.mkdtemp(prefix=' not in nce:
        refuse('%s: there is no private directory to write into' % CE)
    # AND IT IS CLEANED UP. A mkdtemp per run, never removed, fills a
    # temp directory one sweep at a time.
    if '_atexit.register' not in nce:
        refuse('%s: the directory is never removed' % CE)
    # THE SUITE STILL RUNS THE SCRIPT. A round that fixed the race by
    # deleting the probe would pass everything above.
    if 'subprocess.run' not in nce:
        refuse('%s: the probe no longer runs anything' % CE)

    if CHECK:
        print('CE-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CE-1  applied - the probe writes outside the tree.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
