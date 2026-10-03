# -*- coding: utf-8 -*-
"""test_calendar_actions.py - Section MC round MC-2, 3 Oct 2026.

Demetri: "On Calendar view, we have a lot of changes to do to the colours
to bring them in line."

The loudest of them was the week header: View blue, Edit yellow on black
ink, List green, Duplicate teal, Delete red - five filled colours in one
row - plus a blue View and a red x inside every recipe card.

ML-1 had already converted the SAME FIVE ACTIONS on meal_plans.html one
day earlier. The Calendar page was a second private copy of one control.
Asked whether to convert or merely retone, Demetri chose "the same icon
row as the List page".

WHAT THIS SUITE IS REALLY GUARDING is not the colours - section 3 of the
patcher's own gates does that. It is that a COSTUME CHANGE DID NOT CHANGE
WHAT A BUTTON DOES. Eleven controls were rewritten; every handler, every
url and every argument has to still be the one it was, and section 5
reads them out of the backup and compares. A round that quietly changed
confirmDelete's argument would look perfect in a screenshot.

SECTION 6 IS THE CONTROL. The page really did carry TWO
.week-detail-actions .btn rules, 457 lines apart, one of them dead for as
long as both existed. If that is not true of the backup, this round was
built on a misreading.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_calactions'
ME = 'test_calendar_actions.py'
PATCHER = 'apply_calendar_actions.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'meal_plan_calendar.html'
SIBLING = 'meal_plans.html'
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

DEAD = ('week-detail-actions', 'recipe-actions', 'btn-view', 'btn-edit',
        'btn-shopping', 'btn-duplicate', 'btn-delete',
        'btn-action-disabled', 'btn-outline-danger')
WANT = {'icon-view': 2, 'icon-edit': 1, 'icon-list': 1,
        'icon-duplicate': 1, 'icon-delete': 2, 'icon-disabled': 4}
# THE CALLS. Not the classes - the things the user actually sets off.
CALLS = ("confirmDuplicate('{% url 'duplicate_meal_plan'",
         "confirmDelete('{% url 'delete_meal_plan'",
         "removeRecipe({{ recipe.meal_plan_recipe_id }}, "
         "'{{ recipe.name|escapejs }}')")
URLS = ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list',
        'duplicate_meal_plan', 'delete_meal_plan', 'view_recipe')

SCRATCH = tempfile.mkdtemp(prefix='alv_calact_')

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


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W = code_only(was(P))
SIB = code_only(read(alv_tree.path_of(SIBLING)))
BASE = code_only(read(alv_tree.path_of('base.html')))
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

print('=' * 74)
print('%s - MC-2, THE ROW ACTIONS BECOME THE ROW ACTIONS' % ME)
print('=' * 74)

# ==========================================================================
head('1. TWO STRIPS, BOTH OF THEM BASE\'S')
# ==========================================================================
n = CODE.count('class="row-actions"')
ok(n == 2, 'two .row-actions strips - the week header and the recipe card',
   'found %d' % n)
for cls, k in sorted(WANT.items()):
    got = len(re.findall(r'\bicon-action-btn [a-z-]*\b%s\b' % cls, CODE))
    ok(got == k, '%d x .%s' % (k, cls), 'found %d' % got)

for cls in ('.row-actions', '.icon-action-btn', '.icon-view', '.icon-edit',
            '.icon-list', '.icon-duplicate', '.icon-delete',
            '.icon-action-btn.icon-disabled'):
    ok(bool(re.search(re.escape(cls) + r'[\s,{:]', BASE)),
       'base defines %s' % cls)

# ==========================================================================
head('2. ONE CONTROL IN THE TREE, NOT TWO')
# ==========================================================================
# The whole point of the round. The Calendar page and the list page are
# two views of one object with one set of five actions; if the two pages
# disagree about what those five look like, nothing has been fixed.
for cls in ('icon-view', 'icon-edit', 'icon-list', 'icon-duplicate',
            'icon-delete'):
    ok(cls in SIB and cls in CODE,
       'both views wear .%s' % cls,
       'list %s, calendar %s' % (cls in SIB, cls in CODE))
ok('fa-pencil-alt' in CODE,
   'Edit draws the list page\'s fa-pencil-alt, not this page\'s old '
   'fa-edit - two icons for one verb on two views of one object is the '
   'same defect as two stylesheets for one control')
ok('fa-edit' not in CODE, '  and fa-edit is gone')
ok('fa-times' not in CODE,
   'the lone x is gone - every destructive control in the tree is a '
   'trashcan, and a second word for "this removes something" is a second '
   'vocabulary to learn')

# ==========================================================================
head('3. EVERY ICON CARRIES A LABEL')
# ==========================================================================
# An icon-only control with no label is nothing at all to a screen
# reader, and title= is a tooltip, not a name.
btns = re.findall(r'<(?:a|button|span)[^>]*icon-action-btn[^>]*>', CODE)
bare = [b for b in btns if 'aria-label' not in b]
ok(not bare, 'all %d icon controls carry an aria-label' % len(btns),
   '\n'.join(b[:90] for b in bare[:4]))
ok(len(btns) == 11, 'and there are eleven of them', len(btns))

# ==========================================================================
head('4. THE OLD NAMES AND THEIR COLOURS')
# ==========================================================================
for dead in DEAD:
    ok(not re.search(r'\b%s\b' % dead, CODE),
       '%s is gone from markup and CSS alike' % dead)

if W:
    DROP = {'#007bff': 1, '#0056b3': 1, '#ffc107': 1, '#e0a800': 1,
            '#000;': 2, '#218838': 1, '#0e7c8b': 1, '#c82333': 1}
    for lit, k in sorted(DROP.items()):
        got = W.count(lit) - CODE.count(lit)
        ok(got == k, 'dropped %d use(s) of %s' % (k, lit),
           '%d before, %d after' % (W.count(lit), CODE.count(lit)))
    # EACH SHARED LITERAL MEASURED FOR WHAT IT IS, not by symmetry. The
    # patcher's first draft assumed #dc3545 behaved like #28a745 because
    # they sat in the same strip; #dc3545 had only ever had ONE use.
    ok(W.count('#dc3545') == 1 and CODE.count('#dc3545') == 0,
       '#dc3545 had exactly one use, on .btn-delete, and this round took it',
       '%d before, %d after' % (W.count('#dc3545'), CODE.count('#dc3545')))
    ok(W.count('#28a745') - CODE.count('#28a745') == 1,
       '#28a745 had %d uses and this round took exactly one, on '
       '.btn-shopping - MC-3 owns the rest' % W.count('#28a745'),
       '%d before, %d after' % (W.count('#28a745'), CODE.count('#28a745')))
else:
    skip('the literal drops', 'no %s backup' % SUFFIX)

# ==========================================================================
head('5. THE COSTUME CHANGED AND THE ACTION DID NOT')
# ==========================================================================
# The gate this suite exists for. Eleven controls were rewritten by hand;
# a round that quietly changed what confirmDelete is handed would look
# perfect in a screenshot and be a data-loss bug.
if W:
    for call in CALLS:
        a, b = W.count(call), CODE.count(call)
        ok(a == b and b > 0, 'the call %s... is unchanged (%d)'
           % (call[:34], b), '%d before, %d after' % (a, b))
    for u in URLS:
        a = W.count("{%% url '%s'" % u)
        b = CODE.count("{%% url '%s'" % u)
        ok(a == b, '%s resolves the same number of times (%d)' % (u, b),
           '%d before, %d after' % (a, b))
    # AND THE PERMISSION BRANCHES. Five controls were behind
    # can_edit_personal and all five still are.
    a = W.count('{% if perms.auth.can_edit_personal %}')
    b = CODE.count('{% if perms.auth.can_edit_personal %}')
    ok(a == b, 'the same %d permission branches guard the same things' % b,
       '%d before, %d after' % (a, b))
else:
    skip('the action-did-not-change gate', 'no %s backup' % SUFFIX)

# ==========================================================================
head('6. THE CONTROL - TWO RULES FOR ONE STRIP')
# ==========================================================================
if not W:
    skip('the duplicate-rule control', 'no %s backup' % SUFFIX)
else:
    pos = [m.start() for m in
           re.finditer(r'\.week-detail-actions \.btn \{', W)]
    ok(len(pos) == 2,
       'CONTROL: the page really did carry two .btn rules for one strip',
       'found %d' % len(pos))
    if len(pos) == 2:
        gap = W.count('\n', pos[0], pos[1])
        print('         %d lines apart; the later one won and the earlier '
              'one had been dead' % gap)
        print('         for as long as both existed.')

# ==========================================================================
head('7. WHAT THE BROWSER SEES - ELEVEN TARGETS, ONE ROW, NO OVERFLOW')
# ==========================================================================
# Five labelled buttons needed a 3-column grid to survive a phone. Five
# icon buttons are five 44px targets - about 250px of the 390px a phone
# gives - so the grid went. This checks that claim rather than asserting
# it in a comment.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the rendered strip checks', 'playwright not installed')

TAGS = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)
IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                     r'\{%\s*endif\s*%\}', re.S)
IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)


def take_the_if(html):
    """Resolve every {% if %} as TRUE and drop the else branch.

    A FIXTURE THAT RENDERS BOTH BRANCHES IS NOT RENDERING THE PAGE. The
    first draft of section 7 stripped template tags and left their
    CONTENT, which is right for a bar whose {% if %} guards an attribute
    and wrong here: five of these controls sit behind
    can_edit_personal and each has an {% else %} twin, so the browser was
    handed EIGHT buttons and reported a strip that wrapped and
    overflowed a phone - on a page that renders five and does neither.

    Fifteenth time this week an instrument has measured something the
    page never shows. The user this round is for has the permission, so
    the branch the fixture takes is the true one."""
    prev = None
    while prev != html:
        prev = html
        html = IF_ELSE.sub(lambda m: m.group(1), html)
    prev = None
    while prev != html:
        prev = html
        html = IF_ONLY.sub(lambda m: m.group(1), html)
    return TAGS.sub('', html)
JS = """() => {
  const r = document.querySelector('.row-actions');
  if (!r) return null;
  const k = [...r.children];
  const tops = new Set(k.map(e => Math.round(e.getBoundingClientRect().top)));
  return {n: k.length, rows: tops.size,
          sizes: k.map(e => { const b = e.getBoundingClientRect();
                              return [Math.round(b.width), Math.round(b.height)]; }),
          overflow: document.documentElement.scrollWidth
                    > document.documentElement.clientWidth};
}"""

_PW = _BR = None


def browser():
    global _PW, _BR
    if _BR is None:
        _PW = sync_playwright().start()
        _BR = _PW.chromium.launch()
    return _BR


def strip_html():
    i = CODE.index('<div class="row-actions">')
    depth, j = 0, i
    while True:
        m = re.compile(r'</?div\b').search(CODE, j)
        if not m:
            break
        depth += 1 if CODE[m.start():m.start() + 2] == '<d' else -1
        j = m.end()
        if depth == 0:
            break
    # THE PERMITTED BRANCH, NOT BOTH - see take_the_if above.
    return take_the_if(CODE[i:j + 6])


def render(html, width):
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:8px;background:#fff}</style>'
           '<body>%s' % (FIX, css_of(read(alv_tree.path_of('base.html'))),
                         css_of(NOW), html))
    pg = browser().new_page(viewport={'width': width, 'height': 300})
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    try:
        return pg.evaluate(JS)
    finally:
        pg.close()


if sync_playwright is not None and FIX:
    html = strip_html()
    for w, label, floor in ((1280, 'desktop', 30), (390, 'phone', 40)):
        r = render(html, w)
        if not ok(r is not None, 'the week strip renders at %s' % label):
            continue
        ok(r['n'] == 5, '  five controls at %s' % label, r['n'])
        ok(r['rows'] == 1, '  on one row at %s' % label,
           '%d rows' % r['rows'])
        ok(not r['overflow'], '  and nothing scrolls sideways at %s' % label)
        small = [s for s in r['sizes'] if s[0] < floor or s[1] < floor]
        ok(not small,
           '  every target is at least %dpx at %s' % (floor, label), small)
else:
    skip('the rendered strip checks', 'no browser or no fixture')

# ==========================================================================
head('8. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
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

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
