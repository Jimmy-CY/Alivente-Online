# -*- coding: utf-8 -*-
"""test_ra11_category_icons.py - round RA11, 22 Nov 2026.

RELEASE RA11 - AN ICON FOR EACH KIND OF THING TO DO.
Demetri, 22 Nov: "Can we create an icon for each type of Things to Do
category ... place that Icon on the top right of each Things to Do
suggestion" and "could we also show the icon, next to the category name".
One icon a category (travel/_idea_icon.html, drawn - the phone app has no
icon font offline), on each suggestion - in Outside what you asked for too
- and beside each category heading; computer and phone. No network.
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

SUFFIX = '.bak_ra11'
ME = 'test_ra11_category_icons.py'
PATCHER = 'apply_ra11_category_icons.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)








print(__doc__.strip().splitlines()[0])
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from django.template.loader import render_to_string         # noqa: E402
from travel import ideas as ID                              # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. THE ICONS')
ic = read(J(TT, '_idea_icon.html'))
keys = [k for k, _n, _w in ID.INTERESTS]
ok(len(keys) == 11 and all("k == '%s'" % k in ic for k in keys) and
   '{% else %}' in ic, 'ONE ICON A CATEGORY: all 11, and one for Other')
svgs = set()
for k in keys + ['other']:
    s = render_to_string('travel/_idea_icon.html', {'k': k})
    ok(s.count('<svg') == 1 and 'aria-hidden="true"' in s,
       '  %s draws one icon' % k)
    svgs.add(s)
ok(len(svgs) == 12, 'EACH ONE DIFFERENT (12)', len(svgs))
ok('icon font' in ic and 'fa-' not in ic,
   'DRAWN, not the icon font (the phone app has none offline)')
card = read(J(TT, '_ideas_card.html'))
ok("{% include 'travel/_idea_icon.html' with k=i.icon %}" in card and
   'title="{{ i.cat }}"' in card, 'ON EACH SUGGESTION, named on hover')
ok("{% include 'travel/_idea_icon.html' with k=b.k %}" in
   read(J(TT, '_ideas_list.html')), 'BESIDE EACH CATEGORY HEADING')
for f in (J(TT, '_style.html'), J(TV, 'assets', 'travel.css')):
    c = read(f)
    ok('.tv-id-card > .tv-id-ico { position: absolute; top: 10px; '
       'right: 10px; }' in c and '.tv-id-group.has-ico' in c and
       '.tv-id-card .tv-id-pick { padding-right: 34px; }' in c,
       '  styled, top right, the name kept clear: %s' % os.path.basename(f))

head('2. DRIVEN (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import Idea, Trip
    connection.ensure_connection()
    Idea.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra11a', 'ra11a@example.com', 'x')
            me.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=me, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            t = Trip.objects.create(owner=me, name='RA11 Athens')
            psy = Idea.objects.create(trip=t, city='Athens', name='Psyrri',
                                      interest='streets', position=0,
                                      checked=True)
            taf = Idea.objects.create(trip=t, city='Athens', name='Taf',
                                      interest='cafes', position=1,
                                      checked=True)
            acr = Idea.objects.create(trip=t, city='Athens',
                                      name='Acropolis', interest='musts',
                                      position=2, checked=True, flag='far',
                                      flag_text='1.4 km from the centre - '
                                      'outside your 1 km')
            odd = Idea.objects.create(trip=t, city='Athens', name='Oddity',
                                      interest='', position=3, checked=True)

            def card(p, i):
                a = p.find('data-idea="%d"' % i.pk)
                return p[a:p.find('data-idea-hide', a)]
            p = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('data-idea-icon="streets"' in card(p, psy) and
               'title="Neighbourhoods &amp; streets"' in card(p, psy),
               'COMPUTER: the suggestion has its icon, named on hover')
            ok('data-idea-icon="cafes"' in card(p, taf) and
               'data-idea-icon="other"' in card(p, odd),
               '  ...Cafés; and Other for one without a category')
            o = p.find('data-idea-outside')
            ok(o > 0 and p.find('data-idea="%d"' % acr.pk) > o and
               'data-idea-icon="musts"' in card(p, acr),
               'OUTSIDE WHAT YOU ASKED FOR: still shows it is a must-see')
            ok('data-idea-group="streets"' in p and
               'data-idea-group="cafes"' in p and
               p.find('data-idea-group="streets"') <
               p.find('data-idea="%d"' % psy.pk),
               'THE HEADINGS have the icon, above their suggestions')
            ok(p.count('data-idea-group=') == 3,
               '  one a category shown (Neighbourhoods, Cafés, Other)')
            P = Client(SERVER_NAME='localhost')
            P.force_login(me)
            p = P.get('/travel/m/trip/%d/ideas/' % t.pk).content.decode()
            ok('data-idea-icon="streets"' in p and
               'data-idea-group="cafes"' in p and
               'data-idea-icon="musts"' in p,
               'THE PHONE: the same icons and headings')
            raise Rollback
    except Rollback:
        pass

head('3. HELP AND REGISTERED')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok("category&rsquo;s icon at the top right" in adm and
   'a cup for caf&eacute;s' in adm, 'HELP (computer): the icons')
ok('round icon at the top right' in read(J(TT, 'm', 'help.html')),
   'HELP (phone)')
_v = re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 24, 'THE PHONE APP moves to tv24-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
