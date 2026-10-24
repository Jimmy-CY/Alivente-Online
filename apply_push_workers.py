# -*- coding: utf-8 -*-
"""apply_push_workers.py - round WK-1, 23 Oct 2026.

THE PUSH SCRIPT CANNOT BE TOLD HOW MANY WORKERS TO USE, AND THAT HAS
NOW COST THREE PUSHES.

alv_run.py has had --workers since GT-2 and defaults to 6. The push
script builds its argument list from exactly two switches:

    $runArgs = @((Join-Path $root 'alv_run.py'))
    if ($Force)  { $runArgs += '--force' }
    if ($Resume) { $runArgs += '--resume' }

So the only way to sweep at 3 is to run alv_run.py by hand first and
then push - which works, and which Demetri has now had to do twice.

WHAT KEEPS HAPPENING. rc=3221227274 is 0xC0000374, the Windows heap
corruption code, raised under pool contention rather than by anything
in the tree. It has hit test_msg_base.py and test_pick_filter.py on
23 October alone, and both passed when re-run alone - which is the
pool telling the truth about itself. A pool failure CANCELS the rest
of the sweep, so each one costs a whole run.

WHY NOT JUST ADD THEM TO CONTENDED. alv_run.CONTENDED pins a named
suite to the serial phase, and it holds the two print suites. Adding
every suite that has ever died in a pool treats a machine-shaped
problem one suite at a time: the number that is wrong is 6, on this
laptop, and the list would keep growing without ever saying so.

WHY NOT LOWER THE DEFAULT. 6 is right on a machine that can take it,
and alv_run is also run by hand where 6 is what somebody wants. The
default is a sensible guess; what was missing is the ability to
disagree with it at the point where it matters.

SO: -Workers, passed straight through, and ZERO MEANS DO NOT PASS IT
AT ALL - so a push that says nothing behaves exactly as it does
today. That is the whole of the round.

Idempotent. Every file backed up to .bak_pushworkers.
"""
import os
import re
import sys

SUFFIX = '.bak_pushworkers'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WK-1, 23 Oct 2026'
CHECK = False

CREATES = ()

P_WAS = """    [switch]$Resume,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT."""

P_NOW = """    [switch]$Resume,
    # WK-1, 23 Oct 2026 - HOW MANY SUITES RUN AT ONCE.
    #
    # alv_run.py has had --workers since GT-2 and defaults to 6. This
    # script could not pass it, so the only way to sweep at 3 was to
    # run alv_run.py by hand and then push - which Demetri had to do
    # twice on 23 October after rc=3221227274 (0xC0000374, Windows
    # heap corruption under pool contention) killed a sweep at suite
    # 371 and again at 370. Both suites passed when re-run alone.
    #
    # ZERO MEANS SAY NOTHING. The argument is only added when it is
    # asked for, so a push that does not mention workers behaves
    # exactly as every push before this round did.
    [int]$Workers = 0,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT."""

R_WAS = """if ($Force)  { $runArgs += '--force' }
if ($Resume) { $runArgs += '--resume' }"""

R_NOW = """if ($Force)  { $runArgs += '--force' }
if ($Resume) { $runArgs += '--resume' }
# WK-1, 23 Oct 2026. Only when asked - see the parameter.
if ($Workers -gt 0) { $runArgs += @('--workers', "$Workers") }"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('WK-1 REFUSED: %s' % msg)


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

    pp = os.path.join(root, PS1)
    p = read(pp)
    if MARK in p:
        print('WK-1  already applied - the push script can be told how '
              'many workers to use.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T                                   # noqa: F401

    # alv_run MUST ALREADY TAKE IT. A switch the receiver does not
    # understand is a switch that fails at the far end.
    runner = read(os.path.join(root, 'alv_run.py'))
    if "'--workers'" not in runner and '"--workers"' not in runner:
        refuse('alv_run.py does not accept --workers, so passing it '
               'would fail at the far end.')

    p = swap(p, P_WAS, P_NOW, '%s (the parameter)' % PS1)
    p = swap(p, R_WAS, R_NOW, '%s (the argument list)' % PS1)

    # ---- REGISTRATION
    p = swap(p, """    'test_one_list.py'
)""", """    'test_one_list.py',
    # WK-1, 23 Oct 2026 - the push script can be told how many
    # suites to run at once.
    'test_push_workers.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'Push-PendingChanges.ps1'; Text = 'ZERO MEANS SAY NOTHING'; What = 'WK-1: the sweep can be told how many workers to use, and a push that does not mention them behaves exactly as before - 6 is right on a machine that can take it and wrong on one that cannot, and rc=0xC0000374 killed two sweeps on 23 October saying so' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # CF-2, 23 Oct 2026 - one requirements file, not four.
    'test_one_list.py',
]""", """    # CF-2, 23 Oct 2026 - one requirements file, not four.
    'test_one_list.py',
    # WK-1, 23 Oct 2026 - the sweep can be told its own width.
    'test_push_workers.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_onelist',
]""", """    '.bak_onelist',
    # WK-1, 23 Oct 2026 - the sweep can be told its own width.
    '.bak_pushworkers',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # WK-1, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    g = out[pp]

    # THE GATES BELOW ASK WHERE THE TEXT LANDED, NOT WHETHER IT
    # EXISTS.
    #
    # check_gates raised this round for a gate whose pattern matched
    # its own P_NOW, and it was right to: a gate that searches for a
    # literal the round just wrote can only report that the swap ran,
    # which once() already refused to let fail. So each one below is
    # a question the inserted text cannot answer by itself - where it
    # sits relative to text this round did NOT write.

    # THE PARAMETER IS INSIDE THE param() BLOCK. A bad anchor could
    # put a well-formed declaration in a comment two thousand lines
    # down and PowerShell would never see it.
    i_param = g.find('param(')
    i_close = g.find('\n)', i_param)
    i_w = g.find('[int]$Workers = 0,')
    if i_w < 0:
        refuse('%s: $Workers is not declared as [int] defaulting to 0. '
               'The default is what makes this round invisible to every '
               'push that does not use it.' % PS1)
    if not (0 <= i_param < i_w < i_close):
        refuse('%s: the $Workers declaration is not inside param() - '
               'param at %d, declaration at %d, block ends at %d. A '
               'parameter outside the block is a comment.'
               % (PS1, i_param, i_w, i_close))

    # AND IT IS ONLY PASSED WHEN ASKED FOR.
    m = re.search(r'if \(\$Workers -gt 0\) \{ \$runArgs \+= '
                  r'@\(\'--workers\', "\$Workers"\) \}', g)
    if not m:
        refuse('%s: the argument is not added under a greater-than-zero '
               'guard. Passing --workers 0 to alv_run would ask for a '
               'pool of no workers.' % PS1)

    # THE GUARD COMES AFTER $runArgs EXISTS AND BEFORE python IS CALLED.
    i_args = g.find("$runArgs = @((Join-Path $root 'alv_run.py'))")
    i_call = g.find('& python @runArgs')
    if not (0 <= i_args < m.start() < i_call):
        refuse('%s: the workers line is not between the argument list '
               'being built and python being called (args %d, line %d, '
               'call %d)' % (PS1, i_args, m.start(), i_call))

    # AND NOTHING ELSE ABOUT THE CALL MOVED.
    if g.count('& python @runArgs') != 1:
        refuse('%s: there is more than one call to the runner' % PS1)
    if "$runArgs += '--resume'" not in g or "$runArgs += '--force'" not in g:
        refuse('%s: --force or --resume stopped being passed' % PS1)

    if CHECK:
        print('WK-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the push script learns -Workers; zero passes '
              'nothing, so an unchanged push is unchanged')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('WK-1  applied - the push script can be told how many suites '
          'to run at once.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      -Workers 3 on a machine that cannot take 6; say '
          'nothing and nothing changes.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
