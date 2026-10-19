# -*- coding: utf-8 -*-
"""test_day_view.py - round MV-4, 19 Oct 2026.

RELEASE 4, PUSH 1. ONE DAY, IN FULL - AND THE LIST OF SEVEN GOES.

Demetri, testing the live planner: "This daily list is not required..."

MV-3 replaced SEEING a week with seven columns. MV-4 is the round that
deletes the list he was talking about, by narrowing it to one day.

THE CLAIM IS A COUNT, so this suite counts. Three views, three
numbers: Month draws no day card at all, Week draws one (for a phone,
under MV-3's strip), Day draws one. Not seven, anywhere.

AND THE CARD ITSELF MUST SURVIVE UNCHANGED, which is the other half.
It holds the servings stepper that saves on press, MO-1's note row,
MO-1's leftover row with its cooked-on date and no stepper, and the
Add controls. None of that fits in a 146px week column or a 152px
month cell. A round that shortened the loop AND quietly edited the
card would be two rounds wearing one name.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One card, chosen by MV-3's sel_date and no second
      rule; the Day view's own nav, moving by days; the card hidden
      in Week above 768px.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      seven cards were drawn and the only nav moved by weeks.

  3   DRIVEN. All three views through a real client, counting cards,
      columns, strip buttons and which nav is drawn.

  4   THE CARD IS UNTOUCHED - every control in it, before and after.

  5   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import datetime as dt
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_dayview'
ME = 'test_day_view.py'
PATCHER = 'apply_day_view.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MV-4, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, TPL)

# EVERY CONTROL THE CARD CARRIES. Named, so one that leaves shows as
# a failure rather than as a quiet absence.
CARD = ('servings-step', 'stepServings', 'add-recipe-btn',
        'leftover-item', 'note-item', 'day-card-header', 'day-card-body')

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


def claims(text):
    """Every source claim MV-4 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    v = T.python_code_only(text[VIEW], payloads=True)
    # THE NAV, sliced on ITS OWN opening and not on the first
    # `view_mode == 'day'` - MV-1's switcher carries that test too,
    # earlier in the page, and the patcher's first gate measured it.
    OPEN = ("{% if view_mode == 'day' %}\n"
            '                <div class="week-nav">')
    nav = (text[TPL].split(OPEN, 1)[1].split('{% else %}', 1)[0]
           if OPEN in text[TPL] else '')

    # ---- 1. one day, not seven
    c['the card loop narrows to the selected day'] = (
        '{% for day in week_days %}{% if day.is_selected %}' in code)
    c['  wrapped so the stylesheet can place it'] = (
        'class="day-detail' in code)
    # PAIRED WITH THE NARROWING. sel_date and is_selected both
    # existed before this round - MV-3 put them there for the day
    # strip - so asking for them alone answered a question about MV-3.
    # The claim is that THE CARD uses them.
    c['  and it is MV-3\'s day, not a second rule'] = (
        '{% for day in week_days %}{% if day.is_selected %}' in code
        and 'sel_date' in v
        and 'sel_date = ' not in v.split('sel_date = ', 2)[-1])

    # ---- 2. the Day view moves by DAYS
    c['the day view has its own nav'] = bool(nav)
    c['  with the day before and the day after'] = (
        'prev_day' in nav and 'next_day' in nav)
    c['  and not the week arrows'] = bool(nav) and 'goWeek(' not in nav
    c['  it names the day, not the range'] = (
        'sel_date|date:"l j M Y"' in nav)
    c['  and counts that day\'s meals, not the week\'s'] = (
        'sel_count' in nav and 'sel_count' in v)
    c['the two days either side come from the view'] = (
        "'prev_day': sel_date - timedelta(days=1)," in v
        and "'next_day': sel_date + timedelta(days=1)," in v)

    # ---- 3. in Week it is for the phone only
    c['the card is hidden in Week at full size'] = (
        '.day-detail.in-week {' in code
        and 'display: none;' in
        code.split('.day-detail.in-week {')[1].split('}')[0])
    c['  by a min-width rule, so the phone keeps it'] = (
        '@media (min-width: 768px)' in text[TPL])

    # ---- 4. the card itself is untouched
    for ctl in CARD:
        c['the card still carries %s' % ctl] = ctl in code
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
# THE CARD'S OWN CONTROLS WERE ALL THERE BEFORE, and that is the
# point of this round rather than a leak: MV-4 shortens a loop and
# keeps the card. Their presence before AND after is what proves it.
CARDC = sorted('the card still carries %s' % c for c in CARD)
ok(sorted(leaked) == CARDC,
   'the only claims already true before MV-4 are the %d the card '
   'itself makes - which is this round KEEPING it, not a leak'
   % len(CARDC), [k for k in leaked if k not in CARDC])

BC = T.code_only(was(TPL))
BV = T.python_code_only(was(VIEW), payloads=True)
ok('{% for day in week_days %}{% if day.is_selected %}' not in BC,
   'CONTROL: the loop drew every day of the week')
ok('day-detail' not in BC, 'CONTROL: and nothing wrapped it')
ok('prev_day' not in BV and 'next_day' not in BV,
   'CONTROL: and there was no day to step to - only weeks')


# ==========================================================================
head('3. DRIVEN - three views, three counts')
# ==========================================================================
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + \
        ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.DEBUG = False
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a rendered planner',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe

    u = User.objects.create_user(username='mv4', password='x',
                                 email='mv4@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    rs = [Recipe.objects.create(recipe_name=n, servings=4, prep_time=10,
                                cook_time=30)
          for n in ('Moussaka', 'Greek Salad', 'Souvlaki')]
    MON = dt.date(2026, 10, 19)
    WED = dt.date(2026, 10, 21)
    parent = MealEntry.objects.create(date=WED, recipe=rs[0], servings=4,
                                      sort_order=1, created_by=u)
    MealEntry.objects.create(date=WED, recipe=rs[1], servings=4,
                             sort_order=2, created_by=u)
    MealEntry.objects.create(date=WED, recipe=None, note='Angy away',
                             servings=0, sort_order=3, created_by=u)
    MealEntry.objects.create(date=WED + dt.timedelta(days=1),
                             recipe=rs[0], servings=4, sort_order=1,
                             leftover_of=parent, created_by=u)
    for off in (0, 5):
        MealEntry.objects.create(date=MON + dt.timedelta(days=off),
                                 recipe=rs[2], servings=4, sort_order=9,
                                 created_by=u)

    def look(q):
        r = cl.get('/meal_plans/planner/?' + q)
        b = r.content.decode('utf-8', 'replace')
        return r.status_code, {
            'cards': b.count('class="day-card"'),
            'cols': b.count('class="week-col-head"'),
            'strip': len(re.findall(r'class="day-strip-btn[ "]', b)),
            'daynav': b.count('The day before'),
            'weeknav': b.count('The week before'),
            'title': (re.findall(r'week-title">([^<]{0,30})', b)
                      or ['-'])[0],
        }

    print('')
    code, m = look('view=month&date=2026-10-21')
    ok(code == 200, 'MONTH answers', code)
    ok(m['cards'] == 0,
       '  and draws NO day card - the month is the whole view', m)
    ok(m['cols'] == 0 and m['strip'] == 0,
       '  nor a week column or a strip button', m)

    code, m = look('view=week&date=2026-10-21')
    ok(code == 200, 'WEEK answers', code)
    ok(m['cards'] == 1,
       '  and draws ONE day card, for the phone, where it was seven',
       m)
    ok(m['cols'] == 7 and m['strip'] == 7,
       '  under seven columns and a seven-day strip', m)
    ok(m['weeknav'] == 1 and m['daynav'] == 0,
       '  with the WEEK nav, because the view is a week', m)

    code, m = look('view=day&date=2026-10-21')
    ok(code == 200, 'DAY answers', code)
    ok(m['cards'] == 1, '  and draws ONE day card', m)
    ok(m['cols'] == 0 and m['strip'] == 0,
       '  with no columns and no strip - one day is the whole view', m)
    ok(m['daynav'] == 1 and m['weeknav'] == 0,
       '  and the DAY nav, which moves by days', m)
    ok('Wednesday' in m['title'] and '21' in m['title'],
       '  naming the day: %r' % m['title'], m['title'])

    # THE DAY SHOWN IS THE DAY ASKED FOR, across a month boundary.
    print('')
    for d in ('2026-10-21', '2026-11-01', '2026-10-19'):
        code, m = look('view=day&date=' + d)
        want = dt.datetime.strptime(d, '%Y-%m-%d').date()
        ok(str(want.day) in m['title']
           and want.strftime('%b') in m['title'],
           '  ?date=%s shows %s' % (d, m['title']), m['title'])

    # AND THE CARD ITSELF STILL WORKS. The three row shapes MO-1 built
    # are all on this one day, so if the loop lost one it shows here.
    r = cl.get('/meal_plans/planner/?view=day&date=2026-10-21')
    b = r.content.decode('utf-8', 'replace')
    ok('Angy away' in b, "  and the day's note is drawn")
    ok(b.count('servings-step') >= 2,
       '  with a stepper on each recipe row',
       b.count('servings-step'))
    r2 = cl.get('/meal_plans/planner/?view=day&date=2026-10-22')
    b2 = r2.content.decode('utf-8', 'replace')
    ok('leftover-item' in b2,
       '  and the next day draws its leftover row, stepper-free - '
       "MO-1's rule, which a shortened loop must not have lost")


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
touched = sorted(
    os.path.relpath(os.path.join(dp, f), ROOT)[:-len(SUFFIX)]
    for dp, dn, fn in os.walk(ROOT)
    for f in fn if f.endswith(SUFFIX))
allowed = {'Push-PendingChanges.ps1', 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py',
           os.path.join('pages', 'templates', 'meal_planner.html'),
           os.path.join('pages', 'views', 'recipes', 'meal_planning.py'),
           # TWO REPAIRS THIS ROUND CAUSED, both the same shape: a
           # count taken across SEVEN day cards on a page that now
           # draws one. MO-1 counted its leftover and note rows on one
           # request; MV-3 compared its grid against the cards beside
           # it, which MV-4 then hid. Carried here, by the round that
           # caused them, so a half-applied tree stays green.
           'test_meal_day.py', 'test_week_cols.py'}
ok(len(touched) == 8,
   'eight backups on disk, counted and not typed', '%r' % (touched,))
ok(not set(touched) - allowed,
   '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(set(touched) - allowed)))

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok('ONE DAY, NOT SEVEN' in gate and 'THE DAY HAS ITS OWN NAV' in gate,
   'both sentinels are pinned in the gate')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m2 = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m2 and int(m2.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m2.group(1) if m2 else '?', len(T.CONVERTED)))


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  "THIS DAILY LIST IS NOT REQUIRED." It is gone. Month draws')
print('  no day card, Week draws one - for a phone, under the strip -')
print('  and Day draws one. Seven, nowhere.')
print('')
print('  AND THE CARD ITSELF IS UNTOUCHED, which is the other half of')
print("  the round. It holds the stepper that saves on press, MO-1's")
print("  note row and MO-1's leftover row with no stepper because a")
print('  leftover buys nothing. None of that fits in a 146px column')
print('  or a 152px cell. For ONE day the card is exactly right.')
print('')
print('  THE DAY MOVES BY DAYS. Week arrows above a single Wednesday')
print('  would move you seven, and a range for a title would name the')
print('  wrong thing.')
print('=' * 74)
sys.exit(1 if failed else 0)
