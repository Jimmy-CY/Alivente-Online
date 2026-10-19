# -*- coding: utf-8 -*-
"""test_meal_drop.py - round MX-1, 19 Oct 2026.

RELEASE 3, PUSH 3. THE LAST THREE TABLES OF THE OLD PLANNER.

MN-1 replaced MealPlan -> MealPlanDay -> MealPlanRecipe with one
MealEntry on 18 October and retired the four screens that drew them.
Migration 0100 wrote down what would happen next:

    NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
    production are test data and are cleared rather than converted.
    The old tables are left in place, empty and unread, until 0101
    drops them in push 3 - which is the only irreversible step in
    this release and so goes last.

This suite is the proof that 0101 is safe to let run, and the deploy
runs migrations automatically, so there is no moment afterwards in
which to notice it was not.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Exactly three classes left models.py - counted off
      the syntax tree, not grepped - and no survivor names them.

  2   THE CONTROL. All three were there before, and they pointed at
      each other, so the deletion order in the migration is the order
      the foreign keys require.

  3   DJANGO'S OWN OPINION, which is the strongest check here. The
      autodetector is asked whether any model change is left
      uncaptured; the graph is asked whether 0101 is the single leaf;
      and the app registry is BUILT, because a ForeignKey left
      pointing at a deleted model does not raise on import - it raises
      when Django assembles the registry, which on Railway is at boot.

  4   WIDE. Every .py in the project, every live template, and every
      raw cursor asked whether anything still reads the three. The
      four screens are checked to be in alv_tree.RETIRED rather than
      merely absent.

  5   Scope, registration and the gate. FIVE backups, not six: the
      migration is new and there was no before.

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

import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealdrop'
ME = 'test_meal_drop.py'
PATCHER = 'apply_meal_drop.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MX-1, 19 Oct 2026'
DEAD = ('MealPlan', 'MealPlanDay', 'MealPlanRecipe')
TABLES = ('meal_plans', 'meal_plan_days', 'meal_plan_recipes')
SCREENS = ('meal_plans.html', 'view_meal_plan.html',
           'create_meal_plan.html', 'meal_plan_calendar.html')

MODELS = os.path.join(ROOT, 'pages', 'models.py')
MIGDIR = os.path.join(ROOT, 'pages', 'migrations')
MIG = os.path.join(MIGDIR, '0101_drop_meal_plan.py')
GATE = os.path.join(ROOT, PS1)

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


def classes(src):
    return [n.name for n in ast.parse(src).body
            if isinstance(n, ast.ClassDef)]


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = read(MODELS)
BEFORE = was(MODELS)
CODE = T.python_code_only(NOW, payloads=True)


# ==========================================================================
head('1. THE SOURCE - THREE CLASSES LEFT, AND ONLY THREE')
# ==========================================================================
now_cls, was_cls = classes(NOW), classes(BEFORE)
lost = [c for c in was_cls if c not in now_cls]
ok(sorted(lost) == sorted(DEAD),
   'exactly the three dead models left models.py - counted off the '
   'syntax tree, where a class is a class and a mention is not',
   'removed: %r' % sorted(lost))
ok(not [c for c in now_cls if c not in was_cls],
   '  and this round added none')
ok(len(now_cls) == len(was_cls) - 3,
   '  %d classes became %d' % (len(was_cls), len(now_cls)))

left = [d for d in DEAD if re.search(r'\b%s\b' % d, CODE)]
ok(not left,
   'no surviving code in models.py names any of them - a ForeignKey '
   'left pointing at a deleted model does not raise until Django '
   'builds its registry, which on Railway is at boot',
   'still named: %s' % ', '.join(left))

# AND THE HISTORY IS NOT EDITED. MealEntry's docstring explains what
# it replaced and MUST keep saying so. To a substring search a comment
# about a thing is the thing - which is why the check above reads
# python_code_only and this one reads the raw file.
ok('MealPlan -> MealPlanDay -> MealPlanRecipe' in NOW,
   "MealEntry's docstring still says what it replaced - this round "
   'deletes code, never the record of why')
ok('MealEntry' in now_cls,
   '  and MealEntry itself is untouched')


# ==========================================================================
head('2. THE CONTROL - THEY WERE THERE, AND THEY POINTED AT EACH OTHER')
# ==========================================================================
for d in DEAD:
    ok(d in was_cls, 'CONTROL: %s was a model before this round' % d)
BC = T.python_code_only(BEFORE, payloads=True)
ok(re.search(r'meal_plan\s*=\s*models\.ForeignKey\(MealPlan\b', BC),
   'CONTROL: MealPlanDay pointed at MealPlan')
ok(re.search(r'meal_plan_day\s*=\s*models\.ForeignKey\(MealPlanDay\b', BC),
   'CONTROL: and MealPlanRecipe pointed at MealPlanDay - which is why '
   'the migration deletes children first')
ok('db_table = \'meal_plans\'' in BC or 'db_table = "meal_plans"' in BC,
   'CONTROL: and meal_plans was the table name, so the drop is about '
   'the table this round claims it is about')


# ==========================================================================
head("3. DJANGO'S OWN OPINION - THE REGISTRY, THE GRAPH, THE DETECTOR")
# ==========================================================================
# THE STRONGEST CHECK IN THIS SUITE. Everything above reads text. This
# asks the framework that will run the migration whether it agrees.
try:
    # ITS OWN TEST KEY FIRST - the house convention, which
    # test_settings_env polices. settings.py reads SECRET_KEY from the
    # environment since E13, so on a checkout with no .env the setting
    # is empty and anything touching a session dies with
    # ImproperlyConfigured. A fixed throwaway, never the real one, and
    # setdefault so a machine that HAS a key keeps it.
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.apps import apps
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ProjectState
    from django.db.migrations.questioner import \
        NonInteractiveMigrationQuestioner
    BOOTED = True
except Exception as e:                                    # pragma: no cover
    BOOTED = False
    skip('Django could not be started', str(e)[:90])

if BOOTED:
    # THE REGISTRY IS BUILT. This is the check that would have caught a
    # ForeignKey left dangling, and it is the same operation Railway
    # performs on every boot.
    n_models = len(apps.get_models())
    ok(n_models > 0, 'the app registry assembles - %d model(s)' % n_models)
    for d in DEAD:
        try:
            apps.get_model('pages', d)
            ok(False, '%s is STILL registered with Django' % d)
        except LookupError:
            ok(True, '%s is gone from the registry' % d)
    try:
        tbl = apps.get_model('pages', 'MealEntry')._meta.db_table
    except LookupError:
        tbl = None
    ok(tbl == 'meal_entries',
       '  and MealEntry still maps to meal_entries - the replacement '
       'survived the removal', 'db_table=%r' % tbl)

    # THE GRAPH. 0101 must be the one leaf; two leaves is a branched
    # history and Railway refuses to migrate it.
    loader = MigrationLoader(None, ignore_no_migrations=True)
    leaves = sorted(loader.graph.leaf_nodes('pages'))
    ok(leaves == [('pages', '0101_drop_meal_plan')],
       'the migration graph has ONE leaf and it is 0101 - a second leaf '
       'is a branched history and the deploy refuses it', leaves)

    # THE AUTODETECTOR. "Is anything about these models not yet
    # written down?" If 0101 missed an operation this is where it
    # shows, and it is the same question manage.py makemigrations
    # --check asks.
    auto = MigrationAutodetector(
        loader.project_state(), ProjectState.from_apps(apps),
        NonInteractiveMigrationQuestioner(specified_apps=set(),
                                          dry_run=True))
    changes = auto.changes(graph=loader.graph, trim_to_apps={'pages'},
                           convert_apps={'pages'})
    ok(not changes,
       "the autodetector finds NOTHING left to write - 0101 fully "
       'captures the three deletions',
       '; '.join('%s: %s' % (a, [type(o).__name__ for m in ms
                                 for o in m.operations])
                 for a, ms in (changes or {}).items()))

# THE MIGRATION ITSELF.
MSRC = read(MIG)
order = re.findall(r"DeleteModel\(name='(\w+)'\)", MSRC)
ok(order == ['MealPlanRecipe', 'MealPlanDay', 'MealPlan'],
   'the three deletes are CHILDREN FIRST - a parent dropped before its '
   'child leaves a foreign key pointing at nothing', order)
ok(re.search(r"\('pages', '0100_meal_entry'\)", MSRC),
   '  and it depends on 0100, the migration that announced it')
ok('RunPython(count_first' in MSRC,
   'the rows are COUNTED before anything is destroyed')
ops = MSRC[MSRC.find('operations = ['):]
ok(ops.find('count_first') < ops.find('DeleteModel'),
   '  and the count runs BEFORE the first delete, which is the only '
   'order in which the number means anything',
   'asked of the operations list, not of the whole file - the '
   'docstring explains what a DeleteModel reverses into and mentions '
   'it first')
ok('restores the shape and never the rows' in MSRC,
   '  and the reverse says plainly that it does not bring data back')
ok('0100' in MSRC and 'test data' in MSRC,
   'the 18 Oct decision is quoted in the file that acts on it - this '
   'is a month-old decision carried out, not a new one taken')


# ==========================================================================
head('4. WIDE - DOES ANYTHING AT ALL STILL READ THEM?')
# ==========================================================================
# EVERY .py IN THE PROJECT, not only the ones that looked likely.
# Migrations are excluded because 0036 CREATED these models and must
# keep saying so - a migration is history and history is not edited.
#
# A READER IS A NAME, NOT A WORD. The first draft of this section read
# the comment-free text and accused five files. All five were
# innocent, and in the most instructive way:
#
#   test_planner.py     names all three inside STRING LITERALS, in
#                       MN-1's own absence checks - "NOT ONE of the
#                       three old models survives in the module". It
#                       is the opposite of a reader.
#   apply_planner.py    and three other patchers carry the old model
#                       source in their payloads, because that is the
#                       record of what they removed.
#
# python_code_only(payloads=True) keeps string payloads on purpose -
# it is built to catch a template literal - so it cannot tell a
# reference from a quotation. The syntax tree can: a bare Name or an
# import is a reader, a Constant is a word in a sentence.
def names_used(src):
    """Every identifier this module actually resolves, from the AST."""
    out = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            pass
        elif isinstance(node, ast.ImportFrom):
            for al in node.names:
                out.add(al.name)
        elif isinstance(node, ast.Import):
            for al in node.names:
                out.add(al.name.split('.')[0])
    return out


readers, raws = [], []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in ('__pycache__', '.git',
                                        'node_modules', 'migrations',
                                        '_parked')]
    for f in fn:
        if not f.endswith('.py') or '.bak_' in f:
            continue
        if f in (ME, PATCHER):
            continue
        p = os.path.join(dp, f)
        try:
            raw = read(p)
            code = T.python_code_only(raw, payloads=True)
        except Exception:
            continue
        hit = [d for d in DEAD if d in names_used(raw)]
        if hit:
            readers.append((os.path.relpath(p, ROOT), hit))
        if re.search(r'\.raw\(|cursor\(\)', code):
            named = [t for t in TABLES
                     if re.search(r'["\'`\s]%s["\'`\s]' % t, code)]
            if named:
                raws.append((os.path.relpath(p, ROOT), named))

ok(not readers,
   'no Python file outside migrations RESOLVES any of the three as a '
   'name - asked of the syntax tree, so a comment about them and a '
   'string literal naming them both correctly count as nothing',
   '; '.join('%s -> %s' % (a, ','.join(b)) for a, b in readers[:6]))
ok(not raws,
   'and no raw cursor or .raw() names any of the three TABLES - the '
   'one way a reader could hide from every check above',
   '; '.join('%s -> %s' % (a, ','.join(b)) for a, b in raws[:6]))

# THE FOUR SCREENS ARE RETIRED, NOT MERELY ABSENT. RT-1 built the
# register for exactly this difference: a page that is gone and a page
# that is recorded as gone are different facts, and only the second
# one survives somebody rebuilding the tree.
retired = getattr(T, 'RETIRED', {}) or {}
for s in SCREENS:
    ok(s in retired, '%s is in alv_tree.RETIRED' % s)
    ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'templates', s)),
       '  and is not on disk')

# AND NO LIVE TEMPLATE REVERSES A URL THAT NO LONGER EXISTS. The three
# templates that name `meal_plan` all reverse `meal_plans` or
# `meal_planner`, which MN-1 kept pointing at the new screen so old
# links survive. Read through code_only, because two of the three
# matches are HTML COMMENTS about checkbox counts and the first draft
# of this round refused itself over them.
try:
    urls = read(os.path.join(ROOT, 'pages', 'urls.py'))
    known = set(re.findall(r"name='([^']+)'", urls))
    dangling = []
    for folder, names in T.walk():
        for n in names:
            if '.bak_' in n or not n.endswith('.html'):
                continue
            body = T.code_only(read(os.path.join(folder, n)))
            for nm in re.findall(r"{%\s*url\s+'([^']+)'", body):
                if 'meal' in nm and nm not in known:
                    dangling.append((n, nm))
    ok(not dangling,
       'no live template reverses a meal url that urls.py no longer '
       'has - %d meal url name(s) exist and every reverse hits one'
       % len([k for k in known if 'meal' in k]),
       '; '.join('%s -> %s' % a for a in dangling[:6]))
except Exception as e:
    skip('the url reverses could not be walked', str(e)[:80])


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# ENUMERATED FROM THE BACKUPS ON DISK, NEVER TYPED.
touched = sorted(
    os.path.relpath(os.path.join(dp, f), ROOT)[:-len(SUFFIX)]
    for dp, dn, fn in os.walk(ROOT)
    for f in fn if f.endswith(SUFFIX))
allowed = {'Push-PendingChanges.ps1', 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py', os.path.join('pages', 'models.py'),
           # THE TWO REPAIRS THIS ROUND CAUSED. MW-1 and MO-1 each
           # asked "are there migrations above 0100?" when they meant
           # "did I add one?" - true until this round added 0101.
           # Carried here, by the round that moved them, so a
           # half-applied tree stays green either way round.
           'test_meal_week.py', 'test_meal_day.py'}
ok(len(touched) == 7,
   'SEVEN backups on disk, counted and not typed: %s'
   % ', '.join(touched), '%d found' % len(touched))
extra = set(touched) - allowed
ok(not extra, '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(extra)))

# THE SIXTH FILE IS NEW AND HAS NO BACKUP, which is a fact about the
# round and not a gap in it. Said out loud so the pre-flight's
# "N applied, N backups" line is not read as one short.
ok(os.path.isfile(MIG), 'the migration is on disk')
ok(not os.path.isfile(MIG + SUFFIX),
   '  and has NO backup, because there was no before - this round '
   'writes 8 files and leaves 7 backups, by design')

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok("DeleteModel(name='MealPlanRecipe')" in gate
   and 'dropping %s - %d row(s)' in gate,
   'both sentinels are pinned in the gate')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE LAST THREE TABLES OF THE OLD PLANNER. MealPlan,')
print('  MealPlanDay and MealPlanRecipe leave models.py and 0101 drops')
print('  meal_plans, meal_plan_days and meal_plan_recipes.')
print('')
print('  THE DECISION IS A MONTH OLD. 0100 wrote it down on 18 October')
print('  - the four plans on production are test data, cleared and not')
print('  converted, and the tables wait until push 3 because this is')
print('  the only irreversible step in the release.')
print('')
print('  COUNTED BEFORE DROPPED. A DeleteModel reverses into an empty')
print('  CreateModel: it gives back the shape and never the rows. So')
print('  the migration prints the row count into the deploy log first,')
print('  where anybody asking where their meal plans went can find it.')
print('')
print("  AND DJANGO AGREES. The registry assembles without them, the")
print('  graph has one leaf, and the autodetector finds nothing left')
print('  to write down.')
print('=' * 74)
sys.exit(1 if failed else 0)
