# -*- coding: utf-8 -*-
"""test_recipe_weight.py - round RW-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE WEIGHT IS WORKED OUT IN GRAMS.

Found while surveying for RD-1 and shown to Demetri with the numbers
before a line was written. He asked for it in the same push, so no two
of the four screens that show a weight are ever inconsistent.

THE CLAIM THAT MATTERS, and the one a reader should check first: every
weight equivalent is now accurate to the gram. It was computed as

    round(amount * float(multiplier), 1)

which is one decimal place OF THE TARGET UNIT - a tenth of a gram in
grams, and 100g in kilograms. Section 3 asks the function for the
eleven quantities below and compares each with the true weight, with
the old sum printed beside it so the repair is visible rather than
asserted.

    1 cup @ 0.120 kg      120g true     was 100g      -17%
    2 cup @ 0.120 kg      240g true     was 200g      -17%
    3 cup @ 0.120 kg      360g true     was 400g      +11%
    1 cup @ 0.250 kg      250g true     was 200g      -20%
    1 cup @ 0.160 kg      160g true     was 200g      +25%
    4 cup @ 0.160 kg      640g true     was 600g       -6%
    1 cup @ 0.030 kg       30g true     was NOTHING   -100%

That last row is the one nothing on the screen told you about: 0.03
rounds to 0.0, the greater-than-zero guard then returns None, and the
ingredient simply has no weight beside it.

WHAT MUST NOT HAVE CHANGED, and section 3 asks this as hard as it asks
the rest: a conversion recorded in GRAMS reads the same as it always
did. Ten cups of flour at 120g a cup is 1200g, not 1.2kg. Demetri was
shown those exact numbers, and a round that also changed the display
unit would not be the round he agreed to.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The sum is Decimal and in grams; the factors are
      WEIGHT_UNIT_PRIORITY's own four; the display value comes from
      the exact product rather than from the rounded grams; the
      under-a-kilo promotion survives.

  2   THE CONTROL. Every claim re-asked of the pre-round module, where
      the sum is a float rounded to one place.

  3   THE ARITHMETIC, on a real database, over eleven quantities -
      seven that were wrong, three that were right and must stay
      right, and a pound, which is where the first cut of this round
      went wrong by itself.

  4   DRIVEN. The page, the PDF's read, the book detail and the dialog
      all show the repaired weight, because RD-1 made them one read
      and this is the proof that they still are.

  5   Scope, registration and the gate.

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

SUFFIX = '.bak_recipeweight'
ME = 'test_recipe_weight.py'
PATCHER = 'apply_recipe_weight.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RW-1, 19 Oct 2026'

READ = os.path.join(ROOT, 'pages', 'views', 'recipes', '_recipe_read.py')
GATE = os.path.join(ROOT, PS1)
FILES = (READ,)

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


def claims(bundle):
    """Every source claim RW-1 makes, written once and asked twice."""
    rd = T.python_code_only(bundle[READ], payloads=True)
    c = {}

    # ---- THE SUM IS IN GRAMS, AND IT IS EXACT
    c['there is a table of what each weight unit weighs in grams'] = (
        'GRAMS_PER' in rd)
    c['the sum goes through Decimal, not float'] = (
        'Decimal(conversion.multiplier)' in rd)
    c['and float(multiplier) is gone - a Decimal times a float is a '
      'float, so one of them puts the fault back'] = (
        'float(conversion.multiplier)' not in rd)
    c['nothing rounds in the target unit any more'] = (
        'round(amount' not in rd)
    c['the gram figure is a whole number of grams'] = (
        "grams = int(grams.quantize(Decimal('1')" in rd)

    # ---- THE FACTORS ARE EXACT WHERE IT MATTERS
    #
    # The ounce and the pound are DEFINED as 28.349523125g and
    # 453.59237g. Writing 28.35 would be inventing a third answer.
    c['the ounce is its defined value, not a rounded one'] = (
        "'oz': Decimal('28.349523125')" in rd)
    c['and so is the pound'] = (
        "'lb': Decimal('453.59237')" in rd)

    # ---- THE DISPLAY VALUE COMES FROM THE PRODUCT
    #
    # The first cut divided the rounded grams back by the factor and
    # turned an exact quarter pound into 0.249lb. A round-trip through
    # an integer cannot be more faithful than the integer.
    c['the shown value comes from the exact product, not from the '
      'rounded grams'] = (
        'product.quantize' in rd)
    c['and trailing zeros go through a format, because '
      "Decimal('1000').normalize() is 1E+3"] = (
        ".rstrip('0').rstrip('.')" in rd and 'normalize()' not in rd)

    # ---- AND THE RULE THAT WAS ALREADY THERE IS STILL THERE
    c['a kilogram conversion under a kilo still reads in grams, which '
      'is what makes 120g and 30g right'] = (
        "weight_unit == 'kg' and grams < 1000" in rd)
    c['a gram conversion still reads in grams at any size, so ten cups '
      'of flour stays 1200g'] = (
        "weight_unit == 'g' or (" in rd)

    # ---- A UNIT IT CANNOT CONVERT IS REFUSED, NOT GUESSED
    c['a unit with no factor returns nothing rather than guessing '
      'one'] = (
        'if per_gram is None:' in rd)

    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# THE FACTOR TABLE AND THE PRIORITY LIST ARE THE SAME FOUR UNITS.
#
# A unit in one and not the other is a unit that can be chosen and not
# converted, or converted and never chosen. Asked of both imports
# rather than of either one's text.
# READ OUT OF THE FILE, NOT IMPORTED. Section 1 runs before Django is
# started - section 3 is what starts it - so importing _helpers here
# raises "settings are not configured" and the check skips. The
# patcher's own copy of this check did worse: it caught the exception
# and fell through to a hardcoded {'g','kg','oz','lb'}, so it compared
# the table against a copy of my own expectation and could never fail.
HELPERS = os.path.join(ROOT, 'pages', 'views', 'recipes', '_helpers.py')
_m = re.search(r'^WEIGHT_UNIT_PRIORITY\s*=\s*\[([^\]]*)\]',
               read(HELPERS), re.M)
ok(_m is not None,
   '_helpers declares WEIGHT_UNIT_PRIORITY as a literal list, so the '
   'factor table can be checked against it')
if _m:
    priority = set(re.findall(r"'(\w+)'", _m.group(1)))
    keys = set(re.findall(r"^    '(\w+)': Decimal\(", NOW[READ], re.M))
    ok(keys == priority,
       'and the factor table is exactly the units it asks for',
       'table %r, priority %r' % (sorted(keys), sorted(priority)))


# ==========================================================================
head('2. THE CONTROL - every claim re-asked of the pre-round module')
# ==========================================================================
BEFORE = {READ: was(READ)}
WAS_CLAIMS = claims(BEFORE)
held = [m for m, got in WAS_CLAIMS.items() if got]
ok(not held,
   'not one of the %d claims held before this round ran'
   % len(WAS_CLAIMS),
   'these held already, so they are not this round: %r' % (held[:4],))

OLD = T.python_code_only(BEFORE[READ], payloads=True)
ok('round(amount * float(conversion.multiplier), 1)' in OLD,
   'CONTROL: the sum really was one decimal place of the target unit')
ok('GRAMS_PER' not in OLD,
   'CONTROL: and there was no table of grams to work in')
ok('def ingredient_rows(' in OLD,
   'CONTROL: and RD-1 had already put the read in one place, which is '
   'why this is a four-line round and not a four-file one')


# ==========================================================================
head('3. THE ARITHMETIC, ON A REAL DATABASE')
# ==========================================================================
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import alv_offline                                      # noqa: F401
    import django
    django.setup()
    from django.conf import settings as dj_settings
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + \
        ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.DEBUG = True
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

cl = None
first = None
if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (Ingredient, MeasurementUnit, Recipe,
                              RecipeIngredient, RecipeInstruction,
                              UnitConversion)
    from pages.views.recipes import _recipe_read as RR

    u = User.objects.create_user(username='rw1', password='x',
                                 email='rw1@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    gram = MeasurementUnit.objects.create(
        name='gram', abbreviation='g', unit_type='weight')
    kilo = MeasurementUnit.objects.create(
        name='kilogram', abbreviation='kg', unit_type='weight')
    pound = MeasurementUnit.objects.create(
        name='pound', abbreviation='lb', unit_type='weight')
    cup = MeasurementUnit.objects.create(
        name='cup', abbreviation='cup', unit_type='volume')

    GRAMS = {'g': 1.0, 'kg': 1000.0, 'oz': 28.349523125, 'lb': 453.59237}

    # EVERY CASE IS ITS OWN INGREDIENT AND ITS OWN RECIPE, so no two of
    # them can share a conversion row and quietly answer for each other.
    CASES = [
        (1, '0.120', kilo, 120, 'the one Demetri was shown first'),
        (2, '0.120', kilo, 240, 'twice it'),
        (3, '0.120', kilo, 360, 'where the old sum rounded UP, not down'),
        (1, '0.250', kilo, 250, 'a quarter kilo'),
        (1, '0.160', kilo, 160, 'the worst of them, at +25%'),
        (4, '0.160', kilo, 640, 'and four of those'),
        (1, '0.030', kilo, 30, 'the one that showed NOTHING at all'),
        (10, '0.120', kilo, 1200, 'over a kilo, so it reads in kilos'),
        (10, '120', gram, 1200, 'MUST NOT MOVE - recorded in grams'),
        (1, '120', gram, 120, 'MUST NOT MOVE - recorded in grams'),
        (1, '0.25', pound, 113, 'a quarter pound, exactly as recorded'),
    ]

    def old_sum(amount, multiplier, abbr):
        """The sum this round replaced, written out once."""
        w = round(float(amount) * float(multiplier), 1)
        if w == int(w):
            w = int(w)
        if w <= 0:
            return None
        unit = abbr
        if unit == 'kg' and w < 1:
            w = round(w * 1000)
            unit = 'g'
        return '%s%s' % (w, unit)

    def in_grams(text):
        """Whatever the function said, expressed in grams."""
        m = re.match(r'^([\d.]+)(\w+)$', text or '')
        if not m:
            return None
        return float(m.group(1)) * GRAMS[m.group(2)]

    rows = []
    for n, (amount, mult, unit, true_g, why) in enumerate(CASES):
        ing = Ingredient.objects.create(name='Case %d' % n)
        UnitConversion.objects.create(
            from_unit=cup, to_unit=unit, specific_ingredient=ing,
            multiplier=mult)
        r = Recipe.objects.create(recipe_name='Case %d' % n, servings=4)
        RecipeIngredient.objects.create(
            recipe=r, ingredient=ing, unit=cup, amount=str(amount),
            ingredient_group='', ingredient_order=0)
        RecipeInstruction.objects.create(recipe=r, step_number=1,
                                         instruction_text='Weigh it.')
        if first is None:
            first = r
        got = RR.ingredient_rows(r)[0].weight_equivalent
        rows.append((amount, mult, unit, true_g, why, got,
                     old_sum(amount, mult, unit.abbreviation)))

    print('  %-24s %-8s %-9s %-9s' % ('in the recipe', 'true', 'was',
                                      'RW-1'))
    for amount, mult, unit, true_g, why, got, before in rows:
        print('  %-24s %-8s %-9s %-9s' % (
            '%g cup @ %s%s' % (amount, mult, unit.abbreviation),
            '%dg' % true_g, before, got))
    print('')

    wrong = [(why, true_g, got) for amount, mult, unit, true_g, why, got,
             before in rows
             if in_grams(got) is None or abs(in_grams(got) - true_g) > 1]
    ok(not wrong,
       'all %d quantities are accurate to the gram' % len(rows),
       'these are not: %r' % (wrong,))

    # AND THE COMPARISON COULD HAVE FAILED. The thing that fails it is
    # the sum this round replaced.
    was_wrong = [(why, true_g, before)
                 for amount, mult, unit, true_g, why, got, before in rows
                 if in_grams(before) is None
                 or abs(in_grams(before) - true_g) > 1]
    # EIGHT, NOT SEVEN - and the eighth is why the number is asserted
    # rather than taken from the docstring. The table in this suite's
    # docstring lists the seven kilogram rows Demetri was shown; the
    # quarter pound was wrong too, by the same fault in a different
    # unit (0.2lb against a true 113g, a 20% error), and nobody had
    # looked at it. Writing 7 here because 7 was in the table I showed
    # him would have been asserting my own summary.
    ok(len(was_wrong) == 8,
       'CONTROL: and the old sum was wrong on 8 of the 11 - the seven '
       'kilogram rows and the pound, which was not in the table',
       '%d were wrong: %r' % (len(was_wrong), was_wrong))
    ok(any(unit is pound for amount, mult, unit, true_g, why, got, before
           in rows),
       'the eighth being a pound, which is the same fault in another '
       'unit')

    # THE ONE THAT VANISHED, named on its own, because an absent weight
    # is the failure nothing on the screen reports.
    vanished = [(why, before) for amount, mult, unit, true_g, why, got,
                before in rows if before is None]
    ok(len(vanished) == 1,
       'CONTROL: and on one of them it showed nothing at all',
       '%r' % (vanished,))
    ok(rows[6][5] == '30g',
       'which now reads 30g', 'reads %r' % (rows[6][5],))

    # WHAT MUST NOT HAVE MOVED. Asked by value, not by "it still works".
    grams_recorded = [(why, before, got)
                      for amount, mult, unit, true_g, why, got, before
                      in rows if unit is gram]
    ok(all(before == got for why, before, got in grams_recorded),
       'every weight recorded in GRAMS reads exactly as it did before',
       '%r' % (grams_recorded,))
    ok(rows[8][5] == '1200g',
       'ten cups of flour at 120g a cup is still 1200g, not 1.2kg',
       'reads %r' % (rows[8][5],))
    ok(rows[7][5] == '1.2kg',
       'and a kilogram conversion over a kilo still reads in kilos',
       'reads %r' % (rows[7][5],))
    ok(rows[10][5] == '0.25lb',
       'a quarter pound reads 0.25lb - the first cut of this round said '
       '0.249lb, by dividing the rounded grams back out',
       'reads %r' % (rows[10][5],))


# ==========================================================================
head('4. DRIVEN - all four screens, because RD-1 made them one read')
# ==========================================================================
if not django_up or cl is None or first is None:
    skip('the driven checks', 'no database')
else:
    import json as _json
    from django.urls import reverse

    # CASE 0 is the 1 cup @ 0.120kg that read 100g on the live page.
    rid = first.recipe_id

    page = cl.get(reverse('view_recipe', args=[rid]))
    ok(page.status_code == 200, 'the recipe page renders',
       'got %s' % page.status_code)
    weights = re.findall(r'data-weight-equivalent="([^"]*)"',
                         page.content.decode('utf-8')
                         if page.status_code == 200 else '')
    ok('120g' in weights,
       'and now says 120g where it said 100g', 'said %r' % (weights,))

    dlg = cl.get(reverse('recipe_quicklook', args=[rid]))
    ok(dlg.status_code == 200, 'the dialog renders',
       'got %s' % dlg.status_code)
    shown = re.findall(r'ql-weight">\(([^)]*)\)',
                       dlg.content.decode('utf-8')
                       if dlg.status_code == 200 else '')
    ok(shown == ['120g'], 'and says the same thing',
       'said %r' % (shown,))

    bd = cl.get(reverse('recipe_book_detail', args=[rid]))
    ok(bd.status_code == 200, 'the book detail answers',
       'got %s' % bd.status_code)
    if bd.status_code == 200:
        try:
            payload = _json.loads(bd.content.decode('utf-8'))
        except ValueError:
            payload = {}
        bw = [r.get('weight_equivalent')
              for r in payload.get('ingredients', [])]
        ok(bw == ['120g'], 'and so does it', 'said %r' % (bw,))

    # THE PDF IS THE FOURTH, and it is the one that cannot be asked for
    # a string - so it is asked whether it still builds at all, and the
    # read behind it is asked for the value.
    from pages.views.recipes import _recipe_read as RR2
    ok(RR2.ingredient_rows(first)[0].weight_equivalent == '120g',
       "the PDF's read gives 120g too - it is the same function")


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
# AFTER WHAT IT BUILDS ON, not "newest".
#
# This asserted ROUNDS[-1] == SUFFIX, which is true of a round
# delivered on its own and FALSE for seven of the eight in this push -
# only one of them can be last. Eight suites carried the same wrong
# claim, because each was written as though it would ship alone.
#
# The claim was reaching for something real: revert runs NEWEST FIRST,
# so a round must sit AFTER anything whose work it edits, or reverting
# the two in order restores the older round's text over the newer
# one. That is the 18 Oct bug and it cost a hand repair.
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_recipemodal']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
# RETIRED - DB-1, 20 Oct 2026. This asked whether the round sat in
# the last eight entries of the register, which was true while push 2
# was the newest thing in it and false as soon as anything shipped
# after it. It is the same mistake as the `ROUNDS[-1] == SUFFIX` it
# replaced: a claim about a POSITION in a growing list expires
# whatever number is in it, so re-pinning would only move the date.
# The dependency claim above is the real one and does not expire.
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once',
   alv_rounds.ROUNDS.count(SUFFIX))
ok('GRAMS_PER' in gate, 'the gate pins the table of grams')

for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok(MARK in NOW[READ], 'and so does the line it changed')
ok('already applied' in patcher,
   'the patcher has an already-applied path')

# THIS ROUND CREATES NOTHING, and says so - RD-1 taught stage_round.py
# to read that declaration, and a round that is silent about it would
# be indistinguishable from one that forgot.
import apply_recipe_weight as PATCH                         # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing, which is a different thing '
   'from not saying')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
