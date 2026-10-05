# -*- coding: utf-8 -*-
"""test_passport_alias.py - Section PH round PH-1c, 5 Oct 2026.

The backfill ran against production and matched nothing: 21 passports,
four holder names, zero hits. The household members were seeded with
FIRST NAMES (migration 0072 - Demetri, Angy, Erene, Alexandra) and the
passports carry full names. Three of the four are the same person
written two ways; the fourth, Angela Manias against Angy, is a different
name and no rule reaches it. PA-3 said so a day before it happened.

Demetri chose an explicit map over a first-word rule, and confirmed that
Angela and Angy are one person. Four lines, each recording a decision.

SECTION 3 RUNS IT AGAINST THE SHAPE PRODUCTION REALLY HAS - first-name
members, full-name passports - and section 4 against the two ways a map
can be wrong: pointing at a member who is not in that workspace, and two
names pointing at one member. The second is refused by the patcher
before anything is written, because that is how a backfill quietly gives
one person somebody else's documents.
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
import json
import os
import re
import shutil
import sqlite3
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

SUFFIX = '.bak_passalias'
ME = 'test_passport_alias.py'
PATCHER = 'apply_passport_alias.py'
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
head('1. the map, and what it is allowed to be')

src = now(CMD)
ok('ALIASES = {' in src, 'the command carries an explicit map')
ns = {}
exec(compile(src[src.index('ALIASES = {'):src.index('def fold(')],
             'aliases', 'exec'), ns)
AL = ns['ALIASES']
ok(len(AL) == 4, 'it holds %d entries' % len(AL), sorted(AL))
for k, v in sorted(AL.items()):
    print('      %-20s -> %s' % (k, v))

# EVERY KEY IS FOLDED, or it can never match.
bad = [k for k in AL if k != ' '.join(k.split()).casefold()]
ok(not bad, 'every key is folded, so spacing and case cannot defeat it', bad)

# AND NO TWO NAMES POINT AT ONE MEMBER. That is how a backfill quietly
# gives one person somebody else documents.
ok(len(set(AL.values())) == len(AL),
   'no two holder names map to one member',
   sorted(AL.items()))

ok('angela manias' in AL and AL['angela manias'] == 'Angy',
   "Angela Manias maps to Angy - the one PA-3 said no rule could reach")
ok('PA-3' in src and 'no safe automatic mapping' in src,
   '  and the file records why it is written down rather than inferred')

# A FIRST-WORD RULE WAS NOT WRITTEN, and the round says why.
ok('split()[0]' not in src and 'first word' not in src.lower()
   or 'first-word rule' in src,
   'no first-word rule was added - the map is the decision')

# ==========================================================================
head('2. named is a third kind of match, and it is written')

ok("how = 'named'" in src, 'a named match has a name of its own')
ok('named += 1' in src and "'  named   %d' % named" in src,
   '  and is counted and reported separately from exact and loose')
ok('exact + loose + named' in src,
   '  and is written, because a person decided it')
ok('stale.append' in src,
   'a map entry pointing at an absent member is collected')
# THE HEADING IS SPLIT ACROSS TWO STRING LITERALS in the command, to
# keep the line under 79 characters, so searching the source for the
# whole sentence finds nothing. Section 3 checks the OUTPUT, where it
# appears whole; here the first fragment is enough to say it is written.
ok('THE MAP POINTS AT A MEMBER WHO IS NOT ' in src,
   '  and reported under a heading of its own, not silently skipped')

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





def build_real(db):
    """The shape production really has: FIRST-NAME members, FULL-NAME
    passports, plus a name nobody carries and a row in another
    workspace."""
    import datetime
    env = dict(os.environ)
    env['PH1B_DB'] = db
    env['SECRET_KEY'] = env.get('SECRET_KEY', 'test-only-not-a-secret')
    env['DJANGO_SETTINGS_MODULE'] = 'probe_settings'
    env['PYTHONPATH'] = work + os.pathsep + ROOT
    prog = (
        'import django, json\n'
        'django.setup()\n'
        'from pages.models import Passport, HouseholdMember\n'
        'def ddl(m):\n'
        '    cols = []\n'
        '    for f in m._meta.fields:\n'
        '        t = "INTEGER" if f.get_internal_type() in ("AutoField",'
        '"BigAutoField","ForeignKey","IntegerField","BooleanField") '
        'else "TEXT"\n'
        '        cols.append(chr(34)+f.column+chr(34)+" "+t+'
        '(" PRIMARY KEY" if f.primary_key else ""))\n'
        '    return "CREATE TABLE "+chr(34)+m._meta.db_table+chr(34)+'
        '" ("+", ".join(cols)+")"\n'
        'print(json.dumps([ddl(Passport), ddl(HouseholdMember)]))\n')
    r = subprocess.run([sys.executable, '-c', prog], capture_output=True,
                       text=True, cwd=ROOT, env=env, timeout=600)
    stmts = None
    for line in r.stdout.splitlines():
        if line.startswith('['):
            stmts = json.loads(line)
    if stmts is None:
        raise RuntimeError(r.stdout[-400:] + r.stderr[-400:])
    if os.path.exists(db):
        os.remove(db)
    c = sqlite3.connect(db)
    for s in stmts:
        c.execute(s)
    n = datetime.datetime.now().isoformat()
    c.executemany(
        'INSERT INTO household_members (id,workspace_id,name,email,user_id,'
        'is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
        [(1, 1, 'Demetri', '', None, 1, n, n),
         (2, 1, 'Angy', '', None, 1, n, n),
         (3, 1, 'Erene', '', None, 1, n, n),
         (4, 1, 'Alexandra', '', None, 1, n, n)])
    for pid, ws, name in ((1, 1, 'Demetri Manias'), (2, 1, 'Angela Manias'),
                          (3, 1, 'Erene Manias'), (4, 1, 'Alexandra  MANIAS'),
                          (5, 1, 'Somebody Else'), (6, 2, 'Demetri Manias')):
        c.execute(
            'INSERT INTO passports (id,workspace_id,holder_name,'
            'document_type,document_number,country_of_issue,status,'
            'created_at,updated_at,holder_id) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (pid, ws, name, 'passport', 'X1', 'CY', 'active', n, n, None))
    c.commit()
    c.close()

work = tempfile.mkdtemp(prefix='ph1c_')
with open(os.path.join(work, 'probe_settings.py'), 'w',
          encoding='utf-8') as fh:
    fh.write('\n'.join([
        '"""The real settings with the database swapped for a sqlite',
        'file. Nothing from the environment reaches the connection, so',
        'this cannot touch a real database by accident."""',
        'import os',
        'from mysite.settings import *          # noqa: F401,F403',
        '',
        'DATABASES = {',
        "    'default': {",
        "        'ENGINE': 'django.db.backends.sqlite3',",
        "        'NAME': os.environ['PH1B_DB'],",
        '    }',
        '}',
        '']))

try:
    # ======================================================================
    head('3. the shape production really has')

    work2 = work
    db = os.path.join(work2, 'real.sqlite3')
    build_real(db)
    rc, out = run(db)
    ok(rc == 0, 'the command runs', out[-400:])
    for full, short in (('Demetri Manias', 'Demetri'),
                        ('Angela Manias', 'Angy'),
                        ('Erene Manias', 'Erene')):
        ok(re.search(r'named\s+%s\s+->\s+%s' % (re.escape(full), short),
                     out), '  %-18s -> %s' % (full, short), out)
    ok(re.search(r'named\s+Alexandra\s+MANIAS\s+->\s+Alexandra', out),
       '  and a key folds case and spacing: "Alexandra  MANIAS"', out)
    ok('named   4' in out, '  four named matches')
    ok('exact   0' in out and 'loose   0' in out,
       '  and none of them was exact or loose - no rule reached them')

    # THE REPORT SHOWS ITS WORKING NOW.
    ok(re.search(r'Somebody Else\s+workspace 1 has: '
                 r'Alexandra, Angy, Demetri, Erene', out),
       'an unmatched name prints the members available beside it', out)

    # A STALE ENTRY IS REPORTED.
    ok('THE MAP POINTS AT A MEMBER WHO IS NOT THERE' in out,
       'the workspace-2 row, whose member does not exist there, is named')
    ok("expects 'Demetri' in workspace 2" in out,
       '  and says what it expected and where', out)

    before = holders(db)
    ok('DRY RUN' in out and holders(db) == before,
       '  and a dry run still wrote nothing')

    # ======================================================================
    head('4. the write')

    rc, out = run(db, '--write')
    ok(rc == 0, '--write succeeds', out[-300:])
    ok('WRITTEN: 4 row(s)' in out, '  and writes the four named matches')
    after = dict(holders(db))
    ok(after[1] == 1 and after[2] == 2 and after[3] == 3 and after[4] == 4,
       '  each row got the member its map entry names', after)
    ok(after[5] is None, '  the unmatched row was left alone')
    ok(after[6] is None,
       '  and so was the one whose map entry points outside its workspace')

    rc, out = run(db, '--write')
    ok('already 4' in out and 'WRITTEN: 0 row(s)' in out,
       'a second --write finds nothing left to do', out[-300:])
finally:
    shutil.rmtree(work, ignore_errors=True)

# ==========================================================================
head('5. the control - a map that gives one member two names')

bad_src = src.replace("'erene manias': 'Erene',",
                      "'erene manias': 'Demetri',", 1)
ok(bad_src != src, 'the control could be planted')
ns2 = {}
exec(compile(bad_src[bad_src.index('ALIASES = {'):bad_src.index('def fold(')],
             'aliases', 'exec'), ns2)
ok(len(set(ns2['ALIASES'].values())) != len(ns2['ALIASES']),
   '  and two names pointing at one member is seen',
   sorted(ns2['ALIASES'].items()))
ok(len(set(AL.values())) == len(AL),
   '  while the real map is not',)
# AND THE PATCHER REFUSES IT, which is where it matters.
ok('two holder names map to one member' in read(
    os.path.join(ROOT, PATCHER)),
   '  and the patcher refuses that shape before writing anything')

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(CMD + SUFFIX), 'the command has a %s backup' % SUFFIX)
ok('ALIASES' not in was(CMD), '  which predates the map')
ok('PH-1b' in was(CMD),
   '  and carries PH-1b, which this round builds on')

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that Angela Manias IS Angy. No test can know')
print('  that. Demetri said so on 5 Oct, and the file records that it is')
print('  his statement rather than a match that happened to land. If it')
print('  is ever wrong, it is wrong in one line that names itself.')
