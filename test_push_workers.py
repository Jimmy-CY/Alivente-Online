# -*- coding: utf-8 -*-
"""test_push_workers.py - round WK-1, 23 Oct 2026.

THE PUSH SCRIPT CAN BE TOLD HOW MANY SUITES TO RUN AT ONCE.

alv_run.py has had --workers since GT-2 and defaults to 6. The push
script could not pass it, so the only way to sweep at 3 was to run
alv_run.py by hand and then push. rc=3221227274 - 0xC0000374, Windows
heap corruption under pool contention - killed a sweep at suite 371
and again at 370 on 23 October, and both suites passed when re-run
alone.

THERE IS NO POWERSHELL IN THE SANDBOX THESE ROUNDS ARE BUILT IN, so
this suite cannot run the script. Asserting that the text looks right
would be a claim about my own typing. Section 3 does the next
strongest thing available: it READS the argument-building lines out
of the script, evaluates that logic in Python for a range of inputs,
and asks what the runner would actually have been handed. A
transcription can be wrong; a transcription that is exercised and
compared is wrong in a way that shows.

AND SECTION 4 ASKS THE RECEIVER. A switch the far end does not
understand fails at the far end, so --workers is looked for in
alv_run.py's own parser rather than assumed.
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

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_pushworkers'
ME = 'test_push_workers.py'
PATCHER = 'apply_push_workers.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'WK-1, 23 Oct 2026'

GATE = os.path.join(ROOT, PS1)
RUNNER = os.path.join(ROOT, 'alv_run.py')
FILES = (GATE,)

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def arg_lines(src):
    """The block that builds the runner's argument list, read out of
    the script - from `$runArgs = @(` to the call."""
    a = src.find("$runArgs = @((Join-Path $root 'alv_run.py'))")
    b = src.find('& python @runArgs', a)
    return src[a:b] if a >= 0 and b > a else ''


def param_block(src):
    a = src.find('param(')
    b = src.find('\n)', a)
    return src[a:b] if a >= 0 and b > a else ''


def claims(d):
    g = d[GATE]
    blk = arg_lines(g)
    par = param_block(g)
    return {
        # SY-1, 26 Oct 2026 - DEFAULT 2, his decision: every push was
        # being typed with -Workers 2 or 3. -Workers 0 still says nothing.
        'the push script takes a -Workers parameter':
            '[int]$Workers = 2,' in par,
        '  defaulting to two since SY-1, so a bare push sweeps at 2':
            bool(re.search(r'\[int\]\$Workers\s*=\s*2\s*,', par)),
        'and it reaches the runner':
            '--workers' in blk,
        '  only when it is greater than zero':
            bool(re.search(r'if \(\$Workers -gt 0\)', blk)),
        'and --force and --resume still reach it too':
            "'--force'" in blk and "'--resume'" in blk,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

g = NOW[GATE]
ok(g.count('& python @runArgs') == 1,
   'there is exactly one call to the runner', g.count('& python @runArgs'))
ok(MARK in g, 'the round dates itself in the script')
ok('0xC0000374' in g or 'rc=3221227274' in g,
   '  and names the failure that made it worth doing, so the next '
   'reader is not left guessing why a parameter exists')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == ['and --force and --resume still reach it too'],
   'CONTROL: only the GUARD claim held before this round - everything '
   'it adds is new, and the one thing it promises not to break was '
   'already working', held)
ok('--workers' not in arg_lines(OLD[GATE]),
   'CONTROL: the push script really could not pass --workers at all, '
   'which is why sweeping at 3 meant running alv_run.py by hand')


# ==========================================================================
head('3. DRIVEN - what the runner would actually be handed')
# ==========================================================================
# THE LOGIC IS READ OUT OF THE SCRIPT AND EXERCISED, not asserted.
# There is no PowerShell here, so the alternative is to look at the
# text and say it seems right - which is a claim about my typing.
blk = arg_lines(NOW[GATE])


def simulate(force, resume, workers):
    """Evaluate the script's own argument-building lines in Python.

    Each line is matched as `if (<cond>) { $runArgs += <thing> }` and
    the three conditions this script uses are understood. A line in a
    shape this function does not understand FAILS the run rather than
    being skipped - a simulator that silently ignores what it cannot
    read would pass whatever it was given.
    """
    args = ['alv_run.py']
    for line in blk.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('$runArgs ='):
            continue
        m = re.match(r"if \((.+?)\)\s*\{\s*\$runArgs \+= (.+?)\s*\}$", line)
        if not m:
            raise ValueError('unreadable line: %r' % line[:70])
        cond, add = m.group(1).strip(), m.group(2).strip()
        if cond == '$Force':
            take = force
        elif cond == '$Resume':
            take = resume
        elif cond == '$Workers -gt 0':
            take = workers > 0
        else:
            raise ValueError('unknown condition: %r' % cond)
        if not take:
            continue
        if add == "'--force'":
            args.append('--force')
        elif add == "'--resume'":
            args.append('--resume')
        elif add == '@(\'--workers\', "$Workers")':
            args += ['--workers', str(workers)]
        else:
            raise ValueError('unknown addition: %r' % add)
    return args


try:
    cases = [
        ((False, False, 0), ['alv_run.py']),
        ((True, False, 0), ['alv_run.py', '--force']),
        ((False, True, 0), ['alv_run.py', '--resume']),
        ((False, True, 3), ['alv_run.py', '--resume', '--workers', '3']),
        ((False, False, 6), ['alv_run.py', '--workers', '6']),
        ((True, True, 1), ['alv_run.py', '--force', '--resume',
                           '--workers', '1']),
    ]
    for (f_, r_, w_), want in cases:
        got = simulate(f_, r_, w_)
        ok(got == want,
           'Force=%-5s Resume=%-5s Workers=%d  ->  %s'
           % (f_, r_, w_, ' '.join(want[1:]) or '(nothing)'), got)

    # THE ONE THAT MATTERS: zero adds nothing at all.
    # SY-1, 26 Oct 2026 - a push that does not mention workers now
    # passes 2; -Workers 0 is how to leave the choice to the runner.
    ok('--workers' not in simulate(False, True, 0),
       '-Workers 0 adds nothing at all, so the runner own default is '
       'still one word away')

    # AND THE SIMULATOR CAN FAIL. A comparison that cannot fail is
    # not a check - the lesson of 20 October.
    broke = False
    try:
        real_blk = blk
        blk = blk + "\nif ($Nonsense) { $runArgs += '--nope' }"
        simulate(False, False, 0)
    except ValueError:
        broke = True
    finally:
        blk = real_blk
    ok(broke,
       'CONTROL: the simulator REFUSES a line it does not understand, '
       'so it cannot pass a script it failed to read')
except ValueError as e:
    ok(False, 'the argument-building block is readable', str(e))


# ==========================================================================
head('4. THE RECEIVER UNDERSTANDS IT')
# ==========================================================================
run = read(RUNNER)
ok("'--workers'" in run or '"--workers"' in run,
   'alv_run.py really does accept --workers - a switch the far end '
   'does not know is a switch that fails at the far end')
m = re.search(r"add_argument\('--workers'[^)]*default=(\d+)", run)
ok(bool(m), '  and it has a default of its own', m.group(0) if m else None)
if m:
    ok(int(m.group(1)) >= 1,
       '  which is %s - so leaving -Workers at zero is not the same as '
       'asking for none' % m.group(1))
ok('CONTENDED' in run,
   'and the per-suite escape hatch is still there - CONTENDED pins a '
   'named suite to the serial phase, which is the right tool for one '
   'suite and the wrong one for a machine')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
tree = read(os.path.join(ROOT, 'alv_tree.py'))
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
patch = read(os.path.join(ROOT, PATCHER))

ok(ME in g, 'the suite is on the gate')
ok(ME in tree, 'and in alv_tree.CONVERTED')
ok(tree.count("'%s'" % ME) == 1, '  exactly once')
ok("'.bak_pushworkers'" in rounds, 'and the round is in alv_rounds.ROUNDS')
ok('ZERO MEANS SAY NOTHING' in g, 'and the sentinel is on the push gate')
ok(os.path.exists(GATE + SUFFIX), 'backed up: %s' % PS1)
ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = ()' in patch, 'and declares that it creates nothing')
ok('param at %d' in patch or 'inside param()' in patch,
   'and its gate asks WHERE the parameter landed, not merely that the '
   'text exists - check_gates refused the first spelling for matching '
   'the round own output')

# NOTHING ELSE IN THE SCRIPT MOVED.
a, b = arg_lines(OLD[GATE]), arg_lines(NOW[GATE])
added = [l.strip() for l in b.split('\n') if l.strip()
         and l.strip() not in [x.strip() for x in a.split('\n')]]
real = [l for l in added if not l.startswith('#')]
ok(len(real) == 1 and '--workers' in real[0],
   'exactly ONE line was added to the argument block', real)


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that the script runs. There is no PowerShell in the
  sandbox, so section 3 exercises the argument logic read out
  of the file rather than the file itself. The first push
  that passes -Workers is the proof of the script.

  Not that 3 is the right number. It is the number that has
  twice completed a sweep this laptop could not complete at
  6. What the machine can really take is a measurement
  nobody has made.

  Not that pool contention is understood. 0xC0000374 is heap
  corruption; this round lets somebody avoid it, and nothing
  here explains it.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
