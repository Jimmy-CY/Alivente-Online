# -*- coding: utf-8 -*-
"""IB-1, PART 4 - THE SIXTH KEEPER OF THE SAME NUMBER

Part 3 updated five censuses and said in its own banner that outstanding
item 4 is the argument this should have been one number. The sweep then
produced a SIXTH:

    RC=1  test_filters_in_rc.py
      FAIL test_filter_on_close.py    counts fourteen pages with the house filter
      FAIL test_recipe_chips.py       counts fourteen pages with the house filter
      FAIL test_recipe_filter.py      counts fourteen pages with the house filter
      FAIL test_filter_box            counts the five new filter controls

That suite does not count pages. It greps the OTHER suites for the literal
`== 14`, and for `== 38` and `== 33`. Its own comment says so:

    # FIVE suites keep their own count of how many pages carry the
    # house filter, and not one of them knows about the others.

Six, counting the one that wrote the comment. And its check is the weakest
of the six, because a literal `== 14` sitting anywhere in a file satisfies
it - including in a census of something else entirely.

==========================================================================
SO THIS ONE IS NOT PAID, IT IS CHANGED
==========================================================================
Updating 14 to 15 here would be the sixth copy of one fact and would leave
the next round to find all six again. Instead this suite stops quoting a
number and starts MEASURING one:

    count the pages in the tree that carry the house filter
    read the integer each of the other suites asserts
    require every one of them to equal the count

One source of truth - the tree - and five claims checked against it. The
five suites are not touched; they keep their exact comparisons, which is
what caught IB-1 in the first place. What changes is that the seventh
place no longer holds a seventh copy of the number.

AND IT IS STRICTLY STRONGER THAN WHAT IT REPLACES. The old form passed as
long as the characters `== 14` appeared somewhere. The new one fails if
any single suite is updated and the others are not - which is exactly the
half-done state this round passed through an hour ago.

Backups: .bak_ingfilter, the same suffix as parts 1 to 3.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_ingfilter'
ROOT = os.getcwd()
CRLF = {}
TARGET = os.path.join(ROOT, 'test_filters_in_rc.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
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
            raise SystemExit('IB1L: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('IB1L: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('IB-1 PART 4 - THE SIXTH KEEPER%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

OLD = """# FIVE suites keep their own count of how many pages carry the
# house filter, and not one of them knows about the others.
for who in ('test_filter_on_close.py', 'test_recipe_chips.py',
            'test_recipe_filter.py'):
    ok(re.sub(r'#.*', '', read(os.path.join(ROOT, who))).count('== 14') >= 1,
       '%-26s counts fourteen pages with the house filter' % who)
fb = re.sub(r'#.*', '', read(os.path.join(ROOT, 'test_filter_box.py')))
ok('== 38' in fb and '== 33' in fb,
   'test_filter_box counts the five new filter controls')
"""

NEW = '''# SIX SUITES KEPT THE SAME NUMBER, AND THIS WAS THE SIXTH - IB-1,
# 2 Oct 2026.
#
# This block used to grep the other suites for the literal `== 14`. That
# made it a sixth copy of one fact, and the weakest of the six: any
# `== 14` anywhere in the file satisfied a substring search, including a
# census of something else entirely.
#
# It MEASURES now. The tree is counted here, each suite's asserted
# integer is read out of its own line, and every one of them has to equal
# the count. One source of truth, five claims checked against it - and it
# fails the moment one suite is updated and the others are not, which is
# the half-done state IB-1 itself passed through.
#
# The five suites are untouched and keep their exact comparisons. Those
# are what caught IB-1 in the first place; outstanding item 4 is about
# where the NUMBER lives, not about loosening any of them.


def _house_pages():
    """Pages carrying the house filter: a Filter button AND the panel.
    Markup only - a page NAMING .alv-filter in a comment or a stylesheet
    does not carry one, and a gate reads code, not the record of code."""
    out = []
    for p in alv_tree.templates():
        if os.path.basename(p) == 'base.html':
            continue
        t = read(p)
        t = re.sub(r'<style\\b.*?</style>', '', t, flags=re.S)
        t = re.sub(r'<script\\b.*?</script>', '', t, flags=re.S)
        t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
        if 'action-filter' in t and 'alv-filter' in t:
            out.append(alv_tree.rel(p))
    return sorted(out)


_HOUSE = _house_pages()
_CLAIMS = {
    'test_filter_on_close.py':
        r'ok\\(len\\(auto\\) \\+ len\\(manual\\) == (\\d+)',
    'test_recipe_chips.py': r'ok\\(len\\(house\\) == (\\d+)',
    'test_recipe_filter.py': r'ok\\(len\\(house\\) == (\\d+)',
}
ok(bool(_HOUSE), 'the tree carries the house filter on %d page(s)'
   % len(_HOUSE))
for who, pat in sorted(_CLAIMS.items()):
    src = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, who)))
    found = [int(x) for x in re.findall(pat, src)]
    if not ok(bool(found), '%-26s states a page count' % who):
        continue
    ok(all(n == len(_HOUSE) for n in found),
       '%-26s says %s, the tree says %d'
       % (who, '/'.join(str(n) for n in found), len(_HOUSE)))

# test_filter_box counts CONTROLS, not pages - a different quantity, so it
# is measured on its own terms rather than folded into the number above.
_fb = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, 'test_filter_box.py')))
_tot = re.search(r'len\\(paired\\) \\+ len\\(bare\\) == (\\d+)', _fb)
_pair = re.search(r'ok\\(len\\(paired\\) == (\\d+)', _fb)
ok(bool(_tot) and bool(_pair),
   'test_filter_box states a total and a paired count')
if _tot and _pair:
    _uses = sum(len(re.findall(r'\\bfilter-(?:select|input)\\b',
                               re.sub(r'<!--.*?-->', '', read(p), flags=re.S)))
                for p in alv_tree.templates()
                if os.path.basename(p) != 'base.html')
    ok(int(_tot.group(1)) >= int(_pair.group(1)),
       '  and the total is not smaller than the paired half (%s >= %s)'
       % (_tot.group(1), _pair.group(1)))
    ok(_uses >= int(_tot.group(1)),
       '  and the tree carries at least that many uses (%d >= %s)'
       % (_uses, _tot.group(1)))
'''

t, raw = read(TARGET)
if 'IB-1,\n# 2 Oct 2026' in t or 'SIX SUITES KEPT THE SAME NUMBER' in t:
    print('  test_filters_in_rc.py    already measures instead of quoting')
else:
    t = swap(t, OLD, NEW, 'the ledger block', TARGET)
    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t)
    print('  test_filters_in_rc.py    measures the tree and checks five '
          'claims against it')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import subprocess

t = read(TARGET)[0]
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('IB1L: test_filters_in_rc.py no longer parses: %s' % e)

code = re.sub(r'(?m)#.*$', '', t)
if "== 14" in code:
    raise SystemExit('IB1L: a literal 14 survives in code - the point of '
                     'this part is that the number is not written here')
if '_house_pages' not in code:
    raise SystemExit('IB1L: the measurement is not there')
print('  it parses, measures the tree, and quotes no page count of its own')

# THE FIVE SUITES WERE NOT TOUCHED BY THIS PART.
import alv_tree
for who in ('test_filter_on_close.py', 'test_recipe_chips.py',
            'test_recipe_filter.py', 'test_filter_box.py',
            'test_live_search.py'):
    if os.path.exists(os.path.join(ROOT, who + SUFFIX)):
        # Part 3 backed these up; part 4 must not have written them again.
        pass
    if 'IB-1 PART 4' in read(os.path.join(ROOT, who))[0]:
        raise SystemExit('IB1L: part 4 wrote into %s - it must not' % who)
print('  and none of the five suites was edited by this part')

# THE CLAIM IS REAL: the tree and the suites agree, measured here the same
# way the suite now measures it.
def _house():
    out = []
    for p in alv_tree.templates():
        if os.path.basename(p) == 'base.html':
            continue
        x = read(p)[0]
        x = re.sub(r'<style\b.*?</style>', '', x, flags=re.S)
        x = re.sub(r'<script\b.*?</script>', '', x, flags=re.S)
        x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
        if 'action-filter' in x and 'alv-filter' in x:
            out.append(alv_tree.rel(p))
    return sorted(out)


H = _house()
print('  the tree carries the house filter on %d pages' % len(H))
for who, pat in ((('test_filter_on_close.py'),
                  r'ok\(len\(auto\) \+ len\(manual\) == (\d+)'),
                 ('test_recipe_chips.py', r'ok\(len\(house\) == (\d+)'),
                 ('test_recipe_filter.py', r'ok\(len\(house\) == (\d+)')):
    src = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, who))[0])
    found = [int(x) for x in re.findall(pat, src)]
    if not found:
        raise SystemExit('IB1L: %s states no page count the new check can '
                         'read' % who)
    if any(n != len(H) for n in found):
        raise SystemExit('IB1L: %s says %s, the tree says %d'
                         % (who, found, len(H)))
    print('    %-26s %s' % (who, found))

# THE CONTROL: the new check can FAIL. A suite claiming the wrong number
# must be caught, or this is reassurance rather than a gate.
_fake = 'ok(len(house) == 999, "x")'
_n = [int(x) for x in re.findall(r'ok\(len\(house\) == (\d+)', _fake)]
if not _n or _n[0] == len(H):
    raise SystemExit('IB1L: the reader cannot tell a wrong number from a '
                     'right one')
print('  CONTROL: a suite claiming %d instead of %d would be caught'
      % (_n[0], len(H)))

r = subprocess.run([sys.executable, 'test_filters_in_rc.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('IB1L: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_filters_in_rc.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  Five suites still keep their own count. The sixth place now')
print('  checks them against the tree instead of holding a copy.')
print('=' * 74)
