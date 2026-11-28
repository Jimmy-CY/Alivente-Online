# -*- coding: utf-8 -*-
"""test_ra34_santa_test_nickname.py - round RA34, 27 Nov 2026.

RELEASE RA34 - SECRET SANTA: NAME (NICKNAME); THE TEST IS YOU. AND THE
PC SEARCH FROM A RUN'S ROW, AND BACK ON THE ACQUISITIONS OVERVIEW.
Demetri, 27 Nov, on his test email: "why is my name at the top not my
nickname? ... or put in brackets underneath (a.k.a. Jimmy-changa)".
Then: "drop the a.k.a from everywhere, just the nickname in brackets".
Every email now greets the first name with "(nickname)" under it,
and Send me a test / Preview email use his own entry in the event (by his
login email), so they read exactly as his real email will.
Acquisitions: "put a start PC run button or icon ... next to incomplete" -
a desktop icon beside the eye on each scenario's latest cloud run that
finished incomplete with no PC run after it; and "we need a Back button
here to take the user back to the Home page" on the Overview.
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

SUFFIX = '.bak_ra34'
ME = 'test_ra34_santa_test_nickname.py'
PATCHER = 'apply_ra34_santa_test_nickname.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
PG = J(ROOT, 'pages')
T = J(PG, 'templates')

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
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

head('1. THE SOURCE')
santa = read(J(PG, 'santa.py'))
views = read(J(PG, 'views', 'secret_santa.py'))
helpt = read(J(PG, 'help_content', 'administration.html'))
ok("'aka': (" in santa, 'THE GREETING carries (nickname) under the name')
ok(views.count('me = _me(ex, request.user)') == 2 and 'def _me(' in views,
   'THE TEST and THE PREVIEW both greet your own entry')
ok('Ho ho ho, Demetri! (Papa)' in helpt, 'HELP says so')

head('2. DRIVEN')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


try:
    from django.core import mail
    from django.db import transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from pages.models import SantaExchange, SantaPerson
    from pages import santa as SS

    with transaction.atomic():
        me = User.objects.create_user('ss34', 'Demetri34@Example.com', 'x', first_name='Demetri')
        p, _ = Permission.objects.get_or_create(codename='can_access_celebrations', content_type__app_label='auth',
                                                defaults={'name': 'x'})
        me.user_permissions.add(p)
        ex = SantaExchange.objects.create(owner=me, year=2026, title='Full Manias Family', budget=40)
        papa = SantaPerson.objects.create(exchange=ex, first_name='Demetri', surname='Manias',
                                          nickname='Jimmy-changa', email='demetri34@example.com')
        angie = SantaPerson.objects.create(exchange=ex, first_name='Angie', surname='Manias', email='a34@example.com')
        _s, txt, h = SS.message(ex, 'draw', papa, angie)
        ok('Ho ho ho, Demetri!' in h and '>(Jimmy-changa)</div>' in h and 'a.k.a' not in h, 'GREETING: Ho ho ho, Demetri! (Jimmy-changa)')
        ok('Ho ho ho, Demetri!\n(Jimmy-changa)' in txt, '  and in the plain-text email')
        _s, _t, h2 = SS.message(ex, 'draw', angie, papa)
        ok('Ho ho ho, Angie!' in h2 and '>(' not in h2.split('your secret recipient')[0],
           'NO NICKNAME: just the name, no bracket line')
        same = SantaPerson(first_name='Erene', surname='Manias', nickname='Erene')
        ok('>(Erene)' not in SS.message(ex, 'draw', same, papa)[2].split('your secret recipient')[0],
           '  a nickname that only repeats the name is not added')
        off = SantaExchange.objects.create(owner=me, year=2026, title='Team', occasion='office')
        ok('Hi Demetri,' in SS.message(off, 'draw', papa, angie)[2] and '>(Jimmy-changa)</div>' in SS.message(off, 'draw', papa, angie)[2],
           'OFFICE: Hi Demetri, (nickname) too')
        off.delete()
        C = Client(SERVER_NAME='localhost')
        C.force_login(me)
        hp = C.get('/celebrations/secret-santa/preview/?ex=%d' % ex.pk).content.decode()
        ok('Ho ho ho, Demetri!' in hp and '>(Jimmy-changa)</div>' in hp, 'PREVIEW: your own entry, matched by login email')
        mail.outbox = []
        C.post('/celebrations/secret-santa/save/', {'action': 'test', 'ex': ex.pk})
        ok(len(mail.outbox) == 1 and '>(Jimmy-changa)</div>' in mail.outbox[0].alternatives[0][0]
           and mail.outbox[0].subject.startswith('TEST'), 'SEND ME A TEST: the same')
        papa.email = 'other34@example.com'
        papa.save()
        hp = C.get('/celebrations/secret-santa/preview/?ex=%d' % ex.pk).content.decode()
        ok('Ho ho ho, Demetri!' in hp and 'Jimmy-changa' not in hp.split('your secret recipient')[0], 'NOT IN THE EVENT: the login\'s first name, no nickname')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 2 ran', str(e)[:200])

head('3. ACQUISITIONS: THE PC ICON, AND BACK')
runs_t = read(J(ROOT, 'acquisitions', 'templates', 'acquisitions', 'runs.html'))
over_t = read(J(ROOT, 'acquisitions', 'templates', 'acquisitions', 'overview.html'))
base_t = read(J(PG, 'templates', 'base.html'))
ok('icon-action-btn icon-pc-search' in runs_t and 'data-target="#acqPcModal"' in runs_t.split('icon-pc-search')[1][:200],
   'THE ICON opens the PC search pop-up')
ok('.icon-pc-search ' in base_t and "'pc-search': ADVANCE" in read(J(ROOT, 'alv_rowactions.py')),
   '  styled in base, and in the house order (after the eye)')
ok("href=\"{% url 'home' %}\" class=\"btn action-back\"" in over_t, 'THE OVERVIEW has Back to home')
try:
    import io
    from datetime import timedelta
    from django.core.management import call_command
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from django.db import transaction
    from django.utils import timezone
    from acquisitions.models import Scenario, SearchRun, SiteResult, Website
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        flat = Scenario.objects.get(property_type='apartment')
        web = Website.objects.first()
        ed = User.objects.create_user('ra34e', 'ra34e@example.com', 'pw')
        rd = User.objects.create_user('ra34r', 'ra34r@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            ed.user_permissions.add(Permission.objects.get(codename=cn))
        rd.user_permissions.add(Permission.objects.get(codename='can_access_acquisitions'))
        SearchRun.objects.all().delete()
        now_ = timezone.now()

        def run(mins_ago, outcome, where='cloud', done=True):
            r = SearchRun.objects.create(scenario=flat, where=where)
            SearchRun.objects.filter(pk=r.pk).update(
                started_at=now_ - timedelta(minutes=mins_ago),
                finished_at=(now_ - timedelta(minutes=mins_ago - 5)) if done else None)
            if outcome:
                SiteResult.objects.create(run=r, website=web, outcome=outcome)
            return SearchRun.objects.get(pk=r.pk)
        old = run(300, 'blocked')
        new = run(60, 'blocked')
        E = Client(SERVER_NAME='localhost')
        E.force_login(ed)

        def icons(c):
            html_ = c.get('/acquisitions/runs/').content.decode()
            return dict(re.findall(r'href="\?run=(\d+)" class="icon-action-btn icon-view"[^<]*<i[^>]*></i></a>'
                                   r'(<a href="#" class="icon-action-btn icon-pc-search)?', html_))
        got = icons(E)
        ok(got.get(str(new.pk)) and not got.get(str(old.pk)), 'THE ICON: on the latest incomplete cloud run only', got)
        R = Client(SERVER_NAME='localhost')
        R.force_login(rd)
        ok(not any(icons(R).values()), '  not for someone who cannot edit')
        pc = run(30, 'full', where='pc')
        SearchRun.objects.filter(pk=pc.pk).update(follow_up_of=new)
        ok(not any(icons(E).values()), '  gone once a PC run has followed it up')
        SearchRun.objects.filter(pk=pc.pk).update(follow_up_of=None)
        live = run(2, '', done=False)
        ok(not any(icons(E).values()), '  while the newest cloud run is still running: none yet')
        live.delete()
        good = run(10, 'full')
        ok(not any(icons(E).values()), '  a complete latest run: no icon')
        good.delete()
        ok('Back to home' in E.get('/acquisitions/').content.decode(), 'THE OVERVIEW renders Back to home')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 3 ran', str(e)[:200])

head('4. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
