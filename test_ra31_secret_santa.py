# -*- coding: utf-8 -*-
"""test_ra31_secret_santa.py - round RA31, 26 Nov 2026.

RELEASE RA31 - SECRET SANTA, IN CELEBRATIONS.
Demetri, 26 Nov: "capture (and save) up to 20 people, with their Name,
Surname, Nicknames and email addresses. Then I need to have the ability to
exclude certain people buying gifts for certain people. Then I need to
enter an amount that everyone will spend on their randomly allocated
person. The system then needs to allocate people randomly and then send
out a nice personalised Xmas email to everybody explaining what the rules
are, how much to spend, when the secret santa event is happening."
And: last year's pairs never again; he takes part, so the pairings stay
hidden from him; reminders; an optional big reveal; from "Santa
(Demetri)"; Christmas only; no calendar invite. Migration 0122.
No real email leaves: the locmem backend catches every one.
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

SUFFIX = '.bak_ra31'
ME = 'test_ra31_secret_santa.py'
PATCHER = 'apply_ra31_secret_santa.py'
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
models = read(J(PG, 'models.py'))
santa = read(J(PG, 'santa.py'))
views = read(J(PG, 'views', 'secret_santa.py'))
page = read(J(T, 'secret_santa.html'))
dash = read(J(T, 'celebration_dashboard.html'))
mgmt = read(J(T, 'celebration_management.html'))
tick = read(J(PG, 'management', 'commands', 'santa_tick.py'))
daily = read(J(PG, 'management', 'commands', 'check_lease_renewal_and_invoices.py'))
hlp = read(J(PG, 'help_content', 'administration.html'))
mig = read(J(PG, 'migrations', '0122_secret_santa.py'))
ok('class SantaExchange(' in models and 'class SantaPerson(' in models and 'class SantaExclusion(' in models
   and 'class SantaPair(' in models and "'0121_activity_log'" in mig, 'THE MODELS, and migration 0122 after 0121')
ok('def last_year_pairs(' in santa and 'def draw(' in santa and 'SystemRandom' in santa,
   'THE DRAW: random, and last year\'s pairs barred')
ok('.ics' not in santa and 'text/calendar' not in santa, 'NO CALENDAR INVITE ("We don\'t need the calendar invite")')
ok("'Santa (%s)'" in santa and 'reply_to=' in santa, 'FROM "Santa (Demetri)", replies to him')
ok('ex.revealed_at' in views and "if (mine and ex.revealed_at) else []" in views,   # RA32 - and only on his own
   'THE PAIRINGS are read for the page only once he has pressed Reveal')
ok("url 'secret_santa'" in dash and "url 'secret_santa'" in mgmt, 'REACHED from both Celebrations pages')
ok("call_command('santa_tick'" in daily and 'due_reminders' in tick, 'THE REMINDERS ride the daily job')
ok('data-tab-slug="cel-santa"' in hlp, 'HELP: a Secret Santa tab in Celebrations help')
ok('activity' not in views.lower().replace('personal, so nothing here goes in the activity log', ''),
   'personal: nothing here is written to the activity log')

head('2. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
from django.core import mail as _mail                       # noqa: E402
_mail.outbox = []
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


try:
    import datetime
    import random
    from django.core import mail
    from django.core.management import call_command
    from django.db import transaction
    from django.test import Client
    from django.utils import timezone
    from django.contrib.auth.models import Permission, User
    from pages.models import (Contact, SantaExchange, SantaExclusion, SantaPair, SantaPerson,
                              UserProfile)
    from pages.workspace import ensure_workspace
    from pages import santa as SS

    def perm(code):
        p, _ = Permission.objects.get_or_create(codename=code, content_type__app_label='auth',
                                                defaults={'name': code})
        return p
    with transaction.atomic():
        me = User.objects.create_user('ss_me', 'papa@example.com', 'x', first_name='Demetri')
        other = User.objects.create_user('ss_other', 'o@example.com', 'x')
        for u in (me, other):
            u.user_permissions.add(perm('can_access_celebrations'), perm('can_edit_celebrations'))
        ws = ensure_workspace(me)
        C, C2 = Client(SERVER_NAME='localhost'), Client(SERVER_NAME='localhost')
        C.force_login(me)
        C2.force_login(other)
        UserProfile.objects.update_or_create(user=me, defaults={'workspace': ws})
        con = Contact.objects.create(name='Nikos Pappas', email='nikos@example.com', workspace=ws,
                                     relationship='friend', created_by=me)
        Y = 2026
        url = '/celebrations/secret-santa/'
        save = url + 'save/'
        t = C.get(url + '?year=%d' % Y)
        ok(t.status_code == 200 and 'Start this Secret Santa' in t.content.decode(),
           'THE PAGE opens on a new Christmas, asking for the event')
        r = C.post(save, {'action': 'event', 'year': Y, 'title': 'Manias Christmas', 'event_date': '2026-12-20',
                          'event_time': '19:30', 'place': 'Home, Engomi', 'budget': '40',
                          'rules': 'No gift cards. <b>Wrap it</b>.', 'remind_week': '1', 'remind_day': '1'})
        ex = SantaExchange.objects.get(owner=me, year=Y)
        ok(r.status_code == 302 and ex.budget == 40 and ex.event_time.strftime('%H:%M') == '19:30',
           'THE EVENT is saved: date, time, place, budget, rules, reminders')
        for f, s, n, e in (('Demetri', 'Manias', 'Papa', 'papa@example.com'), ('Angie', 'Manias', '', 'angie@example.com'),
                           ('Alexandra', 'Mania', 'Alex', 'alex@example.com'), ('Erene', 'Mania', '', 'erene@example.com')):
            C.post(save, {'action': 'person_add', 'year': Y, 'first_name': f, 'surname': s, 'nickname': n, 'email': e})
        C.post(save, {'action': 'contacts_add', 'year': Y, 'contact': [con.pk]})
        ok(ex.people.count() == 5 and ex.people.filter(first_name='Nikos', surname='Pappas', contact=con).exists(),
           'PEOPLE: four added by hand, one from contacts (name split into name and surname)')
        r = C.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'Dup', 'email': 'ALEX@example.com'})
        ok(ex.people.count() == 5, '  the same email twice is refused')
        C.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'Bad', 'email': 'not-an-email'})
        ok(ex.people.count() == 5, '  so is an address that is not one')
        P = {p.first_name: p for p in ex.people.all()}
        C.post(save, {'action': 'exclude', 'year': Y, 'giver': P['Demetri'].pk, 'receiver': P['Angie'].pk, 'both': '1'})
        ok(SantaExclusion.objects.filter(exchange=ex).count() == 2, 'EXCLUDE a couple: both ways, two rows')
        t = C.get(url + '?year=%d' % Y).content.decode()
        ok('Angie &harr;' in t and 'a valid draw is possible' in t, '  shown as a tag with ↔, and a draw is possible')

        # last year's pairs
        last = SantaExchange.objects.create(owner=me, year=Y - 1, title='Last year', drawn_at=timezone.now())
        la = SantaPerson.objects.create(exchange=last, first_name='Alexandra', email='alex@example.com')
        le = SantaPerson.objects.create(exchange=last, first_name='Erene', email='erene@example.com')
        SantaPair.objects.create(exchange=last, giver=la, receiver=le)
        ok_, banned = SS.allowed(ex)
        ok(banned.get((P['Alexandra'].pk, P['Erene'].pk)) == 'last year'
           and P['Erene'].pk not in ok_[P['Alexandra'].pk],
           "LAST YEAR'S PAIR: Alex drew Erene in %d, so she cannot again" % (Y - 1))
        t = C.get(url + '?year=%d' % Y).content.decode()
        ok('Erene (last year)' in t, '  shown in amber')

        # the draw, many times over: always valid
        bad = 0
        for i in range(300):
            got = SS.draw(ok_, random.Random(i))
            if got is None or sorted(got) != sorted(ok_) or sorted(got.values()) != sorted(ok_) \
               or any(g == r or r not in ok_[g] for g, r in got.items()):
                bad += 1
        ok(bad == 0, 'THE DRAW, 300 times: everyone gives once and receives once, never themselves, never barred')
        ok(SS.draw({1: {2}, 2: {1}, 3: {1, 2}}) is None, '  and an impossible set of rules says so (None)')

        mail.outbox.clear()
        r = C.post(save, {'action': 'test', 'year': Y})
        ok(len(mail.outbox) == 1 and mail.outbox[0].to == ['papa@example.com'] and 'TEST' in mail.outbox[0].subject,
           'SEND ME A TEST: one email, to him')
        m = mail.outbox[0]
        h = m.alternatives[0][0]
        ok('Santa (Demetri)' in m.from_email and m.reply_to == ['papa@example.com'],
           '  from "Santa (Demetri)", replies to him')
        ok('&lt;b&gt;Wrap it&lt;/b&gt;' in h and '<b>Wrap it</b>' not in h and '€40' in h
           and 'Sunday 20 December, 19:30' in h and 'Home, Engomi' in h,
           '  budget, date, time, place and his rules - his text shown, not run as markup')
        ok(not m.attachments, '  no calendar invite attached')

        mail.outbox.clear()
        r = C.post(save, {'action': 'draw', 'year': Y})
        ex.refresh_from_db()
        pairs = list(ex.pairs.select_related('giver', 'receiver'))
        ok(r.status_code == 302 and ex.drawn_at and len(pairs) == 5 and len(mail.outbox) == 5,
           'DRAW AND SEND: five pairs, five emails')
        to = {msg.to[0]: msg for msg in mail.outbox}
        okm = True
        for pr in pairs:
            msg = to.get(pr.giver.email)
            body = msg.alternatives[0][0] if msg else ''
            if not msg or pr.receiver.full_name not in body or 'Ho ho ho, %s!' % pr.giver.called not in body:
                okm = False
        ok(okm, '  each email greets its person by nickname and names whom they drew')
        ok(all(pr.giver_id != pr.receiver_id for pr in pairs)
           and not any((pr.giver_id, pr.receiver_id) in ((P['Demetri'].pk, P['Angie'].pk), (P['Angie'].pk, P['Demetri'].pk),
                                                        (P['Alexandra'].pk, P['Erene'].pk)) for pr in pairs),
           '  and the pairs keep every exclusion and last year\'s pair')
        t = C.get(url + '?year=%d' % Y).content.decode()
        names_after_arrow = [pr.receiver.full_name for pr in pairs]
        ok('Drawn ' in t and '&rarr;' not in t, 'HE TAKES PART: the page says Drawn and shows no pairing')
        # RA32, 27 Nov 2026 - the people are no longer locked after the draw
        # (a redraw follows; test_ra32_santa_back.py drives it). Add and take
        # back out, so the five pairs below stand.
        r = C.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'Late', 'email': 'late@example.com'})
        late = ex.people.filter(email='late@example.com').first()
        ok(late is not None, 'AFTER THE DRAW a person can still be added (RA32)')
        if late is not None:
            C.post(save, {'action': 'person_remove', 'year': Y, 'pid': late.pk})
        ok(ex.people.count() == 5 and ex.pairs.count() == 5, '  and removed again, the draw untouched')
        mail.outbox.clear()
        C.post(save, {'action': 'resend', 'year': Y, 'pid': P['Erene'].pk})
        ok(len(mail.outbox) == 1 and mail.outbox[0].to == ['erene@example.com'], 'RESEND: one email, to that person')
        C.post(save, {'action': 'reveal', 'year': Y})
        ex.refresh_from_db()
        t = C.get(url + '?year=%d' % Y).content.decode()
        ok(ex.revealed_at and t.count('&rarr;') == 5, 'REVEAL: recorded, and then the five pairings show')

        # reminders
        mail.outbox.clear()
        ok(SS.due_reminders(ex, datetime.date(2026, 12, 13)) == ['week'] and SS.due_reminders(ex, datetime.date(2026, 12, 19)) == ['day']
           and SS.due_reminders(ex, datetime.date(2026, 12, 1)) == [] and SS.due_reminders(ex, datetime.date(2026, 12, 20)) == [],
           'REMINDERS fall due a week before and the day before, not otherwise')
        ex.event_date = timezone.localdate() + datetime.timedelta(days=5)
        ex.save()
        call_command('santa_tick', stdout=io.StringIO())
        call_command('santa_tick', stdout=io.StringIO())
        ex.refresh_from_db()
        ok(len(mail.outbox) == 5 and ex.week_sent_at and 'One week to go' in mail.outbox[0].subject,
           '  the week reminder goes once to everyone, however often the job runs')

        mail.outbox.clear()
        C.post(save, {'action': 'reveal_send', 'year': Y})
        ok(len(mail.outbox) == 5 and 'big reveal' in mail.outbox[0].subject.lower()
           and 'your Secret Santa' in mail.outbox[0].alternatives[0][0], 'THE BIG REVEAL: everyone learns who their Santa was')

        C.post(save, {'action': 'unlock', 'year': Y})
        ex.refresh_from_db()
        ok(ex.drawn_at is None and not ex.pairs.exists(), 'UNDO THE DRAW: pairings gone, page unlocked, nobody emailed')

        # private
        r2 = C2.get(url + '?year=%d' % Y).content.decode()
        ok('Manias Christmas' not in r2, 'PRIVATE: another user does not see his Secret Santa')
        C2.post(save, {'action': 'person_add', 'year': Y, 'first_name': 'X', 'email': 'x@example.com'})
        ok(not ex.people.filter(email='x@example.com').exists(), '  and cannot add to it')
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
