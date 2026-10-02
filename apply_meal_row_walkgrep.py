# -*- coding: utf-8 -*-
"""ML-1, PART 3 - A GREP FOR os.walk THAT READS PROSE

The sweep for ML-1 failed two suites:

    test_tree_roots.py    NOT ACCOUNTED FOR: ['test_js_escape.py']
    test_waiting_down.py  the same

Both decide which suites WALK the tree with the same line:

    walking = [n for n in scripts()
               if n.startswith('test_') and n != ME
               and 'os.walk(' in read(os.path.join(ROOT, n))]

A raw substring, on the whole file, comments included.

ML-1 part 2 put a NOTE in test_js_escape.py explaining that its first
draft had used `os.walk(ROOT)` and why that was wrong. The note quotes the
call. So the grep found it, decided the suite walks the tree, looked it up
in the register, did not find it, and failed - because of a comment saying
"this file does not do this any more".

==========================================================================
AND THIS EXACT DEFECT IS ALREADY DOCUMENTED TEN LINES ABOVE IT
==========================================================================
test_tree_roots.py's other detector carries this, from 30 Sep:

    # CODE, NOT PROSE - 30 Sep. This line used to read the whole file,
    # comments included, so a comment that NAMED os.walk of a root was
    # indistinguishable from a call to it. G3a's own patcher was counted
    # that way. Every other gate in this repo strips comments before it
    # reads; this one reads Python, and now does too.
    text = code_only(text)

The repair was made in `walks_own_root()` and NOT in the line that feeds
it. Half a fix, sitting beside its own explanation for two days - and the
half that was missed is the one that fires first.

So both greps strip comments now, with the helper each file already has.

THE RULE, WHICH IS THE SAME ONE AS THE FAVOURITES TAG THIS MORNING: a gate
reads CODE, not the record of code. Every instrument in this repo that
looks for a name has to decide whether a comment naming it counts, and the
answer has been no every single time.

Backups: .bak_mealrow, the same suffix as parts 1 and 2.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealrow'
ROOT = os.getcwd()

TARGETS = ('test_tree_roots.py', 'test_waiting_down.py')
OLD = "and 'os.walk(' in read(os.path.join(ROOT, n))]"


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
            raise SystemExit('ML1G: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ML1G: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('ML-1 PART 3 - THE os.walk GREP READS CODE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

NEW = ("""and 'os.walk(' in code_only(read(os.path.join(ROOT, n)))]
# CODE, NOT PROSE - ML-1, 2 Oct 2026, and the SECOND half of a repair made
# on 30 Sep. The line above used to read the whole file, comments
# included, so a comment that NAMED os.walk was indistinguishable from a
# call to it. That was fixed in walks_own_root() and not here, in the line
# that feeds it - and ML-1 tripped it by writing a note in test_js_escape
# explaining why that suite no longer calls os.walk. The note quoted the
# call; the grep believed it.""")

for label in TARGETS:
    p = os.path.join(ROOT, label)
    t, raw, crlf = read(p)
    if 'ML-1, 2 Oct 2026, and the SECOND half' in t:
        print('  %-24s already reads code' % label)
        continue
    if 'def code_only' not in t:
        raise SystemExit('ML1G: %s has no code_only() to use' % label)
    t = swap(t, OLD, NEW, 'the walking-suite grep in %s' % label, crlf)
    if not CHECK:
        back_up(p, raw)
        write(p, t, crlf)
    print('  %-24s the grep strips comments now' % label)

print('-' * 74)

if CHECK:
    print('  --check: nothing written')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
for label in TARGETS:
    t = read(os.path.join(ROOT, label))[0]
    try:
        ast.parse(t)
    except SyntaxError as e:
        raise SystemExit('ML1G: %s no longer parses: %s' % (label, e))
    if OLD in t:
        raise SystemExit('ML1G: %s still greps the raw file' % label)
    if "'os.walk(' in code_only(read(" not in t:
        raise SystemExit('ML1G: %s does not use code_only here' % label)
print('  both files parse, and both greps go through code_only')

# NO RAW GREP FOR os.walk SURVIVES ANYWHERE IN EITHER FILE.
for label in TARGETS:
    t = read(os.path.join(ROOT, label))[0]
    for m in re.finditer(r"'os\.walk\('\s*in\s+(\w+)\(", t):
        if m.group(1) != 'code_only':
            raise SystemExit('ML1G: %s greps os.walk through %s(), not '
                             'code_only' % (label, m.group(1)))
print('  and neither file has a raw one left')

# BOTH SUITES PASS, AND THE WALKING COUNT WENT DOWN BY THE ONE THAT WAS
# NEVER WALKING.
import subprocess
for label in TARGETS:
    r = subprocess.run([sys.executable, label], capture_output=True,
                       text=True, cwd=ROOT, timeout=600)
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:4]
        raise SystemExit('ML1G: %s fails:\n   %s'
                         % (label, '\n   '.join(bad or [r.stderr[-300:]])))
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    print('  %-24s%s' % (label, tail[-1] if tail else ' rc 0'))

# AND THE PREMISE: test_js_escape really does NAME os.walk in prose and
# really does not CALL it. Asked of the parse tree, which is the only
# instrument that can tell those apart.
js = read(os.path.join(ROOT, 'test_js_escape.py'))[0]
calls = [n for n in ast.walk(ast.parse(js))
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == 'walk' and isinstance(n.func.value, ast.Name)
         and n.func.value.id == 'os']
if calls:
    raise SystemExit('ML1G: test_js_escape CALLS os.walk at line %d'
                     % calls[0].lineno)
if 'os.walk(' not in js:
    raise SystemExit('ML1G: test_js_escape does not mention os.walk at all '
                     '- the premise of this part is wrong')
print('  test_js_escape NAMES os.walk in prose %d time(s) and CALLS it 0'
      % js.count('os.walk('))

print('-' * 74)
print('  A gate reads code, not the record of code. That is twice today.')
print('=' * 74)
