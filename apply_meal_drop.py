# -*- coding: utf-8 -*-
"""apply_meal_drop.py - round MX-1, 19 Oct 2026.

RELEASE 3, PUSH 3. THE LAST THREE TABLES OF THE OLD PLANNER.

MN-1 replaced the chain MealPlan -> MealPlanDay -> MealPlanRecipe with
one MealEntry on 18 October, and retired the four screens that drew
it. Migration 0100 said what would happen next, in its own docstring:

    NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
    production are test data and are cleared rather than converted.
    The old tables are left in place, empty and unread, until 0101
    drops them in push 3 - which is the only irreversible step in
    this release and so goes last.

This is 0101. The decision is a month-old one being carried out, not
a new one being taken.

WHAT IS LEFT TO REMOVE, asked of the tree and not assumed:

    pages/models.py          three model classes, 97 lines
    the database             meal_plans, meal_plan_days,
                             meal_plan_recipes

and nothing else. Every template that drew them is already in
alv_tree.RETIRED - meal_plans.html, view_meal_plan.html,
create_meal_plan.html, meal_plan_calendar.html - and no view, no url,
no admin registration and no live template names any of the three.
The patcher re-asks all of that before it writes, because a migration
that drops a table something still reads is a 500 on production and
not a failed check.

THE ONE IRREVERSIBLE STEP IN THE RELEASE, SO IT COUNTS FIRST. The
migration opens by counting the rows in all three tables and PRINTING
the counts into the deploy log, before anything is dropped. Django
will happily reverse a DeleteModel by creating an empty table again,
which gives back the shape and not the data - so the only honest
safety here is a record of exactly how much was destroyed, written
where it can be found afterwards. If the three counts are zero, as the
18 Oct decision expects, the log says zero.

Idempotent. Every file backed up to .bak_mealdrop.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealdrop'
MODELS = os.path.join('pages', 'models.py')
MIG = os.path.join('pages', 'migrations', '0101_drop_meal_plan.py')
PREV = '0100_meal_entry'
ME = 'test_meal_drop.py'
PATCHER = 'apply_meal_drop.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MX-1, 19 Oct 2026'
DEAD = ('MealPlan', 'MealPlanDay', 'MealPlanRecipe')
TABLES = ('meal_plans', 'meal_plan_days', 'meal_plan_recipes')
CHECK = False


# ============================================================ THE MIGRATION
MIGRATION = '''# -*- coding: utf-8 -*-
"""MX-1, 19 Oct 2026 - release 3, push 3. The old planner's tables go.

0100 wrote down what this migration would be, on 18 October:

    NO DATA MIGRATION, by decision on 18 Oct: the four meal plans on
    production are test data and are cleared rather than converted.
    The old tables are left in place, empty and unread, until 0101
    drops them in push 3 - which is the only irreversible step in
    this release and so goes last.

THE COUNT IS TAKEN BEFORE ANYTHING IS DROPPED, and printed. A
DeleteModel reverses into an empty CreateModel - it gives back the
shape and never the rows - so a record of how much was destroyed is
the only honest safety this migration can offer. It is written into
the deploy log, where it can be found afterwards by anybody asking
where their meal plans went.

CHILDREN FIRST. meal_plan_recipes points at meal_plan_days, which
points at meal_plans, and a parent dropped before its child leaves a
foreign key pointing at nothing.
"""
from django.db import migrations


def count_first(apps, schema_editor):
    """Say what is about to be destroyed, before destroying it."""
    for label in ('MealPlanRecipe', 'MealPlanDay', 'MealPlan'):
        try:
            model = apps.get_model('pages', label)
            n = model.objects.count()
        except Exception as e:                         # pragma: no cover
            print('  MX-1: %s could not be counted (%s)' % (label, e))
            continue
        print('  MX-1: dropping %s - %d row(s)' % (label, n))


def no_going_back(apps, schema_editor):
    """The reverse of a count is a count."""
    print('  MX-1: reversed. The tables come back EMPTY - a DeleteModel '
          'restores the shape and never the rows.')


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '@PREV@'),
    ]

    operations = [
        migrations.RunPython(count_first, no_going_back),
        migrations.DeleteModel(name='MealPlanRecipe'),
        migrations.DeleteModel(name='MealPlanDay'),
        migrations.DeleteModel(name='MealPlan'),
    ]
'''


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },"""
SENT_NOW = """    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },
    # ------------------------------------------------- MX-1, 19 Oct 2026
    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = "DeleteModel(name='MealPlanRecipe')"; What = 'MX-1: the old planner three tables go, children first - the step 0100 said would come last' },
    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = 'dropping %s - %d row(s)'; What = 'MX-1: and the count is taken BEFORE the drop and printed, because a DeleteModel reverses into an empty table' },"""

SUITE_WAS = """    'test_gate_serial.py'
)"""
SUITE_NOW = """    'test_gate_serial.py',
    # MX-1, 19 Oct 2026 - the old planner's three tables. The
    # suite re-asks the whole tree whether anything still reads
    # them, because a migration that drops a table something
    # still names is a 500 and not a failed check.
    'test_meal_drop.py'
)"""

TREE_WAS = """    'test_gate_serial.py',
]"""
TREE_NOW = """    'test_gate_serial.py',
    # MX-1, 19 Oct 2026 - the three dead models leave models.py and
    # 0101 drops their tables. Section 3 walks both template roots and
    # every view, url and admin file looking for a reader.
    'test_meal_drop.py',
]"""

RD_WAS = """    '.bak_gateserial',
]"""
RD_NOW = """    '.bak_gateserial',
    # MX-1, 19 Oct 2026 - MealPlan, MealPlanDay and MealPlanRecipe are
    # deleted and 0101 drops meal_plans, meal_plan_days and
    # meal_plan_recipes. The decision was taken on 18 Oct and written
    # into 0100's docstring; this is it being carried out. The only
    # irreversible step in release 3, which is why it went last.
    '.bak_mealdrop',
]"""

# ========================================= TWO REPAIRS THIS ROUND CAUSED
# "THIS ROUND ADDS NO MIGRATION" IS A QUESTION ABOUT A ROUND, AND BOTH
# SUITES ASKED IT OF THE TREE.
#
# MW-1 and MO-1 each check that they needed no migration of their own.
# Both implemented it as "are there any migrations numbered above
# 0100?" - which was the same answer while 0100 was the leaf, and
# stops being the same answer the moment ANY later round adds one.
# MX-1 is that round, doing exactly what 0100 said it would.
#
# This is the lesson RT-1 paid for on 18 October, in a third place:
# historical and present-tense reads are different questions, and the
# call site is the only place that knows which one is being asked. The
# question MW-1 wants is "did I add a migration", and that is
# answerable forever - a migration MW-1 added would carry MW-1's mark.
#
# A RE-PIN WOULD HAVE BEEN WRONG. Bumping 100 to 101 in both files
# gives a green suite today and the identical failure on the next
# round that migrates. The check is repaired, not re-pinned.
MIGQ_WAS = """ours = sorted(n for n in os.listdir(migs)
              if n.endswith('.py') and n[:4].isdigit() and int(n[:4]) > 100)
ok(not ours, 'this round adds NO migration', ours)"""


def migq_now(mark):
    return """# ASKED OF THIS ROUND, NOT OF THE TREE - repaired by MX-1,
# 19 Oct 2026. This read `int(n[:4]) > 100` and so answered
# "has anybody migrated since 0100?" rather than "did I?". It
# was true until MX-1 added 0101 to drop the old planner's
# tables, which 0100 had announced on 18 October.
#
# A migration THIS round added would carry this round's mark.
# That question keeps its answer no matter how many rounds
# migrate afterwards.
ours = []
for n in sorted(os.listdir(migs)):
    if not (n.endswith('.py') and n[:4].isdigit()):
        continue
    if '%s' in read(os.path.join(migs, n)):
        ours.append(n)
ok(not ours, 'this round adds NO migration', ours)""" % mark


WD_WAS = """CONVERTED_N = 113   # GS-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 114   # MX-1, 19 Oct 2026 - this round own suite   # (was 113)   # GS-1, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('MX-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def cut_class(text, name):
    """Remove one top-level class, SLICED FROM THE TREE not from a payload.

    A hundred lines of model code copied into this file as a literal
    would be a second copy of the thing being deleted, and it would
    stop matching the day anybody touched a docstring in it. So the
    boundaries are found: the class statement, and the next line at
    column zero that starts a new top-level definition.

    Returns (new_text, the_removed_block).
    """
    nl = '\r\n' if text.count('\r\n') > text.count('\n') - text.count('\r\n') \
        else '\n'
    pat = re.compile(r'^class %s\(' % re.escape(name), re.M)
    m = pat.search(text)
    if not m:
        refuse('%s: there is no top-level `class %s(` to remove'
               % (MODELS, name))
    if len(pat.findall(text)) != 1:
        refuse('%s: `class %s(` appears %d times at column zero'
               % (MODELS, name, len(pat.findall(text))))
    start = m.start()
    nxt = re.compile(r'^(class |def |@|[A-Za-z_][A-Za-z_0-9]* = )', re.M)
    end = len(text)
    for m2 in nxt.finditer(text, m.end()):
        end = m2.start()
        break
    block = text[start:end]
    # THE SLICE MUST BE EXACTLY ONE CLASS. If a second top-level class
    # fell inside it the boundary search was wrong, and this round
    # would delete a model nobody asked it to.
    inner = re.findall(r'^class (\w+)\(', block, re.M)
    if inner != [name]:
        refuse('%s: the slice for %s holds classes %r - the boundary '
               'search is wrong and this round will not guess'
               % (MODELS, name, inner))
    # Leave the blank lines that separated it from its neighbour.
    tail = text[end:]
    head = text[:start].rstrip() + nl + nl + nl
    return head + tail, block


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pm = os.path.join(root, MODELS)
    m = read(pm)
    m_before = m

    # ---------------------------------------------------------------- 0
    # ASK THE TREE FIRST.
    if not re.search(r'^class MealPlan\(', m, re.M):
        print('MX-1  already applied - the three models are gone.')
        return 0

    # ---------------------------------------------------------------- 1
    # NOTHING MAY STILL READ THEM. This is the gate the whole round
    # hangs on: a DeleteModel against a table some view still queries
    # is a 500 on production, and the deploy runs migrations
    # automatically, so there is no moment in between to notice.
    #
    # Comments do not count. MealEntry's own docstring explains what it
    # replaced and must keep saying so - to a substring search, a
    # comment about a thing is the thing, and that confusion has cost
    # this project five repairs in two days.
    sys.path.insert(0, root)
    import alv_tree as T

    readers = []
    for dp, dn, fn in os.walk(os.path.join(root, 'pages')):
        dn[:] = [d for d in dn if d not in ('__pycache__', 'migrations')]
        for f in fn:
            if not f.endswith('.py') or '.bak_' in f:
                continue
            p = os.path.join(dp, f)
            if os.path.abspath(p) == os.path.abspath(pm):
                continue
            try:
                code = T.python_code_only(read(p), payloads=True)
            except Exception:
                code = read(p)
            hit = [d for d in DEAD
                   if re.search(r'\b%s\b' % d, code)]
            if hit:
                readers.append((os.path.relpath(p, root), hit))
    if readers:
        refuse('%d file(s) still name the models this round deletes, in '
               'CODE and not in comments: %s'
               % (len(readers),
                  '; '.join('%s -> %s' % (a, ','.join(b))
                            for a, b in readers[:6])))

    # NOT THE TEMPLATES - AND THE REASON IS WORTH WRITING DOWN, because
    # the first draft of this round refused itself over them.
    #
    # It searched every live template for `meal_plan` and found three:
    # base.html and projects_detail.html mention view_meal_plan in HTML
    # COMMENTS about checkbox counts, and meal_plan_shopping_list.html
    # reverses the url names `meal_plans` and `meal_planner` - which MN-1
    # deliberately KEPT, pointing at the new planner, so old links do
    # not break. None of the three is a reader of anything.
    #
    # A template cannot reach a model at all. It renders what a view
    # puts in its context, and the loop above has just proved that no
    # view, url, admin or service module names these three in code. The
    # four screens that did draw them are in alv_tree.RETIRED and the
    # suite checks that separately.
    #
    # THE REAL RESIDUAL RISK IS RAW SQL, which no model reference would
    # show: a cursor or a .raw() naming the table directly walks
    # straight past every check above and fails at runtime.
    sqls = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn
                 if d not in ('__pycache__', '.git', 'node_modules',
                              'migrations')]
        for f in fn:
            if not f.endswith('.py') or '.bak_' in f:
                continue
            p = os.path.join(dp, f)
            if os.path.basename(p) in (PATCHER, ME):
                continue
            try:
                code = T.python_code_only(read(p), payloads=True)
            except Exception:
                continue
            if not re.search(r'\.raw\(|cursor\(\)', code):
                continue
            named = [t for t in TABLES
                     if re.search(r'["\'`\s]%s["\'`\s]' % t, code)]
            if named:
                sqls.append((os.path.relpath(p, root), named))
    if sqls:
        refuse('%d file(s) run raw SQL naming a table this round drops: '
               '%s' % (len(sqls),
                       '; '.join('%s -> %s' % (a, ','.join(b))
                                 for a, b in sqls[:6])))

    # THE MIGRATION IT DEPENDS ON MUST BE THERE AND BE THE LAST ONE.
    md = os.path.join(root, 'pages', 'migrations')
    have = sorted(f[:-3] for f in os.listdir(md)
                  if re.match(r'^\d{4}_.*\.py$', f))
    if PREV not in have:
        refuse('%s is not in pages/migrations, so 0101 has nothing to '
               'depend on' % PREV)
    if have[-1] != PREV:
        refuse('the last migration is %s, not %s - 0101 would branch the '
               'history' % (have[-1], PREV))
    if os.path.exists(os.path.join(root, MIG)):
        refuse('%s already exists' % MIG)

    # ---------------------------------------------------------------- 2
    # THE MODELS. Children first here too, so a slice never has to
    # span a class that is itself about to move.
    removed = {}
    for name in ('MealPlanRecipe', 'MealPlanDay', 'MealPlan'):
        m, block = cut_class(m, name)
        removed[name] = block
    out[pm] = m

    # ---------------------------------------------------------------- 3
    out[os.path.join(root, MIG)] = MIGRATION.replace('@PREV@', PREV)

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pt = os.path.join(root, TREE)
    out[pt] = swap(read(pt), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- 3b
    # THE TWO REPAIRS. Carried by the round that caused them, so a
    # half-applied tree stays green either way round.
    for suite, mark in (('test_meal_week.py', 'MW-1, 19 Oct 2026'),
                        ('test_meal_day.py', 'MO-1, 19 Oct 2026')):
        ps = os.path.join(root, suite)
        out[ps] = swap(read(ps), MIGQ_WAS, migq_now(mark),
                       '%s (the migration question)' % suite)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nm = out[pm]

    # THE THREE ARE GONE AND NOTHING ELSE WENT WITH THEM. Counted off
    # the syntax tree, because this round removes code and the one
    # thing it must never do is remove a fourth model by accident.
    was_cls = [n.name for n in ast.parse(m_before).body
               if isinstance(n, ast.ClassDef)]
    now_cls = [n.name for n in ast.parse(nm).body
               if isinstance(n, ast.ClassDef)]
    lost = [c for c in was_cls if c not in now_cls]
    if sorted(lost) != sorted(DEAD):
        refuse('%s: this round removed %r, expected exactly %r'
               % (MODELS, sorted(lost), sorted(DEAD)))
    gained = [c for c in now_cls if c not in was_cls]
    if gained:
        refuse('%s: this round ADDED class(es) %r' % (MODELS, gained))

    # AND NOTHING THAT SURVIVED NAMES THEM. A ForeignKey left pointing
    # at a deleted model does not raise at import; it raises when
    # Django builds the app registry, which on Railway is at boot.
    left = [d for d in DEAD if re.search(r'\b%s\b' % d,
                                         T.python_code_only(nm,
                                                            payloads=True))]
    if left:
        refuse('%s: %s still appear(s) in code after the cut'
               % (MODELS, ', '.join(left)))

    # THE MIGRATION SAYS THE RIGHT THINGS, asked of its syntax tree.
    mig = ast.parse(out[os.path.join(root, MIG)])
    names = re.findall(r"DeleteModel\(name='(\w+)'\)",
                       out[os.path.join(root, MIG)])
    if names != ['MealPlanRecipe', 'MealPlanDay', 'MealPlan']:
        refuse('%s: the deletes are %r - children must go before their '
               'parents or a foreign key is left pointing at nothing'
               % (MIG, names))
    if 'RunPython' not in out[os.path.join(root, MIG)]:
        refuse('%s: nothing counts the rows before they are destroyed'
               % MIG)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MX-1 --check')
        for name in DEAD:
            print('  cut %-16s %d line(s)'
                  % (name, removed[name].count('\n')))
        print('  models.py  %d class(es) -> %d'
              % (len(was_cls), len(now_cls)))
        print('  migration  %s, after %s' % (os.path.basename(MIG), PREV))
        print('  readers    none - no view, url, admin or live template')
        print('  tables     %s' % ', '.join(TABLES))
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        if os.path.exists(q):
            backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('MX-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('   %s is NEW and has no backup - there was no before.'
          % os.path.basename(MIG))
    print('Now run:  python test_meal_drop.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
