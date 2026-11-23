# -*- coding: utf-8 -*-
"""test_ra15_activity_log.py - round RA15, 23 Nov 2026.

RELEASE RA15 - WHO USED ALIVENTE, HOW AND WHEN.
Demetri, 23 Nov: "I want the sign-ins information. I want the changes to
the business records. I also want the Pages visited and time spent. For
the personal, I want to be able to see which modules/areas are used the
most ... I don't want access to the information they are saving in the
Personal side." - the menus' own modules; kept 12 months; a notice line;
an email after 5 wrong passwords in a row; by calendar month, the last 30
days or the last 12 months. No network: the email goes to Django's test
outbox.
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

SUFFIX = '.bak_ra15'
ME = 'test_ra15_activity_log.py'
PATCHER = 'apply_ra15_activity_log.py'
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
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ['KEY_ALERT_EMAIL'] = 'alerts@example.com'
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
from pages import activity as A                             # noqa: E402
PG = J(ROOT, 'pages')
PT = J(PG, 'templates')
NOTICE = ('Sign-ins, use of each area and changes to business records are '
          'logged. What you save in Personal is never recorded.')

head('1. THE SOURCE')
md = read(J(PG, 'models.py'))
ok(all('class %s(models.Model):' % c in md
       for c in ('ActivityHit', 'SignIn', 'RecordChange')) and
   os.path.isfile(J(PG, 'migrations', '0121_activity_log.py')),
   'THREE RECORDS: pages, sign-ins, changes; MIGRATION pages 0121')
st = read(J(ROOT, 'mysite', 'settings.py'))
mw = st.split('MIDDLEWARE = [')[1].split(']')[0]
ok(mw.strip().rstrip(',').endswith('"pages.activity.ActivityMiddleware"'),
   'THE MIDDLEWARE is last - a page refused above is not a visit')
ok('activity.connect()' in read(J(PG, 'apps.py')),
   'SIGN-INS AND CHANGES wired when the app starts')
ok(NOTICE in read(J(PT, 'login.html')), 'THE NOTICE under the sign-in box')
ua = read(J(PT, 'user_administration.html'))
ok("{% url 'user_activity' %}" in ua and ua.count('fa-history') == 2,
   'USER ADMINISTRATION: Activity (the bar and its More menu)')
ok(A.KEEP_DAYS >= 365 and A.FAILS == 5, 'KEPT 12 MONTHS; AN EMAIL AT 5')

head('2. THE MODULES')
for path, want in (
        ('/properties/', 'properties'), ('/property/12/', 'properties'),
        ('/tenant/', 'tenants'), ('/tenant_edit/4', 'tenants'),
        ('/lease_renewal_report/', 'tenants'),
        ('/lease-timeline/', 'tenants'),
        ('/suppliers/', 'suppliers'), ('/fsr/', 'issues'),
        ('/projects/', 'projects'),
        ('/property_management_dashboard/', 'dashboard'),
        ('/invoices/', 'invoices'), ('/receipts/4/', 'receipts'),
        ('/act_expense_all/', 'expenses'), ('/petty_cash/', 'petty_cash'),
        ('/finance_revenue/', 'financials'),
        ('/tenant_lease_agreement/', 'leases'),
        ('/generate-lease-agreement/', 'generate'),
        ('/title_deeds_management/', 'deeds'),
        ('/lease-signing/3/', 'signing'),
        ('/user-administration/', 'users'), ('/my-profile/', 'menu'),
        ('/administration/signature-and-stamp/', 'marks'),
        ('/administration/company-details/', 'company'),
        ('/notifications/', 'notifications'),
        ('/passport-management/', 'passports'),
        ('/travel/m/trip/3/', 'travel'), ('/recipe_management/', 'recipes'),
        ('/meal_plans/', 'recipes'), ('/celebrations/', 'celebrations'),
        ('/wellness/journal/', 'wellness'),
        ('/personal/household-members/', 'household'), ('/crs/', 'crs'),
        ('/', ''), ('/help/', ''), ('/admin_apms/', '')):
    ok(A.module_of(path) == want, '  %s -> %s' % (path, want or 'none'),
       A.module_of(path))
ok(A.PERSONAL == {'passports', 'travel', 'recipes', 'celebrations',
                  'wellness', 'household', 'crs'},
   'PERSONAL (usage only): Passports, Travel, Recipes, Celebrations, '
   'Wellness, Household Members, CRS Reporting')
p30 = A.period('30', '', dt.date(2026, 11, 23))
p12 = A.period('12', '', dt.date(2026, 11, 23))
pm = A.period('', '2026-10', dt.date(2026, 11, 23))
ok(p30[:2] == (dt.date(2026, 10, 25), dt.date(2026, 11, 23)) and
   p12[0] == dt.date(2025, 12, 1) and
   pm[:3] == (dt.date(2026, 10, 1), dt.date(2026, 10, 31), 'October 2026'),
   'PERIODS: the last 30 days, the last 12 months, a calendar month')


class H:
    def __init__(self, m, module=''):
        self.at = dt.datetime(2026, 11, 23, 10, 0) + dt.timedelta(minutes=m)
        self.module = module


hs = [H(0), H(5), H(50), H(52)]
ss = A.sittings(hs)
ok(len(ss) == 2 and hs[0].spent == dt.timedelta(minutes=5) and
   hs[1].spent == A.LAST and hs[2].spent == dt.timedelta(minutes=2) and
   ss[0]['spent'] == dt.timedelta(minutes=6),
   'TIME SPENT: until the next page; over 30 minutes idle starts a new '
   'sitting; the last page counts a minute')
ok(A.words(dt.timedelta(minutes=95)) == '1h 35m' and
   A.words(dt.timedelta(minutes=7)) == '7m', '  shown as 1h 35m, 7m')
ok(A.device_of('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604.1')
   == 'Phone · Safari' and A.device_of('Mozilla/5.0 (Windows NT 10.0) '
   'AppleWebKit Chrome/120 Safari/537') == 'Computer · Chrome',
   'THE DEVICE: phone or computer, and the browser')

from django.db.models.signals import post_delete, post_save, pre_save  # noqa: E402,E501
_bad = []
for _sig in (pre_save, post_save, post_delete):
    for _row in _sig.receivers:
        _ref = _row[1]
        try:            # exactly as test_project_rollup reads a row
            _fn = _ref() if hasattr(_ref, '__call__') and not hasattr(
                _ref, '__name__') else _ref
        except TypeError as _e:
            _bad.append(str(_e)[:60])
ok(not _bad, 'RECEIVERS READ LIKE ANY OTHER: a row is a weak reference or '
   'a named function - never a partial that runs when called (RA15 push, '
   'test_project_rollup)', _bad)

_src = read(J(PG, 'activity.py'))
ok('at__date__' not in _src and 'def _span' in _src,
   'NO __date LOOKUP: a time range instead (MySQL without its time-zone '
   'tables matches nothing - the Changes and Sign-ins tabs were empty)')

head('3. DRIVEN (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User
    from django.core import mail
    from django.utils import timezone
    from pages.models import ActivityHit, RecordChange, SignIn
    connection.ensure_connection()
    ActivityHit.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])
if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            me = User.objects.create_user('ra15a', 'ra15a@example.com', 'pw1',
                                          is_superuser=True, is_staff=True,
                                          first_name='Papa',
                                          last_name='Tester')
            her = User.objects.create_user('ra15b', 'ra15b@example.com',
                                           'pw2', first_name='Erene',
                                           last_name='Tester')
            A_ = Client(SERVER_NAME='localhost')
            ok(A_.login(username='ra15a', password='pw1') and
               SignIn.objects.filter(user=me, kind='in').count() == 1,
               'SIGNED IN: recorded')
            A_.get('/tenant/', HTTP_USER_AGENT='Mozilla/5.0 (Windows NT '
                   '10.0) Chrome/120 Safari/537')
            A_.get('/wellness/')
            A_.get('/tenant/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            A_.get('/tenant/', HTTP_SEC_FETCH_DEST='empty')
            hits = list(ActivityHit.objects.filter(user=me).order_by('at'))
            ok([h.module for h in hits] == ['tenants', 'wellness'] and
               hits[0].path == '/tenant/' and hits[1].path == '',
               'PAGES: business page kept; in Personal the module only - '
               'and a background fetch is not a visit',
               [(h.module, h.path) for h in hits])
            H_ = Client(SERVER_NAME='localhost')
            mail.outbox = []
            for i in range(6):
                H_.login(username='ra15b', password='wrong')
            fails = SignIn.objects.filter(username='ra15b', kind='failed')
            ok(fails.count() == 6 and fails.first().user_id == her.pk,
               'WRONG PASSWORDS: each one recorded, against the person')
            ok(len(mail.outbox) == 1 and
               '5 wrong passwords for ra15b' in mail.outbox[0].subject and
               mail.outbox[0].to == ['alerts@example.com'],
               'THE 5TH IN A ROW: one email (not again at the 6th)',
               [m.subject for m in mail.outbox])
            H_.login(username='ra15b', password='pw2')
            H_.login(username='ra15b', password='wrong')
            ok(A.in_a_row('ra15b') == 1,
               '  a good sign-in starts the count again')
            tok = A._who.set(me.pk)
            her.first_name = 'Erini'
            her.save()
            her.set_password('new-one')
            her.save()
            A._who.reset(tok)
            ch = list(RecordChange.objects.filter(
                what='User', object_id=str(her.pk)).order_by('at', 'id'))
            names = [c for x in ch for c in x.changes]
            ok(ch and ch[-2].user_id == me.pk and
               ['First name', 'Erene', 'Erini'] in names,
               'CHANGES: by whom, the field, old and new', names)
            ok(['Password', '', ''] in names,
               '  a password shows only that it changed')
            ok(RecordChange.objects.filter(what='User', action='added',
                                           name='ra15b').exists(),
               '  a new record: added')
            p = A_.get('/user-administration/activity/?tab=usage&p=30') \
                .content.decode()
            ok('data-act-module="tenants"' in p and
               'data-act-module="wellness"' in p and 'usage only' in p and
               'Property Operations' in p and 'Last 30 days' in p,
               'ACTIVITY > USAGE: the menus\' modules, Personal usage only')
            p = A_.get('/user-administration/activity/?tab=pages&p=30&u=%d'
                       % me.pk).content.decode()
            ok('/tenant/' in p and '/wellness/' not in p and
               'data-act-sitting' in p,
               'PAGES AND TIME: the business pages, never Personal\'s')
            p = A_.get('/user-administration/activity/?tab=changes&p=30') \
                .content.decode()
            ok('First name: Erene &rarr; Erini' in p and
               'Password: changed' in p, 'CHANGES: shown')
            p = A_.get('/user-administration/activity/?tab=signins&p=12') \
                .content.decode()
            ok('Wrong password' in p and 'Computer' not in p.split(
                'data-act-signins')[0] and 'Last 12 months' in p,
               'SIGN-INS: shown, the last 12 months')
            m = timezone.localdate().strftime('%Y-%m')
            ok(A_.get('/user-administration/activity/?tab=usage&m=%s' % m)
               .status_code == 200, 'A CALENDAR MONTH')
            ok(H_.get('/user-administration/activity/').status_code in (
                302, 403, 404), 'ONLY SUPERUSERS')
            p = A_.get('/user-administration/').content.decode()
            ok('data-activity-link' in p,
               'USER ADMINISTRATION: the Activity button')
            old = ActivityHit.objects.create(
                user=me, at=timezone.now() - dt.timedelta(days=400),
                day=timezone.localdate() - dt.timedelta(days=400),
                module='tenants')
            A._purged['day'] = None
            A.purge()
            ok(not ActivityHit.objects.filter(pk=old.pk).exists() and
               ActivityHit.objects.filter(user=me).exists(),
               'KEPT 12 MONTHS: older deleted once a day')
            raise Rollback
    except Rollback:
        pass
    ok(NOTICE in Client(SERVER_NAME='localhost').get('/login/')
       .content.decode(), 'THE SIGN-IN PAGE says it')

head('4. HELP AND REGISTERED')
adm = read(J(PG, 'help_content', 'administration.html'))
ok('data-tab-slug="ua-activity"' in adm and 'Personal stays private' in adm
   and NOTICE in adm, 'HELP: User Administration > Activity')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
