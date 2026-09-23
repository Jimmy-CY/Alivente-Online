# -*- coding: utf-8 -*-
"""test_dead_files.py - Section D, round D1: four dead templates go, and
the orphan scan learns to read a script.

    python test_dead_files.py

Run from the repo root, after apply_dead_files.py.

  1. The four are gone, each with a backup, and nothing in the project
     names any of them - checked by reading every .py and .html, not by
     trusting the list.
  2. edit_meal_plan still works: its view renders create_meal_plan.html,
     and its URL still points at that view.
  3. script_names(), RUN rather than described: a name a script quotes is
     worn, a name it builds gives a prefix, and a plain word is neither.
  4. The record is corrected: .sorted-asc and .sorted-desc on the two
     Financials pages are NOT dead - both pages draw them at run time -
     and the orphan list no longer names them.
  5. The orphan count moved for that reason, and only that reason: fewer
     than the 282 Section D recorded, and the suite that reports it still
     passes.
  6. Registered in alv_rounds, and on the gate.
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
import subprocess
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import ROUNDS
except Exception as e:
    ROUNDS = []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_dead'
ME = 'test_dead_files.py'
PS1 = 'Push-PendingChanges.ps1'
PANEL = 'test_panel_title.py'
DEAD = ['map_test.html', 'edit_meal_plan.html',
        'create_recipe (OLD DO NOT USE).html',
        'edit_recipe (OLD DO NOT USE).html']
SORTERS = [os.path.join(T, 'finance', 'financial_indicators.html'),
           os.path.join(T, 'finance', 'vacancy_management.html')]
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


# ==========================================================================
head('1. THE FOUR ARE GONE, AND NOTHING NAMED THEM')
# ==========================================================================
for name in DEAD:
    p = os.path.join(T, name)
    ok(not os.path.isfile(p), '%-40s is gone' % name)
    ok(os.path.isfile(p + SUFFIX),
       '  and its backup is here, so the round can be undone')
hits = {}
for base, dirs, files in os.walk('pages'):
    dirs[:] = [d for d in dirs
               if d not in ('__pycache__',) and d != 'site-packages']
    for f in files:
        if not f.endswith(('.py', '.html')) or '.bak_' in f:
            continue
        body = read(os.path.join(base, f))
        for name in DEAD:
            if name in body:
                hits.setdefault(name, []).append(os.path.join(base, f))
ok(not hits, 'no view, no URL and no template names any of them',
   '\n'.join('%s <- %s' % (k, v[0]) for k, v in hits.items()))
_ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(not any(n in _ps1 for n in DEAD), '  and neither does the push gate')

# ==========================================================================
head('2. EDIT MEAL PLAN STILL WORKS')
# ==========================================================================
if not os.path.isfile(VIEW):
    skip('the meal-plan view', 'not in this checkout')
else:
    v = read(VIEW)
    m = re.search(r'def edit_meal_plan\(.*?(?=\ndef )', v, re.S)
    ok(m is not None, 'the edit_meal_plan view is still there')
    ok(m is not None and "render(request, 'create_meal_plan.html'"
       in m.group(0),
       '  and it renders create_meal_plan.html, as it always did')
    ok(m is not None and 'edit_meal_plan.html' not in m.group(0),
       '  and never named the empty file that has gone')
if os.path.isfile(URLS):
    ok(re.search(r"path\('meal_plans/<int:meal_plan_id>/edit/',\s*"
                 r"views\.edit_meal_plan", read(URLS)) is not None,
       'the URL still points at that view')

# ==========================================================================
head('3. script_names(), RUN - NOT DESCRIBED')
# ==========================================================================
panel = read(PANEL) if os.path.isfile(PANEL) else ''
m = re.search(r'\ndef script_names\(text\):.*?\n    return names, prefixes\n',
              panel, re.S)
ok(m is not None, 'the helper is in %s' % PANEL)
if m:
    ns = {'re': re}
    try:
        exec(m.group(0), ns)
        fn = ns['script_names']
        err = None
    except Exception as e:
        fn, err = None, e
    ok(fn is not None, '  and it compiles', err)
if m and fn:
    names, pres = fn("<script>el.classList.add('is-open');</script>")
    ok('is-open' in names, 'a name a script quotes is worn')
    names, pres = fn("<script>var c = 'sorted-' + dir;</script>")
    ok(any('sorted-'.startswith(p) or p == 'sorted-' for p in pres),
       'a name a script BUILDS gives a prefix', sorted(pres))
    names, pres = fn('<script>h.innerHTML = `<th class="hdr ${k}">`;'
                     '</script>')
    ok('hdr' in names, 'a class inside a template literal is worn',
       sorted(names))
    names, pres = fn('<script>var msg = "nothing to do";</script>')
    ok('nothing' in names and not pres,
       '  CONTROL: a plain word is a name and gives no prefix',
       (sorted(names), sorted(pres)))
    names, pres = fn('<p class="only-markup">x</p>')
    ok(not names and not pres,
       '  CONTROL: markup outside a script tells it nothing')

# ==========================================================================
head('4. THE SORT ARROWS WERE NEVER DEAD')
# ==========================================================================
for p in SORTERS:
    rel = os.path.relpath(p, T)
    src = read(p)
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))
    ok('.sorted-asc' in css and '.sorted-desc' in css,
       '%-34s still styles the sorted header' % rel)
    ok("'sorted-' +" in js or "'sorted-'+" in js,
       '  and its script writes the class at run time - it is alive')
    if m and fn:
        _n, _p = fn(src)
        ok(any('sorted-asc'.startswith(x) for x in _p),
           '  so the scan now counts it as worn', sorted(
               x for x in _p if x.startswith('sort')))

# ==========================================================================
head('5. THE ORPHAN LIST IS SMALLER, AND ONLY FOR THAT REASON')
# ==========================================================================
try:
    pr = subprocess.run([sys.executable, PANEL], cwd=ROOT,
                        capture_output=True, text=True, timeout=900)
    out = pr.stdout + pr.stderr
except Exception as e:
    out, pr = 'could not run: %s' % e, None
ok(pr is not None and pr.returncode == 0,
   '%s still passes' % PANEL, out[-400:])
c = re.search(r'(\d+) orphaned rule\(s\)', out)
ok(c is not None, 'it reports an orphan count', out[-300:])
if c:
    n = int(c.group(1))
    ok(n < 282, 'the count is %d, below the 282 Section D recorded' % n)
    ok(n > 100, '  and it is still a real list, not an empty one - the '
       'debt is smaller, not gone', n)
for gone in ('.sorted-asc', '.sorted-desc', '.an-chg', '.an-warn-icon'):
    ok(gone + ' ' not in out and gone + '\n' not in out,
       '  %-14s is no longer called an orphan' % gone)

# ==========================================================================
head('6. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_lease' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_lease'),
   'alv_rounds lists %s after .bak_lease' % SUFFIX)
_s = _ps1[_ps1.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
