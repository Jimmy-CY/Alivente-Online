# -*- coding: utf-8 -*-
"""SECTION P, ROUND P4 - THE FILTER FIELD'S MISSING LINE

ALV FILTER FIELD v1 says, in its own comment, what it is for:

    HEIGHT, not min-height. 44 on the desk and 44 on the phone, so the
    control is the same size everywhere

It sets height: 44px and does not set box-sizing. In the browser's
default content-box that 44 is the CONTENT, and the component's own
padding and border are added to it:

    44 + 10 + 10 + 2 + 2  =  68

MEASURED TODAY, in Chromium, at 1280 and at 390:

    .filter-input, alone                        68px      68px
    .filter-input beside .form-control          44px      44px
    .filter-select, alone                       44px      44px

THE SELECT WAS NEVER WRONG, AND THAT IS WHY NOBODY SAW THIS. The browser's
own stylesheet gives a <select> border-box; it gives a text <input>
content-box. So the same rule, on the same two class names, produced the
right height on one element and 68 on the other - and twenty-five of the
thirty uses also carry .form-control, which Bootstrap makes border-box,
covering the difference everywhere it appears.

Five uses do not pair the class. Three are selects and are already 44.
The other two are text inputs, and they are 68px today: one on
unit_conversions_management, and the search box P1 put on Celebration
Management this afternoon - which is how this was found.

    box-sizing: border-box;

is the whole round. For the twenty-five it changes nothing. For the three
bare selects it changes nothing, because the browser had already decided
it. For the two inputs it is the difference between 68 and the 44 the
component promised.

WHY IN BASE AND NOT ON THE PAGE. A component that needs a second class to
be the right height is not a component - it is a rule and a convention,
and the convention is what broke. The whole point of FILTER FIELD v1 was
that ten pages had drifted to four different heights.

Backups: .bak_filterbox. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filterbox'
PAGE = 'base.html'
CRLF = {}

WAS = """.filter-select,
.filter-input {
  position: relative;
  z-index: 10;
  width: 100%;
  height: 44px;"""

NOW = """.filter-select,
.filter-input {
  position: relative;
  z-index: 10;
  width: 100%;
  /* BORDER-BOX, ADDED 29 SEP 2026, AND THE REASON IS ABOVE THIS BLOCK.
     height: 44px in the browser's default content-box means 44 of
     CONTENT, and this component's own 10px padding and 2px border are
     then added to it: 68.

     IT HID BEHIND TWO THINGS AT ONCE. The browser's own sheet gives a
     <select> border-box and a text <input> content-box, so the same rule
     was right on one element and 68 on the other; and 25 of the 30 uses
     also carry .form-control, which Bootstrap makes border-box, covering
     the difference wherever it appears. Two bare text inputs were left,
     and both measured 68 today.
                                                [test_filter_box.py] */
  box-sizing: border-box;
  height: 44px;"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('P4: %s is not a byte copy' % bak)


print('=' * 74)
print('SECTION P, ROUND P4 - THE FILTER FIELD\'S MISSING LINE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

# THE CENSUS, so the round says who it is for before it changes anything.
bare, paired = [], []
for p in alv_tree.templates():
    t = open(p, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'class="([^"]*\bfilter-(?:input|select)\b[^"]*)"',
                         t):
        (paired if 'form-control' in m.group(1) else bare).append(
            '%s  %s' % (alv_tree.rel(p), m.group(1)))
inputs = [b for b in bare if 'filter-input' in b]
print('  %d use(s) pair the class with .form-control - border-box already'
      % len(paired))
print('  %d do NOT. Of those, %d are selects, which the BROWSER already'
      % (len(bare), len(bare) - len(inputs)))
print('  makes border-box, and %d are text inputs, which it does not:'
      % len(inputs))
for b in bare:
    print('     %-50s %s' % (b, '<- 68px today'
                             if 'filter-input' in b else 'already 44'))

if 'box-sizing: border-box;\n  height: 44px;' in text:
    print('  base already has the line')
else:
    a = eol(path, WAS)
    if text.count(a) != 1:
        raise SystemExit('P4: the filter field block is there %d time(s), '
                         'not 1' % text.count(a))
    text = text.replace(a, eol(path, NOW), 1)
    if text.count('box-sizing: border-box') < 2:
        raise SystemExit('P4: the line did not land')
    print('  box-sizing: border-box added to .filter-select, .filter-input')
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  nothing moves but the %d bare text input(s), which become the 44'
      % len(inputs))
print('  the component has promised since it was written.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
