# -*- coding: utf-8 -*-
"""apply_meal_guide.py - round MH-2, 18 Oct 2026.

THE GUIDE DESCRIBES THE PLANNER NOW.

Demetri, 18 Oct: "You will also need to fully update the help sections
of the whole meal plan module !!" - and, asked whether to ship the
planner with a stale guide or wait for this round, "Rewrite the guide in
push 1."

WHAT WAS WRONG WITH IT. MH-1 wrote a seven-tab guide for five screens,
on 18 October, and MN-1 replaced four of those five screens the same
afternoon. Three whole tabs then described things nobody could reach:

    The Calendar      a month grid beside a list of named plans, a week
                      that could only open ONE plan, days shaded because
                      they fell inside a plan's range, and a "Change the
                      dates" offer on a day outside it
    Building a Plan   Create and Edit, a required plan name, a start and
                      an end date, and a warning that shortening the
                      range drops the meals that fall outside it
    The Plan Page     a plan opened in full, Duplicate under a new name,
                      and "Delete original" to shift a week

None of that exists. A reader following it would have gone looking for
a Create button on a screen that has none.

WHAT THIS ROUND DOES

    Overview        rewritten - the calendar IS the plan, and a line
                    saying plainly what went on 18 October, for anyone
                    who used the old screens
    The Calendar    rewritten for the one screen that is there
    Building a Plan becomes ADDING A MEAL - press Add Recipe, choose a
                    recipe, press Add Meal; servings come from the
                    recipe and the stepper saves as you press
    The Plan Page   REMOVED. Seven tabs become six, because a week of
                    the planner is not a separate screen and a tab
                    about one would be a tab about nothing
    Shopping List   narrowed from "a plan" to "the week on screen"
    Who Can Do What the verbs that went - duplicate, shift - come out of
                    the edit permission's list
    Tips            rewritten. "Plan once, duplicate after" and "Shift
                    rather than reshape" were both about Duplicate

AND ITS SUITE IS RE-PAIRED, which is the half that matters. MH-1's
section 9 is built on one rule - EVERY STATEMENT IN THE GUIDE IS PAIRED
WITH THE THING IT DESCRIBES, AND THE SCREEN IS THE AUTHORITY - and it
read five screens to do it. It reads the planner and the shopping list
now, and it gained the check the old shape could not have:

    THE GUIDE PROMISES NOTHING THE PLANNER CANNOT DO. Every word the
    retired screens owned - Duplicate, Delete original, plan name,
    Change the dates, Create Meal Plan - is asserted ABSENT from all
    six tabs. That is the check that would have caught this round not
    happening.

Idempotent. Every file backed up to .bak_mealguide. The help file is
parsed and its tab count asserted before anything is written.
"""
import os
import re
import sys

SUFFIX = '.bak_mealguide'
HELP = os.path.join('pages', 'help_content', 'administration.html')
MH = 'test_meal_help.py'
ROUNDS = 'alv_rounds.py'
PATCHER = 'apply_meal_guide.py'
MARK = 'MH-2, 18 Oct 2026'
SLUG = 'meal_plans'
CHECK = False

TABS_WAS = 7
TABS_NOW = 6

# THE WORDS THE RETIRED SCREENS OWNED. Asserted absent from the module
# after the rewrite, by the patcher and again by the suite.
#
# ABSENT MEANS ABSENT, INCLUDING IN A SENTENCE ABOUT THEIR ABSENCE.
# The Overview tab tells anyone who used the old screens what went,
# and it says it in words of its own - "the two screens that made
# them, the page that showed one and the button that copied it" -
# rather than naming the buttons. A gate with an exception in it is
# a gate somebody will widen, and a reader searching the guide for
# Duplicate should find nothing rather than a paragraph.
GONE_WORDS = ('Duplicate', 'Delete original', 'plan name', 'Plan name',
              'Create Meal Plan', 'Change the dates', 'start and an end',
              'The Plan Page', 'end date')


OVERVIEW = '''<article data-tab-slug="mp-overview"
           data-tab-name="Overview"
           data-tab-icon="fa-info-circle">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-calendar-alt" style="color:#28a745;"></i> Meal Plans</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;"><strong>The calendar is the plan.</strong> Meals belong to dates, not to a named plan you have to make first: open the planner, click <strong>Add Recipe</strong> on a day, and that meal is planned. There is nothing to name, nothing to date, and nothing to save.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-calendar-week" style="color:#28a745;"></i> One screen.</strong> A month to pick a week from on the left, and the week you picked opened on the right, a card for each of its seven days. It opens on this week every time.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-shopping-cart" style="color:#28a745;"></i> Then shop for it.</strong> <strong>Shopping List</strong> at the top takes the week you are looking at and turns it into one list &mdash; every ingredient across every meal, added up, converted into what you buy it in, and grouped by aisle.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-users" style="color:#0e7c8b;"></i> Everyone sees the same calendar.</strong> Meals are not private to the person who planned them &mdash; this is deliberate, and it matches the recipes they are built from, which are shared across the whole installation. If you can open Recipes, you can see the planner.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-infinity" style="color:#0e7c8b;"></i> No length, and nothing overlaps.</strong> There is one calendar, so two weeks cannot clash and no plan has to end. Plan a fortnight by planning fourteen days.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-history" style="color:#e6a817;"></i> Past dates are allowed.</strong> Nothing stops you planning backwards, and that is useful: a week filled in after the fact is a record of what you actually ate, and the shopping list will still tell you what it cost in ingredients.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>If you used Meal Plans before 18 October 2026:</strong> the named plans, the two screens that made them, the page that showed one and the button that copied it have all gone. Everything they did, the calendar does in one place &mdash; and the test plans that were there have been cleared.
    </div>
  </article>'''

CALENDAR = '''<article data-tab-slug="mp-calendar"
           data-tab-name="The Calendar"
           data-tab-icon="fa-calendar-week">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-calendar-week" style="color:#28a745;"></i> The Calendar</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Two panels. On the left a month grid, to choose a week from. On the right that week in detail, with a card for each of its seven days and the meals planned on each.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-hand-pointer" style="color:#28a745;"></i> Click a week row</strong> in the month grid and that week opens on the right. The row you chose stays highlighted, so you can always see where you are. <strong>Today</strong> brings you back to this week from wherever you have wandered to.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-circle" style="color:#0e7c8b;"></i> The dots</strong> in the month grid mark days that have at least one meal on them, so you can see at a glance which weeks are planned and which are empty. Today is marked as well, in its own colour.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-arrows-alt-h" style="color:#0e7c8b;"></i> Any week, any month.</strong> The arrows above the month move it; the arrows above the week move the week. Every date is reachable and every date can take a meal &mdash; there is no range to stay inside.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-plus" style="color:#28a745;"></i> Add Recipe</strong> sits on every day card. It opens a picker titled with the date you pressed it on, so there is never a question about which day you are adding to.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-trash-alt" style="color:#dc3545;"></i> The trashcan</strong> beside a meal removes it from that day. It asks first, and it removes the one meal, not the day.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-eye" style="color:#0e7c8b;"></i> The eye</strong> beside a meal opens the recipe itself, in the recipe viewer, so you can read the method without leaving the week behind.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> the week travels with you. Go to the shopping list and come back and you land on the same week, not on this one.
    </div>
  </article>'''

ADDING = '''<article data-tab-slug="mp-build"
           data-tab-name="Adding a Meal"
           data-tab-icon="fa-utensils">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-utensils" style="color:#28a745;"></i> Adding a meal to a day</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Press <strong>Add Recipe</strong> on a day, choose a recipe, press <strong>Add Meal</strong>. That is the whole of it &mdash; there is no form to fill in and no Save button, because there is nothing to save but the meal itself.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-search" style="color:#28a745;"></i> The picker</strong> lists every recipe with its photo and the servings it makes, and it is titled <strong>Add a meal to</strong> the date you came from. <strong>Cancel</strong> or the cross closes it and changes nothing.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-balance-scale" style="color:#0e7c8b;"></i> Servings come from the recipe.</strong> A meal arrives making what the recipe's own yield says it makes. Nothing is assumed and nothing is set to four.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-plus-minus" style="color:#0e7c8b;"></i> The stepper changes them, and saves as you press.</strong> The <strong>&minus;</strong> and <strong>+</strong> beside a meal change how many it is for, and each press is stored straight away. One is the floor &mdash; a meal for nobody is not a meal. The shopping list scales every ingredient by whatever you set here.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-layer-group" style="color:#28a745;"></i> As many meals a day as you like.</strong> Breakfast, lunch and dinner on the same card, in the order you added them. There is no slot to fill and none to leave empty.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper and the day cards are all built for a narrow screen, which is where a week usually gets planned.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> repeating a whole week onto another, saved menus, a free-text note on a day, and marking a meal as leftovers. Moving a meal from one day to another comes with them.
    </div>
  </article>'''

TIPS = '''<article data-tab-slug="mp-tips"
           data-tab-name="Tips"
           data-tab-icon="fa-lightbulb">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-lightbulb" style="color:#28a745;"></i> Getting the most out of it</h6>

    <div style="display:flex; flex-direction:column; gap:12px;">

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-calendar-day"></i> Plan the week you are shopping for.</strong> The shopping list takes the week on screen, so pick the week first and press <strong>Shopping List</strong> second. There is no plan to select from a list any more.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-sliders-h"></i> Set the servings before you shop, not after.</strong> Every ingredient on the list is scaled by the servings on the meal, so the stepper is the dial that decides how much you buy.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-balance-scale"></i> Fix the base units once.</strong> Every ingredient that has a shopping unit set is one more line that lands on the list automatically. The <strong>NOT ON THIS LIST</strong> banner names the ones still missing, so it is a finite job rather than a vague one.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-history"></i> Record, as well as plan.</strong> Past dates take meals like any other, so filling last week in afterwards is a perfectly good note of what you ate.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the picker and the dialogs. The shopping list in particular is meant to be read in the shop.
      </div>

    </div>
  </article>'''


# ============================================ THE TABS THAT ONLY REWORD
# Shopping List: it was written for "a plan". The list itself is
# unchanged - SL-1's three share buttons, the two steps, the missing
# conversion and the NOT ON THIS LIST banner all still describe the
# screen exactly. What moved is WHAT IT SHOPS FOR.
SHOP_EDITS = (
    ('Shopping for a whole plan at once',
     'Shopping for a whole week at once'),
    ('The shopping list walks every recipe in the plan, scales each '
     'ingredient to the servings you planned,',
     'The shopping list walks every meal in the week you were looking '
     'at, scales each ingredient to the servings on that meal,'),
    ('Step 1 &mdash; Review Ingredients.</strong> Everything '
     'the plan needs, with its total.',
     'Step 1 &mdash; Review Ingredients.</strong> Everything '
     'the week needs, with its total.'),
)

# Who Can Do What: the two permissions have not changed at all. Three of
# the verbs behind the edit one have.
PERM_EDITS = (
    ('lets you see the list, the calendar, any plan and any shopping '
     'list. Every plan, not only your own.',
     'lets you see the planner and any shopping list &mdash; every '
     'week of it, not only the days you planned yourself.'),
    ('lets you create, edit, duplicate, shift and delete plans, add and '
     'remove meals, and email a shopping list. Again, on any plan '
     '&mdash; not only the ones you made.',
     'lets you add and remove meals, change their servings, and email a '
     'shopping list. Again, on any day &mdash; not only the ones you '
     'planned yourself.'),
)

# ===================================================== THE SUITE, RE-PAIRED
MH_TABS_WAS = """TABS = ('Overview', 'The Calendar', 'Building a Plan', 'The Plan Page',
        'Shopping List', 'Who Can Do What', 'Tips')"""
MH_TABS_NOW = """# MH-2, 18 Oct 2026 - SEVEN BECAME SIX. 'The Plan Page' went with the
# plan page, and 'Building a Plan' is 'Adding a Meal', because you add a
# meal to a day now rather than building a container first.
TABS = ('Overview', 'The Calendar', 'Adding a Meal',
        'Shopping List', 'Who Can Do What', 'Tips')"""

# The More-menu check in claims() still named view_meal_plan.
MH_MORE_WAS = """    # AND THE MORE MENU, on the one page that has one. Asked of that
    # page only: four of the five have no More menu, so requiring it
    # everywhere would be a claim about markup that does not exist.
    c['view_meal_plan has Help in the More menu too'] = (
        T.code_only(text[VIEWT]).count(
            'data-target="#%sHelpModal"' % SLUG) == 2)
    c['  and the other four have one button each'] = all(
        T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
        for p in (LIST, CAL, CREATE, SHOP))"""
MH_MORE_NOW = """    # MH-2, 18 Oct 2026 - AND NEITHER OF THE TWO HAS A MORE MENU.
    # view_meal_plan was the one page that carried Help in a More menu
    # as well as in its bar, and MN-1 retired it. One button each is
    # the whole claim now, which is simpler and still asked of both.
    c['  and each of the two has one Help button'] = all(
        T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
        for p in PAGES if p in text)"""


# A SENTINEL FOR THE WIRING, because MH-1's second one went with the
# page it named. MH-1 put a row on meal_plan_calendar.html asserting
# that screen had a Help button; MN-1 retired the screen and RT-1 took
# the dead row out with fifteen others. The claim is still worth making
# on the screen that exists.
PS1 = 'Push-PendingChanges.ps1'
SENT_WAS = """    # ------------------------------------------------- MH-1, 18 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-slug="meal_plans"'; What = 'MH-1: the Meal Plans guide exists at all' },"""
SENT_NOW = """    # ------------------------------------------------- MH-1, 18 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-slug="meal_plans"'; What = 'MH-1: the Meal Plans guide exists at all' },
    # ------------------------------------------------- MH-2, 18 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'meal_plansHelpModal'; What = 'MH-2: the planner has a Help button, wired to the guide' },
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Adding a Meal"'; What = 'MH-2: and the guide describes adding a meal to a day, not building a plan' },"""

# THE FOUR THINGS MH-1'S SUITE SAID THAT ONLY HELD FOR FIVE SCREENS.
MH_PAGES_WAS = """    # ---- 2. all five pages carry it
    for p in PAGES:"""
MH_PAGES_NOW = """    # ---- 2. BOTH SCREENS CARRY IT, AND ONLY THE ONES HANDED IN.
    # MH-2, 18 Oct 2026 - the control section reads the tree as MH-1 found
    # it, and the planner is not in that tree at all: MN-1 made it two
    # rounds later, with a Help button already on it. So this walks the
    # pages the CALLER has text for, and the live call still walks both.
    for p in [q for q in PAGES if q in text]:"""

MH_SEVEN_WAS = """    c['  and seven of them, no more'] = (
        mine.count('data-tab-slug="mp-') == 7)"""
MH_SEVEN_NOW = """    # MH-2, 18 Oct 2026 - SIX, AND THE NUMBER COMES FROM TABS. It was
    # written out twice, as a word and as a digit, and a round that
    # changes the tab list should not have to find both.
    c['  and %d of them, no more' % len(TABS)] = (
        mine.count('data-tab-slug="mp-') == len(TABS))"""

# MH-1's control reads every file it touched AS IT FOUND IT. The planner
# is not one of those files: MN-1 created it, with a Help button already
# on it, two rounds after MH-1 ran. A control that demands MH-1's backup
# of a page MH-1 never saw cannot run, and a control that cannot run is
# the whole reason the 17 Oct push failed.
MH_BEFORE_WAS = """try:
    BEFORE = dict((p, was(p)) for p in FILES)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))"""
MH_BEFORE_NOW = """# MH-2, 18 Oct 2026 - THE FILES MH-1 ACTUALLY TOUCHED. The planner was
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
   'looks like' % SUFFIX)"""

MH_MISSING_WAS = """missing = [os.path.basename(x) for x in FILES
           if not os.path.isfile(x + SUFFIX)]
ok(not missing, 'every file this round touched has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))"""
MH_MISSING_NOW = """# MH-2, 18 Oct 2026 - the files MH-1 touched, which is HAD. See the
# control section: the planner is not one of them.
missing = [os.path.basename(x) for x in HAD
           if not os.path.isfile(x + SUFFIX)]
ok(not missing and HAD,
   'every file this round touched has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))"""

MH_SENT_WAS = """ok('MH-1: the calendar has a Help button' in ps,
   'and a second one for the wiring')"""
MH_SENT_NOW = """# MH-2, 18 Oct 2026 - ON THE PLANNER NOW. MH-1's second sentinel named
# meal_plan_calendar.html; MN-1 retired the screen and RT-1 took the
# dead row out with fifteen others. The claim moved to the screen that
# exists rather than being dropped.
ok('MH-2: the planner has a Help button, wired to the guide' in ps,
   'and a second one for the wiring, on the planner')"""


MH_BOTH_WAS = """if BEFORE is not None:
    OLD = claims(BEFORE)
    ok(sorted(OLD) == sorted(LIVE),
       'the same %d claims are asked of both trees' % len(LIVE),"""
MH_BOTH_NOW = """if BEFORE is not None:
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
       'the same %d claims are asked of both trees' % len(OLD),"""

MH_BAR_WAS = """        for page in PAGES:
            name = os.path.basename(page)
            src = read(page)"""
MH_BAR_NOW = """        # MH-2, 18 Oct 2026 - THE PAGES MH-1 TOUCHED. This is a
        # before-and-after render, and there is no before for the
        # planner: MN-1 made the page, and MN-1's own suite renders it.
        # A render against a backup that cannot exist is not a measure
        # of anything.
        for page in [q for q in PAGES if os.path.isfile(q + SUFFIX)]:
            name = os.path.basename(page)
            src = read(page)"""


S9_WAS = '''if up and mod:
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
    ok("min=\\"{{ today|date:'Y-m-d' }}\\"" not in T.code_only(create_src),
       '  and neither date input bounds itself to today - D27')

    # AND THE SHIFT OPTION, which the guide says is on all three.
    ok('wherever you find it' in tabs.get('The Plan Page', ''),
       'the guide says Delete original is on every Duplicate dialog')
    for src, name in ((list_src, 'meal_plans.html'),
                      (cal_src, 'meal_plan_calendar.html'),
                      (view_src, 'view_meal_plan.html')):
        ok('name="delete_original"' in src,
           '  and %s really has it - D28' % name)

'''

S9_NOW = '''if up and mod:
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
    ok('week you were looking at' in guide,
       'the guide says the list is the week you were looking at')
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
    ok('removes it from that day' in guide_cal,
       'the guide says the trashcan removes the one meal')
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
    ok("min=\\"{{ today|date:'Y-m-d' }}\\"" not in T.code_only(plan_src),
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
                     'The Plan Page', 'end date')
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

'''

RD_WAS = """    '.bak_retired',
]"""
RD_NOW = '''    '.bak_retired',
    # MH-2, 18 Oct 2026 - the Meal Plans guide describes the
    # planner. MH-1 wrote seven tabs for five screens and MN-1
    # replaced four of the five the same afternoon.
    '.bak_mealguide',
]'''

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
    raise SystemExit('MH-2 REFUSED: %s' % msg)


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


def module_of(text):
    """(start, end) of the meal_plans <section>, by its slug.

    BY THE SLUG AND NOT BY A HEADING. administration.html carries
    sixteen modules and two of them have the word "Recipe" in their
    comment banner; the slug is the thing the renderer keys on and the
    only thing in the file that is unique by construction.
    """
    i = text.find('<section data-module-slug="%s"' % SLUG)
    if i < 0:
        refuse('%s: no module with slug %r' % (HELP, SLUG))
    j = text.find('</section>', i)
    if j < 0:
        refuse('%s: the %r module never closes' % (HELP, SLUG))
    return i, j


def articles(block):
    """[(slug, start, end)] for every tab in a module block."""
    out = []
    for m in re.finditer(r'<article data-tab-slug="([^"]+)"', block):
        start = m.start()
        end = block.find('</article>', start)
        if end < 0:
            refuse('%s: tab %r never closes' % (HELP, m.group(1)))
        out.append((m.group(1), start, end + len('</article>')))
    return out


def set_article(text, slug, new):
    """Replace one whole <article> by its slug. `new` of None drops it."""
    i, j = module_of(text)
    block = text[i:j]
    hits = [a for a in articles(block) if a[0] == slug]
    if len(hits) != 1:
        refuse('%s: tab %r appears %d time(s), expected exactly 1'
               % (HELP, slug, len(hits)))
    _s, a, b = hits[0]
    if new is None:
        # Take the blank line after it as well, so the file does not
        # grow a gap where a tab used to be.
        tail = block[b:b + 20]
        drop = len(tail) - len(tail.lstrip('\r\n '))
        return text[:i] + block[:a].rstrip() + '\n\n  ' \
            + block[b + drop:] + text[j:]
    return text[:i] + block[:a] + fit(text, new) + block[b:] + text[j:]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    ph = os.path.join(root, HELP)
    h = read(ph)
    h_before = h

    # ---------------------------------------------------------------- 0
    if 'data-tab-name="Adding a Meal"' in h:
        print('MH-2  already applied - the guide describes the planner.')
        return 0

    # ---------------------------------------------------------------- 1
    # MN-1 MUST BE APPLIED. This round rewrites the guide to describe
    # the planner; run against a tree that still has the five screens it
    # would describe a planner nobody can open.
    if not os.path.isfile(os.path.join(root, 'pages', 'templates',
                                       'meal_planner.html')):
        refuse('meal_planner.html is not in the tree. MH-2 describes the '
               'planner; apply MN-1 first.')
    for name in ('meal_plans.html', 'create_meal_plan.html',
                 'view_meal_plan.html', 'meal_plan_calendar.html'):
        if os.path.isfile(os.path.join(root, 'pages', 'templates', name)):
            refuse('%s is still in the tree. MH-2 removes the tabs that '
                   'describe it; apply MN-1 first.' % name)

    i, j = module_of(h)
    names = [a[0] for a in articles(h[i:j])]
    if len(names) != TABS_WAS:
        refuse('%s: the %s module has %d tab(s), expected %d - the guide '
               'has moved since this round was written'
               % (HELP, SLUG, len(names), TABS_WAS))

    # ---------------------------------------------------------------- 2
    # THE THREE REWRITES, THE ONE REMOVAL, AND THE TWO REWORDINGS.
    h = set_article(h, 'mp-overview', OVERVIEW)
    h = set_article(h, 'mp-calendar', CALENDAR)
    h = set_article(h, 'mp-build', ADDING)
    h = set_article(h, 'mp-plan', None)
    h = set_article(h, 'mp-tips', TIPS)
    for old, new in SHOP_EDITS + PERM_EDITS:
        h = swap(h, old, new, '%s (a reworded line)' % HELP)

    # ---------------------------------------------------------------- 3
    # SIX TABS, AND NOT ONE WORD THE RETIRED SCREENS OWNED.
    i, j = module_of(h)
    block = h[i:j]
    names = [a[0] for a in articles(block)]
    if len(names) != TABS_NOW:
        refuse('%s: the rewrite leaves %d tab(s), expected %d'
               % (HELP, len(names), TABS_NOW))
    if 'mp-plan' in names:
        refuse('%s: the plan-page tab survived the removal' % HELP)
    left = [w for w in GONE_WORDS if w in block]
    if left:
        refuse('%s: the guide still promises %s - every one of these '
               'belonged to a screen MN-1 retired'
               % (HELP, ', '.join(repr(w) for w in left)))
    out[ph] = h

    # ---------------------------------------------------------------- 4
    # THE SUITE, RE-PAIRED.
    pm = os.path.join(root, MH)
    m = read(pm)
    m = swap(m, MH_TABS_WAS, MH_TABS_NOW, '%s (the tab names)' % MH)
    m = swap(m, MH_MORE_WAS, MH_MORE_NOW, '%s (the More menu)' % MH)
    m = swap(m, S9_WAS, S9_NOW, '%s (section 9)' % MH)
    m = swap(m, MH_PAGES_WAS, MH_PAGES_NOW, '%s (the pages)' % MH)
    m = swap(m, MH_SEVEN_WAS, MH_SEVEN_NOW, '%s (the tab count)' % MH)
    m = swap(m, MH_BEFORE_WAS, MH_BEFORE_NOW, '%s (the control)' % MH)
    m = swap(m, MH_MISSING_WAS, MH_MISSING_NOW, '%s (the backups)' % MH)
    m = swap(m, MH_SENT_WAS, MH_SENT_NOW, '%s (the sentinel)' % MH)
    m = swap(m, MH_BOTH_WAS, MH_BOTH_NOW, '%s (both trees)' % MH)
    m = swap(m, MH_BAR_WAS, MH_BAR_NOW, '%s (the render)' % MH)
    out[pm] = m

    pp = os.path.join(root, PS1)
    out[pp] = swap(read(pp), SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)

    # ---------------------------------------------------------------- 5
    pr = os.path.join(root, ROUNDS)
    out[pr] = swap(read(pr), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 6
    import ast
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))
        if k.endswith('.html'):
            # THE DELTA, NOT THE BALANCE. Measured 18 Oct:
            # administration.html has never balanced by raw count - 74
            # opens against 71 closes - because three of the opens are
            # inside prose that shows markup. A file that balanced
            # would be the surprise. What must hold is that this round
            # removes exactly ONE tab: one open and one close.
            was_o = h_before.count('<article')
            was_c = h_before.count('</article>')
            if (was_o - val.count('<article'),
                    was_c - val.count('</article>')) != (1, 1):
                refuse('%s: the rewrite changed the tab count by %d open '
                       'and %d close, expected 1 and 1'
                       % (os.path.basename(k),
                          was_o - val.count('<article'),
                          was_c - val.count('</article>')))

    if CHECK:
        print('MH-2 --check')
        print('  tabs       : %d -> %d' % (TABS_WAS, TABS_NOW))
        print('  files      : %d' % len(out))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
        print('  wrote %s' % os.path.relpath(k, root))
    print('MH-2  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_meal_help.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
