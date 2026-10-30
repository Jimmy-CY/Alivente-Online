# -*- coding: utf-8 -*-
"""test_wellness_six.py - round WL-4c, 30 Oct 2026.

RELEASE 49 - WELLNESS W-4c: A LINE FROM CLAUDE UNDER THE DAILY QUOTE.
Decision 4 of 30 Oct:

    - The quotes stay a curated library of real quotes. Claude PICKS one
      by its number and writes ONE short labelled line beneath it; it
      never writes a quote, and an answer outside the library is refused.
    - Claude is told the first name, today's habit names and how the week
      has gone - never the journal, the weight or the cycle log.
    - The line is made ahead, by the reminder job; Today never waits on
      Claude, and a day's quote holds all day. It can be turned off.
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

import datetime as dt
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_wellness6'
ME = 'test_wellness_six.py'
PATCHER = 'apply_wellness_six.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
CMD = J(APP, 'management', 'commands', 'wellness_reminders.py')
EDITED = [J(APP, 'views.py'), J(APP, 'guide.py'),
          J(APP, 'assets', 'wellness.css'), J(WT, 'base.html'),
          J(WT, 'today.html'), J(WT, 'settings.html'), CMD]

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

import alv_tree as T                                        # noqa: E402
import ast                                                  # noqa: E402


def py_words(src):
    """Every name, attribute, import and string a Python file USES -
    docstrings and comments left out, so a file may explain what it never
    touches."""
    tree = ast.parse(src)
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and \
                n.body and isinstance(n.body[0], ast.Expr) and \
                isinstance(getattr(n.body[0], 'value', None), ast.Constant):
            docs.add(id(n.body[0].value))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
        elif isinstance(n, ast.alias):
            out.append(n.name)
        elif isinstance(n, ast.ImportFrom):
            out.append(n.module or '')
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and \
                id(n) not in docs:
            out.append(n.value)
    return ' '.join(out).lower()

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
dl = read(J(APP, 'daily_line.py'))
ok(os.path.isfile(J(APP, 'daily_line.py')), 'wellness/daily_line.py is there')
words = py_words(dl)
ok('journalentry' not in words and 'bodymetric' not in words and
   'cycle' not in words, 'CLAUDE IS NEVER TOLD the journal, the body '
   'numbers or the cycle log')
ok("getattr(settings, 'ANTHROPIC_API_KEY', None)" in dl and 'sk-' not in dl,
   "the house key from settings - none written here")
ok("os.environ.get('WELLNESS_LINE_MODEL', 'claude-haiku-4-5')" in dl,
   "the house's small model, changeable without a release")
ok('MAX_TRIES = 3' in dl, 'at most three tries a day')
cmd = read(CMD)
blk = cmd[cmd.index('daily_line as DL') - 300:cmd.index('daily_line as DL') + 400]
ok('try:' in blk and 'except Exception' in blk,
   'the reminder job makes the lines, guarded - a failure never stops the '
   'reminders')
ok(cmd.index('DL.run(') < cmd.index('P.configured()'),
   '  and before the push-key check, so lines come without reminders too')
views = read(J(APP, 'views.py'))
today_fn = views[views.index('def today('):views.index('def _cycle_card')]
ok('DL.for_today(' in today_fn and 'DL.ask(' not in today_fn and
   'DL.make(' not in today_fn, 'TODAY NEVER WAITS ON CLAUDE: it only reads '
   'the line already made')
t = read(J(WT, 'today.html'))
ok('{% if claude_line %}' in t and 'A line from Claude' in t,
   'Today labels the line "A line from Claude", only when there is one')
s = read(J(WT, 'settings.html'))
ok('name="claude_line"' in s and 'never your journal, your weight or your '
   'cycle log' in s, 'settings can turn it off, and says exactly what '
   'Claude sees')
base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
ok(_v == ['wl6-1', 'wl6-1'] and "SW_VERSION = 'wl6-1'" in views,
   'the asset version moved together (wl6-1)', _v)
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('claude_line' not in was(J(WT, 'today.html')),
   'CONTROL: before this round there was no line under the quote')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import daily_line as DL                       # noqa: E402
from wellness import quotes as Q                            # noqa: E402
ok(DL.parse('{"quote": 3, "line": "A gentle start is still a start."}') ==
   {'quote': 3, 'line': 'A gentle start is still a start.'},
   "a fair answer: a library number and one short line")
ok(DL.parse('Sure! {"quote": 3, "line": "Steady   does it."} Hope that '
            'helps') == {'quote': 3, 'line': 'Steady does it.'},
   '  found inside chatter, spaces tidied')
ok(DL.parse('{"quote": %d, "line": "x"}' % len(Q.QUOTES)) is None and
   DL.parse('{"quote": -1, "line": "x"}') is None,
   'NEVER A QUOTE OUTSIDE THE LIBRARY')
ok(DL.parse('{"quote": 1, "line": "%s"}' % ('word ' * 40).strip()) is None,
   '  never a long speech')
ok(DL.parse('{"quote": 1, "line": "read www.example.com"}') is None and
   DL.parse('{"quote": 1, "line": "<b>hi</b>"}') is None,
   '  never a link or markup')
ok(DL.parse('{"quote": 1, "line": "%s"}' % Q.QUOTES[1]['text']) is None,
   '  and never the quote passed off as the line')
ok(DL.parse('no json here') is None and DL.parse('') is None,
   'anything else is no line at all')
f = {'name': 'Demetri', 'weekday': 'Monday', 'today': ['Walk', 'Read'],
     'yesterday_done': 3, 'yesterday_due': 4, 'good_weeks': 2,
     'workouts_this_week': 1}
pr = DL.prompt(f)
ok('%d. "%s"' % (0, Q.QUOTES[0]['text']) in pr and
   "Today's habits: Walk, Read" in pr and '3 of 4' in pr,
   'the prompt: the numbered library and the few plain facts')
ok(set(f) == {'name', 'weekday', 'today', 'yesterday_done', 'yesterday_due',
              'good_weeks', 'workouts_this_week'},
   '  and those facts are all there is')
ok('no medical or diet advice' in DL.SYSTEM and 'no guilt' in DL.SYSTEM,
   'Claude is asked for kind words: no guilt, no medical or diet advice')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import Habit, WellnessProfile
    connection.ensure_connection()
    WellnessProfile.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


class _Block(object):
    def __init__(self, t):
        self.text = t


class _Msg(object):
    def __init__(self, t):
        self.content = [_Block(t)]


class FakeClaude(object):
    """Stands in for the Anthropic client: records what it was asked."""
    def __init__(self, reply):
        self.reply = reply
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if isinstance(self.reply, Exception):
            raise self.reply
        return _Msg(self.reply)


if have_db:
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('w6_a', 'w6a@example.com', 'x',
                                         first_name='Alex')
            b = User.objects.create_user('w6_b', 'w6b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            today = timezone.localdate()
            Habit.objects.create(user=a, name='Walk',
                                 started_on=today - dt.timedelta(days=9))
            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               Q.for_day(a.pk, today)['text'] in t,
               'no line yet: the date\'s own quote and no line - Today '
               'did not wait')
            pa = WellnessProfile.objects.get(user=a)
            ok(pa.prefs.get('seen') == today.isoformat(),
               '  and Today noted it was opened today')
            fake = FakeClaude('{"quote": 7, "line": "A short walk counts, '
                              'Alex."}')
            now = timezone.localtime()
            ok(DL.run(now, client=fake) == 1 and len(fake.calls) == 1,
               'the job makes one line, for the person who uses Wellness '
               '(not the one who has not opened it)')
            sent = fake.calls[0]['messages'][0]['content']
            ok("First name: Alex" in sent and "Today's habits: Walk" in sent
               and 'kg' not in sent.lower() and 'journal' not in
               sent.lower(), '  Claude was told her name and habits - '
               'nothing private')
            t = ca.get('/wellness/').content.decode()
            ok(Q.QUOTES[7]['text'] in t and 'A short walk counts, Alex.'
               in t and 'A line from Claude' in t,
               "Today: Claude's pick from the library, and its line, "
               'labelled')
            ok(DL.run(now, client=fake) == 0 and len(fake.calls) == 1,
               '  made once a day - no second call')
            pa.refresh_from_db()
            prefs = dict(pa.prefs)
            prefs.pop('daily_line')
            prefs.pop('daily_line_try', None)
            pa.prefs = prefs
            pa.save()
            bad = FakeClaude(RuntimeError('network down'))
            for _ in range(5):
                DL.run(now, client=bad)
            ok(len(bad.calls) == 3,
               'a failing Claude is tried three times a day, then left be',
               len(bad.calls))
            t = ca.get('/wellness/').content.decode()
            ok('data-claude-line' not in t and
               Q.for_day(a.pk, today)['text'] in t,
               '  and Today simply shows the date\'s quote')
            ca.post('/wellness/settings/', {})
            pa.refresh_from_db()
            ok(pa.prefs.get('line_off') is True, 'turned off in settings')
            pa.prefs = dict(pa.prefs, daily_line_try={})
            pa.save()
            again = FakeClaude('{"quote": 2, "line": "x y z."}')
            ok(DL.run(now, client=again) == 0 and not again.calls,
               '  and then Claude is never asked')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def parse('" in gate, '  with a sentinel on the answer check')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
