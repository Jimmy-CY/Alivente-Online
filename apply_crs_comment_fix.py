# -*- coding: utf-8 -*-
"""SECTION X, ROUND X12 - A COMMENT THAT WAS NOT A COMMENT

Demetri opened /crs/fis/ and found this in the INs column of every row:

    {# A COUNT, not a health reading - so -info and -neutral, never
       -good. Standard 3.1: --alv-info is informational, neutral
       emphasis, and a colour must not mean two things at once. #}

I wrote that in X3, to record WHY the IN count wears --alv-info rather
than --alv-good. Django's {# #} comment is SINGLE LINE ONLY: the tag ends
at the newline, not at #}, so everything after the first line is template
text and the page prints it. On one line it would have disappeared. Over
three it became content, in a column, on production.

    {% comment %} ... {% endcomment %} is the multi-line form.

That is the whole fix - the words are right and they stay, in the tag
that actually hides them.

WHY THE GATE SWEEPS ALL 146 TEMPLATES AND NOT THIS PAGE
    A gate that checks this file checks the instance. The defect is the
    SHAPE - {# with no #} before the newline - and it is invisible in
    every way a reviewer normally looks: the file reads like a comment,
    the page renders without an error, and no test fails. It shows up
    only as prose in a cell, which is exactly how it reached production.
    So the suite counts the shape across the whole tree and the answer
    must be zero.

Backups: .bak_crscomment. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_crscomment'
PAGE = 'crs/fi_list.html'
CRLF = {}

WAS = """            {# A COUNT, not a health reading - so -info and -neutral, never
               -good. Standard 3.1: --alv-info is informational, neutral
               emphasis, and a colour must not mean two things at once. #}"""

NOW = """            {% comment %}
              A COUNT, not a health reading - so -info and -neutral,
              never -good. Standard 3.1: --alv-info is informational,
              neutral emphasis, and a colour must not mean two things at
              once.

              AND IT IS THIS TAG, NOT THE HASH ONE, BECAUSE THIS NOTE IS
              THREE LINES LONG. Django's hash comment ends at the
              newline, so the version that shipped was never a comment at
              all and the page printed it in the INs column of every row.
              No brace is written inside this block on purpose: a comment
              that quotes tags is the next reader's trap. See
              test_crs_comment_fix.py, which sweeps the whole tree for the
              shape and counts the opens against the closes.
            {% endcomment %}"""


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
            raise SystemExit('X12: %s is not a byte copy' % bak)


def unclosed(text):
    """Every {# whose #} is not on the same line - the defect itself."""
    out = []
    for m in re.finditer(r'\{#', text):
        stop = text.find('\n', m.start())
        seg = text[m.start():stop if stop >= 0 else len(text)]
        if '#}' not in seg:
            out.append(text[:m.start()].count('\n') + 1)
    return out


print('=' * 74)
print('SECTION X, ROUND X12 - A COMMENT THAT WAS NOT A COMMENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = alv_tree.path_of(PAGE)
text, raw = read(path)

if '{% comment %}' in text and not unclosed(text):
    print('  %s is already fixed' % PAGE)
else:
    a = eol(path, WAS)
    if text.count(a) != 1:
        raise SystemExit('X12: the comment is in %s %d time(s), not 1 - it '
                         'has been edited since X3' % (PAGE, text.count(a)))
    lines = unclosed(text)
    if lines != [65]:
        raise SystemExit('X12: %s has unclosed {# on lines %s, and this '
                         'round is written for line 65 alone' % (PAGE, lines))
    text = text.replace(a, eol(path, NOW), 1)
    if unclosed(text):
        raise SystemExit('X12: the replacement STILL leaves an unclosed {#')
    print('  %-24s {# #} over 3 lines  ->  {%% comment %%}' % PAGE)
    if not CHECK:
        back_up(path, raw)
        write(path, text)

# THE SWEEP. The instance is fixed above; this is the shape, everywhere.
print('-' * 74)
left = {}
for p in alv_tree.templates():
    t, _ = read(p)
    if p == path and CHECK:
        t = t.replace(eol(p, WAS), eol(p, NOW), 1)
    ln = unclosed(t)
    if ln:
        left[alv_tree.rel(p)] = ln
if left:
    raise SystemExit('X12: %d template(s) still carry a multi-line {# #}: %s'
                     % (len(left), left))
print('  0 of %d templates carry a multi-line {# #}'
      % len(alv_tree.templates()))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
