# -*- coding: utf-8 -*-
"""test_ra35_santa_details_later.py - round RA35, 28 Nov 2026.

RELEASE RA35 - SECRET SANTA: REQUIRED FIELDS; DATE, TIME AND PLACE LATER.
Demetri, 28 Nov: "I would like to have the following fields mandatory:
Occassion, Name, Budget and Rules. Then for Date, Time and Place, I want a
check box to opt if I want to enter these or not ... it must clear these
fields and grey them out ... In the email, if I don't have a date time and
place, it must correctly state this ... if I at a later stage untick the
checkbox and I then enter and save a date, time and place, it must prompt
me to send out a new email to all parties". Migration pages 0124.
No real email leaves: locmem.
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

SUFFIX = '.bak_ra35'
ME = 'test_ra35_santa_details_later.py'
PATCHER = 'apply_ra35_santa_details_later.py'
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
page = read(J(T, 'secret_santa.html'))
views = read(J(PG, 'views', 'secret_santa.py'))
santa = read(J(PG, 'santa.py'))
helpt = read(J(PG, 'help_content', 'administration.html'))
ok(all(s in page for s in ('id="ssOcc" name="occasion" required', 'name="title" maxlength="120"',
                           'placeholder="40" required', 'maxlength="2000" required')),
   'REQUIRED in the form: Occasion, Name, Budget, Rules')
ok('id="ssLater" name="details_later"' in page and page.count('data-ss-dtp') >= 4,
   'THE BOX: Date, time and place not decided yet; it governs the three fields')
ok("if (on && clear) { el.value = ''; }" in page and 'el.required = !on' in page,
   '  ticking clears and greys them; unticked they are required')
ok('id="ssDetailsModal"' in page and 'Send the date and place' in page, 'THE PROMPT, and the button it leaves')
ok("'details': (" in santa or "TONES['christmas']['details']" in santa, 'THE DETAILS EMAIL in every tone')
ok(os.path.isfile(J(PG, 'migrations', '0124_santa_details_later.py')), 'MIGRATION 0124')
ok('not decided yet' in helpt, 'HELP says so')

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
    from pages.models import SantaExchange
    from pages import santa as SS

    with transaction.atomic():
        me = User.objects.create_user('ss35', 'd35@example.com', 'x', first_name='Demetri')
        p, _ = Permission.objects.get_or_create(codename='can_access_celebrations', content_type__app_label='auth',
                                                defaults={'name': 'x'})
        me.user_permissions.add(p)
        C = Client(SERVER_NAME='localhost')
        C.force_login(me)
        url, save = '/celebrations/secret-santa/', '/celebrations/secret-santa/save/'
        base = {'action': 'event', 'year': 2026, 'occasion': 'christmas', 'title': 'Full Manias Family',
                'budget': '40', 'rules': 'No gift cards.'}
        for gap in ('title', 'budget', 'rules', 'occasion'):
            body_ = dict(base, details_later='1')
            body_.pop(gap)
            r = C.post(save, body_, follow=True)
            ok(not SantaExchange.objects.filter(owner=me).exists() and 'Please fill in' in r.content.decode(),
               'REQUIRED: no %s, nothing saved, and it says what is missing' % gap)
        r = C.post(save, dict(base), follow=True)
        ok(not SantaExchange.objects.filter(owner=me).exists() and 'Date, Time, Place' in r.content.decode(),
           'UNTICKED: Date, Time and Place are required')
        C.post(save, dict(base, details_later='1', event_date='2026-12-25', event_time='13:00', place='Home'))
        ex = SantaExchange.objects.get(owner=me)
        ok(ex.details_later and ex.event_date is None and ex.event_time is None and ex.place == '',
           'TICKED: saved, and the date, time and place are cleared')
        for f, e in (('Demetri', 'd35@example.com'), ('Angie', 'a35@example.com'), ('Alex', 'x35@example.com')):
            C.post(save, {'action': 'person_add', 'ex': ex.pk, 'first_name': f, 'email': e})
        mail.outbox = []
        C.post(save, {'action': 'draw', 'ex': ex.pk})
        ex.refresh_from_db()
        h = mail.outbox[0].alternatives[0][0] if mail.outbox else ''
        ok(len(mail.outbox) == 3 and 'To be confirmed' in h and '>Where<' not in h,
           'THE DRAW EMAIL says: To be confirmed (no Where line)')
        ok("To be confirmed - you'll get an email with the date, time and place" in mail.outbox[0].body,
           '  and in the plain text')
        from django.utils import timezone as _tz
        ok(SS.due_reminders(ex, _tz.localdate()) == [], 'NO DATE: no reminders fall due')
        mail.outbox = []
        r = C.post(save, dict(base, ex=ex.pk, event_date='2026-12-25', event_time='13:00', place="Laz' & Lida's"))
        ex.refresh_from_db()
        ok(not ex.details_later and ex.details_due and r['Location'].endswith('&ask=details') and not mail.outbox,
           'UNTICKED AND SAVED AFTER THE DRAW: details owed, the page asks - nothing sent yet')
        t = C.get(r['Location']).content.decode()
        ok('id="ssDetailsModal"' in t and "modal('show')" in t and 'Send to all 3' in t,
           '  the prompt opens at once: Send to all 3')
        t = C.get(url + '?ex=%d' % ex.pk).content.decode()
        ok("modal('show')" not in t and 'data-target="#ssDetailsModal"' in t, '  Not now: the Send the date and place button stays')
        C.post(save, {'action': 'details_send', 'ex': ex.pk})
        ex.refresh_from_db()
        h = mail.outbox[0].alternatives[0][0] if mail.outbox else ''
        ok(len(mail.outbox) == 3 and not ex.details_due and 'The date and place' in mail.outbox[0].subject
           and 'Friday 25 December, 13:00' in h and 'Laz&#x27; &amp; Lida&#x27;s' in h and 'your secret recipient' in h,
           'SENT: all three get the date, time and place, with whom they are buying for')
        ok('data-target="#ssDetailsModal"' not in C.get(url + '?ex=%d' % ex.pk).content.decode(), '  and the button goes')
        mail.outbox = []
        C.post(save, dict(base, ex=ex.pk, event_date='2026-12-26', event_time='14:00', place='Home'))
        ex.refresh_from_db()
        ok(not ex.details_due, 'A LATER CHANGE of a date that was already set does not ask again')
        off = SantaExchange(owner=me, year=2026, title='Team', occasion='office', details_later=True)
        ok('Date and venue confirmed' in SS.message(off, 'details', ex.people.first(), 'Bob')[0]
           and 'To be confirmed' in SS.message(off, 'draw', ex.people.first(), 'Bob')[2],
           'OFFICE: "Date and venue confirmed", and To be confirmed too')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 2 ran', str(e)[:200])

head('3. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
