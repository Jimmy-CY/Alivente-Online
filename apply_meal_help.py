# -*- coding: utf-8 -*-
"""apply_meal_help.py - round MH-1, 18 Oct 2026.

THE MEAL PLANS USER GUIDE. One guide, seven tabs, five pages.

Demetri, 18 Oct: "You will also need to fully update the help sections
of the whole meal plan module !!"

WHAT WAS THERE, MEASURED BEFORE A WORD WAS WRITTEN. The answer was
worse than stale.

    NONE OF THE FIVE MEAL-PLAN PAGES HAD A HELP BUTTON. Not the list,
    not the calendar, not Create/Edit, not the plan page, not the
    shopping list. Thirty-two other pages in the tree have one.

    THERE WAS NO MEAL-PLAN HELP MODULE. Forty-nine module slugs across
    six files under pages/help_content/, and not one of them was a
    meal-plan slug.

    THE ONLY MEAL-PLAN HELP IN THE APPLICATION was a single 3,067-byte
    tab inside `recipe_management` - reachable only from the Recipe
    Management page, which is not where anybody stands when they have
    a question about a meal plan.

AND WHAT THAT TAB SAID WAS WRONG IN FOUR PLACES.

    "Add or remove recipes directly from the calendar view."

    That is A1. Every such click was a TypeError before the view ran,
    from before the tab was written until MP-1 fixed it this
    afternoon. The help has been describing a server error as a
    feature.

    "Share via Print, Copy, Email or WhatsApp" - SL-4 made the share
    row Copy / Email / WhatsApp on 3 Oct and SL-1 moved Print into the
    page bar. Four named, three there.

    "Tick off what you already have in your pantry" - the screen calls
    that step Review Ingredients, and it is step 1 of 2.

    And it named the Calendar View's dots and the Duplicate dialog
    while saying nothing about Edit, which is the screen that loses
    meals.

NINE THINGS IT DID NOT MENTION AT ALL: the Edit screen; that shortening
a plan removes the meals on the dropped days; that a plan name is
required; that servings default to the recipe's own yield; that two
plans over one week means the calendar shows one of them; that the
shopping-list email goes only to household members; what to do when an
ingredient has no shopping unit; who may view versus edit; and that
every user sees every meal plan, deliberately.

----------------------------------------------------------------------
THE SHAPE, AND WHY IT BREAKS THE HOUSE PATTERN ON PURPOSE

All 32 pages that carry help render EXACTLY ONE module, and no module
is rendered on two pages. Help in this application has been per PAGE,
never per feature.

Read strictly, five meal-plan pages would mean five modules. Demetri
chose ONE GUIDE ACROSS FIVE PAGES on 18 Oct, and the reason is the
reason: the meal plan module is one journey - list, calendar, build,
view, shop - and five separate guides would repeat each other and then
drift apart, which is the fault B12 and CU-1 were both about.

So `meal_plans` is the first module in the tree rendered by more than
one page. The shell keys every id off the slug, so five copies of the
same modal on five different pages collide with nothing.

THE OLD TAB BECOMES A POINTER rather than being deleted. Somebody who
has learnt to find meal-plan help under Recipe Management should not
find a gap where it was - and a second copy of the same prose is how
two documents come to disagree.
"""
import os
import re
import sys

SUFFIX = '.bak_mealhelp'
HELP = os.path.join('pages', 'help_content', 'administration.html')
CAL = os.path.join('pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join('pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join('pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join('pages', 'templates', 'view_meal_plan.html')
PAGES = (LIST, CAL, CREATE, VIEWT, SHOP)
ME = 'test_meal_help.py'
PATCHER = 'apply_meal_help.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
SLUG = 'meal_plans'
CHECK = False

# ===================================================== THE GUIDE ITSELF

# ===================================================== THE GUIDE ITSELF
# Seven tabs, 22.5 KB, in the house help-content style: inline hex
# rather than tokens, because manual_pdf.html takes the help CONTENT
# without the shell and so has no tokens to inherit - recorded in
# test_accent_ink.py section 5.
SECTION = r'''<section data-module-slug="meal_plans"
         data-module-group="Personal"
         data-module-permission="can_access_recipes"
         data-module-name="Meal Plans"
         data-module-icon="fa-calendar-alt"
         data-module-category="Personal"
         data-module-subtitle="Plan a week of meals, then shop for it in one list">

  <article data-tab-slug="mp-overview"
           data-tab-name="Overview"
           data-tab-icon="fa-info-circle">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-calendar-alt" style="color:#28a745;"></i> Meal Plans</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">A <strong>meal plan</strong> is a short stretch of days &mdash; anything from one day to seven &mdash; with recipes assigned to each of them. Once a plan exists you can turn it into a single consolidated <strong>shopping list</strong> that adds up every ingredient across every recipe for the whole plan.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list" style="color:#28a745;"></i> Two ways to look at them:</strong> the <strong>list</strong> shows every plan with its dates and how many meals are on it; the <strong>calendar</strong> shows a month at a glance with one week opened beside it. The two toggle buttons at the top of either page switch between them, and whichever you chose last is the one you come back to.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-users" style="color:#0e7c8b;"></i> Everyone sees every plan.</strong> Meal plans are not private to the person who made them &mdash; this is deliberate, and it matches the recipes they are built from, which are shared across the whole installation. If you can open Recipes, you can see every meal plan.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-calendar-day" style="color:#0e7c8b;"></i> One to seven days.</strong> A plan cannot be longer than a week. If you want a fortnight, make two plans &mdash; or make one and use <strong>Duplicate</strong> to copy it onto the following week.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-history" style="color:#e6a817;"></i> Past dates are allowed.</strong> On both Create and Edit. A meal plan is just as useful as a record of what you <em>did</em> eat as a plan for what you will.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Where to start:</strong> if you have never made one, go to <strong>Meal Plans</strong> and press <strong>Create New Meal Plan</strong>. It opens on next Monday with a seven-day range already filled in, so you can go straight to choosing recipes.
    </div>
  </article>

  <article data-tab-slug="mp-calendar"
           data-tab-name="The Calendar"
           data-tab-icon="fa-calendar-alt">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #0e7c8b; padding-bottom:6px;"><i class="fas fa-calendar-alt" style="color:#0e7c8b;"></i> The Calendar</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">The calendar is two panels. On the left, a month grid and the list of your plans. On the right, <strong>one week opened in detail</strong>, with a card for each of its seven days.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-circle" style="color:#0e7c8b; font-size:10px;"></i> The dots</strong> mark days that have at least one meal planned. Days inside a plan's date range are shaded, whether or not anything is on them yet.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-hand-pointer" style="color:#0e7c8b;"></i> Clicking a week row</strong> in the month grid opens that week on the right, and the row you chose stays highlighted so you can see where you are. Clicking a <strong>plan</strong> in the list on the left does the same thing for the week that plan starts in. Weeks always run Monday to Sunday, however you got there.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-plus" style="color:#28a745;"></i> Adding a recipe to a day:</strong> press <strong>Add Recipe</strong> on the day card, search for the recipe, select it and press Add. The servings box fills itself in from the recipe's own yield &mdash; a recipe that makes six arrives offering six &mdash; and you can change it before adding.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-trash" style="color:#dc3545;"></i> Removing one:</strong> the trashcan on the meal. It asks first, and it removes that meal from that day only &mdash; the recipe itself is untouched.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-info-circle" style="color:#e6a817;"></i> Days outside the plan.</strong> A week always shows seven days, but a plan may be shorter. The days a plan does not cover say so, and offer you <strong>Change the dates</strong> &mdash; lengthening the plan is what makes them available, and it keeps the meals already on it.
      </div>

    </div>

    <div style="background:#fff3cd; border:1px solid #ffeaa7; border-radius:8px; padding:12px; font-size:13px; color:#856404;">
      <i class="fas fa-exclamation-triangle"></i> <strong>Two plans over the same week:</strong> nothing stops you making them, but the calendar can only open <strong>one</strong> plan for a given week. It tells you when there is more than one and names the one it is showing; the others are on the Meal Plans list. Create and Duplicate both warn you before you make an overlap.
    </div>
  </article>

  <article data-tab-slug="mp-build"
           data-tab-name="Building a Plan"
           data-tab-icon="fa-edit">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-edit" style="color:#28a745;"></i> Creating and editing a plan</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Create and Edit are the same screen. Give the plan a <strong>name</strong> and a <strong>start and end date</strong>, and a card appears for each day in the range, ready for recipes.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-tag" style="color:#28a745;"></i> The name is required</strong> on both Create and Edit, because the name is how you tell two plans apart everywhere else in the application.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-calendar-week" style="color:#0e7c8b;"></i> The dates arrive filled in.</strong> Coming from the calendar, the form opens on the week you were looking at. Coming from the list, it opens on next Monday. Either way the range is seven days, and you can shorten it.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-utensils" style="color:#0e7c8b;"></i> Choosing recipes:</strong> <strong>Add Recipe</strong> on a day card opens the picker, with a search box and filters for course, category, protein and author. Select a recipe and it drops onto that day. The servings come from the recipe, and you can change them on the row afterwards.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-clone" style="color:#0e7c8b;"></i> The same recipe twice on one day</strong> is allowed and survives a save &mdash; useful when you cook a double batch, or the same dish for lunch and dinner. Each row keeps its own servings.
      </div>

    </div>

    <div style="background:#fff3cd; border:1px solid #ffeaa7; border-radius:8px; padding:12px; font-size:13px; color:#856404; margin-bottom:16px;">
      <i class="fas fa-exclamation-triangle"></i> <strong>Changing the dates of a plan that already has meals on it.</strong> Days that fall outside the new range are removed, and the meals on them go with them. The page warns you <strong>before you save</strong> and says how many meals and how many days it is about to drop, and the confirmation afterwards says what it removed. Shortening a plan on purpose is a normal thing to do &mdash; the warning is there so it is never a surprise.
    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> if you want to move a plan to different dates rather than reshape it, use <strong>Duplicate</strong> with <strong>Delete original after duplicating</strong> ticked. The meals move with the plan and nothing is dropped.
    </div>
  </article>

  <article data-tab-slug="mp-plan"
           data-tab-name="The Plan Page"
           data-tab-icon="fa-eye">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #0e7c8b; padding-bottom:6px;"><i class="fas fa-eye" style="color:#0e7c8b;"></i> One plan, in full</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Opening a plan shows a card per day, each listing its meals with their photo, servings, times and tags. Clicking a meal opens the recipe.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-pencil-alt" style="color:#0e7c8b;"></i> Edit</strong> takes you to the build screen with everything already filled in. Saving brings you back to where you started &mdash; including the right week of the calendar, if that is where you came from.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-copy" style="color:#e6a817;"></i> Duplicate</strong> makes a copy under a new name, starting on a date you choose, keeping the same duration and the same meals in the same order. Tick <strong>Delete original after duplicating</strong> and it becomes a <strong>shift</strong> instead &mdash; the plan moves to the new dates rather than being copied. This option is on the Duplicate dialog wherever you find it: the list, the calendar and this page.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-shopping-cart" style="color:#28a745;"></i> Shopping List</strong> turns the whole plan into one list to shop from. See the Shopping List tab.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-trash" style="color:#dc3545;"></i> Delete</strong> removes the plan and every meal on it. It asks first. The recipes themselves are never touched by anything on this page.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> on a phone the secondary controls fold into the <strong>More</strong> menu rather than crowding the top of the page. Everything is still there.
    </div>
  </article>

  <article data-tab-slug="mp-shopping"
           data-tab-name="Shopping List"
           data-tab-icon="fa-shopping-cart">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-shopping-cart" style="color:#28a745;"></i> Shopping for a whole plan at once</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">The shopping list walks every recipe in the plan, scales each ingredient to the servings you planned, converts it into the unit you actually buy that ingredient in, adds up the totals across recipes, rounds <strong>up</strong> so you never come home short, and groups the result by aisle.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-check-square" style="color:#0e7c8b;"></i> Step 1 &mdash; Review Ingredients.</strong> Everything the plan needs, with its total. <strong>Tick what you already have at home</strong> and it will be left off the list.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list-ul" style="color:#28a745;"></i> Step 2 &mdash; Items to Buy.</strong> What is left, grouped by category. This is the list you shop from.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-exchange-alt" style="color:#e6a817;"></i> When a conversion is missing.</strong> If a recipe measures something in cups and you buy it in grams, the list needs to know how the two relate. It asks you once, on the page, and remembers the answer for every list afterwards.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-exclamation-triangle" style="color:#dc3545;"></i> NOT ON THIS LIST.</strong> Two things can keep an ingredient off the list entirely, and the page now names them rather than leaving them out in silence. A recipe line with <strong>no unit</strong> has no quantity to add up &mdash; fix it on the recipe. An ingredient with <strong>no shopping unit</strong> has nothing to convert into &mdash; the <strong>Set base units</strong> button takes you to the screen that fixes it.
      </div>

    </div>

    <h6 style="font-weight:700; color:#2c3e50; margin:20px 0 12px; font-size:13px;">Getting the list out of the application</h6>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;">Three buttons above the list:</strong> <strong>Copy</strong> puts it on the clipboard, <strong>WhatsApp</strong> opens a message with it in, and <strong>Email</strong> opens a panel to choose a recipient. <strong>Print</strong> is in the page's own button bar at the top, not among the three.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-paper-plane" style="color:#e6a817;"></i> Email goes to household members only.</strong> The list you choose from is the people on the <strong>Household Members</strong> screen who have an email address and are still active &mdash; plus your own address, always. Nothing else can be sent to, because the message leaves from this application's own address.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> do the ticking before you leave the house, not in the shop. Step 1 is the pantry check and step 2 is the list &mdash; and the quantities are already rounded up to what you can actually buy.
    </div>
  </article>

  <article data-tab-slug="mp-permissions"
           data-tab-name="Who Can Do What"
           data-tab-icon="fa-user-shield">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #0e7c8b; padding-bottom:6px;"><i class="fas fa-user-shield" style="color:#0e7c8b;"></i> Permissions</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Meal plans use the same two permissions as the rest of the Recipes module. There is no separate meal-plan permission to grant.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-eye" style="color:#0e7c8b;"></i> Recipes access</strong> lets you see the list, the calendar, any plan and any shopping list. Every plan, not only your own.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-pencil-alt" style="color:#28a745;"></i> Recipes edit</strong> lets you create, edit, duplicate, shift and delete plans, add and remove meals, and email a shopping list. Again, on any plan &mdash; not only the ones you made.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-ban" style="color:#e6a817;"></i> Without edit permission</strong> the controls that change something are shown greyed out rather than hidden, so the screen looks the same to everybody and it is clear what you would be able to do.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> Permissions are granted per user on the <strong>User Administration</strong> screen, under the Recipes module.
    </div>
  </article>

  <article data-tab-slug="mp-tips"
           data-tab-name="Tips"
           data-tab-icon="fa-lightbulb">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-lightbulb" style="color:#28a745;"></i> Getting the most out of it</h6>

    <div style="display:flex; flex-direction:column; gap:12px;">

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-redo"></i> Plan once, duplicate after.</strong> Build one good week, then duplicate it forward with a new start date. It is faster than starting again, and you can swap out a meal or two on the copy.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-arrows-alt-h"></i> Shift rather than reshape.</strong> If a week slips, duplicate it onto the new dates with <strong>Delete original</strong> ticked. Changing the dates of the plan itself drops the meals on the days that fall outside the new range &mdash; it warns you, but shifting avoids the question.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-balance-scale"></i> Fix the base units once.</strong> Every ingredient that has a shopping unit set is one more line that lands on the list automatically. The <strong>NOT ON THIS LIST</strong> banner tells you exactly which ones are still missing, so it is a finite job rather than a vague one.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-history"></i> Record, as well as plan.</strong> Past dates are allowed, so a plan for last week is a perfectly good note of what you actually ate &mdash; and the shopping list will tell you what it cost in ingredients.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the pickers and the dialogs. The shopping list in particular is meant to be read in the shop.
      </div>

    </div>
  </article>

</section>'''

# ================================================== WHERE IT IS INSERTED
# Immediately before the recipe_management section, so the two sit
# together in the file the way they sit together in the menu. The
# renderer reads every .html in pages/help_content/ and keys on the
# slug, so position does not affect behaviour - it affects whether the
# next person can find it.
ANCHOR = """<section data-module-slug="recipe_management\""""

# ================================================== THE OLD TAB BECOMES A POINTER
# NOT DELETED. Somebody who has learnt to find meal-plan help under
# Recipe Management should not find a gap - and a second copy of the
# same prose is how two documents come to disagree, which is the whole
# of B12 and CU-1.
OLD_TAB_HEAD = """  <article data-tab-slug="rec-mealplans"
           data-tab-name="Meal Plans"
           data-tab-icon="fa-calendar-alt">"""

POINTER = """  <article data-tab-slug="rec-mealplans"
           data-tab-name="Meal Plans"
           data-tab-icon="fa-calendar-alt">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-calendar-alt" style="color:#28a745;"></i> Meal Plans</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Meal plans have their own guide now, with a tab for each screen: the calendar, building a plan, the plan page, the shopping list and who can do what.</p>

    <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d; margin-bottom:16px;">
      <strong style="color:#2c3e50;"><i class="fas fa-book" style="color:#0e7c8b;"></i> Where to find it:</strong> press <strong>Help</strong> on any of the five meal-plan screens &mdash; the list, the calendar, Create or Edit, a plan, or its shopping list. It is the same guide on all five, so whichever screen raised the question is the one that answers it.
    </div>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">In short: a plan is one to seven days with recipes on each of them, every user can see every plan, and the shopping list adds up every ingredient across the whole plan and rounds up so you do not come home short.</p>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> use the Meal Plan Shopping List before your weekly shop. Tick off what is already in the cupboard in step 1 and step 2 is the list you actually take with you.
    </div>
  </article>"""

# ===================================================== THE FIVE PAGES
# {% load %} FIRST. The tag is in help_modal_tags, and a page that
# renders the modal without loading it is a TemplateSyntaxError on the
# page itself - which is a worse outcome than no help at all. Every one
# of the five opens with {% load static %} on line 2.
LOAD_WAS = """{% load static %}"""
LOAD_NOW = """{% load static %}
{# MH-1, 18 Oct 2026 - the Meal Plans guide. One module across all five #}
{# meal-plan screens: list, calendar, build, plan, shopping list. The   #}
{# first module in the tree rendered by more than one page, by          #}
{# Demetri's decision on 18 Oct - the meal plan module is one journey,  #}
{# and five separate guides would repeat each other and then drift.     #}
{% load help_modal_tags %}"""

# THE BUTTON, immediately before the Back control in each bar, because
# Back is last in every bar in the tree. Five different anchors, because
# five pages spell their Back differently - two carry the calendar
# context, one goes to Recipes, one has two Backs for two steps.
HELP_BTN = """        {# MH-1, 18 Oct 2026 - Help, before Back because Back is last in #}
        {# every bar in the tree. The same guide on all five screens.     #}
        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#%sHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>
""" % SLUG

BTN_LIST_WAS = """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">"""
BTN_CAL_WAS = """            <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">"""
BTN_CREATE_WAS = """            <a href="{% if request.GET.from == 'calendar' %}{% url 'meal_plan_calendar' %}?week={{ request.GET.week }}{% else %}{% url 'meal_plans' %}{% endif %}" class="btn action-back" aria-label="Back to Meal Plans">
                <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
            </a>"""
BTN_VIEW_WAS = """        <a href="{% if request.GET.from == 'calendar' %}{% url 'meal_plan_calendar' %}?week={{ request.GET.week }}{% else %}{% url 'meal_plans' %}{% endif %}" class="btn action-back" aria-label="Back to Meal Plans">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>"""
BTN_SHOP_WAS = """        <a href="{% url 'view_meal_plan' meal_plan.meal_plan_id %}{% if request.GET.from == 'calendar' %}?from=calendar&amp;week={{ request.GET.week }}{% endif %}" class="btn action-back" id="backLink" aria-label="Back to Meal Plan">"""

# AND THE MOBILE MORE MENU, on the one page that has one. Without this
# the Help button is in the bar on a phone too, which is exactly what
# the More menu exists to prevent - recipe_management puts Help in both
# places for the same reason.
MORE_WAS = """                <button type="button" class="action-more-item" role="menuitem" onclick="window.print()">"""
MORE_NOW = """                {# MH-1, 18 Oct 2026 - Help in the More menu as well as the  #}
                {# bar, the way recipe_management does it. This is the only   #}
                {# one of the five pages with a More menu.                    #}
                <button type="button" class="action-more-item" role="menuitem" data-toggle="modal" data-target="#%sHelpModal">
                    <i class="fas fa-question-circle"></i> Help
                </button>
                <button type="button" class="action-more-item" role="menuitem" onclick="window.print()">""" % SLUG

# THE MODAL, at the end of the content block. The shell keys every id
# off the slug, so five copies on five pages collide with nothing - and
# a page only ever renders one of them.
RENDER = """{%% render_help_modal "%s" %%}
{%% endblock %%}""" % SLUG


# ================================================ THREE INSTRUMENTS CORRECTED
# Five new Help buttons change three things that are counted elsewhere.
# All three were right to notice.

# (a) THE HELP CENSUS. test_help_label pins the number of Help controls
#     in the tree, and asserts every one writes BARE TEXT - no
#     .action-back-label wrapper. The five new ones follow that, so the
#     claim is unchanged; only the number moves.
HL = 'test_help_label.py'
HL_WAS = """HELP_TOTAL = 41   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)"""
HL_NOW = """HELP_TOTAL = 46   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)"""

# (b) THE SECONDARY-VISIBLE RENDER. SV's section 5 renders every bar
#     that has an action-secondary and NO More menu, under the current
#     base CSS and under the CSS as it was before that round, and
#     requires the two to be identical on the desktop.
#
#     THE MEAL PLANS LIST AND THE CALENDAR HAD NO SECONDARY AT ALL
#     UNTIL NOW. They are new entrants to that set, and for a bar that
#     did not exist in the set when SV ran, the two stylesheets
#     legitimately disagree: the old one hid the secondary and the new
#     one shows it. That IS the round SV shipped.
#
#     MEASURED BEFORE THIS ENTRY WAS WRITTEN, because an exemption
#     written on an assumption is worse than no exemption. All five
#     bars were rendered at 1200 and at 390, before and after MH-1,
#     under the CURRENT stylesheet: same row count, same height, no
#     sideways scroll, one more control in each. The Help button fits.
#     test_meal_help.py section 9 does that measurement on every run,
#     so this is a recorded difference and not a silenced check.
SV = 'test_secondary_visible.py'
SV_WAS = """MOVED_BY = {
    'finance_pl_act.html':
        'PN-1, 3 Oct 2026 - a segment in a bar takes the bar height',
}"""
SV_NOW = """MOVED_BY = {
    'finance_pl_act.html':
        'PN-1, 3 Oct 2026 - a segment in a bar takes the bar height',
    # MH-1, 18 Oct 2026. NEW ENTRANTS, not bars that moved.
    #
    # Neither of these had an action-secondary when this round ran, so
    # neither was in NEEDY and neither was ever rendered here. MH-1 put
    # a Help button in both bars, and for a bar whose secondary did not
    # exist under the old stylesheet the two CSS versions must differ -
    # the old one hid secondaries unconditionally, which is the whole
    # thing this round changed.
    #
    # What matters for these two pages is whether the extra control
    # changes the bar, and that is measured rather than assumed:
    # test_meal_help.py renders all five meal-plan bars at 1200 and 390
    # before and after MH-1 under the current stylesheet, and requires
    # the same row count, the same height and no sideways scroll.
    'meal_plans.html':
        'MH-1, 18 Oct 2026 - a Help button, and this bar had no '
        'secondary at all when this round ran',
    'meal_plan_calendar.html':
        'MH-1, 18 Oct 2026 - the same, on the calendar',
}"""

# (c) THE SENTINEL THAT CANNOT FAIL - and MH-1 did not write it.
#
#     A row has watched help_content/administration.html for the string
#     'nothing to press' since the admin help was written. It sat in
#     test_sentinels' "names a file no round has ever backed up" bucket,
#     where a row is listed but never examined. MH-1 edits that file and
#     so gives it its FIRST BACKUP - which makes the row checkable, and
#     it turns out not to discriminate: the prose has been there longer
#     than the only version there is to compare against.
#
#     THIS HAS HAPPENED BEFORE, ONCE, AND THE ANSWER IS THE SAME. The
#     fifth PINNED entry arrived on 5 Oct for exactly this reason -
#     RA-2 widened alv_rowactions.py, gave it its first backup, and an
#     RA-1 sentinel became checkable and did not discriminate.
SN = 'test_sentinels.py'
SN_WAS = """PINNED = {
    'pd-detail-table':"""
SN_NOW = """PINNED = {
    # THE SIXTH, 18 OCT 2026, and it arrived the way the fifth did -
    # not because anybody wrote it today, but because MH-1 edited
    # help_content/administration.html for the first time and so gave
    # that file its first backup. The row became checkable, and the
    # prose it watches is older than the one version there is to
    # compare it against.
    'nothing to press':
        'the admin help prose, backed up for the first time by MH-1 on '
        '18 Oct - the sentence predates every version this repo holds',
    'pd-detail-table':"""

# ============================================================ REGISTRATION
TREE_WAS = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Twelve
    # display, navigation, query and hygiene items. Wide from birth.
    'test_meal_display.py',
]"""
TREE_NOW = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Twelve
    # display, navigation, query and hygiene items. Wide from birth.
    'test_meal_display.py',
    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Seven tabs, and a
    # Help button on five screens that had none. Wide from birth.
    'test_meal_help.py',
]"""

REG_WAS = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Named
    # MD-1 and not MP-2, which has been a shipped round since 3 October.
    '.bak_mealdisplay',
]"""
REG_NOW = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E. Named
    # MD-1 and not MP-2, which has been a shipped round since 3 October.
    '.bak_mealdisplay',
    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Five screens had no
    # Help button at all, and the only meal-plan help in the application
    # described a calendar feature that was a server error.
    '.bak_mealhelp',
]"""

SUITE_WAS = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E.
    'test_meal_display.py'
)"""
SUITE_NOW = """    # MD-1, 18 Oct 2026 - Meal Plans release 1, groups D and E.
    'test_meal_display.py',
    # MH-1, 18 Oct 2026 - the Meal Plans user guide, on five screens.
    'test_meal_help.py'
)"""

SENT_WAS = (
    "    @{ File = 'pages/templates/view_meal_plan.html'; "
    "Text = '.btn-action-disabled'; What = 'MD-1: the swallowed selector "
    "that made disabled buttons look live' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- MH-1, 18 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-slug="meal_plans"'; What = 'MH-1: the Meal Plans guide exists at all' },
    @{ File = 'pages/templates/meal_plan_calendar.html'; Text = 'meal_plansHelpModal'; What = 'MH-1: the calendar has a Help button' },"""


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
    raise SystemExit('MH-1 REFUSED: %s' % msg)


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


def before(text, anchor, insert, where):
    """Put `insert` immediately before `anchor`, which must be unique."""
    once(text, anchor, where)
    a = fit(text, anchor)
    return text.replace(a, fit(text, insert) + a)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    ph = os.path.join(root, HELP)
    h = read(ph)

    # ---------------------------------------------------------------- 0
    if 'data-module-slug="%s"' % SLUG in h:
        print('MH-1  already applied - the Meal Plans guide is in the tree.')
        return 0

    # ---------------------------------------------------------------- 1
    if not os.path.isfile(os.path.join(root, ME)):
        refuse('%s is not on disk - it is half the round' % ME)

    # THE TAG MUST EXIST. A page that renders a modal from a library it
    # cannot load is a TemplateSyntaxError on the page itself, which is
    # a worse outcome than no help at all.
    tags = os.path.join(root, 'pages', 'templatetags', 'help_modal_tags.py')
    if not os.path.isfile(tags):
        refuse('pages/templatetags/help_modal_tags.py is not on disk, so '
               '{%% render_help_modal %%} would be a TemplateSyntaxError on '
               'all five pages')
    if 'render_help_modal' not in read(tags):
        refuse('help_modal_tags.py does not register render_help_modal')

    # AND THE SLUG MUST BE FREE. Forty-nine modules across six files,
    # and a duplicate slug means the renderer's lookup dict keeps
    # whichever it read last - silently.
    hd = os.path.join(root, 'pages', 'help_content')
    for f in sorted(os.listdir(hd)):
        if not f.endswith('.html') or '.bak_' in f:
            continue
        if 'data-module-slug="%s"' % SLUG in read(os.path.join(hd, f)):
            refuse('help_content/%s already defines the slug %r - the '
                   'renderer keys its lookup on the slug and would keep '
                   'whichever file it read last' % (f, SLUG))

    # ---------------------------------------------------------------- 2
    # THE GUIDE, before its sibling, and the old tab becomes a pointer.
    h = before(h, ANCHOR, SECTION + '\n\n', '%s (the guide)' % HELP)
    # THE OLD TAB, FROM ITS <article> TO ITS </article>. fit() because
    # this file is CRLF and every literal in this patcher is LF - the
    # first spelling of this line looked for an LF anchor in a CRLF file
    # and raised "substring not found" from inside .index(), which says
    # nothing useful. once() would have refused with a sentence.
    _head = fit(h, OLD_TAB_HEAD)
    once(h, OLD_TAB_HEAD, '%s (the old Meal Plans tab)' % HELP)
    i = h.index(_head)
    j = h.index(fit(h, '</article>'), i) + len('</article>')
    h = h[:i] + fit(h, POINTER) + h[j:]
    out[ph] = h

    # ---------------------------------------------------------------- 3
    # THE FIVE PAGES.
    bars = {LIST: BTN_LIST_WAS, CAL: BTN_CAL_WAS, CREATE: BTN_CREATE_WAS,
            VIEWT: BTN_VIEW_WAS, SHOP: BTN_SHOP_WAS}
    for page in PAGES:
        p = os.path.join(root, page)
        t = read(p)
        t = swap(t, LOAD_WAS, LOAD_NOW, '%s (the load tag)' % page)
        anchor = bars[page]
        # The indentation of the bar differs per page, so the button is
        # re-indented to match the control it sits above rather than
        # being written five times.
        pad = anchor[:len(anchor) - len(anchor.lstrip())]
        btn = '\n'.join(
            (pad + ln[8:] if ln.startswith('        ') else ln)
            for ln in HELP_BTN.rstrip('\n').split('\n')) + '\n'
        t = before(t, anchor, btn, '%s (the Help button)' % page)
        # THE MODAL, at the end of the content block. rindex, because a
        # page may carry {% endblock %} more than once and the LAST one
        # closes content.
        # fit(), AND IT WAS MISSING. The first spelling spliced this
        # LF literal straight into the file, and three of the five
        # templates are CRLF - so each took exactly one bare LF and
        # became a file with mixed line endings. test_recipe_photos has
        # a check for precisely that ("not one edited file changed
        # which line ending it uses"), and it is the only thing in the
        # tree that would ever have noticed.
        #
        # rindex, because a page may carry {% endblock %} more than once
        # and the LAST one closes content.
        end = fit(t, '{% endblock %}')
        k = t.rindex(end)
        t = t[:k] + fit(t, RENDER) + t[k + len(end):]
        out[p] = t

    # ---------------------------------------------------------------- 4
    # AND THE MORE MENU, on the one page that has one.
    p = os.path.join(root, VIEWT)
    out[p] = swap(out[p], MORE_WAS, MORE_NOW, '%s (the More menu)' % VIEWT)

    # --------------------------------------------------------------- 4b
    # THE THREE INSTRUMENTS FIVE NEW HELP BUTTONS MOVE.
    p = os.path.join(root, HL)
    out[p] = swap(read(p), HL_WAS, HL_NOW, '%s (the Help census)' % HL)

    p = os.path.join(root, SV)
    out[p] = swap(read(p), SV_WAS, SV_NOW, '%s (MOVED_BY)' % SV)

    p = os.path.join(root, SN)
    out[p] = swap(read(p), SN_WAS, SN_NOW, '%s (PINNED)' % SN)

    # ---------------------------------------------------------------- 5
    # REGISTRATION.
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, 'Push-PendingChanges.ps1')
    t = read(p)
    t = swap(t, SUITE_WAS, SUITE_NOW, 'Push-PendingChanges.ps1 ($suites)')
    t = swap(t, SENT_WAS, SENT_NOW, 'Push-PendingChanges.ps1 (sentinels)')
    out[p] = t

    p = os.path.join(root, WD)
    s = read(p)
    m = re.search(r'CONVERTED_N = (\d+)', s)
    if not m:
        refuse('%s has no CONVERTED_N' % WD)
    was = int(m.group(1))
    out[p] = s.replace('CONVERTED_N = %d' % was,
                       'CONVERTED_N = %d   # MH-1, 18 Oct 2026 - this '
                       'round own suite   # (was %d)' % (was + 1, was), 1)

    if CHECK:
        print('MH-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, val in out.items():
        backup(k)
        write(k, val)
    print('MH-1 applied.  The Meal Plans user guide.')
    print('   seven tabs: Overview, The Calendar, Building a Plan, The Plan')
    print('   Page, Shopping List, Who Can Do What, Tips')
    print('   a Help button on all five meal-plan screens, which had none')
    print('   and the old tab under Recipe Management points at it rather')
    print('   than repeating it - it said the calendar could add recipes,')
    print('   which was a server error from before it was written')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
