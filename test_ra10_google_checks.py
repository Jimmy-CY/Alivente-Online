# -*- coding: utf-8 -*-
"""test_ra10_google_checks.py - round RA10, 21 Nov 2026.

RELEASE RA10 - NOT FOUND ON GOOGLE; WHO USED EACH CHECK.
Demetri, 21 Nov: "Can we check which user used the 35 so far for today?" -
every Google check is logged with who, what for and trip, and listed on
Travel > Google allowance. And a suggestion Google cannot find is marked
Not found on Google instead of being tried - and stopping the morning
catch-up - every day. The distance note gets its own class (Font
Awesome's .far gave it the icon font). Daily spending: a bin beside the
pencil ("Can we not rather just put a trash can next to the pencil?").
Suggestions outside what you asked for go to their own section, closed to
start ("Let's put this in RA10. Let's start it closed for now."). And
Change what you like reuses what Google already said ("I am happy with
your suggestion for reusing Google checks").
No test here calls Google.
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

SUFFIX = '.bak_ra10'
ME = 'test_ra10_google_checks.py'
PATCHER = 'apply_ra10_google_checks.py'
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
import django                                               # noqa: E402
django.setup()
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from travel import gplaces as G                             # noqa: E402
from travel import gquota as Q                              # noqa: E402
from travel import ideas as ID                              # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. THE SOURCE')
md = read(J(TV, 'models.py'))
ok("('nf', 'Not found on Google')" in md and
   'class GoogleCheck(models.Model):' in md,
   'NOT FOUND ON GOOGLE, and a log of every Google check')
ok(os.path.isfile(J(TV, 'migrations', '0014_google_checks.py')),
   'MIGRATION travel 0014')
card = read(J(TT, '_ideas_card.html'))
ok("is-far" in card and "' far'" not in card and ' far{' not in card,
   'THE DISTANCE NOTE: class is-far, not Font Awesome\'s .far')
for f in (J(TT, '_style.html'), J(TV, 'assets', 'travel.css')):
    c = read(f)
    ok('.tv-id-flag.is-far' in c and '.tv-id-flag.far ' not in c and
       '.tv-id-flag.is-nf' in c, '  styled: %s' % os.path.basename(f))
ok("i.flag != 'nf' %} is-dim" in card,
   'NOT FOUND is not greyed out (only noted)')
ok("gquota.purpose('more' if job.more else 'suggest'" in
   read(J(TV, 'ideas.py')), 'A SUGGEST RUN logs as Suggest / Show me more, '
   'by whoever asked')
ok("gquota.purpose('now'" in read(J(TV, 'views_ideas.py')) and
   "gquota.purpose('key')" in read(J(ROOT, 'pages', 'key_health.py')),
   '  Check them now; the key check')
ok(G.key() == '', 'NEVER GOOGLE FROM A TEST: no key here')

bud = read(J(TT, '_budget.html'))
ok('class="tv-spend-trash"' in bud and 'data-spend-del' in bud and
   bud.count('data-spend-del') == 1 and 'action-danger' not in bud,
   'DAILY SPENDING: a bin beside the pencil; no Delete button under '
   'the amount')
ok('.tv-spend-trash' in read(J(TT, '_style.html')), '  styled')
ok('data-budget-clear' in bud and 'fa-trash-alt' in bud and
   '> Change</button>' not in bud and
   'data-budget-clear' not in read(J(TT, '_budget_form.html')),
   'THE BUDGET: the pencil is only a pencil, a bin beside it; no Remove '
   'budget under the form')
ok('.tv-spend-add select.form-control:not([size]):not([multiple]) { '
   'height: 38px;' in read(J(TT, '_style.html')),
   'THE CURRENCY DROP-DOWN is as tall as the other fields')

head('2. DRIVEN (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import (GoogleAllowance, GoogleCheck, GoogleUse,
                               Idea, Trip)
    connection.ensure_connection()
    GoogleCheck.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    _key, _search = G.key, G.search
    try:
        with transaction.atomic():
            GoogleUse.objects.all().delete()
            GoogleCheck.objects.all().delete()
            GoogleAllowance.objects.all().delete()
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra10a', 'ra10a@example.com', 'x',
                                          is_superuser=True,
                                          first_name='Papa',
                                          last_name='Tester')
            her = User.objects.create_user('ra10b', 'ra10b@example.com', 'x',
                                           first_name='Erene',
                                           last_name='Tester')
            for x in (me, her):
                x.user_permissions.add(perm)
                UserProfile.objects.update_or_create(
                    user=x, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            t = Trip.objects.create(owner=me, name='RA10 Beauvais')
            t2 = Trip.objects.create(owner=her, name='RA10 other')
            # ---- the log ----
            with Q.purpose('suggest', user=her, trip=t2):
                Q.note()
                with Q.purpose(trip=t):
                    Q.note()
            Q.note()
            rows = list(GoogleCheck.objects.order_by('id'))
            ok(len(rows) == 3 and rows[0].why == 'suggest' and
               rows[0].user_id == her.pk and rows[0].trip_id == t2.pk,
               'LOGGED: why, who and trip with each check', rows)
            ok(rows[1].why == 'suggest' and rows[1].user_id == her.pk and
               rows[1].trip_id == t.pk,
               '  an inner purpose keeps why and who, changes the trip')
            ok(rows[2].why == 'other' and rows[2].user_id is None,
               '  outside any purpose: Other, nobody')
            ok(GoogleUse.objects.get(day=Q._today()).searches == 3,
               '  and still counted (3 today)')
            GoogleCheck.objects.all().delete()
            GoogleUse.objects.all().delete()
            # ---- not found, and the catch-up no longer stops ----
            t.start_date = Q._today() + dt.timedelta(5)
            t.end_date = Q._today() + dt.timedelta(6)
            t.save()
            for k, n in enumerate(['Plateau du Caumont', 'Gerberoy',
                                   'Beauvais Cathedral']):
                Idea.objects.create(trip=t, city='Beauvais', name=n,
                                    position=k)
            G.key = lambda: 'fake-key'

            def fake(text, near=None, opener=None):
                Q.note()
                if text.startswith(('Plateau', 'Gerberoy')):
                    return None
                return {'status': 'OPERATIONAL', 'gid': 'g', 'lat': 49.43,
                        'lng': 2.08, 'rating': 4.7, 'ratings': 5000,
                        'price': '', 'open_days': {0, 1, 2, 3, 4, 5, 6}}
            G.search = fake
            A.post('/travel/%d/ideas/recheck/' % t.pk)
            nf = Idea.objects.get(trip=t, name='Gerberoy')
            ok(ID.waiting(t).count() == 0 and nf.checked and
               nf.flag == 'nf' and 'Not found on Google' in nf.flag_text,
               'NOT FOUND ON GOOGLE: checked and marked, not waiting',
               (nf.checked, nf.flag))
            ok(Idea.objects.get(trip=t, name='Beauvais Cathedral').rating
               == 4.7, '  ...and the one behind it was still checked')
            ok(set(GoogleCheck.objects.values_list('why', flat=True)) ==
               {'now'} and GoogleCheck.objects.filter(
                   user=me, trip=t).count() == 4,
               'CHECK THEM NOW: logged as Check them now, by me, the trip '
               '(1 centre + 3)', list(GoogleCheck.objects.values_list(
                   'why', 'user_id', 'trip_id')))
            p = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            m = re.search(r'<div class="tv-id-card([^"]*)" data-idea="%d"'
                          % nf.pk, p)
            ok(m and 'is-dim' not in m.group(1) and
               'tv-id-flag is-nf' in p and 'Not found on Google' in p,
               'THE CARD: a grey note, not greyed out, still tickable',
               m and m.group(1))
            Idea.objects.filter(pk=nf.pk).update(
                flag='far', flag_text='3 km from the centre - outside your '
                '1 km')
            p = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('tv-id-flag is-far' in p and 'tv-id-flag far' not in p,
               'THE DISTANCE NOTE has its own class')
            Idea.objects.create(trip=t, city='Beauvais', name='Saint-Pierre',
                                position=9)
            from django.utils import timezone as _tz
            late = _tz.localtime().replace(hour=11)
            ok(Q.daily_recheck(late) == 1 and GoogleCheck.objects.filter(
                why='morning', user=None, trip=t).count() == 2,
               'THE MORNING CATCH-UP: logged as Alivente itself, with the '
               'trip')
            old = GoogleCheck.objects.create(
                day=Q._today() - dt.timedelta(Q.KEEP_DAYS + 5))
            a = Q.allowance()
            a.rechecked_on = None
            a.save()
            Q.daily_recheck(late)
            ok(not GoogleCheck.objects.filter(pk=old.pk).exists(),
               'KEPT 13 MONTHS: older entries tidied once a day')
            u = Q.used_by()
            ok(u['today'] and u['today'][0]['who'] == 'Papa Tester' and
               u['today'][0]['n'] == 4 and
               any(r['who'] == 'Alivente itself' for r in u['today']),
               'WHO USED THEM: by person, most first', u['today'])
            p = A.get('/travel/google/').content.decode()
            ok('data-google-used-today' in p and 'Papa Tester' in p and
               'Check them now' in p and 'Morning catch-up' in p and
               'RA10 Beauvais' in p and 'data-google-used-month' in p,
               'THE ALLOWANCE PAGE lists them: today and this month')
            # ---- outside what you asked for ----
            from travel.models import IdeaRun
            t3 = Trip.objects.create(owner=me, name='RA10 Athens')
            run = IdeaRun.objects.create(trip=t3, status='ready', more=True,
                                         created_by=me)
            fine = Idea.objects.create(trip=t3, city='Athens', name='Plaka',
                                       interest='musts', position=1,
                                       checked=True, run=run)
            far = Idea.objects.create(trip=t3, city='Athens',
                                      name='Acropolis', interest='musts',
                                      position=0, checked=True, flag='far',
                                      flag_text='1.4 km from the centre - '
                                      'outside your 1 km', run=run)
            shut = Idea.objects.create(trip=t3, city='Athens', name='Benaki',
                                       interest='museums', position=2,
                                       checked=True, flag='closed',
                                       flag_text='Closed Mon')
            lost = Idea.objects.create(trip=t3, city='Athens', name='Nowhere',
                                       interest='museums', position=3,
                                       checked=True, flag='nf',
                                       flag_text='Not found on Google')
            p = A.get('/travel/%d/ideas/' % t3.pk).content.decode()
            o = p.find('data-idea-outside')
            ok(o > 0 and 'Outside what you asked for (2)' in p and
               '<details class="tv-id-out" data-idea-outside>' in p,
               'OUTSIDE WHAT YOU ASKED FOR: its own section, closed, with '
               'how many')
            ok(p.find('data-idea="%d"' % fine.pk) < o and
               p.find('data-idea="%d"' % lost.pk) < o and
               p.find('data-idea="%d"' % far.pk) > o and
               p.find('data-idea="%d"' % shut.pk) > o,
               '  what fits (and Not found) above; too far and closed in it')
            ok(p.find('Further from the centre than you asked', o) <
               p.find('Closed on your days', o),
               '  grouped by why')
            ok('(1 of them outside what you asked for)' in p,
               'SHOW ME MORE says how many new ones are outside')
            p = A.get('/travel/%d/ideas/?t=%d' % (t3.pk, shut.pk)) \
                .content.decode()
            ok('data-idea-outside open' in p,
               '  opens by itself when one in it is ticked')
            P = Client(SERVER_NAME='localhost')
            P.force_login(me)
            p = P.get('/travel/m/trip/%d/ideas/' % t3.pk).content.decode()
            ok('data-idea-outside' in p and 'tv-id-list tv-id-out-body' in p,
               'THE PHONE: the same section')
            # ---- Change what you like reuses what Google said ----
            job = ID.begin(t3, me, {'cities': ['Athens'], 'km': 3})
            ru = job.answers.get('reuse') or []
            ok(len(ru) == 4 and not t3.ideas.filter(state='').exists(),
               'CHANGE WHAT YOU LIKE: what Google said about the 4 is kept '
               'with the run before they go', len(ru))
            calls = []
            G.search = lambda *a, **k: calls.append(a) or None
            back = Idea(trip=t3, city='Athens', name='Acropolis',
                        interest='musts')
            closed = Idea(trip=t3, city='Athens', name='Benaki',
                          interest='museums')
            new = Idea(trip=t3, city='Athens', name='Lycabettus Hill',
                       interest='musts')
            for x in ru:
                if x['name'] == 'Acropolis':
                    x['dist_km'] = 1.4
            ok(ID.reused(back, ru, 3) and back.checked and back.flag == ''
               and not calls,
               '  one that comes back: no Google call; 1.4 km is inside the '
               'new 3 km')
            ok(ID.reused(back, ru, 1) and back.flag == 'far' and
               'outside your 1 km' in back.flag_text,
               '  ...and outside 1 km, worked out again')
            ok(ID.reused(closed, ru, 3) and closed.flag == 'closed',
               '  closed on your days stays')
            ok(not ID.reused(new, ru, 3) and not calls,
               '  a new one is not known - it is checked on Google as '
               'before')
            raise Rollback
    except Rollback:
        pass
    G.key, G.search = _key, _search

head('3. HELP AND REGISTERED')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('Who used them' in adm and 'Not found on Google' in adm,
   'HELP (computer): who used them; Not found on Google')
ok('Not found on Google' in read(J(TT, 'm', 'help.html')) and
   'Outside what you asked for' in read(J(TT, 'm', 'help.html')),
   'HELP (phone)')
ok('Outside what you asked for' in adm, 'HELP (computer): the outside '
   'section')
ok('fa-trash-alt' in adm and 'beside the pencil deletes it' in adm and
   'removes the budget' in adm,
   'HELP (computer): the bin beside the pencil')
_v = re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 23, 'THE PHONE APP moves to tv23-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
