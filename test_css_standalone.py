# -*- coding: utf-8 -*-
"""test_css_standalone.py - Section CS round CS-2, 5 Oct 2026.

CS-1's drift census reported six declarations on manual_pdf.html as a
page beating base's stylesheets with a different value. It is not.
manual_pdf has no {% extends %} - help.py renders it with
render_to_string and hands the result to xhtml2pdf - so base's four
stylesheets are not in the document at all. It is a standalone document
styling itself, and the census was comparing it against nothing.

Twelve templates in this tree are standalone. CS-2 teaches alv_tree to
say which, and test_css_order's sections 5 and 5b to skip them.

SECTION 3 IS THE ONE THAT MATTERS. The test is the TAG, not a list, and
a tag is a thing that can be written in a comment. A page explaining in
a comment that it does not extend base is still not extending base -
and a page whose only {% extends %} is commented out IS standalone,
whatever the raw text says. That is CO-1's rule applied to a different
reader, and section 3 plants both cases.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_standalone'
ME = 'test_css_standalone.py'
PATCHER = 'apply_css_standalone.py'
CSS = 'test_css_order.py'
TREE = 'alv_tree.py'
PS1 = 'Push-PendingChanges.ps1'

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. alv_tree knows which templates base cannot reach')

ok(hasattr(alv_tree, 'standalone'), 'alv_tree.standalone() exists')
ok(hasattr(alv_tree, 'inherits_base'), '  and inherits_base() beside it')

sa = alv_tree.standalone()
ok(len(sa) == 12, 'it names %d template(s)' % len(sa), sa)
for s in sa:
    print('      %s' % s)

# EVERY ONE REALLY HAS NO EXTENDS, read off the file rather than trusted.
bad = []
for name in sa:
    p = alv_tree.path_of(name)
    if p is None or re.search(r'\{%\s*extends\b',
                              alv_tree.code_only(read(p))):
        bad.append(name)
ok(not bad, '  and every one of them really has none', bad)

# AND EVERY OTHER TEMPLATE HAS ONE. The claim is a partition, not a list.
missing = []
for p in alv_tree.templates():
    name = alv_tree.rel(p).replace(os.sep, '/')
    if name == 'base.html' or name in sa:
        continue
    if not re.search(r'\{%\s*extends\b', alv_tree.code_only(read(p))):
        missing.append(name)
ok(not missing,
   '  and all %d others do, so the two lists partition the tree'
   % (len(alv_tree.templates()) - len(sa) - 1), missing)

ok(alv_tree.inherits_base(alv_tree.path_of('base.html')),
   '  base.html itself is not in the list - it is the thing not extended')

# ==========================================================================
head('2. manual_pdf, which is where this was found')

p = alv_tree.path_of('manual_pdf.html')
ok('manual_pdf.html' in sa, 'manual_pdf.html is standalone')
ok(not alv_tree.inherits_base(p), '  inherits_base() says so too')
src = read(p)
ok('{% extends' not in src, '  it has no extends tag at all')
ok(not alv_tree.inherits_base(p) and 'badge-info' in src,
   '  and it styles .badge-info itself, which is what the census saw')

views = read(os.path.join(ROOT, 'pages', 'views', 'help.py'))
ok("render_to_string('manual_pdf.html'" in views,
   '  it is rendered by render_to_string, not served to a browser',
   'the view no longer renders it that way - read it again')
ok('pisa.CreatePDF' in views,
   '  and handed to xhtml2pdf, which is why there is no base to inherit')

# ==========================================================================
head('3. the test is the TAG, and a tag can be written in a comment')

# A page whose only extends is COMMENTED OUT is standalone, whatever the
# raw text says. CO-1's rule, applied to a different reader.
probe_out = '{# {% extends "base.html" %} #}\n<p>hello</p>'
ok(not re.search(r'\{%\s*extends\b', alv_tree.code_only(probe_out)),
   'an extends inside a Django comment does not count as one')
probe_html = '<!-- {% extends "base.html" %} -->\n<p>hello</p>'
ok(not re.search(r'\{%\s*extends\b', alv_tree.code_only(probe_html)),
   '  nor one inside an HTML comment')
probe_real = '{% extends "base.html" %}\n<p>hello</p>'
ok(bool(re.search(r'\{%\s*extends\b', alv_tree.code_only(probe_real))),
   '  and a real one still does - the reader is not simply blind')

# CONTROL: the raw text would get all three wrong.
ok(bool(re.search(r'\{%\s*extends\b', probe_out)),
   'CONTROL: the RAW text of the commented one looks like it extends',
   'then this check proves nothing')

# ==========================================================================
head('4. the census stopped counting them')

css_now, css_was = now(os.path.join(ROOT, CSS)), was(os.path.join(ROOT, CSS))
ok('alv_tree.standalone()' in css_now,
   '%s asks alv_tree rather than keeping its own list' % CSS)
ok(css_now.count('alv_tree.standalone()') == 2,
   '  in both section 5 and section 5b',
   css_now.count('alv_tree.standalone()'))
ok('alv_tree.standalone()' not in css_was,
   '  and did neither before this round')
ok("manual_pdf.html\\'s print badges" not in css_now,
   "  5b no longer blames manual_pdf's print badges for the number")

# ==========================================================================
head('5. and the gate says the same thing it said before')

# CS-2 CHANGES WHAT IS COUNTED, NOT WHAT IS ALLOWED. Section 5 is the
# gate; if skipping the standalone pages turned a failure into a pass,
# this round would be hiding something rather than correcting an
# instrument. It was green before and it is green now, because no
# standalone page happens to collide with the block CS-1 moved.
import subprocess
r = subprocess.run([sys.executable, CSS], capture_output=True, text=True,
                   cwd=ROOT, timeout=1800)
ok(r.returncode == 0, '%s is green' % CSS, r.stdout[-600:])
ok('no page redeclares a property of the block CS-1 moved' in r.stdout,
   '  and section 5 still makes its claim')
m = re.search(r'(\d+) page declarations beat', r.stdout)
ok(m is not None, '  5b still prints a number', r.stdout[-400:])
if m:
    print('      5b now reports %s, down from 140 - the six manual_pdf '
          'carried' % m.group(1))
    ok(int(m.group(1)) == 134,
       '  and it is %s, which is 140 less manual_pdf\'s six'
       % m.group(1), m.group(1))
m2 = re.search(r'(\d+) standalone template\(s\) are not counted', r.stdout)
ok(m2 is not None and int(m2.group(1)) == len(sa),
   '  while saying how many it left out', r.stdout[-400:])

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(os.path.join(ROOT, TREE + SUFFIX)),
   '%s has a %s backup - this round changed TWO files' % (TREE, SUFFIX))

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the twelve are standalone for a GOOD')
print('  reason. Four render to PDF, one is an email body, three are')
print('  fragments injected into a page that already has base, and the')
print('  connectivity error page has to render when the database is')
print('  down. Those read as deliberate; the suite proves only that')
print('  none of them extends base, which is what decides whether the')
print('  census may compare them against it.')
