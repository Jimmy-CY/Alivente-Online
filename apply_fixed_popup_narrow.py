# -*- coding: utf-8 -*-
"""PU-1, PART 2 - "NARROW QUERIES" THAT WERE NOT QUERIES

The 225-suite sweep failed test_print_leaks.py on both pages PU-1 touched:

    FAIL categories_management.html        its narrow queries are untouched
                                           [280] vs []
    FAIL measurement_units_management.html  the same

280 is not a query. It is

    .ingredient-popup { max-width: 280px; }

a PROPERTY on the popup, which PU-1 moved into base with the rest of the
component. The suite's own comment says what it means to check:

    # A bare query BELOW the page box is correct and must be left alone.

and then matches `max-width\\s*:\\s*(\\d+)px` anywhere in the stylesheet, so
every max-width PROPERTY in the tree has been counted as a media query
since the print round was written.

==========================================================================
THE SAME DEFECT AS SIX OTHERS THIS WEEK, IN A SEVENTH PLACE
==========================================================================
An instrument matching a SUBSTRING where it means a specific construct:

    \\bbtn-primary\\b                matched inside modal-btn-primary
    'os.walk(' in read(...)        matched a comment saying os.walk
    .filter-bar in a CSS comment   matched the note saying it was removed
    s.split()[0] on a class list   read "alv-pill ..." as "alv-pill"
    'renewal' in a filename        matched a suite about COLOURS
    max-width: Npx anywhere        matches a property, not a query

The repair is the same every time: ask for the construct. A media query's
condition lives inside `@media ( ... )`, so that is where it is read from.

IT IS SYMMETRIC, so nothing is loosened: the same instrument runs on the
before and the after, and the claim stays `was == now`. What changes is
that a page moving a width PROPERTY no longer reads as a page moving a
breakpoint.

Backups: .bak_fixedpop, the same suffix as part 1.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_fixedpop'
ROOT = os.getcwd()
CRLF = {}
TARGET = os.path.join(ROOT, 'test_print_leaks.py')


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
            raise SystemExit('PU1N: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PU1N: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('PU-1 PART 2 - A QUERY IS NOT A PROPERTY%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TARGET)

OLD = """    def _narrow_of(c):
        return sorted(int(x.group(1)) for x in
                      re.finditer(r'max-width\\s*:\\s*(\\d+)px', c, re.I)
                      if int(x.group(1)) < PAPER)
"""

NEW = """    def _narrow_of(c):
        # A QUERY, NOT A PROPERTY - PU-1 part 2, 2 Oct 2026.
        #
        # This used to match `max-width\\s*:\\s*(\\d+)px` anywhere in the
        # stylesheet, so every max-width PROPERTY in the tree counted as a
        # media query. PU-1 moved a popup's `max-width: 280px` into base
        # with the rest of the component and this reported two pages as
        # having lost a breakpoint.
        #
        # The check's own comment says what it means - "a bare query BELOW
        # the page box" - so the condition is read from inside @media,
        # where a condition lives. SYMMETRIC: the same instrument runs on
        # the before and the after, so nothing is loosened.
        out = []
        for q in re.finditer(r'@media([^{]*)\\{', c, re.I):
            for m in re.finditer(r'max-width\\s*:\\s*(\\d+)px', q.group(1),
                                 re.I):
                if int(m.group(1)) < PAPER:
                    out.append(int(m.group(1)))
        return sorted(out)
"""

if 'A QUERY, NOT A PROPERTY' in t:
    print('  test_print_leaks.py      already reads @media conditions')
else:
    t = swap(t, OLD, NEW, 'the narrow-query reader', TARGET)
    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t)
    print('  test_print_leaks.py      reads the condition inside @media, '
          'not every max-width')

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
    raise SystemExit('PU1N: test_print_leaks.py no longer parses: %s' % e)
if re.search(r"(?m)^\s*re\.finditer\(r'max-width", t):
    raise SystemExit('PU1N: a bare max-width scan survives at top level')
if '@media([^{]*)' not in t:
    raise SystemExit('PU1N: the reader does not go through @media')
print('  it parses and reads conditions from inside @media')

# THE INSTRUMENT, ON FIXTURES. A property is not counted; a query is; and
# the two together give one answer, not two.
PAPER = 900
def _narrow_of(c):
    out = []
    for q in re.finditer(r'@media([^{]*)\{', c, re.I):
        for m in re.finditer(r'max-width\s*:\s*(\d+)px', q.group(1), re.I):
            if int(m.group(1)) < PAPER:
                out.append(int(m.group(1)))
    return sorted(out)


CASES = [
    ('.alv-pop { max-width: 280px; }', [],
     'a width PROPERTY is not a query - this is the whole bug'),
    ('@media screen and (max-width: 768px) { .x { color: red } }', [768],
     'a real query is counted'),
    ('@media (max-width: 768px) { .x { max-width: 280px } }', [768],
     'and a property INSIDE a query does not double it'),
    ('@media print { .x { max-width: 280px } }', [],
     'a print query has no max-width condition'),
    ('@media (max-width: 1200px) { .x { color: red } }', [],
     'a query above the page box is left out, as before'),
]
for css, want, why in CASES:
    got = _narrow_of(css)
    if got != want:
        raise SystemExit('PU1N: %r -> %s, expected %s  (%s)'
                         % (css[:48], got, want, why))
    print('    %-28s -> %-8s %s' % (css[:28], got, why))

# AND THE OLD READER REALLY DID GET THE FIRST CASE WRONG - or this part is
# fixing something that was not broken.
old = sorted(int(x.group(1)) for x in
             re.finditer(r'max-width\s*:\s*(\d+)px', CASES[0][0], re.I)
             if int(x.group(1)) < PAPER)
if old != [280]:
    raise SystemExit('PU1N: the old reader did NOT count the property - the '
                     'premise of this part is wrong')
print('  CONTROL: the old reader counted that property as a query (%s)'
      % old)

r = subprocess.run([sys.executable, 'test_print_leaks.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln or
        re.search(r'^\s*\d+ of \d+', ln)]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('PU1N: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_print_leaks.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  Seventh time this week: ask for the construct, not the substring.')
print('=' * 74)
