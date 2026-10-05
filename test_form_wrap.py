# -*- coding: utf-8 -*-
"""test_form_wrap.py - Section RA round RA-3b, 5 Oct 2026.

RA-3 wrapped 21 icon buttons on eight pages and held four back. Three
were held for the same reason: their actions are not bare buttons but
FORMS, one per action, because each posts somewhere different.

A RUN OF BUTTONS WAS THE WRONG UNIT. RA-3 grouped buttons with nothing
but whitespace and template tags between them; between these there is a
</form> and a <form>. Wrapping the buttons would have put a .row-actions
INSIDE each form and left the forms as siblings - three groups of one,
which the drift report reads as three action columns and which tells it
nothing about order.

SO THE UNIT IS THE CELL. Section 2 is the check that matters: every
button, every form and every {% if %} branch between them must end up
inside ONE wrapper, and the forms must still be forms. A wrapper that
swallowed a </form> would be invalid markup that still looked right to a
text census.
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

SUFFIX = '.bak_formwrap'
ME = 'test_form_wrap.py'
PATCHER = 'apply_form_wrap.py'
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


from apply_form_wrap import CELLS, EXPECT_BUTTONS

# ==========================================================================
head('1. ten buttons, three pages, each in its own form')

total = 0
for name, (tag, want) in sorted(CELLS.items()):
    p = path_of(name)
    if not p or not os.path.exists(p + SUFFIX):
        ok(False, '%s has a backup' % name)
        continue
    old = was(p)
    cell_a = old.index(tag) + len(tag)
    cell_b = old.find('</td>', cell_a)
    inner = old[cell_a:cell_b]
    got = len(RA.BTN_FULL.findall(inner))
    ok(got == want, '%-36s held %d loose control(s)' % (name, got),
       'expected %d' % want)
    ok('row-actions' not in inner, '  and no wrapper at all')
    forms = len(re.findall(r'<form\b', inner))
    print('      %-36s %d form(s) in that one cell' % ('', forms))
    total += got
ok(total == EXPECT_BUTTONS, '  %d in all' % total,
   'expected %d' % EXPECT_BUTTONS)

# ==========================================================================
head('2. one wrapper per cell, holding everything in it')

for name, (tag, want) in sorted(CELLS.items()):
    p = path_of(name)
    if not p:
        continue
    src = now(p)
    a = src.index(tag) + len(tag)
    b = src.find('</td>', a)
    inner = src[a:b]
    ok(inner.count('row-actions') == 1,
       '%-36s exactly one wrapper' % name,
       '%d found - a group split in two reads as two action columns'
       % inner.count('row-actions'))
    wraps = RA.wrappers(alv_tree.code_only(src))
    biggest = max([len(RA.BTN_FULL.findall(w[2])) for w in wraps] or [0])
    ok(biggest == want,
       '  holding all %d of its controls' % want,
       'the largest wrapper holds %d' % biggest)
    # THE FORMS ARE STILL FORMS. A wrapper that swallowed a </form>
    # would read fine to a text census and be invalid markup.
    ok(len(re.findall(r'<form\b', inner)) ==
       len(re.findall(r'</form>', inner)),
       '  and every form inside it still closes',
       '%d open, %d close' % (len(re.findall(r'<form\b', inner)),
                              len(re.findall(r'</form>', inner))))
    ok(len(re.findall(r'\{%\s*if\b', inner)) ==
       len(re.findall(r'\{%\s*endif\b', inner)),
       '  and every branch still closes')

# ==========================================================================
head('3. and nothing on those pages is loose any more')

for name in sorted(CELLS):
    p = path_of(name)
    src = alv_tree.code_only(now(p))
    spans = [(a, b) for a, b, _ in RA.wrappers(src)]
    loose = [m for m in RA.BTN_FULL.finditer(src)
             if not any(a <= m.start() < b for a, b in spans)]
    ok(not loose, '%-36s nothing loose' % name,
       [' '.join(m.group(0).split())[:70] for m in loose][:3])

# ==========================================================================
head('4. the control - a wrapper that splits the group')

victim = path_of('invoices.html')
src = now(victim)
planted = src.replace('<span class="row-actions">', '', 1)
ok(planted != src, 'the control could be planted')
code = alv_tree.code_only(planted)
spans = [(a, b) for a, b, _ in RA.wrappers(code)]
ok(any(not any(a <= m.start() < b for a, b in spans)
       for m in RA.BTN_FULL.finditer(code)),
   '  and the census catches a form-shaped action left outside',
   'it did not - then section 3 proves nothing')

# ==========================================================================
head('5. registration')

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
