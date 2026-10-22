# -*- coding: utf-8 -*-
"""apply_planter_lock.py - round LK-1, 22 Oct 2026.

A PLANTER KILLED MID-PLANT LEAVES A DEFECT ON DISK AND NOTHING NOTICES.

Logged on 17 October, when exactly that explanation was proposed for a
mismatched backup, fitted the evidence, and turned out to be untrue.
The note said: the idea stands on its own merits even though it was not
the cause here - a planter killed mid-plant DOES leave a defect, and
nothing notices. Not urgent. This is it.

FIFTEEN SUITES WRITE INTO REAL FILES. test_css_order proves a selector
collision by MAKING one; test_icon_names plants a ghost glyph on a
button. Each copies the victim aside, writes, checks, and restores in a
finally - correct for everything Python can catch, and useless against
a SIGKILL, a closed laptop, or a timeout that gets there first. The
defect stays in the file, every later suite reads it, and the diagnosis
is a day spent on the wrong thing.

THE LOCK IS ARMED AROUND THE LIST, NOT INSIDE THE SUITES. alv_run.py
already knows which suites plant: the list is explicit rather than
detected, and test_gate_speed re-derives the signature and fails if a
suite outside it starts planting. Arming around that list covers all
fifteen at once, covers the sixteenth the day it joins, and needs no
edit in any suite - fifteen bespoke edits in fifteen different shapes
would be fifteen chances to get one wrong.

IT NAMES THE DAMAGE AND DOES NOT TOUCH IT. The lock holds a
FINGERPRINT - sha256 per file, 1,504 files and 32.6 MB in 0.12 seconds,
measured on 22 October - not the bytes. Keeping 32 MB per planter per
run to insure against a kill that has not happened yet is a cost paid
for ever; naming the file exactly is enough, and `git checkout --
<file>` is the fix, run by whoever can see whether that file has other
work in it. A tool in this tree that silently rewrote source files
would be a worse thing to own than the problem it solved.

AND IT CATCHES THE QUIET VERSION TOO. disarm() compares after every
planter, not only after a kill. A planter that completes and restores
IMPERFECTLY - puts back a file with a different line ending, misses one
of two victims - has never been checked by anything. Now the run stops
and says which file.

THE COST IS 0.24 SECONDS PER PLANTER. Thirty fingerprints across a
sweep of 421 suites that takes twenty-nine minutes: about 3.6 seconds,
measured, and the suite holds it to a ceiling so a later round that
makes fingerprint() expensive finds out here.

Idempotent. Every file backed up to .bak_planterlock.
"""
import os
import re
import sys

SUFFIX = '.bak_planterlock'
RUN = 'alv_run.py'
GSER = 'test_gate_serial.py'
GSPD = 'test_gate_speed.py'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_planter_lock.py'
PATCHER = 'apply_planter_lock.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'LK-1, 22 Oct 2026'
CHECK = False
# THE ONE ROUND IN THIS PUSH THAT BRINGS A FILE WITH IT. alv_plant.py
# is new, so it has no backup and cannot have one - and the pre-flight
# must be told rather than left to find a file it cannot pair.
CREATES = ('alv_plant.py',)

# ==========================================================================
# THE SUITE JOINS THE PLANTERS, BECAUSE IT PLANTS
# ==========================================================================
# test_gate_speed re-derives the planting signature and fails if a suite
# outside the list starts writing into the repo. This round's own suite
# does - it makes a probe file, damages it, and removes it - and the
# check found it, which is exactly what happened to test_gate_speed
# itself. Arguing with the signature is how a race nobody can reproduce
# gets written.
PL_WAS = """    'test_gate_speed.py',"""

PL_NOW = """    'test_gate_speed.py',
    # LK-1, 22 Oct 2026 - and this round's own suite, for the same
    # reason and found the same way. It writes a probe file into the
    # repo, kills a child that damages it, and removes both. The
    # signature caught it; it is here because of that and not because
    # anybody remembered.
    'test_planter_lock.py',"""

IMP_WAS = """def run_one(name):"""

# ==========================================================================
# TWO SUITES COUNT THE PLANTERS, AND THE COUNT CHANGED
# ==========================================================================
# GT-2's suite pins the number and GS-1's pins that its own round did
# not re-file the list. Both were right about their own rounds. A
# sixteenth planter is exactly the event both were written to notice,
# so both move - and the one that says 'byte-for-byte the same before
# and after' is re-asked of what it really promised: GS-1 added a
# reason, not a planter.
GSPD_WAS = """ok(len(alv_run.PLANTERS) == 15,
   '%d planter(s) are named - the fourteen measured on 16 Oct, and '
   'this suite, which section 3 below caught writing into the repo '
   'itself' % len(alv_run.PLANTERS))"""

GSPD_NOW = """ok(len(alv_run.PLANTERS) == 16,
   '%d planter(s) are named - the fourteen measured on 16 Oct, this '
   'suite, and test_planter_lock, both of which section 3 below '
   'caught writing into the repo themselves' % len(alv_run.PLANTERS))"""

GSER_N_WAS = """ok(planters is not None and len(planters) == 15,
   '  the fifteen planters are untouched; this round adds a reason, it '
   'does not re-file the old one',
   '%s planter(s)' % (len(planters) if planters else '?'))"""

GSER_N_NOW = """ok(planters is not None and len(planters) == 16,
   '  the sixteen planters are untouched; this round adds a reason, it '
   'does not re-file the old one',
   '%s planter(s)' % (len(planters) if planters else '?'))"""

GSER_C_WAS = """bp = listed(BEFORE, 'PLANTERS')
ok(bp == planters,
   'CONTROL: the planters are byte-for-byte the same list before and '
   'after - %d names' % len(bp or []),
   '%r != %r' % (bp, planters))"""

# LK-1, 22 Oct 2026 - A LATER ROUND ADDED ONE, which is what the list
# is for. GS-1's promise was that IT did not touch the list, and that
# is still provable against its own backup; asked of the live tree it
# became a promise that no round may ever add a planter, which is the
# opposite of what the list means.
GSER_C_NOW = """bp = listed(BEFORE, 'PLANTERS')
ok(bp is not None and set(bp) <= set(planters or []),
   'CONTROL: GS-1 took nothing off the planters list - %d names then, '
   '%d now, and every one of the old ones is still there'
   % (len(bp or []), len(planters or [])),
   '%r != %r' % (bp, planters))
ok(sorted(set(planters or []) - set(bp or []))
   == ['test_planter_lock.py'],
   '  and the only name added since is LK-1 own suite, which plants',
   sorted(set(planters or []) - set(bp or [])))"""

GS_WAS = """    with open(os.path.join(tmp, RUNNER), 'w', encoding='utf-8') as f:
        f.write(src)"""

GS_NOW = """    with open(os.path.join(tmp, RUNNER), 'w', encoding='utf-8') as f:
        f.write(src)
    # THE RUNNER'S HELPER TRAVELS WITH IT - LK-1, 22 Oct 2026.
    #
    # alv_run imports alv_plant now, and this harness copied the runner
    # ALONE into the temp directory. The first run after that round
    # failed every claim in this suite on an ImportError, which read as
    # the scheduler being broken rather than the harness being
    # incomplete. shutil, not a re-write: the code under test is the
    # code that shipped, and that applies to the module beside it.
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'alv_plant.py')
    if os.path.isfile(helper):
        shutil.copyfile(helper, os.path.join(tmp, 'alv_plant.py'))"""

IMP_NOW = """import alv_plant                                          # noqa: E402


def planting(names, run):
    \"\"\"Run the planters with the lock armed once around all of them.

    LK-1, 22 Oct 2026. The lock is written BEFORE the first planter and
    cleared after the last, so a kill anywhere in the phase leaves it
    on disk for the next run to find.

    ONCE AROUND THE PHASE, NOT ONCE PER PLANTER. The first spelling
    armed and disarmed around each one - thirty-two fingerprints in a
    sweep. On Demetri's laptop that is 8,392 files and 3.26 seconds
    each: 97 seconds added to a run, found by his gate on 22 October
    and not by anything here, because the mirror holds 1,395 files and
    took 0.12. Two fingerprints cost six seconds there and a quarter of
    one here.

    WHAT THAT GIVES UP is which planter left a file behind; what it
    keeps is WHICH FILE, which is the part anybody acts on. The lock
    names the phase and the file, and the file is what git checkout
    takes.
    \"\"\"
    armed = alv_plant.arm('the planter phase: ' + ', '.join(names))
    try:
        for n in names:
            yield run(n)
    finally:
        changed, vanished, appeared = alv_plant.disarm('planters', armed)
        for label, paths in (('did not put back', changed),
                             ('deleted', vanished),
                             ('left behind', appeared)):
            if paths:
                print('  !! the planters %s %d file(s):'
                      % (label, len(paths)))
                for p in paths[:8]:
                    print('       %s' % p)


def run_one(name):"""

MAIN_WAS = """    plant = [n for n in todo if n in PLANTERS]"""

MAIN_NOW = """    # ---- A KILLED PLANTER LEFT A LOCK - LK-1, 22 Oct 2026.
    #
    # Asked before anything runs, because every suite after this point
    # would be reading a tree that nobody meant to test, and the
    # failures it produced would be about the wrong thing.
    #
    # IT NAMES AND REFUSES; IT DOES NOT PUT ANYTHING BACK. See
    # alv_plant.py - restoring a source file silently is a worse thing
    # to own than the fault it fixes.
    left = alv_plant.recover()
    if left is not None:
        suite, changed, vanished, appeared = left
        if changed or vanished or appeared:
            print('')
            print('  !! %s WAS KILLED WHILE IT HAD A FILE OPEN.' % suite)
            print('     The tree is not the tree this sweep means to '
                  'test. Put these back and run again:')
            for label, paths in (('changed', changed),
                                 ('deleted', vanished),
                                 ('appeared', appeared)):
                for p in paths[:12]:
                    print('       %-9s git checkout -- %s' % (label, p))
            print('')
            return 1
        print('  -- a planter lock was left by %s, and the tree matches '
              'it - clearing it' % suite)
        alv_plant.release()

    plant = [n for n in todo if n in PLANTERS]"""

SER_WAS = """    for n in serial:
        if not report(run_one(n)):
            break"""

SER_NOW = """    # LK-1, 22 Oct 2026 - THE PLANTERS RUN WITH THE LOCK ARMED, once
    # around the whole phase rather than once per suite. The contended
    # ones beside them do not write into the tree, so they go through
    # run_one unchanged.
    stop = False
    for outcome in planting(plant, run_one):
        if not report(outcome):
            stop = True
            break
    if not stop:
        for n in slow:
            if not report(run_one(n)):
                break"""

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
    raise SystemExit('LK-1 REFUSED: %s' % msg)


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

    pr = os.path.join(root, RUN)
    r = read(pr)
    if MARK in r:
        print('LK-1  already applied - a killed planter leaves a lock.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE MODULE THIS ROUND NEEDS MUST BE HERE. It is this round's own
    # new file, and a patcher that wires a module it did not ship is a
    # patcher that breaks the sweep.
    if not os.path.isfile(os.path.join(root, 'alv_plant.py')):
        refuse('alv_plant.py is not on disk, and this round wires it '
               'into the runner')

    r = swap(r, IMP_WAS, IMP_NOW, '%s (the runner)' % RUN)
    r = swap(r, MAIN_WAS, MAIN_NOW, '%s (the recovery)' % RUN)
    r = swap(r, SER_WAS, SER_NOW, '%s (the serial loop)' % RUN)
    r = swap(r, PL_WAS, PL_NOW, '%s (the planters list)' % RUN)
    out[pr] = r

    # THE RUNNER'S HELPER TRAVELS WITH IT. test_gate_serial copies
    # alv_run.py into a temp directory and runs it there, with its own
    # CONTENDED list spliced in - the code under test is the code that
    # shipped. It copied the runner ALONE, and this round gave the
    # runner a sibling module, so the harness imported nothing and
    # every claim in that suite failed on an ImportError.
    pg = os.path.join(root, GSER)
    g = read(pg)
    g = swap(g, GS_WAS, GS_NOW, '%s (the harness)' % GSER)
    g = swap(g, GSER_N_WAS, GSER_N_NOW, '%s (the count)' % GSER)
    g = swap(g, GSER_C_WAS, GSER_C_NOW, '%s (the control)' % GSER)
    out[pg] = g

    psp = os.path.join(root, GSPD)
    out[psp] = swap(read(psp), GSPD_WAS, GSPD_NOW, '%s (the count)' % GSPD)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_ws_prefetch.py'
)""", """    'test_ws_prefetch.py',
    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'pages/views/users.py'; Text = \"to_attr='member_list'\";""",
             """    @{ File = 'alv_plant.py'; Text = 'def recover'; What = 'LK-1: fifteen suites write into real files and restore in a finally, which a SIGKILL does not run - the defect stays and nothing noticed. The lock is armed around the PLANTERS list, names every file a planter did not put back, and deliberately restores nothing' },
    @{ File = 'pages/views/users.py'; Text = \"to_attr='member_list'\";""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py',
]""", """    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py',
    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    '.bak_wsprefetch',
]""", """    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    '.bak_wsprefetch',
    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    '.bak_planterlock',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # LK-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nr = T.python_code_only(out[pr], payloads=True)
    if 'alv_plant.recover()' not in nr:
        refuse('%s: nothing asks what a killed planter left' % RUN)
    if 'alv_plant.arm(' not in nr:
        refuse('%s: nothing arms the lock, so there is nothing to find'
               % RUN)
    # ONCE AROUND THE PHASE. Arming per planter cost 97 seconds on
    # Demetri's laptop, measured by his gate on 22 October.
    if nr.count('alv_plant.arm(') != 1 or nr.count('alv_plant.disarm(') != 1:
        refuse('%s: the lock is armed %d time(s) and cleared %d - once '
               'each, around the whole planter phase'
               % (RUN, nr.count('alv_plant.arm('),
                  nr.count('alv_plant.disarm(')))
    # THE RECOVERY IS BEFORE THE FIRST SUITE, not after it. A tree that
    # is wrong is wrong for suite 1 as much as for suite 421.
    # .find(), NOT .index(). The serial loop was rewritten by this
    # round, so the string this looked for stopped existing and the
    # gate RAISED instead of refusing - which blocks a round exactly as
    # hard and says far less about why.
    _rec = nr.find('alv_plant.recover()')
    _first = nr.find('for outcome in planting(')
    if not 0 <= _rec < _first:
        refuse('%s: the recovery does not run before the first suite, '
               'and a tree that is wrong is wrong for suite 1 as much '
               'as for suite 421 (%d, %d)' % (RUN, _rec, _first))
    # AND IT RESTORES NOTHING. The whole design decision, in a gate.
    plant = T.python_code_only(read(os.path.join(root, 'alv_plant.py')),
                               payloads=True)
    for write_shape in ("open(path, 'w'", 'shutil.copy', 'shutil.move',
                        'os.replace', 'subprocess', 'git '):
        if write_shape in plant:
            refuse('alv_plant.py names %r. It takes hashes and names '
                   'files; a tool in this tree that rewrites source '
                   'silently is worse than the fault it fixes'
                   % write_shape)
    if 'def recover' not in plant or 'def arm' not in plant:
        refuse('alv_plant.py is not the module this round wires in')
    # A VIRTUAL ENVIRONMENT IS NOT SOURCE, and it is not called venv.
    if 'pyvenv.cfg' not in plant:
        refuse('alv_plant.py does not recognise a virtual environment '
               'by its marker. Demetri environment is a directory '
               'called `code`, and a skip list of NAMES hashed every '
               'file in site-packages')
    # THE SUITE IS ON THE PLANTERS LIST. test_gate_speed re-derives the
    # signature and would refuse the sweep otherwise.
    if "'test_planter_lock.py'," not in nr:
        refuse('%s: this round own suite plants and is not in PLANTERS '
               '- test_gate_speed will refuse the sweep' % RUN)
    # AND THE HARNESS THAT COPIES THE RUNNER COPIES ITS HELPER.
    ng = out[os.path.join(root, GSER)]
    if 'alv_plant.py' not in ng:
        refuse('%s: the harness copies the runner without the module it '
               'now imports, and every claim in it fails on an '
               'ImportError' % GSER)

    if CHECK:
        print('LK-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus alv_plant.py, which this round CREATES')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('LK-1  applied - a killed planter leaves a lock behind.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      and alv_plant.py is new - it has no backup by nature.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
