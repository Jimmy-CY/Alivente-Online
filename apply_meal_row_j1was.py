# -*- coding: utf-8 -*-
"""ML-1, PART 2 - J-1'S `was()` GETS THE SAME TREATMENT ITS `now()` GOT

The sweep for ML-1 failed test_js_escape.py again:

    FAIL  and 45 already carried the filter - so the house knew the answer,
          in 45 places, and not in 147 others

THIS IS THE FIFTH TIME THE SAME DEFECT HAS SURFACED, and the fourth in this
one suite. J-2 fixed the `now()` side eight hours ago - four checks that
read the LIVE file and pinned tree-wide totals from it. This is the other
half of the pair:

    def was(p):
        return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else read(p)

"a backup, or THE FILE ITSELF where the round had nothing to change". That
second clause was true on the day J-1 ran and has been decaying ever since.
ML-1 edited meal_plans.html - a page J-1 never touched, so it has no
.bak_jsescape - and took two |escapejs out of it with the two onclicks it
converted. So J-1's count of what the tree looked like BEFORE J-1 moved
from 45 to 43, and J-1's suite reported it as a failure.

A "before" that is read from today's file is not a before. It is today.

==========================================================================
AND alv_rounds ALREADY HAS THE ANSWER, WRITTEN FOR EXACTLY THIS
==========================================================================
    def as_of(path, when, read):
        \"\"\"The text of `path` as it stood at time `when` - for a file a
        round READ but did not back up: its first backup written after
        `when`, or the file itself if nothing has touched it since.\"\"\"

That docstring describes this situation sentence for sentence. The helper
has been in alv_rounds since X0 and this suite has never called it.

`when` is the moment J-1 ran, which the tree still holds: the mtime of any
.bak_jsescape backup. The oldest is used, because a round writes its
backups as it goes and the first one is the closest thing to its start.

So:

    no .bak_jsescape       ->  as_of(p, when_j1_ran, read)
    a .bak_jsescape        ->  read it, unchanged

and a file ML-1 edits after J-1 ran now resolves to ML-1's own backup -
the file as it stood before ML-1, which is after J-1, which is what J-1's
control needs.

==========================================================================
THE RULE, WRITTEN DOWN FOR THE FIFTH TIME
==========================================================================
A SCOPE OR RECENCY CLAIM MUST BE MEASURED AGAINST THE STATE IT NAMES.

    "as this round left it"     as_left_by(path, SUFFIX, read)
    "as it stood when this round ran"   as_of(path, when, read)
    "before this round"         read(path + SUFFIX)

Never read(path). The live file is a different claim, and it is almost
never the one a suite means.

Backups: .bak_mealrow, the same suffix as part 1.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealrow'
ROOT = os.getcwd()
TARGET = os.path.join(ROOT, 'test_js_escape.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8'), raw, (b'\r\n' in raw)


def write(path, text, crlf):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if crlf
            else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('ML1W: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ML1W: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('ML-1 PART 2 - J-1 was() SCOPE%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

OLD = '''def was(p):
    """BEFORE this round. A backup, or the file itself where the round
    had nothing to change - as_left_by() is not used here because it
    returns the file as the round LEFT it, which is the opposite of a
    control. A1's lesson, and it cost a push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else read(p)'''

NEW = '''# WHEN J-1 RAN. The tree still holds it: the mtime of the oldest
# .bak_jsescape backup. A round writes its backups as it goes, so the
# first one is the closest thing to the moment it started.
#
# AND IT ASKS alv_tree, NOT os.walk. The first draft of this helper wrote
# `for folder, _sub, names in os.walk(ROOT)` - and test_tree_roots.py
# promptly reported this suite as "NOT ACCOUNTED FOR", because a census
# that builds its own walk is the exact mistake X0 exists to stop, and the
# crude detector that finds them does not care that this one was only
# looking for backups. It was right to flag it: J-1 touched twenty
# templates and every one of them is in alv_tree.templates(), so there was
# never a reason to walk the repo.
def _when_j1_ran():
    best = None
    for p in alv_tree.templates():
        b = p + SUFFIX
        if os.path.isfile(b):
            t = os.path.getmtime(b)
            if best is None or t < best:
                best = t
    return best


J1_RAN = _when_j1_ran()


def was(p):
    """BEFORE this round, and BEFORE means before - not today.

    A BACKUP WHERE J-1 MADE ONE. as_left_by() is deliberately not used
    here, because it returns the file as the round LEFT it, which is the
    opposite of a control. A1's lesson, and it cost a push.

    AND as_of() WHERE IT DID NOT. The old second clause read "the file
    itself where the round had nothing to change", which was true on the
    day J-1 ran and decayed from then on. ML-1 edited meal_plans.html -
    a page J-1 never touched, so it carries no .bak_jsescape - and took
    two |escapejs out of it, so this count moved from 45 to 43 and J-1's
    own control failed, eight hours after J-2 fixed the same defect on
    the now() side of this very file.

    as_of() has been in alv_rounds since X0 and does exactly this: the
    file's first backup written after `when`, or the file itself if
    nothing has touched it since. A page edited by a later round now
    resolves to THAT round's backup - the file before it, which is after
    J-1, which is the state this control names.

    THE RULE, FOR THE FIFTH TIME: a scope or recency claim is measured
    against the state it names, never against read(path).
    """
    if os.path.isfile(p + SUFFIX):
        return read(p + SUFFIX)
    if as_of is not None and J1_RAN is not None:
        return as_of(p, J1_RAN, read)
    return read(p)'''

t, raw, crlf = read(TARGET)

if 'def _when_j1_ran' in t:
    print('  test_js_escape.py        already uses as_of')
else:
    t = swap(t, OLD, NEW, 'the was() helper', crlf)
    # as_of has to be imported beside as_left_by.
    t = swap(t, '    from alv_rounds import as_left_by',
             '    from alv_rounds import as_left_by, as_of', 'the import',
             crlf)
    t = swap(t, '    as_left_by = None', '    as_left_by = as_of = None',
             'the import fallback', crlf)
    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t, crlf)
    print('  test_js_escape.py        was() now uses as_of for untouched '
          'files')

print('-' * 74)

if CHECK:
    print('  --check: nothing written')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(TARGET)[0]

import ast
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('ML1W: test_js_escape.py no longer parses: %s' % e)
print('  the suite still parses')

if 'from alv_rounds import as_left_by, as_of' not in t:
    raise SystemExit('ML1W: as_of is not imported')
if re.search(r'(?m)^\s*return read\(p\)\s*$', t.split('def filters_of')[0]
             .split('def was(p)')[1]):
    # the last-resort fallback is allowed, but only AFTER the as_of branch
    seg = t.split('def was(p)')[1].split('def filters_of')[0]
    if seg.index('as_of(') > seg.index('return read(p)'):
        raise SystemExit('ML1W: was() falls back to read(p) before trying '
                         'as_of')
print('  as_of is imported and tried before any fallback')

# AND THIS SUITE DOES NOT WALK THE REPO. test_tree_roots.py found the first
# draft of _when_j1_ran() doing exactly that and refused it, which is what
# X0 built the register for.
# AND IT IS ASKED OF THE PARSE TREE, NOT OF THE TEXT. The first draft of
# this gate grepped for `os.walk(` and failed on its OWN three mentions of
# it - one in the module docstring, one in the note above the helper, one
# inside a check message. That is the sixth time today a gate has read the
# record of a thing as the thing. ast sees calls; it does not see prose.
_walks = [n for n in ast.walk(ast.parse(t))
          if isinstance(n, ast.Call)
          and isinstance(n.func, ast.Attribute) and n.func.attr == 'walk'
          and isinstance(n.func.value, ast.Name) and n.func.value.id == 'os']
if _walks:
    raise SystemExit('ML1W: test_js_escape.py calls os.walk at line %s - '
                     'alv_tree knows where the templates are'
                     % _walks[0].lineno)
print('  and it calls os.walk nowhere - alv_tree is asked instead')

# NOTHING ELSE IN THE SUITE READS THE LIVE FILE IN A LOOP OVER THE TREE.
bad = []
for m in re.finditer(r'for rel, p in sorted\(PATHS\.items\(\)\):(.{0,300})',
                     t, re.S):
    for call in re.finditer(r'\b(?:census|HTML_C\.sub)\([^\n]*', m.group(1)):
        s = call.group(0)
        if 'left_by_j1(' not in s and 'was(' not in s:
            bad.append(s.strip()[:70])
if bad:
    raise SystemExit('ML1W: %d loop(s) still read the live file:\n   %s'
                     % (len(bad), '\n   '.join(bad[:6])))
print('  and no loop over the tree reads the live file')

# THE SUITE PASSES, AND ITS FOUR TOTALS ARE THE ONES J-1 LEFT.
import subprocess
r = subprocess.run([sys.executable, 'test_js_escape.py'],
                   capture_output=True, text=True, cwd=ROOT)
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('ML1W: test_js_escape.py still fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
out = r.stdout
for pat, want, what in (
        (r'and (\d+) are \|escapejs now', '192', 'protected now'),
        (r'and the (\d+) BARE arguments', '111', 'bare arguments'),
        (r'there were (\d+) unprotected before', '147', 'unprotected before'),
        (r'and (\d+) already carried the filter', '45', 'already safe')):
    m = re.search(pat, out)
    if not m or m.group(1) != want:
        raise SystemExit('ML1W: %s is %s, expected %s'
                         % (what, m.group(1) if m else '?', want))
    print('      %-22s %s' % (what, want))
tail = [ln for ln in out.split('\n') if 'passed' in ln]
print('  all four totals are J-1\'s own, and the suite passes -%s'
      % (tail[-1] if tail else ' rc 0'))

# AND THE PREMISE IS ASSERTED: meal_plans.html really did lose two
# |escapejs to ML-1, and really has no .bak_jsescape of its own.
import alv_tree
mp = alv_tree.path_of('meal_plans.html')
if os.path.isfile(mp + '.bak_jsescape'):
    raise SystemExit('ML1W: meal_plans.html HAS a .bak_jsescape - the '
                     'premise of this part is wrong')
a = read(mp)[0].count('|escapejs')
b = read(mp + SUFFIX)[0].count('|escapejs')
if b - a != 2:
    raise SystemExit('ML1W: meal_plans lost %d |escapejs to ML-1, expected 2'
                     % (b - a))
print('  meal_plans.html has no .bak_jsescape and lost 2 |escapejs to ML-1')
print('  - which is exactly why J-1\'s "before" had drifted')

print('-' * 74)
print('=' * 74)
