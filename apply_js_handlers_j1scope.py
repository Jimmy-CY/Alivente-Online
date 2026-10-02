# -*- coding: utf-8 -*-
"""J-2, PART 4 - J-1'S TWO OLDEST CHECKS GET THE SCOPE GUARD IT ALREADY HAD

J-2 removed twelve onclick attributes from recipe_management.html, and six
of them carried `{{ recipe.recipe_name|escapejs }}` with `{{ recipe.recipe_id }}`
beside it as a bare argument. So the tree now holds six fewer |escapejs and
six fewer bare arguments than it did yesterday - and test_js_escape.py
failed:

    FAIL  and 186 are |escapejs now, against 45 before    186, expected 192
    FAIL  and the 105 BARE arguments are left alone       105

NEITHER IS A COMPLAINT ABOUT J-2. Both are J-1's suite measuring the LIVE
TREE and pinning the answer as if it were a fact about J-1. It is not: it
is a fact about today, and every round that lands afterwards moves it.

THE HELPER WAS ALREADY THERE, which is the part worth writing down.
test_js_escape.py defines, at line 431:

    def left_by_j1(path):
        return as_left_by(path, SUFFIX, read) if as_left_by else read(path)

with a note above it saying, in J-1's own words, that this is "the SAME
defect this very round repaired in test_filter_on_close.py, written into a
new check hours after diagnosing it there". J-1 found the bug, named it,
built the cure - and applied it only to the checks it wrote LAST. Its two
oldest checks, in section 1 and section 5, kept reading the live file.

So this round does not invent anything. It moves the helper above the first
check that needs it and uses it in the two places that were missed:

    section 1  the tree-wide census of protected and unprotected values
    section 5  the count of bare arguments left alone
    section 5  the scan for risky confirm() handlers
    section 5  the scan for |escapejs used before another filter

Two of those four were failing today. The other two were found by the gate
at the bottom of this file, which asks the question of EVERY loop over the
tree rather than of the two that happened to break - because a check that
has not failed yet is not a check that is right.

Both counts go back to 192 and 111 - the numbers J-1 actually left - and
stay there however many rounds land on those templates afterwards.

THE LESSON, STATED ONCE MORE BECAUSE IT HAS NOW COST FOUR ROUNDS. A scope
or recency claim must be measured against the state it names. Not "today",
and not "the live file" - the state. as_left_by() is how, and a suite that
defines it and then does not use it everywhere has the hardest version of
the bug, because the fix is sitting in the same file as the fault.

Backups: .bak_jshandlers, the same suffix as parts 1 to 3.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_jshandlers'
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
            raise SystemExit('J2S: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('J2S: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('J-2 PART 4 - J-1 SCOPE GUARD%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

HELPER_OLD = '''def left_by_j1(path):
    return as_left_by(path, SUFFIX, read) if as_left_by else read(path)
'''

t, raw, crlf = read(TARGET)

if 'left_by_j1(p))' in t and t.index('def left_by_j1') < t.index(
        "head('1. THE GATE"):
    print('  test_js_escape.py        already scope-guarded')
else:
    # 1. MOVE THE HELPER ABOVE THE FIRST CHECK THAT NEEDS IT. Its note
    #    stays where it is, with a line saying where the function went -
    #    a note that describes a function three hundred lines away is a
    #    note the next reader cannot use.
    if t.count(HELPER_OLD) != 1:
        raise SystemExit('J2S: left_by_j1 is not where it was')
    t = t.replace(HELPER_OLD,
                  '''# left_by_j1() WAS DEFINED HERE and is now defined above section 1,
# because section 1 needs it too - see the note there. J-2, 2 Oct 2026.
''')

    t = swap(t, '''print('=' * 74)
print("%s - J-1, A NAME WITH AN APOSTROPHE IN IT" % ME)
print('=' * 74)''',
             '''# THE SCOPE GUARD, HOISTED - J-2, 2 Oct 2026.
#
# This was defined three hundred lines below, after the checks that were
# written last, and it was used only by them. The two OLDEST checks in this
# suite - the census in section 1 and the bare-argument count in section 5 -
# read the live file instead, and pinned tree-wide totals taken from it.
#
# So the day J-2 removed twelve onclick attributes from recipe_management,
# six of which carried |escapejs with a bare id beside it, both counts moved
# and this suite failed - complaining about a later round for doing exactly
# what it was supposed to do.
#
# The note that used to sit above this function said it already: J-1 found
# this defect in test_filter_on_close.py, repaired it there, and wrote it
# into its own new checks hours later. What it did not do was apply the cure
# to the checks it had written first. A suite that defines as_left_by() and
# then does not use it everywhere has the hardest version of the bug - the
# fix is in the same file as the fault.
def left_by_j1(path):
    """The file as J-1 LEFT it. as_left_by() walks forward to the next
    backup, so the claim stays about J-1 however many rounds land on the
    file afterwards."""
    return as_left_by(path, SUFFIX, read) if as_left_by else read(path)


print('=' * 74)
print("%s - J-1, A NAME WITH AN APOSTROPHE IN IT" % ME)
print('=' * 74)''', 'the head of the suite', crlf)

    # 2. SECTION 1 - the tree-wide census.
    t = swap(t, '''for rel, p in sorted(PATHS.items()):
    b, s = census(read(p))''',
             '''for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - this is J-1's census and it must stay J-1's.
    b, s = census(left_by_j1(p))''',
             'the section 1 census', crlf)

    # 3. TWO MORE LOOPS, found by the gate below rather than by reading -
    #    the risky-handler scan and the filter-order scan. Four checks in
    #    all were reading the live file, not two, which is why the gate
    #    asks the question of EVERY loop over the tree instead of the two
    #    that happened to fail today.
    t = swap(t, """now_risky = []
for rel, p in sorted(PATHS.items()):
    t = HTML_C.sub('', read(p))""",
             """now_risky = []
for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - same reason as section 1.
    t = HTML_C.sub('', left_by_j1(p))""",
             'the risky-handler scan', crlf)

    t = swap(t, """mid = []
for rel, p in sorted(PATHS.items()):
    for h in HANDLER.finditer(HTML_C.sub('', read(p))):""",
             """mid = []
for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - same reason as section 1.
    for h in HANDLER.finditer(HTML_C.sub('', left_by_j1(p))):""",
             'the filter-order scan', crlf)

    # 4. SECTION 5 - the bare-argument count.
    t = swap(t, '''bare_n = 0
for rel, p in sorted(PATHS.items()):
    t = HTML_C.sub('', read(p))''',
             '''bare_n = 0
for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - same reason as section 1.
    t = HTML_C.sub('', left_by_j1(p))''',
             'the section 5 bare count', crlf)

    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t, crlf)
    print('  test_js_escape.py        helper hoisted, 4 checks scope-guarded')

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
    raise SystemExit('J2S: test_js_escape.py no longer parses: %s' % e)
print('  the suite still parses')

if t.index('def left_by_j1') > t.index("head('1. THE GATE"):
    raise SystemExit('J2S: the helper is still defined below section 1')
if t.count('def left_by_j1') != 1:
    raise SystemExit('J2S: left_by_j1 is defined %d times'
                     % t.count('def left_by_j1'))
print('  left_by_j1 is defined once, above the first check that uses it')

# NOT ONE CENSUS LOOP STILL READS THE LIVE FILE. This is the claim, so it
# is made properly: every `census(` and every `HTML_C.sub` in a loop over
# PATHS must take left_by_j1.
bad = []
for m in re.finditer(r'for rel, p in sorted\(PATHS\.items\(\)\):(.{0,260})',
                     t, re.S):
    seg = m.group(1)
    for call in re.finditer(r'\b(?:census|HTML_C\.sub)\([^\n]*', seg):
        s = call.group(0)
        if 'left_by_j1(' not in s and 'was(' not in s:
            bad.append(s.strip()[:70])
if bad:
    raise SystemExit('J2S: %d loop(s) over the tree still read the live '
                     'file:\n   %s' % (len(bad), '\n   '.join(bad[:6])))
print('  and no loop over the tree reads the live file any more')

# THE SUITE PASSES, AND ITS TWO TOTALS ARE BACK TO WHAT J-1 LEFT.
import subprocess
r = subprocess.run([sys.executable, 'test_js_escape.py'],
                   capture_output=True, text=True, cwd=ROOT)
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('J2S: test_js_escape.py still fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
out = r.stdout
m = re.search(r'and (\d+) are \|escapejs now', out)
n = re.search(r'and the (\d+) BARE arguments', out)
if not m or m.group(1) != '192':
    raise SystemExit('J2S: the escapejs total is %s, expected 192'
                     % (m.group(1) if m else '?'))
if not n or n.group(1) != '111':
    raise SystemExit('J2S: the bare total is %s, expected 111'
                     % (n.group(1) if n else '?'))
tail = [ln for ln in out.split('\n') if 'passed' in ln]
print('  the two totals are back to 192 and 111 - what J-1 left')
print('  and the suite passes -%s' % (tail[-1] if tail else ' rc 0'))

# AND THE PREMISE IS ASSERTED, NOT ASSUMED: recipe_management really did
# lose exactly six |escapejs and six bare ids to J-2, which is the whole
# reason those two totals moved.
#
# THE FIRST DRAFT OF THIS GATE COUNTED THE WRONG THING - a raw
# `.count('|escapejs')` across every template, which came back 261 against
# J-1's 192 and declared the premise wrong. They are different instruments:
# J-1's census counts interpolations INSIDE A JS STRING LITERAL IN A
# HANDLER, and a raw count sees every |escapejs anywhere, script blocks and
# data attributes included. Comparing two instruments and believing the
# difference is the same mistake as reading the live file. Counted on one
# file, with one instrument, both sides.
import alv_tree
rm = os.path.join(ROOT, 'pages', 'templates', 'recipe_management.html')
a = read(rm)[0]
b = read(rm + SUFFIX)[0]
d_esc = b.count('|escapejs') - a.count('|escapejs')
d_bare = (len(re.findall(r'Recipe\(\{\{ recipe\.recipe_id \}\}', b))
          - len(re.findall(r'Recipe\(\{\{ recipe\.recipe_id \}\}', a)))
if d_esc != 6:
    raise SystemExit('J2S: recipe_management lost %d |escapejs to J-2, '
                     'expected 6' % d_esc)
if d_bare != 6:
    raise SystemExit('J2S: recipe_management lost %d bare ids to J-2, '
                     'expected 6' % d_bare)
print('  and recipe_management really did lose 6 |escapejs and 6 bare ids')
print('  to J-2 - which is exactly why those two totals had moved')

print('-' * 74)
print('=' * 74)
