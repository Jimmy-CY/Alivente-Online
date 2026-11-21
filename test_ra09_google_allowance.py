# -*- coding: utf-8 -*-
"""test_ra09_google_allowance.py - round RA09, 21 Nov 2026.

RELEASE RA09 - A MONTHLY GOOGLE ALLOWANCE, AND WHAT IS LEFT.
Demetri, 20 Nov: "In reality a monthly limit would work better for me";
21 Nov: "Yep, Let's build RA09". Alivente counts every Google Places
search, stops checking on Google when the month's or the day's allowance
is used, shows what is left on Suggest things to do, and emails at 80%.
And: "the next day, when the daily allowance is reset, his things to do
information is automatically updated? Or he is prompted" - both.
No test here calls Google or a mail server.
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

SUFFIX = '.bak_ra09'
ME = 'test_ra09_google_allowance.py'
PATCHER = 'apply_ra09_google_allowance.py'
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
import datetime as dt                                       # noqa: E402
import json                                                 # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from travel import gplaces as G                             # noqa: E402
from travel import gquota as Q                              # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. THE SOURCE')
md = read(J(TV, 'models.py'))
ok('class GoogleUse(models.Model):' in md and
   'per_month = models.PositiveIntegerField(default=1000)' in md and
   'per_day = models.PositiveIntegerField(default=100)' in md,
   'COUNTED BY DAY; a month\'s allowance (1,000) and a day\'s (100)')
ok(os.path.isfile(J(TV, 'migrations', '0013_google_allowance.py')),
   'MIGRATION travel 0013')
gp = read(J(TV, 'gplaces.py'))
ok('gquota.has_room()' in gp and 'gquota.note()' in gp,
   'EVERY GOOGLE SEARCH is counted, and only within the allowance')
ok('gquota.note()' in read(J(ROOT, 'pages', 'key_health.py')),
   '  the key watch\'s rare retry counts too')
ok(G.key() == '', 'NEVER GOOGLE FROM A TEST: no key here')

head('2. DRIVEN (database; no network, no mail)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import GoogleAllowance, GoogleUse, Trip
    connection.ensure_connection()
    GoogleUse.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    _key = G.key
    try:
        with transaction.atomic():
            GoogleUse.objects.all().delete()
            GoogleAllowance.objects.all().delete()
            os.environ['KEY_ALERT_EMAIL'] = 'demetri@example.com'
            d = Q._today()
            if d.day == 1:
                d = d + dt.timedelta(1)     # a day before it in the month
            u = Q.usage(d)
            ok(u['month_left'] == 1000 and u['day_left'] == 100 and
               u['room'], 'TO START: 1,000 this month, 100 today')
            for i in range(5):
                Q.note(d, send=lambda m: None)
            Q.note(d - dt.timedelta(1), send=lambda m: None)
            Q.note(d.replace(day=1) - dt.timedelta(1), send=lambda m: None)
            u = Q.usage(d)
            ok(u['day_used'] == 5 and u['month_used'] == 6,
               'COUNTED: 5 today, 6 this month (last month\'s not)', u)
            a = Q.allowance()
            a.per_day = 5
            a.save()
            ok(not Q.has_room(d) and Q.usage(d)['day_out'],
               'TODAY\'S USED UP: no more Google today')
            ok(Q.has_room(d + dt.timedelta(1)), '  ...tomorrow, again')
            a.per_day, a.per_month = 100, 10
            a.save()
            sent = []
            for i in range(2):
                Q.note(d, send=sent.append)
            ok(len(sent) == 1 and '80%' in sent[0].subject and
               'Google' in sent[0].body,
               'AT 80% OF THE MONTH: one email', [m.subject for m in sent])
            Q.note(d, send=sent.append)
            Q.note(d, send=sent.append)
            ok(len(sent) == 1, '  ...and only one that month')
            ok(not Q.has_room(d) and Q.usage(d)['month_out'],
               'THE MONTH\'S USED UP: no more Google until the 1st')
            ok(Q.has_room((d.replace(day=28) + dt.timedelta(5)).replace(day=1)),
               '  ...the 1st, again')
            G.key = lambda: 'fake-key'
            ok(not G.enabled(),
               'THE CHECK IS SKIPPED: suggestions come, unchecked')
            try:
                G.search('Benaki', opener=lambda r, timeout=None: None)
                ok(False, 'a search past the allowance is refused')
            except G.GoogleError as e:
                ok('allowance' in str(e),
                   'A SEARCH PAST THE ALLOWANCE is refused, not sent')
            a.per_month = 1000
            a.save()

            class R(object):
                def __enter__(self):
                    return self

                def __exit__(self, *x):
                    return False

                def read(self):
                    return json.dumps({'places': []}).encode()
            before = Q.usage()['day_used']
            G.search('Benaki', opener=lambda r, timeout=None: R())
            ok(Q.usage()['day_used'] == before + 1,
               'A SEARCH SENT is counted (stubbed Google)')
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra09a', 'ra09a@example.com', 'x',
                                          is_superuser=True)
            her = User.objects.create_user('ra09b', 'ra09b@example.com', 'x')
            for x in (me, her):
                x.user_permissions.add(perm)
                UserProfile.objects.update_or_create(
                    user=x, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            H = Client(SERVER_NAME='localhost')
            H.force_login(her)
            t = Trip.objects.create(owner=me, name='RA09 trip')
            p = A.get('/travel/%d/ideas/new/' % t.pk).content.decode()
            ok('data-gquota' in p and 'this month' in p and
               'data-gquota-change' in p,
               'SUGGEST: Google checks left, this month and today; Change '
               '(superuser)')
            ok(H.get('/travel/google/').status_code == 404,
               'THE ALLOWANCE PAGE: superusers only')
            A.post('/travel/google/', {'per_month': '500', 'per_day': '80'})
            a = Q.allowance()
            ok(a.per_month == 500 and a.per_day == 80,
               '  a superuser sets 500 a month, 80 a day')
            # ---- checked later (stubbed Google) ----
            from travel.models import Idea
            from travel import ideas as ID
            GoogleUse.objects.all().delete()
            a.per_month, a.per_day, a.rechecked_on = 1000, 100, None
            a.save()
            for k, n in enumerate(['Benaki', 'Acropolis', 'Gone Cafe']):
                Idea.objects.create(trip=t, city='Athens', name=n,
                                    position=k)
            t.start_date = Q._today() + dt.timedelta(5)
            t.end_date = Q._today() + dt.timedelta(8)
            t.save()
            _search = G.search
            sent_q = []

            def fake(text, near=None, opener=None):
                sent_q.append(text)
                Q.note()
                if text.startswith('Gone'):
                    return {'status': 'CLOSED_PERMANENTLY', 'gid': 'g',
                            'lat': 1, 'lng': 1, 'rating': None,
                            'ratings': None, 'price': '', 'open_days': None}
                return {'status': 'OPERATIONAL', 'gid': 'g', 'lat': 37.97,
                        'lng': 23.72, 'rating': 4.6, 'ratings': 900,
                        'price': '€€', 'open_days': {0, 1, 2, 3, 4, 5, 6}}
            G.search = fake
            ok(ID.waiting(t).count() == 3, 'WAITING: 3 suggestions not '
               'checked on Google')
            p = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('data-idea-waiting' in p and 'Check them now' in p,
               'THE PROMPT: "3 suggestions weren\'t checked ... Check them '
               'now"')
            A.post('/travel/%d/ideas/recheck/' % t.pk)
            ok(ID.waiting(t).count() == 0 and
               Idea.objects.filter(trip=t).count() == 2 and
               Idea.objects.get(trip=t, name='Benaki').rating == 4.6,
               'CHECK THEM NOW: checked, rated; one closed for good, gone')
            for k, n in enumerate(['Museum A', 'Museum B']):
                Idea.objects.create(trip=t, city='Athens', name=n,
                                    position=10 + k)
            from django.utils import timezone as _tz
            early = _tz.localtime().replace(hour=7)
            ok(Q.daily_recheck(early) is None,
               'THE MORNING CATCH-UP: not before 10:00 (Google\'s day)')
            late = _tz.localtime().replace(hour=11)
            del sent_q[:]
            n1 = Q.daily_recheck(late)
            ok(n1 == 2 and ID.waiting(t).count() == 0,
               '  after 10:00: the waiting ones checked', n1)
            ok(Q.daily_recheck(late) is None, '  ...once a day only')
            Idea.objects.create(trip=t, city='Athens', name='Museum C',
                                position=20)
            a = Q.allowance()
            a.rechecked_on = None
            a.save()
            GoogleUse.objects.update_or_create(day=Q._today(), defaults={
                'searches': 99})
            del sent_q[:]
            Q.daily_recheck(late)
            ok(not sent_q and ID.waiting(t).count() == 1,
               '  never more than half of what is left today', sent_q)
            G.search = _search
            G.key = _key
            p = A.get('/travel/%d/ideas/new/' % t.pk).content.decode()
            ok('data-gquota' not in p, 'NO KEY: nothing about Google shown')
            raise Rollback
    except Rollback:
        pass
    G.key = _key
    os.environ.pop('KEY_ALERT_EMAIL', None)

head('3. HELP AND REGISTERED')
ok("_esc(Q.BY_ID[qid]['text']) in h1" in read(J(ROOT, 'test_quotes.py')),
   'test_quotes compares the quote as the page shows it (escaped), like '
   'test_wellness_six')
ok('data-travel-help' in read(J(TT, 'google_allowance.html')),
   'THE ALLOWANCE PAGE has Help, like every Travel page')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-help-gquota' in adm and 'Google checks left' in adm and
   'checked automatically the next morning' in adm,
   'HELP (computer): Google checks left')
ok('Google checks left' in read(J(TT, 'm', 'help.html')), 'HELP (phone)')
import re as _re                                            # noqa: E402
_v = _re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 22, 'THE PHONE APP moves to tv22-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
