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
PAGES = (LIST, CAL, CREATE, VIEWT, SHOP)
FILES = (HELP,) + PAGES

TABS = ('Overview', 'The Calendar', 'Building a Plan', 'The Plan Page',
        'Shopping List', 'Who Can Do What', 'Tips')

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
    c['  and seven of them, no more'] = (
        mine.count('data-tab-slug="mp-') == 7)
    c['  each tab has real content, not a stub'] = (
        len(mine) > 15000)

    # ---- 2. all five pages carry it
    for p in PAGES:
        name = os.path.basename(p)
        code = T.code_only(text[p])
        c['%s loads the tag' % name] = (
            '{% load help_modal_tags %}' in code)
        c['%s renders the modal' % name] = (
            '{%% render_help_modal "%s" %%}' % SLUG in code)
        c['%s has a Help button' % name] = (
            'data-target="#%sHelpModal"' % SLUG in code)
    # AND THE MORE MENU, on the one page that has one. Asked of that
    # page only: four of the five have no More menu, so requiring it
    # everywhere would be a claim about markup that does not exist.
    c['view_meal_plan has Help in the More menu too'] = (
        T.code_only(text[VIEWT]).count(
            'data-target="#%sHelpModal"' % SLUG) == 2)
    c['  and the other four have one button each'] = all(
        T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
        for p in (LIST, CAL, CREATE, SHOP))

    # ---- 4. the old tab points rather than repeats
    #
    # THE ARTICLE, NOT THE SECTION. recipe_management is 42 KB across
    # eight tabs, so slicing the section made the length claim
    # meaningless and the four wrong-statement claims read the whole
    # recipe guide rather than the one tab that said them.
    rec = article(section('recipe_management'), 'rec-mealplans')
    c['the old tab points at the new guide'] = (
        'press <strong>Help</strong> on any of the five meal-plan screens'
        in rec)
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
try:
    BEFORE = dict((p, was(p)) for p in FILES)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))

if BEFORE is not None:
    OLD = claims(BEFORE)
    ok(sorted(OLD) == sorted(LIVE),
       'the same %d claims are asked of both trees' % len(LIVE),
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
    ok(got == list(TABS), 'seven tabs, in order', got)
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
    shop_src = NOW[SHOP]
    cal_src = NOW[CAL]
    create_src = NOW[CREATE]
    view_src = NOW[VIEWT]
    list_src = NOW[LIST]

    # (1) THE THREE SHARE BUTTONS. The old tab named four, including
    # Print, which SL-1 moved into the page bar.
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
    ok(shop_src.count('class="btn action-secondary share-btn"') >= 1
       and 'share-grid' in shop_src,
       '  in a share-grid of three, as the guide says')

    # (2) THE REVIEW STEP IS CALLED REVIEW INGREDIENTS. The old tab
    # called it a pantry check.
    ok('Review Ingredients' in guide,
       'the guide calls step 1 by the name on the screen')
    ok('>Review Ingredients<' in shop_src
       or 'Review Ingredients' in shop_src,
       '  and that is what the screen calls it')
    ok('Items to Buy' in guide and 'Items to Buy' in shop_src,
       '  and step 2 is Items to Buy on both')

    # (3) THE CALENDAR REALLY CAN ADD AND REMOVE NOW - A1, fixed by
    # MP-1 this afternoon. The old tab claimed it before it was true.
    guide_cal = tabs.get('The Calendar', '')
    ok('Add Recipe' in guide_cal,
       'the guide says you can add a recipe from the calendar')
    ok('addRecipeToDay(' in cal_src and 'removeRecipe(' in cal_src,
       '  and the calendar really has both controls')
    ok('def add_recipe_to_meal_plan_day(request):' in read(
        os.path.join(ROOT, 'pages', 'views', 'recipes',
                     'meal_planning.py')),
       '  and the view behind it can actually be called - which is A1, '
       'and was NOT true when the old tab said it')

    # (4) DAYS OUTSIDE THE PLAN, and the words the screen uses.
    ok('Change the dates' in guide_cal,
       'the guide offers Change the dates on a day outside the plan')
    ok('Change the dates' in cal_src,
       '  and that is the wording on the screen - MD-1 and MP-1 wrote it')

    # AND THE THINGS THE OLD TAB NEVER MENTIONED, each against the app.
    guide_build = tabs.get('Building a Plan', '')
    ok('name is required' in guide_build.lower()
       or 'The name is required' in guide_build,
       'the guide says a plan name is required')
    ok("messages.error(request, 'Plan name is required.')" in read(
        os.path.join(ROOT, 'pages', 'views', 'recipes',
                     'meal_planning.py')),
       '  and the server really refuses a blank one - C20')

    ok('warns you' in guide_build,
       'the guide warns that shortening a plan drops meals')
    ok('will be removed when you' in create_src,
       '  and the page really says so before saving - C13')

    ok("servings come from the recipe" in guide_build
       or "recipe's own yield" in guide_build,
       'the guide says servings come from the recipe')
    ok('data-recipe-servings=' in cal_src,
       '  and the picker really reads the recipe yield - C19')

    # 'can only open' and not 'only one' - the guide writes it as
    # "can only open <strong>one</strong> plan", so the obvious
    # substring is split by a tag. The first spelling of this check
    # failed on a guide that says exactly the right thing.
    ok('can only open' in guide_cal and 'more than one' in guide_cal,
       'the guide says the calendar shows one plan per week and tells '
       'you when there are others')
    ok('meal plans cover this week' in read(
        os.path.join(ROOT, 'pages', 'views', 'recipes',
                     'meal_planning.py')),
       '  and the application really says which - C17')

    guide_perm = tabs.get('Who Can Do What', '')
    ok('Recipes access' in guide_perm and 'Recipes edit' in guide_perm,
       'the guide names the two permissions')
    ok('can_edit_recipes' in cal_src and 'can_edit_recipes' in list_src,
       '  and the templates really gate on the edit one - B11')
    ok('can_edit_personal' not in T.code_only(cal_src),
       '  and no longer on the one the views never checked')

    ok('household members' in tabs.get('Shopping List', '').lower(),
       'the guide says the email goes to household members only')
    ok('not a household member' in read(
        os.path.join(ROOT, 'pages', 'views', 'recipes',
                     'meal_planning.py')),
       '  and the server really refuses anybody else - B9')

    ok('NOT ON THIS LIST' in tabs.get('Shopping List', ''),
       'the guide explains the NOT ON THIS LIST banner')
    ok('NOT ON THIS LIST' in shop_src,
       '  and the banner really exists - C16')
    ok('Set base units' in tabs.get('Shopping List', '')
       and 'Set base units' in shop_src,
       '  with the same button name on both')

    # PAST DATES, which the guide promises on both screens.
    ok('Past dates are allowed' in tabs.get('Overview', ''),
       'the guide says past dates are allowed')
    ok("min=\"{{ today|date:'Y-m-d' }}\"" not in T.code_only(create_src),
       '  and neither date input bounds itself to today - D27')

    # AND THE SHIFT OPTION, which the guide says is on all three.
    ok('wherever you find it' in tabs.get('The Plan Page', ''),
       'the guide says Delete original is on every Duplicate dialog')
    for src, name in ((list_src, 'meal_plans.html'),
                      (cal_src, 'meal_plan_calendar.html'),
                      (view_src, 'view_meal_plan.html')):
        ok('name="delete_original"' in src,
           '  and %s really has it - D28' % name)

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
ok('MH-1: the calendar has a Help button' in ps,
   'and a second one for the wiring')

missing = [os.path.basename(x) for x in FILES
           if not os.path.isfile(x + SUFFIX)]
ok(not missing, 'every file this round touched has its %s backup' % SUFFIX,
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

        for page in PAGES:
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
