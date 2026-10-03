# -*- coding: utf-8 -*-
"""test_meal_row.py - Section ML round ML-1, 2 Oct 2026.

Demetri, with a screenshot of Meal Plans: "This table also needs to be
addressed."

Five filled buttons per row - View #007bff, Edit #ffc107, List #28a745,
Duplicate #0e7c8b, Delete #dc3545 - each with a rule and a hover rule of
its own, on a page carrying 54 local rules and 24 literal colours for a
component base has owned for weeks and that 170 other controls already
use.

SECTION 2 NEEDS A BROWSER, and the claim it makes is not "it looks nicer".
It is that the page is now getting its appearance FROM base: the five
controls are measured against the same controls rendered on a plain base
page, and every box, colour and border must agree. A page that merely
looks similar is a page that has copied the component again.

SECTION 3 IS THE ONE ADDITION TO base, AND IT IS A NAME. There was no icon
name for a shopping list, so .icon-list was added - on var(--alv-view), the
colour .icon-view, .icon-manage and .icon-event already share. base's own
note against .icon-manage states the rule: "the third NAME on an existing
colour, and for the same reason". This suite asserts the palette did not
grow: base's literal-colour count is the same on both sides.

SECTION 4 IS J-2 APPLIED HERE. The phone bar repeats every action, so
leaving the plan name in an onclick would have meant writing it into a JS
string ten times a row instead of carrying it once. It is data-plan-name
now, with one delegated listener per action serving both strips.

WHAT THIS SUITE DOES NOT DO. It does not assert that five controls render;
eight are WRITTEN per strip, because Edit, Duplicate and Delete each have a
permitted form and a disabled one, and only five ever render at once. It
counts what is written and says which is which.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_mealrow'
ME = 'test_meal_row.py'
PATCHER = 'apply_meal_row.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
MP = alv_tree.path_of('meal_plans.html')
BASE = alv_tree.path_of('base.html')

GONE = ('btn-view', 'btn-edit', 'btn-shopping', 'btn-duplicate', 'btn-delete')
LITERALS = ('#007bff', '#0056b3', '#ffc107', '#e0a800', '#28a745', '#218838',
            '#dc3545', '#c82333')

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
code_only = alv_tree.code_only_js


def css_of(t):
    return '\n'.join(STYLE.findall(t))


MP_NOW, MP_WAS = now(MP), was(MP)
CODE = code_only(MP_NOW)
CSS = css_of(CODE)

print('=' * 74)
print('%s - ML-1, THE MEAL PLANS ROW' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PAGE STOPPED PAYING FOR A COMPONENT base OWNS')
# ==========================================================================
for g in GONE:
    ok(g not in CODE, 'the page has no .%s left' % g)

if MP_WAS:
    W = code_only(MP_WAS)
    cw = css_of(W)
    ok(len([g for g in GONE if g in W]) == len(GONE),
       'CONTROL: it carried all five of those names')
    rw = len(re.findall(r'(?m)^\s*\.[\w.-][^\n{}]*\{', cw))
    rn = len(re.findall(r'(?m)^\s*\.[\w.-][^\n{}]*\{', CSS))
    ok(rn < rw, 'local rules %d -> %d' % (rw, rn), '%d vs %d' % (rn, rw))
    lw = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', cw))
    ln = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', CSS))
    ok(ln < lw, 'literal colours %d -> %d' % (lw, ln), '%d vs %d' % (ln, lw))
    # PER-LITERAL, NOT PRESENCE - this page keeps colours in rules the
    # round never touched, so "gone" would be a claim about the wrong thing.
    for lit in LITERALS:
        a, b = CSS.lower().count(lit), cw.lower().count(lit)
        ok(a < b, '  %s  %d -> %d' % (lit, b, a), '%d vs %d' % (a, b))
else:
    skip('the before/after counts', 'no %s backup' % SUFFIX)
    skipped += 10

# EIGHT CONTROLS PER STRIP, NOT FIVE, AND THE SUITE SAYS WHY.
for cls in ('icon-action-btn', 'mobile-action-btn'):
    ok(CODE.count(cls) == 8,
       '%-18s is written 8 times - 2 always-on, plus 3 actions that have a '
       'permitted form AND a disabled one' % cls, CODE.count(cls))
ok(CODE.count('icon-disabled') == 3 and
   CODE.count('mobile-action-disabled') == 3,
   '  of which 3 per strip are the disabled halves',
   '%d / %d' % (CODE.count('icon-disabled'),
                CODE.count('mobile-action-disabled')))

for url in ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list',
            'duplicate_meal_plan', 'delete_meal_plan'):
    n = len(re.findall(r"\{%\s*url '" + url + r"'", CODE))
    ok(n == 2, '%-26s is linked from both strips' % url, n)

used = set(re.findall(r'\bicon-(?:action-btn|color-)?([a-z]+)\b', CODE))
used -= {'action', 'btn'}
bs = read(BASE)
missing = [u for u in sorted(used) if '.icon-%s' % u not in bs
           and '.icon-color-%s' % u not in bs]
ok(not missing, 'and all %d icon names used are ones base defines' % len(used),
   missing)

# ==========================================================================
head('2. RENDERED - THE PAGE GETS ITS LOOK FROM base, NOT FROM A COPY')
# ==========================================================================
# THE CLAIM IS NOT "IT LOOKS NICER". It is that these five controls are now
# base's controls: drawn against a plain base page with no meal_plans CSS
# at all, they must come out IDENTICAL. A page that merely looks similar is
# a page that has copied the component a second time.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

# EVERY ANCHOR CARRIES AN href, AND THAT IS NOT COSMETIC. Bootstrap ships
# `a:not([href]):not([tabindex]) { color: inherit }`, which is (0,2,1) and
# beats `.icon-view` at (0,1,0) - so a fixture anchor written without one
# comes back the body colour and every icon looks identically tinted. The
# first draft of this suite did exactly that, reported all six the same,
# and sent me looking for a defect in base that was not there. A fixture
# <a> with no href is not the <a> the page ships.
#
# The ELEMENT TYPE is uniform here for the same reason: <a> and <button>
# have different default colours, so a strip that mixes them measures the
# tag and not the class.
STRIP = ('<div class="row-actions">' + ''.join(
    '<a href="#" class="icon-action-btn %s"><i class="fas fa-eye"></i></a>' % c
    for c in ('icon-view', 'icon-edit', 'icon-list', 'icon-duplicate',
              'icon-delete', 'icon-disabled')) + '</div>')
LOOK = '''() => [...document.querySelectorAll('.icon-action-btn')].map(e => {
    const c = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    return {cls: e.className, bg: c.backgroundColor, fg: c.color,
            bd: c.borderTopColor + ' ' + c.borderTopWidth,
            w: Math.round(r.width), h: Math.round(r.height)};
})'''

if HAVE_PW and os.path.isfile(BOOT):
    boot = read(BOOT)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 600})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(extra_css, name, w=1280):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style><style>%s</style>'
                         '</head><body><div class="container">%s</div>'
                         '</body></html>'
                         % (boot, css_of(code_only(read(BASE))), extra_css,
                            STRIP))
            pg.set_viewport_size({'width': w, 'height': 600})
            _goto(pg, f)
            pg.wait_for_timeout(50)
            return pg.evaluate(LOOK)

        bare = draw('', 'bare.html')
        withpage = draw(CSS, 'withpage.html')
        ok(len(bare) == 6, 'six controls drawn', len(bare))
        same = [a == b for a, b in zip(bare, withpage)]
        ok(all(same),
           'every control renders IDENTICALLY with and without the page\'s '
           'own CSS - the look comes from base',
           [(a['cls'], a, b) for a, b, s in zip(bare, withpage, same)
            if not s][:2])
        for b in bare:
            ok(b['w'] >= 28 and b['h'] >= 28,
               '  %-34s %dx%d, bg %s' % (b['cls'].replace('icon-action-btn ',
                                                          ''),
                                         b['w'], b['h'], b['bg']), b)

        # EACH NAME IS A DIFFERENT COLOUR FROM ITS NEIGHBOURS WHERE IT
        # SHOULD BE, AND THE SAME WHERE base SAYS IT SHOULD BE.
        by = dict((b['cls'].split()[-1], b) for b in bare)
        ok(by['icon-view']['fg'] == by['icon-list']['fg'],
           'icon-list is the SAME ink as icon-view - a name, not a new '
           'tone: %s' % by['icon-list']['fg'],
           (by['icon-view']['fg'], by['icon-list']['fg']))
        ok(by['icon-view']['bd'] == by['icon-list']['bd'],
           '  and the same border with it', (by['icon-view']['bd'],
                                             by['icon-list']['bd']))
        ok(by['icon-duplicate']['fg'] == by['icon-edit']['fg'],
           '  duplicate rides on edit, which base already said: %s'
           % by['icon-duplicate']['fg'],
           (by['icon-duplicate']['fg'], by['icon-edit']['fg']))
        ok(by['icon-delete']['fg'] != by['icon-view']['fg'],
           '  and delete is its own, as it has to be - %s against %s'
           % (by['icon-delete']['fg'], by['icon-view']['fg']),
           (by['icon-delete']['fg'], by['icon-view']['fg']))
        ok(len({by[k]['fg'] for k in ('icon-view', 'icon-edit',
                                      'icon-delete')}) == 3,
           '  three distinct inks across view, edit and delete - the strip '
           'is not one flat colour',
           sorted({by[k]['fg'] for k in ('icon-view', 'icon-edit',
                                         'icon-delete')}))
        br.close()
elif not HAVE_PW:
    print('  --   the browser section  (no playwright)')
    skipped += 14
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 13

# ==========================================================================
head('3. ONE NAME IN base, AND NOT ONE COLOUR')
# ==========================================================================
BS = code_only(read(BASE))
m = re.search(r'\.icon-list\s*\{([^}]*)\}', BS)
ok(bool(m), 'base defines .icon-list')
if m:
    ok('var(--alv-view)' in m.group(1),
       '  on var(--alv-view) - the colour icon-view, icon-manage and '
       'icon-event already share', m.group(1).strip())
    ok(not re.search(r'#[0-9a-fA-F]{3,6}\b', m.group(1)),
       '  with no literal colour of its own', m.group(1).strip())
if was(BASE):
    a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', BS))
    b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(was(BASE))))
    ok(a == b, 'and base gained NO literal colour: %d -> %d' % (b, a),
       '%d -> %d' % (b, a))
    ok('.icon-list' not in code_only(was(BASE)),
       'CONTROL: base had no .icon-list before this round')
else:
    skip('the base controls', 'no %s backup' % SUFFIX)
    skipped += 1

# ==========================================================================
head('4. AND THE PLAN NAME TRAVELS AS AN ATTRIBUTE - J-2 APPLIED HERE')
# ==========================================================================
ok(not re.search(r'onclick="confirm(?:Delete|Duplicate)\(', CODE),
   'no handler carries the plan name')
ok(len(re.findall(r'data-plan-name="\{\{ plan\.plan_name \}\}"', CODE)) == 4,
   'all four buttons carry data-plan-name',
   len(re.findall(r'data-plan-name=', CODE)))
for cls in ('.js-duplicate-plan', '.js-delete-plan'):
    ok(MP_NOW.count("e.target.closest('%s')" % cls) == 1,
       'one delegated listener for %s, serving BOTH strips' % cls,
       MP_NOW.count("e.target.closest('%s')" % cls))
ok('function confirmDelete(button, mealPlanName)' in MP_NOW
   and 'function confirmDuplicate(button, mealPlanName)' in MP_NOW,
   '  and both functions keep their signatures - only the caller changed')
if MP_WAS:
    ok(bool(re.search(r"onclick=\"confirmDuplicate\(this, '\{\{ plan\.plan_name",
                      code_only(MP_WAS))),
       'CONTROL: the name used to go into the handler as a JS string')
    ok('data-plan-name' not in MP_WAS,
       '  and no button carried it as an attribute')
else:
    skip('the handler controls', 'no %s backup' % SUFFIX)
    skipped += 1

ok(not [i for i, line in enumerate(MP_NOW.split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')
ok(CSS.count('{') == CSS.count('}'), 'and the page CSS still balances')

# ==========================================================================
head('5. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_sentinels'),
       '  and AFTER .bak_sentinels, the round it followed')
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


def _strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


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
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
