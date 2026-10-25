# -*- coding: utf-8 -*-
"""test_preflight_names.py - round PG-2, 24 Oct 2026.

TWO GATES THAT FAILED TODAY, AND NEITHER SAID SO.

SECTION 3 DRIVES THE PRE-FLIGHT rather than reading its regex. It
asks the real check() for a verdict on five subjects - the one from
this morning's push, an unapplied T2 round, an old-shape name, a
FINDING written E24, and a subject with no names at all - because a
pattern can be read as correct and still be wired to nothing.

AND IT REQUIRES BOTH PATTERNS TO HAVE MOVED. NAME reads the subject;
OWNS reads alv_rounds.py to learn who owns a suffix. Widen NAME alone
and every T2 name becomes unresolvable - and an unresolved name is a
REFUSAL, so the gate goes from blind to refusing every push. Section
2 asserts the two carry the same shape.

SECTION 4 IS THE ONE THAT TOOK FOUR ATTEMPTS, and each failure is a
check here:

    v1 asked "is the mark written unbroken ANYWHERE this round
    writes". T2-3 PASSED IT - its wrapped mark went into models.py
    while an unbroken one went into properties.py.

    v2 matched the wrap in any payload or anywhere in the source.
    It fired on FIVE OF SIX correct patchers.

    v3 resolved each payload's target file but read only
    double-quoted payloads, so it missed T2-3 again - that mark was
    in a single-quoted one.

    v4 read both and flagged T2-5, which is CORRECT: it wraps the
    mark in one payload and writes it whole in another, to the same
    file, so its check does fire.

The surviving rule is narrow, and section 4 drives it against a
RECONSTRUCTED T2-3 - the real patcher with its mark re-wrapped - and
then against every apply_*.py in the tree, requiring silence on all
of them. A gate that cries wolf on a correct round is how the two
before it earned theirs.
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
import io
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_pgnames'
ME = 'test_preflight_names.py'
PATCHER = 'apply_preflight_names.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PG-2, 24 Oct 2026'

PRE = os.path.join(ROOT, 'alv_preflight.py')
GATES = os.path.join(ROOT, 'check_gates.py')
GATE = os.path.join(ROOT, PS1)
FILES = (PRE, GATES)

SCRATCH = os.environ.get('ALV_SCRATCH') or os.path.join(ROOT, '_scratch')

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
OLD = dict((p, was(p)) for p in FILES)

CORE = r'[A-Z][A-Z0-9]{0,3}-\d+[a-z]?'


def claims(d):
    return {
        'the pre-flight can see a round name with a digit in it':
            CORE in d[PRE],
        '  and so can the register reader, which must move with it':
            d[PRE].count(CORE) >= 2,
        '  and the refusal says what to do about a false positive':
            'reword the subject' in d[PRE],
        'check_gates knows what a wrapped date mark is':
            'IS WRAPPED IN THE FILE' in d[GATES],
        '  and resolves which file each payload writes':
            'def target(' in d[GATES],
        '  and reads BOTH quote styles, not only one':
            'both.items()' in d[GATES],
        '  and spares a round that writes the mark whole elsewhere':
            'not whole' in d[GATES],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[PRE], 'the round dates itself, on one line')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok(r'[A-Z]{1,4}-\d+' in OLD[PRE],
   'CONTROL: the pre-flight really did match only capitals')
ok(OLD[PRE].count(r'[A-Z]{1,4}-\d+') == 2,
   '  in BOTH patterns, which is why both had to move',
   OLD[PRE].count(r'[A-Z]{1,4}-\d+'))

# AND THE TWO PATTERNS AGREE TODAY. Widening one alone is the failure
# that turns a blind gate into one that refuses every push.
pats = re.findall(r"re\.compile\(r'([^']+)'\)", NOW[PRE])
name_p = [x for x in pats if x.startswith(r'\b(')]
owns_p = [x for x in pats if x.startswith('^#')]
ok(name_p and owns_p and CORE in name_p[0] and CORE in owns_p[0],
   'the subject matcher and the register reader carry the SAME shape',
   [name_p[:1], owns_p[:1]])


# ==========================================================================
head('3. DRIVEN - the pre-flight, asked for real verdicts')
# ==========================================================================
import alv_preflight as P                                   # noqa: E402
import importlib                                            # noqa: E402
importlib.reload(P)


def verdict(subject):
    bad, say = P.check(subject, ROOT)
    return bad, '\n'.join(say)


# (a) THIS MORNING'S SUBJECT, which printed "nothing to check" before
#     this round and is the reason it exists.
bad, say = verdict('T2-3 T2-4 T2-5: the application names a joint '
                   'tenancy one way')
ok('3 round(s) named' in say,
   'the subject from this push names three rounds, and the gate sees '
   'all three', say.splitlines()[:1])
ok(not bad, '  and finds every one of them applied and backed up', bad)
ok('nothing to check' not in say,
   '  rather than reporting nothing to do in the language of success')

# (b) A T2 ROUND THAT IS NOT APPLIED. This is the 16 October shape -
#     a subject naming a round the tree has never heard of - and it
#     was invisible for the whole second-tenant family.
bad, say = verdict('T2-9: a round that does not exist')
ok(bad, 'an UNAPPLIED T2 round is refused, which is the 16 Oct shape '
        'this gate exists for', say)
ok(any('reword the subject' in b for b in bad),
   '  and the refusal says what to do if it was never a round name - '
   'the widened shape catches Q4-2026 too, and a refusal nobody can '
   'act on is a wall')

# (c) THE OLD SHAPE STILL RESOLVES. A widening that broke the names
#     this gate already handled would be a poor trade.
bad, say = verdict('ES-3a WK-1: the fourth tile')
ok('2 round(s) named' in say and not bad,
   'an old-shape name still resolves, and is still found applied', say)

# (d) A FINDING IS NOT A ROUND. E24 has no hyphen and a subject may
#     mention one; matching it would refuse a perfectly good push.
bad, say = verdict('E24 and E11 were the findings behind this')
ok('nothing to check' in say and not bad,
   'a FINDING like E24 is still not matched - no hyphen, not a round, '
   'and a subject may name one', say)

# (e) AND A SUBJECT WITH NO NAMES SAYS SO.
bad, say = verdict('tidy up the help text')
ok('nothing to check' in say and not bad,
   'a subject with no round names says so plainly')

# THE CONTROL: THE OLD FILE REALLY WAS BLIND TO (a) AND (b).
#
# Run from the backup, in a subprocess, because the module under test
# is already imported here.
old_path = os.path.join(SCRATCH, '_pg2_old_preflight.py')
if not os.path.isdir(SCRATCH):
    os.makedirs(SCRATCH)
with io.open(old_path, 'w', encoding='utf-8') as f:
    f.write(OLD[PRE])
try:
    r = subprocess.run([sys.executable, old_path,
                        'T2-3 T2-4 T2-5: the application names a joint '
                        'tenancy one way'],
                       cwd=ROOT, capture_output=True, text=True,
                       timeout=120)
    out = (r.stdout or '') + (r.stderr or '')
    ok('nothing to check' in out,
       'CONTROL: the version before this round printed "no round name '
       'in the subject - nothing to check" for that very subject, and '
       'then a green line', out.strip().splitlines()[-3:])
    ok(r.returncode == 0,
       '  and exited 0 - a gate finding nothing to do, in the language '
       'of success', r.returncode)
except Exception as e:
    ok(False, 'CONTROL ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('4. DRIVEN - the wrapped mark, against a reconstructed T2-3')
# ==========================================================================
#
# THE TRAP IS REBUILT FROM THE REAL PATCHER, not written by hand. The
# shipped apply_generate_second.py has its mark on one line and says
# in a comment why; this puts it back the way it was at about half
# past one on 24 October and asks the gate.
#
# A FIXTURE THAT INVENTED A PATCHER WOULD BE TESTING THE FIXTURE.
TRAP_SRC = os.path.join(ROOT, 'apply_generate_second.py')
ONE_LINE = ('    # WHO MAY HOLD A JOINT TENANCY, lifted out of clean().\n'
            '    # T2-3, 24 Oct 2026 - and it is the same rule it '
            'always was.')
WRAPPED = ('    # WHO MAY HOLD A JOINT TENANCY - lifted out of clean() '
           'by T2-3,\n    # 24 Oct 2026, and it is the same rule it '
           'always was.')


def gates_on(path):
    r = subprocess.run([sys.executable, 'check_gates.py', path],
                       cwd=ROOT, capture_output=True, text=True,
                       timeout=180)
    return (r.stdout or '') + (r.stderr or '')


if not os.path.isfile(TRAP_SRC):
    skip('section 4', 'apply_generate_second.py is not on disk')
else:
    real = read(TRAP_SRC)
    ok(ONE_LINE in real,
       'the shipped T2-3 patcher carries its mark on ONE line')
    ok(gates_on(TRAP_SRC).count('IS WRAPPED IN THE FILE') == 0,
       '  and the gate is silent on it, as it must be')

    trap = os.path.join(SCRATCH, '_pg2_trap.py')
    with io.open(trap, 'w', encoding='utf-8') as f:
        f.write(real.replace(ONE_LINE, WRAPPED))
    said = gates_on(trap)
    ok('IS WRAPPED IN THE FILE' in said,
       'and with the mark put BACK the way it shipped at 13:30, the '
       'gate catches it', said.strip().splitlines()[-6:])
    ok('MODELS' in said,
       '  naming the file main() checks, so the author can tell '
       'whether it bites')

    # THE THREE VERSIONS THAT DID NOT WORK, each asserted as a
    # property of the one that does.
    g = NOW[GATES]
    ok('not whole' in g,
       'v4 FAILED ON T2-5, which wraps the mark in one payload and '
       'writes it whole in another to the same file - so the rule '
       'spares a round whose check does fire')
    ok(gates_on(os.path.join(ROOT, 'apply_invoice_recipients.py'))
       .count('IS WRAPPED IN THE FILE') == 0,
       '  and T2-5 really is silent now, having tripped the version '
       'before')
    ok("'\"' * 3" in g or '"\'" * 3' in g or 'both' in g,
       'v3 MISSED T2-3 because it read only one quote style - the '
       'rule now reads both')
    ok('def target(' in g,
       'v2 FIRED ON FIVE OF SIX correct patchers because it never '
       'asked which file a payload writes')


# ==========================================================================
head('5. SILENT ON EVERY PATCHER IN THE TREE')
# ==========================================================================
#
# THE CHECK THAT STOPS THIS BECOMING THE PREVIOUS THREE. A gate that
# cries wolf on a correct round is ignored by the next author, and
# two of the four versions of this one did exactly that.
pats = sorted(glob.glob(os.path.join(ROOT, 'apply_*.py')))
ok(len(pats) > 400,
   'there are %d patchers to be silent on' % len(pats), len(pats))

# ONE PROCESS, NOT 525. check_gates takes a list.
CHUNK = 60
noisy = []
try:
    for i in range(0, len(pats), CHUNK):
        r = subprocess.run([sys.executable, 'check_gates.py']
                           + pats[i:i + CHUNK],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=600)
        out = (r.stdout or '') + (r.stderr or '')
        cur = None
        for line in out.split('\n'):
            if line.endswith('replacement literal(s)'):
                cur = line.split()[0]
            if 'IS WRAPPED IN THE FILE' in line:
                noisy.append(cur or '?')
    ok(not noisy,
       'and it is silent on every one of them - which is what the '
       'two versions before it could not manage', noisy)
except Exception as e:
    ok(False, 'the sweep over every patcher ran',
       '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('6. THE SENTINELS THIS ROUND ADDS CAN ACTUALLY FAIL')
# ==========================================================================
#
# A SENTINEL THAT CANNOT FAIL IS NOT A SENTINEL, and this round
# shipped one for half an hour.
#
# Its first row watched 'A-Z0-9' on alv_preflight.py. test_sentinels
# compares case-INSENSITIVELY, and the file has carried `[a-z0-9_]+`
# in its suffix regex since PG-1 - so the row matched whether or not
# the widening existed. test_sentinels found it the only way anyone
# could: by having a backup of that file for the first time.
ps1 = read(GATE)
rows = re.findall(r"File = '([^']+)'; Text = '([^']+)'([^}]*)\}", ps1)
# ROWS THIS ROUND ADDS, not every row on those files. PG-1 has its
# own sentinel on alv_preflight and check_gates carries two from NF-1
# - all three predate this round, all three are fine, and asking
# whether THEY were absent from a backup this round created is a
# question with no meaning.
before_ps1 = read(GATE + SUFFIX) if os.path.isfile(GATE + SUFFIX) else ''
mine = [(f, t) for f, t, rest in rows
        if 'Absent' not in rest
        and (f.endswith('alv_preflight.py') or f.endswith('check_gates.py'))
        and ("Text = '%s'" % t) not in before_ps1]
ok(len(mine) >= 2,
   'this round adds sentinels on both files it changes', len(mine))

for fname, txt in mine:
    full = os.path.join(ROOT, *fname.replace('\\', '/').split('/'))
    bak = full + SUFFIX
    if not os.path.isfile(bak):
        continue
    before = read(bak)
    ok(txt.lower() not in before.lower(),
       '%-18s %r was NOT there before, so the row can fail'
       % (os.path.basename(fname), txt[:34]))

# THE CONTROL, AND IT IS THE TEXT THAT WAS ACTUALLY SHIPPED.
old_pre = read(PRE + SUFFIX)
ok('a-z0-9' in old_pre.lower(),
   "CONTROL: 'A-Z0-9' really was in the file already - inside the "
   'suffix regex - so the first version of this row could never have '
   'failed, however wrong the round was')
ok('[a-z][a-z0-9]{0,3}-' not in old_pre.lower(),
   '  while the text it was replaced with really was absent')


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('[A-Z][A-Z0-9]{0,3}-' in gate and 'IS WRAPPED IN THE FILE' in gate,
   '  with sentinels on both halves, each watching text that was '
   'genuinely absent before')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
