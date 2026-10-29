# -*- coding: utf-8 -*-
"""test_celebration_help.py - round CX-1, 29 Oct 2026.

RELEASE 40 - CELEBRATION EMAILS RETRY, AND HELP ON TASK LIST AND GANTT.
His plan of 29 October:

    - The celebrations email goes through _send_email_with_retry like every
      other email the daily job sends; each recipient is sent and retried
      on their own, and one failure no longer stops the rest.
    - Task List and Gantt Chart get a Help button (and a More-menu item on
      a phone) that opens the Projects guide on its Views tab.
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

SUFFIX = '.bak_celebhelp'
ME = 'test_celebration_help.py'
PATCHER = 'apply_celebration_help.py'
PS1 = 'Push-PendingChanges.ps1'
MARKS = ('CX-1, 29 Oct 2026',)

J = os.path.join
CMD = J(ROOT, 'pages', 'management', 'commands',
        'check_lease_renewal_and_invoices.py')
TL = J(ROOT, 'pages', 'templates', 'projects', 'project_task_list.html')
GANTT = J(ROOT, 'pages', 'templates', 'projects', 'project_gantt.html')
GATE = J(ROOT, PS1)
EDITED = [CMD, TL, GANTT]
UNDATED = []

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


def celebration_fn(src):
    code = T.python_code_only(src)
    m = re.search(r'\n    def send_celebration_notification\(.*?(?=\n    def )',
                  code, re.S)
    return m.group(0) if m else ''


def claims(cmd, tl, gantt):
    out = []
    fn = celebration_fn(cmd)
    out.append((bool(fn) and 'self._send_email_with_retry(' in fn
                and 'smtplib.SMTP' not in fn and '.sendmail(' not in fn,
                'the celebrations email is sent through _send_email_with_retry, '
                'not a connection of its own'))
    for t, name in ((tl, 'Task List'), (gantt, 'Gantt Chart')):
        code = T.code_only(t)
        out.append(('{% load help_modal_tags %}' in code
                    and '{% render_help_modal "projects" %}' in code
                    and code.count('data-target="#projectsHelpModal"') == 2
                    and "jQuery('#projects__prjReports-tab').tab('show')" in t,
                    '%s has Help (bar and phone menu) opening the Projects '
                    'guide on its Views tab' % name))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(read(CMD), read(TL), read(GANTT)):
    ok(cond, msg)
dated = [os.path.relpath(p, ROOT) for p in EDITED
         if not any(mk in read(p) for mk in MARKS)]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
for cond, msg in claims(was(CMD), was(TL), was(GANTT)):
    ok(not cond, 'CONTROL: before this round - %s' % msg.strip())

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    import django
    django.setup()
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User
    import pages.models as M
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


if have_db:
    import io
    from importlib import import_module
    Cmd = import_module(
        'pages.management.commands.check_lease_renewal_and_invoices').Command
    sent = []

    def fake(self, msg, from_addr, to_addrs, label='Email', **kw):
        sent.append((to_addrs[0], msg['Subject']))
        return to_addrs[0] != 'b@example.com'

    c = Cmd(stdout=io.StringIO())
    real = Cmd._send_email_with_retry
    Cmd._send_email_with_retry = fake
    try:
        one = {'contact_name': 'Ann', 'event_type': 'Birthday', 'age': 50,
               'relationship': 'Friend', 'notes': ''}
        res = c.send_celebration_notification(
            {'a@example.com': [one], 'b@example.com': [one],
             'c@example.com': [one]})
    finally:
        Cmd._send_email_with_retry = real
    ok([s[0] for s in sent] == ['a@example.com', 'b@example.com',
                                'c@example.com'],
       'each recipient is sent on their own, and a failure for one does not '
       'stop the next', sent)
    ok(res is False, '  and the job reports the one that failed')
    ok(all('Birthday' in (s[1] or '') or 'Celebration' in (s[1] or '')
           for s in sent), '  with the subject it always had', sent)

    try:
        with transaction.atomic():
            import datetime as dt
            p = M.props.objects.create(prop_name='CX1 Flat',
                                       prop_country='Cyprus',
                                       prop_available_for_rent='Yes')
            pj = M.Project.objects.create(project_name='CX1 Project', prop=p)
            u = User.objects.create_user('cx1', 'cx1@example.com', 'x',
                                         is_superuser=True, is_staff=True)
            cl = Client(SERVER_NAME='localhost')
            cl.force_login(u)
            for url, name in (('/projects/%d/task-list/' % pj.pk, 'Task List'),
                              ('/projects/%d/gantt/' % pj.pk, 'Gantt Chart')):
                r = cl.get(url)
                h = r.content.decode('utf-8')
                ok(r.status_code == 200 and 'id="projectsHelpModal"' in h
                   and 'projects__prjReports' in h,
                   '%s renders with the Projects guide and its Views tab'
                   % name, r.status_code)
            raise Rollback()
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'Celebration email to %s'" in gate,
   '  with a sentinel on the celebrations retry')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED + UNDATED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
