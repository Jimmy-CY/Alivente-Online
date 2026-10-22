# -*- coding: utf-8 -*-
"""test_ws_prefetch.py - round WN-1, 22 Oct 2026.

THE WORKSPACE LIST RAN ONE SELECT PER WORKSPACE, AND WM-1 SAID SO.

    # One query per row is pre-existing and still here:
    # a prefetch is its own round.          -- WM-1, 16 Oct 2026

This is that round, and this is the suite that measures it rather than
reading the code and believing it. Section 3 renders the page with one
workspace and then with four, under CaptureQueriesContext, and compares
the two counts. Before the round the second number is three larger than
the first. After it, they are equal.

A COUNT IS THE ONLY HONEST TEST OF AN N+1. A claim that the source now
says prefetch_related is a claim about a string. Django will happily
accept a prefetch that does not apply, a to_attr that nothing reads, or
a select_related inside it that the template then defeats by touching a
field it did not pull - and in every one of those cases the source
reads correctly and the queries go up. So the queries are counted.

to_attr, AND WHY IT IS NOT A STYLE CHOICE. The template reads
ws.member_list. A bare prefetch_related('members') fills
ws.members.all() and leaves member_list undefined - and an undefined
name in a Django template is SILENCE, not an error. Every member popup
on the page would have come up empty, on every row, and no suite that
read the view would have noticed. Section 3 renders the real template
and looks for the usernames in the HTML.

select_related('user') INSIDE THE PREFETCH. The list is ordered by
username and the popup prints usernames. Without it the page would be
two queries plus one per MEMBER - a worse N+1 than the one removed, and
one that only shows up when a workspace has several people in it.
Section 3 gives one workspace four members for exactly that reason.

THE COUNT ANNOTATION IS LEFT ALONE. annotate(Count('members')) is a
GROUP BY on the first query, costs nothing, and is what the column
sorts on.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The loop is gone, the prefetch names to_attr, pulls
      the user and keeps the order, and the count annotation survived.

  2   THE CONTROL. Re-asked of .bak_wsprefetch, where the loop was.

  3   DRIVEN. Queries counted at one workspace and at four; the page
      rendered and the usernames found in it; a workspace with four
      members, so a missing select_related would show.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

SUFFIX = '.bak_wsprefetch'
ME = 'test_ws_prefetch.py'
PATCHER = 'apply_ws_prefetch.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'WN-1, 22 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'users.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'workspace_management.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW,)

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


# SLICED TO THE FUNCTION. users.py is 600 lines and holds a dozen
# querysets; a claim about 'the prefetch' asked of the whole module
# would be answered by any of them. .find(), not .index().
def listing(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def workspace_management')
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\ndef \w+', body[1:])
    return body[:nxt.start() + 1] if nxt else body


# AND THE PREFETCH IS ITS OWN SLICE. The loop this round removed
# ALREADY had select_related('user') and order_by('user__username') in
# it - the N+1 was the loop, not what was inside it - so a claim about
# those two asked of the function held before the round and the control
# section said so. They are asked of the Prefetch.
def prefetch(fn):
    a = fn.find('prefetch_related(Prefetch(')
    b = fn.find(".order_by('name')")
    return fn[a:b] if 0 <= a < b else ''


def claims(d):
    fn = listing(d[VIEW])
    pf = prefetch(fn)
    return {
        'the workspace list does not loop over its rows':
            bool(fn) and 'for ws in workspaces' not in fn,
        '  it prefetches the members instead':
            'prefetch_related(Prefetch(' in fn,
        '  into member_list, which is where the template looks':
            "to_attr='member_list'" in pf,
        '  pulling the user in the same query':
            bool(pf) and "select_related('user')" in pf,
        '  and keeping the order the popup reads':
            bool(pf) and "order_by('user__username')" in pf,
        'and Prefetch is imported':
            'from django.db.models import Count, Prefetch' in d[VIEW],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

FN = listing(NOW[VIEW])
ok("annotate(member_count=Count('members'))" in FN,
   'GUARD: the count annotation survived - it is a GROUP BY on the '
   'first query, costs nothing, and is what the column sorts on')
ok("select_related('owner')" in FN,
   'GUARD: and the owner is still pulled with the row')
ok('member_list' in read(TPL),
   'the template really does read member_list - which is why to_attr '
   'is not a style choice', [l.strip() for l in read(TPL).split('\n')
                             if 'member_list' in l][:2])


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

OLD = listing(BEFORE[VIEW])
ok('for ws in workspaces' in OLD,
   'CONTROL: there really was a loop over the rows')
ok('a prefetch is its own round' in BEFORE[VIEW],
   'CONTROL: and WM-1 named this round on 16 October rather than '
   'leaving it to be discovered')
ok("select_related('user')" in OLD,
   'CONTROL: the old loop already pulled the user - the N+1 was the '
   'loop, not what was inside it')


# ==========================================================================
head('3. DRIVEN - THE QUERIES, COUNTED')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    dj.DEBUG = False
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth.models import User
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    from pages.models import UserProfile, Workspace

    boss = User.objects.create_superuser(
        username='wn1', password='x', email='wn1@example.test')
    cl = Client()
    cl.force_login(boss)
    URL = '/workspace-management/'

    def member(ws, name):
        u = User.objects.create_user(username=name, password='x',
                                     email='%s@example.test' % name)
        p, _ = UserProfile.objects.get_or_create(user=u)
        p.workspace = ws
        p.save()
        return u

    def count_and_page():
        with CaptureQueriesContext(connection) as ctx:
            r = cl.get(URL)
        return len(ctx.captured_queries), r

    # ---- ONE WORKSPACE, FOUR MEMBERS. Four, so that a prefetch which
    #      forgot select_related('user') would show up here rather than
    #      hiding behind a single row.
    one = Workspace.objects.create(name='Alpha', owner=boss)
    for n in ('anna', 'boris', 'chris', 'dimitra'):
        member(one, n)
    n1, r1 = count_and_page()
    ok(r1.status_code == 200, 'the workspace page renders', r1.status_code)
    html1 = r1.content.decode('utf-8', 'replace')
    ok('anna' in html1 and 'dimitra' in html1,
       '  AND THE MEMBER NAMES ARE IN IT - to_attr puts the list where '
       'the template looks, and an undefined name there would have '
       'been silence')
    ok('Alpha' in html1, '  along with the workspace')

    # ---- FOUR WORKSPACES. The whole question in one subtraction.
    for name in ('Beta', 'Gamma', 'Delta'):
        ws = Workspace.objects.create(name=name, owner=boss)
        member(ws, name.lower() + '_one')
        member(ws, name.lower() + '_two')
    n4, r4 = count_and_page()
    html4 = r4.content.decode('utf-8', 'replace')
    ok(r4.status_code == 200, 'and with four workspaces', r4.status_code)
    ok(n4 == n1,
       'FOUR WORKSPACES COST THE SAME QUERIES AS ONE - %d and %d. '
       'Before this round the second number was three larger.'
       % (n1, n4), (n1, n4))
    ok('beta_one' in html4 and 'delta_two' in html4,
       '  and every workspace members are still on the page')

    # ---- AND THE COUNT COLUMN STILL COUNTS.
    ok(re.search(r'\b4\b', html1),
       'the member count is still rendered - the annotation was not '
       'replaced by len(member_list)')
    ws = Workspace.objects.get(name='Alpha')
    page = cl.get(URL)
    got = [w for w in page.context['workspaces'] if w.name == 'Alpha']
    if got:
        ok(got[0].member_count == 4,
           '  and it says 4 for the workspace with four people in it',
           got[0].member_count)
        ok(len(got[0].member_list) == 4,
           '  and member_list has the same four, in username order',
           [m.user.username for m in got[0].member_list])
        ok([m.user.username for m in got[0].member_list]
           == sorted(m.user.username for m in got[0].member_list),
           '  sorted by username, which is what the popup promises',
           [m.user.username for m in got[0].member_list])
    else:
        skip('the count column', 'the context did not carry workspaces')

    # ---- TEN WORKSPACES, because two numbers can agree by accident
    #      and three cannot.
    print('')
    for i in range(6):
        ws = Workspace.objects.create(name='Extra %d' % i, owner=boss)
        member(ws, 'extra%d' % i)
    n10, _ = count_and_page()
    ok(n10 == n1,
       'TEN WORKSPACES COST THE SAME AGAIN - %d, %d, %d for 1, 4 and '
       '10 rows' % (n1, n4, n10), (n1, n4, n10))


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ok(not os.path.isfile(TPL + SUFFIX),
   'NO TEMPLATE CHANGE - member_list kept its name, so the popup and '
   'the count column are untouched')
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'models.py') + SUFFIX),
   'and no model change - this round is one queryset')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok("to_attr='member_list'" in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_ws_prefetch as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that this was the only N+1 in the application. It is')
print('  the one WM-1 wrote down. Nobody has swept for the rest,')
print('  and a sweep is its own round with its own instrument.')
print('')
print('  Not that it is faster on Live. It is fewer round trips,')
print('  measured. What that costs in milliseconds against a')
print('  remote MySQL is a different measurement on a different')
print('  machine.')
print('')
print('  Not that ten workspaces is a lot. It is three data')
print('  points, which is the smallest number that can tell a')
print('  flat line from a coincidence.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
