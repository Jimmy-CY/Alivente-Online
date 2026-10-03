# -*- coding: utf-8 -*-
"""RE-1, PART 2 - A DJANGO COMMENT IS NOT A FLEX ITEM EITHER

The sweep failed test_secondary_visible.py on the page RE-1 touched:

    FAIL preview_imported_recipe.html  its secondary is visible on a phone
    FAIL   the secondary is the height base gives the row  []

The secondary is there. What is also there, for the first time on this
page, is a Django COMMENT - RE-1's note explaining why the Update button
carries form="saveRecipeForm".

That fixture renders the bar verbatim, and it strips exactly two things:

    TMPL_TAG = re.compile(r'\\{%.*?%\\}', re.S)
    TMPL_VAR = re.compile(r'\\{\\{.*?\\}\\}', re.S)

Its own note says why:

    "A TEMPLATE TAG IS NOT A FLEX ITEM. The bar is rendered verbatim, so a
     bare {% if %} sitting between two buttons - not inside an attribute -
     became an anonymous TEXT flex item with real width, and the bar
     wrapped to two rows in the fixture while rendering as one row on the
     page."

A Django comment is not a flex item either. Fourteen lines of explanation
became an anonymous text item hundreds of pixels wide, the bar wrapped,
and the secondary measured as not visible - on a page that is correct.

==========================================================================
EIGHTH TIME THIS WEEK, AND THE THIRD SYNTAX AGAIN
==========================================================================
IB-1 wrote this down two days ago, about a different instrument:

    a template carries Django comments, HTML comments AND CSS/JS block
    comments, and an instrument that strips two of the three can still
    read prose as code

This one strips tags and variables and not comments. Same shape, same
repair: name the third syntax and remove it with the others. Blanking is
not needed here - the fixture measures layout, not line numbers, so the
comment is removed entirely like the tags beside it.

Backups: .bak_seccomment. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_seccomment'
ROOT = os.getcwd()
CRLF = {}
TARGET = os.path.join(ROOT, 'test_secondary_visible.py')


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
            raise SystemExit('RE1b: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('RE1b: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('RE-1 PART 2 - A COMMENT IS NOT A FLEX ITEM%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TARGET)

if 'TMPL_COMMENT' in t:
    print('  test_secondary_visible.py  already strips Django comments')
else:
    t = swap(t, """TMPL_TAG = re.compile(r'\\{%.*?%\\}', re.S)
TMPL_VAR = re.compile(r'\\{\\{.*?\\}\\}', re.S)""",
             """TMPL_TAG = re.compile(r'\\{%.*?%\\}', re.S)
TMPL_VAR = re.compile(r'\\{\\{.*?\\}\\}', re.S)
# AND THE THIRD SYNTAX - RE-1 part 2, 3 Oct 2026.
#
# The note in render() below says a template TAG is not a flex item. A
# Django COMMENT is not one either, and this stripped two of the three
# things a template puts between two buttons. RE-1 added a fourteen-line
# note to preview_imported_recipe's bar explaining its form-owner
# attribute; it became an anonymous text item hundreds of pixels wide, the
# bar wrapped, and the secondary measured as hidden on a page that is
# correct.
#
# Eighth instrument this week to read prose as layout or as code. IB-1
# wrote the rule down two days ago: a template carries Django comments,
# HTML comments AND CSS block comments, and stripping two of three is not
# stripping comments.
TMPL_COMMENT = re.compile(r'\\{#.*?#\\}', re.S)""",
             'the tag patterns', TARGET)

    t = swap(t, "    bar_html = TMPL_VAR.sub('x', TMPL_TAG.sub('', bar_html))",
             "    bar_html = TMPL_VAR.sub('x', TMPL_TAG.sub(\n"
             "        '', TMPL_COMMENT.sub('', bar_html)))",
             'the strip in render()', TARGET)

    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t)
    print('  test_secondary_visible.py  strips Django comments too')

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
ast.parse(t)
if 'TMPL_COMMENT' not in t:
    raise SystemExit('RE1b: the pattern is not there')
if not re.search(r'TMPL_COMMENT\.sub\(', t):
    raise SystemExit('RE1b: it is defined and never used')
print('  it parses, defines the pattern and uses it')

# THE INSTRUMENT, ON A FIXTURE. A comment between two buttons must leave
# nothing behind; a tag and a variable must behave as before.
TC = re.compile(r'\{#.*?#\}', re.S)
TT = re.compile(r'\{%.*?%\}', re.S)
TV = re.compile(r'\{\{.*?\}\}', re.S)
strip = lambda h: TV.sub('x', TT.sub('', TC.sub('', h)))
CASES = [
    ('<a>A</a>{# a fourteen line note #}<a>B</a>', '<a>A</a><a>B</a>',
     'a Django comment leaves nothing between two buttons'),
    ('<a>A</a>{% if x %}<a>B</a>{% endif %}', '<a>A</a><a>B</a>',
     'a tag still goes and its CONTENT still stays'),
    ('<a>{{ name }}</a>', '<a>x</a>', 'a variable still becomes one char'),
    ('<a>A</a>{# {% if x %} #}<a>B</a>', '<a>A</a><a>B</a>',
     'a comment containing a tag goes whole'),
]
for src, want, why in CASES:
    got = strip(src)
    if got != want:
        raise SystemExit('RE1b: %r -> %r, expected %r  (%s)'
                         % (src, got, want, why))
    print('    %-44s %s' % (src[:44], why))

# AND THE OLD STRIP REALLY DID LEAVE THE COMMENT BEHIND.
old = TV.sub('x', TT.sub('', CASES[0][0]))
if old == CASES[0][1]:
    raise SystemExit('RE1b: the old strip handled it too - the premise of '
                     'this part is wrong')
print('  CONTROL: the old strip left %d characters of prose in the bar'
      % (len(old) - len(CASES[0][1])))

r = subprocess.run([sys.executable, 'test_secondary_visible.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n')
        if 'passed' in ln or re.search(r'^\s*\d+ of \d+', ln)]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:5]
    raise SystemExit('RE1b: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_secondary_visible.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  Strip two of three and you have not stripped comments. Eighth')
print('  time this week, in a fixture that already knew the lesson.')
print('=' * 74)
