# -*- coding: utf-8 -*-
"""test_stranded.py - Section IB round IB-2, 3 Oct 2026.

Demetri, 3 Oct 2026: "Search by name field works perfectly. The Category
dropdown does nothing even when a category is selected."

IT WAS NOT THE DROPDOWN. The select had a change handler and the view read
request.GET[category] and filtered on it. Both halves were right. They
never met, because the script holding that handler was written AFTER the
page's {{% endblock %}}.

A CHILD TEMPLATE IS NOT A DOCUMENT. It is a set of blocks, and Django
discards anything outside one - no warning, no error, no output. 2,598
characters had never reached a browser since IB-1 shipped on 2 October,
and four things went with them: the Category filter, the chip row (so the
Filter badge has read 0 ever since), Clear All, and Enter-to-search.
Search survived because THAT half lives in base.

SECTION 1 IS THE CENSUS AND IT IS THE POINT. The bug is invisible: the
page renders, nothing errors, and the only symptom is a control that does
nothing. So the suite asks the whole tree, every time, whether any
template strands anything - and section 2 proves the question can still
be answered yes, by asking it of this round's own backup.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_stranded'
ME = 'test_stranded.py'
PATCHER = 'apply_stranded_script.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_stranded_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('ingredient_base_units_management.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'conversions.py')
END = '{% endblock %}'


def stranded(src):
    """What a child template puts outside every block, and therefore
    throws away. The run after the LAST endblock, or ''.

    READ OFF THE MARKUP WITH COMMENTS BLANKED. A template that merely
    DISCUSSES an endblock in a note has not closed a block - and the
    string this looks for is exactly the one a note about this round
    would want to quote. Sixth time this tree has learned that."""
    c = alv_tree.code_only(src).replace('\r\n', '\n')
    if not re.search(r'\{%\s*extends\b', c):
        return ''
    last = None
    for m in re.finditer(r'\{%\s*endblock[^%]*%\}', c):
        last = m
    return c[last.end():] if last else ''


# ==========================================================================
head('1. THE CENSUS - NOTHING IN THIS TREE IS THROWN AWAY')
# ==========================================================================
children = [p for p in sorted(alv_tree.templates())
            if re.search(r'\{%\s*extends\b', alv_tree.code_only(now(p)))]
ok(len(children) > 100,
   '%d template(s) extend another, so the question applies to them'
   % len(children))

bad = []
for p in children:
    s = stranded(now(p))
    if s.strip():
        bad.append('%s  %d characters' % (alv_tree.rel(p), len(s.strip())))
ok(not bad, 'and not one of them puts markup outside every block',
   '\n'.join(bad[:6]))

# ==========================================================================
head('2. CONTROL - THE QUESTION CAN STILL BE ANSWERED YES')
# ==========================================================================
old = was(PAGE)
if not old:
    skip('before this round, this page did', 'no backup')
    skip('and it was the script', 'no backup')
else:
    lost = stranded(old)
    ok(lost.strip(),
       'before this round this page stranded %d characters'
       % len(lost.strip()))
    ok(lost.strip().startswith('<script>'),
       'and what it stranded was a script, not whitespace')
    # A SYNTHETIC CONTROL TOO, so the gate does not depend on one backup
    # surviving: a template built in SCRATCH with one line after its
    # endblock must be caught.
    probe = ('{% extends "base.html" %}\n{% block content %}\n<p>x</p>\n'
            + END + '\n<script>var a = 1;</script>\n')
    ok(stranded(probe).strip() == '<script>var a = 1;</script>',
       'CONTROL: and a template built here with one line after its '
       'endblock is caught')
    ok(not stranded(probe.replace('\n<script>var a = 1;</script>\n', '\n')
                    ).strip(),
       'CONTROL: and the same template without it is not')

# AND A COMMENT THAT QUOTES THE TAG IS NOT THE TAG. This is the lesson the
# helper is built around, so it is tested rather than asserted.
quoted = ('{% extends "base.html" %}\n{% block content %}\n'
          '{# a note that writes ' + END + ' inside a comment #}\n'
          '<p>x</p>\n' + END + '\n')
ok(not stranded(quoted).strip(),
   'CONTROL: a comment quoting the closing tag does not close a block')

# ==========================================================================
head('3. THE FOUR THINGS THAT WENT WITH IT')
# ==========================================================================
src = alv_tree.code_only(now(PAGE))
inside = src[:src.rindex(END)]
for probe, what in (
        ("categorySelect.addEventListener('change'", 'the Category filter'),
        ('function updateActiveFilters', 'the chip row'),
        ("clearAllBtn.addEventListener('click'", 'Clear All'),
        ("searchInput.addEventListener('keypress'", 'Enter to search')):
    ok(probe in inside, '%-22s is inside the block' % what)
    if old:
        o = alv_tree.code_only(old)
        ok(probe in o[o.rindex(END):],
           '  CONTROL: and before this round it was outside')

# ==========================================================================
head('4. MOVED, NOT REWRITTEN')
# ==========================================================================
# Otherwise this round is quietly a rewrite of IB-1's logic wearing a
# move's clothes, and a bug introduced here would read as a bug IB-1
# shipped.
def squash(x):
    return re.sub(r'\s+', ' ', x).strip()


if old:
    # BOTH SIDES COMMENT-BLANKED. stranded() reads code_only, so the old
    # text has its /* */ notes turned to spaces; comparing that against
    # the RAW new file compares a stripped string with an unstripped one
    # and never matches. Asking the same question of both is the whole
    # trick.
    ok(squash(stranded(old)) in squash(alv_tree.code_only(now(PAGE))),
       'the script that moved is the script that is there, character for '
       'character')
else:
    skip('the script that moved is the script that is there', 'no backup')

# ==========================================================================
head('5. AND THE TWO HALVES STILL MEET')
# ==========================================================================
# A handler that submits a form whose select the view does not read would
# leave the dropdown just as dead, from the other end.
v = read(VIEW)
ok("request.GET.get('category'" in v, 'the view reads GET category')
ok('category__ingredient_category_id=category_filter' in v,
   'and filters the queryset on it')
ok('name="category"' in src, 'the select is named category')
ok('id="categoryFilter"' in src, 'and the handler finds it by id')
form = re.search(r'<form[^>]*id="filterForm"[^>]*>', src)
ok(form is not None, 'the form the handler submits exists')
if form:
    ok("method=\"get\"" in form.group(0).lower(),
       '  and it is a GET - a filter is a view, not a change')
    sel = src.index('id="categoryFilter"')
    ok(src.index(form.group(0)) < sel < src.index('</form>'),
       '  and the select is inside it, or submitting the form would not '
       'carry it')

# ==========================================================================
head('6. THE BLOCKS BALANCE')
# ==========================================================================
opens = re.findall(r'\{%\s*block\b', src)
closes = re.findall(r'\{%\s*endblock[^%]*%\}', src)
ok(len(opens) == len(closes),
   '%d block(s) opened, %d closed' % (len(opens), len(closes)))
ok(len(re.findall(r'\{%\s*block\s+content\s*%\}', src)) == 1,
   'and exactly one of them is content')

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
