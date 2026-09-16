"""apply_gate_wire.py - thirteen suites that were never on the gate.

    python apply_gate_wire.py --check     dry run, writes nothing
    python apply_gate_wire.py

Run from the repo root.

WHAT IS WRONG. `$suites` in Push-PendingChanges.ps1 lists 46 suites. The
repo contains 59. THE THIRTEEN THAT ARE MISSING HAVE NEVER GATED A PUSH -
including every suite written this week. They pass only because somebody
runs them by hand, which means the standards they enforce are not, in fact,
enforced.

Two of them had been FAILING for a day and a half and nothing said so:
test_ia_palette and test_ia_tiles check that no CSS comment in base spells a
script or style tag, and two pieces of prose - one in the standards block,
one in a comment written on 7 Sep - did exactly that.

WHAT THIS ROUND DOES. It adds the thirteen, in one dated block, each with a
line saying what it holds. It changes nothing else.

WHAT IT DOES NOT FIX, and this is worth knowing before a fresh clone

Four of the thirteen read a `.bak_*` snapshot, and those are gitignored. On
a machine that has never run the matching patcher they behave like this:

    test_print_leaks       stops with "no .bak_leak backups" and exits 1
    test_secondary_visible stops with "no base.html.bak_secvis" and exits 1
    test_ia_palette        fails a check naming the missing snapshot
    test_ia_tiles          fails two, same reason
    test_notify_btns       PASSES, having silently dropped three CONTROL
                           checks - 32 becomes 29 and it still reports zero
                           failures, which is the worst of the five

On THIS machine the snapshots exist and all five pass. The gate runs here,
so wiring them on is right; the fresh-clone behaviour is a separate round
and is on the running list. A suite that cannot find its snapshot should say
so loudly and skip, not fail and not quietly shrink.

HOUSE RULES: idempotent, .bak_gatewire backup never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
P = os.path.join(os.getcwd(), 'Push-PendingChanges.ps1')
if not os.path.exists(P):
    sys.exit('! Push-PendingChanges.ps1 not found - run from the repo root')

# The thirteen, each with the standard it holds. Ordered newest last, which
# is the convention the existing list already follows.
ADD = [
    ("test_comment_tint.py",
     "The comment tint on the Issues screens."),
    ("test_payment_days.py",
     "Tenant payment behaviour: the cutoff, and the ageing scale."),
    ("test_ia_palette.py",
     "Issues Analysis colours - AND that no CSS comment in base spells a\n"
     "    # script or style tag, which is how two pieces of prose broke it."),
    ("test_ia_tiles.py",
     "The Issues Analysis tiles, and the drill-down they open."),
    ("test_print_leaks.py",
     "What reaches paper. Needs .bak_leak; see the note in apply_gate_wire."),
    ("test_notify_btns.py",
     "The notification buttons. SILENTLY DROPS three checks when\n"
     "    # .bak_notify is missing - 32 becomes 29 and it still says zero\n"
     "    # failed. On the list to fix."),
    ("test_secondary_visible.py",
     "A secondary button hides only where a More menu carries it."),
    ("test_required_marker.py",
     "One spelling for the required marker, in a colour base owns."),
    ("test_standards_block.py",
     "The standards block: it describes a base that exists, ships nothing,\n"
     "    # and contains no prose shaped like a tag or a comment."),
    ("test_heading_standard.py",
     "Every page heads itself the way base says."),
    ("test_heading_prefix.py",
     "The brand is in the browser tab, not on the heading."),
    ("test_projects_heading.py",
     "Shape B: the module on the h2, MODE LABEL and record name on the h4."),
    ("test_required_sweep.py",
     "Every required field says so. Newest, so most likely to be what\n"
     "    # breaks."),
]

HEADER = """
    # ------------------------------------------------------------------
    # WIRED ON 9 Sep 2026. Every suite below already existed and NONE of
    # them was on this list - they passed only because somebody ran them
    # by hand, which is not the same as being enforced. Two had been
    # failing for a day and a half without anything saying so.
    #
    # Four read a .bak_* snapshot, and those are gitignored: on a fresh
    # clone they fail or, worse, quietly shrink. See apply_gate_wire.py.
    # ------------------------------------------------------------------
"""

with open(P, encoding='utf-8', newline='') as f:
    RAW = f.read()
CRLF = '\r\n' in RAW
t = RAW.replace('\r\n', '\n')

i = t.index('$suites = @(')
depth, k = 0, t.index('@(', i) + 1
while k < len(t):
    if t[k] == '(':
        depth += 1
    elif t[k] == ')':
        depth -= 1
        if depth == 0:
            break
    k += 1
ARRAY = t[i:k]

already = [n for n, _ in ADD if "'" + n + "'" in ARRAY]
if len(already) == len(ADD):
    print('  already wired - nothing to do.')
    sys.exit(0)

FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


todo = [(n, w) for n, w in ADD if "'" + n + "'" not in ARRAY]
block = HEADER + ''.join(
    "    # %s\n    '%s',\n" % (why, name) for name, why in todo)
# the last entry in the array must not carry a trailing comma
block = block.rstrip()
if block.endswith(','):
    block = block[:-1]

NEW_ARRAY = ARRAY.rstrip() + ',\n' + block + '\n'
t = t[:i] + NEW_ARRAY + t[k:]

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
depth, k2 = 0, t.index('@(', t.index('$suites = @(')) + 1
while k2 < len(t):
    if t[k2] == '(':
        depth += 1
    elif t[k2] == ')':
        depth -= 1
        if depth == 0:
            break
    k2 += 1
NEW = t[t.index('$suites = @('):k2 + 1]
names = re.findall(r"'(test_[a-z_]*\.py)'", NEW)

want(len(names) == len(set(names)), 'a suite is listed twice: %s'
     % [n for n in names if names.count(n) > 1][:3])
for n, _ in ADD:
    want(n in names, '%s did not make it into the list' % n)
want(NEW.rstrip().endswith(')'), 'the array does not close')
want(not re.search(r",\s*\)\s*$", NEW.rstrip()),
     'the array ends with a trailing comma, which PowerShell tolerates but '
     'the next reader will not')
# EVERY NAME MUST BE A FILE. A suite listed but absent only warns, so a typo
# would sit there for weeks looking like it was running.
_gone = [n for n in names if not os.path.exists(os.path.join(os.getcwd(), n))]
want(not _gone, 'listed but not on disk: %s' % _gone[:4])
# NOTHING ELSE IN THE SCRIPT MOVED.
want(t.replace(NEW, ARRAY + ')') == RAW.replace('\r\n', '\n'),
     'something outside the suites array changed')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

print('  the gate now runs %d suite(s), up from %d.'
      % (len(names), len(names) - len(todo)))
for n, _ in todo:
    print('    + %s' % n)
print('\n  %d of the repo\'s suites are now on the gate; %d are not.'
      % (len(names),
         len([f for f in os.listdir(os.getcwd())
              if f.startswith('test_') and f.endswith('.py')]) - len(names)))

out = t.replace('\n', '\r\n') if CRLF else t
if not CHECK:
    bak = P + '.bak_gatewire'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(RAW)
    with open(P, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
