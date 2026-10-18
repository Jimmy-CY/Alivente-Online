# -*- coding: utf-8 -*-
"""apply_preflight.py - round PG-1, 18 Oct 2026.  E24.

THE GATE READS THE SUBJECT LINE AND ASKS THE TREE ABOUT IT.

Twice in two days a push went through naming rounds the tree did not
contain, and both times everything downstream was honestly green.

    16 OCT  three rounds delivered as a zip; the zip landed in a folder
            inside the repo and was never extracted. One file changed -
            the archive. The gate ran the OLD suite list, because the
            gate is itself a file those rounds would have changed, so
            every claim it knew about still held. The sentinels could
            not help for the same reason: their rows live in that file.

    17 OCT  six rounds delivered by writing the applied files straight
            into the repo - and their .bak_ files stayed in the sandbox.
            as_left_by() answers "as the round left it" by reading the
            next round's backup, AND WITH NO BACKUP IT READS THE FILE
            LIVE. Every historical comparison became a file compared
            with itself, and the gate failed at suite 15 of 366 on a
            control that was right.

Two mistakes, one shape: the tree did not contain what the subject said
it contained, and nothing read both.

WHAT THE ROUND ADDS: one call, near the top of the gate, to
alv_preflight.py - which resolves every round named in the subject
against alv_rounds.py's own comments and counts its backups on disk.

NOTHING IS HAND-KEPT. The map from AR-1 to .bak_autoretry is already in
the register, written as a comment above the entry, and the backups are
counted from the disk in one walk.

WHY PYTHON. GT-2, 17 Oct: there is no PowerShell here, so anything
written into the .ps1 ships untested, and a broken gate does not cost
an hour - it costs the ability to push. The PowerShell side is five
lines and a call; everything that can be got wrong lives in the file
test_preflight.py can drive.

WHERE IT SITS: before the sentinel table, so a subject naming a round
the tree does not have costs seconds rather than the whole sweep. GT-1
moved the missing-subject refusal to the top for the same reason, and
E-10 paid the full price of having it at the bottom.

WHAT THE MEASUREMENT CHANGED. The round was going to require a sentinel
naming each round as its proof of being applied. The first real subject
it ran against refused CP-1 - which correctly carries no sentinel,
because it changes one suite and asserts its own shape. And a sentinel
proves nothing the register does not: a round whose files never arrived
has no entry in alv_rounds.py either, which is the 16 Oct case and is
already a refusal. So the refusal rests on the register and the
backups, and the sentinel is printed as a note.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_preflight'
MOD = 'alv_preflight.py'
ME = 'test_preflight.py'
PATCHER = 'apply_preflight.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

# ------------------------------------------------------------ the call
CALL_WAS = """# ------------------------------------------------------- 1. is it applied?"""
CALL_NOW = """# ------------------------------------------ 0b. does the tree know it?
#
# PG-1, 18 Oct 2026 - E24. Twice in two days a push went through with a
# subject naming rounds the tree did not contain: an unextracted zip on
# 16 Oct, and six rounds delivered without their .bak_ files on 17 Oct.
# Both looked green all the way down, because everything downstream
# reads the tree in front of it and that tree was self-consistent.
#
# alv_preflight.py reads the SUBJECT and asks two things of each round
# it names: does alv_rounds.py have an entry for it, and is there a
# backup on disk. Both answers are already in the tree; neither is
# hand-kept here.
#
# HERE, not at the bottom. A wrong subject should cost seconds. GT-1
# moved the missing-subject refusal up for the same reason.
#
# IN PYTHON, not in this file. There is no PowerShell in the sandbox,
# so anything written here ships untested - GT-2's lesson, and the
# reason this is five lines and a call.
if ($Apply -and $Message) {
    & python (Join-Path $root 'alv_preflight.py') $Message 2>&1 |
        ForEach-Object { Say $_ }
    if ($LASTEXITCODE -ne 0) {
        Bad 'the subject names a round this tree does not have'
        if (-not $Force) {
            Say ''
            Say '  Stopping.  Nothing has been staged.'
            exit 1
        }
    }
}

# ------------------------------------------------------- 1. is it applied?"""

TREE_WAS = """    # NW-1, 17 Oct 2026 - E20. 87 browser suites fetched Bootstrap,
    # Font Awesome and jQuery from three CDNs on every page they
    # opened. Wide from birth.
    'test_offline.py',
]"""
TREE_NOW = """    # NW-1, 17 Oct 2026 - E20. 87 browser suites fetched Bootstrap,
    # Font Awesome and jQuery from three CDNs on every page they
    # opened. Wide from birth.
    'test_offline.py',
    # PG-1, 18 Oct 2026 - E24. The gate reads the subject line and asks
    # the tree whether it has the rounds it names. Wide from birth.
    'test_preflight.py',
]"""

REG_WAS = """    # NW-1, 17 Oct 2026 - E20. 87 browser suites were fetching from
    # three CDNs on every page they opened.
    '.bak_netguard',
]"""
REG_NOW = """    # NW-1, 17 Oct 2026 - E20. 87 browser suites were fetching from
    # three CDNs on every page they opened.
    '.bak_netguard',
    # PG-1, 18 Oct 2026 - E24. A subject naming a round the tree does
    # not have is refused before the sweep rather than after it.
    '.bak_preflight',
]"""

SUITE_WAS = """    # NW-1, 17 Oct 2026 - E20, the network guard and its 87 suites.
    'test_offline.py'
)"""
SUITE_NOW = """    # NW-1, 17 Oct 2026 - E20, the network guard and its 87 suites.
    'test_offline.py',
    # PG-1, 18 Oct 2026 - E24, the subject read against the tree.
    'test_preflight.py'
)"""

SENT_WAS = (
    "    @{ File = 'alv_offline.py'; Text = 'LOOPBACK'; "
    "What = 'NW-1: the network guard spares a suite own loopback "
    "server' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- PG-1, 18 Oct 2026
    @{ File = 'alv_preflight.py'; Text = 'as_left_by'; What = 'PG-1: the pre-flight says what missing backups cost' },"""


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
    raise SystemExit('PG-1 REFUSED: %s' % msg)


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

    p1 = os.path.join(root, PS1)
    t = read(p1)

    # ---------------------------------------------------------------- 0
    if 'alv_preflight.py' in t:
        print('PG-1  already applied - the gate reads the subject.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE TWO FILES THAT ARE THE ROUND. A patcher that wires a call to
    # a module nobody shipped turns a guard into a broken gate, which
    # is worse than no guard.
    for f in (MOD, ME):
        if not os.path.isfile(os.path.join(root, f)):
            refuse('%s is not on disk - it is the round, not a side '
                   'effect of it' % f)
    # AND THE MODULE MUST ANSWER. Run it against this very tree before
    # wiring it in: a subject naming a round the register holds and the
    # disk has backups for must come back clean.
    sys.path.insert(0, root)
    import alv_preflight
    reg = alv_preflight.register(root)
    if len(reg) < 50:
        refuse('%s parsed only %d round name(s) out of %s - the register '
               'comment shape has moved' % (MOD, len(reg), ROUNDS))
    bad, _ = alv_preflight.check('GT-2 - a round this tree certainly has',
                                 root=root)
    if bad:
        refuse('%s refuses a round this tree does have: %s'
               % (MOD, bad[0][:120]))
    bad, _ = alv_preflight.check('ZQ-9 - a round no tree has', root=root)
    if not bad:
        refuse('%s accepts a round that does not exist - it cannot fail'
               % MOD)

    t = swap(t, CALL_WAS, CALL_NOW, '%s (the call)' % PS1)
    t = swap(t, SUITE_WAS, SUITE_NOW, '%s ($suites)' % PS1)
    t = swap(t, SENT_WAS, SENT_NOW, '%s (the sentinel)' % PS1)
    out[p1] = t

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, WD)
    s = read(p)
    m = re.search(r'CONVERTED_N = (\d+)', s)
    if not m:
        refuse('%s has no CONVERTED_N' % WD)
    was = int(m.group(1))
    out[p] = s.replace('CONVERTED_N = %d' % was,
                       'CONVERTED_N = %d   # PG-1, 18 Oct 2026 - this '
                       'round own suite   # (was %d)' % (was + 1, was), 1)

    # ---------------------------------------------------------------- 4
    for k, v in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(v)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))

    if CHECK:
        print('PG-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('PG-1 applied.')
    print('   the gate reads the subject and asks the tree about it')
    print('   a round with no register entry is refused - the 16 Oct shape')
    print('   a round with no backup on disk is refused - the 17 Oct one')
    print('   and it runs before the sentinels, not after the sweep')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
