# -*- coding: utf-8 -*-
"""apply_gate_speed.py - round GT-2, 17 Oct 2026.

THE GATE'S LOOP MOVES WHERE IT CAN BE TESTED.

Demetri, 17 Oct: "We are waiting 90 minutes for you to develop some
small change and then to do your sweep. Then it takes 60 minutes to run
it through the gates on my laptop. If it fails, then that takes another
60 minutes."

The 60 minutes is 360 suites run ONE AT A TIME by a `foreach` loop
inside this PowerShell script. That loop is correct and has been for two
months. It cannot be IMPROVED from here: this sandbox has no PowerShell,
so every edit to it ships untested, and a broken gate does not cost an
hour - it costs the ability to push at all.

So the loop moves into alv_run.py, where it was run against all 360
suites before this round was written, and the PS1 keeps a call.

WHAT alv_run.py DOES THAT THE LOOP DID NOT

    PARALLEL, except where parallel is a lie. Fourteen suites plant a
    defect into a REAL file, read it, and put it back; run one beside a
    suite reading the same file and the second sees the plant. MEASURED,
    not assumed: test_icon_names passes alone and FAILS beside five
    others. Those fourteen run first, serially, in a quiet tree.

    RENDERS FIRST. E17. 254 of the 360 launch a browser, so a missing
    browser or an unopenable fixture shows at suite 10 rather than 350.

    --Resume. E17. A failure at 300 restarts at 300 - but only for
    suites that could not have been affected by what changed since. The
    rest re-run, and alv_impact decides which those are. A resume that
    skips a suite the fix broke is worse than no resume.

WHAT IT CHANGES ABOUT THE ANSWERS: NOTHING. 359 of 360 suites pass
through the runner, and the one that does not fails alone as well. It
decides ORDER and CONCURRENCY, not claims.

THREE BUGS IT TOOK TO GET THERE, all worth the comment they cost:

    The resume was keyed on MTIME. A planter restores a file by writing
    the original back - same bytes, new timestamp - so every resume
    decided the tree had moved. A timestamp is not a change; it is
    keyed on content now.

    ThreadPoolExecutor.map YIELDS IN LIST ORDER, so finished suites sat
    unreported behind a slow one and a killed run lost them. Three
    resume chunks in a row made no progress. as_completed, and the log
    is written as each suite lands.

    Python BLOCK-BUFFERS stdout through a pipe, so the gate would have
    shown nothing for minutes - which is what a progress counter exists
    to prevent.

THE POWERSHELL SIDE IS AS SMALL AS IT CAN BE: one loop out, one call in,
one switch added. Everything that can be got wrong lives in the file
that was tested.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_gatespeed'
RUNNER = 'alv_run.py'
ME = 'test_gate_speed.py'
PATCHER = 'apply_gate_speed.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 96, 97
ALIAS_WAS, ALIAS_NOW = 102, 103
ALIAS_P_WAS, ALIAS_S_WAS = 51, 51
ALIAS_P_NOW, ALIAS_S_NOW = 52, 51

# ----------------------------------------------------------- the param
PARAM_WAS = """    [string[]]$Checks = @()
)"""
PARAM_NOW = """    [string[]]$Checks = @(),
    # GT-2, 17 Oct 2026 - E17. A failure at suite 300 should restart at
    # 300, not at 1. alv_run.py decides what may be skipped: a suite is
    # only skipped when NOTHING IT COULD READ has changed since the run
    # that passed it, which alv_impact answers. Everything else re-runs.
    [switch]$Resume
)"""

# ------------------------------------------------------------ the loop
# AND THE PROSE ABOVE IT GOES TOO.
#
# The block below describes the loop in detail - how the width of the
# number is computed, why the variables carry a suite prefix, which
# variable name was already taken five hundred lines up. Every word of
# that is about code this round removes. A comment that gives a reason
# the tree no longer has is the drift that cost a round yesterday, so it
# leaves with what it documents.
#
# DEMETRI'S REQUEST SURVIVES, because that is a record of what was asked
# for and alv_run.py still honours it.
LOOP_WAS = """# A suite listed here but not on disk currently prints an amber line and
# carries on. That is the right behaviour for a repo where a suite may not
# have been written yet - but the COUNT of skips is the thing worth seeing,
# because "23 passed" reads identically whether 23 ran or 23 were skipped.
$skipped = @()
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
# the 203, it shows 1/203 and then name for the first one... This way I can
# monitor progress and manage my time better."
#
# THE TOTAL IS $suites.Count, NOT A NUMBER TYPED HERE. The list grows by a
# line every round - 197 three weeks ago, 203 today - and a hardcoded total
# would be wrong the first time somebody appends to it and would go on
# being wrong silently. The width is computed from the count too, so the
# numbers stay in a straight column whether there are 99 or 1,099.
#
# The three names carry a suite prefix because this script is 1,200 lines
# and $label already belongs to the manifest loop five hundred lines up.
$suiteNo = 0
$suiteWide = ('' + $suites.Count).Length
foreach ($t in $suites) {
    $suiteNo++
    $suiteLabel = ('[' + ('' + $suiteNo).PadLeft($suiteWide) + '/' + $suites.Count + ']')
    if (-not (Test-Path (Join-Path $root $t))) {
        Warn ($suiteLabel + ' ' + $t + ' not present - skipped')
        $skipped += $t
        continue
    }
    Say ''
    Say ('  == ' + $suiteLabel + ' ' + $t)
    & python $t 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        # THE NUMBER ON THE FAILURE LINE TOO. In a 203-suite run the failure
        # scrolls past the banner that said which suite was starting, and
        # "test_x FAILED" alone does not say how far in it was.
        Bad ($suiteLabel + ' ' + $t + ' FAILED')
        if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
    }
}

Say ''
if ($skipped.Count -gt 0) {
    Warn ('' + $skipped.Count + ' of ' + $suites.Count + ' suite(s) were not on disk and did not run:')
    foreach ($t in $skipped) { Warn ('     ' + $t) }
} else {
    Good ('all ' + $suites.Count + ' suite(s) ran')
}"""

LOOP_NOW = """# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
# the 203, it shows 1/203 and then name for the first one... This way I can
# monitor progress and manage my time better."
#
# Still true, and alv_run.py still does it - the numbering, the total taken
# from the list rather than typed, and the count of suites that were not on
# disk. What moved is where the loop lives.
#
# GT-2, 17 Oct 2026 - THE LOOP LIVES IN alv_run.py NOW.
#
# It ran one suite at a time, which is where most of the hour went. The
# replacement runs them in a pool, with the fourteen suites that plant
# into real files pinned to a serial phase first, and the browser suites
# before the rest so a bad environment shows early. It reads $suites out
# of THIS FILE, so the list above stays the only place it is kept.
#
# WHY IT IS PYTHON. There is no PowerShell in the sandbox these rounds
# are built in, so nothing written here can be run before it is
# delivered. alv_run.py was run against all 360 suites before this round
# existed: 359 pass through it, and the one that does not fails alone
# too. Everything that can be got wrong is in the file that was tested;
# what is left here is a call.
#
# The numbering, the skip report and the stop-on-failure all moved with
# the loop - see alv_run.py, which prints them in the same shape.
$runArgs = @((Join-Path $root 'alv_run.py'))
if ($Force)  { $runArgs += '--force' }
if ($Resume) { $runArgs += '--resume' }
& python @runArgs 2>&1 | ForEach-Object { Say $_ }
if ($LASTEXITCODE -ne 0) {
    Bad 'one or more suites FAILED - see the lines above'
    if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
} else {
    Good ('all ' + $suites.Count + ' suite(s) accounted for')
}"""

TREE_ANCHOR = """    'test_label_law.py',
]"""
TREE_NEW = """    'test_label_law.py',
    # GT-2, 17 Oct 2026 - the gate's suite loop moves into alv_run.py,
    # where it can be tested: parallel, planters serial, renders first,
    # and --Resume. Wide from birth.
    'test_gate_speed.py',
]"""

ROUNDS_ANCHOR = """    '.bak_labellaw',"""
ROUNDS_NEW = """    '.bak_labellaw',
    # GT-2, 17 Oct 2026 - one loop out of the PS1, one call in.
    '.bak_gatespeed',"""

SUITE_ANCHOR = """    'test_label_law.py'
)"""
SUITE_NEW = """    'test_label_law.py',
    'test_gate_speed.py'
)"""

# ------------------------------------------------------ test_code_only
#
# IT READS A MENTION, NOT A STATEMENT.
#
# The detector finds the line that sets the import path by asking
# whether the words appear on it:
#
#     if 'sys.path' in ln and 'insert' in ln
#
# A COMMENT saying why a file does NOT set the import path matches that
# perfectly, which is how it refused this round - the comment above
# explaining the absence was read as the presence.
#
# That is the sixth time in two days a check has read prose instead of
# structure, and the first time it has been the house's own tooling
# rather than a round's gate. check_gates.py now looks for the pattern
# in a patcher before it is applied; this fixes the one place
# check_gates cannot see, because it is not a patcher.
#
# The shape is a CALL: the name, a dot, the method, an open bracket.
CO_WAS = """    sp = next((i + 1 for i, ln in enumerate(lines)
               if 'sys.path' in ln and 'insert' in ln), None)"""

CO_NOW = """    # THE CALL, NOT THE WORDS. GT-2, 17 Oct 2026 - this asked whether
    # the line contained 'sys.path' and 'insert', so a COMMENT
    # explaining that a file does not set the import path matched it,
    # and the check refused a file that was correct. A statement has a
    # shape; prose about a statement does not.
    sp = next((i + 1 for i, ln in enumerate(lines)
               if re.search(r'(?<!#)\\bsys\\.path\\s*\\.\\s*'
                            r'(?:insert|append)\\s*\\(',
                            ln.split('#')[0])), None)"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- GT-2, 17 Oct 2026
    @{ File = 'Push-PendingChanges.ps1'; Text = 'alv_run.py'; What = 'GT-2: the gate runs its suites through alv_run' },
    # NO ABSENT SENTINEL ON THIS FILE, AND IT IS NOT AN OVERSIGHT.
    #
    # A sentinel row lives IN Push-PendingChanges.ps1. An ABSENT row
    # naming a string therefore PUTS that string into the very file it
    # declares the string missing from, and the check fails the moment
    # it is written. Three spellings were tried before the shape of the
    # problem was clear - the loop header, then a variable, then the
    # padding expression - and every one of them failed the same way,
    # because the fault is structural and not a choice of words.
    #
    # The claim is kept where it can be made: test_gate_speed.py asserts
    # by the SHAPE of the statement that no suite loop survives, which a
    # file checking itself cannot do.
    @{ File = 'alv_run.py'; Text = 'PLANTERS'; What = 'GT-2: the fourteen that must stay serial are named, not guessed' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


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
    raise SystemExit('GT-2 REFUSED: %s' % msg)


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


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    p1 = os.path.join(root, PS1)
    t = read(p1)

    # ---------------------------------------------------------------- 0
    if 'alv_run.py' in t:
        print('GT-2  already applied - the gate calls alv_run.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE RUNNER MUST BE ON DISK AND MUST WORK, before the gate is told
    # to depend on it. A round that points the gate at a file that does
    # not run is a round that takes the push away.
    runner = os.path.join(root, RUNNER)
    if not os.path.isfile(runner):
        refuse('%s is not on disk; the gate would call a file that does '
               'not exist' % RUNNER)
    src = read(runner)
    for need, what in (('PLANTERS', 'the serial list'),
                       ('as_completed', 'the completion-order reporting'),
                       ('suites_from_ps1', 'reading $suites from the gate'),
                       ('line_buffering', 'unbuffered progress')):
        if need not in src:
            refuse('%s does not carry %s (%s)' % (RUNNER, need, what))
    try:
        import ast
        ast.parse(src)
    except SyntaxError as e:
        refuse('%s would not parse - %s' % (RUNNER, e))
    # AND IT MUST READ THIS GATE'S OWN LIST. Asked, not assumed.
    #
    # No sys.path.insert here: Python already puts this script's own
    # directory first, and test_code_only polices files that set
    # sys.path BELOW their code_only alias - which this did, and which
    # it caught.
    import alv_run
    names = alv_run.suites_from_ps1(p1)
    listed = re.findall(r"'([^']+\.py)'",
                        re.search(r'\$suites\s*=\s*@\((.*?)\n\)', t,
                                  re.S).group(1))
    if names != listed:
        refuse('%s reads %d suite(s) from the gate and the gate lists %d'
               % (RUNNER, len(names), len(listed)))
    if len(alv_run.PLANTERS) != 15:
        refuse('%s names %d planter(s); the measurement on 16 Oct found '
               '14 and this round own suite makes 15'
               % (RUNNER, len(alv_run.PLANTERS)))
    # THE ROUND'S OWN SUITE JOINS THE LIST IN THIS SAME ROUND, so the
    # list to check against is the one this round is about to write, not
    # the one on disk. The first spelling compared against the pre-round
    # list and refused because test_gate_speed.py was not in it yet -
    # correctly, for the wrong moment.
    missing = [n for n in alv_run.PLANTERS if n not in names + [ME]]
    if missing:
        refuse('%s names planter(s) the gate does not run: %s'
               % (RUNNER, ', '.join(missing)))

    out = {}

    # ---------------------------------------------------------------- 2
    t = swap(t, PARAM_WAS, PARAM_NOW, '%s (the param block)' % PS1)
    t = swap(t, LOOP_WAS, LOOP_NOW, '%s (the suite loop)' % PS1)
    t = swap(t, SUITE_ANCHOR, SUITE_NEW, '%s ($suites)' % PS1)
    t = swap(t, SENT_ANCHOR, SENT_NEW, '%s ($sentinels)' % PS1)

    # ---------------------------------------------------------------- 3
    # THE GATES, asked of the result.
    # ASKED OF THE LOOP, NOT OF A MENTION OF IT. The first spelling
    # searched the whole file for `foreach ($t in $suites)` - which the
    # sentinel row this round adds contains - so the patcher refused its
    # own output. Fourth time today that a gate read prose instead of
    # structure; this is the shape of the statement.
    if re.search(r'(?m)^foreach \(\$t in \$suites\) \{', t):
        refuse('%s still runs its own loop' % PS1)
    # THE ASSIGNMENT, not a mention of it. This comment and the sentinel
    # row both name the variable; a containment test would refuse the
    # round's own output, which is how the previous two spellings died.
    if re.search(r'(?m)^\$suiteWide\s*=', t):
        refuse('%s still carries the old loop variables' % PS1)
    if '$skipped = @()' in t:
        refuse('%s still declares $skipped, which nothing fills now' % PS1)
    if 'Demetri, 1 Oct 2026' not in t:
        refuse('%s lost the request the numbering exists for' % PS1)
    if 'PadLeft($suiteWide)' in t:
        refuse('%s still pads a suite number, which only the removed '
               'loop did' % PS1)
    if t.count('& python @runArgs') != 1:
        refuse('%s: expected exactly one call to the runner, got %d'
               % (PS1, t.count('& python @runArgs')))
    if 'exit 1' not in t:
        refuse('%s no longer stops on a failing suite' % PS1)
    # THE LIST STAYS WHERE IT WAS. The runner reads it from here.
    if '$suites = @(' not in t:
        refuse('%s lost its $suites list, which the runner reads' % PS1)
    # BALANCED BRACES in the block this round wrote - a PowerShell file
    # that does not parse cannot be caught from a sandbox with no
    # PowerShell in it, so the one check available is counting.
    # THE BLOCK IS THE LITERAL THIS ROUND JUST INSERTED, not a slice
    # between two landmarks - the first spelling cut off before the
    # closing brace and reported its own text unbalanced.
    blk = fit(t, LOOP_NOW)
    if blk.count('{') != blk.count('}'):
        refuse('%s: the replacement block has %d { and %d }'
               % (PS1, blk.count('{'), blk.count('}')))
    if blk.count('(') != blk.count(')'):
        refuse('%s: the replacement block has %d ( and %d )'
               % (PS1, blk.count('('), blk.count(')')))
    out[p1] = t

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_ANCHOR, TREE_NEW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_ANCHOR, ROUNDS_NEW,
                  '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'GT-2, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    # THE ALIAS COUNT IS COUNTED, NOT ASSUMED - LF-1's lesson, one round
    # old. This round's patcher aliases code_only; its suite does not.
    import glob as _glob
    _al = [os.path.basename(f)
           for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    # COUNTED, NOT ASSUMED - AND NOT AN EQUALITY.
    #
    # LF-1 added this because the alias count stopped moving by two:
    # a round whose suite has no use for code_only does not alias it.
    # Counting the files on disk is right; demanding EQUALITY is not,
    # because the files of LATER rounds in the same bundle are already
    # on disk when this one applies. The count on disk is the final
    # figure for the whole bundle, not the figure for this round.
    #
    # So the claim is the one that can be made here: this round must
    # not write a number LARGER than the files that exist. The end
    # state - that test_code_only's number equals the files on disk -
    # is asserted by test_code_only itself, live, on every run.
    if (len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW or len(_sui) < ALIAS_S_NOW):
        refuse('the alias count on disk is %d (%d patchers, %d '
               'suites) and this round would write %d (%d, %d) - '
               'more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    _co = swap(read(p), CO_WAS, CO_NOW, '%s (the import-path detector)' % CO)
    if "if 'sys.path' in ln and 'insert' in ln" in _co:
        refuse('%s still reads the words rather than the call' % CO)
    t2 = bump(_co, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'GT-2, 17 Oct 2026 - this round own patcher',
              '%s (the alias count)' % CO)
    t2 = swap(t2, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[p] = t2

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('GT-2 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('GT-2 applied.')
    print('   the gate runs its suites through alv_run.py')
    print('   parallel, with the 14 planters serial and renders first')
    print('   -Resume restarts at the failure, not at suite 1')
    print('   the PowerShell change is one loop out and one call in')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
