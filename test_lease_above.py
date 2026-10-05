# -*- coding: utf-8 -*-
"""test_lease_above.py - Section LA round LA-1, 5 Oct 2026.

Demetri: "Step 3 needs to say 'click the button above ....' - since we
moved the buttons to the top."

One word. The suite is worth more than the change.

SECTION 2 IS THE REASON THIS EXISTS. It censuses every template for
prose that points at a control by DIRECTION - below, above, on the
right, at the bottom - and prints what it finds. A sentence that tells
somebody where to look goes stale the moment a layout moves, and nothing
in this repo was watching for them. This one was the only "button below"
in 150 templates; the census is what catches the next one.
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
import alv_rowactions as RA

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_leaseabove'
ME = 'test_lease_above.py'
PATCHER = 'apply_lease_above.py'
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


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


print(__doc__.strip().splitlines()[0])


PAGE = path_of('generate_lease_agreement.html')
SRC, OLD = alv_tree.code_only(now(PAGE)), alv_tree.code_only(was(PAGE))

# ==========================================================================
head('1. the sentence pointed the wrong way, and now does not')

ok('click the button below' in OLD,
   'step 3 really did say "click the button below"',
   'it did not - then the round is aimed at a sentence that was not there')
ok('click the button above' in SRC, 'and now says "above"')
ok('click the button below' not in SRC, '  with no "below" left on the page')

# AND THE BUTTON REALLY IS ABOVE IT. A one-word change is only right if
# the geometry says so: the action bar opens before step 3 in the source.
btn = SRC.find('id="generate-btn"')
step3 = SRC.find('click the button above')
ok(btn > 0 and btn < step3,
   '  and the Generate button really is earlier in the page than the line',
   'the button is at %d and the sentence at %d' % (btn, step3))

# ==========================================================================
head('2. every sentence in the tree that points at a control')

DIRECTION = re.compile(
    r'[^<>{}]{0,60}?\b(?:button|link|field|box|form|menu|tab)\s+'
    r'(below|above|on the right|on the left|at the bottom|at the top)'
    r'[^<>{}]{0,40}', re.I)
found = []
for p in alv_tree.templates():
    for m in DIRECTION.finditer(alv_tree.code_only(now(p))):
        found.append((alv_tree.rel(p).replace(os.sep, '/'),
                      ' '.join(m.group(0).split())[:72]))
print('      %d sentence(s) point at a control by direction:' % len(found))
for rel, txt in found[:12]:
    print('        %-34s %s' % (rel[:34], txt))
# PRINTED, NOT BOUNDED. Two of the three are comments inside <script>,
# which no reader ever sees; bounding the count would make this section
# fail the next time somebody writes a helpful note. The census exists to
# put the list in front of a person, and to FAIL on the one case that is
# about a real control a real person was told to look for.
stale = [(rel, txt) for rel, txt in found
         if rel == 'generate_lease_agreement.html' and 'below' in txt.lower()]
ok(not stale,
   '  and the one Demetri reported is not among them',
   stale)

# ==========================================================================
head('3. the control - the sentence put back')

planted = SRC.replace('click the button above', 'click the button below', 1)
ok(planted != SRC, 'the control could be planted')
ok('click the button below' in planted,
   '  and the census catches a sentence pointing the wrong way')
ok('click the button below' not in SRC, '  and the page itself is right')

# ==========================================================================
head('4. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
