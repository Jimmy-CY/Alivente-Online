# -*- coding: utf-8 -*-
"""test_from_calendar.py - Section BK round BK-1, 3 Oct 2026.

Demetri, 3 Oct 2026: "If I am in Calendar View and I select a meal plan,
and the view or edit it, and I then press the back button, it needs to
bring me back to the Calendar view, not the List view."

THE ORIGIN TRAVELS IN THE URL. Demetri chose that over the referrer, and
it is the better of the two: a referrer is blank on a refresh and blank on
a bookmark, so it needs a fallback anyway - and then there are two
mechanisms where one would do.

AND THE WEEK TRAVELS WITH IT. A calendar you return to showing a different
week has not brought you back; it has taken you somewhere else that looks
similar.

SECTION 4 IS THE CHAIN. The Shopping List is a HOP, not a destination -
its Back already goes to the plan, which is right - so it passes the
origin ON, and the chain closes: Calendar, Shopping List, Back to the
plan, Back to the Calendar, on the week it was showing. A page that
swallowed the origin there would strand the reader one hop short, and
nothing in sections 1 to 3 would notice.
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

SUFFIX = '.bak_fromcal'
ME = 'test_from_calendar.py'
PATCHER = 'apply_from_calendar.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_fromcal_')

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


def source(*parts):
    """A python file of this project, BY ITS PATH, not by walking for it.

    A walk here would put this suite on the debt register that
    test_waiting_down keeps - os.walk over a root a file built for itself
    is exactly what alv_tree exists to replace - and it would find the
    first file of that name anywhere under the tree, backups included.
    Named, so a file that moves makes the gate SKIP and say so rather
    than quietly measure something else."""
    p = os.path.join(ROOT, *parts)
    return read(p) if os.path.isfile(p) else ''


CAL = alv_tree.path_of('meal_plan_calendar.html')
VIEW = alv_tree.path_of('view_meal_plan.html')
EDIT = alv_tree.path_of('create_meal_plan.html')
SHOP = alv_tree.path_of('meal_plan_shopping_list.html')
OUT = ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list')


def back_href(src):
    m = re.search(r'<a href="([^"]*)" class="btn action-back"',
                  alv_tree.code_only(src))
    return m.group(1) if m else None


# ==========================================================================
head('1. THE CALENDAR SAYS WHERE THE READER IS')
# ==========================================================================
cal = alv_tree.code_only(now(CAL))
links = re.findall(
    r'<a href="(\{%% url \'(?:%s)\'[^"]*)"' % '|'.join(OUT), cal)
ok(len(links) == 3, '%d links out of the calendar to a plan' % len(links))
for href in links:
    name = re.search(r"url '(\w+)'", href).group(1)
    ok('from=calendar' in href, '  %-24s carries the origin' % name)
    ok('selected_week_start' in href,
       '  %-24s carries the week it is showing' % name)

# THE SEPARATOR IS AN ENTITY. A bare ampersand in an href is the oldest
# HTML bug there is, and a validator reads &week as a character reference.
for href in links:
    ok('&amp;' in href and not re.search(r'&(?!amp;)', href),
       'and its separator is &amp;, not a bare ampersand')

old = was(CAL)
if old:
    o = re.findall(r'<a href="(\{%% url \'(?:%s)\'[^"]*)"' % '|'.join(OUT),
                   alv_tree.code_only(old))
    ok(o and not any('from=' in h for h in o),
       'CONTROL: before this round none of them did')
else:
    skip('CONTROL: before this round none of them did', 'no backup')

# ==========================================================================
head('2. THE TWO DESTINATIONS READ IT, AND KEEP THEIR FALLBACK')
# ==========================================================================
for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html')):
    href = back_href(now(path))
    ok(href is not None, '%s has a Back control' % label)
    if not href:
        continue
    ok("request.GET.from == 'calendar'" in href,
       '  it reads the origin')
    ok("{% url 'meal_plan_calendar' %}" in href,
       '  and points at the calendar when told')
    ok("{% url 'meal_plans' %}" in href,
       '  and at the list otherwise - a conditional with one arm is not '
       'a conditional')
    ok('week=' in href, '  taking the week back with it')

for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html')):
    o = was(path)
    if not o:
        skip('CONTROL: %s went to the list and nowhere else' % label,
             'no backup')
        continue
    h = back_href(o)
    ok(h and 'meal_plan_calendar' not in h,
       'CONTROL: %s went to the list and nowhere else' % label)

# ==========================================================================
head('3. THE TEMPLATE TAGS RESOLVE')
# ==========================================================================
# A url name typed wrong raises NoReverseMatch at RENDER time - on the
# page, in front of him, not here.
urls = source('pages', 'urls.py') + source('mysite', 'urls.py')
ok(urls, 'urls.py is where this suite says it is')
for name in ('meal_plan_calendar', 'meal_plans') + OUT:
    ok("name='%s'" % name in urls or 'name="%s"' % name in urls,
       'url name %-24s exists' % name)

v = source('pages', 'views', 'recipes', 'meal_planning.py')
ok(v and "request.GET.get('week')" in v,
   'and the calendar view reads week, so the trip home lands where it left')

# ==========================================================================
head('4. THE CHAIN - THE SHOPPING LIST IS A HOP')
# ==========================================================================
shop = alv_tree.code_only(now(SHOP))
hops = re.findall(
    r"\{% url 'view_meal_plan' meal_plan\.meal_plan_id %\}"
    r"(\{% if request\.GET\.from[^%]*%\}[^{]*\{\{[^}]*\}\}\{% endif %\})?",
    shop)
ok(hops, '%d link(s) out of the shopping list go to the plan' % len(hops))
ok(all(hops), 'and every one of them passes the origin on',
   '%d drop it' % len([h for h in hops if not h]))
ok(back_href(now(SHOP)) and 'view_meal_plan' in back_href(now(SHOP)),
   'its Back still goes to the plan - it is a hop, not a destination')

o = was(SHOP)
if o:
    oh = re.findall(
        r"\{% url 'view_meal_plan' meal_plan\.meal_plan_id %\}"
        r"(\{% if request\.GET\.from)?", alv_tree.code_only(o))
    ok(oh and not any(oh),
       'CONTROL: before this round not one of them did, so the chain '
       'broke at the first hop')
else:
    skip('CONTROL: before this round not one of them did', 'no backup')

# ==========================================================================
head('5. AND EVERY OTHER WAY IN IS UNCHANGED')
# ==========================================================================
# Reached from the list, from a bookmark, from a link in an email, there
# is no from= and Back goes where it always went. The fallback is not a
# nicety - it is what every reader who did not come from the calendar
# gets, which is most of them.
for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html')):
    href = back_href(now(path)) or ''
    i = href.find('{% else %}')
    ok(i > 0 and "{% url 'meal_plans' %}" in href[i:],
       '%s: the else branch is the list' % label)

# AND THE LIST PAGE ITSELF NEVER LEARNED ABOUT ANY OF THIS.
plans = alv_tree.code_only(now(alv_tree.path_of('meal_plans.html')))
ok('from=calendar' not in plans,
   'CONTROL: meal_plans.html carries no origin - it IS the fallback')

# ==========================================================================
head('6. REGISTERED')
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
