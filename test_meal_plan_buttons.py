# -*- coding: utf-8 -*-
"""test_meal_plan_buttons.py - Section MP round MP-1, 3 Oct 2026.

Demetri, item 3 of eight: "The Green Add Recipe Button need to change
colour and comply with our standards. The same goes for the Red 'Delete'
trashcans."

SECTION 2 IS WHY THIS WAS A ROUND AND NOT AN EDIT. The two class names
appeared ten times, and FOUR of those were inside JavaScript template
strings - the day cards are built in the browser. A find-and-replace on
the markup would have left every card the page makes AFTER load still
painted the old way, and the page would have disagreed with itself
depending on whether you had pressed anything.

SECTION 3 IS THE ONE REAL DECISION. Add Recipe is a SECONDARY, not the
page's primary. Save is the primary, and there is one Add Recipe per day
card - up to seven on a week's plan - so a primary here would put seven
primaries on a screen whose actual primary is one button at the top.

SECTION 4 IS WHAT THIS ROUND DID NOT DO. Two uses of #28a745 survive, on a
hover border and on a Vegetarian badge built in JS. Demetri asked for the
Add Recipe button and the trashcans; changing more than was asked is how a
round stops being reviewable. They are pinned BY WHERE THEY ARE, so a
third one is reported the day it appears.

WHAT THIS SUITE CANNOT DO. It cannot press Add Recipe. It asserts that
every place which built one of these buttons now builds the house one.
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

SUFFIX = '.bak_mealbtn'
ME = 'test_meal_plan_buttons.py'
PATCHER = 'apply_meal_plan_buttons.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'create_meal_plan.html'
OLD_NAMES = ('btn-remove-recipe', 'btn-add-recipe')
OLD_COLOURS = ('#dc3545', '#c82333', '#218838')
# The two this round did not touch, pinned by WHERE they are.
GREEN_LEFT = {
    '.recipe-selector-card:hover': 'a hover border on the recipe picker',
    'recipe-selector-card-badge': 'the Vegetarian badge, built in JS',
}

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


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W = code_only(was(P))

print('=' * 74)
print('%s - MP-1, ADD AND REMOVE' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE TWO NAMES AND THEIR COLOURS ARE GONE')
# ==========================================================================
for dead in OLD_NAMES:
    n = len(re.findall(r'\b%s\b' % dead, CODE))
    ok(n == 0, '%r is gone from markup, CSS and script alike' % dead,
       'still %d' % n)
for lit in OLD_COLOURS:
    ok(lit not in CODE, '%s is gone' % lit)

# ==========================================================================
head('2. INCLUDING WHERE THE PAGE BUILDS THEM ITSELF')
# ==========================================================================
# The reason this was a round. A template string is markup the BROWSER
# writes, and a find-and-replace stopping at the <body> would have missed
# every card made after load.
js_now = re.findall(r'`[^`]*(?:icon-delete|action-secondary)[^`]*`', CODE,
                    re.S)
ok(bool(js_now), 'the page still builds these buttons in JavaScript')
ok(not re.findall(r'`[^`]*btn-(?:remove|add)-recipe[^`]*`', CODE, re.S),
   'and no template string carries an old one')
if W:
    js_was = re.findall(r'`[^`]*btn-(?:remove|add)-recipe[^`]*`', W, re.S)
    ok(bool(js_was),
       'CONTROL: %d template string(s) really did carry the old names'
       % len(js_was))
    ok(len(js_now) >= len(js_was),
       '  and at least as many carry the new ones (%d vs %d)'
       % (len(js_now), len(js_was)))
else:
    skip('the template-string control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. THE HOUSE COMPONENTS, AND THE ONE DECISION')
# ==========================================================================
n_del = len(re.findall(r'class="icon-action-btn icon-delete"', CODE))
ok(n_del == 3, 'three trashcans on base\'s row-action strip', n_del)
for m in re.finditer(r'<button[^>]*icon-delete[^>]*>', CODE):
    ok('aria-label' in m.group(0),
       'and each carries a label - an icon-only button is nothing at all '
       'to a screen reader')
    break
ok(len(re.findall(r'<button[^>]*icon-delete[^>]*>', CODE))
   == len(re.findall(r'<button[^>]*icon-delete[^>]*aria-label', CODE)),
   '  all %d of them' % n_del)

i_add = CODE.find('addRecipe(')
seg = CODE[max(0, i_add - 300):i_add + 200] if i_add >= 0 else ''
ok('action-secondary' in seg, 'Add Recipe is a SECONDARY')
ok('action-primary' not in seg,
   '  and not a primary - there is one per day card, so a primary here is '
   'seven primaries on one screen')

BASE = code_only(read(alv_tree.path_of('base.html')))
for cls in ('.icon-action-btn', '.icon-delete', '.action-secondary'):
    ok(bool(re.search(re.escape(cls) + r'[\s,{:]', BASE)),
       'base defines %s' % cls)

# ==========================================================================
head('4. WHAT THIS ROUND DID NOT DO, PINNED')
# ==========================================================================
found = []
for m in re.finditer(r'#28a745', CODE):
    seg = CODE[max(0, m.start() - 260):m.start()]
    where = [k for k in GREEN_LEFT if k in seg]
    if not where:
        ok(False, 'an unpinned #28a745 at line %d'
           % (CODE.count('\n', 0, m.start()) + 1))
        continue
    found.append(where[-1])
ok(sorted(found) == sorted(GREEN_LEFT),
   '%d use(s) of #28a745 remain, and both are the pinned ones'
   % len(GREEN_LEFT), sorted(found))
for k in sorted(GREEN_LEFT):
    print('      %-34s %s' % (k, GREEN_LEFT[k]))

if W:
    new = (set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', CODE))
           - set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', W)))
    ok(not new, 'and no colour entered the page', sorted(new))

# ==========================================================================
head('5. THE MARKUP CLOSES')
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
   'no Django comment spans lines')

# ==========================================================================
head('6. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
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
ok(len(rows) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows))


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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
