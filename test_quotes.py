# -*- coding: utf-8 -*-
"""test_quotes.py - round QL-1, 17 Nov 2026.

RELEASE 97 - WELLNESS: 240 QUOTES, NEVER THE SAME ONE TWICE IN A ROUND.
Demetri, 17 Nov: "We need to grow our quote library to 240 real quotes.
Then we need to give each quote a fixed ID. and make sure on a user's
record we keep a record of the quotes that they have seen. Once they have
cycled through all 240 quotes, we clear the counter and start again."
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

SUFFIX = '.bak_quotes1'
ME = 'test_quotes.py'
PATCHER = 'apply_quotes_one.py'
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
WA = J(ROOT, 'wellness')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import quotes as Q, daily_line as DL          # noqa: E402
# ==========================================================================
# RA09, 21 Nov 2026 - a page shows a quote HTML-escaped (an apostrophe
# becomes &#x27;): compare it as shown, as test_wellness_six does (RA07).
from django.utils.html import escape as _esc                # noqa: E402
head('1. THE LIBRARY')
# ==========================================================================
ok(len(Q.QUOTES) == 240, '240 quotes', len(Q.QUOTES))
ok([q['id'] for q in Q.QUOTES] == list(range(1, 241)),
   'each with a fixed id, 1 to 240, in order')
ok(len({q['text'].lower() for q in Q.QUOTES}) == 240,
   '  no quote twice')
ok(all(q['text'] and q['author'] for q in Q.QUOTES),
   'every one says whose it is')
THEMES = {'start', 'steady', 'comeback', 'rest', 'gratitude', 'strength',
          'mind'}
ok(all(q['themes'] and set(q['themes']) <= THEMES for q in Q.QUOTES),
   '  and has a theme from the seven')
texts = ' '.join(q['text'] for q in Q.QUOTES).lower()
bad = [b for b in ('be the change', 'best time to plant a tree',
                   'insanity is doing', 'whether you think you can',
                   "i have not failed", 'everyone else is already taken',
                   'it always seems impossible', 'not final, failure')
       if b in texts]
ok(not bad, 'the famous misattributions are left out', bad)
try:
    old = was(J(WA, 'quotes.py'))
    first = old[old.index('QUOTES = ['):]
    ok("'id':" not in old and all(
        q['text'][:30].replace("'", "\\'") in first or q['text'][:30] in first
        for q in Q.QUOTES[:28]),
       'before this round: 28 quotes and no ids - those 28 keep their '
       'places as ids 1 to 28')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. NO REPEATS UNTIL ALL 240 HAVE BEEN SEEN')
# ==========================================================================
prefs = {}
day0 = dt.date(2027, 1, 1)
shown = []
for n in range(240):
    d = day0 + dt.timedelta(days=n)
    qid = DL.choose(prefs, 7, d)
    DL.record(prefs, d, qid)
    shown.append(qid)
ok(len(set(shown)) == 240,
   '240 days, 240 different quotes - not one repeated', len(set(shown)))
d241 = day0 + dt.timedelta(days=240)
ok(prefs['quotes_seen'] == [shown[-1]],
   'ALL SEEN: the counter starts again - holding only the last one, so '
   'tomorrow cannot be the same quote')
q241 = DL.choose(prefs, 7, d241)
ok(q241 != shown[-1], '  day 241 is not day 240\'s quote again')
p2 = {}
DL.record(p2, day0, DL.choose(p2, 7, day0))
first = DL.today_id(p2, day0)
ok(DL.today_id(p2, day0) == first and DL.today_id(p2, d241) is None,
   'THE DAY\'S QUOTE HOLDS all day; tomorrow is a new one')
p3 = {'quotes_seen': list(range(1, 200))}
offered = DL.offer(p3, 7, day0)
ok(len(offered) == 30 and all(i >= 200 for i in offered),
   'CLAUDE IS OFFERED only quotes not yet seen (30 at most)')
ok(len(DL.offer({'quotes_seen': list(range(1, 230))}, 7, day0)) == 11,
   '  or all that are left')
p4 = {'quote_day': {'date': day0.isoformat(), 'id': 42}}
ok(DL.offer(p4, 7, day0) == [42],
   '  and, once the day\'s quote is showing, only that one')
ok(DL.parse('{"quote": 42, "line": "One kind word."}', [42]) and
   DL.parse('{"quote": 41, "line": "One kind word."}', [42]) is None,
   'a quote Claude was not offered is refused')
p5 = {'daily_line': {'date': day0.isoformat(), 'quote': 6, 'line': 'x'}}
ok(DL.today_id(p5, day0) == 7,
   'A LINE MADE BEFORE THIS ROUND (place 6 in the old list) is id 7')
pr = DL.prompt({'name': 'A', 'weekday': 'Monday', 'today': [],
                'yesterday_done': 0, 'yesterday_due': 0, 'good_weeks': 0,
                'workouts_this_week': 0}, [5, 9])
ok('5. "' in pr and '9. "' in pr and '6. "' not in pr,
   'the prompt lists only the offered quotes, by id')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile
    connection.ensure_connection()
    WellnessProfile.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])


class _B(object):
    def __init__(self, t):
        self.text = t


class Fake(object):
    def __init__(self):
        self.messages = self
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        text = kw['messages'][0]['content']
        import re as _re
        n = int(_re.search(r'^(\d+)\. "', text, _re.M).group(1))
        return NS(content=[_B('{"quote": %d, "line": "Steady does it."}'
                              % n)])


from types import SimpleNamespace as NS                     # noqa: E402

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            u = User.objects.create_user('ql1a', 'ql1a@example.com', 'x',
                                         first_name='Ana')
            u.user_permissions.add(perm)
            pf = WellnessProfile.objects.create(user=u, onboarded=True)
            User.objects.exclude(pk=u.pk).update(is_active=False)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            today = timezone.localdate()
            h1 = c.get('/wellness/').content.decode()
            pf.refresh_from_db()
            qid = DL.today_id(pf.prefs, today)
            ok(qid and _esc(Q.BY_ID[qid]['text']) in h1 and
               pf.prefs.get('quotes_seen') == [qid],
               'TODAY: the quote shown is kept on the person\'s record as '
               'seen')
            h2 = c.get('/wellness/').content.decode()
            pf.refresh_from_db()
            ok(_esc(Q.BY_ID[qid]['text']) in h2 and
               pf.prefs.get('quotes_seen') == [qid],
               '  opened again: the same quote, counted once')
            seen = [i for i in Q.IDS if i != qid][:150] + [qid]
            pf.prefs = dict(pf.prefs, quotes_seen=seen, quote_day={})
            pf.prefs.pop('quote_day')
            pf.save()
            h3 = c.get('/wellness/').content.decode()
            pf.refresh_from_db()
            q3 = DL.today_id(pf.prefs, today)
            ok(q3 not in seen and len(pf.prefs['quotes_seen']) == 152,
               'A NEW DAY: one not seen before, added to the record')
            pf.prefs = dict(pf.prefs)
            pf.prefs.pop('quote_day')
            pf.prefs.pop('daily_line', None)
            pf.prefs.pop('daily_line_try', None)
            pf.save()
            fake = Fake()
            ok(DL.run(timezone.localtime(), client=fake) == 1,
               'CLAUDE\'S LINE is made')
            sent = fake.calls[0]['messages'][0]['content']
            import re as _re
            listed = [int(x) for x in _re.findall(r'^(\d+)\. "', sent,
                                                   _re.M)]
            pf.refresh_from_db()
            ok(listed and not set(listed) & set(pf.prefs['quotes_seen'][:-1])
               and len(listed) <= 30,
               '  Claude was offered only quotes not yet seen',
               listed[:5])
            line = pf.prefs['daily_line']
            ok(line.get('qid') == listed[0] and
               pf.prefs['quote_day']['id'] == listed[0] and
               pf.prefs['quotes_seen'][-1] == listed[0],
               '  and its pick is today\'s quote, counted as seen')
            h4 = c.get('/wellness/').content.decode()
            ok(_esc(Q.BY_ID[listed[0]]['text']) in h4 and 'Steady does it.' in h4,
               '  Today shows it, with the line')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. HELP AND REGISTERED')
# ==========================================================================
ok('Will I see the same quote again?' in read(J(WA, 'guide.py')) and
   'no repeats until you have seen all 240' in read(J(WA, 'help.py')),
   'HELP: no repeats until all 240 have been seen')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
