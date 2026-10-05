# -*- coding: utf-8 -*-
"""test_passport_guard.py - Section PH round PH-1b, 5 Oct 2026.

PH-1 shipped backfill_passport_holder. Demetri ran it and got two
hundred lines of traceback ending in

    OperationalError: (1054, "Unknown column 'passports.holder_id'")

because his laptop answers from a local database four migrations behind.
Neither the round nor the migration was at fault. The fault was that the
command walked into a query against a column it had no reason to assume
existed, and said nothing a person could act on.

PH-1b makes it look first.

AND THIS SUITE RUNS IT. PH-1's own suite ended "NOT PROVED HERE: that
the backfill matches the right people", because there is no database in
this sandbox. There does not have to be a MySQL one. Section 3 builds
sqlite databases from Django's own model metadata - so the columns
cannot drift from the models - and runs the real command against them
through manage.py, in a subprocess, with a settings module that reads
NOTHING from the environment for its connection and therefore cannot
reach a real database by accident.

Four cases, end to end: a database with no holder column; a dry run; a
write; and a second write that must find nothing left to do.
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
import shutil
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_passguard'
ME = 'test_passport_guard.py'
PATCHER = 'apply_passport_guard.py'
PS1 = 'Push-PendingChanges.ps1'
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'backfill_passport_holder.py')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:10]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the guard is there, and it is before the first query')

src = now(CMD)
ok('PH-1b, 5 Oct 2026' in src, 'the command carries the guard')
ok('get_table_description' in src,
   '  and it asks the table what columns it has')
ok('except OperationalError' not in src and 'except Exception' not in src,
   '  rather than catching the error - 1054 is also what a typo raises')
g = src.index('PH-1b, 5 Oct 2026')
for first in ('HouseholdMember.objects', 'Passport.objects'):
    ok(src.index(first) > g,
       '  %s is queried after it, not before' % first)
ok('raise CommandError' in src,
   '  and a missing column exits non-zero rather than reporting zero rows')

# IT NAMES THE DATABASE WITHOUT NAMING A SECRET.
ok("connection.alias" in src and "'ENGINE'" in src,
   'it names the alias and the engine it asked')
for leak in ('PASSWORD', 'HOST', 'USER', 'NAME'):
    ok("settings_dict['%s']" % leak not in src,
       "  and never reads settings_dict[%r]" % leak)

# ==========================================================================
head('2. a probe that cannot reach a real database')

work = tempfile.mkdtemp(prefix='ph1b_')
probe = os.path.join(work, 'probe_settings.py')
with open(probe, 'w', encoding='utf-8') as fh:
    fh.write(
        '"""The real settings with the database swapped for a sqlite file.\n'
        'Nothing from the environment reaches the connection, so this\n'
        'cannot touch a real database by accident."""\n'
        'import os\n'
        'from mysite.settings import *          # noqa: F401,F403\n'
        '\n'
        'DATABASES = {\n'
        "    'default': {\n"
        "        'ENGINE': 'django.db.backends.sqlite3',\n"
        "        'NAME': os.environ['PH1B_DB'],\n"
        '    }\n'
        '}\n')
ok(os.path.exists(probe), 'the probe settings module is written')
ok("'django.db.backends.sqlite3'" in read(probe)
   and 'DATABASES' in read(probe),
   '  and it replaces DATABASES outright - no host, no user, no password')


def run(db, *args):
    env = dict(os.environ)
    env['PH1B_DB'] = db
    env['SECRET_KEY'] = env.get('SECRET_KEY', 'test-only-not-a-secret')
    env['DJANGO_SETTINGS_MODULE'] = 'probe_settings'
    env['PYTHONPATH'] = work + os.pathsep + ROOT
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'manage.py'),
         'backfill_passport_holder', '--skip-checks'] + list(args),
        capture_output=True, text=True, cwd=ROOT, env=env, timeout=600)
    return r.returncode, r.stdout + r.stderr


def build(db, drop=()):
    """Tables generated from the MODELS, so they cannot drift from them."""
    import sqlite3
    import datetime
    env = dict(os.environ)
    env['PH1B_DB'] = db
    env['SECRET_KEY'] = env.get('SECRET_KEY', 'test-only-not-a-secret')
    env['DJANGO_SETTINGS_MODULE'] = 'probe_settings'
    env['PYTHONPATH'] = work + os.pathsep + ROOT
    prog = (
        'import os, sys, django, json\n'
        'django.setup()\n'
        'from pages.models import Passport, HouseholdMember\n'
        'def ddl(m, drop):\n'
        '    cols = []\n'
        '    for f in m._meta.fields:\n'
        '        if f.column in drop: continue\n'
        '        t = "INTEGER" if f.get_internal_type() in ("AutoField",'
        '"BigAutoField","ForeignKey","IntegerField","BooleanField") '
        'else "TEXT"\n'
        '        cols.append(chr(34)+f.column+chr(34)+" "+t+'
        '(" PRIMARY KEY" if f.primary_key else ""))\n'
        '    return "CREATE TABLE " + chr(34)+m._meta.db_table+chr(34) + '
        '" (" + ", ".join(cols) + ")"\n'
        'print(json.dumps([ddl(Passport, %r), ddl(HouseholdMember, ())]))\n'
        % (list(drop),))
    r = subprocess.run([sys.executable, '-c', prog], capture_output=True,
                       text=True, cwd=ROOT, env=env, timeout=600)
    stmts = None
    for line in r.stdout.splitlines():
        if line.startswith('['):
            import json
            stmts = json.loads(line)
    if stmts is None:
        raise RuntimeError(r.stdout[-400:] + r.stderr[-400:])
    if os.path.exists(db):
        os.remove(db)
    c = sqlite3.connect(db)
    for s in stmts:
        c.execute(s)
    nowts = datetime.datetime.now().isoformat()
    c.executemany(
        'INSERT INTO household_members (id,workspace_id,name,email,user_id,'
        'is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
        [(1, 1, 'Demetri Manias', '', None, 1, nowts, nowts),
         (2, 1, 'Angy Manias', '', None, 1, nowts, nowts),
         (3, 2, 'Erene Manias', '', None, 1, nowts, nowts)])
    for pid, ws, name in ((1, 1, 'Demetri Manias'),
                          (2, 1, 'angy   manias'),
                          (3, 1, 'A. Manias'),
                          (4, 2, 'Demetri Manias')):
        cols = ('id,workspace_id,holder_name,document_type,document_number,'
                'country_of_issue,status,created_at,updated_at')
        vals = [pid, ws, name, 'passport', 'X1', 'CY', 'active', nowts,
                nowts]
        if 'holder_id' not in drop:
            cols += ',holder_id'
            vals.append(None)
        c.execute('INSERT INTO passports (%s) VALUES (%s)'
                  % (cols, ','.join('?' * len(vals))), vals)
    c.commit()
    c.close()


def holders(db):
    import sqlite3
    c = sqlite3.connect(db)
    out = list(c.execute('select id, holder_id from passports order by id'))
    c.close()
    return out


try:
    # ======================================================================
    head('3. a database with no holder column - the one Demetri hit')

    nodb = os.path.join(work, 'noholder.sqlite3')
    build(nodb, drop=('holder_id',))
    rc, out = run(nodb)
    ok(rc != 0, 'the command exits non-zero', rc)
    ok('has no holder column' in out, '  and says the column is missing')
    ok('0097_passport_holder has not been applied' in out,
       '  and names the migration')
    ok('showmigrations pages' in out, '  and how to confirm it')
    ok('local development database' in out and 'IS production' in out,
       '  and tells the two cases apart')
    ok('Nothing was read and nothing was written' in out,
       '  and says it touched nothing')
    ok('Traceback' not in out,
       '  WITHOUT a traceback - which is the whole round', out[-400:])
    ok("alias 'default'" in out and 'sqlite3' in out,
       '  while naming the database it asked')

    # ======================================================================
    head('4. a dry run, against real rows')

    db = os.path.join(work, 'full.sqlite3')
    build(db)
    before = holders(db)
    rc, out = run(db)
    ok(rc == 0, 'a dry run succeeds', out[-400:])
    ok(re.search(r'exact\s+Demetri Manias\s+->\s+Demetri Manias', out),
       '  an exact match is found', out)
    ok(re.search(r'loose\s+angy\s+manias\s+->\s+Angy Manias', out),
       '  and a loose one - case folded, whitespace collapsed', out)
    ok('A. Manias' in out and 'NO MEMBER MATCHES' in out,
       '  a name no member carries is reported, not guessed')
    # WORKSPACE ISOLATION, which is the one a careless backfill gets wrong.
    ok(out.count('Demetri Manias') >= 3,
       '  and the SAME name in another workspace does NOT match - it is '
       'in the unmatched list too', out)
    ok('DRY RUN - nothing was written' in out, '  and it says it wrote nothing')
    ok(holders(db) == before,
       '  and the rows prove it', '%s -> %s' % (before, holders(db)))

    # ======================================================================
    head('5. the write, and the second write')

    rc, out = run(db, '--write')
    ok(rc == 0, '--write succeeds', out[-400:])
    ok('WRITTEN: 2 row(s)' in out, '  and writes exactly the two')
    after = dict(holders(db))
    ok(after[1] == 1, '  the exact match got its key')
    ok(after[2] == 2, '  the loose one too')
    ok(after[3] is None, '  the unmatched one was left alone')
    ok(after[4] is None,
       '  and so was the one whose only namesake is in another workspace')

    rc, out = run(db, '--write')
    ok(rc == 0, 'a second --write succeeds')
    ok('already 2' in out and 'WRITTEN: 0 row(s)' in out,
       '  and finds nothing left to do - it is idempotent', out[-300:])
    ok(dict(holders(db)) == after, '  and no row moved')
finally:
    shutil.rmtree(work, ignore_errors=True)

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(CMD + SUFFIX), 'the command has a %s backup' % SUFFIX)
ok('PH-1b' not in was(CMD), '  which predates the guard')

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  WHAT THIS DOES AND DOES NOT PROVE. The matching LOGIC is now')
print('  proved end to end against a real database - exact, loose, no')
print('  match, another workspace, the write, and the second write that')
print('  finds nothing. What it cannot prove is what the LIVE rows say,')
print('  which is the whole reason the command is dry by default and')
print('  the unmatched list is printed by name.')
