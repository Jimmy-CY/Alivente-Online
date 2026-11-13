# -*- coding: utf-8 -*-
"""test_wellness_twentysix.py - round PT-4, 13 Nov 2026.

RELEASE 76 - A CELEBRATION ON TODAY OPENS ITS GREETING.
Demetri, 09:01: "when I click on Somebody birthday/nameday/anniversary in
the At Home Today section, it open a mobile friendly version of the
greetings function (Greek and English), with Whatapp connectivity".
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

SUFFIX = '.bak_greetwell'
ME = 'test_wellness_twentysix.py'
PATCHER = 'apply_greeting_wellness.py'
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

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
td = read(J(WT, 'today.html'))
cel = td[td.index('{% for r in home.cel %}'):td.index('{% endfor %}',
                                                      td.index('{% for r in home.cel %}'))]
ok("{% url 'wellness:greeting' r.event_id %}" in cel,
   'TODAY: a celebration line opens its greeting')
gt = read(J(WT, 'greeting.html'))
# PT-5, 13 Nov 2026 - asked through Wellness's own address now (a phone's
# main-app hour sent the old one to the login page); same checks behind it.
ok("{% url 'wellness:greeting_write' event.id %}" in gt and
   'value="Greek"' in gt and 'https://wa.me/' in gt and
   "encodeURIComponent(text.value)" in gt,
   'GREETING: asked through Wellness; English or Greek; WhatsApp '
   'with the words as they stand')
gv = read(J(APP, 'views_greeting.py'))
ok('relevant_to__in=CG.my_member_ids(request.user)' in gv and
   'raise Http404' in gv, '  only for one of your own celebrations')
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
v = read(J(APP, 'views.py'))
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl23-1', 'wl24-1') and
   ("SW_VERSION = '%s'" % vv[0]) in v, 'the app files carry a new version',
   vv)
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import help as HELP                           # noqa: E402
ok(HELP.for_url_name('greeting') and
   all(len(s.split()) <= 40 for s in HELP.for_url_name('greeting')['steps']
       + HELP.for_url_name('today')['steps']) and
   'greeting' in ' '.join(HELP.for_url_name('today')['steps']),
   'HELP: the greeting screen, and Today says a tap sends one')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile
    from pages.models import (HouseholdMember, Contact, CelebrationEvent,
                              UserProfile)
    connection.ensure_connection()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    import importlib
    CG = importlib.import_module('pages.views.celebration_gifts')

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            def perm(code):
                p, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                return p
            a = User.objects.create_user('w26_a', 'w26a@example.com', 'x',
                                         first_name='Al')
            b = User.objects.create_user('w26_b', 'w26b@example.com', 'x',
                                         first_name='Bo')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_wellness'),
                                       perm('can_access_celebrations'))
                WellnessProfile.objects.create(user=u, onboarded=True)
            ws = ensure_workspace(a)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            for u in (a, b):
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ws})
            day = timezone.localdate()
            ma = HouseholdMember.objects.create(workspace=ws, name='W26 Al',
                                                user=a)
            HouseholdMember.objects.create(workspace=ws, name='W26 Bo',
                                           user=b)
            c = Contact.objects.create(name='W26 Eleni', relationship='friend',
                                       phone='+357 99 123456', workspace=ws,
                                       created_by=a)
            e = CelebrationEvent.objects.create(
                contact=c, event_type='anniversary', created_by=a,
                event_date=day.replace(year=day.year - 27))
            e.relevant_to.add(ma)

            t = ca.get('/wellness/').content.decode()
            ok(('/wellness/greeting/%d/' % e.pk) in t and 'W26 Eleni' in t,
               'TODAY: Eleni\'s anniversary links to her greeting')
            r = ca.get('/wellness/greeting/%d/' % e.pk)
            t = r.content.decode()
            ok(r.status_code == 200 and 'W26 Eleni' in t and
               'Anniversary, 27 years' in t and
               'data-number="35799123456"' in t and
               '/wellness/greeting/%d/write/' % e.pk in t,
               'GREETING: her name, 27 years, her WhatsApp number')
            ok(cb.get('/wellness/greeting/%d/' % e.pk).status_code == 404,
               '  Bo, whose celebration it is not, gets nothing')
            real = CG.ask_greeting
            CG.ask_greeting = lambda prompt, client=None: (
                'Χρόνια πολλά Eleni!' if 'Language: Greek' in prompt
                and '27th anniversary' in prompt else None)
            try:
                d = ca.post('/celebrations/event/%d/greeting/' % e.pk,
                            {'language': 'Greek'}).json()
                ok(d.get('text') == 'Χρόνια πολλά Eleni!',
                   '  asked in Greek, for the 27th, it comes back in Greek')
            finally:
                CG.ask_greeting = real
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok("'wellness:greeting'" not in was(J(WT, 'today.html')),
       'before this round: a celebration on Today opened nothing')
except IOError as _e:
    skip('section 3', str(_e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# PT-5, 13 Nov 2026 - LL-1 backed views_greeting.py up again, so its
# sentinel moved to text that backup does not hold.
ok("Text = 'def greeting_write(request, event_id):'" in gate,
   '  with a sentinel on the greeting page')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
