# -*- coding: utf-8 -*-
"""BK-1 - BACK GOES WHERE YOU CAME FROM

Demetri, 3 Oct 2026: "If I am in Calendar View and I select a meal plan,
and the view or edit it, and I then press the back button, it needs to
bring me back to the Calendar view, not the List view."

==========================================================================
THE ORIGIN TRAVELS IN THE URL
==========================================================================
The Calendar links to a plan as

    .../meal_plans/8/?from=calendar&week=2026-09-28

and View, Edit and the Shopping List send Back there instead of to the
list. Demetri chose this over the referrer, and it is the better of the
two: a referrer is blank on a refresh and blank on a bookmark, so it
needs a fallback anyway, and then there are two mechanisms where one
would do. Nothing is remembered behind anyone's back.

THE WEEK TRAVELS WITH IT. A calendar you return to showing a different
week has not brought you back; it has taken you somewhere else that looks
similar. selected_week_start is what the page is already showing, so it
costs one parameter.

==========================================================================
AND IT FALLS BACK TO THE LIST, ALWAYS
==========================================================================
Reached any other way - from the list, from a bookmark, from a link in an
email - there is no from= and Back goes to Meal Plans exactly as it does
today. The three pages are unchanged for every reader who did not come
from the calendar.

Backups: .bak_fromcal. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_fromcal'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

CAL = alv_tree.path_of('meal_plan_calendar.html')
VIEW = alv_tree.path_of('view_meal_plan.html')
EDIT = alv_tree.path_of('create_meal_plan.html')
SHOP = alv_tree.path_of('meal_plan_shopping_list.html')

# The query the calendar hangs on every link out to a plan.
Q = ("?from=calendar&amp;week={{ selected_week_start|date:'Y-m-d' }}")

# What Back points at, on a page that may have been reached from either.
BACK = ("{% if request.GET.from == 'calendar' %}"
        "{% url 'meal_plan_calendar' %}"
        "?week={{ request.GET.week }}"
        "{% else %}{% url 'meal_plans' %}{% endif %}")

NOTE = (
    "{# BK-1, 3 Oct 2026 - BACK GOES WHERE YOU CAME FROM. The Calendar   #}\n"
    "{# links here with from=calendar and the week it was showing, so    #}\n"
    "{# Back returns to THAT week. Reached any other way there is no     #}\n"
    "{# from= and this is the Meal Plans list, exactly as before.        #}\n")


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('BK1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what, times=1):
    c = text.count(old)
    if c != times:
        raise SystemExit('BK1: %s appears %d times, not %d'
                         % (what, c, times))
    return text.replace(old, new)


print('=' * 74)
print('BK-1 - BACK GOES WHERE YOU CAME FROM%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE CALENDAR SAYS WHERE THE READER IS.
# ==========================================================================
t, raw = read(CAL)
nl = t.replace('\r\n', '\n')
if 'from=calendar' in nl:
    print('  meal_plan_calendar.html    already carries the origin')
else:
    for name in ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list'):
        old = ("{%% url '%s' selected_meal_plan.meal_plan_id %%}\"" % name)
        nl = swap(CAL, nl, old, old[:-1] + Q + '"', 'the %s link' % name)
    out = nl.replace('\n', '\r\n') if CRLF.get(CAL) else nl
    if not CHECK:
        back_up(CAL, raw)
        write(CAL, out)
    print('  meal_plan_calendar.html    three links carry from=calendar '
          'and the week')

# ==========================================================================
# 2. THE THREE PAGES READ IT.
# ==========================================================================
OLD_BACK = "<a href=\"{% url 'meal_plans' %}\" class=\"btn action-back\""
for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html'),
                    (SHOP, 'meal_plan_shopping_list.html')):
    t, raw = read(path)
    nl = t.replace('\r\n', '\n')
    if "request.GET.from == 'calendar'" in nl:
        print('  %-26s already reads it' % label)
        continue
    if OLD_BACK not in nl:
        # THE SHOPPING LIST IS A HOP, NOT A DESTINATION. Its Back already
        # goes to the plan, which is right - so it PASSES THE ORIGIN ON,
        # and the chain closes: Calendar, Shopping List, Back to the plan,
        # Back to the Calendar on the week it was showing. A page that
        # swallowed the origin here would strand the reader one hop short.
        OLD_HOP = "{% url 'view_meal_plan' meal_plan.meal_plan_id %}"
        if OLD_HOP not in nl:
            print('  %-26s no Back control, skipped' % label)
            continue
        nl = swap(path, nl, OLD_HOP,
                  OLD_HOP + "{% if request.GET.from == 'calendar' %}"
                  "?from=calendar&amp;week={{ request.GET.week }}{% endif %}",
                  'the hop back to the plan in %s' % label,
                  times=nl.count(OLD_HOP))
        out = nl.replace('\n', '\r\n') if CRLF.get(path) else nl
        if not CHECK:
            back_up(path, raw)
            write(path, out)
        print('  %-26s passes the origin on to the plan' % label)
        continue
    indent = ''
    i = nl.index(OLD_BACK)
    j = nl.rindex('\n', 0, i) + 1
    indent = nl[j:i]
    nl = swap(path, nl, OLD_BACK,
              NOTE.replace('{#', indent + '{#', 1)
                  .replace('\n{#', '\n' + indent + '{#') + indent
              + '<a href="' + BACK + '" class="btn action-back"',
              'the Back control in %s' % label)
    out = nl.replace('\n', '\r\n') if CRLF.get(path) else nl
    if not CHECK:
        back_up(path, raw)
        write(path, out)
    print('  %-26s Back follows the origin' % label)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
cal = alv_tree.code_only(read(CAL)[0])

# 1. EVERY LINK OUT OF THE CALENDAR TO A PLAN CARRIES THE ORIGIN. Asked of
#    the links, not of a count typed here: a fourth action added later
#    would be caught.
links = re.findall(r'<a href="(\{% url \'(?:view_meal_plan|edit_meal_plan|'
                   r'meal_plan_shopping_list)\'[^"]*)"', cal)
if len(links) != 3:
    raise SystemExit('BK1: %d links out of the calendar, expected 3'
                     % len(links))
for href in links:
    if 'from=calendar' not in href:
        raise SystemExit('BK1: a calendar link carries no origin: %s'
                         % href[:70])
    if 'selected_week_start' not in href:
        raise SystemExit('BK1: a calendar link carries no week - returning '
                         'to a different week is not returning')
print('  all 3 links out of the calendar carry the origin and the week')

# 2. AND THE SEPARATOR IS AN ENTITY. An ampersand written raw in an href
#    is the oldest HTML bug there is, and a validator reads &week as a
#    character reference.
for href in links:
    if '&amp;' not in href or re.search(r'&(?!amp;)', href):
        raise SystemExit('BK1: a bare ampersand in %s' % href[:70])
print('  the separator is &amp; and not a bare ampersand')

# 3. THE THREE PAGES SEND BACK TO THE CALENDAR WHEN TOLD, AND TO THE LIST
#    OTHERWISE. BOTH BRANCHES, because a conditional with one arm is not
#    a conditional.
for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html')):
    s = alv_tree.code_only(read(path)[0])
    m = re.search(r'<a href="([^"]*)" class="btn action-back"', s)
    if not m:
        raise SystemExit('BK1: %s has no Back control' % label)
    href = m.group(1)
    if "request.GET.from == 'calendar'" not in href:
        raise SystemExit('BK1: %s does not read the origin' % label)
    if "{% url 'meal_plan_calendar' %}" not in href:
        raise SystemExit('BK1: %s never points at the calendar' % label)
    if "{% url 'meal_plans' %}" not in href:
        raise SystemExit('BK1: %s lost its fallback to the list' % label)
    print('  %-26s calendar when told, the list otherwise' % label)

# 4. CONTROL: BEFORE THIS ROUND ALL THREE WENT TO THE LIST, FULL STOP.
for path, label in ((VIEW, 'view_meal_plan.html'),
                    (EDIT, 'create_meal_plan.html')):
    was = read(path + SUFFIX)[0]
    m = re.search(r'<a href="([^"]*)" class="btn action-back"',
                  alv_tree.code_only(was))
    if not m or 'meal_plan_calendar' in m.group(1):
        raise SystemExit('BK1: CONTROL FAILED - %s already knew about the '
                         'calendar' % label)
print('  CONTROL: before this round both went to the list and nowhere else')

# 4b. AND THE SHOPPING LIST PASSES THE ORIGIN ON RATHER THAN SWALLOWING IT.
#     It is a hop: its Back goes to the plan, and the plan goes home.
shop = alv_tree.code_only(read(SHOP)[0])
hops = re.findall(r"\{% url 'view_meal_plan' meal_plan\.meal_plan_id %\}"
                  r"(\{% if request\.GET\.from[^%]*%\})?", shop)
if not hops:
    raise SystemExit('BK1: the shopping list has no hop back to the plan')
if not all(hops):
    raise SystemExit('BK1: %d of %d hops back to the plan drop the origin'
                     % (len([h for h in hops if not h]), len(hops)))
print('  all %d hops out of the shopping list pass the origin on' % len(hops))

# 5. THE URL NAMES RESOLVE. A name typed wrong raises at RENDER time, on
#    the page, not here - so it is checked against urls.py.
urls = ''
for root, _, files in os.walk(os.path.join(ROOT, 'pages')):
    for f in files:
        if f == 'urls.py':
            urls += read(os.path.join(root, f))[0]
if not urls:
    urls = read(os.path.join(ROOT, 'mysite', 'urls.py'))[0]
for name in ('meal_plan_calendar', 'meal_plans'):
    if "name='%s'" % name not in urls and 'name="%s"' % name not in urls:
        raise SystemExit('BK1: no url named %s - the tag would raise on the '
                         'page' % name)
print('  both url names exist in urls.py')

# 6. AND THE CALENDAR READS week= ALREADY, so the trip home lands where it
#    left. This is the half that makes gate 1 worth anything.
v = ''
for root, _, files in os.walk(os.path.join(ROOT, 'pages', 'views')):
    for f in files:
        if f == 'meal_planning.py':
            v = read(os.path.join(root, f))[0]
if "request.GET.get('week')" not in v:
    raise SystemExit('BK1: the calendar view does not read week - the '
                     'parameter would travel and do nothing')
print('  the calendar view reads week, so Back lands on the week you left')

print('-' * 74)
print('  The origin travels in the URL, so a refresh and a bookmark say')
print('  the same thing a click does, and nothing is remembered behind')
print('  anyone back.')
print('=' * 74)
