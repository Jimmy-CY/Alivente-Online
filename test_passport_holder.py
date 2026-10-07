# -*- coding: utf-8 -*-
"""test_passport_holder.py - Section PH round PH-1, 5 Oct 2026.

PA-3 logged it on 4 Oct and did not do it: Passport.holder_name is a
CharField, nothing connects it to HouseholdMember, and the register and
the household can drift apart. "That is a migration plus a backfill with
no safe automatic mapping for Angy. Its own round."

PH-1 adds a NULLABLE foreign key beside the string and a command that
reports. It changes no view, no template and no filter.

SECTION 3 IS THE ONE THAT MATTERS, because this is the first round all
week to ship a schema change and deploys run migrations automatically.
It asks Django's own autodetector whether the hand-written migration
matches the model - not whether it looks right, whether Django thinks
anything is still missing - and requires the migration to hold exactly
one AddField and no data migration at all.

SECTION 4 IS THE SAFETY OF THE COMMAND: the only write in the file is
under `if write:`, and the ambiguous branch cannot reach it.
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
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_passholder'
ME = 'test_passport_holder.py'
PATCHER = 'apply_passport_holder.py'
PS1 = 'Push-PendingChanges.ps1'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
MIG = os.path.join(ROOT, 'pages', 'migrations', '0097_passport_holder.py')
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'backfill_passport_holder.py')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
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
head('1. the field, beside the string and not instead of it')

m_now, m_was = now(MODELS), was(MODELS)
ok('holder_name = models.CharField(max_length=200)' in m_now,
   'holder_name is still there, unchanged')
ok(m_was.count('holder_name = models.CharField') ==
   m_now.count('holder_name = models.CharField'),
   '  and there are as many of them as before')
ok('holder = models.ForeignKey(' in m_now, 'a holder foreign key is added')
ok('holder' not in m_was or 'holder = models.ForeignKey' not in m_was,
   '  and was not there before')

# THE SHAPE, READ OFF THE SOURCE rather than off a running Django, so
# this section says something even where the database is unreachable.
i = m_now.index('holder = models.ForeignKey(')
block = m_now[i:m_now.index(')', m_now.index('help_text', i))]
ok("'pages.HouseholdMember'" in block, '  it points at HouseholdMember')
ok('null=True' in block and 'blank=True' in block,
   '  nullable and blank, so every existing row is valid as it stands')
ok('on_delete=models.PROTECT' in block,
   '  PROTECT - a register whose subject can be deleted is not a register',
   block[:200])
ok("related_name='passports'" in block, '  and reverses as .passports')

# ==========================================================================
head('2. and nothing reads it yet')

readers = []
for p in alv_tree.templates():
    s = alv_tree.code_only(read(p))
    if re.search(r'\.holder\b(?!_name)', s):
        readers.append(alv_tree.rel(p).replace(os.sep, '/'))
ok(not readers,
   'no template reads .holder - PA-1 filter still works on the string',
   readers)

pyreaders = []
for base, _d, files in os.walk(os.path.join(ROOT, 'pages')):
    if 'migrations' in base or '__pycache__' in base:
        continue
    for f in files:
        if not f.endswith('.py') or f == 'models.py':
            continue
        p = os.path.join(base, f)
        # A GATE READS CODE, NOT THE RECORD OF CODE. The first build
        # read the raw file and flagged pages/views/passports.py, where
        # the only match is a COMMENT explaining that a bookmarked
        # ?holder=... still arrives with the old parameter.
        #
        # ast, NOT A REGEX. CO-1 wrote python_code_only and deliberately
        # did not merge it into alv_tree, and its own note says why a
        # regex cannot do this: stripping "#" from Python eats the "#"
        # in a string literal, which is where half this repo's colour
        # hexes live. Parsing and unparsing drops every comment and
        # keeps every string, exactly.
        s = ast.unparse(ast.parse(read(p)))
        if re.search(r'\bholder\s*=\s*(?!models\.)', s) or \
           re.search(r'\.holder\b(?!_name)', s):
            if 'backfill_passport_holder' not in f:
                pyreaders.append(os.path.relpath(p, ROOT))
ok(not pyreaders,
   '  and no view or form does either, except the backfill command',
   pyreaders)

# ==========================================================================
head('3. the migration - Django is asked, not trusted to look right')

mig = read(MIG)
tree = ast.parse(mig)
ops = re.findall(r'migrations\.(\w+)\(', mig)
ok(ops == ['AddField'],
   'the migration holds exactly one operation, and it is AddField', ops)
ok('RunPython' not in mig and 'RunSQL' not in mig,
   '  no data migration - a migration is the worst place to guess who '
   'somebody is')
ok("('pages', '0096_notification_type_password_reset')" in mig,
   '  and it depends on 0096, which is the one on disk')
ok(os.path.exists(os.path.join(ROOT, 'pages', 'migrations',
                               '0096_notification_type_password_reset.py')),
   '  which really is on disk')

# THE AUTODETECTOR. Everything above is a reading of the text; this is
# Django saying whether the model and the migrations agree.
try:
    import django
    # THE KEY BEFORE THE SETTINGS MODULE, and SE-1's suite caught the
    # first build writing it the other way round. mysite.settings reads
    # SECRET_KEY from the environment the moment the module is imported;
    # naming the module first and supplying the key second is a race
    # that happens to work only because django.setup() comes later.
    # setdefault, so a real key always wins.
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()
    from django.apps import apps
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ProjectState

    loader = MigrationLoader(None, ignore_no_migrations=True)
    auto = MigrationAutodetector(loader.project_state(),
                                 ProjectState.from_apps(apps))
    changes = auto.changes(graph=loader.graph, trim_to_apps={'pages'})
    pending = [str(o) for v in changes.values() for mm in v
               for o in mm.operations]
    ok(not pending,
       "Django's autodetector finds nothing left to migrate", pending)

    names = sorted(n for a, n in loader.disk_migrations if a == 'pages')
    # ITS OWN MIGRATION, NOT THE LAST ONE. [CM-1, 6 Oct 2026]
    # This read names[-1] == '0097_passport_holder' - true the day PH-1
    # shipped and false the moment any later round added a migration,
    # which CM-1 did. A round can only speak for its own work: that the
    # migration is on disk, and that the chain up to it is unbroken.
    ok('0097_passport_holder' in names,
       '  and 0097_passport_holder is on disk', names[-3:])
    nums = sorted(int(n.split('_')[0]) for n in names)
    mine = nums.index(97)
    ok(nums[:mine + 1] == list(range(nums[0], 97 + 1)),
       '  with no gap in the chain before it',
       nums[max(0, mine - 3):mine + 1])

    from pages.models import Passport
    f = Passport._meta.get_field('holder')
    ok(f.null and f.blank, '  the live field is nullable and blank')
    ok(f.remote_field.on_delete.__name__ == 'PROTECT',
       '  on_delete resolves to PROTECT',
       f.remote_field.on_delete.__name__)
    ok(f.related_model.__name__ == 'HouseholdMember',
       '  and it really points at HouseholdMember',
       f.related_model.__name__)
except Exception as e:
    ok(False, 'Django could be booted to check the migration', repr(e)[:300])

# ==========================================================================
head('4. the command writes only when told')

cmd = read(CMD)
ctree = ast.parse(cmd)

saves = [n for n in ast.walk(ctree)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == 'save']
ok(len(saves) == 1, 'there is exactly one save() in the file', len(saves))


def under_write(node, where):
    """Is this node inside an `if write:` block?"""
    for n in ast.walk(where):
        if isinstance(n, ast.If) and isinstance(n.test, ast.Name) \
                and n.test.id == 'write':
            for b in n.body:
                for x in ast.walk(b):
                    if x is node:
                        return True
    return False


ok(saves and under_write(saves[0], ctree),
   '  and it is inside `if write:` - nothing is written without the flag')
ok("'--write', action='store_true'" in cmd,
   '  --write is a flag, so a bare run cannot be a write by accident')
ok('DRY RUN - nothing was written' in cmd,
   '  and a dry run says so in as many words')

# AMBIGUITY IS NEVER WRITTEN.
ok('len(hits) > 1' in cmd and 'ambiguous.append' in cmd,
   'a holder_name matching more than one member is collected, not written')
amb = cmd[cmd.index('elif len(hits) > 1:'):cmd.index('else:',
                                                     cmd.index('elif len'))]
ok('p.save' not in amb and 'p.holder =' not in amb,
   '  and that branch contains no write at all', amb.strip()[:160])

ok('def fold(' in cmd, 'it folds case and whitespace for the loose match')
mod = {}
exec(compile(cmd[cmd.index('def fold('):cmd.index('class Command')],
             'fold', 'exec'), mod)
fold = mod['fold']
ok(fold('Angy  Manias') == fold('angy manias'),
   '  so "Angy  Manias" and "angy manias" are the same person')
ok(fold('Angy') != fold('Angela'),
   '  and "Angy" and "Angela" are not', (fold('Angy'), fold('Angela')))
ok(fold(None) == '', '  and a missing name folds to nothing, not a crash')

# ==========================================================================
head('5. the control')

planted = cmd.replace('if write:\n                    p.holder = hits[0]',
                      'if True:\n                    p.holder = hits[0]', 1)
ok(planted != cmd, 'the control could be planted')
pt = ast.parse(planted)
ps = [n for n in ast.walk(pt)
      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
      and n.func.attr == 'save']
ok(ps and not under_write(ps[0], pt),
   '  and a save outside `if write:` is seen as one',
   'the check cannot tell the two apart, so section 4 proves nothing')

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(MODELS + SUFFIX),
   'models.py has a %s backup' % SUFFIX)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the backfill matches the right people.')
print('  There is no database in this sandbox, and there could not be a')
print('  useful one - the question is what the LIVE rows say. The')
print('  command is dry by default for exactly that reason: run it,')
print('  read what it could not match, and only then --write. PA-3')
print('  recorded that there is no safe automatic mapping for Angy,')
print('  and this round does not invent one.')
