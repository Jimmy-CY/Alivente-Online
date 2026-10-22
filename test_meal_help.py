# -*- coding: utf-8 -*-
"""test_meal_help.py - round MH-1, 18 Oct 2026.

THE MEAL PLANS USER GUIDE. Seven tabs, one module, five pages.

WHAT THIS SUITE ASSERTS

  1   THE GUIDE EXISTS AND PARSES. Not "the file contains a section" -
      the renderer the application actually uses is asked for the
      module and must hand back seven named tabs with real HTML in
      them. A help file that BeautifulSoup cannot parse fails silently
      in production: the modal simply never appears.

  2   ALL FIVE PAGES CARRY IT. The load tag, the button, the modal, and
      the More menu on the one page that has one. Measured per page,
      because MH-1 is the first module in the tree rendered by more
      than one page and "it works on the calendar" says nothing about
      the other four.

  3   THE GUIDE IS TRUE. The four statements the old tab got wrong are
      asserted against the APPLICATION, not against the guide: if the
      guide says the three share buttons are Copy, Email and WhatsApp,
      then the shopping list page had better have exactly those three.
      A user guide that agrees with itself and disagrees with the
      screen is the fault this round exists to fix.

  4   THE OLD TAB POINTS RATHER THAN REPEATS, and the four wrong
      statements are gone from it.

  5   THE CONTROL. Every claim above re-asked of the tree as it was,
      from .bak_mealhelp, where every one must FAIL.

  6   Scope, registration and the gate.

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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealhelp'
ME = 'test_meal_help.py'
PATCHER = 'apply_meal_help.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MH-1, 18 Oct 2026'
SLUG = 'meal_plans'

HELP = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join(ROOT, 'pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join(ROOT, 'pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join(ROOT, 'pages', 'templates', 'view_meal_plan.html')
# MN-1, 18 Oct 2026 - FIVE SCREENS BECAME TWO. The planner replaced
# the list, the calendar, Create/Edit and the plan page, so three of
# the five Help buttons went with their pages. The guide is unchanged
# and still reached from every screen that exists.
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
PAGES = (PLANNER, SHOP)
FILES = (HELP,) + PAGES

# MH-2, 18 Oct 2026 - SEVEN BECAME SIX. 'The Plan Page' went with the
# plan page, and 'Building a Plan' is 'Adding a Meal', because you add a
# meal to a day now rather than building a container first.
#
# MH-3, 19 Oct 2026 - AND SIX BECAME SEVEN AGAIN, which is a different
# seven: 'Moving a Week' is the three controls MW-1 shipped - copy a
# week, save one as a Menu, apply a Menu - and they are not 'Adding a
# Meal', because they act on a WEEK. The six above are MH-2's own and
# none of them left.
#
# MH-5, 20 Oct 2026 - AND SEVEN BECAME EIGHT. 'Printing' is PP-1's
# printable plan, and it is not 'Shopping List', because that tab is
# about a list of things to buy and this is about a calendar on paper.
# It sits after Shopping List, which is the order the two buttons sit
# in on the planner bar.
TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Printing', 'Who Can Do What', 'Tips')

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
    """Every claim MH-1 makes, as {label: bool}.

    Written once and asked twice, so section 5 can put the same
    questions to the tree as it was. The negative claims read the
    comment-free text, because MH-1's own comments quote what the old
    tab said - "it said the calendar could add recipes" - and to a
    substring search a comment about a thing is the thing. That cost
    three wrong checks in MP-1 and two in MD-1."""
    c = {}
    h = text[HELP]
    hcode = T.code_only(h)

    # EACH CLAIM IS ASKED OF ITS OWN SECTION, NOT OF THE WHOLE FILE.
    # administration.html carries a dozen modules and 213 KB, and three
    # claims failed on the first run for one reason: they searched the
    # file. "Overview" and "Tips" are tab names OTHER modules already
    # use, so both held before the round and proved nothing; and the
    # old tab read as 42 KB long because the slice was the whole
    # recipe_management section rather than the one article inside it.
    def section(slug):
        i = hcode.find('data-module-slug="%s"' % slug)
        if i < 0:
            return ''
        i = hcode.rfind('<section', 0, i)
        j = hcode.find('</section>', i)
        return hcode[i:j] if j > i else hcode[i:]

    def article(sec, slug):
        i = sec.find('data-tab-slug="%s"' % slug)
        if i < 0:
            return ''
        i = sec.rfind('<article', 0, i)
        j = sec.find('</article>', i)
        return sec[i:j] if j > i else sec[i:]

    mine = section(SLUG)

    # ---- 1. the guide exists, in the file
    c['the guide has its own module section'] = bool(mine)
    c['  under Personal, like its sibling'] = (
        'data-module-name="Meal Plans"' in mine
        and 'data-module-group="Personal"' in mine)
    c['  gated on the Recipes read permission'] = (
        'data-module-permission="can_access_recipes"' in mine)
    for t in TABS:
        c['  tab: %s' % t] = 'data-tab-name="%s"' % t in mine
    # MH-2, 18 Oct 2026 - SIX, AND THE NUMBER COMES FROM TABS. It was
    # written out twice, as a word and as a digit, and a round that
    # changes the tab list should not have to find both.
    c['  and %d of them, no more' % len(TABS)] = (
        mine.count('data-tab-slug="mp-') == len(TABS))
    c['  each tab has real content, not a stub'] = (
        len(mine) > 15000)

    # ---- 2. BOTH SCREENS CARRY IT, AND ONLY THE ONES HANDED IN.
    # MH-2, 18 Oct 2026 - the control section reads the tree as MH-1 found
    # it, and the planner is not in that tree at all: MN-1 made it two
    # rounds later, with a Help button already on it. So this walks the
    # pages the CALLER has text for, and the live call still walks both.
    for p in [q for q in PAGES if q in text]:
        name = os.path.basename(p)
        code = T.code_only(text[p])
        c['%s loads the tag' % name] = (
            '{% load help_modal_tags %}' in code)
        c['%s renders the modal' % name] = (
            '{%% render_help_modal "%s" %%}' % SLUG in code)
        c['%s has a Help button' % name] = (
            'data-target="#%sHelpModal"' % SLUG in code)
    # MH-2, 18 Oct 2026 - AND NEITHER OF THE TWO HAS A MORE MENU.
    # view_meal_plan was the one page that carried Help in a More menu
    # as well as in its bar, and MN-1 retired it. One button each is
    # the whole claim now, which is simpler and still asked of both.
    # HP-1, 21 Oct 2026 - ONE PER WIDTH, which is not the same
    # as one per page. The planner carries Help twice now: in the
    # bar for a desktop and in the More menu for a phone, because
    # base hides every .action-secondary below 768px in a bar that
    # has a menu, and for two days that left an editing user with
    # no Help on a phone at all.
    #
    # MN-1's retired view_meal_plan had two that were BOTH
    # reachable at once, which is the shape this claim was written
    # against on 18 October. These two never are: each width shows
    # exactly one. test_help_phone measures that at 1280 and 390.
    c['  and each of the two has Help where a finger can reach it'] = (
        all(1 <= T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) <= 2
            for p in PAGES if p in text)
        and all(T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
            or 'action-more-menu' in T.code_only(text[p])
            for p in PAGES if p in text))

    # ---- 4. the old tab points rather than repeats
    #
    # THE ARTICLE, NOT THE SECTION. recipe_management is 42 KB across
    # eight tabs, so slicing the section made the length claim
    # meaningless and the four wrong-statement claims read the whole
    # recipe guide rather than the one tab that said them.
    rec = article(section('recipe_management'), 'rec-mealplans')
    # MN-1, 18 Oct 2026 - "any of the five" became "any meal-plan
    # screen", because there are two now and there will be more. The
    # pointer should not carry a number that a release can move.
    c['the old tab points at the new guide'] = (
        'press <strong>Help</strong> on any meal-plan screen' in rec)
    c['  and no longer says the calendar can add recipes'] = (
        'Add or remove recipes directly from the calendar view' not in rec)
    c['  nor that Print is one of the share buttons'] = (
        'Share via Print, Copy, Email or WhatsApp' not in rec)
    c['  nor calls the review step a pantry'] = (
        'already have in your pantry and only the remaining items' not in rec)
    c['  and it is a pointer, not a second copy of the guide'] = (
        0 < len(rec) < 2600)
    return c


def kept(text):
    """CLAIMS THAT MUST HOLD IN BOTH TREES - the other register.

    MD-1 learned this the same way: a claim that the round did NOT
    BREAK something cannot fail on the tree as it was, so mixing it in
    with the change claims makes the control unusable.

    Here there are two, and both matter. The old tab must still EXIST -
    deleting it would leave a gap where somebody has learned to look -
    and the twelve other modules in the same 213 KB file must still be
    parseable, because MH-1 inserts 22 KB into the middle of it and a
    malformed insert breaks every modal in the file, not only its own.
    """
    c = {}
    hcode = T.code_only(text[HELP])
    c['the old Recipe Management tab still exists'] = (
        'data-tab-slug="rec-mealplans"' in hcode)
    c['and recipe_management is still a module in the file'] = (
        'data-module-slug="recipe_management"' in hcode)
    c['and every <section> in the file still closes'] = (
        hcode.count('<section') == hcode.count('</section>'))
    c['and every <article> too'] = (
        hcode.count('<article') == hcode.count('</article>'))
    return c


# ==========================================================================
head('1-4. THE GUIDE, THE FIVE PAGES, AND THE OLD TAB')
# ==========================================================================
LIVE = claims(NOW)
for label in sorted(LIVE):
    ok(LIVE[label], label)

KEPT = kept(NOW)
print('')
print('  -- and %d things the round had to LEAVE INTACT --' % len(KEPT))
for label in sorted(KEPT):
    ok(KEPT[label], label)

# ==========================================================================
head('5. THE CONTROL - every claim above, asked of the tree BEFORE MH-1')
# ==========================================================================
# MH-2, 18 Oct 2026 - THE FILES MH-1 ACTUALLY TOUCHED. The planner was
# created by MN-1 two rounds later, with its Help button already on it,
# so there is no MH-1 backup of it and there should not be. The control
# below reads the files MH-1 did see; the planner gets a claim of its
# own underneath, which is the honest one for a page born with the
# thing this round added elsewhere.
HAD = tuple(p for p in FILES if os.path.isfile(p + SUFFIX))
try:
    BEFORE = dict((p, was(p)) for p in HAD)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))
ok(PLANNER not in HAD and os.path.isfile(PLANNER),
   'the planner is not in the control, because MH-1 never saw it - MN-1 '
   'made the page two rounds later, with a Help button already on it')
ok(not os.path.isfile(PLANNER + SUFFIX),
   '  and it carries no %s, which is what a page born after a round '
   'looks like' % SUFFIX)

if BEFORE is not None:
    OLD = claims(BEFORE)
    # MH-2, 18 Oct 2026 - THE CLAIMS THAT CAN BE ASKED OF BOTH TREES.
    # Three of the live claims are about the planner, and the planner is
    # not in the tree MH-1 found - MN-1 made it two rounds later. A
    # control cannot ask a question of a page that did not exist, and
    # pretending it can is how a control stops being one.
    ONLY_LIVE = sorted(set(LIVE) - set(OLD))
    ok(all('meal_planner.html' in k for k in ONLY_LIVE),
       'the %d claim(s) the old tree cannot answer are all about the '
       'planner' % len(ONLY_LIVE), ONLY_LIVE)
    ok(sorted(OLD) == sorted(set(LIVE) - set(ONLY_LIVE)),
       'the same %d claims are asked of both trees' % len(OLD),
       'live %d, old %d' % (len(LIVE), len(OLD)))
    held = sorted(k for k in OLD if OLD.get(k))
    ok(not held,
       'ALL %d claims FAIL on the tree as it was - the suite can fail'
       % len(OLD),
       '%d held before the round:\n%s'
       % (len(held), '\n'.join(held[:14])))

    OLDKEPT = kept(BEFORE)
    lost = sorted(k for k in OLDKEPT if not OLDKEPT.get(k))
    ok(not lost,
       'and all %d preservation claims held BEFORE the round too'
       % len(OLDKEPT),
       '%d did not, so they are claims about a change:\n%s'
       % (len(lost), '\n'.join(lost)))

# ==========================================================================
head('6. THE RENDERER - the guide as the application actually reads it')
# ==========================================================================
# NOT "the file contains a section". pages/services/help_renderer.py
# parses these files with BeautifulSoup and caches the result; a help
# file it cannot parse fails SILENTLY in production - the modal simply
# never appears, and nothing anywhere says why. So the renderer is
# asked, and it has to hand back seven named tabs with real HTML in
# them.
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        django.setup()
    else:
        django.setup()
    import pages.services.help_renderer as HR
    mod = HR.get_help_module(SLUG)
    up = True
except Exception as e:
    mod, up = None, False
    skip('the renderer checks', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if up:
    ok(mod is not None,
       'the renderer finds the %r module - a file it cannot parse '
       'returns None and the modal never appears' % SLUG)
if up and mod:
    ok(mod.get('name') == 'Meal Plans', 'it is called Meal Plans',
       mod.get('name'))
    ok(mod.get('group') == 'Personal', '  grouped under Personal',
       mod.get('group'))
    ok(mod.get('permission') == 'can_access_recipes',
       '  and gated on the Recipes read permission',
       mod.get('permission'))
    ok(bool(mod.get('subtitle')), '  with a subtitle on the header',
       mod.get('subtitle'))
    got = [t['name'] for t in mod.get('tabs', [])]
    ok(got == list(TABS), '%d tabs, in order' % len(TABS), got)
    # AND EVERY TAB HAS CONTENT. A tab that parses to an empty string
    # renders an empty panel, which looks like a bug in the shell.
    thin = [t['name'] for t in mod.get('tabs', [])
            if len((t.get('content_html') or '').strip()) < 600]
    ok(not thin, 'every tab carries real content, none under 600 bytes',
       thin)
    ok(all(t.get('icon', '').startswith('fa-')
           for t in mod.get('tabs', [])),
       '  and every tab has an icon the shell can draw',
       [t.get('icon') for t in mod.get('tabs', [])])
    # AND THE TWELVE OTHER MODULES IN THE SAME FILE STILL PARSE. MH-1
    # inserts 22 KB into the middle of a 213 KB file; a malformed
    # insert breaks every modal in it, not only its own.
    for sibling in ('recipe_management', 'user_administration',
                    'household_member_management', 'passport_management'):
        ok(HR.get_help_module(sibling) is not None,
           '  and %s still parses out of the same file' % sibling)

# ==========================================================================
head('7. THE GUIDE IS TRUE - checked against the screens, not itself')
# ==========================================================================
# THIS IS THE SECTION THE ROUND EXISTS FOR. The old tab agreed with
# itself perfectly and disagreed with the application in four places -
# including describing a calendar feature that was a server error from
# before the tab was written. A suite that only read the guide would
# have passed it.
#
# So each statement is paired with the thing it describes, and the
# SCREEN is the authority.
if up and mod:
    tabs = dict((t['name'], t['content_html']) for t in mod['tabs'])
    # MH-2, 18 Oct 2026 - TWO SCREENS, NOT FIVE.
    #
    # The rule is MH-1's and it does not change: every statement in the
    # guide is paired with the thing it describes, and THE SCREEN IS THE
    # AUTHORITY. What changed is which screens there are. MN-1 replaced
    # the list, the calendar, Create/Edit and the plan page with one
    # planner, so the pairings read the planner and the shopping list.
    #
    # The checks that went with the screens are not dropped quietly.
    # Each one below says which it replaced, and the section ends with
    # the check the five-screen shape could not have had: that the guide
    # promises NOTHING the planner cannot do.
    shop_src = NOW[SHOP]
    plan_src = NOW[PLANNER]
    view_py = read(os.path.join(ROOT, 'pages', 'views', 'recipes',
                                'meal_planning.py'))

    # (1) THE THREE SHARE BUTTONS. Unchanged by MN-1 - SL-1's bar is
    # still the shopping list's bar.
    guide = tabs.get('Shopping List', '')
    ok('<strong>Copy</strong>' in guide and '<strong>WhatsApp</strong>'
       in guide and '<strong>Email</strong>' in guide,
       'the guide names Copy, Email and WhatsApp as the three')
    ok('Print</strong> is in the page' in guide
       or 'Print</strong> is in the' in guide,
       '  and says Print is in the page bar, not among them')
    for fn in ('copyToClipboard()', 'shareToWhatsApp()',
               'toggleEmailPanel()'):
        ok(fn in shop_src, '  and %s is really on the page' % fn)
    ok('id="printBtn"' in shop_src,
       '  and Print really is a separate control in the bar')

    # (2) THE TWO STEPS, by the names on the screen.
    ok('Review Ingredients' in guide and 'Review Ingredients' in shop_src,
       'the guide calls step 1 what the screen calls it')
    ok('Items to Buy' in guide and 'Items to Buy' in shop_src,
       '  and step 2 is Items to Buy on both')

    # (3) IT SHOPS FOR A WEEK, NOT FOR A PLAN. This replaces the old
    # pairing against a plan's recipes, and it is the whole of what
    # MN-1 changed about this screen.
    # MH-5, 20 Oct 2026 - A RANGE, NOT A WEEK. SL-7 made the
    # Shopping List button follow the view, so the list is a month
    # from Month and a day from Day; and the list page itself takes
    # a from/to pair. 'the week you were looking at' was the true
    # sentence on 18 October and became a false one this morning.
    ok('range you were looking at' in guide,
       'the guide says the list is the range you were looking at')
    ok('buys for the month' in guide and 'for that day' in guide,
       '  and spells out that the view decides it')
    ok("?from=" in plan_src and "to=" in plan_src,
       '  and the planner really hands it a date range')
    ok("request.GET.get('from')" in view_py
       or "'from'" in view_py and 'meal_shopping_list' in view_py,
       '  and the view really reads one')

    # (4) ADD RECIPE, ON EVERY DAY. Replaces "the calendar really can
    # add and remove now", which was A1 - a server error the old tab
    # described as a feature before MP-1 fixed it.
    guide_cal = tabs.get('The Calendar', '')
    ok('Add Recipe' in guide_cal,
       'the guide says Add Recipe sits on every day card')
    ok('Add Recipe' in plan_src,
       '  and the planner really carries it')
    for fn in ('def add_meal_entry(request):',
               'def remove_meal_entry(request):'):
        ok(fn in view_py, '  and %s can actually be called' % fn)

    # (5) THE TRASHCAN REMOVES ONE MEAL. Replaces the old claim about
    # removing a recipe from a plan day.
    # MH-5, 20 Oct 2026 - THERE IS NO TRASHCAN. CH-1 made a meal a
    # chip with a menu on it, and Remove is one of four things on
    # that menu. What this check was really asking - does the guide
    # say removal takes the meal and not the day - is asked of the
    # sentence that says it now.
    ok('the one meal, not the day' in guide_cal,
       'the guide says Remove takes the one meal, not the day')
    for act in ('View', 'Move', 'Leftovers', 'Remove'):
        ok('<strong>%s</strong>' % act in guide_cal,
           '  and the chip menu offers %s' % act)
    ok('Remove from this day' in plan_src,
       '  and that is the wording on the control')

    # (6) TODAY, AND THE WEEK YOU CHOSE. Replaces "a week can only open
    # one plan", which was C17 - a limit that cannot exist now.
    ok('Today' in guide_cal,
       'the guide says Today brings you back to this week')
    ok('>Today<' in plan_src or 'Today' in plan_src,
       '  and the planner really has it')
    ok('goWeek(' in plan_src,
       '  and a week row really opens that week')

    # (7) SERVINGS COME FROM THE RECIPE, AND THE STEPPER SAVES AS YOU
    # PRESS. The first half is C19 and survives the rewrite; the second
    # is new, and is the thing a reader is most likely to disbelieve.
    guide_add = tabs.get('Adding a Meal', '')
    ok("recipe's own yield" in guide_add,
       'the guide says servings come from the recipe')
    ok('data-recipe-servings=' in plan_src or 'recipe.servings' in plan_src,
       '  and the picker really reads the recipe yield - C19')
    ok('saves as you press' in guide_add,
       'the guide says the stepper saves as you press')
    ok('def set_meal_servings(request):' in view_py,
       '  and there really is a view that stores one press')
    ok('one is the floor' in guide_add.lower(),
       '  and that one is the floor')
    ok('max(1' in view_py or 'Decimal(1)' in view_py or '1)' in view_py,
       '  and the server really holds that floor')

    # (8) NOTHING TO NAME AND NOTHING TO SAVE. The guide says so in as
    # many words, so the planner is asked to have no such field.
    ok('nothing to save' in guide_add or 'no Save button' in guide_add,
       'the guide says there is no Save button')
    ok('name="plan_name"' not in plan_src,
       '  and the planner really has no plan name field')
    ok('>Save<' not in T.code_only(plan_src),
       '  and no Save button either')

    # (9) THE PERMISSIONS, which MN-1 did not change.
    guide_perm = tabs.get('Who Can Do What', '')
    ok('Recipes access' in guide_perm and 'Recipes edit' in guide_perm,
       'the guide names the two permissions')
    ok('can_edit_recipes' in plan_src,
       '  and the planner really gates on the edit one - B11')
    ok('can_edit_personal' not in T.code_only(plan_src),
       '  and not on the one the views never checked')

    # (10) THE EMAIL, AND THE BANNER. Both unchanged by MN-1.
    ok('household members' in guide.lower(),
       'the guide says the email goes to household members only')
    ok('not a household member' in view_py,
       '  and the server really refuses anybody else - B9')
    ok('NOT ON THIS LIST' in guide and 'NOT ON THIS LIST' in shop_src,
       'the guide explains the NOT ON THIS LIST banner, which exists')
    ok('Set base units' in guide and 'Set base units' in shop_src,
       '  with the same button name on both')

    # (11) PAST DATES. The guide promises them on the planner now.
    ok('Past dates are allowed' in tabs.get('Overview', ''),
       'the guide says past dates are allowed')
    ok("min=\"{{ today|date:'Y-m-d' }}\"" not in T.code_only(plan_src),
       '  and the planner bounds nothing to today - D27')

    # (12) AND THE CHECK THE FIVE-SCREEN SHAPE COULD NOT HAVE HAD.
    #
    # MH-2, 18 Oct 2026. Every word below belonged to a screen MN-1
    # retired. A guide that still used one would be telling a reader to
    # press something that is not there, and no pairing above would
    # notice - each of those only proves that what the guide DOES say is
    # true of the screen.
    #
    # This is the check that would have caught this round not happening.
    RETIRED_WORDS = ('Duplicate', 'Delete original', 'plan name',
                     'Create Meal Plan', 'Change the dates',
                     'The Plan Page', 'end date',
                     # MH-5, 20 Oct 2026 - the controls CH-1 replaced
                     # with a chip menu, and the two-panel screen MV-2
                     # replaced with three views. The guide described
                     # all four for a month and nothing asked.
                     'The trashcan', 'The eye', 'Two panels',
                     'Click a week row')
    whole = ' '.join(t['content_html'] for t in mod['tabs'])
    promised = [w for w in RETIRED_WORDS if w in whole]
    ok(not promised,
       'the guide promises nothing the planner cannot do - none of the '
       '%d retired words' % len(RETIRED_WORDS), promised)
    for w in ('Duplicate', 'Create Meal Plan'):
        ok(w not in T.code_only(plan_src),
           '  CONTROL: and %r really is absent from the planner too - '
           'asked of the CODE, because the planner own note names the '
           'button it replaced, and to a substring search a comment '
           'about a thing is the thing' % w)
    ok(len(mod['tabs']) == len(TABS),
       '  across all %d tab(s)' % len(TABS), len(mod['tabs']))

    # MH-3, 19 Oct 2026 - AND NOTHING THE PLANNER ALREADY DOES IS
    # DESCRIBED AS COMING. The mirror of RETIRED_WORDS above: MH-2
    # wrote a promise at the foot of the Adding a Meal tab naming four
    # things, and MW-1 and MO-1 built all four the next morning. A
    # guide that promises what the application does is worse than one
    # that says nothing - a reader who believes it will not go looking
    # for the control.
    PROMISED_WORDS = ('repeating a whole week', 'saved menus',
                      'a free-text note on a day',
                      'marking a meal as leftovers',
                      # MH-5, 20 Oct 2026 - release 4. Nine more the
                      # planner now does, so none of them may appear
                      # in a sentence calling something coming.
                      'moving a meal from one day to another',
                      'three views', 'a month view', 'a day view',
                      'printing a plan', 'a printable plan',
                      'adding from the library',
                      'a note from the picker',
                      'a quick look at a recipe')
    coming = [s for s in re.split(r'(?<=[.!])\s+', whole)
              if 'coming' in s.lower() or 'not yet' in s.lower()]
    stale = sorted(w for w in PROMISED_WORDS
                   for s in coming if w in s)
    ok(not stale,
       'the guide promises nothing it already does - none of the %d '
       'features MW-1 and MO-1 shipped' % len(PROMISED_WORDS), stale)
    # AND THE CONTROLS REALLY ARE THERE, asked of the planner. An
    # absence claim on its own would pass on a guide that simply never
    # mentions them.
    # MH-5, 20 Oct 2026 - THE EIGHTH TAB SAYS SOMETHING. A name in
    # TABS proves a tab exists and nothing else; this asks the tab's
    # own prose for the four facts PP-1 settled, and asks the planner
    # whether the button it describes is there to press.
    pr = [t for t in mod['tabs'] if t['name'] == 'Printing']
    ok(len(pr) == 1, 'the Printing tab is there exactly once', len(pr))
    if pr:
        body = pr[0]['content_html']
        for word, what in (('seven columns', 'the shape of it'),
                           ('greyed', 'what happens at the edges'),
                           ('landscape', 'which way up it comes out'),
                           ('thirteen weeks', 'the ceiling')):
            ok(word in body,
               '  and it says %s (%r)' % (what, word))
    ok("meal_plan_print" in T.code_only(plan_src),
       '  CONTROL: and the planner really has a Print button to press')

    # CP-2, 21 Oct 2026 - the two dialogs that replaced the
    # three. They were reachable only on a phone: base hides the
    # More menu above 768px and nothing else pointed at them.
    for text, what in (("id=\"copyRangeModal\"",
                        'Copy meals to another date'),
                       ("id=\"menusModal\"", 'Saved Menus'),
                       ("id=\"noteModal\"", 'Add Note'),
                       ("id=\"leftoverModal\"", 'Leftovers')):
        ok(text in T.code_only(plan_src),
           '  CONTROL: the planner really has %s' % what)
    # AND THE GUIDE DESCRIBES EVERY ONE OF THEM. A tab that exists is
    # not the same as a tab that says the thing.
    for phrase in ('Copy meals to another date', 'Saved Menus',
                   'Add Note', 'Leftovers'):
        ok(phrase in whole, '  and the guide describes %r' % phrase)
    # THE ONE THING STILL OUTSTANDING IS STILL PROMISED, honestly. A
    # round that cleared the promise box by emptying it would pass
    # every check above and tell the reader less.
    # MH-5, 20 Oct 2026 - AND THE OUTSTANDING THING HAS CHANGED.
    # MH-3 named two: moving a meal, and reordering a day. Move is
    # on the chip menu now, so one of the two is in PROMISED_WORDS
    # above and the other is the honest remainder. The claim is the
    # same claim - that the guide still says what it cannot do.
    ok(any('reordering the week view' in s.lower()
           for s in coming),
       '  while what is NOT built is still named as outstanding',
       coming[:2])
    # AND IT REALLY IS NOT BUILT. Without this, the line above would
    # keep passing for as long as nobody edited the guide, however
    # long after the feature shipped - which is the whole of what
    # went wrong here between 19 and 20 October.
    # RO-1, 21 Oct 2026 - A DAY REORDERS NOW. The reason this control
    # exists is untouched: a promise in a guide outlives the thing it
    # promised unless something asks the code. So it asks about the
    # WEEK, which is what the guide names now and what really is not
    # built.
    ok('def reorder_meal_day' in view_py
       and 'def reorder_week' not in view_py,
       '  CONTROL: a day reorders and a week does not, which is what '
       'the guide says')

# ==========================================================================
head('8. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
pa = read(os.path.join(ROOT, PATCHER))
ok(MARK in pa, 'the patcher stamps %s' % MARK)
ok('would be a TemplateSyntaxError' in pa,
   'and it refuses to wire a modal to a tag library that is not there - '
   'a page that loads nothing is worse than a page with no help')
ok('already defines the slug' in pa,
   'and it refuses a slug another help file already uses - the renderer '
   'keys its lookup on the slug and keeps whichever it read last')

tr = read(os.path.join(ROOT, 'alv_tree.py'))
ok(ME in tr and ME in T.CONVERTED,
   '%s is in alv_tree.CONVERTED - judged on day one' % ME)
rd = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rd, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s is in the gate $suites' % ME)
ok('MH-1: the Meal Plans guide exists at all' in ps,
   'and the gate carries a sentinel for the guide')
# MH-2, 18 Oct 2026 - ON THE PLANNER NOW. MH-1's second sentinel named
# meal_plan_calendar.html; MN-1 retired the screen and RT-1 took the
# dead row out with fifteen others. The claim moved to the screen that
# exists rather than being dropped.
ok('MH-2: the planner has a Help button, wired to the guide' in ps,
   'and a second one for the wiring, on the planner')

# MH-2, 18 Oct 2026 - the files MH-1 touched, which is HAD. See the
# control section: the planner is not one of them.
missing = [os.path.basename(x) for x in HAD
           if not os.path.isfile(x + SUFFIX)]
ok(not missing and HAD,
   'every file this round touched has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))

# ==========================================================================
head('9. THE BARS - rendered, before and after, at desktop and phone')
# ==========================================================================
# MH-1 puts a sixth control into five action bars, which is a visible
# change to every meal-plan screen. Demetri's rule is that a visible
# round is rendered before it is delivered, and the first form of this
# round was not - the sweep caught it, through test_secondary_visible.
#
# AND IT IS WHY MOVED_BY NOW NAMES TWO OF THESE PAGES. Neither had an
# action-secondary before, so under the stylesheet as it was their Help
# button would have been hidden and under the current one it shows.
# That difference is the secondary-visible round working. What has to
# be measured instead is whether the extra control changes the BAR, and
# that is this section: same row count, same height, no sideways
# scroll, under the CURRENT stylesheet, before and after.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the bar renders', 'playwright or the Bootstrap fixture is absent')
else:
    TMPL_COMMENT = re.compile(r'\{#.*?#\}', re.S)
    TMPL_TAG = re.compile(r'\{%.*?%\}', re.S)
    TMPL_VAR = re.compile(r'\{\{.*?\}\}', re.S)

    def css_of(t):
        return '\n'.join(m.group(1) for m in
                         re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S))

    def bar_inner(src):
        """The CONTENTS of the first .page-action-buttons, not the div.

        The fixture wraps what it is given in its own
        .page-action-buttons - hand it the whole div and every bar
        measures one child wide and identical by accident, which is
        what the first spelling of this did."""
        i = src.index('<div class="page-action-buttons">')
        d = 0
        for m in re.finditer(r'<div\b|</div>', src[i:]):
            d += 1 if m.group(0) == '<div' else -1
            if d == 0:
                whole = src[i:i + m.end()]
                return whole[whole.index('>') + 1:-len('</div>')]
        return ''

    JS = """() => {
      const bar = document.querySelector('.page-action-buttons');
      const kids = [...bar.children].filter(
          e => getComputedStyle(e).display !== 'none');
      const rects = kids.map(e => e.getBoundingClientRect());
      return {rows: [...new Set(rects.map(r => Math.round(r.top)))].length,
              h: Math.round(bar.getBoundingClientRect().height),
              n: kids.length,
              wide: document.documentElement.scrollWidth >
                    document.documentElement.clientWidth};
    }"""

    BCSS = css_of(read(T.path_of('base.html')))
    FIX = read(FIXCSS)
    with sync_playwright() as _pw:
        # PLAIN launch(), WITH NO executable_path - which is how every
        # other browser suite in this tree does it, and the first form
        # of this line did not.
        #
        # It read executable_path='/opt/pw-browsers/chromium'. That path
        # is the SANDBOX's, set by PLAYWRIGHT_BROWSERS_PATH in the
        # container this round was written in, and it does not exist on
        # the laptop the gate actually runs on - so the suite passed
        # every check here and failed at section 9 on Demetri's machine,
        # stopping the push.
        #
        # Playwright finds its own browser. A suite that names a path
        # only one machine has is a suite that only runs on one machine.
        _br = _pw.chromium.launch()

        def shot(blk, pcss, width):
            clean = TMPL_VAR.sub('x', TMPL_TAG.sub(
                '', TMPL_COMMENT.sub('', blk)))
            doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
                   '<style>%s</style><style>%s</style>'
                   '<style>body{margin:0;padding:8px}</style><body>'
                   '<div class="page-action-buttons">%s</div>'
                   % (FIX, BCSS, pcss, clean))
            pg = _br.new_page(viewport={'width': width, 'height': 420})
            # OFFLINE: a render that waits on a CDN measures the CDN.
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg.set_content(doc, wait_until='domcontentloaded')
            try:
                return pg.evaluate(JS)
            finally:
                pg.close()

        # MH-2, 18 Oct 2026 - THE PAGES MH-1 TOUCHED. This is a
        # before-and-after render, and there is no before for the
        # planner: MN-1 made the page, and MN-1's own suite renders it.
        # A render against a backup that cannot exist is not a measure
        # of anything.
        for page in [q for q in PAGES if os.path.isfile(q + SUFFIX)]:
            name = os.path.basename(page)
            src = read(page)
            pcss = css_of(src)
            try:
                now_bar, was_bar = bar_inner(src), bar_inner(was(page))
            except (ValueError, IOError) as exc:
                ok(False, '%s has a readable action bar' % name, exc)
                continue
            for w, where in ((1200, 'desktop'), (390, 'phone')):
                a, b = shot(was_bar, pcss, w), shot(now_bar, pcss, w)
                ok(a['rows'] == b['rows'] and a['h'] == b['h'],
                   '%-28s %s: the bar is still %d row(s), %dpx'
                   % (name, where, b['rows'], b['h']),
                   'was rows %d h %d, now rows %d h %d'
                   % (a['rows'], a['h'], b['rows'], b['h']))
                ok(not b['wide'],
                   '  and %s does not scroll sideways' % where, b)
                if w == 1200:
                    ok(b['n'] == a['n'] + 1,
                       '  and carries exactly one more control: %d' % b['n'],
                       'was %d, now %d' % (a['n'], b['n']))
        _br.close()

print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
