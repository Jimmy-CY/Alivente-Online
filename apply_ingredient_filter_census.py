# -*- coding: utf-8 -*-
"""IB-1, PART 3 - FIVE CENSUSES AND ONE REAL FINDING

The 223-suite sweep came back with six failures, all of them IB-1's doing
and all of them correct:

    test_filter_box.py        38 class uses -> 39, 33 paired -> 34
    test_filter_on_close.py   14 pages carry the house filter -> 15
    test_recipe_chips.py      14 wear it -> 15, and 14 chip rows -> 15
    test_recipe_filter.py     14 have a Filter button -> 15
    test_live_search.py       a CANDIDATE was opted in and must leave
    test_filter_distinct.py   a select came INTO scope - see below

FIVE SUITES EACH KEEP THEIR OWN COUNT OF THE SAME SET. That is written
down as outstanding item 4 and this round does not fix it; it pays the
toll again, which is exactly the argument for fixing it. A page joining
the house filter should touch ONE number.

THE COUNTS ARE EXACT ON PURPOSE AND STAY EXACT. Every one of these could
be >= and none of them is: the census exists so the set cannot change in
silence, which is the only reason the sweep caught this round at all.

==========================================================================
THE ONE THAT IS NOT A COUNT
==========================================================================
    test_filter_distinct.py
      every filter select that loops lists CHOICES, not rows
        [('ingredient_base_units_management.html', 'categoryFilter',
          'categories', 'cat.ingredient_category_id')]

F3's rule: a filter dropdown must list one option per CHOICE, never one
per row. The Category select loops `categories` and sends
`cat.ingredient_category_id`.

IT DID THAT BEFORE THIS ROUND TOO. What changed is that F3's detector only
looks at selects it can recognise as filter selects, and the old markup
carried `class="form-control"` inside a bespoke `.filter-bar`. Joining the
house panel put it in scope for the first time - a rule reaching a page it
was always meant to cover, which is what a shared component is FOR.

And the answer is the one F3 already gave twice: IT SENDS AN ID. Two
categories with the same name are two different categories, and the view
filters on `category__ingredient_category_id`, so an option per row IS an
option per choice here. Same ruling as Actual Expenses' and Projects'
Property dropdowns, named in the same table with the same sentence.

Backups: .bak_ingfilter, the same suffix as parts 1 and 2.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_ingfilter'
ROOT = os.getcwd()
CRLF = {}
PAGE = 'ingredient_base_units_management.html'


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
            raise SystemExit('IB1C: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('IB1C: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


NOTE = '# FIFTEEN SINCE IB-1, 2 Oct 2026 - Ingredient Shopping Units.\n'

EDITS = [
    ('test_filter_box.py', 'IB-1, 2 Oct 2026', [
        ("""ok(len(paired) + len(bare) == 38,
   'thirty-eight uses of the two class names across the tree',""",
         """# 39 SINCE IB-1, 2 Oct 2026. Ingredient Shopping Units joined the
# house panel and its Category select gained .filter-select.
ok(len(paired) + len(bare) == 39,
   'thirty-nine uses of the two class names across the tree',""",
         'the class-use census'),
        ("""ok(len(paired) == 33, '  thirty-three pair it with .form-control, and do '""",
         """ok(len(paired) == 34, '  thirty-four pair it with .form-control, and do '""",
         'the paired census'),
    ]),
    ('test_filter_on_close.py', 'IB-1, 2 Oct 2026', [
        ("""ok(len(auto) + len(manual) == 14, 'fourteen pages carry the house filter',""",
         """# FIFTEEN SINCE IB-1, 2 Oct 2026 - Ingredient Shopping Units.
ok(len(auto) + len(manual) == 15, 'fifteen pages carry the house filter',""",
         'the page census'),
    ]),
    ('test_recipe_chips.py', 'IB-1, 2 Oct 2026', [
        ("""ok(len(house) == 14, 'fourteen pages wear the house filter', len(house))""",
         """# FIFTEEN SINCE IB-1, 2 Oct 2026 - Ingredient Shopping Units, which
# arrived with its chip row in the same round, so both numbers move
# together. A page wearing the filter WITHOUT a chip row would leave
# base's badge reading zero for ever, and the gap below is what says so.
ok(len(house) == 15, 'fifteen pages wear the house filter', len(house))""",
         'the house census'),
        ("""ok(len(rows) == 14,
   'and TWELVE of twelve now put their chips on base\\'s row - the fourth '
   'copy was the last one', sorted(set(house) - set(rows)))""",
         """ok(len(rows) == 15,
   'and all fifteen put their chips on base\\'s row - no page keeps its own',
   sorted(set(house) - set(rows)))""",
         'the chip-row census'),
    ]),
    ('test_recipe_filter.py', 'IB-1, 2 Oct 2026', [
        ("""ok(len(house) == 14, 'fourteen pages have one, all the same', len(house))""",
         """# FIFTEEN SINCE IB-1, 2 Oct 2026 - Ingredient Shopping Units.
ok(len(house) == 15, 'fifteen pages have one, all the same', len(house))""",
         'the Filter-button census'),
    ]),
    ('test_live_search.py', 'IB-1, 2 Oct 2026', [
        ("""CANDIDATES = ('ingredient_base_units_management.html',
              'unit_conversions_management.html')""",
         """# ingredient_base_units_management LEFT THIS LIST - IB-1, 2 Oct 2026,
# which is the shape this comment already asks for: "A page leaving this
# list is a decision taken, and comes off it in the same round." The
# decision it needed was which column the server matches - name__icontains
# and nothing else - and IB-1's own suite re-asks the view rather than
# trusting the markup, so the answer cannot rot quietly.
#
# THE TRAILING COMMA IS LOAD-BEARING. Taking the first entry out left one
# string in brackets, which is a STRING and not a tuple, so the loop below
# iterated its characters and asked alv_tree for a template named 'u'. The
# suite crashed rather than failed - and a crash blocks a push exactly as
# hard as a failure while saying far less about why.
CANDIDATES = ('unit_conversions_management.html',)""",
         'the candidate list'),
        ("""OPTED_IN_BY_N3 = ('properties.html', 'fsr.html',
                  'tenant_lease_agreement.html', 'act_expense.html')""",
         """OPTED_IN_BY_N3 = ('properties.html', 'fsr.html',
                  'tenant_lease_agreement.html', 'act_expense.html')
# And one since, by a later round. Kept separate from N3's four so the
# claim stays true about WHO opted each page in.
OPTED_IN_SINCE = ('ingredient_base_units_management.html',)""",
         'the opted-in list'),
        ("""for rel in OPTED_IN_BY_N3:
    p = alv_tree.path_of(rel)
    ok('data-live-search' in read(p),
       '%-40s opted in by N3, 1 Oct' % rel)""",
         """for rel in OPTED_IN_BY_N3:
    p = alv_tree.path_of(rel)
    ok('data-live-search' in read(p),
       '%-40s opted in by N3, 1 Oct' % rel)
for rel in OPTED_IN_SINCE:
    p = alv_tree.path_of(rel)
    ok('data-live-search' in read(p),
       '%-40s opted in by IB-1, 2 Oct' % rel)""",
         'the opted-in loop'),
    ]),
    ('test_filter_distinct.py', 'IB-1, 2 Oct 2026', [
        ("""    ('projects/projects.html', 'propertySelect'):
        'sends prop_id - same reason',
}""",
         """    ('projects/projects.html', 'propertySelect'):
        'sends prop_id - same reason',
    # IB-1, 2 Oct 2026. Not a new select - a select that came INTO SCOPE.
    # It looped `categories` and sent an id before this round too; what
    # changed is that it now carries .filter-select inside a house panel,
    # so F3's detector can see it. A rule reaching a page it was always
    # meant to cover is what a shared component is for.
    #
    # And the ruling is the one above, twice over: IT SENDS AN ID. Two
    # categories with the same name are two different categories, and the
    # view filters on category__ingredient_category_id.
    ('ingredient_base_units_management.html', 'categoryFilter'):
        'sends ingredient_category_id - same reason',
}""",
         'the LEFT table'),
    ]),
]

print('=' * 74)
print('IB-1 PART 3 - FIVE CENSUSES AND ONE FINDING%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

for name, marker, edits in EDITS:
    p = os.path.join(ROOT, name)
    t, raw = read(p)
    if marker in t:
        print('  %-26s already updated' % name)
        continue
    for old, new, what in edits:
        t = swap(t, old, new, '%s in %s' % (what, name), p)
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    print('  %-26s %d edit(s)' % (name, len(edits)))

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

for name, _m, _e in EDITS:
    p = os.path.join(ROOT, name)
    try:
        ast.parse(read(p)[0])
    except SyntaxError as e:
        raise SystemExit('IB1C: %s no longer parses: %s' % (name, e))
print('  all %d suites still parse' % len(EDITS))

# THE PAGE IS REALLY IN EVERY SET IT IS NOW COUNTED IN. Asked of the
# template, not of the numbers - a census moved to match a page that does
# not qualify would pass its own suite and be wrong.
import alv_tree
tpl = read(alv_tree.path_of(PAGE))[0]
for frag, what in (('action-filter', 'a Filter button'),
                   ('alv-filter', 'the house panel'),
                   ('class="alv-filter-active"', 'the chip row'),
                   ('filter-select', 'a house filter select'),
                   ('data-live-search', 'the live search')):
    if frag not in tpl:
        raise SystemExit('IB1C: %s has no %s, so it does not belong in the '
                         'censuses this round moved' % (PAGE, what))
print('  and %s really does carry all five things it is now counted for'
      % PAGE)

# NO NUMBER WAS LOOSENED. Every census this round touched is still an
# EXACT comparison - the whole value of these suites is that >= would
# have let IB-1 through in silence.
loose = []
for name, _m, edits in EDITS:
    t = read(os.path.join(ROOT, name))[0]
    for _old, new, _w in edits:
        for ln in new.split('\n'):
            if re.search(r'\bok\(len\([^)]*\)\s*(>=|<=|>|<)\s*\d', ln):
                loose.append('%s: %s' % (name, ln.strip()[:70]))
if loose:
    raise SystemExit('IB1C: a census was loosened:\n   %s'
                     % '\n   '.join(loose))
print('  every census this round touched is still an EXACT count')

# AND EVERY LIST THIS ROUND EDITED IS STILL A TUPLE OF STRINGS. Taking an
# entry out of a two-element tuple leaves one string in brackets, which is
# a string - the loop over it then iterates CHARACTERS. That crashed
# test_live_search rather than failing it, and ast.parse had nothing to
# say about it, so the shape is asked for directly.
import importlib
for _m in ('test_live_search',):
    sys.modules.pop(_m, None)
_mod_src = read(os.path.join(ROOT, 'test_live_search.py'))[0]
for _name in ('CANDIDATES', 'OPTED_IN_BY_N3', 'OPTED_IN_SINCE'):
    _m2 = re.search(r'(?m)^%s = (\([\s\S]*?\))' % _name, _mod_src)
    if not _m2:
        raise SystemExit('IB1C: %s is not where this round left it' % _name)
    _val = ast.literal_eval(_m2.group(1))
    if not isinstance(_val, tuple):
        raise SystemExit('IB1C: %s is a %s, not a tuple - a one-entry tuple '
                         'needs its trailing comma'
                         % (_name, type(_val).__name__))
    if not all(isinstance(x, str) and x.endswith('.html') for x in _val):
        raise SystemExit('IB1C: %s holds something that is not a template '
                         'name: %r' % (_name, _val))
    print('    %-18s %d template name(s)' % (_name, len(_val)))

# AND THE SIX RUN GREEN.
bad = []
for name, _m, _e in EDITS:
    r = subprocess.run([sys.executable, name], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        f = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:3]
        bad.append('%s:\n     %s' % (name, '\n     '.join(f or ['rc %d'
                                                                % r.returncode])))
    print('  %-26s%s' % (name, tail[-1] if tail else ' rc %d' % r.returncode))
if bad:
    raise SystemExit('IB1C: %d suite(s) still fail:\n   %s'
                     % (len(bad), '\n   '.join(bad)))

print('-' * 74)
print('  Five suites, one set, five numbers. Outstanding item 4 is the')
print('  argument that this should have been one, and this is the toll.')
print('=' * 74)
