# -*- coding: utf-8 -*-
"""test_meal_week.py - round MW-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE WEEK MOVES.

Three things a week can now do, and all three were Demetri's choice out
of a set of options put to him on 19 October:

    COPY THIS WEEK TO...    a date, and every meal lands on the
                            matching weekday of that week with its
                            servings. Nothing stays linked afterwards.

    SAVE THIS WEEK AS A     a name, and the week is kept by WEEKDAY -
    MENU                    day indexes 0 to 6 - so it can be stamped
                            onto a week in a different month.

    APPLY A MENU...         and the Menus are managed in that dialog, a
                            trashcan per row, because release 3 is
                            about meal planning being one screen.

AND COLLISIONS ADD ALONGSIDE, AND SAY SO FIRST. Nothing is replaced and
nothing is skipped. The dialog asks the server what the target week
already holds BEFORE the button can be pressed, and says it.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The five views, the five routes, the three dialogs,
      the More menu, and the one new block of CSS.

  2   THE CONTROL. Every source claim re-asked of the .bak_mealweek
      backups, where every one of them must FAIL. A claim that passes
      on the pre-round tree is a claim about nothing.

  3   THE BEHAVIOUR, DRIVEN FOR REAL, against a live database. This is
      the register that matters. "The source says copy_week_rows" is a
      claim about text; "a leftover copied without its parent is
      dropped rather than charging the new week for a meal in the old
      one" is a claim about the application, and it is the one that
      would cost Demetri money on a shopping list.

  4   THE TWO PAGE COUNTS, which this round moves 31 -> 32 - the
      SECOND move in two days, and the reason is in section 4.

  5   NO MIGRATION, asked of the tree rather than asserted. Menu and
      MenuItem shipped with 0100 in push 1.

  6   WIDE FROM BIRTH. Every page in both template roots asked whether
      it has grown a second copy of these dialogs, or a second element
      answering to base's #actionMoreBtn.

  7   Scope, registration and the gate.

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
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealweek'
ME = 'test_meal_week.py'
PATCHER = 'apply_meal_week.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MW-1, 19 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
MM = os.path.join(ROOT, 'test_more_menu.py')
LM = os.path.join(ROOT, 'test_last_menus.py')

FILES = (VIEW, URLS, TPL, MM, LM)

VIEWS_ADDED = ('meal_week_preview', 'copy_meal_week', 'save_menu',
               'apply_menu', 'delete_menu')
HELPERS_ADDED = ('monday_of', 'week_entries', 'day_label', 'week_label',
                 'copy_week_rows')
# CP-2, 21 Oct 2026 - TWO, not three. The three were reachable
# only on a phone: base hides .action-more-wrapper above 768px,
# so a feature whose only control lives in that menu cannot be
# used on a desktop at all. Demetri: "I don't see Copy this week
# nor save this week as a menu???"
#
# Save-as and Apply are two halves of one idea - a named set of
# meals kept by weekday - and live in one dialog now, which also
# gives Delete a home instead of a trashcan buried inside Apply.
DIALOGS = ('copyRangeModal', 'menusModal')

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


def claims(text):
    """Every source claim MW-1 makes, written once and asked twice.

    ASKED OF THE CODE, NOT OF THE FILE. The patcher's prose names the
    retired Duplicate screen, C13, C19, E29 and the decisions behind
    all three dialogs, and the round's own comments in the view and the
    template do the same: to a substring search a comment about a thing
    is the thing, which cost three wrong checks in MP-1, two in MD-1,
    one wrong refusal in MD-1's patcher - and one in THIS round's, where
    the gate that forbids %-d refused the round over day_label's
    docstring explaining why it does not use %-d.
    """
    c = {}
    vcode = T.python_code_only(text[VIEW])
    ucode = T.python_code_only(text[URLS])
    tcode = T.code_only_js(text[TPL])
    # THE CSS, COMMENT-FREE, AND IT HAD TO BE. The first cut of the
    # three removal claims below read the raw file and failed on this
    # round's own prose: the comment that explains why #recipeList and
    # .recipe-option > div were deleted NAMES them both. A comment
    # about a thing is the thing, and this is the fifth round to pay
    # for that sentence.
    ccss = T.code_only(text[TPL])

    # ---- 1. the five views and the five helpers
    for fn in VIEWS_ADDED:
        c['%s is a view' % fn] = 'def %s(request):' % fn in vcode
    for fn in HELPERS_ADDED:
        c['%s is a helper' % fn] = ('def %s(' % fn) in vcode

    # ---- 2. the tiers. A count is a read; a change is an edit.
    #         Asked of the decorator stack above each def, not of the
    #         module - every one of these decorators appears a dozen
    #         times in this file and only the position means anything.
    def tier(fn):
        i = vcode.find('def %s(request):' % fn)
        return vcode[max(0, i - 260):i] if i >= 0 else ''

    c['meal_week_preview is READ-tier - it only counts'] = (
        'can_access_recipes' in tier('meal_week_preview')
        and 'can_edit_recipes' not in tier('meal_week_preview'))
    # PAIRED WITH THE PRESENCE, so the control section can refuse it.
    # An absence on its own is true of every tree that never had the
    # thing, which is every tree before this round.
    c['  and is NOT require_POST - a count is a GET'] = (
        'def meal_week_preview(request):' in vcode
        and 'require_POST' not in tier('meal_week_preview'))
    for fn in ('copy_meal_week', 'save_menu', 'apply_menu', 'delete_menu'):
        c['%s is EDIT-tier' % fn] = 'can_edit_recipes' in tier(fn)
        c['  and %s is POST-only' % fn] = 'require_POST' in tier(fn)

    # ---- 3. the five routes
    for fn in VIEWS_ADDED:
        c['  the route %s is registered' % fn] = (
            "views.%s, name='%s'" % (fn, fn)) in ucode

    # ---- 4. what makes a copy correct
    c['a copy is ATOMIC'] = 'with transaction.atomic():' in vcode.split(
        'def copy_meal_week')[-1].split('def ')[0]
    c['  parents are placed before leftovers'] = (
        'if e.leftover_of_id:' in vcode and 'mapping[e.meal_entry_id]' in vcode)
    c['  and a leftover re-points at the COPY of its parent'] = (
        'parent = mapping.get(e.leftover_of_id)' in vcode)
    c['  an orphan leftover is DROPPED, not copied flat'] = (
        'if parent is None:' in vcode)
    # SCOPED TO copy_week_rows. add_meal_entry has taken the tail of a
    # day this way since MN-1, so the module-wide reading was true
    # before this round and the control section said so.
    c['  the copy lands AFTER what the day holds, not interleaved'] = (
        "Max('sort_order')" in vcode.split('def copy_week_rows')[-1]
        .split('@login_required')[0])
    c['  a week cannot be copied onto itself'] = (
        'cannot be copied onto itself' in vcode)

    # ---- 5. what makes a menu a template and not a week
    # MN-2, 21 Oct 2026 - FROM THE START OF THE RANGE, not from a
    # Monday. MN-1 measured the offset from the week on screen because
    # the week on screen was the only thing a menu could be. The
    # column always said otherwise - "0 is the first day of the menu,
    # not a weekday" - and now the view agrees with it.
    c['a menu stores a DAY OFFSET, computed from the start of the range'] = (
        "day_index=(e.date - start).days" in vcode)
    c['  a leftover is NOT saved into a menu'] = (
        'if e.leftover_of_id:' in vcode.split('def save_menu')[-1]
        .split('def ')[0])
    c['  a menu needs a name'] = 'A menu needs a name.' in vcode
    c['  and the name is unique, case-blind'] = (
        'name__iexact=name' in vcode)
    c['applying reads the day offset back'] = (
        'timedelta(days=it.day_index)' in vcode)
    # MN-2, 21 Oct 2026 - THE CEILING MOVED AND THE RULE DID NOT. A
    # menu was 0..6 by construction; it is 0..91 now, and an offset
    # past the end is still DROPPED rather than wrapped - a row that
    # says a year would otherwise land a year away.
    c['  and a day offset past the ceiling is dropped, not wrapped'] = (
        'if not 0 <= it.day_index < MENU_MAX_DAYS:' in vcode)
    c['  the ceiling is a quarter, declared where the rule lives'] = (
        'MENU_MAX_DAYS = 92' in vcode)
    c['  and a menu lands where you say, not on the week on screen'] = (
        "onto = week_of(request.POST.get('onto'), week)" in vcode
        and 'when = onto + timedelta(days=it.day_index)' in vcode)
    c['deleting a menu leaves the meals it stamped'] = (
        'are still there' in vcode)

    # ---- 6. the planner hands the dialog its menus, counted in ONE query
    c['the planner context carries the menus'] = "'menus':" in vcode
    # MN-2, 21 Oct 2026 - AND ITS LENGTH, IN THE SAME annotate. The
    # Apply half says which days a menu will cover; it works that out
    # in the page from a number the planner already has. A second
    # annotate, or a count per row, would be E29's fault coming back
    # on the screen MW-1 took it off.
    c['  counted by annotate, not once per row'] = (
        "item_count=Count('items')," in vcode
        and "span_days=Coalesce(Max('items__day_index'), -1) + 1" in vcode
        and vcode.count('Menu.objects.annotate(') == 1)

    # ---- 7. the three dialogs, and one control each
    for mid in DIALOGS:
        c['%s is on the planner' % mid] = (
            tcode.count('id="%s"' % mid) == 1)
    # CP-2, 21 Oct 2026 - THE BAR, AND THE MENU AS A TWIN. The menu
    # is a phone control: base hides it above 768px. A feature whose
    # only control lives there is a feature nobody can reach on a
    # desktop, which is what these two were for two days.
    c['the two controls live on the bar'] = (
        tcode.count('id="actionMoreBtn"') == 1
        and tcode.count('data-menu-panel') == 1
        and all('data-target="#%s"' % m in
                tcode[tcode.index('page-action-buttons'):
                      tcode.index('action-more-menu')]
                for m in DIALOGS))
    c['  and the page writes NO handler for it - base binds it'] = (
        tcode.count('id="actionMoreBtn"') == 1
        and "getElementById('actionMoreBtn')" not in tcode)
    # TWO EACH, AND THAT IS THE POINT - CP-2, 21 Oct 2026. One in
    # the bar for a desktop and one in the More menu for a phone,
    # because base hides each of those at the other's width. Exactly
    # one is reachable at a time; test_copy_menus measures that over
    # all 32 bars in the application, in both directions.
    for mid in DIALOGS:
        c['  two controls target %s - bar and menu' % mid] = (
            len(re.findall(r'<(?:button|a)\b[^>]*data-target="#%s"' % mid,
                           tcode)) == 2)

    # ---- 8. SAY SO FIRST, which is half of the collision decision
    c['the copy dialog asks the server what is already there'] = (
        'meal_week_preview' in tcode and 'function copyPreview()' in tcode)
    # CP-2, 21 Oct 2026 - renamed with the dialog, and the question
    # it asks is a RANGE now rather than a week. The decision it
    # serves is unchanged and is the reason this claim exists: "add
    # alongside, AND SAY SO FIRST".
    c['  and the Copy button starts DISABLED'] = (
        'id="cpGo" disabled' in tcode)
    c['  and the dialog says the copy is added alongside'] = (
        'added alongside' in tcode)
    # SL-4: a browser dialog blocks every event after it. Paired with
    # the function, so the claim is about this round's JavaScript and
    # not about a page that had none.
    c['  it says it in the page, not in an alert'] = (
        'function copyPreview()' in tcode and 'alert(' not in tcode)

    # ---- 9. and the shapes that break a page rather than a feature
    # CP-2, 21 Oct 2026 - the apply form is inside menusModal now,
    # and the delete form is still its own top-level <form hidden>.
    # The claim is unchanged in substance: a form cannot nest, and a
    # delete nested inside apply would submit the wrong action.
    c['the delete form is OUTSIDE the apply form'] = (
        tcode.find('id="deleteMenuForm"') > tcode.find('id="menusModal"')
        and '</form>' in tcode[tcode.find('id="menusModal"'):
                               tcode.find('id="deleteMenuForm"')])
    c['the trashcan stops the click selecting the row'] = (
        'ev.stopPropagation();' in tcode)
    c['the menu rows have a visible selected state'] = (
        '.menu-option.selected {' in ccss)
    c['  and it is two signals, not one'] = (
        'box-shadow: 0 0 0 2px var(--alv-accent-ring);' in ccss)
    # EVERY RULE THIS ROUND WRITES, AND NOTHING ELSE - from .menu-list
    # to .empty-day, which is where the round's insert ends. Sliced
    # rather than read whole, because the page has carried colour
    # literals in two places since before MC-2 and this claim is about
    # what MW-1 adds. It is false on the pre-round tree because the
    # slice does not exist there, which is what the control needs.
    block = (ccss.split('.menu-list {')[1].split('.empty-day {')[0]
             if '.menu-list {' in ccss and '.empty-day {' in ccss else None)
    c['no colour literal enters the page'] = bool(block) and not re.search(
        r'(?m)^\s*(background|border-color|box-shadow|color)\s*:'
        r'[^;]*#[0-9a-fA-F]{3,6}', block)
    # CP-2, 21 Oct 2026 - the empty state can point UP now rather
    # than at a dialog the reader cannot see from here: Save and
    # Apply are two sections of one dialog, so the control that makes
    # a menu is eighty pixels above the sentence that names it.
    #
    # MN-2, 21 Oct 2026 - AND THE CONTROL IS NOT CALLED THAT ANY MORE.
    # Saving takes a range, so the button says "Save these days" and
    # this sentence says the same words it does. The claim is still
    # that the empty state names the real control; only the control
    # was renamed.
    c['the Apply dialog says where menus come from when there are none'] = (
        'Save these days</strong> above' in tcode)

    # ---- 10. THE SECOND SUBJECT. Demetri was offered this three ways
    #          on 19 Oct and chose to fold it into this round, so these
    #          checks sit in this suite rather than in one of their own.
    #          .recipe-option had NO RULE in this file, in base, or in
    #          any backup of this template or its ancestor: the picker
    #          has added a .selected class since it was written and
    #          nothing drew it.
    c['the picker row is laid out at all'] = '.recipe-option {' in ccss
    c['  and its selected state is visible'] = (
        '.recipe-option.selected {' in ccss)
    c['  two signals there as well, not one'] = (
        ccss.count('box-shadow: 0 0 0 2px var(--alv-accent-ring);') == 2)
    c['the picker list is capped and scrolls'] = (
        '#pickerList {' in ccss and 'max-height: 320px;' in ccss)
    # THE REMOVALS. Three rules for selectors nothing matches, all
    # three inside the under-768px block - which is to say all three
    # were dead on a phone, where they were the only ones.
    c['#recipeList is gone - MN-1 renamed that list'] = (
        '#recipeList' not in ccss)
    # SCOPED TO THE PHONE BLOCK. Both dead rules lived under 768px and
    # that is where this round deleted them. The first cut asked the
    # whole stylesheet and failed as soon as PK-1 - a later round in
    # the same push - added a LIVE `.recipe-option > div { min-width:
    # 0 }` at the top level, for a card in a 240px grid column whose
    # name has to wrap. Same selector, different rule, different
    # block, and the claim was never about it.
    # THE SPELLING THE FILE USES. `@media screen and (max-width:
    # 768px)` - the first cut of this split looked for `@media
    # (max-width: 768px)`, found nothing, and fell back to the whole
    # stylesheet, which is the bug it was written to avoid. A fallback
    # that silently widens a scope is worse than no scope at all.
    #
    # AND FROM THE FIRST OCCURRENCE, NOT THE LAST. [-1] took the slice
    # after the LAST 768px block - there are two, and the rules this
    # round deleted were in the first. A scope that silently lands on
    # the wrong block is the same fault as a fallback that silently
    # widens one.
    PHONE_AT = '@media screen and (max-width: 768px)'
    phone = ccss.split(PHONE_AT, 1)[1] if PHONE_AT in ccss else ''
    # PAIRED, like every other absence in this dict. "The phone block
    # exists" was true before this round and the control section said
    # so - correctly, and that is the register working. What is this
    # round's is that the block names #pickerList, which is what MN-1
    # renamed #recipeList to and what this round corrected here.
    c['the phone block is where those rules lived'] = (
        bool(phone) and '#pickerList {' in phone)
    c['.recipe-option > div is gone from the phone block'] = (
        '.recipe-option > div' not in phone)
    c['  and .recipe-option img is KEPT there - it matches'] = (
        '.recipe-option img {' in phone)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
# A CLAIM THAT PASSES ON THE PRE-ROUND TREE IS A CLAIM ABOUT NOTHING.
# This is the register the 17 October push failed on: it shipped a suite
# whose control section could not run, so nobody knew the claims were
# vacuous until the round after it.
WASC = claims(dict((p, was(p)) for p in FILES))
# NOTHING IS EXCLUDED BY NAME. The first cut of this section carried a
# line that dropped one tautology from the list, and a control with an
# exception in it is a control somebody will widen - MH-2's absence
# gate taught that two days ago. Every absence claim above is instead
# PAIRED with the presence that makes it mean something, so all 65 are
# false on the pre-round tree and this list is simply empty.
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
ok(not leaked,
   'not one of the %d claims above was already true before MW-1'
   % len(NOW_CLAIMS), '\n'.join(leaked))
ok(len(NOW_CLAIMS) >= 60,
   '  and there are %d of them' % len(NOW_CLAIMS), len(NOW_CLAIMS))


# ==========================================================================
head('3. THE BEHAVIOUR, DRIVEN FOR REAL')
# ==========================================================================
# THIS IS THE REGISTER THAT MATTERS. "The source says copy_week_rows"
# is a claim about text. "A leftover copied without its parent is
# dropped, so the shopping list does not charge the new week for a meal
# in the old one" is a claim about the application, and it is the one
# that would cost Demetri money at the till.
django_up = False
try:
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.EMAIL_BACKEND = \
        'django.core.mail.backends.locmem.EmailBackend'
    dj_settings.DEBUG = True           # connection.queries needs it
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    # QUIET THE 400s. Section 3a asks the preview route five junk
    # dates on purpose and every refusal makes Django's own
    # django.request logger print `WARNING ... Bad Request`. Those are
    # the checks PASSING, and five warning lines in the middle of a
    # green run is the kind of noise that makes a gate harder to read
    # - which is the opposite of what the numbering Demetri asked for
    # on 1 October was for.
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    _buf = io.StringIO()
    call_command('migrate', run_syncdb=True, verbosity=0, stdout=_buf)
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    import datetime as _dt
    import json as _json
    from django.contrib.auth.models import User, Permission
    from django.db import connection, reset_queries
    from django.test import Client
    from pages.models import MealEntry, Menu, MenuItem, Recipe

    editor = User.objects.create_user(username='mw_edit', password='x',
                                      email='mw1@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        editor.user_permissions.add(
            Permission.objects.get(codename=codename))
    reader = User.objects.create_user(username='mw_read', password='x',
                                      email='mw2@example.test')
    reader.user_permissions.add(
        Permission.objects.get(codename='can_access_recipes'))

    cl = Client()
    cl.force_login(editor)
    ro = Client()
    ro.force_login(reader)

    # TWO MONDAYS AND A WEDNESDAY, in two different months, because a
    # Menu that could only be applied inside the month it was saved in
    # would be a week and not a menu.
    SRC = _dt.date(2026, 10, 19)          # Monday
    DST = _dt.date(2026, 11, 23)          # Monday, five weeks on
    DST_WED = _dt.date(2026, 11, 25)      # a Wednesday in that week

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)
    pie = Recipe.objects.create(recipe_name='Fish pie', servings=4)

    def entry(d, recipe=None, note='', servings=4, order=0, parent=None):
        return MealEntry.objects.create(
            date=d, recipe=recipe, note=note, servings=servings,
            sort_order=order, leftover_of=parent, created_by=editor)

    def on(d):
        return list(MealEntry.objects.filter(date=d)
                    .order_by('sort_order', 'meal_entry_id'))

    def post(url, data, client=None):
        return (client or cl).post(url, data)

    def clear():
        MealEntry.objects.all().delete()
        Menu.objects.all().delete()

    PREVIEW = '/meal_plans/week_preview/'
    COPY = '/meal_plans/copy_week/'
    SAVE = '/meal_plans/menus/save/'
    APPLY = '/meal_plans/menus/apply/'
    DELETE = '/meal_plans/menus/delete/'

    # ----------------------------------------------------------------
    head('3a. the preview counts what is there, and says so FIRST')
    # ----------------------------------------------------------------
    clear()
    entry(SRC, soup, servings=6, order=1)
    entry(SRC + _dt.timedelta(days=2), stew, servings=2, order=1)
    entry(SRC + _dt.timedelta(days=2), pie, servings=4, order=2)

    r = cl.get(PREVIEW + '?week=' + SRC.strftime('%Y-%m-%d'))
    ok(r.status_code == 200, 'GET the preview is 200', r.status_code)
    d = _json.loads(r.content.decode('utf-8'))
    ok(d.get('success') is True, '  it answers success')
    ok(d.get('meals') == 3, '  3 meals on that week', d.get('meals'))
    ok(d.get('days_with_meals') == 2, '  on 2 days',
       d.get('days_with_meals'))
    ok(d.get('week') == SRC.strftime('%Y-%m-%d'),
       '  and the week it answers for is the Monday', d.get('week'))

    # ANY DAY OF THE WEEK IS THE WEEK. The dialog's date box takes a
    # date, not a Monday, and the help text under it says so.
    r = cl.get(PREVIEW + '?week=' + DST_WED.strftime('%Y-%m-%d'))
    d = _json.loads(r.content.decode('utf-8'))
    ok(d.get('week') == DST.strftime('%Y-%m-%d'),
       '  a Wednesday is answered as its Monday', d.get('week'))
    ok(d.get('meals') == 0, '  and that week is empty', d.get('meals'))

    # A BAD DATE IS A 400 WITH A SENTENCE, not a 500. Every planner
    # route in this module has taken a junk ?week= since MN-1 and this
    # one is asked the same question.
    for bad in ('', '?week=', '?week=nope', '?week=2026-13-45',
                '?week=99999-01-01'):
        r = cl.get(PREVIEW + bad)
        ok(r.status_code in (200, 400),
           '  the preview survives %r' % bad, r.status_code)
        if r.status_code == 400:
            ok('error' in _json.loads(r.content.decode('utf-8')),
               '    and says what was wrong')

    # READ-TIER CAN COUNT. A count is a read, and the dialog that does
    # the counting is only built for an editor - but the ROUTE must not
    # be the thing that decides that.
    r = ro.get(PREVIEW + '?week=' + SRC.strftime('%Y-%m-%d'))
    ok(r.status_code == 200, '  a read-tier user may count a week',
       r.status_code)

    # ----------------------------------------------------------------
    head('3b. a copy lands on the matching weekday, with its servings')
    # ----------------------------------------------------------------
    r = post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                    'to_week': DST_WED.strftime('%Y-%m-%d')})
    ok(r.status_code == 302, 'the copy redirects', r.status_code)
    ok(DST.strftime('%Y-%m-%d') in r['Location'],
       '  to the week it landed on', r['Location'])

    ok(len(on(DST)) == 1, 'the Monday of the new week has 1 meal',
       len(on(DST)))
    ok(on(DST)[0].recipe_id == soup.recipe_id,
       '  and it is the Monday recipe', on(DST)[0].recipe)
    ok(on(DST)[0].servings == 6,
       '  with the servings it was cooked for, not the recipe yield',
       on(DST)[0].servings)
    wed = on(DST + _dt.timedelta(days=2))
    ok(len(wed) == 2, 'the Wednesday has both of its meals', len(wed))
    ok([e.recipe_id for e in wed] == [stew.recipe_id, pie.recipe_id],
       '  in the order they were put there',
       [e.recipe.recipe_name for e in wed])
    # AND NOTHING IS LINKED AFTERWARDS. "Nothing linked" was the
    # decision: this is a copy, not a subscription. Changing the new
    # week must not reach back into the old one.
    ok(all(e.leftover_of_id is None for e in on(DST) + wed),
       '  and nothing on the new week points at the old one')
    ok(len(on(SRC)) == 1 and len(on(SRC + _dt.timedelta(days=2))) == 2,
       '  the week copied FROM is untouched')

    # ----------------------------------------------------------------
    head('3c. ADD ALONGSIDE - nothing replaced, nothing skipped')
    # ----------------------------------------------------------------
    # THE DECISION, AND THE REASON THE OTHER TWO WERE REJECTED.
    # Replacing is the only one of the three that can destroy
    # something kept, and that is exactly what C13 did when changing a
    # plan's dates dropped the meals outside the new range. Skipping
    # loses nothing either, but leaves a week that is neither the copy
    # nor what was there.
    clear()
    entry(SRC, soup, servings=6, order=1)
    sitting = entry(DST, pie, servings=4, order=1)

    post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                'to_week': DST.strftime('%Y-%m-%d')})
    rows = on(DST)
    ok(len(rows) == 2, 'a day that had a meal and gains one has TWO',
       len(rows))
    ok(rows[0].meal_entry_id == sitting.meal_entry_id,
       '  the one that was there is still there, and still first',
       rows[0].recipe)
    ok(rows[1].recipe_id == soup.recipe_id,
       '  and the copy is behind it, not interleaved', rows[1].recipe)
    ok(rows[1].sort_order > rows[0].sort_order,
       '  by sort_order and not by luck',
       (rows[0].sort_order, rows[1].sort_order))
    ok(MealEntry.objects.filter(meal_entry_id=sitting.meal_entry_id)
       .exists(), '  and NOTHING was deleted to make room')

    # AND THE DIALOG SAYS SO BEFORE THE BUTTON. This is the half of
    # the decision that lives in the browser, and the route that
    # serves it is what makes it possible.
    d = _json.loads(cl.get(PREVIEW + '?week=' + DST.strftime('%Y-%m-%d'))
                    .content.decode('utf-8'))
    ok(d['meals'] == 2, '  the preview can see both of them', d['meals'])

    # ----------------------------------------------------------------
    head('3d. A LEFTOVER FOLLOWS ITS PARENT, or it is dropped')
    # ----------------------------------------------------------------
    # THE ONE THAT WOULD HAVE COST MONEY. leftover_of points at the
    # meal a leftover came from, and MealEntry.counts_on_shopping_list
    # returns False for it. Copied FLAT, the new week's leftover would
    # point at a meal in the OLD week - which still reads as free, so
    # nothing would look wrong, and the parent it was free because of
    # would never be shopped for on the new week.
    clear()
    parent = entry(SRC, soup, servings=6, order=1)
    left = entry(SRC + _dt.timedelta(days=1), soup, servings=6, order=1,
                 parent=parent)
    ok(left.counts_on_shopping_list is False,
       'a leftover costs nothing on the shopping list')

    post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                'to_week': DST.strftime('%Y-%m-%d')})
    new_parent = on(DST)[0]
    new_left = on(DST + _dt.timedelta(days=1))[0]
    ok(new_left.leftover_of_id == new_parent.meal_entry_id,
       'the copied leftover points at the COPY of its parent',
       new_left.leftover_of_id)
    ok(new_left.leftover_of_id != parent.meal_entry_id,
       '  and NOT back into the week it was copied from')
    ok(new_parent.counts_on_shopping_list is True
       and new_left.counts_on_shopping_list is False,
       '  so the new week is shopped for exactly once')

    # AN ORPHAN LEFTOVER IS DROPPED. A week whose Monday parent is
    # outside it - a leftover of last Sunday's roast, say - cannot be
    # copied meaningfully: a leftover of nothing is a row that buys
    # nothing and says nothing.
    clear()
    outside = entry(SRC - _dt.timedelta(days=1), soup, servings=6, order=1)
    entry(SRC, soup, servings=6, order=1, parent=outside)
    entry(SRC, pie, servings=4, order=2)
    post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                'to_week': DST.strftime('%Y-%m-%d')})
    rows = on(DST)
    ok(len(rows) == 1, 'a leftover whose parent is outside the week is '
                       'DROPPED', [str(e) for e in rows])
    ok(rows[0].recipe_id == pie.recipe_id,
       '  and the real meal beside it still copied', rows[0].recipe)
    ok(MealEntry.objects.filter(
        meal_entry_id=outside.meal_entry_id).exists(),
       '  and the parent outside the week was not touched')

    # ----------------------------------------------------------------
    head('3e. the copies that must REFUSE')
    # ----------------------------------------------------------------
    clear()
    entry(SRC, soup, order=1)
    before_n = MealEntry.objects.count()

    r = post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                    'to_week': SRC.strftime('%Y-%m-%d')})
    ok(r.status_code == 302 and MealEntry.objects.count() == before_n,
       'a week cannot be copied onto itself', MealEntry.objects.count())
    # AND A DAY OF THE SAME WEEK IS THE SAME WEEK. The box takes a
    # date, so the check has to be made on the Mondays and not on what
    # was typed.
    r = post(COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                    'to_week': (SRC + _dt.timedelta(days=4))
                    .strftime('%Y-%m-%d')})
    ok(MealEntry.objects.count() == before_n,
       '  and neither can a Friday of that same week',
       MealEntry.objects.count())

    r = post(COPY, {'from_week': DST.strftime('%Y-%m-%d'),
                    'to_week': SRC.strftime('%Y-%m-%d')})
    ok(MealEntry.objects.count() == before_n,
       'an empty week refuses to be copied, rather than copying nothing',
       MealEntry.objects.count())

    for junk, why in (({}, 'nothing at all'),
                      ({'from_week': 'nope', 'to_week': 'nope'},
                       'two junk weeks'),
                      ({'from_week': SRC.strftime('%Y-%m-%d')},
                       'no week to copy TO'),
                      ({'to_week': DST.strftime('%Y-%m-%d')},
                       'no week to copy FROM')):
        r = post(COPY, junk)
        ok(r.status_code == 302, 'a copy with %s redirects, it does not '
           '500' % why, r.status_code)
    ok(MealEntry.objects.count() == before_n,
       '  and not one of them wrote a row', MealEntry.objects.count())

    r = cl.get(COPY)
    ok(r.status_code == 405, 'the copy route refuses a GET', r.status_code)

    # ----------------------------------------------------------------
    head('3f. a week saved as a Menu is kept by WEEKDAY, not by date')
    # ----------------------------------------------------------------
    # THE WHOLE REASON Menu IS A SEPARATE TABLE. MN-1 gave MenuItem a
    # day_index and not a date precisely so that a week saved in
    # October can be stamped onto a week in December, and this is the
    # check that holds it to that.
    clear()
    entry(SRC, soup, servings=6, order=1)                      # Monday
    entry(SRC + _dt.timedelta(days=3), stew, servings=2, order=1)  # Thu
    entry(SRC + _dt.timedelta(days=6), pie, note='', servings=4, order=1)
    entry(SRC + _dt.timedelta(days=6), None, note='Eat out', order=2)

    r = post(SAVE, {'week': SRC.strftime('%Y-%m-%d'),
                    'name': 'The usual rotation'})
    ok(r.status_code == 302, 'saving a menu redirects', r.status_code)
    menu = Menu.objects.filter(name='The usual rotation').first()
    ok(menu is not None, 'the menu exists, under the name that was typed')
    items = list(menu.items.all())
    ok(len(items) == 4, '  with all four of the week\'s rows', len(items))
    ok([i.day_index for i in items] == [0, 3, 6, 6],
       '  on day indexes 0, 3, 6 and 6 - not dates',
       [i.day_index for i in items])
    ok(all(0 <= i.day_index <= 6 for i in items),
       '  and every one of them inside 0..6')
    ok([i.servings for i in items] == [6, 2, 4, 4],
       '  servings carried across', [i.servings for i in items])
    ok(items[3].recipe_id is None and items[3].note == 'Eat out',
       '  and a note is a row too - it is a planned night',
       (items[3].recipe_id, items[3].note))
    ok(menu.created_by_id == editor.id,
       '  and the menu knows who made it', menu.created_by_id)

    # A LEFTOVER IS NOT SAVED. MenuItem has no leftover_of, which is
    # right: a leftover is a consequence of a particular week, not
    # something anybody plans five weeks ahead.
    clear()
    p2 = entry(SRC, soup, servings=6, order=1)
    entry(SRC + _dt.timedelta(days=1), soup, servings=6, order=1, parent=p2)
    post(SAVE, {'week': SRC.strftime('%Y-%m-%d'), 'name': 'Just the roast'})
    m2 = Menu.objects.get(name='Just the roast')
    ok(m2.items.count() == 1, 'a leftover is NOT saved into a menu',
       m2.items.count())
    ok(m2.items.first().day_index == 0,
       '  and the meal it came from is', m2.items.first().day_index)

    # ----------------------------------------------------------------
    head('3g. the saves that must REFUSE')
    # ----------------------------------------------------------------
    n_menus = Menu.objects.count()
    for data, why in (
            ({'week': SRC.strftime('%Y-%m-%d'), 'name': ''},
             'a menu with no name'),
            ({'week': SRC.strftime('%Y-%m-%d'), 'name': '    '},
             'a menu named with spaces'),
            ({'week': SRC.strftime('%Y-%m-%d')}, 'a menu with no name at all'),
            ({'name': 'No week'}, 'a save with no week'),
            ({'week': 'nope', 'name': 'Bad week'}, 'a save with a junk week'),
            ({'week': DST.strftime('%Y-%m-%d'), 'name': 'Empty week'},
             'a save of a week with nothing on it')):
        r = post(SAVE, data)
        ok(r.status_code == 302 and Menu.objects.count() == n_menus,
           '%s is refused' % why, Menu.objects.count())

    # THE NAME IS UNIQUE, CASE-BLIND, because the name is how you tell
    # two of them apart in the Apply list and nowhere else.
    r = post(SAVE, {'week': SRC.strftime('%Y-%m-%d'),
                    'name': 'JUST THE ROAST'})
    ok(Menu.objects.count() == n_menus,
       'a name that differs only in case is refused',
       [m.name for m in Menu.objects.all()])
    # AND A NAME IS TRIMMED, so two that LOOK the same are the same.
    r = post(SAVE, {'week': SRC.strftime('%Y-%m-%d'),
                    'name': '  Just the roast  '})
    ok(Menu.objects.count() == n_menus,
       '  and so is one that differs only in spaces',
       [m.name for m in Menu.objects.all()])

    r = cl.get(SAVE)
    ok(r.status_code == 405, 'the save route refuses a GET', r.status_code)

    # ----------------------------------------------------------------
    head('3h. a Menu stamps onto ANY week, in any month')
    # ----------------------------------------------------------------
    clear()
    entry(SRC, soup, servings=6, order=1)                          # Mon
    entry(SRC + _dt.timedelta(days=3), stew, servings=2, order=1)  # Thu
    post(SAVE, {'week': SRC.strftime('%Y-%m-%d'), 'name': 'Two nights'})
    menu = Menu.objects.get(name='Two nights')
    MealEntry.objects.all().delete()

    r = post(APPLY, {'week': DST_WED.strftime('%Y-%m-%d'),
                     'menu_id': menu.menu_id})
    ok(r.status_code == 302, 'applying a menu redirects', r.status_code)
    ok(DST.strftime('%Y-%m-%d') in r['Location'],
       '  to the week it landed on', r['Location'])
    ok(len(on(DST)) == 1, 'day 0 of the menu is the Monday of that week',
       len(on(DST)))
    ok(on(DST)[0].recipe_id == soup.recipe_id,
       '  and it is the right recipe', on(DST)[0].recipe)
    ok(on(DST)[0].servings == 6,
       '  with the servings the menu kept', on(DST)[0].servings)
    ok(len(on(DST + _dt.timedelta(days=3))) == 1,
       'day 3 is the Thursday', len(on(DST + _dt.timedelta(days=3))))
    # FIVE WEEKS AND A MONTH BOUNDARY APART, which is the point.
    ok(SRC.month != DST.month,
       '  and the menu was saved in a different month from the one it '
       'was applied to', (SRC.month, DST.month))
    ok(menu.items.count() == 2,
       'and the MENU is unchanged - a stamp is not a move',
       menu.items.count())

    # APPLYING ADDS ALONGSIDE TOO. Same decision, same reason.
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(len(on(DST)) == 2, 'applying the same menu twice gives two meals',
       len(on(DST)))
    ok(on(DST)[0].sort_order < on(DST)[1].sort_order,
       '  the second behind the first',
       [e.sort_order for e in on(DST)])

    # A DAY OFFSET OUTSIDE THE MENU IS DROPPED, NOT WRAPPED.
    #
    # MN-2, 21 Oct 2026 - THE CEILING MOVED AND THE RULE DID NOT. This
    # read 9 and -1 and expected both dropped, because a menu was
    # seven days by construction. A menu is up to 92 days now, so 9 is
    # an ordinary Tuesday-after-next and lands; 92 and -1 are the ones
    # outside, and they are still dropped rather than wrapped. A row
    # that said 400 would otherwise land more than a year away, which
    # is a surprise nobody asked for and nobody would find.
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=92, recipe=pie,
                            servings=4, sort_order=1)
    MenuItem.objects.create(menu=menu, day_index=-1, recipe=pie,
                            servings=4, sort_order=1)
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(MealEntry.objects.count() == 2,
       'a day offset outside 0..91 is DROPPED', MealEntry.objects.count())
    ok(not MealEntry.objects.filter(
        date__gte=DST + _dt.timedelta(days=92)).exists(),
       '  and nothing landed a quarter away')
    ok(not MealEntry.objects.filter(date__lt=DST).exists(),
       '  or before the landing date')
    # AND 9 IS NOW AN ORDINARY DAY, which is the behaviour that
    # changed rather than a pin that moved.
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=9, recipe=pie,
                            servings=4, sort_order=1)
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    ok(MealEntry.objects.filter(
        date=DST + _dt.timedelta(days=9)).exists(),
       '  while day 9 LANDS - a menu is no longer seven days long',
       list(MealEntry.objects.values_list('date', flat=True)))

    # ----------------------------------------------------------------
    head('3i. deleting a Menu forgets the menu, not the meals')
    # ----------------------------------------------------------------
    # A STAMP, NOT A SUBSCRIPTION. The MealEntry rows an Apply made are
    # real meals on real dates with no link back to the menu, which is
    # the point: deleting the template cannot reach into a week you
    # have already planned. CASCADE takes MenuItem and nothing else.
    clear()
    entry(SRC, soup, servings=6, order=1)
    post(SAVE, {'week': SRC.strftime('%Y-%m-%d'), 'name': 'Doomed'})
    menu = Menu.objects.get(name='Doomed')
    post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                 'menu_id': menu.menu_id})
    stamped = MealEntry.objects.count()
    ok(stamped == 2, 'a week, saved and stamped onto another', stamped)

    r = post(DELETE, {'week': DST.strftime('%Y-%m-%d'),
                      'menu_id': menu.menu_id})
    ok(r.status_code == 302, 'deleting a menu redirects', r.status_code)
    ok(not Menu.objects.filter(menu_id=menu.menu_id).exists(),
       '  the menu is gone')
    ok(MenuItem.objects.filter(menu_id=menu.menu_id).count() == 0,
       '  its rows went with it - CASCADE',
       MenuItem.objects.filter(menu_id=menu.menu_id).count())
    ok(MealEntry.objects.count() == stamped,
       '  and every meal it stamped is still on its week',
       MealEntry.objects.count())

    # A MENU THAT IS ALREADY GONE IS A SENTENCE, not a 500. Two people
    # with the dialog open and one of them presses the trashcan.
    # NAMED, NOT PRINTED FROM THE PAYLOAD. The first cut labelled
    # these with sorted(data.keys()) and printed the same line twice -
    # a gate line that cannot tell you WHICH case it was is a gate
    # line that wastes the minute it takes to find out.
    for data, why in (({'week': DST.strftime('%Y-%m-%d'),
                        'menu_id': menu.menu_id}, 'a menu already gone'),
                      ({'menu_id': 'nope'}, 'an id that is not a number'),
                      ({'menu_id': ''}, 'a blank id'),
                      ({}, 'nothing at all')):
        r = post(DELETE, data)
        ok(r.status_code == 302,
           'deleting with %s redirects, it does not 500' % why,
           r.status_code)
    # AND THE SAME QUESTION ASKED OF APPLY, which is the one that would
    # otherwise write rows against a menu that no longer exists.
    before_n = MealEntry.objects.count()
    for data, why in (({'week': DST.strftime('%Y-%m-%d'),
                        'menu_id': menu.menu_id}, 'a menu already gone'),
                      ({'week': DST.strftime('%Y-%m-%d'),
                        'menu_id': 'nope'}, 'an id that is not a number'),
                      ({'week': 'nope', 'menu_id': '1'}, 'a junk week'),
                      ({}, 'nothing at all')):
        r = post(APPLY, data)
        ok(r.status_code == 302,
           'applying with %s redirects, it does not 500' % why,
           r.status_code)
    ok(MealEntry.objects.count() == before_n,
       '  and not one of them wrote a row', MealEntry.objects.count())

    # AN EMPTY MENU REFUSES, rather than succeeding at nothing and
    # saying it added 0 meals.
    hollow = Menu.objects.create(name='Nothing on it', created_by=editor)
    r = post(APPLY, {'week': DST.strftime('%Y-%m-%d'),
                     'menu_id': hollow.menu_id})
    ok(MealEntry.objects.count() == before_n,
       'a menu with nothing on it refuses to be applied',
       MealEntry.objects.count())

    for url in (APPLY, DELETE):
        ok(cl.get(url).status_code == 405,
           'GET %s is 405' % url, cl.get(url).status_code)

    # ----------------------------------------------------------------
    head('3j. a reader may read, and may change NOTHING')
    # ----------------------------------------------------------------
    # FOUR ROUTES THAT WRITE, AND ONE THAT COUNTS. The dialogs are
    # only rendered for an editor, but a route that trusted the
    # template to hide it would be a route anybody can post to.
    clear()
    entry(SRC, soup, servings=6, order=1)
    post(SAVE, {'week': SRC.strftime('%Y-%m-%d'), 'name': 'Editor only'})
    locked = Menu.objects.get(name='Editor only')
    meals, menus = MealEntry.objects.count(), Menu.objects.count()

    for url, data, what in (
            (COPY, {'from_week': SRC.strftime('%Y-%m-%d'),
                    'to_week': DST.strftime('%Y-%m-%d')}, 'copy a week'),
            (SAVE, {'week': SRC.strftime('%Y-%m-%d'),
                    'name': 'Reader made this'}, 'save a menu'),
            (APPLY, {'week': DST.strftime('%Y-%m-%d'),
                     'menu_id': locked.menu_id}, 'apply a menu'),
            (DELETE, {'week': DST.strftime('%Y-%m-%d'),
                      'menu_id': locked.menu_id}, 'delete a menu')):
        r = post(url, data, client=ro)
        ok(r.status_code in (302, 403),
           'a read-tier user cannot %s' % what, r.status_code)
    ok(MealEntry.objects.count() == meals,
       '  and not one meal was written or removed',
       MealEntry.objects.count())
    ok(Menu.objects.count() == menus,
       '  and not one menu was made or deleted', Menu.objects.count())
    ok(Menu.objects.filter(menu_id=locked.menu_id).exists(),
       '  the menu a reader tried to delete is still there')

    # ----------------------------------------------------------------
    head('3k. the planner costs the same however many Menus there are')
    # ----------------------------------------------------------------
    # E29 TOOK THIS FAULT OFF FOUR SCREENS and this round is not
    # putting it back on one. The Apply dialog prints a meal count per
    # row, which is N+1 queries written the obvious way; the context
    # annotates instead.
    clear()
    url = '/meal_plans/planner/?week=' + SRC.strftime('%Y-%m-%d')

    def cost(u):
        reset_queries()
        resp = cl.get(u)
        return resp, len(connection.queries)

    r, one = cost(url)
    ok(r.status_code == 200, 'the planner answers with no menus at all',
       r.status_code)
    for n in range(12):
        m = Menu.objects.create(name='Rotation %02d' % n,
                                created_by=editor)
        for day in range(7):
            MenuItem.objects.create(menu=m, day_index=day, recipe=soup,
                                    servings=4, sort_order=1)
    r, many = cost(url)
    ok(r.status_code == 200, '  and with twelve of them, 84 rows',
       r.status_code)
    ok(many <= one + 1,
       '  for %d queries against %d - the count is annotated, not '
       'asked per row' % (many, one), (one, many))
    ok(len(r.context['menus']) == 12,
       '  and all twelve reach the dialog', len(r.context['menus']))
    ok(all(hasattr(m, 'item_count') for m in r.context['menus']),
       '  each carrying its own item_count')
    ok([m.item_count for m in r.context['menus']] == [7] * 12,
       '  and the count is right', [m.item_count
                                    for m in r.context['menus']][:3])
    ok([m.name for m in r.context['menus']]
       == sorted(m.name for m in r.context['menus']),
       '  in name order, so the list does not shuffle between visits')
    body = r.content.decode('utf-8', 'replace')
    ok(body.count('class="menu-option"') == 12,
       '  and the dialog draws twelve rows',
       body.count('class="menu-option"'))
    ok(body.count('icon-action-btn icon-delete') >= 12,
       '  with a trashcan on each - MANAGED HERE, not on a page of '
       'its own', body.count('icon-action-btn icon-delete'))
    ok('7 meals' in body, '  and says how many meals each one holds')


# ==========================================================================
head('4. THE TWO PAGE COUNTS - 31 to 32, the second move in two days')
# ==========================================================================
# BOTH ARE PRESENT-TENSE READINGS OF THE TREE, which is why both move
# whenever a page gains or loses base's More menu - and this is the
# second time in two days. RT-1 took them 32 -> 31 on 18 October when
# MN-1 retired view_meal_plan.html, which carried one; the planner that
# replaced it had none. This round hangs one on the planner, for the
# three controls that move a week, so the number comes back.
#
# IT IS NOT THE SAME 32. One page has left the set and another has
# joined it, and test_last_menus' section 2 still reads H8's 32 off the
# backups - a different number that happens to share a value.
wearing = [p for p in T.templates(include_base=False)
           if 'actionMoreBtn' in T.code_only(read(p))]
ok(len(wearing) == 32,
   '32 pages in both roots carry base\'s More menu', len(wearing))
ok(os.path.join('pages', 'templates', 'meal_planner.html')
   in '\n'.join(wearing), '  and the planner is one of them')
ok(not [p for p in wearing if T.code_only(read(p)).count(
    'id="actionMoreBtn"') > 1],
   '  and not one of them has two - base keys its binder on that id')

for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    body = read(suite)
    ok('== 32' in body and MARK in body,
       '%s reads 32, and says which round moved it' % label)
    ok('== 31' not in body, '  with no 31 left in it')
# AND THE REPAIR, WHICH IS THE PART THAT MATTERS. Each suite now reads
# its present-tense census with a present-tense read. test_more_menu
# takes this round's set from this round's BACKUPS - touched_by - so a
# later round joining the census cannot contaminate a claim about the
# past; test_last_menus reads today's text with today(), and now() is
# left where it belongs, in the sections that ask what H10 did.
mm_body, lm_body = read(MM), read(LM)
ok('alv_tree.touched_by(SUFFIX)' in mm_body,
   'test_more_menu takes this round\'s pages from its own backups')
ok('mine = [(n, p) for n, p in pages if n in TOUCHED]' in mm_body,
   '  and not by subtracting two lists from today\'s census')
ok("LATER == ['meal_planner.html']" in mm_body,
   '  and NAMES the page a later round put on the binder')
ok('def today(p):' in lm_body,
   'test_last_menus reads its present-tense census in the present tense')
ok('markup(now(p))' not in lm_body.split('head(\'2.')[0],
   '  with no historical read left in section 1')
# THE SEVEN RULES. H10 recorded that one page still painted the
# component; DB-5 took them on 12 October and the claim went on
# passing for a week because it was asked of H10's tree. Both halves
# are asserted now - the past from the backups, the present from the
# tree - and this suite insists both halves are there.
ok('painted it with 7 rules when H10 ran' in lm_body,
   '  the 7 rules H10 measured are asserted from the backups')
ok('DB-5 took the last seven' in lm_body,
   '  and TODAY nothing paints it, with the round that paid it named')

# AND THEY STILL PASS. A re-pin is a claim that the suite agrees, and
# the only way to know is to run it. Run as subprocesses, because both
# import modules this one has already imported with a different
# database configured underneath them.
import subprocess                                            # noqa: E402
for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    pr = subprocess.run([sys.executable, suite], cwd=ROOT,
                        capture_output=True, text=True, timeout=900)
    ok(pr.returncode == 0, '%s passes with the new number' % label,
       (pr.stdout or '')[-500:] + (pr.stderr or '')[-300:])

# ==========================================================================
head('5. NO MIGRATION - asked of the tree, not asserted')
# ==========================================================================
# MENU AND MENUITEM SHIPPED WITH 0100 IN PUSH 1, holding DAY INDEXES
# and not dates precisely so that this round could exist. A round that
# claimed "no migration needed" without checking would be a round that
# deploys and then cannot write a Menu.
migs = os.path.join(ROOT, 'pages', 'migrations')
# BY THE NUMBER, NOT BY THE STRING. The first cut of this check read
# `n > '0100'` and failed on 0100 itself: '0100_meal_entry.py' sorts
# after '0100' because it is longer. A comparison that looks like
# arithmetic and is not is worse than one that looks wrong.
# ASKED OF THIS ROUND, NOT OF THE TREE - repaired by MX-1,
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
    if 'MW-1, 19 Oct 2026' in read(os.path.join(migs, n)):
        ours.append(n)
ok(not ours, 'this round adds NO migration', ours)
ok(any(n.startswith('0100') for n in os.listdir(migs)),
   '  and 0100, the one that made the tables, IS there')
mcode = T.python_code_only(read(MODELS))
ok('class Menu(models.Model):' in mcode, 'Menu is already a model')
ok('class MenuItem(models.Model):' in mcode, 'MenuItem is already a model')
ok('day_index = models.IntegerField(' in mcode,
   '  and MenuItem keeps a DAY INDEX, which is why a menu is not a week')
ok('leftover_of' not in mcode.split('class MenuItem')[1].split('class ')[0],
   '  and has NO leftover_of - a leftover is not something you plan')
m100 = os.path.join(migs, '0100_meal_entry.py')
ok(os.path.isfile(m100), 'and 0100 is the one that made them')
if os.path.isfile(m100):
    code = T.python_code_only(read(m100))
    for name in ('menus', 'menu_items'):
        ok("'%s'" % name in code or '"%s"' % name in code,
           '  0100 creates %s' % name)

# ==========================================================================
head('6. WIDE FROM BIRTH - every page in both roots, asked')
# ==========================================================================
# THE THREE DIALOGS BELONG TO ONE SCREEN. base owns the ids of the More
# menu and this round owns the ids of the dialogs; a second page that
# grew a copy of either would be two elements answering to one id,
# which is the fault H8 spent a round taking off 31 pages.
pages_all = T.templates(include_base=False)
ok(len(pages_all) > 100, 'the census reads %d pages in both roots'
   % len(pages_all), len(pages_all))
for mid in DIALOGS:
    holders = [T.rel(p) for p in pages_all
               if 'id="%s"' % mid in T.code_only(read(p))]
    ok(holders == ['meal_planner.html'],
       'only the planner carries %s' % mid, holders)
for fn in ('function copyPreview()', 'function pickMenu(',
           'function deleteMenu('):
    holders = [T.rel(p) for p in pages_all
               if fn in T.code_only_js(read(p))]
    ok(holders == ['meal_planner.html'],
       'only the planner defines %s' % fn.rstrip('('), holders)
# AND THE ROUTES ARE REVERSED BY NAME NOWHERE ELSE. A page that
# reversed one of these would be a page that needs the dialog too.
urls_code = T.python_code_only(read(URLS))
for fn in VIEWS_ADDED:
    ok("name='%s'" % fn in urls_code,
       'the route %s is registered exactly once' % fn,
       urls_code.count("name='%s'" % fn))
    ok(urls_code.count("name='%s'" % fn) == 1, '  and only once')


# ==========================================================================
head('7. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

# THE REVERT CONTROLS. Each one says which section would fail if the
# round came out, which is the only way to know the section is testing
# the round and not the weather.
ok('def copy_meal_week(' not in T.python_code_only(was(VIEW)),
   'reverting the view takes the five views out, so section 1 would FAIL')
ok("name='copy_meal_week'" not in T.python_code_only(was(URLS)),
   '  and the routes with them')
ok('id="copyWeekModal"' not in T.code_only(was(TPL)),
   '  and reverting the planner takes the three dialogs')
ok('.recipe-option {' not in T.code_only(was(TPL)),
   '  and leaves the picker row unstyled again, so section 1 would FAIL '
   'on the second subject too')
ok('#recipeList' in T.code_only(was(TPL)),
   '  with the three dead phone rules back')

# AND THE INSTRUMENTS, ASKED THE SAME QUESTIONS THEY ARE TRUSTED WITH.
# Every one of these reads this round's own prose in section 1, and a
# reader that blanked the wrong thing would have made that section say
# whatever the comments said.
ok('fa-trash' not in T.code_only('<!-- fa-trash -->'),
   'the markup reader does not see a class named in an HTML comment')
ok('fa-trash' not in T.code_only('{# fa-trash #}'),
   '  or in a Django comment')
ok('menu-option' not in T.code_only(
    '<style>/* .menu-option */ a{x:1}</style>'),
   '  or in a CSS comment inside a style block')
ok('alert(' not in T.code_only_js('<script>// alert( no\n</script>'),
   '  and code_only_js does not see a call named in a // comment')
ok('//example.com' in T.code_only_js('<a href="http://example.com">x</a>'),
   '  but a // inside a URL is not a comment  [CO-1]')
ok('%-d' not in T.python_code_only('def f():\n    """no %-d here"""\n'),
   'python_code_only blanks a docstring - the gate in this round\'s own '
   'patcher refused it over one')
ok("'%-d'" in T.python_code_only("X = '%-d'"),
   '  and keeps a payload string, which is where a round writes its text')

# NO %-d IN THE VIEW, asked of the code. Windows strftime has no %-d
# and Linux has no %#d; this project runs on the laptop AND on Railway.
vcode = T.python_code_only(NOW[VIEW])
for bad in ('%-d', '%#d', '%-m', '%#m'):
    ok(bad not in vcode, 'the view uses no %s - one platform has it, the '
                         'other does not' % bad)
ok("'%d %s' % (d.day, d.strftime('%b'))" in vcode,
   '  day_label builds the date from .day instead')

# THE TEMPLATE'S OWN SHAPES, re-asked here because the patcher's gates
# only run at apply time and a later round can break any of them.
tpl = NOW[TPL]
ok(tpl.count('/*') == tpl.count('*/'),
   'the planner\'s CSS comments balance - %d /* and %d */'
   % (tpl.count('/*'), tpl.count('*/')))
for o, c in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
    ok(tpl.count(o) == tpl.count(c),
       '  and its %s tags close - %d and %d'
       % (o, tpl.count(o), tpl.count(c)))
depth, worst = 0, 0
for m in re.finditer(r'<form\b|</form>', tpl):
    depth += 1 if m.group(0) == '<form' else -1
    worst = max(worst, depth)
ok(worst == 1 and depth == 0,
   '  and no form is nested in another - %d deep, closing at %d'
   % (worst, depth))
# BOOTSTRAP 4.1.3, which is what base.html loads. A4 spent a release on
# a Bootstrap 5 `new bootstrap.Modal(...)` call on this very page.
# ASKED OF THE CODE. This one caught its own author: the picker's
# comment and this round's own name A4's Bootstrap 5 call in order to
# say it must not come back, and the raw file therefore contains the
# string. Fourth time in this suite.
tcode = T.code_only_js(tpl)
ok('new bootstrap.Modal' not in tcode,
   '  and no Bootstrap 5 modal call - base loads 4.1.3  [A4]')
ok('new bootstrap.Modal' in tpl,
   '  though two comments NAME it, which is why that is asked of the '
   'code and not of the file')
ok(tcode.count("$('#pickerModal').modal('show')") == 1,
   '  the one dialog opened from script uses the 4.x call')

# REGISTRATION. A round that ships and registers nothing is a round
# whose absence nobody notices next week.
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
# AFTER THE ROUND BEFORE IT, NOT LAST. The first cut of this line
# asserted ROUNDS[-1] == SUFFIX and MO-1 broke it twenty minutes later,
# in the same push - which is the whole of lesson 54: the claim is the
# ORDER, and "I am the newest round" is a claim that can only be true
# until the next one. as_left_by walks this list, so what matters is
# that MW-1 sits after MH-2 and before whatever comes next.
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealguide'),
   '  and after .bak_mealguide, the round before it  [lesson 54]',
   ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
# CP-2, 21 Oct 2026 - the two dialogs that replaced the three. A
# sentinel pointed at a string a round renamed stops the push BEFORE
# any suite runs, and twenty-two suites in this tree check that every
# sentinel still resolves - so three stale ones turned one change
# into twenty-two red suites in the 21 October sweep.
for text in ('id="copyRangeModal"', 'id="menusModal"',
             'added alongside',
             'def copy_week_rows(', "name='meal_week_preview'"):
    ok(text in ps1, '  the pre-flight can see %r' % text)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
# AND THE TWO REGISTERS AGREE. Not a number - a number here would be
# this round claiming to be the last one again. test_waiting_down owns
# the count; all this round needs is that its own suite is counted and
# that the two registers have not drifted apart.
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m is not None, 'test_waiting_down declares a CONVERTED_N')
ok(m and int(m.group(1)) == len(T.CONVERTED),
   '  and it agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))
ok(len(T.CONVERTED) >= 107,
   '  which is at least the 107 this round made it', len(T.CONVERTED))

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE WEEK MOVES. Copy it onto a week you pick, save it under a')
print('  name and stamp that name onto any week later - and when two of')
print('  them land on the same day, both are there and the dialog said')
print('  so before the button was pressed.')
print('')
print('  AND TWO CLAIMS WERE BEING ASKED OF THE PAST. Re-pinning one')
print('  page count from 31 to 32 broke seven checks in two suites,')
print('  because both read a present-tense census through')
print('  as_left_by - the page as their own round left it. That is the')
print('  same reading on 31 pages and a different one on a page that')
print('  joined later. Behind it: H10 has recorded since 10 October')
print('  that one page still paints the More menu, and DB-5 took the')
print('  last seven of those rules on 12 October. The claim passed for')
print('  seven days because it was looking at the wrong tree.')
print('')
print('  Historical and present-tense reads are different questions,')
print('  and the call site is the only place that knows which one is')
print('  being asked.')
print('=' * 74)
sys.exit(1 if failed else 0)
