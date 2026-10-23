# -*- coding: utf-8 -*-
"""test_print_origin.py - round PT-1, 22 Oct 2026.

THE PRINT SHEET DID NOT KNOW WHICH VIEW SENT IT.

Demetri, 22 October, five findings about Print in Meal Plans:

  1. Day View must not offer the date options at all.
  2. Week View must bound them to the week shown, and print only the
     range selected.
  3. Back from a printed week must return to that week.
  4. Back from a printed day must return to that day.
  5. Back from a printed month must return to that month.

FIVE FINDINGS, ONE CAUSE. meal_plan_print took ?from= and ?to= and
nothing else. The SHAPE of the sheet is worked out from those two
dates - RG-1 does that deliberately - but the ORIGIN cannot be: a day
sheet and a one-day range are the same two dates, and a week sheet and
a Monday-to-Sunday range are the same two dates. Back was therefore
the bare planner URL and landed on the default view on today's date.

SECTION 3 DRIVES ALL FOUR ORIGINS through the real view and reads the
real HTML back. Section 4 drives the two things a browser would not
stop: a ?from= outside the week, typed, and a week narrowed to three
days. A min attribute is a request to a browser; the clamp is what
makes it true, and only one of those can be tested by reading markup.

SECTION 5 IS THE ONE THAT OVERRULES AN EARLIER ROUND. RG-1 renders
whole Monday-to-Sunday weeks and greys the days outside the range, so
that three blank cells at the front of a seven-column grid do not read
as missing data. Demetri overruled it: "the print must only show, and
then only print the date range selected." The crop is claimed here,
and so is the thing that makes it legible - a grid with as many
columns as it has days.
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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_printorigin'
ME = 'test_print_origin.py'
PATCHER = 'apply_print_origin.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PT-1, 22 Oct 2026'

VIEWS = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
PRINT = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_print.html')
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEWS, PRINT, PLANNER)

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def claims(d):
    v = T.python_code_only(d[VIEWS], payloads=True)
    t = T.code_only(d[PRINT])
    p = T.code_only(d[PLANNER])
    return {
        'the view reads which view sent the reader':
            "origin = request.GET.get('view')" in v,
        '  and the date that view was showing':
            "came_from = week_of(request.GET.get('date'), None)" in v,
        'the bounds come from that period':
            'range_min = monday_of(came_from)' in v,
        '  and the SERVER clamps, not only the browser':
            'start = min(max(start, range_min), range_max)' in v,
        'Back is built from the origin':
            "back_url = '%s?view=%s&date=%s'" in v,
        'the range form is conditional':
            '{% if show_range %}' in t,
        '  and Back uses the built address':
            '{{ back_url }}' in t,
        '  and the pickers carry min and max':
            t.count('min="{{ range_min|date:\'Y-m-d\' }}"') == 2,
        'a narrowed period is cropped':
            'crop = bool(range_min and range_max' in v,
        '  and the weekday strip goes with it':
            "{% if sheet != 'week' and not crop %}" in t,
        '  and the grid takes as many columns as it has days':
            'repeat({{ week.cols }}' in t,
        'both print links carry the origin':
            p.count('&amp;view={{ view_mode }}&amp;date={{ anchor') == 2,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(not held, 'CONTROL: not one of this round holds before it',
   '\n'.join(held))

oldt = T.code_only(OLD[PRINT])
ok("<a href=\"{% url 'meal_planner' %}\" class=\"btn action-back\"" in oldt,
   'CONTROL: Back really was the bare planner URL - findings 3, 4 and 5')
ok('{% if show_range %}' not in oldt,
   'CONTROL: and the range form was rendered whatever sent you')
ok('min="' not in oldt,
   'CONTROL: and the pickers offered every date there is')


# ==========================================================================
head('3. DRIVEN - all four origins, through the real view')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('sections 3, 4 and 5', 'no database')
else:
    from django.contrib.auth.models import User
    from django.test import Client

    # A MONDAY, SO THE WEEK ARITHMETIC IS NOT A COINCIDENCE.
    MON = '2026-10-19'
    SUN = '2026-10-25'

    try:
        boss = User.objects.create_superuser('pt1boss', 'pt1@x.com', 'x')
        cl = Client()
        cl.force_login(boss)

        def sheet(**qs):
            url = '/meal_plans/print/'
            if qs:
                url += '?' + '&'.join('%s=%s' % kv for kv in qs.items())
            r = cl.get(url)
            return r.status_code, r.content.decode('utf-8', 'replace')

        # ---- DAY
        code, html = sheet(**{'from': MON, 'to': MON,
                              'view': 'day', 'date': MON})
        ok(code == 200, 'the day sheet renders', code)
        ok('id="ppFrom"' not in html,
           'DAY: the date options are NOT on the page at all',
           'finding 1')
        ok('Show these days' not in html,
           '  nor the button that would apply them')
        # READ THE RENDERED LINK, do not guess the address. The first
        # version of this typed the planner's URL and failed on a
        # claim that was about nothing but my spelling.
        def back_href(h):
            m = re.search(r'<a href="([^"]*)"\s+class="btn action-back"',
                          h)
            return m.group(1) if m else ''

        bh = back_href(html)
        ok('view=day' in bh and MON in bh,
           'DAY: Back returns to the day that was showing', bh)

        # ---- WEEK
        code, html = sheet(**{'from': MON, 'to': SUN,
                              'view': 'week', 'date': MON})
        ok(code == 200, 'the week sheet renders', code)
        ok('id="ppFrom"' in html, 'WEEK: the date options ARE offered')
        ok(html.count('min="%s"' % MON) == 2
           and html.count('max="%s"' % SUN) == 2,
           'WEEK: and both pickers are bounded to the week below',
           'finding 2 - min %d, max %d'
           % (html.count('min="%s"' % MON), html.count('max="%s"' % SUN)))
        ok('view=week' in html and MON in html,
           'WEEK: Back returns to the week that was showing')

        # ---- MONTH
        code, html = sheet(**{'from': '2026-10-01', 'to': '2026-10-31',
                              'view': 'month', 'date': '2026-10-01'})
        ok(code == 200, 'the month sheet renders', code)
        ok(html.count('min="2026-10-01"') == 2
           and html.count('max="2026-10-31"') == 2,
           'MONTH: bounded to the month below')
        ok('view=month' in html,
           'MONTH: Back returns to the month that was showing',
           'finding 5')

        # ---- NOTHING PASSED, which must behave exactly as before
        code, html = sheet(**{'from': MON, 'to': SUN})
        ok(code == 200, 'and a hand-typed address still renders', code)
        ok('id="ppFrom"' in html and 'min="' not in html,
           '  with the form shown and no bounds, as it always was')

        # ==============================================================
        head('4. DRIVEN - what a browser would not stop')
        # ==============================================================
        # min= IS A REQUEST TO A BROWSER. ?from= is a string anybody
        # can type, and A5 says every one of these falls back rather
        # than raising. Only the server can make the bound true.
        code, html = sheet(**{'from': '2026-01-01', 'to': SUN,
                              'view': 'week', 'date': MON})
        ok(code == 200, 'a from-date outside the week still renders', code)
        ok('value="%s"' % MON in html,
           'CLAMPED: it is pulled back to the first day of the week',
           re.findall(r'id="ppFrom"[^>]*', html)[:1])
        ok('2026-01-01' not in html,
           '  and the date that was typed is gone entirely')

        code, html = sheet(**{'from': MON, 'to': '2027-12-31',
                              'view': 'week', 'date': MON})
        ok('value="%s"' % SUN in html,
           'CLAMPED: and a to-date past the week comes back to Sunday',
           re.findall(r'id="ppTo"[^>]*', html)[:1])

        # ==============================================================
        head('5. DRIVEN - a narrowed week prints only what was asked')
        # ==============================================================
        # THIS OVERRULES RG-1, which renders whole Monday-to-Sunday
        # weeks and greys what is outside the range. Demetri, 22 Oct:
        # "the print must only show, and then only print the date
        # range selected."
        code, html = sheet(**{'from': '2026-10-21', 'to': '2026-10-23',
                              'view': 'week', 'date': MON})
        ok(code == 200, 'a three-day slice of a week renders', code)
        cells = html.count('class="pp-day')
        ok(cells == 3,
           'CROPPED: three day cells, not seven', '%d cells' % cells)
        # THE MARKUP, NOT THE PAGE. '.pp-day.is-out' is a rule in the
        # inline stylesheet and is there on every sheet; the claim is
        # about whether any CELL wears the class.
        ok('class="pp-day is-out' not in html,
           '  and none of them is a greyed out-of-range day',
           re.findall(r'class="pp-day[^"]*"', html))
        ok('repeat(3, minmax(0, 1fr))' in html,
           '  and the grid is three columns wide, not seven')
        ok('>Mon<' not in html,
           '  and the Monday-to-Sunday strip is gone, since it would '
           'now be describing days that are not there')

        # AND A WHOLE WEEK IS UNTOUCHED - RG-1's sheet, unchanged.
        code, html = sheet(**{'from': MON, 'to': SUN,
                              'view': 'week', 'date': MON})
        ok(html.count('class="pp-day') == 7,
           'and a WHOLE week still prints all seven days',
           html.count('class="pp-day'))
        ok('repeat(' not in html.split('pp-sheet')[1][:4000],
           '  with no inline column override - RG-1\'s grid as it was')
    except Exception as exc:
        ok(False, 'sections 3 to 5 ran to the end', repr(exc)[:300])


# ==========================================================================
head('6. REGISTRATION')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('{{ back_url }}' in gate, 'and a sentinel watches Back')
ok('start = min(max(start, range_min), range_max)' in gate,
   'and one watches the clamp')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the printed sheet fits the paper. Nobody has put')
print('  one through a printer yet - it is still the highest-yield')
print('  untested thing in this module, and no render in a headless')
print('  browser replaces it.')
print('')
print('  Not that the shopping list page learned the same lesson. It')
print('  takes the same two dates from the same planner and its own')
print('  Back has not been looked at.')
print('')
print('  Not that cropping is the right call for a MONTH narrowed to')
print('  a few days. It is what Demetri asked for and what the round')
print('  does; whether a part-month reads better cropped or dimmed is')
print('  a thing to look at on paper.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
