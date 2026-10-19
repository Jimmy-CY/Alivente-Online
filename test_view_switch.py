# -*- coding: utf-8 -*-
"""test_view_switch.py - round MV-1, 19 Oct 2026.

RELEASE 4, PUSH 1. THREE ZOOM LEVELS ON ONE CALENDAR.

Demetri, testing the live planner: "why does this still have the time
calendar?" and "This daily list is not required...". Then, on the
design: "Monthly Calendar first - full page."

This suite judges the SWITCHER. MV-2, MV-3 and MV-4 are the views it
switches between, and all four ship in one push.

THE CLAIM THAT MATTERS, and the one a reader should check first: a
switcher that loses the date is worse than no switcher. Press Week
while looking at December and landing on this week is a control that
cannot be trusted, and nobody presses it twice. So the three views
travel on ONE `?date=`, and section 3 drives every link and asks the
page which day it landed on.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. view_mode is clamped to three names, Month is the
      default, the anchor is read in one place, and the switcher is
      base's .alv-seg with nothing of base's restated.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      there is one view and ?week= is read in a block of its own.

  3   DRIVEN, through a real client. Six addresses including two bad
      ones, and the day carried across every switch.

  4   RENDERED at 1200 and 390. One row, three equal thumb-sized
      thirds on the phone, and the current view actually painted -
      MC-1 is the round where both halves of a toggle were in the
      markup and the inactive one was white on white.

  5   Scope, registration, the gate, and one dead rule removed.

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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_viewswitch'
ME = 'test_view_switch.py'
PATCHER = 'apply_view_switch.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MV-1, 19 Oct 2026'
VIEWS = ('month', 'week', 'day')

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
FILES = (VIEW, TPL)

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
    """Every source claim MV-1 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW], payloads=True)
    # The bar, sliced on the CLASS ATTRIBUTE - this round writes the
    # name twice, once as a selector and once as the element, and a
    # slice from the first ran through the whole action bar.
    bar = code.split('class="planner-view-bar"', 1)[-1] \
              .split('calendar-layout', 1)[0]

    # ---- 1. the view is one of three, and Month lands
    c['the view is read from the address'] = (
        "request.GET.get('view', 'month')" in v)
    c['  clamped to the three it knows'] = (
        "if view_mode not in ('month', 'week', 'day')" in v)
    c['  and Month is the one it lands on'] = (
        "view_mode = request.GET.get('view', 'month')" in v)

    # ---- 2. ONE anchor, read once
    c['one anchor date serves all three views'] = (
        'ONE ANCHOR DATE FOR THREE VIEWS' in text[VIEW])
    c['  read from ?date= first'] = "for _param in ('date', 'week')" in v
    c['  then ?week=, which old links still send'] = (
        "'week')" in v and 'week_start = anchor' in v)
    c['  and today when neither parses  [A5]'] = (
        'if anchor is None:\n        anchor = today' in v)
    c['  the month follows the anchor, not the clock'] = (
        "request.GET.get('year', anchor.year)" in v
        and "request.GET.get('month', anchor.month)" in v)
    c['  and the week is the anchor\'s week'] = 'week_start = anchor' in v
    c['the view and the anchor reach the template'] = (
        "'view_mode': view_mode," in v and "'anchor': anchor," in v)

    # ---- 3. the control is BASE'S, and it is a link
    c['the switcher is base\'s .alv-seg'] = (
        'class="alv-seg" role="group" aria-label="Calendar view"' in code)
    c['  and the page restates none of base\'s rules'] = (
        not re.search(r'(?m)^\s*\.alv-seg\s*\{', code))
    c['  three links, one per view'] = (
        sorted(re.findall(r'href="\?view=(\w+)&amp;', bar))
        == sorted(VIEWS))
    c['  every one carrying the anchor'] = (
        bar.count("&amp;date={{ anchor|date:'Y-m-d' }}") == 3)
    c['  and the current one marked'] = (
        bar.count('aria-current="page"') == 3)
    # LINKS AND NOT BUTTONS. The view is in the URL, so it survives a
    # refresh and can be sent to somebody. MC-1 is why this page does
    # not roll its own.
    # PAIRED WITH THE BAR EXISTING. A page with no view bar has no
    # onclick in one either, so the absence on its own was true before
    # this round - the pairing PK-1 had to make for the same reason,
    # and the control section caught it here too.
    c['nothing in the bar needs JavaScript'] = (
        'class="planner-view-bar"' in code
        and 'onclick=' not in bar and '<button' not in bar)
    c['  and no script reaches for it'] = (
        'class="planner-view-bar"' in code
        and not re.search(r'planner-view-bar["\']\s*\)', js))

    # ---- 4. the phone gets three thumbs
    c['the bar is full width on a phone'] = (
        '.planner-view-bar .alv-seg {' in code
        and 'width: 100%;' in
        code.split('.planner-view-bar .alv-seg {')[1].split('}')[0])
    c['  with each third at least 44px'] = (
        '.planner-view-bar .alv-seg > * {' in code
        and 'min-height: 44px;' in
        code.split('.planner-view-bar .alv-seg > * {')[1].split('}')[0])

    # ---- 5. EVERY address this page builds carries the view
    #
    # A view that only survives its own switcher is not in the URL.
    # goWeek and goMonth built their own addresses and neither carried
    # `view`, so the week arrow in Week view dropped you on the Month.
    # This suite drove the three switcher links and proved the DAY
    # survived them, and never pressed anything else - which is
    # testing a control against the half that was never in doubt.
    c['every address this page builds carries the view'] = (
        'function plannerUrl(' in js and "p.set('view'" in js)
    # PAIRED WITH plannerUrl EXISTING, for the third time in this
    # file: a page with no plannerUrl has no copies of the line
    # either, so the absence alone was true before this round.
    c['  from ONE place, not a copy in each function'] = (
        'function plannerUrl(' in js and js.count("p.set('view'") <= 2)
    for _fn in ('goWeek', 'goMonth', 'goDay'):
        _b = js.split('function %s(' % _fn)[-1].split('\nfunction ')[0]
        c['  %s() among them' % _fn] = (
            'plannerUrl(' in _b or "p.set('view'" in _b)

    # ---- 6. the dead rule PF-2 left
    c['the dead .picker-filter .alv-seg rule is gone'] = (
        not re.search(r'\.picker-filter\s+\.alv-seg', code))
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
# THE PAGE RESTATED NONE OF BASE'S RULES BEFORE EITHER, because it had
# no seg at all - the same pairing PK-1 had to make for the same
# reason. And `then ?week=` was true before in a different sense: the
# old block read it directly.
ALLOWED = ("  and the page restates none of base's rules",)
ok(sorted(leaked) == sorted(ALLOWED),
   'the only claim already true before MV-1 is the absence of an '
   '.alv-seg rule, which was true because there was no seg', leaked)
BV = T.python_code_only(was(VIEW), payloads=True)
ok("asked = request.GET.get('week')" in BV,
   'CONTROL: ?week= was read in a block of its own, and nothing else '
   'read a date')
ok('view_mode' not in BV, 'CONTROL: and there was no view at all')
ok("request.GET.get('year', today.year)" in BV,
   'CONTROL: the month followed the clock, which was right while it '
   'was a navigation strip and not a view')
ok(re.search(r'\.picker-filter\s+\.alv-seg', T.code_only(was(TPL))),
   "CONTROL: and PF-2's dead rule really was there to remove")


# ==========================================================================
head('3. DRIVEN - six addresses, and the day carried across every switch')
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
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

body = ''
if django_up:
    import datetime as _dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.utils import timezone

    u = User.objects.create_user(username='mv1', password='x',
                                 email='mv1@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)
    TODAY = timezone.now().date()

    def ask(q):
        r = cl.get('/meal_plans/planner/' + q)
        if r.status_code != 200:
            return None, None, r.status_code
        b = r.content.decode('utf-8', 'replace')
        cur = re.findall(
            r'href="\?view=(\w+)&amp;date=([\d-]+)"\s*\n?\s*'
            r'aria-current="page"', b)
        every = sorted(set(re.findall(
            r'href="\?view=\w+&amp;date=([\d-]+)"', b)))
        return (cur[0] if cur else None), every, 200

    cur, every, code = ask('')
    ok(code == 200, 'the planner answers with no parameters at all', code)
    ok(cur and cur[0] == 'month',
       '  and lands on MONTH - his own words, "Monthly Calendar first"',
       cur)
    ok(cur and cur[1] == TODAY.strftime('%Y-%m-%d'),
       '  anchored on today', cur)
    ok(every == [TODAY.strftime('%Y-%m-%d')],
       '  and all three links offer the same day', every)

    # THE CLAIM THAT MATTERS. Switch zoom level, keep the day.
    print('')
    print('   THE DAY SURVIVES THE SWITCH')
    FAR = '2026-12-03'
    for want in VIEWS:
        cur, every, code = ask('?view=%s&date=%s' % (want, FAR))
        ok(cur == (want, FAR),
           '  ?view=%-5s lands on %-5s still showing %s'
           % (want, want, FAR), cur)
        ok(every == [FAR],
           '    and the other two offer that day too', every)

    # A STRING SOMEBODY CAN TYPE - A5. Every one falls back.
    print('')
    print('   THE ADDRESS BAR IS A STRING SOMEBODY CAN TYPE  [A5]')
    for q, why in (
            ('?view=nonsense', 'a view that does not exist'),
            ('?view=', 'an empty view'),
            ('?date=rubbish', 'a date that does not parse'),
            ('?date=2026-13-45', 'a date that parses as nothing real'),
            ('?view=month&date=', 'an empty date')):
        cur, every, code = ask(q)
        ok(code == 200, '  %-22s answers 200 - %s' % (q, why), code)
        if cur:
            ok(cur[0] in VIEWS,
               '    and lands on a view it knows (%s)' % cur[0], cur)

    # OLD LINKS STILL WORK. MN-1 kept this screen's url names pointing
    # here so they would not break; its query string is the same
    # promise.
    print('')
    print('   THE ADDRESSES THAT ALREADY EXIST')
    cur, every, code = ask('?week=2026-10-19')
    ok(cur and cur[1] == '2026-10-19',
       '  ?week= is still read - the Shopping List link and the Copy '
       'Week dialog both send it', cur)
    cur, every, code = ask('?view=week&date=2026-10-22')
    ok(cur == ('week', '2026-10-22'),
       '  and ?date= wins over ?week= when both could apply', cur)

    resp = cl.get('/meal_plans/planner/')
    body = resp.content.decode('utf-8', 'replace')
    # COUNTED IN THE BAR, NOT IN THE PAGE. base's stylesheet carries
    # `.alv-seg > [aria-current="page"]` and a hover rule that negates
    # it, so the whole page holds three and only one of them is an
    # attribute. A selector about a thing is not the thing.
    rbar = body.split('class="planner-view-bar"', 1)[-1] \
               .split('calendar-layout', 1)[0]
    ok(rbar.count('aria-current="page"') == 1,
       'exactly ONE view is marked current, not none and not three',
       rbar.count('aria-current="page"'))


# ==========================================================================
head('4. RENDERED - the bar at 1200 and at 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

if not django_up or not body:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the bar is drawn', 'playwright or the Bootstrap fixture is '
                             'absent')
else:
    FIX = '<style>%s</style>' % read(FIXCSS)
    i = body.lower().find('</head>')
    DRESSED = body[:i] + FIX + body[i:] if i > 0 else FIX + body

    MEASURE = """() => {
        const bar = document.querySelector('.planner-view-bar');
        const seg = bar.querySelector('.alv-seg');
        const ls = [...seg.querySelectorAll('a')];
        const cur = ls.find(a => a.getAttribute('aria-current'));
        const st = cur ? getComputedStyle(cur) : null;
        return {
            links: ls.length,
            rows: new Set(ls.map(
                a => Math.round(a.getBoundingClientRect().top))).size,
            widths: ls.map(
                a => Math.round(a.getBoundingClientRect().width)),
            heights: ls.map(
                a => Math.round(a.getBoundingClientRect().height)),
            segW: Math.round(seg.getBoundingClientRect().width),
            barW: Math.round(bar.getBoundingClientRect().width),
            curBg: st ? st.backgroundColor : null,
            curInk: st ? st.color : null,
            wide: document.documentElement.scrollWidth >
                  document.documentElement.clientWidth
        };
    }"""

    with sync_playwright() as _pw:
        br = _pw.chromium.launch()
        try:
            for w, where in ((1200, 'DESKTOP 1200'), (390, 'PHONE 390')):
                ctx = br.new_context(viewport={'width': w,
                                               'height': 900})
                pg = ctx.new_page()
                pg.set_content(DRESSED, wait_until='domcontentloaded')
                m = pg.evaluate(MEASURE)
                print('')
                print('   %s' % where)
                ok(m['links'] == 3, '  three links are drawn', m['links'])
                ok(m['rows'] == 1,
                   '  on ONE row - a switcher that wraps reads as two '
                   'controls', m)
                ok(not m['wide'],
                   '  and the page does not scroll sideways', m)

                # THE CURRENT ONE IS PAINTED. MC-1 is the round where
                # both halves of a toggle were in the markup and the
                # inactive one was white on white; a class name is not
                # a picture.
                ok(m['curBg'] not in (None, 'rgba(0, 0, 0, 0)',
                                      'transparent'),
                   '  the current view carries a filled ground, %s'
                   % m['curBg'], m['curBg'])
                ok(m['curInk'] not in (None, m['curBg']),
                   '  with ink that is not its own ground, %s'
                   % m['curInk'], m['curInk'])

                if w < 768:
                    ok(m['segW'] >= m['barW'] - 2,
                       '  the seg fills the bar - %dpx of %dpx'
                       % (m['segW'], m['barW']), m)
                    ok(max(m['widths']) - min(m['widths']) <= 2,
                       '  three equal thirds, %r' % m['widths'],
                       m['widths'])
                    ok(min(m['heights']) >= 44,
                       '  every one at least 44px tall, %r'
                       % m['heights'], m['heights'])
                else:
                    ok(m['segW'] < m['barW'],
                       '  the seg is its own width inside a centred '
                       'bar - %dpx of %dpx' % (m['segW'], m['barW']), m)
                ctx.close()
        finally:
            br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
touched = sorted(
    os.path.relpath(os.path.join(dp, f), ROOT)[:-len(SUFFIX)]
    for dp, dn, fn in os.walk(ROOT)
    for f in fn if f.endswith(SUFFIX))
allowed = {'Push-PendingChanges.ps1', 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py',
           os.path.join('pages', 'templates', 'meal_planner.html'),
           os.path.join('pages', 'views', 'recipes', 'meal_planning.py')}
ok(len(touched) == 6,
   'six backups on disk, counted and not typed', '%r' % (touched,))
ok(not set(touched) - allowed,
   '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(set(touched) - allowed)))

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok('aria-label="Calendar view"' in gate
   and 'ONE ANCHOR DATE FOR THREE VIEWS' in gate,
   'both sentinels are pinned in the gate')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))

# AND THE DEAD RULE IS GONE EVERYWHERE, not only on this page.
stray = [T.rel(p) for p in T.templates(include_base=False)
         if re.search(r'\.picker-filter\s+\.alv-seg', T.code_only(read(p)))]
ok(not stray,
   "PF-2's dead rule is gone from every page - a selector that matches "
   'nothing is a claim about the page that has stopped being true',
   stray)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THREE ZOOM LEVELS ON ONE CALENDAR, and they travel on ONE')
print('  ?date=. Three parameters would each have to be kept in step')
print('  by every link that moves the date - the week arrows, the')
print('  month arrows, Today, the picker - six places to forget one.')
print('')
print('  A SWITCHER THAT LOSES THE DATE IS WORSE THAN NONE. Press')
print('  Week while looking at December and land on this week, and')
print('  nobody presses it twice. Section 3 drives every link and')
print('  asks the page which day it landed on.')
print('')
print("  SERVER-RENDERED, ON BASE'S COMPONENT. The view is in the URL,")
print('  so it survives a refresh and can be sent to somebody. MC-1 is')
print('  why this page does not roll its own: the last hand-written')
print('  toggle had both halves in the markup and painted the inactive')
print('  one white on white.')
print('=' * 74)
sys.exit(1 if failed else 0)
