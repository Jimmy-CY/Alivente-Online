# -*- coding: utf-8 -*-
"""test_shopping_list.py - Section SL rounds SL-1, SL-2 and SL-3, 3 Oct 2026.

Demetri's eight Shopping List items, with the two questions he answered on
3 Oct. Three rounds, ONE SUITE, because they are one programme on one page
and the alternative is three suites reading the same file - which is the
duplication the filter census is still paying for five times over.

SECTION 1 IS THE FUNCTIONAL BUG, AND IT LEADS. "Print butoon brings up an
empty list. Should not appear until shopping list has been defined."

Three facts, each correct alone: the bar's Print called window.print()
unconditionally; @media print FORCED #step2Content visible whatever state
it was in; and #finalShoppingList is filled only by generateShoppingList().
So before Generate, printing gave one sheet headed "Items to Buy" with
nothing under it. And goBackToReview() never cleared the list, so printing
from step 1 AFTER a Generate printed a stale one - worse, because it looks
right.

THREE GUARDS, AND THE SUITE CHECKS THEM SEPARATELY. The markup ships the
button hidden; the handler refuses when the list is empty; the stylesheet
prints whatever step is open. Each can be reached without the others - a
keyboard Ctrl+P touches neither the markup nor the handler - so a suite
that only proved one of them would be proving the wrong thing.

SECTION 2 IS THE BAR. Demetri: to the top, Cancel becomes Back, and on
step 2 BOTH the share box and Back/Done move up. The bar sits above both
step contents, so it carries every control and setBar() decides which are
on screen. Back means two different things - leave the page on step 1, go
back a step on step 2 - and that is correct, so both are asserted.

SECTION 3 IS THE COLOUR, AND ITS CLAIM IS AN EXCEPTION. 20 distinct
literals became ONE: #25D366, WhatsApp's own green, kept by Demetri's
decision and pinned here BY NAME so it is a recorded exception rather than
a stray. The step badges stop being green because a step is not a verdict -
the same distinction UC-1 settled a day earlier.

WHAT THIS SUITE CANNOT DO. It cannot tell you a printed sheet looks right
on paper. It asserts which controls exist when, that one function prints,
and that the page names only colours base defines.
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
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

# THREE ROUNDS, THREE SUFFIXES. Each claim is measured against the state
# the round it is about was built on, which is what the scope rule means -
# never read(path).
SUF1, SUF2, SUF3 = '.bak_printguard', '.bak_shopbar', '.bak_shoptone'
SUFFIX = SUF3           # the latest, for now()
ME = 'test_shopping_list.py'
PATCHERS = ('apply_print_guard.py', 'apply_shopping_bar.py',
            'apply_shopping_tone.py')
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'meal_plan_shopping_list.html'
EXCEPTION = '#25D366'

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


def was(p, suf):
    return read(p + suf) if os.path.isfile(p + suf) else ''


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def fn_body(src, name):
    i = src.find('function %s(' % name)
    if i < 0:
        return ''
    j = src.find('\n    }', i)
    return src[i:j] if j > i else src[i:]


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W1 = code_only(was(P, SUF1))

print('=' * 74)
print('%s - SL-1, SL-2, SL-3' % ME)
print('=' * 74)

# ==========================================================================
head('1. PRINT, AND THE THREE WAYS IN')
# ==========================================================================
btn = re.search(r'<button[^>]*id="printBtn"[^>]*>', CODE)
if ok(bool(btn), 'the bar carries a Print button with an id'):
    b = btn.group(0)
    ok(' hidden' in b or 'hidden ' in b,
       'GUARD 1 (markup): it ships hidden')
    ok('disabled' not in b,
       '  hidden, not disabled - a disabled control still says you may '
       'print and then refuses')
    ok('onclick="printList()"' in b, '  and it goes through printList()')

h = fn_body(CODE, 'hasPrintableList')
ok(bool(h), 'GUARD 2 (handler): hasPrintableList exists')
ok("classList.contains('active')" in h,
   '  it checks the step is actually open')
ok('children.length > 0' in h, '  AND that the list has rows')
ok('window.finalShoppingList' not in h,
   '  and it asks the DOM, not a flag - a flag is a second record of one '
   'fact')

pm = re.search(r'@media print \{(.*?)\n\}', CODE, re.S)
if ok(bool(pm), 'GUARD 3 (stylesheet): the print block is there'):
    pb = pm.group(1)
    ok(not re.search(r'#step2Content\s*\{[^}]*display:\s*block', pb),
       '  it no longer forces step 2 visible whatever its state')
    ok(bool(re.search(r'\.step-content\.active\s*\{[^}]*display:\s*block',
                      pb)),
       '  it prints the step that is OPEN - the only guard that also '
       'covers Ctrl+P')
    ok('#step1Content' in pb,
       '  and step 1 is still hidden, or the review list would print under '
       'the shopping list')

calls = [m.start() for m in re.finditer(r'window\.print\(\)', CODE)]
pl = CODE.find('function printList()')
pl_end = CODE.find('\n    }', pl) if pl >= 0 else -1
outside = [c for c in calls if not (0 <= pl < c < pl_end)]
ok(not outside, 'window.print() is called from exactly one place',
   [CODE.count('\n', 0, c) + 1 for c in outside])
ok(len(re.findall(r'onclick="printList\(\)"', CODE)) == 1,
   'and exactly one control calls printList()')

gen = fn_body(CODE, 'generateShoppingList')
back = fn_body(CODE, 'goBackToReview')
ok("removeAttribute('hidden')" in gen, 'Generate reveals the button')
ok("setAttribute('hidden', '')" in back,
   'and going Back hides it again - a list no longer on screen must not be '
   'printable')

if W1:
    ok('onclick="window.print()"' in W1,
       'CONTROL: the bar really did call window.print() directly before')
    ok(bool(re.search(r'#step2Content\s*\{[^}]*display:\s*block\s*'
                      r'!important', W1)),
       '  and the sheet really did force step 2')
    ok('hasPrintableList' not in W1, '  and no guard existed')
else:
    skip('the SL-1 controls', 'no %s backup' % SUF1)

# ==========================================================================
head('2. ONE BAR, AND IT SAYS WHICH STEP YOU ARE ON')
# ==========================================================================
for dead in ('step-navigation', 'btn-secondary'):
    n = len(re.findall(r'\b%s\b' % dead, CODE))
    ok(n == 0, '%r is gone from markup and CSS alike' % dead, 'still %d' % n)

bar = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', CODE,
                re.S)
if ok(bool(bar), 'the action bar is there'):
    b = bar.group(1)
    for bid, want_hidden, what in (('genBtn', False, 'Generate List'),
                                   ('doneBtn', True, 'Done'),
                                   ('printBtn', True, 'Print'),
                                   ('backLink', False, 'Back to the plan'),
                                   ('backStep', True, 'Back a step')):
        m = re.search(r'<(?:button|a)[^>]*id="%s"[^>]*>' % bid, b)
        if not ok(bool(m), 'the bar carries %s (%s)' % (bid, what)):
            continue
        hid = ' hidden' in m.group(0) or 'hidden ' in m.group(0)
        ok(hid == want_hidden, '  %s ships %s' % (bid, 'hidden' if hid
                                                  else 'visible'))
    for step, ids in ((1, ('genBtn', 'backLink')),
                      (2, ('doneBtn', 'printBtn', 'backStep'))):
        pos = [b.find('id="%s"' % i) for i in ids]
        ok(pos == sorted(pos) and -1 not in pos,
           'step %d reads %s - A-BAR order' % (step, ' / '.join(ids)), pos)

sb = fn_body(CODE, 'setBar')
ok(bool(sb), 'setBar decides which controls are on screen')
for bid in ('genBtn', 'doneBtn', 'backLink', 'backStep'):
    ok(bid in sb, '  it sets %s' % bid)
ok('printBtn' not in sb,
   '  and NOT printBtn - that depends on whether a list exists, which is a '
   'different question from which step is open')
ok('setBar(2)' in gen and 'setBar(1)' in back,
   'and both step switches call it, so the bar cannot drift out of step')

i_share = CODE.find('class="email-section"')
i_list = CODE.find('<h2>Items to Buy</h2>')
ok(0 <= i_share < i_list,
   'the share box sits ABOVE the list - Demetri chose both to the top')
sh = CODE[i_share:i_list] if 0 <= i_share < i_list else ''
ok('printList()' not in sh, 'and it no longer carries its own Print')
for role, what in (('action-secondary', 'Copy'),
                   ('action-primary', 'Email')):
    ok(role in sh, '%s is on %s' % (what, role))
ok(not re.findall(r'style="[^"]*background[^"]*"', sh),
   'and no button in it paints its own background')

W2 = code_only(was(P, SUF2))
if W2:
    ok(len(re.findall(r'<div class="step-navigation">', W2)) == 2,
       'CONTROL: there really were two bottom bars before')
    ok('Cancel' in W2, '  and a Cancel that is now a Back')
else:
    skip('the SL-2 controls', 'no %s backup' % SUF2)

# ==========================================================================
head('3. ONE LITERAL LEFT, AND IT IS A DECISION')
# ==========================================================================
left = sorted(set(x.upper() for x in
                  re.findall(r'#[0-9a-fA-F]{3,8}\b', CODE)))
ok(left == [EXCEPTION],
   'exactly one literal colour on the page, and it is %s' % EXCEPTION, left)
ok(CODE.count(EXCEPTION) == 1,
   'written once - an exception written twice is two literals and one note')
ok('share-whatsapp' in CODE,
   'and it is named, so the exception has somewhere to be explained')
ok('linear-gradient' not in CODE, 'no gradient survives')

for sel, want in (('.step-badge.active', '--alv-accent'),
                  ('.step-badge.completed', '--alv-accent-soft')):
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', CODE)
    if not ok(bool(m), '%s is there' % sel):
        continue
    ok(want in m.group(1), '  %s is on %s' % (sel, want),
       m.group(1).strip()[:70])
    bad = [v for v in ('--alv-good', '--alv-warn', '--alv-bad')
           if v in m.group(1)]
    ok(not bad, '  and carries no verdict tone - a step is not a verdict',
       bad)

m = re.search(r'\.conversions-needed-card\s*\{([^}]*)\}', CODE)
ok(bool(m) and '--alv-warn' in (m.group(1) if m else ''),
   'the conversions card is STILL a warning - only its values moved')
ok('alv-pill alv-pill-info' in CODE,
   'and the quantity chip is a house pill, as UC-1 made the conversion ones')

BASE = code_only(read(alv_tree.path_of('base.html')))
used = sorted(set(re.findall(r'var\((--alv-[\w-]+)\)', CODE)))
missing = [v for v in used if not re.search(re.escape(v) + r'\s*:', BASE)]
ok(not missing,
   'all %d tokens this page names are defined in base' % len(used), missing)

W3 = code_only(was(P, SUF3))
if W3:
    n = len(set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', W3)))
    ok(n >= 15, 'CONTROL: the page carried %d distinct literals before '
       'SL-3' % n)
    ok('linear-gradient' in W3, '  and a gradient')
    ok(bool(re.search(r'\.step-badge\.active\s*\{[^}]*#28a745', W3)),
       '  and the active step badge really was green')
else:
    skip('the SL-3 controls', 'no %s backup' % SUF3)

# ==========================================================================
head('4. THE MARKUP CLOSES, AND NO COMMENT IS MISPLACED')
# ==========================================================================
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', CODE))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', CODE))
    ok(a == z, 'every {%% %s %%} closes - %d / %d' % (tag, a, z))
_b = re.sub(r'<(script|style)\b.*?</\1>', '', CODE, flags=re.S)
ok(len(re.findall(r'<div\b', _b)) == len(re.findall(r'</div\s*>', _b)),
   'and every <div> closes')
ok(not [i for i, ln in enumerate(NOW.split('\n'), 1)
        if '{#' in ln and '#}' not in ln],
   'no Django comment spans lines - the lexer has no DOTALL')
OPENER, CLOSER = '<' + '!--', '--' + '>'
_d, _bad = 0, []
for mm in re.finditer(r'<[a-zA-Z/!]|>', NOW):
    if mm.group(0) == '>':
        _d = max(0, _d - 1)
    elif NOW.startswith(OPENER, mm.start()):
        if _d:
            _bad.append(NOW.count('\n', 0, mm.start()) + 1)
    else:
        _d = 1
ok(not _bad, 'no comment opens while a tag is still open  [B-1b]', _bad[:4])

# ==========================================================================
head('5. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
for p in PATCHERS:
    ok(os.path.isfile(os.path.join(ROOT, p)), '%s is on disk' % p)
try:
    from alv_rounds import ROUNDS
    for s in (SUF1, SUF2, SUF3):
        ok(s in ROUNDS, '%s is in ROUNDS' % s)
    ok(ROUNDS.index(SUF1) < ROUNDS.index(SUF2) < ROUNDS.index(SUF3),
       '  and in build order - SL-1, SL-2, SL-3')
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
