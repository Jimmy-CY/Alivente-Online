# -*- coding: utf-8 -*-
"""apply_meal_guide5.py - round MH-5, 20 Oct 2026.

RELEASE 4, PUSH 3. THE GUIDE CATCHES UP WITH THE CALENDAR.

Demetri's standing instruction: "You will also need to fully update
the help sections of the whole meal plan module !!"

MH-3 LEFT IT ON 19 OCTOBER. Twenty-nine rounds have landed on the
planner since, and the guide still describes the screen MV-2 retired:

    "Two panels. On the left a month grid, to choose a week from. On
     the right that week in detail."

There are no two panels. There is one calendar at three zoom levels.
The Calendar tab then tells a reader to "click a week row in the month
grid and that week opens on the right", to use "the trashcan beside a
meal" and "the eye beside a meal" - three controls that have not
existed since CH-1 made a meal a chip with a menu on it.

A GUIDE THAT DESCRIBES A SCREEN NOBODY HAS is worse than no guide:
a reader who cannot find the control concludes the feature is missing,
and the controls are the whole point of three pushes.

WHAT THIS ROUND DOES

    THE CALENDAR, REWRITTEN. Three views and the switcher, the date
    bar and what its arrows move, the chip and the four things on its
    menu, and a day being a day in every view. The two-panel prose,
    the week-row click, the trashcan and the eye all go.

    ADDING A MEAL grows the three ways in that did not exist when it
    was last written: the picker that stays open with a strip of the
    day under it, the Note button inside that picker, and the library
    route - a calendar beside the heart, three shortcuts, and an Undo
    in the toast. Its promise box is rewritten to promise the one
    thing still outstanding.

    A NEW TAB - Printing. PP-1 shipped a printable plan today and
    there was nowhere to describe it: the Shopping List tab is about
    a list, and this is about a calendar on paper. Eight tabs where
    MH-3 left seven, and the two suite pins that count them move
    with it.

    SHOPPING LIST learns that its range follows the view, which SL-7
    changed this morning - a month buys for a month now - and that
    the list page itself takes a from/to pair.

    TIPS. Two go stale with SL-7 and PP-1 and are rewritten; two are
    added for the two features most likely to go unused because
    nobody knew they were there.

    AND THE GATE GROWS BY NINE WORDS. PROMISED_WORDS is MH-3's
    register of features the planner already has, asserted absent
    from any sentence calling something coming. RETIRED_WORDS is
    MH-2's register of words from screens that are gone. This round
    adds to both - the retired half with the controls CH-1 replaced,
    which is the half that would have caught this round's own
    subject a day earlier.

WHAT IS STILL OUTSTANDING, AND SAID SO HONESTLY: reordering the meals
on a day. Moving one from day to day, which MH-3 listed beside it, is
on the chip menu now.

Idempotent. Every file backed up to .bak_mealguide5.
"""
import os
import re
import sys

SUFFIX = '.bak_mealguide5'
HELP = os.path.join('pages', 'help_content', 'administration.html')
PLAN = os.path.join('pages', 'templates', 'meal_planner.html')
MH = 'test_meal_help.py'
G3 = 'test_meal_guide3.py'
ME = 'test_meal_guide5.py'
PATCHER = 'apply_meal_guide5.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MH-5, 20 Oct 2026'
SLUG = 'meal_plans'
CHECK = False
CREATES = ()

TABS_WAS_N = 7
TABS_NOW_N = 8

GREEN = '#28a745'
TEAL = '#0e7c8b'
BOX = ('background:#f8f9fa; border-radius:8px; padding:12px; '
       'border-left:4px solid %s; font-size:13px; color:#6c757d;')
TIP = ('background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; '
       'padding:12px; font-size:13px; color:#155724;')


# =====================================================================
# THE CALENDAR TAB - the screen MV-2 retired is still described here
# =====================================================================

CAL_LEAD_WAS = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Two panels. On the left a month grid, to choose a week from. On the right that week in detail, with a card for each of its seven days and the meals planned on each.</p>"""

CAL_LEAD_NOW = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">One calendar, at three zoom levels. <strong>Month</strong> for the shape of a month, <strong>Week</strong> for seven days side by side, <strong>Day</strong> for one day in full. The same meals, the same dates, drawn three ways &mdash; and the view you are in decides what the buttons at the top act on.</p>"""

# The three boxes that describe the retired two-panel screen, in the
# order they appear. Each is swapped for what is really there.
CAL_ROW_WAS = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-hand-pointer" style="color:#28a745;"></i> Click a week row</strong> in the month grid and that week opens on the right. The row you chose stays highlighted, so you can always see where you are. <strong>Today</strong> brings you back to this week from wherever you have wandered to.
      </div>"""

CAL_ROW_NOW = """      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-layer-group" style="color:%s;"></i> Month, Week, Day</strong> is a switcher on the bar at the top, and it is the first thing to decide: everything else on that bar follows it. <strong>Today</strong> returns you to today at whatever zoom you are on.
      </div>

      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-hand-pointer" style="color:%s;"></i> A day is a day in every view.</strong> Click one in the month and it opens in Day; click one in the week and the same thing happens. You are never dropped somewhere you did not ask for, and a dialog returns you to the day you were on.
      </div>""" % (BOX % GREEN, GREEN, BOX % TEAL, TEAL)

CAL_ARROWS_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-arrows-alt-h" style="color:#0e7c8b;"></i> Any week, any month.</strong> The arrows above the month move it; the arrows above the week move the week. Every date is reachable and every date can take a meal &mdash; there is no range to stay inside."""

CAL_ARROWS_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-arrows-alt-h" style="color:#0e7c8b;"></i> The arrows move by whatever you are looking at.</strong> A month in Month, a week in Week, a day in Day &mdash; one pair of arrows, and they always step by the unit on screen. Every date is reachable and every date can take a meal; there is no range to stay inside."""

CAL_ADD_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-plus" style="color:#28a745;"></i> Add Recipe</strong> sits on every day card. It opens a picker titled with the date you pressed it on, so there is never a question about which day you are adding to."""

CAL_ADD_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-plus" style="color:#28a745;"></i> Add on any day, in any view.</strong> Every day carries a way in &mdash; the <strong>+</strong> on a month cell, the one on a week column, <strong>Add Recipe</strong> on the day card &mdash; and all three open the same picker, titled with the date you pressed."""

# THE TRASHCAN AND THE EYE. Both gone since CH-1: a meal is a chip and
# the chip has a menu. Two boxes become one, because they describe one
# control now.
CAL_BIN_WAS = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-trash-alt" style="color:#dc3545;"></i> The trashcan</strong> beside a meal removes it from that day. It asks first, and it removes the one meal, not the day.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-eye" style="color:#0e7c8b;"></i> The eye</strong> beside a meal opens the recipe itself, in the recipe viewer, so you can read the method without leaving the week behind.
      </div>"""

CAL_BIN_NOW = """      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-ellipsis-h" style="color:%s;"></i> A meal is a chip, and the chip has a menu.</strong> Click one and four things are offered: <strong>View</strong> opens the recipe without leaving the calendar, <strong>Move</strong> puts it on another day, <strong>Leftovers</strong> puts a free second helping on a later one, and <strong>Remove</strong> takes it off &mdash; the one meal, not the day. A note has only Move and Remove, because there is no recipe behind it to view or to have leftovers of.
      </div>

      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-tint" style="color:%s;"></i> The colours mean something.</strong> A leftover is drawn quieter than the meal it came from and says so, and a note is drawn differently again. At a glance a week tells you which nights are cooking and which are not.
      </div>""" % (BOX % TEAL, TEAL, BOX % TEAL, TEAL)

CAL_TIP_WAS = """      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> the week travels with you. Go to the shopping list and come back and you land on the same week, not on this one."""

CAL_TIP_NOW = """      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> where you are travels with you. Go to the shopping list, print a plan, open a recipe, add a note &mdash; and you come back to the same view on the same day, not to this week."""


# =====================================================================
# ADDING A MEAL - three ways in that did not exist when it was written
# =====================================================================

BUILD_PICK_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-search" style="color:#28a745;"></i> The picker</strong> lists every recipe with its photo and the servings it makes, and it is titled <strong>Add a meal to</strong> the date you came from. <strong>Cancel</strong> or the cross closes it and changes nothing."""

BUILD_PICK_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-search" style="color:#28a745;"></i> The picker adds on a click, and stays open.</strong> It lists every recipe with its photo and the servings it makes, titled <strong>Add a meal to</strong> the date you came from, and it searches and filters exactly as the recipe library does. Click a recipe and it is on the day &mdash; no second button &mdash; and the strip underneath shows what is on that day so far, so a mis-click is something you can see and undo rather than discover later. <strong>Done</strong> closes it and the calendar comes back with everything you added."""

BUILD_NOTE_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-store" style="color:#28a745;"></i> Add Note, for a night you are not cooking.</strong> Eat out, takeaway, at a friend's. It sits on the day like a meal does, so the week reads as a plan rather than as a plan with holes in it &mdash; and it buys nothing: a note never reaches the shopping list. Three suggestions are offered so a planned night is one tap."""

BUILD_NOTE_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-store" style="color:#28a745;"></i> Add Note, for a night you are not cooking.</strong> Eat out, takeaway, at a friend's. It sits on the day like a meal does, so the week reads as a plan rather than as a plan with holes in it &mdash; and it buys nothing: a note never reaches the shopping list. Three suggestions are offered so a planned night is one tap. <strong>Note</strong> is in the picker's own footer as well, so a night you are not cooking does not need the picker closed first."""

BUILD_PHONE_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper, the two Add buttons and the day cards are all built for a narrow screen, which is where a week usually gets planned."""

BUILD_PHONE_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-calendar-plus" style="color:#e6a817;"></i> Or from the recipe library, without opening the planner at all.</strong> Every recipe card carries a calendar beside its heart. Press it and three shortcuts are offered &mdash; <strong>Today</strong>, <strong>Tomorrow</strong> and this <strong>Saturday</strong> &mdash; with a small month underneath for any other date. The meal is added where you stand, and the message that confirms it carries an <strong>Undo</strong>.
      </div>

      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-image" style="color:%s;"></i> And the photo is a quick look.</strong> Clicking a recipe's picture in the library opens it to read &mdash; ingredients, method, servings &mdash; without leaving the list you were browsing. It is the fastest way to decide whether a recipe is tonight's before you plan it.
      </div>

      <div style="%s">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper, the chip menu, the calendar button and the day cards are all built for a narrow screen, which is where a week usually gets planned.""" % (BOX % TEAL, TEAL, BOX % '#ffc107')

BUILD_PROMISE_WAS = """      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> moving a meal from one day to another, and reordering the meals on a day. Everything else this tab used to list as coming is now on the <strong>Moving a Week</strong> tab or above."""

BUILD_PROMISE_NOW = """      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> reordering the meals on a day. Moving one from day to day, which stood here beside it, is <strong>Move</strong> on the chip menu now."""


# =====================================================================
# SHOPPING LIST - SL-7 changed what it buys for
# =====================================================================

SHOP_LEAD_WAS = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">The shopping list walks every meal in the week you were looking at, scales each ingredient to the servings on that meal, converts it into the unit you actually buy that ingredient in, adds up the totals across recipes, rounds <strong>up</strong> so you never come home short, and groups the result by aisle.</p>"""

SHOP_LEAD_NOW = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">The shopping list walks every meal in the range you were looking at, scales each ingredient to the servings on that meal, converts it into the unit you actually buy that ingredient in, adds up the totals across recipes, rounds <strong>up</strong> so you never come home short, and groups the result by aisle.</p>

    <div style="%s">
      <strong style="color:#2c3e50;"><i class="fas fa-calendar-check" style="color:%s;"></i> It buys for what you are looking at.</strong> Press <strong>Shopping List</strong> in Month and it buys for the month; in Week, for that week; in Day, for that day. The button follows the view rather than always meaning a week, so there is nothing to set before you press it.
    </div>

    <div style="%s">
      <strong style="color:#2c3e50;"><i class="fas fa-sliders-h" style="color:%s;"></i> And any other stretch of days.</strong> The list page itself carries a <strong>From</strong> and a <strong>To</strong>. A long weekend, ten days, the fortnight before a holiday &mdash; none of which is a view, and all of which is a shop.
    </div>""" % (BOX % GREEN, GREEN, BOX % TEAL, TEAL)


# =====================================================================
# THE NEW TAB - PP-1 shipped a printable plan and nothing described it
# =====================================================================

PRINT_TAB = """  <article data-tab-slug="mp-print"
           data-tab-name="Printing"
           data-tab-icon="fa-print">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid %(g)s; padding-bottom:6px;"><i class="fas fa-print" style="color:%(g)s;"></i> Putting a plan on the fridge</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;"><strong>Print</strong> on the planner opens a page built for paper rather than for a screen: a grid of seven columns for each week, the meals written into the days, and none of the application around it. What comes out is a calendar you can pin up.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="%(green)s">
        <strong style="color:#2c3e50;"><i class="fas fa-calendar-check" style="color:%(g)s;"></i> It prints what you are looking at.</strong> Like the shopping list, the <strong>Print</strong> button takes the view you are in &mdash; a month, a week or a single day &mdash; so there is nothing to choose before you press it.
      </div>

      <div style="%(teal)s">
        <strong style="color:#2c3e50;"><i class="fas fa-sliders-h" style="color:%(t)s;"></i> Or any dates you like.</strong> The printable page takes a <strong>from</strong> and a <strong>to</strong> of its own, the same pair the shopping list takes, up to thirteen weeks at a time.
      </div>

      <div style="%(teal)s">
        <strong style="color:#2c3e50;"><i class="fas fa-border-all" style="color:%(t)s;"></i> Whole weeks, always.</strong> A range that starts on a Wednesday still prints Monday to Sunday, with the days outside what you asked for greyed. Three blank cells at the front of a week read as missing data; a greyed Monday reads as a boundary.
      </div>

      <div style="%(teal)s">
        <strong style="color:#2c3e50;"><i class="fas fa-file-alt" style="color:%(t)s;"></i> Landscape, and a week never splits.</strong> The page asks your printer for landscape, because seven columns want the wider sheet, and no week is ever broken across two pages.
      </div>

      <div style="%(amber)s">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> On a phone</strong> the bar has room for one button, so <strong>Print this plan</strong> sits in the <strong><i class="fas fa-ellipsis-v"></i></strong> menu beside it &mdash; and the printable page itself folds to two columns to be read on the way to the shop.
      </div>

    </div>

    <div style="%(tip)s">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> print the month at the start of it and the week on the Sunday. The month is the one that goes on the fridge; the week is the one that tells you what to take out of the freezer.
    </div>
  </article>

""" % {'g': GREEN, 't': TEAL, 'green': BOX % GREEN, 'teal': BOX % TEAL,
       'amber': BOX % '#ffc107', 'tip': TIP}


# =====================================================================
# TIPS - two went stale this morning
# =====================================================================

TIP_WEEK_WAS = """        <strong><i class="fas fa-calendar-day"></i> Plan the week you are shopping for.</strong> The shopping list takes the week on screen, so pick the week first and press <strong>Shopping List</strong> second. There is no plan to select from a list any more."""

TIP_WEEK_NOW = """        <strong><i class="fas fa-calendar-day"></i> Choose the view, then press the button.</strong> Both <strong>Shopping List</strong> and <strong>Print</strong> take whatever is on screen &mdash; a month, a week or a day. Switching the view is how you choose what they act on, and it is the only step there is."""

TIP_PHONE_WAS = """        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the picker and the dialogs. The shopping list in particular is meant to be read in the shop."""

TIP_PHONE_NOW = """        <strong><i class="fas fa-calendar-plus"></i> Plan from the library, not from the calendar.</strong> When you are browsing recipes rather than filling a week, the calendar beside a recipe's heart is quicker than opening the planner: Today, Tomorrow or Saturday in one press, with an Undo if you misfire.
      </div>

      <div style="%s">
        <strong><i class="fas fa-print"></i> Paper beats a phone on a Tuesday.</strong> A printed week on the fridge is read by everybody in the house without anybody logging in, and it is the cheapest way to stop the six o'clock question.
      </div>

      <div style="%s">
        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the picker and the dialogs. The shopping list in particular is meant to be read in the shop.""" % (TIP, TIP)


# ===================================================== THE SUITE, RE-PINNED

MH_TABS_WAS = """TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Who Can Do What', 'Tips')"""

MH_TABS_NOW = """#
# MH-5, 20 Oct 2026 - AND SEVEN BECAME EIGHT. 'Printing' is PP-1's
# printable plan, and it is not 'Shopping List', because that tab is
# about a list of things to buy and this is about a calendar on paper.
# It sits after Shopping List, which is the order the two buttons sit
# in on the planner bar.
TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Printing', 'Who Can Do What', 'Tips')"""

# THE TWO REGISTERS GROW.
#
# RETIRED_WORDS holds words from screens and controls the planner no
# longer has. It is the half that would have caught this round's own
# subject a day earlier: the Calendar tab still said "the trashcan
# beside a meal" and "the eye beside a meal" a month after CH-1
# replaced both with a chip menu, and nothing asked.
MH_RETIRED_WAS = """    RETIRED_WORDS = ('Duplicate', 'Delete original', 'plan name',
                     'Create Meal Plan', 'Change the dates',
                     'The Plan Page', 'end date')"""

MH_RETIRED_NOW = """    RETIRED_WORDS = ('Duplicate', 'Delete original', 'plan name',
                     'Create Meal Plan', 'Change the dates',
                     'The Plan Page', 'end date',
                     # MH-5, 20 Oct 2026 - the controls CH-1 replaced
                     # with a chip menu, and the two-panel screen MV-2
                     # replaced with three views. The guide described
                     # all four for a month and nothing asked.
                     'The trashcan', 'The eye', 'Two panels',
                     'Click a week row')"""

MH_PROMISE_WAS = """    PROMISED_WORDS = ('repeating a whole week', 'saved menus',
                      'a free-text note on a day',
                      'marking a meal as leftovers')"""

MH_PROMISE_NOW = """    PROMISED_WORDS = ('repeating a whole week', 'saved menus',
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
                      'a quick look at a recipe')"""

# THREE PINS THAT PIN A SCREEN THAT CHANGED.
#
# MH-1 and MH-2 wrote these against the planner of 18 October, and
# each asserts a SENTENCE the guide no longer carries because the
# thing it describes is no longer true. They are moved, not deleted:
# the question each was asking is still the right question, and the
# answer is what moved.
#
#   (3)  "the week you were looking at"  - SL-7 made it a range.
#   (5)  "the trashcan"                  - CH-1 made it a chip menu.
#   (p)  "moving a meal ... is coming"   - the chip menu does it.
MH_WEEK_WAS = """    ok('week you were looking at' in guide,
       'the guide says the list is the week you were looking at')"""

MH_WEEK_NOW = """    # MH-5, 20 Oct 2026 - A RANGE, NOT A WEEK. SL-7 made the
    # Shopping List button follow the view, so the list is a month
    # from Month and a day from Day; and the list page itself takes
    # a from/to pair. 'the week you were looking at' was the true
    # sentence on 18 October and became a false one this morning.
    ok('range you were looking at' in guide,
       'the guide says the list is the range you were looking at')
    ok('buys for the month' in guide and 'for that day' in guide,
       '  and spells out that the view decides it')"""

MH_BIN_WAS = """    ok('removes it from that day' in guide_cal,
       'the guide says the trashcan removes the one meal')"""

MH_BIN_NOW = """    # MH-5, 20 Oct 2026 - THERE IS NO TRASHCAN. CH-1 made a meal a
    # chip with a menu on it, and Remove is one of four things on
    # that menu. What this check was really asking - does the guide
    # say removal takes the meal and not the day - is asked of the
    # sentence that says it now.
    ok('the one meal, not the day' in guide_cal,
       'the guide says Remove takes the one meal, not the day')
    for act in ('View', 'Move', 'Leftovers', 'Remove'):
        ok('<strong>%s</strong>' % act in guide_cal,
           '  and the chip menu offers %s' % act)"""

MH_OUTSTANDING_WAS = """    ok(any('moving a meal from one day to another' in s.lower()
           for s in coming),
       '  while what is NOT built is still named as coming', coming[:2])"""

MH_OUTSTANDING_NOW = """    # MH-5, 20 Oct 2026 - AND THE OUTSTANDING THING HAS CHANGED.
    # MH-3 named two: moving a meal, and reordering a day. Move is
    # on the chip menu now, so one of the two is in PROMISED_WORDS
    # above and the other is the honest remainder. The claim is the
    # same claim - that the guide still says what it cannot do.
    ok(any('reordering the meals on a day' in s.lower()
           for s in coming),
       '  while what is NOT built is still named as outstanding',
       coming[:2])
    # AND IT REALLY IS NOT BUILT. Without this, the line above would
    # keep passing for as long as nobody edited the guide, however
    # long after the feature shipped - which is the whole of what
    # went wrong here between 19 and 20 October.
    ok('def reorder' not in view_py,
       '  CONTROL: and there is still no way to reorder a day')"""

# AND THE NEW TAB IS REALLY DESCRIBED. An eighth name in TABS proves a
# tab exists; it does not prove it says anything. The planner has to
# hold the control and the guide has to hold the word.
MH_SAYS_WAS = """    for text, what in (("id=\\"copyWeekModal\\"", 'Copy this week to'),"""

MH_SAYS_NOW = """    # MH-5, 20 Oct 2026 - THE EIGHTH TAB SAYS SOMETHING. A name in
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

    for text, what in (("id=\\"copyWeekModal\\"", 'Copy this week to'),"""


# =====================================================================
# MH-3's OWN SUITE, RE-PINNED
# =====================================================================
#
# test_meal_guide3.py judges the guide against the guide of 19
# October, which is its job - but four of its pins are counts and
# lists, and this round changes all four. MH-3 did exactly this to
# MH-2's pins and wrote down why: a pin that is moved with the thing
# it pins stays a pin, and a pin nobody moves becomes a failure
# nobody reads.
G3_ORDER_WAS = """ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-permissions', 'mp-tips')"""
G3_ORDER_NOW = """# MH-5, 20 Oct 2026 - AND AN EIGHTH, after Shopping List: PP-1's
# printable plan. It sits there because that is the order the two
# buttons sit in on the planner bar, and a guide that disagrees with
# the screen about order is a guide somebody stops trusting.
ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-permissions', 'mp-tips')"""

G3_OUT_WAS = """# And the one that is not built, which must still be promised.
OUTSTANDING = 'moving a meal from one day to another'"""
G3_OUT_NOW = """# And the one that is not built, which must still be promised.
#
# MH-5, 20 Oct 2026 - MOVE SHIPPED. CH-1 put it on the chip menu, so
# the sentence this pin was watching for would now be a lie. The
# claim is unchanged - the guide still says what it cannot do - and
# what it cannot do is the other half of MH-3's pair.
OUTSTANDING = 'reordering the meals on a day'"""

G3_SEVEN_WAS = """    c['the module has seven tabs'] = len(tabs) == 7"""
G3_SEVEN_NOW = """    c['the module has %d tabs' % len(ORDER)] = len(tabs) == len(ORDER)
    c['  and mp-print is one of them'] = 'mp-print' in slugs
    c['  called Printing'] = names.get('mp-print') == 'Printing'"""

G3_PARSE_WAS = """    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Who Can Do What',
               'Tips'],
       'seven named tabs, in order, out of the real parser', got)"""
G3_PARSE_NOW = """    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)"""

G3_ART_WAS = """ok(blk.count('<article') == blk.count('</article>') == 7,
   'seven <article> open and seven close - %d and %d'
   % (blk.count('<article'), blk.count('</article>')))"""
G3_ART_NOW = """ok(blk.count('<article') == blk.count('</article>') == len(ORDER),
   '%d <article> open and %d close - %d and %d'
   % (len(ORDER), len(ORDER),
      blk.count('<article'), blk.count('</article>')))"""

# THE RENDER PINS. MH-3 froze the six tabs it did not touch and let
# the two it did GROW - `b > a['h']`. MH-5 touches four, and one of
# the four DELETES more than it writes: the Calendar tab loses the
# two-panel paragraph, the week-row click, the trashcan and the eye.
# Measured, it still ends up taller (540 -> 673 at 1200px), because
# what replaced them is longer again - but that is an accident of this
# round's prose, not a property of the claim. A round that trims a tab
# is a correct round, and `>` would call it a failure. What is really
# being asserted is that these four MOVED and the other four did not.
G3_HEIGHT_WAS = """                if slug in ('mp-build', 'mp-tips'):
                    ok(b > a['h'],
                       '%-16s %-7s grew, as this round intends: %d -> %d'
                       % (slug, where, a['h'], b), (a['h'], b))"""
G3_HEIGHT_NOW = """                # MH-5, 20 Oct 2026 - FOUR MOVE NOW, NOT TWO, and
                # the test is `!=` rather than `>`. mp-calendar
                # DELETES four pieces of prose about controls that no
                # longer exist; a round that trims a tab is a correct
                # round and `>` would call it a failure. (This one
                # happens to end up taller anyway, 540 -> 673, but a
                # pin that depends on that is a pin waiting to break.)
                if slug in ('mp-build', 'mp-tips', 'mp-calendar',
                            'mp-shopping'):
                    ok(b != a['h'],
                       '%-16s %-7s moved, as this round intends: '
                       '%d -> %d' % (slug, where, a['h'], b),
                       (a['h'], b))"""

G3_NEWTAB_WAS = """            for slug in ORDER:
                if slug == 'mp-week':
                    continue"""
G3_NEWTAB_NOW = """            for slug in ORDER:
                # mp-print has no 'before' to compare against either -
                # MH-5 creates it, as MH-3 created mp-week.
                if slug in ('mp-week', 'mp-print'):
                    continue"""

G3_TALL_WAS = """            tallest = max(heights[(s, w)] for s in ORDER if s != 'mp-week')"""
G3_TALL_NOW = """            tallest = max(heights[(s, w)] for s in ORDER
                          if s not in ('mp-week', 'mp-print'))"""


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
    raise SystemExit('MH-5 REFUSED: %s' % msg)


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


def section(text):
    """The meal_plans section of the help file, and nowhere else.

    administration.html holds five modules. Every anchor below is
    asked of this slice, so a sentence that also appears under
    recipe_management cannot be the one that gets rewritten.
    """
    i = text.index('<section data-module-slug="%s"' % SLUG)
    j = text.index('<section data-module-slug=', i + 10)
    return i, j, text[i:j]


def tab_names(blob):
    return re.findall(r'data-tab-name="([^"]*)"', blob)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    ph = os.path.join(root, HELP)
    h = read(ph)

    if 'data-tab-slug="mp-print"' in h:
        print('MH-5  already applied - the guide has its Printing tab.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    i, j, sec = section(h)
    names = tab_names(sec)
    if len(names) != TABS_WAS_N:
        refuse('%s: %s has %d tab(s), expected %d - another round has '
               'moved this guide and the anchors below are stale'
               % (HELP, SLUG, len(names), TABS_WAS_N))

    # ---- THE CALENDAR TAB
    s = sec
    s = swap(s, CAL_LEAD_WAS, CAL_LEAD_NOW, 'The Calendar (the lead)')
    s = swap(s, CAL_ROW_WAS, CAL_ROW_NOW, 'The Calendar (the week row)')
    s = swap(s, CAL_ARROWS_WAS, CAL_ARROWS_NOW,
             'The Calendar (the arrows)')
    s = swap(s, CAL_ADD_WAS, CAL_ADD_NOW, 'The Calendar (Add Recipe)')
    s = swap(s, CAL_BIN_WAS, CAL_BIN_NOW,
             'The Calendar (the trashcan and the eye)')
    s = swap(s, CAL_TIP_WAS, CAL_TIP_NOW, 'The Calendar (the tip)')

    # ---- ADDING A MEAL
    s = swap(s, BUILD_PICK_WAS, BUILD_PICK_NOW,
             'Adding a Meal (the picker)')
    s = swap(s, BUILD_NOTE_WAS, BUILD_NOTE_NOW,
             'Adding a Meal (Add Note)')
    s = swap(s, BUILD_PHONE_WAS, BUILD_PHONE_NOW,
             'Adding a Meal (the library route)')
    s = swap(s, BUILD_PROMISE_WAS, BUILD_PROMISE_NOW,
             'Adding a Meal (the promise)')

    # ---- SHOPPING LIST
    s = swap(s, SHOP_LEAD_WAS, SHOP_LEAD_NOW,
             'Shopping List (what it buys for)')

    # ---- THE NEW TAB, between Shopping List and Who Can Do What,
    # which is the order the two buttons sit in on the planner bar.
    s = swap(s, """  <article data-tab-slug="mp-permissions\"""",
             PRINT_TAB + """  <article data-tab-slug="mp-permissions\"""",
             'the Printing tab')

    # ---- TIPS
    s = swap(s, TIP_WEEK_WAS, TIP_WEEK_NOW, 'Tips (the stale week tip)')
    s = swap(s, TIP_PHONE_WAS, TIP_PHONE_NOW, 'Tips (the two new ones)')

    out[ph] = h[:i] + s + h[j:]

    # ---- THE SUITE'S PINS
    pm = os.path.join(root, MH)
    m = read(pm)
    m = swap(m, MH_TABS_WAS, MH_TABS_NOW, '%s (the tab names)' % MH)
    m = swap(m, MH_RETIRED_WAS, MH_RETIRED_NOW,
             '%s (RETIRED_WORDS)' % MH)
    m = swap(m, MH_PROMISE_WAS, MH_PROMISE_NOW,
             '%s (PROMISED_WORDS)' % MH)
    m = swap(m, MH_SAYS_WAS, MH_SAYS_NOW, '%s (the new tab)' % MH)
    m = swap(m, MH_WEEK_WAS, MH_WEEK_NOW, '%s (a range, not a week)' % MH)
    m = swap(m, MH_BIN_WAS, MH_BIN_NOW, '%s (the trashcan)' % MH)
    m = swap(m, MH_OUTSTANDING_WAS, MH_OUTSTANDING_NOW,
             '%s (what is outstanding)' % MH)
    out[pm] = m

    # ---- MH-3's SUITE, which judges this guide against yesterday's
    pg3 = os.path.join(root, G3)
    g = read(pg3)
    g = swap(g, G3_ORDER_WAS, G3_ORDER_NOW, '%s (ORDER)' % G3)
    g = swap(g, G3_OUT_WAS, G3_OUT_NOW, '%s (OUTSTANDING)' % G3)
    g = swap(g, G3_SEVEN_WAS, G3_SEVEN_NOW, '%s (the tab count)' % G3)
    g = swap(g, G3_PARSE_WAS, G3_PARSE_NOW, '%s (the parsed names)' % G3)
    g = swap(g, G3_ART_WAS, G3_ART_NOW, '%s (the article count)' % G3)
    g = swap(g, G3_HEIGHT_WAS, G3_HEIGHT_NOW, '%s (the render pins)' % G3)
    g = swap(g, G3_NEWTAB_WAS, G3_NEWTAB_NOW, '%s (the new tab)' % G3)
    g = swap(g, G3_TALL_WAS, G3_TALL_NOW, '%s (the tallest read)' % G3)
    out[pg3] = g

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    sp = read(pp)
    sp = swap(sp, """    'test_print_plan.py'
)""", """    'test_print_plan.py',
    # MH-5, 20 Oct 2026 - the guide catches up with the calendar, and
    # stops describing two panels, a trashcan and an eye.
    'test_meal_guide5.py'
)""", '%s (the suites)' % PS1)
    sp = swap(sp,
              """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def meal_plan_print(';""",
              """    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-slug="mp-print"'; What = 'MH-5: the meal plans guide has eight tabs and no longer describes the two-panel screen, the trashcan or the eye - none of which has existed since release 4 push 1' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def meal_plan_print(';""",
              '%s (the sentinels)' % PS1)
    out[pp] = sp

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # PP-1, 20 Oct 2026 - the plan on paper, which the application
    # could not do at all.
    'test_print_plan.py',
]""", """    # PP-1, 20 Oct 2026 - the plan on paper, which the application
    # could not do at all.
    'test_print_plan.py',
    # MH-5, 20 Oct 2026 - the guide describes the calendar that is
    # there, rather than the one that was there on 19 October.
    'test_meal_guide5.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # PP-1, 20 Oct 2026 - a meal plan you can put on the fridge.
    '.bak_printplan',
]""", """    # PP-1, 20 Oct 2026 - a meal plan you can put on the fridge.
    '.bak_printplan',
    # MH-5, 20 Oct 2026 - the guide catches up with the calendar.
    '.bak_mealguide5',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # MH-5, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    _i, _j, ns = section(out[ph])
    got = tab_names(ns)
    if len(got) != TABS_NOW_N:
        refuse('%s: %d tab(s) after this round, expected %d'
               % (HELP, len(got), TABS_NOW_N))
    if got != ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips']:
        refuse('%s: the tabs are in the wrong order - %s' % (HELP, got))

    # THE RETIRED SCREEN IS REALLY GONE FROM THE PROSE. This is the
    # round's own subject, asked of its own output: a guide that still
    # says "two panels" has not caught up with anything.
    text = T.code_only(ns)
    for dead, why in (('Two panels', 'MV-2 retired the two-panel layout'),
                      ('Click a week row',
                       'there is no week row to click'),
                      ('The trashcan', 'CH-1 replaced it with a menu'),
                      ('The eye', 'CH-1 replaced it with a menu'),
                      ('opens on the right', 'there is no right panel')):
        if dead in text:
            refuse('%s: the guide still says %r - %s' % (HELP, dead, why))

    # AND THE THINGS IT NOW CLAIMS ARE REALLY ON THE PLANNER.
    # An absence gate alone passes on a guide that says nothing; these
    # are asked of the page the guide is describing.
    plan = T.code_only(read(os.path.join(root, PLAN)))
    for probe, what in (('meal_plan_print', 'a Print button'),
                        ('alv-seg', 'the view switcher'),
                        ("data-act=\"move\"", 'Move on the chip menu'),
                        ("data-act=\"leftovers\"",
                         'Leftovers on the chip menu'),
                        ('pickerNote', 'Note in the picker')):
        if probe not in plan:
            refuse('%s: the guide describes %s and the planner has no '
                   '%r' % (PLAN, what, probe))

    # THE PROMISE IS DOWN TO ONE THING, and that one thing really is
    # still missing. A guide promising what exists is MH-3's finding;
    # a guide promising what it already has would repeat it.
    promise = [p for p in re.split(r'(?<=[.!])\s+', text)
               if 'not yet' in p.lower() or 'coming' in p.lower()]
    for gone in ('moving a meal from one day to another',
                 'a free-text note on a day', 'saved menus'):
        if any(gone in p for p in promise):
            refuse('%s: still promises %r, which the planner does'
                   % (HELP, gone))
    # AND THE WORD 'coming' APPEARS ONLY IN THE PROMISE.
    #
    # THE RECURRING TRAP, from the other side. The suite finds the
    # promise by collecting every sentence containing 'coming' and
    # then asking what those sentences name - so ordinary English
    # joins the register. This round's first draft wrote "coming back
    # from a dialog", "without coming here at all" and "the coming
    # Saturday", and the guide's own suite reported three promises
    # that were not promises. A word a gate reads as a keyword cannot
    # also be used as a word.
    loose = [p.strip()[:70]
             for p in re.split(r'(?<=[.!])\s+', text)
             if 'coming' in p.lower() and 'Not yet' not in p]
    if loose:
        refuse('%s: %r uses the word "coming" outside the promise box, '
               'and test_meal_help reads that word as the marker of a '
               'promise' % (HELP, loose[0]))

    pv = T.python_code_only(
        read(os.path.join(root, 'pages', 'views', 'recipes',
                          'meal_planning.py')), payloads=True)
    if 'def reorder' in pv:
        refuse('%s: reordering a day exists now, so the one remaining '
               'promise is stale too' % HELP)

    if CHECK:
        print('MH-5  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        tabs: %d -> %d' % (TABS_WAS_N, TABS_NOW_N))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('MH-5  applied - the guide describes the calendar that is there.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      tabs: %d -> %d' % (TABS_WAS_N, TABS_NOW_N))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
