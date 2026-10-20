# -*- coding: utf-8 -*-
"""test_recipe_modal.py - round RD-1, 19 Oct 2026.

RELEASE 4, PUSH 2. A RECIPE WITHOUT LEAVING THE CALENDAR.

Demetri, answering Q2 of the Release 4 questions: clicking a meal
should let him "view the recipe (a detailed view of the recipe in a
modal)". This suite judges the dialog, and the extraction that had to
happen before it could exist.

THE CLAIM THAT MATTERS, and the one a reader should check first: the
page, the PDF and the dialog now give the SAME weight for the same
ingredient, and it is the weight the rest of the recipes package would
give. Before this round `view_recipe` and `recipe_pdf` each held their
own copy of the forty lines that turn an amount into a weight, and the
two copies disagreed with each other AND with
`_helpers.get_preferred_weight_conversion`, which is the authority
everything else in the package asks.

So section 3 does not compare the new code with the old code. It
compares the new code with THE AUTHORITY, on every ingredient of every
recipe it builds - and then shows the two blocks it replaced failing
the same comparison. A round that replaced one answer with another
answer would pass a self-comparison and still be wrong.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One module holds the read; recipe_crud calls it
      three times and keeps no copy; the module asks
      WEIGHT_UNIT_PRIORITY rather than inventing an order; the
      endpoint is read-tier; the dialog's rules are in the half that
      arrives once, not the half that arrives on every open.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      the read is in two places and there is no endpoint at all.

  3   THE SAME ANSWER AS THE AUTHORITY, on a real database, over
      eight ingredient cases built so that each one separates
      something - including a unit with two legal weight conversions,
      which is where the old blocks and the authority part company.

  4   DRIVEN, through a real client. The whole recipe in the partial,
      a bad id refused, read-tier enforced, and the trigger still a
      link that works with the dialog switched off.

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

SUFFIX = '.bak_recipemodal'
ME = 'test_recipe_modal.py'
PATCHER = 'apply_recipe_modal.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RD-1, 19 Oct 2026'

READ = os.path.join(ROOT, 'pages', 'views', 'recipes', '_recipe_read.py')
CRUD = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
PART = os.path.join(ROOT, 'pages', 'templates', 'recipe_quicklook.html')
SHELL = os.path.join(ROOT, 'pages', 'templates',
                     'recipe_quicklook_shell.html')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)

# THE FILES THE CONTROL CAN ASK. _recipe_read.py, the partial and the
# shell did not exist before this round, so they have no backup and the
# control asks a different question of them: it asks the DISK whether
# they were there.
FILES = (CRUD, URLS, TPL, os.path.join(ROOT, 'stage_round.py'))
NEW_FILES = (READ, PART, SHELL)

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
for _p in NEW_FILES:
    NOW[_p] = read(_p) if os.path.isfile(_p) else ''


def claims(bundle):
    """Every source claim RD-1 makes, written once and asked twice.

    `bundle` is {path: text}, so section 2 can hand this the same
    questions with the pre-round text behind them.
    """
    rd = T.python_code_only(bundle[READ], payloads=True) \
        if bundle[READ] else ''
    cr = T.python_code_only(bundle[CRUD], payloads=True)
    ur = T.python_code_only(bundle[URLS], payloads=True)
    part = T.code_only(bundle[PART]) if bundle[PART] else ''
    shell = T.code_only(bundle[SHELL]) if bundle[SHELL] else ''
    tpl = T.code_only(bundle[TPL])

    c = {}

    # ---- ONE MODULE HOLDS THE READ
    c['the read is a module of its own'] = (
        'def ingredient_rows(' in rd and 'def instruction_rows(' in rd)
    c['and it exposes the two halves separately, because the PDF '
      'wants both and a caller may want one'] = (
        'def weight_conversions(' in rd and 'def weight_equivalent(' in rd)

    # ---- AND IT ASKS THE AUTHORITY RATHER THAN INVENTING AN ORDER
    #
    # A SECOND ORDER WOULD BE THE SAME DRIFT IN A NEW PLACE. The point
    # of the extraction is that one answer exists, not that a third
    # implementation agrees with itself.
    c['the module asks WEIGHT_UNIT_PRIORITY, the list '
      'get_preferred_weight_conversion already walks'] = (
        'WEIGHT_UNIT_PRIORITY' in rd)
    # AN ABSENCE IS TRIVIALLY TRUE OF A FILE THAT IS NOT THERE.
    #
    # This claim and the two marked the same way below are about
    # something NOT being present, and the control section hands this
    # function an empty string for every file the round invented. So
    # each one is asked of the subject FIRST: `bool(rd) and ...`. Three
    # of them were not, and the control duly reported that three of
    # this round's claims held before the round ran - which was the
    # control working, on the suite rather than on the tree.
    c['and spells no order of its own'] = (
        bool(rd) and "'g', 'kg', 'oz', 'lb'" not in rd)
    c['it constrains to_unit to a weight, so a volume cannot be '
      'presented as one'] = (
        "to_unit__unit_type='weight'" in rd)
    c['and it does not query with an empty __in, which the page did '
      'on every all-weights recipe'] = (
        'if not unit_ids:' in rd)

    # ---- recipe_crud KEEPS NO COPY, AND THERE WERE THREE
    c['recipe_crud calls ingredient_rows three times - the page, the '
      'PDF and the dialog'] = (
        cr.count('ingredient_rows(recipe)') == 3)
    c['and weight_equivalent once more, for the book detail - which '
      'wants plain values for JSON, not decorated rows'] = (
        cr.count('weight_equivalent(ing, _convs)') == 1)
    c['not one copy of the weight arithmetic is left in it'] = (
        bool(cr) and 'weight_amount = round' not in cr)
    c['nor the nested helper the book detail used'] = (
        bool(cr) and 'get_weight_equivalent' not in cr)
    c['and get_preferred_weight_conversion is no longer imported '
      'there, because nothing in the file asks it'] = (
        bool(cr) and 'get_preferred_weight_conversion' not in cr)
    for dead in ('conversion_map', 'units_needed', 'conversions_qs'):
        c['and keeps no %s of its own' % dead] = (
            bool(cr) and dead not in cr)

    # ---- THE ENDPOINT
    c['there is an endpoint that returns the recipe as a partial'] = (
        'def recipe_quicklook(' in cr)
    c['it is read-tier, like the page and the PDF it sits beside'] = (
        bool(re.search(
            r"@permission_required\('auth\.can_access_recipes',[^)]*\)\s*"
            r"\ndef recipe_quicklook\(", cr)))
    c['and it is routed under the recipe, beside the PDF'] = (
        "name='recipe_quicklook'" in ur and
        "'recipe/<int:recipe_id>/quick-look/'" in ur)

    # ---- THE RULES ARE IN THE HALF THAT ARRIVES ONCE
    #
    # WCIM's quick view put its stylesheet in the fetched partial,
    # which re-sends it every time a recipe is looked at.
    c['the partial carries no stylesheet - it arrives on every '
      'open'] = (
        bool(part) and '<style>' not in part)
    c['the shell carries them, because it arrives once'] = (
        '<style>' in shell)
    c['and the shell is included exactly once by the planner'] = (
        tpl.count("{% include 'recipe_quicklook_shell.html' %}") == 1)

    # ---- NO PATH SPELLED OUT IN JAVASCRIPT
    c['the shell spells no URL in its JavaScript - the server renders '
      'one onto each trigger'] = (
        bool(shell) and 'quick-look/' not in shell)

    # ---- A TRIGGER IS A LINK THAT STILL WORKS
    #
    # ASKED OF THE ANCHOR, not of the attribute. A page HAVING
    # data-quicklook and the EYE being a link that carries it are
    # different facts, and a button would have satisfied the first.
    c['both eyes on the day card are anchors that also carry '
      'data-quicklook'] = (
        len(re.findall(
            r"<a href=\"\{% url 'view_recipe'[^>]*?data-quicklook=",
            tpl, re.S)) == 2)
    c['and a modified click is let through, so the tab still '
      'works'] = (
        'e.metaKey' in shell and 'e.ctrlKey' in shell)

    # ---- THE HOUSE'S OWN DIALOG, AND NOTHING RESTATED OF IT
    c["the dialog's header is base's .alv-modal-head"] = (
        'alv-modal-head' in part)
    # ASKED OF THE SUBJECT FIRST - an absence in a file that is not
    # there is not this round's doing.
    c['and neither new template redefines a rule base owns'] = (
        bool(shell) and not any(
            re.search(r'(?m)^\s*\.%s\s*\{' % sel, shell)
            for sel in ('modal-overlay', 'modal-content',
                        'alv-modal-head')))

    # ---- AND screen, NOT A BARE max-width
    c['the phone rule names a media type, so it does not also '
      'match print'] = (
        '@media (max-width' not in shell and
        '@media screen and (max-width: 767px)' in shell)

    # ---- NO LITERAL COLOUR IN EITHER NEW TEMPLATE
    #
    # A hex is a colour the standards suites cannot reason about and
    # the dark ground would keep.
    # ASKED OF THE SUBJECT FIRST, for the same reason.
    c['no literal hex colour in the partial or the shell'] = (
        bool(part) and bool(shell) and not (
            re.search(r'#[0-9a-fA-F]{3,8}\b', part) or
            re.search(r'#[0-9a-fA-F]{3,8}\b', shell)))

    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for msg, got in NOW_CLAIMS.items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL - every claim re-asked of the pre-round files')
# ==========================================================================
# THREE OF THE FILES ARE NEW, so the control hands this an empty string
# for each and the claims about them must fail. That is the point: a
# claim that passes against a tree where the thing does not exist is a
# claim about nothing.
BEFORE = dict((p, was(p)) for p in FILES)
for _p in NEW_FILES:
    BEFORE[_p] = ''

WAS_CLAIMS = claims(BEFORE)
held = [m for m, got in WAS_CLAIMS.items() if got]
ok(not held,
   'not one of the %d claims held before this round ran'
   % len(WAS_CLAIMS),
   'these held already, so they are not this round: %r' % (held[:4],))

# AND THE FAULT WAS REALLY THERE - asked of the backup directly, not
# inferred from a claim being false.
OLD_CRUD = T.python_code_only(BEFORE[CRUD], payloads=True)
ok(OLD_CRUD.count('conversion_map') >= 2,
   'CONTROL: recipe_crud held conversion_map in TWO places - the read '
   'was duplicated, which is what the extraction is for',
   'count was %d' % OLD_CRUD.count('conversion_map'))
# THREE, NOT TWO - AND THIS IS THE CHECK THAT FOUND THE THIRD.
#
# The round was written for two copies, because the survey read the two
# functions it had been told about. This line counted them and was
# answered 3: recipe_book_detail had a nested get_weight_equivalent of
# its own, and it was the only one of the three that asked the
# authority. The round was reverted and rewritten for three.
#
# Asking the tree beats reading the part of it you went looking in.
ok(OLD_CRUD.count('weight_amount = round(amount') == 3,
   'CONTROL: and the weight arithmetic was written out THREE times - '
   'the page, the PDF and the book detail',
   'count was %d' % OLD_CRUD.count('weight_amount = round(amount'))
ok('def get_weight_equivalent(ing):' in OLD_CRUD,
   'CONTROL: the third was a nested helper inside recipe_book_detail')
ok('get_preferred_weight_conversion' in OLD_CRUD,
   'CONTROL: and it asked the authority, which is why it was the only '
   'one of the three that was right')
ok('def recipe_quicklook(' not in OLD_CRUD,
   'CONTROL: there was no endpoint')
ok(not os.path.isfile(READ + SUFFIX),
   'CONTROL: and _recipe_read.py has no backup, because it did not '
   'exist to back up')
OLD_TPL = T.code_only(BEFORE[TPL])
ok('data-quicklook' not in OLD_TPL,
   'CONTROL: and nothing on the planner opened a dialog')
ok(OLD_TPL.count("{% url 'view_recipe'") >= 2,
   'CONTROL: the eye was there, and it went to the page')


# ==========================================================================
head('3. THE SAME ANSWER AS THE AUTHORITY, ON A REAL DATABASE')
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
recipe = None
cases = []
if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (Ingredient, MeasurementUnit, Recipe,
                              RecipeCategory, RecipeCourse,
                              RecipeIngredient, RecipeInstruction,
                              UnitConversion)
    from pages.views.recipes._helpers import \
        get_preferred_weight_conversion
    from pages.views.recipes import _recipe_read as RR

    u = User.objects.create_user(username='rd1', password='x',
                                 email='rd1@example.test')
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
    stone = MeasurementUnit.objects.create(
        name='stone', abbreviation='st', unit_type='weight')
    cup = MeasurementUnit.objects.create(
        name='cup', abbreviation='cup', unit_type='volume')
    tbsp = MeasurementUnit.objects.create(
        name='tablespoon', abbreviation='tbsp', unit_type='volume')
    each = MeasurementUnit.objects.create(
        name='each', abbreviation='ea', unit_type='other')
    mil = MeasurementUnit.objects.create(
        name='millilitre', abbreviation='ml', unit_type='volume')

    flour = Ingredient.objects.create(name='Flour')
    sugar = Ingredient.objects.create(name='Sugar')
    lentil = Ingredient.objects.create(name='Lentils')
    onion = Ingredient.objects.create(name='Onion')
    salt = Ingredient.objects.create(name='Salt')

    # THE CASE THAT DECIDES IT, written kg-first on purpose.
    #
    # unique_together on unit_conversions is
    # (from_unit, to_unit, specific_ingredient), so a cup of flour may
    # legally be recorded BOTH as 0.120kg and as 120g. The map key
    # (cup, flour) then holds two candidates, and which one is read
    # decides what the screen says.
    UnitConversion.objects.create(from_unit=cup, to_unit=kilo,
                                  specific_ingredient=flour,
                                  multiplier='0.120')
    UnitConversion.objects.create(from_unit=cup, to_unit=gram,
                                  specific_ingredient=flour,
                                  multiplier='120')
    # The generic cup, the same way, so the fallback path is covered too.
    UnitConversion.objects.create(from_unit=cup, to_unit=kilo,
                                  multiplier='0.240')
    UnitConversion.objects.create(from_unit=cup, to_unit=gram,
                                  multiplier='240')
    # A tablespoon with ONE answer - the undisputed case, which must
    # still come out the same or the extraction has broken the easy path.
    UnitConversion.objects.create(from_unit=tbsp, to_unit=gram,
                                  multiplier='15')
    # A CONVERSION TO A UNIT THAT IS NOT A WEIGHT. Its product is not a
    # weight equivalent, whatever it is called.
    UnitConversion.objects.create(from_unit=each, to_unit=mil,
                                  multiplier='50')
    # AND A WEIGHT UNIT OUTSIDE THE PRIORITY LIST, as the only
    # candidate. get_preferred_weight_conversion can never reach it.
    UnitConversion.objects.create(from_unit=mil, to_unit=stone,
                                  multiplier='0.0002')

    cases = [
        (flour, cup, '10', 'the rival conversions, far enough apart to show'),
        (flour, cup, '1', 'the rival conversions, where the kg rule hides it'),
        (sugar, cup, '10', 'the generic fallback, also rivalled'),
        (lentil, tbsp, '3', 'one answer only - the easy path'),
        (onion, each, '2', 'a conversion to a volume'),
        (salt, mil, '5', 'a weight unit the priority list never asks for'),
        (lentil, gram, '500', 'already a weight'),
        (onion, cup, '0', 'no amount to convert'),
    ]
    recipe = Recipe.objects.create(recipe_name='Every case', servings=5,
                                   author='Maria', prep_time=15,
                                   cook_time=45, is_vegetarian=True)
    recipe.courses.add(RecipeCourse.objects.create(name='Soup',
                                                   display_order=1))
    recipe.categories.add(RecipeCategory.objects.create(name='Greek'))
    for i, (ing, unit, amt, _why) in enumerate(cases):
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=ing, unit=unit, amount=amt,
            ingredient_group='', ingredient_order=i)
    RecipeInstruction.objects.create(recipe=recipe, step_number=1,
                                     instruction_text='Rinse the lentils.')
    RecipeInstruction.objects.create(recipe=recipe, step_number=2,
                                     instruction_text='Simmer 45 minutes.')

    def kg_rule(amount, conversion):
        """The arithmetic, written ONCE here so the three answers below
        differ only in WHICH conversion they chose - which is the thing
        under test. RW-1 is the round that changes this arithmetic."""
        try:
            w = round(amount * float(conversion.multiplier), 1)
        except (TypeError, ValueError):
            return None
        if w == int(w):
            w = int(w)
        if w <= 0:
            return None
        unit = (conversion.to_unit.abbreviation or conversion.to_unit.name)
        if unit == 'kg' and w < 1:
            w = round(w * 1000)
            unit = 'g'
        return '%s%s' % (w, unit)

    def amount_of(ing):
        try:
            return float(ing.amount) if ing.amount else 0
        except (TypeError, ValueError):
            return 0

    def authority(ingredients):
        """get_preferred_weight_conversion, one query at a time."""
        out = []
        for ing in ingredients:
            got = None
            if ing.unit and ing.unit.unit_type != 'weight':
                amount = amount_of(ing)
                if amount > 0:
                    conv = get_preferred_weight_conversion(ing.unit,
                                                           ing.ingredient)
                    if conv:
                        got = kg_rule(amount, conv)
            out.append(got)
        return out

    def old_bulk(ingredients, ordered):
        """The block this round deleted. `ordered` picks view_recipe's
        spelling (it added an .order_by) or recipe_pdf's (it did not)."""
        needed = set()
        for ing in ingredients:
            if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
                needed.add(ing.unit_id)
        qs = UnitConversion.objects.filter(from_unit_id__in=needed) \
            .select_related('from_unit', 'to_unit', 'specific_ingredient')
        if ordered:
            qs = qs.order_by('specific_ingredient', 'from_unit')
        cmap = {}
        for conv in qs:
            ks = (conv.from_unit_id, conv.specific_ingredient_id)
            kg_ = (conv.from_unit_id, None)
            if ks not in cmap:
                cmap[ks] = conv
            if conv.specific_ingredient_id is None and kg_ not in cmap:
                cmap[kg_] = conv
        out = []
        for ing in ingredients:
            got = None
            if ing.unit and ing.unit.unit_type != 'weight':
                amount = amount_of(ing)
                if amount > 0:
                    conv = (cmap.get((ing.unit_id, ing.ingredient_id)) or
                            cmap.get((ing.unit_id, None)))
                    if conv:
                        got = kg_rule(amount, conv)
            out.append(got)
        return out

    rows = RR.ingredient_rows(recipe)
    new = [i.weight_equivalent for i in rows]
    auth = authority(rows)
    page_was = old_bulk(rows, ordered=True)
    pdf_was = old_bulk(rows, ordered=False)

    print('  %-34s %-9s %-9s %-9s' %
          ('case', 'authority', 'RD-1', 'was'))
    for (ing, unit, amt, why), a, n, o in zip(cases, auth, new, page_was):
        print('  %-34s %-9s %-9s %-9s' % (why[:34], a, n, o))
    print('')

    ok(new == auth,
       'the extracted read gives the authority\'s answer on all %d '
       'cases' % len(cases),
       'authority %r\nRD-1      %r' % (auth, new))

    # AND THE COMPARISON COULD HAVE FAILED. A control that cannot fail
    # is not a check - and here the thing that fails it is the code
    # this round deleted.
    ok(page_was != auth,
       'CONTROL: and the block view_recipe carried did NOT - so this is '
       'a repair, not a re-pin',
       'authority %r\nwas       %r' % (auth, page_was))
    ok(pdf_was != auth,
       'CONTROL: nor the one recipe_pdf carried')

    # THE THREE DISAGREEMENTS, each named, so a future reader knows
    # which fault this round fixed and which it left to RW-1.
    disagree = [(w[:30], a, o)
                for (ing, unit, amt, w), a, o in zip(cases, auth, page_was)
                if a != o]
    ok(len(disagree) >= 2,
       'the old block differed on %d of the %d cases'
       % (len(disagree), len(cases)),
       '%r' % (disagree,))
    ok(any(o and o.endswith('ml') for o in page_was),
       'CONTROL: and one of them presented a VOLUME as a weight - the '
       'fault that made this an extraction rather than a third copy',
       'was %r' % (page_was,))

    # THE QUERY COUNT DID NOT GO UP. The bulk map exists because the
    # authority is one query per unit per ingredient; an extraction
    # that kept the answer and lost the speed would be a bad trade.
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    with CaptureQueriesContext(connection) as cap:
        RR.ingredient_rows(recipe)
    n_new = len(cap.captured_queries)
    with CaptureQueriesContext(connection) as cap:
        authority(list(RR.ingredient_rows(recipe)))
    n_auth = len(cap.captured_queries)
    ok(n_new <= 3,
       'and it costs %d quer%s, not one per ingredient'
       % (n_new, 'y' if n_new == 1 else 'ies'))
    ok(n_auth > n_new,
       'CONTROL: the authority itself costs %d, which is why nobody '
       'called it from the page' % n_auth)


# ==========================================================================
head('4. DRIVEN - the dialog, through a real client')
# ==========================================================================
if not django_up or cl is None:
    skip('the driven checks', 'no database')
else:
    from django.contrib.auth.models import User as DUser
    from django.test import Client as DClient
    from django.urls import reverse

    url = reverse('recipe_quicklook', args=[recipe.recipe_id])
    resp = cl.get(url)
    ok(resp.status_code == 200,
       'the endpoint answers 200', 'got %s' % resp.status_code)
    html = resp.content.decode('utf-8') if resp.status_code == 200 else ''

    # THE WHOLE RECIPE, which is what Demetri chose: "the whole recipe,
    # read-only".
    for want, what in [
            ('Every case', 'its name'),
            ('Serves 5', 'what it feeds'),
            ('15 min prep', 'the prep time'),
            ('45 min cook', 'the cook time'),
            ('Maria', 'the author'),
            ('Soup', 'its course'),
            ('Greek', 'its category'),
            ('Vegetarian', 'that it is vegetarian'),
            ('Lentils', 'an ingredient'),
            ('Rinse the lentils.', 'the first step of the method'),
            ('Simmer 45 minutes.', 'and the last'),
            ('Open full recipe', 'and the way out to the page')]:
        ok(want in html, 'the partial carries %s' % what)

    ok('alv-modal-head' in html,
       "and its header is base's, not one of its own")
    ok('<style>' not in html,
       'and no stylesheet rides along on every open')

    # THE WEIGHT IN THE MARKUP, not just in the function. A read that
    # is right and a template that does not print it are different
    # facts.
    shown = re.findall(r'ql-weight">\(([^)]*)\)', html)
    ok('1200g' in shown,
       'the dialog prints the authority\'s weight for ten cups of '
       'flour', 'printed %r' % (shown,))
    ok(not any(s.endswith('ml') for s in shown),
       'and prints no volume as a weight', 'printed %r' % (shown,))

    # AND THE PAGE AGREES WITH IT NOW, which is the whole claim.
    page = cl.get(reverse('view_recipe', args=[recipe.recipe_id]))
    ok(page.status_code == 200,
       'the recipe page still renders after the extraction',
       'got %s' % page.status_code)
    page_html = page.content.decode('utf-8') if page.status_code == 200 \
        else ''
    page_weights = re.findall(r'data-weight-equivalent="([^"]*)"',
                              page_html)
    ok('1200g' in page_weights,
       'and now says the same thing the dialog does',
       'page said %r' % (page_weights,))

    # THE THIRD CALL SITE, DRIVEN. recipe_book_detail returns JSON,
    # so its weight is a value in a payload rather than a string in
    # markup - and it is the one that was already right, so it must
    # still say the same thing it said before.
    import json as _json
    bd = cl.get(reverse('recipe_book_detail', args=[recipe.recipe_id]))
    ok(bd.status_code == 200,
       'the book detail still answers 200 after the extraction',
       'got %s' % bd.status_code)
    if bd.status_code == 200:
        try:
            payload = _json.loads(bd.content.decode('utf-8'))
        except ValueError:
            payload = {}
        bweights = [row.get('weight_equivalent')
                    for row in payload.get('ingredients', [])]
        ok('1200g' in bweights,
           'and gives the same weight the dialog and the page now give',
           'book detail said %r' % (bweights,))
        ok(not any(w and w.endswith('ml') for w in bweights),
           'and no volume among them')

    # A BAD ID IS REFUSED, not rendered empty.
    ok(cl.get(reverse('recipe_quicklook', args=[999999])).status_code
       == 404,
       'a recipe that does not exist is a 404')

    # READ-TIER IS ENFORCED. A dialog that showed a recipe to somebody
    # who may not open its page would be a way ROUND the permission.
    stranger = DUser.objects.create_user(username='nobody', password='x',
                                         email='no@example.test')
    c2 = DClient()
    c2.force_login(stranger)
    ok(c2.get(url).status_code in (302, 403),
       'and somebody without can_access_recipes is refused',
       'got %s' % c2.get(url).status_code)

    # THE TRIGGER IS STILL A LINK. Driven, because the claim is about
    # what the browser would do, not about an attribute.
    plan = cl.get(reverse('meal_planner'))
    ok(plan.status_code == 200,
       'the planner still renders', 'got %s' % plan.status_code)
    ptext = plan.content.decode('utf-8') if plan.status_code == 200 else ''
    ok('quickLookModal' in ptext,
       'and carries the dialog exactly once',
       'found %d' % ptext.count('id="quickLookModal"'))
    ok(ptext.count('id="quickLookModal"') == 1,
       'one dialog, not one per meal')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate,
   'the suite is on the gate')
ok(ME in T.CONVERTED,
   'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS,
   'and the round is in alv_rounds.ROUNDS, newest last',
   'ROUNDS tail %r' % (alv_rounds.ROUNDS[-3:],))
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
for _dep in []:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
ok(_i >= len(alv_rounds.ROUNDS) - 8,
   'and it is among the eight newest, where this push put it',
   'it is at %d of %d' % (_i, len(alv_rounds.ROUNDS)))

# THE SENTINELS NAME THE THING, not a file.
for frag in ('def ingredient_rows(', 'def recipe_quicklook(',
             'data-quicklook'):
    ok(frag in gate,
       'the gate pins %r' % frag)

# EVERY FILE THIS ROUND TOUCHED IS BACKED UP, except the three it
# invented - and the pre-flight enumerates from the disk, so a missing
# backup is a push that cannot be reverted.
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
for p in NEW_FILES:
    ok(os.path.isfile(p),
       'written: %s' % os.path.relpath(p, ROOT))

ok(MARK in read(os.path.join(ROOT, PATCHER)),
   'the patcher dates itself')
ok(MARK in NOW[READ],
   'and so does the module it wrote')

# AND THE PATCHER IS IDEMPOTENT, asked of the tree rather than of a
# promise in a docstring.
ok('already applied' in read(os.path.join(ROOT, PATCHER)),
   'the patcher has an already-applied path')

# ---- AND THE THREE FILES IT INVENTED CAN BE STAGED AND REVERTED
#
# stage_round.py and revert_all.sh both enumerate a round from its
# .bak files, and a file that did not exist has none. PF-2 created
# _recipe_filter.py on 19 October and it shipped only because its name
# was typed on the staging command line - the hand-written list the 17
# October push failed on. A revert would have left it in the tree.
import apply_recipe_modal as PATCH                          # noqa: E402
ok(hasattr(PATCH, 'CREATES'),
   'the patcher DECLARES the files it creates, where the round lives')
declared = set(getattr(PATCH, 'CREATES', ()))
ok(declared == {os.path.relpath(p, ROOT) for p in NEW_FILES},
   'and the declaration is the three files, no more and no fewer',
   'declared %r' % (sorted(declared),))
for rel in sorted(declared):
    ok(os.path.isfile(os.path.join(ROOT, rel)),
       'declared and present: %s' % rel)

stage = read(os.path.join(ROOT, 'stage_round.py'))
ok("getattr(patcher, 'CREATES', ())" in stage,
   'and stage_round ASKS THE PATCHER rather than whoever typed the '
   'command')
ok('CREATES' not in was(os.path.join(ROOT, 'stage_round.py'))
   if os.path.isfile(os.path.join(ROOT, 'stage_round.py') + SUFFIX)
   else False,
   'CONTROL: before this round it could not see a created file at all')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
